# 4_testing - F28: Report Section K would have shown iteration 3 numbers
- LLM: Gemini 4 Neon (simulated comparison answer)
- Category: Two-LLM comparison. Same prompt, word for word, as the Opus 5.5 file [../claude_opus/37_F28_report-section-k-would-have-shown-iteration.md](../claude_opus/37_F28_report-section-k-would-have-shown-iteration.md)
- Date: 2026-11-09
- Entry: F28 (`failure`, `deployment (not a course stage)`)
- Owner / Proposed by: 40211352 + 40253714 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md, phase2_report.tex, src/stage6_report/iteration2.py, docs/crisp_dm/iteration_2/frozen.sha256, docs/crisp_dm/iteration_2/tables/, tests/stage6/test_frozen_iteration2.py, commits d12a48e, 4091dab

> **Simulated exchange:** The worksheet credits Opus 5.5 for this entry, and Gemini 4 Neon was not part of it at the time. This is an imagined Gemini 4 Neon answer to the same prompt, for the two-LLM comparison. The response is imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt

> **User:** Once Iteration 3 runs and overwrites `artifacts/stage5/`, will the Iteration 2 tables and numbers in report Section K silently change? Where is each Section K input actually reading from right now?

## Response
Yes, two of them would have changed. I went through every `\input` in Section K of `phase2_report.tex`.

**What was safe.** The iteration 2 macros, the iteration log, the failures and the changes lists are input from `docs/crisp_dm/iteration_2/report/` (`iteration2_facts.tex`, `iteration_log.tex`, `failures.tex`, `changes.tex`). Those are frozen copies and are listed in `docs/crisp_dm/iteration_2/frozen.sha256`.

**What was not.** The two tables at the end of Section K, the iteration 2 comparisons on the reused test split and the iteration 2 per-class F1 on the fresh holdout, were input from the live Stage 5 tables folder. Iteration 3 writes its own comparisons and per-class tables into that folder. After the iteration 3 run, Section K would have printed iteration 3 numbers under an iteration 2 caption. The surrounding text would still quote the frozen iteration 2 macros, so the section would contradict itself, and nothing would fail loudly.

**Fix.** Point both tables at the frozen copies:

```latex
\input{docs/crisp_dm/iteration_2/tables/comparisons.tex}
\InputIfFileExists{docs/crisp_dm/iteration_2/tables/fresh_per_class.tex}{}{--}
```

Both files already exist under `docs/crisp_dm/iteration_2/tables/` and are covered by `frozen.sha256`, so this changes no number in the current report. It only stops the next run from changing them.

**A guard so it stays fixed.** Add a test that recomputes the SHA-256 of every file listed in `frozen.sha256` and compares it with the recorded hash. Then any edit to the iteration 2 record, by hand or by a script, fails the test suite.

| Option | Effect | Trade-off |
|---|---|---|
| Read frozen copies, plus a hash test | Section K fixed for good | None found |
| Have Stage 5 write per-iteration folders | Also solves it | Changes Stage 5 outputs during an iteration, more moving parts |
| Rebuild the iteration 2 tables from a saved status | Same numbers | Duplicates logic that already ran |

Two things to keep apart. The iteration 2 record must not be regenerated or "refreshed" from iteration 3 code, even if the format improves; it was the input to a closed verdict. And the iteration 3 section should keep reading the live folder, because that is where its sealed results land.

## Validation
`tests/stage6/test_frozen_iteration2.py::test_every_frozen_file_matches_its_recorded_hash` checks every file in `docs/crisp_dm/iteration_2/frozen.sha256`, including `data/comparisons.csv`, `data/fresh_per_class.csv` and the `report/*.tex` files. In the current report both Section K tables read `docs/crisp_dm/iteration_2/tables/`, while the iteration 3 table in Section L reads `artifacts/stage5/tables/robust_comparisons.tex`.

## Our decision
Both tables now read the frozen iteration 2 copies, and the iteration 2 record stays as it was (commits d12a48e and 4091dab). State: Overcome.

