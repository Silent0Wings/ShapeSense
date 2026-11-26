"""The dataset-awareness CLI runner: same prompt for both models, no tools, never overwrites a record."""
import datetime as dt
import subprocess

import pytest

from scripts import llm_check as lc


def test_both_models_get_the_same_prompt_file():
    prompt = lc.PROMPT_FILE.read_text(encoding="utf-8")
    for model in lc.MODELS.values():
        assert model.command(prompt)[2] == prompt
    for tag in ("1A", "1B", "1C", "1D", "2A", "2B", "2C", "2D"):
        assert f"### Prompt {tag}" in prompt


def test_claude_runs_with_no_tools_and_no_settings():
    cmd = lc.MODELS["claude"].command("p")
    assert cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--setting-sources") + 1] == ""
    assert "--strict-mcp-config" in cmd and cmd[cmd.index("--model") + 1] == "claude-opus-5-5"


def test_gemini_runs_sandboxed_in_a_new_project():
    cmd = lc.MODELS["gemini"].command("p")
    assert {"--sandbox", "--new-project"} <= set(cmd)
    assert cmd[cmd.index("--model") + 1] == "gemini-4-neon-medium"


def test_shown_command_hides_the_prompt_and_quotes_empty_values():
    shown = lc.shown_command(lc.MODELS["claude"].command("long prompt text"))
    assert "long prompt text" not in shown and "<cli_prompt.txt>" in shown and '--tools ""' in shown
    full_path = lc.shown_command([r"C:\Users\someone\bin\agy.EXE", "-p", "x", "--sandbox"])
    assert full_path == "agy -p <cli_prompt.txt> --sandbox"


def test_next_number_follows_the_highest_prefix(tmp_path):
    for name in ("00_a.md", "02_b.md", "notes.md"):
        (tmp_path / name).write_text("x")
    assert lc.next_number(tmp_path) == 3
    (tmp_path / "empty").mkdir()
    assert lc.next_number(tmp_path / "empty") == 1


def test_record_states_the_run_and_is_not_counted():
    text = lc.record(lc.MODELS["gemini"], ["agy", "-p", "P", "--sandbox"], "1.5.13",
                     dt.datetime(2026, 11, 26, 12, 0, tzinfo=dt.timezone.utc), 42.0, 0, "Model: X\nanswer",
                     "", "abc", True)
    assert "Exit code: 0." in text and "empty after the call: yes" in text
    assert "SHA-256 `abc`" in text and "Model: X\nanswer" in text and "Not counted" in text


def test_dry_run_calls_no_cli(monkeypatch, capsys):
    def boom(*a, **k):
        raise AssertionError("a CLI was called in a dry run")
    monkeypatch.setattr(subprocess, "run", boom)
    assert lc.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "[claude]" in out and "[gemini]" in out


def test_unknown_model_is_rejected():
    with pytest.raises(SystemExit):
        lc.main(["--models", "gpt", "--dry-run"])
