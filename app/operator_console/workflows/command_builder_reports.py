"""Workflow report parsing and evaluation helpers for the Operator Console."""

from __future__ import annotations

import json
from typing import Any, Mapping

from ..state.core.value_coercion import safe_int


def parse_review_channel_report(output: str) -> dict[str, Any]:
    """Parse a JSON review-channel payload for the Start Swarm flow."""
    report = _parse_json_report(output, report_name="review-channel")
    return report


def parse_operator_decision_report(output: str) -> dict[str, Any]:
    """Parse a JSON operator-decision payload for approval routing."""
    report = _parse_json_report(output, report_name="operator-decision")
    return report


def parse_orchestrate_status_report(output: str) -> dict[str, Any]:
    """Parse a JSON orchestration-audit payload."""
    report = _parse_json_report(output, report_name="orchestrate-status")
    return report


def parse_swarm_run_report(output: str) -> dict[str, Any]:
    """Parse a JSON swarm-run payload."""
    report = _parse_json_report(output, report_name="swarm_run")
    return report


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
    heartbeat_note = _heartbeat_refresh_note(report)
    return (
        True,
        " ".join(
            bit
            for bit in (
                f"Preflight ok: {codex_lanes} Codex lanes and {claude_lanes} Claude lanes ready.",
                heartbeat_note,
            )
            if bit
        ),
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
    heartbeat_note = _heartbeat_refresh_note(report)
    return (
        True,
        " ".join(
            bit
            for bit in (
                f"Swarm started: {codex_lanes} Codex lanes and {claude_lanes} Claude lanes launched.",
                heartbeat_note,
            )
            if bit
        ),
    )


def evaluate_review_channel_launch(
    report: Mapping[str, object],
    *,
    live: bool,
) -> tuple[bool, str]:
    """Return a user-facing outcome for direct launch or dry-run commands."""
    codex_lanes = safe_int(report.get("codex_lane_count"))
    claude_lanes = safe_int(report.get("claude_lane_count"))
    if not bool(report.get("ok")):
        fallback = "Live launch failed." if live else "Dry run failed."
        return False, _first_report_message(report, fallback=fallback)
    if live:
        if not bool(report.get("launched")):
            return False, "Live launch did not open the requested sessions."
        heartbeat_note = _heartbeat_refresh_note(report)
        return (
            True,
            " ".join(
                bit
                for bit in (
                    f"Live launch started: {codex_lanes} Codex lanes and {claude_lanes} Claude lanes launched.",
                    heartbeat_note,
                )
                if bit
            ),
        )
    heartbeat_note = _heartbeat_refresh_note(report)
    return (
        True,
        " ".join(
            bit
            for bit in (
                f"Dry run ready: {codex_lanes} Codex lanes and {claude_lanes} Claude lanes configured.",
                heartbeat_note,
            )
            if bit
        ),
    )


def evaluate_review_channel_rollover(report: Mapping[str, object]) -> tuple[bool, str]:
    """Return a user-facing outcome for rollover commands."""
    if not bool(report.get("ok")):
        return False, _first_report_message(report, fallback="Rollover failed.")
    if bool(report.get("handoff_ack_required")):
        ack_observed = report.get("handoff_ack_observed")
        if isinstance(ack_observed, bool):
            if ack_observed:
                return True, "Rollover completed and fresh-session ACK was observed."
            return False, "Rollover completed but fresh-session ACK was not observed."
    return True, "Rollover completed through the shared review-channel flow."


def evaluate_review_channel_post(
    report: Mapping[str, object],
    *,
    target_agent: str,
) -> tuple[bool, str]:
    """Return a user-facing outcome for review-channel post commands."""
    if not bool(report.get("ok")):
        return False, _first_report_message(
            report,
            fallback=f"Live summary post to {target_agent} failed.",
        )
    packet = report.get("packet")
    if isinstance(packet, Mapping):
        packet_id = packet.get("packet_id")
        status = packet.get("status")
        if isinstance(packet_id, str) and packet_id.strip():
            state_suffix = f" [{status}]" if isinstance(status, str) and status else ""
            return (
                True,
                f"Live summary request posted to {target_agent} as {packet_id}{state_suffix}.",
            )
    return True, f"Live summary request posted to {target_agent}."


def evaluate_orchestrate_status_report(
    report: Mapping[str, object],
) -> tuple[bool, str]:
    """Return a user-facing outcome for orchestration audits."""
    if not bool(report.get("ok")):
        return False, _first_report_message(report, fallback="Workflow audit failed.")

    git = report.get("git")
    branch = "current branch"
    changed_count = 0
    if isinstance(git, Mapping):
        raw_branch = git.get("branch")
        if isinstance(raw_branch, str) and raw_branch.strip():
            branch = raw_branch.strip()
        changed_count = safe_int(git.get("changed_count"))
    return (
        True,
        " ".join(
            bit
            for bit in (
                (
                    "Workflow audit ok: active-plan sync and multi-agent sync are "
                    f"green on {branch} ({changed_count} changed paths)."
                ),
                _first_warning_message(report),
            )
            if bit
        ),
    )


def evaluate_swarm_run_report(report: Mapping[str, object]) -> tuple[bool, str]:
    """Return a user-facing outcome for markdown-plan loop runs."""
    continuous = report.get("continuous")
    cycles_completed = 0
    max_cycles = 0
    stop_reason = "unknown"
    if isinstance(continuous, Mapping):
        cycles_completed = safe_int(continuous.get("cycles_completed"))
        max_cycles = safe_int(continuous.get("max_cycles"))
        raw_stop_reason = continuous.get("stop_reason")
        if isinstance(raw_stop_reason, str) and raw_stop_reason.strip():
            stop_reason = raw_stop_reason.strip()

    mp_scope = str(report.get("mp_scope") or "selected plan").strip() or "selected plan"
    run_dir = str(report.get("run_dir") or "").strip()
    run_dir_note = f" Run bundle: {run_dir}." if run_dir else ""
    next_step_note = _first_string_list_item(report.get("next_steps"))

    if not bool(report.get("ok")):
        detail = _first_report_message(
            report,
            fallback=(
                f"Plan loop stopped after {max(1, cycles_completed)} cycle(s) "
                f"for {mp_scope}."
            ),
        )
        return False, f"{detail}{run_dir_note}".strip()

    stop_detail = _swarm_stop_reason_message(
        stop_reason,
        cycles_completed=cycles_completed,
        max_cycles=max_cycles,
        mp_scope=mp_scope,
    )
    if next_step_note:
        stop_detail = f"{stop_detail} Latest focus: {next_step_note}."
    if run_dir_note:
        stop_detail += run_dir_note
    return True, stop_detail


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


def _first_warning_message(report: Mapping[str, object]) -> str:
    warnings = report.get("warnings")
    if isinstance(warnings, list):
        for item in warnings:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return ""


def _heartbeat_refresh_note(report: Mapping[str, object]) -> str:
    refresh = report.get("bridge_heartbeat_refresh")
    if not isinstance(refresh, Mapping):
        return ""
    refreshed_at = refresh.get("last_codex_poll_utc")
    if not isinstance(refreshed_at, str) or not refreshed_at.strip():
        return "Reviewer heartbeat was auto-refreshed before launch."
    return f"Reviewer heartbeat was auto-refreshed at {refreshed_at} before launch."


def _first_string_list_item(value: object) -> str:
    if not isinstance(value, list):
        return ""
    for item in value:
        if isinstance(item, str) and item.strip():
            return item.strip()
    return ""


def _swarm_stop_reason_message(
    stop_reason: str,
    *,
    cycles_completed: int,
    max_cycles: int,
    mp_scope: str,
) -> str:
    if stop_reason == "plan_complete":
        return f"Plan loop completed for {mp_scope}: no unchecked checklist items remain."
    if stop_reason == "max_cycles_reached":
        return (
            f"Plan loop completed {cycles_completed}/{max_cycles} cycles for {mp_scope} "
            "and hit the configured cycle limit."
        )
    if stop_reason == "single_cycle_complete":
        return f"Plan run completed 1 cycle for {mp_scope}."
    if stop_reason == "no_cycles_executed":
        return f"Plan loop did not execute any cycles for {mp_scope}."
    return (
        f"Plan loop completed {max(1, cycles_completed)} cycle(s) for {mp_scope} "
        f"with stop reason `{stop_reason}`."
    )


def _parse_json_report(output: str, *, report_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:  # pragma: no cover - exercised via tests
        raise ValueError(f"{report_name} output was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{report_name} output was not a JSON object")
    return payload
