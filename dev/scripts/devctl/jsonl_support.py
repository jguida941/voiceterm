"""Shared JSONL parsing helpers for devctl telemetry stores."""

from __future__ import annotations

import json
from typing import Any


def parse_json_line_dict(line: str) -> dict[str, Any] | None:
    """Parse one JSONL row and keep only object payloads."""
    text = line.strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
