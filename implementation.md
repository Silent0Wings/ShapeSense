# Plan: Model A vs Model B evaluation — 7 stages, 6 owners

> **Current direction (2026-11-09).** This is the original v4 plan, kept as
> written. The project has since run two failed experiments, added arms A2 and
> P, and moved to a third iteration on robustness. Stage 7 (`stages/stage_7.md`)
> is new. Where this plan disagrees with the record, follow
> [`docs/crisp_dm/README.md`](docs/crisp_dm/README.md).

> **v4.** Reconciles the plan with the code that is actually committed and
> fixes the defects found in the v3 audit (`plan_issues.md`, P-20–P-38).
>
> Four changes a returning reader should know about:
>
> 1. **Names follow the repository, not the plan.** Stages live in
>    `src/stageN_*/`, settings in `configs/pipeline.yaml` and
>    `configs/taxonomy.yaml`, outputs in `artifacts/stageN/`. The v3
>    names (`src/shapes/`, `params.yaml`, `artifacts/sN/`) are gone.
>    Stage 0 no longer renames anything.
> 2. **`run_pipeline.py` is the pipeline.** DVC is an optional add-on,
>    not a dependency. Caching and input hashes are explicit fields in
>    `status.json`.
> 3. **The split is rebuilt, and the Phase 1 counts will not survive.**
>    pHash groups are now computed across all sources (Decision 15), and
>    the gemstone filter runs before the split. 12,761 / 2,890 / 2,849
>    are historical numbers.
> 4. **Decisions 13–16 are new**: the epoch budget and what it holds
>    constant, baseline evaluation, split recomputation, and where the
>    frozen splits live.

The work is split into stages with one owner each. Each stage has a
contract: **Input** (what it consumes), **Action** (what the owner does),
**Output** (the artifact handed off), and **Done when** (the checkable
finish line). Source facts come from the Phase 1 report.

Each stage owner also has a standalone brief in `stages/stage_N.md`
(N = 0–6), covering focus, goals, requirements, deliverables, pitfalls, a
glossary and three practice missions. `stages/stage_7.md` is the final
stage: a frozen public dashboard, built only after every gate is met and
the user approves.

## Decisions to lock first (whole team, before Stage 1)

1. **Gemstone diamonds (Quick, Draw!).** Filter before the split;
   filtering later would change the test set and break the freeze.
   *Diverges from the report*, which says the gemstones "might" be
   filtered later (sections C and D); Stage 6 updates that wording.
   - **Review method:** two team members independently review all 500
     Quick, Draw! `diamond` images from a contact sheet. A drawing counts
     as a gemstone if it has facet lines inside the outline, a flat
     "crown" top, or more than four outer vertices. A third member
     settles disagreements. About 1 hour, done before Stage 1 runs.
   - **The list is keyed on content, not position.** `image_id` is
     assigned by position in the Phase 1 build
     (`f"{source}_{label}_{i:06d}"`, `build_unified_dataset.py:185`), so
     any rebuild from a slightly different raw set renumbers every later
     image and an ID-keyed list would silently drop the wrong drawings.
     The committed file `configs/gemstone_ids.csv` therefore carries
     `image_id, md5` and Stage 1 matches on `md5`, failing the stage if
     any row fails to match exactly once. The contact sheet prints the
     md5 prefix under each thumbnail so reviewers record both.
   - `filter_gemstones` in `configs/pipeline.yaml` is frozen once this is
     decided; changing it invalidates every stage.
2. **Three arms, not two.** A plain A-vs-B mixes the augmentation effect
   with the synthetic effect. A0 (real only), A1 (real + aug),
   B (real + aug + synthetic) isolate both. Cost: ~1 extra training day.
   *Diverges from the report*, whose Figure 2 (`fig:evalsplit`) and
   evaluation goal describe two models; Stage 6 updates both.
3. **When the success criterion is locked.** The criterion itself is
   Decision 10. It is written into `configs/pipeline.yaml` on D0, before
   any model is trained, and it is not editable after Stage 4 starts.
   Changing it needs a PR that every owner approves and that states what
   was known at the time. This process rule, not the threshold, is what
   keeps the evaluation honest.
4. **Pipeline runner.** `run_pipeline.py`, already committed. Stages are
   self-contained under `src/stageN_*/` and expose `run(config)`. Each
   stage records its input hashes in `status.json`, and a stage is
   skipped when every input hash matches its last recorded run.
   DVC is an **optional** add-on for anyone who wants `dvc repro`
   caching; the file contracts below are identical either way, so
   adopting it later costs nothing. It is not on the critical path and
   no Done-when depends on it.
5. **Data sharing.** `data_set/` is gitignored. Primary: a shared
   network/OneDrive folder holding the raw archive plus its SHA-256,
   verified by Stage 0 on a second machine. A DVC remote on Google Drive
   is an optional upgrade, not a prerequisite.
   The *splits* are shared through Git instead — see Decision 16.
6. **Training machine.** Name the machine that runs the CNN trainings. The
   budget is **up to 23 runs**, not 15:

   | Runs | What |
   |---|---|
   | 6 | Decision 7's tuning grid (3 LR × 2 dropout, A1, one seed) |
   | 9–15 | 3 arms × 3–5 seeds |
   | 2 | Decision 12's leave-one-source-out A1 and B, if triggered |
   | 2 | Decision 14's baselines (minutes each, not hours) |

   A small CNN on 64×64 single-channel images is feasible on CPU; a GPU
   only shortens Stage 4. Stage 4's D3 loader benchmark turns this count
   into a wall-clock estimate before the sweep starts.
7. **Hyperparameter tuning rule.** Tune **once**, on **arm A1's
   validation** split. A1 is the middle arm, so neither A0 nor B is
   favoured. Use a small fixed grid (learning rate {3e-4, 1e-3, 3e-3} ×
   dropout {0.2, 0.4}) with one seed — 6 runs. Then freeze the winner in
   `configs/pipeline.yaml#train` for every arm and every seed. No arm is
   ever tuned separately. Stage 4 records the grid results.
8. **Default CNN (starting point for Decision 7).**
   - Layers: input 1×64×64 → 3 blocks of
     [Conv 3×3 → BatchNorm → ReLU → MaxPool 2] with 32 / 64 / 128
     channels → global average pool → Dropout → Linear(128 → 10).
     About 100k parameters, which is CPU-friendly.
   - Training: AdamW (weight decay 1e-4), batch 256, at most 30 epochs,
     cosine learning-rate schedule, early stopping with patience 5 on
     validation macro-F1.
   - All of this lives in `configs/pipeline.yaml#train`; the code only
     reads it.
