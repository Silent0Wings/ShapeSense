"""A finished run is reused only if it was trained with the same recipe
(architecture, augmentation, generator, code) — not just the same hparams."""

import copy
import json

from src.common.config import load_config
from src.stage4_train.train import (MODEL_FILE, RUN_JSON, VAL_PROBS_FILE, completed_run,
                                    recipe_fingerprint)


def _fake_run(tmp_path, recipe):
    (tmp_path / RUN_JSON).write_text(json.dumps(
        {"hparams": {"lr": 0.001, "dropout": 0.2}, "steps_per_epoch": 50, "recipe": recipe}),
        encoding="utf-8")
    (tmp_path / MODEL_FILE).write_bytes(b"x")
    (tmp_path / VAL_PROBS_FILE).write_bytes(b"x")


def test_recipe_changes_with_architecture_and_augmentation():
    cfg = load_config()
    base = recipe_fingerprint(cfg)
    for edit in (("train", "channels", [32, 64, 128]), ("augment", "frame_margin", 0.0)):
        other = copy.deepcopy(cfg)
        other[edit[0]][edit[1]] = edit[2]
        assert recipe_fingerprint(other) != base
    quiet = copy.deepcopy(cfg)
    quiet["train"]["parallel_runs"] = 1          # scheduling only: same results
    assert recipe_fingerprint(quiet) == base


def test_old_recipe_run_not_reused(tmp_path):
    cfg = load_config()
    _fake_run(tmp_path, "sha256:old-recipe")
    hp = {"lr": 0.001, "dropout": 0.2}
    assert completed_run(tmp_path, hp, 50, recipe_fingerprint(cfg)) is None
    _fake_run(tmp_path, recipe_fingerprint(cfg))
    assert completed_run(tmp_path, hp, 50, recipe_fingerprint(cfg)) is not None


def test_recipe_changes_when_training_data_changes(tmp_path):
    cfg = copy.deepcopy(load_config())
    cfg["paths"]["splits_dir"] = str(tmp_path)
    for s in ("train", "val"):
        (tmp_path / f"{s}.csv").write_text("image_id\na\n", encoding="utf-8")
    before = recipe_fingerprint(cfg)
    (tmp_path / "train.csv").write_text("image_id\nb\n", encoding="utf-8")
    assert recipe_fingerprint(cfg) != before
