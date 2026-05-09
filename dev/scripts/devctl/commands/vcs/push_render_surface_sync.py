"""Policy-owned render-surface sync for governed push preflight."""

from __future__ import annotations

import sys
from pathlib import Path

from ...governance.surfaces import load_surface_policy
from .push_preflight_commit import (
    auto_commit_selected_preflight_generated_changes,
    preflight_blocking_dirty_paths,
)

POLICY_RENDER_SURFACE_SYNC = "policy_render_surface_sync"


def refresh_policy_owned_render_surfaces_before_preflight(
    state,
    policy,
    *,
    repo_root: Path,
    command_runner,
    quality_policy_path: str | None = None,
) -> dict[str, object]:
    """Regenerate tracked repo-pack surfaces before docs-check can fail."""
    surface_paths = _tracked_policy_owned_surface_paths(
        repo_root=repo_root,
        policy_path=quality_policy_path,
    )
    if not surface_paths:
        return render_surface_phase_state(
            status="skipped",
            reason="no_tracked_surfaces",
        )
    baseline_dirty_paths = preflight_blocking_dirty_paths(policy, repo_root=repo_root)
    command = [
        sys.executable,
        "dev/scripts/devctl.py",
        "render-surfaces",
        "--write",
        "--format",
        "json",
    ]
    if quality_policy_path:
        command.extend(["--quality-policy", quality_policy_path])
    step = command_runner(
        "push-refresh-render-surfaces",
        command,
        cwd=repo_root,
    )
    if step.get("returncode", 1) != 0:
        detail = str(step.get("failure_output") or step.get("error") or "").strip()
        suffix = f": {detail}" if detail else ""
        state.errors.append(
            f"render-surfaces refresh failed before push preflight{suffix}"
        )
        return render_surface_phase_state(status="failed", step=step)

    commit_result = auto_commit_selected_preflight_generated_changes(
        state,
        policy,
        allowed_paths=surface_paths,
        repo_root=repo_root,
        baseline_dirty_paths=baseline_dirty_paths,
    )
    committed = bool(commit_result.get("committed"))
    commit_sha = str(commit_result.get("commit_sha", "") or "")
    paths = tuple(str(path) for path in commit_result.get("paths", ()) or ())
    if committed and commit_sha and paths:
        state.warnings.append(
            "Committed policy-owned generated surface receipt "
            f"{commit_sha[:12]} for {', '.join(paths)} before push."
        )
    status = "blocked" if getattr(state, "errors", ()) else "completed"
    return render_surface_phase_state(
        status=status,
        step=step,
        committed=committed,
        commit_sha=commit_sha,
        paths=paths,
    )


def render_surface_phase_state(
    *,
    status: str,
    reason: str = "",
    step: dict[str, object] | None = None,
    committed: bool = False,
    commit_sha: str = "",
    paths: tuple[str, ...] = (),
) -> dict[str, object]:
    result: dict[str, object] = {
        "phase": POLICY_RENDER_SURFACE_SYNC,
        "status": status,
        "committed": committed,
        "commit_sha": commit_sha,
        "paths": paths,
    }
    if reason:
        result["reason"] = reason
    if step is not None:
        result["step_returncode"] = step.get("returncode")
    return result


def render_surface_pre_validation_fields(
    render_result: dict[str, object],
) -> dict[str, object]:
    return {
        "render_surface_sync": dict(render_result),
        "render_surface_receipt_committed": bool(render_result.get("committed")),
        "render_surface_receipt_commit_sha": str(
            render_result.get("commit_sha", "") or ""
        ),
        "render_surface_paths": tuple(
            str(path) for path in render_result.get("paths", ()) or ()
        ),
    }


def _tracked_policy_owned_surface_paths(
    *,
    repo_root: Path,
    policy_path: str | None,
) -> tuple[str, ...]:
    try:
        surface_policy = load_surface_policy(
            repo_root=repo_root,
            policy_path=policy_path,
        )
    except (OSError, ValueError):
        return ()
    paths = [
        str(spec.output_path or "").strip()
        for spec in surface_policy.surfaces
        if bool(getattr(spec, "tracked", False))
        and not bool(getattr(spec, "local_only", False))
    ]
    return tuple(dict.fromkeys(path for path in paths if path))


__all__ = [
    "POLICY_RENDER_SURFACE_SYNC",
    "refresh_policy_owned_render_surfaces_before_preflight",
    "render_surface_phase_state",
    "render_surface_pre_validation_fields",
]
