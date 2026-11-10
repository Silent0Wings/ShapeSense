"""E26: class-balanced real sampling, 70/30 per-batch synthetic mix,
reproducible batches (stages/stage_4.md R6, R7, R9, Mission M2)."""

import numpy as np
import pytest

from src.common.batch import validate_batch
from src.stage4_train.sampling import (
    BatchStream,
    balanced_labels,
    batch_composition,
    class_index,
    make_batch,
    sample_real_indices,
    step_rng,
)

N_CLASSES = 10
SIZE = 16             # small test images; make_batch is size-agnostic
BATCH = 256           # mirrors train.batch_size (test fixture, not a config read)
FRACTION = 0.3        # mirrors synthetic_fraction (test fixture)
A0 = {"augment": False, "synthetic": False}
A1 = {"augment": True, "synthetic": False}
B = {"augment": True, "synthetic": True}


def _store(seed=0, per_class=12):
    """Real images whose top-left pixel encodes the label; white elsewhere."""
    rng = np.random.default_rng(seed)
    labels = np.repeat(np.arange(N_CLASSES, dtype=np.int64), per_class)
    rng.shuffle(labels)
    images = np.full((labels.size, SIZE, SIZE), 255, dtype=np.uint8)
    images[:, 0, 0] = labels.astype(np.uint8)
    images[:, 1, 1] = rng.integers(0, 200, size=labels.size).astype(np.uint8)
    return images, labels, class_index(labels, N_CLASSES)


def _transform(img, label, rng):
    return np.roll(img, 1, axis=1)


