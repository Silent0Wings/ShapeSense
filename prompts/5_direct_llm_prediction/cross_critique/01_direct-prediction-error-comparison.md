# : Cross-Model Error and Confusion Comparison (200 test images)

This is the aggregate document that the ten batch files feed into. It is structurally different from the batch files — it is not a per-fold result but a **three-way comparison** (CNN, Opus 5.5, Gemini 4 Neon) with per-class, per-source, and per-tile decompositions. The depth is in what the aggregate reveals that no batch file can, and in the gaps the aggregate still leaves.

The expansion follows the established pattern: cross-model synthesis first (the depth no single table shows), then per-section expansion, then the open questions that matter.

---

# Part 1 — Cross-Model Synthesis: What the Aggregate Reveals

## The headline is not the headline

The document's title table says Opus loses to the CNN by 4.95 Macro F1 and Gemini loses by 3.53. A reader who stops there concludes "Gemini is closer to the CNN than Opus." That conclusion is **correct on the aggregate and misleading on the structure**, and the rest of the document exists to correct it. The per-class, per-source, and per-tile tables each tell a different story:

| Lens                               | Opus vs CNN | Gemini vs CNN | What it means                                        |
| ---------------------------------- | ----------- | ------------- | ---------------------------------------------------- |
| Macro F1 (aggregate)               | −4.95       | −3.53         | Gemini is closer                                     |
| Accuracy (aggregate)               | −4.5        | −3.5          | Same                                                 |
| Perfect batches (from batch files) | 3/10        | (not stated)  | Opus and Gemini have similar batch variance          |
| `circle` F1                        | −13.51      | −13.51        | **Identical** — both VLMs fail circle identically    |
| `ellipse` F1                       | −13.72      | −9.07         | Gemini is closer on ellipse                          |
| `hexagon` F1                       | −10.26      | −5.82         | Gemini is closer on hexagon                          |
| `pentagon` F1                      | −2.56       | 0.00          | Gemini matches CNN exactly                           |
| `github_handdrawn` accuracy        | 92.31%      | 94.87%        | Gemini is closer                                     |
| `kaggle_reevald` accuracy          | 89.13%      | 91.30%        | Gemini is closer                                     |
| `quickdraw` accuracy               | 77.78%      | 77.78%        | **Identical** — both VLMs fail quickdraw identically |
| Complementary wins vs CNN          | 2           | 1             | Opus recovers more CNN errors                        |

**The 1.42-point gap between Opus and Gemini is not uniform.** It is concentrated in `ellipse` (−13.72 vs −9.07, a 4.65-point difference) and `hexagon` (−10.26 vs −5.82, a 4.44-point difference). On `circle` and `quickdraw`, the two VLMs are **identical** — they fail the same tiles in the same way. On `pentagon`, Gemini is perfect and Opus is −2.56. On complementary wins, Opus is *better* than Gemini (2 vs 1).

**This is the finding the headline table cannot show:** the two VLMs are not "Gemini is uniformly closer." They are "Gemini is closer on `ellipse` and `hexagon`; Opus is closer on complementary wins; they are identical on `circle` and `quickdraw`." A reader who reads only the headline would attribute the gap to general vision quality; a reader who reads the per-class table would attribute it to two specific confusion pairs.

## The per-source table is the document's real argument

The per-class table says *which shapes* are hard. The per-source table says *why* they are hard:

| Source              | n   | CNN     | Opus   | Gemini  |
| ------------------- | --- | ------- | ------ | ------- |
| `mendeley_elkorchi` | 88  | 100.00% | 98.86% | 100.00% |
| `kaggle_reevald`    | 46  | 100.00% | 89.13% | 91.30%  |
| `github_handdrawn`  | 39  | 94.87%  | 92.31% | 94.87%  |
| `quickdraw`         | 27  | 88.89%  | 77.78% | 77.78%  |

**The CNN is 100% on two sources and ~90% on two sources.** The 97.50 Macro F1 is a weighted average of perfect and near-perfect. The CNN's errors are **entirely on `github_handdrawn` and `quickdraw`** — the two hand-drawn sources, not the two clean sources. This is a source-level weakness that the aggregate Macro F1 hides.

**The VLMs' errors are on the same two sources, but worse.** `quickdraw` is 77.78% for both VLMs — a 22-point drop from `mendeley_elkorchi`. The `quickdraw` source is the hardest for all three models, and the two VLMs are **identical** on it. This is the strongest evidence that `quickdraw` tiles are intrinsically ambiguous at 64×64 — the difficulty is in the tiles, not the models.

