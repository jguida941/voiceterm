"""Workflow command-construction helpers for the Operator Console."""

from __future__ import annotations

import json
import shlex
import sys
from typing import Sequence

from ..collaboration.context_pack_refs import context_pack_refs_payload
from ..state.core.models import ApprovalRequest

DEVCTL_ENTRYPOINT = "dev/scripts/devctl.py"
DEVCTL_PYTHON = sys.executable
REVIEW_CHANNEL_SUBCOMMAND = "review-channel"
OPERATOR_DECISION_MODULE = "app.operator_console.state.review.operator_decisions"
LIVE_REVIEW_CHANNEL_TERMINAL = "terminal-app"
LIVE_REVIEW_CHANNEL_PLATFORM = "darwin"


def _base_devctl(
    subcommand: str,
    *,
    output_format: str,
    extra_flags: list[str] | None = None,
) -> list[str]:
    """Build a canonical devctl command prefix plus optional flags."""
    cmd = [DEVCTL_PYTHON, DEVCTL_ENTRYPOINT, subcommand]
    if extra_flags:
        cmd.extend(extra_flags)
    cmd.extend(["--format", output_format])
    return cmd


def _base_review_channel(
    *,
    action: str,
    live: bool,
    output_format: str,
    refresh_bridge_heartbeat_if_stale: bool = False,
    extra_flags: list[str] | None = None,
) -> list[str]:
    """Build the shared prefix for any review-channel invocation."""
    terminal_mode = LIVE_REVIEW_CHANNEL_TERMINAL if live else "none"
    cmd = [
        DEVCTL_PYTHON,
        DEVCTL_ENTRYPOINT,
        REVIEW_CHANNEL_SUBCOMMAND,
        "--action",
        action,
        "--terminal",
        terminal_mode,
        "--format",
        output_format,
    ]
    if extra_flags:
        cmd.extend(extra_flags)
    if refresh_bridge_heartbeat_if_stale:
        cmd.append("--refresh-bridge-heartbeat-if-stale")
    if not live:
        cmd.append("--dry-run")
    return cmd


def build_launch_command(
    *,
    live: bool,
    output_format: str = "md",
    refresh_bridge_heartbeat_if_stale: bool = False,
) -> list[str]:
    """Build the current review-channel launch command."""
    return _base_review_channel(
        action="launch",
        live=live,
        output_format=output_format,
        refresh_bridge_heartbeat_if_stale=refresh_bridge_heartbeat_if_stale,
    )


def build_review_channel_post_command(
    *,
    to_agent: str,
    summary: str,
    body: str,
    output_format: str = "json",
    from_agent: str = "operator",
    kind: str = "draft",
    requested_action: str = "review_only",
    policy_hint: str = "review_only",
) -> list[str]:
    """Build a typed review-channel event post command."""
    normalized_to = to_agent.strip().lower()
    normalized_from = from_agent.strip().lower()
    normalized_kind = kind.strip().lower()
    if normalized_to not in {"codex", "claude", "cursor", "operator", "system"}:
        raise ValueError("to_agent must be codex/claude/cursor/operator/system")
    if normalized_from not in {"codex", "claude", "cursor", "operator", "system"}:
        raise ValueError("from_agent must be codex/claude/cursor/operator/system")
    if normalized_kind not in {
        "finding",
        "question",
        "draft",
        "instruction",
        "action_request",
        "approval_request",
        "decision",
        "system_notice",
    }:
        raise ValueError("kind is not a valid review-channel event kind")
    cleaned_summary = summary.strip()
    if not cleaned_summary:
        raise ValueError("summary must not be empty")
    if not body.strip():
        raise ValueError("body must not be empty")
    return _base_devctl(
        REVIEW_CHANNEL_SUBCOMMAND,
        output_format=output_format,
        extra_flags=[
            "--action",
            "post",
            "--from-agent",
            normalized_from,
            "--to-agent",
            normalized_to,
            "--kind",
            normalized_kind,
            "--summary",
            cleaned_summary,
            "--body",
            body,
            "--requested-action",
            requested_action,
            "--policy-hint",
            policy_hint,
        ],
    )


def build_rollover_command(
    *,
    threshold_pct: int,
    await_ack_seconds: int,
    live: bool,
    output_format: str = "md",
    refresh_bridge_heartbeat_if_stale: bool = False,
) -> list[str]:
    """Build the current review-channel rollover command."""
    if threshold_pct < 1 or threshold_pct > 100:
        raise ValueError("threshold_pct must be between 1 and 100")
    if await_ack_seconds < 0:
        raise ValueError("await_ack_seconds must be zero or greater")
    return _base_review_channel(
        action="rollover",
        live=live,
        output_format=output_format,
        refresh_bridge_heartbeat_if_stale=refresh_bridge_heartbeat_if_stale,
        extra_flags=[
            "--rollover-threshold-pct",
            str(threshold_pct),
            "--await-ack-seconds",
            str(await_ack_seconds),
        ],
    )


