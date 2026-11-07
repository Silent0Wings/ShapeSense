"""
Functional-dependency check for the Phase 1 report (Section C).

Reads the unified metadata built by build_unified_dataset.py and checks
each candidate FD by grouping on the left-hand side and verifying the
right-hand side is constant within every group. Also runs an
injected-violation test to confirm the check catches conflicts.

    python scripts/check_fds.py
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "data_set", "unified", "metadata.csv")

CHECKS = [
    ("source_id -> domain", ["source_id"], ["domain"]),
    ("source_id -> license", ["source_id"], ["license"]),
    ("(source_id, original_label) -> label_id", ["source_id", "original_label"], ["label_id"]),
    ("label_id -> label_name", ["label_id"], ["label_name"]),
    ("image_id -> (path, split)", ["image_id"], ["path", "split"]),
    ("source_id -> (native_width, native_height)", ["source_id"], ["native_width", "native_height"]),
]


def check_fd(rows, lhs, rhs):
    groups = {}
    for r in rows:
        groups.setdefault(tuple(r[c] for c in lhs), set()).add(tuple(r[c] for c in rhs))
    violations = {k: v for k, v in groups.items() if len(v) > 1}
    return len(groups), violations


def main():
    with open(META, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Rows: {len(rows)}\n")
    for name, lhs, rhs in CHECKS:
        n, v = check_fd(rows, lhs, rhs)
        status = "HOLDS" if not v else f"VIOLATED in {len(v)} group(s), e.g. {next(iter(v.items()))}"
        print(f"{name}: {n} groups, {status}")

    print("\n--- Injected-violation test ---")
    bad = dict(rows[0], label_id="999")
    _, v = check_fd(rows + [bad], ["source_id", "original_label"], ["label_id"])
    print(f"1 injected row -> {len(v)} violating group(s): {v}")


if __name__ == "__main__":
    main()
