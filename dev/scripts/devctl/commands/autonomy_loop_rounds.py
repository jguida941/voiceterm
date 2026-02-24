"""Round execution helpers for `devctl autonomy-loop`."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from ..autonomy_loop_helpers import (
    HARD_REASON_CODES,
    build_checkpoint_packet,
    build_loop_packet_args,
    build_triage_args,
    json_load,
    packet_risk,
    utc_now,
)
from ..autonomy_phone_status import (
    build_phone_status,
    render_phone_status_markdown,
)
from . import loop_packet as loop_packet_command
from . import triage_loop as triage_loop_command
from .autonomy_loop_support import write_round_phone_status


def run_controller_rounds(
    *,
    args,
    repo: str,
    plan_id: str,
    branch_base: str,
    working_prefix: str,
    effective_mode: str,
    controller_run_id: str,
    run_packet_root: Path,
    queue_inbox: Path,
    phone_root: Path,
    phone_latest_json: Path,
    phone_latest_md: Path,
    replay_window_seconds: int,
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    started_at = utc_now()
    max_duration = timedelta(hours=float(args.max_hours))
    rounds: list[dict[str, Any]] = []
    tasks_completed = 0
    resolved = False
    reason = "max_rounds_reached"
    latest_packet: str | None = None
    latest_working_branch: str | None = None
    last_triage_report: dict[str, Any] = {}
    last_loop_packet_report: dict[str, Any] = {}
    last_checkpoint_packet: dict[str, Any] = {}

    for round_index in range(1, int(args.max_rounds) + 1):
        now = utc_now()
        elapsed = now - started_at
        if elapsed > max_duration:
            reason = "max_hours_reached"
            break
        if tasks_completed >= int(args.max_tasks):
            reason = "max_tasks_reached"
            break

        working_branch = f"{working_prefix}/{plan_id}/{controller_run_id}/r{round_index:03d}"
        latest_working_branch = working_branch
        loop_branch = branch_base if args.loop_branch_mode == "base" else working_branch

        round_dir = run_packet_root / f"round-{round_index:03d}"
        round_dir.mkdir(parents=True, exist_ok=True)
        triage_json_path = round_dir / "triage-loop.json"
        loop_packet_json_path = round_dir / "loop-packet.json"

        triage_args = build_triage_args(
            repo=repo,
            loop_branch=loop_branch,
            workflow=args.workflow,
            mode=effective_mode,
            fix_command=(args.fix_command or "").strip() or None,
            max_attempts=args.loop_max_attempts,
            run_list_limit=args.run_list_limit,
            poll_seconds=args.poll_seconds,
            timeout_seconds=args.timeout_seconds,
            notify=args.notify,
            comment_target=args.comment_target,
            comment_pr_number=args.comment_pr_number,
            bundle_dir=round_dir,
            bundle_prefix=f"coderabbit-ralph-loop-r{round_index:03d}",
            dry_run=bool(args.dry_run),
            output_path=triage_json_path,
        )
        triage_rc = triage_loop_command.run(triage_args)
        triage_report, triage_error = json_load(triage_json_path)
        if triage_error or triage_report is None:
            errors.append(f"round {round_index}: failed to read triage-loop report ({triage_error})")
            reason = "triage_report_missing"
            break

        loop_packet_args = build_loop_packet_args(
            source_json=triage_json_path,
            max_age_hours=args.max_packet_age_hours,
            max_draft_chars=args.max_draft_chars,
            allow_auto_send=bool(args.allow_auto_send),
            output_path=loop_packet_json_path,
        )
        loop_packet_rc = loop_packet_command.run(loop_packet_args)
        loop_packet_report, loop_packet_error = json_load(loop_packet_json_path)
        if loop_packet_error or loop_packet_report is None:
            errors.append(
                f"round {round_index}: failed to read loop-packet report ({loop_packet_error})"
            )
            reason = "packet_report_missing"
            break

        checkpoint_packet = build_checkpoint_packet(
            plan_id=plan_id,
            controller_run_id=controller_run_id,
            branch_base=branch_base,
            working_branch=working_branch,
            round_index=round_index,
            triage_report=triage_report,
            loop_packet_report=loop_packet_report,
            replay_window_seconds=replay_window_seconds,
            trace_lines=args.terminal_trace_lines,
            packet_source_refs=[str(triage_json_path), str(loop_packet_json_path)],
        )
        packet_id = str(checkpoint_packet.get("idempotency_key") or f"r{round_index:03d}")
        checkpoint_path = round_dir / "checkpoint-packet.json"
        checkpoint_path.write_text(json.dumps(checkpoint_packet, indent=2), encoding="utf-8")
        last_triage_report = triage_report
        last_loop_packet_report = loop_packet_report
        last_checkpoint_packet = checkpoint_packet

        phone_payload = build_phone_status(
            plan_id=plan_id,
            controller_run_id=controller_run_id,
            repo=repo,
            branch_base=branch_base,
            mode_effective=effective_mode,
            reason=str(triage_report.get("reason") or "running"),
            resolved=False,
            rounds_completed=len(rounds) + 1,
            tasks_completed=tasks_completed + 1,
            max_rounds=int(args.max_rounds),
            max_tasks=int(args.max_tasks),
            current_round=round_index,
            latest_working_branch=working_branch,
            triage_report=triage_report,
            loop_packet_report=loop_packet_report,
            checkpoint_packet=checkpoint_packet,
            warnings=warnings,
            errors=errors,
            max_draft_chars=int(args.max_draft_chars),
            max_trace_lines=int(args.terminal_trace_lines),
        )
        phone_markdown = render_phone_status_markdown(phone_payload)
        round_phone_json, _ = write_round_phone_status(
            payload=phone_payload,
            markdown=phone_markdown,
            round_dir=round_dir,
            phone_root=phone_root,
            controller_run_id=controller_run_id,
            round_index=round_index,
            latest_json=phone_latest_json,
            latest_md=phone_latest_md,
        )

        if round_index % int(args.checkpoint_every) == 0 or triage_rc != 0:
            inbox_path = queue_inbox / f"{controller_run_id}-r{round_index:03d}-{packet_id}.json"
            inbox_path.write_text(json.dumps(checkpoint_packet, indent=2), encoding="utf-8")
        latest_packet = str(checkpoint_path)

        unresolved = int(triage_report.get("unresolved_count") or 0)
        triage_reason = str(triage_report.get("reason") or "unknown")
        rounds.append(
            {
                "round": round_index,
                "working_branch": working_branch,
                "loop_branch": loop_branch,
                "triage_rc": triage_rc,
                "packet_rc": loop_packet_rc,
                "triage_reason": triage_reason,
                "unresolved_count": unresolved,
                "risk": packet_risk(loop_packet_report, triage_report),
                "packet_path": str(checkpoint_path),
                "phone_status_json": str(round_phone_json),
                "requires_approval": bool(checkpoint_packet.get("requires_approval")),
            }
        )
        tasks_completed += 1

        if triage_reason in HARD_REASON_CODES:
            errors.append(f"round {round_index}: hard stop reason from triage-loop ({triage_reason})")
            reason = triage_reason
            break
        if triage_rc not in (0, 1):
            errors.append(f"round {round_index}: triage-loop exited {triage_rc}")
            reason = "triage_loop_failed"
            break
        if loop_packet_rc not in (0, 1):
            errors.append(f"round {round_index}: loop-packet exited {loop_packet_rc}")
            reason = "loop_packet_failed"
            break
        if unresolved <= 0 and triage_reason == "resolved":
            resolved = True
            reason = "resolved"
            break

    return {
        "started_at": started_at,
        "rounds": rounds,
        "tasks_completed": tasks_completed,
        "resolved": resolved,
        "reason": reason,
        "latest_packet": latest_packet,
        "latest_working_branch": latest_working_branch,
        "last_triage_report": last_triage_report,
        "last_loop_packet_report": last_loop_packet_report,
        "last_checkpoint_packet": last_checkpoint_packet,
    }
