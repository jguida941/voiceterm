"""Staging helpers for governed managed-projection receipts."""

from __future__ import annotations

from pathlib import Path

from ...runtime.vcs import run_git_capture


def stage_managed_projection_paths(
    *,
    dirty_paths: tuple[str, ...],
    managed_paths: set[str],
    repo_root: Path,
) -> dict[str, object]:
    before_staged_result = staged_paths(repo_root=repo_root)
    if not before_staged_result["ok"]:
        return before_staged_result
    before_staged = set(str(path) for path in before_staged_result["staged_paths"])
    add_code, _, add_error = run_git_capture(
        ["add", "--", *dirty_paths],
        repo_root=repo_root,
    )
    if add_code != 0:
        return {
            "ok": False,
            "reason": "git_add_failed",
            "error": add_error,
            "paths": dirty_paths,
        }

    staged_result = staged_paths(repo_root=repo_root)
    if not staged_result["ok"]:
        return staged_result
    after_staged = tuple(str(path) for path in staged_result["staged_paths"])
    staged_dirty_paths = tuple(path for path in after_staged if path in dirty_paths)
    if not staged_dirty_paths:
        return {"ok": True, "reason": "projection_receipt_unchanged", "paths": ()}

    unmanaged_staged = sorted(
        path
        for path in set(after_staged).difference(before_staged)
        if path not in managed_paths
    )
    if unmanaged_staged:
        return {
            "ok": False,
            "reason": "non_projection_paths_staged",
            "error": ", ".join(unmanaged_staged),
            "paths": staged_dirty_paths,
        }
    return {
        "ok": True,
        "reason": "projection_receipt_staged",
        "staged_paths": staged_dirty_paths,
    }


def staged_paths(*, repo_root: Path) -> dict[str, object]:
    code, output, error = run_git_capture(
        ["diff", "--cached", "--name-only"],
        repo_root=repo_root,
    )
    if code != 0:
        return {"ok": False, "reason": "staged_paths_lookup_failed", "error": error}
    return {
        "ok": True,
        "reason": "staged_paths_loaded",
        "staged_paths": tuple(
            line.strip() for line in output.splitlines() if line.strip()
        ),
    }


__all__ = ["stage_managed_projection_paths", "staged_paths"]
