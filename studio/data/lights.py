"""The seven stage status lights."""

from __future__ import annotations

from studio.data.tables import read_json

STAGE_TITLES = ("Infrastructure", "Data freeze", "Augmentation", "Synthetic generator",
                "Training", "Evaluation", "Report and export")


def rows() -> list[dict]:
    out = []
    for n, title in enumerate(STAGE_TITLES):
        status = read_json(f"status{n}")
        out.append({"stage": n, "title": title, "page": f"stage{n}.html",
                    "status": status["status"] if status else "not_run",
                    "finished_at": status.get("finished_at") if status else None,
                    "run_id": status.get("run_id") if status else None})
    return out


def verdict() -> dict | None:
    status = read_json("status5")
    if status is None or "verdict" not in status.get("metrics", {}):
        return None
    m = status["metrics"]
    return {"verdict": m["verdict"], "delta": m["delta"], "ci": m["ci"], "reasons": m["reasons"],
            "label": m["primary"]["label"]}
