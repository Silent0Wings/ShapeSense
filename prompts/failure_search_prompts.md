# Search prompts for every failure

> **Prompts to run, not a record.** Each failure on the Failure timeline (`results/phase2_snapshot/iteration_log.json`)
> is restated as a research question for an LLM to search: when does this happen in general, and why? All 31 were
> answered by Claude Opus 5.5 with web search on 2026-11-20, saved as `NN_Fnn_*-search.md` in each stage's
> `claude_opus/` folder. Gemini 4 Neon has not been asked yet. Save each exchange you run in the stage's `claude_opus/`, `gemini_4_neon/` or
> `cross_critique/` folder, as `NN_short-title.md` with the template in [README.md](README.md).

## Send this first

> Search the web and the research literature to answer the question below. Cite every claim with a link, and prefer
> papers, official documentation and bug trackers over blogs. Separate what is well established from what is a single
> report or your own reasoning. Then say how the findings apply to our project: a small CNN that classifies 10 shapes in
> 64x64 grayscale images merged from four public sources, with five training arms (A0 real only, A1 real + augmented,
> B real + synthetic, A2 full mix, P synthetic pretraining) compared by macro F1 on sealed test data.

The failures follow the order of the Failure timeline. Each one links to its  prompt, which holds the
documented cause, so you can compare what the search finds with what we found.

## Before this timeline

<a id="f17"></a>

### F17 - The first CNN could not see a whole shape.

