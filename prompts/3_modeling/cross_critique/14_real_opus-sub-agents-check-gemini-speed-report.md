# 3_modeling - Opus 5.5 sub-agents check Gemini 4 Neon's speed report

- LLM: Claude Opus 5.5, medium effort (`opus_medium_5.5`), in Claude Code (`claude-opus-5-5` on every reply)
- Critiqued output: Gemini 4 Neon (its report is pasted verbatim inside the prompt)
- Category: Two-LLM comparison (one LLM critiques the other)
- Date: 2026-11-09 (times are local, UTC-5)
- Owner: 40256377
- Worksheet entries: C31, C32, C39
- Source: **exchange**, from a saved Claude Code session. Prompts and replies are verbatim. Only the main conversation's text is kept: tool calls, tool output and sub-agent transcripts are left out, editor file-open notices are removed, and session IDs are removed.
-  [C32](../../3_modeling/claude_opus/26_C32_repeated-search-runs.md)

## Prompt (21:47)

> create a sub agents that will investigate wether the sub sets of points this repoort makes  holds ===["
>
> <pasted_content id="8717">
> =============
> **Fix the search first, then the batch pipeline.** The 200-trial search is about 9 h of your roughly 11.5 h total (9 h search plus 2.5 h final retrain). Inside each run, the step loop is slower than it needs to be. The figures below are my estimates from your diagram and the code I read. I haven't profiled anything.
>
> ## Where the time goes
>
> Per step you measured 226–376 ms to prepare a batch on one core and about 70 ms on the GPU. With 7 workers, prep is roughly 32–54 ms per batch. Your diagram has prep and the GPU step alternating (`P1 → G1 → P1`), so they run one after the other. That puts a step at roughly 100–125 ms, and 49 steps at about 5–6 s, the top of your 2–6 s per epoch.
>
> The GPU step itself is also slow. By my count, a forward pass of your CNN is about 48M multiply-accumulates per image. For a 256 batch with the backward pass, that is about 74 GFLOP per step. A modern GPU should do that in 10–20 ms, so 70 ms means it is underused. Likely causes are fp32 with no TF32 or AMP, no `channels_last`, deterministic-mode kernels, `cudnn.benchmark=False`, and two runs sharing the GPU.
>
> ## Fixes ranked by payoff
>
> | Fix | Where | Rough gain |
> | --- | --- | --- |
> | Prune the search | search.py | 9 h to about 1.5–2 h |
> | Overlap prep with the GPU step (prefetch queue) | batch loop | up to about 1.5× per run |
> | GPU augmentation | Stage 2 | removes the 226–376 ms prep |
> | AMP, TF32, channels_last | train.py | 2–4× on the GPU step |
> | Remove per-step syncs | train.py | few ms per step |
> | Pre-generated synthetic pool | Stage 3 | cuts the Stage 3 cost |
>
> ## How to do each
>
> - **Search.** 200 trials for a few knobs (lr, dropout, augmentation ranges) is too many. Use Optuna with a Hyperband or successive-halving pruner. Give each trial a short budget (about 8 epochs, one seed), then fully train only the top 5–8. A 3-fold grouped CV only on the finalists, as I suggested earlier, keeps the cost low.
> - **Prefetch.** Run batch preparation in a background thread or process with a queue of 2–4 batches, so the GPU never waits. `sampling.py` currently says it runs in one process, but your diagram shows 7 workers. Check which one is true.
> - **GPU augmentation.** Put the whole train set on the GPU as uint8 (12,405 × 4,096 bytes is about 51 MB). Do rotation, scale and translation with `affine_grid` and `grid_sample`. Do noise, blur and thresholding as tensor ops. The re-frame step can use per-image bounding boxes from `amax`. At 64×64 and batch 256, this should take a few milliseconds.
> - **Synthetic pool.** Pre-generate 50–200k synthetic images (about 200–800 MB as uint8) once, then sample and augment them on the GPU. You lose fresh draws each batch, so keep the pool large and re-seed it per run.
> - **AMP and sync.** Enable bf16 or fp16 autocast, TF32, and `channels_last`. `train.py` calls `float(loss.detach())` and `int((logits.argmax(...) == y).sum())` every step, which force a GPU sync each time. Accumulate them in GPU tensors and read them once per epoch.
> - **Determinism.** Turn off `use_deterministic_algorithms` and set `cudnn.benchmark=True` during the search. Keep deterministic mode only for the final 40 retrains.
> - **Profile first.** A cost of 226–376 ms for 256 small images is about 1 ms per image, which is too slow for plain OpenCV on 64×64. One function is probably the hotspot, perhaps the supersampled synthetic render (`s=2`) or the morphology step. Run `py-spy record` or `cProfile` on `make_batch` before rewriting anything.
>
> ## Stages to leave alone for now
>
> - **Stage 1 near-duplicate grouping** is O(N²) at about 1.6e8 pairs, but it runs once per data freeze. If you re-freeze often, use 64-bit perceptual hashes with bucketed lookup.
> - **Stage 5 bootstrap** is untimed. Time it before optimizing. Precomputed per-cluster confusion counts are the main trick.
> - **Stage 0 hashing** could be cached by file size and mtime.
>
> ## Risks when you change the pipeline
>
> - A new GPU augmentation will not match the CPU version pixel for pixel. Your recipe fingerprint will correctly invalidate old runs. Before trusting it, compare per-class aspect-ratio, stroke-width and size histograms with the CPU pipeline. That is the same area where I suspected the re-frame problem earlier, so do not carry any defect over.
> - Your diagram says E=60 but the training config I read used max 30 epochs. It says 40 final runs where I read 20 (five seeds, four arms), though that count may include ablations. Fix the diagram so the 3.7 min figure and the 9 h estimate are consistent.
>
> Do you want the Optuna search rewritten first, or the GPU batch pipeline? The search rewrite is quicker and the bigger win.
>
> =============
> **The biggest saving is in `search.py`.** It runs about 166 full trainings, and 20 of them repeat runs you already did. Per-run speed is the second target: the current step loop serializes CPU batch preparation and the GPU step, and forces a GPU sync on every step. Everything below comes from your diagram plus the code I read. The speed gains are my estimates, not measurements. I haven't seen the Stage 2/3 code or your GPU model.
>
> ## Where the time goes
>
> **Search budget.** Counting the phases in `search.py` gives 166 runs, not the 200 in your diagram. Ablation is 10 conditions × 3 seeds = 30 runs, augment is 24, synth 16, shares 12, and the lr × dropout grid is 4 arms × 6 = 24. Confirm is 4 arms × top 5 settings × 3 seeds = 60. At 3.7 min per run that is about 10 h sequential. Confirm alone is about 3.7 h.
>
> **Duplicate work.** Every confirm candidate was already trained at seed 0 with the same overrides and hyperparameters, because the random phases and the grid use `SEEDS[0]`. Confirm retrains it into a different folder, so `run_trial` can't reuse it. That is 20 redundant runs, about 74 min.
>
> **Per-run cost.** A step is about 40–54 ms of batch prep per worker (226–376 ms ÷ 7) plus about 70 ms on the GPU. They run back to back, so a step is roughly 110–125 ms, and 49 steps give 5–6 s per epoch. The 70 ms was measured while two runs shared the GPU. On Windows, two processes time-slice one GPU, so `parallel_runs=2` is probably not doubling throughput. A lone run is likely about 35 ms.
>
> **GPU work.** I counted about 48M multiply-accumulates per image forward. That is about 74 GFLOP per 256-image step including the backward pass, which a modern GPU should do in 10–20 ms. Fixes below target the gap.
>
> ## Cut the search
>
> 1. **Stop retraining seed 0 in confirm.** Reuse the earlier result and train only seeds 1 and 2 of each setting:
>
> ```
> carried, specs = [], []
> for i, r in enumerate(top_settings(candidates)):
>     ov, hp = r["settings"]["overrides"], r["settings"]["hparams"]
>     carried.append({**r, "name": f"{arm}_c{i}_s0"})
>     specs += [_spec(config, config_path, "confirm", f"{arm}_c{i}_s{s}", arm, s, ov, hp)
>               for s in SEEDS[1:]]
> confirmed = carried + execute(config, specs)
> ```
>
> The mean-by-name grouping below it still works. This saves about 20 runs. If you also drop `TOP_K` to 3, confirm falls from 60 runs to 24.
>
> 2. **Prune bad trials early.** `train_one` has a `val_scorer(epoch_idx, probs, labels)` hook. It currently picks the epoch to keep, but you can use it to stop a trial. Raise an exception when validation macro-F1 falls below a reference curve:
>
> ```
> class Pruned(Exception): ...
>
> def make_pruner(ref, margin=2.0, start=6):   # ref[e] = 25th-percentile val F1 at epoch e
>     def scorer(epoch_idx, probs, labels):
>         f1 = macro_f1_points(labels, probs.argmax(1), probs.shape[1])
>         if epoch_idx >= start and f1 < ref[min(epoch_idx, len(ref) - 1)] - margin:
>             raise Pruned(f1)
>         return f1
>     return scorer
> ```
>
> Build `ref` from the `train_log.csv` files of your ablation runs. Catch `Pruned` in `run_trial` and write a `result.json` with `"pruned": True`. Pass `val_scorer=make_pruner(ref)` to `train_one`.
>
> 3. **Don't shorten the schedule.** Strong augmentation and synthetic data usually learn slower, so a short-epoch proxy would favor weak settings. Prune with a reference curve at the same epochs, don't cut `max_epochs`. If you want a short proxy anyway, check its rank correlation with full runs on about 10 settings first.
> 4. **Shrink the ablation.** Run all 10 conditions at one seed, then add two seeds only for the 3–4 conditions with the largest effect. That is about 18 runs instead of 30.
> 5. **Check your own numbers first.** The script below shows how many epochs your runs really use. If the median best epoch is much less than 30, tighten the patience.
>
> ```
> import json, glob, numpy as np
> rs = [json.load(open(p)) for p in glob.glob("artifacts/stage4/tuning_iter2/**/result.json", recursive=True)]
> for k in ("best_epoch", "epochs_run"):
>     print(k, np.percentile([r[k] for r in rs], [10, 50, 90]))
> ```
>
> | Phase | Now | After |
> | --- | --- | --- |
> | Ablation | 30 | about 18 |
> | Augment, synth, shares (52 trials) | 52 | about 23 full-run equivalents with pruning |
> | Grid | 24 | about 14 with pruning |
> | Confirm | 60 | 24 (top 3, new seeds only) |
> | Total | 166 (about 10.2 h) | about 79 (about 4.9 h) |
>
> ## Make each run faster
>
> - **Remove per-step syncs.** `float(loss.detach())` and `int((logits.argmax(1) == y).sum())` force the CPU to wait for the GPU every step. Accumulate on the GPU and read once per epoch:
>
> ```
> loss_sum = torch.zeros((), device=device); correct = torch.zeros((), device=device, dtype=torch.long)
> # inside the step
> loss_sum += loss.detach() * y.shape[0]
> correct  += (logits.argmax(1) == y).sum()
> # after the epoch
> train_loss = float(loss_sum) / seen
> ```
>
> - **Prefetch.** Prepare the next batches in a background thread while the GPU works. Order is preserved, so the RNG sequence and determinism stay intact:
>
> ```
> import queue, threading
> def prefetch(it, depth=3):
>     q = queue.Queue(depth)
>     def work():
>         for b in it:
>             q.put((torch.from_numpy(b.images).pin_memory(),
>                    torch.from_numpy(b.labels).pin_memory(), b.is_synthetic))
>         q.put(None)
>     threading.Thread(target=work, daemon=True).start()
>     while (item := q.get()) is not None:
>         yield item
> ```
>
> If the augmentation is pure Python, the GIL limits overlap. Use a process there.
>
> - **Use cheaper GPU math.** Enable TF32, bf16 autocast (Ampere or newer, otherwise fp16 with `GradScaler`), `channels_last` and fused AdamW:
>
> ```
> torch.backends.cuda.matmul.allow_tf32 = torch.backends.cudnn.allow_tf32 = True
> model = model.to(device, memory_format=torch.channels_last)
> opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd, fused=True)
> with torch.autocast("cuda", dtype=torch.bfloat16):
>     logits = model(x)
> loss = F.cross_entropy(logits.float(), y)
> ```
>
> Skip `torch.compile`. It is awkward on Windows.
>
> - **Search-only determinism relaxation.** Turn off `use_deterministic_algorithms` and set `cudnn.benchmark=True` during the search. Keep deterministic mode for the final runs.
> - **Put the data on the GPU.** The train set is about 51 MB as uint8. Sample indices on the CPU, as now (256 ints), and gather the images on the GPU. Send uint8 and convert to float on the GPU, which cuts transfer 4×.
> - **Move augmentation to the GPU.** At 64×64 and batch 256 this takes about a millisecond per op:
>
> ```
> def gpu_augment(x_u8, labels, rot_lim, g, cfg):        # x_u8 (N,64,64) uint8 on GPU, white background
>     x = (255 - x_u8).float().div_(255).unsqueeze(1)    # ink=1, so zero padding is background
>     N, dev = x.shape[0], x.device
>     u = lambda lo, hi: lo + (hi - lo) * torch.rand(N, device=dev, generator=g)
>     ang, sc = torch.deg2rad(u(-1, 1) * rot_lim[labels]), u(cfg.scale_lo, cfg.scale_hi)
>     c, s = torch.cos(ang) / sc, torch.sin(ang) / sc
>     theta = torch.zeros(N, 2, 3, device=dev)
>     theta[:, 0, 0], theta[:, 0, 1], theta[:, 1, 0], theta[:, 1, 1] = c, -s, s, c
>     x = F.grid_sample(x, F.affine_grid(theta, x.shape, align_corners=False),
>                       padding_mode="zeros", align_corners=False)
>     return x   # then: masked blur, noise, threshold, re-frame with a UNIFORM scale
> ```
>
> Use per-class rotation caps (`rot_lim[labels]`). Skip shear and non-uniform scale for the five classes that have it off, with a per-class mask. Re-frame by bounding box with a uniform scale only. A stretch that fills the frame would destroy rectangle versus square and circle versus ellipse, which is the failure I suspected earlier. Seed with `torch.Generator("cuda")` per (seed, epoch).
>
> - **Check synthetic cost.** At `s=2`, each image is drawn on 128×128 and downsampled, so 71 per batch could be the hotspot. A pool is hard in search, because `sample_synth` changes the generator parameters (radius, jitter, ratios, inner star ratio) per trial, so a pool must be rebuilt per synth trial. A 30k pool of 4 KB images is only 120 MB, but rebuild time matters. Pool it only for final runs.
> - **Profile before rewriting.** 226–376 ms for 256 small images is slow for OpenCV. Find the hotspot first:
>
> ```
> import cProfile, pstats
> cProfile.run("for _ in range(20): make_batch(store.images, store.labels, store.class_idx, arm_cfg, 256, frac, 10, rng, transform=T, generate=G)", "mb.prof")
> pstats.Stats("mb.prof").sort_stats("cumtime").print_stats(15)
> ```
>
> `py-spy` also works on Windows. Add the new flags to `config["train"]` so the recipe fingerprint changes and old runs aren't mixed with new ones.
>
> ## Evaluation and other stages
>
> - **Run Stage 5 inference on the GPU.** `predict_torchscript` loads with `map_location="cpu"`. A damaged-set pass is about 103,500 images (23 levels × 4,500) per model, roughly 10 TFLOP, so 40 models is about 400 TFLOP. That is probably tens of minutes on CPU and a few minutes on GPU:
>
> ```
> dev = "cuda" if torch.cuda.is_available() else "cpu"
> model = torch.jit.load(str(model_path), map_location=dev).eval()
> with torch.inference_mode():
>     for i in range(0, n, 4096):
>         x = torch.from_numpy(images_u8[i:i+4096]).to(dev).float().div_(PIXEL_SCALE).unsqueeze(1)
>         out.append(torch.softmax(model(x), 1).cpu())
> ```
>
> Keep fp32 here. GPU and CPU results can differ slightly on borderline images. Don't delete existing prediction caches casually, because a fresh read of the test split adds counted reads.
>
> - **Make the bootstrap a matrix product.** Draw the cluster resample weights once with a multinomial, `W = rng.multinomial(G, np.ones(G)/G, size=R)`. Precompute per-cluster confusion counts `C` of shape `(G, k²)` for each model and level. Then the bootstrap confusions are `W @ C`, one matrix product. Reusing `W` across all levels, models and comparisons also keeps every comparison paired.
> - **Stage 1 and Stage 0** are fine as they are. The 1.6e8-pair step runs once per freeze, and the hashing is cheap. Revisit them only if the data grows 10×.
>
> ## Order of work
>
> 1. Run the `result.json` stats and profile `make_batch`. Time the GPU step alone with `benchmark.py`'s `step_time_fn`.
> 2. Apply the zero-risk changes: duplicate-seed fix, sync removal, prefetch, TF32, `channels_last`, fused AdamW.
> 3. Add pruning and the smaller ablation and confirm.
> 4. Port augmentation to the GPU. Before trusting it, compare CPU and GPU versions on 5k images per class. Check ink pixel count, bounding-box aspect ratio, stroke width and mean image per class, then train one seed of A1 on each and compare validation F1 within your seed-disagreement noise.
> 5. Move Stage 5 inference and the bootstrap to the faster forms.
>
> My rough expectations, not measurements:
>
> | Stage of work | Search | Per run |
> | --- | --- | --- |
> | Today | about 10 h | 3.7 min |
> | Steps 2–3 | about 3–4 h | about 1.5–2.5 min |
> | Step 4 | about 1–1.5 h | about 0.5–1 min |
>
> Tell me your GPU model, and whether the profile shows batch prep or the GPU step dominating after the sync fix. With those, I can tell you whether to port augmentation to the GPU or whether prefetch alone is enough.
> =============
> </pasted_content id="8717">
>
> "]

## Response

I'm splitting this report into four independent areas, with one investigating agent each. These four only read and report: no edits, nothing executed. Each claim gets a verdict with evidence from the current code.

Four agents are now checking the report's claims, one area each:

1. Search budget and pruning
2. Training loop and GPU settings
3. GPU augmentation and synthetic images
4. Evaluation and infrastructure

They can only read the code and report a verdict on each claim, so they won't edit or run anything. The independent code reviewer is still working too. I'll combine all the verdicts into one summary when they finish.

The GPU augmentation check is done. The main verdict is that a GPU port isn't worth doing in this iteration. A faithful version would have to rebuild most of the per-image logic and would force the settings to be selected again. The code doesn't use OpenCV at all, and the synthetic drawing isn't a hotspot. Three claim-checking agents and the code reviewer are still working.

The search-budget check is done, and most of those claims don't hold for the current code. They describe iteration 2's search (166 trials, 30 epochs), and iteration 3's is 200 trials at 60 epochs. Most of the proposed cuts, such as pruning, Optuna and a smaller top-K, are also ruled out by the pre-registered rules.

One point is worth keeping: 9 runs repeat work already done and could be reused, saving about 35 minutes. Two claim-checking agents and the code reviewer are still working.

The training-loop check is done. The report's analysis was out of date on most of this: batches are already prepared in parallel, the per-step GPU sync is already gone, and the byte-to-float conversion is already exact. Its "zero-risk" list doesn't hold, because TF32 for convolutions is already on and the matmul setting changes outputs, while `channels_last` and fused AdamW can't be confirmed exact without running.

The useful next step is timing a single lone run, once you allow it. One claim-checking agent and the code reviewer are still working.

All four claim checks are done, and only the code reviewer is still working. One finding from this last check matters beyond the report: the edit to `src/common/features.py` is included in the Stage 5 model fingerprint, so older saved predictions will count as out of date. Regenerating them would mean extra counted reads of the sealed data, so I'll treat that carefully in the run plan I bring you.

I'll send the combined summary when the reviewer reports. Nothing has been run.

**All the code work is finished, and none of it has been run or tested.** Nothing has been committed either: 18 files have uncommitted edits. The independent reviewer found no certain defects and confirmed most changes are exact by reasoning alone.

**What changed**

| Area | Change | Expected effect |
|---|---|---|
| Stages 2 and 3 | Cached ink facts, faster morphology, smaller array steps | Moderate CPU saving per image |
| Stage 4 | One long-lived worker pool, uint8 batches with an exact GPU lookup, no per-step GPU sync, cached validation images and data loading | Less overhead per trial; 5 bugs in my earlier code fixed |
| Stage 5 | Bootstrap does 2 matrix products per block instead of 46 | Probably seconds |
| Stages 0 and 1 | Faster hashing and near-duplicate grouping, lighter start-up | Seconds per run, near-duplicate step about 20 times faster |
| Stage 6 | One crash fix only | No speed change |

**The outside report:** most of it doesn't hold for today's code.
- **Out of date:** it describes iteration 2's search, and parallel prep, the GPU sync fix and the bootstrap matrix product already exist.
- **Would change results:** dividing by 255 on the GPU differs on 126 of 256 pixel values. AMP and relaxed determinism change results too, and determinism relaxed only for the search could change which settings win.
- **Not allowed:** pruning, Optuna and a smaller top-K break the pre-registered rules.
- **Not worth it now:** GPU augmentation, because a faithful port would force re-selecting the settings.
- **Worth keeping:** reusing 9 duplicate runs, about 35 minutes.

**Things to know before any run**
- **Don't run the full pipeline.** Shared code changed, so every stage's cache is invalid and a full run would read the sealed data.
- **Finished runs:** Stage 4's own cache will retrain finished runs. The 16 search trials can stay only if a rerun matches them exactly.
- **Only a run can confirm:** the GPU lookup, float64 loss accumulation, the shared pool on Windows, the Pillow change and the parallel guards.
- **Registering optimizations:** I'll add these to the CRISP-DM record once they're measured to help, as you asked.

**Proposed order, nothing starts until you approve**
1. Run the Stage 2, 3, 4 and contract tests.
2. Rerun two finished trials and compare every logged number with the originals.
3. If they match, relaunch the search and keep the 16 trials. If not, investigate first.

**Bugs found but left for you to decide**
- Stage 6 can report `passed` even when a traceability check fails.
- Stage 6's cache doesn't track some of its inputs.

Search trials also no longer write `val_curve.png`. Nothing reads it, and it saves about 2 minutes in total.

**Questions for you:**
- Can I run step 1 now?
- Should I fix the two Stage 6 bugs, and should I add the 9-run reuse? I'd do both, recording the reuse as a change.

The goal is still unfinished, but I'm not continuing it yet, because you told me not to run anything until I check with you. That still applies, and the automatic goal reminder doesn't override it.

One correction to that reminder: the search isn't running. I stopped it at 16 of 200 trials for this code-only session. The remaining phases need runs, so they're waiting on your answer.

I need two things from you:
1. Can I run the Stage 2, 3, 4 and contract tests?
2. Should I fix the two Stage 6 bugs and add the 9-run reuse?

The goal remains incomplete, and I'm still holding at your instruction. I won't run anything until you answer the two questions above.

Still holding: the goal isn't finished, and nothing will run until you reply.

Blocked on your approval, as the reminder itself notes. I'm waiting for your reply.

Waiting for your approval before anything runs.

Still waiting for your go-ahead.

The goal is blocked until you approve the next step.

Blocked pending your approval. Nothing is running.

## Validation

_Validation, Our decision and Measured effect are written by the team from the project record ([attribution_worksheet.csv](../../../results/llm_comparison/attribution_worksheet.csv)). They are not part of the session._

Four read-only agents each checked one area of the report against the current code and gave every claim a verdict.

## Our decision

Most of the report's cuts (pruning, Optuna, a smaller top-K) were ruled out by the pre-registered rules or described iteration 2's search. We kept one point: 9 runs repeated finished work and could be reused (C32).

## Measured effect

About 35 minutes saved on the search. No change to macro F1.

---

##  Comparison: Opus 5.5 Audits of Gemini 4 Neon (File 14 & Cross-File Synthesis)

### 1. What these files are

All four cross-critique files (`11_A14` through `14_real`) record the same pattern: **Claude Opus 5.5 (medium effort, in Claude Code) critiquing Gemini 4 Neon's reports** in a real, saved session. Files `12`–`14` are verbatim exchanges; `11_A14`

| File | Gemini report under review | Opus verdict | Worksheet entries |
|---|---|---|---|
| `12_…checks…gemini-review-of-the-training-document` | Review of the training document (4 precision errors, claims to verify, design points) | Mostly right; 3 of 27 points don't stand | C23–C27 |
| `13_…checks…speed-and-voting-audit` | Speed audit + equal-weight voting design | Direction right, several fixes overstated, some facts wrong | C40, C30, C31, F24 |
| `14_…sub-agents-check…speed-report` | Two-part speed/budget report (search + per-run) | Mostly out of date for iteration-3 code; one reuse point kept | C31, C32, C39 |
| `11_A14_…model-py-still-names-three-blocks` | `model.py` still defaults to three blocks | Stands; fixed in iteration 3 | A14 |

The through-line: **Gemini's findings were checked against code and measurements, not accepted or dismissed wholesale.** Valid points became iteration-3 work; invalid or out-of-date ones were dropped or disclosed.

### 2. File 14 — Sub-agents check the speed report

Opus split Gemini's two-part report into **four read-only areas**, one agent each — no edits, nothing executed:

1. Search budget and pruning
2. Training loop and GPU settings
3. GPU augmentation and synthetic images
4. Evaluation and infrastructure

**Verdicts:**
- **GPU augmentation:** not worth doing this iteration. A faithful port would have to rebuild most per-image logic and force the settings to be selected again. The code doesn't use OpenCV at all; synthetic drawing isn't a hotspot.
- **Search budget:** most claims don't hold for the current code — they describe iteration 2's search (166 trials, 30 epochs); iteration 3 is 200 trials at 60 epochs. Pruning, Optuna and a smaller top-K are **ruled out by the pre-registered rules**. One point kept: **9 runs repeat work already done** and could be reused, saving ~35 minutes (C32).
- **Training loop:** out of date — batches already prepared in parallel, per-step GPU sync already gone, byte-to-float conversion already exact. TF32 for convolutions already on; the matmul setting changes outputs; `channels_last` and fused AdamW can't be confirmed exact without running. Useful next step: time a single lone run, once allowed.

**What changed in the code (none of it run or tested):**

| Area | Change | Expected effect |
|---|---|---|
| Stages 2 and 3 | Cached ink facts, faster morphology, smaller array steps | Moderate CPU saving per image |
| Stage 4 | One long-lived worker pool, uint8 batches with exact GPU lookup, no per-step sync, cached validation images and data loading | Less overhead per trial; 5 bugs in earlier code fixed |
| Stage 5 | Bootstrap does 2 matrix products per block instead of 46 | Probably seconds |
| Stages 0 and 1 | Faster hashing and near-duplicate grouping, lighter start-up | Seconds per run; near-duplicate step ~20× faster |
| Stage 6 | One crash fix only | No speed change |

**What Gemini's report got, for today's code:** mostly out of date (iteration 2's search; parallel prep, GPU sync fix and bootstrap matrix product already exist); some "would change results" (GPU /255 differs on 126 of 256 pixel values; AMP and relaxed determinism change results; search-only relaxed determinism could change which settings win); some "not allowed" (pruning, Optuna, smaller top-K break pre-registered rules); one "worth keeping" (9 duplicate runs, ~35 min).

**Safety notes before any run:** don't run the full pipeline (shared code changed → every stage's cache invalid → a full run would read sealed data); Stage 4's own cache will retrain finished runs; the 16 search trials can stay only if a rerun matches exactly; only a run can confirm the GPU lookup, float64 loss accumulation, shared pool on Windows, Pillow change and parallel guards.

**Proposed order (nothing starts until approved):** (1) run Stage 2/3/4 and contract tests; (2) rerun two finished trials and compare every logged number; (3) if they match, relaunch and keep the 16 trials; if not, investigate.

**Bugs found but left for the owner:** Stage 6 can report `passed` even when a traceability check fails; Stage 6's cache doesn't track some inputs. Search trials no longer write `val_curve.png` (nothing reads it; saves ~2 min total). The session ends blocked, waiting on approval — the goal remains incomplete and nothing ran.

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

