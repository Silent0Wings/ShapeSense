"""Class-safe augmentation for Stage 2: `transform(img, label, rng)`.

Contract (stages/stage_2.md R1-R7):
  img    uint8 (S, S), S = config["image_size"]; black (0) outline on white (255)
  label  int, index into configs/taxonomy.yaml; never changes
  rng    np.random.Generator; the only source of randomness
  return uint8 (S, S), values only in {0, 255}; never a label

Shear and non-uniform scale apply only to labels NOT listed in
taxonomy.no_shear_no_nonuniform_scale (read from config, not hard-coded).
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from src.common.config import load_default_config
from src.stage2_augment.geometry import (
    BLACK_LEVEL,
    WHITE_LEVEL,
    compose_affine,
    ink_coords,
    within_frame,
)

INK_VALUE = 1.0            # ink level in the float ink map (paper = 0.0), unitless
BINARY_LEVEL = 0.5         # re-threshold on the 0..1 ink map (half of INK_VALUE)
FRAME_MARGIN_PX = 1        # pixels kept white between the ink and the frame edge
FIT_SHRINK_FACTOR = 0.97   # multiplicative scale step when the ink does not fit, unitless
MAX_FIT_STEPS = 100        # bound on shrink iterations (0.97**100 is about 0.05)
THIN_LINE_LEVEL = 0.2      # share of the warped peak kept for 1-px strokes, so they stay joined
SHAPE_CACHE_SIZE = 20_000  # stored images whose ink facts are kept; synthetic images churn through it


@dataclass(frozen=True)
class _Ranges:
    """Augmentation ranges read from config["augment"] and config["image_size"]."""

    size: int                     # frame side, pixels
    ink_threshold: float          # grey level below which a pixel is ink
    rotate_deg: float             # +/- degrees
    scale: tuple[float, float]    # uniform scale factor range
    nonuniform_scale: float       # +/- per-axis extra factor (allowed labels only)
    shear_deg: float              # +/- degrees (allowed labels only)
    translate_px: float           # +/- pixels per axis
    noise_p: float                # probability of outline noise
    noise_fraction: float         # share of frame pixels flipped when noise applies
    blur_p: float                 # probability of Gaussian blur
    blur_sigma: tuple[float, float]  # sigma range, pixels
    frame_margin: float           # standardization margin, share of the bbox side


@functools.lru_cache(maxsize=8)
def _outer_ring(size: int, width: int) -> np.ndarray:
    """(size, size) bool mask of the outermost `width` pixels (the frame margin). Read-only."""
    mask = np.ones((size, size), dtype=bool)
    mask[width:size - width, width:size - width] = False
    mask.setflags(write=False)
    return mask


@functools.lru_cache(maxsize=SHAPE_CACHE_SIZE)
def _ink_facts(pixels: bytes, size: int, threshold: float) -> tuple[np.ndarray, bool]:
    """(ink pixel positions, whether the stroke is 1 px thin) for one image. Read-only.

    The same stored images are augmented many times, and neither fact depends on the random draw.
    """
    img = np.frombuffer(pixels, dtype=np.uint8).reshape(size, size)
    pts = ink_coords(img, threshold)
    pts.setflags(write=False)
    ink = img < threshold
    # Thin means no 2x2 block is all ink, which is what a 2x2 binary erosion tests.
    solid = ink[:-1, :-1] & ink[:-1, 1:] & ink[1:, :-1] & ink[1:, 1:]
    return pts, not solid.any()


def _render(ink: np.ndarray, matrix: np.ndarray, center: np.ndarray,
            shift: np.ndarray, size: int, sigma: float | None, thin: bool = False) -> np.ndarray:
    """Warp the float ink map about the centroid, optionally blur, then binarise.

    ink: (S, S) float64 in {0, INK_VALUE}. matrix: (2, 2) forward linear map.
    center, shift: (2,) float. sigma: Gaussian sigma in pixels, or None.
    Returns (S, S) bool, True where ink remains.
    """
    inv = np.linalg.inv(matrix)
    offset = center - inv @ (center + shift)
    warped = ndimage.affine_transform(ink, inv, offset=offset, output_shape=(size, size),
                                      order=1, mode="constant", cval=0.0)
    if sigma is not None:
        warped = ndimage.gaussian_filter(warped, sigma=sigma, mode="constant", cval=0.0)
    # Shrinking spreads a 2-px stroke's ink over fewer pixels at lower levels;
    # lowering the cut by the linear shrink keeps the outline connected
    # (stages/stage_2.md Should 2) without thickening it at scale >= 1.
    shrink = min(1.0, float(np.sqrt(abs(np.linalg.det(matrix)))))
    level = BINARY_LEVEL * shrink
    if sigma is not None and warped.max() > 0:
        # A blurred 1-px sketch line peaks below 0.5; cut relative to the
        # blurred peak so blur softens the outline but never erases it.
        level = min(level, BINARY_LEVEL * float(warped.max()))
    if thin:
        # A warped 1-px line spreads over two pixels and dips between them.
        level = min(level, THIN_LINE_LEVEL * float(warped.max()))
    return warped >= level


def _dilate_1px(mask: np.ndarray) -> np.ndarray:
    """`mask` grown by 1 px in all 8 directions, inside the frame (a full 3x3 dilation).

    One pass along each axis, using slices. mask: (S, S) bool. Returns a new (S, S) bool array.
    """
    rows = mask.copy()
    rows[1:] |= mask[:-1]
    rows[:-1] |= mask[1:]
    grown = rows.copy()
    grown[:, 1:] |= rows[:, :-1]
    grown[:, :-1] |= rows[:, 1:]
    return grown


def _flip_near_outline(binary: np.ndarray, ring: np.ndarray, fraction: float,
                       rng: np.random.Generator) -> np.ndarray:
    """Add ink to `fraction` of all pixels, chosen among background pixels
    within 1 px of the outline (stroke jitter). Ink is only added, never
    removed, so the outline stays connected (stages/stage_2.md Should 2).

    binary: (S, S) bool. ring: (S, S) bool frame margin, never touched.
    Returns a new (S, S) bool array.
    """
    near = _dilate_1px(binary) & ~binary & ~ring
    candidates = np.flatnonzero(near)
    n_flip = min(int(round(fraction * binary.size)), candidates.size)
    if n_flip == 0:
        return binary
    chosen = rng.choice(candidates, size=n_flip, replace=False)
    flat = binary.reshape(-1).copy()
    flat[chosen] = True
    return flat.reshape(binary.shape)


def _augment(img: np.ndarray, shear_allowed: bool, r: _Ranges,
             rng: np.random.Generator, rotate_cap: float | None = None) -> np.ndarray:
    """One augmented sample. img: (S, S) uint8. Returns (S, S) uint8 in {0, 255}."""
    if img.shape != (r.size, r.size) or img.dtype != np.uint8:
        raise ValueError(f"expected uint8 ({r.size}, {r.size}), got {img.dtype} {img.shape}")
    pts, thin = _ink_facts(img.tobytes(), r.size, r.ink_threshold)
    if pts.shape[0] == 0:
        return np.full((r.size, r.size), WHITE_LEVEL, dtype=np.uint8)
    ink = (img < r.ink_threshold).astype(np.float64) * INK_VALUE
    center = pts.mean(axis=0)

    # Fixed draw order, so a seed alone determines the output.
    rotate_deg = r.rotate_deg if rotate_cap is None else min(r.rotate_deg, rotate_cap)
    rot = np.deg2rad(rng.uniform(-rotate_deg, rotate_deg))
    scale = rng.uniform(*r.scale)
    shear_max = r.shear_deg if shear_allowed else 0.0
    stretch = r.nonuniform_scale if shear_allowed else 0.0
    shear = np.deg2rad(rng.uniform(-shear_max, shear_max))
    axis_factors = 1.0 + rng.uniform(-stretch, stretch, size=2)
    orient = rng.uniform(0.0, np.pi)
    shift = rng.uniform(-r.translate_px, r.translate_px, size=2)
    do_blur = rng.random() < r.blur_p
    sigma = rng.uniform(*r.blur_sigma)
    do_noise = rng.random() < r.noise_p

    linear = compose_affine(rot, shear, axis_factors, orient)
    # Re-frame like Stage 1's standardization (P-55): the transformed shape's
    # bounding box fills the frame minus the standardization margin, times
    # the configured scale jitter, and is centred (plus a small translation).
    # Without this, rotation + fit-to-frame shrinks training shapes below the
    # size of every (never augmented) validation/test image.
    q = (pts - center) @ linear.T
    q_max, q_min = q.max(axis=0), q.min(axis=0)
    extent = float((q_max - q_min).max()) + 1.0
    target = r.size / (1.0 + 2.0 * r.frame_margin)
    scale = scale * target / extent
    mid = 0.5 * (q_max + q_min) * scale
    frame_center = np.full(2, (r.size - 1) / 2.0)
    shift = frame_center - center - mid + shift
    ring = _outer_ring(r.size, FRAME_MARGIN_PX)
    binary = None
    # Cheap analytic fit first (ink pixel centres), then render; re-render
    # only if interpolation/blur still reaches the frame margin.
    steps = 0
    while (steps < MAX_FIT_STEPS
           and not within_frame(pts, scale * linear, center, shift, r.size, FRAME_MARGIN_PX)):
        scale *= FIT_SHRINK_FACTOR
        steps += 1
    for _ in range(max(1, MAX_FIT_STEPS - steps)):  # always render at least once
        matrix = scale * linear
        binary = _render(ink, matrix, center, shift, r.size, sigma if do_blur else None, thin)
        if not binary[ring].any():
            break
        scale *= FIT_SHRINK_FACTOR
    # Guard: if the shrink loop was exhausted, the frame margin is still cleared.
    binary = binary & ~ring
    if do_noise:
        binary = _flip_near_outline(binary, ring, r.noise_fraction, rng)
    return WHITE_LEVEL - binary.astype(np.uint8) * (WHITE_LEVEL - BLACK_LEVEL)


def build_transform(config: dict) -> Callable[[np.ndarray, int, np.random.Generator], np.ndarray]:
    """Build the class-safe transform from a merged config (load_config() output).

    Reads config["augment"], config["image_size"] and
    config["taxonomy"] (classes, no_shear_no_nonuniform_scale).
    Returns fn(img, label, rng) -> uint8 (S, S) in {0, 255}; never a label.
    Raises ValueError for an unknown label or a wrongly shaped image.
    """
    aug = config["augment"]
    tax = config["taxonomy"]
    ranges = _Ranges(
        size=int(config["image_size"]),
        ink_threshold=float(aug["ink_threshold"]),
        rotate_deg=float(aug["rotate_deg"]),
        scale=(float(aug["scale"][0]), float(aug["scale"][1])),
        nonuniform_scale=float(aug["nonuniform_scale"]),
        shear_deg=float(aug["shear_deg"]),
        translate_px=float(aug["translate_px"]),
        noise_p=float(aug["noise_p"]),
        noise_fraction=float(aug["noise_fraction"]),
        blur_p=float(aug["blur_p"]),
        blur_sigma=(float(aug["blur_sigma"][0]), float(aug["blur_sigma"][1])),
        frame_margin=float(aug["frame_margin"]),
    )
    label_of = {name: int(idx) for idx, name in tax["classes"].items()}
    known_labels = frozenset(label_of.values())
    no_shear = frozenset(label_of[name] for name in tax["no_shear_no_nonuniform_scale"])
    # Optional rotation cap per class, for classes that orientation helps separate.
    rotate_caps = {label_of[name]: float(deg) for name, deg in tax.get("rotate_limit_deg", {}).items()}

    def _transform(img: np.ndarray, label: int, rng: np.random.Generator) -> np.ndarray:
        label = int(label)
        if label not in known_labels:
            raise ValueError(f"unknown label {label}; taxonomy has {sorted(known_labels)}")
        return _augment(np.asarray(img), label not in no_shear, ranges, rng, rotate_caps.get(label))

    return _transform


@functools.lru_cache(maxsize=1)
def _default_transform() -> Callable[[np.ndarray, int, np.random.Generator], np.ndarray]:
    """The transform built once from the committed config."""
    return build_transform(load_default_config())


def transform(img: np.ndarray, label: int, rng: np.random.Generator) -> np.ndarray:
    """Class-safe augmentation using the committed config (see build_transform).

    img: uint8 (S, S), black outline on white. label: taxonomy index.
    rng: np.random.Generator. Returns uint8 (S, S) with values only in {0, 255}.
    """
    return _default_transform()(img, label, rng)
