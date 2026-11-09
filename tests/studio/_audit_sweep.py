"""Subprocess body of test_no_test_split_read: record every file the studio opens.

An audit hook sees each ``open`` while every endpoint is called once. Prints JSON
with the forbidden opens found, and proves first that the hook itself works.
"""

import json
import sys
import tempfile
from pathlib import Path

opened: list[tuple[str, str]] = []


def _hook(event, args):
    if event == "open" and isinstance(args[0], (str, Path)):
        opened.append((str(args[0]).replace("\\", "/"), str(args[1])))


sys.addaudithook(_hook)

from starlette.testclient import TestClient  # noqa: E402

sys.path.insert(0, ".")
from studio.server.app import create_app  # noqa: E402
from studio.settings import ARMS, ERRORS_ARM  # noqa: E402

ALLOWED_PREDICTIONS = {f"ensemble_{a}.npz" for a in ARMS} | {f"ensemble_{ERRORS_ARM}_errors.npz"}


def forbidden(path: str, mode: str) -> bool:
    if path.endswith("configs/splits/test.csv") or "/data_set/unified/test/" in path:
        return True
    if "/artifacts/stage0/rebuild/" in path:
        return True
    if path.endswith(("configs/splits/fresh_holdout.csv", "configs/splits/fresh_holdout_2.csv")):
        return True
    if "/data_set/fresh_holdout/" in path or "/data_set/fresh_holdout_2/" in path:
        return True
    if any(f"/artifacts/stage5/{folder}/" in path for folder in ("predictions_fresh", "predictions_fresh2", "predictions_robust", "perturbed_fresh2")):
        return True
    if "/artifacts/stage5/predictions/" in path and path.rsplit("/", 1)[1] not in ALLOWED_PREDICTIONS:
        return True
    return path.endswith("test_access.log") and mode != "r" and mode != "rb"


with tempfile.TemporaryDirectory() as tmp:
    probe = Path(tmp) / "configs" / "splits"
    probe.mkdir(parents=True)
    (probe / "test.csv").write_text("x", encoding="utf-8")
    opened.clear()
    (probe / "test.csv").read_text(encoding="utf-8")
    hook_works = any(forbidden(p, m) for p, m in opened)

opened.clear()
client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
page = client.get
for name in ("home", "business", "stage0", "stage1", "stage2", "stage3", "stage4", "stage5",
             "stage6", "live", "iteration1", "iteration2", "experiments", "failures", "failure", "robustness", "changes"):
    page(f"/api/page/{name}")
stage2 = page("/api/page/stage2").json()["defaults"]
stage3 = page("/api/page/stage3").json()["defaults"]
for label in range(10):
    for split in ("train", "val", "test", "fresh_holdout", "fresh_holdout_2"):
        page(f"/api/samples?label={label}&split={split}&n=4")
        page(f"/api/class-stats?label={label}&split={split}")
    client.post("/api/augment", json={"label": label, "index": 0, "seed": 0, "n": 2, "values": stage2})
    client.post("/api/synth", json={"label": label, "seed": 0, "n": 2, "values": stage3})
for arm in ARMS:
    page(f"/api/stage5/confusion/{arm}")
    page(f"/img/confusion_{arm}")
    page(f"/img/iter1_confusion_{arm}")
page("/img/robustness_examples")
for true in range(10):
    for pred in range(10):
        page(f"/api/stage5/errors?true={true}&pred={pred}")
page("/api/stage4/run/A0_0")
client.post("/api/whatif", json={"min_gain": 1, "max_class_drop": 2, "require_ci": True})
for group in page("/api/page/stage1").json()["duplicates"][:2]:
    page(f"/api/group?group={group['group']}")

bad = sorted({p for p, m in opened if forbidden(p, m)})
print("RESULT" + json.dumps({"hook_works": hook_works, "forbidden": bad, "n_opens": len(opened)}))
