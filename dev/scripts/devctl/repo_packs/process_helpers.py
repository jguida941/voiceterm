"""Thin process-level helpers owned by devctl instead of the checks layer."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def resolve_repo(raw: str | None) -> str:
    """Return a GitHub repo slug from an explicit arg or GITHUB_REPOSITORY env."""
    value = str(raw or "").strip()
    if value:
        return value
    return str(os.getenv("GITHUB_REPOSITORY", "")).strip()


def run_capture(
    cmd: list[str], *, cwd: Path | None = None
) -> tuple[int, str, str]:
    """Run a command and capture stdout/stderr without raising on failure."""
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return completed.returncode, completed.stdout or "", completed.stderr or ""
