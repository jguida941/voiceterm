"""Core helpers shared by CodeRabbit workflow gate scripts."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from typing import Any, Callable


def looks_like_sha(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", value.strip()))


def parse_iso(value: Any) -> tuple[bool, datetime]:
    raw = str(value or "").strip()
    if not raw:
        return False, datetime.min
    normalized = raw.replace("Z", "+00:00")
    try:
        return True, datetime.fromisoformat(normalized)
    except ValueError:
        return False, datetime.min


def resolve_sha(
    raw: str | None,
    *,
    run_capture: Callable[[list[str]], tuple[int, str, str]],
) -> tuple[str, str | None]:
    if raw:
        value = raw.strip()
        if value:
            return value, None
    rc, stdout, stderr = run_capture(["git", "rev-parse", "HEAD"])
    if rc != 0:
        return "", (stderr or stdout or "failed to resolve HEAD SHA").strip()
    return stdout.strip(), None


def resolve_branch(
    raw: str | None,
    *,
    sha: str,
    run_capture: Callable[[list[str]], tuple[int, str, str]],
) -> tuple[str, str | None]:
    if raw:
        value = raw.strip()
        if value:
            return value, None

    rc, stdout, _stderr = run_capture(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc == 0:
        branch = stdout.strip()
        if branch and branch != "HEAD":
            return branch, None

    rc, stdout, stderr = run_capture(
        ["git", "branch", "--contains", sha, "--format", "%(refname:short)"]
    )
    if rc == 0:
        candidates = [
            line.strip()
            for line in stdout.splitlines()
            if line.strip() and line.strip() != "HEAD"
        ]
        if candidates:
            for preferred in ("master", "develop"):
                if preferred in candidates:
                    return preferred, None
            return candidates[0], None

    detail = (stderr or stdout or "failed to resolve branch").strip()
    return "", detail


def current_branch_name(
    *,
    run_capture: Callable[[list[str]], tuple[int, str, str]],
) -> str:
    rc, stdout, _stderr = run_capture(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc != 0:
        return ""
    branch = stdout.strip()
    return "" if branch == "HEAD" else branch


def gh_run_list(
    *,
    workflow: str,
    sha: str,
    limit: int,
    repo: str | None,
    branch: str,
    run_capture: Callable[[list[str]], tuple[int, str, str]],
) -> tuple[list[dict[str, Any]], str | None]:
    cmd = [
        "gh",
        "run",
        "list",
        "--workflow",
        workflow,
        "--commit",
        sha,
        "--limit",
        str(limit),
        "--json",
        "status,conclusion,headSha,url,createdAt,name",
    ]
    if branch:
        cmd.extend(["--branch", branch])
    if repo:
        cmd.extend(["--repo", repo])

    rc, stdout, stderr = run_capture(cmd)
    if rc != 0:
        return [], f"gh_run_list_failed: {(stderr or stdout).strip()}"

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return [], f"invalid_json_from_gh_run_list: {exc}"
    if not isinstance(payload, list):
        return [], "unexpected_gh_run_list_payload"
    return [row for row in payload if isinstance(row, dict)], None


def build_report(
    args: Any,
    *,
    run_capture: Callable[[list[str]], tuple[int, str, str]],
    local_workflow_exists_by_name: Callable[[str], bool],
    is_ci_environment: Callable[[], bool],
    looks_like_connectivity_error: Callable[[str], bool],
    default_wait_seconds: int,
    default_poll_seconds: int,
) -> dict[str, Any]:
    allow_branch_fallback = bool(getattr(args, "allow_branch_fallback", False))
    report: dict[str, Any] = {
        "command": "check_coderabbit_gate",
        "ok": False,
        "workflow": args.workflow,
        "sha": "",
        "branch": "",
        "branch_requested": "",
        "reason": "",
        "checked_runs": 0,
        "matching_runs": 0,
        "fallback_without_branch": False,
        "allow_branch_fallback": allow_branch_fallback,
        "warnings": [],
        "latest_match": {},
        "wait_seconds": max(int(getattr(args, "wait_seconds", default_wait_seconds) or 0), 0),
        "poll_seconds": max(int(getattr(args, "poll_seconds", default_poll_seconds) or 1), 1),
    }

    sha, sha_error = resolve_sha(args.sha, run_capture=run_capture)
    if sha_error:
        report["reason"] = f"resolve_sha_failed: {sha_error}"
        return report
    report["sha"] = sha

    requested_branch = str(args.branch or "").strip()
    report["branch_requested"] = requested_branch
    branch_filter = requested_branch
    if requested_branch and looks_like_sha(requested_branch):
        report["warnings"].append(
            "branch argument resembles a commit SHA; ignored branch filter and used commit filter only."
        )
        branch_filter = ""
    elif not requested_branch:
        resolved_branch, branch_error = resolve_branch(
            None,
            sha=sha,
            run_capture=run_capture,
        )
        if resolved_branch:
            branch_filter = resolved_branch
        elif branch_error:
            report["warnings"].append(f"branch auto-detect skipped: {branch_error}")

    report["branch"] = branch_filter
    if args.repo:
        report["repo"] = args.repo

    wait_seconds = report["wait_seconds"]
    poll_seconds = report["poll_seconds"]
    deadline = time.monotonic() + wait_seconds
    fallback_warning = "no runs found for branch filter; retried with commit-only filter."

    while True:
        runs, run_error = gh_run_list(
            workflow=args.workflow,
            sha=sha,
            limit=args.limit,
            repo=args.repo,
            branch=branch_filter,
            run_capture=run_capture,
        )
        if run_error:
            workflow_missing = "could not find any workflows named" in run_error.lower()
            current_branch = current_branch_name(run_capture=run_capture)
            if (
                workflow_missing
                and branch_filter
                and current_branch
                and current_branch != branch_filter
                and local_workflow_exists_by_name(args.workflow)
            ):
                report["ok"] = True
                report["reason"] = "workflow_not_present_on_target_branch_yet"
                report["warnings"].append(
                    "workflow is defined locally but not found on the requested branch; "
                    "treated as non-blocking outside that target branch."
                )
                return report
            if looks_like_connectivity_error(run_error) and not is_ci_environment():
                report["ok"] = True
                report["reason"] = "gh_unreachable_local_non_blocking"
                report["warnings"].append(
                    "unable to reach GitHub API from local environment; "
                    "treated as non-blocking outside CI/release lanes."
                )
                return report
            report["reason"] = run_error
            return report

        if not runs and branch_filter:
            if not allow_branch_fallback:
                report["reason"] = "no_workflow_runs_for_requested_branch"
                report["warnings"].append(
                    "branch filter returned no runs and commit-only fallback is disabled "
                    "(use --allow-branch-fallback to enable fallback)."
                )
                return report
            fallback_runs, fallback_error = gh_run_list(
                workflow=args.workflow,
                sha=sha,
                limit=args.limit,
                repo=args.repo,
                branch="",
                run_capture=run_capture,
            )
            if fallback_error:
                report["reason"] = fallback_error
                return report
            report["fallback_without_branch"] = True
            if fallback_warning not in report["warnings"]:
                report["warnings"].append(fallback_warning)
            report["branch"] = ""
            runs = fallback_runs

        report["checked_runs"] = len(runs)
        matching = [
            run
            for run in runs
            if isinstance(run, dict) and str(run.get("headSha") or "").strip() == sha
        ]
        report["matching_runs"] = len(matching)

        if matching:
            def _sort_key(row: dict[str, Any]) -> tuple[int, datetime]:
                parsed_ok, parsed_value = parse_iso(row.get("createdAt"))
                return (1 if parsed_ok else 0, parsed_value)

            matching.sort(key=_sort_key, reverse=True)
            latest = matching[0]
            status = str(latest.get("status") or "").strip().lower()
            conclusion = str(latest.get("conclusion") or "").strip().lower()
            report["latest_match"] = {
                "status": status,
                "conclusion": conclusion,
                "url": latest.get("url"),
                "created_at": latest.get("createdAt"),
            }

            if status == "completed" and conclusion == args.require_conclusion:
                report["ok"] = True
                report["reason"] = "coderabbit_gate_passed"
                return report

            if status != "completed":
                report["reason"] = f"latest_matching_run_not_completed: status={status}"
            else:
                report["reason"] = (
                    f"latest_matching_run_conclusion_{conclusion or 'unknown'}"
                    f"_does_not_match_required_{args.require_conclusion}"
                )
        else:
            report["latest_match"] = {}
            report["reason"] = "no_matching_workflow_runs_for_sha"

        if time.monotonic() >= deadline:
            return report
        time.sleep(poll_seconds)


def render_report_md(report: dict[str, Any], *, title: str) -> str:
    """Render a standard gate report in markdown format."""
    lines = [f"# {title}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- workflow: {report.get('workflow')}")
    if report.get("repo"):
        lines.append(f"- repo: {report.get('repo')}")
    lines.append(f"- branch_requested: {report.get('branch_requested') or '(none)'}")
    lines.append(f"- branch: {report.get('branch')}")
    lines.append(f"- allow_branch_fallback: {report.get('allow_branch_fallback')}")
    lines.append(f"- fallback_without_branch: {report.get('fallback_without_branch')}")
    lines.append(f"- sha: {report.get('sha')}")
    lines.append(f"- checked_runs: {report.get('checked_runs')}")
    lines.append(f"- matching_runs: {report.get('matching_runs')}")
    lines.append(f"- reason: {report.get('reason')}")
    warnings = report.get("warnings")
    if isinstance(warnings, list):
        for warning in warnings:
            lines.append(f"- warning: {warning}")
    latest = report.get("latest_match")
    if isinstance(latest, dict) and latest:
        lines.append(
            "- latest_match: "
            + ", ".join(
                [
                    f"status={latest.get('status')}",
                    f"conclusion={latest.get('conclusion')}",
                    f"url={latest.get('url')}",
                    f"created_at={latest.get('created_at')}",
                ]
            )
        )
    return "\n".join(lines)
