"""Escalation comment helpers for `devctl triage-loop`."""

from __future__ import annotations

from typing import Any

from .loop_comment import upsert_comment
from .triage_loop_render import render_attempt_lines
from .triage_loop_support import resolve_comment_target


def _review_escalation_marker(target: dict[str, Any]) -> str:
    source_run_id = target.get("source_run_id")
    source_sha = target.get("source_sha")
    run_label = str(source_run_id) if isinstance(source_run_id, int) else "none"
    sha_label = str(source_sha or "none")
    return (
        "<!-- coderabbit-ralph-loop-escalation:"
        f"target={target.get('kind')}:{target.get('id')};"
        f"run_id={run_label};"
        f"sha={sha_label}"
        " -->"
    )


def render_review_escalation_comment(report: dict, *, marker: str) -> str:
    lines = [
        marker,
        "## CodeRabbit Ralph Loop Escalation",
        "",
        "Bounded remediation exhausted attempts with unresolved medium/high findings.",
        "",
        f"- repo: `{report.get('repo')}`",
        f"- branch: `{report.get('branch')}`",
        f"- mode: `{report.get('mode')}`",
        f"- unresolved_count: `{report.get('unresolved_count')}`",
        f"- max_attempts: `{report.get('max_attempts')}`",
        f"- completed_attempts: `{report.get('completed_attempts')}`",
        f"- reason: `{report.get('reason')}`",
        "",
        "### Reviewer Actions Requested",
        "",
        "1. Review unresolved medium/high findings in the latest backlog artifact.",
        "2. Confirm whether current fix command scope is sufficient or needs update.",
        "3. Post explicit next-step decision (manual fix, command allowlist change, or defer rationale).",
        "",
        "### Attempt Trace",
        "",
    ]
    lines.extend(render_attempt_lines(report.get("attempts", [])))
    return "\n".join(lines)


def publish_review_escalation_comment(
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

    marker = _review_escalation_marker(target)
    body = render_review_escalation_comment(report, marker=marker)
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
