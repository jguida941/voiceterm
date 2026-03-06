"""Shared helpers for workflow bridge scripts."""

from __future__ import annotations

import json
import re
from pathlib import Path

ALLOWED_LOOP_MODES = {"report-only", "plan-then-fix", "fix-only"}
ALLOWED_NOTIFY_MODES = {"summary-only", "summary-and-comment"}
ALLOWED_COMMENT_TARGETS = {"auto", "pr", "commit"}


def read_json(path: Path) -> dict:
    """Read a UTF-8 JSON file into a dictionary payload."""
    return json.loads(path.read_text(encoding="utf-8"))


def append_output(path: Path, fields: list[tuple[str, str]]) -> None:
    """Append simple key/value pairs to a GitHub output file."""
    with path.open("a", encoding="utf-8") as handle:
        for key, value in fields:
            handle.write(f"{key}={value}\n")


def append_multiline_output(path: Path, key: str, value: str) -> None:
    """Append a multi-line output value using the heredoc GitHub format."""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{key}<<EOF\n")
        handle.write(f"{value}\n")
        handle.write("EOF\n")


def validate_positive_int(raw_value: str, *, minimum: int, message: str) -> str:
    """Validate unsigned integer inputs and enforce a minimum value."""
    if not re.fullmatch(r"[0-9]+", raw_value or ""):
        raise ValueError(message)
    if int(raw_value) < minimum:
        raise ValueError(message)
    return raw_value


def validate_decimal_hours(raw_value: str, *, message: str) -> str:
    """Validate decimal hour values such as `1` or `1.5`."""
    if not re.fullmatch(r"[0-9]+([.][0-9]+)?", raw_value or ""):
        raise ValueError(message)
    return raw_value


def validate_allowed(raw_value: str, *, allowed: set[str], message: str) -> str:
    """Ensure the provided string is present in the given allowlist."""
    if raw_value not in allowed:
        raise ValueError(message)
    return raw_value
