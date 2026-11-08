"""QA sample sheet for the Stage 3 generator (matplotlib, Agg backend, file output)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

QA_CELL_INCHES = 0.9  # inches per grid cell
QA_LABEL_INCHES = 1.6  # inches reserved for row labels
QA_DPI = 100  # dots per inch of the PNG


def qa_sheet(gen_fn: Callable[[int, np.random.Generator], np.ndarray],
             class_names: Sequence[str], rng: np.random.Generator,
             out_path: str | Path, per_class: int = 10) -> Path:
    """Draw `per_class` samples per class in a grid and save it as a PNG.

    Row i shows label i (taxonomy index) and is labelled with class_names[i].

    Args:
        gen_fn: generate(label, rng) -> uint8 (H, W).
        class_names: names in label-index order.
        rng: source of randomness for the samples.
        out_path: PNG destination; parent folders are created.
        per_class: columns in the grid.

    Returns:
        The path written.
    """
    n_rows = len(class_names)
    fig = Figure(figsize=(per_class * QA_CELL_INCHES + QA_LABEL_INCHES,
                          n_rows * QA_CELL_INCHES), dpi=QA_DPI)
    FigureCanvasAgg(fig)
    axes = fig.subplots(n_rows, per_class, squeeze=False)
    for row, name in enumerate(class_names):
        for col in range(per_class):
            ax = axes[row, col]
            img = gen_fn(row, rng)
            ax.imshow(img, cmap="gray", vmin=0, vmax=255)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
        axes[row, 0].set_ylabel(name, rotation=0, ha="right", va="center", fontsize=9)
    fig.subplots_adjust(left=QA_LABEL_INCHES / fig.get_figwidth(), right=0.995,
                        top=0.995, bottom=0.005, wspace=0.04, hspace=0.04)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="png")
    return out
