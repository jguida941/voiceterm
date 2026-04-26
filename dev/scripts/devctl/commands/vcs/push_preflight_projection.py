"""Managed projection refresh helpers for governed push preflight."""

from __future__ import annotations

import sys
from pathlib import Path

from ...common import run_cmd
from ...config import REPO_ROOT
from ...runtime.review_snapshot_refresh import refresh_review_snapshot_file
from .push_projection_receipt import auto_commit_managed_projection_receipt


def refresh_managed_projections_before_preflight(
    state,
    policy,
    *,
    repo_root: Path = REPO_ROOT,
    command_runner=None,
) -> dict[str, object]:
    """Refresh ReviewSnapshot and commit managed projection drift before preflight."""
    warnings = refresh_review_snapshot_file(repo_root=repo_root)
    state.warnings.extend(warning for warning in warnings if warning)
    receipt_result = auto_commit_managed_projection_receipt(
        state,
        policy,
        repo_root=repo_root,
    )
    if not isinstance(receipt_result, dict):
        receipt_result = {}
    result = {
        "ok": bool(receipt_result.get("ok", True)),
        "receipt_committed": bool(receipt_result.get("committed"))
        or bool(str(receipt_result.get("commit_sha", "") or "").strip()),
        "paths": tuple(str(path) for path in receipt_result.get("paths", ()) or ()),
        "snapshot_warning_count": len([warning for warning in warnings if warning]),
    }
    if result["receipt_committed"] and not getattr(state, "errors", ()):
        _refresh_system_picture_inputs_after_projection_receipt(
            state,
            command_runner=run_cmd if command_runner is None else command_runner,
            repo_root=repo_root,
        )
    return result


def _refresh_system_picture_inputs_after_projection_receipt(
    state,
    *,
    command_runner,
    repo_root: Path,
) -> None:
    """Refresh freshness-guard inputs after a managed receipt moves HEAD."""
    refresh_steps = (
        (
            "push-refresh-startup-context",
            (
                sys.executable,
                "dev/scripts/devctl.py",
                "startup-context",
                "--format",
                "summary",
            ),
            "startup-context",
        ),
        (
            "push-refresh-context-graph",
            (
                sys.executable,
                "dev/scripts/devctl.py",
                "context-graph",
                "--mode",
                "bootstrap",
                "--format",
                "md",
            ),
            "context-graph",
        ),
    )
    for step_name, command, label in refresh_steps:
        step = command_runner(step_name, list(command), cwd=repo_root)
        if step.get("returncode", 1) != 0:
            state.errors.append(
                "Managed projection receipt moved HEAD, but "
                f"{label} refresh failed before push preflight."
            )
            return
    state.warnings.append(
        "Refreshed startup-context and context-graph after managed projection "
        "receipt before push preflight."
    )


__all__ = ["refresh_managed_projections_before_preflight"]
