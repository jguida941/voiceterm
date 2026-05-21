"""Agent-supervision signals consumed by `/develop` orchestration."""

from __future__ import annotations

import shlex
from collections.abc import Mapping
from pathlib import Path

from ...runtime.agent_supervise_driver import (
    AgentSuperviseInput,
    AgentSuperviseReport,
    evaluate_agent_supervision,
)
from ...runtime.relaunch_loop_models import DEFAULT_RELAUNCH_WINDOW_SECONDS
from .models import DevelopmentAgentLoopInput, DevelopmentOrchestrationSignal


def agent_supervise_signals(
    repo_root: Path,
    review_state: Mapping[str, object],
    rows: tuple[DevelopmentAgentLoopInput, ...],
) -> tuple[DevelopmentOrchestrationSignal, ...]:
    """Project non-healthy supervision reports into `/develop` blockers."""
    signals: list[DevelopmentOrchestrationSignal] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        actor = row.actor_id.strip()
        if not actor:
            continue
        role = row.actor_role.strip() or "reviewer"
        key = (actor, role, row.session_id.strip())
        if key in seen:
            continue
        seen.add(key)
        report = evaluate_agent_supervision(
            AgentSuperviseInput(
                actor=actor,
                provider=actor,
                role=role,
                session_id=row.session_id,
                repo_root=repo_root,
                review_state=review_state,
                staleness_threshold_seconds=DEFAULT_RELAUNCH_WINDOW_SECONDS,
            )
        )
        if report.status in {"healthy", "ignored_helper_closed"}:
            # v4.55.1 priority 1 (rev_pkt_4762/4763): a closed read-only
            # helper sidecar audited via explicit `--session-id` produces a
            # typed nonblocking AgentSuperviseReport; skip it so develop
            # orchestration does not promote a dead helper into a blocker.
            continue
        signals.append(_signal_for_report(report))
    return tuple(signals)


def _signal_for_report(report: AgentSuperviseReport) -> DevelopmentOrchestrationSignal:
    command = _supervise_command(report)
    status = "action_required" if report.status == "spawn_authorized" else "blocked"
    next_command = report.next_command or command
    return DevelopmentOrchestrationSignal(
        source="agent-supervise",
        signal_id=f"agent-supervise:{report.actor}:{report.role}:{report.session_id}",
        status=status,
        summary=_summary(report),
        source_surface="agent-supervise",
        severity=_severity(report),
        recommended_action=(
            "launch_replacement_agent"
            if report.status == "spawn_authorized"
            else "resolve_agent_supervision_blocker"
        ),
        closure_check_command=command,
        source_command=command,
        suggested_command=next_command,
    )


def _summary(report: AgentSuperviseReport) -> str:
    parts = [
        f"agent-supervise {report.actor}:{report.role}",
        f"status={report.status}",
        f"process_state={report.process_state}",
    ]
    if report.trigger_reason:
        parts.append(f"trigger={report.trigger_reason}")
    if report.continuation_anchor_packet_id:
        parts.append(f"continuation_anchor={report.continuation_anchor_packet_id}")
    if report.blocked_reasons:
        parts.append("blocked_reasons=" + ",".join(report.blocked_reasons))
    return " ".join(parts)


def _severity(report: AgentSuperviseReport) -> str:
    if report.process_exit_detected or report.status == "spawn_authorized":
        return "high"
    if report.freeze_detected:
        return "medium"
    return "low"


def _supervise_command(report: AgentSuperviseReport) -> str:
    parts = [
        "python3",
        "dev/scripts/devctl.py",
        "agent-supervise",
        "--actor",
        report.actor or "codex",
        "--provider",
        report.provider or report.actor or "codex",
        "--role",
        report.role or "reviewer",
    ]
    if report.session_id:
        parts.extend(["--session-id", report.session_id])
    parts.extend(
        ["--staleness-threshold-seconds", str(report.staleness_threshold_seconds)]
    )
    parts.extend(["--format", "json"])
    return shlex.join(parts)


__all__ = ["agent_supervise_signals"]
