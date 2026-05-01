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
    """Attach command-vs-runtime readiness and align top-level ok."""
    readiness = build_runtime_readiness(report)
    report["runtime_readiness"] = readiness
    report["command_ok"] = readiness["command_ok"]
    report["ok"] = readiness["system_ok"]


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
        return coerce_bool(authority.get("safe_to_continue"))
    attention_status = _text(attention.get("status"))
    if attention_status.lower() not in _HEALTHY_ATTENTION_STATUSES:
        return False
    doctor_status = _text(doctor.get("status"))
    if doctor_status.lower() not in _HEALTHY_ATTENTION_STATUSES:
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


__all__ = ["attach_runtime_readiness", "build_runtime_readiness"]
