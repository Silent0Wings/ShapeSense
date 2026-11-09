"""Fixed, seeded perturbations. Each takes a uint8 (S, S) image and a generator."""

from __future__ import annotations

import io
import zlib
from typing import Callable

import numpy as np
from PIL import Image
from scipy import ndimage

Perturb = Callable[[np.ndarray, np.random.Generator], np.ndarray]

WHITE = 255
INK_CUT = 128
SUPERSAMPLE = 4
THIN_COVER = 0.25      # share of a pixel that must be ink, so 1-px strokes survive the resize
OCCLUDER = 128         # mid-grey, so a patch adds neither ink nor background

ANGLES = (0, 15, 30, 45, 90, 135, 180)
GAUSS_SIGMAS = (0.02, 0.05, 0.1, 0.2)
SALT_PEPPER = (0.01, 0.05, 0.1, 0.2)
BLUR_RADII = (1, 2, 3)
JPEG_QUALITIES = (90, 50, 20)
BRIGHTNESS = (-0.4, -0.2, 0.2, 0.4)
CONTRAST = (0.75, 0.5, 0.25)
PATCHES = (8, 16, 24)


def _to_u8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, WHITE).astype(np.uint8)


def rotate(image: np.ndarray, degrees: float) -> np.ndarray:
    """Rotate on a white background and keep the drawing's size, so no corner is cut off.

    Real images are all framed to the same size, and a turned shape would otherwise
    run past the 64-px frame or shrink, which would give a cue unrelated to the angle.
    """
    if degrees == 0:
        return image.copy()
    size = image.shape[0]
    ink = np.argwhere(image < INK_CUT)
    if ink.size == 0:
        return image.copy()
    side = int((ink.max(0) - ink.min(0)).max()) + 1
    big = Image.fromarray(image).resize((size * SUPERSAMPLE, size * SUPERSAMPLE), Image.Resampling.NEAREST)
    turned = np.asarray(big.rotate(degrees, Image.Resampling.BILINEAR, expand=True, fillcolor=WHITE))
    points = np.argwhere(turned < INK_CUT)
    top, left = points.min(0)
    bottom, right = points.max(0) + 1
    height, width = bottom - top, right - left
    scale = min(side, size - 2) / max(height, width)
    target = (max(int(round(width * scale)), 1), max(int(round(height * scale)), 1))
    crop = Image.fromarray(turned[top:bottom, left:right]).resize(target, Image.Resampling.BOX)
    canvas = np.full((size, size), WHITE, dtype=np.float32)
    shape = np.asarray(crop, dtype=np.float32)
    y, x = (size - shape.shape[0]) // 2, (size - shape.shape[1]) // 2
    canvas[y:y + shape.shape[0], x:x + shape.shape[1]] = shape
    return np.where(canvas <= WHITE * (1 - THIN_COVER), 0, WHITE).astype(np.uint8)


def gaussian(image: np.ndarray, sigma: float, rng: np.random.Generator) -> np.ndarray:
    return _to_u8(image + rng.normal(0.0, sigma * WHITE, image.shape))


def salt_pepper(image: np.ndarray, share: float, rng: np.random.Generator) -> np.ndarray:
    out = image.copy()
    hit = rng.random(image.shape) < share
    out[hit] = rng.choice([0, WHITE], size=int(hit.sum()))
    return out


def blur(image: np.ndarray, radius: int) -> np.ndarray:
    """Gaussian blur with sigma ``radius`` and a kernel of ``2 * radius + 1`` pixels."""
    return _to_u8(ndimage.gaussian_filter(image.astype(np.float32), sigma=radius, truncate=1.0, mode="nearest"))


def jpeg(image: np.ndarray, quality: int) -> np.ndarray:
    buffer = io.BytesIO()
    Image.fromarray(image).save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    return np.asarray(Image.open(buffer).convert("L"), dtype=np.uint8).copy()


def brightness(image: np.ndarray, delta: float) -> np.ndarray:
    return _to_u8(image.astype(np.float32) + delta * WHITE)


def contrast(image: np.ndarray, factor: float) -> np.ndarray:
    middle = WHITE / 2
    return _to_u8(middle + (image.astype(np.float32) - middle) * factor)


def occlude(image: np.ndarray, patch: int, rng: np.random.Generator) -> np.ndarray:
    out = image.copy()
    y, x = rng.integers(0, image.shape[0] - patch + 1, size=2)
    out[y:y + patch, x:x + patch] = OCCLUDER
    return out


def _sets() -> dict[str, tuple[str, str, Perturb]]:
    """name -> (family, level shown on charts, function), in plotting order."""
    out: dict[str, tuple[str, str, Perturb]] = {"clean": ("clean", "clean", lambda im, g: im.copy())}
    for a in ANGLES:
        out[f"rot{a}"] = ("rotated", f"{a}°", lambda im, g, a=a: rotate(im, a))
    for v in GAUSS_SIGMAS:
        out[f"gauss{v}"] = ("gaussian", f"σ {v}", lambda im, g, v=v: gaussian(im, v, g))
    for v in SALT_PEPPER:
        out[f"saltpepper{v}"] = ("salt_pepper", f"{v:.0%}", lambda im, g, v=v: salt_pepper(im, v, g))
    for v in BLUR_RADII:
        out[f"blur{v}"] = ("blur", f"radius {v}", lambda im, g, v=v: blur(im, v))
    for v in JPEG_QUALITIES:
        out[f"jpeg{v}"] = ("jpeg", f"quality {v}", lambda im, g, v=v: jpeg(im, v))
    for v in BRIGHTNESS:
        out[f"bright{v:+}"] = ("brightness", f"{v:+}", lambda im, g, v=v: brightness(im, v))
    for v in CONTRAST:
        out[f"contrast{v}"] = ("contrast", f"× {v}", lambda im, g, v=v: contrast(im, v))
    for v in PATCHES:
        out[f"occlude{v}"] = ("occlusion", f"{v} px", lambda im, g, v=v: occlude(im, v, g))
    return out


SETS = _sets()


def build_set(name: str, images: np.ndarray, seed: int) -> np.ndarray:
    """One perturbed copy of ``images``; the same name and seed always give the same bytes."""
    rng = np.random.default_rng([seed, zlib.crc32(name.encode("utf-8"))])
    function = SETS[name][2]
    return np.stack([function(image, rng) for image in images])
