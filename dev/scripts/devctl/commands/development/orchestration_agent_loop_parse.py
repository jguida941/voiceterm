"""Agent-loop row parsing for `/develop` orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .models import DevelopmentAgentLoopInput


def agent_loop_input(
    row: Mapping[str, object],
) -> DevelopmentAgentLoopInput | None:
    """Convert one typed row into the controller input contract."""
    actor_id = _text(row.get("actor_id"))
    actor_role = _text(row.get("actor_role"))
    if not actor_id and not actor_role:
        return None
    return DevelopmentAgentLoopInput(
        actor_id=actor_id,
        actor_role=actor_role,
        session_id=_text(row.get("session_id")),
        lifecycle_state=_text(row.get("lifecycle_state")),
        required_action=_text(row.get("required_action")),
        loop_mode=_text(row.get("loop_mode")),
        should_continue_loop=bool(row.get("should_continue_loop")),
        safe_to_continue=bool(row.get("safe_to_continue")),
        may_mutate=bool(row.get("may_mutate")),
        proof_state=_text(row.get("proof_state")),
        pending_packet_count=_int(row.get("pending_packet_count")),
        top_blocker=_text(row.get("top_blocker") or row.get("reason")),
        next_loop_command=_text(row.get("next_loop_command")),
        missing_proofs=_text_tuple(row.get("missing_proofs")),
    )


def _text(value: object) -> str:
    return str(value or "").strip()


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _text_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(_text(item) for item in value if _text(item))


__all__ = ["agent_loop_input"]