- Before iteration 1 · State: Overcome · Record: [F17](3_modeling/inferred_prompts.md#f17)

> How large does a CNN's receptive field need to be, relative to the object, to classify whole shapes? Search for how the theoretical and the effective receptive field are computed (for example Luo et al. 2016 and Araujo et al. 2019) and for evidence on what happens when the receptive field is smaller than the object. Our case: three blocks gave a 22-px receptive field on 64-px images.


## 1. Dropping the diamonds

<a id="f01"></a>

### F01 - Most Quick, Draw! diamonds were not rhombi.

- Iteration 1 · State: Overcome · Record: [F01](2_data_preparation/cleaning/inferred_prompts.md#f01)

> How much label noise and off-definition drawing is there in crowd-sourced sketch datasets such as Quick, Draw!, and how do published works detect and handle samples that do not match a class's definition (drop, relabel or keep)? How much label noise can a small CNN tolerate before a class's accuracy drops? Our case: most Quick, Draw! 'diamonds' were gems, cones or shields, not rhombi.


## 2. Training and the first evaluation

<a id="f02"></a>

### F02 - Leave-one-source-out training could not run on all ten classes.

- Iteration 1 · State: Partly · Record: [F02](3_modeling/inferred_prompts.md#f02)

> How do domain-generalization studies run leave-one-domain-out evaluation when some classes exist in only one domain? Search for protocols for partial or open domain generalization and for how they score a held-out domain that lacks some classes. Our case: ellipses exist only in the Hand-Drawn source.

<a id="f03"></a>

### F03 - Stage 4 stalled on the GPU.

- Iteration 1 · State: Overcome · Record: [F03](3_modeling/inferred_prompts.md#f03)

> Why does PyTorch training stall or slow down sharply when several training processes share one 8 GB GPU? Search for what is known about GPU memory oversubscription, CUDA context overhead per process and how to size the number of parallel runs.

<a id="f04"></a>

### F04 - B vs A1 failed: -0.36 points, CI [-1.17, 0.41], and A0 with no augmentation scored highest.

- Iteration 1 · State: Verdict stands · Record: [F04](4_testing/inferred_prompts.md#f04)

> When does adding synthetic images to augmented real images fail to beat augmented real images alone, and when does augmentation lose to no augmentation at all? Search for studies where synthetic data or heavy augmentation gave no gain or hurt image classification, and for the reasons they give (synthetic-to-real gap, label-changing augmentation, a reduced share of real images per batch, untuned hyperparameters). Our case: B (real + synthetic) vs A1 (real + augmented) failed at -0.36 macro F1 points, and A0 with no augmentation scored highest.


## 3. Finding out why

<a id="f05"></a>

### F05 - The images reveal which source they came from.

- Iteration 2 · State: Partly · Record: [F05](1_data_integration/inferred_prompts.md#f05)

> Can a classifier tell which dataset an image came from, and what does that mean for a model trained on the merged datasets? Search for work on dataset bias and the 'Name That Dataset' experiment (Torralba and Efros 2011), shortcut learning (Geirhos et al. 2020), and how to measure and report the risk. Our case: a classifier named the source 91.7% of the time against a 46.7% baseline.

<a id="f06"></a>

### F06 - Augmentation and generator ranges were set by hand, and only A1 was tuned.

- Iteration 2 · State: Overcome · Record: [F06](3_modeling/inferred_prompts.md#f06)

> Is it a fair comparison to tune hyperparameters on one method and reuse them for the others? Search for evidence on tuning-budget bias in ML comparisons (for example Melis et al. 2018 and Bouthillier et al. 2021) and for recommended protocols when arms differ in their training data.

<a id="f07"></a>

### F07 - Rotation up to ±180° hurt the classes that depend on orientation.

- Iteration 2 · State: Overcome · Record: [F07](2_data_preparation/transformation/inferred_prompts.md#f07)

> When does rotation augmentation hurt classes whose identity depends on orientation (square vs diamond, rectangle orientations)? Search for work on label-preserving vs label-changing augmentation and on class-dependent effects of augmentation (for example Balestriero et al. 2022), and for how safe ranges are chosen per class.

<a id="f08"></a>

### F08 - Augmented shapes came out about 6 px too small.

- Iteration 2 · State: Overcome · Record: [F08](2_data_preparation/transformation/inferred_prompts.md#f08)

> How do geometric augmentations shift object scale and framing away from the real data, and how much does a train-test scale mismatch cost a CNN? Search for evidence such as FixRes (Touvron et al. 2019) and for how augmentation pipelines keep object size realistic. Our case: augmented shapes filled about 51 px against 57 px for real images.

<a id="f09"></a>

### F09 - 1-px strokes broke into pieces after warping.

- Iteration 2 · State: Overcome · Record: [F09](2_data_preparation/transformation/inferred_prompts.md#f09)

> Why do 1-px lines break into pieces under affine warping and interpolation, and which methods keep thin strokes connected (warping vector strokes before rasterizing, anti-aliasing, morphological closing, supersampling)? Search image processing and sketch-recognition sources.

<a id="f10"></a>

### F10 - Synthetic strokes were thinner than real ones.

- Iteration 2 · State: Overcome · Record: [F10](2_data_preparation/transformation/inferred_prompts.md#f10)

> How much does a mismatch in low-level statistics such as stroke width between synthetic and real images contribute to the synthetic-to-real gap? Search for studies that compare matching synthetic statistics to the real data with domain randomization. Our case: synthetic strokes were 2 px against about 3.1 px real.

<a id="f11"></a>

### F11 - A1 was still improving when training ended, and early stopping is unstable.

- Iteration 2 · State: Partly · Record: [F11](3_modeling/inferred_prompts.md#f11)

> When is early stopping unreliable, and how should the training budget be set fairly across compared methods? Search for evidence on noisy validation curves at high learning rates, methods that are still improving when the budget ends, and fixed-budget comparison protocols. Our case: validation swung by up to 30 points between epochs at learning rate 0.003.

<a id="f12"></a>

### F12 - The first polarity experiment gave invalid results.

- Iteration 2 · State: Overcome · Record: [F12](3_modeling/inferred_prompts.md#f12)

> How can state leak between reused worker processes in Python multiprocessing (patched modules, global variables, maxtasksperchild), and what are the reproducibility best practices for experiments run through process pools?


## 4. The second evaluation

<a id="f13"></a>

### F13 - The test split had already been read in iteration 1.

- Iteration 2 · State: Partly · Record: [F13](4_testing/inferred_prompts.md#f13)

> What happens to the validity of a test set after it has been read and used for decisions? Search for work on adaptive overfitting and test-set reuse (Recht et al. 2019 on ImageNet, the reusable holdout of Dwork et al. 2015) and for when a fresh holdout is needed.

<a id="f14"></a>

### F14 - A2 vs A0 failed: +0.06 on test and +0.08 on the fresh holdout, both CIs include 0.

- Iteration 2 · State: Still open · Record: [F14](4_testing/inferred_prompts.md#f14)

> When does a model trained on real + augmented + synthetic data fail to beat a model trained on real data alone, and why? Search for studies where synthetic data or augmentation gave no gain on in-distribution test images but did help on out-of-distribution, unseen-source or corrupted images, and for what the authors concluded. Our case: A2 (full mix) vs A0 (real only) gained only +0.06 on test and +0.08 on a fresh holdout, both CIs including 0, from the same sources used in training.


## 5. Closing out

<a id="f15"></a>

### F15 - Drawing on the live page failed once the fourth arm was added.

- Iteration 2 · State: Overcome · Record: [F15](4_testing/inferred_prompts.md#f15)

> What makes client-side inference break when the number of models on a web page grows? Search for known limits and best practices for loading several ONNX models in ONNX Runtime Web (memory per session, hard-coded model lists, lazy loading).

<a id="f16"></a>

### F16 - A clean clone could not find the tuning result.

- Iteration 2 · State: Overcome · Record: [F16](4_testing/inferred_prompts.md#f16)

> Why do ML results that run in the working folder fail on a clean clone, and what do reproducibility checklists recommend (committed artifacts vs generated ones, data and artifact versioning, clean-clone tests)? Search for the NeurIPS reproducibility checklist and similar guidance.


## 6. Iteration 3

<a id="f18"></a>

### F18 - A time limit killed the second holdout build.

- Iteration 3 · State: Overcome · Record: [F18](1_data_integration/inferred_prompts.md#f18)

> How should long data builds handle being killed part way (time limits, interruptions)? Search for best practices such as writing to a temporary folder and renaming atomically, manifests and checksums, and resumable builds.

<a id="f19"></a>

### F19 - The first launch of the validation experiments crashed.

- Iteration 3 · State: Partly · Record: [F19](3_modeling/inferred_prompts.md#f19)

> What causes 'invalid handle' errors in Python's concurrent.futures.ProcessPoolExecutor on Windows, where processes start with the spawn method and workers are started on demand as jobs arrive? Search the CPython bug tracker and forum threads for known causes and fixes, and for whether multiprocessing.Pool, which starts every worker at once, avoids the problem. Our case: the error came back with no code edits during start-up.

<a id="f20"></a>

### F20 - The 108-trial experiment run hung silently after 6 trials.

- Iteration 3 · State: Partly · Record: [F20](3_modeling/inferred_prompts.md#f20)

> Why can a Python multiprocessing pool hang silently, with workers waiting for work and the parent waiting for results? Search for known causes (a worker dying, a pickling failure, deadlocks after fork or spawn) and for how long jobs detect stalls (timeouts, watchdogs, faulthandler).

<a id="f21"></a>

### F21 - Image preparation made training about five times slower than the GPU allowed.

- Iteration 3 · State: Partly · Record: [F21](3_modeling/inferred_prompts.md#f21)

> How often is the input pipeline, not the GPU, the bottleneck in training small CNNs, and how is it fixed? Search for work on data stalls (for example Mohan et al. 2021), the cost of CPU augmentation, and prefetching with several worker processes. Our case: image preparation made training about five times slower than the GPU allowed.

<a id="f22"></a>

### F22 - The search stopped at 66 of 191 trials with a GPU error.

- Iteration 3 · State: Partly · Record: [F22](3_modeling/inferred_prompts.md#f22)

> What causes a cuDNN execution failure (CUDNN_STATUS_EXECUTION_FAILED) part way through a long PyTorch training search on a Windows desktop GPU, when the system log shows no driver error? Search for known causes (driver timeout detection and recovery, other programs releasing or claiming the GPU, memory pressure, overheating) and for how long searches checkpoint and resume safely. Our case: it happened at 66 of 191 trials, while other programs were being closed.

<a id="f23"></a>

### F23 - The first shared worker pool had five bugs.

- Iteration 3 · State: Overcome · Record: [F23](3_modeling/inferred_prompts.md#f23)

> What are the common pitfalls when building a persistent shared worker pool for batch preparation? Search for known issues with random seeds across workers (for example the duplicated NumPy seed in PyTorch DataLoader workers), shared memory, error propagation and clean shutdown.

<a id="f24"></a>

### F24 - Converting pixels on the GPU would have changed every result.

- Iteration 3 · State: Overcome · Record: [F24](3_modeling/inferred_prompts.md#f24)

> Why does moving image preprocessing (uint8 to float conversion, resampling) from the CPU to the GPU change numerical results? Search for sources on floating-point differences between CPU and GPU, cuDNN nondeterminism and how to keep a pipeline bit-for-bit reproducible.

<a id="f25"></a>

### F25 - The GPU looked idle in Windows Task Manager during training.

- Iteration 3 · State: Overcome · Record: [F25](3_modeling/inferred_prompts.md#f25)

> Why does Windows Task Manager show the GPU as almost idle during CUDA training? Search for which engines Task Manager graphs by default (3D, copy, video vs CUDA or compute) and for the right tools to measure GPU use (nvidia-smi).

<a id="f26"></a>

### F26 - Stage 6 could pass with a failed report check.

- Iteration 3 · State: Overcome · Record: [F26](4_testing/inferred_prompts.md#f26)

> How can a pipeline stage report success while one of its checks failed? Search for common causes (ignored subprocess exit codes, exceptions caught and logged, a missing set -e) and for fail-closed practices in ML and CI pipelines.

<a id="f27"></a>

### F27 - Report macro names broke for arm A2 and collided for hold-out runs.

- Iteration 3 · State: Overcome · Record: [F27](4_testing/inferred_prompts.md#f27)

> Why can LaTeX macro names generated from data break or collide (digits are not allowed in control-word names, different keys mapping to the same name)? Search for LaTeX macro naming rules and for safe ways to feed computed numbers into a LaTeX report (csname, datatool, key-value storage). Our case: arm A2 and the hold-out-source runs.

<a id="f28"></a>

### F28 - Report Section K would have shown iteration 3 numbers.

- Iteration 3 · State: Overcome · Record: [F28](4_testing/inferred_prompts.md#f28)

> How do reproducible reports make sure each section shows the numbers of its own experiment or iteration and not newer ones? Search for practices around frozen result snapshots, provenance and versioned outputs in literate programming and ML reporting.

<a id="f29"></a>

### F29 - The dashboard listed arm P twice.

- Iteration 3 · State: Overcome · Record: [F29](4_testing/inferred_prompts.md#f29)

> How do you make a data correction or migration script idempotent, so running it twice does no harm? Search for idempotency patterns in database migrations and data-fix scripts.

<a id="f30"></a>

### F30 - The first vote comparison scored an empty class as zero.

- Iteration 3 · State: Overcome · Record: [F30](3_modeling/inferred_prompts.md#f30)

> How should macro F1 handle a class that has no predictions or no true samples in a subset? Search for how scikit-learn's zero_division setting works, for how papers treat undefined per-class F1 (for example Opitz and Burst 2019), and for the effect on comparisons between models.

<a id="f31"></a>

### F31 - The page for failure F14 showed iteration 3 numbers.

- Iteration 3 · State: Partly · Record: [F31](4_testing/inferred_prompts.md#f31)

> How do experiment dashboards keep historical views stable while new runs keep arriving? Search for practices in experiment tracking tools (immutable run records, snapshots per release) and for how a page can be pinned to the frozen record of its own iteration.
