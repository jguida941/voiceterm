"""Runtime surface refresh helpers after governed push receipt commits."""

from __future__ import annotations

import sys
from pathlib import Path

from ...repo_packs import active_path_config
from ...review_channel.handoff import (
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from ...review_channel.peer_liveness import (
    CODEX_POLL_STALE_AFTER_SECONDS,
    reviewer_mode_is_active,
)
from .push_projection_bundle_refresh import (
    refresh_review_channel_projection_bundle_after_projection_receipt as _refresh_review_channel_projection_bundle_after_projection_receipt,
)
from .push_recovery_loop_payload import (
    startup_context_step_needs_recovery,
)
from .push_recovery_loop_checkpoint import (
    defer_startup_context_checkpoint_gate,
    startup_context_step_is_checkpoint_gate,
)
from .push_recovery_loop_repair import (
    PRE_VALIDATION_RECOVERY_LOOP_REPAIR,
    mark_recovery_required_from_startup_context_step,
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
REVIEW_CHANNEL_REVIEWER_HEARTBEAT_COMMAND = (
    sys.executable,
    "dev/scripts/devctl.py",
    "review-channel",
    "--action",
    "reviewer-heartbeat",
    "--reviewer-mode",
    "active_dual_agent",
    "--reason",
    "auto-refresh-during-publication",
    "--terminal",
    "none",
    "--format",
    "json",
)


def refresh_stale_reviewer_heartbeat_before_publication(
    state,
    *,
    command_runner,
    repo_root: Path,
    next_step_label: str,
) -> dict[str, object]:
    """Run one bounded reviewer heartbeat refresh before routed push checks."""
    config = active_path_config()
    bridge_path = repo_root / config.bridge_rel
    result: dict[str, object] = {
        "step": "reviewer_heartbeat_refresh",
        "status": "skipped",
        "reason": "bridge_missing",
        "threshold_seconds": CODEX_POLL_STALE_AFTER_SECONDS,
    }
    if not bridge_path.is_file():
        return result
    try:
        bridge_text = bridge_path.read_text(encoding="utf-8")
        liveness = summarize_bridge_liveness(extract_bridge_snapshot(bridge_text))
    except (OSError, ValueError) as exc:
        result.update(status="failed", reason="bridge_liveness_unreadable")
        state.errors.append(
            "Unable to inspect reviewer heartbeat before "
            f"{next_step_label}: {exc}"
        )
        return result

    reviewer_mode = str(liveness.reviewer_mode or "").strip()
    poll_age_seconds = liveness.last_codex_poll_age_seconds
    result.update(
        reviewer_mode=reviewer_mode,
        last_codex_poll_age_seconds=poll_age_seconds,
    )
    if not reviewer_mode_is_active(reviewer_mode):
        result["reason"] = "reviewer_mode_inactive"
        return result
    if (
        poll_age_seconds is None
        or poll_age_seconds <= CODEX_POLL_STALE_AFTER_SECONDS
    ):
        result["reason"] = "reviewer_heartbeat_not_stale"
        return result

    step = command_runner(
        "push-refresh-reviewer-heartbeat",
        list(REVIEW_CHANNEL_REVIEWER_HEARTBEAT_COMMAND),
        cwd=repo_root,
    )
    result["command_step"] = step
    if step.get("returncode", 1) != 0:
        detail = str(step.get("failure_output") or step.get("error") or "").strip()
        suffix = f": {detail}" if detail else ""
        result.update(status="failed", reason="reviewer_heartbeat_refresh_failed")
        state.errors.append(
            "Reviewer heartbeat auto-refresh failed before "
            f"{next_step_label}{suffix}"
        )
        return result

    result.update(status="refreshed", reason="reviewer_heartbeat_stale")
    state.warnings.append(
        "Auto-refreshed stale reviewer heartbeat during push pre-validation "
        f"before {next_step_label}."
    )
    return result


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
            if label == "startup-context" and startup_context_step_is_checkpoint_gate(step):
                defer_startup_context_checkpoint_gate(
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
                if startup_context_step_is_checkpoint_gate(retry_step):
                    defer_startup_context_checkpoint_gate(
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


__all__ = [
    "PRE_VALIDATION_RECOVERY_LOOP_REPAIR",
    "refresh_stale_reviewer_heartbeat_before_publication",
    "refresh_runtime_surfaces_after_projection_receipt",
]
