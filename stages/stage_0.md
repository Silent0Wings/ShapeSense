# Stage 0 — Infrastructure and reproducibility

> **Current state (2026-11-09).** Three sets are now sealed: the test split, the first fresh holdout
> and fresh holdout 2. A full pipeline run needs iteration 3's frozen search
> winners, so it fails until they exist. `--check` is unaffected.
> The rest of this brief is the original design. The record of what changed is
> [`docs/crisp_dm/README.md`](../docs/crisp_dm/README.md).

> Owner brief. Everything here is about Stage 0 only. The full project
> plan is `../implementation.md`; the issue review is `../plan_issues.md`.

- **Owner:** ______ (Stage 0 is ~0.5 day; this owner takes a full share
  of another stage — Stage 1 is the natural pairing)
- **Code folders:** `src/common/`, `run_pipeline.py`, `tests/contracts/`
- **Depends on:** nothing — day 1, parallel with Stage 1
- **Blocks:** no development work; every stage starts against stub contracts
- **Effort:** ~0.5 day

## Focus

Give all six later stages **one runnable, reproducible skeleton** with
shared configuration, artifact contracts, import boundaries, test-set
guards, environment setup and data sharing. Stage 0 supplies the rails;
it does not implement the experiment.

**The skeleton already exists.** `src/stageN_*/`, `src/common/`,
`configs/pipeline.yaml`, `configs/taxonomy.yaml`, `artifacts/stageN/`
and `run_pipeline.py` are committed. Stage 0 fills in what is missing
and moves the Phase 1 scripts in. It renames nothing — the plan adopted
these names in v4 precisely so that this stage stays small.

## Goals

1. Make the pipeline work end-to-end with stub stages on a clean clone.
2. Move the Phase 1 scripts into `src/stage1_freeze/` and `src/common/`
   **without changing their output**.
3. Make `configs/pipeline.yaml` the only source of shared experimental
   settings, and `configs/taxonomy.yaml` the only source of class
   definitions.
4. Make boundary violations and test-set misuse fail automatically.
5. Let a new teammate install, pull data, run checks and open the
   dashboard from one README.

## Out of scope

- Splitting data, augmentation, generation, training or evaluation.
- Choosing experimental results or changing Phase 1 standardization.
- Building dashboard/demo features (Stage 6 owns those applications).

## Inputs

| Input | Where |
|---|---|
| Existing Phase 1 scripts | `scripts/` |
| Report build command | `build.ps1` |
| Team names | `team.json` |
| Raw/local data | `data_set/` (gitignored) |
| Committed skeleton | `src/`, `configs/`, `run_pipeline.py` |
| Pipeline and interface decisions | `implementation.md` Decisions 4–6, 13–16 |

## Requirements

**Must**
- R1. Add the folders that do not exist yet: `artifacts/stage0/`,
  `tests/contracts/`, `dashboard/`, `demo/`, `export/`. Do **not**
  rename anything that is already committed.
- R2. Before moving any script, record the existing catalog hash, row
  count, class counts and per-(source,label) pHash groups. After the
  move, rerun the build and reproduce all of them exactly; any
  difference fails Stage 0 rather than becoming a silent data change.
  This proves *the move* changed nothing. Decision 15's deliberate
  change to pHash grouping scope happens in Stage 1 and is expected to
  move the numbers — do not confuse the two.
- R3. Remove `sys.path` hacks and private cross-script imports such as
  `audit_dataset.py → build_unified_dataset._qd_loader`
  (`audit_dataset.py:21–22`); `_qd_loader` becomes a public helper in
  `common`.
- R4. Implement config loading with validation and clear errors, for
  both files: `configs/pipeline.yaml` (seed set, split, arms,
  augmentation ranges, synthetic ratio, step budget, training defaults,
  tuning grid, evaluation criterion) and `configs/taxonomy.yaml`
  (classes, ambiguity margins, label-safety rules).
- R5. Replace the hard-coded constants in `src/common/batch.py`
  (`IMAGE_SIZE`, `IMAGE_CHANNELS`, `SYNTHETIC_FRACTION = 0.3`) with
  config reads. Two sources of truth for the synthetic ratio is exactly
  the failure mode the plan forbids.
- R6. Update `src/common/interfaces.py` to the frozen hand-off
  signatures: `TransformFn` gains the `rng` parameter it currently
  lacks, and `GeneratorFn.sample` becomes `generate(label, rng)`.
  Stages 2 and 3 cannot meet their reproducibility requirement without
  this.
- R7. Extend `run_pipeline.py` with `--check`, `--dashboard`, `--demo`,
  `--force`, and the hash-cache skip. Guards run before any stage.
- R8. Implement `common.status` (schema, writer, one `run_id` per
  invocation, input-hash cache) and `common.load_split` (test guard plus
  the append-only `artifacts/test_access.log`, one line per read:
  `iso_timestamp, run_id, caller_module, split, n_rows`). The log is
  never truncated; callers check only lines carrying the current
  `run_id`.
- R9. Add import-linter, pytest contract-test skeletons, pre-commit and
  CODEOWNERS configuration.
- R10. Ship placeholder LaTeX tables from the Stage 5 stub
  (`artifacts/stage5/tables/*.tex`, each containing a dash). `build.ps1`
  runs with `-halt-on-error`, so without them the report cannot compile
  until Stage 5 finishes — and Stage 6 starts its figure work on day 1.