**The `kaggle_reevald` gap is the document's most interesting row.** The CNN is 100% on `kaggle_reevald`; Opus is 89.13%; Gemini is 91.30%. This is the largest Opus-vs-CNN gap of any source (10.87 points), and it is on a *clean* source. The `kaggle_reevald` errors are the `circle → ellipse` confusions (T055, T103, T142, T175) — the CNN has learned the `kaggle_reevald` circle/ellipse boundary from data, and both VLMs have not.

## The confusion pairs are the document's central taxonomy

The document lists three sets of confusions:
- **CNN (5 errors):** `hexagon → octagon` (2), `ellipse → triangle` (1), `rectangle → diamond` (1), `octagon → hexagon` (1).
- **Opus (15 errors):** `circle → ellipse` (4), `hexagon → octagon` (4), `ellipse → circle` (1), `ellipse → hexagon` (1), `square → rectangle` (1), `rectangle → ellipse` (1), `pentagon → hexagon` (1), `octagon → hexagon` (1).
- **Gemini (12 errors):** `circle → ellipse` (4), `hexagon → octagon` (4), `ellipse → circle` (1), `square → rectangle` (1), `rectangle → diamond` (1), `octagon → hexagon` (1).

**The two VLMs share the same top two confusions** (`circle → ellipse` ×4, `hexagon → octagon` ×4) — that is 8 of Opus's 15 and 8 of Gemini's 12. The remaining 7 (Opus) and 4 (Gemini) are where the 1.42-point gap lives.

**The CNN's confusions are structurally different:** it has `hexagon → octagon` (2) and `octagon → hexagon` (1), which are the same adjacent-pair the VLMs struggle with. But its other two errors (`ellipse → triangle`, `rectangle → diamond`) are **non-adjacent** — the CNN's idiosyncratic errors are on tiles the VLMs get right (T091, T154). This is the complementary structure the document names but does not fully analyze.

**The confusion counts don't sum to the error counts.** Opus's confusion list sums to 14, but the document says 15 errors. Gemini's sums to 12, matching. CNN's sums to 5, matching. **Opus has one error not listed in the confusion breakdown.** This is a small but real inconsistency — either the list is incomplete or one confusion is a repeat. A reader verifying the arithmetic would find it.

## The per-tile table is the document's evidence, and it is incomplete

The per-tile table lists **18 tiles** — the tiles where at least one model missed. But the document's error counts are CNN 5, Opus 15, Gemini 12. The 18 tiles cover:
- Tiles where all three missed: T017, T063, T069 (3 tiles).
- Tiles where CNN and one VLM missed: T039, T055, T072, T080, T091, T103, T111, T117, T142, T162, T175, T176, T178 (13 tiles).
- Tiles where only one VLM missed: T031, T154 (2 tiles).

**The 18 tiles are the union of all misses, not the sum.** The sum is 5 + 15 + 12 = 32 misses across 18 tiles, which means 14 tiles have multiple misses. This is the complementary structure the document names but does not tabulate: a reader cannot see *which* tiles have multiple misses from the list alone.

## The "explaining the gap" section is the document's weakest section

The three numbered explanations are correct but **not the same kind of claim**:
1. "Task-specific inductive bias" — a *model* explanation.
2. "Vertex-counting and aspect-ratio sensitivity" — a *tile* explanation.
3. "Human/VLM robustness vs. CNN edge cases" — a *complementary* explanation.

These are three different claims about *why* the gap exists, and the document does not say which one explains *which part* of the gap. The per-class and per-source tables are the evidence for each, but the document does not connect them:
- `circle → ellipse` (8 of 24 VLM errors) is explanation #2 (aspect-ratio sensitivity).
- `hexagon → octagon` (8 of 24 VLM errors) is explanation #2 (vertex-counting).
- The `kaggle_reevald` gap (10.87 points for Opus) is explanation #1 (source-specific boundary).
- The complementary wins (T091, T154) are explanation #3 (semantic closure).

**A reader who wants to know "which explanation is the biggest contributor" cannot get the answer from the document.** The document names three explanations and three tables, and leaves the mapping implicit.

---

# Part 2 — Per-Section Expansion

---

## Headline comparison

**Constraints made explicit:** (1) same 200 images, same metric; (2) `A2_0` is the final exported model; (3) the reference score (`96.25` on all `2,776` test images) is a *different* population — the 200-image subset is a seed-0 draw, and the two numbers are not directly comparable.

