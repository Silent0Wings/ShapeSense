"""Pure batch sampling for Stage 4 (NumPy only, no I/O, no global RNG).

Implements Decision 11 (class-balanced real sampling, synthetic share
spread evenly over classes), stages/stage_4.md R6/R7/R9 and Mission M2:

* every batch draws its real images class-balanced (R6);
* arm B replaces ``round(batch_size * synthetic_fraction)`` images of
  EVERY batch with generator output (R7) — the ratio is applied per
  batch, never per epoch (stage_4.md Pitfalls);
* when the arm augments, ``transform`` is applied to every image, real
  and synthetic alike (R7 "synthetic images are augmented too");
* all randomness comes from an injected ``np.random.Generator``, and
  :class:`BatchStream` derives one generator per (seed, epoch), so
  (arm, seed, epoch) reproduces the identical batch sequence (R9).

Stage 2 / Stage 3 code is never imported here. ``transform`` and
``generate`` arrive as injected callables matching
``src.common.interfaces.TransformFn`` / ``GeneratorFn``.

Why single-process: the train/val images live in memory as one uint8
array (see ``data.ImageStore``) and the transforms are NumPy functions,
so one process produces batches faster than the CPU model consumes them.
DataLoader worker processes would only add pickling overhead on Windows.
``worker_seed`` is kept so a multi-worker variant stays reproducible.

Image conventions: uint8 (S, S) in, float32 (N, 1, S, S) in [0, 1] out.
"""

from __future__ import annotations

from typing import Callable, Iterator

import numpy as np

from src.common.batch import Batch
from src.common.features import PIXEL_SCALE

UINT8_MAX = PIXEL_SCALE  # grey levels; divisor for the uint8 -> [0, 1] conversion

TransformLike = Callable[[np.ndarray, int, np.random.Generator], np.ndarray]
GenerateLike = Callable[[int, np.random.Generator], np.ndarray]


def balanced_labels(n: int, n_classes: int, rng: np.random.Generator) -> np.ndarray:
    """Return ``n`` labels spread as evenly as possible over ``n_classes``.

    Each class receives ``n // n_classes`` labels; the ``n % n_classes``
    remainder goes to classes drawn by ``rng`` without replacement. The
    result is shuffled with ``rng``.

    Returns: int64 array of shape (n,), values in [0, n_classes).
    """
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    if n_classes < 1:
        raise ValueError(f"n_classes must be >= 1, got {n_classes}")
    base, rem = divmod(n, n_classes)
    counts = np.full(n_classes, base, dtype=np.int64)
    if rem:
        extra = rng.choice(n_classes, size=rem, replace=False)
        counts[extra] += 1
    labels = np.repeat(np.arange(n_classes, dtype=np.int64), counts)
    rng.shuffle(labels)
    return labels


def _labels_for_batch(n: int, n_classes: int, excluded: tuple[int, ...],
                      rng: np.random.Generator) -> np.ndarray:
    """``balanced_labels`` over every class except ``excluded``.

    With nothing excluded this is exactly ``balanced_labels`` (same draws).
    Used only by leave-one-source-out runs (P-61).
    """
    if not excluded:
        return balanced_labels(n, n_classes, rng)
    active = np.array([c for c in range(n_classes) if c not in excluded], dtype=np.int64)
    return active[balanced_labels(n, active.size, rng)]


def batch_composition(arm_cfg: dict, batch_size: int,
                      synthetic_fraction: float) -> tuple[int, int]:
    """Return ``(n_real, n_syn)`` for one batch of the given arm.

    ``n_syn = round(batch_size * synthetic_fraction)`` when
    ``arm_cfg["synthetic"]`` is true, else 0 (Python ``round``: 256 * 0.3
    = 76.8 -> 77). Tuned shares come from the arm's own ``synthetic_fraction``. The split is a per-batch quantity by construction.
    """
    if batch_size < 1:
        raise ValueError(f"batch_size must be >= 1, got {batch_size}")
    share = float(arm_cfg.get("synthetic_fraction", synthetic_fraction))
    if not 0.0 <= share <= 1.0:
        raise ValueError(f"synthetic_fraction must be in [0, 1], got {share}")
    n_syn = int(round(batch_size * share)) if arm_cfg["synthetic"] else 0
    if arm_cfg.get("equal_real"):       # synthetic images on top of a full real batch
        return batch_size, n_syn
    return batch_size - n_syn, n_syn