- R11. Pin Python and dependency versions; document CPU-only and GPU
  setup if both are supported.
- R12. Publish the raw archive plus its SHA-256 in the shared folder and
  verify that a second machine retrieves the same hash.
- R13. Write `README.md`: prerequisites, environment creation, data
  pull, all run commands, owner map, artifact layout and troubleshooting.
- R14. `artifacts/`, model checkpoints and `data_set/` stay out of Git.
  The split manifests in `configs/splits/` are the deliberate exception
  (Decision 16) — they are committed.

**Should**
- Provide stub stage entry points that write `not_run` status files.
- Keep the contracts compatible with DVC in case the team adopts it
  later; nothing in this stage should depend on it.
- Document Windows execution-policy and Python-on-PATH fixes.

## Deliverables

- Completed skeleton and migrated public modules.
- Validated `configs/pipeline.yaml` and `configs/taxonomy.yaml`; extended
  `run_pipeline.py`.
- `common.status`, `common.load_split`, `common.hashing`; updated
  `interfaces.py` and `batch.py`.
- Placeholder Stage 5 LaTeX tables so the report compiles on day 1.
- Pinned environment, shared-folder data setup and `README.md`.
- Migration-equivalence report in `artifacts/stage0/`.
- `artifacts/stage0/status.json`.

## Done when

- [ ] A clean clone follows the README and reaches seven stub status
      files **and a compiling report PDF**.
- [ ] A second run skips every unchanged stage.
- [ ] Catalog hash, counts and pHash groups match the pre-move record.
- [ ] A deliberate cross-stage import and a fake test-set read are blocked.
- [ ] A second machine retrieves raw data with an identical SHA-256.
- [ ] All owners can run their contract tests without other stages
      implemented.

## Interfaces you provide

- `common.config`, `common.status`, `common.load_split`.
- Root commands and artifact/status conventions.
- No stage-specific scientific logic.

## Pitfalls

- **Refactoring behavior while moving files** — move first, prove output
  equivalence, then make separately reviewed improvements.
- **Shared SQLite connections across Windows workers** — each training
  worker must open its own read-only connection (benchmarked in Stage 4).
- **Two sources of truth for a number** — the committed `batch.py`
  already duplicates the synthetic ratio from `configs/pipeline.yaml`.
  Find the rest before someone edits one of them.
- **Truncating `test_access.log` to make a check pass** — the check is
  scoped to `run_id` for exactly this reason. Resetting the file
  destroys the audit trail it exists to provide.
- **Stub status looking like success** — stubs must say `not_run`, never
  `passed`.
- **Guard theater** — a configuration file is not enough; the Done-when
  checks require deliberate violations to fail.

## Glossary

- **Reproducible run**: the same code, data and settings produce the same
  outputs. Example: rerunning Stage 1 with seed 42 gives identical manifests.
- **Pipeline DAG**: stages connected by their input/output dependencies.
  Example: Stages 2 and 3 both depend on Stage 1 but not on each other.
- **Caching**: reusing a stage output when none of its inputs changed.
  Example: editing only the report does not retrain the CNN.
- **Contract test**: a test of a public interface rather than its internals.
  Example: `generate()` must always return a 64×64 uint8 image.
- **Pre-commit hook**: a local check run before a commit is accepted.
  Example: import-linter rejects `stage2_augment → stage3_synth`.
- **Shared data folder**: storage for data too large or unsuitable for
  Git, identified by a published hash. Example: a OneDrive folder whose
  archive SHA-256 matches on every machine.
- **Run id**: one identifier minted per pipeline invocation and written
  into every stage's status file. Example: Stage 5 counts the test reads
  carrying today's run id and ignores yesterday's.
- **Migration equivalence**: proof that restructuring code did not change
  its output. Example: the catalog hash is identical before and after.

## Missions

### M1 Identify the boundary violation (recognition)
Prompt: which imports violate the plan?

1. `stage4_train` imports `stage2_augment.transform`.
2. `stage2_augment` imports `stage3_synth.generate` to preview images.
3. `stage1_freeze` imports `common.phash`.
4. `demo` imports `stage4_train.SmallCNN` to rebuild the model.

Expected outcome: 2 and 4 violate the boundaries. 1 and 3 are allowed.
The demo must use the exported bundle, not training code.

### M2 Fail-closed status writer (application)
Prompt: implement a helper that always leaves valid machine-readable
status, including on failure.

```python
def run_stage(name, fn, **metadata):
    started = utc_now()
    try:
        result = fn()
        write_status(name, status="passed", started_at=started,
                     finished_at=utc_now(), **result)
    except Exception as exc:
        write_status(name, status="failed", started_at=started,
                     finished_at=utc_now(), error=str(exc), **metadata)
        raise
```
Expected outcome: a successful stub writes `passed`; a stub that raises
writes `failed` and exits nonzero; neither can silently leave stale
`passed` output from an earlier run.

### M3 One-click clean-clone rehearsal (synthesis)
Prompt: rehearse the whole owner hand-off using stub stages.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pre-commit install
python run_pipeline.py --check
python run_pipeline.py
python run_pipeline.py              # second run: all cached
python run_pipeline.py --dashboard
```
Expected outcome: every command is documented in the README; the first
run creates seven `not_run`/stage-result files and a compiling
`phase2_report.pdf` built from placeholder tables, the second skips
unchanged work, and the dashboard renders missing artifacts without
errors. Temporarily add a forbidden import and verify that the run stops
before Stage 1.
