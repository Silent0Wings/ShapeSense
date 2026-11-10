"""E28: one fair run end-to-end (stages/stage_4.md M3, R1-R5, R8, R11, R12).

Tiny synthetic 64x64 data only: no data_set/, no test split, 2-epoch runs.
The config is the committed pipeline.yaml with the training budget
overridden on a deep copy, so every other number stays single-sourced.
"""

import copy
import csv
import json
import math

import numpy as np
import pytest
import torch

from src.common.config import load_config
from src.stage4_train.data import ImageStore
from src.stage4_train.sampling import batch_composition, to_float
from src.stage4_train.sweep import seed_disagreement
from src.stage4_train.train import (RUN_JSON, TRAIN_LOG_CSV, VAL_PROBS_FILE, MODEL_FILE,
                                    VAL_CURVE_FILE, macro_f1_points,
                                    required_steps_per_epoch, train_one)
from src.stage4_train.tuning import run_tuning

N_CLASSES = 3
SIZE = 64                 # the CNN pools 64 -> 8; inputs must be 64x64
N_TRAIN = 40
N_VAL = 12
BATCH = 16                # toy batch size (fixture)
STEPS = math.ceil(N_TRAIN / BATCH)   # = 3, the Decision 13 budget of the toy A0 store
TOY_EPOCHS = 2
TOY_THREADS = 1
SOURCES = ("quickdraw", "github_handdrawn")


def _toy_image(label: int, rng: np.random.Generator) -> np.ndarray:
    """Black bar on white: horizontal (0), vertical (1), diagonal (2) + salt noise."""
    img = np.full((SIZE, SIZE), 255, dtype=np.uint8)
    if label == 0:
        img[28:36, :] = 0
    elif label == 1:
        img[:, 28:36] = 0
    else:
        idx = np.arange(SIZE)
        img[idx, idx] = 0
        img[idx[:-1], idx[:-1] + 1] = 0
    flips = rng.integers(0, SIZE, size=(6, 2))
    img[flips[:, 0], flips[:, 1]] = 0
    return img


def _store(n: int, seed: int) -> ImageStore:
    rng = np.random.default_rng(seed)
    labels = np.arange(n, dtype=np.int64) % N_CLASSES
    images = np.stack([_toy_image(int(l), rng) for l in labels])
    sources = np.array([SOURCES[i % len(SOURCES)] for i in range(n)])
    return ImageStore(images, labels, sources, N_CLASSES)


def _transform(img, label, rng):
    return np.roll(img, int(rng.integers(-2, 3)), axis=1)


def _generate(label, rng):
    return _toy_image(int(label), rng)


def _toy_config(**train_overrides) -> dict:
    cfg = copy.deepcopy(load_config())
    cfg["train"].update({"max_epochs": TOY_EPOCHS, "batch_size": BATCH, "steps_per_epoch": STEPS,
                         "num_threads": TOY_THREADS, "parallel_runs": 1})
    cfg["train"].update(train_overrides)
    return cfg


def _hparams(cfg: dict) -> dict:
    return {"lr": cfg["train"]["lr"], "dropout": cfg["train"]["dropout"]}


def _train(cfg, arm, seed, out_dir, **kwargs):
    return train_one(f"{arm}_{seed}", arm, seed, cfg, _store(N_TRAIN, 1), _store(N_VAL, 2),
                     _transform, _generate, _hparams(cfg), out_dir,
                     steps_per_epoch=STEPS, **kwargs)


