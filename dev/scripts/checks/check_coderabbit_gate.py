#!/usr/bin/env python3
"""Verify that CodeRabbit triage gate passed for a specific commit SHA."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from dev.scripts.checks.coderabbit_gate_support import (
        is_ci_environment,
        local_workflow_exists_by_name,
        looks_like_connectivity_error,
    )
except ModuleNotFoundError:
    from coderabbit_gate_support import (
        is_ci_environment,
        local_workflow_exists_by_name,
        looks_like_connectivity_error,
    )

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKFLOW = "CodeRabbit Triage Bridge"
DEFAULT_LIMIT = 50


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def _resolve_sha(raw: str | None) -> tuple[str, str | None]:
    if raw:
        value = raw.strip()
        if value:
            return value, None
    rc, stdout, stderr = _run_capture(["git", "rev-parse", "HEAD"])
    if rc != 0:
        return "", (stderr or stdout or "failed to resolve HEAD SHA").strip()
    return stdout.strip(), None


def _looks_like_sha(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", value.strip()))


def _resolve_branch(raw: str | None, sha: str) -> tuple[str, str | None]:
    if raw:
        value = raw.strip()
        if value:
            return value, None

    rc, stdout, stderr = _run_capture(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc == 0:
        branch = stdout.strip()
        if branch and branch != "HEAD":
            return branch, None

    rc, stdout, stderr = _run_capture(["git", "branch", "--contains", sha, "--format", "%(refname:short)"])
    if rc == 0:
        candidates = [line.strip() for line in stdout.splitlines() if line.strip() and line.strip() != "HEAD"]
        if candidates:
            for preferred in ("master", "develop"):
                if preferred in candidates:
                    return preferred, None
            return candidates[0], None

    detail = (stderr or stdout or "failed to resolve branch").strip()
    return "", detail


def _current_branch_name() -> str:
    rc, stdout, _stderr = _run_capture(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc != 0:
        return ""
    branch = stdout.strip()
    if branch == "HEAD":
        return ""
    return branch


def _local_workflow_exists_by_name(workflow_name: str) -> bool:
    return local_workflow_exists_by_name(REPO_ROOT, workflow_name)


def _gh_run_list(
    *,
    workflow: str,
    sha: str,
    limit: int,
    repo: str | None,
    branch: str,
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

    rc, stdout, stderr = _run_capture(cmd)
    if rc != 0:
        return [], f"gh_run_list_failed: {(stderr or stdout).strip()}"

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return [], f"invalid_json_from_gh_run_list: {exc}"
    if not isinstance(payload, list):
        return [], "unexpected_gh_run_list_payload"
    return [row for row in payload if isinstance(row, dict)], None


def _is_ci_environment() -> bool:
    return is_ci_environment()


def _looks_like_connectivity_error(message: str) -> bool:
    return looks_like_connectivity_error(message)


def _parse_iso(value: Any) -> tuple[bool, datetime]:
    raw = str(value or "").strip()
    if not raw:
        return False, datetime.min
    normalized = raw.replace("Z", "+00:00")
    try:
        return True, datetime.fromisoformat(normalized)
    except ValueError:
        return False, datetime.min


def _build_report(args) -> dict:
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
        "warnings": [],
        "latest_match": {},
    }

    sha, sha_error = _resolve_sha(args.sha)
    if sha_error:
        report["reason"] = f"resolve_sha_failed: {sha_error}"
        return report
    report["sha"] = sha

    requested_branch = str(args.branch or "").strip()
    report["branch_requested"] = requested_branch
    branch_filter = requested_branch
    if requested_branch and _looks_like_sha(requested_branch):
        report["warnings"].append(
            "branch argument resembles a commit SHA; ignored branch filter and used commit filter only."
        )
        branch_filter = ""
    elif not requested_branch:
        resolved_branch, branch_error = _resolve_branch(None, sha)
        if resolved_branch:
            branch_filter = resolved_branch
        elif branch_error:
            report["warnings"].append(f"branch auto-detect skipped: {branch_error}")

    report["branch"] = branch_filter
    if args.repo:
        report["repo"] = args.repo

    runs, run_error = _gh_run_list(
        workflow=args.workflow,
        sha=sha,
        limit=args.limit,
        repo=args.repo,
        branch=branch_filter,
    )
    if run_error:
        workflow_missing = "could not find any workflows named" in run_error.lower()
        current_branch = _current_branch_name()
        if (
            workflow_missing
            and branch_filter
            and current_branch
            and current_branch != branch_filter
            and _local_workflow_exists_by_name(args.workflow)
        ):
            report["ok"] = True
            report["reason"] = "workflow_not_present_on_target_branch_yet"
            report["warnings"].append(
                "workflow is defined locally but not found on the requested branch; "
                "treated as non-blocking outside that target branch."
            )
            return report
        if _looks_like_connectivity_error(run_error) and not _is_ci_environment():
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
        fallback_runs, fallback_error = _gh_run_list(
            workflow=args.workflow,
            sha=sha,
            limit=args.limit,
            repo=args.repo,
            branch="",
        )
        if fallback_error:
            report["reason"] = fallback_error
            return report
        report["fallback_without_branch"] = True
        report["warnings"].append("no runs found for branch filter; retried with commit-only filter.")
        report["branch"] = ""
        runs = fallback_runs

    report["checked_runs"] = len(runs)
    matching = [run for run in runs if isinstance(run, dict) and str(run.get("headSha") or "").strip() == sha]
    report["matching_runs"] = len(matching)
    if not matching:
        report["reason"] = "no_matching_workflow_runs_for_sha"
        return report

    def _sort_key(row: dict) -> tuple[int, datetime]:
        parsed_ok, parsed_value = _parse_iso(row.get("createdAt"))
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

    if status != "completed":
        report["reason"] = f"latest_matching_run_not_completed: status={status}"
        return report
    if conclusion != args.require_conclusion:
        report["reason"] = (
            f"latest_matching_run_conclusion_{conclusion or 'unknown'}"
            f"_does_not_match_required_{args.require_conclusion}"
        )
        return report

    report["ok"] = True
    report["reason"] = "coderabbit_gate_passed"
    return report


def _render_md(report: dict) -> str:
    lines = ["# check_coderabbit_gate", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- workflow: {report.get('workflow')}")
    if report.get("repo"):
        lines.append(f"- repo: {report.get('repo')}")
    lines.append(f"- branch_requested: {report.get('branch_requested') or '(none)'}")
    lines.append(f"- branch: {report.get('branch')}")
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW)
    parser.add_argument("--repo", help="owner/repo override for gh run list")
    parser.add_argument("--sha", help="Commit SHA to validate (default: HEAD)")
    parser.add_argument(
        "--branch",
        help="Optional branch hint for gh run list; commit filtering is always applied.",
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--require-conclusion", default="success")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = _build_report(args)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
