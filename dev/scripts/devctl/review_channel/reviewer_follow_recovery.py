"""Stale-peer recovery helpers for reviewer follow loops."""

from __future__ import annotations

from typing import Callable

from .follow_loop import STALL_ESCALATION_POLLS
from .peer_liveness import reviewer_mode_is_active
from .reviewer_follow_runtime import (
    reviewer_progress_token,
    reviewer_runtime_mapping,
    reviewer_runtime_text,
)
from .reviewer_follow_restore_policy import (
    auto_relaunch_allowed,
    restore_action_from_report,
)
from .reviewer_follow_recovery_support import (
    build_launch_action_args,
    build_recover_action_args,
    build_rollover_action_args,
    implementer_ack_current,
    recover_provider_from_report,
)
from .reviewer_follow_recovery_models import (
    AUTO_RECOVERY_ATTENTION_STATUSES,
    AUTO_RELAUNCH_ATTENTION_STATUSES,
    AUTO_RELAUNCH_LAUNCH_TRUTHS,
    AUTO_ROLLOVER_ATTENTION_STATUSES,
    ReviewerFollowRecoveryInput,
    ReviewerFollowRecoveryState,
    ReviewerFollowRolloverInput,
    ReviewerFollowRolloverState,
    refresh_stall_progress,
)

# Re-export for downstream consumers
__all__ = [
    "ReviewerFollowRecoveryInput",
    "ReviewerFollowRecoveryState",
    "ReviewerFollowRolloverInput",
    "ReviewerFollowRolloverState",
    "maybe_auto_recover_stale_implementer",
    "maybe_auto_relaunch_review_loop",
    "maybe_auto_trigger_rollover_on_stale_codex",
]


def maybe_auto_recover_stale_implementer(
    *,
    recovery_fn: Callable[..., tuple[dict[str, object], int]] | None,
    recovery_input: ReviewerFollowRecoveryInput,
) -> dict[str, object] | None:
    """Return one recovery payload when the implementer side is stale."""
    if recovery_fn is None:
        return None

    reviewer_runtime = reviewer_runtime_mapping(recovery_input.report)
    bridge_liveness = recovery_input.report.get("bridge_liveness")
    attention = recovery_input.report.get("attention")
    if not isinstance(bridge_liveness, dict) or not isinstance(attention, dict):
        refresh_stall_progress(
            recovery_input.recovery_state, recovery_input.progress_token,
            key_attr="last_recovery_key",
        )
        return None

    reviewer_mode = str(
        reviewer_runtime_text(reviewer_runtime, "effective_reviewer_mode")
        or bridge_liveness.get("effective_reviewer_mode")
        or bridge_liveness.get("reviewer_mode")
        or ""
    )
    if not reviewer_mode_is_active(reviewer_mode):
        refresh_stall_progress(
            recovery_input.recovery_state, recovery_input.progress_token,
            key_attr="last_recovery_key",
        )
        return None

    if bool(recovery_input.report.get("review_needed")):
        refresh_stall_progress(
            recovery_input.recovery_state, recovery_input.progress_token,
            key_attr="last_recovery_key",
        )
        return None

    unchanged_polls = refresh_stall_progress(
        recovery_input.recovery_state, recovery_input.progress_token,
        key_attr="last_recovery_key",
    )
    attention_status = (
        reviewer_runtime_text(reviewer_runtime, "stale_reason")
        or str(attention.get("status") or "")
    )
    recovery_action_allowed = reviewer_runtime_text(
        reviewer_runtime, "recovery_action_allowed",
    )
    if (
        attention_status not in AUTO_RECOVERY_ATTENTION_STATUSES
        or (
            recovery_action_allowed
            and "review-channel --action recover" not in recovery_action_allowed
        )
        or unchanged_polls < STALL_ESCALATION_POLLS
    ):
        return None

    current_instruction_revision = str(
        bridge_liveness.get("current_instruction_revision") or ""
    )
    recovery_key = "\0".join((
        attention_status, current_instruction_revision, recovery_input.progress_token,
    ))
    if recovery_key and recovery_key == recovery_input.recovery_state.last_recovery_key:
        return None

    recovery_args = build_recover_action_args(
        recovery_input.args,
        recover_provider=recover_provider_from_report(recovery_input.report),
    )
    recovery_report, recovery_exit_code = recovery_fn(
        args=recovery_args,
        repo_root=recovery_input.repo_root,
        paths=recovery_input.paths,
    )
    if recovery_exit_code == 0 and recovery_key:
        recovery_input.recovery_state.last_recovery_key = recovery_key

    return _build_recovery_payload(
        action="recover", attention_status=attention_status,
        exit_code=recovery_exit_code, report=recovery_report,
        unchanged_polls=unchanged_polls,
    )


