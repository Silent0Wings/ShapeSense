"""
Functional-dependency DISCOVERY on the unified metadata (Section C).

Instead of only checking FDs we designed, this tests every left-hand side
of 1 or 2 columns against every other column and reports:
  - exact FDs   X -> Y holds on every row (minimal X only)
  - approx FDs  X -> Y holds after removing at most MAX_ERROR of rows
                (g3 error: share of rows that break it)

    python -m src.stage1_freeze.discover_fds
"""
import csv
import itertools
from collections import Counter, defaultdict

from src.common.config import load_default_config, resolve

# Categorical columns. Per-image unique ids (image_id, path, phash) and
# continuous measurements are left out: a unique column determines
# everything trivially.
COLS = ["source_id", "domain", "license", "original_label", "label_id",
        "label_name", "split", "native_width", "native_height",
        "native_mode", "outline_redrawn"]
MAX_ERROR = 0.05


def g3(rows, lhs, rhs):
    """Share of rows to delete so lhs -> rhs holds exactly."""
    groups = defaultdict(Counter)
    for r in rows:
        groups[tuple(r[c] for c in lhs)][r[rhs]] += 1
    keep = sum(c.most_common(1)[0][1] for c in groups.values())
    return 1 - keep / len(rows)


def main():
    meta = resolve(load_default_config()["paths"]["metadata"])   # paths.metadata, read at call time
    with open(meta, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    exact, approx = [], []
    for k in (1, 2):
        for lhs in itertools.combinations(COLS, k):
            for rhs in COLS:
                if rhs in lhs:
                    continue
                # skip if a smaller lhs already determines rhs (not minimal)
                if any(set(e[0]) < set(lhs) and e[1] == rhs for e in exact):
                    continue
                err = g3(rows, lhs, rhs)
                if err == 0:
                    exact.append((lhs, rhs))
                elif err <= MAX_ERROR and k == 1:
                    approx.append((lhs, rhs, err))
    print(f"Rows: {len(rows)}\n\n--- Exact minimal FDs ---")
    for lhs, rhs in exact:
        print(f"{', '.join(lhs)} -> {rhs}")
    print(f"\n--- Approximate FDs (error <= {MAX_ERROR:.0%}) ---")
    for lhs, rhs, err in sorted(approx, key=lambda a: a[2]):
        print(f"{', '.join(lhs)} -> {rhs}   error {err:.2%}")


if __name__ == "__main__":
    main()
