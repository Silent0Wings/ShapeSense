"""The rebuilt direct-LLM contact sheets follow the committed CSVs (no data_set/ needed)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from scripts.direct_llm_sheets import (RESULTS, TILE_PX, batches, fewshot_rows_by_class,
                                       read_csv, render_batch, render_fewshot)

REPO = Path(__file__).resolve().parents[2]


def test_batches_follow_blind_map():
    blind = read_csv(REPO / RESULTS / "blind_id_map.csv")
    sample = {r["image_id"] for r in read_csv(REPO / RESULTS / "sample_ids.csv")}
    groups = batches(blind)
    assert list(groups) == [f"batch_{k:02d}" for k in range(1, 11)]
    ids = [r["blind_id"] for rows in groups.values() for r in rows]
    assert ids == [f"T{k:03d}" for k in range(1, 201)]
    assert all(len(rows) == 20 for rows in groups.values())
    assert {r["image_id"] for rows in groups.values() for r in rows} == sample


def test_fewshot_has_five_per_class_in_label_order():
    groups = fewshot_rows_by_class(read_csv(REPO / RESULTS / "fewshot_example_ids.csv"))
    assert [name for name, _ in groups] == ["circle", "ellipse", "triangle", "square", "rectangle",
                                            "pentagon", "hexagon", "octagon", "star", "diamond"]
    assert all(len(rows) == 5 for _, rows in groups)


def test_render_is_deterministic():
    rows = [{"blind_id": f"T{k:03d}", "image_id": f"img{k}"} for k in range(1, 21)]
    tiles = {r["image_id"]: np.full((TILE_PX, TILE_PX), k * 10, np.uint8) for k, r in enumerate(rows)}
    a, b = render_batch(rows, tiles), render_batch(rows, tiles)
    assert a.tobytes() == b.tobytes()
    fs = render_fewshot([("circle", rows[:5])], tiles)
    assert fs.width > 5 * TILE_PX and fs.height >= TILE_PX