def maybe_auto_relaunch_review_loop(
    *,
    bridge_action_fn: Callable[..., tuple[dict[str, object], int]] | None,
    rollover_input: ReviewerFollowRolloverInput,
) -> dict[str, object] | None:
    """Return one launch payload when review is pending but the loop is detached."""
    if bridge_action_fn is None:
        return None

    reviewer_runtime = reviewer_runtime_mapping(rollover_input.report)
    if restore_action_from_report(
        report=rollover_input.report, reviewer_runtime=reviewer_runtime,
    ) != "launch":
        return None

    bridge_liveness = rollover_input.report.get("bridge_liveness")
    attention = rollover_input.report.get("attention")
    if not isinstance(bridge_liveness, dict) or not isinstance(attention, dict):
        refresh_stall_progress(
            rollover_input.rollover_state, "", key_attr="last_restore_key",
        )
        return None

    attention_status = (
        reviewer_runtime_text(reviewer_runtime, "stale_reason")
        or str(attention.get("status") or "")
    )
    reviewer_progress = reviewer_progress_token(
        reviewer_runtime=reviewer_runtime,
        bridge_liveness=bridge_liveness,
        attention_status=attention_status,
    )
    reviewer_mode = str(
        reviewer_runtime_text(reviewer_runtime, "effective_reviewer_mode")
        or bridge_liveness.get("effective_reviewer_mode")
        or bridge_liveness.get("reviewer_mode")
        or ""
    )
    if not reviewer_mode_is_active(reviewer_mode):
        refresh_stall_progress(
            rollover_input.rollover_state, reviewer_progress,
            key_attr="last_restore_key",
        )
        return None

    unchanged_polls = refresh_stall_progress(
        rollover_input.rollover_state, reviewer_progress,
        key_attr="last_restore_key",
    )
    launch_truth = str(
        reviewer_runtime_text(reviewer_runtime, "launch_truth")
        or bridge_liveness.get("launch_truth")
        or ""
    ).strip()
    ack_current = implementer_ack_current(
        reviewer_runtime=reviewer_runtime, bridge_liveness=bridge_liveness,
    )
    if (
        attention_status not in AUTO_RELAUNCH_ATTENTION_STATUSES
        or launch_truth not in AUTO_RELAUNCH_LAUNCH_TRUTHS
        or not bool(rollover_input.report.get("review_needed"))
        or not ack_current
        or not auto_relaunch_allowed(rollover_input.report)
        or unchanged_polls < STALL_ESCALATION_POLLS
    ):
        return None

    relaunch_key = "\0".join(("launch", attention_status, reviewer_progress)).strip("\0")
    if relaunch_key and relaunch_key == rollover_input.rollover_state.last_restore_key:
        return None

    launch_args = build_launch_action_args(rollover_input.args)
    launch_report, launch_exit_code = bridge_action_fn(
        args=launch_args,
        repo_root=rollover_input.repo_root,
        paths=rollover_input.paths,
    )
    launched = launch_exit_code == 0 and bool(launch_report.get("launched"))
    if launched and relaunch_key:
        rollover_input.rollover_state.last_restore_key = relaunch_key

    payload: dict[str, object] = {
        "attempted": True,
        "launched": launched,
        "relaunch_action": "launch",
        "attention_status": attention_status,
        "launch_truth": launch_truth,
        "review_needed": True,
        "implementer_ack_current": ack_current,
        "unchanged_reviewer_polls": unchanged_polls,
        "launch_exit_code": launch_exit_code,
    }
    _append_errors(payload, launch_report)
    return payload


