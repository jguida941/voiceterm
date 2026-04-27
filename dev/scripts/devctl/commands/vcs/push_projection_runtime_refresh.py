"""Runtime surface refresh helpers after governed push receipt commits."""

from __future__ import annotations

import sys
from pathlib import Path

from ...repo_packs import active_path_config
from ...review_channel.event_reducer import load_or_refresh_event_bundle
from ...review_channel.event_store import resolve_artifact_paths
from ...review_channel.state import refresh_status_snapshot
from .push_recovery_loop_repair import (
    PRE_VALIDATION_RECOVERY_LOOP_REPAIR,
    mark_recovery_required_from_startup_context_step,
    startup_context_step_needs_recovery,
)


STARTUP_CONTEXT_REFRESH_COMMAND = (
    sys.executable,
    "dev/scripts/devctl.py",
    "startup-context",
    "--format",
    "summary",
)
REVIEW_CHANNEL_ENSURE_FOLLOW_COMMAND = (
    sys.executable,
    "dev/scripts/devctl.py",
    "review-channel",
    "--action",
    "ensure",
    "--follow",
    "--terminal",
    "none",
    "--format",
    "json",
    "--max-follow-snapshots",
    "1",
    "--follow-interval-seconds",
    "1",
    "--follow-inactivity-timeout-seconds",
    "1",
)


def refresh_runtime_surfaces_after_projection_receipt(
    state,
    *,
    command_runner,
    repo_root: Path,
    next_step_label: str,
    repo_pack_id: str = "",
) -> None:
    """Refresh freshness-guard inputs after a managed receipt moves HEAD."""
    if not _refresh_review_channel_projection_bundle_after_projection_receipt(
        state,
        repo_root=repo_root,
        next_step_label=next_step_label,
    ):
        return
    refresh_steps = (
        (
            "push-refresh-startup-context",
            STARTUP_CONTEXT_REFRESH_COMMAND,
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
            if label == "startup-context" and startup_context_step_needs_recovery(step):
                _defer_startup_context_recovery(
                    state,
                    step,
                    next_step_label=next_step_label,
                )
                continue
            if label == "startup-context":
                retry_step = _retry_startup_context_refresh_after_reviewer_follow(
                    state,
                    command_runner=command_runner,
                    repo_root=repo_root,
                    next_step_label=next_step_label,
                )
                if retry_step is None:
                    return
                if retry_step.get("returncode", 1) == 0:
                    continue
                if startup_context_step_needs_recovery(retry_step):
                    _defer_startup_context_recovery(
                        state,
                        retry_step,
                        next_step_label=next_step_label,
                        after_reviewer_follow=True,
                    )
                    continue
                step = retry_step
            state.errors.append(
                "Managed projection receipt moved HEAD, but "
                f"{label} refresh failed before {next_step_label}."
            )
            return
    state.warnings.append(
        "Refreshed startup-context and context-graph after managed projection "
        f"receipt before {next_step_label}."
    )


def _defer_startup_context_recovery(
    state,
    step,
    *,
    next_step_label: str,
    after_reviewer_follow: bool = False,
) -> None:
    recovery_record = mark_recovery_required_from_startup_context_step(state, step)
    sync = getattr(state, "pre_validation_managed_projection_sync", {})
    if isinstance(sync, dict):
        sync["startup_context_recovery_required"] = True
        sync["startup_context_recovery"] = recovery_record
        state.pre_validation_managed_projection_sync = sync
    recovery_source = " after reviewer follow" if after_reviewer_follow else ""
    state.warnings.append(
        "Managed projection receipt moved HEAD and startup-context reported "
        f"bounded recovery{recovery_source}; deferring to "
        f"{PRE_VALIDATION_RECOVERY_LOOP_REPAIR} before {next_step_label}."
    )


def _retry_startup_context_refresh_after_reviewer_follow(
    state,
    *,
    command_runner,
    repo_root: Path,
    next_step_label: str,
) -> dict[str, object] | None:
    ensure_step = command_runner(
        "push-refresh-review-channel-ensure-follow",
        list(REVIEW_CHANNEL_ENSURE_FOLLOW_COMMAND),
        cwd=repo_root,
    )
    if ensure_step.get("returncode", 1) != 0:
        detail = str(
            ensure_step.get("failure_output") or ensure_step.get("error") or ""
        ).strip()
        suffix = f": {detail}" if detail else ""
        state.errors.append(
            "Managed projection receipt moved HEAD, but review-channel "
            f"ensure --follow failed before {next_step_label}{suffix}"
        )
        return None
    state.warnings.append(
        "Startup-context refresh failed after managed projection receipt; ran "
        f"review-channel ensure --follow and retried once before {next_step_label}."
    )
    return command_runner(
        "push-refresh-startup-context-retry",
        list(STARTUP_CONTEXT_REFRESH_COMMAND),
        cwd=repo_root,
    )


def _refresh_review_channel_projection_bundle_after_projection_receipt(
    state,
    *,
    repo_root: Path,
    next_step_label: str,
) -> bool:
    """Keep review-state sibling projections on the same proof tick as HEAD."""
    config = active_path_config()
    review_channel_path = repo_root / config.review_channel_rel
    if not review_channel_path.is_file():
        return True
    try:
        artifact_paths = resolve_artifact_paths(repo_root=repo_root)
        event_log_path = Path(artifact_paths.event_log_path)
        state_path = Path(artifact_paths.state_path)
        if event_log_path.exists() or state_path.exists():
            load_or_refresh_event_bundle(
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )
            state.warnings.append(
                "Refreshed review-channel projections after managed projection "
                f"receipt before {next_step_label}."
            )
            return True
        bridge_path = repo_root / config.bridge_rel
        if bridge_path.is_file():
            refresh_status_snapshot(
                repo_root=repo_root,
                bridge_path=bridge_path,
                review_channel_path=review_channel_path,
                output_root=repo_root / config.review_status_dir_rel,
            )
            state.warnings.append(
                "Refreshed bridge-backed review projections after managed "
                f"projection receipt before {next_step_label}."
            )
    except (OSError, ValueError) as exc:
        state.errors.append(
            "Managed projection receipt moved HEAD, but review-channel "
            f"projection refresh failed before {next_step_label}: {exc}"
        )
        return False
    return True


__all__ = [
    "PRE_VALIDATION_RECOVERY_LOOP_REPAIR",
    "refresh_runtime_surfaces_after_projection_receipt",
]
