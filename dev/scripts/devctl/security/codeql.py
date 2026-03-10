"""Shared helpers for optional CodeQL alert checks in `devctl security`."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable

CODEQL_SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
GIT_REMOTE_RE = re.compile(
    r"""^(?:https://github\.com/|git@github\.com:)(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?$"""
)


def repo_from_origin_remote(repo_root: Path) -> str | None:
    """Return owner/repo from `origin` remote URL when possible."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    remote = (result.stdout or "").strip()
    if not remote:
        return None
    match = GIT_REMOTE_RE.match(remote)
    if not match:
        return None
    return match.group("repo")


def _normalize_codeql_severity(value: str | None) -> str | None:
    raw = (value or "").strip().lower()
    if raw in CODEQL_SEVERITY_ORDER:
        return raw
    if raw == "error":
        return "high"
    if raw == "warning":
        return "medium"
    if raw == "note":
        return "low"
    return None


def _is_nonblocking_codeql_api_state(message: str) -> bool:
    """Return True for known non-actionable CodeQL API states in optional mode."""
    normalized = message.lower()
    return (
        "no analysis found" in normalized
        or 'needs the "admin:repo_hook" scope' in normalized
    )


def run_codeql_alerts_step(
    *,
    repo_root: Path,
    repo_slug: str,
    min_severity: str,
    required: bool,
    dry_run: bool,
    env: dict,
    make_internal_step: Callable[..., dict],
) -> tuple[dict, list[str]]:
    """Query open CodeQL alerts and fail if any meet/exceed severity threshold."""
    cmd = [
        "gh",
        "api",
        f"/repos/{repo_slug}/code-scanning/alerts?state=open&tool_name=CodeQL&per_page=100",
    ]
    if dry_run:
        return (
            make_internal_step(
                name="codeql-alerts",
                cmd=cmd,
                returncode=0,
                duration_s=0.0,
                skipped=True,
                details={
                    "repo": repo_slug,
                    "min_severity": min_severity,
                    "reason": "dry-run",
                },
            ),
            [],
        )

    if shutil.which("gh") is None:
        message = "gh is not installed. Install it to query CodeQL alerts."
        if required:
            return (
                make_internal_step(
                    name="codeql-alerts",
                    cmd=cmd,
                    returncode=127,
                    duration_s=0.0,
                    error=message,
                ),
                [],
            )
        return (
            make_internal_step(
                name="codeql-alerts",
                cmd=cmd,
                returncode=0,
                duration_s=0.0,
                skipped=True,
                details={"reason": message},
            ),
            [message],
        )

    start = time.time()
    result = subprocess.run(
        cmd,
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        message = stderr or "failed to query CodeQL alerts with gh api"
        if not required and _is_nonblocking_codeql_api_state(message):
            step = make_internal_step(
                name="codeql-alerts",
                cmd=cmd,
                returncode=0,
                duration_s=time.time() - start,
                skipped=True,
                details={"reason": message},
            )
            return step, []
        step = make_internal_step(
            name="codeql-alerts",
            cmd=cmd,
            returncode=1 if required else 0,
            duration_s=time.time() - start,
            skipped=not required,
            error=message if required else None,
            details=None if required else {"reason": message},
        )
        return (step, [] if required else [message])

    payload = (result.stdout or "").strip()
    if not payload:
        step = make_internal_step(
            name="codeql-alerts",
            cmd=cmd,
            returncode=0,
            duration_s=time.time() - start,
            details={
                "repo": repo_slug,
                "min_severity": min_severity,
                "open_alerts": 0,
                "blocking_alerts": 0,
            },
        )
        return step, []

    try:
        alerts = json.loads(payload)
    except json.JSONDecodeError as exc:
        message = f"invalid JSON from gh api: {exc}"
        step = make_internal_step(
            name="codeql-alerts",
            cmd=cmd,
            returncode=1 if required else 0,
            duration_s=time.time() - start,
            skipped=not required,
            error=message if required else None,
            details=None if required else {"reason": message},
        )
        return (step, [] if required else [message])

    if not isinstance(alerts, list):
        message = "unexpected gh api payload: expected a JSON list of alerts"
        step = make_internal_step(
            name="codeql-alerts",
            cmd=cmd,
            returncode=1 if required else 0,
            duration_s=time.time() - start,
            skipped=not required,
            error=message if required else None,
            details=None if required else {"reason": message},
        )
        return (step, [] if required else [message])

    threshold = CODEQL_SEVERITY_ORDER[min_severity]
    blocking_alerts = 0
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        rule = alert.get("rule") or {}
        severity = _normalize_codeql_severity(rule.get("security_severity_level"))
        if severity is None:
            severity = _normalize_codeql_severity(rule.get("severity"))
        if severity is None:
            continue
        if CODEQL_SEVERITY_ORDER[severity] >= threshold:
            blocking_alerts += 1

    details = {
        "repo": repo_slug,
        "min_severity": min_severity,
        "open_alerts": len(alerts),
        "blocking_alerts": blocking_alerts,
    }
    step = make_internal_step(
        name="codeql-alerts",
        cmd=cmd,
        returncode=0 if blocking_alerts == 0 else 1,
        duration_s=time.time() - start,
        details=details,
    )
    return step, []