**Depth only close reading reveals:** the `97.50` on 200 images and the `96.25` on 2,776 images are **not the same measurement**. The 200-image subset is a seed-0 draw, which may over- or under-represent hard classes. A reader who compares `97.50` to `96.25` would conclude the subset is easier; a reader who compares `97.50` to the *subset's* `A2_0` score would compare like to like. The document's reference parenthetical is correct but easy to misread — it is a *population* reference, not a *subset* reference.

**Edge cases:** the accuracy and Macro F1 are **identical for the CNN** (`97.50` and `97.50%`), which means the CNN's per-class F1s are balanced. For Opus, accuracy is `92.50%` and Macro F1 is `92.55` — a 0.05-point difference, negligible. For Gemini, `94.00%` vs `93.97` — also negligible. **All three models have accuracy ≈ Macro F1**, which means none is systematically failing on a rare class. This is a *validation* that the per-class F1s are not driven by class imbalance — the 200-image sample is 20 per class, so Macro F1 and accuracy are close by construction, but the closeness is still worth stating.

**Decision rationale:** reporting both accuracy and Macro F1 is redundant when they are equal, but the redundancy is the *evidence* that the sample is balanced. A document that reported only Macro F1 would hide the balance check.

**Changelog:** [1] `97.50` vs `96.25` are different populations, not different subsets; [2] accuracy ≈ Macro F1 for all three models — balance check; [3] redundant metrics as evidence.

**Open questions:** Is the 200-image subset's `A2_0` score (`97.50`) statistically distinguishable from the full-test `96.25`? With n=200, the binomial standard error on 97.5% is ~1.1 points; 97.50 vs 96.25 is a 1.25-point difference, which is ~1.1 SE — borderline. A bootstrap CI on the subset score would answer this; the document does not include one.

---

## Per-class Macro F1 breakdown

**Constraints made explicit:** (1) 20 images per class; (2) F1 is per-class, not micro-averaged; (3) deltas are vs CNN, signed.

**Depth only close reading reveals:** three rows are the document's most important:

1. **`circle`:** CNN 100.00, Opus 86.49, Gemini 86.49. **Identical.** Both VLMs fail `circle` identically — every `circle → ellipse` error is a VLM error the other VLM shares. This is the strongest evidence that the `circle/ellipse` confusion is a *VLM-general* failure, not a model-specific one.
2. **`triangle`:** CNN 97.56, Opus 100.00, Gemini 100.00. **Both VLMs beat the CNN.** The CNN's `ellipse → triangle` error (T154) is the only `triangle` miss; both VLMs get it right. This is the one class where the VLMs are uniformly better.
3. **`pentagon`:** CNN 100.00, Opus 97.44, Gemini 100.00. **Gemini matches CNN; Opus misses one** (T072, `pentagon → hexagon`). This is the only per-class row where Opus and Gemini *disagree* in a way that explains part of the 1.42-point gap.

**The `circle` and `quickdraw` identical scores are the document's deepest structural finding.** Two different models, trained differently, with different architectures, fail the *same tiles* in the same way. The only explanation is that the tiles are intrinsically ambiguous at 64×64 — the `circle/ellipse` boundary is a judgment call, and both VLMs make the same judgment. The CNN, trained on 12,405 images, has learned the specific threshold; the VLMs, with 50 few-shot examples, have not.

**Edge cases:** `diamond` is Opus −0.12 (97.44 vs 97.56) — a tiny difference, but it is the only class where Opus is *closer than Gemini* (Gemini is +0.00). A reader who reads the deltas in order might miss that `diamond` is the one class where Opus beats Gemini — but the difference is one tile (T178: Opus square, Gemini diamond, CNN diamond), and one tile is not a class-level finding.

**Changelog:** [1] `circle` identical — VLM-general failure; [2] `triangle` both VLMs beat CNN — the CNN's one error is a VLM correct; [3] `pentagon` the one class where Opus and Gemini disagree; [4] `diamond` Opus's only per-class win — one tile, not a class finding.

**Open questions:** The per-class F1 for `hexagon` is CNN 92.31, which is *lower* than the CNN's `octagon` (92.68) — the CNN's weakest class is `hexagon`. Is the CNN's `hexagon` weakness concentrated in `quickdraw` hexagons (T017, T063, T069)? If so, the CNN's `hexagon` F1 is a source effect, not a class effect. The document's per-class and per-source tables are separate; a cross-tab (class × source) would be more informative than either alone.

