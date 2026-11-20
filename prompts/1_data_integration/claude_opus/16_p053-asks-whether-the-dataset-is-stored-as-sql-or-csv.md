# 1_data_integration - P053: Asks whether the dataset is stored as SQL or CSV
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P053. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

is it sql is it csv ?

## Response

Both. The images are PNG files, and their information is stored in two places: a SQLite database that the code reads from, and a flat CSV file that is exported from the same information. The short answer is that the SQLite catalog is the working copy and the CSV is a readable copy alongside it. Neither replaces the PNG files themselves.

##### SQLite catalog (main copy)
- **`catalog.sqlite`** is the main store. [src/common/catalog.py:3](../../../src/common/catalog.py#L3) calls it the authority on the dataset. The same docstring says it is the authority on paths, labels and sources, while split membership comes only from the Stage 1 manifests through `common.load_split` (Decision 15). So the catalog does not decide which split an image belongs to.
- It holds a 5-table database design. The table list is set in [src/stage0_infra/migration.py](../../../src/stage0_infra/migration.py) as `Source`, `Label`, `LabelMapping`, `Image` and `AugmentationRecord`.
- The pipeline reads the image list from this catalog. `image_paths` in [src/common/catalog.py](../../../src/common/catalog.py) runs `SELECT image_id, path FROM Image` and returns a map from each image ID to its PNG path. The connection is opened read-only (`mode=ro`), one per process, which the docstring notes is for Windows safety.
- The path of the catalog comes from the config: `paths.catalog` in [configs/pipeline.yaml](../../../configs/pipeline.yaml) points to `data_set/unified/catalog.sqlite`.

##### CSV export (flat copy)
- **`metadata.csv`** is a flat, one-table export of the same information. It has one row per image. Its path comes from `paths.metadata` in [configs/pipeline.yaml](../../../configs/pipeline.yaml), which points to `data_set/unified/metadata.csv`. The notes in docs/notes/pairs/7_meta_and_other.md (`prompts/claude_code_session_pairs.md`, not in the repository) describe it as having 17 columns (ID, source, license, label, split, original size and image statistics). That column count is from the notes and I did not re-count it here.
- It is easy to read by hand because it is plain text, so it can be opened in a spreadsheet or a text editor without a SQLite tool.
- Unconfirmed: the claim that "a few audit scripts use this file" was not checked against a specific script in this pass.
- [src/stage0_infra/migration.py](../../../src/stage0_infra/migration.py) hashes the catalog rows and the metadata CSV content, along with row counts, class counts and pHash near-duplicate groups. It compares a rebuild made by the moved code against the pre-move build. This checks that the move of scripts from `scripts/` to `src/` changed nothing. It does not compare the catalog directly against the CSV row by row, so "the two copies match" should be read as "both were unchanged across the move".

##### Sheet entry
The sheet value is:

```
18,000 rows (64x64 grayscale PNG images, indexed in a SQLite catalog with a CSV export), 35 MB
```

This entry matches what the other notes in this repo record: 18,000 rows and about 35 MB for the unified dataset. The 35 MB figure is an approximate size measured on the older copy, which has 18,500 images, so the true size of the 18,000-image final set is slightly smaller. The size of the data itself is not stored in this repo.

##### Sheet entry
The sheet value is:

```
18,000 rows (64x64 grayscale PNG images, indexed in a SQLite catalog with a CSV export), 35 MB
```

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
