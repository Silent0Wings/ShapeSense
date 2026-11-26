# 4_testing - F16: A clean clone could not find the tuning result. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F16 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f16) · Record: [F16](../inferred_prompts.md#f16)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> Why do ML results that run in the working folder fail on a clean clone, and what do reproducibility checklists recommend (committed artifacts vs generated ones, data and artifact versioning, clean-clone tests)? Search for the NeurIPS reproducibility checklist and similar guidance.

## Response

### Well established

- **The NeurIPS checklists ask for code, data and instructions that are enough to reproduce the main results.** The 2022 checklist asks: "Did you include the code, data, and instructions needed to reproduce the main experimental results (either in the supplemental material or as a URL)?" ([NeurIPS 2022 Paper Checklist](https://neurips.cc/Conferences/2022/PaperInformation/PaperChecklist); [2021 version](https://neurips.cc/Conferences/2021/PaperInformation/PaperChecklist)). The checklist grew out of the NeurIPS 2019 reproducibility program, which combined a code submission policy, a reproducibility challenge and the checklist ([Pineau et al., JMLR 22(164), 2021](https://jmlr.org/papers/v22/20-303.html); [arXiv 2003.12206](https://arxiv.org/pdf/2003.12206)). The original checklist PDF is hosted by Pineau ([ReproducibilityChecklist.pdf](https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf)).
- **Current checklist guidance**, as quoted in a 2025 paper's filled-in checklist, says instructions should contain "the exact command and environment needed to run to reproduce the results", and should explain how to get raw, preprocessed, intermediate and generated data ([arXiv 2511.16842](https://arxiv.org/pdf/2511.16842)). That is a sample answer, not the official page, so check the current year's wording.
- **Keep intermediate results and the data behind every figure.** Sandve et al.'s "Ten Simple Rules for Reproducible Computational Research" includes Rule 5, "Record All Intermediate Results, When Possible in Standardized Formats", and also advise against manual data manipulation ([PLoS Comput Biol 2013, PMC3812051](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3812051/)).
- **Large artifacts can be versioned outside Git through small pointer files.** DVC stores data and models in a cache or remote while Git tracks metadata files and a `dvc.lock` for pipeline outputs ([DVC on PyPI](https://pypi.org/project/dvc/); [DVC data and model access](https://dvc.org/doc/start/data-and-model-access)). DataLad offers a similar approach ([DataLad handbook](https://handbook.datalad.org/en/latest/beyond_basics/101-168-dvc.html)).

### Single sources or community guidance

- The NeurIPS 2020 "releasing research code" guidance recommends a README that pairs each result in a table with the precise command that produces it, and lists pretrained models as part of a complete release ([releasing-research-code mirror](https://github.com/vvhanxing/releasing-research-code)). This is a copy of the paperswithcode repository, not the conference page.

### My own reasoning: why the working folder lies

- A working folder holds every file you ever produced, including ignored ones. A pipeline that silently reads an ignored file passes locally and fails on a clean clone. Any `.gitignore` entry that a later stage reads from is a hidden input.
- The fix comes in two parts: (1) decide which generated outputs are *frozen decisions* (a tuning result that later stages depend on and that would be expensive or nondeterministic to recreate) and commit those as source; (2) run the pipeline from a fresh clone, routinely, as a test. None of the checklists above spells out a "clean-clone test", but it is the direct way to check the NeurIPS "exact command and environment" requirement.

### How it applies to ShapeSense

1. `artifacts/` is a build folder. Keeping it out of Git follows normal practice, and DVC-style pointers would be the heavy alternative for checkpoints ([DVC](https://dvc.org/doc/start/data-and-model-access)).
2. The tuning winners are a *decision*, not a rebuildable output: re-running the search costs GPU time and may not choose the same winners. Committing them under `docs/crisp_dm/` fits Sandve's Rule 5 ([PMC3812051](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3812051/)).
3. A full rehearsal on a fresh clone is the practical check for the NeurIPS "code, data and instructions" item ([NeurIPS checklist](https://neurips.cc/Conferences/2022/PaperInformation/PaperChecklist)).

## Validation

The record's documented cause is that `artifacts/` is not in Git while Stages 4 and 6 read the winners from there. That matches the hidden-input pattern above. The literature agrees with the fix: commit the intermediate result that matters ([Sandve et al.](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3812051/)), document exact commands ([NeurIPS checklist](https://neurips.cc/Conferences/2022/PaperInformation/PaperChecklist)), and prove it with a run from scratch. It adds a general audit worth doing: list every path in `.gitignore` that any stage reads, and make sure each one is either rebuilt by an earlier stage or restored from a committed copy. Nothing contradicts the record.

## Our decision

The project kept `artifacts/` out of Git, committed the frozen winners under `docs/crisp_dm/`, added `restore_frozen_winners` to `run_pipeline.py` (it copies only when the file is absent), unit-tested both the restore and no-overwrite cases, and ran a fresh-clone rehearsal that reproduced every result. The findings support this. Possible additions are the `.gitignore` audit above and running a clean-clone check before each freeze. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Info(`F16`)

### Metadata & Lineage
* **Entry ID / Type:** `F16` (`failure`, `4_testing` — literature audit)
* **Failure Mode:** Clean git clones failed in Stages 4 and 6 because `artifacts/` is gitignored while the pipeline required `artifacts/stage4/tuning_iter2/winners.json` produced by an expensive offline hyperparameter search.
* **Primary Sources:**
  * Sandve et al. (2013), *Ten Simple Rules for Reproducible Computational Research* (*PLOS Computational Biology* 9(10): e1003285, `PMC3812051`)
  * Pineau et al. (2021), *Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program)* (*JMLR* 22(164):1–20)
  * DVC Documentation: *Pipelines, Tracked Stage Outputs, and Clean-Checkout Hydration*

### 1. DAG Closure Under Clean-Clone Projections
Let $\mathcal{G} = (V, E)$ be the pipeline execution DAG, and let $\Pi_{\text{git}}(V)$ denote the subset of files persisted in version control (excluding `.gitignore` paths such as `artifacts/`). A pipeline suffers from **untracked ancestor starvation** if any default stage $v \in V_{\text{default}}$ depends on an edge $(u, v) \in E$ where $u \notin \Pi_{\text{git}}(V)$ and $u$ is produced only by an opt-in offline stage ($u \in V_{\text{offline}}$, e.g., `--run-iter2-search`):
1. **Committed Canonical Provenance + Ephemeral Hydration:** For small, high-cost decision artifacts (hyperparameter search winners, frozen iteration status summaries, SHA-256 manifests), committing the canonical JSON under a versioned evidence directory (`docs/crisp_dm/iteration_*/`) satisfies $\Pi_{\text{git}}$ closure without bloating the repository with multi-gigabyte binary checkpoints.
2. **Idempotent Pre-Flight Materialization:** Before executing downstream stages, the orchestrator executes an idempotent hydration step (`restore_frozen_winners`) that copies tracked evidence into `artifacts/` *only if* the runtime path is absent, preserving any freshly computed local search outputs while guaranteeing zero-configuration execution on a fresh clone.

### 2. ShapeSense Verification & Experimental Controls
* **Hydration Hook (`src/common/pipeline_helpers.py` & `run_pipeline.py`):** `restore_frozen_winners()` materializes `artifacts/stage4/tuning_iter2/winners.json` from tracked repository evidence prior to Stage 4 and Stage 6 execution.
* **Clean-Checkout Regression Test (`tests/test_stage6.py`):** Unit tests are a clean checkout by removing the runtime `artifacts/` tuning file, invoking the restoration helper, and asserting that downstream verification passes cleanly.

