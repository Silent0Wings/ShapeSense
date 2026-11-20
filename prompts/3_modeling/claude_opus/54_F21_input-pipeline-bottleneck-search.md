# 3_modeling - F21: Image preparation made training about five times slower than the GPU allowed. (failure search)
- LLM: Claude Opus 5.5 (claude-opus-5-5), with web search
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Entry: F21 · Question from [failure_search_prompts.md](../../failure_search_prompts.md#f21) · Record: [F21](../inferred_prompts.md#f21)

## Prompt
> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.
>
> How often is the input pipeline, not the GPU, the bottleneck in training small CNNs, and how is it fixed? Search for work on data stalls (for example Mohan et al. 2021), the cost of CPU augmentation, and prefetching with several worker processes. Our case: image preparation made training about five times slower than the GPU allowed.

## Response

### Well established

- **Data stalls often dominate training time.** Mohan, Phanishayee, Raniwala and Chidambaram, "Analyzing and Mitigating Data Stalls in DNN Training", PVLDB 14(5), 2021 ([arXiv 2007.06775](https://arxiv.org/abs/2007.06775), [NSF copy](https://par.nsf.gov/servlets/purl/10286582)), find that "in many cases, DNN training time is dominated by data stall time". They split it into *fetch* stalls (I/O) and *prep* stalls (CPU pre-processing).
- **Small models stall the most.** The same paper ([full text](https://ar5iv.labs.arxiv.org/html/2007.06775)) reports that DNNs "need 3–24 CPU cores per GPU for pre-processing". Heavy models such as ResNet50 need about 3 to 4 cores, while light ones such as ResNet18 and AlexNet need 12 to 24, because the GPU finishes each step quickly. With the data fully cached, prep stalls took 50 to 65% of epoch time for ResNet18.
- **GPU-side pre-processing helps but doesn't solve it.** In the same paper, NVIDIA DALI "is able to reduce, but not eliminate prep stalls", and it costs GPU memory.
- **Hyperparameter search makes it worse.** Concurrent search jobs each pre-process the same data again ("the same data item is processed eight times"). The paper's CoorDL shares that work, which is where its biggest gains came from ([MSR page](https://www.microsoft.com/en-us/research/publication/analyzing-and-mitigating-data-stalls-in-dnn-training/)).
- **This is common in production too.** Murray et al., "tf.data: A Machine Learning Data Processing Framework" ([arXiv 2101.12127](https://arxiv.org/pdf/2101.12127)), say input processing takes a large share of job resources across Google's fleet. Their Figure 1 caption says about 20% of jobs spend more than a third of their compute time in the input pipeline. Checked on 2026-11-20: the same sentence appears in arXiv v1, in v2 (the current version, 2021-02-23) and in the published paper (PVLDB 14(12), 2021, [doi 10.14778/3476311.3476374](https://doi.org/10.14778/3476311.3476374)), so it can be quoted.
- **The standard fix is parallel, overlapped preparation.** The [PyTorch performance tuning guide](https://docs.pytorch.org/tutorials/recipes/recipes/tuning_guide.html) notes that the default `num_workers=0` loads data synchronously in the main process. "Setting num_workers > 0 enables asynchronous data loading and overlap between the training and data loading", and the worker count "should be tuned". `pin_memory=True` speeds up host-to-GPU copies.
- **Purpose-built loaders target the same bottleneck.** FFCV (Leclerc et al., [CVPR 2023](https://openaccess.thecvf.com/content/CVPR2023/html/Leclerc_FFCV_Accelerating_Training_by_Removing_Data_Bottlenecks_CVPR_2023_paper.html)) combines an efficient file format, caching, pre-loading, asynchronous transfer and JIT compilation. It reports ResNet-50 ImageNet accuracy matching the best baselines in about half the time.

### Single reports

I found no study measuring a 64x64 grayscale CNN specifically. The numbers above come from ImageNet-scale image decoding, which costs much more per image than ShapeSense's augmentation. The trend (lighter model, more CPU per GPU) is documented, but the exact ratio for our model is not.

### Reasoning (mine, not sourced)

For a CNN this small, a GPU step takes milliseconds. Per-sample Python or NumPy warping and stroke rendering on one core can easily take several times longer, so a step that is about 80% preparation, as measured, is what the Mohan et al. trend predicts at the extreme light end. The remaining epoch-time spread (2 to 6 s) lines up with CPU saturation, as the record notes (99% against 90%). That is consistent with "the pipeline is still CPU-bound, now across 7 cores".

### How it applies to ShapeSense

The fix the project chose, several persistent worker processes building batches ahead of the training thread, is the documented mainstream remedy. ShapeSense's strict reproducibility rule rules out the easy alternatives: GPU augmentation (DALI or kornia) would change the pixel values (see F24), and changing the order of random draws would change results. The literature's other big lever, sharing preparation across concurrent search trials (CoorDL), would also only be safe if each trial's random stream were kept intact. Arms A1, B, A2 and P, which augment or draw shapes, gain the most. A0 has little preparation to speed up.

## Validation

The record's cause (augmentation and synthetic drawing on one CPU core, about 80% of each step, GPU waiting) matches the "prep stall" category in Mohan et al. exactly, and their finding that light models need the most CPU per GPU explains why a small CNN was hit so hard. The record's outcome (7 processes, epochs from about 20 s to 2 to 6 s, identical validation scores across process counts) is the textbook fix, plus a determinism check the literature rarely demands. Nothing contradicts the record. The literature adds that remaining variance tied to the CPU is expected while preparation still saturates the cores.

## Our decision

The project moved batch preparation to 7 worker processes, checked that the scores were identical across process counts, and put the slow epochs down to the rest of the machine competing for the CPU. The findings suggest two further options, if speed matters again: profile what share of the step is still preparation now, and cache deterministic per-image work. Each would need the same equivalence check. Nothing was changed in this pass.

## Measured effect
None. Research only, no run.

---

## Data-Stall Taxonomy & Small-CNN Compute/I-O Imbalance (`F21`)

### Metadata & Lineage

* **Entry ID / Type:** `F21` (`failure`, `3_modeling` — literature audit)
* **Date:** `2026-11-20`
* **Owner / LLM:** `opus_medium_5.5` (`claude-opus-5-5`, web-grounded synthesis)
* **Primary Artifacts:** `src/stage4_train/prep.py`, `configs/pipeline.yaml` (`prep_workers: 7`)

### Literature Grounding: Prep Stalls in Lightweight Architectures

* **Fetch Stalls vs. Prep Stalls (Mohan et al., *PVLDB* 14(5), 2021, arXiv:2007.06775):** Decomposes DNN input bottlenecks into storage I/O (*fetch stalls*) and CPU transformation latency (*prep stalls*). Crucially, **lightweight architectures exhibit the sharpest CPU-to-GPU starvation ratio**: whereas heavy backbones (ResNet-50) require `3–4` CPU cores per GPU, compact models (ResNet-18, AlexNet) complete forward/backward passes in milliseconds and require **`12–24` CPU cores per GPU** to avoid starving the accelerator (`50%–65%` epoch stall time even when datasets are cached in RAM).
* **Fleet-Scale Input Overhead (Murray et al., *PVLDB* 14(12), 2021, arXiv:2101.12127):** Across Google production ML fleets, `~20%` of jobs spend over one-third of total compute resources inside the input pipeline.
* **Why GPU-Accelerated Augmentation (DALI / Kornia) Was Excluded:** While NVIDIA DALI reduces host prep stalls at the expense of VRAM, GPU-side affine warping, interpolation, and scalar division introduce floating-point non-associativity and reciprocal-multiplication drift (`F24`), violating ShapeSense's bit-exact cross-iteration reproducibility contract.

### Quantitative Mapping to ShapeSense's `SmallCNN`

With a `242,250`-parameter CNN operating on `(256, 1, 64, 64)` tensors, single-core Python/NumPy augmentation and Pillow synthetic rasterization consumed **`~80%` of step wall-clock time** (`~20 s/epoch`). Moving batch preparation onto a persistent **7-worker `spawn` prefetch pool** reduced epoch latency to **`2.0–6.0 s`** with bit-identical validation scores across worker counts, while explaining why residual epoch-time variance (`2.0 s` vs. `6.0 s`) tracks host CPU saturation (`90%` vs. `99%` aggregate utilization) across arms `A1`, `B`, `A2`, and `P`.

