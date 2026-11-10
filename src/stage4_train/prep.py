"""Prepare training batches on several CPU cores.

Augmentation and the synthetic generator are about 80% of a training step and
run in Python, so threads cannot share the work. Each step draws from its own
generator (``sampling.step_rng``), so the batches are identical for any number
of workers. Children rebuild ``transform`` and ``generate`` from the config,
because both are closures and cannot be pickled.
"""

from __future__ import annotations

import copy
import multiprocessing
import sys
from contextlib import contextmanager
from typing import Iterator

from threadpoolctl import threadpool_limits

from src.common.batch import Batch
from src.stage2_augment import build_transform
from src.stage3_synth import build_generator
from src.stage4_train.sampling import BatchStream

BATCH_TIMEOUT_S = 600   # a dead worker's batch never arrives, so a stall must become an error

_CHILD: dict[str, BatchStream] = {}


def _init_child(stream: BatchStream, config: dict) -> None:
    threadpool_limits(1)   # one math thread each, or the children fight over the cores
    stream.transform = build_transform(config) if stream.arm_cfg["augment"] else None
    stream.generate = build_generator(config) if stream.arm_cfg["synthetic"] else None
    _CHILD["stream"] = stream


def _make_batch(job: tuple[int, int]) -> Batch:
    return _CHILD["stream"].batch(*job)


@contextmanager
def _light_children():
    """Keep spawned children from re-importing ``__main__``.

    Each child would otherwise load the whole training program, PyTorch
    included, one at a time, about 15 seconds each. They need none of it.
    """
    main = sys.modules["__main__"]
    saved = main.__dict__.get("__spec__"), main.__dict__.pop("__file__", None)
    main.__spec__ = None
    try:
        yield
    finally:
        main.__spec__ = saved[0]
        if saved[1] is not None:
            main.__file__ = saved[1]


class BatchPool:
    """A stream's batches, in order, prepared by ``workers`` processes.

    ``multiprocessing.Pool`` starts every worker at once. ``ProcessPoolExecutor``
    starts them as jobs arrive, and on Windows that broke with an invalid handle.
    """

    def __init__(self, stream: BatchStream, config: dict, workers: int) -> None:
        bare = copy.copy(stream)
        bare.transform, bare.generate = None, None
        self.steps = stream.steps
        with _light_children():
            self.pool = multiprocessing.get_context("spawn").Pool(workers, _init_child, (bare, config))

    def epoch(self, epoch: int) -> Iterator[Batch]:
        results = self.pool.imap(_make_batch, ((epoch, step) for step in range(self.steps)))
        for _ in range(self.steps):
            yield results.next(timeout=BATCH_TIMEOUT_S)

    def close(self) -> None:
        self.pool.terminate()
        self.pool.join()


def prepared(stream: BatchStream, config: dict, workers: int) -> BatchStream | BatchPool:
    """``stream`` itself when it has no costly work to share, else a pool for it."""
    costly = stream.arm_cfg["augment"] or stream.arm_cfg["synthetic"]
    return BatchPool(stream, config, workers) if workers > 1 and costly else stream