def maybe_auto_trigger_rollover_on_stale_codex(
    *,
    bridge_action_fn: Callable[..., tuple[dict[str, object], int]] | None,
    rollover_input: ReviewerFollowRolloverInput,
) -> dict[str, object] | None:
    """Return one rollover payload when the reviewer side stays stale."""
    if bridge_action_fn is None:
        return None

    reviewer_runtime = reviewer_runtime_mapping(rollover_input.report)
    restore_action = restore_action_from_report(
        report=rollover_input.report, reviewer_runtime=reviewer_runtime,
    )
    if restore_action and restore_action != "rollover":
        return None

    bridge_liveness = rollover_input.report.get("bridge_liveness")
    attention = rollover_input.report.get("attention")
    if not isinstance(bridge_liveness, dict) or not isinstance(attention, dict):
        refresh_stall_progress(
            rollover_input.rollover_state, "", key_attr="last_restore_key",
        )
        return None

    attention_status = (
        reviewer_runtime_text(reviewer_runtime, "stale_reason")
        or str(attention.get("status") or "")
    )
    reviewer_progress = reviewer_progress_token(
        reviewer_runtime=reviewer_runtime,
        bridge_liveness=bridge_liveness,
        attention_status=attention_status,
    )
    reviewer_mode = str(
        reviewer_runtime_text(reviewer_runtime, "effective_reviewer_mode")
        or bridge_liveness.get("effective_reviewer_mode")
        or bridge_liveness.get("reviewer_mode")
        or ""
    )
    if not reviewer_mode_is_active(reviewer_mode):
        refresh_stall_progress(
            rollover_input.rollover_state, reviewer_progress,
            key_attr="last_restore_key",
        )
        return None

    unchanged_polls = refresh_stall_progress(
        rollover_input.rollover_state, reviewer_progress,
        key_attr="last_restore_key",
    )
    if (
        attention_status not in AUTO_ROLLOVER_ATTENTION_STATUSES
        or unchanged_polls < STALL_ESCALATION_POLLS
    ):
        return None

    rollover_key = "\0".join((attention_status, reviewer_progress)).strip("\0")
    if rollover_key and rollover_key == rollover_input.rollover_state.last_restore_key:
        return None

    rollover_args = build_rollover_action_args(
        rollover_input.args, rollover_provider=rollover_input.rollover_provider,
    )
    rollover_report, rollover_exit_code = bridge_action_fn(
        args=rollover_args,
        repo_root=rollover_input.repo_root,
        paths=rollover_input.paths,
    )
    if rollover_exit_code == 0 and rollover_key:
        rollover_input.rollover_state.last_restore_key = rollover_key

    payload: dict[str, object] = {
        "attempted": True,
        "rolled_over": rollover_exit_code == 0,
        "rollover_action": "rollover",
        "attention_status": attention_status,
        "unchanged_reviewer_polls": unchanged_polls,
        "rollover_exit_code": rollover_exit_code,
        "launched": bool(rollover_report.get("launched")),
    }
    if rollover_input.rollover_provider:
        payload["rollover_provider"] = rollover_input.rollover_provider

    handoff_ack_observed = rollover_report.get("handoff_ack_observed")
    if isinstance(handoff_ack_observed, dict):
        payload["handoff_ack_observed"] = handoff_ack_observed

    handoff_bundle = rollover_report.get("handoff_bundle")
    if isinstance(handoff_bundle, dict):
        payload["handoff_bundle"] = handoff_bundle

    _append_errors(payload, rollover_report)
    return payload


# ── Shared payload helpers ───────────────────────────────────────


def _build_recovery_payload(
    *, action: str, attention_status: str,
    exit_code: int, report: dict[str, object],
    unchanged_polls: int,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "attempted": True,
        "recovered": exit_code == 0,
        "recovery_action": action,
        "attention_status": attention_status,
        "unchanged_progress_polls": unchanged_polls,
        "recovery_exit_code": exit_code,
        "launched": bool(report.get("launched")),
    }
    recover_ack_observed = report.get("recover_ack_observed")
    if isinstance(recover_ack_observed, dict):
        payload["recover_ack_observed"] = recover_ack_observed

    _append_errors(payload, report)
    return payload


def _append_errors(payload: dict[str, object], report: dict[str, object]) -> None:
    errors = report.get("errors")
    if isinstance(errors, list) and errors:
        payload["errors"] = [str(item).strip() for item in errors if str(item).strip()]
