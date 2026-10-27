"""Frozen self-authored clauses and labels; never injected as answers into prompts."""

import hashlib
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "tests/evaluation"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def manifest():
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(DATA.glob("*.json"))
    }
