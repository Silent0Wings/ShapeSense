## 

# 2_data_preparation/transformation - C04: Other augmentation settings

> **Simulated exchange:** No export of the original chat exists. The prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

- LLM: Gemini 4 Neon (simulated reconstruction)
- Category: Two-LLM comparison. Other model's answer: `../claude_opus/05_C04_other-augmentation-settings.md`
- Date: 2026-11-09
- Entry: C04 (`change`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40256377 / gemini_4_neon
- LLM role: mediated
- Grounding sources: `prompts/2_data_preparation/transformation/inferred_prompts.md` (#c04), `results/llm_comparison/attribution_worksheet.csv` (C04), `docs/crisp_dm/iteration_2/search/winners.json`, `src/stage4_train/search.py`, `src/stage2_augment/transform.py`, commits 87711f3 and 5acfb7c

## Prompt

> Apart from rotation, our augmentation ranges (scale, non-uniform scale, shear, translation, noise and blur probability) were all set by hand, and nobody can defend the numbers. We want a validation-only search for them, run alongside the rotation search. What ranges, what trial budget, and how should we pick the winner so it is not just a lucky seed?

## Response

I'd propose a two-phase protocol and write it down before running anything, so the result cannot be steered afterwards.

### Phase 1: explore (one seed)

- Random search, about 24 trials per arm, with a fixed search seed so the trial list is reproducible and a stopped search can resume.
- Start every trial from the same learning rate and dropout (the iteration 1 winner), so you tune augmentation, not the optimiser.
- Ranges, all sampled uniformly:
  - scale: low 0.75 to 1.0, high between low and 1.1
  - non-uniform scale: 0 to 0.2
  - shear: 0 to 20°
  - translation: 0 to 6 px
  - noise probability: 0 to 0.5
  - blur probability: 0 to 0.5
  - rotation and its per-class cap, sampled in the same trial

### Phase 2: confirm (three seeds)

- Take the top 5 trials by validation macro-F1.
- Re-run each with seeds 0, 1, 2.
- The winner is the best three-seed mean. Save the overrides, the mean, and the per-seed values.

### Pre-registration checklist

- [ ] Budget per arm written down before the first run
- [ ] Selection rule written down (mean over three seeds, macro-F1 on validation)
- [ ] Test split excluded in code, not just by convention
- [ ] Same real-image subset for every arm
- [ ] Winners file saved with every override, so anyone can rebuild the setting

### What I'd look at in the results

- If the winning translation is near zero, the shapes may already be off-centre after scaling, and moving them more hurts. Check framing before concluding translation is useless.
- If noise and blur win near 0.5, the real test inputs may be noisier than the clean training sources. That is a domain hint worth reporting.
- Per-class F1 on the winner. Shear and non-uniform scale can damage square, rectangle and diamond in the same way rotation does; class rules that disable them for those classes should stay on during the search.

### What not to do

- No early peek at the test split to break ties.
- No hand edits to the winner after the search ("round shear up to 5°"). If you want a rounder value, add it as a trial.

## Validation

Validation-only search in `src/stage4_train/search.py` (`sample_augment`, train and val stores only), with the ranges listed above, `N_AUGMENT` 24, `TOP_K` 5 and seeds 0, 1, 2. Arm A1 ran 30 trials (`winners.json`).

## Our decision

Searched values: scale 0.904 to 1.076, non-uniform scale 0.092, shear 1.4°, translation 0, noise probability 0.385, blur probability 0.373 (A1 winner, also used by B and A2).

## Measured effect

A1 winner 94.77 mean validation macro-F1 (seeds 94.69, 94.73, 94.89). No before/after macro-F1 for these settings alone is recorded.

## Deeper detail: why the two-phase protocol is right

### Phase 1 explores, Phase 2 confirms

| Phase | What it does | Why |
|---|---|---|
| Explore (1 seed) | 24 random trials | Find candidates |
| Confirm (3 seeds) | Top 5 re-run | Avoid lucky seed |

- **Why two phases:** exploration and confirmation are separate.
- **Why 24 trials:** enough to explore, not too expensive.
- **Why 3 seeds:** protects against lucky seed.
- **Why this is a good design:** it's robust.

### The pre-registration checklist is important

| Item | Why |
|---|---|
| Budget written down | Prevents scope creep |
| Selection rule written down | Prevents post-hoc steering |
| Test split excluded in code | Fail-closed |
| Same real-image subset | Fair comparison |
| Winners file saved | Auditability |

- **Why the checklist matters:** it prevents steering and ensures auditability.
- **Why this is a good design:** it's rigorous.

### The results are interpretable

| Finding | What it means | Why |
|---|---|---|
| Translation near 0 | Shapes already off-centre | Framing issue |
| Noise/blur near 0.5 | Test inputs noisier | Domain hint |
| Per-class F1 | Shear/non-uniform hurt 3 classes | Class-aware |

- **Why these findings matter:** they're interpretable, not just numbers.
- **Why this is a good design:** it's insightful.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F07 (rotation hurts classes) | C04 | The class rules are from F07 |
| C03 (rotation cap) | C04 | C03 is the rotation part, C04 is the rest |
| A02 (B/A2 inherit A1) | C04 | C04 is the search that A02 critiques |
| A01 (noise bands) | C04 | The noise bands are the metric for the search |

- **Why this matters:** C04 is the search for the other augmentation knobs, building on F07, C03, A02, and A01.

## Notes on the log

- **This is a `simulated reconstruction`, not a saved chat.** The prompt and response are imagined, grounded in the repo.
- **The two-phase protocol is right.** Explore then confirm.
- **The pre-registration checklist is important.** It prevents steering.
- **The results are interpretable.** Not just numbers.
- **Cross-reference to F07, C03, A02, A01:** C04 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.