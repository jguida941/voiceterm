"""JSONL row readers for substrate commit checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_plan_rows(path: Path) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    return read_jsonl_rows(path, missing_ok=False, warning_prefix="plan_index")


def read_jsonl_rows(
    path: Path,
    *,
    missing_ok: bool,
    warning_prefix: str,
) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        if missing_ok:
            return (), ()
        return (), (f"{warning_prefix}_missing:{path}",)
    except OSError as exc:
        return (), (
            f"{warning_prefix}_read_failed:{exc.__class__.__name__}:{path}",
        )
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"invalid_{warning_prefix}_json:{line_number}:{exc.msg}")
            continue
        if not isinstance(payload, dict):
            warnings.append(f"non_object_{warning_prefix}_row:{line_number}")
            continue
        rows.append(payload)
    return tuple(rows), tuple(warnings)