9. **Seed aggregation and the primary hypothesis.**
   - **Primary hypothesis (one test, α = 0.05):** B vs A1 on macro-F1.
   - **Primary analysis:** each arm's seeds are combined into a
     **soft-vote ensemble** (averaged softmax), giving one prediction per
     test image per arm. The primary macro-F1 difference gets a paired
     bootstrap 95% CI. McNemar's test on paired correctness is a
     supporting accuracy comparison, not a test of macro-F1 itself.
   - **Robustness check:** the per-seed paired differences (seed *k* of
     A1 vs seed *k* of B), reported as mean ± std. The report states
     whether the difference has the same sign for every seed.
   - **Secondary comparisons:** A0 vs A1 and A0 vs B use a Holm
     correction across the two tests.
   - **Per-class and per-source results are descriptive**, with one
     stated exception: the class-drop guardrail in Decision 10 uses
     per-class bootstrap intervals. That guardrail is a pre-registered
     stopping rule, not a significance claim, so no multiplicity
     correction is applied to it and no per-class p-value is reported.
10. **Noise-aware success criterion.** Test classes are **not** equally
    sized. Phase 1 test counts range from 150 to 572:

    | Class | n | Noise band | Class | n | Noise band |
    |---|---:|---:|---|---:|---:|
    | ellipse | 150 | 2.4 | star | 245 | 1.9 |
    | pentagon | 157 | 2.4 | rectangle | 300 | 1.7 |
    | diamond | 225 | 2.0 | circle | 375 | 1.5 |
    | hexagon | 225 | 2.0 | square | 375 | 1.5 |
    | octagon | 225 | 2.0 | triangle | 572 | 1.3 |

    The band is `100 × sqrt(0.9 × 0.1 / n)` — one standard error of
    recall at 90% accuracy, in F1 points. A flat "285 per class" figure
    understates the band on ellipse and pentagon and overstates it on
    triangle, so it is wrong in both directions at once.
    Stage 1 recomputes this table for the new split and writes it to
    `artifacts/stage1/split_stats.csv`; Stage 5 reads it rather than
    hard-coding the numbers above.
    - **Main rule:** B passes if its ensemble macro-F1 gain over A1 is at
      least 1 point and its 95% CI excludes 0.
    - **Class-drop guardrail:** B fails if any class's F1 drops by more
      than `max(2.0, its noise band)` points **and** that class's paired
      bootstrap CI for the drop excludes 0. In practice that is 2.4
      points for ellipse and pentagon, 2.0 for every other class. A drop
      inside the band is reported, but it does not fail the criterion.
    - **Power check before the test set is opened:** Stage 5 runs the
      same paired bootstrap on A1's and B's **validation** predictions
      and rescales the half-width by `sqrt(n_val / n_test)`. Validation
      and test are nearly the same size, so that factor is ≈ 1.01 and the
      validation half-width is a direct estimate of the test one. If it
      exceeds 1 point, the report says up front that the experiment may
      be unable to detect a 1-point gain. The criterion is not changed.
      (Seed-to-seed disagreement is a separate robustness number. It does
      **not** estimate this CI, because the primary comparison is between
      two ensembles and the bootstrap resamples images, not seeds.)
11. **Class balance and synthetic mix.**
    - The loader uses **class-balanced sampling** for every arm: each
      batch draws real images evenly across the 10 classes, so the
      single-source classes are not under-trained. The same sampler runs
      in all arms, so it does not affect the comparison.
    - The ~30% synthetic share in arm B is spread **evenly across all 10
      classes**.
12. **What happens if the source classifier finds a shortcut.** Trigger:
    on classes with two or more sources, a source classifier trained on
    standardized pixels beats the majority-source rate by more than 10
    points. If it fires:
    - Stage 5 reports accuracy per source for every arm as a required
      table, not an optional one.
    - Pentagon and ellipse results carry the asterisk.
    - A leave-one-source-out run moves from "if time allows" to
      **required**: retrain A1 and B without the Hand-Drawn source, then
      test only on Hand-Drawn. Costs 2 extra training runs.
13. **Epoch budget, and what is held constant across arms.** Because
    Decision 11 uses class-balanced sampling, an "epoch" is no longer a
    pass over the training set — it is a fixed number of optimizer steps.
    - `steps_per_epoch` is computed **once** from arm A0
      (`ceil(n_train / batch_size)`) and frozen in
      `configs/pipeline.yaml#train`. Every arm runs the same steps per
      epoch, the same maximum epochs and the same early-stopping rule.
    - **Stated consequence:** at a 30% synthetic share, arm B draws 0.7 ×
      `batch_size` real images per step, so over the frozen step budget B
      sees ~30% fewer real-image draws than A1. The primary comparison is
      therefore *equal compute*, and it answers: **does replacing 30% of
      each batch with synthetic data help?** The report must say this in
      the results section — it is half of what the number means.
    - The other question (does synthetic data help when *added* to the
      real stream rather than substituted for part of it?) is the
      optional `B_equalreal` ablation in Stage 6: 256 real + 110
      synthetic per batch, same step budget.
14. **Baselines are evaluated on the test set.** Two baselines — logistic
    regression on raw pixels and a linear SVM on HOG features — train on
    the same class-balanced real stream as A0 and are selected on
    validation. Stage 5 evaluates each **once** on test, so the report
    compares baselines and CNNs on the same data. They are context, not
    part of the primary hypothesis. The test-access accounting in
    *Separation of concerns* counts them.
15. **The split is recomputed, and the Phase 1 counts will change.**
    - pHash near-duplicate groups are formed **globally over all
      sources**. The Phase 1 build grouped only within each
      (source, label) pair (`build_unified_dataset.py:162`), so a shape
      that two sources drew near-identically was never grouped and could
      straddle train and test. Stage 1 fixes this.
    - Combined with Decision 1's filter, 12,761 / 2,890 / 2,849 will not
      be reproduced. Stage 1 publishes the new counts and Stage 6 updates
      the report's **Split** paragraph (`phase1_report.tex:466–467`).
      Nobody forces the old numbers.
    - `Image.split` in the catalog and the `data_set/unified/{train,
      val,test}/` path prefixes are Phase 1 artifacts. From Stage 1
      onward they are ignored; `common.load_split()` is the only
      authority on split membership.
16. **The frozen splits live in Git.** Stage 1 writes
    `configs/splits/{train,val,test}.csv` and they are **committed**.
    `artifacts/` is gitignored, so a split kept there would be
    per-machine and unreviewable; a split in Git means the freeze is a
    diff that every owner can see, and changing it requires a PR.
    `data_set/` stays gitignored.

## Repository layout

What is already committed:

```
src/
  common/            config.py, interfaces.py, registry.py, batch.py
  stage1_freeze/     stage2_augment/   stage3_synth/
  stage4_train/      stage5_eval/      stage6_report/
configs/
  pipeline.yaml      experiment settings (the shared numbers)
  taxonomy.yaml      10 classes, ambiguity margins, label-safety rules
  splits/            frozen manifests, written by Stage 1 (Decision 16)
artifacts/stage1 … stage6/        stage outputs (gitignored)
scripts/             Phase 1: standardize, taxonomy, build, audit, FD checks
run_pipeline.py      the pipeline entry point
build.ps1            LaTeX build, called by Stage 6
```

