"""Managed projection receipt commits for governed push preflight."""

from __future__ import annotations

from pathlib import Path

from ...config import REPO_ROOT
from ...runtime.vcs import run_git_capture
from .push_owned_commit_proof import record_push_owned_commit_proof
from .push_projection_paths import managed_projection_receipt_paths
from .push_projection_staging import stage_managed_projection_paths
from .push_projection_status import dirty_managed_projection_paths
from .push_review_snapshot_receipt_guard import (
    current_head_is_managed_review_snapshot_receipt,
)


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
    managed_paths = set(_managed_receipt_paths(policy, repo_root=repo_root))
    dirty_result = dirty_managed_projection_paths(
        managed_paths=managed_paths,
        repo_root=repo_root,
    )
    if not dirty_result["ok"]:
        return dirty_result

    dirty_paths = tuple(str(path) for path in dirty_result["dirty_paths"])
    unmanaged = tuple(str(path) for path in dirty_result.get("unmanaged_paths", ()))
    if unmanaged:
        return {"ok": True, "reason": "non_projection_dirty_paths_present", "paths": ()}
    if not dirty_paths:
        return {"ok": True, "reason": "no_projection_drift", "paths": ()}
    if current_head_is_managed_review_snapshot_receipt(repo_root=repo_root):
        return {
            "ok": True,
            "reason": "already_managed_review_snapshot_receipt",
            "paths": dirty_paths,
            "committed": False,
        }

    staged_result = stage_managed_projection_paths(
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
        [
            "commit",
            "-m",
            f"Refresh external review snapshot for {head_short}",
            "--",
            *staged_paths,
        ],
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
    proof_result = record_push_owned_commit_proof(
        repo_root=repo_root,
        commit_sha=commit_sha,
        artifact_paths=staged_paths,
    )
    if not proof_result.ok:
        result = _projection_receipt_commit_result(
            ok=False,
            reason="projection_receipt_commit_proof_failed",
            committed=True,
            commit_sha=commit_sha,
            paths=staged_paths,
        )
        result["error"] = proof_result.failure_reason
        result["proof_store"] = proof_result.proof_store
        result["proof_verified"] = proof_result.verified
        return result
    result = _projection_receipt_commit_result(
        ok=True,
        reason="projection_receipt_committed",
        committed=True,
        commit_sha=commit_sha,
        paths=staged_paths,
    )
    result["proof_store"] = proof_result.proof_store
    result["proof_verified"] = proof_result.verified
    return result


def _managed_receipt_paths(policy, *, repo_root: Path) -> tuple[str, ...]:
    return managed_projection_receipt_paths(policy, repo_root=repo_root)


def _projection_receipt_commit_result(
    *,
    ok: bool,
    reason: str,
    committed: bool,
    commit_sha: str,
    paths: tuple[str, ...],
) -> dict[str, object]:
    result: dict[str, object] = {
        "ok": ok,
        "reason": reason,
        "committed": committed,
    }
    result["commit_sha"] = commit_sha
    result["paths"] = paths
    return result


__all__ = [
    "auto_commit_managed_projection_receipt",
    "managed_projection_receipt_paths",
]
