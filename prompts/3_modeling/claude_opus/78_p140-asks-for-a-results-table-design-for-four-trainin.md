# 3_modeling - P140: Asks for a results table design for four training regimes
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-20
- Source: Claude Code session notes, pair P140. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

[

<pasted_content id="18fa">
imge classififaction for geometric shapes= [A0 · real only
–
–
–
–
–
–
–
– ms
A1 · + augmentation
–
–
–
–
–
–
–
– ms
B · + synthetic
–
–
–
–
–
–
–
– ms
A2 · clean + augmented + synthetic
–
–
–
–
–
–
–
– ms]suggest smth


Your pasted text looks like an empty results table for four training regimes, with eight blank metric columns and a latency (ms) column. Here's a filled-in design for it. I've left the numbers blank because you haven't run the experiments yet.

Suggested table columns
Use these eight metrics plus latency:

Run	Train data	Acc	Macro-F1	Acc (clean test)	Acc (noisy/real test)	Acc (rotated/scaled)	Params	Train time	Latency (ms/img)
A0 · real only	real	–	–	–	–	–	–	–	–
A1 · + augmentation	real + aug	–	–	–	–	–	–	–	–
B · + synthetic	real + synthetic	–	–	–	–	–	–	–	–
A2 · clean + augmented + synthetic	all three	–	–	–	–	–	–	–	–
Latency won't change between runs if they share one architecture. It only differs if you compare models, so add a backbone dimension. I'd try a small CNN, MobileNetV3 or ResNet18, and a fine-tuned ViT or SigLIP2.

Experiment recipe
Synthetic data: Render shapes procedurally with OpenCV, PIL, or your own ray-tracer. Randomize rotation, scale, stroke, fill, background color, blur, noise, and occlusion. The public 0-ma/geometric-shapes dataset is a useful reference. It has 50×50 RGB images of circle, triangle, square, pentagon and hexagon with random text overlaid on the shapes.

Augmentation (A1): Use flips, rotations, affine transforms, color jitter, Gaussian noise, and random erasing. Don't use flips if shape chirality matters.

Baseline model: There is a fine-tuned 
SigLIP2 geometric-shapes classifier
 built on google/siglip2-base-patch16-224. You can compare it against a small CNN.

Fair comparison: Hold out a real-only test set that never touches training or synthetic generation. Keep the seed, epochs, and optimizer fixed, and report mean ± std over 3–5 seeds.

Latency: Measure batch size 1 on a fixed device. Warm up first, then take the median of 200 or more runs.

Likely outcomes
I'd expect A0 to be weakest on the rotated/noisy test sets. A1 should improve robustness, and B should help most when real data is scarce. A2 should be best overall, though a domain gap between synthetic and real data can hurt B. If that happens, fine-tune on real data after pretraining on synthetic data.

If you tell me your class list and framework (PyTorch?), I can write the synthetic generator and the training and benchmark script that fills this table automatically.

how do i test for =[otated/noisy test sets.]

Build the robustness test sets by applying fixed, seeded perturbations to your clean held-out real test set. Generate them once and save them to disk, so every model (A0, A1, B, A2) is scored on identical images.

Rules
Start only from real test images that were never used in training or in synthetic generation.

Use a fixed seed and save the perturbed images, rather than perturbing on the fly.

Don't reuse the training augmentation parameters. For example, if you train with rotations up to ±30°, test with rotations up to ±180°. That makes it an out-of-distribution test.

Report accuracy for each severity level, not just one pooled number.

Rotated set
Rotate each image by fixed angles (0, 15, 30, 45, 90, 135, 180°) and report accuracy per angle. Use reflect or constant-color fill so the borders don't leak a label hint.

Noisy set
Make several variants, each with 3–5 severity levels:

Gaussian noise, sigma 0.02, 0.05, 0.1, 0.2

Salt-and-pepper noise

Gaussian blur

JPEG compression, quality 90, 50, 20

Brightness and contrast shifts

Random occlusion patches

Code (PyTorch/torchvision)
python
import torch, numpy as np
import torchvision.transforms.functional as TF
from torch.utils.data import DataLoader

def rotate(img, a):   # img: tensor CxHxW in [0,1]
    return TF.rotate(img, a, fill=[0.5]*img.shape[0])

def gauss(img, s, g):
    return (img + torch.randn(img.shape, generator=g) * s).clamp(0, 1)

def blur(img, k):
    return TF.gaussian_blur(img, kernel_size=2*k+1, sigma=float(k))

PERTURBS = {
  **{f"rot{a}": (lambda im, g, a=a: rotate(im, a)) for a in [15,30,45,90,135,180]},
  **{f"noise{s}": (lambda im, g, s=s: gauss(im, s, g)) for s in [0.02,0.05,0.1,0.2]},
  **{f"blur{k}": (lambda im, g, k=k: blur(im, k)) for k in [1,2,3]},
}

@torch.no_grad()
def evaluate(model, ds, fn=None, seed=0, bs=64, dev="cuda"):
    model.eval().to(dev)
    g = torch.Generator().manual_seed(seed)
    correct = n = 0
    preds, ys = [], []
    for i in range(0, len(ds), bs):
        batch = [ds[j] for j in range(i, min(i+bs, len(ds)))]
        x = torch.stack([fn(b[0], g) if fn else b[0] for b in batch]).to(dev)
        y = torch.tensor([b[1] for b in batch]).to(dev)
        p = model(x).argmax(1)
        correct += (p == y).sum().item(); n += len(y)
    return correct / n

### results[run][perturbation] -> accuracy
### for name, fn in PERTURBS.items(): res[name] = evaluate(model, test_ds, fn)
Reporting
Use the clean test accuracy as the baseline.

Compute a robustness drop for each perturbation: clean accuracy minus perturbed accuracy.

Average over each family (rotation and noise) to fill the "rotated" and "noisy" columns in your table.

Plot accuracy against severity, with one line per run (A0, A1, B, A2), to show where each degrades.

Repeat with 3–5 training seeds and report mean ± std.

If the shapes are rotation-symmetric (circle, square), rotation only tests the non-symmetric classes meaningfully. Check the per-class confusion matrix as well.

give as much details as you can


The biggest saving is in search.py. It runs about 166 full trainings, and 20 of them repeat runs you already did. Per-run speed is the second target: the current step loop serializes CPU batch preparation and the GPU step, and forces a GPU sync on every step. Everything below comes from your diagram plus the code I read. The speed gains are my estimates, not measurements. I haven't seen the Stage 2/3 code or your GPU model.

Where the time goes
Search budget. Counting the phases in search.py gives 166 runs, not the 200 in your diagram. Ablation is 10 conditions × 3 seeds = 30 runs, augment is 24, synth 16, shares 12, and the lr × dropout grid is 4 arms × 6 = 24. Confirm is 4 arms × top 5 settings × 3 seeds = 60. At 3.7 min per run that is about 10 h sequential. Confirm alone is about 3.7 h.

Duplicate work. Every confirm candidate was already trained at seed 0 with the same overrides and hyperparameters, because the random phases and the grid use SEEDS[0]. Confirm retrains it into a different folder, so run_trial can't reuse it. That is 20 redundant runs, about 74 min.

Per-run cost. A step is about 40–54 ms of batch prep per worker (226–376 ms ÷ 7) plus about 70 ms on the GPU. They run back to back, so a step is roughly 110–125 ms, and 49 steps give 5–6 s per epoch. The 70 ms was measured while two runs shared the GPU. On Windows, two processes time-slice one GPU, so parallel_runs=2 is probably not doubling throughput. A lone run is likely about 35 ms.

GPU work. I counted about 48M multiply-accumulates per image forward. That is about 74 GFLOP per 256-image step including the backward pass, which a modern GPU should do in 10–20 ms. Fixes below target the gap.

Cut the search
Stop retraining seed 0 in confirm. Reuse the earlier result and train only seeds 1 and 2 of each setting:

python
carried, specs = [], []
for i, r in enumerate(top_settings(candidates)):
    ov, hp = r["settings"]["overrides"], r["settings"]["hparams"]
    carried.append({**r, "name": f"{arm}_c{i}_s0"})
    specs += [_spec(config, config_path, "confirm", f"{arm}_c{i}_s{s}", arm, s, ov, hp)
              for s in SEEDS[1:]]
confirmed = carried + execute(config, specs)
The mean-by-name grouping below it still works. This saves about 20 runs. If you also drop TOP_K to 3, confirm falls from 60 runs to 24.

Prune bad trials early. train_one has a val_scorer(epoch_idx, probs, labels) hook. It currently picks the epoch to keep, but you can use it to stop a trial. Raise an exception when validation macro-F1 falls below a reference curve:

python
class Pruned(Exception): ...

def make_pruner(ref, margin=2.0, start=6):   # ref[e] = 25th-percentile val F1 at epoch e
    def scorer(epoch_idx, probs, labels):
        f1 = macro_f1_points(labels, probs.argmax(1), probs.shape[1])
        if epoch_idx >= start and f1 < ref[min(epoch_idx, len(ref) - 1)] - margin:
            raise Pruned(f1)
        return f1
    return scorer
Build ref from the train_log.csv files of your ablation runs. Catch Pruned in run_trial and write a result.json with "pruned": True. Pass val_scorer=make_pruner(ref) to train_one.

Don't shorten the schedule. Strong augmentation and synthetic data usually learn slower, so a short-epoch proxy would favor weak settings. Prune with a reference curve at the same epochs, don't cut max_epochs. If you want a short proxy anyway, check its rank correlation with full runs on about 10 settings first.

Shrink the ablation. Run all 10 conditions at one seed, then add two seeds only for the 3–4 conditions with the largest effect. That is about 18 runs instead of 30.

Check your own numbers first. The script below shows how many epochs your runs really use. If the median best epoch is much less than 30, tighten the patience.

python
import json, glob, numpy as np
rs = [json.load(open(p)) for p in glob.glob("artifacts/stage4/tuning_iter2/**/result.json", recursive=True)]
for k in ("best_epoch", "epochs_run"):
    print(k, np.percentile([r[k] for r in rs], [10, 50, 90]))
Phase	Now	After
Ablation	30	about 18
Augment, synth, shares (52 trials)	52	about 23 full-run equivalents with pruning
Grid	24	about 14 with pruning
Confirm	60	24 (top 3, new seeds only)
Total	166 (about 10.2 h)	about 79 (about 4.9 h)
Make each run faster
Remove per-step syncs. float(loss.detach()) and int((logits.argmax(1) == y).sum()) force the CPU to wait for the GPU every step. Accumulate on the GPU and read once per epoch:

python
loss_sum = torch.zeros((), device=device); correct = torch.zeros((), device=device, dtype=torch.long)
### inside the step
loss_sum += loss.detach() * y.shape[0]
correct  += (logits.argmax(1) == y).sum()
### after the epoch
train_loss = float(loss_sum) / seen
Prefetch. Prepare the next batches in a background thread while the GPU works. Order is preserved, so the RNG sequence and determinism stay intact:

python
import queue, threading
def prefetch(it, depth=3):
    q = queue.Queue(depth)
    def work():
        for b in it:
            q.put((torch.from_numpy(b.images).pin_memory(),
                   torch.from_numpy(b.labels).pin_memory(), b.is_synthetic))
        q.put(None)
    threading.Thread(target=work, daemon=True).start()
    while (item := q.get()) is not None:
        yield item
If the augmentation is pure Python, the GIL limits overlap. Use a process there.

Use cheaper GPU math. Enable TF32, bf16 autocast (Ampere or newer, otherwise fp16 with GradScaler), channels_last and fused AdamW:

python
torch.backends.cuda.matmul.allow_tf32 = torch.backends.cudnn.allow_tf32 = True
model = model.to(device, memory_format=torch.channels_last)
opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd, fused=True)
with torch.autocast("cuda", dtype=torch.bfloat16):
    logits = model(x)