def _read_log(out_dir):
    with open(out_dir / TRAIN_LOG_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# --------------------------------------------------------------------------- #
# Decision 13: the frozen step budget
# --------------------------------------------------------------------------- #

def test_refuses_null_steps_per_epoch(tmp_path):
    cfg = _toy_config(steps_per_epoch=None)
    with pytest.raises(ValueError, match=f"set train.steps_per_epoch: {STEPS}"):
        required_steps_per_epoch(cfg, N_TRAIN)
    with pytest.raises(ValueError, match="steps_per_epoch"):
        _train(cfg, "A0", 0, tmp_path / "A0_0")
    assert not (tmp_path / "A0_0" / RUN_JSON).exists()


def test_refuses_mismatched_steps_per_epoch(tmp_path):
    cfg = _toy_config(steps_per_epoch=STEPS + 2)
    with pytest.raises(ValueError, match="mismatched"):
        required_steps_per_epoch(cfg, N_TRAIN)
    with pytest.raises(ValueError, match="differs from the frozen"):
        _train(cfg, "A0", 0, tmp_path / "A0_0")
    good = _toy_config()
    assert required_steps_per_epoch(good, N_TRAIN) == STEPS


def test_same_steps_every_arm(tmp_path):
    cfg = _toy_config()
    infos = {arm: _train(cfg, arm, 0, tmp_path / f"{arm}_0") for arm in ("A0", "B")}
    for arm, info in infos.items():
        on_disk = json.loads((tmp_path / f"{arm}_0" / RUN_JSON).read_text(encoding="utf-8"))
        assert on_disk["steps_per_epoch"] == STEPS
        assert on_disk["optimizer_steps"] == STEPS * on_disk["epochs_run"]
        assert on_disk["max_epochs"] == TOY_EPOCHS
        assert len(_read_log(tmp_path / f"{arm}_0")) == on_disk["epochs_run"]
        assert info["optimizer_steps"] == on_disk["optimizer_steps"]
    assert infos["A0"]["optimizer_steps"] == infos["B"]["optimizer_steps"]
    assert infos["A0"]["epochs_run"] == infos["B"]["epochs_run"] == TOY_EPOCHS
    # the only difference is the data stream: B substitutes synthetic images
    n_real_b, n_syn_b = batch_composition(cfg["arms"]["B"], BATCH, cfg["synthetic_fraction"])
    assert infos["A0"]["realized_synthetic_share"] == 0.0
    assert infos["A0"]["real_draws_per_step"] == BATCH
    assert infos["B"]["real_draws_per_step"] == n_real_b
    assert infos["B"]["realized_synthetic_share"] == pytest.approx(n_syn_b / BATCH)
    for arm in ("A0", "B"):
        for name in (MODEL_FILE, VAL_PROBS_FILE, VAL_CURVE_FILE, TRAIN_LOG_CSV, RUN_JSON):
            assert (tmp_path / f"{arm}_0" / name).is_file()


# --------------------------------------------------------------------------- #
# Mission M3: reproducibility and validation-based selection
# --------------------------------------------------------------------------- #

def test_reproducible_val_f1_same_seed(tmp_path):
    cfg = _toy_config()
    first = _train(cfg, "A0", 0, tmp_path / "run1")
    second = _train(cfg, "A0", 0, tmp_path / "run2")
    assert first["val_macro_f1"] == second["val_macro_f1"]
    assert first["best_epoch"] == second["best_epoch"]
    with np.load(tmp_path / "run1" / VAL_PROBS_FILE) as a, \
            np.load(tmp_path / "run2" / VAL_PROBS_FILE) as b:
        assert np.array_equal(a["probs"], b["probs"])
        assert np.array_equal(a["labels"], b["labels"])
        assert np.array_equal(a["image_ids"], b["image_ids"])


def test_early_stopping_keeps_best_epoch(tmp_path):
    patience = 2
    scores = [10.0, 30.0, 20.0, 5.0, 40.0, 50.0]  # epoch 2 wins; patience 2 stops after epoch 4
    cfg = _toy_config(max_epochs=len(scores), early_stopping_patience=patience)
    seen_probs = {}

    def scorer(epoch_idx, probs, labels):
        seen_probs[epoch_idx] = probs.copy()
        return scores[epoch_idx]

    info = _train(cfg, "A1", 0, tmp_path / "A1_0", val_scorer=scorer)
    assert info["best_epoch"] == 2
    assert info["epochs_run"] == 4
    assert info["selection_score"] == 30.0
    assert len(_read_log(tmp_path / "A1_0")) == 4
    with np.load(tmp_path / "A1_0" / VAL_PROBS_FILE) as data:
        saved = data["probs"]
        labels = data["labels"]
    assert np.array_equal(saved, seen_probs[1])
    assert info["val_macro_f1"] == pytest.approx(
        macro_f1_points(labels, saved.argmax(axis=1), N_CLASSES))
    # model.pt holds the epoch-2 weights, not the last epoch's
    val = _store(N_VAL, 2)
    scripted = torch.jit.load(str(tmp_path / "A1_0" / MODEL_FILE))
    scripted.eval()
    with torch.no_grad():
        probs = torch.softmax(scripted(torch.from_numpy(to_float(val.images))), dim=1).numpy()
    assert np.allclose(probs, saved, atol=1e-5)


def test_val_probs_rows_sum_to_one(tmp_path):
    cfg = _toy_config()
    ids = np.array([f"img{i}" for i in range(N_VAL)])
    _train(cfg, "A1", 1, tmp_path / "A1_1", val_image_ids=ids)
    with np.load(tmp_path / "A1_1" / VAL_PROBS_FILE) as data:
        probs, labels, image_ids = data["probs"], data["labels"], data["image_ids"]
    assert probs.shape == (N_VAL, N_CLASSES) and probs.dtype == np.float32
    assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-5)
    assert (probs >= 0).all()
    assert labels.dtype == np.int64 and labels.shape == (N_VAL,)
    assert list(image_ids) == list(ids)


