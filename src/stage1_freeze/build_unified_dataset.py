"""
Build the unified, standardized shape dataset from the installed sources.

    python -m src.stage1_freeze.build_unified_dataset [--out DIR]

Order of operations (dedup BEFORE split, nothing augmented here):
  1. Sample candidates per (source, label), map labels to the 10-class
     taxonomy, drop out-of-taxonomy classes.
  2. Standardize every image (src/stage1_freeze/standardize.py); rejected images are
     logged to rejects.csv with the reason (Section D outlier examples).
  3. Remove exact duplicates (identical standardized pixels), across all
     sources.
  4. Cap each (source, label) group so no single source dominates a class.
  5. Group near-duplicates (pHash Hamming distance <= 2) and split by group,
     70/15/15, so near-identical images never straddle train and test.
  6. Write PNGs, metadata.csv, and catalog.sqlite (the 5-table ERD).

Outputs go to data_set/unified/ by default (git-ignored, like all of data_set/);
--out writes elsewhere (Stage 0 migration check rebuilds into artifacts/).
"""
import argparse
import csv
import glob
import json
import os
import random
import shutil
import sqlite3
from collections import Counter, defaultdict

from PIL import Image

from src.common.config import REPO_ROOT
from src.common.imaging import md5, phash
from src.common.neardup import near_dup_groups as _near_dup_groups
from src.common.quickdraw import quickdraw_loader
from src.stage1_freeze.standardize import Rejected, standardize
from src.stage1_freeze.taxonomy import TAXONOMY  # fixed label set, label_id = index

ROOT = str(REPO_ROOT)
DATA = os.path.join(ROOT, "data_set")
OUT = os.path.join(DATA, "unified")
SEED = 42
CANDIDATES_PER_GROUP = 1500
MAX_PER_GROUP = 1000
NEAR_DUP_HAMMING = 2
SPLIT = (0.70, 0.15, 0.15)

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


def candidates(data=DATA):
    """Yield (source_id, original_label, ref, loader) for every raw item."""
    for path in sorted(glob.glob(os.path.join(data, "quickdraw", "subset", "*.ndjson"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                yield "quickdraw", rec["word"], f"quickdraw/{rec['key_id']}", quickdraw_loader(rec)
    for path in sorted(glob.glob(os.path.join(data, "kaggle_reevald", "dataset", "*", "*", "*.jpg"))):
        yield "kaggle_reevald", os.path.basename(os.path.dirname(path)), path, path
    for path in sorted(glob.glob(os.path.join(data, "2D geometric shapes dataset", "output", "*.png"))):
        yield "mendeley_elkorchi", os.path.basename(path).split("_")[0], path, path
    for path in sorted(glob.glob(os.path.join(data, "github_handdrawn", "data", "*", "images", "*", "*.png"))):
        yield "github_handdrawn", os.path.basename(os.path.dirname(path)), path, path


def near_dup_groups(hashes):
    """Union-find over pairs with Hamming distance <= NEAR_DUP_HAMMING."""
    return _near_dup_groups(hashes, NEAR_DUP_HAMMING)


def build(out=OUT, data=DATA):
    rng = random.Random(SEED)
    groups = defaultdict(list)
    dropped_classes = Counter()
    for src, orig, ref, loader in candidates(data):
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
    if os.path.isdir(out):
        shutil.rmtree(out)
    for i, r in enumerate(sorted(kept, key=lambda r: (r["source_id"], r["label"], r["ref"]))):
        r["image_id"] = f"{r['source_id']}_{r['label']}_{i:06d}"
        rel = os.path.join(r["split"], r["label"], r["image_id"] + ".png")
        os.makedirs(os.path.join(out, os.path.dirname(rel)), exist_ok=True)
        Image.fromarray(r["arr"]).save(os.path.join(out, rel))
        r["path"] = rel.replace(os.sep, "/")

    cols = ["image_id", "source_id", "domain", "license", "original_label", "label_id",
            "label_name", "path", "split", "native_width", "native_height", "native_mode",
            "outline_redrawn", "bg_luma", "fg_fraction", "shape_px", "phash"]
    with open(os.path.join(out, "metadata.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in kept:
            w.writerow({**{k: r[k] for k in cols if k in r},
                        "domain": SOURCES[r["source_id"]]["domain"],
                        "license": SOURCES[r["source_id"]]["license"],
                        "label_id": TAXONOMY.index(r["label"]),
                        "label_name": r["label"], "phash": f"{r['phash']:016x}"})
    with open(os.path.join(out, "rejects.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source_id", "original_label", "ref", "reason",
                                          "native_width", "native_height"])
        w.writeheader()
        w.writerows(rejects)

    # SQLite catalog: exactly the five ERD entities from the report.
    db = sqlite3.connect(os.path.join(out, "catalog.sqlite"))
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
        "disk_mb": round(sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(out)
                             for f in fs) / 2**20, 1),
    }
    text = json.dumps({k: {str(kk): vv for kk, vv in v.items()} if isinstance(v, dict) else v
                       for k, v in summary.items()}, indent=2)
    with open(os.path.join(out, "summary.json"), "w") as f:
        f.write(text)
    print(text)


def main():
    parser = argparse.ArgumentParser(description="Build the unified, standardized shape dataset.")
    parser.add_argument("--out", default=OUT, help="output directory (default data_set/unified)")
    parser.add_argument("--data", default=DATA, help="raw data directory (default data_set)")
    args = parser.parse_args()
    build(args.out, args.data)


if __name__ == "__main__":
    main()
