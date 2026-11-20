#  prompts: 3_modeling

> **These are reconstructions, not the original prompts.** The original prompts are not reproduced here.
> Each prompt below was inferred afterwards from the failure log (`results/phase2_snapshot/iteration_log.json`)
> and the project documentation. The failure, its cause and how it was handled are copied from that log.
> No LLM response is reproduced here.
> Each **Answer** below was written on 2026-11-20 from the recorded cause, outcome and results. It is not the original LLM reply.

<a id="f02"></a>

## F02 - Leave-one-source-out training could not run on all ten classes.

- Iteration: Iteration 1
- LLM: gemini_4_neon
- State: Partly
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> Leave-one-source-out training fails because one class exists in only one source. How do we design a hold-out-source test that is still valid with this class imbalance across sources?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
The run fails because ellipses exist only in the Hand-Drawn source: hold that source out and the training store has no ellipse image, so the sampler cannot fill the class. No hardware or training change fixes that. A valid design restricts the hold-out runs to the classes that remain:
- Train those runs on nine classes. Leave the lost class out of real and synthetic sampling and out of validation macro-F1. An ordinary run with an empty class should still fail loudly.
- Score the held-out models only on the Hand-Drawn classes they could have learned, here triangles and rectangles (302 test images, `results/phase2_snapshot/per_source.csv`). Report the result separately as "unseen-source generalization", not as part of the 10-class comparison.
- Do not use synthetic-only ellipses as a stand-in. That would turn the check into a synthetic-to-real test.

Opus recommended this 9-class option over a synthetic-only ellipse or dropping the hold-out, and the user chose it (`prompts/3_modeling/claude_opus/16_d04-move-training-to-gpu-machine.md`). To check it, confirm that a hold-out run trains on nine classes and that an ordinary run with an empty class still raises. In iteration 3, hold-out accuracy ran from 63.6% to 72.2% across arms and seeds (`per_source.csv`). Ellipse generalization to an unseen source stays untested, which is why the entry is only Partly solved.

**Documented cause:** Ellipses exist only in the Hand-Drawn source.

**Documented outcome:** Runs use nine classes and are scored on Hand-Drawn triangles and rectangles only.

<a id="f03"></a>

## F03 - Stage 4 stalled on the GPU.

- Iteration: Iteration 1
- LLM: none (40248536)
- State: Overcome
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> Stage 4 training stalls on an 8 GB GPU when several runs start in parallel. What is the likely cause, and how many parallel runs are safe?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
The likely cause is GPU memory, not compute. Each parallel run is its own process with its own CUDA context, model, optimizer state and batches. The parent process also keeps its GPU memory after the loader benchmark, so 3 run workers meant 4 GPU processes on the 8 GB card. Once the card filled, the runs stalled instead of failing (the comment on `train.parallel_runs` in `configs/pipeline.yaml`). The safe number is two (three GPU processes counting the parent), set as `train.parallel_runs: 2`. With that limit all 32 trainings finished (F03 in `docs/crisp_dm/iteration_log.json`). Check it by watching per-process memory in `nvidia-smi` through a full epoch. Changing the number does not change results, because each run is deterministic from its (arm, seed). Iteration 3 later moved to one run at a time so that the batch-preparation pools are not nested.

**Documented cause:** Too many training workers ran at once for 8 GB of memory.

**Documented outcome:** Limited training to two parallel runs.

<a id="f06"></a>

## F06 - Augmentation and generator ranges were set by hand, and only A1 was tuned.

- Iteration: Iteration 2
- LLM: both (mediated, proposed by gemini_4_neon)
- State: Overcome
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> We tuned the learning rate and dropout on arm A1 only and reused them for every arm, and set augmentation ranges by hand. Is that a fair comparison? Design a per-arm search on validation only.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
No. A setting tuned on A1 is A1's best setting, and the other arms train on different data (clean only, or with synthetic images), so the same learning rate and dropout can under- or over-regularize them. The hand-set ranges, such as ±180° rotation, were a second confound. A fair per-arm search on validation only:
1. Hold fixed for every arm: the architecture, optimizer, batch size, 49 steps per epoch and the epoch budget.
2. Search each arm's own data settings with trial counts and a search seed fixed in the pre-registration: augmentation on A1, generator ranges and synthetic share on B, batch shares on A2.
3. Run the same 3 × 2 grid of learning rate and dropout for every arm, A0 included, on that arm's best setting.
4. Re-run the top settings on seeds 0, 1 and 2 and keep the highest three-seed mean. Keep the test split sealed and report the trials per arm.

Iteration 2 ran this as 166 trials. A1 rose from 90.64 with hand-set ranges to 94.77 (F06 in `docs/crisp_dm/iteration_log.json`). The winners were A0 92.61, A1 94.77, B 94.20 and A2 95.17, with 6, 30, 22 and 18 trials (`docs/crisp_dm/iteration_2/search/winners.json`). One limit stays disclosed in the outside-review log: in iteration 2, B and A2 kept the augmentation settings searched on A1, and only their generator and mix were searched.

**Recommended (summary, from the worksheet notes):** the team was split, most blaming the data and others the training. Gemini 4 Neon proposed a compute-heavy per-arm search of augmentation, generator and hyperparameters on validation (about 2 days, hundreds of models), and both LLMs mediated between the two views. No chat export is in the repo yet.

**Documented cause:** Iteration 1 tuned learning rate and dropout on A1 alone and reused the result for every arm.

**Documented outcome:** Searched augmentation, generator and hyperparameters per arm on validation: 166 trials.

<a id="f11"></a>

## F11 - A1 was still improving when training ended, and early stopping is unstable.

- Iteration: Iteration 2
- LLM: none (40297573)
- State: Partly
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> A1 is still improving at the end of the 30-epoch budget, and validation swings by up to 30 points between epochs. Should we change the budget or early stopping, and how do we keep the comparison fair between arms?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Probably yes, but change it for every arm at once and only under a rule written before the results are seen. Never tune the budget per arm. When validation can swing by 30 points between epochs at learning rate 0.003, patience-based early stopping can end a run on a random dip. So within iteration 2 the right move was to keep 30 epochs with early stopping for all arms, as was done. Iteration 3 then tested three options on A0, A1 and A2 with three seeds each: 60 epochs, 30 epochs with no stopping, and 60 epochs with no stopping. The pre-registered rule was to adopt one only if every tested arm gained at least 0.5 validation points. In `results/phase2_snapshot/exp_budget.json`, 60 epochs with early stopping lost points (A0 −3.37, A1 −1.53, A2 −1.02, and A0 stopped after 12.7 epochs on average). 60 epochs with no stopping gained A0 +1.99, A1 +0.51 and A2 +0.71, so it was adopted for every arm. To check, look at the per-epoch validation curves and the three-seed gain over the 30-epoch baseline.

**Documented cause:** The budget is 30 epochs, and at learning rate 0.003 validation scores can swing by 30 points between epochs.

**Documented outcome:** Kept the same budget and early stopping for every arm so the comparison stays fair. Not fixed in iteration 2, whose results stay at 30 epochs. Iteration 3 trained every arm for 60 epochs with no early stopping.

<a id="f12"></a>

## F12 - The first polarity experiment gave invalid results.