def clean_count(arm_cfg: dict, batch_size: int) -> int:
    """Real images in a batch that stay unaugmented (arm A2, iteration 2)."""
    return int(round(batch_size * float(arm_cfg.get("clean_fraction", 0.0))))


def class_index(labels: np.ndarray, n_classes: int) -> list[np.ndarray]:
    """Return, per class, the int64 positions in ``labels`` holding that class.

    ``labels``: int array (N,). Result: list of length ``n_classes``; entry
    ``c`` is a (sorted) int64 array of indices with ``labels[i] == c``
    (possibly empty).
    """
    labels = np.asarray(labels)
    if labels.size and (labels.min() < 0 or labels.max() >= n_classes):
        raise ValueError(f"labels must lie in [0, {n_classes}), "
                         f"got range [{labels.min()}, {labels.max()}]")
    return [np.flatnonzero(labels == c).astype(np.int64) for c in range(n_classes)]


def sample_real_indices(class_idx: list[np.ndarray], real_labels: np.ndarray,
                        rng: np.random.Generator) -> np.ndarray:
    """Pick one stored image index per requested label (with replacement).

    For every entry of ``real_labels`` a uniformly random position from
    ``class_idx[label]`` is drawn, so the real part of a batch is exactly
    class-balanced when ``real_labels`` is (R6, Decision 11).

    Returns: int64 array of shape ``(len(real_labels),)``.
    Raises ValueError if a requested class has no stored images.
    """
    real_labels = np.asarray(real_labels, dtype=np.int64)
    out = np.empty(real_labels.shape[0], dtype=np.int64)
    for c, pool in enumerate(class_idx):
        pos = np.flatnonzero(real_labels == c)
        if pos.size == 0:
            continue
        if pool.size == 0:
            raise ValueError(f"class {c} requested but the store holds no image of it")
        out[pos] = pool[rng.integers(0, pool.size, size=pos.size)]
    return out


def to_float(images_u8: np.ndarray) -> np.ndarray:
    """Convert uint8 (N, S, S) grey images to float32 (N, 1, S, S) in [0, 1]."""
    images_u8 = np.asarray(images_u8)
    if images_u8.ndim != 3:
        raise ValueError(f"expected (N, S, S) images, got shape {images_u8.shape}")
    return (images_u8.astype(np.float32) / UINT8_MAX)[:, None, :, :]


def make_batch(images_u8: np.ndarray, labels: np.ndarray, class_idx: list[np.ndarray],
               arm_cfg: dict, batch_size: int, synthetic_fraction: float,
               n_classes: int, rng: np.random.Generator,
               transform: TransformLike | None = None,
               generate: GenerateLike | None = None,
               excluded_classes: tuple[int, ...] = ()) -> Batch:
    """Build one training batch for an arm (Mission M2).

    Args:
        images_u8: stored real images, uint8 (N, S, S).
        labels: their labels, int (N,).
        class_idx: ``class_index(labels, n_classes)``.
        arm_cfg: ``{"augment": bool, "synthetic": bool}`` from
            ``configs/pipeline.yaml#arms``.
        batch_size, synthetic_fraction, n_classes: config values.
        rng: the only source of randomness.
        transform: Stage 2 ``transform(img, label, rng)`` or None.
        generate: Stage 3 ``generate(label, rng)`` or None.
        excluded_classes: labels never drawn, real or synthetic (P-61:
            a held-out source that owns a whole class). Any other empty
            class still raises in ``sample_real_indices``.

    Steps: balanced real labels -> class-balanced real indices; balanced
    synthetic labels -> ``generate``; if ``arm_cfg["augment"]`` apply
    ``transform`` to every image (real and synthetic); shuffle jointly.

    Returns a ``Batch`` with images float32 (batch_size, 1, S, S) in
    [0, 1], labels int64, is_synthetic bool.
    Raises ValueError when the arm needs a callable that is None. Arm A0
    never calls ``transform`` or ``generate``.
    """
    if arm_cfg["augment"] and transform is None:
        raise ValueError("arm augments but no transform callable was given")
    if arm_cfg["synthetic"] and generate is None:
        raise ValueError("arm uses synthetic data but no generate callable was given")
    n_real, n_syn = batch_composition(arm_cfg, batch_size, synthetic_fraction)

    excluded = tuple(int(c) for c in excluded_classes)
    n_clean = clean_count(arm_cfg, batch_size)
    if n_clean > n_real:
        raise ValueError(f"clean images ({n_clean}) cannot exceed real images ({n_real})")
    real_labels = np.concatenate([_labels_for_batch(n_clean, n_classes, excluded, rng),
                                  _labels_for_batch(n_real - n_clean, n_classes, excluded, rng)])
    real_idx = sample_real_indices(class_idx, real_labels, rng)
    real_imgs = np.asarray(images_u8)[real_idx]

    syn_labels = _labels_for_batch(n_syn, n_classes, excluded, rng)
    if n_syn:
        syn_imgs = np.stack([np.asarray(generate(int(lbl), rng), dtype=np.uint8)
                             for lbl in syn_labels])
    else:
        syn_imgs = np.empty((0,) + real_imgs.shape[1:], dtype=np.uint8)

    imgs = np.concatenate([real_imgs, syn_imgs], axis=0)
    lbls = np.concatenate([real_labels, syn_labels]).astype(np.int64)
    is_syn = np.concatenate([np.zeros(n_real, bool), np.ones(n_syn, bool)])

    if arm_cfg["augment"]:
        # The first n_clean images are the clean real ones.
        imgs = np.stack([img if i < n_clean else np.asarray(transform(img, int(lbl), rng), dtype=np.uint8)
                         for i, (img, lbl) in enumerate(zip(imgs, lbls))])

    perm = rng.permutation(n_real + n_syn)
    return Batch(images=to_float(imgs[perm]), labels=lbls[perm], is_synthetic=is_syn[perm])


