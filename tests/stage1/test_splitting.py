"""E21: global pHash groups and the group-aware stratified split (R3, R4, R6, R7)."""

from collections import Counter

import numpy as np

from src.stage1_freeze.leakage import write_manifests
from src.stage1_freeze.splitting import (SPLIT_NAMES, global_groups, group_labels,
                                         group_split)

RATIOS = [0.70, 0.15, 0.15]
SEED = 42


def _rows(n, n_labels=4, n_sources=2, group_size=1, seed=0):
    """n synthetic rows; rows i and i+1.. in blocks of group_size share a group."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        g = i // group_size
        rows.append({
            "image_id": f"img_{i:06d}",
            "md5": f"m{i:06d}",
            "label_id": int(rng.integers(n_labels)) if group_size == 1 else g % n_labels,
            "source_id": f"s{(g % n_sources)}",
            "phash_group": f"g{g:06d}",
        })
    return rows


def _attach(rows, splits):
    for r, s in zip(rows, splits):
        r["split"] = s
    return rows


def _splits_per_group(rows):
    seen = {}
    for r in rows:
        seen.setdefault(r["phash_group"], set()).add(r["split"])
    return seen


def test_groups_never_span():
    rows = _rows(400, group_size=20)
    _attach(rows, group_split(rows, RATIOS, SEED))
    assert all(len(s) == 1 for s in _splits_per_group(rows).values())
    assert len({r["split"] for r in rows}) == 3            # all three splits are used


def test_ratios_close_to_target():
    rows = _rows(2000)
    splits = group_split(rows, RATIOS, SEED)
    counts = Counter(splits)
    for name, ratio in zip(SPLIT_NAMES, RATIOS):
        share = counts[name] / len(rows)
        assert abs(share - ratio) <= 0.02, (name, share)


def test_deterministic_for_seed(tmp_path):
    texts = []
    for k in range(2):
        rows = _rows(300, group_size=3)
        _attach(rows, group_split(rows, RATIOS, SEED))
        d = tmp_path / f"run{k}"
        write_manifests(rows, d)
        texts.append({p.name: p.read_bytes() for p in sorted(d.glob("*.csv"))})
    assert texts[0] == texts[1]
    assert set(texts[0]) == {"train.csv", "val.csv", "test.csv"}
    # a different seed moves at least one row (the split is seed-driven, not fixed)
    rows = _rows(300, group_size=3)
    assert group_split(rows, RATIOS, SEED) != group_split(rows, RATIOS, SEED + 1)


def test_large_group_kept_whole():
    rows = _rows(600)                                   # many singleton groups
    for r in rows[:175]:                                # one 175-row pentagon-like group
        r["phash_group"] = "gBIG"
        r["label_id"] = 5
        r["source_id"] = "mendeley_elkorchi"
    _attach(rows, group_split(rows, RATIOS, SEED))
    big = {r["split"] for r in rows if r["phash_group"] == "gBIG"}
    assert len(big) == 1
    assert sum(1 for r in rows if r["phash_group"] == "gBIG") == 175


def test_cross_source_near_duplicates_grouped():
    # Phase 1 grouped per (source, label); the same pHash from two sources must now share a group.
    phashes = [0xF0F0, 0xF0F0, 0x0F0F, 0x0F0E]
    members = global_groups(phashes, max_hamming=2)
    labels = group_labels(members)
    assert labels[0] == labels[1]            # identical pHash, different sources
    assert labels[2] == labels[3]            # Hamming distance 1
    assert labels[0] != labels[2]
    assert labels[0] == "g000001" and labels[2] == "g000002"


def test_whole_groups_in_mixed_label_group():
    # a group whose members disagree on label still goes to one split
    rows = _rows(50)
    for r in rows[:6]:
        r["phash_group"] = "gMIX"
    for i, r in enumerate(rows[:6]):
        r["label_id"] = i % 2
    _attach(rows, group_split(rows, RATIOS, SEED))
    assert len({r["split"] for r in rows if r["phash_group"] == "gMIX"}) == 1
