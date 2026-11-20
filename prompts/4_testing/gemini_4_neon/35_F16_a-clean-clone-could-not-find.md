# 4_testing - F16: A clean clone could not find the tuning result
- LLM: Gemini 4 Neon (simulated comparison answer)
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/35_F16_a-clean-clone-could-not-find-the-tuning-resu.md](../claude_opus/35_F16_a-clean-clone-could-not-find-the-tuning-resu.md)
- Date: 2026-11-09
- Entry: F16 (`failure`, `deployment (not a course stage)`)
- Owner / Proposed by: 40304911 / opus_medium_5.5 + 40304911
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md, run_pipeline.py, tests/stage0/test_runner.py, src/stage6_report/run.py, src/stage6_report/iteration2.py, docs/crisp_dm/iteration_2/search/winners.json, commit 3a5a3b3

> **Simulated exchange:** The worksheet credits Opus 5.5 for this entry, and Gemini 4 Neon was not part of it at the time. This is an imagined Gemini 4 Neon answer to the same prompt, for the two-LLM comparison. The response is imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt

> **User:** On a clean clone, the pipeline fails because `artifacts/` is gitignored and Stages 4 and 6 expect `artifacts/stage4/tuning_iter2/winners.json`. How do we make a fresh clone reproduce the full pipeline without rewriting the frozen Stage 4 code?

## Response
The cause is a gap between what is committed and what the stages read. The search result is committed, as a frozen copy under `docs/crisp_dm/iteration_2/search/winners.json`, but Stages 4 and 6 read the working copy under `artifacts/stage4/`, and `artifacts/` is ignored by Git. On any machine that ran the search the file exists, so the gap never shows. On a fresh clone it is missing and Stage 4 fails.

There are three ways to close it:

| Option | Effect | Trade-off |
|---|---|---|
| Rerun the search on every fresh clone | Always self-contained | Hours of GPU time, and a rerun on other hardware may not pick the same winners, so it is not a reproduction |
| Commit `artifacts/` | Nothing to restore | Large binary outputs in Git, and every run dirties the repository |
| Restore the committed copy into `artifacts/` when it is absent | Fresh clone runs the same settings | One small, explicit step in the runner |

I recommend the third. In `run_pipeline.py`, after the guards pass and before any stage runs, copy the committed winners to the path Stages 4 and 6 read, but only if no file is there:

```python
def restore_frozen_winners(artifacts: Path, source: Path) -> bool:
    """Copy the committed search result to where Stages 4 and 6 read it, if absent."""
```

The "only if absent" part matters. A machine that has just run the search keeps its own result, so the restore can never overwrite fresh work with an older copy. It also means the restore cannot quietly change a result: the committed file is the same search output the main run used.

Two further points:
- Add a unit test with a temporary folder: the copy happens when the target is missing, and an existing target is left untouched.
- Then repeat the fresh-clone rehearsal end to end and compare the outputs with the main run. Stage 6 hashes the winners file among its inputs, so a mismatch would show up as a changed cache key rather than a silent difference.

This does not touch any sealed data or any evaluation rule, so there is no pre-registration concern. It only makes the recorded search result reachable.

## Validation
`tests/stage0/test_runner.py::test_frozen_winners_restored_only_when_absent` checks both cases: the restore copies the committed file when the target is missing, and it returns False and leaves an existing file unchanged. The iteration log records that the rehearsal then reproduced every result. In the current repository the constant `FROZEN_WINNERS` points at the iteration 3 copy, `docs/crisp_dm/iteration_3/search/winners.json`.

## Our decision
`run_pipeline.py` restores the committed copy when it is absent (commit 3a5a3b3). The rehearsal then reproduced every result. State: Overcome.

## Measured effect
Fresh clone: Stage 4 failed on a missing tuning result -> all seven stages pass with the same results as the main run. No separate timing or numeric comparison is recorded.

---

## Upgraded & Expanded Technical Analysis (`F16`)

### 1. The Committed-vs.-Working-Copy Projection Gap
In ShapeSense's repository layout, `artifacts/` is excluded via `.gitignore` (to keep multi-megabyte model binaries and transient logs out of Git), whereas frozen CRISP-DM decision records are committed under `docs/crisp_dm/iteration_*/search/winners.json`.
- **Why the Bug Is Invisible on the Authoring Machine:** On the workstation that executed the offline hyperparameter search, `artifacts/stage4/tuning_iter2/winners.json` remains on disk across subsequent runs, masking the fact that Stages 4 and 6 depend on an untracked path.
- **Why Re-Running the Search Violates Reproducibility:** Re-executing a multi-hour GPU search on a fresh clone can select different hyperparameter winners under different GPU hardware/driver stacks, turning a *reproduction* of the committed experiment into a *new experiment*.

### 2. Monotone Idempotency of `restore_frozen_winners` & Cache-Key Sensitivity
```python
def restore_frozen_winners(artifacts: Path, source: Path) -> bool:
    """Copy the committed search result to where Stages 4 and 6 read it, if absent."""
```
- **"Only-If-Absent" Monotonicity:** Checking `if target.is_file(): return False` before copying guarantees that a machine actively running a new tuning search never has its fresh working output overwritten by the frozen baseline, while a clean checkout deterministically materializes the exact byte-for-byte `winners.json` (`FROZEN_WINNERS`).
- **Stage 6 Hash Verification:** Because `src/stage6_report/run.py#inputs(config)` hashes `winners.json` via `sha256_path`, restoring the exact committed bytes ensures the Stage 6 input signature matches the primary run without triggering a spurious cache miss (`test_frozen_winners_restored_only_when_absent`).


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** "a rerun is not a reproduction." A rerun on this machine reproduces the winners on this machine, not the run, which includes hardware, BLAS version and seed. Only restoring the committed `winners.json` reproduces the selection, and the "only if absent" condition makes that restore safe on a machine that has just run the search.

**Changelog:** [1] rejection of option 1 rests on "a rerun is not a reproduction"; [2] `FROZEN_WINNERS` is iteration-specific, and the code confirms it points at `docs/crisp_dm/iteration_3/search/winners.json`; [3] the restore changes access, not content, which is the scope argument for why no pre-registration is affected.

**Open questions:** Is there a test that fails when `FROZEN_WINNERS` and the current iteration in `configs/pipeline.yaml` disagree? Without one, a future fresh clone restores the wrong winners silently. Is the restore included in the cache key? If not, a run that restored winners and one that did not could share a key.
