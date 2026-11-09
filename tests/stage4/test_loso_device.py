"""P-61 and the GPU path: 9-class leave-one-source-out runs and device selection.

No data_set/ needed. The CUDA test runs only where a GPU is visible.
"""

import copy

import numpy as np
import pytest
import torch

from src.common.config import load_config
from src.stage4_train import sweep
from src.stage4_train.data import ImageStore
from src.stage4_train.sampling import BatchStream, balanced_labels, class_index, make_batch
from src.stage4_train.train import (MODEL_FILE, VAL_PROBS_FILE, macro_f1_points,
                                    recipe_fingerprint, resolve_device, runtime_id, train_one)

N_CLASSES = 10
SIZE = 16             # small test images; make_batch is size-agnostic
BATCH = 256           # mirrors train.batch_size (test fixture, not a config read)
FRACTION = 0.3        # mirrors synthetic_fraction (test fixture)
ELLIPSE = 1           # the class only Hand-Drawn owns
B = {"augment": False, "synthetic": True}   # synthetic draws without the transform


def _config(device=None) -> dict:
    cfg = copy.deepcopy(load_config())
    if device is None:
        cfg["train"].pop("device", None)
    else:
        cfg["train"]["device"] = device
    return cfg


def _no_gpu(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)


def _gpu(monkeypatch, name="Fake GPU"):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda index=0: name)


def _arrays(missing=()):
    labels = np.array([c for c in range(N_CLASSES) if c not in missing for _ in range(12)],
                      dtype=np.int64)
    images = np.full((labels.size, SIZE, SIZE), 255, dtype=np.uint8)
    images[:, 0, 0] = labels.astype(np.uint8)
    return images, labels, class_index(labels, N_CLASSES)


def _generate(seen):
    def generate(label, rng):
        seen.append(int(label))
        return np.full((SIZE, SIZE), 255, dtype=np.uint8)
    return generate


# --- device -----------------------------------------------------------------

def test_cpu_choice_ignores_a_visible_gpu(monkeypatch):
    _gpu(monkeypatch)
    assert resolve_device(_config("cpu")) == "cpu"


def test_auto_follows_gpu_availability(monkeypatch):
    _gpu(monkeypatch)
    assert resolve_device(_config("auto")) == "cuda"
    _no_gpu(monkeypatch)
    assert resolve_device(_config("auto")) == "cpu"


def test_missing_key_means_auto(monkeypatch):
    _gpu(monkeypatch)
    assert resolve_device(_config()) == "cuda"


def test_explicit_cuda_never_falls_back_to_cpu(monkeypatch):
    _no_gpu(monkeypatch)
    with pytest.raises(ValueError, match="no CUDA GPU"):
        resolve_device(_config("cuda"))


def test_unknown_device_rejected():
    with pytest.raises(ValueError, match="train.device"):
        resolve_device(_config("tpu"))


def test_runtime_id_names_device_gpu_and_torch(monkeypatch):
    _gpu(monkeypatch, "RTX Test")
    assert runtime_id(_config("cuda")) == {"device": "cuda", "device_name": "RTX Test",
                                           "torch": torch.__version__}
    assert runtime_id(_config("cpu")) == {"device": "cpu", "device_name": "cpu",
                                          "torch": torch.__version__}


# --- the recipe -------------------------------------------------------------

def test_recipe_changes_with_the_hardware(monkeypatch):
    _gpu(monkeypatch, "GPU one")
    cfg = _config("cuda")
    one = recipe_fingerprint(cfg)
    _gpu(monkeypatch, "GPU two")
    assert recipe_fingerprint(cfg) != one
    assert recipe_fingerprint(_config("cpu")) != one


def test_recipe_changes_with_the_torch_build(monkeypatch):
    cfg = _config("cpu")
    before = recipe_fingerprint(cfg)
    monkeypatch.setattr(torch, "__version__", "0.0.0+other")
    assert recipe_fingerprint(cfg) != before


def test_device_key_alone_does_not_change_the_recipe(monkeypatch):
    """`auto` and `cuda` resolve to the same hardware, so the same runs."""
    _gpu(monkeypatch)
    assert recipe_fingerprint(_config("auto")) == recipe_fingerprint(_config("cuda"))


# --- classes lost to the hold-out -------------------------------------------

