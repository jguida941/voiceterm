"""devctl controller-action command implementation."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..common import emit_output, pipe_output, write_output
from ..controller_action_support import (
    ControllerActionName,
    autonomy_mode,
    branch_allowed,
    build_controller_typed_action,
    dispatch_workflow_command,
    is_non_blocking_local_connectivity_error,
    load_controller_policy,
    load_phone_payload,
    remote_mode_command,
    render_markdown,
    requested_mode_for_action,
    workflow_allowed,
    write_controller_mode,
)
from ..phone_status_views import view_payload

from ..repo_packs.process_helpers import resolve_repo, run_capture


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class ControllerActionReport:
    command: str
    timestamp: str
    ok: bool
    action: str
    reason: str
    repo: str
    branch: str
    workflow: str
    autonomy_mode_runtime: str
    dry_run: bool
    typed_action: dict[str, object] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_report(
    args,
    repo: str,
    runtime_mode: str,
    *,
    action: ControllerActionName,
) -> ControllerActionReport:
    return ControllerActionReport(
        command="controller-action",
        timestamp=_timestamp(),
        ok=False,
        action=action.value,
        reason="",
        repo=repo,
        branch=str(args.branch),
        workflow=str(args.workflow),
        autonomy_mode_runtime=runtime_mode,
        dry_run=bool(args.dry_run),
    )


def _run_command(
    command: list[str], *, dry_run: bool
) -> tuple[bool, str, dict[str, Any]]:
    if dry_run:
        return True, "dry-run", {"command": " ".join(command)}
    rc, stdout, stderr = run_capture(command)
    message = (stderr or stdout or "").strip()
    if rc == 0:
        return True, "ok", {"command": " ".join(command), "output": message}
    return False, message or f"command exited {rc}", {"command": " ".join(command)}


def _dispatch_report_only(
    report: ControllerActionReport, args, policy: dict[str, Any]
) -> None:
    workflow = str(args.workflow).strip()
    branch = str(args.branch).strip()
    if not workflow_allowed(policy, workflow):
        report.reason = "workflow_not_allowlisted"
        report.errors.append(f"workflow not allowlisted by policy: {workflow}")
        return
    if not branch_allowed(policy, branch):
        report.reason = "branch_not_allowlisted"
        report.errors.append(f"branch not allowlisted by policy: {branch}")
        return
    if report.autonomy_mode_runtime == "off":
        report.reason = "autonomy_mode_off"
        report.errors.append("AUTONOMY_MODE=off blocks dispatch actions")
        return
    command = dispatch_workflow_command(
        workflow=workflow,
        repo=report.repo,
        branch=branch,
        max_attempts=int(args.max_attempts),
    )
    ok, message, result = _run_command(command, dry_run=bool(args.dry_run))
    report.result = result
    if ok:
        report.ok = True
        report.reason = "dispatched_report_only"
        return
    if is_non_blocking_local_connectivity_error(message):
        report.ok = True
        report.reason = "gh_unreachable_local_non_blocking"
        report.warnings.append(
            "unable to reach GitHub API in local environment; dispatch treated as non-blocking"
        )
        return
    report.reason = "dispatch_failed"
    report.errors.append(message)


def apply_mode_change(
    report: ControllerActionReport, args, *, requested_mode: str
) -> None:
    if report.autonomy_mode_runtime == "off":
        report.reason = "autonomy_mode_off"
        report.errors.append("AUTONOMY_MODE=off blocks controller mode actions")
        return
    remote_ok = True
    remote_result: dict[str, Any] = {}
    if args.remote:
        command = remote_mode_command(repo=report.repo, requested_mode=requested_mode)
        remote_ok, message, remote_result = _run_command(
            command, dry_run=bool(args.dry_run)
        )
        if not remote_ok and is_non_blocking_local_connectivity_error(message):
            report.warnings.append(
                "unable to reach GitHub API in local environment; remote mode update treated as non-blocking"
            )
            remote_ok = True
        elif not remote_ok:
            report.errors.append(message)
    mode_file_path = write_controller_mode(
        mode_file=str(args.mode_file),
        action=report.action,
        requested_mode=requested_mode,
        repo=report.repo,
        branch=str(args.branch),
        remote_enabled=bool(args.remote),
        remote_ok=remote_ok,
        dry_run=bool(args.dry_run),
        warnings=report.warnings,
        errors=report.errors,
        typed_action=report.typed_action,
    )
    report.result = {
        "requested_mode": requested_mode,
        "mode_file": mode_file_path,
        "remote": bool(args.remote),
        "remote_result": remote_result,
    }
    if remote_ok and not report.errors:
        report.ok = True
        report.reason = "mode_updated"
    else:
        report.reason = "mode_update_failed"


def refresh_status_report(report: ControllerActionReport, args) -> None:
    payload, load_error = load_phone_payload(str(args.phone_json))
    if load_error:
        report.reason = "phone_status_unavailable"
        report.errors.append(load_error)
        return
    projection = view_payload(payload, str(args.view))
    report.result = {
        "view": str(args.view),
        "phone_json": str(args.phone_json),
        "projection": projection,
    }
    report.ok = True
    report.reason = "status_refreshed"


def run(args) -> int:
    """Execute one policy-gated controller action."""
    action = ControllerActionName(str(args.action))
    if int(args.max_attempts) < 1:
        print("Error: --max-attempts must be >= 1")
        return 2
    if (
        not args.dry_run
        and action is not ControllerActionName.REFRESH_STATUS
        and not shutil.which("gh")
    ):
        print("Error: gh CLI is required for controller actions that call GitHub.")
        return 2

    repo = resolve_repo(args.repo)
    if not repo and action is not ControllerActionName.REFRESH_STATUS:
        print(
            "Error: unable to resolve repository (pass --repo or set GITHUB_REPOSITORY)."
        )
        return 2
    if not repo:
        repo = str(args.repo or "unknown/unknown")

    policy = load_controller_policy()
    runtime_mode = autonomy_mode(policy)
    report = build_report(args, repo, runtime_mode, action=action)

    requested_mode = requested_mode_for_action(action)
    report.typed_action = asdict(
        build_controller_typed_action(
            args=args,
            action=action,
            repo=repo,
            requested_mode=requested_mode,
        )
    )

    if action is ControllerActionName.REFRESH_STATUS:
        refresh_status_report(report, args)
    elif action is ControllerActionName.DISPATCH_REPORT_ONLY:
        _dispatch_report_only(report, args, policy)
    elif action in {
        ControllerActionName.PAUSE_LOOP,
        ControllerActionName.RESUME_LOOP,
    }:
        apply_mode_change(report, args, requested_mode=requested_mode)
    else:
        report.reason = "unsupported_action"
        report.errors.append(f"unsupported action: {action.value}")

    report_payload = asdict(report)
    json_payload = json.dumps(report_payload, indent=2)
    output = (
        json_payload if args.format == "json" else render_markdown(report_payload)
    )
    pipe_code = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        additional_outputs=[(json_payload, args.json_output)] if args.json_output else None,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_code != 0:
        return pipe_code
    return 0 if report.ok else 1
