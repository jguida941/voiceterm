"""Read-only JSONL helpers for governed-exception lifecycle state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .governed_exception_contracts import (
    GovernedExceptionLifecycle,
    pending_lifecycle_status,
)
from .jsonl_support import parse_json_line_dict

DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL = Path(
    "dev/state/governed_exception_lifecycles.jsonl"
)


@dataclass(frozen=True, slots=True)
class GovernedExceptionStoreLoadResult:
    """Result of loading lifecycle JSONL with fail-visible parse errors."""

    lifecycles: tuple[GovernedExceptionLifecycle, ...]
    errors: tuple[str, ...] = ()


def load_governed_exception_lifecycles(
    path: Path,
) -> tuple[GovernedExceptionLifecycle, ...]:
    """Load lifecycle rows from JSONL, returning an empty tuple if missing."""
    result = load_governed_exception_lifecycles_with_errors(path)
    if result.errors:
        raise ValueError("; ".join(result.errors))
    return result.lifecycles


def load_governed_exception_lifecycles_with_errors(
    path: Path,
) -> GovernedExceptionStoreLoadResult:
    """Load lifecycle rows and report malformed JSONL instead of dropping it."""
    rows, read_errors = _load_jsonl(path)
    lifecycles: list[GovernedExceptionLifecycle] = []
    errors: list[str] = list(read_errors)
    for index, payload in rows:
        try:
            lifecycles.append(GovernedExceptionLifecycle.from_mapping(payload))
        except (TypeError, ValueError) as exc:
            errors.append(f"{path}: line {index}: invalid_lifecycle:{exc}")
    return GovernedExceptionStoreLoadResult(
        lifecycles=tuple(lifecycles),
        errors=tuple(errors),
    )


def pending_governed_exception_lifecycles(
    path: Path,
) -> tuple[GovernedExceptionLifecycle, ...]:
    """Return lifecycle rows that are not closed/resolved."""
    return tuple(
        lifecycle
        for lifecycle in load_governed_exception_lifecycles(path)
        if pending_lifecycle_status(lifecycle.status)
    )


def _load_jsonl(path: Path) -> tuple[tuple[int, Mapping[str, object]], tuple[str, ...]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return (), ()
    errors: list[str] = []
    rows: list[tuple[int, Mapping[str, object]]] = []
    for index, line in enumerate(lines, start=1):
        payload = parse_json_line_dict(
            line,
            source=str(path),
            line_number=index,
            warning_sink=lambda message: errors.append(message),
        )
        if payload is not None:
            rows.append((index, payload))
    return tuple(rows), tuple(errors)


__all__ = [
    "DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL",
    "GovernedExceptionStoreLoadResult",
    "load_governed_exception_lifecycles",
    "load_governed_exception_lifecycles_with_errors",
    "pending_governed_exception_lifecycles",
]
