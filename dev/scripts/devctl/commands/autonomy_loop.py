"""devctl autonomy-loop command implementation."""

from __future__ import annotations

import hashlib
import os

from ..autonomy_loop_helpers import (
    DEFAULT_REPLAY_WINDOW_SECONDS,
    allowed_branch as _allowed_branch,
    autonomy_policy as _autonomy_policy,
    iso_z as _iso_z,
    load_policy as _load_policy,
    render_markdown as _render_markdown,
    resolve_path as _resolve_path,
    slug as _slug,
    utc_now as _utc_now,
)
from ..autonomy_phone_status import (
    build_phone_status as _build_phone_status,
    render_phone_status_markdown as _render_phone_status_markdown,
)
from .autonomy_loop_rounds import run_controller_rounds as _run_controller_rounds
from .autonomy_loop_support import (
    build_controller_report as _build_controller_report,
    emit_controller_report as _emit_controller_report,
    validate_args as _validate_args,
    write_final_phone_status as _write_final_phone_status,
    write_validation_error as _write_validation_error,
)

try:
    from dev.scripts.checks.coderabbit_ralph_loop_core import resolve_repo
except ModuleNotFoundError:
    from checks.coderabbit_ralph_loop_core import resolve_repo

def run(args) -> int:
    """Run bounded autonomous controller rounds over triage-loop + packet emission."""
    repo = resolve_repo(args.repo)
    if not repo:
        print("Error: unable to resolve repository (pass --repo or set GITHUB_REPOSITORY).")
        return 2

    arg_error = _validate_args(args)
    if arg_error:
        print(arg_error)
        return 2

    plan_id = _slug(args.plan_id, fallback="plan")
    branch_base = str(args.branch_base).strip()
    working_prefix = _slug(args.working_branch_prefix, fallback="autoloop")

    warnings: list[str] = []
    errors: list[str] = []

    policy = _load_policy()
    autonomy_cfg = _autonomy_policy(policy)
    if not _allowed_branch(branch_base, autonomy_cfg):
        errors.append(f"branch '{branch_base}' is not allowed by autonomy_loop.allowed_branches policy")

    max_rounds_cap = int(autonomy_cfg.get("max_rounds_hard_cap") or 0)
    if max_rounds_cap > 0 and args.max_rounds > max_rounds_cap:
        errors.append(f"--max-rounds={args.max_rounds} exceeds policy cap {max_rounds_cap}")
    max_hours_cap = float(autonomy_cfg.get("max_hours_hard_cap") or 0)
    if max_hours_cap > 0 and args.max_hours > max_hours_cap:
        errors.append(f"--max-hours={args.max_hours} exceeds policy cap {max_hours_cap}")
    max_tasks_cap = int(autonomy_cfg.get("max_tasks_hard_cap") or 0)
    if max_tasks_cap > 0 and args.max_tasks > max_tasks_cap:
        errors.append(f"--max-tasks={args.max_tasks} exceeds policy cap {max_tasks_cap}")

    requested_mode = str(args.mode)
    default_autonomy_mode = str(policy.get("autonomy_mode_default") or "read-only").strip() or "read-only"
    runtime_autonomy_mode = str(os.getenv("AUTONOMY_MODE") or default_autonomy_mode).strip() or default_autonomy_mode
    effective_mode = requested_mode
    if requested_mode != "report-only" and runtime_autonomy_mode != "operate":
        warnings.append("AUTONOMY_MODE is not 'operate'; forced controller mode to report-only for safety")
        effective_mode = "report-only"

    packet_root = _resolve_path(str(args.packet_out))
    queue_root = _resolve_path(str(args.queue_out))
    policy_packet_root = str(autonomy_cfg.get("packet_root") or "").strip()
    if policy_packet_root:
        packet_root = _resolve_path(policy_packet_root)
    policy_queue_root = str(autonomy_cfg.get("queue_root") or "").strip()
    if policy_queue_root:
        queue_root = _resolve_path(policy_queue_root)

    replay_window_seconds = int(
        autonomy_cfg.get("replay_window_seconds")
        or (policy.get("security") or {}).get("enforce_replay_window_seconds")
        or DEFAULT_REPLAY_WINDOW_SECONDS
    )

    if errors:
        return _write_validation_error(
            args,
            warnings,
            errors,
            repo=repo,
            plan_id=plan_id,
            branch_base=branch_base,
            mode_requested=requested_mode,
            mode_effective=effective_mode,
            packet_root=packet_root,
            queue_root=queue_root,
        )

    run_seed = f"{_iso_z(_utc_now())}|{plan_id}|{repo}|{branch_base}"
    controller_run_id = hashlib.sha256(run_seed.encode("utf-8")).hexdigest()[:12]
    run_packet_root = packet_root / controller_run_id
    queue_inbox = queue_root / "inbox"
    queue_outbox = queue_root / "outbox"
    queue_archive = queue_root / "archive"
    phone_root = queue_root / "phone"
    run_packet_root.mkdir(parents=True, exist_ok=True)
    queue_inbox.mkdir(parents=True, exist_ok=True)
    queue_outbox.mkdir(parents=True, exist_ok=True)
    queue_archive.mkdir(parents=True, exist_ok=True)
    phone_root.mkdir(parents=True, exist_ok=True)
    phone_latest_json = phone_root / "latest.json"
    phone_latest_md = phone_root / "latest.md"

    round_results = _run_controller_rounds(
        args=args,
        repo=repo,
        plan_id=plan_id,
        branch_base=branch_base,
        working_prefix=working_prefix,
        effective_mode=effective_mode,
        controller_run_id=controller_run_id,
        run_packet_root=run_packet_root,
        queue_inbox=queue_inbox,
        phone_root=phone_root,
        phone_latest_json=phone_latest_json,
        phone_latest_md=phone_latest_md,
        replay_window_seconds=replay_window_seconds,
        warnings=warnings,
        errors=errors,
    )
    started_at = round_results["started_at"]
    rounds = round_results["rounds"]
    tasks_completed = int(round_results["tasks_completed"])
    resolved = bool(round_results["resolved"])
    reason = str(round_results["reason"])
    latest_packet = round_results["latest_packet"]
    latest_working_branch = round_results["latest_working_branch"]
    last_triage_report = round_results["last_triage_report"]
    last_loop_packet_report = round_results["last_loop_packet_report"]
    last_checkpoint_packet = round_results["last_checkpoint_packet"]

    finished_at = _utc_now()
    elapsed_hours = max((finished_at - started_at).total_seconds() / 3600.0, 0.0)
    ok = not errors and reason in {"resolved", "max_rounds_reached", "max_hours_reached", "max_tasks_reached"}

    final_phone_payload = _build_phone_status(
        plan_id=plan_id,
        controller_run_id=controller_run_id,
        repo=repo,
        branch_base=branch_base,
        mode_effective=effective_mode,
        reason=reason,
        resolved=resolved,
        rounds_completed=len(rounds),
        tasks_completed=tasks_completed,
        max_rounds=int(args.max_rounds),
        max_tasks=int(args.max_tasks),
        current_round=len(rounds),
        latest_working_branch=latest_working_branch,
        triage_report=last_triage_report,
        loop_packet_report=last_loop_packet_report,
        checkpoint_packet=last_checkpoint_packet,
        warnings=warnings,
        errors=errors,
        max_draft_chars=int(args.max_draft_chars),
        max_trace_lines=int(args.terminal_trace_lines),
    )
    final_phone_markdown = _render_phone_status_markdown(final_phone_payload)
    final_phone_json, final_phone_md = _write_final_phone_status(
        payload=final_phone_payload,
        markdown=final_phone_markdown,
        phone_root=phone_root,
        controller_run_id=controller_run_id,
        latest_json=phone_latest_json,
        latest_md=phone_latest_md,
    )

    report = _build_controller_report(
        finished_at_iso=_iso_z(finished_at),
        ok=ok,
        resolved=resolved,
        reason=reason,
        plan_id=plan_id,
        controller_run_id=controller_run_id,
        repo=repo,
        branch_base=branch_base,
        mode_requested=requested_mode,
        mode_effective=effective_mode,
        loop_branch_mode=args.loop_branch_mode,
        max_rounds=int(args.max_rounds),
        max_hours=float(args.max_hours),
        max_tasks=int(args.max_tasks),
        rounds_completed=len(rounds),
        tasks_completed=tasks_completed,
        elapsed_hours=round(elapsed_hours, 3),
        run_packet_root=run_packet_root,
        queue_root=queue_root,
        latest_packet=latest_packet,
        latest_working_branch=latest_working_branch,
        phone_latest_json=phone_latest_json,
        phone_latest_md=phone_latest_md,
        final_phone_json=final_phone_json,
        final_phone_md=final_phone_md,
        warnings=warnings,
        errors=errors,
        rounds=rounds,
    )

    emit_code = _emit_controller_report(
        args=args,
        report=report,
        render_markdown_fn=_render_markdown,
        run_packet_root=run_packet_root,
    )
    if emit_code != 0:
        return emit_code

    return 0 if ok else 1
