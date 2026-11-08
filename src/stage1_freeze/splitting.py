"""Global near-duplicate groups and the group-aware stratified split.

Pure functions on lists of dicts (stages/stage_1.md R3, R4, R6, R7;
Decision 15). Groups are computed ONCE over all rows, never per source:
grouping within a source was the Phase 1 bug that let cross-source
near-duplicates straddle train and test.

Assignment: each group's stratum is (majority label_id, majority
source_id). Within a stratum the groups are shuffled with a seeded
Generator, stably sorted by size (largest first) and each goes to the
split furthest below its target share, whole. A 175-row group therefore
lands in one split and may push that stratum off 70/15/15; that is
reported, never "fixed" by breaking the group.
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence

import numpy as np

from src.common.neardup import near_dup_groups

SPLIT_NAMES = ("train", "val", "test")   # order also breaks deficit ties
GROUP_ID_FORMAT = "g{:06d}"              # g000001, ... in first-appearance order


def global_groups(phashes: Sequence[int], max_hamming: int) -> list[int]:
    """Group member-index per row, over ALL rows at once (Decision 15, R3)."""
    return near_dup_groups(list(phashes), max_hamming)


def group_labels(member_groups: Sequence[int]) -> list[str]:
    """Stable string ids (`g000001`...) numbered by first appearance.

    Call with rows already sorted by image_id so the ids, and therefore the
    manifests, are byte-identical across runs (R7).
    """
    ids: dict[int, str] = {}
    out: list[str] = []
    for g in member_groups:
        if g not in ids:
            ids[g] = GROUP_ID_FORMAT.format(len(ids) + 1)
        out.append(ids[g])
    return out


def _furthest_below_target(targets: Sequence[float], filled: Sequence[int]) -> int:
    """Index of the split with the largest relative deficit; ties -> lowest index."""
    deficits = [(t - f) / t for t, f in zip(targets, filled)]
    return max(range(len(deficits)), key=lambda j: deficits[j])


def group_split(rows: list[dict], ratios: Sequence[float], seed: int) -> list[str]:
    """Split name per row; whole groups only (R4), deterministic for a seed (R7).

    rows must carry label_id, source_id and phash_group. ratios are the
    train/val/test shares from configs/pipeline.yaml (R6).
    """
    if len(ratios) != len(SPLIT_NAMES):
        raise ValueError(f"expected {len(SPLIT_NAMES)} ratios, got {len(ratios)}")
    groups: dict[str, list[int]] = {}
    for i, r in enumerate(rows):
        groups.setdefault(r["phash_group"], []).append(i)

    strata: dict[tuple[int, str], list[str]] = {}
    for gid, idx in groups.items():
        label = Counter(int(rows[i]["label_id"]) for i in idx).most_common(1)[0][0]
        source = Counter(str(rows[i]["source_id"]) for i in idx).most_common(1)[0][0]
        strata.setdefault((label, source), []).append(gid)

    rng = np.random.default_rng(seed)
    split_of_row: list[str | None] = [None] * len(rows)
    for key in sorted(strata):
        gids = sorted(strata[key])
        order = [gids[p] for p in rng.permutation(len(gids))]
        order.sort(key=lambda g: len(groups[g]), reverse=True)  # stable: largest first
        n = sum(len(groups[g]) for g in gids)
        targets = [ratio * n for ratio in ratios]
        filled = [0] * len(SPLIT_NAMES)
        for g in order:
            k = _furthest_below_target(targets, filled)
            for i in groups[g]:
                split_of_row[i] = SPLIT_NAMES[k]
            filled[k] += len(groups[g])
    if any(s is None for s in split_of_row):
        raise RuntimeError("group_split left a row unassigned")  # cannot happen
    return [str(s) for s in split_of_row]


def group_sizes(rows: list[dict]) -> Counter:
    """phash_group -> number of rows."""
    return Counter(r["phash_group"] for r in rows)


def mixed_label_groups(rows: list[dict]) -> int:
    """Number of groups whose members carry more than one label_id."""
    labels: dict[str, set] = {}
    for r in rows:
        labels.setdefault(r["phash_group"], set()).add(int(r["label_id"]))
    return sum(1 for s in labels.values() if len(s) > 1)
