"""Confusion-matrix heatmaps and error galleries (stages/stage_5.md R3, R8b).

Stage 6 may not read test images, so the galleries of misclassified test
images for the key confusion pairs are rendered here. Images follow the
project convention: black outline on white (``cmap="gray"``, vmin 0,
vmax 255), captioned ``true→pred``. Matplotlib runs on the Agg backend.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.stage5_eval.metrics import confusion  # noqa: E402

HEATMAP_CMAP = "Blues"  # one hue, light -> dark: magnitude only
CELL_INCHES = 0.62  # heatmap cell size
GALLERY_COLS = 8  # thumbnails per gallery row
THUMB_INCHES = 1.1  # thumbnail size
MAX_PER_DIRECTION = 16  # misclassified examples shown per direction
TEXT_FLIP_LEVEL = 0.55  # row-normalized value above which cell text turns white
DPI = 150
IMG_VMIN, IMG_VMAX = 0, 255  # uint8 display range (black ink on white)


def confusion_figure(conf, class_names: Sequence[str], title: str, path: str | Path) -> Path:
    """Row-normalized heatmap annotated with raw counts; returns the PNG path."""
    conf = np.asarray(conf, dtype=np.int64)
    k = len(class_names)
    if conf.shape != (k, k):
        raise ValueError(f"conf must be ({k}, {k}), got {conf.shape}")
    row_sums = conf.sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        norm = np.where(row_sums > 0, conf / np.where(row_sums > 0, row_sums, 1), 0.0)

    size = max(4.0, CELL_INCHES * k + 1.8)
    fig, ax = plt.subplots(figsize=(size, size), dpi=DPI)
    im = ax.imshow(norm, cmap=HEATMAP_CMAP, vmin=0.0, vmax=1.0)
    ax.set_xticks(range(k))
    ax.set_yticks(range(k))
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.set_yticklabels(class_names)
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title(title)
    for t in range(k):
        for p in range(k):
            color = "white" if norm[t, p] > TEXT_FLIP_LEVEL else "black"
            ax.text(p, t, str(int(conf[t, p])), ha="center", va="center",
                    fontsize=7, color=color)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("share of true class")
    fig.tight_layout()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out


def error_gallery(
    images_u8,
    y,
    pred,
    class_a: int,
    class_b: int,
    class_names: Sequence[str],
    path: str | Path,
    max_per_direction: int = MAX_PER_DIRECTION,
) -> Path:
    """Misclassified test images a→b and b→a, black on white, captioned true→pred.

    Args:
        images_u8: uint8 (N, S, S) test images in the same order as ``y``.
        y, pred: shape (N,) true and predicted class indices.
        class_a, class_b: the pair's class indices.
        class_names: label-index-ordered names.
        path: output PNG.
        max_per_direction: cap on thumbnails per direction.
    """
    images_u8 = np.asarray(images_u8)
    y = np.asarray(y)
    pred = np.asarray(pred)
    a_to_b = np.flatnonzero((y == class_a) & (pred == class_b))[:max_per_direction]
    b_to_a = np.flatnonzero((y == class_b) & (pred == class_a))[:max_per_direction]
    name_a, name_b = class_names[class_a], class_names[class_b]

    sections = [(f"{name_a}→{name_b}", a_to_b), (f"{name_b}→{name_a}", b_to_a)]
    rows_per_section = [max(1, int(np.ceil(len(idx) / GALLERY_COLS))) for _, idx in sections]
    n_rows = sum(rows_per_section)
    fig, axes = plt.subplots(n_rows, GALLERY_COLS,
                             figsize=(THUMB_INCHES * GALLERY_COLS, THUMB_INCHES * n_rows + 0.6),
                             dpi=DPI, squeeze=False)
    for ax in axes.ravel():
        ax.axis("off")
    r0 = 0
    for (caption, idx), n_r in zip(sections, rows_per_section):
        if len(idx) == 0:
            axes[r0, 0].text(0.0, 0.5, f"{caption}: no errors", fontsize=8, va="center")
        for j, i in enumerate(idx):
            ax = axes[r0 + j // GALLERY_COLS, j % GALLERY_COLS]
            ax.imshow(images_u8[i], cmap="gray", vmin=IMG_VMIN, vmax=IMG_VMAX)
            ax.set_title(f"{class_names[int(y[i])]}→{class_names[int(pred[i])]}", fontsize=7)
        r0 += n_r
    fig.suptitle(f"B ensemble errors: {name_a} / {name_b} "
                 f"({len(a_to_b)} {name_a}→{name_b}, {len(b_to_a)} {name_b}→{name_a})",
                 fontsize=9)
    fig.tight_layout()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out


def confusion_from_predictions(y, pred, n_classes: int):
    """Convenience wrapper so run.py needs one import for the figure step."""
    return confusion(y, pred, n_classes)
