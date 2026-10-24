"""Validate database identifiers before SQL interpolation."""

import re


def identifier(value: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", value):
        raise ValueError("Invalid database schema identifier")
    return value
