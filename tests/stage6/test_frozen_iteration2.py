"""Iteration 2's frozen record never changes."""

import hashlib
from pathlib import Path

FROZEN = Path(__file__).resolve().parents[2] / "docs" / "crisp_dm" / "iteration_2"


def test_every_frozen_file_matches_its_recorded_hash():
    lines = (FROZEN / "frozen.sha256").read_text(encoding="utf-8").splitlines()
    assert len(lines) > 20
    for line in lines:
        digest, name = line.split("  ", 1)
        assert hashlib.sha256((FROZEN / name).read_bytes()).hexdigest() == digest, name
