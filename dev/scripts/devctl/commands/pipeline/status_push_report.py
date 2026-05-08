"""Latest push-report projection for commit-pipeline status."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..vcs.push_artifact import latest_push_report_relpath, load_latest_push_report


def load_pipeline_push_report(repo_root: Path) -> dict[str, Any] | None:
    """Load the latest managed push report for pipeline status."""
    return load_latest_push_report(repo_root=repo_root)


def push_report_view(
    report: dict[str, Any] | None,
    *,
    repo_root: Path,
    current_branch: str,
    current_head: str,
) -> dict[str, Any]:
    path = latest_push_report_relpath(repo_root=repo_root)
    if not isinstance(report, dict):
        return _empty_push_report_view(path)
    artifacts = report.get("artifacts")
    if isinstance(artifacts, dict):
        path = str(
            artifacts.get("push_report_json")
            or artifacts.get("latest_json")
            or path
        )
    head_commit = str(report.get("head_commit") or "")
    branch = str(report.get("branch") or "")
    view = _empty_push_report_view(path)
    view["exists"] = True
    view["status"] = str(report.get("status") or "")
    view["reason"] = str(report.get("reason") or "")
    view["head_commit"] = head_commit
    view["branch"] = branch
    view["published_remote"] = bool(report.get("published_remote"))
    view["post_push_green"] = bool(report.get("post_push_green"))
    view["matches_current_head"] = bool(current_head and head_commit == current_head)
    view["matches_current_branch"] = bool(current_branch and branch == current_branch)
    return view


def _empty_push_report_view(path: str) -> dict[str, Any]:
    view: dict[str, Any] = {}
    view["exists"] = False
    view["path"] = path
    view["status"] = ""
    view["reason"] = ""
    view["head_commit"] = ""
    view["branch"] = ""
    view["published_remote"] = False
    view["post_push_green"] = False
    view["matches_current_head"] = False
    view["matches_current_branch"] = False
    return view
