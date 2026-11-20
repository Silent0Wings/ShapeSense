# 0_data_discovery - Opus 5.5 grounds and resizes Gemini 4 Neon's visualization plan

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code
- Critiqued output: Gemini 4 Neon (its draft plan, linked in the Response)
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-10-19
- Owner: 40256377
- Source: **evidence file**, rebuilt from the saved work, not from a chat export. **The prompt is inferred** from the artifact and was not saved. The Response quotes the LLM's saved output files verbatim.

## Prompt (inferred, not saved)

> _Inferred:_ Find real documentation for the visualization and auditing tools proposed in plan 05, and recommend a toolset sized to a one-report student project.

## Response (saved output, verbatim)

### `research_notes/Shape dataset integration and tooling/visualization_tools.md`

_From the project snapshot of 2026-11-08 (`ignore/comp33 project/`, not in the repo)._

````markdown
# Visualization and Auditing Tools for a Multi-Source Image Classification Dataset

## What are the standard, free/open-source tools for building a quick interactive data-exploration dashboard for an image dataset (Streamlit, Gradio, or simpler alternatives)? What do official docs/examples show for image-dataset browsing use cases specifically?

### Takeaway
Streamlit and Gradio are both free, pure-Python, pip-installable frameworks that can turn a dataset-browsing script into a shareable local web app in minutes; Streamlit's own official demo repo is literally an image-dataset browser, while Gradio's `Gallery`/`Dataset` components are the documented building blocks for showing grids of images with captions. For a small project, these are lower setup cost than a custom web app but higher cost than just running Matplotlib grids in a notebook.