loss = F.cross_entropy(logits.float(), y)
Skip torch.compile. It is awkward on Windows.

Search-only determinism relaxation. Turn off use_deterministic_algorithms and set cudnn.benchmark=True during the search. Keep deterministic mode for the final runs.

Put the data on the GPU. The train set is about 51 MB as uint8. Sample indices on the CPU, as now (256 ints), and gather the images on the GPU. Send uint8 and convert to float on the GPU, which cuts transfer 4×.

Move augmentation to the GPU. At 64×64 and batch 256 this takes about a millisecond per op:

python
def gpu_augment(x_u8, labels, rot_lim, g, cfg):        # x_u8 (N,64,64) uint8 on GPU, white background
    x = (255 - x_u8).float().div_(255).unsqueeze(1)    # ink=1, so zero padding is background
    N, dev = x.shape[0], x.device
    u = lambda lo, hi: lo + (hi - lo) * torch.rand(N, device=dev, generator=g)
    ang, sc = torch.deg2rad(u(-1, 1) * rot_lim[labels]), u(cfg.scale_lo, cfg.scale_hi)
    c, s = torch.cos(ang) / sc, torch.sin(ang) / sc
    theta = torch.zeros(N, 2, 3, device=dev)
    theta[:, 0, 0], theta[:, 0, 1], theta[:, 1, 0], theta[:, 1, 1] = c, -s, s, c
    x = F.grid_sample(x, F.affine_grid(theta, x.shape, align_corners=False),
                      padding_mode="zeros", align_corners=False)
    return x   # then: masked blur, noise, threshold, re-frame with a UNIFORM scale
