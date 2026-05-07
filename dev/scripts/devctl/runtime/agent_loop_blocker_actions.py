"""Blocker-to-action mapping for AgentLoopDecision."""

from __future__ import annotations

from .checkpoint_repair_authority import GOVERNED_CHECKPOINT_COMMIT


def required_action_for_blocker(top_blocker: str, *, next_action: str = "") -> str:
    """Return the typed action an agent-loop blocker requires."""
    if next_action == GOVERNED_CHECKPOINT_COMMIT:
        return GOVERNED_CHECKPOINT_COMMIT
    blocker = top_blocker.lower()
    if "startup authority" in blocker or "import_index_atomicity" in blocker:
        return "repair_startup_authority"
    if "checkpoint" in blocker:
        return "cut_checkpoint"
    if "review" in blocker:
        return "wait_for_review"
    return "resolve_blocker"


__all__ = ["required_action_for_blocker"]
