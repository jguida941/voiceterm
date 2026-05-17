"""Python interpreter and repo-owned script resolution helpers."""

import sys
from collections.abc import Sequence
from pathlib import Path

from .config import REPO_ROOT


def resolve_repo_python_command(cmd: list[str], *, cwd: Path | None = None) -> list[str]:
    """Use the active interpreter for repo-owned Python scripts launched as `python3 ...`."""
    if len(cmd) < 2 or cmd[0] != "python3":
        return cmd
    script_arg = cmd[1]
    resolved = None
    if script_arg.endswith(".py"):
        resolved = resolve_repo_python_target(script_arg, cwd=cwd)
    elif script_arg == "-m":
        resolved = resolve_repo_owned_pytest_target(cmd, cwd=cwd)
    if resolved is None:
        return cmd
    return [sys.executable or "python3", *cmd[1:]]


def resolve_repo_python_target(
    raw_target: str,
    *,
    cwd: Path | None,
) -> Path | None:
    """Resolve one Python-run target when it lives under the repo root."""
    target_path = Path(raw_target).expanduser()
    if not target_path.is_absolute():
        target_path = (cwd or REPO_ROOT) / target_path
    try:
        resolved = target_path.resolve(strict=False)
        resolved.relative_to(REPO_ROOT)
    except (OSError, ValueError):
        return None
    return resolved


def resolve_repo_owned_pytest_target(
    parts: Sequence[str],
    *,
    cwd: Path | None,
) -> Path | None:
    """Return the first repo-owned pytest path target for `python3 -m pytest ...`."""
    if len(parts) < 4 or parts[1] != "-m" or parts[2] != "pytest":
        return None
    for raw_target in parts[3:]:
        if raw_target.startswith("-"):
            continue
        resolved = resolve_repo_python_target(raw_target, cwd=cwd)
        if resolved is not None:
            return resolved
    return None