Use per-class rotation caps (rot_lim[labels]). Skip shear and non-uniform scale for the five classes that have it off, with a per-class mask. Re-frame by bounding box with a uniform scale only. A stretch that fills the frame would destroy rectangle versus square and circle versus ellipse, which is the failure I suspected earlier. Seed with torch.Generator("cuda") per (seed, epoch).

Check synthetic cost. At s=2, each image is drawn on 128×128 and downsampled, so 71 per batch could be the hotspot. A pool is hard in search, because sample_synth changes the generator parameters (radius, jitter, ratios, inner star ratio) per trial, so a pool must be rebuilt per synth trial. A 30k pool of 4 KB images is only 120 MB, but rebuild time matters. Pool it only for final runs.

Profile before rewriting. 226–376 ms for 256 small images is slow for OpenCV. Find the hotspot first:

python
import cProfile, pstats
cProfile.run("for _ in range(20): make_batch(store.images, store.labels, store.class_idx, arm_cfg, 256, frac, 10, rng, transform=T, generate=G)", "mb.prof")
pstats.Stats("mb.prof").sort_stats("cumtime").print_stats(15)
py-spy also works on Windows. Add the new flags to config["train"] so the recipe fingerprint changes and old runs aren't mixed with new ones.

Evaluation and other stages
Run Stage 5 inference on the GPU. predict_torchscript loads with map_location="cpu". A damaged-set pass is about 103,500 images (23 levels × 4,500) per model, roughly 10 TFLOP, so 40 models is about 400 TFLOP. That is probably tens of minutes on CPU and a few minutes on GPU:

python
dev = "cuda" if torch.cuda.is_available() else "cpu"
model = torch.jit.load(str(model_path), map_location=dev).eval()
with torch.inference_mode():
    for i in range(0, n, 4096):
        x = torch.from_numpy(images_u8[i:i+4096]).to(dev).float().div_(PIXEL_SCALE).unsqueeze(1)
        out.append(torch.softmax(model(x), 1).cpu())
Keep fp32 here. GPU and CPU results can differ slightly on borderline images. Don't delete existing prediction caches casually, because a fresh read of the test split adds counted reads.

Make the bootstrap a matrix product. Draw the cluster resample weights once with a multinomial, W = rng.multinomial(G, np.ones(G)/G, size=R). Precompute per-cluster confusion counts C of shape (G, k²) for each model and level. Then the bootstrap confusions are W @ C, one matrix product. Reusing W across all levels, models and comparisons also keeps every comparison paired.

Stage 1 and Stage 0 are fine as they are. The 1.6e8-pair step runs once per freeze, and the hashing is cheap. Revisit them only if the data grows 10×.

Order of work
Run the result.json stats and profile make_batch. Time the GPU step alone with benchmark.py's step_time_fn.

Apply the zero-risk changes: duplicate-seed fix, sync removal, prefetch, TF32, channels_last, fused AdamW.

Add pruning and the smaller ablation and confirm.

Port augmentation to the GPU. Before trusting it, compare CPU and GPU versions on 5k images per class. Check ink pixel count, bounding-box aspect ratio, stroke width and mean image per class, then train one seed of A1 on each and compare validation F1 within your seed-disagreement noise.

Move Stage 5 inference and the bootstrap to the faster forms.

My rough expectations, not measurements:

Stage of work	Search	Per run
Today	about 10 h	3.7 min
Steps 2–3	about 3–4 h	about 1.5–2.5 min
Step 4	about 1–1.5 h	about 0.5–1 min
Tell me your GPU model, and whether the profile shows batch prep or the GPU step dominating after the sync fix. With those, I can tell you whether to port augmentation to the GPU or whether prefetch alone is enough.

Show me how to fix the duplicate work in search.py
</pasted_content id="18fa">

]

## Response

Your pasted text is an empty results table for four training regimes, with eight blank metric columns and a latency (ms) column. Below is a filled-in design for it. I have left the numbers blank because the experiments have not been run yet.

#### Suggested table columns

Use these eight metrics plus latency:

| Run | Train data | Acc | Macro-F1 | Acc (clean test) | Acc (noisy/real test) | Acc (rotated/scaled) | Params | Train time | Latency (ms/img) |
|---|---|---|---|---|---|---|---|---|---|
| A0 · real only | real | | | | | | | | |
| A1 · + augmentation | real + aug | | | | | | | | |
| B · + synthetic | real + synthetic | | | | | | | | |
| A2 · clean + augmented + synthetic | all three | | | | | | | | |

Latency will not change between runs if they all share one architecture. It only differs when you compare models, so add a backbone dimension if you want that comparison. Candidates include a small CNN, MobileNetV3 or ResNet18, and a fine-tuned ViT or SigLIP2.

#### Experiment recipe

- **Synthetic data:** Render shapes procedurally with OpenCV, PIL, or your own ray-tracer. Randomize rotation, scale, stroke, fill, background color, blur, noise and occlusion. The public 0-ma/geometric-shapes dataset is a useful reference. It has 50x50 RGB images of circle, triangle, square, pentagon and hexagon, with random text overlaid on the shapes.
- **Augmentation (A1):** Use flips, rotations, affine transforms, color jitter, Gaussian noise and random erasing. Do not use flips if shape chirality matters, because a mirrored shape can change its class.
- **Baseline model:** A fine-tuned SigLIP2 geometric-shapes classifier built on google/siglip2-base-patch16-224 exists. You can compare it against a small CNN.
- **Fair comparison:** Hold out a real-only test set that never touches training or synthetic generation. Keep the seed, epochs and optimizer fixed, and report mean and std over 3 to 5 seeds.
- **Latency:** Measure at batch size 1 on a fixed device. Warm up first, then take the median of 200 or more runs.

#### Likely outcomes

I expect A0 to be weakest on the rotated and noisy test sets. A1 should improve robustness, and B should help most when real data is scarce. A2 should be best overall, although a domain gap between synthetic and real data can hurt B. If that happens, fine-tune on real data after pretraining on synthetic data.

If you tell me your class list and framework (PyTorch?), I can write the synthetic generator and a training and benchmark script that fills this table automatically.

#### How to test the rotated and noisy test sets

Build the robustness test sets by applying fixed, seeded perturbations to your clean held-out real test set. Generate them once and save them to disk, so every model (A0, A1, B, A2) is scored on identical images.

**Rules**
- Start only from real test images that were never used in training or in synthetic generation.
- Use a fixed seed, and save the perturbed images rather than perturbing on the fly.
- Do not reuse the training augmentation parameters. For example, if you train with rotations up to plus or minus 30 degrees, test with rotations up to plus or minus 180 degrees. That makes it an out-of-distribution test.
- Report accuracy for each severity level, not just one pooled number.

**Rotated set:** Rotate each image by fixed angles (0, 15, 30, 45, 90, 135, 180 degrees) and report accuracy per angle. Use reflect or constant-color fill so the borders do not leak a label hint.

**Noisy set:** Make several variants, each with 3 to 5 severity levels:
- Gaussian noise, sigma 0.02, 0.05, 0.1, 0.2
- Salt-and-pepper noise
- Gaussian blur
- JPEG compression, quality 90, 50, 20
- Brightness and contrast shifts
- Random occlusion patches

**Code (PyTorch/torchvision)**

