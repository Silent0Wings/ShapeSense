"""Rule-based exclusions applied before the split (Decision 1 amendment).

CRISP-DM iteration 1 (2026-11-08, docs/crisp_dm/): the Quick, Draw!
"diamond" drawings are mostly gemstone/cone/shield doodles rather than
rhombi, i.e. label noise against the taxonomy definition. They are excluded
by rule — a (source, class) pair from configs/pipeline.yaml
`exclude_source_labels` — instead of an image-by-image list. Like the
gemstone filter, it runs BEFORE the split so the test set never contains the
excluded images.
"""

from __future__ import annotations


def apply_source_label_exclusions(rows: list[dict], pairs: list[list[str]],
                                  class_names: list[str]) -> tuple[list[dict], dict[str, int]]:
    """Drop every row whose (source_id, class name) is listed in `pairs`.

    rows: dicts with "source_id" and int "label_id". pairs: [[source, class], ...].
    Returns (kept rows in input order, {"source/class": n_removed}). A listed
    pair that matches no row raises ValueError (a typo must not pass silently).
    """
    wanted = {(src, class_names.index(name)): f"{src}/{name}" for src, name in pairs}
    removed = {key: 0 for key in wanted.values()}
    kept = []
    for r in rows:
        key = wanted.get((r["source_id"], int(r["label_id"])))
        if key is None:
            kept.append(r)
        else:
            removed[key] += 1
    empty = [k for k, n in removed.items() if n == 0]
    if empty:
        raise ValueError(f"exclude_source_labels: no rows match {empty}")
    return kept, removed
