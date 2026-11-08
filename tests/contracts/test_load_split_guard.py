"""E14: test-split guard + append-only access log (stages/stage_0.md R8, D4).

All manifests here are temporary fixtures; the real configs/splits/test.csv
is never read.
"""

import sys
import types

import pytest

from src.common import splits

HEADER = "image_id,md5,label_id,source_id,phash_group,split\n"


@pytest.fixture()
def env(tmp_path, monkeypatch):
    sdir = tmp_path / "splits"
    sdir.mkdir()
    for name, n in (("train", 3), ("val", 2), ("test", 2)):
        rows = "".join(f"{name}_{i},m{name}{i},0,src,g{name}{i},{name}\n" for i in range(n))
        (sdir / f"{name}.csv").write_text(HEADER + rows, encoding="utf-8")
    log = tmp_path / "test_access.log"
    monkeypatch.setenv("SHAPESENSE_RUN_ID", "run-A")
    return sdir, log


def _stage5_module():
    """A module object living under src.stage5_eval, used as a caller."""
    mod = types.ModuleType("src.stage5_eval._fake_reader")
    exec("from src.common.splits import load_split\n"
         "def read(**kw):\n    return load_split('test', **kw)\n", mod.__dict__)
    sys.modules[mod.__name__] = mod
    return mod


def test_train_read_allowed_anywhere(env):
    sdir, log = env
    rows = splits.load_split("train", splits_dir=sdir, log_path=log)
    assert len(rows) == 3 and rows[0]["image_id"] == "train_0"
    assert not log.exists()  # only test reads are logged


def test_test_read_blocked_outside_stage5(env):
    sdir, log = env
    with pytest.raises(splits.TestSplitAccessError):
        splits.load_split("test", splits_dir=sdir, log_path=log)
    assert not log.exists()


def test_test_read_allowed_from_stage5_module(env):
    sdir, log = env
    rows = _stage5_module().read(splits_dir=sdir, log_path=log)
    assert len(rows) == 2
    line = log.read_text(encoding="utf-8").strip().split(",")
    assert line[1] == "run-A"
    assert line[2] == "src.stage5_eval._fake_reader"
    assert line[3:] == ["test", "2"]


def test_each_test_read_appends_one_line(env):
    sdir, log = env
    mod = _stage5_module()
    for _ in range(3):
        mod.read(splits_dir=sdir, log_path=log)
    assert len(log.read_text(encoding="utf-8").splitlines()) == 3


def test_log_never_truncated(env, monkeypatch):
    sdir, log = env
    log.write_text("2026-01-01T00:00:00,old-run,src.stage5_eval.run,test,9\n",
                   encoding="utf-8")
    _stage5_module().read(splits_dir=sdir, log_path=log)
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and "old-run" in lines[0]


def test_count_scoped_to_run_id(env, monkeypatch):
    sdir, log = env
    mod = _stage5_module()
    mod.read(splits_dir=sdir, log_path=log)
    monkeypatch.setenv("SHAPESENSE_RUN_ID", "run-B")
    mod.read(splits_dir=sdir, log_path=log)
    mod.read(splits_dir=sdir, log_path=log)
    assert splits.count_test_reads("run-A", log_path=log) == 1
    assert splits.count_test_reads("run-B", log_path=log) == 2
    assert splits.count_test_reads("run-C", log_path=log) == 0


def test_unknown_split_name_rejected(env):
    sdir, log = env
    with pytest.raises(ValueError, match="unknown split"):
        splits.load_split("holdout", splits_dir=sdir, log_path=log)


def test_missing_manifest_says_run_stage1(tmp_path):
    with pytest.raises(FileNotFoundError, match="Stage 1"):
        splits.load_split("train", splits_dir=tmp_path, log_path=tmp_path / "l.log")


def test_main_module_in_stage5_dir_allowed(env):
    """`python -m src.stage5_eval.run` has __name__ == "__main__"; the guard
    must still recognise the file as Stage 5."""
    from pathlib import Path
    sdir, log = env
    stage5_file = Path(splits.__file__).resolve().parents[1] / "stage5_eval" / "run.py"
    mod = types.ModuleType("__main__fake")
    mod.__dict__["__name__"] = "__main__"
    mod.__dict__["__file__"] = str(stage5_file)
    exec("from src.common.splits import load_split\n"
         "def read(**kw):\n    return load_split('test', **kw)\n", mod.__dict__)
    assert len(mod.read(splits_dir=sdir, log_path=log)) == 2


def test_main_module_elsewhere_blocked(env, tmp_path):
    sdir, log = env
    mod = types.ModuleType("__main__fake2")
    mod.__dict__["__name__"] = "__main__"
    mod.__dict__["__file__"] = str(tmp_path / "evil.py")
    exec("from src.common.splits import load_split\n"
         "def read(**kw):\n    return load_split('test', **kw)\n", mod.__dict__)
    with pytest.raises(splits.TestSplitAccessError):
        mod.read(splits_dir=sdir, log_path=log)
