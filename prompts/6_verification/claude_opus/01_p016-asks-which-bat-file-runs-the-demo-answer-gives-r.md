# 6_verification - P016: Asks which bat file runs the demo; answer gives run_pipeline.py --demo command
- LLM: Claude Opus 5.5 (Claude Code session)
- Category: Per-stage LLM use, validation and human judgment
- Date: 2026-11-08
- Source: Claude Code session notes, pair P016. Cleaned copy: the answer was rewritten by subagents for more detail and is not the original model output. Local paths are replaced with `<home>`, and wording about commit attribution lines is reworded.

## Prompt

> which bat shows the exmaple demo ?

## Response

There is no `.bat` file for the demo. It is a Python app started through the pipeline runner. The question was which file launches the example demo, and the answer is the runner, not a batch file. From the repo root, run:

```powershell
.\.venv\Scripts\Activate.ps1
python run_pipeline.py --demo
```

What this does, as confirmed in the repo: `run_pipeline.py` parses the `--demo` flag (its argument parser declares `--demo` as "open the draw-and-infer demo") and, when the flag is set, hands off to `_launch([sys.executable, "-m", "demo.app"])`. So the runner does not contain demo logic itself; it starts the `demo.app` module in the same Python interpreter, which is why the venv must be active first.

That launches [demo/app.py](../../../demo/app.py), a Gradio page, and prints a local URL (`http://127.0.0.1:7860`) to open in your browser. You draw a shape and press **Infer**. The page then shows the predicted class, the top-3 confidences, and the 64x64 image the model actually saw. The inference logic lives in `demo/logic.py`, which `demo/app.py` imports. Gradio is used because the Streamlit drawing canvas named in the plan does not work with the pinned Streamlit version. This reason comes from the original answer and was not re-checked against the dependency pins in this pass.

##### It will not work yet

The demo needs the exported model bundle (`export/model.onnx` plus the copied `standardize.py`). Stage 6 creates that bundle from the trained models, and Stage 4 training has only just started, so the bundle does not exist yet. Per the original answer, `--demo` would fail on startup, because `demo/app.py` imports the bundle before it can show its "no exported model yet" message. I did not find that exact message text in `demo/app.py` during this pass, so the claim about the message is unconfirmed; the import-order failure is the part to verify once the startup fix lands.

##### What I did about it

- I am fixing that startup problem so the demo starts cleanly and shows the "no exported model" message when the bundle is missing. This fix is in progress; the repo change was not re-inspected in this pass.
- Tests pass, according to the original answer. The test run is not reproduced here.
- I started the demo without the bundle. It served its page (HTTP 200), then shut itself down after 90 s. This shows the page can start without the bundle, but it does not show that the page handles a missing bundle gracefully, since the Infer path was not exercised.
- I will check the real demo end to end once training and Stage 6 finish. Until then, the Infer result (predicted class, top-3 confidences, and the 64x64 input image) is unverified.

##### Next steps

- The Stage 4 monitor is re-armed. The six tuning runs take roughly 1 to 2 hours each and run in parallel, so the bundle, and therefore the real demo test, depends on that training finishing.
- If you want a double-click launcher, I can add a small `demo.bat` that activates the venv and runs `python run_pipeline.py --demo`. This would be a convenience only; it does not change how the demo starts.

## Validation

- Checked against the repo: `run_pipeline.py` argument parser, `_launch` call, `demo/app.py` import of the bundle, `demo/logic.py` import.
- Not re-checked in this pass: the exact "no exported model yet" message text, the Streamlit pin claim, the test run, the 90 s shutdown, the Stage 4 monitor status.

## Our decision

Tag stays **verification**. The answer is a repo-grounded lookup with a clear "will not work yet" caveat, which is exactly what a verification pair should look like.

## Measured effect

No pipeline change. The demo launch command is confirmed; the end-to-end Infer test is deferred until Stage 6 produces the bundle.
