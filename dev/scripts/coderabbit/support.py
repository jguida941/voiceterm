#!/usr/bin/env python3
"""Shared helpers for CodeRabbit triage workflow bridge."""

from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any


def gh_api(path: str, *, default: Any, warnings: list[str]) -> Any:
    try:
        output = subprocess.check_output(
            ["gh", "api", "-H", "Accept: application/vnd.github+json", path],
            text=True,
        )
        return json.loads(output)
    except Exception as exc:  # broad-except: allow reason=workflow helper must degrade cleanly when gh/auth/network access is unavailable fallback=append warning and return caller default  # pragma: no cover - workflow helper
        warnings.append(f"gh api failed for {path}: {exc}")
        return default


def has_coderabbit_token(text: Any) -> bool:
    return "coderabbit" in str(text or "").lower()


def is_coderabbit_user(user: Any) -> bool:
    return isinstance(user, dict) and has_coderabbit_token(user.get("login"))


def summarize(body: Any, fallback: str) -> str:
    for raw_line in str(body or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[`>#*\-\s]+", "", line).strip()
        if line:
            return line[:220]
    return fallback


def classify_category(text: str) -> str:
    lowered = text.lower()
    if re.search(r"\b(security|injection|credential|secret|xss|sqli)\b", lowered):
        return "security"
    if re.search(r"\b(ci|workflow|pipeline|action|check)\b", lowered):
        return "ci"
    if re.search(r"\b(perf|performance|latency|throughput|allocation|memory)\b", lowered):
        return "performance"
    if re.search(r"\b(doc|readme|guide|changelog)\b", lowered):
        return "docs"
    return "quality"


def classify_severity(text: str, *, default: str = "info") -> str:
    lowered = text.lower()
    if re.search(r"\b(critical|sev0|p0|blocker)\b", lowered):
        return "critical"
    if re.search(r"\b(high|sev1|p1|urgent)\b", lowered):
        return "high"
    if re.search(r"\b(low|sev3|p3|minor)\b", lowered):
        return "low"
    if re.search(r"\b(info|informational|nit|p4)\b", lowered):
        return "info"
    if re.search(r"\b(medium|moderate|sev2|p2|warning|warn)\b", lowered):
        return "medium"
    return default


def dedupe_findings(items: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for finding in items:
        key = (finding.get("category"), finding.get("severity"), finding.get("summary"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped


def resolve_repository(event: dict[str, Any], repo_input: str | None) -> str:
    repo = (repo_input or "").strip()
    if not repo:
        repo = str(event.get("repository", {}).get("full_name") or "").strip()
    if not repo:
        repo = str(os.getenv("GITHUB_REPOSITORY", "")).strip()
    if not repo:
        raise RuntimeError("Unable to resolve repository slug.")
    return repo


def resolve_pr_number(
    *,
    event: dict[str, Any],
    event_name: str,
    repo: str,
    pr_input: str | None,
    pushed_sha: str,
    warnings: list[str],
) -> str:
    pr_number = (pr_input or "").strip()
    if not pr_number:
        pr = event.get("pull_request")
        if isinstance(pr, dict):
            pr_number = str(pr.get("number") or "").strip()
    if not pr_number:
        issue = event.get("issue")
        if isinstance(issue, dict) and issue.get("pull_request"):
            pr_number = str(issue.get("number") or "").strip()
    if not pr_number and event_name == "push":
        pulls = gh_api(
            f"/repos/{repo}/commits/{pushed_sha}/pulls?per_page=20",
            default=[],
            warnings=warnings,
        )
        if isinstance(pulls, list):
            selected = None
            for pull in pulls:
                if isinstance(pull, dict) and pull.get("merged_at"):
                    selected = pull
                    break
            if selected is None and pulls:
                selected = pulls[0]
            if isinstance(selected, dict):
                pr_number = str(selected.get("number") or "").strip()
    if not pr_number and event_name != "push":
        raise RuntimeError("Unable to resolve pull request number.")
    return pr_number