- Iteration: Iteration 2
- LLM: none (40253714)
- State: Overcome
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> Our polarity experiment gives strange results. Could state leak between reused worker processes? How do we check, and how do we rerun it safely?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Yes, and that is what happened. When a pool reuses its worker processes, a patch applied inside one task (here, the polarity change) stays in that process. Later tasks that expected the standard setting then run with it too, so conditions mix depending on which worker picked up which task. To check, log the setting actually in force and the process id in every task, or rerun a few conditions in fresh processes and compare. Results that depend on which worker ran them show the leak. To rerun safely, give every task a fresh worker (one task per worker) or pass the condition through the config instead of a patch, and throw away the contaminated results. The valid rerun showed no polarity effect, three seeds each: A0 91.69 standard against 91.93 inverted, and A1 93.62 against 93.57, within seed noise (F12 in `docs/crisp_dm/iteration_log.json`). The iteration 2 investigation also found no polarity bug (`docs/crisp_dm/iteration_2/investigation/report.md`).

**Documented cause:** A patch leaked between reused worker processes.

**Documented outcome:** Discarded it and reran with one task per worker. Polarity made no difference.

<a id="f17"></a>

## F17 - The first CNN could not see a whole shape.

- Iteration: Before iteration 1
- LLM: gemini_4_neon
- State: Overcome
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> Can our three-block CNN see a whole shape on a 64x64 image? Compute its receptive field and suggest a change if it is too small.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
No. Each 3x3 convolution adds 2 × the current jump to the receptive field, and each 2x2 max pool adds 1 × the jump and then doubles it. That gives 4, 10 and 22 px after blocks 1 to 3, on an 8x8 map. A typical standardized shape spans about 55 px of the 64-px image (F17 in `docs/crisp_dm/iteration_log.json`). So no unit before global average pooling sees a whole shape, and no single unit can compare opposite sides, which square vs rectangle and hexagon vs octagon need. Add a fourth block: the field grows to 46 px on a 4x4 map. Keep that block at 128 channels (32/64/128/128), which gives 242,250 parameters (`results/phase2_snapshot/loader_benchmark.json`). Make the change once, for every arm, before any arm trains. To check, compute the field from the real module list. `tests/studio/test_architecture_recipes.py` asserts 46 px. This is the theoretical field. The effective field is smaller, and no accuracy comparison of three against four blocks is recorded.

**Documented cause:** Three blocks gave a 22-px receptive field on 64-px images.

**Documented outcome:** Moved to four convolution blocks.

<a id="f19"></a>

## F19 - The first launch of the validation experiments crashed.

- Iteration: Iteration 3
- LLM: gemini_4_neon (assisted, proposed by 40297573)
- State: Partly
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> The validation experiments crash at launch with an invalid-handle error from the worker pool on Windows. What is the cause, and how do we make the pool reliable?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
On Windows, Python starts worker processes with spawn, and `ProcessPoolExecutor` (used for runs in `src/stage4_train/sweep.py`) starts its workers on demand as jobs arrive. The first explanation, code edited during start-up, was ruled out when the same error came back with no edits. The records point to the on-demand start on Windows, but the exact root cause is not established, which is why the entry is only Partly solved. To make the pool reliable:
- Start every worker at once. `src/stage4_train/prep.py` uses `multiprocessing.get_context("spawn").Pool`, and its docstring states the reason.
- Keep workers from re-importing PyTorch, which had cost about 2 minutes a trial (`docs/crisp_dm/README.md`).
- Put a time limit on every batch (`BATCH_TIMEOUT_S = 600`), so a dead worker raises an error instead of hanging.
- Train one run at a time, so the pools are not nested.
- Never edit training code while a job runs.

To check, relaunch several times and run the pool tests in `tests/stage4/test_prep.py`.

**Documented cause:** The worker pool broke with an invalid-handle error. It was first blamed on the training code being edited during start-up, but the same error came back later with no edits, in the way Python starts pool workers on demand on Windows.

**Documented outcome:** Relaunched at first. Training later replaced that pool with one that starts every worker at once and turns a stalled batch into an error.

<a id="f20"></a>

## F20 - The 108-trial experiment run hung silently after 6 trials.

- Iteration: Iteration 3
- LLM: opus_medium_5.5 + 40256377
- State: Partly
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> A 108-trial run hung silently after 6 trials, with no error in the log. How do we find out why, and how do we detect a stall in long jobs?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
To find out why, get stack dumps from the stuck parent and workers before killing them, for example with Python's `faulthandler`. A silent deadlock, where workers wait for work while the parent waits for results, leaves nothing in an ordinary log. In this case the cause was never established. The job used the same on-demand worker pool as F19, but that link is not proven. To catch a stall:
- Make every wait time-limited, so a stall becomes an error. Batch preparation now does this with `BATCH_TIMEOUT_S = 600` in `src/stage4_train/prep.py`.
- Keep per-trial result files, so a stopped job can be relaunched without losing finished trials.
- Run an outside watcher that checks progress on a fixed interval. The project now runs one every 5 minutes on every long job (`docs/crisp_dm/README.md`).

The cost of not watching is on record: 6 trials were done at 12:11, the hang was found at 14:28, and the job was relaunched at 14:31 with the finished trials reused (F20 in `docs/crisp_dm/iteration_log.json`).

**Documented cause:** Not established. The workers waited for work while the parent waited for results, with no error in the log, and nothing was watching for a stall. It used the same on-demand worker pool as F19, but that link is not proven.

**Documented outcome:** Found about 2 hours 17 minutes later, on a status request. Stopped that job and relaunched it with the finished trials reused. Long jobs now run with a stall watcher checked every 5 minutes. Training later stopped using that worker pool.

<a id="f21"></a>

## F21 - Image preparation made training about five times slower than the GPU allowed.

- Iteration: Iteration 3
- LLM: none (40253714)
- State: Partly
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> Training is much slower than the GPU allows. Profile one step: where does the time go, and how do we move augmentation and synthetic drawing off the training thread without changing results?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Time one step in two parts: building the batch, and the GPU forward and backward pass. Here, building a batch took 226 to 376 ms against about 70 ms for the GPU step, so image preparation was about 80% of each step. It ran on one CPU core while the GPU waited (`docs/crisp_dm/README.md`). To move it off the training thread without changing results:
1. Give each step its own random generator, derived from (seed, epoch, step) (`step_rng` in `src/stage4_train/sampling.py`). Then a batch does not depend on which process built it, or when.
2. Build whole batches in a pool of worker processes, not threads, because most of this code is Python and threads would contend for the interpreter lock. Here that is 7 processes, ahead of the GPU.
3. Prove equality: batches from the pool must match the single-process stream, and validation scores must be identical at different process counts.

Result: an epoch fell from about 20 s to 2 to 6 s, with identical scores at 4 and 7 processes (F21 in `docs/crisp_dm/iteration_log.json`). Note that the new per-step generator gives a different random stream from the one the earlier validation experiments used. The slow epochs that remain come from other load on the machine: the CPU was 99% busy in slow epochs against 90% in fast ones, and Windows Defender used about 2 cores (`docs/crisp_dm/README.md`).

**Documented cause:** Augmentation and synthetic drawing ran on one CPU core, on the training thread, taking about 80% of every step while the GPU waited.

**Documented outcome:** Batches are now built by 7 processes, so an epoch fell from about 20 seconds to between 2 and 6 seconds. Validation scores were identical at different process counts. The slow epochs come from the rest of the machine: the CPU was 99% busy in them, against 90% in fast ones, with no change in temperature.

<a id="f22"></a>

## F22 - The search stopped at 66 of 191 trials with a GPU error.

- Iteration: Iteration 3
- LLM: gemini_4_neon + 40256377 + 40211352
- State: Partly
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> The search stopped at trial 66 of 191 with a cuDNN execution failure. Is the GPU damaged, and how do we resume without losing the finished trials?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Probably not damaged. A single cuDNN execution failure with no GPU driver error in the system log points to a passing disruption, and it happened while other programs were being closed. The cause is recorded as not established. To check, run `nvidia-smi` to confirm the card is visible and to find any leftover Python process holding memory, kill it, and run a short GPU test. Here the test passed. To resume, relaunch exactly one copy from the same config and code. The search reuses any finished trial whose saved settings match exactly (`src/stage4_train/search.py`), so only the interrupted trial is lost. All 66 finished trials carried over (F22 in `docs/crisp_dm/iteration_log.json`). Opus's real session reported the same, and also advised not closing GPU-related programs during the run in case that was the trigger (`prompts/3_modeling/claude_opus/38_real_is-training-on-the-right-gpu.md`). If the same failure comes back after a clean relaunch, stop and investigate, as the long-job recovery rule (C37) says.