What Stage 0 adds: `src/common/{status.py, splits.py, hashing.py}`,
`artifacts/stage0/`, `tests/contracts/`, `dashboard/`, `demo/`,
`export/`, `requirements.txt`, `.python-version`, `.importlinter`,
`.pre-commit-config.yaml`, `CODEOWNERS`, `README.md`.

**Two config files, one rule each.** `configs/taxonomy.yaml` holds what
a class *is* — the 10 names, the ambiguity margins, the list of classes
that shear and non-uniform scale would relabel. It was settled in
Phase 1 and should not change. `configs/pipeline.yaml` holds every
experimental setting: seed set, split ratios, `filter_gemstones`,
synthetic ratio, the augmentation ranges, the `runs` list (arm × seed),
training defaults and tuning grid, balanced-sampling flags, step budget
(Decision 13) and the evaluation criterion. No stage hard-codes any of
these — including `src/common/batch.py`, whose current
`SYNTHETIC_FRACTION = 0.3` and `IMAGE_SIZE = 64` constants Stage 0
replaces with config reads.

## Pipeline overview

```
  Stage 0  infrastructure  (status writer, split guard, contract tests,
     │     import boundaries, environment, README)
     │     — every stage below plugs into it —
     ▼
  Stage 1            Stage 2   augmentation module
  data freeze  ───┬──────────→ (class-safe transforms) ──┐
  + splits        │           Stage 3   synthetic        │
                  └──────────→ generator (Pillow)     ──┤
                                                         ↓
                    Stage 4   training: A0 / A1 / B
                    (loader, baselines, CNN, 3–5 seeds)
                                                         ↓
                    Stage 5   evaluation + statistics
                    (test set touched ONCE here)
                                                         ↓
                    Stage 6   report + packaging

  Dashboard (read-only) ◄── artifacts/stage0 … stage6/status.json
```

Stages 2 and 3 are independent and run in parallel. Stage 4 can start its
loader, baselines and A0 arm while 2 and 3 are still running. Stage 6's
figure and dashboard work can start immediately; only its results tables
wait on Stage 5. Stage 0 delivers working stubs on day 1, so nobody waits
for it.

## One-click run

```
python run_pipeline.py                 # every stage whose inputs changed
python run_pipeline.py --stages 3      # one stage (and its dependencies)
python run_pipeline.py --check         # guards only: imports + contract tests
python run_pipeline.py --dashboard     # open the read-only dashboard
python run_pipeline.py --demo          # draw a shape, press Infer (export/ only)
python run_pipeline.py --force         # ignore the hash cache, rerun everything
```

The guards run first; a guard failure stops the run before any stage
executes. Stage 6 shells out to `build.ps1 -File phase2_report.tex` to
compile the report — note the `-File` argument, because `build.ps1`
defaults to `phase1_report.tex`.

**Caching.** Each stage writes the hash of every input it read into
`status.json → inputs`. On the next run, a stage whose recorded hashes
all still match is skipped. One mechanism, visible in one file, no extra
tool. Stage 0 implements it once in `common.status`; stages never
implement their own.

## Shared conventions

**`artifacts/stageN/status.json`** — written by every stage through
`common.status`, never by hand:

```json
{
  "stage": "stage1",
  "owner": "______",
  "run_id": "2026-11-10T09:00:00-05:00/3f9a1c",
  "status": "passed",
  "started_at": "2026-11-10T09:00:00-05:00",
  "finished_at": "2026-11-10T09:04:12-05:00",
  "inputs":  { "data_set/unified/catalog.sqlite": "sha256:…",
               "configs/pipeline.yaml#split": "sha256:…" },
  "outputs": [ "configs/splits/train.csv", "…" ],
  "metrics": { "train": 0, "val": 0, "test": 0, "gemstones_removed": 0 },
  "checks":  { "no_id_in_two_splits": true, "no_phash_group_spans": true }
}
```

`status` is one of `not_run | passed | failed` and describes whether the
stage *worked*. Results such as Stage 5's verdict live in `metrics`, so a
failed success criterion is still `status: passed`. `run_id` is minted
once per `run_pipeline.py` invocation and shared by every stage in that
run; the test-access log keys off it.

**Hand-off interfaces** (frozen at the Stage 1/2/3 handoff). These update
`src/common/interfaces.py`, whose current `TransformFn` has no `rng`
parameter and whose `GeneratorFn.sample` is renamed:

- `stage2_augment.transform(img: uint8[64,64], label: int, rng) -> uint8[64,64]`
- `stage3_synth.generate(label: int, rng) -> uint8[64,64]`
- Batch format: uint8 64×64 single channel, black outline on white;
  label = index from `configs/taxonomy.yaml`; normalized to [0, 1] in the
  loader. `Batch` keeps its `is_synthetic` mask so Stage 4 can log the
  realized mix per batch.
- Manifest schema (`configs/splits/{train,val,test}.csv`):
  `image_id, md5, label_id, source_id, phash_group, split`.

The `md5` column is new. The Phase 1 catalog stores no content hash — the
`Image` table is `(image_id, source_id, label_id, path, size, split)` —
so Stage 1 computes it and carries it forward. It is what makes
Decision 1's exclusion list stable and what lets any later stage prove it
read the image it thinks it read.

**Where pHash comes from.** Also not in the catalog. It lives in
`data_set/unified/metadata.csv`, which Stage 1 reads alongside the
catalog. Stage 1 recomputes grouping globally (Decision 15) rather than
reusing the Phase 1 `phash_group` values.

## Separation of concerns (enforced, not by convention)

1. **Import boundaries — `import-linter`**, run by the pre-commit hook
   and by `--check`:
   - *Independence contract:* `stage1_freeze`, `stage2_augment`,
     `stage3_synth`, `stage4_train`, `stage5_eval`, `stage6_report` do
     not import each other.
   - *Allowed exceptions:* `stage4_train` may import only
     `stage2_augment.transform` and `stage3_synth.generate`.
   - All stages may import `common`; `common` imports no stage.
   - `dashboard` may import `common.status` only.
   - `demo` may import `export` only (no `src.*`), which proves the
     exported bundle is self-contained.
   - The existing `sys.path` hacks and the private import of
     `_qd_loader` that `audit_dataset.py` takes from
     `build_unified_dataset.py` (`audit_dataset.py:21–22`) are removed by
     Stage 0; the loader becomes a public helper in `common`.
