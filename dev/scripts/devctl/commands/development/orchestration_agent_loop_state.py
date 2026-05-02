"""Agent-loop state/ranking helpers for `/develop` orchestration."""

from __future__ import annotations

from .models import DevelopmentAgentLoopInput


def agent_loop_rank(
    row: DevelopmentAgentLoopInput,
    *,
    actor: str,
) -> tuple[int, int, int, str]:
    """Rank the active actor and blocked rows ahead of background rows."""
    actor_rank = 0 if row.actor_id == actor else 1
    action_rank = 0 if agent_loop_status(row) != "current" else 1
    safe_rank = 0 if not row.safe_to_continue else 1
    return (actor_rank, action_rank, safe_rank, row.session_id)


def agent_loop_status(row: DevelopmentAgentLoopInput) -> str:
    """Classify one row for the controller status surface."""
    if row.missing_proofs or row.proof_state == "missing":
        return "missing"
    if row.pending_packet_count > 0 or row.should_continue_loop:
        if not row.safe_to_continue or row.top_blocker:
            return "blocked"
        return "action_required"
    return "current"


def agent_loop_signal_id(row: DevelopmentAgentLoopInput) -> str:
    parts = [row.actor_id or "actor", row.actor_role or "role"]
    if row.session_id:
        parts.append(row.session_id[:12])
    return ":".join(parts)


def agent_loop_summary(row: DevelopmentAgentLoopInput) -> str:
    blocker = row.top_blocker or row.required_action or row.lifecycle_state
    return (
        f"{row.actor_id or 'actor'} {row.actor_role or 'role'} "
        f"requires {row.required_action or 'attention'}; "
        f"safe={row.safe_to_continue}; may_mutate={row.may_mutate}; "
        f"blocker={blocker or 'none'}"
    )


def agent_loop_severity(row: DevelopmentAgentLoopInput, status: str) -> str:
    if status == "missing":
        return "high"
    if row.pending_packet_count > 0:
        return "high"
    if status == "blocked":
        return "medium"
    if status == "action_required":
        return "medium"
    return "info"


__all__ = [
    "agent_loop_rank",
    "agent_loop_severity",
    "agent_loop_signal_id",
    "agent_loop_status",
    "agent_loop_summary",
]
