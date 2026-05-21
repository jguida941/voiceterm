"""Agent-loop row parsing for `/develop` orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ...runtime.value_coercion import coerce_bool

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
        # v4.45.5 (rev_pkt_4743): migrate remaining boolean fields off raw
        # ``bool()`` so projection-shaped values like ``"false"`` / ``"0"``
        # round-trip correctly. ``can_run_next_command`` was already
        # converted in v4.45.3; codex's read-only audit caught these still
        # raw-coerced. Missing keys remain False (``coerce_bool(None)``).
        should_continue_loop=coerce_bool(row.get("should_continue_loop")),
        safe_to_continue=coerce_bool(row.get("safe_to_continue")),
        may_mutate=coerce_bool(row.get("may_mutate")),
        proof_state=_text(row.get("proof_state")),
        # v4.45.3 (rev_pkt_4739): use coerce_bool so string projections
        # like ``"false"`` / ``"0"`` parse as False instead of bool("false")
        # which is True. Without this, blocked decisions that serialize
        # ``can_run_next_command="false"`` were re-hydrated as True downstream,
        # re-enabling next_loop_command emission.
        can_run_next_command=coerce_bool(row.get("can_run_next_command")),
        advance_allowed=coerce_bool(row.get("advance_allowed")),
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
        operator_override_active=coerce_bool(operator_override.get("active")),
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
        gate_failure=dict(_mapping(row.get("gate_failure"))) or None,
        new_peer_input=coerce_bool(row.get("new_peer_input")),
        switch_to_packet_goal=coerce_bool(row.get("switch_to_packet_goal")),
        continue_before_final=coerce_bool(row.get("continue_before_final")),
        # Phase 0.6.A v4.23 link 7 (rev_pkt_4694): parse BlockerSnapshot typed
        # action fields from the AgentLoopDecision row. Use coerce_bool (not
        # raw bool()) so projections that serialize "false" / "0" survive as
        # False rather than getting coerced to True via Python's truthy-string
        # default. Missing field keeps the contract default of True.
        blocker_owner=_text(row.get("blocker_owner")),
        blocker_target=_text(row.get("blocker_target")),
        blocker_reason=_text(row.get("blocker_reason")),
        repair_command=_text(row.get("repair_command")),
        stop_anchor=_text(row.get("stop_anchor")),
        repair_command_runnable=_parse_repair_command_runnable(row),
    )


def _parse_repair_command_runnable(row: Mapping[str, object]) -> bool:
    """Coerce ``repair_command_runnable`` while preserving the True default.

    v4.23 rev_pkt_4694: ``bool("false") == True`` in Python so the raw cast
    silently flips projection values like ``"false"`` / ``"0"``. coerce_bool
    treats those as False. Missing field falls back to True (the contract
    default for live-agent commands that have not been classified yet).
    """
    if "repair_command_runnable" not in row:
        return True
    value = row.get("repair_command_runnable")
    if value is None:
        return True
    return coerce_bool(value)


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
    # v4.45.6 (rev_pkt_4747): shared coerce_bool so projection
    # ``active="false"`` is correctly treated as inactive. Pre-v4.45.6 the
    # top-level ``operator_override_active`` field parsed via coerce_bool
    # (v4.45.5) while this helper used raw ``bool()``, producing the
    # contradictory shape ``active=False`` + ``edit_allowed=True``.
    if not coerce_bool(value.get("active")):
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