def build_status_command(
    *,
    include_ci: bool = True,
    require_ci: bool = False,
    output_format: str = "md",
) -> list[str]:
    """Build the current repo-owned status command."""
    flags: list[str] = []
    if include_ci or require_ci:
        flags.append("--ci")
    if require_ci:
        flags.append("--require-ci")
    return _base_devctl("status", output_format=output_format, extra_flags=flags)


def build_triage_command(
    *,
    include_ci: bool = True,
    output_format: str = "md",
) -> list[str]:
    """Build the current repo-owned triage command."""
    flags = ["--ci"] if include_ci else []
    return _base_devctl("triage", output_format=output_format, extra_flags=flags)


def build_process_audit_command(
    *,
    strict: bool = True,
    output_format: str = "md",
) -> list[str]:
    """Build the current repo-owned process-audit command."""
    flags = ["--strict"] if strict else []
    return _base_devctl(
        "process-audit",
        output_format=output_format,
        extra_flags=flags,
    )


def build_orchestrate_status_command(*, output_format: str = "md") -> list[str]:
    """Build the current repo-owned orchestration audit command."""
    return _base_devctl("orchestrate-status", output_format=output_format)


def build_swarm_run_command(
    *,
    plan_doc: str,
    mp_scope: str,
    output_format: str = "json",
    continuous: bool = True,
    continuous_max_cycles: int = 10,
    feedback_sizing: bool = True,
    run_label: str | None = None,
) -> list[str]:
    """Build the guarded markdown-plan loop command used by the GUI."""
    cleaned_plan_doc = plan_doc.strip()
    cleaned_mp_scope = mp_scope.strip()
    if not cleaned_plan_doc:
        raise ValueError("plan_doc must not be empty")
    if not cleaned_mp_scope:
        raise ValueError("mp_scope must not be empty")
    if continuous_max_cycles < 1:
        raise ValueError("continuous_max_cycles must be greater than zero")

    flags = [
        "--plan-doc",
        cleaned_plan_doc,
        "--mp-scope",
        cleaned_mp_scope,
        "--mode",
        "report-only",
    ]
    if continuous:
        flags.append("--continuous")
        flags.extend(["--continuous-max-cycles", str(continuous_max_cycles)])
    if feedback_sizing:
        flags.append("--feedback-sizing")
    else:
        flags.append("--no-feedback-sizing")
    if run_label and run_label.strip():
        flags.extend(["--run-label", run_label.strip()])
    return _base_devctl("swarm_run", output_format=output_format, extra_flags=flags)


def terminal_app_live_supported(*, platform_name: str | None = None) -> bool:
    """Return whether Terminal.app-backed live review commands are available."""
    current_platform = platform_name or sys.platform
    return current_platform == LIVE_REVIEW_CHANNEL_PLATFORM


def terminal_app_live_support_detail(*, platform_name: str | None = None) -> str:
    """Describe the current Terminal.app live-command capability honestly."""
    current_platform = platform_name or sys.platform
    if terminal_app_live_supported(platform_name=current_platform):
        return (
            "Live launch, rollover, and Start Swarm can open Terminal.app review "
            "sessions from this macOS host."
        )
    return (
        "Live launch, rollover, and Start Swarm use Terminal.app session spawning "
        f"and are only available on macOS (current platform: {current_platform}). "
        "Use Dry Run to execute the repo-visible preflight without opening live sessions."
    )


def build_operator_decision_command(
    *,
    approval: ApprovalRequest,
    decision: str,
    note: str = "",
    output_format: str = "json",
) -> list[str]:
    """Build the typed wrapper command for operator approve/deny actions."""
    normalized_decision = decision.strip().lower()
    if normalized_decision not in {"approve", "deny"}:
        raise ValueError("decision must be `approve` or `deny`")

    approval_json = json.dumps(
        {
            "packet_id": approval.packet_id,
            "from_agent": approval.from_agent,
            "to_agent": approval.to_agent,
            "summary": approval.summary,
            "body": approval.body,
            "policy_hint": approval.policy_hint,
            "requested_action": approval.requested_action,
            "status": approval.status,
            "evidence_refs": list(approval.evidence_refs),
            "context_pack_refs": context_pack_refs_payload(approval.context_pack_refs),
        }
    )
    cmd = [
        DEVCTL_PYTHON,
        "-m",
        OPERATOR_DECISION_MODULE,
        "--repo-root",
        ".",
        "--decision",
        normalized_decision,
        "--approval-json",
        approval_json,
        "--format",
        output_format,
    ]
    if note.strip():
        cmd.extend(["--note", note])
    return cmd


def render_command(command: Sequence[str]) -> str:
    """Return a shell-rendered representation of a command list."""
    return shlex.join(list(command))
