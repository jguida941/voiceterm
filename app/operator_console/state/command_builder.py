"""Command builders for the optional PyQt6 Operator Console.

All command construction routes through this module so the GUI→typed-command
boundary is auditable in one place. The canonical devctl entrypoint path and
the local operator-decision module path are defined here as constants; flag
names and choice values mirror the current argparse definitions used by those
surfaces.
"""

from __future__ import annotations

import json
import shlex
import sys
from typing import Any, Mapping, Sequence

from .models import ApprovalRequest
from .value_coercion import safe_int

# Canonical path to the repo-owned devctl entrypoint (relative to repo root).
# If the entrypoint moves, update this constant and all tests that reference it.
DEVCTL_ENTRYPOINT = "dev/scripts/devctl.py"
DEVCTL_PYTHON = sys.executable
REVIEW_CHANNEL_SUBCOMMAND = "review-channel"
OPERATOR_DECISION_MODULE = "app.operator_console.state.operator_decisions"
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
    if not live:
        cmd.append("--dry-run")
    return cmd


def build_launch_command(*, live: bool, output_format: str = "md") -> list[str]:
    """Build the current review-channel launch command."""
    return _base_review_channel(action="launch", live=live, output_format=output_format)


def build_rollover_command(
    *,
    threshold_pct: int,
    await_ack_seconds: int,
    live: bool,
    output_format: str = "md",
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


def parse_review_channel_report(output: str) -> dict[str, Any]:
    """Parse a JSON review-channel payload for the Start Swarm flow."""
    return _parse_json_report(output, report_name="review-channel")


def parse_operator_decision_report(output: str) -> dict[str, Any]:
    """Parse a JSON operator-decision payload for approval routing."""
    return _parse_json_report(output, report_name="operator-decision")


def evaluate_start_swarm_preflight(report: Mapping[str, object]) -> tuple[bool, str]:
    """Return whether the dry-run preflight is healthy enough for live launch."""
    codex_lanes = safe_int(report.get("codex_lane_count"))
    claude_lanes = safe_int(report.get("claude_lane_count"))
    if not bool(report.get("ok")):
        return False, _first_report_message(
            report,
            fallback="Start Swarm preflight failed.",
        )
    if not bool(report.get("bridge_active")):
        return False, "Start Swarm preflight blocked: review bridge is inactive."
    if codex_lanes < 1 or claude_lanes < 1:
        return False, "Start Swarm preflight blocked: lane assignments are incomplete."
    return (
        True,
        f"Preflight ok: {codex_lanes} Codex lanes and {claude_lanes} Claude lanes ready.",
    )


def evaluate_start_swarm_launch(report: Mapping[str, object]) -> tuple[bool, str]:
    """Return whether the live launch completed successfully."""
    codex_lanes = safe_int(report.get("codex_lane_count"))
    claude_lanes = safe_int(report.get("claude_lane_count"))
    if not bool(report.get("ok")):
        return False, _first_report_message(
            report,
            fallback="Start Swarm live launch failed.",
        )
    if not bool(report.get("launched")):
        return False, "Start Swarm live launch did not open the requested sessions."
    return (
        True,
        f"Swarm started: {codex_lanes} Codex lanes and {claude_lanes} Claude lanes launched.",
    )


def _first_report_message(
    report: Mapping[str, object],
    *,
    fallback: str,
) -> str:
    for key in ("errors", "warnings"):
        raw = report.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str) and item.strip():
                    return item.strip()
    return fallback


def _parse_json_report(output: str, *, report_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:  # pragma: no cover - exercised via tests
        raise ValueError(f"{report_name} output was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{report_name} output was not a JSON object")
    return payload
