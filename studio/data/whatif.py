"""The locked success rule, re-applied to stored results with what-if thresholds.

Changes nothing and stores nothing. Mirrors src/stage5_eval/criterion.py:88-95
and is pinned to it by tests/studio/test_whatif_parity.py. Per-class drops come
from a table rounded to 0.1, so values close to a threshold can differ slightly
from the exact rule; the page says so.
"""

from __future__ import annotations

from studio.data.tables import read_csv, read_json


def _class_rows() -> list[dict] | None:
    per_class = read_csv("per_class")
    bands = read_csv("noise_bands")
    if per_class is None or bands is None:
        return None
    band_of = {r["label_name"]: float(r["noise_band_points"]) for r in bands}
    rows = []
    for r in per_class:
        name = r["class"].rstrip("*")
        rows.append({"class": name, "drop": -float(r["drop_B_minus_A1"]),
                     "drop_ci_lo": float(r["drop_ci_lo"]), "noise_band": band_of[name]})
    return rows


def evaluate(min_gain: float, max_class_drop: float, require_ci: bool) -> dict | None:
    """What the rule would say with these thresholds. None before Stage 5."""
    status = read_json("status5")
    rows = _class_rows()
    if status is None or rows is None:
        return None
    delta = float(status["metrics"]["delta"])
    ci_lo, ci_hi = (float(v) for v in status["metrics"]["ci"])
    reasons = []
    if delta < min_gain:
        reasons.append(f"gain {delta:.2f} < {min_gain:.2f} points")
    if require_ci and ci_lo <= 0.0:
        reasons.append(f"CI includes 0 ([{ci_lo:.2f}, {ci_hi:.2f}])")
    harmful = []
    for row in rows:
        threshold = max(max_class_drop, row["noise_band"])
        row["threshold"] = threshold
        row["harmful"] = row["drop"] > threshold and row["drop_ci_lo"] > 0.0
        if row["harmful"]:
            harmful.append(row["class"])
            reasons.append(f"{row['class']}: drop {row['drop']:.1f} > {threshold:.1f} and CI excludes 0")
    return {"verdict": "pass" if not reasons else "fail", "delta": delta, "ci": [ci_lo, ci_hi],
            "reasons": reasons, "harmful_classes": harmful, "classes": rows}
