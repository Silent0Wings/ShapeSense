"""check_fds / discover_fds read metadata.csv from the config, not a hard-coded path."""

import csv

from src.stage1_freeze import check_fds, discover_fds

COLUMNS = ("image_id", "source_id", "domain", "license", "original_label", "label_id",
           "label_name", "split", "native_width", "native_height", "native_mode",
           "outline_redrawn", "path", "phash")


def _metadata(tmp_path):
    p = tmp_path / "elsewhere" / "metadata.csv"
    p.parent.mkdir(parents=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(COLUMNS), lineterminator="\n")
        w.writeheader()
        for i in range(3):
            w.writerow({"image_id": f"s_circle_{i:06d}", "source_id": "s", "domain": "sketch",
                        "license": "CC0", "original_label": "circle", "label_id": 0,
                        "label_name": "circle", "split": "train", "native_width": 28,
                        "native_height": 28, "native_mode": "L", "outline_redrawn": "False",
                        "path": f"train/circle/{i}.png", "phash": f"{i:016x}"})
    return p


def test_check_fds_main_reads_config_metadata(tmp_path, monkeypatch, capsys):
    meta = _metadata(tmp_path)
    monkeypatch.setattr(check_fds, "load_default_config",
                        lambda: {"paths": {"metadata": str(meta)}})
    check_fds.main()
    out = capsys.readouterr().out
    assert out.startswith("Rows: 3")
    assert "source_id -> domain: 1 groups, HOLDS" in out


def test_discover_fds_main_reads_config_metadata(tmp_path, monkeypatch, capsys):
    meta = _metadata(tmp_path)
    monkeypatch.setattr(discover_fds, "load_default_config",
                        lambda: {"paths": {"metadata": str(meta)}})
    discover_fds.main()
    assert capsys.readouterr().out.startswith("Rows: 3")
