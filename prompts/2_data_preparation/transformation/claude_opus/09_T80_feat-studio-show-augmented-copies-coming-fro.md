## 

# 2_data_preparation/transformation - T80: feat(studio): show augmented copies coming from one source image

> **Simulated exchange:** No export of the original chat exists. The prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

- LLM: Claude Opus 5.5, medium effort (simulated reconstruction)
- Category: Two-LLM comparison. Other model's answer: `../gemini_4_neon/10_T80_feat-studio-show-augmented-copies-coming-fro.md`
- Date: 2026-11-10
- Entry: T80 (`built`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40297573 / 40297573
- LLM role: reviewed
- Grounding sources: `results/llm_comparison/commit_tasks.csv` (T80), `studio/server/routes_ops.py`, `studio/server/schemas.py`, `studio/settings.py`, `studio/ops/overrides.py`, `studio/web/js/pages/stage2.js`, commit 33858dc

## Prompt

> I'm adding a view to the studio's augmentation page: pick one real training image and show several augmented copies made from it by the real transform, so people can see what the settings do. Can you review the plan? What should the page show, what should the endpoint accept, and what could go wrong with data access?

## Response

The plan is good. A grid of copies from one source is the clearest way to show that augmentation creates variety around a single drawing, not new drawings. A few points before you build it.

### Use the real transform, not a copy of it

The endpoint should build the transform from the tuned config with the slider values merged in, and validate the result with the same config checker the pipeline uses. If the studio reimplements rotation or shear, the picture can drift from what training does, and then the page misleads.

### What the page should show

- The original image, large, with its source id. The source id matters: augmented copies of one image are near duplicates, and seeing the source makes that obvious.
- N copies, each an independent draw with the same seed sequence, so "New random draw" changes them and a refresh does not.
- The per-class rotation cap, stated in words when the chosen class has one ("capped at ±10°").
- For classes where shear or non-uniform scale is disabled, grey out those sliders with a reason, instead of hiding them.
- Optionally an "uncapped" toggle, so a reviewer can see the turned squares that the cap prevents. That makes F07 visible.

### Endpoint contract

- Inputs: class label, image index within the class, seed, number of copies, slider values, uncapped flag.
- Bound `n` with a schema maximum, and bound every slider to the ranges the search used, so a request cannot ask for a pathological transform.
- Return base64 PNGs plus the source id.

### Data access: the part I'd be strict about

- Augmentation runs on the training side only, so read the source image from the train split and nothing else. Make the split a server-side constant, not a request field.
- Any browse endpoint that takes a split should reject anything outside train and val before a file is opened. The test split should never be viewable from the studio, even locally, or it becomes easy to "tune by eye" on test images.
- Keep the server bound to localhost.

### Checks

- A test that the endpoint returns `n` images of 64 x 64 and the right source id.
- A test that a capped class with uncapped = false never exceeds its cap.
- A test that asking for the test split returns 403.

## Validation

`commit_tasks.csv` lists T80 as built, with both LLMs in a `reviewed` role and no test or metric recorded. In the current studio code, `/api/augment` (`studio/server/routes_ops.py`) reads from `AUGMENT_SPLIT = "train"` (`studio/settings.py`), the request schema bounds `n` by `MAX_VARIANTS` and has an `uncapped` flag (`studio/server/schemas.py`), and browse routes reject splits outside train and val. I did not read the diff of commit 33858dc, so which of these parts that commit added is not confirmed here.

## Our decision

Feature built as in commit 33858dc. The page in `studio/web/js/pages/stage2.js` shows the original with its source id, independent draws, and the rotation cap for the chosen class.

## Measured effect

No measured effect recorded in the repo. This is a display feature with no metric.

## Deeper detail: why the real transform matters

### The real transform, not a copy

| Approach | Risk | Verdict |
|---|---|---|
| Reimplement transform in studio | Picture drifts from training | Reject |
| Build from tuned config + sliders | Picture matches training | Adopt |

- **Why the real transform matters:** if the studio reimplements it, the picture can drift.
- **Why the config checker matters:** it validates the merged result.
- **Why this is a good design:** it's consistent with the training pipeline.

### The page shows the right things

| Element | Why it matters |
|---|---|
| Original + source id | Shows the copies are near-duplicates |
| N independent draws | Shows the variety |
| Rotation cap in words | Makes the cap visible |
| Greyed-out sliders | Explains why they're off |
| Uncapped toggle | Makes F07 visible |

- **Why these elements matter:** they make the augmentation behavior visible and explainable.
- **Why this is a good design:** it's educational.

### Data access is strict

| Rule | Why |
|---|---|
| Train split only | Augmentation runs on training side |
| Reject test split | Prevents "tune by eye" on test |
| Localhost only | Limits exposure |

- **Why data access is strict:** it prevents leakage and misuse.
- **Why this is a good design:** it's consistent with the fail-closed pattern.

### Cross-reference to the rest of the pipeline

| Entry | What it builds on | How |
|---|---|---|
| F07 (rotation cap) | T80 | The uncapped toggle makes F07 visible |
| S07 (class definitions) | T80 | The per-class cap is from S07 |
| C04 (other augmentation) | T80 | The sliders are the searched values |
| C08 (generator ranges) | T80 | The generator is separate from the transform |

- **Why this matters:** T80 is a display feature that makes the augmentation behavior visible, building on F07, S07, C04, and C08.

## Notes on the log

- **This is a `simulated reconstruction`, not a saved chat.** The prompt and response are imagined, grounded in the repo.
- **The real transform matters.** A copy would drift.
- **The page shows the right things.** They make the behavior visible and explainable.
- **Data access is strict.** It prevents leakage and misuse.
- **Cross-reference to F07, S07, C04, C08:** T80 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.