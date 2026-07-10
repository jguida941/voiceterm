"""Shared helpers for badge renderer entrypoints."""

from __future__ import annotations

import json
from pathlib import Path


def write_badge(path: Path, label: str, message: str, color: str) -> None:
    """Write one shields endpoint JSON payload."""
    payload = {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": color,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
