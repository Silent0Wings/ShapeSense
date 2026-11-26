# 3_modeling - Opus 5.5 checks Gemini 4 Neon's speed and voting audit

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Critiqued output: Gemini 4 Neon (its report is pasted verbatim inside the prompt)
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: C40, C30, C31, F24
- Source: **exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.

## Prompt 1 (21:22)

> process and audit this ====[
>
> <pasted_content id="8717">
> Analyzed prep.py:L1-86
> Analyzed sampling.py:L1-268
> Analyzed train.py:L1-150
> Analyzed train.py:L300-460
> Analyzed train.py:L461-513
> Analyzed batch.py:L1-39
> Analyzed transform.py:L1-160
> Analyzed generate.py:L1-100
> Analyzed render.py:L1-50
> Analyzed train.py:L230-300
> Analyzed search.py:L1-100
> Analyzed sweep.py:L1-100
> Analyzed sweep.py:L150-240
> Analyzed pipeline.yaml:L100-160
>
> ### 1. Model Question: Ensemble / Voting System (Equal Weight vs. Class-Weighted)
>
> #### The Verdict: Start with Equal-Weight Soft Voting (Probability Averaging); Skip Class Weights
>
> * **Why Equal-Weight Soft Voting is superior:**
>   1. **Zero Parameters & No Overfitting:** Averaging predicted softmax probabilities across models ($\frac{1}{M}\sum_{m=1}^M P_m(c)$) has zero tuneable parameters. A model that is 98% confident naturally outweighs one that is 51% confident without any manual calibration.
>   2. **Validation Differences Are Mostly Noise:** Across iterations, the top arms differ on clean validation sets by only 0.2–0.5 points. Tuning a matrix of per-class weights ($M \text{ models} \times 10 \text{ classes} = 50 \text{ parameters}$) will simply overfit the validation split rather than learn genuine domain invariance.
>   3. **The Clean vs. Noisy Distribution Mismatch:** A model trained on clean data might achieve 99% accuracy on clean validation circles, but collapse on deformed freehand sketches. A static high weight for that class will cause it to override more robust models (like A2 or B) precisely when user drawings get messy.
>   4. **Latency / ONNX Footprint:** Running 4–5 ONNX models per sketch in the browser studio will multiply client-side inference time and asset download size by $4\times$–$5\times$. For lightweight CNNs this remains interactive (~15–30 ms), but it is worth exposing in the dashboard as an optional *"All Models Ensemble"* toggle rather than replacing the primary model.
>
> ---
>
> ### 2. Culprits Causing Slow or Unoptimized Code in ShapeSense
>
> Below is the breakdown of the specific bottlenecks identified in the codebase across data loading, augmentation, synthesis, IPC, training, and OS contention:
>
> ---
>
> #### A. Data Augmentation Culprits ([`transform.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage2_augment/transform.py))
>
> 1. **Per-Image Python Loops Instead of Batched Array Operations:**
>    * In [`sampling.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/sampling.py#L206-L207), 256 images per batch are passed through a Python list comprehension:
>      ```python
>      imgs = np.stack([img if i < n_clean else np.asarray(transform(img, int(lbl), rng), dtype=np.uint8)
>                       for i, (img, lbl) in enumerate(zip(imgs, lbls))])
>      ```
>      This triggers 256 individual Python function calls per batch, executing interpreted Python code rather than vectorized C/CUDA tensor operations.
> 2. **Heavy SciPy CPU Filtering Per Image:**
>    * **`scipy.ndimage.affine_transform`**: Executed on CPU per individual image for rotation, scale, and shear.
>    * **`scipy.ndimage.gaussian_filter`**: Executed on CPU whenever blur triggers (`blur_p`).
>    * **`scipy.ndimage.binary_dilation` & `binary_erosion`**: Executed for stroke jitter and thin line preservation.
> 3. **Redundant Feature Recalculations:**
>    * [`ink_coords(img, r.ink_threshold)`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage2_augment/transform.py#L120): Computes `np.flatnonzero` on the $64 \times 64$ grid for every augmented sample to find ink centers and extents. For stored dataset images, bounding boxes and centers could be pre-computed once.
>    * [`_outer_ring`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage2_augment/transform.py#L58-L62): Allocates a fresh boolean mask (`np.ones((size, size), dtype=bool)`) on every single augmented image instead of reusing a pre-allocated constant array.
>    * **Iterative Fit Loop:** Lines 159–162 in `transform.py` run a `while` loop scaling down up to 100 iterations if a shape exceeds the margin.
>
> ---
>
> #### B. Synthetic Data Generation Culprits ([`generate.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage3_synth/generate.py), [`render.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage3_synth/render.py))
>
> 1. **Pillow Canvas Overhead & Supersampling:**
>    * [`render_outline`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage3_synth/render.py#L18-L50) allocates a new Pillow canvas (`Image.new("L", (hi, hi))`) at supersampled resolution ($128 \times 128$).
>    * Iterates through Python lists (`[tuple(p) for p in ring.tolist()]`) and executes Python-level draw calls (`draw.line`, `draw.rectangle`).
>    * Calls Pillow `canvas.resize(..., Image.Resampling.BOX)` and converts back to NumPy arrays (`np.asarray(...)` and `np.where(...)`).
> 2. **Double Transformation for Synthetic Images:**
>    * In Arm B and P, synthetic shapes are first rendered via Pillow/CPU, and then *fed directly into `transform()`* for affine warping, blur, and noise. They pay the cumulative cost of Stage 3 rasterization **plus** Stage 2 SciPy transformations.
>
> ---
>
> #### C. Inter-Process Communication (IPC) & Memory Passing ([`prep.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/prep.py), [`batch.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/common/batch.py))
>
> 1. **Massive Pickled IPC Payloads Over OS Pipes:**
>    * In [`BatchPool`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/prep.py#L59-L81), worker processes return a [`Batch`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/common/batch.py#L19-L23) object containing `images` as `(256, 1, 64, 64)` **float32** arrays.
>    * **Payload size:** Each batch is **4 MB** of uncompressed floats. Over a 60-epoch trial (2,940 steps), **~12 GB of tensor data is serialized with `pickle` and pushed across OS pipes per trial**.
>    * Passing `uint8` images (1 MB) and converting to `float32` directly on the GPU would cut IPC volume by **75%**.
> 2. **Lack of Shared Memory & Page-Locked (Pinned) Memory:**
>    * Python's standard `multiprocessing.Pool.imap` does not use POSIX/Windows shared memory segments or PyTorch's pinned memory buffer (`pin_memory=True`).
>    * The host-to-device transfer in [`train.py` L424](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/train.py#L424):
>      ```python
>      x = torch.from_numpy(batch.images).to(device)
>      ```
>      is a synchronous blocking DMA transfer (cannot use `non_blocking=True`).
>
> ---
>
> #### D. Training Loop & GPU Synchronizations ([`train.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/train.py))
>
> 1. **Per-Step GPU Pipeline Stalls (Synchronous CPU-GPU sync):**
>    * In the inner training loop ([`train.py` L433-434](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/train.py#L433-L434)):
>      ```python
>      loss_sum += float(loss.detach()) * int(y.shape[0])
>      correct += int((logits.argmax(dim=1) == y).sum())
>      ```
>    * Calling `float(...)` and `int(...)` forces CUDA to flush and synchronize the GPU stream on **every single step**, preventing PyTorch from queueing asynchronous GPU operations ahead of time.
> 2. **Deterministic Algorithm Constraints:**
>    * `torch.backends.cudnn.benchmark = False` and `torch.use_deterministic_algorithms(True, warn_only=True)` enforce slower deterministic CUDA kernels.
> 3. **No Mixed Precision (FP32 only):**
>    * The training runs in pure FP32 on an RTX 3080 Laptop GPU without `torch.cuda.amp.autocast()`, bypassing Tensor Cores.
>
> ---
>
> #### E. Validation & Metric Evaluation Overhead ([`train.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/train.py))
>
> 1. **Redundant Float Conversions Every Epoch:**
>    * In [`predict_proba`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/train.py#L230-L253), validation is run every single epoch on all 2,820 validation images:
>      ```python
>      x = torch.from_numpy(to_float(images_u8[start:start + batch_size])).to(device)
>      ```
>    * Calling `to_float` re-allocates and normalizes 2,820 images from scratch 60 times per trial (169,200 redundant image allocations per trial). The validation set never changes and could reside directly in GPU VRAM as a persistent pre-normalized float tensor.
> 2. **Matplotlib Plotting at Trial Completion:**
>    * [`_plot_curve`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/train.py#L270-L297) runs Matplotlib figure layout and font rendering (`Agg`) to save `val_curve.png` at the end of every trial. As seen in stack profiling, font layout and rendering on Windows can take several seconds per trial.
>
> ---
>
> #### F. System, Hardware & OS Contention (Windows Laptop Environment)
>
> 1. **Thermal & Power Sharing (CPU vs. GPU Power Cap):**
>    * On laptop architectures, the CPU and GPU share the same thermal chassis and power budget. Running 7 CPU worker processes at 100% load triggers the GPU's hardware power cap (`clocks_event_reasons.sw_power_cap: Active`), dropping GPU clock speeds.
> 2. **Background Process Contention:**
>    * Active Windows Defender real-time scanning (`MsMpEng`) consumes ~2 full cores scanning temporary python processes and artifacts.
>    * Other background processes (IDE, CMake, shell commands) reduce the cores available for the 7 batch workers, causing epoch duration to swing between 2.2s (clean) and 6–13s (contested).
>
> ---
>
> ### Summary Checklist of Potential Code Speedups
>
> | Area | Bottleneck | Low-Effort / High-Impact Optimization | Result Impact |
> |---|---|---|---|
> | **IPC** | 4 MB float32 batches sent via pipe | Send `uint8` arrays (1 MB); convert to `float32` on GPU | 75% reduction in IPC serialization |
> | **GPU Sync** | `float(loss)` & `int(acc)` every step | Accumulate tensor metrics on GPU; sync once per epoch | Eliminates 49 GPU pipeline flushes per epoch |
> | **Val Eval** | Re-normalizing 2,820 val images 60x | Cache `val_tensors` in VRAM or RAM as float32 once | Eliminates 169k redundant allocations per trial |
> | **Augment** | SciPy per-image filters in Python loop | Precompute ink bounding boxes/centers; reuse outer ring mask | Cuts per-image CPU overhead |
> | **I/O** | Matplotlib chart generation per trial | Generate curve figures in batches or only for winning models | Eliminates multi-second font rasterization lag |
> | **OS** | Windows Defender scanning python/venv | Add exclusion for repo and `.venv` | Eliminates ~2 cores of background CPU contention |
>
> Listed 0 tasks
> Canceled read-only search progress check
> Killed task Read-only search progress check
> Ran check finished search trials
>
> ### 1. Concrete Blueprint to Eliminate Bottlenecks (Without Breaking Reproducibility)
>
> When you are ready to implement optimizations in a future iteration, here is the technical roadmap for how each bottleneck can be solved without altering random seeds or breaking CRISP-DM reproducibility:
>
> ```
> [ Current Pipeline ]
> Worker Process --(4MB float32 pickle via pipe)--> Main Process --> Blocking GPU Copy --> [GPU Step] --> float(loss) sync stall
>                                                                                                       --> int(acc) sync stall
>
> [ Optimized Pipeline ]
> Worker Process --(1MB uint8 array)--> Main Process --> pin_memory / non_blocking --> [GPU Step] (loss & acc stay on GPU)
>                                                                                                --> Sync only at epoch end
> ```
>
> ---
>
> #### Fix 1: Pass Batches as `uint8` Over IPC and Convert on GPU
> * **Where:** [`prep.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/prep.py) and [`sampling.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/sampling.py#L210)
> * **Current Issue:** Workers convert arrays to `float32` in CPU RAM (`to_float`), producing 4 MB per batch. Serializing 4 MB per batch over pipes consumes ~12 GB of IPC throughput per trial.
> * **Optimization:** Keep batches in `uint8` (`256 × 1 × 64 × 64` = 1 MB). Once in the training loop on the main process:
>   ```python
>   # Transferred as uint8 (1 MB), converted to float32 on GPU at high memory bandwidth:
>   x = torch.from_numpy(batch.images_u8).to(device, non_blocking=True).float() / 255.0
>   ```
> * **Impact:** 75% less IPC serialization latency and lower CPU memory bus pressure.
>
> ---
>
> #### Fix 2: Remove Synchronous GPU Stalls in the Inner Loop
> * **Where:** [`train.py` Lines 433–434](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/train.py#L433-L434)
> * **Current Issue:**
>   ```python
>   loss_sum += float(loss.detach()) * int(y.shape[0])   # Forces CUDA pipeline sync
>   correct += int((logits.argmax(dim=1) == y).sum())    # Forces CUDA pipeline sync
>   ```
>   Every batch forces the GPU execution queue to halt and wait for the CPU to read scalar values.
> * **Optimization:** Accumulate metrics as GPU tensors and sync only **once per epoch**:
>   ```python
>   # In the training loop: accumulate directly on GPU (no CPU stalls)
>   loss_sum_tensor += loss.detach() * y.shape[0]
>   correct_tensor += (logits.argmax(dim=1) == y).sum()
>
>   # After all steps in epoch: sync once
>   loss_sum = float(loss_sum_tensor.cpu())
>   correct = int(correct_tensor.cpu())
>   ```
> * **Impact:** Allows CUDA to stream all 49 batches continuously without stopping between steps.
>
> ---
>
> #### Fix 3: Pre-Compute & Cache Validation Tensors in Memory / VRAM
> * **Where:** [`train.py` Line 244](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage4_train/train.py#L244)
> * **Current Issue:** The 2,820 validation images are re-sliced, converted to float32, and copied from CPU to GPU 60 times per trial (169,200 allocations per trial).
> * **Optimization:** Pre-convert the validation set to normalized float32 tensors once at startup:
>   ```python
>   # Created once during store initialization:
>   val_images_tensor = torch.from_numpy(to_float(val_store.images)).to(device)
>   val_labels_tensor = torch.from_numpy(val_labels).to(device)
>   ```
> * **Impact:** Validation passes take ~15 ms instead of hundreds of milliseconds every epoch.
>
> ---
>
> #### Fix 4: Augmentation Caching & Outer-Ring Re-Use
> * **Where:** [`transform.py`](file:///c:/Users/Gica/Github_Clones/ShapeSense/src/stage2_augment/transform.py#L58-L62)
> * **Current Issue:**
>   1. `_outer_ring` allocates a fresh `(64, 64)` boolean array on every augmented image call.
>   2. `ink_coords` re-computes `np.flatnonzero` to find shape bounds for static training images.
> * **Optimization:**
>   * Cache `_outer_ring` as a constant module-level array.
>   * For stored real images, compute `(pts, center)` once at dataset load time and attach them to `ImageStore`.
>
> ---
>
> #### Fix 5: Windows Defender Exclusion
> * **Issue:** Windows Defender (`MsMpEng`) was detected using up to 190% CPU (~2 cores) continuously scanning temporary files, spawned Python processes, and artifacts.
> * **Recommendation:** Adding a folder exclusion for `C:\Users\Gica\Github_Clones\ShapeSense` in Windows Defender settings immediately gives back ~2 cores to the batch workers with zero code changes.
>
> ---
>
> ### 2. Deep Dive: Equal-Weight Ensemble Architecture ("All Models Vote")
>
> When iteration 3 finishes, adding the combined voting model as the next goal will follow this exact design:
>
> #### A. Mathematical Formulation
> Given $M$ models (e.g., $M = 4$ for A0, A1, A2, B, or $M = 5$ including P), each model $m$ produces a softmax probability distribution over $K = 10$ classes:
> $$\mathbf{p}_m = [p_{m,1}, p_{m,2}, \dots, p_{m,10}], \quad \sum_{k=1}^{10} p_{m,k} = 1$$
>
> The ensemble probability vector $\mathbf{P}_{\text{ensemble}}$ is simply the arithmetic mean:
> $$\mathbf{P}_{\text{ensemble}} = \frac{1}{M} \sum_{m=1}^M \mathbf{p}_m$$
> $$\hat{y}_{\text{ensemble}} = \operatorname{argmax}_k \left( P_{\text{ensemble}, k} \right)$$
>
> #### B. Why This Beats Class-Weighted Voting on This Dataset
> 1. **Self-Weighting Property of Softmax:**
>    If Model A is very certain ($\mathbf{p}_A = [0.96, 0.01, \dots]$) and Model B is uncertain/confused between two shapes ($\mathbf{p}_B = [0.48, 0.45, \dots]$), their average automatically favors Model A:
>    $$\frac{0.96 + 0.48}{2} = 0.72 \quad \text{vs.} \quad \frac{0.01 + 0.45}{2} = 0.23$$
>    You get confidence-weighting for free without learning artificial multipliers.
> 2. **Complementary Decision Boundaries:**
>    * **A0:** Trained on pristine real data $\rightarrow$ highest precision on clean, standard drawings.
>    * **A1 & A2:** Trained with affine augmentations $\rightarrow$ resilient to rotations, scale variations, and shear.
>    * **B & P:** Exposed to synthetic primitives $\rightarrow$ robust to unusual geometric aspects and edge topologies.
>    * When a user draws an ambiguous shape, idiosyncratic model blind spots get outvoted by the collective consensus.
>
> #### C. Studio Web & ONNX Implementation
> * In the browser ([`studio/web`](file:///c:/Users/Gica/Github_Clones/ShapeSense/studio/web)), you already have the ONNX runtime running for individual models.
> * To support the ensemble:
>   1. Load the ONNX sessions for all 4–5 final models.
>   2. On canvas input, run inference concurrently (`Promise.all([sessionA0.run(...), sessionA1.run(...), ...])`).
>   3. Average the resulting output tensors in JavaScript with a single loop and display the consensus bar chart.
>
> ---
>
> ### 3. Current Live Status of the Search
>
> * **Current Progress:** **12 of 200 trials finished** in `artifacts/stage4/tuning_iter3/`.
> * **Health:** Running smoothly with zero errors in `run_search3.log`.
> * **Execution:** Proceeding through Phase 5 at the updated speed (~3.6–5s per epoch).
> </pasted_content id="8717">
>
> ]

## Response 1

I'll check this report against the code and against real measurements. The checks are small and CPU-only, so the search isn't disturbed.

All of the report's claims are now checked. I'll register your rule in the CRISP-DM record and add what the audit found about which fixes are worth doing.

**The report's direction is mostly right, but it overstates several fixes and gets some facts wrong.** Its recommended fixes would save little. The largest cost it identifies, CPU contention, needs a decision from you rather than a code change.

**Confirmed**
- Equal-weight voting is the right choice, and its arithmetic checks out.
- The code it points to exists at the lines it cites: per-image Python loops, repeated ink calculations, and a GPU sync on every step.
- 4 MB batches, about 12 GB per trial, and 128×128 supersampling are all correct.

**Wrong or overstated**

| Claim | What I found |
|---|---|
| The browser already runs ONNX | It doesn't. The studio runs models on the server through `/api/infer`, so the `Promise.all` design only applies to Stage 7. |
| Validation caching saves "hundreds of ms" | The conversion takes 43 ms of a roughly 3.4-second epoch, about 1%. The set is also 2,819 images, not 2,820. |
| Matplotlib costs "several seconds" per trial | It costs 0.57 seconds. |
| The fit loop is a culprit | It almost never repeats: 1,529 checks across 1,510 images. |
| The 1 MB batch fix is a big win | It saves at most about 3 ms of a roughly 69 ms step. |
| A hardware power cap causes the slowdown | The counter is a software cap, and slow epochs had a higher GPU clock, not a lower one. |
| `non_blocking=True` fixes the transfer | It does nothing without pinned memory, and the report also says it can't be used. |
| FP32 "bypasses Tensor Cores" | That's imprecise: PyTorch allows TF32 for convolutions by default. |
| A0 has the highest precision on clean data | Not supported: A0 was lowest on validation in iteration 3 and level with the rest on test in iteration 2. |
| All fixes preserve reproducibility | Not proven. Each would need checking that results stay identical. |

**What it missed**
- About 16 seconds of each 220-second trial falls outside the epochs, roughly 7% or about 55 minutes in total. A single long-lived worker pool could recover most of that.
- These fixes must not go in during the search. Workers reload the transform code for every trial, so an edit would silently mix code versions within the search.

**Worth doing, in order**
1. Reduce other CPU load, including the Defender exclusion, which is your call.
2. Cache each image's ink points and thin-line flag, about 18% of the transform's time. That figure comes from a profile.
3. Keep one worker pool across trials.

I've registered your rule in the CRISP-DM record: a speed fix becomes an optimization step under Modeling once it's measured to help. The parallel batch preparation qualifies and is listed. The audited items above are listed as candidates, because none is built yet.

The search is at 14 of 200 with no errors, averaging about 3.7 minutes per trial, and should finish around 5 to 6 a.m.

The 5-minute watcher has been restarted for the next 30 minutes.

The new watcher started at 21:28 with 15 of 200 search trials done.

## Prompt 2 (21:28)

> Defender exclusion done , what are my other options ?

## Response 2

I'll check whether the exclusion made a measurable difference, then lay out what's left.

The new `prep.py` wasn't saved, because the tool wanted a fresh read of the file first, and that explains the two failing tests. Re-reading and writing it.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Opus 5.5 measured each claim on the CPU without disturbing the running search, for example validation conversion 43 ms of a 3.4 s epoch and matplotlib 0.57 s per trial.

## Our decision

We kept the equal-weight vote, which both LLMs agreed on. We dropped the fixes that save little or risk changing results, such as converting pixels on the GPU (F24). No code was changed during the search.

## Measured effect

No change to macro F1. Most of the proposed speed-ups were measured at about 1% or less of a step.

---

##  Comparison: Opus 5.5 Audits of Gemini 4 Neon (File 13 & Cross-File Synthesis)

### 1. What these files are

All four cross-critique files (`11_A14` through `14_real`) record the same pattern: **Claude Opus 5.5 (medium effort, in Claude Code) critiquing Gemini 4 Neon's reports** in a real, saved session. Files `12`–`14` are verbatim exchanges; `11_A14`

| File | Gemini report under review | Opus verdict | Worksheet entries |
|---|---|---|---|
| `12_…checks…gemini-review-of-the-training-document` | Review of the training document (4 precision errors, claims to verify, design points) | Mostly right; 3 of 27 points don't stand | C23–C27 |
| `13_…checks…speed-and-voting-audit` | Speed audit + equal-weight voting design | Direction right, several fixes overstated, some facts wrong | C40, C30, C31, F24 |
| `14_…sub-agents-check…speed-report` | Two-part speed/budget report (search + per-run) | Mostly out of date for iteration-3 code; one reuse point kept | C31, C32, C39 |
| `11_A14_…model-py-still-names-three-blocks` | `model.py` still defaults to three blocks | Stands; fixed in iteration 3 | A14 |

The through-line: **Gemini's findings were checked against code and measurements, not accepted or dismissed wholesale.** Valid points became iteration-3 work; invalid or out-of-date ones were dropped or disclosed.

### 2. File 13 — The speed and voting audit

Gemini's audit made two big claims: **equal-weight soft voting** is the right ensemble choice, and it catalogued speed bottlenecks (data loading, augmentation, synthesis, IPC, training loop, OS contention). Opus measured each claim small and CPU-only so the running search wasn't disturbed.

**Confirmed:**
- Equal-weight soft voting is the right choice, and its arithmetic checks out (self-weighting property of softmax, zero tuneable parameters, complementary decision boundaries).
- The code it cites exists at those lines: per-image Python loops, repeated ink calculations, a GPU sync on every step.
- 4 MB batches, ~12 GB per trial, 128×128 supersampling are all correct.

**Wrong or overstated:**

| Gemini claim | Opus's finding |
|---|---|
| Browser already runs ONNX | It doesn't; studio runs models server-side via `/api/infer`, so `Promise.all` design applies only to Stage 7 |
| Validation caching saves "hundreds of ms" | Conversion takes 43 ms of a ~3.4 s epoch (~1%); set is 2,819 images, not 2,820 |
| Matplotlib costs "several seconds" per trial | 0.57 s |
| Fit loop is a culprit | Almost never repeats: 1,529 checks across 1,510 images |
| 1 MB batch fix is a big win | Saves at most ~3 ms of a ~69 ms step |
| Hardware power cap causes slowdown | Counter is a software cap; slow epochs had a *higher* GPU clock |
| `non_blocking=True` fixes the transfer | Does nothing without pinned memory (and the report says it can't be used) |
| FP32 "bypasses Tensor Cores" | Imprecise: PyTorch allows TF32 for convolutions by default |
| A0 has highest precision on clean data | Not supported: A0 was lowest on validation in iter 3, level on test in iter 2 |
| All fixes preserve reproducibility | Not proven; each needs checking results stay identical |

**What Gemini missed:**
- ~16 s of each 220 s trial falls outside epochs (~7%, ~55 min total); one long-lived worker pool could recover most of it.
- These fixes **must not go in during the search**: workers reload transform code every trial, so an edit would silently mix code versions.

**Worth doing, in order:** (1) reduce other CPU load, including the Defender exclusion (user's call); (2) cache each image's ink points and thin-line flag (~18% of transform time, from a profile); (3) keep one worker pool across trials.

**Outcome:** Equal-weight vote kept (both LLMs agreed). Fixes that save little or risk changing results dropped — e.g., converting pixels on the GPU (F24). No code changed during the search. Measured effect: **no change to macro F1**; most proposed speed-ups were ~1% or less of a step.

### 3. Consolidated verdict ledger

**Gemini claims that stood and became work:** second never-read holdout; arm P; grouped 3-fold CV selection; equal-real/scarcity/budget experiments; damaged-image primary test; all four precision corrections; determinism wording; stale-text extension; all seven design disclosures; equal-weight soft voting; 9-run reuse (~35 min); `SmallCNN` default fix.

**Gemini claims that did not stand or were out of date:** browser-side ONNX; validation-caching magnitude; Matplotlib magnitude; fit-loop culprit; 1 MB batch as big win; hardware power cap; `non_blocking` without pinned memory; "FP32 bypasses Tensor Cores"; A0 clean-data precision; "all fixes preserve reproducibility"; iteration-2 search counts applied to iteration 3; most "zero-risk" training-loop list; GPU augmentation now; pruning/Optuna/smaller top-K (pre-registered rules).

**Deferred or disclosed rather than fixed:** 13 of 27 training-document points; Stage 6 traceability and cache bugs (owner's call); `val_curve.png` removed.

**Measured effects:** no change to macro F1 from the speed work; ~35 min search saving from reuse; iteration-3 headline: A2 beat A0 by **+9.20 macro F1, 95% CI [8.89, 9.53]**, on 4,500 never-read damaged images (C23).

### 4. What ties them together

Three principles recur across all four files:

1. **Check, don't accept.** Every Gemini claim was tested against code, a profile, or a measurement — never accepted on authority. Where Opus couldn't verify (e.g., `configs/pipeline.yaml`, Stages 2–3 in the first review), it said so.
2. **Pre-registration constrains the fixes.** Valid points were folded into iteration 3 *before* any run. Cuts that would violate the pre-registered rules (pruning, Optuna, smaller top-K) were rejected even though they'd have been faster — and the 13 deferred fixes were deferred precisely because fixing them would force a retrain or alter a frozen analysis.
3. **Don't touch a running search.** Shared-code edits during the search would silently mix code versions; the code-only session stopped the search at 16/200 and held everything for approval rather than proceeding. Reproducibility was treated as a first-class constraint, not an afterthought.

