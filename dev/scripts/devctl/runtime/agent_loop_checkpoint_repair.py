"""Checkpoint repair promotion readers for AgentLoopDecision."""

from __future__ import annotations

from collections.abc import Mapping

from .checkpoint_repair_authority import (
    GOVERNED_CHECKPOINT_COMMIT,
    GOVERNED_CHECKPOINT_COMMIT_COMMAND,
    checkpoint_repair_authority_from_mapping,
)
from .value_coercion import coerce_mapping as _mapping


def checkpoint_repair_authority_for_loop(
    review_state: Mapping[str, object],
) -> Mapping[str, object]:
    """Return verified checkpoint repair authority from typed review state."""
    direct = checkpoint_repair_authority_from_mapping(
        _mapping(review_state.get("checkpoint_repair_authority"))
    )
    if direct is not None:
        return direct.to_dict()
    commit_pipeline = _mapping(review_state.get("commit_pipeline"))
    promoted = checkpoint_repair_authority_from_mapping(
        _mapping(commit_pipeline.get("checkpoint_repair_authority"))
    )
    if promoted is not None:
        return promoted.to_dict()
    promoted = checkpoint_repair_authority_from_mapping(
        _mapping(commit_pipeline.get("push_failure_transition"))
    )
    return promoted.to_dict() if promoted is not None else {}


def checkpoint_repair_next_action(
    *,
    authority: Mapping[str, object],
    top_blocker: str,
    next_action: str,
    next_command: str,
) -> tuple[str, str]:
    """Promote startup checkpoint blockers when verified repair proof exists."""
    if not authority or not _checkpoint_repair_matches_blocker(
        top_blocker=top_blocker,
        next_action=next_action,
    ):
        return next_action, next_command
    return GOVERNED_CHECKPOINT_COMMIT, GOVERNED_CHECKPOINT_COMMIT_COMMAND


def checkpoint_repair_next_action_for_review_state(
    review_state: Mapping[str, object],
    *,
    top_blocker: str,
    next_action: str,
    next_command: str,
) -> tuple[str, str]:
    """Return the checkpoint-repair next action for an agent-loop context."""
    return checkpoint_repair_next_action(
        authority=checkpoint_repair_authority_for_loop(review_state),
        top_blocker=top_blocker,
        next_action=next_action,
        next_command=next_command,
    )


def _checkpoint_repair_matches_blocker(
    *,
    top_blocker: str,
    next_action: str,
) -> bool:
    blocker = top_blocker.lower()
    action = next_action.lower()
    return (
        "startup authority" in blocker
        or "checkpoint" in blocker
        or action.startswith("checkpoint_blocked_by_startup_authority")
    )


__all__ = [
    "checkpoint_repair_authority_for_loop",
    "checkpoint_repair_next_action",
    "checkpoint_repair_next_action_for_review_state",
]