---

## Per-source accuracy breakdown

**Constraints made explicit:** (1) source is the data origin, not the class; (2) n varies by source (88, 46, 39, 27); (3) accuracy is per-source, not per-class.

**Depth only close reading reveals:** the per-source table is the document's **causal** table, and it makes three claims the per-class table cannot:

1. **The CNN is 100% on both clean sources** (`mendeley_elkorchi`, `kaggle_reevald` are clean, not hand-drawn) and ~90% on both hand-drawn sources (`github_handdrawn`, `quickdraw`). The 97.50 Macro F1 is a weighted average of perfect and near-perfect, and the CNN's errors are **entirely** on hand-drawn sources. This is a source-level weakness the aggregate hides.
2. **The VLMs' gap is largest on `kaggle_reevald`** (Opus −10.87, Gemini −8.70), which is a *clean* source. This is counterintuitive — the VLMs should be *better* on clean sources, not worse. The explanation: `kaggle_reevald` is where the `circle/ellipse` errors concentrate (T055, T103, T142, T175 are all `kaggle_reevald_circle`), and the CNN has learned the `kaggle_reevald` circle/ellipse boundary exactly. The VLMs have not.
3. **`quickdraw` is 77.78% for both VLMs and 88.89% for the CNN** — all three models fail on `quickdraw`, and the two VLMs fail identically. This is the strongest evidence that `quickdraw` tiles are intrinsically ambiguous.

**The `github_handdrawn` row is the document's most important for the complementary analysis.** The CNN is 94.87% (37/39), Opus is 92.31% (36/39), Gemini is 94.87% (37/39). Gemini matches the CNN exactly on `github_handdrawn` — same 2 errors. Opus has one more. The two tiles where the CNN misses are T091 and T154, both `github_handdrawn`; Gemini misses T154 but not T091 (it calls T091 diamond, same as CNN), and Opus misses neither (it gets both T091 and T154 right). **The three models' `github_handdrawn` errors are not the same tiles** — the source is hard for all three, but the specific hard tiles differ. This is the complementary structure at the source level, and the document does not state it.

**Edge cases:** `mendeley_elkorchi` is 88 of 200 images — 44% of the sample. The CNN is 100% on it, Opus is 98.86%, Gemini is 100%. The VLMs' `mendeley_elkorchi` gap is negligible (1 image for Opus, 0 for Gemini), which means the aggregate 4.95/3.53-point gaps are **not** driven by the cleanest, most-represented source. They are driven by `kaggle_reevald` (the second-cleanest) and `quickdraw` (the hardest).

**Changelog:** [1] CNN's 100% on clean sources — the 97.50 is a weighted average of perfect and near-perfect; [2] `kaggle_reevald` is the largest VLM gap, on a clean source — counterintuitive; [3] `quickdraw` 77.78% for both VLMs — intrinsic difficulty; [4] `github_handdrawn` complementary structure not stated; [5] `mendeley_elkorchi` not the driver of the aggregate gap.

**Open questions:** Is the CNN's 100% on `kaggle_reevald` a *source* effect (the `kaggle_reevald` conventions are easy) or a *class* effect (the classes in `kaggle_reevald` are easy)? The `kaggle_reevald` sample is 46 images, heavily weighted toward `diamond` and `rectangle` (from the batch files: T023, T027, T033, T057, T060, T082, T084, T086, T090, T096, T097, T101, T104, T138, T147, T153, T168, T169, T178, T179, T187, T192, T195, T198 are all `kaggle_reevald`). A class × source cross-tab would let a reader see whether the CNN's `kaggle_reevald` strength is a source or class effect.

---

## Top confusion pairs and complementary agreement

**Constraints made explicit:** (1) confusion pairs are counted across the 200 tiles; (2) complementary wins are *per-tile*, not aggregate; (3) inter-model agreement is a pairwise measure.

**Depth only close reading reveals:** the complementary wins list is the document's **most under-analyzed** section. It lists:
- CNN right, Opus wrong (12): T142, T103, T175, T055, T162, T117, T031, T111, T072, T039, T080, T178.
- Opus right, CNN wrong (2): T154, T091.
- CNN right, Gemini wrong (8): T142, T103, T175, T055, T117, T176, T039, T080.
- Gemini right, CNN wrong (1): T154.

