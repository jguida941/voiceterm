"""Receipt-aware HEAD movement reducer for pipeline commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...runtime.review_snapshot_refresh import (
    receipt_commit_ancestor_shas,
    receipt_commit_parent_sha,
)

HEAD_MOVEMENT_AUTHORIZED = "authorized_head"
HEAD_MOVEMENT_MANAGED_RECEIPT = "managed_receipt"
HEAD_MOVEMENT_MOVED = "moved"
HEAD_MOVEMENT_UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class HeadMovementContext:
    """Reduced HEAD-vs-pipeline movement evidence."""

    head_has_moved: bool
    classification: str
    managed_receipt_parent_sha: str = ""


def managed_receipt_parent_for_current_head(
    payload: dict[str, Any],
    *,
    current_head: str,
    repo_root: Path,
) -> str:
    """Return the receipt parent when current HEAD is a governed receipt commit."""
    if not _head_differs_from_authorized(payload, current_head=current_head):
        return ""
    parent_sha = receipt_commit_parent_sha(
        repo_root=repo_root,
        current_head=current_head,
        governance=None,
    )
    candidates = _pipeline_head_candidates(payload)
    receipt_ancestors = receipt_commit_ancestor_shas(
        repo_root=repo_root,
        current_head=current_head,
        governance=None,
    )
    for candidate in (*receipt_ancestors, parent_sha):
        if candidate in candidates:
            return candidate
    return ""


def head_movement_context(
    payload: dict[str, Any],
    *,
    current_head: str,
    receipt_parent_sha: str = "",
) -> HeadMovementContext:
    """Classify whether HEAD drift is actionable pipeline drift."""
    if not current_head:
        return HeadMovementContext(False, HEAD_MOVEMENT_UNKNOWN)
    if not _authorized_head_sha_of(payload):
        return HeadMovementContext(False, HEAD_MOVEMENT_UNKNOWN)
    if not _head_differs_from_authorized(payload, current_head=current_head):
        return HeadMovementContext(False, HEAD_MOVEMENT_AUTHORIZED)
    if receipt_parent_sha in _pipeline_head_candidates(payload):
        return HeadMovementContext(
            False,
            HEAD_MOVEMENT_MANAGED_RECEIPT,
            receipt_parent_sha,
        )
    return HeadMovementContext(True, HEAD_MOVEMENT_MOVED)


def head_has_moved(
    payload: dict[str, Any],
    *,
    current_head: str,
    receipt_parent_sha: str = "",
) -> bool:
    """Return true only for actionable HEAD drift, excluding managed receipts."""
    return head_movement_context(
        payload,
        current_head=current_head,
        receipt_parent_sha=receipt_parent_sha,
    ).head_has_moved


def _head_differs_from_authorized(
    payload: dict[str, Any],
    *,
    current_head: str,
) -> bool:
    authorized = _authorized_head_sha_of(payload)
    return bool(current_head and authorized and current_head != authorized)


def _pipeline_head_candidates(payload: dict[str, Any]) -> set[str]:
    values = (
        _authorized_head_sha_of(payload),
        str(payload.get("commit_sha") or ""),
    )
    return {value for value in values if value}


def _authorized_head_sha_of(payload: dict[str, Any]) -> str:
    auth = payload.get("push_authorization")
    if not isinstance(auth, dict):
        return ""
    value = auth.get("authorized_head_sha")
    return str(value) if isinstance(value, str) else ""