**Documented cause:** Not established. cuDNN reported an execution failure during a training step. It happened around the time other programs were being closed, and no GPU driver error appears in the system log.

**Documented outcome:** Confirmed the GPU still worked, stopped the leftover process and relaunched. The 66 finished trials carried over.

<a id="f23"></a>

## F23 - The first shared worker pool had five bugs.

- Iteration: Iteration 3
- LLM: opus_medium_5.5
- State: Overcome
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> Audit our new shared worker pool for bugs: leftover temporary files after a crash, cleanup that hides the real error, reused file paths, and failed restarts.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
The audit found five bugs, and each has a small fix:
1. A crash inside the training loop skipped closing the batch streams and left temporary stream files behind. Wrap the loop in `try/finally` so the streams always close.
2. Deleting the temporary file during cleanup could raise on Windows while a worker still held it, which hid the real training error. Suppress that error so cleanup can safely run twice.
3. Workers cache a stream by its file path, so a reused temporary path could give a worker the wrong data. Add a running number to every temporary file name (`_STREAM_NUMBERS`).
4. A failed pool restart left a dead pool in the shared entry. Clear the entry first, and record the new pool only once it has started (as `_shared_pool` in `src/stage4_train/prep.py` now does).
5. A failure while writing the stream file left it behind. Close and delete it on any error.

The details of each fix come from the reconstructed Opus file `prompts/3_modeling/claude_opus/19_F23_the-first-shared-worker-pool-had-five-bugs.md`. The real session is `36_real_complexity-diagram-and-code-only-audit.md`. To check: tests that one shared pool serves successive runs with batches identical to the single-process stream, plus full reruns compared on every logged number. Both passed: the reruns matched exactly (F23 in `docs/crisp_dm/iteration_log.json`).

**Documented cause:** A crash during training left temporary files behind, a repeat cleanup could hide the real error, a reused file path could give a worker the wrong data, and a failed pool restart left a dead entry.

**Documented outcome:** A code audit found and fixed all five before they caused harm. Tests passed and reruns matched exactly.

<a id="f24"></a>

## F24 - Converting pixels on the GPU would have changed every result.

- Iteration: Iteration 3
- LLM: none (40211352)
- State: Overcome
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> An outside report recommends converting pixels to float on the GPU (divide by 255) to speed up training. Will that change any results compared with the CPU path? Measure it before we adopt it.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Yes, it would change results. Float division on the GPU does not always round the same way as the CPU conversion. Measured over all 256 pixel values, dividing by 255 on the GPU gave a different float for 126 of them (F24 in `docs/crisp_dm/iteration_log.json`). Every input would shift slightly, so no result could be reproduced exactly. To measure it, convert `np.arange(256)` both ways and count the values that are not bit-identical. Keep the speed gain without the drift: send the batch as uint8 bytes and index a 256-entry lookup table built from the exact CPU values. This is `pixel_values` in `src/stage4_train/train.py`. The gain is small, at most about 3 ms of a roughly 69 ms step (`docs/crisp_dm/README.md`). Exactness was confirmed by full reruns that matched earlier trials on every logged number.

**Documented cause:** Dividing by 255 on the GPU rounds 126 of the 256 pixel values differently from the CPU. An outside report had recommended exactly that.

**Documented outcome:** Measured it before using it, and used a lookup table of the exact CPU values instead.

<a id="f25"></a>

## F25 - The GPU looked idle in Windows Task Manager during training.

- Iteration: Iteration 3
- LLM: gemini_4_neon + 40253714
- State: Overcome
- CRISP-DM step: Modeling · Pipeline stage: 4 · Training

** prompt**

> Windows Task Manager shows the GPU idle during training. Is training really running on the RTX 3080?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Yes. Task Manager's default GPU graphs show 3D, copy and video work, not CUDA compute, so they read 0% while training runs. Check with `nvidia-smi -l 2` instead: the training process should be listed on the RTX 3080 as a compute process, with dedicated memory in use. Also check the device saved in each run's record. The config pins `train.device: cuda`, so a run stops with an error instead of falling back to another device. In the real Opus session the `nvidia-smi` output showed the training process on the RTX 3080 holding 2,733 MiB. Its use swung between 0% and 96%, averaging about 44%, because the GPU waits for the CPU to prepare the next batch (`prompts/3_modeling/claude_opus/38_real_is-training-on-the-right-gpu.md`). That swing is expected and is not a fault. It shows that batch preparation on the CPU, not the GPU, limits speed.

**Documented cause:** Task Manager's default GPU graphs do not include CUDA compute work, so the training GPU read 0% while it was busy.

**Documented outcome:** Confirmed with nvidia-smi and the run records that training was on the RTX 3080. Its use swings between 0% and 96% as it waits for the next batch.

<a id="f30"></a>

## F30 - The first vote comparison scored an empty class as zero.

- Iteration: Iteration 3
- LLM: opus_medium_5.5 + 40248536
- State: Overcome
- CRISP-DM step: Modeling · Pipeline stage: 6 · Report and export

** prompt**

> Our vote comparison scores some classes as zero on a random half of validation. Why, and how should we split and score so absent classes do not count?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Validation is split by near-duplicate group, and some groups are large. So a random half can hold no image of a class at all. Macro-F1 then scores that class as zero, which cost 10 points, and per-class weights learned on that half get a zero for it (F30 in `docs/crisp_dm/iteration_log.json`). The fix:
- Balance the two halves by class, still keeping each group whole.
- Leave out of the score any class absent from the scored half.
- Give equal weights to any class missing from the learning half.
- Add a test with a half that lacks a class.

With that fixed, the held-apart comparison gave equal weights 95.59 against per-class weights 94.80 (`results/phase2_snapshot/exp_vote_check.json`). Those numbers reuse validation, so they are optimistic.

**Documented cause:** Near-duplicate groups are large, so a random half of validation could hold no image of a class, which cost 10 macro-F1 points and gave the per-class weights a zero.

**Documented outcome:** Halves are now balanced by class, absent classes are left out of the score, and a class missing from the learning half gets equal weights. A test covers it.

## Changes, decisions and notes

> **These are reconstructions too.** Each prompt below was inferred afterwards from
> `results/llm_comparison/attribution_worksheet.csv`, the change log in `results/phase2_snapshot/iteration_log.json`
> and the project documentation. Where no LLM is recorded, the prompt is the question the team member
> worked on. No LLM response is reproduced here.

<a id="c09"></a>

## C09 - CNN depth

- Kind: change (model)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> Our three-block CNN has a 22-px receptive field on 64-px images. What depth and channel widths would let it see a whole shape while staying small, and how do we check the receptive field after the change?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Use four blocks with channels 32/64/128/128. Keep the same Conv 3x3, BatchNorm, ReLU and MaxPool 2 block, and add one more. The receptive field goes 4 → 10 → 22 → 46 px, and global pooling gets a 4x4 map, so one unit covers most of a typical 55-px shape. Holding the last block at 128 instead of doubling it keeps the model at 242,250 parameters (`results/phase2_snapshot/loader_benchmark.json`). That matters because every arm and seed trains this network. Doubling to 256 would give about 391k, a figure from the reconstructed Opus file `prompts/3_modeling/claude_opus/20_C09_cnn-depth.md` that is not separately measured. Make it a config-only change (`train.channels` in `configs/pipeline.yaml`), applied to every arm before training. To check, use a test that computes the field from the real model and asserts 46 px, and one that checks the diagram against the real forward shapes and parameter count. Both are in `tests/studio/test_architecture_recipes.py`. No accuracy comparison of three against four blocks is recorded.

