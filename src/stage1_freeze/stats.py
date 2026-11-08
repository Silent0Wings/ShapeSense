"""Split statistics, Decision 10 noise bands and the FD-check frame (R8, R12).

Pure functions. Stage 5 reads its per-class class-drop thresholds from
the noise-band table, so the band is stored at full precision; rounding
is for display only.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Mapping, Sequence

TEST_SPLIT = "test"


def split_stats(rows: list[dict], class_names: Sequence[str]) -> list[dict]:
    """Per (split, label_id, source_id) counts, sorted; label_name attached."""
    counts = Counter((str(r["split"]), int(r["label_id"]), str(r["source_id"])) for r in rows)
    return [{"split": s, "label_id": lab, "label_name": class_names[lab], "source_id": src, "n": n}
            for (s, lab, src), n in sorted(counts.items())]


def noise_band_points(n: int, accuracy: float) -> float:
    """100 * sqrt(p(1-p)/n): one standard error of recall at `accuracy`, in points."""
    if n <= 0:
        raise ValueError("noise band needs n > 0 test rows")
    return 100.0 * math.sqrt(accuracy * (1.0 - accuracy) / n)


def noise_bands(rows: list[dict], class_names: Sequence[str], accuracy: float,
                min_drop_points: float) -> list[dict]:
    """Per class: n_test, noise_band_points and threshold = max(floor, band).

    Raises ValueError if a class has no test rows: every class must be
    measurable on the test split (Decision 10).
    """
    n_test = Counter(int(r["label_id"]) for r in rows if str(r["split"]) == TEST_SPLIT)
    out = []
    for lab, name in enumerate(class_names):
        n = n_test.get(lab, 0)
        if n == 0:
            raise ValueError(f"class {lab} ({name}) has no rows in the test split")
        band = noise_band_points(n, accuracy)
        out.append({"label_id": lab, "label_name": name, "n_test": n,
                    "noise_band_points": band,
                    "threshold_points": max(float(min_drop_points), band)})
    return out


def fd_rows(filtered_rows: list[dict], metadata_rows: list[dict],
            split_of: Mapping[str, str]) -> list[dict]:
    """metadata.csv rows restricted to the filtered image_ids, `split` set to the NEW split.

    This is the frame check_fds.check_rows must see (R8): never metadata.csv
    as-is, whose rows include filtered-out images and Phase 1 splits.
    """
    keep = {r["image_id"] for r in filtered_rows}
    out = []
    for m in metadata_rows:
        iid = m["image_id"]
        if iid in keep:
            out.append({**m, "split": split_of[iid]})
    return out


def source_test_share(rows: list[dict]) -> dict[str, float]:
    """Each source's share of the test split (Should 1)."""
    test = [str(r["source_id"]) for r in rows if str(r["split"]) == TEST_SPLIT]
    n = len(test)
    return {s: c / n for s, c in sorted(Counter(test).items())} if n else {}
