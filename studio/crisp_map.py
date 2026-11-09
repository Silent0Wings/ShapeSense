"""How the six CRISP-DM steps map to pipeline stages and pages."""

from __future__ import annotations

from studio.data import lights
from studio.data.tables import read_csv, read_json

STAGE_PHASE = {0: "Foundations for every step", 1: "Data Understanding and Preparation",
               2: "Data Preparation", 3: "Data Preparation", 4: "Modeling", 5: "Evaluation",
               6: "Deployment"}

PHASES = (
    {"id": "business", "name": "Business Understanding", "page": "business.html", "stages": []},
    {"id": "data", "name": "Data Understanding", "page": "stage1.html", "stages": [1]},
    {"id": "prep", "name": "Data Preparation", "page": "stage2.html", "stages": [1, 2, 3]},
    {"id": "model", "name": "Modeling", "page": "stage4.html", "stages": [4]},
    {"id": "eval", "name": "Evaluation", "page": "stage5.html", "stages": [5]},
    {"id": "deploy", "name": "Deployment", "page": "live.html", "stages": [6]},
)


def _image_total() -> int:
    rows = read_csv("split_stats") or []
    return sum(int(r["n"]) for r in rows)


def _status_lines() -> dict[str, str]:
    verdict = lights.verdict()
    tuning = read_json("tuning") or {}
    card = read_json("model_card") or {}
    winner = tuning.get("winner", {})
    return {
        "business": ("Does synthetic data help a small CNN? "
                     + (f"Verdict: {verdict['verdict']}." if verdict else "No verdict yet.")),
        "data": f"{_image_total():,} images from four public sources, leak-free split.",
        "prep": "Class-safe augmentation and a synthetic generator, train side only.",
        "model": (f"Three arms, three seeds, tuned once (lr {winner.get('lr')}, dropout "
                  f"{winner.get('dropout')})." if winner else "No trained runs yet."),
        "eval": (f"B vs A1: {verdict['delta']:+.2f} points, CI [{verdict['ci'][0]:.2f}, "
                 f"{verdict['ci'][1]:.2f}]." if verdict else "Not evaluated yet."),
        "deploy": (f"ONNX bundle from {card.get('run_name')}, drawn shapes scored live."
                   if card else "No exported model yet."),
    }


def phases() -> list[dict]:
    lines = _status_lines()
    return [{**p, "status_line": lines[p["id"]]} for p in PHASES]
