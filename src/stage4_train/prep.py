"""Prepare training batches on several CPU cores.

Augmentation and the synthetic generator are about 80% of a training step and
run in Python, so threads cannot share the work. Each step draws from its own
generator (``sampling.step_rng``), so the batches are identical for any number
of workers. One pool of workers serves every run in a process, and each run
hands them its stream through a temporary file. Children rebuild ``transform``
and ``generate`` from the config, because both are closures and cannot be
pickled. Batches come back as uint8, which is a quarter of the size of float32.
"""

from __future__ import annotations

import copy
import itertools
import multiprocessing
import os
import pickle
import sys
import tempfile
from contextlib import contextmanager, suppress
from typing import Iterator

from threadpoolctl import threadpool_limits

from src.common.batch import Batch
from src.stage2_augment import build_transform
from src.stage3_synth import build_generator
from src.stage4_train.sampling import BatchStream

BATCH_TIMEOUT_S = 600   # a dead worker's batch never arrives, so a stall must become an error

_CHILD: dict = {}
_SHARED: dict = {}
_STREAM_NUMBERS = itertools.count()   # in every temp name, so workers can never mistake a reused path for its old stream


def _init_child() -> None:
    threadpool_limits(1)   # one math thread each, or the children fight over the cores


def _load_stream(path: str) -> BatchStream:
    if _CHILD.get("path") != path:
        with open(path, "rb") as f:
            stream, config = pickle.load(f)
        stream.transform = build_transform(config) if stream.arm_cfg["augment"] else None
        stream.generate = build_generator(config) if stream.arm_cfg["synthetic"] else None
        _CHILD.update(path=path, stream=stream)
    return _CHILD["stream"]


def _make_batch(job: tuple[str, int, int]) -> Batch:
    path, epoch, step = job
    return _load_stream(path).raw_batch(epoch, step)


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


def _shared_pool(workers: int):
    """The process-wide pool, so workers and their caches outlive each run.

    ``multiprocessing.Pool`` starts every worker at once. ``ProcessPoolExecutor``
    starts them as jobs arrive, and on Windows that broke with an invalid handle.
    """
    if _SHARED.get("workers") != workers:
        old = _SHARED.pop("pool", None)
        _SHARED.clear()   # no half-updated entry if starting the new pool fails
        if old is not None:
            old.terminate()
            old.join()
        with _light_children():
            pool = multiprocessing.get_context("spawn").Pool(workers, _init_child)
        _SHARED.update(workers=workers, pool=pool)
    return _SHARED["pool"]


class BatchPool:
    """A stream's batches, in order, as uint8 (N, 1, S, S), from ``workers`` processes."""

    def __init__(self, stream: BatchStream, config: dict, workers: int) -> None:
        bare = copy.copy(stream)
        bare.transform, bare.generate = None, None
        self.steps = stream.steps
        self.pool = _shared_pool(workers)
        handle, self.path = tempfile.mkstemp(prefix=f"shapesense_stream_{next(_STREAM_NUMBERS)}_", suffix=".pkl")
        try:
            with os.fdopen(handle, "wb") as f:
                pickle.dump((bare, config), f, protocol=pickle.HIGHEST_PROTOCOL)
        except BaseException:
            self.close()
            raise

    def epoch(self, epoch: int) -> Iterator[Batch]:
        results = self.pool.imap(_make_batch, ((self.path, epoch, step) for step in range(self.steps)))
        for _ in range(self.steps):
            yield results.next(timeout=BATCH_TIMEOUT_S)

    def close(self) -> None:
        """Delete the temp file. Safe to repeat, and never hides the error of a failed run."""
        # After a failed run a worker may still hold the file open, and Windows then refuses.
        with suppress(OSError):
            os.unlink(self.path)


def prepared(stream: BatchStream, config: dict, workers: int) -> BatchStream | BatchPool:
    """``stream`` itself when it has no costly work to share, else a pool for it."""
    costly = stream.arm_cfg["augment"] or stream.arm_cfg["synthetic"]
    return BatchPool(stream, config, workers) if workers > 1 and costly else stream