2. **Test-set guard.** The only way to read a split is
   `common.load_split(name)`. For `name == "test"` it raises unless the
   calling module is in `src.stage5_eval`, and every access appends one
   line to `artifacts/test_access.log`:
   `iso_timestamp, run_id, caller_module, split, n_rows`.
   - The log is **append-only and never truncated**. Checks are scoped to
     the current `run_id`, so reruns do not poison it.
   - Stage 4's Done-when: **no** line carries the current `run_id`.
   - Stage 5's Done-when: exactly `len(runs) + 2` lines carry the current
     `run_id` — one per trained seed model, plus Decision 14's two
     baselines. Ensembles reuse cached probabilities and add no reads.
   - Because `artifacts/` is gitignored, Stage 5 copies the per-run count
     into its `status.json → checks.test_reads` and Stage 6 prints it in
     the report's reproducibility note. That is what makes the guarantee
     visible to a reader who never saw the machine.
3. **Contract tests (`tests/contracts/`, pytest)** — every owner can run
   them without the other stages being finished:
   - `transform` returns 64×64 uint8, never changes the label, and
     applies no shear / non-uniform scale to circle, ellipse, square,
     rectangle, diamond.
   - `generate` returns 64×64 uint8 and respects the margins (ellipse and
     rectangle ratio ≥ 1.2, diamond angles clearly off 90°).
   - Manifests match the schema; no `image_id`, `md5` or `phash_group`
     appears in two splits.
   - Every `status.json` validates against the schema.
4. **Ownership.** `CODEOWNERS` maps `src/stageN_*/` to its stage owner
   (names from `team.json`), so changes to a stage need that owner's
   review. `src/common/`, `configs/pipeline.yaml` and `configs/splits/`
   need the Stage 0 owner plus one other.

## Stage 0 — Infrastructure

- **Owner:** ______
- **Depends on:** nothing (day 1, parallel with Stage 1)
- **Input:** the committed skeleton (`src/`, `configs/`,
  `run_pipeline.py`), Phase 1 `scripts/`, `build.ps1`, `team.json`.
- **Action:**
  - Fill in `src/common/`: `status.py` (schema, writer, `run_id`, hash
    cache), `splits.py` (`load_split` + the test guard and access log),
    `hashing.py` (file and config-subtree hashes). Replace the
    hard-coded constants in `batch.py` with config reads.
  - Update `src/common/interfaces.py` to the frozen signatures above
    (`transform` gains `rng`; `GeneratorFn.sample` becomes `generate`).
  - Move the Phase 1 scripts into `src/stage1_freeze/` (`standardize`,
    `taxonomy`, the build and FD scripts) and shared helpers (`md5`,
    `phash`, `_qd_loader`, catalog access) into `src/common/`. Remove the
    `sys.path` hacks and the private cross-script import.
  - Extend `run_pipeline.py` with `--check`, `--dashboard`, `--demo`,
    `--force` and the hash-cache skip.
  - Write the guards: import-linter config, pre-commit hook, contract
    test skeletons, `CODEOWNERS`.
  - Ship **placeholder LaTeX tables** from the Stage 5 stub
    (`artifacts/stage5/tables/*.tex` containing a dash). `build.ps1` runs
    with `-halt-on-error`, so without them the report cannot compile
    until Stage 5 finishes — and Stage 6's figure work is supposed to
    start on day 1.
  - Environment: pin the Python version (`.python-version`), write
    `requirements.txt` with exact versions (Pillow, NumPy, SciPy,
    Matplotlib, Albumentations, PyTorch, scikit-learn, scikit-image,
    statsmodels, PyYAML, Streamlit, import-linter, pytest, pre-commit).
  - Set up the shared data folder (Decision 5), publish the raw archive's
    SHA-256, and verify a second machine gets the same hash.
  - **Prove migration equivalence:** before moving code, record the
    catalog hash, row and class counts, and the per-(source,label) pHash
    groups. After the move, rerun the build and require all of them to
    match. Save the comparison in
    `artifacts/stage0/migration_check.json`. This checks only that
    *moving the code* changed nothing — Decision 15's deliberate change
    to grouping scope happens in Stage 1 and is expected to move the
    numbers.
  - Write `README.md`: prerequisites, environment setup, data pull, every
    `run_pipeline.py` mode, owner/artifact map, Windows troubleshooting
    (execution policy, Python on PATH).
- **Output:** a skeleton that runs end-to-end with stub stages; each stub
  writes a `status.json` with `status: not_run`; migration report;
  `artifacts/stage0/status.json`.
- **Done when:** on a clean clone, the README gets a new teammate from
  setup to seven stub status files and a compiling report; a second run
  skips every stage; the migration comparison shows no data change; a
  deliberate forbidden import and a fake test-set read are both blocked.
- **Effort:** ~0.5 day. Adopting the committed layout removed the rename
  and the DVC setup, so this owner takes a full share of another stage.

## Stage 1 — Data freeze and splits

- **Owner:** ______
- **Depends on:** nothing (starts day 1; develops against the Stage 0
  skeleton)
- **Input:** `data_set/unified/catalog.sqlite` (identity, labels,
  sources) **and** `data_set/unified/metadata.csv` (pHash and the
  standardization fields — the catalog has neither pHash nor md5);
  `configs/gemstone_ids.csv`; `configs/pipeline.yaml`.
- **Action:**
  - Compute `md5` for every image from its standardized PNG and carry it
    into the manifests. This is the stable identity every later stage and
    every exclusion list keys on.
  - Apply Decision 1: match `configs/gemstone_ids.csv` on `md5`, fail the
    stage if any row matches zero or more than one image, and record
    `gemstones_removed`.
  - Recompute pHash near-duplicate groups **globally across all
    sources** (Decision 15), not per (source, label).
  - 70/15/15 split by near-duplicate group, stratified by class and
    source where possible. Ratios come from `configs/pipeline.yaml`.
    **Expect the counts to move** off 12,761 / 2,890 / 2,849 — both the
    filter and the new grouping scope change them. Publish the new
    numbers; Stage 6 updates the report.
  - Build assertions: no `image_id` or `md5` in two splits, no pHash
    group spanning splits. Fail the stage (`status: failed`) if either
    fires, and write no manifests.
  - Recompute the per-class test counts and noise bands for Decision 10
    into `split_stats.csv`.
  - Run the FD check on the **filtered** data. `check_fds.py` reads
    `data_set/unified/metadata.csv` (`check_fds.py:15`), not the catalog,
    so Stage 1 regenerates that file after filtering or points the check
    at its own filtered frame — doing neither checks the wrong rows.
  - Sanity check: train a quick source classifier on classes with two or
    more sources, using train and validation data only. Apply
    Decision 12's trigger and record `shortcut_detected`. If it fires,
    notify Stages 4–6: per-source tables and leave-one-source-out
    evaluation become required, and pentagon/ellipse results keep their
    asterisk.
- **Output:** `configs/splits/{train,val,test}.csv` (committed —
  Decision 16); `artifacts/stage1/`: `split_stats.csv` (per class ×
  source × split, plus the noise-band table), `source_classifier.json`,
  `status.json`.
- **Done when:** leakage assertions pass, the removed diamonds match
  `configs/gemstone_ids.csv` exactly, the new counts are published with a
  note for Stage 6, the catalog hash and seed are recorded, and the
  manifest contract tests pass. The test split is locked from this
  point — touched only by Stage 5.