def _generate(label, rng):
    img = np.full((SIZE, SIZE), 255, dtype=np.uint8)
    img[SIZE // 2, :] = label           # label-dependent row
    img[2, 2] = rng.integers(0, 100)    # consumes rng
    return img


def _forbidden(*args, **kwargs):
    raise AssertionError("callable must not be invoked for this arm")


def _counting(fn):
    calls = {"n": 0}

    def wrapped(*args):
        calls["n"] += 1
        return fn(*args)
    return wrapped, calls


# --- composition -----------------------------------------------------------

def test_batch_composition_b_is_179_real_77_synthetic():
    assert batch_composition(B, BATCH, FRACTION) == (179, 77)
    assert batch_composition(A1, BATCH, FRACTION) == (BATCH, 0)
    assert batch_composition(A0, BATCH, FRACTION) == (BATCH, 0)


def test_b_batch_77_synthetic_179_real():
    images, labels, cidx = _store()
    batch = make_batch(images, labels, cidx, B, BATCH, FRACTION, N_CLASSES,
                       np.random.default_rng(1), transform=_transform, generate=_generate)
    assert batch.labels.shape == (BATCH,)
    assert int(batch.is_synthetic.sum()) == 77
    assert int((~batch.is_synthetic).sum()) == 179


def test_synthetic_labels_balanced():
    images, labels, cidx = _store()
    batch = make_batch(images, labels, cidx, B, BATCH, FRACTION, N_CLASSES,
                       np.random.default_rng(2), transform=_transform, generate=_generate)
    counts = np.bincount(batch.labels[batch.is_synthetic], minlength=N_CLASSES)
    assert counts.sum() == 77
    assert set(counts.tolist()) <= {7, 8}
    # the generator stamped its label into the middle row (transform rolls columns only)
    syn_imgs = (batch.images[batch.is_synthetic, 0] * 255).round().astype(np.uint8)
    assert np.array_equal(syn_imgs[:, SIZE // 2, 0], batch.labels[batch.is_synthetic])


def test_real_labels_balanced():
    images, labels, cidx = _store()
    batch = make_batch(images, labels, cidx, A0, BATCH, FRACTION, N_CLASSES,
                       np.random.default_rng(3))
    counts = np.bincount(batch.labels, minlength=N_CLASSES)
    assert counts.sum() == BATCH
    assert set(counts.tolist()) <= {25, 26}  # 256 over 10 classes
    # real labels match the stored image (top-left pixel encodes the label)
    pix = (batch.images[:, 0, 0, 0] * 255).round().astype(np.int64)
    assert np.array_equal(pix, batch.labels)


def test_balanced_labels_remainder_goes_to_distinct_classes():
    rng = np.random.default_rng(0)
    for n in (0, 1, 9, 10, 77, 256):
        lbls = balanced_labels(n, N_CLASSES, rng)
        assert lbls.dtype == np.int64 and lbls.shape == (n,)
        counts = np.bincount(lbls, minlength=N_CLASSES)
        assert counts.max() - counts.min() <= 1


def test_sample_real_indices_respects_class():
    images, labels, cidx = _store()
    req = balanced_labels(50, N_CLASSES, np.random.default_rng(4))
    idx = sample_real_indices(cidx, req, np.random.default_rng(5))
    assert np.array_equal(labels[idx], req)


def test_sample_real_indices_empty_class_raises():
    images, labels, cidx = _store()
    cidx[3] = np.empty(0, dtype=np.int64)
    with pytest.raises(ValueError, match="class 3"):
        sample_real_indices(cidx, np.array([3]), np.random.default_rng(0))


# --- arm behaviour ---------------------------------------------------------

def test_a0_no_aug_no_synth():
    images, labels, cidx = _store()
    batch = make_batch(images, labels, cidx, A0, BATCH, FRACTION, N_CLASSES,
                       np.random.default_rng(6), transform=_forbidden, generate=_forbidden)
    assert not batch.is_synthetic.any()
    # images are untouched copies of stored ones: white except two pixels
    white = (batch.images[:, 0] == 1.0).sum(axis=(1, 2))
    assert (white >= SIZE * SIZE - 2).all()


def test_a1_augments_real_only_no_synth():
    images, labels, cidx = _store()
    tf, calls = _counting(_transform)
    batch = make_batch(images, labels, cidx, A1, BATCH, FRACTION, N_CLASSES,
                       np.random.default_rng(7), transform=tf, generate=_forbidden)
    assert not batch.is_synthetic.any()
    assert calls["n"] == BATCH
    # np.roll by one column moved the label pixel from (0,0) to (0,1)
    pix = (batch.images[:, 0, 0, 1] * 255).round().astype(np.int64)
    assert np.array_equal(pix, batch.labels)


def test_b_augments_synthetic_too():
    images, labels, cidx = _store()
    tf, tcalls = _counting(_transform)
    gen, gcalls = _counting(_generate)
    make_batch(images, labels, cidx, B, BATCH, FRACTION, N_CLASSES,
               np.random.default_rng(8), transform=tf, generate=gen)
    assert gcalls["n"] == 77
    assert tcalls["n"] == BATCH  # every image, real and synthetic, is transformed


def test_missing_callable_raises():
    images, labels, cidx = _store()
    with pytest.raises(ValueError, match="transform"):
        make_batch(images, labels, cidx, A1, BATCH, FRACTION, N_CLASSES,
                   np.random.default_rng(0), transform=None, generate=_generate)
    with pytest.raises(ValueError, match="generate"):
        make_batch(images, labels, cidx, B, BATCH, FRACTION, N_CLASSES,
                   np.random.default_rng(0), transform=_transform, generate=None)


# --- format & determinism --------------------------------------------------

def test_batch_validates():
    images, labels, cidx = _store()
    for arm in (A0, A1, B):
        batch = make_batch(images, labels, cidx, arm, BATCH, FRACTION, N_CLASSES,
                           np.random.default_rng(9), transform=_transform, generate=_generate)
        validate_batch(batch, image_size=SIZE, channels=1)
        assert batch.images.dtype == np.float32
        assert batch.labels.dtype == np.int64
        assert batch.is_synthetic.dtype == bool


def test_same_seed_same_batch():
    images, labels, cidx = _store()
    kw = dict(transform=_transform, generate=_generate)
    b1 = make_batch(images, labels, cidx, B, BATCH, FRACTION, N_CLASSES, np.random.default_rng(11), **kw)
    b2 = make_batch(images, labels, cidx, B, BATCH, FRACTION, N_CLASSES, np.random.default_rng(11), **kw)
    b3 = make_batch(images, labels, cidx, B, BATCH, FRACTION, N_CLASSES, np.random.default_rng(12), **kw)
    assert np.array_equal(b1.images, b2.images)
    assert np.array_equal(b1.labels, b2.labels)
    assert np.array_equal(b1.is_synthetic, b2.is_synthetic)
    assert not np.array_equal(b1.images, b3.images)


def test_ratio_per_batch_not_per_epoch():
    images, labels, _ = _store()
    stream = BatchStream(images, labels, B, BATCH, FRACTION, N_CLASSES, seed=0, steps=20,
                         transform=_transform, generate=_generate)
    counts = [int(b.is_synthetic.sum()) for b in stream]
    assert len(counts) == 20
    assert counts == [77] * 20


def test_stream_reproducible_per_epoch():
    images, labels, _ = _store()

    def mk():
        return BatchStream(images, labels, B, BATCH, FRACTION, N_CLASSES, seed=5, steps=3,
                           transform=_transform, generate=_generate)

    e0a = list(mk().epoch(0))
    e0b = list(mk().epoch(0))
    e1 = list(mk().epoch(1))
    assert len(e0a) == len(mk()) == 3
    for a, b in zip(e0a, e0b):
        assert np.array_equal(a.images, b.images)
        assert np.array_equal(a.labels, b.labels)
    assert not all(np.array_equal(a.images, c.images) for a, c in zip(e0a, e1))


def test_step_rng_deterministic():
    r1 = step_rng(3, 2, 0).integers(0, 1 << 30, size=4)
    r2 = step_rng(3, 2, 0).integers(0, 1 << 30, size=4)
    r3 = step_rng(3, 3, 0).integers(0, 1 << 30, size=4)
    assert np.array_equal(r1, r2) and not np.array_equal(r1, r3)
