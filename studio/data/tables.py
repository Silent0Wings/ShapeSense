"""Read allow-listed documents. Missing files come back as None, never an error."""

from __future__ import annotations

import csv
import json

from studio.allowlist import doc_path


def read_json(key: str) -> dict | None:
    path = doc_path(key)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(key: str) -> list[dict] | None:
    path = doc_path(key)
    if not path.is_file():
        return None
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_text(key: str) -> str | None:
    path = doc_path(key)
    return path.read_text(encoding="utf-8") if path.is_file() else None
