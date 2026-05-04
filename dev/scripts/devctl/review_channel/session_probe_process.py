"""Process and workspace probes for repo-owned conductor sessions."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def current_branch_for_workspace(workspace_path_text: str) -> str:
    if not workspace_path_text:
        return ""
    workspace = Path(workspace_path_text)
    if not workspace.exists():
        return ""
    try:
        result = subprocess.run(
            ["git", "-C", str(workspace), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    branch = (result.stdout or "").strip()
    return "" if branch == "HEAD" else branch


def probe_script_running(
    script_path_text: str | None,
    *,
    session_pid: int | None = None,
) -> bool | None:
    pid = session_pid if session_pid is not None else probe_script_pid(script_path_text)
    if pid is not None:
        return True
    if not script_path_text or shutil.which("pgrep") is None:
        return None
    try:
        result = subprocess.run(
            ["pgrep", "-f", script_path_text],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode == 1:
        return False
    return None


def probe_script_pid(script_path_text: str | None) -> int | None:
    if not script_path_text or shutil.which("pgrep") is None:
        return None
    try:
        result = subprocess.run(
            ["pgrep", "-fo", script_path_text],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip().splitlines()[0])
    except (IndexError, TypeError, ValueError):
        return None
