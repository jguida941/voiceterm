"""Shared helpers for governance ledger modules (review log, external findings)."""

from __future__ import annotations

import json
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any


def optional_text(value: object) -> str | None:
    """Normalize a value to stripped text or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def required_text(value: object, *, field_name: str) -> str:
    """Require a non-empty stripped text value, raising ValueError if missing."""
    text = optional_text(value)
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def optional_line_number(value: object) -> int | None:
    """Parse a value as a positive line number, or return None."""
    if value is None or value == "":
        return None
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"line numbers must be integers: {value!r}") from exc
    if result <= 0:
        raise ValueError(f"line numbers must be positive: {value!r}")
    return result


def rate(numerator: int, denominator: int) -> float:
    """Compute a percentage rate, returning 0.0 when denominator is non-positive."""
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def latest_rows_by_finding(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate rows by finding_id, keeping the last occurrence of each."""
    latest: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in rows:
        finding_id = optional_text(row.get("finding_id"))
        if not finding_id:
            continue
        if finding_id not in latest:
            order.append(finding_id)
        latest[finding_id] = row
    return [latest[finding_id] for finding_id in order if finding_id in latest]


def resolve_ledger_path(
    raw_path: str | Path | None,
    *,
    default_rel: Path,
    repo_root_fn: Callable[[], Path | None],
    repo_root: Path | None = None,
) -> Path:
    """Resolve a ledger JSONL or summary-root path relative to the repo."""
    effective_root = repo_root or repo_root_fn() or Path(".")
    candidate = (
        Path(raw_path).expanduser()
        if raw_path is not None and str(raw_path).strip()
        else effective_root / default_rel
    )
    if not candidate.is_absolute():
        candidate = effective_root / candidate
    return candidate.resolve()


def read_ledger_rows(
    log_path: Path,
    *,
    max_rows: int,
    parse_line_fn: Callable[..., dict[str, Any] | None],
) -> list[dict[str, Any]]:
    """Read JSONL rows bounded to the most recent max_rows entries."""
    rows: deque[dict[str, Any]] = deque(maxlen=max(1, max_rows))
    try:
        with log_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                payload = parse_line_fn(
                    line, source=str(log_path), line_number=line_number,
                )
                if payload is not None:
                    rows.append(payload)
    except OSError:
        return []
    return list(rows)


def append_ledger_rows(
    rows: list[dict[str, Any]],
    *,
    log_path: Path,
) -> None:
    """Append one or more rows to a JSONL ledger."""
    if not rows:
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


