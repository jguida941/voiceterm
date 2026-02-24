"""devctl triage-loop command implementation."""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

from ..common import pipe_output, write_output
from ..config import REPO_ROOT
from ..loop_comment import coerce_pr_number, upsert_comment
from ..triage_loop_render import (
    build_master_plan_proposal,
    render_attempt_lines,
    render_markdown,
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


def _resolve_path(raw_path: str, *, relative_to_repo: bool = True) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute() or not relative_to_repo:
        return path
    return REPO_ROOT / path


def _mode_fix_command(mode: str, fix_command: str | None) -> str | None:
    if mode == "report-only":
        return None
    return (fix_command or "").strip() or None


def _default_mp_proposal_path() -> str:
    return str(
        Path(tempfile.gettempdir()) / "devctl-triage-loop-master-plan-proposal.md"
    )


def _first_attempt(report: dict) -> dict[str, Any]:
    attempts = report.get("attempts", [])
    if not isinstance(attempts, list) or not attempts:
        return {}
    first = attempts[0]
    if not isinstance(first, dict):
        return {}
    return first


def _resolve_source_ids(report: dict) -> Tuple[int | None, str | None]:
    source_run_id = report.get("source_run_id")
    if not isinstance(source_run_id, int) or source_run_id <= 0:
        source_run_id = None
    source_sha = normalize_sha(str(report.get("source_run_sha") or ""))
    if not source_sha:
        first = _first_attempt(report)
        source_sha = normalize_sha(str(first.get("run_sha") or ""))
    return source_run_id, source_sha or None


def _resolve_comment_target(report: dict, args) -> tuple[dict[str, Any], str | None]:
    explicit_pr = coerce_pr_number(args.comment_pr_number)
    first = _first_attempt(report)
    artifact_pr = coerce_pr_number(first.get("backlog_pr_number"))
    if artifact_pr is None:
        artifact_pr = coerce_pr_number(report.get("backlog_pr_number"))
    source_run_id, source_sha = _resolve_source_ids(report)

    target = str(args.comment_target or "auto")
    if target == "pr":
        pr_number = explicit_pr or artifact_pr
        if pr_number is None:
            return {}, "comment-target=pr requires --comment-pr-number or backlog pr_number metadata"
        return {
            "kind": "pr",
            "id": pr_number,
            "source_run_id": source_run_id,
            "source_sha": source_sha,
        }, None
    if target == "commit":
        if not source_sha:
            return {}, "comment-target=commit requires source sha from --source-run-sha or loop attempt run sha"
        return {
            "kind": "commit",
            "id": source_sha,
            "source_run_id": source_run_id,
            "source_sha": source_sha,
        }, None

    pr_number = explicit_pr or artifact_pr
    if pr_number is not None:
        return {
            "kind": "pr",
            "id": pr_number,
            "source_run_id": source_run_id,
            "source_sha": source_sha,
        }, None
    if not source_sha:
        return {}, "auto comment target could not resolve PR or commit sha"
    return {
        "kind": "commit",
        "id": source_sha,
        "source_run_id": source_run_id,
        "source_sha": source_sha,
    }, None


def _comment_marker(report: dict, target: dict[str, Any]) -> str:
    source_run_id = target.get("source_run_id")
    source_sha = target.get("source_sha")
    run_label = str(source_run_id) if isinstance(source_run_id, int) else "none"
    sha_label = str(source_sha or "none")
    return (
        "<!-- coderabbit-ralph-loop:"
        f"target={target.get('kind')}:{target.get('id')};"
        f"run_id={run_label};"
        f"sha={sha_label}"
        " -->"
    )


def _render_notification_comment(report: dict, target: dict[str, Any], marker: str) -> str:
    lines = [
        marker,
        "## CodeRabbit Ralph Loop",
        "",
        f"- repo: `{report.get('repo')}`",
        f"- branch: `{report.get('branch')}`",
        f"- mode: `{report.get('mode')}`",
        f"- notify: `{report.get('notify')}`",
        f"- source_event: `{report.get('source_event')}`",
        f"- source_run_id: `{report.get('source_run_id') or 'n/a'}`",
        f"- source_run_sha: `{report.get('source_run_sha') or 'n/a'}`",
        f"- source_correlation: `{report.get('source_correlation')}`",
        f"- unresolved_count: `{report.get('unresolved_count')}`",
        f"- reason: `{report.get('reason')}`",
        "",
        "### Attempts",
        "",
    ]
    lines.extend(render_attempt_lines(report.get("attempts", [])))
    return "\n".join(lines)


def _publish_notification_comment(report: dict, args) -> dict[str, Any]:
    if report.get("notify") != "summary-and-comment":
        return {"ok": True, "mode": "summary-only", "skipped": True}

    target, target_error = _resolve_comment_target(report, args)
    if target_error:
        return {"ok": False, "mode": "summary-and-comment", "error": target_error}

    marker = _comment_marker(report, target)
    body = _render_notification_comment(report, target, marker)
    payload, publish_error = upsert_comment(
        str(report.get("repo", "")),
        target,
        marker=marker,
        body=body,
        gh_json_fn=gh_json,
        run_capture_fn=run_capture,
    )
    if publish_error:
        return {
            "ok": False,
            "mode": "summary-and-comment",
            "target_kind": target.get("kind"),
            "target_id": target.get("id"),
            "error": publish_error,
        }
    return {
        "ok": True,
        "mode": "summary-and-comment",
        "target_kind": target.get("kind"),
        "target_id": target.get("id"),
        "comment_id": payload.get("id"),
        "comment_url": payload.get("html_url"),
        "action": payload.get("action"),
    }


def _write_report_bundle(
    report: dict, *, bundle_dir: Path, prefix: str, include_mp_proposal: bool
) -> dict:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    md_path = bundle_dir / f"{prefix}.md"
    json_path = bundle_dir / f"{prefix}.json"
    payload = {
        "written": True,
        "dir": str(bundle_dir),
        "markdown": str(md_path),
        "json": str(json_path),
    }
    if include_mp_proposal:
        proposal_path = bundle_dir / f"{prefix}-master-plan-proposal.md"
        proposal_path.write_text(build_master_plan_proposal(report), encoding="utf-8")
        payload["mp_proposal"] = str(proposal_path)
    report_with_bundle = dict(report)
    report_with_bundle["bundle"] = payload
    md_path.write_text(render_markdown(report_with_bundle), encoding="utf-8")
    json_path.write_text(json.dumps(report_with_bundle, indent=2), encoding="utf-8")
    return payload


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
    effective_fix_command = _mode_fix_command(args.mode, args.fix_command)
    if args.mode in {"plan-then-fix", "fix-only"} and not effective_fix_command:
        warnings.append(
            f"mode={args.mode} requested but no --fix-command configured; backlog can only be reported."
        )

    if args.dry_run:
        loop_report: Dict[str, Any] = {
            "ok": True,
            "repo": repo,
            "branch": args.branch,
            "workflow": args.workflow,
            "max_attempts": args.max_attempts,
            "completed_attempts": 0,
            "attempts": [],
            "unresolved_count": 0,
            "reason": "dry-run",
            "fix_command_configured": bool(effective_fix_command),
            "source_run_id": args.source_run_id if args.source_run_id and args.source_run_id > 0 else None,
            "source_run_sha": normalize_sha(args.source_run_sha) or None,
            "source_event": args.source_event,
            "source_correlation": "dry-run",
        }
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
    if not args.dry_run and args.notify == "summary-and-comment":
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
        bundle_dir = _resolve_path(args.bundle_dir)
        report["bundle"] = _write_report_bundle(
            report,
            bundle_dir=bundle_dir,
            prefix=args.bundle_prefix,
            include_mp_proposal=bool(args.mp_proposal or args.mode == "plan-then-fix"),
        )

    if args.mp_proposal and not args.emit_bundle:
        proposal_path = _resolve_path(
            args.mp_proposal_path or _default_mp_proposal_path(),
            relative_to_repo=False,
        )
        proposal_path.parent.mkdir(parents=True, exist_ok=True)
        proposal_path.write_text(build_master_plan_proposal(report), encoding="utf-8")
        report["bundle"] = {
            "written": True,
            "mp_proposal": str(proposal_path),
        }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = render_markdown(report)

    write_output(output, args.output)
    if args.json_output:
        json_payload = json.dumps(report, indent=2)
        write_output(json_payload, args.json_output)
    if args.pipe_command:
        pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_rc != 0:
            return pipe_rc

    return 0 if report.get("ok") else 1
