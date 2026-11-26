# 3_modeling - F17: The first CNN could not see a whole shape.
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: F17 (`failure`, `3_modeling`)
- Owner / Proposed by: 40248536 + 40256377 / gemini_4_neon
- Calibration: `winning-decision (70% tier)`
- Grounding sources: `src/stage4_train/model.py`, `configs/pipeline.yaml`, `configs/models/A0.yaml`, `results/phase2_snapshot/iteration_log.json`, `ShapeSense_Deployed/web/stage4.html`, `ShapeSense_Deployed/web/failures.html`, commits `62c5fe8`, `8984a50`


## Prompt
Can our three-block CNN see a whole shape on a 64x64 image? Compute its receptive field and suggest a change if it is too small.

Literature/search framing: How large does a CNN's receptive field need to be, relative to the object, to classify whole shapes? Search for how the theoretical and the effective receptive field are computed (for example Luo et al. 2016 and Araujo et al. 2019) and for evidence on what happens when the receptive field is smaller than the object. Our case: three blocks gave a 22-px receptive field on 64-px images.

## Response
No - a three-block `SmallCNN` cannot see a whole standardized shape on a `64 x 64` canvas.

### Receptive field calculation
In `src/stage4_train/model.py`, every block is `[Conv2d(k=3, p=1, s=1) -> BatchNorm2d -> ReLU -> MaxPool2d(k=2, s=2)]` followed by `AdaptiveAvgPool2d(1)` (`GAP`) and `Linear`. Using the standard receptive field recurrence (Araujo et al., 2019):
$$r_l = r_{l-1} + (k_l - 1) \cdot j_{l-1}, \qquad j_l = j_{l-1} \cdot s_l$$
starting from input pixel resolution $r_0 = 1, j_0 = 1$:
- **Block 1:** Conv $3\times 3$ gives $r = 1 + 2(1) = 3$, $j = 1$; MaxPool $2\times 2$ gives $r = 3 + 1(1) = 4$, $j = 2$ (output $32\times 32$).
- **Block 2:** Conv $3\times 3$ gives $r = 4 + 2(2) = 8$, $j = 2$; MaxPool $2\times 2$ gives $r = 8 + 1(2) = 10$, $j = 4$ (output $16\times 16$).
- **Block 3:** Conv $3\times 3$ gives $r = 10 + 2(4) = 18$, $j = 4$; MaxPool $2\times 2$ gives $r = 18 + 1(4) = 22\text{ px}$, $j = 8$ (output $8\times 8$).

Even worse, as Luo et al. (2016) showed, the **effective receptive field (ERF)** decays roughly as a Gaussian from the center, meaning the practical region influencing any single $8\times 8$ spatial unit before `GAP` is much narrower than 22 px. On standardized `64 x 64` ShapeSense drawings, shapes occupy roughly `55-57 px` across the frame (`augment.frame_margin: 0.06` / Stage 1 standardization). Because `GAP` averages local feature maps without spatial coordinates, each pre-pool feature vector can only inspect local corners or edge arcs (`<= 22 px`) and cannot jointly measure opposite-side parallelism, vertex count (e.g., `hexagon` vs `octagon`), or major-vs-minor axis ratios (`circle` vs `ellipse`, `square` vs `rectangle`).

### Recommended fix
Extend `configs/pipeline.yaml#train.channels` from 3 blocks to **4 blocks**, e.g. `[32, 64, 128, 128]`:
- **Block 4:** Conv $3\times 3$ gives $r = 22 + 2(8) = 38$, $j = 8$; MaxPool $2\times 2$ gives $r = 38 + 1(8) = \mathbf{46\text{ px}}$, $j = 16$ (output $4\times 4$).
A 46-px theoretical receptive field on a `64 x 64` canvas spans ~84% of a typical 55-px shape in a single pre-`GAP` feature cell, allowing global shape closure and opposite-edge relations to be encoded directly before global pooling while keeping parameter count compact (`~242k` parameters).

## Validation
- Verified `SmallCNN` receptive-field geometry and output tensor shapes (`64 -> 32 -> 16 -> 8 -> 4 -> 1x1 GAP`) and `count_params` (`242,250` trainable parameters at `10` classes) in `src/stage4_train/model.py` and `configs/models/A0.yaml`.
- Updated `configs/pipeline.yaml#train.channels` to `[32, 64, 128, 128]` (recorded as `4 blocks: 46-px receptive field`), and later updated `SmallCNN`'s default `channels` argument and docstring in `src/stage4_train/model.py` during Iteration 3 after the outside review flagged that the code default still mentioned 3 blocks.
- Confirmed `ShapeSense_Deployed/web/stage4.html` (`networkExplorer`) renders all 4 blocks and their spatial shrink accurately.

## Our decision
Adopted the four-block architecture (`train.channels: [32, 64, 128, 128]`) as the shared `SmallCNN` across all arms (`A0`, `A1`, `B`, `A2`, `P`) prior to Iteration 1's frozen runs (`F17` marked `Overcome`).