**Before:** Three blocks, 22-px receptive field

**After:** Four blocks, 46-px receptive field

**Documented reason:** The network could not see a whole shape.

<a id="c10"></a>

## C10 - Training arms

- Kind: change (model)
- LLM: opus_medium_5.5 (proposed, proposed by opus_medium_5.5 + 40256377 + 40248536)

** prompt**

> Arms A1 and B never see a clean real image during training. Should we add an arm that mixes clean, augmented and synthetic images in each batch? Propose the batch make-up for a 256-image batch and how it fits our comparison.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Yes. Add a new arm, A2, and leave A0, A1 and B exactly as defined, so iteration 1's result stands. Every A2 batch has three parts: clean real, augmented real and synthetic images. The counts come from shares through the same rounding as B, `round(256 × share)`. Do not hand-pick the split. Search it on validation within limits written down in advance (clean share 0.1 to 0.6, synthetic 0.1 to 0.4, total at most 0.8, so augmented images never vanish). The iteration 2 search chose 105 clean, 100 augmented and 51 synthetic images, from `clean_fraction` 0.411 and `synthetic_fraction` 0.198 (`docs/crisp_dm/iteration_2/search/winners.json`). Fairness: A2 gets the same seeds, step budget and architecture as the other arms, and its own tuning. A2 was designed after the test split had been read, so pre-register it before training, with A2 vs A0 as the primary test, and score it on a fresh holdout. Outcome: no gain on clean images in iteration 2 (A2 vs A0 +0.06, CI [−0.69, 0.83] on the reused test split). In iteration 3 it passed on damaged images of fresh holdout 2: +9.20 points, CI [8.89, 9.53] (`docs/crisp_dm/iteration_log.json`).

**Before:** A0, A1, B

**After:** A0, A1, B, A2. A2 batches hold 105 clean, 100 augmented and 51 synthetic images

**Documented reason:** A1 and B saw no clean images during training.

<a id="c11"></a>

## C11 - Synthetic share of a batch

- Kind: change (model)
- LLM: both (mediated, proposed by gemini_4_neon)

** prompt**

> What share of each batch should be synthetic for arms B and A2? Should we fix it at 30% or search it on validation per arm, and how do we report the actual count per 256-image batch?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Search it per arm on validation. 30% was set by hand, like the augmentation ranges, and A2 had no prior value at all. Searching the share keeps it fair only under the same rules as every other setting: ranges and trial counts fixed before training, selection on validation macro-F1 only, and iteration 1's B result left unchanged. Put B's share in its generator search and A2's in its batch-share search. Report both the configured share and the real count, because the sampler rounds: 30% was actually 77 of 256 images. The iteration 2 search chose B at 0.278, which is 71 of 256 images, and A2 at 0.198, which is 51 of 256 (`docs/crisp_dm/iteration_2/search/winners.json`, C11 in `docs/crisp_dm/iteration_log.json`). No separate measurement of the share alone is recorded. The iteration 3 search moved the shares again, to 0.168 for B and 0.12 for A2 (`configs/pipeline.yaml`).

**Before:** B 30%

**After:** B 71 of 256 images (configured 27.8%), A2 51 of 256 (configured 19.8%)

**Documented reason:** Chosen by the validation search.

<a id="c12"></a>

## C12 - Hyperparameter tuning

- Kind: change (model)
- LLM: both (mediated, proposed by gemini_4_neon)

** prompt**

> We tuned learning rate and dropout on A1 and reused them for every arm. Design a per-arm tuning on validation so no arm is favoured, and say how to report the chosen values.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
A shared setting is not neutral: chosen on A1, it is A1's best setting and can mis-regularize the other arms. So make the procedure equal, not the values:
1. Use the same 3 × 2 grid for every arm, A0 included: learning rate 0.0003, 0.001 or 0.003 by dropout 0.2 or 0.4.
2. Run the grid on each arm's own best data setting.
3. Use the same step budget and stopping rule in every grid cell.
4. Confirm the top settings on seeds 0, 1 and 2 and pick the highest mean, on validation only.

Report the full grid per arm, the trials per arm and each arm's frozen values in its `hparams` entry in `configs/pipeline.yaml`. Say so when arms land on the same values. Iteration 2 chose learning rate 0.003 for every arm and dropout 0.2, except A0 at 0.4. A0's grid gave 94.18 at dropout 0.4 against 93.91 at 0.2 on seed 0 (`docs/crisp_dm/iteration_2/search/winners.json`). In iteration 3, with 60 epochs and grouped cross-validation, A0 moved back to dropout 0.2, so all five arms use 0.003 and 0.2 (`results/phase2_snapshot/winners.json`).

**Before:** Learning rate and dropout tuned on A1, shared by every arm

**After:** Tuned per arm: learning rate 0.003 for all, dropout 0.2, except A0 at 0.4

**Documented reason:** A single arm's settings could favour that arm.

<a id="c13"></a>

## C13 - Training seeds

- Kind: change (model)
- LLM: opus_medium_5.5 (assisted, proposed by 40253714)

** prompt**

> Three seeds per arm give a noisy picture of seed variation. How many seeds per arm do we need, and should we add hold-out-source runs per arm? Estimate the training cost of each option.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Use five seeds per arm for the final retrain, the same seed list for every arm, plus three hold-out-source runs per arm. One hold-out run per arm cannot rank arms: in the iteration 2 investigation, three A0 hold-out runs scored 47.0, 64.1 and 49.3% accuracy (`docs/crisp_dm/iteration_2/investigation/report.md`). The records do not settle exactly how many seeds are statistically enough. Five was a choice, not a power calculation. Cost in trainings for four arms: three seeds plus three hold-out runs each is 12 + 12 = 24. Five seeds plus three hold-out runs is 20 + 12 = 32, so 8 more. That matches the 32 trainings of iteration 2 (F03 in `docs/crisp_dm/iteration_log.json`). Final runs have a fixed step budget, so cost grows linearly, and the search costs far more than the seeds. Keep search confirmation on seeds 0 to 2 only. Keep the hold-out runs descriptive, scored on Hand-Drawn triangles and rectangles. Iteration 3 kept five seeds and three hold-out runs for all five arms (`configs/pipeline.yaml`: `loso_seeds: 3`).

**Before:** Three per arm

**After:** Five per arm, plus three hold-out-source runs per arm

**Documented reason:** To measure seed variation better.

<a id="c14"></a>

## C14 - Parallel GPU runs

- Kind: change (model)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> Stage 4 stalls when several training runs share our 8 GB GPU. How many parallel runs fit in memory, and how do we make that a config setting instead of a hard-coded number?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Count GPU processes, not workers. The parent keeps GPU memory after the loader benchmark, so 3 run workers were 4 CUDA processes on the 8 GB card, and that setup stalled. Use two runs: three GPU processes counting the parent, one fewer than the setup that failed. Treat the largest value you have watched finish a full epoch without stalling as the safe one, rather than a memory estimate. To make it a setting, add `train.parallel_runs` to `configs/pipeline.yaml` with a comment recording why, and have `run_specs` in `src/stage4_train/sweep.py` use `min(parallel_runs, number of jobs)` workers. Record the value in the stage status. Keep it out of the recipe fingerprint, so changing it never forces a retrain. Each run stays deterministic from its (arm, seed), so the setting cannot change results. F03 is recorded as Overcome. In iteration 3 the value moved to 1, so the batch-preparation pools are not nested (`configs/pipeline.yaml`).

