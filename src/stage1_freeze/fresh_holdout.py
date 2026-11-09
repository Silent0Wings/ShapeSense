"""Build the fresh holdout for CRISP-DM iteration 2.

    python -m src.stage1_freeze.fresh_holdout

The test split was read in iteration 1, so it is no longer clean evidence. This
draws images that never entered the catalog from the raw source folders, gives
them the same standardization, and drops anything within the near-duplicate
threshold of the catalog or of another holdout image. Quick, Draw! is skipped
because all of its 3,500 local drawings are already in the catalog.

Writes ``configs/splits/fresh_holdout.csv`` and PNGs under
``data_set/fresh_holdout/``, read only through ``common.load_split``.
"""

from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from src.common.config import REPO_ROOT, load_config, resolve
from src.common.imaging import md5, phash
from src.stage1_freeze.build_unified_dataset import LABEL_MAP, candidates
from src.stage1_freeze.standardize import Rejected, standardize
from src.stage1_freeze.taxonomy import TAXONOMY

SEED = 20261109
PER_GROUP = 300              # images kept per (source, label)
SKIP_SOURCES = ("quickdraw",)
SPLIT_NAME = "fresh_holdout"
OUT_DIR = REPO_ROOT / "data_set" / SPLIT_NAME
COLUMNS = ["image_id", "md5", "label_id", "source_id", "phash_group", "split", "path"]


def catalog_hashes(metadata: Path) -> np.ndarray:
    """uint64 pHash of every catalog image, from metadata.csv."""
    with open(metadata, newline="", encoding="utf-8") as f:
        return np.array([int(r["phash"], 16) for r in csv.DictReader(f)], dtype=np.uint64)


def near(hashes: np.ndarray, value: int, max_hamming: int) -> bool:
    """True when ``value`` is within ``max_hamming`` bits of any hash."""
    if hashes.size == 0:
        return False
    x = np.bitwise_xor(hashes, np.uint64(value))
    bits = np.unpackbits(x.view(np.uint8).reshape(-1, 8), axis=1).sum(axis=1)
    return bool((bits <= max_hamming).any())


def build() -> Counter:
    config = load_config()
    max_hamming = int(config["split"]["phash_hamming_max"])
    known = catalog_hashes(resolve(config["paths"]["metadata"]))
    label_id = {name: i for i, name in enumerate(TAXONOMY)}
    rng = random.Random(SEED)
    groups: dict[tuple[str, str], list] = defaultdict(list)
    for source, original, _ref, loader in candidates():
        label = LABEL_MAP[source].get(original)
        if label is not None and source not in SKIP_SOURCES:
            groups[(source, label)].append(loader)

    kept_hashes: list[int] = []
    rows, counts = [], Counter()
    for key in sorted(groups):
        source, label = key
        items = groups[key]
        rng.shuffle(items)
        for loader in items:
            if counts[key] >= PER_GROUP:
                break
            image = loader() if callable(loader) else Image.open(loader)
            try:
                arr, _info = standardize(image)
            except Rejected:
                continue
            value = phash(arr)
            if near(known, value, max_hamming) or near(np.array(kept_hashes, dtype=np.uint64), value, max_hamming):
                counts[("near_duplicate_dropped", source)] += 1
                continue
            digest = md5(arr)
            image_id = f"fresh_{digest[:16]}"
            relative = Path(label) / f"{image_id}.png"
            (OUT_DIR / label).mkdir(parents=True, exist_ok=True)
            Image.fromarray(arr).save(OUT_DIR / relative)
            kept_hashes.append(value)
            rows.append({"image_id": image_id, "md5": digest, "label_id": label_id[label],
                         "source_id": source, "phash_group": f"f{len(rows)}", "split": SPLIT_NAME,
                         "path": relative.as_posix()})
            counts[key] += 1

    manifest = resolve(config["paths"]["splits_dir"]) / f"{SPLIT_NAME}.csv"
    with open(manifest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return counts


if __name__ == "__main__":
    for key, n in sorted(build().items(), key=str):
        print(key, n)
