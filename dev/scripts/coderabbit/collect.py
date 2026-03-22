#!/usr/bin/env python3
"""CodeRabbit finding collection helper for workflow bridge."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dev.scripts.coderabbit.support import (
    classify_category,
    classify_severity,
    dedupe_findings,
    gh_api,
    has_coderabbit_token,
    is_coderabbit_user,
    summarize,
)


def collect_findings(
    *,
    event: dict[str, Any],
    event_name: str,
    repo: str,
    pr_number: str,
    pushed_sha: str,
    warnings: list[str],
) -> tuple[list[dict[str, str]], str]:
    pr_payload = event.get("pull_request") if pr_number else {}
    if pr_number and not isinstance(pr_payload, dict):
        pr_payload = gh_api(
            f"/repos/{repo}/pulls/{pr_number}",
            default={},
            warnings=warnings,
        )

    head_sha = str(pr_payload.get("head", {}).get("sha") or "").strip()
    if not head_sha and pushed_sha:
        head_sha = pushed_sha
    if not head_sha:
        warnings.append("Unable to resolve PR head SHA; check-run ingestion skipped.")

    review_comments = (
        gh_api(
            f"/repos/{repo}/pulls/{pr_number}/comments?per_page=100",
            default=[],
            warnings=warnings,
        )
        if pr_number
        else []
    )
    issue_comments = (
        gh_api(
            f"/repos/{repo}/issues/{pr_number}/comments?per_page=100",
            default=[],
            warnings=warnings,
        )
        if pr_number
        else []
    )
    reviews = (
        gh_api(
            f"/repos/{repo}/pulls/{pr_number}/reviews?per_page=100",
            default=[],
            warnings=warnings,
        )
        if pr_number
        else []
    )
    check_runs_payload = (
        gh_api(
            f"/repos/{repo}/commits/{head_sha}/check-runs?per_page=100",
            default={},
            warnings=warnings,
        )
        if head_sha
        else {}
    )

    findings: list[dict[str, str]] = []

    if isinstance(review_comments, list):
        for comment in review_comments:
            if not is_coderabbit_user(comment.get("user")):
                continue
            body = str(comment.get("body") or "")
            comment_commit = str(comment.get("commit_id") or "").strip()
            if head_sha and comment_commit and comment_commit != head_sha:
                continue
            summary = summarize(body, "CodeRabbit review comment")
            path = str(comment.get("path") or "").strip()
            line = comment.get("line") or comment.get("original_line")
            if path:
                location = f"{path}:{line}" if line else path
                summary = f"{location} - {summary}"
            findings.append(
                {
                    "category": classify_category(body),
                    "severity": classify_severity(body, default="low"),
                    "path": path,
                    "line": line,
                    "summary": summary,
                }
            )

    if isinstance(issue_comments, list):
        for comment in issue_comments:
            if not is_coderabbit_user(comment.get("user")):
                continue
            body = str(comment.get("body") or "")
            findings.append(
                {
                    "category": classify_category(body),
                    "severity": classify_severity(body, default="info"),
                    "summary": summarize(body, "CodeRabbit PR comment"),
                }
            )

    if isinstance(reviews, list):
        for review in reviews:
            if not is_coderabbit_user(review.get("user")):
                continue
            state = str(review.get("state") or "").strip().upper()
            body = str(review.get("body") or "")
            review_commit = str(review.get("commit_id") or "").strip()
            if head_sha and review_commit and review_commit != head_sha:
                continue
            default_severity = "high" if state == "CHANGES_REQUESTED" else "info"
            findings.append(
                {
                    "category": classify_category(body),
                    "severity": classify_severity(body, default=default_severity),
                    "summary": summarize(body, f"CodeRabbit review state: {state or 'UNKNOWN'}"),
                }
            )

    if isinstance(check_runs_payload, dict):
        check_runs = check_runs_payload.get("check_runs", [])
        if isinstance(check_runs, list):
            for check_run in check_runs:
                app = check_run.get("app") or {}
                app_slug = str(app.get("slug") or "")
                app_name = str(app.get("name") or "")
                run_name = str(check_run.get("name") or "")
                if not any(has_coderabbit_token(value) for value in (app_slug, app_name, run_name)):
                    continue
                conclusion = str(check_run.get("conclusion") or "pending").lower()
                if conclusion in {"success", "neutral", "skipped"}:
                    continue
                findings.append(
                    {
                        "category": "ci",
                        "severity": "high" if conclusion == "failure" else "medium",
                        "summary": f"CodeRabbit check '{run_name or app_name}' concluded '{conclusion}'",
                    }
                )

    _ = event_name
    deduped = dedupe_findings(findings)
    if warnings:
        deduped.append(
            {
                "category": "infra",
                "severity": "medium",
                "summary": "; ".join(warnings),
            }
        )
    return deduped, head_sha
