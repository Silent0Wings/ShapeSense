"""
Draw-and-infer demo (CRISP-DM step 6, plan 33 / E33). Started with
``python -m demo.app`` (the runner starts it with ``--demo``).

Drawings made here are informal evidence only (R17): they are not test
data, never used for training, and never change the Stage 5 verdict.

This app imports only the ``export`` package (R15); the pure logic lives
in ``demo/logic.py``.
"""
import gradio as gr

from demo import logic


class MissingBundle:
    """Stand-in when export/ has not been generated yet (no model, no copied
    standardize.py): the app still starts and shows logic.NO_MODEL_MESSAGE."""

    class Rejected(Exception):
        pass

    @staticmethod
    def model_available() -> bool:
        return False


def load_bundle():
    """export.predict if the bundle exists, else MissingBundle (R16)."""
    try:
        from export import predict
    except ImportError:
        return MissingBundle()
    return predict


bundle = load_bundle()


def _markdown(result):
    if result["message"] is not None:
        return f"**{result['message']}**"
    if result["confident"]:
        return f"**Prediction: {result['label']}**"
    best_name, best_p = result["top3"][0]
    return (f"**Not sure** — best guess {best_name} at {best_p:.0%} "
            f"(below {logic.NOT_SURE_THRESHOLD:.0%})")


def _on_infer(value):
    result = logic.infer(logic.canvas_to_rgba(value), bundle)
    scores = {name: p for name, p in result["top3"]} or None
    return scores, _markdown(result), result["x64"]


def _on_clear():
    return None, None, "", None


def build_app():
    with gr.Blocks(title="ShapeSense — draw a shape") as demo:
        gr.Markdown("# Draw a shape\nSketch one of the 10 shapes, press **Infer**.")
        with gr.Row():
            sketch = gr.Sketchpad(
                type="numpy",
                image_mode="RGBA",
                canvas_size=(256, 256),
                brush=gr.Brush(default_size=8, colors=["#000000"], color_mode="fixed"),
                label="Draw",
            )
            with gr.Column():
                infer_btn = gr.Button("Infer", variant="primary")
                clear_btn = gr.Button("Clear")
                message = gr.Markdown()
                top3 = gr.Label(num_top_classes=logic.TOP_K, label="Top-3 confidences")
                seen = gr.Image(label="What the model saw (64×64)", image_mode="L",
                                width=128, height=128)
        gr.Markdown(
            "Data and model credits: see `export/README.md`. "
            "Drawings are informal evidence only; they are not used for training "
            "or for the test verdict."
        )
        infer_btn.click(_on_infer, inputs=sketch, outputs=[top3, message, seen])
        clear_btn.click(_on_clear, inputs=None, outputs=[sketch, top3, message, seen])
    return demo


def main():
    build_app().launch(server_name="127.0.0.1")


if __name__ == "__main__":
    main()