## Stage 2 — Augmentation pipeline

- **Owner:** ______
- **Depends on:** the format spec for day-1 development; Stage 1's train
  manifest for final QA. Independent of Stage 3 — run in parallel.
- **Input:** train split manifest; `configs/pipeline.yaml#augment`;
  `configs/taxonomy.yaml`.
- **Action:**
  - Albumentations pipeline: rotation, scale, shear, noise, blur.
  - Enforce class-safe rules: shear and non-uniform scaling disabled for
    circle, ellipse, square, rectangle and diamond — read from
    `configs/taxonomy.yaml#no_shear_no_nonuniform_scale`, not hard-coded.
  - Visual QA: dump 10 augmented samples per class, check for
    label-changing artifacts (stretched square → rectangle, near-round
    ellipse → circle).
- **Output:** `stage2_augment.transform` (the one function the Stage 4
  loader calls on the fly); `artifacts/stage2/`: QA sheet, `status.json`.
- **Done when:** zero label-changing artifacts in the QA sheet, the
  per-class disabled-transform rules are enforced by config rather than
  by convention, and the `transform` contract tests pass.

## Stage 3 — Synthetic generator

- **Owner:** ______
- **Depends on:** the format spec only (independent of Stage 2 — run in
  parallel)
- **Input:** `configs/taxonomy.yaml` (classes and ambiguity margins), the
  standardized format spec (64×64, black outline on white);
  `configs/pipeline.yaml#synth`.
- **Action:**
  - Pillow `ImageDraw` renderer with randomized parameters, matching the
    standardized outline format. Rendered on the fly, never stored.
  - Explicit ambiguity margins: ellipse axis ratio ≥ 1.2, rectangle side
    ratio ≥ 1.2, diamond angles at least 10° off 90°.
  - Log the actual parameter ranges used so Stage 6 can state them.
  - Visual QA: 10 rendered samples per class, same artifact check as
    Stage 2.
  - Measure throughput against an **absolute** target: **≥ 2,000
    images/s single-threaded** on the training machine. At batch 256 and
    a 30% share that is 77 images in under 40 ms, comfortably inside one
    CPU training step. Stage 4's D3 loader benchmark re-checks this
    against the real step time, but Stage 3 does not wait for it.
- **Output:** `stage3_synth.generate`; `artifacts/stage3/`:
  `param_ranges.json`, QA sheet, throughput measurement, `status.json`.
- **Done when:** QA passes, margins are enforced and covered by contract
  tests, and measured throughput meets the absolute target.

## Stage 4 — Training (baselines + A0 / A1 / B)

- **Owner:** ______
- **Depends on:** Stage 1; Stage 2 and 3 for arms A1 and B (loader,
  baselines and A0 can start earlier)
- **Input:** train/val manifests (Stage 1), `transform` (Stage 2),
  `generate` (Stage 3), `configs/pipeline.yaml#runs`, `#train`,
  `#evaluation`.