**The Opus and Gemini lists overlap heavily.** Of Opus's 12 "CNN right, Opus wrong" tiles, 8 are also "CNN right, Gemini wrong" (T142, T103, T175, T055, T117, T039, T080 — and T162 is *not* in Gemini's list, but T176 is). The two VLMs miss **the same CNN-correct tiles**, which is the complementary structure at the tile level: the CNN's correct tiles are the VLMs' error tiles, and the VLMs' error tiles are largely the same. The only tiles where Opus misses and Gemini doesn't (T162, T031, T072, T178) are 4 tiles, and the only tiles where Gemini misses and Opus doesn't (T176) is 1 tile. **The 1.42-point gap is 5 tiles.**

**The "Opus right, CNN wrong" list is 2 tiles, both `github_handdrawn`.** T154 (ellipse, CNN triangle) and T091 (rectangle, CNN diamond). Both are the CNN's idiosyncratic errors. **Opus recovers both.** Gemini recovers only T154. **The one tile where Opus beats Gemini is T091** — the `github_handdrawn_rectangle_001081` that the CNN calls diamond. Opus says rectangle; Gemini says diamond (same as CNN). This single tile is 0.5% of the 200, and it is the *only* tile where Opus's complementary win exceeds Gemini's. A 1.42-point Macro F1 gap is not explained by one tile; the explanation is in the `ellipse` and `hexagon` per-class gaps, not the complementary wins.

**Inter-model agreement:** Opus vs Gemini 96.00%, CNN vs Opus 93.00%, CNN vs Gemini 95.50%. **The two VLMs agree more with each other than either agrees with the CNN.** This is the structural signature: the VLMs share a *vision prior* (same broad shape categories, same adjacent-pair confusions), and the CNN has a *data-learned boundary* that neither VLM shares. The 96% VLM agreement is the strongest evidence that the VLM errors are a *shared* failure mode, not a model-specific one.

**Edge cases:** the 96.00% agreement means the two VLMs disagree on 8 of 200 tiles. Those 8 tiles are where the 1.42-point gap lives. The document lists them implicitly (T162, T031, T072, T178 for Opus-miss-Gemini-correct; T176 for Gemini-miss-Opus-correct; plus 3 more not listed). **The 8 disagreement tiles should be a separate table** — they are the *only* tiles where the aggregate comparison is not a tie.

**Changelog:** [1] the complementary lists overlap heavily — the VLMs miss the same CNN-correct tiles; [2] the 1.42-point gap is 5 tiles, not a broad difference; [3] T091 is the only tile where Opus's complementary win exceeds Gemini's; [4] VLM agreement (96%) > CNN agreement (93%, 95.5%) — shared vision prior; [5] the 8 VLM-disagreement tiles should be a separate table.

**Open questions:** The inter-model agreement matrix is incomplete — it lists 3 of 3 pairwise agreements, which is correct, but does not break down by class or source. Is the VLM agreement higher on `mendeley_elkorchi` (clean) than on `quickdraw` (hard)? If so, the shared-prior hypothesis is supported. If not, the VLMs share a prior even on the hard tiles, which would mean the prior is robust to tile difficulty — a stronger claim.

---

## Concrete misclassified test tiles

**Constraints made explicit:** (1) 18 tiles shown; (2) all three models' predictions shown; (3) true labels from the frozen test set.

**Depth only close reading reveals:** the 18-tile table is the document's **evidence**, and it is structurally incomplete:

1. **It includes tiles where only one model missed** (T031, T154) alongside tiles where all three missed (T017, T063, T069). The reader cannot tell from the table alone which tiles are "all-model failures" and which are "single-model failures" — the visual grouping is by blind ID, not by failure type.
2. **It omits the 14 misses that are not on these 18 tiles.** With 32 total misses across 18 tiles, 14 tiles have *multiple* misses, but the table shows only the union. A reader who wants to know "which tiles did Opus and Gemini both miss?" cannot answer from the table — the answer is "all the tiles in the table except T031, T154, T091, T176, T072, T162, T178" (where the two VLMs differ), and that is a subtraction the reader has to do.
3. **The table does not show the CNN's correct predictions on the VLM-error tiles.** For T055 (Opus and Gemini both ellipse, true circle, CNN circle), the table shows the CNN's correct prediction — good. But for T017 (all three octagon, true hexagon), the CNN's prediction is *also wrong* (octagon). The table shows the CNN's prediction for every tile, which is correct, but the *interpretation* — "is this a tile the CNN got right?" — is left to the reader.

