"""The direct-classification CLI runner: blind CSV in, checked labels out, scored on the same images."""
import subprocess

import pytest

from scripts import llm_classify as lc


def test_batches_cover_the_200_images_in_blind_order():
    batches = lc.load_batches()
    assert list(batches) == [f"batch_{i:02d}" for i in range(1, 11)]
    assert all(len(rows) == 20 for rows in batches.values())


def test_blank_csv_holds_blind_ids_and_no_truth():
    rows = lc.load_batches()["batch_01"]
    text = lc.blank_csv(rows)
    assert text.splitlines()[0] == "blind_id,predicted_label"
    assert text.splitlines()[1] == "T001,"
    for r in rows:
        assert r["true_label"] not in text and r["image_id"] not in text


def test_prompt_names_the_batch_and_its_range():
    rows = lc.load_batches()["batch_02"]
    prompt = lc.render_prompt(lc.PROMPT_FILE.read_text(encoding="utf-8"), "batch_02", rows)
    assert "batch_02.png" in prompt and "T021" in prompt and "T040" in prompt and "{" not in prompt


def test_parse_accepts_a_clean_fill():
    answers, issues = lc.parse_filled("blind_id,predicted_label\nT001,Pentagon\nT002, circle\n", ["T001", "T002"])
    assert answers == {"T001": "pentagon", "T002": "circle"} and issues == []


def test_parse_reports_bad_labels_missing_rows_and_duplicates():
    text = "blind_id,predicted_label\nT001,blob\nT001,circle\nT009,star\n"
    answers, issues = lc.parse_filled(text, ["T001", "T002"])
    assert answers == {"T001": "circle"}
    joined = "; ".join(issues)
    assert "invalid label 'blob'" in joined and "unexpected row 'T009'" in joined and "no valid label for T002" in joined


def test_parse_reports_a_changed_header():
    _, issues = lc.parse_filled("id,label\nT001,circle\n", ["T001"])
    assert any("header changed" in i for i in issues)


def test_missing_answers_count_as_wrong():
    rows = lc.load_batches()["batch_01"]
    perfect = lc.score(rows, {r["blind_id"]: r["true_label"] for r in rows})
    assert perfect["correct"] == 20 and perfect["macro_f1"] == 100.0
    half = lc.score(rows, {r["blind_id"]: r["true_label"] for r in rows[:10]})
    assert half["answered"] == 10 and half["correct"] == 10


def test_recorded_cnn_scores_match_the_summary():
    rows = [r for b in lc.load_batches().values() for r in b]
    assert lc.recorded_score("trained_cnn_predictions.csv", rows)["macro_f1"] == 97.5


def test_claude_can_only_read_and_edit_files():
    cmd = lc.MODELS["claude"].command("p")
    assert cmd[cmd.index("--tools") + 1] == "Read,Edit,Write"
    assert cmd[cmd.index("--setting-sources") + 1] == ""


def test_dry_run_calls_no_cli(monkeypatch, capsys):
    def boom(*a, **k):
        raise AssertionError("a CLI was called in a dry run")
    monkeypatch.setattr(subprocess, "run", boom)
    assert lc.main(["--dry-run", "--batches", "1"]) == 0
    assert "[gemini]" in capsys.readouterr().out


def test_unknown_batch_is_rejected():
    with pytest.raises(SystemExit):
        lc.main(["--batches", "11", "--dry-run"])
