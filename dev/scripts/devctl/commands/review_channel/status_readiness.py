"""Runtime readiness projection for review-channel status surfaces."""

from __future__ import annotations

from collections.abc import Mapping

from ...runtime.value_coercion import (
    coerce_bool,
    coerce_mapping as _mapping,
    coerce_text as _text,
)

_HEALTHY_ATTENTION_STATUSES = frozenset({"", "ok", "healthy", "none"})
_VCS_COMMAND_ACTIONS = (
    ("devctl.py commit", "vcs.commit"),
    ("devctl.py push", "vcs.push"),
    ("git commit", "vcs.commit"),
    ("git push", "vcs.push"),
)


def attach_runtime_readiness(report: dict[str, object]) -> None:
    """Attach command-vs-runtime readiness without conflating status health."""
    readiness = build_runtime_readiness(report)
    report["runtime_readiness"] = readiness
    report["command_ok"] = readiness["command_ok"]
    report["ok"] = readiness["command_ok"]


def append_runtime_readiness_markdown(
    lines: list[str],
    report: Mapping[str, object],
) -> None:
    """Render read-only command health separately from runtime readiness."""
    readiness = _mapping(report.get("runtime_readiness"))
    if not readiness:
        return
    lines.append("")
    lines.append("## Runtime Readiness")
    lines.append(f"- command_ok: {coerce_bool(readiness.get('command_ok'))}")
    lines.append(f"- system_ok: {coerce_bool(readiness.get('system_ok'))}")
    lines.append(f"- status: {readiness.get('status') or 'unknown'}")
    if readiness.get("required_action"):
        lines.append(f"- required_action: {readiness.get('required_action')}")
    if readiness.get("recommended_command"):
        lines.append(
            f"- recommended_command: `{readiness.get('recommended_command')}`"
        )
        lines.append(
            "- recommended_command_allowed: "
            f"{coerce_bool(readiness.get('recommended_command_allowed'))}"
        )
    blockers = _string_list(readiness.get("recommended_command_blockers"))
    if blockers:
        lines.append("- recommended_command_blockers: " + ", ".join(blockers))


def build_runtime_readiness(
    report: Mapping[str, object],
) -> dict[str, object]:
    command_ok = not bool(report.get("errors"))
    if "exit_ok" in report:
        command_ok = command_ok and coerce_bool(report.get("exit_ok"))
    elif "exit_code" in report:
        command_ok = command_ok and str(report.get("exit_code")) in {"", "0"}

    authority = _mapping(report.get("authority_snapshot"))
    attention = _mapping(report.get("attention"))
    doctor = _mapping(report.get("doctor"))
    recovery = _mapping(report.get("recovery_assessment"))
    recovery_decision = _mapping(recovery.get("decision"))
    coordination_state = _mapping(report.get("coordination_state"))
    observed_runtime = _mapping(coordination_state.get("observed_runtime"))

    blocked_actions = _string_list(authority.get("blocked_actions"))
    safe_to_continue = _safe_to_continue(authority, attention, doctor)
    recommended_command = _recommended_command(report, attention, doctor)
    command_blockers = _command_blockers(
        recommended_command=recommended_command,
        blocked_actions=blocked_actions,
    )
    required_action = (
        _text(authority.get("required_action"))
        or _text(recovery_decision.get("action_id"))
        or _text(attention.get("status"))
        or _text(doctor.get("status"))
    )
    status = "ready" if command_ok and safe_to_continue else "blocked"
    system_ok = command_ok and safe_to_continue and not command_blockers
    return {
        "schema_version": 1,
        "contract_id": "ReviewChannelRuntimeReadiness",
        "command_ok": command_ok,
        "system_ok": system_ok,
        "status": status,
        "safe_to_continue": safe_to_continue,
        "required_action": required_action,
        "attention_status": _text(attention.get("status")),
        "doctor_status": _text(doctor.get("status")),
        "recommended_command": recommended_command,
        "recommended_command_source": _text(report.get("recommended_command_source")),
        "recommended_command_allowed": not command_blockers,
        "recommended_command_blockers": command_blockers,
        "blocked_actions": blocked_actions,
        "coordination_topology": _text(
            coordination_state.get("coordination_topology")
        ),
        "legacy_reviewer_mode": _text(coordination_state.get("legacy_reviewer_mode")),
        "active_runtime_providers": _string_list(
            observed_runtime.get("active_runtime_providers")
        ),
        "work_board_row_counts": dict(
            _mapping(observed_runtime.get("work_board_row_counts"))
        ),
    }


def _safe_to_continue(
    authority: Mapping[str, object],
    attention: Mapping[str, object],
    doctor: Mapping[str, object],
) -> bool:
    if "safe_to_continue" in authority:
        authority_safe = coerce_bool(authority.get("safe_to_continue"))
        if authority_safe:
            return True
        return _read_only_status_can_continue(authority, attention, doctor)
    attention_status = _text(attention.get("status"))
    if attention_status.lower() not in _HEALTHY_ATTENTION_STATUSES:
        return False
    doctor_status = _text(doctor.get("status"))
    if doctor_status.lower() not in _HEALTHY_ATTENTION_STATUSES:
        return False
    return True


def _read_only_status_can_continue(
    authority: Mapping[str, object],
    attention: Mapping[str, object],
    doctor: Mapping[str, object],
) -> bool:
    """Do not make read-only status fail just because observer mutation is blocked."""
    attention_status = _text(attention.get("status")).lower()
    doctor_status = _text(doctor.get("status")).lower()
    if attention_status not in _HEALTHY_ATTENTION_STATUSES:
        return False
    if doctor_status not in _HEALTHY_ATTENTION_STATUSES:
        return False
    if _text(authority.get("implementation_permission")) in {"blocked", "suspended"}:
        return False
    if _text(authority.get("current_instruction_revision")):
        return False
    if _text(authority.get("implementer_ack_state")) in {"stale"}:
        return False
    required_action = _text(authority.get("required_action"))
    if required_action and required_action not in {"continue_scoped_loop"}:
        return False
    coordination_state = _text(authority.get("coordination_state"))
    if coordination_state and coordination_state not in {
        "ready",
        "single_agent",
        "single_agent_authoritative",
    }:
        return False
    return True


def _recommended_command(
    report: Mapping[str, object],
    attention: Mapping[str, object],
    doctor: Mapping[str, object],
) -> str:
    return (
        _text(report.get("recommended_command"))
        or _text(doctor.get("recommended_command"))
        or _text(attention.get("recommended_command"))
    )


def _command_blockers(
    *,
    recommended_command: str,
    blocked_actions: list[str],
) -> list[str]:
    if not recommended_command:
        return []
    lowered = recommended_command.lower()
    blocked = set(blocked_actions)
    return [
        action for marker, action in _VCS_COMMAND_ACTIONS
        if marker in lowered and action in blocked
    ]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_text(item) for item in value if _text(item)]


__all__ = [
    "append_runtime_readiness_markdown",
    "attach_runtime_readiness",
    "build_runtime_readiness",
]