**Before:** More workers than the GPU could hold

**After:** At most two (train.parallel_runs: 2)

**Documented reason:** Stage 4 stalled on 8 GB of GPU memory.

<a id="c25"></a>

## C25 - Training arms

- Kind: change (model)
- LLM: gemini_4_neon (proposed, proposed by gemini_4_neon + 40297573 + 40211352)

** prompt**

> Would pretraining on synthetic images and then fine-tuning on real images recover the synthetic-to-real gap? Propose it as a new arm P, its schedule, and whether it should be tested or reported descriptively.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
It is worth adding as arm P, reported descriptively, outside the pre-registered primary and secondary tests. Its best schedule was unknown beforehand, and adding it to the tested family would weaken the primary A2 vs A0 test. Schedule:
- Train the first part of the epochs on synthetic images only, then the rest on augmented real images.
- Use the same total steps, optimizer and one continuous cosine learning-rate schedule as every other arm.
- Search the length of the synthetic phase on validation.
- Never let a synthetic-only epoch be picked as the best epoch.

The search chose `pretrain_fraction` 0.132, which is 7 synthetic epochs of 60 (`configs/pipeline.yaml`, `configs/models/P.yaml`). It does not simply recover the gap. With all real data, P scored 94.26 clean validation macro-F1 against A2's 95.17. It led only when real data was scarce: 92.63 against A2's 92.03 at 10% real, and 93.54 against 91.58 at 25% (`results/phase2_snapshot/exp_scarcity.json`). Its 5-seed test soft vote was 96.2 (`results/phase2_snapshot/metrics.csv`). To measure it, compare P with A0 and A2 across the real-data fractions, on clean and damaged validation.

**Before:** A0, A1, B, A2

**After:** Arm P added: pretrained on synthetic images, then fine-tuned on real images. Reported descriptively

**Documented reason:** To test whether pretraining recovers a synthetic-to-real gap.

<a id="c26"></a>

## C26 - Choosing the search winner

- Kind: change (model)
- LLM: gemini_4_neon (assisted, proposed by 40304911)

** prompt**

> One validation split can favour a search setting by chance. How do we re-score the top settings per arm with grouped cross-validation over train and validation, and confirm the winner on several seeds?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Use a two-stage filter that never touches test or holdout data:
1. Rank each arm's search trials on the single validation split and keep the top 5 distinct settings.
2. Pool train and validation and split them into 3 folds grouped by near-duplicate group (`phash_group`), so near-copies never sit on both sides. Do not group by source: ellipse, pentagon and diamond each come from one source, so source groups would drop whole classes from folds.
3. Train each setting on each fold at a short budget (15 epochs, pre-registered) to keep the cost bounded.
4. Pick the setting with the best mean clean CV macro-F1. Keep the damaged images out of selection.
5. Confirm the winner on seeds 0, 1 and 2 on the standard split, reusing any identical finished trial.

The CV changed the pick for four of five arms. Only A2's winner was also its top single-split setting. The three-seed confirmations were A0 94.19, A1 95.20, B 95.06, A2 95.80 and P 95.17 (`results/phase2_snapshot/winners.json`). Check it with the fold test (groups kept whole, every image covered) and by confirming that no sealed read happened.

**Before:** Scored on the single validation split

**After:** Top 5 settings per arm re-scored by grouped 3-fold CV over train and validation at 15 epochs, winner by clean CV macro-F1, confirmed on three seeds

**Documented reason:** One validation split can favour a setting by chance.

<a id="c27"></a>

## C27 - Training options

- Kind: change (model)
- LLM: gemini_4_neon (proposed)

** prompt**

> We want to measure scarcity, equal real images and training length in validation experiments. What training options should we add (equal-real, real-fraction, training length), and under what pre-registered rule would a longer budget be adopted?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Add three options, all off by default, and use them only in validation experiments:
- **Equal-real**: keep a full 256 real images per step and add the synthetic images on top, instead of replacing real images. This answers the point that arms see different numbers of real images.
- **Real-fraction**: train on a fixed share of the real images (10%, 25%, 50% or 100%). Take the subset per class and by whole near-duplicate group, with one fixed seed, so every arm gets the same subset. Keep 49 steps per epoch.
- **Training length**: 60 epochs, 30 epochs with no early stopping, and 60 epochs with no early stopping, against the 30-epoch baseline with early stopping.

The adoption rule, written before any results: switch every arm to a longer budget only if every tested arm (A0, A1, A2, three seeds each) gains at least 0.5 clean validation points. The search must not start until the rule has been applied. Results: equal-real lowered clean validation for B (94.20 → 92.18) and A2 (95.17 → 94.66) (`results/phase2_snapshot/exp_equal_real.json`). 60 epochs with no early stopping passed the rule (`exp_budget.json`, see C29).

**Before:** One fixed real-image share and training length

**After:** Equal-real, real-fraction and training-length options, used in validation experiments. A longer budget is adopted only under the pre-registered rule

**Documented reason:** To measure scarcity, equal real images and training length.

<a id="c29"></a>

## C29 - Training budget

- Kind: change (model)
- LLM: gemini_4_neon (assisted, proposed by 40297573)

** prompt**

> We pre-registered that a longer budget is adopted only if each tested arm gains at least 0.5 validation points. Here are the gains at 60 epochs with no early stopping. Does the rule say we switch, and how do we apply it to every arm?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Yes. At 60 epochs with no early stopping, the three-seed gains over 30 epochs with early stopping were A0 +1.99, A1 +0.51 and A2 +0.71 (`results/phase2_snapshot/exp_budget.json`). The smallest is 0.506, which is at least 0.5, so the rule adopts it. A1 clears by very little, but the rule was fixed in advance precisely to avoid judgment calls after the results. Adding an extra check on B and P, or changing the patience, would break the pre-registration. Opus reached the same conclusion in its real session: "A1 cleared the 0.5-point bar by only 0.01, but the rule was fixed in advance, so it applies" (`prompts/3_modeling/claude_opus/40_real_iteration-3-search-and-final-retrain.md`). To apply it to every arm, set `train.max_epochs: 60` and `train.early_stopping_patience: 999` once in the shared `train` block of `configs/pipeline.yaml`, not per arm. The search then takes the adopted budget for every phase, while the CV stage keeps its 15 epochs. The generated `configs/models/*.yaml` should show 60 epochs and no early stopping for all five arms. The other options failed the rule: 60 epochs with early stopping lost points for every arm, and 30 epochs with no stopping gained 0.00 for A1 and A2.

**Before:** 30 epochs with early stopping

**After:** 60 epochs with no early stopping, for every arm

**Documented reason:** The pre-registered rule: each tested arm gained at least 0.5 validation points (A0 1.99, A1 0.51, A2 0.71).

<a id="c30"></a>

## C30 - Batch preparation

- Kind: change (model)
- LLM: gemini_4_neon (proposed, proposed by gemini_4_neon + 40248536 + 40297573)

** prompt**

> Image preparation takes about 80% of each training step. Propose a faster batch preparation (random generator per step, several processes building batches ahead of the GPU) that gives identical batches at any process count.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
The design has five parts:
1. **One random generator per step**, seeded from (seed, epoch, step) (`step_rng` in `src/stage4_train/sampling.py`). Each batch then depends only on its own index, never on the order in which batches were built or on which process built them.
2. **A pool of worker processes**, 7 here, each building whole batches, augmented and synthetic images included, ahead of the GPU. Use processes, because this code is mostly Python, and start every worker at once (`multiprocessing.Pool` in `src/stage4_train/prep.py`). Ship batches back as uint8, in order, with a timeout.
3. **Keep A0 in the main process**, since it uses neither augmentation nor synthesis.
4. **Train one run at a time**, so the pools are not nested.
5. **Test the equality**: pool batches must equal the single-process stream, and validation must be identical across process counts. Here scores were identical at 4 and 7 processes (`docs/crisp_dm/README.md`).