**The T091 row is the table's most important:** `github_handdrawn_rectangle_001081`, true rectangle, CNN diamond, Opus rectangle, Gemini diamond. **This is the one tile where Opus beats Gemini and the CNN.** It is 1/200 = 0.5% of the sample. A reader looking at the 18-tile table might infer that Opus's advantage over Gemini is more than one tile; the table shows it is exactly one tile (plus T162, T178, T031 where Opus misses and Gemini doesn't, which are Gemini-correct-Opus-wrong, not the reverse). **The aggregate 1.42-point gap is not visible in the 18-tile table's pattern — it is in the *unlisted* 8 VLM-disagreement tiles.**

**Edge cases:** T117 is the only non-adjacent VLM error (true ellipse, CNN ellipse, Opus hexagon, Gemini circle). The table shows it, and it is the tile that most clearly demonstrates the VLMs' shape priors can be actively wrong (not just uncertain). A reader who wanted to see "the VLM's worst failure" would find it in T117, not in the more common `circle → ellipse` errors — but the table does not flag T117 as special.

**Changelog:** [1] the table mixes all-model and single-model failures — no visual grouping; [2] 14 misses not shown — the table is the union, not the sum; [3] T091 as the one tile where Opus's advantage is visible — the 1.42-point gap is not in the table; [4] T117 as the worst VLM failure — not flagged.

**Open questions:** Should the 18-tile table be re-sorted by *failure type* (all-model, CNN-only, Opus-only, Gemini-only) rather than by blind ID? A sorted table would show the complementary structure directly; the current table requires the reader to classify each row. Also: should the table include a column for "CNN confidence" (logit margin or softmax)? That would let a reader distinguish "CNN right because confident" from "CNN right by luck" — and would test the hypothesis that the CNN's correct tiles are the ones it is most confident about.

---

## Explaining the gap

**Constraints made explicit:** (1) three explanations; (2) each is a hypothesis, not a proof; (3) the explanations are not mutually exclusive.

**Depth only close reading reveals:** the three explanations are **not the same kind of claim**, and the document does not map them to the evidence:

| Explanation                                            | Kind          | Evidence in the document                               | Strength                                          |
| ------------------------------------------------------ | ------------- | ------------------------------------------------------ | ------------------------------------------------- |
| Task-specific inductive bias (12,405 training samples) | Model         | Per-source: CNN 100% on clean, ~90% on hand-drawn      | Strong for `kaggle_reevald`, weak for `quickdraw` |
| Vertex-counting / aspect-ratio sensitivity             | Tile          | Per-class: `circle/ellipse` and `hexagon/octagon` gaps | Strong — 16 of 24 VLM errors                      |
| Human/VLM robustness vs. CNN edge cases                | Complementary | 2 (Opus) and 1 (Gemini) complementary wins             | Weak — 3 tiles total                              |

**The first explanation is the most-cited but the least-precise.** "Task-specific inductive bias" says the CNN trained on more data does better on the specific conventions. But the per-source table shows the CNN is **100% on `mendeley_elkorchi` and `kaggle_reevald`** and **~90% on `github_handdrawn` and `quickdraw`** — the inductive bias is not uniform, it is *source-specific*. The CNN has learned the clean-source conventions exactly and the hand-drawn conventions approximately. A more precise claim: **the CNN's inductive bias is a clean-source bias** — it is trained on more clean data than hand-drawn data, and its errors are on the hand-drawn sources. The document's explanation #1 does not say this.

**The second explanation is the strongest by error count.** 16 of the 24 VLM errors are `circle → ellipse` (8) or `hexagon → octagon` (8). These are vertex-counting and aspect-ratio confusions. The explanation is correct, but the document does not say **how much** of the 1.42-point Opus-vs-Gemini gap is explained by it. The per-class table shows: `circle` is identical (no gap), `ellipse` is −13.72 vs −9.07 (4.65-point gap), `hexagon` is −10.26 vs −5.82 (4.44-point gap). **The 1.42-point aggregate gap is ~9.09 points of per-class difference on two classes, divided by 10.** The arithmetic: (4.65 + 4.44) / 10 = 0.91, plus smaller contributions from other classes, sums to 1.42. **The 1.42-point gap is almost entirely `ellipse` and `hexagon`.** The document's explanation #2 is the *entire* explanation of the Opus-vs-Gemini gap; explanation #1 explains the CNN-vs-both gap; explanation #3 explains a rounding error.

**The third explanation is a single-tile story.** T091 and T154 are the CNN's two idiosyncratic errors. Opus recovers both; Gemini recovers one. The 2 vs 1 complementary wins are a 1-tile difference, which is 0.5% of the sample and ~0.35 points of Macro F1. **Explanation #3 explains at most 0.35 of the 1.42-point gap (Opus vs Gemini) and at most 0.7 of the 3.53-point gap (Gemini vs CNN).** It is the smallest contributor and the document presents it last, which is appropriate — but it should be labeled as "small" rather than presented as a peer of the other two.

**Changelog:** [1] three explanations are three kinds of claim, mapped to evidence; [2] "inductive bias" is a *clean-source* bias — CNN's errors are on hand-drawn sources; [3] explanation #2 explains ~all of the Opus-vs-Gemini gap (0.91 of 1.42); [4] explanation #3 is a 1-tile story, ~0.35 of 1.42.

**Open questions:** The document says `A2_0` "trains directly on `64x64` standardized silhouettes with Stage 2 clean/augmented real strokes and Stage 3 synthetic geometry across `12,405` labeled training images." Is the `12,405` evenly distributed across sources, or weighted toward clean sources? If weighted toward clean, the "clean-source bias" hypothesis is directly supported; if evenly distributed, the CNN's hand-drawn weakness is a *model* limitation, not a *data* limitation. The document does not say.

---

## Validation

**Constraints made explicit:** (1) 200/200 pixel-MD5 verification; (2) alignment against `sample_ids.csv` and `blind_id_map.csv`; (3) full metrics JSON saved.

**Depth only close reading reveals:** the validation is **methodologically sound but incomplete**:

1. **Pixel-MD5 verification** confirms the 200 tiles are the same images across all three models — correct and necessary.
2. **Alignment against `sample_ids.csv`** confirms the ground truth is the frozen test subset — correct.
3. **`summary.json` saved** — correct, but the document does not say what is in it. A reader who wants the raw predictions has to find `claude_opus_predictions.csv` (from the batch files) and a Gemini equivalent (not mentioned). The `summary.json` is the aggregate; the per-prediction files are the raw data. The document cites the aggregate and does not cite the raw files.

**The validation does not include a bootstrap confidence interval on the Macro F1 scores.** With n=200, the 95% CI on a 92.55% score is roughly ±1.8 points; on 97.50%, ±1.1. **The Opus-vs-Gemini gap (1.42) is smaller than the CI on either score (±1.8, ±1.1), which means the two VLMs' aggregate scores are not statistically distinguishable.** The CNN-vs-Opus gap (4.95) exceeds the CI on Opus but is close to the CI on the CNN; the CNN-vs-Gemini gap (3.53) is comparable. **The aggregate table's ordering is directionally correct but the pairwise differences are not all significant.** A reader who treats 92.55 vs 93.97 as a real difference is over-interpreting the data.

**The validation also does not include a per-class CI.** The per-class F1s are on 20 images each — a single-tile difference changes a class F1 by up to 5 points. **The per-class table's deltas (e.g., `circle` −13.51) are within CI noise on 20 images.** The `circle` gap is real (both VLMs have the same F1, and the CNN is perfect — a 13.51-point gap on 20 images is 3 tiles, which is a large effect), but the `diamond` Opus −0.12 is one tile and is not a real class-level difference.

**Changelog:** [1] pixel-MD5 and alignment are sound; [2] the document cites the aggregate but not the raw prediction files; [3] no bootstrap CI on the Macro F1 scores — Opus-vs-Gemini gap is within noise; [4] per-class CIs absent — 20-image classes have ±5-point noise.

**Open questions:** Should the document include a bootstrap CI on the 200-image Macro F1 for each model? Yes — without it, the aggregate table's ordering is directionally informative but not statistically defensible. The CI would also let a reader see whether the Opus-vs-Gemini gap (1.42) is significant, which it likely is not.

---

# Part 3 — What the Aggregate Cannot Say, and What to Add

## The three highest-value additions

1. **A class × source cross-tab.** The per-class and per-source tables are separate; their interaction is the document's missing piece. Is `hexagon` hard because of `quickdraw` hexagons, or because of all hexagons? Is the CNN's `kaggle_reevald` strength a source effect or a class effect? The cross-tab answers both.

2. **Bootstrap CIs on the aggregate and per-class scores.** The 200-image sample gives ±1.1–1.8 points on the aggregate; the 20-image classes give ±5 points. The document's ordering is directionally correct, but the pairwise gaps (especially Opus vs Gemini at 1.42) are within noise. A CI would make the document honest about what it can and cannot claim.

3. **The 8 VLM-disagreement tiles as a separate table.** The 1.42-point Opus-vs-Gemini gap is 5 tiles (T162, T031, T072, T178 for Opus-miss-Gemini-correct; T176 for Gemini-miss-Opus-correct; plus 3 more from the 8 disagreements). The aggregate hides them; the 18-tile table buries them. A table of the 8 disagreements would make the gap visible and analyzable.

## The document's unstated assumption

The document assumes the 200-image subset is representative of the 2,776-image test set. The subset's `A2_0` score is `97.50`; the full set's is `96.25`. **The subset is 1.25 points easier for the CNN.** This means the VLMs' scores on the 200 images (`92.55`, `93.97`) are likely **optimistic** relative to the full test set — the subset over-represents the clean sources where the CNN is 100%, and the VLMs' aggregate scores on the full test set would be lower. The document's aggregate comparison is valid (same 200 images for all three), but the *absolute* scores are subset-specific. A reader who compares `92.55` to the full-test `96.25` is comparing different populations.

## The document's strongest claim, stated precisely

The document's strongest claim is **not** "the CNN is better than the VLMs" (the aggregate gap is directionally correct but the pairwise CIs overlap). It is:

> **The CNN's errors are entirely on hand-drawn sources; the VLMs' errors are concentrated in two adjacent-pair confusions (`circle/ellipse`, `hexagon/octagon`) that are the same for both VLMs. The CNN has learned the adjacent-pair boundaries from data; the VLMs have not. The VLMs' aggregate scores are within CI of each other; the CNN's aggregate is higher but the gap is source-concentrated, not uniform.**

This claim is supported by the per-source table, the per-class table, and the confusion pairs. The document's headline table supports a weaker claim ("the CNN is better") and the rest of the document supports the stronger one. **The expansion's job is to make the stronger claim the explicit one.**

---

# Changelog for This Turn

| #   | What was done                                                                                                   | Type               |
| --- | --------------------------------------------------------------------------------------------------------------- | ------------------ |
| 1   | Cross-model synthesis: the headline gap is not uniform; it is concentrated in `ellipse` and `hexagon`           | Structural depth   |
| 2   | Per-source table identified as the document's causal argument (clean vs hand-drawn)                             | Depth              |
| 3   | `circle` and `quickdraw` identical VLM scores — VLM-general failure                                             | Structural finding |
| 4   | `kaggle_reevald` as the largest VLM gap on a clean source — counterintuitive                                    | Depth              |
| 5   | `triangle` as the one class where both VLMs beat the CNN                                                        | Depth              |
| 6   | Complementary wins are 1 tile (T091) — the 1.42-point gap is not there                                          | Arithmetic         |
| 7   | VLM agreement (96%) > CNN agreement (93%, 95.5%) — shared vision prior                                          | Structural finding |
| 8   | The 18-tile table mixes all-model and single-model failures — no grouping                                       | Clarity            |
| 9   | The three explanations mapped to evidence and sized: #2 explains ~all of Opus-vs-Gemini; #3 is ~0.35            | Depth              |
| 10  | "Inductive bias" is a *clean-source* bias — CNN's errors are on hand-drawn                                      | Depth              |
| 11  | No bootstrap CIs — Opus-vs-Gemini gap is within noise                                                           | Statistical rigor  |
| 12  | Per-class CIs absent — 20-image classes have ±5-point noise                                                     | Statistical rigor  |
| 13  | The 200-image subset is 1.25 points easier for the CNN than the full test — absolute scores are subset-specific | Validity           |
| 14  | The document's strongest claim stated precisely                                                                 | Coherence          |
| 15  | Three highest-value additions: class × source cross-tab, bootstrap CIs, 8-disagreement table                    | Actionable         |

**The single highest-value addition:** the bootstrap CIs. Without them, the document's aggregate table reads as a definitive ranking (CNN > Gemini > Opus), but the Opus-vs-Gemini gap (1.42) is smaller than the CI on either score. The document is *directionally* correct and *statistically* overconfident. A reader who treats 92.55 vs 93.97 as a real difference is over-interpreting a 5-tile difference on a 200-tile sample. The CI would let the document say "the CNN is clearly ahead; the two VLMs are not clearly ordered" — which is the honest claim the data supports.