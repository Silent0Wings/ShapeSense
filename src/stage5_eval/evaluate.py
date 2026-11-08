"""One test read per evaluated model, cached predictions, ensembles from cache
(stages/stage_5.md R1, R4; implementation.md § Separation of concerns 2).

``evaluate_models`` is the only place in the pipeline that touches the test
split. It calls the injected ``test_reader`` exactly once per model that is
not already served from ``artifacts/stage5/predictions/<name>.npz``; the
reader itself goes through ``common.load_split`` and therefore appends one
line to the access log per call. Ensembles are formed from the cached
per-seed probabilities and never trigger another read.

Model loading is by file only (TorchScript / joblib), never by importing
Stage 4.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from src.common.catalog import connect_readonly, load_split_images, load_split_rows
from src.common.config import resolve
from src.common.features import PIXEL_SCALE, hog_features, pixel_features
from src.common.hashing import sha256_path
from src.stage5_eval.metrics import soft_vote

KIND_CNN = "cnn"  # TorchScript model.pt with softmax probabilities
KIND_BASELINE = "baseline"  # joblib estimator with hard labels only
FEATURE_PIXELS = "pixels"
FEATURE_HOG = "hog"
PREDICT_BATCH = 1024  # images per TorchScript forward pass
CACHE_HASH_KEY = "model_hash"  # npz key carrying the model file hash
CACHE_MANIFEST_KEY = "manifest_hash"  # npz key carrying the test manifest (test.csv) hash
TEST_MANIFEST_FILE = "test.csv"  # under paths.splits_dir
EMPTY_PROBS_SHAPE = (0, 0)  # stored when a model yields labels only

# A predictor maps uint8 (N, S, S) images to (probs or None, predicted labels).
PredictFn = Callable[[np.ndarray], tuple[np.ndarray | None, np.ndarray]]
# A test reader returns (manifest rows, uint8 images, int64 labels).
TestReader = Callable[[], tuple[list[dict], np.ndarray, np.ndarray]]


@dataclass(frozen=True)
class ModelSpec:
    """One model to evaluate once on the test split.

    ``fingerprint`` is the content hash of the model file; a cached
    prediction file is reused only when its stored hash matches.
    ``source_filter`` restricts evaluation to test rows of one source_id
    (the leave-one-source-out models, R10).
    """

    name: str
    kind: str
    path: Path
    fingerprint: str
    features: str | None = None
    hog_pixels_per_cell: int | None = None
    source_filter: str | None = None
    extra: dict = field(default_factory=dict)


def model_fingerprint(path: str | Path) -> str:
    return sha256_path(path)


def test_manifest_hash(config: dict) -> str:
    """Content hash of ``configs/splits/test.csv``.

    Fingerprinting the file bytes with ``sha256_path`` is not a split read:
    it does not go through ``load_split`` and writes no access-log line. A
    cached prediction is only valid for the manifest it was made from.
    """
    return sha256_path(resolve(config["paths"]["splits_dir"]) / TEST_MANIFEST_FILE)


# --------------------------------------------------------------------------- #
# Predictors (file-based; no Stage 4 import)
# --------------------------------------------------------------------------- #


def predict_torchscript(model_path: str | Path, images_u8: np.ndarray,
                        batch: int = PREDICT_BATCH) -> np.ndarray:
    """Softmax probabilities, float32 (N, k), from a TorchScript classifier.

    Input contract (Stage 4): float32 (N, 1, S, S) = uint8 / 255; output
    logits (N, k).
    """
    import torch  # heavy import kept local so pure callers never pay for it

    model = torch.jit.load(str(model_path), map_location="cpu")
    model.eval()
    n = images_u8.shape[0]
    out: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, n, batch):
            chunk = images_u8[start:start + batch].astype(np.float32) / np.float32(PIXEL_SCALE)
            x = torch.from_numpy(chunk[:, None, :, :])
            logits = model(x)
            out.append(torch.softmax(logits, dim=1).cpu().numpy().astype(np.float32))
    if not out:
        return np.empty((0, 0), dtype=np.float32)
    return np.concatenate(out, axis=0)


def predict_baseline(model: Any, features_kind: str, images_u8: np.ndarray,
                     hog_pixels_per_cell: int | None) -> np.ndarray:
    """Predicted int64 labels of a saved scikit-learn baseline."""
    if features_kind == FEATURE_PIXELS:
        feats = pixel_features(images_u8)
    elif features_kind == FEATURE_HOG:
        if hog_pixels_per_cell is None:
            raise ValueError("hog_pixels_per_cell is required for HOG features")
        feats = hog_features(images_u8, int(hog_pixels_per_cell))
    else:
        raise ValueError(f"unknown features kind {features_kind!r}")
    return np.asarray(model.predict(feats)).astype(np.int64)


def default_predictor(spec: ModelSpec) -> PredictFn:
    """Build the predictor for a spec from its model file."""
    if spec.kind == KIND_CNN:
        def _cnn(images_u8: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            probs = predict_torchscript(spec.path, images_u8)
            return probs, probs.argmax(axis=1).astype(np.int64)
        return _cnn
    if spec.kind == KIND_BASELINE:
        import joblib

        model = joblib.load(Path(spec.path))

        def _baseline(images_u8: np.ndarray) -> tuple[None, np.ndarray]:
            return None, predict_baseline(model, spec.features or FEATURE_PIXELS, images_u8,
                                          spec.hog_pixels_per_cell)
        return _baseline
    raise ValueError(f"unknown model kind {spec.kind!r}")


# --------------------------------------------------------------------------- #
# Data access
# --------------------------------------------------------------------------- #


def default_test_reader(config: dict) -> TestReader:
    """A reader that performs exactly ONE logged test read per call.

    ``load_split_rows`` goes through the guard (one access-log line) and
    ``load_split_images(..., rows=rows)`` reuses those rows, so no second
    line is written.
    """
    def _read() -> tuple[list[dict], np.ndarray, np.ndarray]:
        rows = load_split_rows(config, "test")
        images, labels = load_split_images(config, "test", rows=rows)
        return rows, images, labels
    return _read


def load_source_domains(config: dict) -> dict[str, str]:
    """source_id -> domain ("render" / "sketch") from the catalog's Source table."""
    con = connect_readonly(resolve(config["paths"]["catalog"]))
    try:
        return {str(s): str(d) for s, d in con.execute("SELECT source_id, domain FROM Source")}
    except sqlite3.OperationalError:
        return {}
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# Prediction cache
# --------------------------------------------------------------------------- #