def test_macro_f1_points_helper():
    labels = np.array([0, 0, 1, 1, 2, 2])
    assert macro_f1_points(labels, labels, 3) == pytest.approx(100.0)
    preds = np.array([0, 0, 1, 1, 0, 0])  # class 2 never predicted -> F1 0
    f1_0 = 2 * 2 / (2 * 2 + 2 + 0)
    assert macro_f1_points(labels, preds, 3) == pytest.approx(100.0 * (f1_0 + 1.0 + 0.0) / 3)


# --------------------------------------------------------------------------- #
# R11 seed disagreement, R4 tuning selection
# --------------------------------------------------------------------------- #

def _write_probs(root, name, probs):
    (root / name).mkdir(parents=True)
    np.savez(root / name / VAL_PROBS_FILE, probs=probs.astype(np.float32),
             labels=np.zeros(len(probs), np.int64),
             image_ids=np.array([str(i) for i in range(len(probs))]))


def test_seed_disagreement_identical_runs_zero(tmp_path):
    probs = np.random.default_rng(0).random((20, N_CLASSES)).astype(np.float32)
    _write_probs(tmp_path, "A0_0", probs)
    _write_probs(tmp_path, "A0_1", probs)
    flipped = probs.copy()
    flipped[:5] = np.roll(flipped[:5], 1, axis=1)  # 5 of 20 argmaxes change
    _write_probs(tmp_path, "A1_0", probs)
    _write_probs(tmp_path, "A1_1", flipped)
    _write_probs(tmp_path, "A1_loso_handdrawn_0", flipped[:7])
    runs = [{"run_name": "A0_0", "arm": "A0", "seed": 0},
            {"run_name": "A0_1", "arm": "A0", "seed": 1},
            {"run_name": "A1_0", "arm": "A1", "seed": 0},
            {"run_name": "A1_1", "arm": "A1", "seed": 1},
            {"run_name": "A1_loso_handdrawn_0", "arm": "A1", "seed": 0,
             "holdout_source": "github_handdrawn"}]
    result = seed_disagreement(tmp_path, runs)
    assert result["per_arm"]["A0"]["mean_pairwise_disagreement"] == 0.0
    assert result["per_arm"]["A1"]["mean_pairwise_disagreement"] == pytest.approx(5 / 20)
    assert result["per_arm"]["A1"]["runs"] == ["A1_0", "A1_1"]  # LOSO run excluded
    assert "not the power check" in result["note"].lower()  # R11: robustness number only


def test_tuning_selects_by_val(tmp_path):
    cfg = _toy_config()
    tuning_cfg = cfg["train"]["tuning"]
    preset = {(float(lr), float(do)): 50.0 + 10 * i
              for i, (lr, do) in enumerate((lr, do) for lr in tuning_cfg["lr"]
                                           for do in tuning_cfg["dropout"])}
    expected = max(preset, key=preset.get)
    calls = []

    def fake_trainer(**kwargs):
        calls.append(kwargs)
        key = (float(kwargs["hparams"]["lr"]), float(kwargs["hparams"]["dropout"]))
        return {"val_macro_f1": preset[key], "best_epoch": 1}

    result = run_tuning(cfg, None, None, None, None, STEPS, tmp_path, trainer=fake_trainer)
    assert len(calls) == len(preset)
    assert {c["arm"] for c in calls} == {tuning_cfg["arm"]}
    assert {c["seed"] for c in calls} == {cfg["seed_set"][0]}
    assert all(c["steps_per_epoch"] == STEPS for c in calls)
    assert (result["winner"]["lr"], result["winner"]["dropout"]) == expected
    written = json.loads((tmp_path / "tuning.json").read_text(encoding="utf-8"))
    assert written["winner"] == result["winner"]
    assert len(written["grid"]) == len(preset)
    # same grid + arm -> reused, no retraining
    again = run_tuning(cfg, None, None, None, None, STEPS, tmp_path, trainer=fake_trainer)
    assert len(calls) == len(preset)
    assert again["winner"] == result["winner"]


def test_train_log_columns():
    from src.stage4_train.train import LOG_COLUMNS

    assert "train_acc_trainmode" in LOG_COLUMNS and "train_acc" not in LOG_COLUMNS
