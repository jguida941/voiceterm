"""Collect git/CI/mutation status for reports."""

import json
import shutil
import subprocess
from typing import Dict

from .config import REPO_ROOT


def collect_git_status() -> Dict:
    """Return branch and dirty state info from git."""
    if not shutil.which("git"):
        return {"error": "git not found"}
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
        status_raw = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        return {"error": f"git failed: {exc}"}

    changes = []
    for line in status_raw.splitlines():
        if not line:
            continue
        status = line[:2].strip()
        path = line[3:]
        if "->" in path:
            path = path.split("->")[-1].strip()
        changes.append({"status": status, "path": path})

    changed_paths = {change["path"] for change in changes}
    return {
        "branch": branch,
        "changes": changes,
        "changelog_updated": "dev/CHANGELOG.md" in changed_paths,
        "master_plan_updated": "dev/active/MASTER_PLAN.md" in changed_paths,
    }


def collect_ci_runs(limit: int) -> Dict:
    """Return recent GitHub Actions runs via gh, if available."""
    if not shutil.which("gh"):
        return {"error": "gh not found"}
    try:
        output = subprocess.check_output(
            [
                "gh",
                "run",
                "list",
                "--limit",
                str(limit),
                "--json",
                "status,conclusion,displayTitle,headSha,createdAt,updatedAt",
            ],
            cwd=REPO_ROOT,
            text=True,
        )
        return {"runs": json.loads(output)}
    except Exception as exc:
        return {"error": f"gh run list failed: {exc}"}


def collect_mutation_summary() -> Dict:
    """Return the latest mutation summary via mutants.py."""
    if not shutil.which("python3"):
        return {"error": "python3 not found"}
    try:
        output = subprocess.check_output(
            ["python3", "dev/scripts/mutants.py", "--results-only", "--json"],
            cwd=REPO_ROOT,
            text=True,
        )
        return {"results": json.loads(output)}
    except Exception as exc:
        return {"error": f"mutants summary failed: {exc}"}
