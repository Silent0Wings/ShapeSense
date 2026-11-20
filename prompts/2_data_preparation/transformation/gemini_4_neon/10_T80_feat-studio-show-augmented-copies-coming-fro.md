## Expanded entry

# 2_data_preparation/transformation - T80: feat(studio): show augmented copies coming from one source image

> **Simulated exchange:** No export of the original chat exists. The prompt and the response below are imagined, grounded in the committed ShapeSense repository and the attribution worksheet. Every number comes from a repository file. A Google Drive search for the original transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

- LLM: Gemini 4 Neon (simulated reconstruction)
- Category: Two-LLM comparison. Other model's answer: `../claude_opus/09_T80_feat-studio-show-augmented-copies-coming-fro.md`
- Date: 2026-11-10
- Entry: T80 (`built`, `2_data_preparation/transformation`)
- Owner / Proposed by: 40297573 / 40297573
- LLM role: reviewed
- Grounding sources: `results/llm_comparison/commit_tasks.csv` (T80), `studio/server/routes_ops.py`, `studio/server/schemas.py`, `studio/settings.py`, `studio/ops/overrides.py`, `studio/web/js/pages/stage2.js`, commit 33858dc

## Prompt

> I'm adding a view to the studio's augmentation page: pick one real training image and show several augmented copies made from it by the real transform, so people can see what the settings do. Can you review the plan? What should the page show, what should the endpoint accept, and what could go wrong with data access?

## Response

I'd focus the review on the user's question the page answers: "if I move this slider, what happens to my training data?" Everything on the page should serve that.

### Layout suggestion

- Left: the controls (one slider per augmentation setting, defaulting to the tuned config values), plus three buttons: new random draw, next image, reset to config.
- Right: the original image, then a grid of copies. Draw a thin line from the original to each copy, so it reads as "one source, many copies" at a glance.
- Under the grid, one status line: the source id, "each tile is an independent draw", and the class's rotation cap if it has one.

### Interaction details

- Keep the scale sliders ordered: if low passes high, move the other one.
- When the class has shear or non-uniform scale switched off, disable those sliders and say why ("it would change the label"). Sending zeros for those keys from the client is fine, but the server should enforce the class rule too.
- Only one request in flight at a time; drop stale responses when sliders move fast.

### Endpoint

| Field | Rule |
|---|---|
| label | class id, 0 to 9 |
| index | which image of that class |
| seed | integer, so a draw is reproducible |
| n | 1 to a fixed maximum |
| values | every slider, typed and range-checked |
| uncapped | optional, shows what the per-class cap prevents |

Merge the values into the tuned config and run the config validator before augmenting.

### Data access risks

1. **Test leakage by eye.** If the page can browse test images, someone will adjust settings until test shapes "look right". Fix the augment source to the train split on the server, and reject any other split in browse routes with a 403 before opening a file.
2. **Remote access.** A local tool should accept only localhost hosts and JSON requests.
3. **Payload size.** Cap `n` and the request body, since every copy is a PNG in the response.

### How to check it

- Server tests: correct count and size of images; 403 on a test-split request; 422 on an out-of-range slider.
- A manual check on a square with and without the cap, to confirm the picture matches F07's story.

## Validation

`commit_tasks.csv` records T80 as built, LLM role `reviewed`, no test or metric listed. Current code: `/api/augment` reads from the train split only (`AUGMENT_SPLIT` in `studio/settings.py`), `n` is bounded by `MAX_VARIANTS` and `uncapped` is a request flag (`studio/server/schemas.py`), browse routes allow only train and val, and the host list is localhost only. The diff of commit 33858dc was not read, so which parts it introduced is not confirmed here.

## Our decision

Feature built as in commit 33858dc (`studio/web/js/pages/stage2.js`: original with source id, independent draws, rotation cap note).

## Measured effect

No measured effect recorded in the repo.

## Deeper detail: why the page answers the user's question

### The page answers "what happens to my training data?"

| Element | What it answers | Why |
|---|---|---|
| Sliders | What each setting does | Direct answer |
| Original + copies | One source, many copies | Shows the variety |
| Status line | Source id + cap | Context |

- **Why the page answers the question:** everything serves it.
- **Why this is a good design:** it's user-centered.

### The interaction details are thoughtful

| Detail | Why |
|---|---|
| Ordered sliders | Low can't pass high |
| Disabled sliders with reason | Explains why |
| One request in flight | No stale responses |

- **Why these details matter:** they make the page usable.
- **Why this is a good design:** it's polished.

### The endpoint is well-specified

| Field | Rule | Why |
|---|---|---|
| label | 0-9 | Valid class |
| index | Which image | Valid source |
| seed | Integer | Reproducible |
| n | 1 to max | Bounded |
| values | Typed + range-checked | Safe |
| uncapped | Optional | Shows the cap |

- **Why the endpoint is well-specified:** it's typed and range-checked.
- **Why this is a good design:** it's safe.

### Data access is strict

| Risk | Fix | Why |
|---|---|---|
| Test leakage by eye | Train split only + 403 | Prevents tuning on test |
| Remote access | Localhost + JSON only | Limits exposure |
| Payload size | Cap n + body | Prevents abuse |

- **Why data access is strict:** it prevents leakage and misuse.
- **Why this is a good design:** it's fail-closed.

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
- **The page answers the user's question.** Everything serves it.
- **The interaction details are thoughtful.** They make the page usable.
- **The endpoint is well-specified.** It's typed and range-checked.
- **Data access is strict.** It prevents leakage and misuse.
- **Cross-reference to F07, S07, C04, C08:** T80 builds on all of these.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.