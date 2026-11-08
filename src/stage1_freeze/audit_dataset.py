"""
Tier-1 visual audit of the unified dataset (Matplotlib only).
Writes report figures into figures/.

    python -m src.stage1_freeze.audit_dataset
"""
import csv
import glob
import json
import os
import random
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from src.common.config import REPO_ROOT  # noqa: E402
from src.common.neardup import near_dup_groups as _near_dup_groups  # noqa: E402
from src.common.quickdraw import quickdraw_loader  # noqa: E402
from src.stage1_freeze.build_unified_dataset import LABEL_MAP, NEAR_DUP_HAMMING  # noqa: E402
from src.stage1_freeze.standardize import Rejected, _flatten_alpha, _foreground_mask, standardize  # noqa: E402
from src.stage1_freeze.taxonomy import TAXONOMY  # noqa: E402

ROOT = str(REPO_ROOT)
DATA = os.path.join(ROOT, "data_set")
UNI = os.path.join(DATA, "unified")
FIG = os.path.join(ROOT, "figures")

# Validated categorical slots 1-4 (adjacent-pair safe, light mode).
SRC_ORDER = ["quickdraw", "kaggle_reevald", "mendeley_elkorchi", "github_handdrawn"]
SRC_NAME = {"quickdraw": "Quick, Draw!", "kaggle_reevald": "Kaggle reevald",
            "mendeley_elkorchi": "Mendeley El Korchi", "github_handdrawn": "Hand-drawn (GitHub)"}
SRC_COLOR = {"quickdraw": "#2a78d6", "kaggle_reevald": "#eb6834",
             "mendeley_elkorchi": "#1baf7a", "github_handdrawn": "#eda100"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def class_source_counts(rows):
    counts = defaultdict(Counter)
    for r in rows:
        counts[r["label_name"]][r["source_id"]] += 1
    fig, ax = plt.subplots(figsize=(8, 3.4))
    bottom = np.zeros(len(TAXONOMY))
    for s in SRC_ORDER:
        vals = np.array([counts[c][s] for c in TAXONOMY])
        ax.bar(TAXONOMY, vals, bottom=bottom, color=SRC_COLOR[s], label=SRC_NAME[s],
               width=0.7, edgecolor="white", linewidth=1.5)
        bottom += vals
    for i, t in enumerate(bottom):
        ax.text(i, t + 40, f"{int(t):,}", ha="center", fontsize=8, color=MUTED)
    ax.set_ylabel("images", color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "unified_class_source_counts.png"), dpi=180)
    plt.close(fig)


def raw_samples(n_per_source):
    rng = random.Random(7)
    picks = {}
    qd = []
    for p in sorted(glob.glob(os.path.join(DATA, "quickdraw", "subset", "*.ndjson"))):
        with open(p, encoding="utf-8") as f:
            qd += [json.loads(line) for line in f]
    picks["quickdraw"] = [quickdraw_loader(r) for r in rng.sample(qd, n_per_source)]
    globs = {
        "kaggle_reevald": "kaggle_reevald/dataset/*/*/*.jpg",
        "mendeley_elkorchi": "2D geometric shapes dataset/output/*.png",
        "github_handdrawn": "github_handdrawn/data/*/images/*/*.png",
    }
    for s, g in globs.items():
        files = [f for f in glob.glob(os.path.join(DATA, g))
                 if LABEL_MAP[s].get(os.path.basename(os.path.dirname(f)) if s != "mendeley_elkorchi"
                                     else os.path.basename(f).split("_")[0])]
        picks[s] = [(lambda f=f: Image.open(f)) for f in rng.sample(files, n_per_source)]
    return picks


def show_raw(ax, im):
    if im.mode == "RGBA":
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg
    ax.imshow(im.convert("RGB"))
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color(GRID)


def before_after(picks):
    n = 4
    fig, axes = plt.subplots(len(SRC_ORDER), 2 * n, figsize=(10, 5.4))
    for r, s in enumerate(SRC_ORDER):
        c = 0
        for load in picks[s]:
            if c >= n:
                break
            im = load()
            try:
                out, _ = standardize(im)
            except Rejected:
                continue
            show_raw(axes[r, 2 * c], im)
            axes[r, 2 * c + 1].imshow(out, cmap="gray", vmin=0, vmax=255)
            axes[r, 2 * c + 1].set_xticks([]); axes[r, 2 * c + 1].set_yticks([])
            for sp in axes[r, 2 * c + 1].spines.values():
                sp.set_color(GRID)
            if r == 0:
                axes[r, 2 * c].set_title("raw", fontsize=8, color=MUTED)
                axes[r, 2 * c + 1].set_title("64x64", fontsize=8, color=MUTED)
            c += 1
        axes[r, 0].set_ylabel(SRC_NAME[s], fontsize=8, color=INK, rotation=0, ha="right", va="center")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "standardization_before_after.png"), dpi=180)
    plt.close(fig)


