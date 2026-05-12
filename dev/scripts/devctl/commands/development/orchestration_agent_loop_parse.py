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
    operator_override = _mapping(row.get("operator_override"))
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
        can_run_next_command=bool(row.get("can_run_next_command")),
        advance_allowed=bool(row.get("advance_allowed")),
        effective_authority_source=_text(row.get("effective_authority_source")),
        pending_packet_count=_int(row.get("pending_packet_count")),
        target_kind=_text(row.get("target_kind")),
        target_ref=_text(row.get("target_ref")),
        top_blocker=_text(row.get("top_blocker") or row.get("reason")),
        next_command=_text(row.get("next_command")),
        next_loop_command=_text(row.get("next_loop_command")),
        missing_proofs=_text_tuple(row.get("missing_proofs")),
        allowed_actions=_text_tuple(row.get("allowed_actions")),
        blocked_actions=_text_tuple(row.get("blocked_actions")),
        operator_override_active=bool(operator_override.get("active")),
        operator_override_edit_allowed=_operator_override_edit_allowed(
            operator_override
        ),
        operator_override_scope=_text(operator_override.get("scope")),
        operator_override_target_kind=_text(operator_override.get("target_kind")),
        operator_override_target_ref=_text(operator_override.get("target_ref")),
        active_packet_id=_text(row.get("active_packet_id")),
        attention_packet_id=_text(row.get("attention_packet_id")),
        user_action=_text(row.get("user_action")),
        continuation_goal=_text(row.get("continuation_goal")),
        why_not_done=_text(row.get("why_not_done")),
        user_continue_state=_text(row.get("user_continue_state")),
        new_peer_input=bool(row.get("new_peer_input")),
        switch_to_packet_goal=bool(row.get("switch_to_packet_goal")),
        continue_before_final=bool(row.get("continue_before_final")),
    )


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _text_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(_text(item) for item in value if _text(item))


def _operator_override_edit_allowed(value: Mapping[str, object]) -> bool:
    if not bool(value.get("active")):
        return False
    if _text(value.get("scope")) != "edit-only":
        return False
    allowed = set(_text_tuple(value.get("allowed_actions")))
    blocked = set(_text_tuple(value.get("blocked_actions")))
    return "implementation.edit" in allowed and {
        "vcs.stage",
        "vcs.commit",
        "vcs.push",
    }.issubset(blocked)


__all__ = ["agent_loop_input"]
