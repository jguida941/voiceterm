"""Round execution helpers for `devctl autonomy-loop`."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

from ...autonomy.loop_helpers import (
    build_checkpoint_packet,
    build_loop_packet_args,
    build_triage_args,
    json_load,
    utc_now,
)
from ...autonomy.phone_status import build_phone_status, render_phone_status_markdown
from ...watchdog.probe_gate import run_probe_scan
from .. import loop_packet as loop_packet_command
from .. import triage_loop as triage_loop_command
from .loop_round_state import (
    RoundInfo,
    RoundReports,
    StopCheck,
    build_round_summary as _build_round_summary,
    resolve_round_exit as _resolve_round_exit,
    should_stop_before_round as _should_stop_before_round,
)
from .loop_support import write_round_phone_status


@dataclass
class RoundControllerContext:
    args: Any
    repo: str
    plan_id: str
    branch_base: str
    working_prefix: str
    effective_mode: str
    controller_run_id: str
    run_packet_root: Path
    queue_inbox: Path
    phone_root: Path
    phone_latest_json: Path
    phone_latest_md: Path
    replay_window_seconds: int
    warnings: list[str]
    errors: list[str]


@dataclass(frozen=True)
class RoundPaths:
    triage_json_path: Path
    loop_packet_json_path: Path


@dataclass(frozen=True)
class LoopRound:
    round_index: int
    working_branch: str
    loop_branch: str
    round_dir: Path
    paths: RoundPaths


@dataclass
class RoundArtifacts:
    triage_rc: int | None = None
    triage_report: dict[str, Any] | None = None
    loop_packet_rc: int | None = None
    loop_packet_report: dict[str, Any] | None = None


@dataclass
class ControllerRoundResults:
    started_at: Any
    rounds: list[dict[str, Any]] = field(default_factory=list)
    tasks_completed: int = 0
    resolved: bool = False
    reason: str = "max_rounds_reached"
    latest_packet: str | None = None
    latest_working_branch: str | None = None
    last_triage_report: dict[str, Any] = field(default_factory=dict)
    last_loop_packet_report: dict[str, Any] = field(default_factory=dict)
    last_checkpoint_packet: dict[str, Any] = field(default_factory=dict)


def _build_round(context: RoundControllerContext, round_index: int) -> LoopRound:
    working_branch = (
        f"{context.working_prefix}/{context.plan_id}/"
        f"{context.controller_run_id}/r{round_index:03d}"
    )
    loop_branch = (
        context.branch_base
        if context.args.loop_branch_mode == "base"
        else working_branch
    )
    round_dir = context.run_packet_root / f"round-{round_index:03d}"
    round_dir.mkdir(parents=True, exist_ok=True)
    return LoopRound(
        round_index=round_index,
        working_branch=working_branch,
        loop_branch=loop_branch,
        round_dir=round_dir,
        paths=RoundPaths(
            triage_json_path=round_dir / "triage-loop.json",
            loop_packet_json_path=round_dir / "loop-packet.json",
        ),
    )


def _run_round_tools(
    context: RoundControllerContext,
    round_info: LoopRound,
) -> RoundArtifacts:
    triage_args = build_triage_args(
        repo=context.repo,
        loop_branch=round_info.loop_branch,
        workflow=context.args.workflow,
        mode=context.effective_mode,
        fix_command=(context.args.fix_command or "").strip() or None,
        max_attempts=context.args.loop_max_attempts,
        run_list_limit=context.args.run_list_limit,
        poll_seconds=context.args.poll_seconds,
        timeout_seconds=context.args.timeout_seconds,
        notify=context.args.notify,
        comment_target=context.args.comment_target,
        comment_pr_number=context.args.comment_pr_number,
        bundle_dir=round_info.round_dir,
        bundle_prefix=f"coderabbit-ralph-loop-r{round_info.round_index:03d}",
        dry_run=bool(context.args.dry_run),
        output_path=round_info.paths.triage_json_path,
    )
    triage_rc = triage_loop_command.run(triage_args)
    triage_report, _triage_error = json_load(round_info.paths.triage_json_path)
    if triage_report is None:
        return RoundArtifacts()

    loop_packet_args = build_loop_packet_args(
        source_json=round_info.paths.triage_json_path,
        max_age_hours=context.args.max_packet_age_hours,
        max_draft_chars=context.args.max_draft_chars,
        allow_auto_send=bool(context.args.allow_auto_send),
        output_path=round_info.paths.loop_packet_json_path,
    )
    loop_packet_rc = loop_packet_command.run(loop_packet_args)
    loop_packet_report, _loop_packet_error = json_load(
        round_info.paths.loop_packet_json_path
    )
    if loop_packet_report is None:
        return RoundArtifacts(
            triage_rc=triage_rc,
            triage_report=triage_report,
        )
    return RoundArtifacts(
        triage_rc=triage_rc,
        triage_report=triage_report,
        loop_packet_rc=loop_packet_rc,
        loop_packet_report=loop_packet_report,
    )


def _build_checkpoint_packet_with_probe(
    context: RoundControllerContext,
    round_info: LoopRound,
    artifacts: RoundArtifacts,
) -> dict[str, Any]:
    checkpoint_packet = build_checkpoint_packet(
        plan_id=context.plan_id,
        controller_run_id=context.controller_run_id,
        branch_base=context.branch_base,
        working_branch=round_info.working_branch,
        round_index=round_info.round_index,
        triage_report=artifacts.triage_report or {},
        loop_packet_report=artifacts.loop_packet_report or {},
        replay_window_seconds=context.replay_window_seconds,
        trace_lines=context.args.terminal_trace_lines,
        packet_source_refs=[
            str(round_info.paths.triage_json_path),
            str(round_info.paths.loop_packet_json_path),
        ],
    )
    try:
        probe_result = run_probe_scan(timeout_seconds=120)
        checkpoint_packet["probe_scan"] = probe_result.to_dict()
    # broad-except: allow reason=probe scan must fail open fallback=omit probe scan from checkpoint packet
    except Exception:
        checkpoint_packet["probe_scan"] = None
    return checkpoint_packet


def _write_checkpoint_and_phone_status(
    context: RoundControllerContext,
    round_info: LoopRound,
    tasks_completed: int,
    artifacts: RoundArtifacts,
    checkpoint_packet: dict[str, Any],
) -> tuple[Path, Path]:
    packet_id = str(
        checkpoint_packet.get("idempotency_key")
        or f"r{round_info.round_index:03d}"
    )
    checkpoint_path = round_info.round_dir / "checkpoint-packet.json"
    checkpoint_path.write_text(json.dumps(checkpoint_packet, indent=2), encoding="utf-8")
    phone_payload = build_phone_status(
        plan_id=context.plan_id,
        controller_run_id=context.controller_run_id,
        repo=context.repo,
        branch_base=context.branch_base,
        mode_effective=context.effective_mode,
        reason=str((artifacts.triage_report or {}).get("reason") or "running"),
        resolved=False,
        rounds_completed=round_info.round_index,
        tasks_completed=tasks_completed + 1,
        max_rounds=int(context.args.max_rounds),
        max_tasks=int(context.args.max_tasks),
        current_round=round_info.round_index,
        latest_working_branch=round_info.working_branch,
        triage_report=artifacts.triage_report or {},
        loop_packet_report=artifacts.loop_packet_report or {},
        checkpoint_packet=checkpoint_packet,
        warnings=context.warnings,
        errors=context.errors,
        max_draft_chars=int(context.args.max_draft_chars),
        max_trace_lines=int(context.args.terminal_trace_lines),
    )
    phone_markdown = render_phone_status_markdown(phone_payload)
    round_phone_json, _ = write_round_phone_status(
        payload=phone_payload,
        markdown=phone_markdown,
        round_dir=round_info.round_dir,
        phone_root=context.phone_root,
        controller_run_id=context.controller_run_id,
        round_index=round_info.round_index,
        latest_json=context.phone_latest_json,
        latest_md=context.phone_latest_md,
    )
    if (
        round_info.round_index % int(context.args.checkpoint_every) == 0
        or artifacts.triage_rc != 0
    ):
        inbox_path = (
            context.queue_inbox
            / f"{context.controller_run_id}-r{round_info.round_index:03d}-{packet_id}.json"
        )
        inbox_path.write_text(json.dumps(checkpoint_packet, indent=2), encoding="utf-8")
    return checkpoint_path, round_phone_json


def run_controller_rounds(
    context: RoundControllerContext,
) -> ControllerRoundResults:
    started_at = utc_now()
    max_duration = timedelta(hours=float(context.args.max_hours))
    results = ControllerRoundResults(started_at=started_at)

    for round_index in range(1, int(context.args.max_rounds) + 1):
        stop_reason = _should_stop_before_round(
            StopCheck(
                started_at=started_at,
                max_duration=max_duration,
                tasks_completed=results.tasks_completed,
                max_tasks=int(context.args.max_tasks),
            )
        )
        if stop_reason is not None:
            results.reason = stop_reason
            break

        round_info = _build_round(context, round_index)
        results.latest_working_branch = round_info.working_branch
        artifacts = _run_round_tools(context, round_info)
        if artifacts.triage_report is None:
            context.errors.append(
                f"round {round_index}: failed to read triage-loop report"
            )
            results.reason = "triage_report_missing"
            break
        if artifacts.loop_packet_report is None:
            context.errors.append(
                f"round {round_index}: failed to read loop-packet report"
            )
            results.reason = "packet_report_missing"
            break

        checkpoint_packet = _build_checkpoint_packet_with_probe(
            context,
            round_info,
            artifacts,
        )
        results.last_triage_report = artifacts.triage_report
        results.last_loop_packet_report = artifacts.loop_packet_report
        results.last_checkpoint_packet = checkpoint_packet

        checkpoint_path, round_phone_json = _write_checkpoint_and_phone_status(
            context,
            round_info,
            results.tasks_completed,
            artifacts,
            checkpoint_packet=checkpoint_packet,
        )
        results.latest_packet = str(checkpoint_path)
        round_reports = RoundReports(
            triage_rc=int(artifacts.triage_rc or 0),
            loop_packet_rc=int(artifacts.loop_packet_rc or 0),
            triage_report=artifacts.triage_report,
            loop_packet_report=artifacts.loop_packet_report,
        )
        results.rounds.append(
            _build_round_summary(
                round_info=RoundInfo(
                    round_index=round_info.round_index,
                    working_branch=round_info.working_branch,
                    loop_branch=round_info.loop_branch,
                ),
                reports=round_reports,
                checkpoint_path=str(checkpoint_path),
                round_phone_json=str(round_phone_json),
                checkpoint_packet=checkpoint_packet,
            )
        )
        results.tasks_completed += 1

        should_exit, results.reason, results.resolved = _resolve_round_exit(
            round_info=RoundInfo(
                round_index=round_info.round_index,
                working_branch=round_info.working_branch,
                loop_branch=round_info.loop_branch,
            ),
            reports=round_reports,
            errors=context.errors,
        )
        if should_exit:
            break

    return results
