# 4_testing - T16: docs(readme): explain the Stage 3 throughput gate needs an idle CPU
- LLM: Gemini 4 Neon 
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Entry: T16 (`task`, `deployment (not a course stage)`)
- Owner / Proposed by: 40297573 / 40297573
- Calibration: `winning-decision (70% tier)`
- Grounding sources: README.md, stages/stage_3.md, configs/pipeline.yaml, ShapeSense_Deployed/README.md, ShapeSense_Deployed/web/js/content/explain.js, ShapeSense_Deployed/web/stage6.html, ShapeSense_Deployed/web/changes.html, git commit 61cdf30

> **Simulated response:** The original Gemini 4 Neon chat was not exported. This file reconstructs a simulated Gemini 4 Neon response grounded in the committed ShapeSense repository and ShapeSense_Deployed static site.

## Prompt
Task T16 (documented, stage `deployment (not a course stage)`): docs(readme): explain the Stage 3 throughput gate needs an idle CPU. Propose or assist with the exact implementation, checks, and configuration needed for commit `61cdf30`.

## Response
In `stages/stage_3.md` (Requirement R8), Stage 3 enforces an absolute single-threaded throughput gate of `>= 2,000 images/s` so that a batch of 256 at 30% synthetic share (77 synthetic images) generates in under 40 ms without stalling Stage 4 training. With `configs/pipeline.yaml#synth.supersample: 2`, `generate(label, rng)` measures `5,929.7 img/s` (recorded in `ShapeSense_Deployed/web/js/content/explain.js`) on an idle machine, whereas `supersample: 4` previously failed the `2,000 img/s` gate.

However, if a teammate runs `python run_pipeline.py --stages 3` while Stage 4 training (`train.prep_workers` or background CPU workers) is saturating the cores, the single-threaded benchmark suffers OS scheduling contention and can dip below `2,000 img/s`, causing a spurious Stage 3 gate failure even though the generator itself is unchanged.

Add a concise troubleshooting bullet directly in the troubleshooting section of `README.md` (right after the `--dashboard` bullet and before the `Stage 4 is slow` bullet):

```markdown
- **Stage 3 fails its 2,000 img/s throughput gate**: the gate measures an idle
  CPU. Stop any training first, then rerun `--stages 3`.
```

This keeps the fix purely documentary - avoiding any relaxation of the `2,000 img/s` R8 threshold in `stages/stage_3.md` or Stage 3's benchmark script.

## Validation
1. Inspected `git diff README.md` to confirm the exact 2-line bullet placement in the troubleshooting list (`1 file changed, 2 insertions(+)`).
2. Verified consistency against `stages/stage_3.md` R8 (`>= 2,000 images/s single-threaded`) and `configs/pipeline.yaml` (`synth.supersample: 2`).
3. Confirmed that running `python run_pipeline.py --stages 3` on an idle CPU clears the `2,000 img/s` gate cleanly (`5,929.7 img/s` measured throughput vs `2,000 img/s` target).

## Our decision
The team committed the two-line `README.md` note verbatim in `61cdf30`, keeping the strict `2,000 img/s` Stage 3 R8 gate intact while giving teammates an explicit recovery step when background training causes CPU contention.

## Measured effect
- `README.md`: 2 lines added (`1 file changed, 2 insertions(+)`).
- Stage 3 R8 throughput gate (`2,000 img/s`) preserved without relaxation; idle-CPU runs sustain `5,929.7 img/s` at `synth.supersample: 2`.

---

## Upgraded & Expanded Technical Analysis (`T16`)

### 1. Real-Time Mini-Batch Budget Arithmetic (`< 40 ms` per Batch)
The `>= 2,000 images/s` single-threaded gate in `stages/stage_3.md` (Requirement R8) is derived directly from Stage 4's mini-batch synthesis budget:
- At mini-batch size $B = 256$ and `synthetic_fraction = 0.30`, each training step requires $n_{\text{syn}} = \text{round}(256 \times 0.30) = 77$ procedural shape renders.
- At the minimum gate threshold of $2,000\text{ img/s}$, generating $77$ images takes $77 / 2000 = 38.5\text{ ms} < 40\text{ ms}$, ensuring CPU batch preparation never starves the GPU forward/backward pass.
- At `configs/pipeline.yaml#synth.supersample: 2` ($128\times 128 \to 64\times 64$ area-box downsample), single-threaded throughput on an idle CPU reaches **$5,929.7\text{ img/s}$** ($\sim 13.0\text{ ms}$ per 77-image batch, $\sim 3\times$ safety headroom), whereas `supersample: 4` ($256\times 256 \to 64\times 64$, $4\times$ pixel fill cost) dropped below the $2,000\text{ img/s}$ threshold.

### 2. Why Documentary Remediation Preserves Gate Integrity
- **Environmental Contention vs. Algorithmic Regression:** When `run_pipeline.py --stages 3` runs concurrently with Stage 4's multiprocess `prep_workers` or GPU training loop, OS CPU scheduler time-slicing inflates wall-clock elapsed time inside the single-threaded benchmark, causing a false-negative gate failure.
- **Refusing to Relax the Threshold:** Lowering the R8 constant below $2,000\text{ img/s}$ to tolerate CPU contention would turn a strict performance guard into a weak check that permits genuine $O(S^2)$ rendering regressions (such as accidentally re-enabling `supersample: 4`). Documenting the idle-CPU precondition in `README.md` resolves operator confusion while keeping the benchmark fail-closed.


---

## Reviewer addendum (cross-entry review, not part of the simulated response)

**Depth only close reading reveals:** the fix is to refuse to change the code. The generator measures 5,929.7 img/s on an idle machine; a slow reading under contention is a measurement problem. Relaxing the 2,000 img/s gate would hide real regressions, and a retry loop would hide contention. The correct action is to free the CPU.

**Changelog:** [1] "change the process, not the threshold"; [2] gate integrity preserved; [3] bullet placement follows reader order: "Stage 3 fails" before "Stage 4 is slow."

**Open questions:** Is there a CI or idle-machine check that keeps the 5,929.7 figure current? Without one, the README can cite a stale number.