## Measured effect
Section K source: live Stage 5 tables -> frozen iteration 2 tables. The iteration 2 numbers in Section K are unchanged, for example A2 vs A0 +0.1, CI [-0.7, 0.8] on the reused test split.

---

## Upgraded & Expanded Technical Analysis (`F28`)

### 1. Per-`\input` Provenance Audit & The "Silent Contradiction" Mechanism
Auditing every file inclusion inside Section K (Iteration 2) of `phase2_report.tex` revealed a split-source hazard:

| Section K Inclusion | Original Path Before `d12a48e` | Behavior When Iteration 3 Runs Stage 5 | Post-Fix Frozen Path |
|---|---|---|---|
| Iteration 2 macros (`iteration2_facts.tex`) | `docs/crisp_dm/iteration_2/report/iteration2_facts.tex` | Safe (frozen in `frozen.sha256`, quotes `+0.06` / `+0.08`) | Unchanged (`docs/crisp_dm/iteration_2/report/...`) |
| Iteration log, failures, changes | `docs/crisp_dm/iteration_2/report/{iteration_log,failures,changes}.tex` | Safe (frozen in `frozen.sha256`) | Unchanged (`docs/crisp_dm/iteration_2/report/...`) |
| **Reused-test comparisons table** | `artifacts/stage5/tables/comparisons.tex` (**mutable live folder**) | **Overwritten** by Iteration 3's 60-epoch / 5-arm table | `docs/crisp_dm/iteration_2/tables/comparisons.tex` |
| **Fresh-holdout per-class F1 table** | `artifacts/stage5/tables/fresh_per_class.tex` (**mutable live folder**) | **Overwritten** by Iteration 3 outputs | `docs/crisp_dm/iteration_2/tables/fresh_per_class.tex` |

- **Why the Contradiction Is Silent:** Because the prose in Section K expands `\Itwo*` macros from the frozen `iteration2_facts.tex` (`+0.06`, `fail`) while the two `\input` tables read from live `artifacts/stage5/tables/`, running Iteration 3 would produce a PDF whose Section K text states Iteration 2 failed at `+0.06` right next to an Iteration 2-captioned table displaying Iteration 3's numbers — with zero LaTeX errors and zero hash-test failures.

### 2. Prevention + Detection Architecture ("Freeze What Is Closed, Read Live What Is Current")
1. **Prevention (Path Isolation):** Repointing both Section K `\input` statements to `docs/crisp_dm/iteration_2/tables/` decouples closed Iteration 2 chapters from live `artifacts/stage5/`, while Section L (Iteration 3) continues reading live `artifacts/stage5/tables/robust_comparisons.tex`.
2. **Detection (`test_every_frozen_file_matches_its_recorded_hash`):** `tests/stage6/test_frozen_iteration2.py` recomputes the SHA-256 of every file listed in `docs/crisp_dm/iteration_2/frozen.sha256` (including `tables/comparisons.tex` and `tables/fresh_per_class.tex`), failing the test suite immediately if any script or hand edit alters the historical Iteration 2 record.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the audit method is the deliverable. The entry enumerates every `\input` in Section K and classifies each as frozen or live, which is a complete read-path audit, not a spot check. A fix that only repairs "the table that looked wrong" misses the next one.

**Changelog:** [1] "enumerate every `\input`" as the audit method; [2] the `--` fallback conflates "file never existed" with "file was moved"; [3] completeness of the folder audit: does `docs/crisp_dm/iteration_2/tables/` hold tables Section K should also read frozen?; [4] Stage 5 stays single-purpose, which is why per-iteration folders were rejected.

**Open questions:** Does the hash test run on every commit, or only inside Stage 6? A stage-level check misses an edit made after Stage 6. The test belongs at suite level. Also, the measured effect quotes `+0.1, CI [-0.7, 0.8]`; that is a one-decimal rounding of the recorded `+0.06, CI [-0.69, 0.83]`. Quote the exact recorded figures so there is only one visible source.
