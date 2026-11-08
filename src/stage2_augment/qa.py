"""QA sheet for Stage 2: original/augmented pairs, one row per class.

Rendered with matplotlib's Agg canvas (no pyplot, no global backend state),
black outline on white (grey colormap, vmin 0, vmax 255).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from src.stage2_augment.geometry import BLACK_LEVEL, WHITE_LEVEL

QA_COLS = 10              # 5 original/augmented pairs per class row (10 x 10 sheet)
ORIGINAL_FRAME = "#b0b0b0"  # light grey frame marks an original
AUGMENTED_FRAME = "#000000"  # black frame marks an augmentation
CELL_INCHES = 1.2         # figure size of one sample cell, inches
LABEL_INCHES = 1.4        # figure width reserved for class-name labels, inches
FIGURE_DPI = 100          # pixels per inch of the saved PNG
LABEL_FONT_SIZE = 9       # points


def qa_sheet(images_by_label: Mapping[int, Sequence[np.ndarray]],
             class_names: list[str],
             transform_fn: Callable[[np.ndarray, int, np.random.Generator], np.ndarray],
             rng: np.random.Generator,
             out_path: str | Path) -> Path:
    """Render and save the QA sheet; returns the written PNG path.

    images_by_label: label -> non-empty list of (S, S) uint8 source images.
    class_names: names in label-index order; one grid row per name.
    transform_fn: fn(img, label, rng) -> (S, S) uint8.
    rng: np.random.Generator used for every augmentation drawn for the sheet.
    Row i shows QA_COLS augmented samples of label i. Sources are cycled
    when a class has fewer than QA_COLS images.
    """
    n_rows = len(class_names)
    width = LABEL_INCHES + QA_COLS * CELL_INCHES
    height = n_rows * CELL_INCHES
    fig = Figure(figsize=(width, height), dpi=FIGURE_DPI)
    FigureCanvasAgg(fig)
    axes = fig.subplots(n_rows, QA_COLS, squeeze=False)
    for label, name in enumerate(class_names):
        pool = images_by_label.get(label)
        if not pool:
            raise ValueError(f"no source images for label {label} ({name})")
        for col in range(QA_COLS):
            # Pairs: even column = the original, odd column = its augmentation,
            # so a reviewer can tell a label-changing transform from a source
            # image that is already ambiguous.
            source = pool[(col // 2) % len(pool)]
            shown = source if col % 2 == 0 else transform_fn(source, label, rng)
            ax = axes[label, col]
            ax.imshow(shown, cmap="gray", vmin=BLACK_LEVEL, vmax=WHITE_LEVEL,
                      interpolation="nearest")
            ax.set_xticks([]); ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_color(ORIGINAL_FRAME if col % 2 == 0 else AUGMENTED_FRAME)
            if label == 0:
                ax.set_title("original" if col % 2 == 0 else "augmented",
                             fontsize=LABEL_FONT_SIZE)
        axes[label, 0].text(-0.08, 0.5, name, transform=axes[label, 0].transAxes,
                            ha="right", va="center", fontsize=LABEL_FONT_SIZE)
    fig.subplots_adjust(left=LABEL_INCHES / width, right=0.995, top=0.97,
                        bottom=0.005, wspace=0.03, hspace=0.03)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, format="png", dpi=FIGURE_DPI, facecolor="white")
    return out
