"""Managed projection receipt commits for governed push preflight."""

from __future__ import annotations

from pathlib import Path

from ...config import REPO_ROOT
from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.review_snapshot_refresh import receipt_artifact_relpaths
from ...runtime.vcs import run_git_capture


def auto_commit_managed_projection_receipt(
    state,
    policy,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, object]:
    """Commit dirty generated projection artifacts before a governed push.

    This intentionally handles only managed receipt artifacts such as
    ``bridge.md`` and the configured ReviewSnapshot path. Real generated source
    changes stay owned by the broader preflight-generated auto-commit path.
    """
    result = _commit_projection_receipt_if_needed(policy, repo_root=repo_root)
    if result["ok"]:
        commit_sha = str(result.get("commit_sha", "") or "").strip()
        paths = tuple(str(path) for path in result.get("paths", ()) or ())
        if commit_sha and paths:
            state.warnings.append(
                "Committed managed projection receipt "
                f"{commit_sha[:12]} for {', '.join(paths)} before push."
            )
        return result
    reason = str(result.get("reason", "projection_receipt_failed"))
    detail = str(result.get("error", "") or "").strip()
    suffix = f": {detail}" if detail else ""
    state.errors.append(f"Managed projection receipt failed: {reason}{suffix}")
    return result


def _commit_projection_receipt_if_needed(
    policy,
    *,
    repo_root: Path,
) -> dict[str, object]:
    dirty_result = _dirty_paths(repo_root=repo_root)
    if not dirty_result["ok"]:
        return dirty_result

    dirty_paths = tuple(str(path) for path in dirty_result["dirty_paths"])
    if not dirty_paths:
        return {"ok": True, "reason": "no_projection_drift", "paths": ()}

    managed_paths = set(_managed_receipt_paths(policy, repo_root=repo_root))
    unmanaged = sorted(path for path in dirty_paths if path not in managed_paths)
    if unmanaged:
        return {"ok": True, "reason": "non_projection_dirty_paths_present", "paths": ()}

    staged_result = _stage_managed_projection_paths(
        dirty_paths=dirty_paths,
        managed_paths=managed_paths,
        repo_root=repo_root,
    )
    if not staged_result["ok"] or not staged_result.get("staged_paths"):
        return staged_result
    return _commit_staged_projection_receipt(
        staged_paths=tuple(str(path) for path in staged_result["staged_paths"]),
        repo_root=repo_root,
    )


def _stage_managed_projection_paths(
    *,
    dirty_paths: tuple[str, ...],
    managed_paths: set[str],
    repo_root: Path,
) -> dict[str, object]:
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

    staged_result = _staged_paths(repo_root=repo_root)
    if not staged_result["ok"]:
        return staged_result
    staged_paths = tuple(str(path) for path in staged_result["staged_paths"])
    if not staged_paths:
        return {"ok": True, "reason": "projection_receipt_unchanged", "paths": ()}

    unmanaged_staged = sorted(path for path in staged_paths if path not in managed_paths)
    if unmanaged_staged:
        return {
            "ok": False,
            "reason": "non_projection_paths_staged",
            "error": ", ".join(unmanaged_staged),
            "paths": staged_paths,
        }
    return {
        "ok": True,
        "reason": "projection_receipt_staged",
        "staged_paths": staged_paths,
    }


def _commit_staged_projection_receipt(
    *,
    staged_paths: tuple[str, ...],
    repo_root: Path,
) -> dict[str, object]:
    head_code, head_short, head_error = run_git_capture(
        ["rev-parse", "--short", "HEAD"],
        repo_root=repo_root,
    )
    if head_code != 0:
        return {"ok": False, "reason": "head_lookup_failed", "error": head_error}

    commit_code, _, commit_error = run_git_capture(
        ["commit", "-m", f"Refresh external review snapshot for {head_short}"],
        repo_root=repo_root,
        extra_env={
            "DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH": "1",
            "DEVCTL_REVIEW_SNAPSHOT_RECEIPT_COMMIT": "1",
        },
    )
    if commit_code != 0:
        return {
            "ok": False,
            "reason": "git_commit_failed",
            "error": commit_error,
            "paths": staged_paths,
        }

    commit_lookup_code, commit_sha, commit_lookup_error = run_git_capture(
        ["rev-parse", "HEAD"],
        repo_root=repo_root,
    )
    if commit_lookup_code != 0:
        return {
            "ok": False,
            "reason": "receipt_head_lookup_failed",
            "error": commit_lookup_error,
            "paths": staged_paths,
        }
    return {
        "ok": True,
        "reason": "projection_receipt_committed",
        "committed": True,
        "commit_sha": commit_sha,
        "paths": staged_paths,
    }


def managed_projection_receipt_paths(
    policy,
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[str, ...]:
    """Return the managed projection paths owned by receipt commits."""
    try:
        governance = scan_repo_governance_safely(repo_root)
    except (OSError, ValueError):
        governance = None
    configured = tuple(getattr(policy.checkpoint, "compatibility_projection_paths", ()))
    return tuple(dict.fromkeys((*receipt_artifact_relpaths(governance), *configured)))


def _managed_receipt_paths(policy, *, repo_root: Path) -> tuple[str, ...]:
    return managed_projection_receipt_paths(policy, repo_root=repo_root)


def _dirty_paths(*, repo_root: Path) -> dict[str, object]:
    paths: set[str] = set()
    for label, command in (
        ("worktree", ["diff", "--name-only"]),
        ("index", ["diff", "--cached", "--name-only"]),
        ("untracked", ["ls-files", "--others", "--exclude-standard"]),
    ):
        code, output, error = run_git_capture(command, repo_root=repo_root)
        if code != 0:
            return {
                "ok": False,
                "reason": f"{label}_dirty_lookup_failed",
                "error": error,
            }
        paths.update(line.strip() for line in output.splitlines() if line.strip())
    return {
        "ok": True,
        "reason": "dirty_paths_loaded",
        "dirty_paths": tuple(sorted(paths)),
    }


def _staged_paths(*, repo_root: Path) -> dict[str, object]:
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


__all__ = [
    "auto_commit_managed_projection_receipt",
    "managed_projection_receipt_paths",
]
