"""Pending action for the governed exception command."""

from __future__ import annotations

from typing import Any

from ...common import resolve_repo_path
from ...runtime.governed_exception_lifecycle import GovernedExceptionLifecycle
from ...runtime.governed_exception_store import (
    DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL,
    GovernedExceptionStoreLoadResult,
    load_governed_exception_lifecycles_with_errors,
)
from .exceptions_report import base_report


def pending_action(args: Any) -> tuple[dict[str, object], int]:
    """Render pending governed-exception lifecycles."""
    store_path = resolve_repo_path(
        getattr(args, "store_path", ""),
        DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL,
    )
    result = load_governed_exception_lifecycles_with_errors(store_path)
    rows = _pending_rows(result)
    payload = base_report("pending", store_path=store_path)
    payload["ok"] = not result.errors
    payload["errors"] = list(result.errors)
    payload["pending_count"] = len(rows)
    payload["lifecycles"] = [row.to_dict() for row in rows]
    return payload, 0 if not result.errors else 1


def _pending_rows(
    result: GovernedExceptionStoreLoadResult,
) -> list[GovernedExceptionLifecycle]:
    return [
        row
        for row in result.lifecycles
        if row.status.strip() not in {"closed", "resolved"}
    ]


__all__ = ["pending_action"]
