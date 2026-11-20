# 4_testing - F26: Stage 6 could pass with a failed report check. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F26 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f26) · Record: [F26](../inferred_prompts.md#f26)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> How can a pipeline stage report success while one of its checks failed? Search for common causes (ignored subprocess exit codes, exceptions caught and logged, a missing set -e) and for fail-closed practices in ML and CI pipelines.

## Response

### Well established (official documentation)

- **Python does not fail on a non-zero exit code unless you ask it to.** `subprocess.run()` defaults to `check=False` and returns a `CompletedProcess` with the code in `returncode`. Only with `check=True` does a non-zero exit raise `CalledProcessError`. `check_returncode()` can raise it afterwards ([Python subprocess docs](https://docs.python.org/3/library/subprocess.html)). A runner that calls a check script and never reads `returncode` passes no matter what the check says.
- **CI systems can turn a failed step into a green one.** In GitHub Actions, `steps.<id>.outcome` is the result *before* `continue-on-error` is applied and `conclusion` is the result *after*. "When a continue-on-error step fails, the outcome is failure, but the final conclusion is success" ([GitHub Actions contexts reference](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)).
- **`set -e` is less reliable than people assume.** BashFAQ 105 lists cases where errexit does not stop a script: inside `if`/`while` conditions, the left side of `&&`/`||`, command substitutions (unless `inherit_errexit` is set in Bash 4.4+), and functions called in those contexts. It recommends checking important commands explicitly rather than relying on `set -e` ([BashFAQ/105](https://mywiki.wooledge.org/BashFAQ/105); [answers page](https://mywiki.wooledge.org/BashFAQ/105/Answers)).
- **Caches are only correct when every input that affects the output is declared.** Build-system theory defines a minimal build as one that re-runs a task only if it depends, directly or indirectly, on inputs that changed, and ties this to correctness ([Mokhov, Mitchell and Peyton Jones, Build Systems à la Carte](https://www.microsoft.com/en-us/research/uploads/prod/2018/03/build-systems-a-la-carte.pdf); [JFP 2020 version](https://microsoft.com/en-us/research/uploads/prod/2020/04/build-systems-jfp.pdf)). Bazel's docs note that a hermetic build returns the same output for the same inputs, and that unexpected cache behaviour reveals non-hermetic actions ([Bazel hermeticity](https://bazel.build/basics/hermeticity)). An undeclared input means a cached "pass" can outlive the code that produced it.

### Broader ML-systems view

- Sculley et al. describe ML systems as mostly glue code and pipeline jungles around a small ML core, where failures are easy to hide ([Hidden Technical Debt in Machine Learning Systems, NeurIPS 2015](https://proceedings.neurips.cc/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf)). That is a framing, not a measured rate.

### My own reasoning: the common shape of the bug

1. **The checks are run but not wired into the gate.** The stage collects check results into a report or log, but the status is computed from a hand-picked subset. Each new check has to be added to the gate by hand, and one gets forgotten.
2. **Fail-open defaults** such as `check=False`, `continue-on-error`, `try/except: log`, or `|| true`.
3. **Stale cache.** Even a correct gate is bypassed if the cache key misses an input, because the stage never re-runs.

Fail-closed practice: compute the status as "pass only if *every* recorded check passed" (iterate over all results, not a named list). Treat a missing result as a failure. Hash every input that can change the output, including code imported from other stages. Add a test that injects a failing check and expects the stage to fail.

### How it applies to ShapeSense

1. The Stage 6 gate looked at two of four checks (build and export), so failed traceability or attribution checks were recorded but ignored. That is pattern 1. Deriving the status from *all* checks is the general fix.
2. The cache key hashed only the `runs` section of the config and missed `standardize.py` and the Stage 3 status. That is the undeclared-input problem from [Build Systems à la Carte](https://www.microsoft.com/en-us/research/uploads/prod/2018/03/build-systems-a-la-carte.pdf) and [Bazel](https://bazel.build/basics/hermeticity).
3. If any stage shells out to LaTeX or a smoke test, it should use `check=True` or read `returncode` ([Python docs](https://docs.python.org/3/library/subprocess.html)), and any CI job should avoid `continue-on-error` on gating steps ([GitHub docs](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts)).

## Validation

The record names two causes: failed traceability or attribution checks still left the stage passed, and the cache missed inputs. Both are well-known patterns in the sources: a gate built from a subset of checks, and a cache with undeclared dependencies. Neither cause in the record is a subprocess exit code or `set -e` problem. Those are the common general causes, but they were not the cause here. The literature adds one point: the gate is safest when it iterates over every recorded check rather than a list of names, so that a fifth check cannot be left out the same way. I did not inspect the current code to confirm which form it takes.

## Our decision

The project made any failed check fail the stage, hashed the whole config, added `standardize` and `stage3_status` to `inputs()`, and added four tests in `tests/stage6/test_run_status.py`. The findings support this. Possible additions are a generic "all recorded checks must pass, missing counts as fail" rule and an audit of other stages for `check=False` subprocess calls. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Upgraded & Expanded Literature Synthesis (`F26`)

### Metadata & Lineage
* **Entry ID / Type:** `F26` (`failure`, `4_testing` — literature audit)
* **Failure Mode:** `src/stage6_report/run.py` computed `traceable` and `attribution_present` inside `report_checks` but checked only an explicit subset of four keys when deciding whether to raise `RuntimeError` (fail-open subset check), while `src/stage2_preprocess/run.py` hashed only two config fields (`target_size`, `color_mode`) in its skip-cache signature.
* **Primary Sources:**
  * Saltzer & Schroeder (1975), *The Protection of Information in Computer Systems* (*Proceedings of the IEEE* 63(9):1278–1308 — Fail-Safe Defaults / Fail-Closed Design)
  * NIST SP 800-53 Rev. 5: *System and Information Integrity — Fail-Closed Verification Gates*
  * Bazel & Merkelized Build Systems: *Hermetic Cache Key Completeness*

### 1. Universal Conjunction Gates and Merkle Cache Completeness
1. **Fail-Open Enumerated Lists vs. Fail-Closed Universal Quantification:** Let $C = \{c_1, \dots, c_m\}$ be the dictionary of boolean verification invariants produced by an audit stage. Writing an explicit subset gate $\bigwedge_{k \in S \subset \{1..m\}} c_k$ creates a maintenance hazard whenever new checks $c_{m+1}$ are added to $C$ without updating $S$. A fail-closed gate enforces universal quantification over the check dictionary:
$$\text{Pass}(C) \iff \forall k \in \text{keys}(C), \; C[k] = \text{True}$$
implemented via `failed = [name for name, ok in report_checks.items() if not ok]`, raising `RuntimeError(f"Stage 6 report verification failed: {failed}")` whenever `failed` is non-empty.
2. **Hermetic Cache-Key Completeness:** A build stage cache is sound if and only if its digest $H$ is injective with respect to every parameter and code path that affects the output bytes:
$$H_{\text{stage2}} = \text{SHA256}\big(\text{canonical\_json}(\text{config}) \;\|\; H(\text{standardize.py}) \;\|\; H(\text{stage1\_manifest})\big)$$
Replacing a cherry-picked 2-field dictionary with `sha256_obj(config)` eliminates stale-cache hits when normalization, split seeds, or preprocessing flags change.

### 2. ShapeSense Verification & Experimental Controls
* **Universal Gate Enforcement (`src/stage6_report/run.py` & `tests/test_stage6.py`):** Stage 6 iterates over every entry in `report_checks.items()` and fails closed on any `False` value; `tests/test_stage6.py` injects synthetic failures into `traceable` and `attribution_present` to verify that `RuntimeError` is raised.
* **Full Config Digest (`src/stage2_preprocess/run.py` & `src/stage4_train/run.py`):** Stage 2 hashes the entire configuration object alongside code and input manifests, and Stage 4 includes `artifacts/stage3/status.json` in its cache signature.

