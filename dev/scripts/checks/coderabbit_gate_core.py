"""Core helpers shared by CodeRabbit workflow gate scripts."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from typing import Any, Callable

try:
    from dev.scripts.checks.coderabbit_gate_support import (
        classify_matching_runs,
        non_blocking_missing_run_reason,
        remote_refs_containing_sha,
        resolve_requested_branch,
        render_report_md,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script fallback
    from coderabbit_gate_support import (
        classify_matching_runs,
        non_blocking_missing_run_reason,
        remote_refs_containing_sha,
        resolve_requested_branch,
        render_report_md,
    )

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
        "wait_seconds": max(
            int(getattr(args, "wait_seconds", default_wait_seconds) or 0), 0
        ),
        "poll_seconds": max(
            int(getattr(args, "poll_seconds", default_poll_seconds) or 1), 1
        ),
    }

    sha, sha_error = resolve_sha(args.sha, run_capture=run_capture)
    if sha_error:
        report["reason"] = f"resolve_sha_failed: {sha_error}"
        return report
    report["sha"] = sha

    requested_branch = str(args.branch or "").strip()
    report["branch_requested"] = requested_branch
    branch_filter, initial_branch_filter, branch_warnings = resolve_requested_branch(
        requested_branch,
        sha=sha,
        run_capture=run_capture,
        looks_like_sha_fn=looks_like_sha,
        resolve_branch_fn=resolve_branch,
    )
    report["warnings"].extend(branch_warnings)

    report["branch"] = branch_filter
    if args.repo:
        report["repo"] = args.repo
    current_branch = current_branch_name(run_capture=run_capture)

    wait_seconds = report["wait_seconds"]
    poll_seconds = report["poll_seconds"]
    deadline = time.monotonic() + wait_seconds
    fallback_warning = (
        "no runs found for branch filter; retried with commit-only filter."
    )

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
            missing_run_status = non_blocking_missing_run_reason(
                effective_branch=branch_filter,
                current_branch=current_branch,
                remote_refs=[],
                allow_branch_fallback=allow_branch_fallback,
            )
            if missing_run_status is not None and branch_filter != current_branch:
                reason, warning = missing_run_status
                report["ok"] = True
                report["reason"] = reason
                report["warnings"].append(warning)
                return report
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
        matching_count, matched_success, matched_reason, latest_match = classify_matching_runs(
            runs,
            sha=sha,
            require_conclusion=args.require_conclusion,
        )
        report["matching_runs"] = matching_count
        report["latest_match"] = latest_match
        if matched_success is True:
            report["ok"] = True
            report["reason"] = matched_reason
            return report
        if matched_success is False:
            report["reason"] = matched_reason
        else:
            remote_refs, remote_refs_error = remote_refs_containing_sha(
                sha,
                run_capture=run_capture,
            )
            if remote_refs_error:
                report["warnings"].append(
                    f"remote publication detection skipped: {remote_refs_error}"
                )
            effective_branch = initial_branch_filter or current_branch
            missing_run_status = non_blocking_missing_run_reason(
                effective_branch=effective_branch,
                current_branch=current_branch,
                remote_refs=remote_refs,
                allow_branch_fallback=allow_branch_fallback,
            )
            if missing_run_status is not None:
                reason, warning = missing_run_status
                report["ok"] = True
                report["reason"] = reason
                report["warnings"].append(warning)
                return report
            report["reason"] = matched_reason

        if time.monotonic() >= deadline:
            return report
        time.sleep(poll_seconds)
