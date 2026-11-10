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


def _other_arms(metrics: dict) -> list[dict]:
    """The other arms against the same reference. P was descriptive, so it has no interval."""
    robust = metrics.get("robust") or {}
    secondary = robust.get("secondary", {})
    rows = [{"label": name, "delta": secondary[name]["delta"], "ci": secondary[name]["ci"]}
            for name in ("B vs A0", "A1 vs A0") if name in secondary]
    ensembles = robust.get("ensembles", {})
    if "P" in ensembles and "A0" in ensembles:
        rows.append({"label": "P vs A0", "ci": None,
                     "delta": ensembles["P"]["perturbed_macro_f1"] - ensembles["A0"]["perturbed_macro_f1"]})
    return sorted(rows, key=lambda row: -row["delta"])


def iteration_results() -> dict[int, dict]:
    """Each iteration's pre-registered result, from its frozen record."""
    out = {}
    for iteration, name in ((1, "iter1_status"), (2, "iter2_status"), (3, "status5")):
        m = (read_json(name) or {}).get("metrics", {})
        if "verdict" in m:
            out[iteration] = {"verdict": m["verdict"], "delta": m["delta"], "ci": m["ci"], "label": m["primary"]["label"]}
    return out


def _clean_gain(metrics: dict) -> dict | None:
    """Full mix against Real only on clean images. Older records may not have it, so it is optional."""
    row = ((metrics.get("robust") or {}).get("clean") or {}).get("A2 vs A0")
    return None if row is None else {"label": "A2 vs A0", "delta": row["delta"], "ci": row["ci"]}


def verdict() -> dict | None:
    status = read_json("status5")
    if status is None or "verdict" not in status.get("metrics", {}):
        return None
    m = status["metrics"]
    return {"verdict": m["verdict"], "delta": m["delta"], "ci": m["ci"], "reasons": m["reasons"],
            "label": m["primary"]["label"], "others": _other_arms(m), "clean": _clean_gain(m)}
