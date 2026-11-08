"""Content identity of standardized images (moved from scripts/standardize.py).

md5   exact identity of the standardized uint8 array (Stage 1 manifests,
      Decision 1 gemstone list).
phash 64-bit perceptual hash for near-duplicate grouping (Decision 15).
Behaviour is byte-identical to the Phase 1 functions.
"""

import hashlib

import numpy as np
from PIL import Image
from scipy import fft

PHASH_SIZE = 32   # pixels; resize side before the DCT
PHASH_LOW = 8     # keep the 8x8 low-frequency block -> 64 bits


def md5(arr: np.ndarray) -> str:
    """Hex md5 of the array's raw bytes (not of a PNG file)."""
    return hashlib.md5(arr.tobytes()).hexdigest()


def phash(arr: np.ndarray) -> int:
    """64-bit perceptual hash (DCT method, as in the imagehash library):
    resize to 32x32, 2-D DCT, keep the 8x8 low-frequency block, threshold
    at its median. Returned as an int so Hamming distance is a popcount."""
    small = np.asarray(Image.fromarray(arr).resize((PHASH_SIZE, PHASH_SIZE),
                                                   Image.Resampling.LANCZOS),
                       dtype=np.float64)
    low = fft.dctn(small, norm="ortho")[:PHASH_LOW, :PHASH_LOW]
    bits = (low > np.median(low)).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)
