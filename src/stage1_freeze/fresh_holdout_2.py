"""Build a second fresh holdout for CRISP-DM iteration 3.

    python -m src.stage1_freeze.fresh_holdout_2

The first fresh holdout was read in iteration 2. This repeats that build's seeded
walk through the raw source folders, so its images are known without opening them
(the rebuilt manifest must hash to the stored one), then takes the next images in
each group. Anything within the
near-duplicate threshold of the catalog or of either holdout is dropped.

Writes ``configs/splits/fresh_holdout_2.csv`` and PNGs under
``data_set/fresh_holdout_2/``, read only through ``common.load_split``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from src.common.config import REPO_ROOT, load_config, resolve
from src.common.hashing import sha256_path
from src.common.imaging import md5, phash
from src.stage1_freeze.build_unified_dataset import LABEL_MAP, candidates
from src.stage1_freeze.fresh_holdout import (COLUMNS, PER_GROUP, SEED, SKIP_SOURCES, SPLIT_NAME as FIRST_NAME,
                                             catalog_hashes, near)
from src.stage1_freeze.standardize import Rejected, standardize
from src.stage1_freeze.taxonomy import TAXONOMY

SPLIT_NAME = "fresh_holdout_2"
OUT_DIR = REPO_ROOT / "data_set" / SPLIT_NAME
SECOND_PER_GROUP = 300


def _csv_hash(rows: list[dict]) -> str:
    """The sha256_path form of a manifest holding ``rows``, without writing it."""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return "sha256:" + hashlib.sha256(buffer.getvalue().encode("utf-8")).hexdigest()


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

    # First pass: the first holdout again, checked only against itself, as it was built.
    first_kept: list[int] = []
    first_rows, first, positions = [], Counter(), {}
    for key in sorted(groups):
        source, label = key
        items = groups[key]
        rng.shuffle(items)
        at = 0
        while at < len(items) and first[key] < PER_GROUP:
            loader, at = items[at], at + 1
            image = loader() if callable(loader) else Image.open(loader)
            try:
                arr, _info = standardize(image)
            except Rejected:
                continue
            value = phash(arr)
            if near(known, value, max_hamming) or near(np.array(first_kept, dtype=np.uint64), value, max_hamming):
                continue
            digest = md5(arr)
            first_rows.append({"image_id": f"fresh_{digest[:16]}", "md5": digest, "label_id": label_id[label],
                               "source_id": source, "phash_group": f"f{len(first_rows)}", "split": FIRST_NAME,
                               "path": (Path(label) / f"fresh_{digest[:16]}.png").as_posix()})
            first_kept.append(value)
            first[key] += 1
        positions[key] = at
    splits_dir = resolve(config["paths"]["splits_dir"])
    if _csv_hash(first_rows) != sha256_path(splits_dir / f"{FIRST_NAME}.csv"):
        raise RuntimeError("could not reproduce the first holdout, so its images cannot be excluded")

    # Second pass: carry on from where the first stopped in each group.
    kept = list(first_kept)
    rows, counts = [], Counter()
    for key in sorted(groups):
        source, label = key
        for loader in groups[key][positions[key]:]:
            if counts[key] >= SECOND_PER_GROUP:
                break
            image = loader() if callable(loader) else Image.open(loader)
            try:
                arr, _info = standardize(image)
            except Rejected:
                continue
            value = phash(arr)
            if near(known, value, max_hamming) or near(np.array(kept, dtype=np.uint64), value, max_hamming):
                continue
            kept.append(value)
            digest = md5(arr)
            image_id = f"fresh2_{digest[:16]}"
            relative = Path(label) / f"{image_id}.png"
            (OUT_DIR / label).mkdir(parents=True, exist_ok=True)
            Image.fromarray(arr).save(OUT_DIR / relative)
            rows.append({"image_id": image_id, "md5": digest, "label_id": label_id[label],
                         "source_id": source, "phash_group": f"g{len(rows)}", "split": SPLIT_NAME,
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