### Cited Findings
- Streamlit's official demo repo, `demo-self-driving`, is "an image browser for the Udacity self-driving-car dataset with realtime object detection using YOLO" — the closest official example to an image-dataset browsing use case. — [Streamlit (via search aggregation of streamlit/demo-self-driving)](https://www.github.com/streamlit)
- The current official `st.columns` API reference shows building an image grid by creating columns and placing `st.image` calls inside them (e.g. `left, middle, right = st.columns(3, vertical_alignment=...)` followed by image calls), and documents `vertical_alignment` (top/center/bottom) for grid alignment and `st.columns([3,1,2])` for ratio-based widths. — [Streamlit st.columns docs](https://docs.streamlit.io/develop/api-reference/layout/st.columns)
- A documented pattern for turning a single row of columns into a full image grid is to call `st.columns` inside a loop and use modulo indexing (`col = cols[idx % cols_count]`) to place each image in the next available column, then call `st.image(..., use_container_width=True)`; a Hugging Face Space example implements exactly this pattern. — [Streamlit blog: New layout options](https://blog.streamlit.io/introducing-new-layout-options-for-streamlit)
- Gradio's official `gr.Gallery` component displays "a grid of images or videos with optional captions"; items are clickable to view larger (controlled via `allow_preview`), `value` accepts a list of images/videos or a callable for the initial value, and `format` (default `"webp"`) sets the image save format sent to the frontend. — [Gradio Gallery docs](https://gradio.app/docs/gradio/gallery)
- Gradio's `gr.Dataset` component "creates a gallery or table to display data samples," and the docs note it is "primarily designed for internal use to display examples" (e.g., example inputs for a demo) rather than as a general dataset browser. — [Gradio Dataset docs](https://gradio.app/4.44.1/docs/gradio/dataset)
- Older Streamlit code in the wild uses deprecated APIs (`use_column_width`, `st.beta_columns`); the current API uses `use_container_width` and `st.columns` — relevant for a small team following older tutorials. — [Streamlit docs/blog cross-reference](https://docs.streamlit.io/develop/api-reference/layout/st.columns)

### Inferences
- For a small academic project, Streamlit's column-loop grid pattern (a handful of lines) is likely the lowest-effort way to build an actual "click through and inspect images with filters" dashboard, since it requires no frontend code, only Python plus `pip install streamlit`.
- Gradio's `Gallery` is comparable in simplicity for a read-only browsing view, but `Dataset` is not intended as a general-purpose dataset auditing widget — it's built for example pickers in demos, so `Gallery` + custom layout is the better Gradio primitive for this use case.

### Gaps
- No official Streamlit tutorial page specifically titled "image dataset browser" was retrieved (only the demo repo, found via secondhand search description) — the actual code of `demo-self-driving` was not directly fetched/verified in this research pass.
- No official Gradio tutorial fetched that builds a full filterable dataset-auditing app end-to-end (e.g., with class filter dropdowns); only the component-level docs were confirmed.

---

## What are standard plotting approaches (Matplotlib/Seaborn) for class-balance bar charts, image-resolution/aspect-ratio scatter plots, and pixel-intensity histograms when auditing a dataset?

### Takeaway
Class balance is standardly shown with a categorical count/bar chart (seaborn's `countplot`, or Yellowbrick's purpose-built `ClassBalance` visualizer); resolution/aspect-ratio checks are standardly done with a width-vs-height `plt.scatter`; and pixel-intensity checks use per-channel histograms — all three are implemented together by the small open-source CLI tool `basic-image-eda`, which exists specifically to catch image reading/resizing/normalization mistakes.

### Cited Findings
- `seaborn.countplot` is described in the official docs as showing "the counts of observations in each categorical bin," functioning as "a histogram across a categorical, rather than quantitative, variable," and it shares its API with `barplot()` (supports `x`/`y`/`hue`/`order`/`orient`/`stat`/`dodge`/`log_scale`, etc.). — [seaborn.countplot official docs](https://seaborn.pydata.org/generated/seaborn.countplot.html)
- Seaborn's `stat` parameter on `countplot` can rescale bars from raw counts to percentages/proportions, and `order=` can be passed explicitly to control category ordering (seaborn otherwise defaults to the order found in the data, often alphabetical). — [seaborn.countplot official docs](https://seaborn.pydata.org/generated/seaborn.countplot.html); ordering note corroborated by [Getgalaxy guide](https://www.getgalaxy.io/learn/glossary/plotting-value-counts-with-seaborn)
- Yellowbrick's `ClassBalance` visualizer draws a bar chart of per-class support specifically to let a practitioner inspect imbalance before choosing a corrective strategy, and its docs warn that severe imbalance "may be masked by relatively good F1 and accuracy scores" if not checked visually first. — [Yellowbrick ClassBalance docs](https://yellowbrick.readthedocs.io/en/v1.5/api/target/class_balance.html)
- The open-source CLI/Python tool `basic-image-eda` (`pip install basic-image-eda`) scans an image directory recursively and produces: image count, per-channel pixel mean/std (0–1 scale), min/max/mean/median height and width, mean/median aspect ratio, and recommended model input sizes; it exposes a height-vs-width scatter plot via `-d/--dimension_plot` and per-channel pixel-intensity histograms via `-c/--channel_hist`. It is explicitly built to catch "reading, resizing, and normalizing" mistakes before images are fed to a neural network. — [basic-image-eda GitHub](https://github.com/Soongja/basic-image-eda)
- `basic-image-eda` has real limitations relevant to a multi-source dataset: it converts all images to 3-channel RGB internally (so mixed grayscale/RGB sources can look misleading if not handled explicitly), only supports uint8/uint16 (mixing dtypes errors out), and channel histograms "significantly increase run time." It depends on `opencv-python`, `numpy`, `matplotlib`, `scikit-image`, `tifffile`, and `tqdm`. — [basic-image-eda GitHub](https://github.com/Soongja/basic-image-eda)
- A separate blog-snippet tool (Hugging Face Space `Spiral-ND/eda.py`) plots width vs. height with `plt.scatter`, using alpha blending and labeled axes, as a minimal manual alternative to a packaged EDA tool — i.e., the scatter-plot approach is simple enough to hand-roll in a few lines without any extra dependency. — [Hugging Face Space eda.py](https://huggingface.co/spaces/cycool29/Spiral-ND/blob/main/eda.py)
- A book chapter ("Exploring Image Data," in *Data Labeling in Machine Learning with Python*, Packt) covers plotting pixel-value histograms for grayscale images, per-channel histograms for RGB images, and analyzing image size/aspect ratio with NumPy + Matplotlib — confirming this is treated as a standard workflow in ML engineering literature, though the chapter itself is paywalled and wasn't read in full. — [Packt chapter listing](https://www.packtpub.com/en-us/product/data-labeling-in-machine-learning-with-python-6-9781804610541/chapter/chapter-4-exploring-image-data)
- A dataset-scale audit by Pebblous DataClinic, reviewing 134 image classification datasets, used the max-to-min class-count ratio as its imbalance metric, finding 25% of datasets (33/134) perfectly balanced and 15 datasets with a max/min ratio exceeding 100x; their ImageNet case study notes that a count-only verdict can miss *semantic* imbalance (e.g., 120 of ImageNet's 1,000 classes are dog breeds). This is a useful caution for a multi-source merged dataset: raw per-class counts should be checked per-source as well as overall. — [Pebblous DataClinic](https://blog.pebblous.ai/story/dataclinic-dataset-stats-story-pb/en/); [ImageNet case study](https://blog.pebblous.ai/story/dataclinic-report-123-imagenet-story-pb/en/)

### Inferences
- For a merged dataset of sketches/renders/synthetic images, the single most actionable standard chart set is: (1) `sns.countplot(x="class", hue="source")` to see both overall and per-source class balance in one chart, (2) a width-vs-height scatter (color-coded by source) to catch resolution outliers or sources that weren't resized consistently, and (3) per-channel pixel-intensity histograms (color-coded by source) to catch preprocessing bugs like unconverted grayscale channels or inverted/clipped pixel ranges.
- Given `basic-image-eda`'s RGB-coercion limitation, a project mixing sketches (often grayscale) with renders (often RGB) should either run the tool per-source-subset or write the ~10-20 lines of manual Matplotlib/Seaborn code directly rather than relying on the packaged tool, to avoid silently losing channel information.

### Gaps
- No official Matplotlib gallery page specifically titled for "image resolution scatter plot" or "pixel intensity histogram" was directly fetched/confirmed — the scatter/histogram code pattern is corroborated by secondary sources (Packt chapter, HF Space snippet, basic-image-eda) rather than an official Matplotlib tutorial.

---

## What is the standard approach for visualizing high-dimensional image feature similarity/clustering (t-SNE and UMAP) to check whether images from different sources/domains form separable or overlapping clusters?

### Takeaway
The standard workflow is: extract a feature embedding per image (e.g., from a pretrained CNN or simple pixel/HOG features), optionally reduce to ~50 dimensions with PCA, then project to 2D with scikit-learn's `TSNE` or `umap-learn`'s `UMAP`, and scatter-plot the 2D points colored by source/domain label to visually check for separable vs. overlapping clusters. Both libraries are free, pip-installable, and scikit-learn-API compatible, so setup cost is low.

### Cited Findings
- Scikit-learn's official `TSNE` docs describe it as a tool "for visualizing high-dimensional data" using `n_components` (2 or 3 for visualization) and `perplexity` (default 30.0, docs suggest "a value between 5 and 50," noting "larger datasets usually require a larger perplexity," and perplexity must be less than the number of samples). — [scikit-learn TSNE docs](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html)
- Scikit-learn's docs state the t-SNE cost function is non-convex, so "different initializations can give different results" — the official recommendation is `init="pca"` (the default), which is "usually more globally stable than random initialization." For reproducibility, `random_state` should be fixed, and it's advised to compare a few perplexity values/seeds before drawing conclusions (illustrated in the official gallery example "t-SNE: The effect of various perplexity values on the shape"). — [scikit-learn TSNE docs](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html)
- Scikit-learn's docs explicitly recommend reducing very high-dimensional data to around 50 dimensions with PCA (for dense data) or TruncatedSVD (for sparse data) before running t-SNE, to suppress noise and speed up pairwise-distance computation — directly applicable since raw image pixels or CNN features are high-dimensional. — [scikit-learn TSNE docs](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html)
- Scikit-learn documents two solvers: `"barnes_hut"` (default, O(N log N), the practical choice for datasets beyond a few thousand points) and `"exact"` (O(N²), more accurate but doesn't scale to large N); `learning_rate` defaults to `"auto"` (computed as `max(N / early_exaggeration / 4, 50)`), with guidance that a too-high rate makes the embedding look like an undifferentiated "ball" and too-low makes points look like a "compressed dense cloud." — [scikit-learn TSNE docs](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html)
- The official umap-learn basic-usage docs show the canonical workflow: scale features (e.g., `StandardScaler`), then `reducer = umap.UMAP(); embedding = reducer.fit_transform(scaled_data)`, producing an `(n_samples, 2)` array by default that can be scatter-plotted directly, colored by class label; the docs state UMAP is "designed to be compatible with scikit-learn," so it can be used in sklearn pipelines and follows the same `fit`/`transform`/`fit_transform` conventions. — [umap-learn basic usage docs](https://umap-learn.readthedocs.io/en/latest/basic_usage.html)
- The umap-learn docs show `UMAP(random_state=42)` for reproducible runs on a digits-dataset example, and default parameter values of `n_neighbors=15` and `min_dist=0.1` appear in the printed object repr, though the basic-usage page itself doesn't explain their effect in depth and points to further parameter tutorials instead. — [umap-learn basic usage docs](https://umap-learn.readthedocs.io/en/latest/basic_usage.html)
- Third-party domain-specific documentation (Arize Phoenix, Fiddler AI) independently confirms the same general pattern for ML observability: UMAP is used to project high-dimensional embeddings into a 2D/3D space specifically "so clusters and outliers are easier to spot," corroborating that this technique is an industry-standard way to visually check for separable vs. overlapping groups in embedding space (these are commercial-adjacent docs, not open-source project docs, included here only as corroboration, not as a tool recommendation). — [Fiddler embedding visualization docs](https://docs.fiddler.ai/observability/llm/embedding-visualization-with-umap)

### Inferences
- For checking whether sketches/renders/synthetic images form separable or overlapping clusters, the standard, low-setup-cost pipeline for a small project is: extract embeddings (even simple ones, e.g. flattened/resized pixel vectors or a pretrained ImageNet CNN's penultimate-layer features), run PCA to ~50 dims if using raw pixels or high-dim CNN features, then run either `sklearn.manifold.TSNE(init="pca", random_state=...)` or `umap.UMAP(random_state=...)`, and scatter the 2D output colored by source label. Running both t-SNE and UMAP and comparing is reasonable given both are near-zero marginal cost once embeddings are computed, and the two methods have different distortion behaviors.
- Because t-SNE's layout is explicitly non-deterministic/initialization-sensitive per scikit-learn's own docs, any claim like "sources X and Y overlap" drawn from a single t-SNE run should be treated cautiously; the officially-recommended practice of checking multiple perplexity values/seeds is a direct, citable justification for running sensitivity checks before writing up conclusions in a report.

### Gaps
- Did not retrieve the official umap-learn docs' dedicated plotting/parameter-tuning page (only basic_usage.html) — exact guidance on choosing `n_neighbors`/`min_dist` for the specific purpose of separating domains vs. just visualizing overall structure was not found in official docs during this pass; secondary "skill" pages (non-canonical) suggested `min_dist` 0.0 for clustering, 0.1-0.3 for visualization, but this is not sourced to the official docs and should be treated as unverified.
- No official scikit-learn tutorial specifically for *image* embeddings with t-SNE was found; the workflow described above is inferred/generalized from the general-purpose TSNE docs plus third-party tools (MMPretrain, thelper) that wrap scikit-learn's TSNE for image feature visualization.

---

## Are there existing open-source dataset-auditing/EDA tools built specifically for image datasets (FiftyOne, CleanLab, Lightly) that a small project could adopt instead of building a custom dashboard? What do they offer and what's the setup cost?

### Takeaway
FiftyOne (Voxel51) is the most directly applicable turnkey tool — a free, Apache-2.0-licensed, `pip install`-able Python library with a browser-based visual app for filtering, sorting, and tagging image datasets, launchable with a few lines of code. Cleanlab's ecosystem offers two relevant free pieces — `cleanvision` (image-file-level issue detection: duplicates, blur, exposure) and `Datalab`/core `cleanlab` (label/outlier/duplicate detection from model embeddings or predictions) — with low-to-moderate setup cost depending on whether you already have model embeddings. Lightly was searched but no official documentation was retrieved in this pass, so its specifics are a gap.

### Cited Findings
- FiftyOne is installed via `pip install fiftyone` into a virtual environment; the official installation docs state this "installs FiftyOne and all of its dependencies," and a successful install produces no output when the package is imported. — [FiftyOne installation docs](https://docs.voxel51.com/installation/index.html)
- The official FiftyOne quickstart workflow is a few lines: load a small built-in sample dataset via the dataset zoo (`foz.load_zoo_dataset("quickstart")`) and launch the interactive visual App (`fo.launch_app(dataset)`); if run from a script rather than a Python shell, `session.wait()` is needed to keep the App open. — [FiftyOne installation/quickstart docs, via PyPI listing](https://pypi.python.org/project/fiftyone/0.7.2/)
- FiftyOne's PyPI description states the library and App let users "search, sort, filter, visualize, analyze, and improve" datasets, confirming filtering/tagging/visualization are first-class, built-in features rather than something to build manually. — [FiftyOne PyPI listing](https://pypi.python.org/project/fiftyone/0.7.0/)
- Additional FiftyOne setup requirements beyond `pip install`: video datasets require FFmpeg (installed via apt/brew, or a manual Windows build); macOS requires Xcode Command Line Tools; Linux may need Python headers (`python3-dev` on Debian-based systems) for the `psutil` dependency. Installation issues are commonly resolved per the docs by running `pip install --upgrade pip setuptools wheel build` before reinstalling FiftyOne. — [FiftyOne installation docs](https://docs.voxel51.com/installation/index.html)
- (Secondhand, lower confidence — from aggregator/review sites, not FiftyOne's own docs directly) FiftyOne users report using it to visually audit large datasets and build complex filters on ground-truth labels, model predictions, and custom tags to catch labeling errors; one source claims FiftyOne found "over 1/3 of Open Images false positives are annotation errors." These specific quotes were not verified against Voxel51's own primary documentation in this research pass and should be treated as corroborating color, not confirmed fact. — [aggregator/directory listing](https://us.fitgap.com/products/003778/fiftyone); [Voxel51 blog on Open Images](https://voxel51.com/blog/fiftyone-open-images-collaboration)
- **CleanVision** (free, open-source, part of the Cleanlab ecosystem) "automatically detects various issues in image datasets, such as images that are: (near) duplicates, blurry, over/under-exposed," operating directly on raw image files (no model/embeddings required) — making it a near-zero-setup check for corrupted/duplicate images after preprocessing. — [CleanVision GitHub README](https://github.com/cleanlab/cleanvision/blob/main/README.md)
- The core **cleanlab** package's **Datalab** module instead detects issues like outliers and (near) duplicates using model-derived feature embeddings or predicted probabilities — i.e., it requires you to already have a trained model or extracted embeddings, raising its setup cost relative to CleanVision. Datalab scores each example's "outlier quality... inversely proportional to its distance to its K nearest neighbors in the dataset." — [Cleanlab Datalab docs](https://docs.cleanlab.ai/v2.6.2/cleanlab/datalab/guide/issue_type_description.html); [Datalab quickstart tutorial](https://docs.cleanlab.ai/v2.6.4/tutorials/datalab/datalab_quickstart.html)
- Cleanlab's own blog cites a commercial product (Cleanlab Studio) finding issues on ImageNet and Food-101N (e.g., 8,519 flagged outliers on Food-101N) — these results are from the paid Studio product, not the free open-source `cleanlab`/`cleanvision` packages, so they should not be read as evidence for the free tools' exact capabilities, only as a sign the underlying detection approach is used at scale. — [Cleanlab Studio blog](https://cleanlab.ai/blog/learn/csa/csa-5/)
- An independent academic study (retinal imaging) used Cleanlab's near-duplicate detection and confirmed 638 duplicate images across six datasets, flagging train/test leakage from duplicates as the main risk this check catches — directly relevant precedent for a "merged from several sources" dataset, where duplicate/near-duplicate images across sources are a real risk. — [researchsquare.com preprint](https://www.researchsquare.com/article/rs-10775714)
- No official Lightly documentation was retrieved via search in this pass; search results surfaced only tangential/unrelated tools (Apple's "Embedding Atlas," TensorBoard's Embedding Projector, a tool called "VEST"). This is a confirmed gap, not a finding about Lightly itself.
- As a side note, Apple's **Embedding Atlas** is a free, open-source (per search-result description) tool "for visualizing and exploring large-scale embeddings interactively," running entirely client-side in the browser, available as a Python package or an npm library — a plausible lightweight alternative to UMAP+Matplotlib for the clustering-visualization question above, though this was not verified against Apple's own project page directly. — [InfoQ coverage of Embedding Atlas](https://www.infoq.com/news/2025/11/embedding-atlas); [arXiv paper](https://arxiv.org/abs/2505.06386)

### Inferences
- For a small project with no labeled-model-output pipeline yet, **CleanVision** is the lowest-setup-cost option of the Cleanlab tools (works on raw files, no embeddings needed) and is well-matched to the stated goal of checking that preprocessing hasn't corrupted images or introduced duplicates/blur/exposure problems. **cleanlab Datalab** is a reasonable second step once a baseline classifier or embedding extractor exists, since it adds outlier/near-duplicate detection in feature space (useful for catching cross-source near-duplicates).
- **FiftyOne** is the most complete single tool for the "visual browsing + filtering + tagging" half of the request (overlapping with the dashboard question above) and could substitute for a hand-built Streamlit/Gradio app, at the cost of a heavier dependency footprint (its own App server, optional FFmpeg, and some OS-level build prerequisites) — appropriate if the team wants more built-in query/filter power and is willing to learn FiftyOne's own query API instead of writing custom code.

### Gaps
- Lightly's own setup cost, feature set, and documentation were not found in this research pass; a dedicated follow-up search directly on `docs.lightly.ai` or Lightly's GitHub README is needed to answer that part of the question.
- The specific, numeric claims attributed to FiftyOne users (e.g. "over 1/3 of Open Images false positives are annotation errors") come from secondary/aggregator sources, not Voxel51's own primary documentation, and could not be verified directly in this pass.

---

## What's a reasonable, minimal toolset recommendation for a small academic project to visually confirm that preprocessing (resize, grayscale conversion, padding) hasn't corrupted images, and that classes/domains are balanced?

### Takeaway
Based on the findings above, a minimal, low-setup, all-free Python toolset is: Matplotlib for direct before/after image-grid spot checks, `seaborn.countplot` for class/source balance bars, a hand-rolled or `basic-image-eda`-assisted width/height scatter + pixel-histogram check for preprocessing corruption, and (optionally) `cleanvision` for an automated duplicate/blur/exposure pass — all of which can run inside a single Jupyter notebook without needing a dedicated dashboard server.

### Cited Findings
- All claims in this synthesis are drawn from the Cited Findings already sourced above under the other four key questions (seaborn countplot docs, basic-image-eda GitHub README, CleanVision README, scikit-learn TSNE docs, umap-learn basic usage docs); no new sources were fetched specifically for this synthesis question.

### Inferences
- Setup-cost ranking from lowest to highest for this specific project's stated goal (confirm preprocessing didn't corrupt images + confirm class/domain balance):
  1. **Matplotlib image grids** (e.g., `plt.subplots` + `imshow` on a random sample per class/source, before vs. after preprocessing) — zero new dependencies beyond what's already needed for the ML pipeline; directly answers "did resize/grayscale/padding break anything" by eyeballing actual images.
  2. **`seaborn.countplot(x="class", hue="source")`** — one line of code once data is in a DataFrame; directly answers the class/domain balance question with both an overall and a per-source breakdown in a single chart.
  3. **Width/height scatter + pixel histograms**, either hand-rolled in Matplotlib (a dozen lines, as shown in the Hugging Face Space snippet cited above) or via `pip install basic-image-eda` for a packaged CLI report — catches silent resize/padding bugs (e.g., images not actually resized, unexpected channel counts) that a human eyeballing a 3x3 grid might miss.
  4. **`pip install cleanvision`** (optional but cheap) — a few more lines to run an automated near-duplicate/blur/exposure scan across the merged dataset, useful specifically because the dataset merges multiple sources where accidental duplicates across sources are plausible.
  5. **A full FiftyOne or Streamlit/Gradio dashboard** — the highest setup cost of the options surveyed (new dependency, its own server process, some OS-level prerequisites for FiftyOne); worth adopting only if the team anticipates needing repeated, interactive, filterable browsing sessions (e.g., ongoing labeling-error triage) rather than a one-time preprocessing/balance sanity check for a report.
  6. **t-SNE/UMAP cluster visualization** is a nice-to-have, not a minimal requirement, for the stated goal (confirming preprocessing correctness and balance) — it answers a different question (do sources form separable domains in feature space) and requires a feature extractor to already exist, so it's reasonably deferred until after the basic corruption/balance checks pass.

### Gaps
- No direct academic-project case study was found describing exactly this minimal toolset choice (i.e., no single blog post explicitly recommends "just Matplotlib + seaborn + cleanvision for a student project"); this recommendation is a synthesis/inference from the individually-sourced findings above rather than a directly cited claim, and is labeled as such.
````

### `09_visualization_tools_grounded.md`

_From the local plan folder (`ignore/plan/`, not in the repo)._

````markdown
> **Status (2026-10-19):** DONE (Tier 1): scripts/audit_dataset.py. Tiers 2-3 not needed for Phase 1.

# Plan 09: Grounded, Tiered Visualization Toolset (replaces Plan 05)

## 1. Why this exists
Plan 05 proposed a fairly heavy toolset (Streamlit dashboard, Gradio,
custom manifold explorer, etc.) without weighing setup cost against project
scope. A deep-research pass found real documentation for each option and
produced a tiered recommendation sized to a one-report student project, not
a production pipeline. Full sourcing:
`research_notes/Shape dataset integration and tooling/visualization_tools.md`.
Mistral Vision / OCR tooling is explicitly out of scope per an earlier
decision — not included here.

## 2. Tier 1 (zero new dependencies, do this first)
- **Matplotlib** before/after image grids: catches resize, grayscale, and
  padding bugs by direct inspection. No new dependency beyond what training
  already needs.
- **`seaborn.countplot(x="class", hue="source")`** for class/source balance
  — documented categorical-histogram API, same interface as `barplot`.
  https://seaborn.pydata.org/generated/seaborn.countplot.html
- Width-vs-height scatter + per-channel pixel-intensity histograms
  (hand-rolled, ~a dozen lines) to check resolution/channel consistency
  across merged sources.

## 3. Tier 2 (small, free, purpose-built — adopt if Tier 1 isn't enough)
- **`basic-image-eda`** (open-source CLI): scans a directory, reports
  per-channel pixel stats, aspect-ratio summaries, recommended input sizes.
  https://github.com/Soongja/basic-image-eda
  **Caveat**: coerces everything to 3-channel RGB internally — run it
  per-source-subset if the dataset deliberately mixes grayscale (sketches)
  and color (renders) sources, or channel information is lost.
- **CleanVision** (Cleanlab ecosystem): operates on raw files, no model or
  embeddings needed, flags near-duplicates/blur/over-under-exposure.
  Near-zero setup. https://github.com/cleanlab/cleanvision
  Real precedent: an academic retinal-imaging study used the same approach
  to confirm 638 duplicate images across six merged sources and flagged the
  resulting train/test leakage risk.
- **Yellowbrick's `ClassBalance`** visualizer as an alternative to
  `countplot` — explicitly warns that imbalance "may be masked by
  relatively good F1 and accuracy scores" if not checked visually.
  https://yellowbrick.readthedocs.io/en/v1.5/api/target/class_balance.html

## 4. Tier 3 (heavier, optional — only if ongoing triage is needed)
- **FiftyOne** (Voxel51): most complete turnkey interactive browse/filter/
  tag tool. `pip install fiftyone`, launch with a few lines. Heaviest
  footprint surveyed (own server process, optional FFmpeg, OS build
  prerequisites) — worth it only for repeated, ongoing dataset triage, not
  a one-time Phase-1 sanity pass.
  https://docs.voxel51.com/installation/index.html
- **t-SNE / UMAP** clustering (scikit-learn `TSNE`, `umap-learn`) to check
  whether different sources/domains form separable feature-space clusters.
  scikit-learn's own docs recommend PCA-reducing to ~50 dims first, using
  `init="pca"`, and checking multiple perplexity/seed values (non-convex
  cost function). Answers a different question than basic corruption/
  balance auditing — a later-stage addition, not part of the minimal
  toolset.
  https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html
  https://umap-learn.readthedocs.io/en/latest/basic_usage.html

## 5. What NOT to over-invest in for Phase 1
- A full Streamlit/Gradio dashboard is real and documented (Streamlit's own
  demo repo is an image browser; Gradio has a built-in `gr.Gallery`
  component) but is setup cost better justified once the dataset is final,
  not while sources are still being corrected (see Plans 06-07).
- Note: Gradio's `gr.Dataset` component is explicitly **not** a general
  dataset browser per its own docs — it's built for example pickers. Don't
  reach for it by name alone.
- Lightly: no official docs were retrieved in this research pass — treat as
  an open gap, not a recommended tool, until checked directly.

## 6. Action items
- [ ] Implement Tier 1 (Matplotlib grids + seaborn countplot + resolution
      scatter/histograms) as the baseline audit for whatever dataset results
      from Plans 06-07.
- [ ] Add CleanVision as a cheap dedup/quality safety net before the
      train/test split (ties directly into Plan 08's dedup-before-split rule).
- [ ] Only adopt FiftyOne or t-SNE/UMAP if the project's scope grows beyond
      a single Phase-1 report deliverable.
- [ ] Update Section E's tools table in `phase1_report.tex` to reflect this
      tiered framing instead of a flat list, if/when Section E is revised.
````

## Validation

_Validation, Our decision and Measured effect are written by the team from the saved record (status lines, todo `done` lines, `docs/findings.md`, [attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the LLM output._

Each option was checked against its official documentation and examples.

## Our decision

Tier 1 (Matplotlib) was implemented in `scripts/audit_dataset.py`. Tiers 2 and 3 (Streamlit, Gradio, manifold explorer) were judged not needed for Phase 1.

## Measured effect

No model at this stage.
