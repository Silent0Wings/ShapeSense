# 4_testing - C56: Final audit on 2026-11-10

> **Reconstructed.** This file is not the original chat. Real Claude Opus 5.5 exchange covering this entry: [52_real_is-the-project-done-and-final-audit.md](52_real_is-the-project-done-and-final-audit.md)
- LLM: Claude Opus 5.5, medium effort 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-10
- Entry: C56 (`change`, `deployment (not a course stage)`)
- Owner / Proposed by: 40297573 / opus_medium_5.5
- LLM role: proposed
- Grounding sources: results/llm_comparison/attribution_worksheet.csv, results/phase2_snapshot/iteration_log.json, prompts/4_testing/inferred_prompts.md, stages/stage_7.md, README.md, results/phase2_snapshot/status5.json, docs/crisp_dm/iteration_1/data/test_reads.csv, docs/crisp_dm/iteration_2/data/test_reads.csv, commit f3b3bdb

> **Simulated exchange:** No export of the original Claude Opus chat exists. The user prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file.

## Prompt
Iteration 3 is closed and the screen review fixes are in, but nobody has checked the project as a whole since then. Before anyone talks about deploying it publicly, can you audit everything: tests, guards, stage status and caches, the test access log, the shipped model, the README, and the Stage 7 publishing gates? Tell me what passes and what is still open.

## Response
I would run the audit in a fixed order, from the cheapest mechanical checks to the gates that need a person, and record each result with its evidence. Proposed checklist:

| # | Check | How | Pass condition |
|---|---|---|---|
| 1 | Full test suite | `pytest` on the whole `tests/` tree | Every test passes, none skipped without a reason |
| 2 | Both guards | `run_pipeline.py --check` (import-linter and the contract tests) | Both report true |
| 3 | Stage status and caches | Read every `artifacts/stage*/status.json`, then rerun the pipeline | All seven stages `passed`, and the rerun is served from cache |
| 4 | Sealed-data reads | Compare the test access log with the expected reads per iteration | No read since the iteration 3 sealed run |
| 5 | Shipped model | Hash the exported model and compare it with the A2 export | Byte-for-byte identical |
| 6 | Documentation | Read the README against what the studio actually offers | No feature listed as future work that already exists |
| 7 | Stage 7 gates | Check G1 to G4 against `stages/stage_7.md` | Each gate with its evidence |

Notes on the parts that need care:

- **Item 3:** a stage served from cache proves its inputs have not changed since it passed. A stage that reruns during an audit is a finding in itself.
- **Item 4:** the expected total is the sum of the per-iteration counts: 13 in iteration 1, 52 in iteration 2 and 92 in iteration 3. Any extra read after the sealed run would mean something touched the test data after the verdict.
- **Item 5:** compare hashes, not file sizes or a quick prediction. The point is that the public model is exactly the one the verdict describes.
- **Item 6:** the README still describes the equal-weight "All models vote" option as future work, but it exists in the studio now. That is a one-line fix and should say there is no claimed accuracy for the vote.

**The gates.** G1 (work complete) and G2 (metrics pass) can be checked from files: G2 reads the closing iteration's primary verdict as written, which is pass (A2 vs A0, +9.20, CI [8.89, 9.53]). G3 and G4 cannot be closed by me:

- **G3 License:** the team has to choose a license for its own code and model weights, and confirm that every image shown publicly is allowed by its source's license.
- **G4 User approval:** `stages/stage_7.md` says it plainly: "G4 cannot be inferred. A finished task or a passing test run is not approval." It needs written approval for a named commit.

So my expected outcome is "complete, but not yet publishable": record G3 and G4 as open rather than marking the stage done.

## Validation
The audit result is recorded in `results/phase2_snapshot/iteration_log.json` (change "Final audit on 2026-11-10", commit f3b3bdb). `README.md` now reads: 'The studio also offers an equal-weight "All models vote" option'. The per-iteration read counts are in `docs/crisp_dm/iteration_1/data/test_reads.csv` (13), `docs/crisp_dm/iteration_2/data/test_reads.csv` (52) and `status5.json` (`test_reads` 92 of 92).

## Our decision
Adopted as proposed: the solution should be confirmed complete before any public deployment. The README was corrected, and G3 and G4 were left open.

## Measured effect
- All 535 tests and both guards pass, all seven stages are passed and cached.
- The test access log is unchanged at 157 reads.
- The shipped model is the A2 export byte for byte.
- README: "All models vote" listed as future work -> listed as existing.
- Stage 7: G1 and G2 hold; G3 (a license for the team's code and weights) and G4 (the user's written approval to publish) are still open.

---

## Expanded & Upgraded: Complexity, Logic Depth, and Cross-Document Synthesis (`C56`)

### The audit as a publishability predicate

Define $\text{Publishable} = G_1 \land G_2 \land G_3 \land G_4$. The audit evaluates each gate with evidence:
- **$G_1$ (work complete):** all 535 tests pass, both guards pass, all 7 stages passed and cached $\rightarrow$ `true`.
- **$G_2$ (metrics pass):** the closing iteration's primary verdict as written is pass (`+9.20 [8.89, 9.53]`) $\rightarrow$ `true`.
- **$G_3$ (license):** team must choose a license for code *and weights*, and confirm every public image is license-permitted $\rightarrow$ **cannot be closed by an LLM** (legal/organizational decision).
- **$G_4$ (user approval):** `stage_7.md`: *"G4 cannot be inferred. A finished task or a passing test run is not approval."* Needs written approval for a named commit $\rightarrow$ **cannot be closed by an LLM.**

So $\text{Publishable} = \text{true} \land \text{true} \land G_3 \land G_4$ = **false until a human closes $G_3/G_4$.** The expected outcome is `"complete, but not yet publishable"` — recording $G_3/G_4$ as open rather than marking the stage done.

### Cache-as-evidence & read-log chain of custody

- **Cache-as-evidence:** a stage served from cache proves its inputs have not changed since it passed (using `F26`'s cache-key completeness invariant as an *audit instrument*).
- **Read-log arithmetic:** expected = `13` (Iter 1) + `52` (Iter 2) + `92` (Iter 3) = **`157`**. The access log is at `157` and unchanged $\rightarrow$ zero post-verdict reads.
- **README drift fix:** `"All models vote"` was updated from future work to existing, explicitly noting `"no claimed accuracy for the vote"` (`F30`/`C40` discipline).

