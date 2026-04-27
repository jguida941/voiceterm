"""Approved-target identity validation helpers for governed push."""

from __future__ import annotations

from datetime import datetime, timezone

from ...governance.push_state import current_head_commit_sha
from .push_findings_identity import (
    APPROVED_TARGET_IDENTITY_MAX_AGE_SECONDS,
    APPROVED_TARGET_IDENTITY_VIOLATION,
)
from .push_findings_payloads import append_finding


def append_approved_identity_errors(
    state: object,
    *,
    authorization: object,
    repo_root,
) -> None:
    current_head = current_head_commit_sha(repo_root=repo_root)
    authorized_head = str(
        getattr(authorization, "authorized_head_sha", "") or ""
    ).strip()

    append_head_identity_error(
        state,
        authorized_head=authorized_head,
        current_head=current_head,
    )

    approved_worktree = str(
        getattr(authorization, "worktree_identity", "") or ""
    ).strip()
    current_worktree = str(getattr(state, "current_worktree_identity", "") or "")

    append_worktree_identity_error(
        state,
        approved_worktree=approved_worktree,
        current_worktree=current_worktree,
    )

    approved_at = str(getattr(authorization, "approved_at_utc", "") or "").strip()
    target_identity = str(
        getattr(authorization, "approved_target_identity", "") or ""
    ).strip()

    append_stale_identity_error(
        state,
        target_identity=target_identity,
        approved_at=approved_at,
    )


def append_head_identity_error(
    state: object,
    *,
    authorized_head: str,
    current_head: str,
) -> None:
    if not authorized_head or not current_head or authorized_head == current_head:
        return

    append_finding(
        state,
        APPROVED_TARGET_IDENTITY_VIOLATION,
        "Approved target identity is not bound to the current HEAD.",
        evidence=dict(
            authorized_head_sha=authorized_head,
            current_head=current_head,
        ),
    )


def append_worktree_identity_error(
    state: object,
    *,
    approved_worktree: str,
    current_worktree: str,
) -> None:
    if (
        not approved_worktree
        or not current_worktree
        or approved_worktree == current_worktree
    ):
        return

    append_finding(
        state,
        APPROVED_TARGET_IDENTITY_VIOLATION,
        "Approved target identity is not bound to the current worktree.",
        evidence=dict(
            approved_worktree_identity=approved_worktree,
            current_worktree_identity=current_worktree,
        ),
    )


def append_stale_identity_error(
    state: object,
    *,
    target_identity: str,
    approved_at: str,
) -> None:
    if approved_identity_is_stale(target_identity, approved_at=approved_at):
        append_finding(
            state,
            APPROVED_TARGET_IDENTITY_VIOLATION,
            "Approved target identity is stale and must be refreshed before push.",
            evidence=dict(
                approved_target_identity=target_identity,
                approved_at_utc=approved_at,
                max_age_seconds=APPROVED_TARGET_IDENTITY_MAX_AGE_SECONDS,
            ),
        )


def approved_identity_is_stale(identity: str, *, approved_at: str) -> bool:
    del identity
    if not approved_at:
        return False

    parsed = parse_utc_timestamp(approved_at)
    if parsed is None:
        return False

    return (
        datetime.now(timezone.utc) - parsed
    ).total_seconds() > APPROVED_TARGET_IDENTITY_MAX_AGE_SECONDS


def parse_utc_timestamp(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None

    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S%fZ"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except ValueError:
        return None


__all__ = [
    "append_approved_identity_errors",
    "append_head_identity_error",
    "append_stale_identity_error",
    "append_worktree_identity_error",
    "approved_identity_is_stale",
    "parse_utc_timestamp",
]