def worker_seed(run_seed: int, worker_id: int) -> int:
    """Deterministic per-worker seed derived from the run seed (R9, Pitfalls)."""
    return int(np.random.SeedSequence([int(run_seed), int(worker_id)]).generate_state(1)[0])


def epoch_rng(seed: int, epoch: int) -> np.random.Generator:
    """The generator that produces epoch ``epoch`` of run seed ``seed``."""
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(seed), int(epoch)])))


class BatchStream:
    """Exactly ``steps`` batches per epoch from a (seed, epoch)-derived RNG.

    ``iter(stream)`` (or ``stream.epoch(e)``) yields ``steps`` batches
    drawn with :func:`epoch_rng`, so the same (arm, seed, epoch) always
    gives the identical sequence (R9). Decision 13: an epoch is a fixed
    step budget, not a pass over the data. Runs in-process; see the
    module docstring for why no DataLoader workers are used.
    """

    def __init__(self, images_u8: np.ndarray, labels: np.ndarray, arm_cfg: dict,
                 batch_size: int, synthetic_fraction: float, n_classes: int,
                 seed: int, steps: int,
                 transform: TransformLike | None = None,
                 generate: GenerateLike | None = None,
                 class_idx: list[np.ndarray] | None = None,
                 epoch: int = 0,
                 excluded_classes: tuple[int, ...] = ()) -> None:
        if steps < 1:
            raise ValueError(f"steps must be >= 1, got {steps}")
        self.images_u8 = np.asarray(images_u8)
        self.labels = np.asarray(labels, dtype=np.int64)
        self.class_idx = class_idx if class_idx is not None else class_index(self.labels, n_classes)
        self.arm_cfg = dict(arm_cfg)
        self.batch_size = int(batch_size)
        self.synthetic_fraction = float(synthetic_fraction)
        self.n_classes = int(n_classes)
        self.seed = int(seed)
        self.steps = int(steps)
        self.transform = transform
        self.generate = generate
        self.current_epoch = int(epoch)
        self.excluded_classes = tuple(int(c) for c in excluded_classes)

    def epoch(self, epoch: int) -> Iterator[Batch]:
        """Yield the ``steps`` batches of ``epoch`` (composition fixed per batch)."""
        rng = epoch_rng(self.seed, epoch)
        for _ in range(self.steps):
            yield make_batch(self.images_u8, self.labels, self.class_idx, self.arm_cfg,
                             self.batch_size, self.synthetic_fraction, self.n_classes,
                             rng, transform=self.transform, generate=self.generate,
                             excluded_classes=self.excluded_classes)

    def __iter__(self) -> Iterator[Batch]:
        return self.epoch(self.current_epoch)

    def __len__(self) -> int:
        return self.steps
