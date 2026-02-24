"""Shared helpers for CodeRabbit workflow-gate checks."""

from __future__ import annotations

import os
from pathlib import Path

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