- **Action:**
  - On-demand data loader querying the SQLite catalog per batch, through
    `common` (never reading the test manifest). Each Windows worker opens
    its own read-only connection.
  - Benchmark at least 100 batches with the intended worker settings
    before the sweep; record batches/s, images/s and the estimated time
    for one run and for all 23 (Decision 6). If loading is the
    bottleneck, optimize the loader without changing the data recipe.
  - Apply Decision 11: class-balanced real sampling and an evenly
    class-balanced synthetic share, identical across arms. Log the
    realized per-batch mix from `Batch.is_synthetic`.
  - Freeze `steps_per_epoch` from arm A0 per Decision 13 and use the same
    value for every arm.
  - Baselines first (Decision 14): logistic regression on raw pixels and
    a linear SVM on HOG features, trained on the same stream as A0 and
    selected on validation. They calibrate what "easy" looks like.
  - Run Decision 7's tuning grid on A1 validation only, freeze the
    selected settings, then train the CNN from Decision 8. Identical
    architecture, optimizer, step budget, schedule and seed set for all
    arms; only the data stream differs:
    - **A0:** real only (the report's "Model A")
    - **A1:** real + augmentation
    - **B:** 70% real + 30% synthetic, with augmentation (the report's
      "Model B")
  - 3–5 seeds per arm, same seed set across arms so paired tests stay
    valid. The validation split is used for early stopping and the one
    tuning pass only; selected epochs are recorded.
  - Measure validation prediction disagreement between seeds of the same
    arm, as a robustness number for the report. (It is **not** the power
    check — Decision 10 moved that to Stage 5.)
  - If Decision 12 fires, add the required Hand-Drawn leave-one-source-out
    training for A1 and B using the same frozen settings.
- **Output:** `artifacts/stage4/<arm>_<seed>/`: trained model, training
  log, validation curve, validation predictions **and softmax
  probabilities** (Stage 5 needs the probabilities for the power check);
  `artifacts/stage4/`: `baselines.json`, `tuning.json`,
  `loader_benchmark.json`, `seed_disagreement.json`, `status.json`
  summarizing all runs.
- **Done when:** every required arm × seed and both baselines are
  trained, validation-based model selection is recorded, the loader
  benchmark exists, and no line in `artifacts/test_access.log` carries
  this run's `run_id`.

## Stage 5 — Evaluation and statistics

- **Owner:** ______
- **Depends on:** Stage 4
- **Input:** trained models and baselines (Stage 4), locked test split
  (Stage 1), `artifacts/stage1/split_stats.csv` for the noise bands. The
  only stage whose caller `load_split("test")` permits.
- **Action:**
  - **Before any test prediction**, run Decision 10's power check: the
    paired bootstrap on A1's and B's *validation* probabilities, rescaled
    by `sqrt(n_val / n_test)`. Record the expected half-width. Do not
    change the criterion after seeing results.
  - Evaluate each seed model and each baseline **once** on test and cache
    predictions and softmax probabilities. Form each arm's soft-vote
    ensemble from the cached probabilities, without rereading test
    images.
  - Metrics per model, per arm ensemble and per baseline: accuracy,
    macro-F1, per-class F1, confusion matrices (key pairs: square/
    diamond, square/rectangle, circle/ellipse), accuracy per source and
    per domain (render vs sketch).
  - Primary comparison: B vs A1 macro-F1 on ensemble predictions, with a
    paired bootstrap 95% CI. McNemar's test on paired correctness is the
    supporting accuracy comparison (Decision 9).
  - Secondary comparisons: A0 vs A1 (augmentation effect) and A0 vs B
    (the report's original question). Apply Holm correction to the two
    McNemar p-values; report macro-F1 CIs alongside them.
  - Report per-seed mean ± std and paired per-seed differences as a
    robustness check; do not pool duplicate test predictions.
  - Apply the locked criterion (Decision 10): B passes if ensemble
    macro-F1 improves by ≥ 1 point with a CI excluding 0, **and no class
    has both** an F1 drop above its own threshold
    (`max(2.0, noise band)`, read from `split_stats.csv`) and a paired
    bootstrap CI for that drop excluding 0.
    Secondary: does A1 beat A0? If augmentation alone closes most of the
    gap, the report must say the generator adds little.
  - Build the **error galleries** — misclassified test images for the
    three key confusion pairs. Stage 6 may not read test images, so
    Stage 5 renders them.
  - If Decision 12 fired, evaluate the required leave-one-source-out
    models on Hand-Drawn only and label that result as unseen-source
    generalization, separate from the primary same-source test.
- **Output:** `artifacts/stage5/`: `predictions/`, `tables/` (CSV +
  LaTeX, replacing Stage 0's placeholders), `figures/`
  (`confusion_<arm>.png`, `errors_<pair>.png`), `power_check.json`,
  `status.json` with the verdict in `metrics.verdict` (`pass` / `fail`)
  and the test-read count in `checks.test_reads`.
- **Done when:** the verdict is delivered with CIs and the stated power
  limitation, and `artifacts/test_access.log` carries exactly
  `len(runs) + 2` lines for this `run_id`. If the verdict fails, the
  CRISP-DM loop goes back to Business Understanding — likely fixes are
  the synthetic ratio, the generator or the label rules.

## Stage 6 — Report, figures, dashboard and packaging

- **Owner:** ______
- **Depends on:** Stage 5 for results; figure, report-fix and dashboard
  work can start day 1
- **Input:** artifacts from all stages.
- **Action:**
  - Build the dashboard (below) early; it doubles as the team's progress
    board.
  - Reconcile the report with this plan:
    - Figure 2 (`fig:evalsplit`): add the validation split, dedup stage,
      seed annotations and the A1 arm (TikZ below). **Move it out of its
      0.32\linewidth minipage** — see the note under the figure.
    - Evaluation goal paragraph (section A): describe three arms.
    - **Split paragraph** (`phase1_report.tex:466–467`): the new counts
      from Stage 1. This is where the split sizes live — `tab:stats`
      (Table 3) holds per-source file counts, not split counts.
    - Gemstone wording in sections C and D and the label-mapping table:
      state the filter and the removed count.
    - Fix typos in `phase1_report.tex`: "clasifies", "geometrc",
      "categoreis", "dosent" (×2), "chnage", "dont" (×2),
      "training..", "later..", and the stray spaces before periods at
      lines 81, 86, 237, 275, 302, 337, 473, 503.
  - Results tables, confusion matrices and error galleries — read from
    `artifacts/stage5/`, never retyped.
  - State Decision 13's equal-compute framing in the results section: B's
    gain or loss is measured against A1 at the same step budget, with 30%
    of each batch substituted rather than added.
  - Limitations: reevald's dashed-line hint, gemstone diamonds (and what
    the filter removed), near-duplicate pentagon groups, single-source
    classes (pentagon, ellipse) with the Stage 1 source-classifier
    caveat, and the equal-compute framing above.
  - Ablations if time allows: `B_equalreal` (Decision 13), synthetic
    ratio 0/15/30/50% (the 0% point is A1, already free), per-augmentation
    removal, sketch-only test slice. Each ablation is a new entry in
    `configs/pipeline.yaml#runs`, so the pipeline runs it with no code
    change.
  - Export the best model (ONNX) with `standardize.py`, `predict.py` and
    `labels.json` bundled in `export/`.
  - Complete the course-requirements checklist and add source/license
    attribution to the report and `export/README.md`. Label the primary
    result as same-source generalization; include the required
    leave-one-source-out result if Decision 12 fired.
  - Build the "draw and infer" deployment demo (below) and update the
    report's CRISP-DM figure (`fig:crisp`): Deployment is no longer "not
    in this report".
- **Output:** Phase 2 report, `export/` with README and notices,
  `demo/app.py`, `dashboard/app.py`, completed rubric checklist,
  `artifacts/stage6/status.json`.
- **Done when:** the report compiles through the pipeline, every number
  in it traces back to a Stage 1/3/5 artifact, no rubric item is silently
  unmet, attribution is present, the export loads and predicts on a fresh
  image, `--demo` turns a mouse drawing into a prediction using only
  `export/`, and the dashboard shows all seven stages.

## Dashboard (owned by Stage 6)

A read-only **Streamlit** app (`dashboard/app.py`, opened with
`python run_pipeline.py --dashboard`). It only reads `artifacts/` and
`configs/`; it never computes results, never trains, and never reads the
test split. Missing artifacts show as grey "not run", so it is useful
from day 1.

| Tab | Shows |
|---|---|
| Overview | 7 status lights (grey not run / green passed / red failed), owner, last run time, input hashes |
| 0 Infra | migration check, environment pins, guard results |
| 1 Data | split counts, leakage checks, gemstones removed, per-class noise bands, source-classifier result |
| 2 Augment | QA image sheet, per-class disable rules from `configs/taxonomy.yaml` |
| 3 Synthetic | QA image sheet, parameter-range log, throughput vs the 2,000 img/s target |
| 4 Training | validation curves per arm × seed, baseline scores, loader benchmark, test-access log (must be clean for this run) |
| 5 Evaluation | confusion matrices, error galleries, three paired comparisons, CIs, power check, verdict |
| 6 Report | PDF link, number-traceability check, export smoke test |

Eight tabs, seven lights — Stage 0 writes a `status.json` like every
other stage, so it gets a light and a tab. MLflow is an optional add-on
for browsing Stage 4 runs; it is not required.

## Deployment demo — "draw and infer" (CRISP-DM step 6, owned by Stage 6)

The Phase 1 report leaves Deployment as "not in this report". Phase 2
closes that step with a tiny interactive demo. A user draws a shape in a
small canvas, presses **Infer**, and sees the model's prediction.

**Usage story.** "As a visitor, I sketch a shape with the mouse, press
Infer, and within a second I see the predicted class, the model's top-3
confidences, and the 64×64 image the model actually saw."

**How it works**

```
 canvas 256×256 (black stroke, ~8 px, white bg)
        │  Infer
        ▼
 export/predict.py ── standardize.py  (same Phase 1 cleaning: crop,
        │                               pad to square, 64×64 outline)
        ▼
 export/model.onnx  ──►  softmax  ──►  top-3 classes + bars
                                        + the 64×64 preprocessed image
```

- **Separate app:** `demo/app.py`, started with `--demo`. It is kept
  apart from the dashboard because it imports only the `export/` folder
  (`predict.py`, `standardize.py`, `model.onnx`, `labels.json`). If the
  demo runs from `export/` alone, so can anyone else.
- **UI:** Streamlit + `streamlit-drawable-canvas`, with a Draw canvas, an
  **Infer** button and a **Clear** button. Fallback if the canvas
  component misbehaves with the pinned Streamlit version: Gradio's
  `Sketchpad` with the same `predict()` call.
- **Stroke width:** about 8 px on a 256 px canvas becomes about 2 px
  after the 4× downscale to 64×64, which matches the standardized 2-px
  outline.
- **Same preprocessing as training:** the drawing goes through
  `standardize.py`, never a separate resize. Showing the 64×64 image
  makes any mismatch visible. `standardize._flatten_alpha` already
  composites RGBA onto white, so the canvas output needs no conversion
  first.

**Edge cases**
- Empty canvas → show "Draw a shape first" and do not call the model.
  **Test the alpha channel** (`rgba[..., 3].sum() == 0`), not the RGB
  values: the canvas returns unpainted pixels as `(0, 0, 0, 0)`, so an
  RGB-darkness test reads a blank canvas as solid ink and never fires.
- `standardize()` raises `Rejected` on an image with no contrast (a
  single dot, a stray mark) → catch it and show the same "Draw a shape
  first" message rather than a traceback.
- Confidence of the top class below 0.5 → show the prediction as "not
  sure" with the top-3 list.
- Open or unclosed strokes → standardize keeps open strokes as they are
  (Phase 1 rule), so the model sees what the user drew.
- `export/model.onnx` missing → the app starts and says "no exported
  model yet — run the pipeline".

**Evaluation boundary.** Drawings made in the demo are informal evidence
only. They are not test data, they never feed back into training, and
they do not change the Stage 5 verdict. A small "live sketch check" can
go in the report as an anecdote: each team member draws each of the 10
classes once, and the report states how many of these 60 drawings were
classified correctly.

## Failure behaviour

- A stage fails → the pipeline stops, later stages do not run, its status
  is `failed`, and the dashboard shows a red light on that stage.
- `configs/pipeline.yaml` changes → only the stages whose recorded input
  hashes no longer match rerun.
- `filter_gemstones` changes → Stage 1 and everything downstream rerun;
  this is why it is frozen after Decision 1.
- Stage 5 verdict "fail" → the stage still `passed`; the dashboard shows
  the stage status and the verdict separately.
- Test split read outside Stage 5 → `load_split` raises; if bypassed, the
  access log carries a line with this `run_id` and Stage 4's Done-when
  fails.
- A split manifest changes → it is a committed file, so the change shows
  up as a PR diff that every owner reviews (Decision 16).

## Timeline sketch

| Stage | Output | Rough effort | Runs |
|---|---|---|---|
| 0 Infrastructure | common helpers, guards, env, README | 0.5 day | day 1, parallel with 1 |
| 1 Data freeze | Locked splits, leakage asserts, noise bands | 1 day | first |
| 2 Augmentation | Aug module + QA | 1 day | starts day 1; final QA after 1, parallel with 3 |
| 3 Synthetic | Generator + QA | 1.5 days | starts day 1, parallel with 2 |
| 4 Training | Baselines, A0/A1/B, multi-seed | 2.5–3 days | starts with 1, completes after 2+3 |
| 5 Evaluation | Metrics, tests, verdict, galleries | 1–1.5 days | after 4 |
| 6 Report | Report fixes, phase report, export | 1–2 days | figures early, tables after 5 |
| 6 Dashboard | Streamlit viewer | 0.5–1 day | day 1–2, by Stage 6 owner |
| 6 Demo | Draw-and-infer app on `export/` | 0.5 day | UI early with a stub model; real model after 5 |

Stage 0 shifts no dependency: every stage develops against the stub
skeleton from day 1 and replaces its stub when ready. Stage 1 grew to a
full day because of the md5 pass and the global pHash regrouping; Stage 0
shrank by the same amount because it no longer renames packages or sets
up DVC.

Coordination points: freeze the hand-off interfaces (*Shared
conventions*) at the Stage 1/2/3 handoff so Stages 2, 3 and 4 never block
each other on details. All shared numbers live in
`configs/pipeline.yaml`.

## Team workflow and hand-off

- **Branches:** one short-lived branch per stage/task, for example
  `stage/s2-augment`. No direct commits to `main`.
- **Reviews:** every change goes through a pull request. The stage owner
  reviews its folder; changes to `src/common/`, `configs/` or an
  interface also need the Stage 0 owner and the affected consumer.
  CODEOWNERS encodes this once owners are assigned.
- **Main stays runnable:** required pre-commit/CI checks are
  import-linter, contract tests, schema validation and a no-test-access
  check. A PR is not merged with a failing guard.
- **Daily integration:** merge completed, reviewed increments rather than
  stockpiling six long-lived branches. Use `--check` before requesting
  review and `--stages N` before hand-off.
- **Hand-off definition:** a stage is handed off only when its PR is
  merged, its Done-when checklist is complete, its artifacts and
  `status.json` exist, and the consuming owner has reproduced the stage
  once from the README. A verbal "done" is not a hand-off.
- **Shared-file ownership:** only Stage 0 changes interfaces or shared
  config semantics, with the affected owners reviewing. Stage owners do
  not edit each other's folders to make their own stage pass.
- **Conflict rule:** artifacts are regenerated, not manually merged;
  source and config conflicts are resolved in review. A conflict in
  `configs/splits/` is never resolved by hand — rerun Stage 1.

## Calendar (relative dates)

`D0` is the first project workday. Replace it with a real date and work
backwards once the Phase 2 deadline is supplied. `D` values are working
days, not calendar dates.

| Day | Team checkpoint | Required exit |
|---|---|---|
| D0 | Kickoff; assign owners; obtain rubric/deadline; lock Decisions 1–16 | Owner map and submission requirements recorded |
| D1 | Stage 0 skeleton; gemstone double review; Stage 1; Stage 2/3/6 start | Clean-clone run works; gemstone md5 list committed |
| D2 | Data freeze hand-off; interface freeze; dashboard skeleton | Stage 1 green; splits committed; new counts published |
| D3 | Stage 2/3 QA; Stage 4 loader benchmark, baselines and A0 | Contract tests pass; 23-run time estimate |
| D4–D5 | A1 tuning pass, frozen settings, all-arm seed sweep | Stage 4 green; clean access log; probabilities cached |
| D6 | Stage 5 power check, evaluation and verdict | One cached prediction set per model; verdict + CIs |
| D7–D8 | Report integration, export, demo, attribution and rubric audit | Every number traceable; demo and export smoke tests pass |
| D9 | Full clean-clone rehearsal and submission-package freeze | All checks green on a second machine |
| D10 | Reserve for a failed-verdict CRISP-DM loop or integration fixes | Scope changes re-reviewed; no silent criterion edits |

If the actual deadline leaves fewer than 11 working days, reduce seeds to
3, defer optional ablations, and cut optional dashboard polish — not the
leakage guard, frozen test protocol or statistical checks.

## Course requirements checklist (rubric needed)

The official Phase 2 rubric and page/format limits are not in the
repository. Stage 6 owns this checklist, and the team fills it from the
official document before D1:

- [ ] **Deadline and submission channel:** ______
- [ ] **Required sections and page/file limits:** ______
- [ ] **Required model families or baselines:** ______ (do not assume the
      CNN + two baselines is sufficient until checked)
- [ ] **Required validation/statistical methods:** ______
- [ ] **Required data/FD/CRISP-DM evidence carried from Phase 1:** ______
- [ ] **Required demo, export, reproducibility or individual-contribution
      evidence:** ______
- [ ] **Citation and file-naming rules:** ______

Any rubric requirement that conflicts with this plan becomes a reviewed
change to Decisions 1–16. The plan must not quietly drop a course
requirement to preserve its current scope.

## Attribution and redistribution

The Phase 2 report and `export/README.md` must identify the training
sources and their licenses: Quick, Draw! (CC BY 4.0), reevald Geometric
Shapes Mathematics (CC0), El Korchi 2D geometric shapes (CC BY 4.0), and
Hand-Drawn Shapes (CC BY 4.0 for data; MIT for its code). Include the
source names, creators, links and license links already in the Phase 1
bibliography, plus a summary of the standardization, filtering and
splitting applied.

State whether the submission redistributes images, derived outlines,
model weights or only code. Do not assume a license for the team's own
code or model; choosing one is a team decision. The demo displays a short
"Data and model credits" link to the same notice.

## Workload balance (why tasks sit where they do)

- **Stage 0 is now ~0.5 day**, so its owner takes a full share of another
  stage. The natural pairing is Stage 1: the Phase 1 scripts being moved
  are Stage 1's code, and Stage 1 grew when the md5 pass and global
  regrouping landed.
- The **source-classifier sanity check** lives in Stage 1, not Stage 5,
  because it is a property of the frozen data, not of any trained model.
  If source is predictable from standardized pixels, every later stage
  needs to know on day one.
- **The power check moved from Stage 4 to Stage 5** because it is a
  bootstrap over validation predictions — the same computation Stage 5
  runs on test, on data Stage 5 is already handling. Stage 4 keeps the
  seed-disagreement measurement, which is a different and separately
  reportable number.
- **Error galleries moved from Stage 6 to Stage 5** because they need
  test images, which only Stage 5 may read.
- **Stage 4 has the heaviest load** (~3 days: loader, baselines, three
  arms × seeds), so nothing optional was added to it.
- **The dashboard sits in Stage 6** because Stage 6's figure work starts
  on day 1 and the dashboard reuses the same artifacts and figures.
- **Ablations sit in Stage 6 marked "if time allows"** because they only
  affect the report, not the verdict. If Stage 5 finishes early, its
  owner can take them — moving them changes no interfaces.
- Stages 2 and 3 are deliberately similar in shape (module + QA sheet) so
  either owner can review the other's work.

## Risks and assumptions

- **CPU-only training** may stretch Stage 4. Mitigation: start A0 early,
  use 3 seeds first and add seeds 4–5 only if time allows. The D3
  benchmark turns Decision 6's 23 runs into a number before the sweep
  commits the team to it.
- **The new split invalidates a reported number.** Decision 15 guarantees
  the report's Split paragraph is wrong until Stage 6 updates it. Track
  it as a Stage 6 task, not a surprise.
- **Windows pre-commit hooks** need Python on PATH; Stage 0 documents the
  setup in the README.
- **Shared-folder data drift.** The archive hash is the only thing
  standing between a teammate and a silently different dataset. Stage 0
  verifies it on a second machine; Stage 1 records the catalog hash in
  `status.json` so a drift shows up as a changed input hash rather than
  as a mysterious result.
- **Owners** are still blank; assign them from `team.json` before day 1.

## LaTeX-ready extension of Figure 2 (Stage 6 deliverable)

The current figure is missing the validation split, the dedup/split stage
and the A1 arm. Paste these nodes into the existing `fig:evalsplit`
`tikzpicture` in `phase1_report.tex`, replacing its node and arrow lines;
the `box` and `arr` styles are defined in that picture's options and are
not repeated here.

```latex
\node[box]   (pool)  at (4.5,10.8) {Real data pool\\(all installed sources)};
\node[box]   (dedup) at (4.5,9.3)  {Dedup + split by\\pHash group, 70/15/15};
\node[box]   (train) at (0.9,7.6)  {Train split\\(real images)};
\node[box]   (val)   at (4.5,7.6)  {Validation split\\(tuning + early stopping)};
\node[box]   (test)  at (8.1,7.6)  {Test split\\(real images,\\held out)};
\node[box]   (modelA0) at (0.6,5.2) {Model A0:\\real only\\(3--5 seeds)};
\node[box]   (modelA1) at (4.3,5.2) {Model A1:\\real + aug\\(3--5 seeds)};
\node[box, fill=gray!20] (augbox) at (4.3,3.5) {+ Synthetic data};
\node[box]   (modelB) at (4.3,1.9) {Model B:\\real + aug\\+ synthetic\\(3--5 seeds)};
\node[box, fill=gray!20, text width=3.4cm] (compare) at (7.2,0.0)
  {Compare on the same\\held-out real test set};

\draw[arr] (pool)  -- (dedup);
\draw[arr] (dedup) -| (train);
\draw[arr] (dedup) -- (val);
\draw[arr] (dedup) -| (test);
\draw[arr] (train) -- (modelA0);
\draw[arr] (train) -- (modelA1);
\draw[arr] (modelA1) -- (augbox);
\draw[arr] (augbox)  -- (modelB);

% Routing to the comparison node (all three models + test split)
\draw[arr] (modelA0.south) -- (0.6,0.8) -- (7.2,0.8) -- (compare.north);
\draw[arr] (modelA1.east)  -- (6.3,5.2) -- (6.3,0.8) -- (7.2,0.8) -- (compare.north);
\draw[arr] (modelB.south)  -- (4.3,0.8) -- (7.2,0.8) -- (compare.north);
\draw[arr] (test.south)    -- (8.1,0.8) -- (7.2,0.8) -- (compare.north);
```

Coordinates are chosen so no two boxes touch at `\footnotesize` with the
picture's `text width=3.0cm` and `inner sep=5pt`: the tightest vertical
gap is 0.39 cm (augbox → Model B) and the tightest horizontal gap is
0.24 cm (train → validation, and validation → test). The A1 arrow runs
down x = 6.3, centred in the corridor between the validation and test
boxes. Check the compiled output anyway — the A1 → augmentation step
means "same training stream plus synthetic", not that B is fine-tuned
from A1.

**The figure needs a wider home.** It currently sits in a
`0.32\linewidth` minipage under `\resizebox{\linewidth}{!}`. The extended
picture is about 10.9 × 11.8 cm, so that minipage scales it to roughly
half size and the `\footnotesize` labels land near 4 pt — unreadable in
print. Give it at least `0.60\linewidth`, or move it to its own
full-width figure and let the Phase 1 neighbours keep the row.
