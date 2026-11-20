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

The four sources are also packed into one archive, attached to the GitHub release `data_set`:

- Download: https://github.com/Silent0Wings/ShapeSense/releases/download/data_set/shapesense_raw_sources_v1.zip
- Size: 285,695,841 bytes (157,350 files)
- SHA-256: `e06fcbabacda920a9fe7109513094e5bdc7274fbce97f7cf30af01567531cf6e`

It unpacks to `data_set/` with the folder names Stage 1 expects: `2D geometric shapes dataset/`, `kaggle_reevald/`,
`github_handdrawn/`, `quickdraw/` and `quickdraw_repo/`. It leaves out `kaggle_dinesh/` (excluded source), `unified/`
(built by Stage 1) and the fresh holdouts (built by the project scripts). Rebuild it with `scripts/make_data_zip.bat`.

The release's automatic "Source code" archives (`archive/refs/tags/data_set.zip` and `.tar.gz`) contain the
repository code at that tag, not the data.
