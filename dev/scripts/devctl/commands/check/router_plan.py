"""Command planning helpers for check-router."""

from __future__ import annotations

from .router_range import normalize_router_command

_SERIAL_REQUIRED_COMMAND_MARKERS: tuple[tuple[str, str], ...] = (
    (
        "dev/scripts/devctl.py check ",
        "profile command orchestrates its own phased checks and writes reports",
    ),
    (
        "dev/scripts/devctl.py docs-check",
        "docs-check consumes multi-agent and docs projections that must be stable",
    ),
    (
        "dev/scripts/devctl.py hygiene",
        "hygiene consumes process/report state and should not race projection readers",
    ),
    (
        "dev/scripts/devctl.py orchestrate-",
        "orchestration commands read/write coordination projections",
    ),
    (
        "dev/scripts/devctl.py status ",
        "status reads the current review/control-plane projection",
    ),
    (
        "dev/scripts/devctl.py process-cleanup",
        "process cleanup verifies host state and must stay ordered",
    ),
    (
        "dev/scripts/devctl.py test-python",
        "focused pytest add-on should not compete with guard subprocesses for CPU",
    ),
    (
        "check_active_plan_sync.py",
        "active-plan sync reads mutable plan projections",
    ),
    (
        "check_system_picture_freshness.py",
        "system-picture freshness consumes generated projection state",
    ),
    (
        "check_review_snapshot_freshness.py",
        "review snapshot freshness depends on current review-state projections",
    ),
    (
        "check_instruction_surface_sync.py",
        "instruction-surface sync consumes generated instruction projections",
    ),
    (
        "check_review_channel_bridge.py",
        "review-channel bridge checks current bridge/review projections",
    ),
    (
        "check_startup_authority_contract.py",
        "startup authority consumes current startup and review projections",
    ),
    (
        "check_review_surface_consistency.py",
        "review-surface consistency requires one stable proof-tick snapshot",
    ),
    (
        "check_tandem_consistency.py",
        "tandem consistency consumes current collaboration projections",
    ),
    (
        "check_multi_agent_sync.py",
        "multi-agent sync consumes current agent-loop/work-board projections",
    ),
)


def build_planned_rows(
    *,
    bundle_name: str,
    bundle_commands: list[str],
    risk_addons: list[dict],
    policy_path: str | None,
    since_ref: str | None,
    head_ref: str,
) -> list[dict[str, str]]:
    planned_rows = [
        _planned_row(
            source=bundle_name,
            command=command,
            policy_path=policy_path,
            since_ref=since_ref,
            head_ref=head_ref,
        )
        for command in bundle_commands
    ]
    for addon in risk_addons:
        planned_rows.extend(
            _planned_row(
                source=addon["id"],
                command=command,
                policy_path=policy_path,
                since_ref=since_ref,
                head_ref=head_ref,
            )
            for command in addon["commands"]
        )
    return planned_rows


def _planned_row(
    *,
    source: str,
    command: str,
    policy_path: str | None,
    since_ref: str | None,
    head_ref: str,
) -> dict[str, str]:
    normalized_command = normalize_router_command(
        command,
        policy_path,
        since_ref=since_ref,
        head_ref=head_ref,
    )
    safety, reason = _parallel_safety_for_command(normalized_command)
    return {
        "source": source,
        "command": normalized_command,
        "parallel_safety": safety,
        "parallel_reason": reason,
    }


def _parallel_safety_for_command(command: str) -> tuple[str, str]:
    for marker, reason in _SERIAL_REQUIRED_COMMAND_MARKERS:
        if marker in command:
            return "serial_required", reason
    return "parallel_safe", "independent guard/probe command"


__all__ = ["build_planned_rows"]
