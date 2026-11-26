# 1_data_integration - Standardize the sources into one merged dataset

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-10-19
- Owner: 40256377
- Worksheet entries: I01, I06
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. The prompt is verbatim from the session log (recorded in `docs/prompts.csv` of the snapshot); the reply was not saved. The Response quotes the LLM's saved output files verbatim.
-  [I01](04_I01_schema-harmonization-and-label-mapping.md), [I01](../gemini_4_neon/03_I01_source-capping-and-label-harmonization.md), [I06](09_I06_cross-source-standardization-and-outline-redraw.md), [I06](../gemini_4_neon/08_I06_standardization-and-holdout-rebuild-recovery.md)

## Prompt P05 (verbatim, 2026-10-19)

> if there is a dplciate then 1 mst be detleted , do what is right  start working on the todoes ,a dn advancing the plans , for example alot of these data sets are not compatible at all , adreess dimensionality , color range , normalisation , and a standarzied merged data set that will fit all to 1 expected format + complet the open entries in the todo

_Source: Claude Code session 2026-10-19, user message 65. Confidence: medium. Commit is 2026-10-19 and the prompt is from the same day. Commit title is 'add functional dependency discovery script and update report with findings', so the link is inferred._

## Response (the reply was not saved; the work it produced, verbatim)

### `scripts/standardize.py`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````python
"""
Shared standardization step for every image source (real and synthetic).

Every image, whatever its origin, leaves this module in ONE format:

    64x64, single channel, uint8, black (0) outline strokes on a
    white (255) background, shape cropped to its bounding box and
    centered with aspect ratio preserved.

Normalization to float [0, 1] happens at load time (see shape_dataset.py),
not on disk, so the stored files stay lossless and inspectable.

Steps, in order (each one fixes a real incompatibility between sources):
  1. Alpha flattening   RGBA (hand-drawn set) composited onto white.
  2. Foreground mask    distance from the estimated background colour in
                        RGB space. Handles random background colours
                        (Dinesh, El Korchi), either polarity (dark-on-light
                        or light-on-dark), and shapes whose grey level
                        equals the background's even though the colours
                        differ (a plain RGB->grey conversion would erase
                        those).
  3. Outlier gate       blank or near-blank images, and shapes too small
                        to carry shape information, are rejected.
  4. Crop + letterbox   crop to the foreground bounding box plus a margin,
                        pad to a square (aspect ratio preserved, so a
                        rectangle never becomes a square), resize to 64.
  5. Outline redraw     every CLOSED shape (solid fill, thick ring, or
                        hollow-centred star) is redrawn as the same 2-px
                        outline of its silhouette; open or dashed sketches
                        keep their original strokes. Without this, "filled"
                        or "thick stroke" would identify the source instead
                        of the shape. Fills become outlines, not the other
                        way round, because an open sketch cannot be filled.
"""
import hashlib

import numpy as np
from PIL import Image
from scipy import fft, ndimage

TARGET = 64
BG_DISTANCE_T = 60.0      # max RGB distance threshold for ink
MIN_CONTRAST = 8.0        # strongest contrast below this: nothing visible
MIN_FG_FRACTION = 0.0015  # below this share of ink pixels: blank image
MIN_SHAPE_PX = 12         # bounding box smaller than this: unreadably tiny
MARGIN = 0.08             # margin around the bounding box, share of its size
FILLED_CORE = 0.30        # share of ink surviving erosion -> treat as filled
MIN_INK_64 = 20           # ink pixels left at 64x64 below this: degenerate


