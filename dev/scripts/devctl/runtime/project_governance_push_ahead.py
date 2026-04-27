"""Ahead-commit parsing for the ProjectGovernance push contract."""

from __future__ import annotations

from collections.abc import Mapping

from .value_coercion import coerce_int


def ahead_commit_kwargs(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "ahead_of_upstream_source_commits": _optional_int(
            payload, "ahead_of_upstream_source_commits"
        ),
        "ahead_of_upstream_managed_receipt_commits": (
            coerce_int(payload.get("ahead_of_upstream_managed_receipt_commits"))
            or 0
        ),
        "ahead_of_upstream_unclassified_commits": _optional_int(
            payload, "ahead_of_upstream_unclassified_commits"
        ),
    }


def _optional_int(payload: Mapping[str, object], key: str) -> int | None:
    value = payload.get(key)
    return coerce_int(value) if value is not None else None
