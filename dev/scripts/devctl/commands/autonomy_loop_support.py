"""Validation/error helpers for `devctl autonomy-loop`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from ..autonomy_loop_helpers import iso_z, render_markdown, utc_now
from ..common import pipe_output, write_output


def validate_args(args) -> str | None:
    if args.max_rounds < 1:
        return "Error: --max-rounds must be >= 1"
    if args.max_hours <= 0:
        return "Error: --max-hours must be > 0"
    if args.max_tasks < 1:
        return "Error: --max-tasks must be >= 1"
    if args.checkpoint_every < 1:
        return "Error: --checkpoint-every must be >= 1"
    if args.loop_max_attempts < 1:
        return "Error: --loop-max-attempts must be >= 1"
    if args.poll_seconds < 5:
        return "Error: --poll-seconds must be >= 5"
    if args.timeout_seconds < 60:
        return "Error: --timeout-seconds must be >= 60"
    if args.max_packet_age_hours <= 0:
        return "Error: --max-packet-age-hours must be > 0"
    if args.max_draft_chars < 200:
        return "Error: --max-draft-chars must be >= 200"
    if args.terminal_trace_lines < 1:
        return "Error: --terminal-trace-lines must be >= 1"
    return None


def write_validation_error(
    args,
    warnings: list[str],
    errors: list[str],
    *,
    repo: str,
    plan_id: str,
    branch_base: str,
    mode_requested: str,
    mode_effective: str,
    packet_root: Path,
    queue_root: Path,
) -> int:
    report = {
        "command": "autonomy-loop",
        "timestamp": iso_z(utc_now()),
        "ok": False,
        "resolved": False,
        "reason": "policy_denied",
        "plan_id": plan_id,
        "repo": repo,
        "branch_base": branch_base,
        "mode_requested": mode_requested,
        "mode_effective": mode_effective,
        "packet_root": str(packet_root),
        "queue_root": str(queue_root),
        "warnings": warnings,
        "errors": errors,
        "rounds": [],
    }
    output = json.dumps(report, indent=2) if args.format == "json" else render_markdown(report)
    write_output(output, args.output)
    if args.json_output:
        write_output(json.dumps(report, indent=2), args.json_output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return 1


def write_round_phone_status(
    *,
    payload: dict[str, Any],
    markdown: str,
    round_dir: Path,
    phone_root: Path,
    controller_run_id: str,
    round_index: int,
    latest_json: Path,
    latest_md: Path,
) -> tuple[Path, Path]:
    round_phone_json = round_dir / "phone-status.json"
    round_phone_md = round_dir / "phone-status.md"
    round_phone_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    round_phone_md.write_text(markdown, encoding="utf-8")

    phone_history_json = phone_root / f"{controller_run_id}-r{round_index:03d}.json"
    phone_history_md = phone_root / f"{controller_run_id}-r{round_index:03d}.md"
    phone_history_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    phone_history_md.write_text(markdown, encoding="utf-8")
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_md.write_text(markdown, encoding="utf-8")
    return round_phone_json, round_phone_md


def write_final_phone_status(
    *,
    payload: dict[str, Any],
    markdown: str,
    phone_root: Path,
    controller_run_id: str,
    latest_json: Path,
    latest_md: Path,
) -> tuple[Path, Path]:
    final_phone_json = phone_root / f"{controller_run_id}-final.json"
    final_phone_md = phone_root / f"{controller_run_id}-final.md"
    final_phone_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    final_phone_md.write_text(markdown, encoding="utf-8")
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_md.write_text(markdown, encoding="utf-8")
    return final_phone_json, final_phone_md


def emit_controller_report(
    *,
    args,
    report: dict[str, Any],
    render_markdown_fn: Callable[[dict[str, Any]], str],
    run_packet_root: Path,
) -> int:
    summary_json_path = run_packet_root / "controller-summary.json"
    summary_md_path = run_packet_root / "controller-summary.md"
    summary_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary_md_path.write_text(render_markdown_fn(report), encoding="utf-8")
    report["summary_json"] = str(summary_json_path)
    report["summary_md"] = str(summary_md_path)

    output = json.dumps(report, indent=2) if args.format == "json" else render_markdown_fn(report)
    write_output(output, args.output)
    if args.json_output:
        write_output(json.dumps(report, indent=2), args.json_output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return 0


def build_controller_report(
    *,
    finished_at_iso: str,
    ok: bool,
    resolved: bool,
    reason: str,
    plan_id: str,
    controller_run_id: str,
    repo: str,
    branch_base: str,
    mode_requested: str,
    mode_effective: str,
    loop_branch_mode: str,
    max_rounds: int,
    max_hours: float,
    max_tasks: int,
    rounds_completed: int,
    tasks_completed: int,
    elapsed_hours: float,
    run_packet_root: Path,
    queue_root: Path,
    latest_packet: str | None,
    latest_working_branch: str | None,
    phone_latest_json: Path,
    phone_latest_md: Path,
    final_phone_json: Path,
    final_phone_md: Path,
    warnings: list[str],
    errors: list[str],
    rounds: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "command": "autonomy-loop",
        "timestamp": finished_at_iso,
        "ok": ok,
        "resolved": resolved,
        "reason": reason,
        "plan_id": plan_id,
        "controller_run_id": controller_run_id,
        "repo": repo,
        "branch_base": branch_base,
        "mode_requested": mode_requested,
        "mode_effective": mode_effective,
        "loop_branch_mode": loop_branch_mode,
        "max_rounds": max_rounds,
        "max_hours": max_hours,
        "max_tasks": max_tasks,
        "rounds_completed": rounds_completed,
        "tasks_completed": tasks_completed,
        "elapsed_hours": elapsed_hours,
        "packet_root": str(run_packet_root),
        "queue_root": str(queue_root),
        "latest_packet": latest_packet,
        "latest_working_branch": latest_working_branch,
        "phone_status_latest_json": str(phone_latest_json),
        "phone_status_latest_md": str(phone_latest_md),
        "phone_status_final_json": str(final_phone_json),
        "phone_status_final_md": str(final_phone_md),
        "warnings": warnings,
        "errors": errors,
        "rounds": rounds,
    }
