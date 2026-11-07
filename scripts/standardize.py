"""
Shared standardization step for every image source (real and synthetic).

Every image, whatever its origin, leaves this module in ONE format:

    64x64, single channel, uint8, black (0) outline strokes on a
    white (255) background, shape cropped to its bounding box and
    centered with aspect ratio preserved.

Normalization to float [0, 1] happens at load time (see shape_dataset.py),
not on disk, so the stored files stay lossless and inspectable.

Steps, in order (each one fixes a real incompatibility between sources):
  1. Alpha flattening   RGBA (hand-drawn set) composited onto white.
  2. Foreground mask    distance from the estimated background colour in
                        RGB space. Handles random background colours
                        (Dinesh, El Korchi), either polarity (dark-on-light
                        or light-on-dark), and shapes whose grey level
                        equals the background's even though the colours
                        differ (a plain RGB->grey conversion would erase
                        those).
  3. Outlier gate       blank or near-blank images, and shapes too small
                        to carry shape information, are rejected.
  4. Crop + letterbox   crop to the foreground bounding box plus a margin,
                        pad to a square (aspect ratio preserved, so a
                        rectangle never becomes a square), resize to 64.
  5. Outline redraw     every CLOSED shape (solid fill, thick ring, or
                        hollow-centred star) is redrawn as the same 2-px
                        outline of its silhouette; open or dashed sketches
                        keep their original strokes. Without this, "filled"
                        or "thick stroke" would identify the source instead
                        of the shape. Fills become outlines, not the other
                        way round, because an open sketch cannot be filled.
"""
import hashlib

import numpy as np
from PIL import Image
from scipy import fft, ndimage

TARGET = 64
BG_DISTANCE_T = 60.0      # max RGB distance threshold for ink
MIN_CONTRAST = 8.0        # strongest contrast below this: nothing visible
MIN_FG_FRACTION = 0.0015  # below this share of ink pixels: blank image
MIN_SHAPE_PX = 12         # bounding box smaller than this: unreadably tiny
MARGIN = 0.08             # margin around the bounding box, share of its size
FILLED_CORE = 0.30        # share of ink surviving erosion -> treat as filled
MIN_INK_64 = 20           # ink pixels left at 64x64 below this: degenerate


class Rejected(Exception):
    """Raised when an image fails the outlier gate. `reason` says why."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _flatten_alpha(im):
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        return bg.convert("RGB")
    return im.convert("RGB")


def _foreground_mask(rgb):
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, axis=0)
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=2))
    # Strongest local contrast: max after a 3x3 median filter, so a tiny
    # shape still counts (a percentile would land on background pixels)
    # but an isolated noisy pixel does not.
    contrast = ndimage.median_filter(dist, size=3).max()
    if contrast < MIN_CONTRAST:
        raise Rejected("no_contrast")
    # Threshold adapts to the image: half its strongest contrast, so a
    # dark-orange shape on an orange background is still found, but capped
    # so JPEG noise around strong edges is not.
    t = min(BG_DISTANCE_T, max(MIN_CONTRAST, 0.5 * contrast))
    return dist > t, bg


def _to_square(mask, bbox):
    r0, r1, c0, c1 = bbox
    crop = mask[r0:r1 + 1, c0:c1 + 1]
    side = max(crop.shape)
    m = max(2, int(round(MARGIN * side)))
    crop = np.pad(crop, m)
    h, w = crop.shape
    s = max(h, w)
    top, left = (s - h) // 2, (s - w) // 2
    return np.pad(crop, ((top, s - h - top), (left, s - w - left)))


def _resize_mask(square):
    im = Image.fromarray(square.astype(np.uint8) * 255)
    method = Image.Resampling.BOX if square.shape[0] > TARGET else Image.Resampling.BILINEAR
    return np.asarray(im.resize((TARGET, TARGET), method), dtype=np.float32) / 255.0


def standardize(im):
    """Return (uint8 64x64 array, info dict) or raise Rejected."""
    native = {"native_width": im.width, "native_height": im.height,
              "native_mode": im.mode}
    rgb = np.asarray(_flatten_alpha(im), dtype=np.float32)
    mask, bg = _foreground_mask(rgb)
    h, w = mask.shape

    if mask.mean() < MIN_FG_FRACTION:
        raise Rejected("blank_or_near_blank")
    rows, cols = np.where(mask)
    bbox = (rows.min(), rows.max(), cols.min(), cols.max())
    shape_px = max(bbox[1] - bbox[0], bbox[3] - bbox[2]) + 1
    if shape_px < MIN_SHAPE_PX:
        raise Rejected("shape_too_small")

    small = _resize_mask(_to_square(mask, bbox))

    # Closed vs open, decided at 64x64 where every shape has the same size.
    # Fill holes first: a closed outline (any stroke width) and a solid
    # silhouette (even a hollow-centred star) both become the same solid
    # region. Eroding 3 px then removes open/dashed strokes but keeps a
    # large core of any closed region.
    ink_any = small > 0.25  # low threshold keeps thin strokes after downscale
    region = ndimage.binary_fill_holes(ink_any)
    core = ndimage.binary_erosion(region, iterations=3)
    closed = region.sum() > 0 and core.sum() / region.sum() > FILLED_CORE

    if closed:
        # Redraw every closed shape as the same 2-px outline of its
        # silhouette, whatever its original fill or stroke width.
        ink = region & ~ndimage.binary_erosion(region)
        ink = ndimage.binary_dilation(ink)
    else:
        ink = ink_any

    if ink.sum() < MIN_INK_64:
        raise Rejected("degenerate_after_resize")

    out = np.where(ink, 0, 255).astype(np.uint8)
    info = dict(native,
                bg_luma=float(0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]),
                outline_redrawn=bool(closed),
                fg_fraction=float(mask.mean()),
                shape_px=int(shape_px))
    return out, info


def md5(arr):
    return hashlib.md5(arr.tobytes()).hexdigest()


def phash(arr):
    """64-bit perceptual hash (DCT method, as in the imagehash library):
    resize to 32x32, 2-D DCT, keep the 8x8 low-frequency block, threshold
    at its median. Returned as an int so Hamming distance is a popcount."""
    small = np.asarray(Image.fromarray(arr).resize((32, 32), Image.Resampling.LANCZOS),
                       dtype=np.float64)
    low = fft.dctn(small, norm="ortho")[:8, :8]
    bits = (low > np.median(low)).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)
