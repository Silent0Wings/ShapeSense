"""Loader benchmark for Stage 4 (stages/stage_4.md R10, Decision 6).

Times at least ``train.benchmark_batches`` batches of ``make_batch`` on
the intended machine, optionally including one model step per batch,
and turns the result into time estimates for one run and for the whole
sweep. Writing ``loader_benchmark.json`` is the caller's job
(``run.py``); this module only measures and computes.
"""

from __future__ import annotations

import time
from typing import Any, Callable

import numpy as np

from src.common.batch import Batch
from src.stage4_train.sampling import GenerateLike, TransformLike, make_batch

MS_PER_S = 1000.0  # milliseconds per second


def benchmark(store: Any, arm_cfg: dict, batch_size: int, synthetic_fraction: float,
              n_classes: int, n_batches: int, rng: np.random.Generator,
              transform: TransformLike | None = None,
              generate: GenerateLike | None = None,
              step_time_fn: Callable[[Batch], Any] | None = None,
              min_batches: int | None = None) -> dict:
    """Time ``n_batches`` batches from ``store`` for one arm.

    Args:
        store: anything with ``images`` uint8 (N, S, S), ``labels`` int64
            (N,) and ``class_idx`` (an ``ImageStore``).
        arm_cfg, batch_size, synthetic_fraction, n_classes: config values.
        n_batches: batches to time; must be >= ``min_batches`` when given
            (R10 asks for >= ``train.benchmark_batches``).
        rng: generator used for the sampled batches.
        transform, generate: injected Stage 2 / Stage 3 callables.
        step_time_fn: optional ``fn(batch)`` performing one model step;
            it is timed separately per batch.

    Returns a dict with ``n_batches``, ``batch_size``, ``n_real``,
    ``n_syn``, ``total_s``, ``batches_per_s``, ``images_per_s``,
    ``mean_batch_ms`` (loader only) and, when a step function is given,
    ``mean_step_ms``; ``per_step_s`` is the mean loader + step time.
    """
    if n_batches < 1:
        raise ValueError(f"n_batches must be >= 1, got {n_batches}")
    if min_batches is not None and n_batches < min_batches:
        raise ValueError(f"benchmark needs at least {min_batches} batches (R10), got {n_batches}")

    batch_s: list[float] = []
    step_s: list[float] = []
    for _ in range(n_batches):
        t0 = time.perf_counter()
        batch = make_batch(store.images, store.labels, store.class_idx, arm_cfg, batch_size,
                           synthetic_fraction, n_classes, rng,
                           transform=transform, generate=generate)
        batch_s.append(time.perf_counter() - t0)
        if step_time_fn is not None:
            t1 = time.perf_counter()
            step_time_fn(batch)
            step_s.append(time.perf_counter() - t1)

    n_real = int((~batch.is_synthetic).sum())
    n_syn = int(batch.is_synthetic.sum())
    total_batch_s = float(sum(batch_s))
    mean_batch_s = total_batch_s / n_batches
    mean_step_s = float(sum(step_s)) / n_batches if step_s else 0.0
    result = {
        "n_batches": int(n_batches),
        "batch_size": int(batch_size),
        "n_real": n_real,
        "n_syn": n_syn,
        "total_s": total_batch_s + float(sum(step_s)),
        "batches_per_s": (n_batches / total_batch_s) if total_batch_s > 0 else float("inf"),
        "images_per_s": (n_batches * batch_size / total_batch_s) if total_batch_s > 0 else float("inf"),
        "mean_batch_ms": mean_batch_s * MS_PER_S,
        "per_step_s": mean_batch_s + mean_step_s,
    }
    if step_time_fn is not None:
        result["mean_step_ms"] = mean_step_s * MS_PER_S
    return result


def est_run_s(steps_per_epoch: int, max_epochs: int, per_step_s: float) -> float:
    """Worst-case seconds for one run: every epoch of the frozen step budget."""
    if steps_per_epoch < 1 or max_epochs < 1:
        raise ValueError("steps_per_epoch and max_epochs must be >= 1")
    return float(steps_per_epoch) * float(max_epochs) * float(per_step_s)


def est_all_runs_s(n_runs: int, steps_per_epoch: int, max_epochs: int,
                   per_step_s: float) -> float:
    """Worst-case seconds for the whole sweep (Decision 6: up to 23 runs)."""
    if n_runs < 0:
        raise ValueError(f"n_runs must be >= 0, got {n_runs}")
    return n_runs * est_run_s(steps_per_epoch, max_epochs, per_step_s)
