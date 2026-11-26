"""Rebuild the contact sheets shown to the LLMs in the direct-prediction step.

``python -m scripts.direct_llm_sheets`` writes, under
results/direct_llm_prediction/sheets/:

- ``fewshot_examples.png``: the 50 labelled training images of
  fewshot_example_ids.csv, one row per class (5 tiles), class name on the left;
- ``batch_01.png`` .. ``batch_10.png``: the 200 test images of blind_id_map.csv,
  20 per sheet in T-ID order, captioned only with the blind ID (no filename,
  class or source).

Every tile is the standardized 64x64 grayscale PNG the CNN was scored on
(paths from data_set/unified/catalog.sqlite), and its pixel md5 must match
the frozen manifest (configs/splits/train.csv for the examples, test.csv for
the test images), or the script stops. The manifests are read as plain CSV
for their md5 column only; no labels or images are used for modelling here.

The original sheets of 2026-11-19 were made by hand and not kept. These are
a rebuild of the same images in the same blind order, not byte-identical
copies: tile spacing, borders and the caption font (Pillow's bundled sans
font, 12 px) were chosen here for readability. Output is deterministic for a
given Pillow build.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.common.catalog import image_paths, read_png
from src.common.config import load_config, resolve
from src.common.imaging import md5

RESULTS = Path("results/direct_llm_prediction")
OUT_DIR = RESULTS / "sheets"
TILE_PX = 64            # standardized image side, pixels (shown at native size)
GAP_PX = 12             # space between tiles, pixels
CAPTION_PX = 16         # caption strip under each batch tile, pixels
FONT_PX = 12            # caption and class-name font size, pixels
LABEL_W_PX = 80         # class-name column of the reference sheet, pixels
MARGIN_PX = 10          # outer margin, pixels
BATCH_COLUMNS = 5       # 20 tiles -> 5 columns x 4 rows
BACKGROUND = 255        # white
INK = 0                 # black
FRAME = 160             # grey tile border


def read_csv(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def batches(blind_rows: list[dict]) -> dict[str, list[dict]]:
    """batch name -> its rows in blind-ID order."""
    out: dict[str, list[dict]] = {}
    for r in sorted(blind_rows, key=lambda r: r["blind_id"]):
        out.setdefault(r["batch"], []).append(r)
    return dict(sorted(out.items()))


def fewshot_rows_by_class(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    """(class name, its example rows) in label_id order, slots in file order."""
    by_label: dict[int, list[dict]] = {}
    for r in rows:
        by_label.setdefault(int(r["label_id"]), []).append(r)
    return [(by_label[k][0]["true_label"], by_label[k]) for k in sorted(by_label)]


def _font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Pillow's bundled sans font (no system font lookup), so the rebuild does not
    # depend on what is installed; the old bitmap font draws "T" much like "r".
    return ImageFont.load_default(size=FONT_PX)


def _paste(page: Image.Image, draw: ImageDraw.ImageDraw, tile: np.ndarray, x: int, y: int) -> None:
    page.paste(Image.fromarray(tile), (x, y))
    draw.rectangle((x - 1, y - 1, x + TILE_PX, y + TILE_PX), outline=FRAME)


def render_batch(rows: list[dict], tiles: dict[str, np.ndarray]) -> Image.Image:
    n_rows = -(-len(rows) // BATCH_COLUMNS)
    cell_w, cell_h = TILE_PX + GAP_PX, TILE_PX + CAPTION_PX + GAP_PX
    page = Image.new("L", (2 * MARGIN_PX + BATCH_COLUMNS * cell_w - GAP_PX,
                           2 * MARGIN_PX + n_rows * cell_h - GAP_PX), BACKGROUND)
    draw, font = ImageDraw.Draw(page), _font()
    for k, r in enumerate(rows):
        x = MARGIN_PX + (k % BATCH_COLUMNS) * cell_w
        y = MARGIN_PX + (k // BATCH_COLUMNS) * cell_h
        _paste(page, draw, tiles[r["image_id"]], x, y)
        w = draw.textlength(r["blind_id"], font=font)
        draw.text((x + (TILE_PX - w) / 2, y + TILE_PX + 3), r["blind_id"], fill=INK, font=font)
    return page


def render_fewshot(groups: list[tuple[str, list[dict]]], tiles: dict[str, np.ndarray]) -> Image.Image:
    per_row = max(len(g) for _, g in groups)
    cell = TILE_PX + GAP_PX
    page = Image.new("L", (2 * MARGIN_PX + LABEL_W_PX + per_row * cell - GAP_PX,
                           2 * MARGIN_PX + len(groups) * cell - GAP_PX), BACKGROUND)
    draw, font = ImageDraw.Draw(page), _font()
    for i, (name, group) in enumerate(groups):
        y = MARGIN_PX + i * cell
        draw.text((MARGIN_PX, y + TILE_PX // 2 - FONT_PX // 2), name, fill=INK, font=font)
        for j, r in enumerate(group):
            _paste(page, draw, tiles[r["image_id"]], MARGIN_PX + LABEL_W_PX + j * cell, y)
    return page


def load_verified(config: dict, image_ids: list[str], manifest: Path) -> dict[str, np.ndarray]:
    """image_id -> pixels, after checking each pixel md5 against the manifest."""
    expected = {r["image_id"]: r["md5"] for r in read_csv(manifest)}
    paths, root = image_paths(config), resolve(config["paths"]["unified_dir"])
    tiles, bad = {}, []
    for iid in image_ids:
        if iid not in paths or iid not in expected:
            bad.append(f"{iid}: not in catalog or {manifest.name}")
            continue
        arr = read_png(root / paths[iid])
        if arr.shape != (TILE_PX, TILE_PX) or md5(arr) != expected[iid]:
            bad.append(f"{iid}: md5 or size differs from {manifest.name}")
        tiles[iid] = arr
    if bad:
        raise SystemExit("image check failed:\n  " + "\n  ".join(bad))
    return tiles


def main() -> None:
    config = load_config()
    splits = resolve(config["paths"]["splits_dir"])
    blind = read_csv(resolve(RESULTS / "blind_id_map.csv"))
    sample = {r["image_id"] for r in read_csv(resolve(RESULTS / "sample_ids.csv"))}
    if {r["image_id"] for r in blind} != sample or len(blind) != len(sample):
        raise SystemExit("blind_id_map.csv does not cover sample_ids.csv exactly once")
    fewshot = read_csv(resolve(RESULTS / "fewshot_example_ids.csv"))

    test_tiles = load_verified(config, [r["image_id"] for r in blind], splits / "test.csv")
    train_tiles = load_verified(config, [r["image_id"] for r in fewshot], splits / "train.csv")

    out = resolve(OUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    render_fewshot(fewshot_rows_by_class(fewshot), train_tiles).save(out / "fewshot_examples.png")
    for name, rows in batches(blind).items():
        render_batch(rows, test_tiles).save(out / f"{name}.png")
    print(f"wrote fewshot_examples.png ({len(fewshot)} tiles) and "
          f"{len(batches(blind))} batch sheets ({len(blind)} tiles) to {OUT_DIR.as_posix()}; "
          f"all {len(blind) + len(fewshot)} pixel md5s match the manifests")


if __name__ == "__main__":
    main()
