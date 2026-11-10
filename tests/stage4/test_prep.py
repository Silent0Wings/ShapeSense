"""Batches prepared on several cores match the single-process stream exactly."""

import numpy as np

from src.common.config import load_config
from src.stage2_augment import build_transform
from src.stage3_synth import build_generator
from src.stage4_train.prep import BatchPool, prepared
from src.stage4_train.sampling import BatchStream, step_rng

N_CLASSES = 10
BATCH = 16


def _images() -> tuple[np.ndarray, np.ndarray]:
    images = np.full((40, 64, 64), 255, dtype=np.uint8)
    for i, image in enumerate(images):
        low, high = 14 + i % 5, 48 - i % 7
        image[low:high, low] = image[low:high, high] = image[low, low:high] = image[high, low:high + 1] = 0
    return images, np.arange(40, dtype=np.int64) % N_CLASSES


def _stream(config: dict, arm: str, steps: int = 3) -> BatchStream:
    images, labels = _images()
    cfg = config["arms"][arm]
    return BatchStream(images, labels, cfg, BATCH, 0.25, N_CLASSES, seed=7, steps=steps,
                       transform=build_transform(config) if cfg["augment"] else None,
                       generate=build_generator(config) if cfg["synthetic"] else None)


def test_each_step_has_its_own_repeatable_generator():
    first = step_rng(1, 2, 3).integers(0, 1 << 30, size=4)
    assert (first == step_rng(1, 2, 3).integers(0, 1 << 30, size=4)).all()
    assert (first != step_rng(1, 2, 4).integers(0, 1 << 30, size=4)).any()


def test_a_step_does_not_depend_on_the_steps_before_it():
    config = load_config()
    stream = _stream(config, "B")
    alone = stream.batch(0, 2)
    assert (alone.images == list(stream.epoch(0))[2].images).all()


def test_batches_match_the_single_process_stream():
    config = load_config()
    stream = _stream(config, "B")
    pool = BatchPool(stream, config, 2)
    try:
        for fast, slow in zip(pool.epoch(1), stream.epoch(1), strict=True):
            assert (fast.images == slow.images).all()
            assert (fast.labels == slow.labels).all()
            assert (fast.is_synthetic == slow.is_synthetic).all()
    finally:
        pool.close()


def test_real_images_alone_stay_in_process():
    config = load_config()
    stream = _stream(config, "A0")
    assert prepared(stream, config, 4) is stream


def test_one_worker_stays_in_process():
    config = load_config()
    stream = _stream(config, "B")
    assert prepared(stream, config, 1) is stream
