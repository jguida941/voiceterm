"""Single-step execution helpers for check-router."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

RunCommand = Callable[[str, list[str]], dict]


def execute_router_row(
    *,
    index: int,
    row: dict[str, str],
    dry_run: bool,
    json_format: bool,
    repo_root: Path,
    runner: Callable[..., dict],
) -> dict:
    step_name = f"router-{index:02d}"
    if dry_run and json_format:
        return dry_run_step_result(step_name, row, repo_root=repo_root)
    result = runner(
        step_name,
        ["bash", "-lc", row["command"]],
        cwd=repo_root,
        dry_run=dry_run,
    )
    result["source"] = row["source"]
    result["router_command"] = row["command"]
    return result


def dry_run_step_result(
    name: str,
    row: dict[str, str],
    *,
    repo_root: Path,
) -> dict[str, object]:
    return dict(
        name=name,
        cmd=["bash", "-lc", row["command"]],
        cwd=str(repo_root),
        returncode=0,
        duration_s=0.0,
        skipped=True,
        source=row["source"],
        router_command=row["command"],
        parallel_safety=row.get("parallel_safety", "parallel_safe"),
        parallel_reason=row.get("parallel_reason", ""),
    )


__all__ = ["dry_run_step_result", "execute_router_row"]
