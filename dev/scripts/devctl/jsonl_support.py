"""Shared JSONL parsing helpers for devctl telemetry stores."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any


def parse_json_line_dict(
    line: str,
    *,
    source: str = "",
    line_number: int | None = None,
    warning_sink: Callable[[str], None] | None = None,
) -> dict[str, Any] | None:
    """Parse one JSONL row and keep only object payloads."""
    text = line.strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        _emit_jsonl_warning(
            "invalid JSON object",
            source=source,
            line_number=line_number,
            warning_sink=warning_sink,
        )
        return None
    if isinstance(payload, dict):
        return payload
    _emit_jsonl_warning(
        "expected top-level JSON object",
        source=source,
        line_number=line_number,
        warning_sink=warning_sink,
    )
    return None


def _emit_jsonl_warning(
    detail: str,
    *,
    source: str,
    line_number: int | None,
    warning_sink: Callable[[str], None] | None,
) -> None:
    location = source or "jsonl stream"
    if line_number is not None:
        location = f"{location}:{line_number}"
    message = f"[jsonl] warning: skipped malformed row at {location}: {detail}"
    if warning_sink is not None:
        warning_sink(message)
        return
    print(message, file=sys.stderr)