An epoch fell from about 20 s to 2 to 6 s (F21). One honest cost is recorded: the per-step generator draws a different random stream from the one the 108 validation experiments used. Those keep their recorded numbers but cannot be retrained exactly from the new code. Opus at first suggested waiting until after the iteration for exactly this reason, and the team chose to do it first (`prompts/3_modeling/claude_opus/35_real_training-speed-parallel-batch-preparation.md`).

**Before:** One random generator per epoch, batches built on the training thread, two runs at once

**After:** One generator per step, batches built by 7 processes, one run at a time

**Documented reason:** Image preparation was about 80% of a step. The batches are the same at any process count, but differ from the stream the validation experiments used.

<a id="c31"></a>

## C31 - Optimization stage

- Kind: change (model)
- LLM: gemini_4_neon (proposed)

** prompt**

> A 60-epoch trial takes 5 to 7.5 minutes and image preparation runs on one core. Plan an optimization stage inside Modeling: which changes to try, how to measure each, and how to prove the results do not change.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Make it a named stage inside Modeling, because CRISP-DM has six steps. The rule: a change is registered only after a measurement shows it helped, and anything that could change numbers or repeatability is excluded, such as mixed precision or relaxed determinism. What to try, in order of the measured cost (`docs/crisp_dm/README.md`):
1. Batch preparation in 7 processes with a generator per step. Preparation was 226 to 376 ms against about 70 ms on the GPU.
2. Stop workers re-importing PyTorch, which cost about 2 minutes a trial.
3. Keep one worker pool across trials (16 s of about 220 s per trial was outside the epochs).
4. Cache each image's ink points (about 18% of the transform's time).
5. Send uint8 batches with an exact GPU lookup table.
6. Stop syncing with the GPU on every step.
7. Cache validation images on the GPU.
8. Skip plots for search trials.

Measure each one by per-trial wall time and per-epoch seconds. Prove no change in two ways: unit tests that batches match across worker counts and with caching, and full 60-epoch reruns compared on every logged number. Two reruns with the latest code took 163 s and 176 s and matched the earlier trials exactly (C31 in `docs/crisp_dm/iteration_log.json`).

**Before:** About 5 to 7.5 minutes per 60-epoch trial, image preparation on one core

**After:** About 3.7 minutes after the first parallel version, and 163 and 176 seconds on two reruns with the latest code

**Documented reason:** A named stage inside Modeling. Optimizations are registered once measured. Both reruns matched the earlier trials on every logged number.

<a id="c32"></a>

## C32 - Repeated search runs

- Kind: change (model)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> 9 of our 200 search runs repeat a finished trial with identical settings. Is it safe to reuse the finished result instead of training again, and how do we detect identical settings reliably?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Yes, it is safe, because training is deterministic. Each step's generator comes from the run seed, epoch and step, so identical settings give the same batches, model and scores, and retraining would only reproduce the number. The 9 repeats come from how the search is built. Four are the lr 0.003, dropout 0.2 grid cell for A1, B, A2 and P, which equals that arm's best phase trial. Five are each arm's seed 0 confirmation run. 200 − 9 = 191 trainings. To detect identical settings:
1. Key each trial on everything that defines it: arm, seed, overrides, hparams and fold. Serialize the key with sorted keys.
2. Reuse a finished result only when the settings saved in its `result.json` match exactly.
3. Keep the recipe fingerprint check, so any code or budget change forces a retrain.
4. Never merge a CV fold run with a full-data run, or one seed with another.

The 9 still count toward their phase, so no trial limit changes. `tests/stage4/test_search_iter3.py` covers the reuse. No separate time saving was recorded.

**Before:** 9 of the 200 search runs repeated a finished trial with identical settings

**After:** Those 9 reuse the finished result, so 191 runs train

**Documented reason:** Identical settings give the same result, so training them again adds nothing. No trial limit changes.

<a id="c37"></a>

## C37 - Long-job recovery

- Kind: change (model)
- LLM: opus_medium_5.5 (proposed, proposed by opus_medium_5.5 + 40211352)

** prompt**

> A long search crashed at 66 of 191 trials and we had no written rule for what to do. Write a recovery procedure for long jobs: what to check, what to record, how to relaunch, and when to stop.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
The risk after a crash is not lost work, because finished trials are reused. The risks are a second running copy, a half-alive process, or a failure nobody wrote down. The procedure:
1. **Check the log**: the error, the trial name and how many trials finished.
2. **Check the GPU** with `nvidia-smi`: the card is visible, and no leftover Python process is holding memory. Kill every process from the crashed job, workers included.
3. **Record it** in the iteration log: the time, the trial count, the error text and what else was running. Write "cause not established" unless it was established.
4. **Relaunch exactly one copy** from the same config and code. Do not edit training code while it runs, and keep the 5-minute stall watcher on.
5. **Stop after repeated failures.** If the same job fails again after a clean relaunch, keep the logs and investigate instead of relaunching.

Never change a setting, seed or trial limit to get past a crash. The records do not set how many failures count as "repeated". Applied to F22, the relaunch carried all 66 finished trials over (`docs/crisp_dm/iteration_log.json`).

**Before:** No written rule for a job that crashed

**After:** Check the log and GPU, record it, relaunch one copy, and stop after repeated failures

**Documented reason:** A crash at 66 of 191 trials showed the gap.

<a id="c38"></a>

## C38 - Search winners

- Kind: change (model)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> The iteration 3 search is finished. How do we freeze its winners in the pipeline config and a winners file, and confirm them on more seeds before the sealed test?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Freeze the winners in two places, from one source, and check that the two agree:
1. Copy the generated `winners.json`, unchanged, to `docs/crisp_dm/iteration_3/search/winners.json`. It is the evidence and is never edited by hand.
2. Generate each arm's `hparams`, overrides and shares in `configs/pipeline.yaml` from that file. Put the shared budget (60 epochs, no early stopping) in `train`, not in an arm's overrides.
3. Check before the retrain: every config value matches its `winners.json` entry. Each winner is the best clean CV mean among that arm's top 5, as pre-registered, not the best single-seed score. Confirmation used seeds 0 to 2. The CV folds came from train and validation only.

Then train five seeds per arm plus the hold-out runs from the frozen config, and record validation before any sealed read. The winners were A0 `grid_A0_lr0.003_d0.2`, A1 `augment_t17`, B `synth_t15`, A2 `synth_a2_t03` and P `pretrain_t00`. Their three-seed means were 94.19, 95.20, 95.06, 95.80 and 95.17 (`results/phase2_snapshot/winners.json`). The five-seed retrain gave A0 94.33, A1 95.27, B 95.12, A2 95.82 and P 95.22 (`docs/crisp_dm/iteration_log.json`).

**Before:** Iteration 2 settings

**After:** Winners of the iteration 3 search, frozen in configs/pipeline.yaml and docs/crisp_dm/iteration_3/search/winners.json

**Documented reason:** Chosen on grouped cross-validation over train and validation, confirmed on three seeds.

<a id="c39"></a>

## C39 - Optimization stage, measured

- Kind: change (model)
- LLM: gemini_4_neon (proposed, proposed by gemini_4_neon + 40211352)

** prompt**

> Here are the measured trial times by phase after the optimizations. Summarize the optimization stage with before and after numbers, and say what part of the gain may come from a quieter machine.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Summary from `docs/crisp_dm/README.md`, time per 60-epoch trial:

| Version | Time per trial |
|---|---|
| Original, preparation on one core | About 5 to 7.5 min effective, with two trials at once |
| First parallel version | About 3.7 min on average (2.6 to 5) |
| Latest code | Median 92 to 184 s by phase |

Two exact-match reruns with the latest code took 163 s and 176 s. For the whole search, the projected 9 hours became 175 trainings in about 3 h 50 min. Every change kept results identical: the two reruns matched earlier trials on every logged number. Part of the gain is not from the code. Slow epochs had the CPU 99% busy against 90% in fast ones, with no change in temperature. Windows Defender used about 2 cores and other programs several more. Other programs were closed part way through the search, and a Defender exclusion was added. The records do not separate the code gain from the quieter-machine gain, so report the 92 to 184 s as the combined result. The cleanest available code-only comparison is the two reruns against the earlier 3.7 min, though even those were not timed on an identical machine load.

**Before:** About 3.7 minutes per 60-epoch trial, and about 9 hours for the search

**After:** Median trial 92 to 184 seconds by phase, and 175 trainings in about 3 hours 50 minutes

**Documented reason:** Every optimization that left results unchanged. Two reruns matched the earlier trials on every logged number. Other programs were closed part way through, so the gain is partly from a quieter machine.

<a id="c40"></a>

## C40 - All models vote

- Kind: change (deploy)
- LLM: none (team)

** prompt**

> The team disagrees on how the all-models vote should combine models: equal weights, weighted by validation score, or per-class weights. How do we compare them on held-apart validation, and what can we claim about the result?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Start with an equal-weight average of the models' class probabilities. Keep a weighted scheme only if it clearly beats that. Opus gave this advice in the real session: equal weights have nothing to fit, and the arms share one network and the same real images, so per-class differences are likely noise (`prompts/3_modeling/claude_opus/34_real_equal-weight-vs-weighted-vote.md`). To compare:
1. Use each run's saved validation probabilities.
2. Split validation into two halves balanced by class.
3. Learn any weights on one half and score on the other, then swap the halves.
4. Leave absent classes out of the score (F30).
5. Set a margin in advance: here 0.5 points.

Result: equal weights 95.59 against per-class weights 94.80 macro-F1, so equal weights stay (`results/phase2_snapshot/exp_vote_check.json`). Validation-score weights are not reported there separately. What you can claim is limited. Validation was reused from tuning, so the numbers are optimistic, and the vote is a new model. The dashboard therefore shows it with no claimed score. A real claim would need a pre-registered test on sealed data it has never seen.

**Before:** One answer per model

**After:** An equal-weight average of every model's class probabilities on the Draw and predict page, with no claimed score

**Documented reason:** On held-apart validation, equal weights scored 95.59 and per-class weights 94.80, so equal weights stay. Validation was reused, so these are optimistic.

<a id="c48"></a>

## C48 - Architecture and training diagrams

- Kind: change (model)
- LLM: opus_medium_5.5 (proposed, proposed by opus_medium_5.5 + 40253714 + 40256377)

** prompt**

> A reader cannot see that all models share one network and differ only in training images. Design an interactive diagram of the network's operations, the batch-preparation pool and training loop, and what each model sees per batch, read from the config and run list.

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
The diagram has to land one message: one network, five training diets. Build three linked views from one data builder that reads the config and the run list, never from numbers typed into the page:
1. **The shared network.** Each block is a stack of slabs, one per operation (convolution, BatchNorm, ReLU, max pool), shrinking with the image. Show each operation's output shape, parameters and receptive field, highlight the selected one, and add small worked examples of max pooling and global average pooling.
2. **How a training run works.** A clickable flow from the image index and batch plan, through the pool of batch-preparation workers (`prep_workers: 7`), to the update step and validation checkpoint.
3. **What each model saw.** One bar per model splitting a 256-image batch into clean real, augmented real and synthetic images. P gets a second bar for its pretraining epochs.

Keep it from drifting with tests against the real code: summed parameters equal the PyTorch model's count, block shapes match a forward pass, the last block sees 46 px, and the bars match the trainer's batch composition. These exist in `tests/studio/test_architecture_recipes.py`, with the builder in `studio/data/architecture.py`. No reader-testing measurement is recorded.

**Before:** The network was a table, and how each model was trained was only in the config

**After:** An interactive diagram of every operation in the shared network with worked pooling examples, a clickable view of the batch-preparation pool and training loop, and what each model saw per batch, read from the config and run list. Each slab in a block stands for one operation, and the selected one is highlighted

**Documented reason:** A reader could not see that the models share one network and differ in their training images.

<a id="c53"></a>

## C53 - One config file per model

- Kind: change (model)
- LLM: opus_medium_5.5 (assisted, proposed by 40304911)

** prompt**

> Each model's full setup must be pieced together from the shared config and its overrides. How do we generate one config file per model, and add a test that keeps them in step with the shared config?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Keep `configs/pipeline.yaml` as the only source of truth and treat the per-model files as a generated view. A script (`scripts/export_model_configs.py`) resolves each arm with the same override logic the pipeline uses and writes `configs/models/<arm>.yaml`, headed "generated, do not edit". Each file holds the network, training settings, batch mix, and augmentation and generator ranges. Compute derived values with the real code rather than by hand: batch counts from the trainer's batch composition, parameters by building the model. Write `null` for a section an arm does not use, so it reads as "off" rather than "forgotten". Never let the pipeline read these files, or there would be two sources of truth. The test (`tests/studio/test_model_configs.py`) checks four things: each saved file equals a fresh export, compared as data rather than text; each batch mix adds up to the batch size; arms without augmentation or synthesis list none; only P has a pretraining phase. Example output: B is 0 / 213 / 43 per 256 (clean, augmented, synthetic), A2 is 105 / 120 / 31, and every model has 242,250 parameters (`configs/models/`).

**Before:** Each model's full setup had to be pieced together from the shared config and its overrides

**After:** configs/models holds one generated file per model with its network, training settings, batch mix, augmentation and generator ranges, and a test keeps them in step with the shared config

**Documented reason:** A reader can see one model's whole setup in one place.

<a id="d01"></a>

## D01 - Add model voting to raise overall performance: combine the class probabilities of several models instead of trusting one

- Kind: decision (model)
- LLM: none (40297573)

** prompt**

> Can we raise overall performance by letting several models vote, as with MLP voting, instead of trusting one model? How do we combine class probabilities, and how do we measure the gain over the per-seed mean?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Yes, usually by a small amount. Use a soft vote: average the models' class probabilities and take the highest class, rather than counting one vote per model. A confident model then counts for more, and there is nothing to fit. Voting helps only where the models disagree. These models share one network and the same real images, so expect a small gain. To measure it, score the vote of the 5 seeds of each arm on the same split as each seed alone, and compare it with the per-seed mean. Recorded on the test split (`results/phase2_snapshot/metrics.csv`), macro-F1 rose for every arm: A0 94.6 → 95.5, A1 95.8 → 96.2, B 95.6 → 95.8, A2 95.8 → 96.0 and P 95.8 → 96.2. Choose weights for a vote across arms on validation, not on test (see C40 and F30). Treat the vote as a new model when making claims about it.

**Documented outcome:** Inspired by voting across MLP models. Measured on the test split, soft-vote ensembles of the 5 seeds beat the per-seed mean for every arm: A0 94.6 -> 95.5, A1 95.8 -> 96.2, B 95.6 -> 95.8, A2 95.8 -> 96.0, P 95.8 -> 96.2 macro F1 (results/phase2_snapshot/metrics.csv). Extended to an equal-weight vote across all models (see C40, F30).

<a id="n01"></a>

