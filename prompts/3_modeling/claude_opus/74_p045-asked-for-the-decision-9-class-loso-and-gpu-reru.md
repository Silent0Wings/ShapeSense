# 3_modeling - P045: Asked for the decision; 9-class LOSO and GPU rerun chosen
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P045. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

so what is my decision here , mcq trigger

## Response

#### Decision recorded

You chose **9-class LOSO**, with the rerun on the new machine's GPU. No training was run in this session.

#### Why the change was needed

Stage 4 had crashed because the ellipse class exists only in the source that the held-out runs leave out. So the leave-one-source-out runs could not train as they were.

#### What I changed

- **9-class LOSO:** the held-out runs now skip any class they lose, for both real and synthetic images, and leave it out of validation macro-F1. Stage 5 scores only the Hand-Drawn triangle and rectangle for those models. An empty class in an ordinary run still fails, as it should.
- **GPU:** I added `train.device: auto` and moved Stage 4 training onto it. Saved models stay loadable on CPU, so Stages 5 and 6 do not change.
- **No mixing machines:** the GPU model and torch version are now part of the recipe, so runs from different machines cannot be combined.
- **Docs:** I updated the README, the report's LOSO wording, P-61 in `plan_issues.md`, the tracker and the handoff.

#### Verification

- 338 tests pass, with 4 export tests still skipped, and the guards are green. All 12 deliberate code breakages were caught by the new tests.
- One real arm B LOSO epoch ran on CPU, where it had crashed before: 49 steps, 9 classes, no ellipse.
- **Not verified:** the GPU path has never run on a GPU, because this machine has none. The first run on the 3080 will be its first real test.
- The 9 finished runs are now out of date, because the recipe changed. All 15 trainings will rerun. There are still no test reads.
- Nothing is committed yet.

#### Steps on the new machine

1. Copy the whole repo folder, including `data_set/` and `artifacts/`, but not `.venv`.
2. Create a fresh venv, install `requirements.txt`, then install the CUDA build of PyTorch.
3. Confirm `python -c "import torch; print(torch.cuda.is_available())"` prints `True`.
4. Run `python run_pipeline.py --stages 4`, then `--stages 5`, then `--stages 6`.

#### Two decisions before the rerun

1. Should I commit these changes through the guard? I recommend yes, so the code you carry over is a known version.
2. Should the tracker's other training changes be included first, such as the continuous non-uniform scale fix and the zero-padding question? They also change the recipe, so anything left out costs another full rerun later. My recommendation is to leave them out unless you already want them, so this rerun tests only the changes you approved.

##### Why the chosen change set matters
- Each training change alters the recipe, so every run made before it becomes stale. Leaving extra changes out now avoids a second full rerun later.
- The 9-class LOSO change, the GPU device option and the recipe fields for GPU and torch version are the approved set in this note. The test suite (338 passing) and the 12 deliberate breakages caught by the new tests support that these changes work as described.

##### Consequences
- The GPU path has never run on a GPU, because this machine has none. The first run on the RTX 3080 is therefore the first real test of it, and any problem there is unverified until then.
- The 9 finished runs are out of date and will retrain. No test reads were used, so the test split is still sealed.

## Validation

Not recorded in the session notes.

## Our decision

Not recorded in the session notes.

## Measured effect

Not recorded in the session notes.
