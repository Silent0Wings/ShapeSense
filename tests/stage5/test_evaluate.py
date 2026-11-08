"""E30: one test read per evaluated model, cache reuse, ensembles from cache,
power check before the first test read (stage_5.md R1, R4, R8).

Synthetic arrays and a fake reader only: the real test split is never read.
"""

import numpy as np
import pytest

from src.stage5_eval import evaluate
from src.stage5_eval.run import stage5_pipeline

K = 3
N = 40
S = 8  # tiny image side; the fake predictors ignore pixel content
MANIFEST = "manifest-v1"  # stands in for sha256_path(configs/splits/test.csv)
MANIFEST_CHANGED = "manifest-v2"


class CountingReader:
    """A test_reader stand-in that counts calls and returns the same split."""

    def __init__(self, rng: np.random.Generator) -> None:
        self.calls = 0
        self.labels = rng.integers(0, K, size=N).astype(np.int64)
        self.images = rng.integers(0, 256, size=(N, S, S)).astype(np.uint8)
        self.rows = [{"image_id": f"img_{i:03d}", "source_id": "src_a" if i % 2 else "src_b"}
                     for i in range(N)]

    def __call__(self):
        self.calls += 1
        return self.rows, self.images, self.labels


def _fake_predictor(seed: int, labels: np.ndarray):
    """Predicts the truth except on a seed-specific stripe; returns probs + preds."""
    def _predict(images_u8: np.ndarray):
        n = images_u8.shape[0]
        preds = labels[:n].copy()
        preds[seed::5] = (preds[seed::5] + 1) % K
        probs = np.full((n, K), 0.1, dtype=np.float32)
        probs[np.arange(n), preds] = 0.8
        return probs, preds
    return _predict


def _specs(tmp_path, names):
    specs = []
    for i, name in enumerate(names):
        p = tmp_path / f"{name}.pt"
        p.write_bytes(f"fake model {i}".encode("utf-8"))
        specs.append(evaluate.ModelSpec(name=name, kind=evaluate.KIND_CNN, path=p,
                                        fingerprint=evaluate.model_fingerprint(p),
                                        extra={"arm": "A", "seed": i}))
    return specs


@pytest.fixture
def setup(tmp_path):
    rng = np.random.default_rng(0)
    reader = CountingReader(rng)
    names = ["A_0", "A_1", "A_2"]
    specs = _specs(tmp_path, names)
    predictors = {n: _fake_predictor(i, reader.labels) for i, n in enumerate(names)}
    return reader, specs, predictors, tmp_path / "predictions"


def _evaluate(specs, reader, pred_dir, predictors, manifest_hash=MANIFEST):
    return evaluate.evaluate_models({}, specs, reader, pred_dir, predictors=predictors,
                                    manifest_hash=manifest_hash)


def test_test_reader_called_once_per_model(setup):
    reader, specs, predictors, pred_dir = setup
    out = _evaluate(specs, reader, pred_dir, predictors)
    assert reader.calls == len(specs) == 3
    assert out["n_reads"] == 3
    for spec in specs:
        rec = out["models"][spec.name]
        assert rec["from_cache"] is False
        assert (pred_dir / f"{spec.name}.npz").is_file()
        assert rec["preds"].shape == (N,) and rec["probs"].shape == (N, K)
        assert np.array_equal(rec["labels"], reader.labels)
        assert rec["source_ids"][1] == "src_a"
    assert out["images"] is not None and out["images"].shape == (N, S, S)


def test_ensemble_does_not_reread(setup):
    reader, specs, predictors, pred_dir = setup
    out = _evaluate(specs, reader, pred_dir, predictors)
    calls_after_eval = reader.calls
    ens = evaluate.ensemble([out["models"][s.name] for s in specs])
    assert reader.calls == calls_after_eval == 3
    assert ens["preds"].shape == (N,) and ens["probs"].shape == (N, K)
    expected = np.mean([out["models"][s.name]["probs"] for s in specs], axis=0).argmax(axis=1)
    assert np.array_equal(ens["preds"], expected)


def test_cached_predictions_skip_reader(setup):
    reader, specs, predictors, pred_dir = setup
    first = _evaluate(specs, reader, pred_dir, predictors)
    assert reader.calls == 3
    second = _evaluate(specs, reader, pred_dir, predictors)
    assert reader.calls == 3, "a rerun with unchanged models must not reread the test split"
    assert second["n_reads"] == 0 and second["images"] is None
    for spec in specs:
        assert second["models"][spec.name]["from_cache"] is True
        assert np.array_equal(second["models"][spec.name]["preds"],
                              first["models"][spec.name]["preds"])
    # A changed model file invalidates only its own cache entry.
    specs[1].path.write_bytes(b"retrained")
    changed = evaluate.ModelSpec(name=specs[1].name, kind=specs[1].kind, path=specs[1].path,
                                 fingerprint=evaluate.model_fingerprint(specs[1].path),
                                 extra=specs[1].extra)
    third = _evaluate([specs[0], changed, specs[2]], reader, pred_dir, predictors)
    assert reader.calls == 4 and third["n_reads"] == 1
    assert third["models"][specs[1].name]["from_cache"] is False