## N01 - Training ran on the CPU: the first machine was CPU-only (14 cores), and a run could also fall back to the CPU silently by mistake. A full Stage 4 run took about 24 hours

- Kind: note (Iteration 1)
- LLM: none

** prompt**

> A training run takes about 24 hours. Is it running on the CPU instead of the GPU? How do we check, and how do we make a run fail instead of silently falling back to the CPU?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
On the first machine it was on the CPU, because that machine had no GPU (14 cores, CPU only), so 24 hours was expected and not a bug. Quick checks: `python -c "import torch; print(torch.cuda.is_available())"` must print `True` on a CUDA build of PyTorch, `nvidia-smi` should list the training process, and the run record should save the device. A setting such as `device: auto` falls back to the CPU whenever CUDA is missing, for example with a CPU-only PyTorch build, and that fallback is silent. Pin the device instead: `train.device: cuda` in `configs/pipeline.yaml`, whose comment says "cuda fails loudly when no GPU is visible". Training then stops with an error instead of running slowly. The project did this, moved training to the RTX 3080 machine (D04) and documented the CUDA install. Also keep every arm of one experiment on the same hardware, because GPU and CPU runs are not numerically identical (`prompts/3_modeling/claude_opus/16_d04-move-training-to-gpu-machine.md`).

**Documented outcome:** Moved training to the RTX 3080 machine (D04) and pinned train.device: cuda, so a run fails instead of silently falling back to the CPU; documented the CUDA install. The CPU-run backup folder was kept out of Git.

<a id="n02"></a>

## N02 - The model waited on the data store (SQL catalog and manifest) to prepare each batch, and preparation was single-threaded, so the GPU sat idle (CPU-GPU overhead)

- Kind: note (Iteration 1 to 3)
- LLM: none

** prompt**

> The GPU sits idle while each batch waits on the SQL catalog and manifest and on single-threaded preparation. How do we read the manifest once and build batches ahead of the GPU?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
There are two separate fixes, and each has to keep results identical:
1. **Read the manifest once.** Load the image index (manifest and catalog) a single time when the image store opens, and keep it in memory. Each batch then looks images up in memory instead of querying the data store every time. Per the entry's own outcome, `ImageStore` now does this (commit e10169d).
2. **Build batches ahead of the GPU.** Move augmentation and synthetic drawing into worker processes that prepare future batches while the GPU trains on the current one. Give each step its own random generator, so the batches do not depend on the number of workers. Here 7 processes do this (C30), later as one shared pool kept across runs, with validation images cached on the GPU.

To measure, time batch preparation against the GPU step. Before the change, preparation took 226 to 376 ms against about 70 ms on the GPU (`docs/crisp_dm/README.md`). The latest benchmark shows 115.4 ms per batch built and 18.5 ms per GPU step (`results/phase2_snapshot/loader_benchmark.json`). To check correctness, compare batches against the single-process stream and rerun a trial to match every logged number. Even now the GPU still waits on the CPU part of the time (F25).

**Documented outcome:** ImageStore now reads its manifest once (e10169d). Batches are built ahead of the GPU by 7 processes (b3bb15d), and one shared pool with cached validation images followed (534643d). See F21 and C30.

<a id="d03"></a>

## D03 - Opus 5.5 critiqued the model configuration: the network depth, the choice of layers and the activation function

- Kind: decision (Before iteration 1)
- LLM: opus_medium_5.5 (critiqued)

** prompt**

> Critique our CNN configuration for 64x64 grayscale shapes: the number of blocks, the layers in each block, the channel widths, the pooling, the head and the activation function. What would you change and why?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Only the depth is clearly worth changing. Three blocks give a 22-px receptive field on 64-px images, so no unit sees a whole shape. Add a fourth block for 46 px (F17, C09). The rest is reasonable:
- **Block width.** Keep the fourth block at 128 channels, not 256, which keeps 242,250 parameters (`results/phase2_snapshot/loader_benchmark.json`).
- **Block layers.** Conv 3x3, BatchNorm, ReLU and MaxPool 2 is a stable block. BatchNorm is useful because augmented and synthetic batches shift the input statistics. Make sure evaluation always runs in `eval()` mode.
- **Activation.** ReLU is fine for line drawings. Test another activation only as a one-off ablation applied to all arms.
- **Head.** Global average pooling, dropout and one linear layer keep the head small and independent of where the shape sits. Dropout is already tuned.
- **Pooling.** Max pooling keeps 1-px strokes, but is sensitive to small shifts. Revisit it only if robustness results show a shift problem.

Make any change once, for every arm, before training. The only change on record is the depth, and the rest of Opus's advice was not recorded (the worksheet note above). The points beyond depth come from a reconstruction (`prompts/3_modeling/gemini_4_neon/20_D03_opus-5-5-critiqued-the-model.md`), not a saved chat. The committed model keeps ReLU, max pooling and conv bias (`src/stage4_train/model.py`).

**Recommended (summary, from the worksheet):** Opus 5.5 reviewed the network depth, the choice of layers and the activation function. The one recorded change is the depth: three blocks gave a 22-px receptive field on 64-px images, so it moved to four blocks with a 46-px field (F17, C09). The rest of its advice is not recorded. No chat export is in the repo yet.

**Documented outcome:** Final network (src/stage4_train/model.py): 4 blocks of Conv 3x3 -> BatchNorm -> ReLU -> MaxPool 2, channels 32/64/128/128, then global average pooling, Dropout and one Linear layer (242,250 parameters). The depth change from 3 to 4 blocks (22-px to 46-px receptive field on 64-px images) is F17/C09.

<a id="d04"></a>

## D04 - Move training from the CPU-only machine to the new machine (NVIDIA RTX 3080, 32 GB RAM, high-core CPU), because one CRISP-DM loop of Stage 4 on the CPU cost most of a day

- Kind: decision (Iteration 1)
- LLM: opus_medium_5.5 (proposed)

** prompt**

> One CRISP-DM loop of Stage 4 on our CPU-only machine takes most of a day. Should we move training to the new machine (RTX 3080, 32 GB RAM, high-core CPU)? What has to change, how do we keep the comparison fair across hardware, and how long should the 17-run budget take?

**Answer** *(written 2026-11-20 from the repo's records, not the original LLM reply)*
Yes, for every future Stage 4 run. The gain is speed only, not accuracy, and it matters because each CRISP-DM loop currently costs most of a day. A dedicated GPU helps most, a faster CPU is needed alongside it because augmentation and synthesis run on the CPU, and more memory adds nothing (about 600 MB per training process). What has to change:
- Add GPU support to Stage 4 and install a CUDA build of PyTorch.
- Pin `train.device: cuda` so a run cannot fall back to the CPU.
- Copy the unified data set and frozen splits to the new machine.

Fairness: train every arm of one experiment on the same machine, because GPU and CPU runs are not numerically identical. Put the GPU model and torch version into the recipe so runs from different machines cannot be mixed, and retrain finished CPU runs instead of combining them. Opus estimated the 17-run budget at about 1 to 2 h instead of 12+ h, but that was not measured (`prompts/3_modeling/claude_opus/16_d04-move-training-to-gpu-machine.md`). The later measurement is 175 trainings in about 3 h 50 min in the iteration 3 search, after the optimization stage (C39). That figure is not directly comparable to the 17-run estimate.

**Documented outcome:** Added GPU support with a CUDA build of PyTorch and pinned train.device: cuda so a run cannot fall back to the CPU. Rule kept: every arm of one experiment trains on the same hardware, because GPU and CPU runs are not numerically identical. Estimated 1 to 2 h instead of 12+ h for the 17-run budget (estimate, 2026-11-08); measured later: 175 trainings in about 3 h 50 min in the iteration 3 search (C39).
