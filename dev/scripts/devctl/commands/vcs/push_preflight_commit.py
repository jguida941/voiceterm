"""Auto-commit preflight-generated changes to break the push dirty-tree loop."""

from __future__ import annotations

from pathlib import Path

from ...collect import collect_git_status
from ...config import REPO_ROOT
from ...runtime.vcs import run_git_capture
from .push_projection_receipt import managed_projection_receipt_paths
from .push_worktree_changes import blocking_dirty_paths

POST_VALIDATION_AUTO_COMMIT_REPAIR = "post_validation_auto_commit_repair"


def auto_commit_preflight_generated_changes(
    state,
    policy,
    *,
    repo_root: Path = REPO_ROOT,
) -> None:
    """Auto-commit changes the preflight generated so the push doesn't loop.

    The preflight runs check-router which may trigger render-surfaces,
    code generation passes, or test updates. Those changes dirty the
    worktree, causing the push to fail its own clean-tree check on the
    next attempt — creating an infinite commit-push-fail loop.

    This function detects preflight-generated changes and auto-commits
    them with a machine-generated message so the push can proceed.
    """
    try:
        git = collect_git_status(repo_root=repo_root)
    except (OSError, FileNotFoundError):
        return
    changes = git.get("changes", [])
    exclusions = (
        *managed_projection_receipt_paths(policy, repo_root=repo_root),
        *policy.checkpoint.advisory_context_paths,
    )
    dirty = blocking_dirty_paths(changes, exclude_paths=exclusions)
    if not dirty:
        return
    add_code, _, add_error = run_git_capture(
        ["add", "--", *dirty],
        repo_root=repo_root,
    )
    if add_code != 0:
        state.errors.append(
            _auto_commit_failure_message(
                dirty=dirty,
                step="git add",
                error=add_error,
            )
        )
        return

    commit_code, _, commit_error = run_git_capture(
        ["commit", "-m", "chore(push): auto-commit preflight-generated changes"],
        repo_root=repo_root,
    )
    if commit_code != 0:
        state.errors.append(
            _auto_commit_failure_message(
                dirty=dirty,
                step="git commit",
                error=commit_error,
            )
        )


def run_post_validation_auto_commit_repair_phase(
    state,
    policy,
    *,
    repo_root: Path,
    current_head_fn=None,
    repair_fn=None,
    validation_passed: bool,
) -> dict[str, object]:
    """Run the preflight-generated repair path only after validation passes."""
    if not validation_passed:
        result = _post_validation_phase_state(
            allowed=False,
            status="forbidden",
            reason="validation_failed",
        )
        _record_phase_state(state, result)
        return result

    head_fn = current_head_fn or _current_head_sha
    before_head = head_fn(repo_root=repo_root)
    if repair_fn is None:
        auto_commit_preflight_generated_changes(state, policy, repo_root=repo_root)
    else:
        repair_fn(
            state,
            policy,
            repo_root=repo_root,
        )
    after_head = head_fn(repo_root=repo_root)
    result = _post_validation_phase_state(
        allowed=True,
        status="blocked" if getattr(state, "errors", ()) else "completed",
        reason="validation_passed",
        head_moved=bool(before_head and after_head and before_head != after_head),
    )
    _record_phase_state(state, result)
    return result


def _post_validation_phase_state(
    *,
    allowed: bool,
    status: str,
    reason: str,
    head_moved: bool | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {}
    result["phase"] = POST_VALIDATION_AUTO_COMMIT_REPAIR
    result["allowed"] = allowed
    result["status"] = status
    result["reason"] = reason
    if head_moved is not None:
        result["head_moved"] = head_moved
    return result


def _current_head_sha(*, repo_root: Path) -> str:
    code, stdout, _ = run_git_capture(["rev-parse", "HEAD"], repo_root=repo_root)
    return stdout.strip() if code == 0 else ""


def _record_phase_state(state, result: dict[str, object]) -> None:
    try:
        setattr(state, "post_validation_auto_commit_repair", dict(result))
    except (AttributeError, TypeError):
        return


def _auto_commit_failure_message(
    *,
    dirty: list[str],
    step: str,
    error: str,
) -> str:
    paths = ", ".join(dirty[:5])
    detail = f": {error}" if error else ""
    return (
        f"Preflight generated {len(dirty)} dirty path(s) but {step} failed"
        f" for {paths}{detail}"
    )
