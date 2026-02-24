"""devctl triage-loop command implementation."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from typing import Any, Dict

from ..common import pipe_output, write_output
from ..triage_loop_render import build_master_plan_proposal, render_markdown
from ..triage_loop_support import (
    build_dry_run_report,
    default_mp_proposal_path,
    mode_fix_command,
    non_blocking_connectivity_report,
    publish_notification_comment as _publish_notification_comment_support,
    resolve_path,
    write_report_bundle,
)

try:
    from dev.scripts.checks.coderabbit_gate_support import (
        is_ci_environment as _is_ci_environment,
        looks_like_connectivity_error as _looks_like_connectivity_error,
    )
except ModuleNotFoundError:
    from checks.coderabbit_gate_support import (
        is_ci_environment as _is_ci_environment,
        looks_like_connectivity_error as _looks_like_connectivity_error,
    )

try:
    from dev.scripts.checks.coderabbit_ralph_loop_core import (
        execute_loop,
        gh_json,
        normalize_sha,
        resolve_repo,
        run_capture,
    )
except ModuleNotFoundError:
    from checks.coderabbit_ralph_loop_core import (
        execute_loop,
        gh_json,
        normalize_sha,
        resolve_repo,
        run_capture,
    )


def _is_non_blocking_local_connectivity_error(message: str) -> bool:
    return bool(message) and _looks_like_connectivity_error(message) and not _is_ci_environment()


def _preflight_github_connectivity() -> str | None:
    rc, stdout, stderr = run_capture(["gh", "api", "rate_limit", "--jq", ".resources.core.remaining"])
    if rc == 0:
        return None
    message = (stderr or stdout or "gh api rate_limit failed").strip()
    if _is_non_blocking_local_connectivity_error(message):
        return message
    return None


def _publish_notification_comment(report: dict[str, Any], args) -> dict[str, Any]:
    return _publish_notification_comment_support(
        report,
        args,
        normalize_sha_fn=normalize_sha,
        gh_json_fn=gh_json,
        run_capture_fn=run_capture,
    )


def run(args) -> int:
    """Run a bounded CodeRabbit medium/high backlog loop and emit reports."""
    repo = resolve_repo(args.repo)
    if not repo:
        print(
            "Error: unable to resolve repository (pass --repo or set GITHUB_REPOSITORY)."
        )
        return 2
    if args.max_attempts < 1:
        print("Error: --max-attempts must be >= 1")
        return 2
    if args.poll_seconds < 5:
        print("Error: --poll-seconds must be >= 5")
        return 2
    if args.timeout_seconds < 60:
        print("Error: --timeout-seconds must be >= 60")
        return 2
    if args.source_event == "workflow_run" and not args.source_run_id:
        print("Error: --source-event workflow_run requires --source-run-id")
        return 2
    if not args.dry_run and not shutil.which("gh"):
        print("Error: gh CLI is required for triage-loop.")
        return 2

    warnings: list[str] = []
    effective_fix_command = mode_fix_command(args.mode, args.fix_command)
    if args.mode in {"plan-then-fix", "fix-only"} and not effective_fix_command:
        warnings.append(
            f"mode={args.mode} requested but no --fix-command configured; backlog can only be reported."
        )

    if args.dry_run:
        loop_report: Dict[str, Any] = build_dry_run_report(
            repo=repo,
            args=args,
            effective_fix_command=effective_fix_command,
            normalize_sha_fn=normalize_sha,
        )
    else:
        connectivity_error = _preflight_github_connectivity()
        if connectivity_error:
            warnings.append(
                "unable to reach GitHub API from local environment; "
                "triage-loop treated as non-blocking outside CI."
            )
            loop_report = non_blocking_connectivity_report(
                repo=repo,
                args=args,
                effective_fix_command=effective_fix_command,
                message=connectivity_error,
                normalize_sha_fn=normalize_sha,
            )
        else:
            loop_report = execute_loop(
                repo=repo,
                branch=args.branch,
                workflow=args.workflow,
                max_attempts=args.max_attempts,
                run_list_limit=args.run_list_limit,
                poll_seconds=args.poll_seconds,
                timeout_seconds=args.timeout_seconds,
                fix_command=effective_fix_command,
                source_run_id=args.source_run_id,
                source_run_sha=args.source_run_sha,
                source_event=args.source_event,
            )

    reason_text = str(loop_report.get("reason") or "")
    if _is_non_blocking_local_connectivity_error(reason_text):
        warnings.append(
            "nested triage-loop reported GitHub connectivity failure; "
            "converted to non-blocking local result."
        )
        loop_report = {
            **loop_report,
            "ok": True,
            "reason": "gh_unreachable_local_non_blocking",
        }

    report: Dict[str, Any] = dict(loop_report)
    report.update(
        {
            "command": "triage-loop",
            "timestamp": datetime.now().isoformat(),
            "mode": args.mode,
            "notify": args.notify,
            "comment_target": args.comment_target,
            "comment_pr_number": args.comment_pr_number,
            "dry_run": bool(args.dry_run),
            "fix_command_requested": bool((args.fix_command or "").strip()),
            "fix_command_effective": bool(effective_fix_command),
            "warnings": warnings,
            "bundle": {"written": False},
        }
    )
    if report.get("reason") == "gh_unreachable_local_non_blocking":
        report["notify_result"] = {
            "ok": True,
            "mode": str(args.notify),
            "skipped": True,
            "reason": "gh_unreachable_local_non_blocking",
        }
    elif not args.dry_run and args.notify == "summary-and-comment":
        notify_result = _publish_notification_comment(report, args)
        report["notify_result"] = notify_result
        if not notify_result.get("ok"):
            report["ok"] = False
            report["reason"] = "notification_comment_failed"
            warnings.append(
                "summary-and-comment requested but comment publication failed: "
                + str(notify_result.get("error") or "unknown error")
            )
    elif args.notify == "summary-only":
        report["notify_result"] = {"ok": True, "mode": "summary-only", "skipped": True}

    if args.emit_bundle:
        bundle_dir = resolve_path(args.bundle_dir)
        report["bundle"] = write_report_bundle(
            report,
            bundle_dir=bundle_dir,
            prefix=args.bundle_prefix,
            include_mp_proposal=bool(args.mp_proposal or args.mode == "plan-then-fix"),
        )

    if args.mp_proposal and not args.emit_bundle:
        proposal_path = resolve_path(
            args.mp_proposal_path or default_mp_proposal_path(),
            relative_to_repo=False,
        )
        proposal_path.parent.mkdir(parents=True, exist_ok=True)
        proposal_path.write_text(build_master_plan_proposal(report), encoding="utf-8")
        report["bundle"] = {
            "written": True,
            "mp_proposal": str(proposal_path),
        }

    output = json.dumps(report, indent=2) if args.format == "json" else render_markdown(report)

    write_output(output, args.output)
    if args.json_output:
        json_payload = json.dumps(report, indent=2)
        write_output(json_payload, args.json_output)
    if args.pipe_command:
        pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_rc != 0:
            return pipe_rc

    return 0 if report.get("ok") else 1
