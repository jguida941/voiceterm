"""Shared state vocabulary for the remote commit/push pipeline."""

from __future__ import annotations

from collections.abc import Mapping

from .value_coercion import coerce_bool, coerce_mapping, coerce_string

STATE_DELIVERED_LOCALLY_PENDING_PUBLISH = "delivered_locally_pending_publish"

ACTIVE_PIPELINE_STATES = frozenset({
    "drafted",
    "staged",
    "guards_running",
    "guards_passed",
    "operator_approval_pending",
    "approved",
    "commit_pending",
    "commit_recorded",
    "push_pending",
})

BLOCKING_PIPELINE_STATES = frozenset({
    "commit_recorded",
    "push_pending",
    "push_blocked",
})

RECOVERABLE_PIPELINE_STATES = frozenset({
    "commit_recorded",
    "push_blocked",
})

REFRESHABLE_PIPELINE_STATES = frozenset({
    "commit_recorded",
    "push_blocked",
    "awaiting_push",
})

TERMINAL_PIPELINE_STATES = frozenset({
    "push_completed",
    "abandoned",
    STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
})

PUSHABLE_PIPELINE_STATES = frozenset({
    "commit_recorded",
    "push_pending",
    "push_blocked",
})


def eligible_for_local_delivery(
    payload: Mapping[str, object],
    *,
    current_head: str,
) -> bool:
    """Return True when a local commit can leave the active pipeline slot."""
    state = coerce_string(payload.get("state"))
    if state not in {"push_blocked", "commit_recorded"}:
        return False
    commit_sha = coerce_string(payload.get("commit_sha"))
    if not commit_sha or commit_sha != current_head:
        return False
    commit_result = coerce_mapping(payload.get("commit_result"))
    if not coerce_bool(commit_result.get("ok")):
        return False
    authorization = coerce_mapping(payload.get("push_authorization"))
    if coerce_string(authorization.get("authorized_head_sha")) != commit_sha:
        return False
    push_result = coerce_mapping(payload.get("push_result"))
    if coerce_bool(push_result.get("partial_progress")):
        return False
    return True


__all__ = [
    "ACTIVE_PIPELINE_STATES",
    "BLOCKING_PIPELINE_STATES",
    "PUSHABLE_PIPELINE_STATES",
    "RECOVERABLE_PIPELINE_STATES",
    "REFRESHABLE_PIPELINE_STATES",
    "STATE_DELIVERED_LOCALLY_PENDING_PUBLISH",
    "TERMINAL_PIPELINE_STATES",
    "eligible_for_local_delivery",
]
