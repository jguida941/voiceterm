"""Runtime readiness projection for review-channel status surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from ...time_utils import parse_utc_timestamp, utc_timestamp
from ...runtime.value_coercion import (
    coerce_bool,
    coerce_mapping as _mapping,
    coerce_text as _text,
)

_HEALTHY_ATTENTION_STATUSES = frozenset({"", "ok", "healthy", "none"})
_COMMAND_FRESHNESS_STALE_AFTER_SECONDS = 300
_VCS_COMMAND_ACTIONS = (
    ("devctl.py commit", "vcs.commit"),
    ("devctl.py push", "vcs.push"),
    ("git commit", "vcs.commit"),
    ("git push", "vcs.push"),
)


@dataclass(frozen=True)
class ReviewChannelCommandFreshness:
    """Freshness metadata for read-only review-channel command output."""

    command_generated_at_utc: str
    observed_at_utc: str
    command_age_seconds: int | None
    command_freshness_status: str
    runtime_snapshot_at_utc: str
    runtime_snapshot_age_seconds: int | None
    runtime_snapshot_freshness_status: str
    stale_after_seconds: int
    snapshot_id: str
    zref: str
    schema_version: int = 1
    contract_id: str = "ReviewChannelCommandFreshness"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def attach_runtime_readiness(report: dict[str, object]) -> None:
    """Attach command-vs-runtime readiness without conflating status health."""
    readiness = build_runtime_readiness(report)
    report["runtime_readiness"] = readiness
    report["command_freshness"] = readiness["command_freshness"]
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
    freshness = _mapping(readiness.get("command_freshness"))
    if freshness:
        lines.append(
            "- command_generated_at_utc: "
            f"{freshness.get('command_generated_at_utc') or 'unknown'}"
        )
        if freshness.get("command_age_seconds") is not None:
            lines.append(
                f"- command_age_seconds: {freshness.get('command_age_seconds')}"
            )
        lines.append(
            "- command_freshness_status: "
            f"{freshness.get('command_freshness_status') or 'unknown'}"
        )
        lines.append(
            "- command_stale_after_seconds: "
            f"{freshness.get('stale_after_seconds')}"
        )
        if freshness.get("runtime_snapshot_at_utc"):
            lines.append(
                "- runtime_snapshot_at_utc: "
                f"{freshness.get('runtime_snapshot_at_utc')}"
            )
            if freshness.get("runtime_snapshot_age_seconds") is not None:
                lines.append(
                    "- runtime_snapshot_age_seconds: "
                    f"{freshness.get('runtime_snapshot_age_seconds')}"
                )
            lines.append(
                "- runtime_snapshot_freshness_status: "
                f"{freshness.get('runtime_snapshot_freshness_status') or 'unknown'}"
            )
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
    command_freshness = build_command_freshness(report)

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
        "command_freshness": command_freshness,
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


def build_command_freshness(
    report: Mapping[str, object],
    *,
    stale_after_seconds: int = _COMMAND_FRESHNESS_STALE_AFTER_SECONDS,
    observed_at_utc: str | None = None,
) -> dict[str, object]:
    """Return freshness metadata for read-only command output and runtime data."""
    observed_at = _text(observed_at_utc) or utc_timestamp()
    observed_dt = parse_utc_timestamp(observed_at) or datetime.now(timezone.utc)
    command_generated_at = _text(report.get("timestamp")) or observed_at
    runtime_snapshot_at = _runtime_snapshot_at(report)
    command_age = _age_seconds(command_generated_at, observed_dt)
    runtime_age = _age_seconds(runtime_snapshot_at, observed_dt)
    return ReviewChannelCommandFreshness(
        command_generated_at_utc=command_generated_at,
        observed_at_utc=observed_at,
        command_age_seconds=command_age,
        command_freshness_status=_freshness_status(
            command_age,
            stale_after_seconds=stale_after_seconds,
        ),
        runtime_snapshot_at_utc=runtime_snapshot_at,
        runtime_snapshot_age_seconds=runtime_age,
        runtime_snapshot_freshness_status=_freshness_status(
            runtime_age,
            stale_after_seconds=stale_after_seconds,
        ),
        stale_after_seconds=stale_after_seconds,
        snapshot_id=_text(report.get("snapshot_id")),
        zref=_text(report.get("zref")),
    ).to_dict()


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


def _runtime_snapshot_at(report: Mapping[str, object]) -> str:
    doctor = _mapping(report.get("doctor"))
    bridge_liveness = _mapping(report.get("bridge_liveness"))
    reviewer_runtime = _mapping(report.get("reviewer_runtime"))
    return (
        _text(report.get("last_codex_poll_utc"))
        or _text(doctor.get("last_codex_poll_utc"))
        or _text(bridge_liveness.get("last_codex_poll_utc"))
        or _text(reviewer_runtime.get("last_packet_observed_at_utc"))
        or _text(report.get("timestamp"))
    )


def _age_seconds(value: object, observed_dt: datetime) -> int | None:
    parsed = parse_utc_timestamp(value)
    if parsed is None:
        return None
    return max(0, int((observed_dt - parsed).total_seconds()))


def _freshness_status(
    age_seconds: int | None,
    *,
    stale_after_seconds: int,
) -> str:
    if age_seconds is None:
        return "unknown"
    return "fresh" if age_seconds <= stale_after_seconds else "stale"


def _string_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_text(item) for item in value if _text(item)]


__all__ = [
    "ReviewChannelCommandFreshness",
    "append_runtime_readiness_markdown",
    "attach_runtime_readiness",
    "build_command_freshness",
    "build_runtime_readiness",
]
