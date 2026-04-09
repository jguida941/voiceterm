"""Shared helpers for CodeRabbit workflow-gate checks."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

LOCAL_CONNECTIVITY_ERROR_HINTS = (
    "error connecting to api.github.com",
    "check your internet connection",
    "failed to connect",
    "network is unreachable",
)


def workflow_name_from_file(path: Path) -> str:
    """Return workflow `name:` from one workflow file, or empty when missing."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower().startswith("name:"):
            return stripped.split(":", 1)[1].strip().strip("\"'")
        break
    return ""


def local_workflow_exists_by_name(repo_root: Path, workflow_name: str) -> bool:
    """Check whether a workflow with `workflow_name` exists under `.github/workflows`."""
    workflows_dir = repo_root / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return False
    for candidate in workflows_dir.glob("*.yml"):
        if workflow_name_from_file(candidate) == workflow_name:
            return True
    for candidate in workflows_dir.glob("*.yaml"):
        if workflow_name_from_file(candidate) == workflow_name:
            return True
    return False


def is_ci_environment() -> bool:
    """Return True when current process is running under CI semantics."""
    ci_value = str(os.getenv("CI", "")).strip().lower()
    return ci_value in {"1", "true", "yes"}


def looks_like_connectivity_error(message: str) -> bool:
    """Return True when message matches known local GitHub-connectivity failures."""
    lowered = message.lower()
    return any(hint in lowered for hint in LOCAL_CONNECTIVITY_ERROR_HINTS)


def remote_refs_containing_sha(
    sha: str,
    *,
    run_capture: Callable[[list[str]], tuple[int, str, str]],
) -> tuple[list[str], str | None]:
    """Return local remote-tracking refs that already contain ``sha``."""
    rc, stdout, stderr = run_capture(
        ["git", "branch", "-r", "--contains", sha, "--format", "%(refname:short)"]
    )
    if rc != 0:
        detail = (stderr or stdout or "failed to inspect remote-tracking refs").strip()
        return [], detail
    refs = [line.strip() for line in stdout.splitlines() if line.strip()]
    return refs, None


def non_blocking_missing_run_reason(
    *,
    effective_branch: str,
    current_branch: str,
    remote_refs: list[str],
    allow_branch_fallback: bool,
) -> tuple[str, str] | None:
    """Return a non-blocking missing-run classification when one applies."""
    if (
        effective_branch
        and current_branch
        and effective_branch != current_branch
        and not remote_refs
    ):
        return (
            "workflow_runs_not_present_on_target_branch_yet",
            "requested branch does not yet contain this commit; treated as "
            "non-blocking until publish reaches that branch.",
        )

    if (
        allow_branch_fallback
        and effective_branch
        and current_branch
        and effective_branch == current_branch
        and not remote_refs
    ):
        return (
            "workflow_runs_not_present_for_unpublished_sha_yet",
            "current SHA is not present in local remote-tracking refs yet; "
            "treated as non-blocking until the commit is published.",
        )

    return None


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


def resolve_requested_branch(
    requested_branch: str,
    *,
    sha: str,
    run_capture: Callable[[list[str]], tuple[int, str, str]],
    looks_like_sha_fn: Callable[[str], bool],
    resolve_branch_fn: Callable[..., tuple[str, str | None]],
) -> tuple[str, str, list[str]]:
    """Resolve the branch filter and any associated warnings."""
    warnings: list[str] = []
    branch_filter = requested_branch
    initial_branch_filter = requested_branch

    if requested_branch and looks_like_sha_fn(requested_branch):
        warnings.append(
            "branch argument resembles a commit SHA; ignored branch filter and used commit filter only."
        )
        return "", "", warnings

    if requested_branch:
        return branch_filter, initial_branch_filter, warnings

    resolved_branch, branch_error = resolve_branch_fn(
        None,
        sha=sha,
        run_capture=run_capture,
    )
    if resolved_branch:
        return resolved_branch, resolved_branch, warnings
    if branch_error:
        warnings.append(f"branch auto-detect skipped: {branch_error}")
    return "", "", warnings


def classify_matching_runs(
    runs: list[dict[str, Any]],
    *,
    sha: str,
    require_conclusion: str,
) -> tuple[int, bool | None, str, dict[str, Any]]:
    """Classify the newest matching workflow run for ``sha``."""
    matching = [
        run
        for run in runs
        if isinstance(run, dict) and str(run.get("headSha") or "").strip() == sha
    ]
    if not matching:
        return 0, None, "no_matching_workflow_runs_for_sha", {}

    def _parse_iso(value: Any) -> tuple[bool, datetime]:
        raw = str(value or "").strip()
        if not raw:
            return False, datetime.min
        normalized = raw.replace("Z", "+00:00")
        try:
            return True, datetime.fromisoformat(normalized)
        except ValueError:
            return False, datetime.min

    def _sort_key(row: dict[str, Any]) -> tuple[int, datetime]:
        parsed_ok, parsed_value = _parse_iso(row.get("createdAt"))
        return (1 if parsed_ok else 0, parsed_value)

    matching.sort(key=_sort_key, reverse=True)
    latest = matching[0]
    status = str(latest.get("status") or "").strip().lower()
    conclusion = str(latest.get("conclusion") or "").strip().lower()
    latest_match = {
        "status": status,
        "conclusion": conclusion,
        "url": latest.get("url"),
        "created_at": latest.get("createdAt"),
    }

    if status == "completed" and conclusion == require_conclusion:
        return len(matching), True, "coderabbit_gate_passed", latest_match
    if status != "completed":
        return (
            len(matching),
            False,
            f"latest_matching_run_not_completed: status={status}",
            latest_match,
        )
    return (
        len(matching),
        False,
        f"latest_matching_run_conclusion_{conclusion or 'unknown'}"
        f"_does_not_match_required_{require_conclusion}",
        latest_match,
    )