class Rejected(Exception):
    """Raised when an image fails the outlier gate. `reason` says why."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def _flatten_alpha(im):
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        return bg.convert("RGB")
    return im.convert("RGB")


def _foreground_mask(rgb):
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, axis=0)
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=2))
    # Strongest local contrast: max after a 3x3 median filter, so a tiny
    # shape still counts (a percentile would land on background pixels)
    # but an isolated noisy pixel does not.
    contrast = ndimage.median_filter(dist, size=3).max()
    if contrast < MIN_CONTRAST:
        raise Rejected("no_contrast")
    # Threshold adapts to the image: half its strongest contrast, so a
    # dark-orange shape on an orange background is still found, but capped
    # so JPEG noise around strong edges is not.
    t = min(BG_DISTANCE_T, max(MIN_CONTRAST, 0.5 * contrast))
    return dist > t, bg


def _to_square(mask, bbox):
    r0, r1, c0, c1 = bbox
    crop = mask[r0:r1 + 1, c0:c1 + 1]
    side = max(crop.shape)
    m = max(2, int(round(MARGIN * side)))
    crop = np.pad(crop, m)
    h, w = crop.shape
    s = max(h, w)
    top, left = (s - h) // 2, (s - w) // 2
    return np.pad(crop, ((top, s - h - top), (left, s - w - left)))


def _resize_mask(square):
    im = Image.fromarray(square.astype(np.uint8) * 255)
    method = Image.Resampling.BOX if square.shape[0] > TARGET else Image.Resampling.BILINEAR
    return np.asarray(im.resize((TARGET, TARGET), method), dtype=np.float32) / 255.0


def standardize(im):
    """Return (uint8 64x64 array, info dict) or raise Rejected."""
    native = {"native_width": im.width, "native_height": im.height,
              "native_mode": im.mode}
    rgb = np.asarray(_flatten_alpha(im), dtype=np.float32)
    mask, bg = _foreground_mask(rgb)
    h, w = mask.shape

    if mask.mean() < MIN_FG_FRACTION:
        raise Rejected("blank_or_near_blank")
    rows, cols = np.where(mask)
    bbox = (rows.min(), rows.max(), cols.min(), cols.max())
    shape_px = max(bbox[1] - bbox[0], bbox[3] - bbox[2]) + 1
    if shape_px < MIN_SHAPE_PX:
        raise Rejected("shape_too_small")

    small = _resize_mask(_to_square(mask, bbox))

    # Closed vs open, decided at 64x64 where every shape has the same size.
    # Fill holes first: a closed outline (any stroke width) and a solid
    # silhouette (even a hollow-centred star) both become the same solid
    # region. Eroding 3 px then removes open/dashed strokes but keeps a
    # large core of any closed region.
    ink_any = small > 0.25  # low threshold keeps thin strokes after downscale
    region = ndimage.binary_fill_holes(ink_any)
    core = ndimage.binary_erosion(region, iterations=3)
    closed = region.sum() > 0 and core.sum() / region.sum() > FILLED_CORE

    if closed:
        # Redraw every closed shape as the same 2-px outline of its
        # silhouette, whatever its original fill or stroke width.
        ink = region & ~ndimage.binary_erosion(region)
        ink = ndimage.binary_dilation(ink)
    else:
        ink = ink_any

    if ink.sum() < MIN_INK_64:
        raise Rejected("degenerate_after_resize")

    out = np.where(ink, 0, 255).astype(np.uint8)
    info = dict(native,
                bg_luma=float(0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]),
                outline_redrawn=bool(closed),
                fg_fraction=float(mask.mean()),
                shape_px=int(shape_px))
    return out, info


def md5(arr):
    return hashlib.md5(arr.tobytes()).hexdigest()


def phash(arr):
    """64-bit perceptual hash (DCT method, as in the imagehash library):
    resize to 32x32, 2-D DCT, keep the 8x8 low-frequency block, threshold
    at its median. Returned as an int so Hamming distance is a popcount."""
    small = np.asarray(Image.fromarray(arr).resize((32, 32), Image.Resampling.LANCZOS),
                       dtype=np.float64)
    low = fft.dctn(small, norm="ortho")[:8, :8]
    bits = (low > np.median(low)).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)
````

### `scripts/build_unified_dataset.py`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````python
"""
Build the unified, standardized shape dataset from the installed sources.

    python scripts/build_unified_dataset.py

Order of operations (dedup BEFORE split, nothing augmented here):
  1. Sample candidates per (source, label), map labels to the 10-class
     taxonomy, drop out-of-taxonomy classes.
  2. Standardize every image (scripts/standardize.py); rejected images are
     logged to rejects.csv with the reason (Section D outlier examples).
  3. Remove exact duplicates (identical standardized pixels), across all
     sources.
  4. Cap each (source, label) group so no single source dominates a class.
  5. Group near-duplicates (pHash Hamming distance <= 2) and split by group,
     70/15/15, so near-identical images never straddle train and test.
  6. Write PNGs, metadata.csv, and catalog.sqlite (the 5-table ERD).

