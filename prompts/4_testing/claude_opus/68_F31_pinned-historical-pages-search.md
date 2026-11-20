# 4_testing - F31: The page for failure F14 showed iteration 3 numbers. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F31 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f31) · Record: [F31](../inferred_prompts.md#f31)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> How do experiment dashboards keep historical views stable while new runs keep arriving? Search for practices in experiment tracking tools (immutable run records, snapshots per release) and for how a page can be pinned to the frozen record of its own iteration.

## Response

### Well established (official documentation)

- **Immutable versions plus movable aliases.** MLflow's Model Registry increments the version number for each new registration under a name, and an alias is "a mutable, named reference to a particular version". A URI like `models:/MyModel@champion` keeps working while the alias moves ([MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/)). A historical view should use the version, and only the "current" view should use the alias.
- **The same split in research archiving.** Zenodo registers one DOI per version and a concept DOI for all versions. "The Concept DOI resolves to the landing page of the latest version" ([Zenodo DOI versioning](https://zenodo.org/help/versioning)). The Turing Way says to cite the version DOI for reproducibility, because it "never changes" ([Turing Way: citable versioning](https://book.the-turing-way.org/communication/citable/citable-versioning)).
- **Frozen computed output.** Quarto stores the results of frozen documents in `_freeze`, reuses them on later renders, and recommends committing them ([Quarto: Managing Execution](https://quarto.org/docs/projects/code-execution.html)).

### Single sources or unofficial

- For Weights & Biases I could not open the official artifacts page (it now redirects to another domain). Third-party guides say each logged artifact gets a new immutable version (v0, v1, …) while aliases like `latest` or `production` are mutable and move between versions ([W&B Artifacts overview report](https://wandb.ai/wandb/customers/reports/W-B-Artifacts-Overview--VmlldzoxMTE2NjM2Ng)). Treat that as unconfirmed against the current official docs.
- DVC exposes artifacts by name and version through `dvc artifacts get`, so a consumer can pin a version ([DVC data and model access](https://dvc.org/doc/start/data-and-model-access)).

### My own reasoning: pinning a page to its own iteration

1. **Every view carries its own context.** Each failure, chart or section records the iteration it belongs to. That is the "version" in the MLflow and Zenodo sense.
2. **Resolve the data source from that context, not from "latest".** If the view's iteration is the live one, read the live outputs. Otherwise read that iteration's frozen record. That is the alias-vs-version rule.
3. **Fail visibly when the frozen record lacks the data.** Show a note rather than falling back to live data. A silent fallback to "latest" is exactly how the bug returns.
4. **Inputs count too, not only results.** A view whose *computation* runs live (a preview that re-applies current settings) is also unpinned, even if the numbers it shows come from a frozen file. Pinning it means storing the settings of that iteration with the snapshot.
5. **Test it.** For each historical view, compare its headline number to the frozen status file of its iteration. A screen review catches this once. A test catches it every time.

### How it applies to ShapeSense

1. F14's chart read `stage5` (live) and showed iteration 3's +9.20 instead of iteration 2's +0.06 / +0.08. That is a historical view bound to an alias ("latest") instead of a version ([MLflow](https://mlflow.org/docs/latest/ml/model-registry/), [Zenodo](https://zenodo.org/help/versioning)).
2. The fix (`LIVE_ITERATION = 3`, iterations 1 and 2 mapped to `iteration1`/`iteration2`) is points 1 and 2 above. F11 showing a note because no per-epoch log was kept is point 3.
3. The previews on F07, F08 and F10 still run on current settings, which is point 4 and why the entry is "Partly". Storing each iteration's augmentation and render settings with its frozen record would let those previews read their own iteration.
4. `LIVE_ITERATION` is a constant that someone has to bump by hand. Reading it from the iteration log would remove one more chance of drift. That is my suggestion, not taken from the sources.

## Validation

The record's documented cause, a chart that read live results which changed when iteration 3 finished, is the version-vs-latest confusion the sources describe. The recorded fix matches the documented practice of pinning historical references to immutable versions ([MLflow](https://mlflow.org/docs/latest/ml/model-registry/), [Zenodo](https://zenodo.org/help/versioning), [Quarto](https://quarto.org/docs/projects/code-execution.html)). The search adds two points: freeze the *settings* along with the results (which would close the remaining "Partly" gap on F07, F08 and F10), and add an automated check that compares each historical page with `iter1_status.json` / `iter2_status.json` instead of relying on a screen review. Evidence on W&B specifically was thin, because I could not reach the official page.

## Our decision

The project gave each failure its iteration, mapped earlier iterations to their frozen records in `studio/web/js/widgets/failure-visuals.js`, showed a note where the frozen record lacks data (F11), and left the live previews on F07, F08 and F10 marked as a known gap. The findings support this and suggest freezing per-iteration settings for those previews and automating the number check. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Upgraded & Expanded Literature Synthesis (`F31`)

### Metadata & Lineage
* **Entry ID / Type:** `F31` (`failure`, `4_testing` — literature audit)
* **Failure Mode:** `studio/web/js/widgets/failure-visuals.js` read live `status.stage5` (`evaluation_summary.json`) for every failure card, which would have caused historical Iteration 2 failure cards (such as `F14`, where `A2 vs A0` failed at `+0.06` / `+0.08`) to render Iteration 3's passing `+9.20` numbers.
* **Primary Sources:**
  * MLflow Model Registry: *Immutable Version Pinning vs. Mutable Stage/Alias Pointers*
  * Zenodo Versioning Architecture: *Version-Specific Record Identifiers vs. Latest-Version Redirects*
  * Quarto Execution Freeze: *Pinning Historical Visuals Across Iterative Rebuilds*

### 1. Epoch-Scoped Data Binding in Longitudinal Dashboards
Let $\mathcal{E} = \{e_1, e_2, \dots, e_m\}$ be a set of historical failure or decision cards in an interactive scientific dashboard, where each entry $e_i$ occurred during a specific CRISP-DM iteration $\tau(e_i) \in \{1, 2, 3\}$.
1. **Mutable Head Pointer Anti-Pattern:** Binding all visual components to a single mutable head state `status.latest` ($S_{\text{head}} = S_3$) violates temporal referential integrity whenever $\tau(e_i) < 3$. Specifically, for `F14` ($\tau(\text{F14}) = 2$), rendering $S_3$ displays the Iteration 3 damaged-test victory (`+9.20`) inside a card explaining why Iteration 2 failed (`+0.06` on reused test, `+0.08` on `fresh_holdout`).
2. **Iteration-Indexed Snapshot Routing:** By indexing the dashboard data payload by iteration epoch—$\mathcal{S} = \{1: S_1, \; 2: S_2, \; 3: S_3\}$ backed by frozen snapshots `iter1_status.json`, `iter2_status.json`, and live `status.json`—every visual widget resolves its data source via:
$$\text{DataSource}(e_i) = \mathcal{S}[\tau(e_i)]$$
This guarantees that historical failure diagnostics remain invariant under future experimental iterations while live Iteration 3 panels reflect current results.

### 2. ShapeSense Verification & Experimental Controls
* **Iteration-Pinned Visual Resolver (`studio/web/js/widgets/failure-visuals.js`):** Each failure visualization resolves its metrics from the snapshot matching the failure's recorded iteration (`iter1_status.json` for Iteration 1 failures, `iter2_status.json` for Iteration 2 failures like `F14`, and live Iteration 3 status for Iteration 3 analyses).
* **Static Export Verification (`scripts/build_static_site.py`):** The static dashboard builder bundles all frozen iteration snapshots alongside the live Iteration 3 evaluation summary and verifies that historical cards retain their exact frozen numbers.

