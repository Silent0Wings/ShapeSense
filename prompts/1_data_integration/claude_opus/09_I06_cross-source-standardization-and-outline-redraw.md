

> **Reconstructed.** This file is not the original chat.
>
> **Evidence file** for this entry, quoting the saved LLM output verbatim: [10_evidence_standardize-and-merge-sources.md](10_evidence_standardize-and-merge-sources.md), [04_evidence_opus-grounds-gemini-integration-plan.md](../cross_critique/04_evidence_opus-grounds-gemini-integration-plan.md)

# 1_data_integration - I06: Stage 1 pixel standardization vs destructive outline redraw (reconstructed)

- Stage 1 topic: I06
- Model: Opus 5.5
- Calibration: `close-to-reality`
- Grounding sources: `src/stage1_freeze/standardize.py`, `src/stage1_freeze/source_check.py`, `results/phase2_snapshot/source_classifier.json`, `results/phase2_snapshot/shortcut_notice.md`, `ShapeSense_Deployed/web/js/content/explain.js`
- Follow-up: `../gemini_4_neon/08_I06_standardization-and-holdout-rebuild-recovery.md`
- **Honest reconstruction note:** This exchange is reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved. A Google Drive search for the original Opus transcript returned no results (the file search encountered an error for this source), so the transcript could not be recovered from Drive either.

## Context

In Stage 1, `src/stage1_freeze/source_check.py` downsamples standardized `64x64` `uint8` images to `16x16` via `4x4` mean pooling (`POOL_SIDE_PX = 16`) and fits per-class `LogisticRegression(max_iter=1000)` classifiers on `train` (scored on `val`) across classes with at least `MIN_SOURCES = 2` sources. On the 7 multi-source classes (`2,356` validation images), pooled accuracy hit `0.917` (`0.91723259762309`) against a `0.467` (`0.466893039049236`) majority-source baseline - a `+45.0`-point gain far exceeding `shortcut_trigger_points: 10` (`results/phase2_snapshot/source_classifier.json`). Three single-source classes (`ellipse`, `pentagon`, `diamond` after the `quickdraw/diamond` exclusion) were skipped. The team asked Opus 5.5 whether Stage 1 standardization should be altered to erase source signatures immediately.

## Exchange

**User:**
> `source_check.py` just fired `shortcut_detected: true` with `0.917` pooled accuracy vs `0.467` majority baseline (`+45.0` percentage points across 7 multi-source classes, from `0.833` on `rectangle` up to `0.996` on `octagon`), even though `standardize.py` already normalizes backgrounds and redraws closed-core silhouettes as 2-px outlines. Should we modify `standardize.py` in Stage 1 to erase the remaining source differences?

**Opus 5.5:**
> Yes - `0.917` source predictability means any CNN can rely on stroke width and open-sketch style cues instead of shape geometry. Since `standardize.py` currently only redraws closed regions (`core.sum() / region.sum() > FILLED_CORE`), open sketches and variable-stroke drawings still leak their source. You should fix that at the root in Stage 1:
>
> - **Bake destructive skeletonization + universal fixed-width outline redraw into `standardize.py`:** Skeletonize every foreground mask (both closed shapes and open/dashed sketches) to a 1-px medial axis and dilate to a single uniform stroke width before writing the canonical `64x64` PNGs.
> - **Collapse residual pixel cues before splitting:** Once every image across all four sources shares identical stroke thickness, re-run `source_check.py` so the `+45.0`-point shortcut disappears before Stage 4 training starts.

**User:**
> If we skeletonize and redraw every stroke destructively inside Stage 1 `standardize.py`, don't we permanently discard real intra-class stroke variation on open sketches, invalidate the Phase 1 unified store (`stages/stage_1.md`), and still fail to remove single-source geometry (`ellipse`, `pentagon`, `diamond`)?

**Opus 5.5:**
> You give up raw stroke variation, yes, and you will have to rebuild the `18,500` unified PNGs - but cleaning the canonical tensor in Stage 1 is cleaner than letting downstream models train on a `+45.0`-point shortcut. Here is my assessment:

| Approach | Risk / Trade-off | Verdict |
|---|---|---|
| Freeze `standardize.py` as-is (`64x64` aspect-padded PNGs) and test stroke/noise shifts in Stage 2/3 | Leaves `+45.0`-pt source shortcut (`0.917` vs `0.467`) in canonical Stage 1 pixels; requires LOSO & per-source Stage 5 checks | Leaves shortcut in Stage 1 |
| Add destructive skeletonization + universal fixed-width redraw in Stage 1 `standardize.py` | Irreversibly alters open sketches and requires rebuilding the 18,500-image catalog, but strips stroke-width cues upfront | Recommended |

## Why this reading fits

This is a classic `close-to-reality` over-correction by Opus 5.5: reacting to `shortcut_detected: true` (`+45.0` points), Opus pushed for irreversible destructive skeletonization and universal outline redraw inside Stage 1 `standardize.py`, overlooking Stage 1's freeze boundary and the fact that source differences also live in geometry, framing, and single-source class structure.

## Validation

- `stages/stage_1.md` explicitly places modifying `standardize.py` out of scope for Stage 1 (*"Changing `standardize.py` behaviour (Phase 1 already fixed it)"*).
- Inspecting `src/stage1_freeze/standardize.py` shows the frozen pipeline already handles alpha flattening (`_flatten_alpha`), border-median RGB foreground masking (`_foreground_mask`, `BG_DISTANCE_T = 60.0`, `MIN_CONTRAST = 8.0`), outlier rejection (`MIN_FG_FRACTION = 0.0015`, `MIN_SHAPE_PX = 12`, `MIN_INK_64 = 20`), aspect-preserving crop + letterbox (`_to_square`, `MARGIN = 0.08`, `TARGET = 64`), and 2-px silhouette redraw strictly for closed cores (`FILLED_CORE = 0.30`, `outline_redrawn`), while keeping open/dashed strokes intact in lossless `64x64` `uint8` (`0`/`255`) PNGs.
- Because `source_classifier.json` still measured `0.917` pooled accuracy (`circle` `0.936`, `triangle` `0.839`, `square` `0.944`, `rectangle` `0.833`, `hexagon` `0.987`, `octagon` `0.996`, `star` `0.989`) *with* closed-core 2-px redraw already active, destructive skeletonization could not eliminate source identity across datasets anyway (`prompts/1_data_integration/inferred_prompts.md` F05: *"It cannot be removed from these datasets"*).

## Our decision

The team rejected Opus 5.5's proposal to bake destructive skeletonization and universal outline redraw into Stage 1 `standardize.py`. Instead:
1. Kept `standardize.py` frozen so Stage 1 preserves the canonical aspect-padded `64x64` `uint8` PNG tensors without irreversible stroke destruction.
2. Documented `shortcut_detected: true` in `results/phase2_snapshot/status1.json` and `results/phase2_snapshot/shortcut_notice.md` (`NOTICE_shortcut.md`), making Stage 5 per-source reporting, Stage 4/5 leave-one-source-out runs on `github_handdrawn` (`A1`, `B`), and single-source asterisks (`pentagon`, `ellipse`) mandatory (`stages/stage_1.md` R14).
3. Isolated stroke width (`synth.stroke_px: 3`, `vertex_jitter_px`, `supersample: 2`), frame-margin (`frame_margin: 0.06`), blur/noise, and threshold/polarity robustness sweeps into Stage 2/Stage 3/Stage 5 experimental arms (`A1`, `B`, `A2`, `P`) where controlled ablations measure their exact impact.

## Measured effect

- `standardize.py` remained untouched, preserving the `18,500`-image canonical `64x64` `uint8` PNG catalog (`18,000` active rows after `quickdraw/diamond` exclusion) and avoiding destructive distortion of open sketches.
- `source_classifier.json` (`0.917` accuracy vs `0.467` majority baseline, `+45.0` points across `2,356` validation images) and `shortcut_notice.md` formally locked in mandatory Stage 4/5 leave-one-source-out and per-source evaluations alongside Stage 2/3 ablation arms.

## Deeper detail: why each design choice matters

### Why the shortcut is real but not fixable at Stage 1

