"""devctl mutation-loop command implementation."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ..common import pipe_output, write_output
from ..config import REPO_ROOT
from ..loop_comment import coerce_pr_number, upsert_comment
from ..mutation_loop_render import render_attempt_lines, render_markdown, render_playbook
from ..mutation_loop_policy import evaluate_fix_policy, load_policy

try:
    from dev.scripts.checks.mutation_ralph_loop_core import (
        execute_loop,
        gh_json,
        resolve_repo,
        run_capture,
    )
except ModuleNotFoundError:
    from checks.mutation_ralph_loop_core import execute_loop, gh_json, resolve_repo, run_capture


def _resolve_path(raw_path: str, *, relative_to_repo: bool = True) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute() or not relative_to_repo:
        return path
    return REPO_ROOT / path


def _mode_fix_command(mode: str, fix_command: str | None) -> str | None:
    if mode == "report-only":
        return None
    return (fix_command or "").strip() or None


def _resolve_comment_target(report: dict, args) -> tuple[dict[str, Any], str | None]:
    explicit_pr = coerce_pr_number(args.comment_pr_number)
    attempts = report.get("attempts", [])
    latest = attempts[-1] if isinstance(attempts, list) and attempts else {}
    if not isinstance(latest, dict):
        latest = {}
    source_sha = str(latest.get("run_sha") or report.get("last_run_sha") or "").strip()
    target = str(args.comment_target or "auto")

    if target == "pr":
        if explicit_pr is None:
            return {}, "comment-target=pr requires --comment-pr-number for mutation-loop"
        return {"kind": "pr", "id": explicit_pr, "source_sha": source_sha}, None
    if target == "commit":
        if not source_sha:
            return {}, "comment-target=commit requires run sha from mutation attempts"
        return {"kind": "commit", "id": source_sha, "source_sha": source_sha}, None

    if explicit_pr is not None:
        return {"kind": "pr", "id": explicit_pr, "source_sha": source_sha}, None
    if not source_sha:
        return {}, "auto comment target could not resolve PR or commit sha"
    return {"kind": "commit", "id": source_sha, "source_sha": source_sha}, None


def _comment_marker(report: dict, target: dict[str, Any]) -> str:
    attempts = report.get("attempts", [])
    latest = attempts[-1] if isinstance(attempts, list) and attempts else {}
    if not isinstance(latest, dict):
        latest = {}
    run_id = latest.get("run_id")
    run_id_label = str(run_id) if isinstance(run_id, int) else "none"
    sha_label = str(target.get("source_sha") or "none")
    return (
        "<!-- mutation-ralph-loop:"
        f"target={target.get('kind')}:{target.get('id')};"
        f"run_id={run_id_label};"
        f"sha={sha_label}"
        " -->"
    )


def _render_notification_comment(report: dict, marker: str) -> str:
    lines = [
        marker,
        "## Mutation Ralph Loop",
        "",
        f"- repo: `{report.get('repo')}`",
        f"- branch: `{report.get('branch')}`",
        f"- mode: `{report.get('mode')}`",
        f"- threshold: `{report.get('threshold')}`",
        f"- last_score: `{report.get('last_score', 'n/a')}`",
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
    body = _render_notification_comment(report, marker)
    payload, error = upsert_comment(
        str(report.get("repo") or ""),
        target,
        marker=marker,
        body=body,
        gh_json_fn=gh_json,
        run_capture_fn=run_capture,
    )
    if error:
        return {
            "ok": False,
            "mode": "summary-and-comment",
            "target_kind": target.get("kind"),
            "target_id": target.get("id"),
            "error": error,
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


def _write_report_bundle(report: dict, *, bundle_dir: Path, prefix: str) -> dict[str, Any]:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    md_path = bundle_dir / f"{prefix}.md"
    json_path = bundle_dir / f"{prefix}.json"
    playbook_path = bundle_dir / f"{prefix}-playbook.md"
    payload = {
        "written": True,
        "dir": str(bundle_dir),
        "markdown": str(md_path),
        "json": str(json_path),
        "playbook": str(playbook_path),
    }
    report_with_bundle = dict(report)
    report_with_bundle["bundle"] = payload
    md_path.write_text(render_markdown(report_with_bundle), encoding="utf-8")
    json_path.write_text(json.dumps(report_with_bundle, indent=2), encoding="utf-8")
    playbook_path.write_text(render_playbook(report_with_bundle), encoding="utf-8")
    return payload


def run(args) -> int:
    """Run a bounded mutation remediation loop and emit reports."""
    repo = resolve_repo(args.repo)
    if not repo:
        print("Error: unable to resolve repository (pass --repo or set GITHUB_REPOSITORY).")
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
    if args.threshold <= 0 or args.threshold > 1:
        print("Error: --threshold must be in the range (0, 1]")
        return 2
    if not args.dry_run and not shutil.which("gh"):
        print("Error: gh CLI is required for mutation-loop.")
        return 2

    warnings: list[str] = []
    policy = load_policy(REPO_ROOT)
    effective_fix_command = _mode_fix_command(args.mode, args.fix_command)
    fix_block_reason = evaluate_fix_policy(
        mode=args.mode,
        branch=args.branch,
        fix_command=effective_fix_command,
        policy=policy,
    )
    if fix_block_reason:
        warnings.append(fix_block_reason)

    if args.dry_run:
        loop_report: dict[str, Any] = {
            "ok": True,
            "repo": repo,
            "branch": args.branch,
            "workflow": args.workflow,
            "mode": args.mode,
            "max_attempts": args.max_attempts,
            "threshold": args.threshold,
            "completed_attempts": 0,
            "attempts": [],
            "reason": "dry-run",
            "fix_command_configured": bool(effective_fix_command),
            "fix_block_reason": fix_block_reason,
            "last_score": None,
        }
    else:
        loop_report = execute_loop(
            repo=repo,
            branch=args.branch,
            workflow=args.workflow,
            mode=args.mode,
            max_attempts=args.max_attempts,
            run_list_limit=args.run_list_limit,
            poll_seconds=args.poll_seconds,
            timeout_seconds=args.timeout_seconds,
            threshold=args.threshold,
            fix_command=effective_fix_command,
            fix_block_reason=fix_block_reason,
        )

    report: dict[str, Any] = dict(loop_report)
    report.update(
        {
            "command": "mutation-loop",
            "timestamp": datetime.now().isoformat(),
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
        report["bundle"] = _write_report_bundle(report, bundle_dir=bundle_dir, prefix=args.bundle_prefix)

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = render_markdown(report)

    write_output(output, args.output)
    if args.json_output:
        write_output(json.dumps(report, indent=2), args.json_output)
    if args.pipe_command:
        pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_rc != 0:
            return pipe_rc

    return 0 if report.get("ok") else 1