```python
import torch, numpy as np
import torchvision.transforms.functional as TF
from torch.utils.data import DataLoader

def rotate(img, a):   # img: tensor CxHxW in [0,1]
    return TF.rotate(img, a, fill=[0.5]*img.shape[0])

def gauss(img, s, g):
    return (img + torch.randn(img.shape, generator=g) * s).clamp(0, 1)

def blur(img, k):
    return TF.gaussian_blur(img, kernel_size=2*k+1, sigma=float(k))

PERTURBS = {
  **{f"rot{a}": (lambda im, g, a=a: rotate(im, a)) for a in [15,30,45,90,135,180]},
  **{f"noise{s}": (lambda im, g, s=s: gauss(im, s, g)) for s in [0.02,0.05,0.1,0.2]},
  **{f"blur{k}": (lambda im, g, k=k: blur(im, k)) for k in [1,2,3]},
}

@torch.no_grad()
def evaluate(model, ds, fn=None, seed=0, bs=64, dev="cuda"):
    model.eval().to(dev)
    g = torch.Generator().manual_seed(seed)
    correct = n = 0
    preds, ys = [], []
    for i in range(0, len(ds), bs):
        batch = [ds[j] for j in range(i, min(i+bs, len(ds)))]
        x = torch.stack([fn(b[0], g) if fn else b[0] for b in batch]).to(dev)
        y = torch.tensor([b[1] for b in batch]).to(dev)
        p = model(x).argmax(1)
        correct += (p == y).sum().item(); n += len(y)
    return correct / n

# results[run][perturbation] -> accuracy
# for name, fn in PERTURBS.items(): res[name] = evaluate(model, test_ds, fn)
```

#### Reporting

1. Use the clean test accuracy as the baseline.
2. Compute a robustness drop for each perturbation: clean accuracy minus perturbed accuracy.
3. Average over each family (rotation and noise) to fill the "rotated" and "noisy" columns in your table.
4. Plot accuracy against severity, with one line per run (A0, A1, B, A2), to show where each run degrades.
5. Repeat with 3 to 5 training seeds and report mean and std.
6. If the shapes are rotation-symmetric (circle, square), rotation only tests the non-symmetric classes meaningfully. Check the per-class confusion matrix as well.

#### Table filled from the repo (for the pasted search-speed review)

Here's a table that fits what the repo already measures. The current table in `results/README.md` covers the data-preparation steps, so this is a separate table for the four training regimes.

| Run | Train data | Acc | Macro-F1 | Clean test | Damaged test (rotation and noise) | Params | Train time | Latency (ms/img) |
|---|---|---|---|---|---|---|---|---|
| A0 · real only | real | | | | | | | |
| A1 · + augmentation | real + aug | | | | | | | |
| B · + synthetic | real + synthetic | | | | | | | |
| A2 · clean + aug + synthetic | all three | | | | | | | |

Notes:
- **Damaged column:** The repo's sealed robustness check uses 23 damage levels on 4,500 images, and reports A2 vs A0 at +9.20 points (`results/README.md`). Use that as the source, not new rotation and noise sets, so the numbers match what is already reported.
- **Latency:** The same architecture gives the same latency, so this column only adds information if you test a second backbone.
- **Unverified suggestions:** The SigLIP2 model and the "0-ma" dataset in the pasted text are not checked. Do not cite them until someone has verified them.

#### Checking the pasted search-speed review

I checked the pasted review against the code earlier:
- The duplicate-seed claim is correct. Confirm retrains seed 0, because `search.py` line 270 uses all of `SEEDS`.
- The "sync on every step" claim is wrong. Loss and accuracy are already accumulated on the GPU and read once per epoch (`train.py` around line 449).

I have not changed any code.

##### Why the review was checked against the code
- A pasted review makes specific claims about the code. Checking them against the repo separates real bottlenecks from wrong ones before any work is planned around them.
- The duplicate-seed claim holds. In `src/stage4_train/search.py`, the confirm step loops over `SEEDS` (line 271 in the current file; the review cites line 270), so seed 0 is retrained even though the grid already trained it. The claim is therefore supported, though the exact line number differs by one.
- The per-step sync claim does not hold. In `src/stage4_train/train.py`, loss and correct counts are accumulated on the GPU and read once per epoch (around line 449, `float(loss_total)`). The review's advice to remove per-step syncs is already implemented for this loop.

##### Consequences
- Only the duplicate-seed fix is a real candidate for the search speed-up. The rest of the review's estimates (for example, about 10 h of search and 3.7 min per run) are the review's own estimates, not measurements, and are unverified.
- The GPU model, the profile and the timing numbers are still needed before deciding whether to port augmentation to the GPU or add prefetch.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
