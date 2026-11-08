"""E15: md5 / pHash helpers keep their Phase 1 behaviour."""

import numpy as np

from src.common.imaging import md5, phash


def _square():
    img = np.full((64, 64), 255, np.uint8)
    img[10:54, 10:12] = img[10:54, 52:54] = 0
    img[10:12, 10:54] = img[52:54, 10:54] = 0
    return img


def test_md5_stable_and_content_based():
    a = _square()
    assert md5(a) == md5(a.copy())
    b = a.copy()
    b[0, 0] = 0
    assert md5(a) != md5(b)


def test_phash_is_64_bit_deterministic_and_discriminative():
    a = _square()
    circle = np.full((64, 64), 255, np.uint8)
    yy, xx = np.mgrid[:64, :64]
    circle[np.abs(np.hypot(yy - 32, xx - 32) - 20) < 1.2] = 0
    ha = phash(a)
    assert 0 <= ha < 2 ** 64
    assert phash(a.copy()) == ha
    assert bin(ha ^ phash(circle)).count("1") > 2