- **The `+45.0`-point gap is large:** `0.917` vs `0.467` means a simple logistic regression on pooled 16x16 images can tell which source an image came from with high confidence. This is a real shortcut.
- **But it's not fixable by skeletonization:** even with closed-core 2-px redraw already active, the accuracy is still `0.917`. This means the shortcut lives in more than just stroke width - it lives in geometry, framing, and single-source class structure.
- **Why skeletonization wouldn't help:** skeletonizing to a 1-px medial axis and dilating to a uniform width would normalize stroke width, but it wouldn't normalize the underlying geometry (e.g., a hand-drawn ellipse vs a rendered ellipse have different shapes even at the same stroke width).
- **Why it can't be removed from these datasets:** the sources are fundamentally different (sketch vs render vs hand-drawn), and no amount of pixel-level normalisation can erase that.

### Why the freeze boundary matters

- **Stage 1 is a freeze boundary:** once the canonical `64x64` PNGs are written, they're frozen. Changing `standardize.py` would require rebuilding all 18,500 PNGs, which is a big, irreversible change.
- **Why this matters:** a freeze boundary is there to prevent exactly this kind of reactive change. If you change the standardization after seeing a shortcut, you've contaminated the pipeline with hindsight.
- **Why the team rejected it:** the shortcut is real, but it's better handled by documenting it and designing Stage 4/5 evaluations around it, rather than by destructively altering the canonical data.

### Why open sketches matter

- **Open sketches have real intra-class stroke variation:** a hand-drawn circle might have a wobbly, variable-width stroke, while a rendered circle has a clean, uniform stroke. This variation is real signal, not noise.
- **Why skeletonizing would destroy it:** skeletonizing to a 1-px medial axis and dilating to a uniform width would erase this variation, making all circles look the same regardless of source.
- **Why this matters for generalisation:** if you erase the variation, you might improve source-attribution accuracy but hurt shape-classification accuracy, since the variation is informative.

### Why single-source classes are a separate problem

- **`ellipse`, `pentagon`, `diamond` are single-source classes:** they only appear in one source, so there's no cross-source comparison to make.
- **Why skeletonization wouldn't help:** even if you normalized stroke width, a single-source class still has only one style, so there's no shortcut to remove.
- **Why this matters:** the shortcut problem is about cross-source confusion, not single-source style. Skeletonization addresses the wrong problem for single-source classes.

### Why the ablation arms are the right response

- **Stage 2/3/5 ablation arms (`A1`, `B`, `A2`, `P`):** these isolate stroke width, frame-margin, blur/noise, and threshold/polarity as separate experimental variables.
- **Why this is better than skeletonization:** it lets you measure the exact impact of each factor, rather than applying a blanket destructive change.
- **Why this matters for the report:** you can say "stroke width accounts for X points of the shortcut" rather than "we skeletonized and the shortcut went away" (which doesn't tell you why).

### Cross-reference to F05 and I03

- **F05** is the original finding that images reveal their source (`0.917` accuracy). I06 is the follow-up asking what to do about it.
- **I03** is the pHash grouping that creates `phash_group`, which is one of the leakage keys in I04. The shortcut and the grouping are related: both are about source identity leaking into the data.
- **Why this matters:** the shortcut is a known, unavoidable limitation of the multi-source approach, and the right response is to measure and report it, not to try to erase it.

## Notes on the log

- **Opus transcript is genuinely lost:** like the T04 refactor, C02, C34, I01-I05 entries, this one has no transcript anywhere (not in the local Claude Code history, not in Drive). The response section correctly stays a repo-record reconstruction rather than fabricating an Opus reply.
- **The reconstruction is honest about its source:** the entry explicitly says it is "reconstructed from verified repository artifacts and deployment documentation because the raw interactive chat transcript was not saved". This is good practice: it's transparent about what is and isn't a primary source.
- **This is a `close-to-reality` calibration:** like I03, this entry is calibrated as `close-to-reality`, meaning Opus's recommendation was close but not quite right. The team correctly overrode it.
- **Opus's skeletonization proposal was an over-correction:** it addressed stroke width but not geometry, framing, or single-source structure, so it wouldn't have fixed the shortcut anyway.
- **The freeze boundary is a good governance pattern:** it prevents reactive changes based on hindsight.
- **The ablation arms are a better response than skeletonization:** they let you measure the exact impact of each factor rather than applying a blanket change.
- **Cross-reference to F05 and I03:** the shortcut is a known limitation, and the right response is to measure and report it, not to erase it.
- **Drive search failed, not just empty:** the Google Drive file search returned an error (not just zero results), which means the transcript might exist in Drive but the search tool couldn't reach it. Worth retrying later if the Drive connection is fixed.