def cache_path(predictions_dir: str | Path, name: str) -> Path:
    return Path(predictions_dir) / f"{name}.npz"


def save_predictions(path: Path, *, probs: np.ndarray | None, preds: np.ndarray,
                     labels: np.ndarray, image_ids: np.ndarray, source_ids: np.ndarray,
                     model_hash: str, manifest_hash: str) -> None:
    """Write one prediction cache file keyed on BOTH the model and the manifest hash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        probs=(np.asarray(probs, dtype=np.float32) if probs is not None
               else np.empty(EMPTY_PROBS_SHAPE, dtype=np.float32)),
        preds=np.asarray(preds, dtype=np.int64),
        labels=np.asarray(labels, dtype=np.int64),
        image_ids=np.asarray(image_ids).astype(str),
        source_ids=np.asarray(source_ids).astype(str),
        **{CACHE_HASH_KEY: np.asarray(model_hash), CACHE_MANIFEST_KEY: np.asarray(manifest_hash)},
    )


def load_predictions(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as z:
        probs = z["probs"]
        return {
            "probs": None if probs.size == 0 else probs,
            "preds": z["preds"].astype(np.int64),
            "labels": z["labels"].astype(np.int64),
            "image_ids": z["image_ids"].astype(str),
            "source_ids": z["source_ids"].astype(str),
            CACHE_HASH_KEY: str(z[CACHE_HASH_KEY]),
            CACHE_MANIFEST_KEY: str(z[CACHE_MANIFEST_KEY]),
        }


def cached_for(path: Path, fingerprint: str, manifest_hash: str) -> dict | None:
    """The cached predictions if the file exists and was made by this model file
    on this test manifest. A cache written before the manifest key existed has
    no ``manifest_hash`` entry and is treated as stale (KeyError -> None).
    """
    if not path.is_file():
        return None
    try:
        rec = load_predictions(path)
    except (OSError, KeyError, ValueError):
        return None
    if rec[CACHE_HASH_KEY] != fingerprint or rec[CACHE_MANIFEST_KEY] != manifest_hash:
        return None
    return rec


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #


def _rows_arrays(rows: Sequence[Mapping[str, str]]) -> tuple[np.ndarray, np.ndarray]:
    image_ids = np.asarray([str(r["image_id"]) for r in rows]).astype(str)
    source_ids = np.asarray([str(r["source_id"]) for r in rows]).astype(str)
    return image_ids, source_ids


def evaluate_models(
    config: dict,
    model_specs: Sequence[ModelSpec],
    test_reader: TestReader,
    predictions_dir: str | Path,
    predictors: Mapping[str, PredictFn] | None = None,
    manifest_hash: str | None = None,
) -> dict:
    """Evaluate every spec once on the test split; serve repeats from cache.

    For each spec, in order: if ``predictions_dir/<name>.npz`` exists with
    the spec's fingerprint AND the current test-manifest hash, it is loaded
    and ``test_reader`` is **not** called. Otherwise ``test_reader()`` is
    called exactly once, the model predicts, and the result is cached.
    ``predictors`` overrides the file-based predictor per model name (tests
    inject fakes here). ``manifest_hash`` defaults to
    ``test_manifest_hash(config)``; tests pass a literal.

    Returns:
        ``{"models": {name: record}, "n_reads": int, "images": uint8 array
        or None, "image_ids": ids of the full test split or None}``. Each
        record has ``probs`` (or None), ``preds``, ``labels``,
        ``image_ids``, ``source_ids``, ``from_cache`` and ``path``.
        ``images`` are the test images of the last fresh read (all reads
        return the same split, verified by image id), kept so the error
        galleries need no extra read.
    """
    predictors = dict(predictors or {})
    if manifest_hash is None:
        manifest_hash = test_manifest_hash(config)
    results: dict[str, dict] = {}
    n_reads = 0
    last_images: np.ndarray | None = None
    last_ids: np.ndarray | None = None
    last_labels: np.ndarray | None = None
    last_sources: np.ndarray | None = None
    for spec in model_specs:
        path = cache_path(predictions_dir, spec.name)
        cached = cached_for(path, spec.fingerprint, manifest_hash)
        if cached is not None:
            results[spec.name] = {**cached, "from_cache": True, "path": path}
            continue
        rows, images, labels = test_reader()
        n_reads += 1
        image_ids, source_ids = _rows_arrays(rows)
        images = np.asarray(images)
        labels = np.asarray(labels, dtype=np.int64)
        if not (images.shape[0] == labels.shape[0] == image_ids.shape[0]):
            raise ValueError("test reader returned rows, images and labels of different length")
        if last_ids is not None and not np.array_equal(image_ids, last_ids):
            raise ValueError("test reader returned a different image order between models")
        last_images, last_ids, last_labels, last_sources = images, image_ids, labels, source_ids

        if spec.source_filter is not None:
            mask = source_ids == spec.source_filter
            images, labels = images[mask], labels[mask]
            image_ids, source_ids = image_ids[mask], source_ids[mask]
        predict = predictors.get(spec.name) or default_predictor(spec)
        probs, preds = predict(images)
        preds = np.asarray(preds, dtype=np.int64)
        if preds.shape != labels.shape:
            raise ValueError(f"{spec.name}: predictor returned {preds.shape}, expected {labels.shape}")
        save_predictions(path, probs=probs, preds=preds, labels=labels, image_ids=image_ids,
                         source_ids=source_ids, model_hash=spec.fingerprint,
                         manifest_hash=manifest_hash)
        results[spec.name] = {
            "probs": None if probs is None else np.asarray(probs, dtype=np.float32),
            "preds": preds, "labels": labels, "image_ids": image_ids,
            "source_ids": source_ids, "from_cache": False, "path": path,
        }
    return {"models": results, "n_reads": n_reads, "images": last_images,
            "image_ids": last_ids, "labels": last_labels, "source_ids": last_sources}


def check_alignment(records: Mapping[str, dict],
                    reference_ids: np.ndarray | None = None) -> np.ndarray:
    """Assert that every full-split record lists the same image ids in the same order.

    Paired statistics (bootstrap, McNemar, per-seed differences) index the
    arrays row by row, so a cached record made on another manifest or in
    another order would silently pair the wrong images. ``records`` maps
    name -> record (``image_ids`` key); ``reference_ids`` are the ids of the
    fresh read when one happened. Raises ``ValueError`` naming the offending
    record; returns the common id array.
    """
    ref: np.ndarray | None = None if reference_ids is None else np.asarray(reference_ids).astype(str)
    ref_name = "fresh test read"
    for name, rec in records.items():
        ids = np.asarray(rec["image_ids"]).astype(str)
        if ref is None:
            ref, ref_name = ids, name
            continue
        if ids.shape != ref.shape or not np.array_equal(ids, ref):
            raise ValueError(
                f"prediction records are misaligned: {name!r} lists different image ids "
                f"(or another order) than {ref_name!r}; stale cache? delete "
                f"artifacts/stage5/predictions and rerun Stage 5")
    if ref is None:
        raise ValueError("check_alignment needs at least one record")
    return ref


def ensemble(records: Sequence[dict]) -> dict:
    """Soft-vote ensemble of cached per-seed records (no test read).

    Every record must carry ``probs`` and list the same image ids in the
    same order. Returns a record-shaped dict with ``probs``, ``preds``,
    ``labels``, ``image_ids`` and ``source_ids``.
    """
    if not records:
        raise ValueError("ensemble needs at least one record")
    ref = records[0]
    stack = []
    for rec in records:
        if rec["probs"] is None:
            raise ValueError("ensemble needs softmax probabilities for every member")
        if not np.array_equal(rec["image_ids"], ref["image_ids"]):
            raise ValueError("ensemble members list different image ids")
        stack.append(np.asarray(rec["probs"], dtype=np.float64))
    probs = soft_vote(np.stack(stack, axis=0))
    return {
        "probs": probs.astype(np.float32),
        "preds": probs.argmax(axis=1).astype(np.int64),
        "labels": np.asarray(ref["labels"], dtype=np.int64),
        "image_ids": np.asarray(ref["image_ids"]).astype(str),
        "source_ids": np.asarray(ref["source_ids"]).astype(str),
    }
