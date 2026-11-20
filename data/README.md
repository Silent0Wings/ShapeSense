# Data

The raw images are too large for the repository and live in `data_set/` (ignored by git).
Download links and licenses for each source:

| Source | Link | License |
|---|---|---|
| QuickDraw (subset) | https://github.com/googlecreativelab/quickdraw-dataset | CC BY 4.0 |
| Kaggle reevald geometric shapes | https://www.kaggle.com/datasets/reevald/geometric-shapes-mathematics | CC0 |
| Mendeley 2D geometric shapes | https://data.mendeley.com/datasets/wzr2yv7r53/1 | CC BY 4.0 |
| GitHub hand-drawn shapes | https://github.com/frobertpixto/hand-drawn-shapes-dataset | CC BY 4.0 (data), MIT (code) |

Full details: [docs/source.md](../docs/source.md).

## One-file download

The whole `data_set/` folder is packed into one archive, attached to the GitHub release `data_set`:

- Download: https://github.com/Silent0Wings/ShapeSense/releases/download/data_set/shapesense_data_set_v1.zip
- Size: 329,220,587 bytes (214,857 files)
- SHA-256: `a61fed163171f6c0668b97476c1a9320a3affc6741816abf331939240aac33ab`

It unpacks to `data_set/` and holds every folder the pipeline reads: the four raw sources (`2D geometric shapes
dataset/`, `kaggle_reevald/`, `github_handdrawn/`, `quickdraw/`, with `quickdraw_repo/`), the built `unified/` dataset
that Stage 0 compares a fresh rebuild against, the sealed `fresh_holdout/` and `fresh_holdout_2/` that Stage 5 reads,
and `kaggle_dinesh/`, which the Stage 1 audit samples even though the source is excluded from training. Rebuild it
with `scripts/make_data_zip.bat`.

An earlier asset, `shapesense_raw_sources_v1.zip`, holds only the four raw sources. Stage 0 fails with it because
`unified/` is missing; do not use it for a pipeline run.

The release's automatic "Source code" archives (`archive/refs/tags/data_set.zip` and `.tar.gz`) contain the
repository code at that tag, not the data.
