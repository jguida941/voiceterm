"""Governed-exception and push-proof read helpers for campaign reports."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ...config import REPO_ROOT
from ...runtime.governed_exception_store import (
    DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL,
    load_governed_exception_lifecycles_with_errors,
)
from ...runtime.governed_exception_validation import pending_lifecycle_status


@dataclass(frozen=True, slots=True)
class GovernedExceptionProjection:
    store_path: str
    pending_count: int
    error_count: int
    status: str


@dataclass(frozen=True, slots=True)
class PushProofProjection:
    path: str
    status: str
    head_commit: str
    published_remote: bool
    post_push_green: bool
    matches_current_head: bool
    worktree_dirty: bool
    current_head: str


def governed_exception_projection(
    exception_store_path: Path | None,
) -> GovernedExceptionProjection:
    store_path = exception_store_path or (
        REPO_ROOT / DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL
    )
    result = load_governed_exception_lifecycles_with_errors(store_path)
    pending_count = sum(
        1
        for lifecycle in result.lifecycles
        if pending_lifecycle_status(lifecycle.status)
    )
    if result.errors:
        status = "store_error"
    elif pending_count:
        status = "open_exception_debt"
    else:
        status = "clear"
    return GovernedExceptionProjection(
        store_path=str(store_path),
        pending_count=pending_count,
        error_count=len(result.errors),
        status=status,
    )


def push_proof_projection(review_state: Mapping[str, object]) -> PushProofProjection:
    push_enforcement = _push_enforcement(review_state)
    status = _text(
        push_enforcement.get("selected_push_report_status")
        or push_enforcement.get("latest_push_report_status")
    )
    path = _text(
        push_enforcement.get("selected_push_report_path")
        or push_enforcement.get("latest_push_report_path")
    )
    head_commit = _text(
        push_enforcement.get("selected_push_report_head_commit")
        or push_enforcement.get("latest_push_report_head_commit")
    )
    published_remote = bool(
        push_enforcement.get("selected_push_report_published_remote")
        or push_enforcement.get("latest_push_report_published_remote")
    )
    post_push_green = bool(
        push_enforcement.get("selected_push_report_post_push_green")
        or push_enforcement.get("latest_push_report_post_push_green")
    )
    matches_current_head = bool(
        push_enforcement.get("selected_push_report_matches_current_head")
        or push_enforcement.get("latest_push_report_matches_current_head")
    )
    return PushProofProjection(
        path=path,
        status=status,
        head_commit=head_commit,
        published_remote=published_remote,
        post_push_green=post_push_green,
        matches_current_head=matches_current_head,
        worktree_dirty=bool(push_enforcement.get("worktree_dirty")),
        current_head=_text(push_enforcement.get("current_head_commit")),
    )


def bypass_posture(
    *,
    exception_projection: GovernedExceptionProjection,
    push_projection: PushProofProjection,
) -> str:
    if exception_projection.error_count:
        return "blocked_governed_exception_store_error"
    if exception_projection.pending_count:
        return "blocked_open_governed_exception_debt"
    if (
        push_projection.status == "post_push_green"
        and push_projection.published_remote
        and push_projection.post_push_green
        and push_projection.matches_current_head
    ):
        if push_projection.worktree_dirty:
            return "retired_governed_push_green_checkpoint_pending"
        return "retired_governed_push_green"
    if not push_projection.status:
        return "no_governed_push_proof"
    return "blocked_governed_push_proof_incomplete"


def publication_proof_summary(
    *,
    posture: str,
    push_projection: PushProofProjection,
    exception_projection: GovernedExceptionProjection,
) -> str:
    return (
        f"{posture}; exceptions={exception_projection.status} "
        f"pending={exception_projection.pending_count} "
        f"errors={exception_projection.error_count}; "
        f"push_status={push_projection.status or 'none'} "
        f"published={push_projection.published_remote} "
        f"post_push_green={push_projection.post_push_green} "
        f"matches_head={push_projection.matches_current_head}"
    )


def _push_enforcement(review_state: Mapping[str, object]) -> Mapping[str, object]:
    candidates = (
        review_state.get("push_enforcement"),
        _mapping(review_state.get("governance")).get("push_enforcement"),
        _mapping(review_state.get("bridge_liveness")).get("push_enforcement"),
        _mapping(review_state.get("_compat")).get("push_enforcement"),
    )
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            return candidate
    return {}


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "GovernedExceptionProjection",
    "PushProofProjection",
    "bypass_posture",
    "governed_exception_projection",
    "publication_proof_summary",
    "push_proof_projection",
]
