"""E26: in-memory ImageStore — never the test split (stage_4.md R8),
leave-one-source-out filtering (Decision 12), class index coverage."""

import numpy as np
import pytest

from src.stage4_train.benchmark import benchmark, est_all_runs_s, est_run_s
from src.stage4_train.data import ImageStore, to_float

N_CLASSES = 10
SIZE = 16
CONFIG = {"taxonomy": {"classes": {i: f"c{i}" for i in range(N_CLASSES)}}}


def _fake_split(n_per_class=5, seed=0):
    rng = np.random.default_rng(seed)
    labels = np.repeat(np.arange(N_CLASSES, dtype=np.int64), n_per_class)
    images = rng.integers(0, 256, size=(labels.size, SIZE, SIZE), dtype=np.uint8)
    sources = np.where(np.arange(labels.size) % 3 == 0, "hand_drawn", "quickdraw")
    rows = [{"image_id": str(i), "md5": "x", "label_id": str(l), "source_id": s,
             "phash_group": "g", "split": "train"}
            for i, (l, s) in enumerate(zip(labels, sources))]
    return images, labels, rows


def _loaders(images, labels, rows, seen):
    def loader(config, split, rows=None):
        seen.append(split)
        return images, labels

    def rows_loader(config, split):
        return rows
    return loader, rows_loader


def test_store_refuses_test_split():
    images, labels, rows = _fake_split()
    seen = []
    loader, rows_loader = _loaders(images, labels, rows, seen)
    with pytest.raises(ValueError, match="test"):
        ImageStore.from_split(CONFIG, "test", loader=loader, rows_loader=rows_loader)
    assert seen == []  # refused before any loader ran
    for bad in ("Test", "all", ""):
        with pytest.raises(ValueError):
            ImageStore.from_split(CONFIG, bad, loader=loader, rows_loader=rows_loader)


def test_store_loads_train_and_val():
    images, labels, rows = _fake_split()
    seen = []
    loader, rows_loader = _loaders(images, labels, rows, seen)
    for split in ("train", "val"):
        store = ImageStore.from_split(CONFIG, split, loader=loader, rows_loader=rows_loader)
        assert len(store) == labels.size
        assert store.images.dtype == np.uint8 and store.images.shape == (labels.size, SIZE, SIZE)
        assert store.labels.dtype == np.int64
        assert store.source_ids.shape == (labels.size,)
        assert store.n_classes == N_CLASSES
    assert seen == ["train", "val"]


def test_store_rejects_row_count_mismatch():
    images, labels, rows = _fake_split()
    loader, rows_loader = _loaders(images, labels, rows[:-1], [])
    with pytest.raises(ValueError, match="manifest rows"):
        ImageStore.from_split(CONFIG, "train", loader=loader, rows_loader=rows_loader)


def test_filter_out_source():
    images, labels, rows = _fake_split()
    store = ImageStore(images, labels, [r["source_id"] for r in rows], N_CLASSES)
    n_hand = int((store.source_ids == "hand_drawn").sum())
    assert n_hand > 0
    sub = store.filter_out_source("hand_drawn")
    assert len(sub) == len(store) - n_hand
    assert not (sub.source_ids == "hand_drawn").any()
    assert (sub.source_ids == "quickdraw").all()
    keep = store.source_ids != "hand_drawn"
    assert np.array_equal(sub.images, images[keep])
    assert np.array_equal(sub.labels, labels[keep])
    assert len(store) == labels.size  # original untouched
    assert sum(len(ix) for ix in sub.class_idx) == len(sub)


def test_class_index_covers_all():
    images, labels, rows = _fake_split()
    store = ImageStore(images, labels, [r["source_id"] for r in rows], N_CLASSES)
    assert len(store.class_idx) == N_CLASSES
    allidx = np.sort(np.concatenate(store.class_idx))
    assert np.array_equal(allidx, np.arange(len(store)))
    for c, ix in enumerate(store.class_idx):
        assert (store.labels[ix] == c).all()
    assert np.array_equal(store.class_counts(), np.full(N_CLASSES, 5))


def test_to_float_shape_range():
    images, _, _ = _fake_split()
    f = to_float(images)
    assert f.shape == (images.shape[0], 1, SIZE, SIZE)
    assert f.dtype == np.float32
    assert f.min() >= 0.0 and f.max() <= 1.0
    assert np.isclose(f[0, 0, 0, 0], images[0, 0, 0] / 255.0)


def test_benchmark_reports_throughput_and_estimates():
    images, labels, rows = _fake_split()
    store = ImageStore(images, labels, [r["source_id"] for r in rows], N_CLASSES)
    arm_b = {"augment": True, "synthetic": True}
    steps = []
    res = benchmark(store, arm_b, batch_size=20, synthetic_fraction=0.3, n_classes=N_CLASSES,
                    n_batches=5, rng=np.random.default_rng(0),
                    transform=lambda img, l, rng: img,
                    generate=lambda l, rng: np.full((SIZE, SIZE), 255, np.uint8),
                    step_time_fn=lambda batch: steps.append(batch.labels.shape[0]))
    assert res["n_batches"] == 5 and res["batch_size"] == 20
    assert res["n_real"] == 14 and res["n_syn"] == 6
    assert steps == [20] * 5
    assert res["batches_per_s"] > 0 and res["images_per_s"] > 0
    assert res["mean_batch_ms"] >= 0 and "mean_step_ms" in res
    assert res["per_step_s"] >= 0
    with pytest.raises(ValueError, match="at least 100"):
        benchmark(store, arm_b, 20, 0.3, N_CLASSES, 5, np.random.default_rng(0),
                  transform=lambda img, l, rng: img,
                  generate=lambda l, rng: np.full((SIZE, SIZE), 255, np.uint8),
                  min_batches=100)
    assert est_run_s(50, 30, 0.5) == pytest.approx(750.0)
    assert est_all_runs_s(23, 50, 30, 0.5) == pytest.approx(23 * 750.0)


def test_store_reads_manifest_once(monkeypatch):
    """Images and source ids come from one read of the manifest."""
    import src.common.catalog as catalog

    images, _, rows = _fake_split()
    reads = []

    def counting_rows(config, split):
        reads.append(split)
        return rows
    monkeypatch.setattr(catalog, "load_split_rows", counting_rows)
    monkeypatch.setattr(catalog, "load_images", lambda config, ids: images[[int(i) for i in ids]])
    store = ImageStore.from_split(CONFIG, "train")
    assert reads == ["train"]
    assert store.source_ids.tolist() == [r["source_id"] for r in rows]
