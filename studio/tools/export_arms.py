"""Export each arm's best-validation run to ONNX for the arm comparison.

Run once after Stage 4: ``python -m studio.tools.export_arms``. Reads only
validation scores and writes only under studio/out/arms.
"""

from __future__ import annotations

import json

import onnxruntime  # noqa: F401  # loaded before torch, as src/stage6_report/export.py does
from src.common.hashing import sha256_path
from src.stage6_report.export import export_candidates, export_onnx, select_model, stage4_dir

from studio.context import config
from studio.settings import ARMS_DIR, ARMS_MANIFEST

ARMS_TO_EXPORT = ("A0", "A1", "B", "A2", "P")


def main() -> None:
    cfg = config()
    names = export_candidates(cfg)
    manifest = {}
    for arm in ARMS_TO_EXPORT:
        chosen = select_model(stage4_dir(cfg), [n for n in names if n.startswith(f"{arm}_")])
        out = ARMS_DIR / arm / "model.onnx"
        out.parent.mkdir(parents=True, exist_ok=True)
        export_onnx(chosen["model_path"], out, int(cfg["image_size"]))
        manifest[arm] = {"run": chosen["run_name"], "val_macro_f1": chosen["val_macro_f1"],
                         "sha256": sha256_path(out)}
        print(f"{arm}: {chosen['run_name']} (val macro-F1 {chosen['val_macro_f1']:.2f}) -> {out}")
    ARMS_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