Outputs go to data_set/unified/ (git-ignored, like all of data_set/).
"""
import csv
import glob
import json
import os
import random
import shutil
import sqlite3
import sys
from collections import Counter, defaultdict

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from standardize import Rejected, md5, phash, standardize  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data_set")
OUT = os.path.join(DATA, "unified")
SEED = 42
CANDIDATES_PER_GROUP = 1500
MAX_PER_GROUP = 1000
NEAR_DUP_HAMMING = 2
SPLIT = (0.70, 0.15, 0.15)

from taxonomy import TAXONOMY  # noqa: E402  (fixed label set, label_id = index)

SOURCES = {
    "quickdraw": dict(name="Quick, Draw! (subset)", domain="sketch", license="CC BY 4.0"),
    "kaggle_reevald": dict(name="Geometric Shapes Mathematics (reevald)", domain="render", license="CC0"),
    "mendeley_elkorchi": dict(name="2D geometric shapes dataset (El Korchi)", domain="render", license="CC BY 4.0"),
    "github_handdrawn": dict(name="Hand-Drawn Shapes Dataset (frobertpixto)", domain="sketch", license="CC BY 4.0"),
}
# kaggle_dinesh is installed but deliberately excluded: its Kaggle license
# field reads "Unknown", and it only adds circle/square/triangle, which
# three other sources already cover.

LABEL_MAP = {
    "quickdraw": {c: c for c in ["circle", "diamond", "hexagon", "octagon", "square", "star", "triangle"]},
    "kaggle_reevald": {"circle": "circle", "square": "square", "triangle": "triangle",
                       "rectangle": "rectangle", "rhombus": "diamond",
                       "kite": None, "trapezoid": None, "parallelogram": None},
    "mendeley_elkorchi": {"Circle": "circle", "Triangle": "triangle", "Square": "square",
                          "Pentagon": "pentagon", "Hexagon": "hexagon", "Octagon": "octagon",
                          "Star": "star", "Heptagon": None, "Nonagon": None},
    "github_handdrawn": {"ellipse": "ellipse", "rectangle": "rectangle",
                         "triangle": "triangle", "other": None},
}


def _qd_loader(rec):
    def load():
        im = Image.new("RGB", (256, 256), "white")
        d = ImageDraw.Draw(im)
        for xs, ys in rec["drawing"]:
            d.line(list(zip(xs, ys)), fill="black", width=3)
        return im
    return load


def candidates():
    """Yield (source_id, original_label, ref, loader) for every raw item."""
    for path in sorted(glob.glob(os.path.join(DATA, "quickdraw", "subset", "*.ndjson"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                yield "quickdraw", rec["word"], f"quickdraw/{rec['key_id']}", _qd_loader(rec)
    for path in sorted(glob.glob(os.path.join(DATA, "kaggle_reevald", "dataset", "*", "*", "*.jpg"))):
        yield "kaggle_reevald", os.path.basename(os.path.dirname(path)), path, path
    for path in sorted(glob.glob(os.path.join(DATA, "2D geometric shapes dataset", "output", "*.png"))):
        yield "mendeley_elkorchi", os.path.basename(path).split("_")[0], path, path
    for path in sorted(glob.glob(os.path.join(DATA, "github_handdrawn", "data", "*", "images", "*", "*.png"))):
        yield "github_handdrawn", os.path.basename(os.path.dirname(path)), path, path


def near_dup_groups(hashes):
    """Union-find over pairs with Hamming distance <= NEAR_DUP_HAMMING."""
    n = len(hashes)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    h = np.array(hashes, dtype=np.uint64)
    for i in range(n):
        x = np.bitwise_xor(h[i + 1:], h[i])
        dist = np.unpackbits(x.view(np.uint8).reshape(-1, 8), axis=1).sum(axis=1)
        for j in np.nonzero(dist <= NEAR_DUP_HAMMING)[0]:
            a, b = find(i), find(i + 1 + int(j))
            if a != b:
                parent[b] = a
    return [find(i) for i in range(n)]


def main():
    rng = random.Random(SEED)
    groups = defaultdict(list)
    dropped_classes = Counter()
    for src, orig, ref, loader in candidates():
        label = LABEL_MAP[src].get(orig)
        if label is None:
            dropped_classes[(src, orig)] += 1
            continue
        groups[(src, label)].append((orig, ref, loader))

    kept, rejects = [], []
    seen_md5 = set()
    exact_dups = Counter()
    for key in sorted(groups):
        src, label = key
        items = groups[key]
        rng.shuffle(items)
        n_kept = 0
        for orig, ref, loader in items[:CANDIDATES_PER_GROUP]:
            im = loader() if callable(loader) else Image.open(loader)
            try:
                arr, info = standardize(im)
            except Rejected as e:
                rejects.append(dict(source_id=src, original_label=orig, ref=ref, reason=e.reason,
                                    native_width=im.width, native_height=im.height))
                continue
            h = md5(arr)
            if h in seen_md5:
                exact_dups[src] += 1
                continue
            seen_md5.add(h)
            kept.append(dict(source_id=src, original_label=orig, label=label, ref=ref,
                             arr=arr, phash=phash(arr), **info))
            n_kept += 1
            if n_kept >= MAX_PER_GROUP:
                break
        print(f"{src:18s} {label:10s} kept {n_kept}")

    # Split by near-duplicate group, stratified by (source, label).
    by_key = defaultdict(list)
    for r in kept:
        by_key[(r["source_id"], r["label"])].append(r)
    near_dup_members = 0
    for key, rows in by_key.items():
        gid = near_dup_groups([r["phash"] for r in rows])
        clusters = defaultdict(list)
        for r, g in zip(rows, gid):
            clusters[g].append(r)
        near_dup_members += sum(len(c) for c in clusters.values() if len(c) > 1)
        # Largest groups first, each to the split furthest below its target.
        # Keeps whole groups together (no leakage) while still hitting
        # ~70/15/15 even when a few groups are very large.
        order = list(clusters.values())
        rng.shuffle(order)
        order.sort(key=len, reverse=True)
        n = len(rows)
        target = {"train": SPLIT[0] * n, "val": SPLIT[1] * n, "test": SPLIT[2] * n}
        filled = {"train": 0, "val": 0, "test": 0}
        for c in order:
            split = max(target, key=lambda s: (target[s] - filled[s]) / target[s])
            for r in c:
                r["split"] = split
            filled[split] += len(c)

    # Write images + metadata.
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for i, r in enumerate(sorted(kept, key=lambda r: (r["source_id"], r["label"], r["ref"]))):
        r["image_id"] = f"{r['source_id']}_{r['label']}_{i:06d}"
        rel = os.path.join(r["split"], r["label"], r["image_id"] + ".png")
        os.makedirs(os.path.join(OUT, os.path.dirname(rel)), exist_ok=True)
        Image.fromarray(r["arr"]).save(os.path.join(OUT, rel))
        r["path"] = rel.replace(os.sep, "/")

    cols = ["image_id", "source_id", "domain", "license", "original_label", "label_id",
            "label_name", "path", "split", "native_width", "native_height", "native_mode",
            "outline_redrawn", "bg_luma", "fg_fraction", "shape_px", "phash"]
    with open(os.path.join(OUT, "metadata.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in kept:
            w.writerow({**{k: r[k] for k in cols if k in r},
                        "domain": SOURCES[r["source_id"]]["domain"],
                        "license": SOURCES[r["source_id"]]["license"],
                        "label_id": TAXONOMY.index(r["label"]),
                        "label_name": r["label"], "phash": f"{r['phash']:016x}"})
    with open(os.path.join(OUT, "rejects.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source_id", "original_label", "ref", "reason",
                                          "native_width", "native_height"])
        w.writeheader()
        w.writerows(rejects)

    # SQLite catalog: exactly the five ERD entities from the report.
    db = sqlite3.connect(os.path.join(OUT, "catalog.sqlite"))
    db.executescript("""
        CREATE TABLE Source (source_id TEXT PRIMARY KEY, name TEXT, license TEXT, domain TEXT);
        CREATE TABLE Label (label_id INTEGER PRIMARY KEY, label_name TEXT UNIQUE);
        CREATE TABLE LabelMapping (source_id TEXT REFERENCES Source, original_label TEXT,
                                   label_id INTEGER REFERENCES Label,
                                   PRIMARY KEY (source_id, original_label));
        CREATE TABLE Image (image_id TEXT PRIMARY KEY, source_id TEXT REFERENCES Source,
                            label_id INTEGER REFERENCES Label, path TEXT, size TEXT, split TEXT);
        CREATE TABLE AugmentationRecord (image_id TEXT, parent_id TEXT REFERENCES Image,
                                         transform TEXT);
    """)
    db.executemany("INSERT INTO Source VALUES (?,?,?,?)",
                   [(k, v["name"], v["license"], v["domain"]) for k, v in SOURCES.items()])
    db.executemany("INSERT INTO Label VALUES (?,?)", list(enumerate(TAXONOMY)))
    db.executemany("INSERT INTO LabelMapping VALUES (?,?,?)",
                   [(s, o, None if t is None else TAXONOMY.index(t))
                    for s, m in LABEL_MAP.items() for o, t in m.items()])
    db.executemany("INSERT INTO Image VALUES (?,?,?,?,?,?)",
                   [(r["image_id"], r["source_id"], TAXONOMY.index(r["label"]), r["path"],
                     f"{r['native_width']}x{r['native_height']}", r["split"]) for r in kept])
    db.commit()
    n_cols = sum(len(db.execute(f"PRAGMA table_info({t})").fetchall())
                 for t in ["Source", "Label", "LabelMapping", "Image", "AugmentationRecord"])
    db.close()

    summary = {
        "kept": len(kept),
        "by_split": Counter(r["split"] for r in kept),
        "by_label": Counter(r["label"] for r in kept),
        "by_source": Counter(r["source_id"] for r in kept),
        "outline_redrawn": Counter(r["source_id"] for r in kept if r["outline_redrawn"]),
        "rejected": Counter((r["source_id"], r["reason"]) for r in rejects),
        "exact_duplicates_removed": exact_dups,
        "near_duplicate_images_grouped": near_dup_members,
        "test_by_label": Counter(r["label"] for r in kept if r["split"] == "test"),
        "dropped_out_of_taxonomy": dropped_classes,
        "catalog_tables": 5,
        "catalog_columns": n_cols,
        "disk_mb": round(sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT)
                             for f in fs) / 2**20, 1),
    }
    text = json.dumps({k: {str(kk): vv for kk, vv in v.items()} if isinstance(v, dict) else v
                       for k, v in summary.items()}, indent=2)
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
````

### `data_set/build_log.txt`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````text
github_handdrawn   ellipse    kept 1000
github_handdrawn   rectangle  kept 1000
github_handdrawn   triangle   kept 1000
kaggle_reevald     circle     kept 1000
kaggle_reevald     diamond    kept 1000
kaggle_reevald     rectangle  kept 1000
kaggle_reevald     square     kept 1000
kaggle_reevald     triangle   kept 1000
mendeley_elkorchi  circle     kept 1000
mendeley_elkorchi  hexagon    kept 1000
mendeley_elkorchi  octagon    kept 1000
mendeley_elkorchi  pentagon   kept 1000
mendeley_elkorchi  square     kept 1000
mendeley_elkorchi  star       kept 1000
mendeley_elkorchi  triangle   kept 1000
quickdraw          circle     kept 500
quickdraw          diamond    kept 500
quickdraw          hexagon    kept 500
quickdraw          octagon    kept 500
quickdraw          square     kept 500
quickdraw          star       kept 500
quickdraw          triangle   kept 500
{
  "kept": 18500,
  "by_split": {
    "train": 12761,
    "test": 2849,
    "val": 2890
  },
  "by_label": {
    "ellipse": 1000,
    "rectangle": 2000,
    "triangle": 3500,
    "circle": 2500,
    "diamond": 1500,
    "square": 2500,
    "hexagon": 1500,
    "octagon": 1500,
    "pentagon": 1000,
    "star": 1500
  },
  "by_source": {
    "github_handdrawn": 3000,
    "kaggle_reevald": 5000,
    "mendeley_elkorchi": 7000,
    "quickdraw": 3500
  },
  "outline_redrawn": {
    "github_handdrawn": 2267,
    "kaggle_reevald": 2228,
    "mendeley_elkorchi": 7000,
    "quickdraw": 995
  },
  "rejected": {
    "('mendeley_elkorchi', 'no_contrast')": 1
  },
  "exact_duplicates_removed": {
    "github_handdrawn": 1,
    "mendeley_elkorchi": 31
  },
  "near_duplicate_images_grouped": 2972,
  "test_by_label": {
    "ellipse": 150,
    "rectangle": 300,
    "triangle": 572,
    "circle": 375,
    "diamond": 225,
    "square": 375,
    "hexagon": 225,
    "octagon": 225,
    "pentagon": 157,
    "star": 245
  },
  "dropped_out_of_taxonomy": {
    "('kaggle_reevald', 'kite')": 2500,
    "('kaggle_reevald', 'parallelogram')": 2500,
    "('kaggle_reevald', 'trapezoid')": 2500,
    "('mendeley_elkorchi', 'Heptagon')": 10000,
    "('mendeley_elkorchi', 'Nonagon')": 10000,
    "('github_handdrawn', 'other')": 7287
  },
  "catalog_tables": 5,
  "catalog_columns": 18,
  "disk_mb": 12.1
}
````

### `data_set/unified/summary.json`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````json
{
  "kept": 18500,
  "by_split": {
    "train": 12761,
    "test": 2849,
    "val": 2890
  },
  "by_label": {
    "ellipse": 1000,
    "rectangle": 2000,
    "triangle": 3500,
    "circle": 2500,
    "diamond": 1500,
    "square": 2500,
    "hexagon": 1500,
    "octagon": 1500,
    "pentagon": 1000,
    "star": 1500
  },
  "by_source": {
    "github_handdrawn": 3000,
    "kaggle_reevald": 5000,
    "mendeley_elkorchi": 7000,
    "quickdraw": 3500
  },
  "outline_redrawn": {
    "github_handdrawn": 2267,
    "kaggle_reevald": 2228,
    "mendeley_elkorchi": 7000,
    "quickdraw": 995
  },
  "rejected": {
    "('mendeley_elkorchi', 'no_contrast')": 1
  },
  "exact_duplicates_removed": {
    "github_handdrawn": 1,
    "mendeley_elkorchi": 31
  },
  "near_duplicate_images_grouped": 2972,
  "test_by_label": {
    "ellipse": 150,
    "rectangle": 300,
    "triangle": 572,
    "circle": 375,
    "diamond": 225,
    "square": 375,
    "hexagon": 225,
    "octagon": 225,
    "pentagon": 157,
    "star": 245
  },
  "dropped_out_of_taxonomy": {
    "('kaggle_reevald', 'kite')": 2500,
    "('kaggle_reevald', 'parallelogram')": 2500,
    "('kaggle_reevald', 'trapezoid')": 2500,
    "('mendeley_elkorchi', 'Heptagon')": 10000,
    "('mendeley_elkorchi', 'Nonagon')": 10000,
    "('github_handdrawn', 'other')": 7287
  },
  "catalog_tables": 5,
  "catalog_columns": 18,
  "disk_mb": 12.1
}
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Counts alone hid bugs, so the output images were inspected. Thick rings became double lines, hollow stars kept solid arms, and 333 visible low-contrast shapes were rejected as blank (findings.md section 4).

## Our decision

Fixes: fill holes before deciding closed vs open, measure contrast as the strongest local contrast with the floor lowered to 8, and split near-duplicate groups largest-first to the split furthest below target (the test set had only 34 pentagons).

## Measured effect

18,500 images, 10 classes, 64x64 single channel. Split 12,761 / 2,890 / 2,849. No model at this stage.