def test_classes_lost_to_holdout_finds_the_empty_class():
    images, labels, _ = _arrays(missing=(ELLIPSE,))
    store = ImageStore(images, labels, np.full(labels.size, "quickdraw"), N_CLASSES)
    assert sweep.classes_lost_to_holdout(store) == (ELLIPSE,)


def test_nothing_lost_when_every_class_remains():
    images, labels, _ = _arrays()
    store = ImageStore(images, labels, np.full(labels.size, "quickdraw"), N_CLASSES)
    assert sweep.classes_lost_to_holdout(store) == ()


# --- sampling ---------------------------------------------------------------

def test_excluded_class_never_drawn_real_or_synthetic():
    images, labels, idx = _arrays(missing=(ELLIPSE,))
    drawn = []
    batch = make_batch(images, labels, idx, B, BATCH, FRACTION, N_CLASSES,
                       np.random.default_rng(0), generate=_generate(drawn),
                       excluded_classes=(ELLIPSE,))
    assert ELLIPSE not in set(batch.labels.tolist())
    assert drawn and ELLIPSE not in drawn
    assert set(batch.labels[batch.is_synthetic == 1].tolist()) == set(range(N_CLASSES)) - {ELLIPSE}


def test_empty_class_still_raises_when_not_excluded():
    images, labels, idx = _arrays(missing=(ELLIPSE,))
    with pytest.raises(ValueError, match="no image"):
        make_batch(images, labels, idx, {"augment": False, "synthetic": False}, BATCH, FRACTION,
                   N_CLASSES, np.random.default_rng(0))


def test_a_second_empty_class_still_raises():
    images, labels, idx = _arrays(missing=(ELLIPSE, 4))
    with pytest.raises(ValueError, match="no image"):
        make_batch(images, labels, idx, {"augment": False, "synthetic": False}, BATCH, FRACTION,
                   N_CLASSES, np.random.default_rng(0), excluded_classes=(ELLIPSE,))


def test_no_exclusion_keeps_the_same_draws():
    """Ordinary runs must be untouched by the P-61 change."""
    images, labels, idx = _arrays()
    arm = {"augment": False, "synthetic": False}
    plain = make_batch(images, labels, idx, arm, BATCH, FRACTION, N_CLASSES,
                       np.random.default_rng(7))
    again = make_batch(images, labels, idx, arm, BATCH, FRACTION, N_CLASSES,
                       np.random.default_rng(7), excluded_classes=())
    assert np.array_equal(plain.labels, again.labels)
    assert np.array_equal(plain.images, again.images)
    expected = balanced_labels(BATCH, N_CLASSES, np.random.default_rng(7))
    assert np.array_equal(np.sort(plain.labels), np.sort(expected))


def test_batch_stream_passes_the_exclusion_to_every_batch():
    images, labels, idx = _arrays(missing=(ELLIPSE,))
    stream = BatchStream(images, labels, B, BATCH, FRACTION, N_CLASSES, seed=0, steps=3,
                         generate=_generate([]), class_idx=idx, excluded_classes=(ELLIPSE,))
    batches = list(stream.epoch(0))
    assert len(batches) == 3
    assert all(ELLIPSE not in set(b.labels.tolist()) for b in batches)


# --- scoring ----------------------------------------------------------------

def test_macro_f1_leaves_out_excluded_classes():
    y = np.array([0, 0, 2, 2])
    p = np.array([0, 0, 2, 2])
    # Classes 0 and 2 are perfect; class 1 has no support and would pull the mean down.
    assert macro_f1_points(y, p, 3) == pytest.approx(200.0 / 3)
    assert macro_f1_points(y, p, 3, excluded=(1,)) == pytest.approx(100.0)


# --- the worker -------------------------------------------------------------

def _patched_job(monkeypatch, n_lost):
    seen = {}
    missing = (ELLIPSE,) if n_lost else ()
    images, labels, _ = _arrays(missing=missing)
    store = ImageStore(images, labels, np.full(labels.size, "quickdraw"), N_CLASSES)
    monkeypatch.setattr(sweep, "load_config", lambda path: _config("cpu"))
    monkeypatch.setattr(sweep, "threadpool_limits", lambda n: None)
    monkeypatch.setattr(sweep, "recipe_fingerprint", lambda cfg: "r")
    monkeypatch.setattr(sweep, "completed_run", lambda *a: None)
    monkeypatch.setattr(sweep, "load_stores", lambda cfg, holdout: (store, store, np.array([])))
    monkeypatch.setattr(sweep, "build_transform", lambda cfg: None)
    monkeypatch.setattr(sweep, "build_generator", lambda cfg: None)

    def fake_train(*args, **kwargs):
        seen.update(kwargs)
        return {}
    monkeypatch.setattr(sweep, "train_one", fake_train)
    return seen