## Measured effect
- **Theoretical receptive field:** Doubled from **22 px** (3 blocks, `8 x 8` pre-GAP map on a `55-px` shape) to **46 px** (4 blocks, `4 x 4` pre-GAP map).
- **Model capacity & fairness:** Locked at **242,250** parameters across all five arms (`A0`, `A1`, `B`, `A2`, `P`), achieving `95.5-96.2` ensemble macro-F1 on test (`results/phase2_snapshot/metrics.csv`) and `97.8-98.5` clean / `75.6-84.8` damaged macro-F1 on `fresh_holdout_2` (`results/phase2_snapshot/iteration_log.json`).

---

## : Gemini 4 Neon Corpus Synthesis (`F17` & Cross-Entry Lineage)

### 1. Entry Complexity, Risk & Adoption Verdict

* **Entry:** `F17` (`failure`)
* **Logic Depth:** **High** (feeds `D03`, `A14`, and sets the fixed `242,250`-parameter capacity shared by every arm)
* **Risk if Wrong:** **High** (receptive-field arithmetic `22 → 46 px` sets shared capacity; wrong $\rightarrow$ every arm mis-sized)
* **Adoption Status:** **Adopted verbatim** (fourth block `[32, 64, 128, 128]`, 46-px receptive field, 242,250 parameters locked prior to Iteration 1).

### 2. Group Synthesis: Architecture and the Three-Block Failure (`F17` $\rightarrow$ `D03` $\rightarrow$ `A14`)

* **`F17`** is the arithmetic spine. Every block is `Conv3x3(p=1) → BN → ReLU → MaxPool2`; with the recurrence $r_l = r_{l-1} + (k_l - 1) \cdot j_{l-1}$, three blocks give **22 px** at an `8×8` map, four give **46 px** at a `4×4` map. On 64-px drawings where shapes span `~55–57 px`, 22 px cannot see a whole shape before GAP — so `square` vs. `rectangle` and `hexagon` vs. `octagon` are unlearnable from local arcs. The fix (`[32, 64, 128, 128]`, **242,250** params) was adopted **before Iteration 1** and locked across all five arms.
* **`D03`** is the Gemini critique of the same design. It agrees on depth (High), leans `128` not `256` for block 4 (to stay near Decision 8's `~100k` target), and says keep the block, ReLU, GAP head. Its key discipline: *"change it once, for every arm, before any arm trains."* The record is explicit that **only the depth change was adopted**; conv bias, activation ablation, and anti-aliased pooling were *not* recorded as adopted.
* **`A14`** closes the loop: the pipeline used four blocks, but `SmallCNN.__init__` still defaulted to `(32, 64, 128)`. No trained weights were affected (all runs went through `build_model(config, …)`), but any direct `SmallCNN()` caller silently got the obsolete net. Fixed in Iteration 3; `SmallCNN()` now matches at `242,250` params.

**Depth note:** `F17` $\rightarrow$ `D03` $\rightarrow$ `A14` is a clean example of *one arithmetic result propagating into a design critique and then into a code-default fix*, with the team explicitly declining the critique's optional extras.

### 3. Corpus Dependency Graph (`3_modeling` Gemini 4 Neon Entries)

```text
F17 (3→4 blocks, 46-px RF, 242,250 params)
 ├── D03 (critique that produced F17's depth change; only depth adopted)
 ├── A14 (model.py default still said 3 blocks → fixed iter 3)
 └── F17's 242k params is the fixed capacity every arm shares

F02 (LOSO: ellipse only in Hand-Drawn → 9-class hold-out)
 ├── T17 (implements excluded_classes in sampling/sweep/eval)
 ├── T22 (seed_disagreement must skip LOSO runs → run_sweep marks holdout_source)
 └── C26 (grouping on source_id would drop classes → must group on phash_group)

C12 (per-arm lr/dropout grid) ──→ T15/T23 (record the winner as a comment)
                                   └── recipe_fingerprint unchanged → no retrain

C11 (per-arm synthetic share) ──→ F06 (augmentation/generator ranges only tuned on A1)
                                   └── both are "tuning-budget bias" fixes

C27 (equal_real, real_fraction, budget) ──→ C29 (budget gate fires)
C29 (e60_nostop adopted) ──→ C26 (CV at 15 epochs to bound cost)
C26 (CV re-ranks top-5) ──→ C12 (per-arm grid feeds top-5)
                         └── C25 (P added as descriptive arm; CV changes 4/5 winners)

F19 (invalid handle) ──→ C30 (eager Pool, _light_children)
C30 (parallel prep) ──→ C31 (optimization stage) ──→ C39 (measured before/after)
F22 (cuDNN halt at 66/191) ──→ relies on C30's atomic result.json resume
F25 (GPU looks idle) ──→ explains C30/C31's CPU-bound pacing
```

