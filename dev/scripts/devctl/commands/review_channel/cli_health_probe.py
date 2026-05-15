"""CLI health probe attachment for review-channel status."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...runtime.value_coercion import coerce_bool

CLI_HEALTH_PROBE_TOGGLE_ID = "CLIHealthProbeAutomation"
CLI_HEALTH_PROBE_MODES = ("scheduled", "on_error", "disabled")

_HEALTHY_STATUSES = frozenset({"", "ok", "healthy", "ready", "none"})
_RECOVERY_COMMAND_SOURCES = frozenset(
    {
        "doctor",
        "attention",
        "authority_snapshot",
        "reviewer_runtime",
    }
)
_BENIGN_REQUIRED_ACTIONS = frozenset({"", "continue_scoped_loop"})


def build_cli_health_probe_report(
    *,
    status_report: Mapping[str, object],
    exit_code: int,
    mode: str = "scheduled",
) -> dict[str, Any]:
    """Build the P152 CLI health probe from one status report."""
    normalized_mode = _normalize_mode(mode)
    base = {
        "schema_version": 1,
        "contract_id": CLI_HEALTH_PROBE_TOGGLE_ID,
        "toggle_id": CLI_HEALTH_PROBE_TOGGLE_ID,
        "mode": normalized_mode,
        "source_action": status_report.get("action"),
        "source_exit_code": exit_code,
        "snapshot_id": _text(status_report.get("snapshot_id")),
        "zref": _text(status_report.get("zref")),
    }
    if normalized_mode == "disabled":
        return {
            **base,
            "ok": True,
            "active": False,
            "status": "disabled",
            "requires_recovery": False,
            "reason": "recovery probe disabled by P152 toggle",
            "recommended_command": "",
            "recommended_command_source": "",
            "evidence": [],
        }

    assessment = _assess_status(status_report=status_report, exit_code=exit_code)
    if normalized_mode == "on_error" and not assessment["requires_recovery"]:
        return {
            **base,
            "ok": True,
            "active": False,
            "status": "not_triggered",
            "requires_recovery": False,
            "reason": "no status or runtime recovery condition detected",
            "recommended_command": "",
            "recommended_command_source": "",
            "evidence": assessment["evidence"],
        }

    status = "healthy"
    if assessment["command_failed"]:
        status = "error"
    elif assessment["requires_recovery"]:
        status = "attention"
    return {
        **base,
        "ok": not assessment["command_failed"],
        "active": True,
        "status": status,
        "requires_recovery": assessment["requires_recovery"],
        "reason": assessment["reason"],
        "recommended_command": assessment["recommended_command"],
        "recommended_command_source": assessment["recommended_command_source"],
        "recovery_action_id": assessment["recovery_action_id"],
        "recovery_command": assessment["recovery_command"],
        "doctor_status": assessment["doctor_status"],
        "runtime_readiness_status": assessment["runtime_readiness_status"],
        "runtime_system_ok": assessment["runtime_system_ok"],
        "authority_required_action": assessment["authority_required_action"],
        "evidence": assessment["evidence"],
    }


def attach_cli_health_probe(
    report: dict[str, object],
    *,
    exit_code: int,
    mode: str = "scheduled",
) -> None:
    """Attach the CLI health probe report in-place."""
    report["cli_health_probe"] = build_cli_health_probe_report(
        status_report=report,
        exit_code=exit_code,
        mode=mode,
    )


def attach_cli_health_probe_if_requested(
    report: dict[str, object],
    *,
    args,
    exit_code: int,
) -> None:
    """Attach the probe only when the status CLI flag requests it."""
    if not bool(getattr(args, "recovery_probe", False)):
        return
    attach_cli_health_probe(
        report,
        exit_code=exit_code,
        mode=getattr(args, "recovery_probe_mode", "scheduled"),
    )


def append_cli_health_probe_markdown(
    lines: list[str],
    probe: object,
) -> None:
    """Render the CLI health probe attachment for markdown status output."""
    if not isinstance(probe, Mapping) or not probe:
        return
    lines.append("")
    lines.append("## CLI Health Probe")
    lines.append(f"- toggle_id: {probe.get('toggle_id')}")
    lines.append(f"- mode: {probe.get('mode')}")
    lines.append(f"- active: {coerce_bool(probe.get('active'))}")
    lines.append(f"- ok: {coerce_bool(probe.get('ok'))}")
    lines.append(f"- status: {probe.get('status') or 'unknown'}")
    lines.append(f"- requires_recovery: {coerce_bool(probe.get('requires_recovery'))}")
    if probe.get("reason"):
        lines.append(f"- reason: {probe.get('reason')}")
    if probe.get("recommended_command"):
        lines.append(f"- recommended_command: `{probe.get('recommended_command')}`")
        if probe.get("recommended_command_source"):
            lines.append(
                "- recommended_command_source: "
                f"{probe.get('recommended_command_source')}"
            )
    if probe.get("recovery_action_id"):
        lines.append(f"- recovery_action_id: {probe.get('recovery_action_id')}")
    if probe.get("recovery_command"):
        lines.append(f"- recovery_command: `{probe.get('recovery_command')}`")


def _normalize_mode(mode: str) -> str:
    normalized = str(mode or "scheduled").strip()
    if normalized in CLI_HEALTH_PROBE_MODES:
        return normalized
    return "scheduled"


def _assess_status(
    *,
    status_report: Mapping[str, object],
    exit_code: int,
) -> dict[str, object]:
    errors = _string_list(status_report.get("errors"))
    command_failed = exit_code != 0 or bool(errors)
    doctor = _mapping(status_report.get("doctor"))
    recovery = _mapping(status_report.get("recovery_assessment"))
    recovery_decision = _mapping(recovery.get("decision"))
    recovery_diagnosis = _mapping(recovery.get("diagnosis"))
    readiness = _mapping(status_report.get("runtime_readiness"))
    authority = _mapping(status_report.get("authority_snapshot"))
    doctor_status = _text(doctor.get("status"))
    diagnosis_status = _text(recovery_diagnosis.get("status"))
    readiness_status = _text(readiness.get("status"))
    authority_required_action = _text(authority.get("required_action"))
    recommended_command = _text(status_report.get("recommended_command"))
    recommended_command_source = _text(status_report.get("recommended_command_source"))
    recovery_command = _text(recovery_decision.get("command")) or _text(
        doctor.get("decision_command")
    )
    recovery_action_id = _text(recovery_decision.get("action_id")) or _text(
        doctor.get("decision_action_id")
    )

    conditions: list[str] = []
    if command_failed:
        conditions.append("status_command_failed")
    if doctor_status.lower() not in _HEALTHY_STATUSES:
        conditions.append(f"doctor_status:{doctor_status or 'unknown'}")
    if diagnosis_status.lower() not in _HEALTHY_STATUSES:
        conditions.append(f"recovery_diagnosis:{diagnosis_status or 'unknown'}")
    if readiness_status == "blocked" and not _benign_readiness_block(readiness):
        conditions.append("runtime_readiness:blocked")
    if authority_required_action not in _BENIGN_REQUIRED_ACTIONS:
        conditions.append(f"required_action:{authority_required_action}")
    if recommended_command and recommended_command_source in _RECOVERY_COMMAND_SOURCES:
        conditions.append(f"recommended_command_source:{recommended_command_source}")
    if recovery_command:
        conditions.append("recovery_command_present")

    requires_recovery = bool(conditions)
    if command_failed:
        reason = "status command failed; inspect errors and recovery evidence"
    elif requires_recovery:
        reason = "runtime recovery condition detected"
    else:
        reason = "review-channel status and runtime recovery signals are healthy"

    return {
        "command_failed": command_failed,
        "requires_recovery": requires_recovery,
        "reason": reason,
        "recommended_command": recommended_command,
        "recommended_command_source": recommended_command_source,
        "recovery_action_id": recovery_action_id,
        "recovery_command": recovery_command,
        "doctor_status": doctor_status,
        "runtime_readiness_status": readiness_status,
        "runtime_system_ok": coerce_bool(readiness.get("system_ok")),
        "authority_required_action": authority_required_action,
        "evidence": _evidence(
            errors=errors,
            conditions=conditions,
            doctor_status=doctor_status,
            diagnosis_status=diagnosis_status,
            readiness_status=readiness_status,
            authority_required_action=authority_required_action,
            recommended_command_source=recommended_command_source,
        ),
    }


def _benign_readiness_block(readiness: Mapping[str, object]) -> bool:
    command = _text(readiness.get("recommended_command"))
    blockers = set(_string_list(readiness.get("recommended_command_blockers")))
    if "dev/scripts/devctl.py push --execute" in command:
        return True
    return bool(blockers) and blockers.issubset({"vcs.commit", "vcs.push"})


def _evidence(
    *,
    errors: list[str],
    conditions: list[str],
    doctor_status: str,
    diagnosis_status: str,
    readiness_status: str,
    authority_required_action: str,
    recommended_command_source: str,
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for error in errors:
        entries.append(
            {
                "code": "status_error",
                "surface": "review-channel.status",
                "value": error,
            }
        )
    for condition in conditions:
        entries.append(
            {
                "code": "recovery_condition",
                "surface": "cli_health_probe",
                "value": condition,
            }
        )
    for code, surface, value in (
        ("doctor_status", "doctor", doctor_status),
        ("diagnosis_status", "recovery_assessment", diagnosis_status),
        ("runtime_readiness_status", "runtime_readiness", readiness_status),
        ("required_action", "authority_snapshot", authority_required_action),
        ("recommended_command_source", "review-channel.status", recommended_command_source),
    ):
        if value:
            entries.append({"code": code, "surface": surface, "value": value})
    return entries


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := str(item or "").strip())]
