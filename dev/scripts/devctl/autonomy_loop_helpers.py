"""Shared helper logic for `devctl autonomy-loop`."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .config import REPO_ROOT

POLICY_PATH = REPO_ROOT / "dev/config/control_plane_policy.json"
DEFAULT_REPLAY_WINDOW_SECONDS = 300
HARD_REASON_CODES = {
    "source_run_sha_mismatch",
    "source_run_id_mismatch",
    "source_correlation_failed",
    "notification_comment_failed",
}


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def slug(value: str, *, fallback: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._")
    return (normalized or fallback)[:80]


def resolve_path(raw_path: str, *, relative_to_repo: bool = True) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute() or not relative_to_repo:
        return path
    return REPO_ROOT / path


def load_policy() -> dict[str, Any]:
    try:
        payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def autonomy_policy(payload: dict[str, Any]) -> dict[str, Any]:
    section = payload.get("autonomy_loop")
    return section if isinstance(section, dict) else {}


def allowed_branch(branch: str, policy: dict[str, Any]) -> bool:
    allowed = policy.get("allowed_branches")
    if not isinstance(allowed, list) or not allowed:
        return True
    normalized = {str(item).strip() for item in allowed if str(item).strip()}
    if not normalized:
        return True
    return branch in normalized


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# devctl autonomy-loop", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- resolved: {report.get('resolved')}")
    lines.append(f"- plan_id: {report.get('plan_id')}")
    lines.append(f"- controller_run_id: {report.get('controller_run_id')}")
    lines.append(f"- repo: {report.get('repo')}")
    lines.append(f"- branch_base: {report.get('branch_base')}")
    lines.append(f"- mode_requested: {report.get('mode_requested')}")
    lines.append(f"- mode_effective: {report.get('mode_effective')}")
    lines.append(f"- rounds_completed: {report.get('rounds_completed')}")
    lines.append(f"- tasks_completed: {report.get('tasks_completed')}")
    lines.append(f"- reason: {report.get('reason')}")
    lines.append(f"- packet_root: {report.get('packet_root')}")
    lines.append(f"- queue_root: {report.get('queue_root')}")
    lines.append(f"- latest_packet: {report.get('latest_packet') or 'n/a'}")
    lines.append(f"- phone_status_latest_json: {report.get('phone_status_latest_json') or 'n/a'}")
    lines.append(f"- phone_status_latest_md: {report.get('phone_status_latest_md') or 'n/a'}")
    lines.append(f"- latest_working_branch: {report.get('latest_working_branch') or 'n/a'}")
    warnings = report.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.append("- warnings: " + " | ".join(str(row) for row in warnings))
    errors = report.get("errors", [])
    if isinstance(errors, list) and errors:
        lines.append("- errors: " + " | ".join(str(row) for row in errors))

    lines.append("")
    lines.append("## Rounds")
    lines.append("")
    rounds = report.get("rounds", [])
    if not isinstance(rounds, list) or not rounds:
        lines.append("- none")
    else:
        for row in rounds:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- "
                + f"r{row.get('round')} "
                + f"branch={row.get('working_branch')} "
                + f"unresolved={row.get('unresolved_count')} "
                + f"risk={row.get('risk')} "
                + f"reason={row.get('triage_reason')}"
            )
            if row.get("packet_path"):
                lines.append(f"  packet: {row.get('packet_path')}")
    return "\n".join(lines)


def json_load(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, str(exc)
    except json.JSONDecodeError as exc:
        return None, f"invalid json ({exc})"
    if not isinstance(payload, dict):
        return None, "expected object json"
    return payload, None


def terminal_trace(triage_report: dict[str, Any], max_lines: int) -> list[str]:
    lines: list[str] = []
    attempts = triage_report.get("attempts", [])
    if isinstance(attempts, list):
        for attempt in attempts:
            if not isinstance(attempt, dict):
                continue
            row = (
                f"attempt={attempt.get('attempt')} "
                f"run_id={attempt.get('run_id')} "
                f"sha={attempt.get('run_sha')} "
                f"conclusion={attempt.get('run_conclusion')} "
                f"backlog={attempt.get('backlog_count')} "
                f"status={attempt.get('status')}"
            )
            lines.append(row)
            message = str(attempt.get("message") or "").strip()
            if message:
                lines.append(f"note={message}")
    if not lines:
        lines.append(f"reason={triage_report.get('reason')}")
    if max_lines <= 0:
        return []
    return lines[:max_lines]


def packet_risk(loop_packet_report: dict[str, Any], triage_report: dict[str, Any]) -> str:
    risk = str(loop_packet_report.get("risk") or "").strip().lower()
    if risk in {"low", "medium", "high"}:
        return risk
    unresolved = int(triage_report.get("unresolved_count") or 0)
    if unresolved <= 0:
        return "low"
    if unresolved >= 8:
        return "high"
    return "medium"


def build_triage_args(
    *,
    repo: str,
    loop_branch: str,
    workflow: str,
    mode: str,
    fix_command: str | None,
    max_attempts: int,
    run_list_limit: int,
    poll_seconds: int,
    timeout_seconds: int,
    notify: str,
    comment_target: str,
    comment_pr_number: int | None,
    bundle_dir: Path,
    bundle_prefix: str,
    dry_run: bool,
    output_path: Path,
) -> SimpleNamespace:
    return SimpleNamespace(
        repo=repo,
        branch=loop_branch,
        workflow=workflow,
        max_attempts=max_attempts,
        run_list_limit=run_list_limit,
        poll_seconds=poll_seconds,
        timeout_seconds=timeout_seconds,
        mode=mode,
        fix_command=fix_command,
        emit_bundle=True,
        bundle_dir=str(bundle_dir),
        bundle_prefix=bundle_prefix,
        mp_proposal=False,
        mp_proposal_path=None,
        notify=notify,
        comment_target=comment_target,
        comment_pr_number=comment_pr_number,
        source_run_id=None,
        source_run_sha=None,
        source_event="workflow_dispatch",
        dry_run=dry_run,
        format="json",
        output=str(output_path),
        json_output=None,
        pipe_command=None,
        pipe_args=None,
    )


def build_loop_packet_args(
    *,
    source_json: Path,
    max_age_hours: float,
    max_draft_chars: int,
    allow_auto_send: bool,
    output_path: Path,
) -> SimpleNamespace:
    return SimpleNamespace(
        source_json=[str(source_json)],
        prefer_source="triage-loop",
        max_age_hours=max_age_hours,
        max_draft_chars=max_draft_chars,
        allow_auto_send=allow_auto_send,
        format="json",
        output=str(output_path),
        pipe_command=None,
        pipe_args=None,
    )


def build_checkpoint_packet(
    *,
    plan_id: str,
    controller_run_id: str,
    branch_base: str,
    working_branch: str,
    round_index: int,
    triage_report: dict[str, Any],
    loop_packet_report: dict[str, Any],
    replay_window_seconds: int,
    trace_lines: int,
    packet_source_refs: list[str],
) -> dict[str, Any]:
    now = utc_now()
    risk = packet_risk(loop_packet_report, triage_report)
    mode = str(triage_report.get("mode") or "report-only")
    unresolved = int(triage_report.get("unresolved_count") or 0)
    requires_approval = risk == "high" or mode != "report-only" or unresolved > 0
    nonce = secrets.token_hex(12)
    id_seed = "|".join(
        [
            plan_id,
            controller_run_id,
            str(round_index),
            str(triage_report.get("timestamp") or ""),
            str(loop_packet_report.get("summary") or ""),
        ]
    )
    idempotency_key = hashlib.sha256(id_seed.encode("utf-8")).hexdigest()[:24]

    terminal_packet = loop_packet_report.get("terminal_packet")
    if not isinstance(terminal_packet, dict):
        terminal_packet = {}

    return {
        "schema_version": 1,
        "plan_id": plan_id,
        "controller_run_id": controller_run_id,
        "round": round_index,
        "timestamp_utc": iso_z(now),
        "source": "triage-loop",
        "working_branch": working_branch,
        "promotion_branch": branch_base,
        "risk": risk,
        "requires_approval": requires_approval,
        "draft_text": str(terminal_packet.get("draft_text") or "").strip(),
        "terminal_packet": terminal_packet,
        "proposed_actions": [
            str(row).strip()
            for row in (loop_packet_report.get("next_actions") or [])
            if str(row).strip()
        ],
        "evidence_refs": packet_source_refs,
        "idempotency_key": idempotency_key,
        "nonce": nonce,
        "expires_at_utc": iso_z(now + timedelta(seconds=max(1, replay_window_seconds))),
        "status": "pending",
        "reason_code": str(triage_report.get("reason") or "unknown"),
        "unresolved_count": unresolved,
        "terminal_trace": terminal_trace(triage_report, trace_lines),
    }
