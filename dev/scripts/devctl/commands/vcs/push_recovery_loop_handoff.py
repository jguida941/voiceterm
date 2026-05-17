"""Completed-handoff gating for governed push recovery-loop repair."""

from __future__ import annotations

from pathlib import Path

from ...runtime.agent_session_outcome import AgentSessionOutcomeState
from ...runtime.completed_handoff_authority import (
    current_completed_handoff_outcome,
    handoff_target_revisions,
)
from .push_recovery_loop_payload import field_value, payload_allows_bounded_recovery

_BLOCKED_IMPLEMENTATION_PERMISSIONS = frozenset({"blocked", "suspended"})


def completed_handoff_outcome_for_startup_payload(
    *,
    repo_root: Path,
    payload: dict[str, object],
) -> AgentSessionOutcomeState | None:
    if not payload_is_completed_handoff_repair(payload):
        return None

    return current_completed_handoff_outcome(repo_root=repo_root)


def payload_is_completed_handoff_repair(payload: dict[str, object]) -> bool:
    if not payload_allows_bounded_recovery(payload):
        return False

    action = field_value(payload, "advisory_action") or field_value(payload, "action")
    if action != "repair_reviewer_loop":
        return False

    if field_value(payload, "attention_status") != "runtime_missing":
        return False

    permission = field_value(payload, "implementation_permission")
    if permission and permission not in _BLOCKED_IMPLEMENTATION_PERMISSIONS:
        return False

    topology = field_value(payload, "observed_control_topology")
    recovery_basis = field_value(payload, "recovery_basis")
    if topology:
        return topology == "no_live_agents"

    return recovery_basis in {"process_dead", "runtime_missing"}


def _handoff_target_revisions(repo_root: Path) -> tuple[str, ...]:
    return handoff_target_revisions(repo_root)

__all__ = [
    "completed_handoff_outcome_for_startup_payload",
    "payload_is_completed_handoff_repair",
]
