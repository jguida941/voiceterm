"""Focused status helpers for work-intake coordination reduction."""

from __future__ import annotations

from .control_topology import is_sanctioned_local_single_agent
from .review_state_models import ReviewState
from .work_intake_models import WorkIntakeOwnershipState


def active_implementation_owner(
    participants: tuple[tuple[str, str], ...],
) -> str:
    """Return the current live implementer when one is present."""
    for name, role in participants:
        if role == "implementer" and name:
            return name
    return ""


def resync_required(
    *,
    review_state: ReviewState | None,
    duplicate_delegated_worktrees: tuple[str, ...],
    ownership: WorkIntakeOwnershipState,
    collaboration_topology: str,
) -> bool:
    """Return whether coordination must resync before implementation resumes."""
    if duplicate_delegated_worktrees or ownership.concurrent_writer_detected:
        return True
    if review_state is None:
        return False

    sanctioned_single_agent = (
        collaboration_topology == "single_agent"
        and is_sanctioned_local_single_agent(review_state)
    )
    attention = getattr(review_state, "attention", None)
    attention_status = str(getattr(attention, "status", "") or "").strip()
    if attention_status and attention_status not in {"clear", "ready"}:
        if not (sanctioned_single_agent and attention_status == "inactive"):
            return True

    collaboration = getattr(review_state, "collaboration", None)
    for gate in tuple(getattr(collaboration, "ready_gates", ()) or ()):
        gate_id = str(getattr(gate, "gate_id", "") or "").strip()
        gate_status = str(getattr(gate, "status", "") or "").strip()
        if (
            sanctioned_single_agent
            and gate_id in {"runtime_truth", "review_truth", "implementer_state"}
            and gate_status in {"blocked", "pending"}
        ):
            continue
        if gate_status in {"blocked", "pending", "planned"}:
            return True

    return False


__all__ = ["active_implementation_owner", "resync_required"]