def _spec(holdout):
    return {"run_name": "x", "arm": "A1", "seed": 0, "holdout_source": holdout,
            "hparams": {"lr": 0.001, "dropout": 0.2}, "steps_per_epoch": 1,
            "config_path": "unused", "out_dir": "unused"}


def test_held_out_run_excludes_the_lost_class(monkeypatch):
    seen = _patched_job(monkeypatch, n_lost=1)
    sweep.run_job(_spec("github_handdrawn"))
    assert seen["excluded_classes"] == (ELLIPSE,)


def test_ordinary_run_never_excludes_an_empty_class(monkeypatch):
    """An empty class in a normal run must keep failing, not be skipped."""
    seen = _patched_job(monkeypatch, n_lost=1)
    sweep.run_job(_spec(None))
    assert seen["excluded_classes"] == ()


# --- real GPU ---------------------------------------------------------------

def _toy_store(n, seed):
    rng = np.random.default_rng(seed)
    labels = np.arange(n, dtype=np.int64) % 3
    images = np.full((n, 64, 64), 255, dtype=np.uint8)
    for i, label in enumerate(labels):
        row = int(rng.integers(10, 50))
        if label == 0:
            images[i, row:row + 4, :] = 0
        elif label == 1:
            images[i, :, row:row + 4] = 0
    return ImageStore(images, labels, np.full(n, "quickdraw"), 3)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs a CUDA GPU")
def test_cuda_run_saves_a_cpu_model(tmp_path):
    cfg = _config("cuda")
    cfg["train"].update({"max_epochs": 1, "batch_size": 16, "steps_per_epoch": 2,
                         "num_threads": 1, "parallel_runs": 1})
    cfg["taxonomy"] = copy.deepcopy(cfg["taxonomy"])
    cfg["taxonomy"]["classes"] = {i: f"c{i}" for i in range(3)}
    out = train_one("toy", "A0", 0, cfg, _toy_store(32, 0), _toy_store(12, 1), None, None,
                    {"lr": 0.001, "dropout": 0.2}, tmp_path, steps_per_epoch=2,
                    val_image_ids=np.array([str(i) for i in range(12)]))
    assert out["device"] == "cuda"
    assert out["excluded_classes"] == []
    model = torch.jit.load(tmp_path / MODEL_FILE)
    assert {p.device.type for p in model.parameters()} == {"cpu"}


# --- seed disagreement with held-out runs ------------------------------------

def test_sweep_results_mark_held_out_runs_so_disagreement_skips_them(tmp_path):
    """Held-out runs have a smaller validation set and must not be compared."""
    cfg = _config("cpu")
    cfg["train"]["parallel_runs"] = 1
    cfg["runs"] = [{"arm": "A1", "seed": 0}, {"arm": "A1", "seed": 1}]
    sizes = {"A1_0": 20, "A1_1": 20, "A1_loso_handdrawn_0": 7, "B_loso_handdrawn_0": 7}

    def fake_job(spec):
        out = tmp_path / spec["run_name"]
        out.mkdir()
        np.savez(out / VAL_PROBS_FILE, probs=np.eye(N_CLASSES)[np.zeros(sizes[spec["run_name"]],
                                                                        dtype=np.int64)])
        return {"run_name": spec["run_name"], "arm": spec["arm"], "seed": spec["seed"]}

    results = sweep.run_sweep(cfg, 1, {"lr": 0.001, "dropout": 0.2}, True, out_dir=tmp_path,
                              job_runner=fake_job)
    held_out = {r["run_name"]: r["holdout_source"] for r in results}
    assert held_out == {"A1_0": None, "A1_1": None,
                        "A1_loso_handdrawn_0": "github_handdrawn",
                        "B_loso_handdrawn_0": "github_handdrawn"}
    out = sweep.seed_disagreement(tmp_path, results)
    assert out["per_arm"]["A1"]["runs"] == ["A1_0", "A1_1"]
    assert "B" not in out["per_arm"]
