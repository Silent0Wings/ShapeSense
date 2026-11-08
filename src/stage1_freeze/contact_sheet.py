"""Review contact sheets for the gemstone-diamond decision (Decision 1).

Renders every Quick, Draw! image of the class under review as a grid of
thumbnails, each captioned with the positional id suffix and the md5
prefix, so reviewers can record `image_id, md5` in configs/gemstone_ids.csv.
The code never classifies a drawing as a gemstone; humans do.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.common.catalog import read_png
from src.stage1_freeze.gemstones import EXCLUSION_COLUMNS

REVIEW_SOURCE = "quickdraw"       # source whose drawings are reviewed (Decision 1)
REVIEW_CLASS_NAME = "diamond"     # taxonomy class name under review; index looked up
COLUMNS = 10                      # thumbnails per row
TILE_PX = 64                      # thumbnail side, pixels (standardized size)
CELL_W_PX = 100                   # grid cell width, pixels
CELL_H_PX = 84                    # grid cell height, pixels (tile + caption)
CAPTION_PAD_PX = 2                # gap between tile and caption, pixels
MD5_PREFIX_CHARS = 8              # md5 characters printed under each tile
BACKGROUND = 255                  # white
INK = 0                           # black
SHEET_PREFIX = "gemstone_contact_sheet_"


def select_review_rows(rows: list[dict], label_id: int,
                       source_id: str = REVIEW_SOURCE) -> list[dict]:
    """Rows of `source_id` with `label_id`, sorted by image_id."""
    picked = [r for r in rows if r["source_id"] == source_id and int(r["label_id"]) == label_id]
    return sorted(picked, key=lambda r: r["image_id"])


def caption_for(row: dict) -> str:
    """'<image_id suffix> <md5 prefix>' — what reviewers copy into the list."""
    suffix = row["image_id"].rsplit("_", 1)[-1]
    return f"{suffix} {row['md5'][:MD5_PREFIX_CHARS]}"


def render_page(rows: list[dict], unified_dir: Path, per_page: int) -> Image.Image:
    """One page: up to `per_page` tiles, COLUMNS per row, captions below."""
    n_rows = max(1, math.ceil(per_page / COLUMNS))
    page = Image.new("L", (COLUMNS * CELL_W_PX, n_rows * CELL_H_PX), BACKGROUND)
    draw = ImageDraw.Draw(page)
    font = ImageFont.load_default()
    for k, r in enumerate(rows):
        col, row_i = k % COLUMNS, k // COLUMNS
        x0, y0 = col * CELL_W_PX, row_i * CELL_H_PX
        tile = Image.fromarray(read_png(unified_dir / r["path"]))
        if tile.size != (TILE_PX, TILE_PX):
            tile = tile.resize((TILE_PX, TILE_PX), Image.Resampling.NEAREST)
        page.paste(tile, (x0 + (CELL_W_PX - TILE_PX) // 2, y0))
        draw.text((x0 + 2, y0 + TILE_PX + CAPTION_PAD_PX), caption_for(r), fill=INK, font=font)
    return page


def write_contact_sheets(rows: list[dict], unified_dir: str | Path, out_dir: str | Path,
                         label_id: int, per_page: int = 100,
                         source_id: str = REVIEW_SOURCE) -> list[Path]:
    """Write `gemstone_contact_sheet_<k>.png` pages under out_dir; return their paths.

    Stale pages from an earlier run are removed first so the page count
    always matches the current rows.
    """
    unified_dir, out_dir = Path(unified_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob(f"{SHEET_PREFIX}*.png"):
        stale.unlink()
    review = select_review_rows(rows, label_id, source_id)
    paths: list[Path] = []
    for k in range(math.ceil(len(review) / per_page)):
        chunk = review[k * per_page:(k + 1) * per_page]
        p = out_dir / f"{SHEET_PREFIX}{k}.png"
        render_page(chunk, unified_dir, per_page).save(p)
        paths.append(p)
    return paths


def write_template(path: str | Path) -> bool:
    """Create the header-only exclusion list if absent. Returns True if written."""
    p = Path(path)
    if p.exists():
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(",".join(EXCLUSION_COLUMNS) + "\n", encoding="utf-8")
    return True