def test_stale_cache_rejected_when_manifest_changes(setup):
    """A cache made on another test manifest must not be served (audit finding 1)."""
    reader, specs, predictors, pred_dir = setup
    _evaluate(specs, reader, pred_dir, predictors, manifest_hash=MANIFEST)
    assert reader.calls == 3
    # Same models, same manifest: fully cached.
    same = _evaluate(specs, reader, pred_dir, predictors, manifest_hash=MANIFEST)
    assert reader.calls == 3 and same["n_reads"] == 0
    # Same models, a re-frozen test split: every model must be re-evaluated.
    fresh = _evaluate(specs, reader, pred_dir, predictors, manifest_hash=MANIFEST_CHANGED)
    assert reader.calls == 6, "unchanged model files must not hide a changed test manifest"
    assert fresh["n_reads"] == 3
    assert all(not fresh["models"][s.name]["from_cache"] for s in specs)
    # The manifest hash is stored next to the model hash in every cache file.
    for spec in specs:
        rec = evaluate.load_predictions(evaluate.cache_path(pred_dir, spec.name))
        assert rec[evaluate.CACHE_HASH_KEY] == spec.fingerprint
        assert rec[evaluate.CACHE_MANIFEST_KEY] == MANIFEST_CHANGED
    # A pre-audit cache file without the manifest key is stale, not an error.
    legacy = evaluate.cache_path(pred_dir, specs[0].name)
    with np.load(legacy, allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files if k != evaluate.CACHE_MANIFEST_KEY}
    np.savez_compressed(legacy, **arrays)
    assert evaluate.cached_for(legacy, specs[0].fingerprint, MANIFEST_CHANGED) is None


def test_misaligned_arms_raise(setup):
    """Paired statistics need identical image_id arrays in every record."""
    reader, specs, predictors, pred_dir = setup
    out = _evaluate(specs, reader, pred_dir, predictors)
    records = {s.name: out["models"][s.name] for s in specs}
    ids = evaluate.check_alignment(records, reference_ids=out["image_ids"])
    assert np.array_equal(ids, out["image_ids"])

    # A permuted (stale) record for one model is rejected before any comparison.
    bad = dict(records[specs[1].name])
    bad["image_ids"] = bad["image_ids"][::-1].copy()
    with pytest.raises(ValueError, match="misaligned"):
        evaluate.check_alignment({**records, specs[1].name: bad},
                                 reference_ids=out["image_ids"])
    # A record that disagrees with the fresh read is rejected too.
    with pytest.raises(ValueError, match="misaligned"):
        evaluate.check_alignment(records, reference_ids=out["image_ids"][::-1])
    # A baseline with a different length is rejected (no silent broadcasting).
    short = dict(records[specs[0].name])
    short["image_ids"] = short["image_ids"][:-1]
    with pytest.raises(ValueError, match="misaligned"):
        evaluate.check_alignment({**records, "baseline_x": short})
    with pytest.raises(ValueError):
        evaluate.check_alignment({})


def test_source_filter_restricts_rows(setup):
    reader, specs, predictors, pred_dir = setup
    spec = evaluate.ModelSpec(name="A_loso", kind=evaluate.KIND_CNN, path=specs[0].path,
                              fingerprint=specs[0].fingerprint, source_filter="src_a",
                              extra={"arm": "A", "loso": True})
    out = _evaluate([spec], reader, pred_dir, {"A_loso": predictors["A_0"]})
    rec = out["models"]["A_loso"]
    assert reader.calls == 1
    assert set(rec["source_ids"].tolist()) == {"src_a"}
    assert rec["labels"].size == N // 2


def test_power_check_before_test_read():
    order: list[str] = []

    def power_fn():
        order.append("power")
        return {"underpowered": False}

    def evaluate_fn(power):
        assert power == {"underpowered": False}
        order.append("evaluate")
        return {"n_reads": 2}

    def analyse_fn(power, ev):
        order.append("analyse")
        return {"metrics": {"reads": ev["n_reads"]}}

    result = stage5_pipeline(power_fn, evaluate_fn, analyse_fn)
    assert order == ["power", "evaluate", "analyse"]
    assert order.index("power") < order.index("evaluate")
    assert result == {"metrics": {"reads": 2}}
