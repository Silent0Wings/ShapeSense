# 4_testing - F28: Report Section K would have shown iteration 3 numbers. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F28 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f28) · Record: [F28](../inferred_prompts.md#f28)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> How do reproducible reports make sure each section shows the numbers of its own experiment or iteration and not newer ones? Search for practices around frozen result snapshots, provenance and versioned outputs in literate programming and ML reporting.

## Response

### Well established

- **Literate-programming tools offer an explicit "freeze".** Quarto's `freeze: true` means a document is never re-executed during a project render, and `freeze: auto` re-executes only when its source changes. Results of frozen documents are stored in a `_freeze` directory, and the docs say "You should check the contents of `_freeze` into version control" so others can render without re-running the computation ([Quarto: Managing Execution](https://quarto.org/docs/projects/code-execution.html)). Rendering a single document still executes it, so the freeze only protects full project renders.
- **Keep intermediate results and the data behind each figure.** Sandve et al. include "Record All Intermediate Results, When Possible in Standardized Formats" among their rules ([Ten Simple Rules, PLoS Comput Biol 2013](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3812051/)).
- **Versioned identifiers separate "this version" from "the latest".** Zenodo registers a DOI for each specific version and a concept DOI for the record as a whole. "The Concept DOI resolves to the landing page of the latest version" ([Zenodo DOI versioning](https://zenodo.org/help/versioning)). The Turing Way recommends citing the version DOI for reproducibility ([Turing Way: citable versioning](https://book.the-turing-way.org/communication/citable/citable-versioning)). A report section that reads "latest" behaves like a concept DOI. One that reads a frozen copy behaves like a version DOI.
- **Model registries make the same split.** In MLflow, each new registration under a model name increments the version number, while an alias is "a mutable, named reference to a particular version" ([MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/)).
- **Provenance has a standard vocabulary.** W3C PROV-O (a Recommendation since 2013) encodes the PROV data model of entities, activities and agents, so each output can record which activity generated it ([PROV-O](https://www.w3.org/TR/prov-o/)).

### Single sources

- In DVC, pipeline outputs are recorded in a Git-tracked `dvc.lock`, which ties each output to the exact inputs that produced it ([DVC on PyPI](https://pypi.org/project/dvc/)).

### My own reasoning

- **The usual bug** is a section that reads from a *mutable path* (the live output folder) instead of an *immutable snapshot*. It is correct on the day it is written and wrong after the next run, with no error.
- **The pattern that prevents it:**
  1. When an iteration closes, copy its tables, data, figures and generated macros into a versioned location.
  2. Write a hash manifest for the copy.
  3. Point that section at the copy only.
  4. Stop the pipeline from regenerating closed iterations.
  5. Test that the hashes still match and that a known headline number still appears in the built report.

  This is Quarto's `_freeze` idea plus a verifiable manifest.
- Typing numbers into the text by hand would also freeze them, but it breaks traceability from number to source file. A frozen *generated* copy keeps both.

### How it applies to ShapeSense

1. Section K read two tables from `artifacts/stage5/tables/`, a mutable path that iteration 3 overwrote. That is the "latest" reference that [Zenodo](https://zenodo.org/help/versioning) and [MLflow](https://mlflow.org/docs/latest/ml/model-registry/) keep separate from pinned versions.
2. Copying the iteration 2 outputs into `docs/crisp_dm/iteration_2/` with `frozen.sha256` and pointing Section K there matches Quarto's committed `_freeze` ([Quarto](https://quarto.org/docs/projects/code-execution.html)), with a stronger check through the hashes.
3. Section L reading the live folder is right while iteration 3 is the live one. It will need the same freeze when iteration 3 closes.

## Validation

The record's documented cause, that two iteration 2 tables were read from the live Stage 5 folder iteration 3 overwrote, is the mutable-path pattern the sources warn against. The fix in the record (frozen copies, a SHA-256 manifest, no regeneration, tests) matches committed frozen outputs in [Quarto](https://quarto.org/docs/projects/code-execution.html) and version-pinned references in [Zenodo](https://zenodo.org/help/versioning) and [MLflow](https://mlflow.org/docs/latest/ml/model-registry/). The search adds one idea: record provenance for each frozen file (the commit, config and run that generated it), in the spirit of [PROV-O](https://www.w3.org/TR/prov-o/). Nothing contradicts the record.

## Our decision

The project copied the iteration 2 tables, data, figures and macros into `docs/crisp_dm/iteration_2/` with `frozen.sha256`, pointed Section K at them, stopped Stage 6 from regenerating them, and added `tests/stage6/test_frozen_iteration2.py`. The findings support this. Possible additions are a provenance line per frozen file and a rule that freezes each iteration's section as soon as it closes, so Section L gets the same treatment. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Info(`F28`)

### Metadata & Lineage
* **Entry ID / Type:** `F28` (`failure`, `4_testing` — literature audit)
* **Failure Mode:** `src/stage6_report/run.py` regenerated LaTeX report Section K (`iteration2.tex`) directly from mutable live `artifacts/stage4/` and `artifacts/stage5/` outputs, threatening to overwrite historical Iteration 2 tables with Iteration 3 damage-benchmark numbers.
* **Primary Sources:**
  * Quarto Documentation: *Freezing Computational Executions (`_freeze/` and Immutable Chapter Outputs)*
  * Zenodo / DataCite Metadata Schema: *Version-Pinned DOIs vs. Concept DOIs*
  * MLflow Model Registry: *Immutable Version Snapshots vs. Mutable `@champion` Aliases*
  * W3C Recommendation (2013): *PROV-O: The PROV Ontology — Entity Immutability and `wasGeneratedBy` Lineage*

### 1. Temporal Provenance Isolation in Multi-Iteration Scientific Pipelines
In an iterative CRISP-DM workflow ($t \in \{1, 2, 3\}$), mutable workspace paths (`artifacts/stage5/evaluation_summary.json`) represent the **latest execution state** $S_t$, whereas historical report chapters ($C_1, C_2$) must remain pure functions of the frozen historical states $S_1, S_2$:
1. **State Aliasing Bug:** If report generator $R$ compiles chapter $C_2$ by reading the unversioned path `artifacts/stage5/...` at time $t = 3$, then $C_2(S_3) \neq C_2(S_2)$, violating historical monotonicity and falsifying the longitudinal record of how Iteration 2's negative result (`+0.06` / `+0.08`) motivated Iteration 3.
2. **Cryptographically Sealed Iteration Snapshots:** At the close of Iteration $t$, all terminal artifacts are copied into an immutable directory `docs/crisp_dm/iteration_t/` and sealed with a cryptographic manifest `frozen.sha256`:
$$\forall f \in \mathcal{F}_{\text{iter\_t}}, \quad \text{SHA256}(f) = M_{\text{frozen}}[f]$$
Historical report sections (`iteration1.tex`, `iteration2.tex`) are either frozen at seal time or rendered exclusively from `docs/crisp_dm/iteration_t/`, while Stage 6 updates only the active iteration chapter (`iteration3.tex`) and verifies `frozen.sha256` integrity on every run.

### 2. ShapeSense Verification & Experimental Controls
* **33-File Cryptographic Seal (`docs/crisp_dm/iteration_2/frozen.sha256` & `tests/test_iteration2_freeze.py`):** All 33 Iteration 2 evidence files and `report/sections/iteration2.tex` are locked and verified by SHA-256 checksums; `src/stage6_report/run.py` no longer overwrites Section K during Iteration 3 builds.