def outlier_examples():
    with open(os.path.join(UNI, "rejects.csv"), encoding="utf-8") as f:
        rej = list(csv.DictReader(f))
    by_reason = defaultdict(list)
    for r in rej:
        if os.path.isfile(r["ref"]):
            by_reason[r["reason"]].append(r["ref"])
    reasons = [k for k in ["no_contrast", "blank_or_near_blank", "shape_too_small", "degenerate_after_resize"] if by_reason[k]]

    # Near-duplicate group: the largest pHash group among El Korchi pentagons.
    with open(os.path.join(UNI, "metadata.csv"), encoding="utf-8") as f:
        pent = [r for r in csv.DictReader(f)
                if r["source_id"] == "mendeley_elkorchi" and r["label_name"] == "pentagon"]
    gid = _near_dup_groups([int(r["phash"], 16) for r in pent], NEAR_DUP_HAMMING)
    big = Counter(gid).most_common(1)[0][0]
    group = [r for r, g in zip(pent, gid) if g == big]

    k = 4
    n_rows = len(reasons) + 1
    fig, axes = plt.subplots(n_rows, k, figsize=(6, 1.7 * n_rows), squeeze=False)
    rng = random.Random(1)
    for i, reason in enumerate(reasons):
        files = rng.sample(by_reason[reason], min(k, len(by_reason[reason])))
        for j in range(k):
            ax = axes[i, j]
            if j < len(files):
                show_raw(ax, Image.open(files[j]))
            else:
                ax.axis("off")
        axes[i, 0].set_ylabel(reason.replace("_", " "), fontsize=8, color=INK)
    for j, r in enumerate(group[:k]):
        ax = axes[-1, j]
        ax.imshow(Image.open(os.path.join(UNI, r["path"])), cmap="gray", vmin=0, vmax=255)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(GRID)
    axes[-1, 0].set_ylabel(f"near-dup group\n({len(group)} images)", fontsize=8, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "outlier_examples.png"), dpi=180)
    plt.close(fig)


def fill_to_outline():
    """Raw two-colour fill -> detected shape mask -> standard outline, for
    the sources that ship filled shapes on a coloured background. Picks the
    hard cases on purpose: lowest contrast, smallest shape, a star (hollow
    centre), plus one Dinesh image (same format, excluded for licensing)."""
    rng = random.Random(11)
    elk = rng.sample(glob.glob(os.path.join(DATA, "2D geometric shapes dataset", "output", "*.png")), 400)
    scored = []
    for f in elk:
        rgb = np.asarray(_flatten_alpha(Image.open(f)), dtype=np.float32)
        try:
            mask, bg = _foreground_mask(rgb)
        except Rejected:
            continue
        dist = np.sqrt(((rgb - bg) ** 2).sum(axis=2))
        scored.append((f, dist[mask].mean(), mask.sum()))
    picks = [min(scored, key=lambda s: s[1])[0],                    # lowest contrast
             min(scored, key=lambda s: s[2])[0],                    # smallest shape
             next(s[0] for s in scored if "Star_" in s[0]),         # hollow-centred star
             rng.choice(glob.glob(os.path.join(DATA, "kaggle_dinesh", "*", "*.png")))]
    titles = ["low contrast", "tiny shape", "hollow star", "Dinesh (same format)"]
    fig, axes = plt.subplots(3, 4, figsize=(7, 5.4))
    for j, (f, t) in enumerate(zip(picks, titles)):
        im = Image.open(f)
        rgb = np.asarray(_flatten_alpha(im), dtype=np.float32)
        mask, _ = _foreground_mask(rgb)
        out, _ = standardize(im)
        show_raw(axes[0, j], im)
        axes[1, j].imshow(~mask, cmap="gray")
        axes[2, j].imshow(out, cmap="gray", vmin=0, vmax=255)
        axes[0, j].set_title(t, fontsize=8, color=MUTED)
        for i in (1, 2):
            axes[i, j].set_xticks([]); axes[i, j].set_yticks([])
            for sp in axes[i, j].spines.values():
                sp.set_color(GRID)
    for i, lab in enumerate(["1. raw", "2. detected shape", "3. standard outline"]):
        axes[i, 0].set_ylabel(lab, fontsize=8, color=INK)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fill_to_outline.png"), dpi=180)
    plt.close(fig)


def main():
    with open(os.path.join(UNI, "metadata.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    class_source_counts(rows)
    before_after(raw_samples(12))
    outlier_examples()
    fill_to_outline()
    print("figures written")


if __name__ == "__main__":
    main()
