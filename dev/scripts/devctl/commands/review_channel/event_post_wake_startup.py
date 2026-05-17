"""Startup-blocked packet wake reports."""

from __future__ import annotations

from collections.abc import Mapping

STARTUP_BLOCKED_ATTENTION_SHAPE = "startup_blocked"
STARTUP_AUTHORITY_CLOSURE_COMMAND = (
    "python3 dev/scripts/checks/check_startup_authority_contract.py --format md"
)


def startup_blocked_attention_report(
    *,
    report: Mapping[str, object],
    packet: Mapping[str, object],
    target_agent: str,
    next_pivot_event: str,
) -> dict[str, object] | None:
    """Return a wake report when startup authority blocked packet wake."""
    decision = _startup_blocked_loop_decision(
        report=report,
        target_agent=target_agent,
        packet_id=_text(packet.get("packet_id")),
    )
    if decision is None:
        return None

    blocker = _text(decision.get("top_blocker") or decision.get("reason"))
    wake: dict[str, object] = {}
    wake["attempted"] = True
    wake["woke"] = False
    wake["reason"] = "packet_arrival_blocked_by_startup_authority"
    wake["wake_method"] = "typed_attention_event"
    wake["attention_decision_shape"] = STARTUP_BLOCKED_ATTENTION_SHAPE
    wake["next_pivot_event"] = next_pivot_event
    wake["packet_id"] = _text(packet.get("packet_id"))
    wake["requested_action"] = _text(packet.get("requested_action"))
    wake["target_agent"] = target_agent
    wake["target_role"] = _text(packet.get("target_role"))
    wake["target_session_id"] = _text(packet.get("target_session_id"))
    wake["startup_blocker"] = blocker
    wake["startup_blocker_kind"] = _startup_blocker_kind(blocker)
    wake["closure_check_command"] = STARTUP_AUTHORITY_CLOSURE_COMMAND
    wake["safe"] = bool(decision.get("safe_to_continue"))
    wake["may_mutate"] = bool(decision.get("may_mutate"))
    wake["required_action"] = _text(decision.get("required_action"))
    wake["next_action"] = _text(decision.get("next_action"))
    wake["loop_mode"] = _text(decision.get("loop_mode"))
    return wake


def _startup_blocked_loop_decision(
    *,
    report: Mapping[str, object],
    target_agent: str,
    packet_id: str,
) -> Mapping[str, object] | None:
    decisions = report.get("agent_loop_decisions")
    if not isinstance(decisions, list):
        return None

    fallback: Mapping[str, object] | None = None
    for decision in decisions:
        if not isinstance(decision, Mapping):
            continue
        if _text(decision.get("actor_id")) != target_agent:
            continue
        if not _is_startup_blocked_decision(decision):
            continue
        if packet_id and packet_id in _decision_packet_ids(decision):
            return decision
        if fallback is None:
            fallback = decision
    return fallback


def _is_startup_blocked_decision(decision: Mapping[str, object]) -> bool:
    blocker = _text(decision.get("top_blocker") or decision.get("reason"))
    if not blocker.startswith("startup authority:"):
        return False
    return not bool(decision.get("safe_to_continue"))


def _decision_packet_ids(decision: Mapping[str, object]) -> set[str]:
    return {
        _text(decision.get(key))
        for key in ("active_packet_id", "attention_packet_id", "executing_packet_id")
        if _text(decision.get(key))
    }


def _startup_blocker_kind(blocker: str) -> str:
    prefix = "startup authority:"
    if blocker.startswith(prefix):
        return blocker[len(prefix) :].strip()
    return blocker


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "STARTUP_AUTHORITY_CLOSURE_COMMAND",
    "STARTUP_BLOCKED_ATTENTION_SHAPE",
    "startup_blocked_attention_report",
]
