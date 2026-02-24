"""Shared helper logic for `devctl triage-loop`."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

from .config import REPO_ROOT
from .loop_comment import coerce_pr_number, upsert_comment
from .triage_loop_render import (
    build_master_plan_proposal,
    render_attempt_lines,
    render_markdown,
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


def resolve_path(raw_path: str, *, relative_to_repo: bool = True) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute() or not relative_to_repo:
        return path
    return REPO_ROOT / path


def mode_fix_command(mode: str, fix_command: str | None) -> str | None:
    if mode == "report-only":
        return None
    return (fix_command or "").strip() or None


def default_mp_proposal_path() -> str:
    return str(Path(tempfile.gettempdir()) / "devctl-triage-loop-master-plan-proposal.md")


def is_non_blocking_local_connectivity_error(message: str) -> bool:
    return bool(message) and _looks_like_connectivity_error(message) and not _is_ci_environment()


def preflight_github_connectivity(run_capture_fn) -> str | None:
    rc, stdout, stderr = run_capture_fn(
        ["gh", "api", "rate_limit", "--jq", ".resources.core.remaining"]
    )
    if rc == 0:
        return None
    message = (stderr or stdout or "gh api rate_limit failed").strip()
    if is_non_blocking_local_connectivity_error(message):
        return message
    return None


def non_blocking_connectivity_report(
    *,
    repo: str,
    args,
    effective_fix_command: str | None,
    message: str,
    normalize_sha_fn,
) -> dict[str, Any]:
    return {
        "ok": True,
        "repo": repo,
        "branch": args.branch,
        "workflow": args.workflow,
        "max_attempts": args.max_attempts,
        "completed_attempts": 0,
        "attempts": [],
        "unresolved_count": 0,
        "reason": "gh_unreachable_local_non_blocking",
        "fix_command_configured": bool(effective_fix_command),
        "source_run_id": (
            args.source_run_id
            if args.source_run_id and args.source_run_id > 0
            else None
        ),
        "source_run_sha": normalize_sha_fn(args.source_run_sha) or None,
        "source_event": args.source_event,
        "source_correlation": "branch_latest_fallback",
        "connectivity_error": message,
    }


def build_dry_run_report(
    *,
    repo: str,
    args,
    effective_fix_command: str | None,
    normalize_sha_fn,
) -> Dict[str, Any]:
    return {
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
        "source_run_id": (
            args.source_run_id
            if args.source_run_id and args.source_run_id > 0
            else None
        ),
        "source_run_sha": normalize_sha_fn(args.source_run_sha) or None,
        "source_event": args.source_event,
        "source_correlation": "dry-run",
    }


def first_attempt(report: dict) -> dict[str, Any]:
    attempts = report.get("attempts", [])
    if not isinstance(attempts, list) or not attempts:
        return {}
    first = attempts[0]
    if not isinstance(first, dict):
        return {}
    return first


def resolve_source_ids(report: dict, normalize_sha_fn) -> Tuple[int | None, str | None]:
    source_run_id = report.get("source_run_id")
    if not isinstance(source_run_id, int) or source_run_id <= 0:
        source_run_id = None
    source_sha = normalize_sha_fn(str(report.get("source_run_sha") or ""))
    if not source_sha:
        first = first_attempt(report)
        source_sha = normalize_sha_fn(str(first.get("run_sha") or ""))
    return source_run_id, source_sha or None


def resolve_comment_target(
    report: dict,
    args,
    normalize_sha_fn,
) -> tuple[dict[str, Any], str | None]:
    explicit_pr = coerce_pr_number(args.comment_pr_number)
    first = first_attempt(report)
    artifact_pr = coerce_pr_number(first.get("backlog_pr_number"))
    if artifact_pr is None:
        artifact_pr = coerce_pr_number(report.get("backlog_pr_number"))
    source_run_id, source_sha = resolve_source_ids(report, normalize_sha_fn)

    target = str(args.comment_target or "auto")
    if target == "pr":
        pr_number = explicit_pr or artifact_pr
        if pr_number is None:
            return (
                {},
                "comment-target=pr requires --comment-pr-number or backlog pr_number metadata",
            )
        return {
            "kind": "pr",
            "id": pr_number,
            "source_run_id": source_run_id,
            "source_sha": source_sha,
        }, None
    if target == "commit":
        if not source_sha:
            return (
                {},
                "comment-target=commit requires source sha from --source-run-sha or loop attempt run sha",
            )
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


def comment_marker(target: dict[str, Any]) -> str:
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


def render_notification_comment(
    report: dict,
    *,
    target: dict[str, Any],
    marker: str,
) -> str:
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


def publish_notification_comment(
    report: dict,
    args,
    *,
    normalize_sha_fn,
    gh_json_fn,
    run_capture_fn,
) -> dict[str, Any]:
    if report.get("notify") != "summary-and-comment":
        return {"ok": True, "mode": "summary-only", "skipped": True}

    target, target_error = resolve_comment_target(report, args, normalize_sha_fn)
    if target_error:
        return {"ok": False, "mode": "summary-and-comment", "error": target_error}

    marker = comment_marker(target)
    body = render_notification_comment(report, target=target, marker=marker)
    payload, publish_error = upsert_comment(
        str(report.get("repo", "")),
        target,
        marker=marker,
        body=body,
        gh_json_fn=gh_json_fn,
        run_capture_fn=run_capture_fn,
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


def write_report_bundle(
    report: dict,
    *,
    bundle_dir: Path,
    prefix: str,
    include_mp_proposal: bool,
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
