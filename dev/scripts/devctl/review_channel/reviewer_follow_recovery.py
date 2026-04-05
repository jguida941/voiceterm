"""Stale-peer recovery helpers for reviewer follow loops."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

from .follow_loop import STALL_ESCALATION_POLLS
from .peer_liveness import AttentionStatus, reviewer_mode_is_active
from .reviewer_follow_runtime import (
    reviewer_progress_token,
    reviewer_runtime_mapping,
    reviewer_runtime_text,
)

_AUTO_RECOVERY_ATTENTION_STATUSES = frozenset(
    {
        AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED.value,
    }
)

_AUTO_ROLLOVER_ATTENTION_STATUSES = frozenset(
    {
        AttentionStatus.RUNTIME_MISSING.value,
        AttentionStatus.REVIEWER_HEARTBEAT_MISSING.value,
        AttentionStatus.REVIEWER_HEARTBEAT_STALE.value,
        AttentionStatus.REVIEWER_OVERDUE.value,
        AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value,
    }
)


@dataclass
class ReviewerFollowRecoveryState:
    """Mutable state for bounded stale-implementer auto-recovery."""

    last_progress_token: str = ""
    unchanged_progress_polls: int = 0
    last_recovery_key: str = ""


@dataclass
class ReviewerFollowRolloverState:
    """Mutable state for bounded stale-reviewer auto-rollover."""

    last_progress_token: str = ""
    unchanged_progress_polls: int = 0
    last_rollover_key: str = ""


@dataclass(frozen=True)
class ReviewerFollowRecoveryInput:
    """Immutable inputs for one stale-implementer recovery decision."""

    args: object
    repo_root: Path
    paths: dict[str, object]
    report: dict[str, object]
    progress_token: str
    recovery_state: ReviewerFollowRecoveryState


@dataclass(frozen=True)
class ReviewerFollowRolloverInput:
    """Immutable inputs for one stale-reviewer rollover decision."""

    args: object
    repo_root: Path
    paths: dict[str, object]
    report: dict[str, object]
    rollover_state: ReviewerFollowRolloverState
    rollover_provider: str = ""


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
        _refresh_stall_progress(
            recovery_input.recovery_state,
            recovery_input.progress_token,
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
        _refresh_stall_progress(
            recovery_input.recovery_state,
            recovery_input.progress_token,
            key_attr="last_recovery_key",
        )
        return None
    if bool(recovery_input.report.get("review_needed")):
        _refresh_stall_progress(
            recovery_input.recovery_state,
            recovery_input.progress_token,
            key_attr="last_recovery_key",
        )
        return None

    unchanged_polls = _refresh_stall_progress(
        recovery_input.recovery_state,
        recovery_input.progress_token,
        key_attr="last_recovery_key",
    )
    attention_status = (
        reviewer_runtime_text(reviewer_runtime, "stale_reason")
        or str(attention.get("status") or "")
    )
    recovery_action_allowed = reviewer_runtime_text(
        reviewer_runtime,
        "recovery_action_allowed",
    )
    if (
        attention_status not in _AUTO_RECOVERY_ATTENTION_STATUSES
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
    recovery_key = "\0".join(
        (
            attention_status,
            current_instruction_revision,
            recovery_input.progress_token,
        )
    )
    if recovery_key and recovery_key == recovery_input.recovery_state.last_recovery_key:
        return None

    recovery_args = _build_recover_action_args(recovery_input.args)
    recovery_report, recovery_exit_code = recovery_fn(
        args=recovery_args,
        repo_root=recovery_input.repo_root,
        paths=recovery_input.paths,
    )
    if recovery_exit_code == 0 and recovery_key:
        recovery_input.recovery_state.last_recovery_key = recovery_key

    payload: dict[str, object] = {}
    payload["attempted"] = True
    payload["recovered"] = recovery_exit_code == 0
    payload["recovery_action"] = "recover"
    payload["attention_status"] = attention_status
    payload["unchanged_progress_polls"] = unchanged_polls
    payload["recovery_exit_code"] = recovery_exit_code
    payload["launched"] = bool(recovery_report.get("launched"))
    recover_ack_observed = recovery_report.get("recover_ack_observed")
    if isinstance(recover_ack_observed, dict):
        payload["recover_ack_observed"] = recover_ack_observed
    errors = recovery_report.get("errors")
    if isinstance(errors, list) and errors:
        payload["errors"] = [str(item).strip() for item in errors if str(item).strip()]
    return payload


def maybe_auto_trigger_rollover_on_stale_codex(
    *,
    rollover_fn: Callable[..., tuple[dict[str, object], int]] | None,
    rollover_input: ReviewerFollowRolloverInput,
) -> dict[str, object] | None:
    """Return one rollover payload when the reviewer side stays stale."""
    if rollover_fn is None:
        return None
    reviewer_runtime = reviewer_runtime_mapping(rollover_input.report)
    bridge_liveness = rollover_input.report.get("bridge_liveness")
    attention = rollover_input.report.get("attention")
    if not isinstance(bridge_liveness, dict) or not isinstance(attention, dict):
        _refresh_stall_progress(
            rollover_input.rollover_state,
            "",
            key_attr="last_rollover_key",
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
        _refresh_stall_progress(
            rollover_input.rollover_state,
            reviewer_progress,
            key_attr="last_rollover_key",
        )
        return None

    unchanged_polls = _refresh_stall_progress(
        rollover_input.rollover_state,
        reviewer_progress,
        key_attr="last_rollover_key",
    )
    if (
        attention_status not in _AUTO_ROLLOVER_ATTENTION_STATUSES
        or unchanged_polls < STALL_ESCALATION_POLLS
    ):
        return None

    rollover_key = "\0".join((attention_status, reviewer_progress)).strip("\0")
    if rollover_key and rollover_key == rollover_input.rollover_state.last_rollover_key:
        return None

    rollover_args = _build_rollover_action_args(
        rollover_input.args,
        rollover_provider=rollover_input.rollover_provider,
    )
    rollover_report, rollover_exit_code = rollover_fn(
        args=rollover_args,
        repo_root=rollover_input.repo_root,
        paths=rollover_input.paths,
    )
    if rollover_exit_code == 0 and rollover_key:
        rollover_input.rollover_state.last_rollover_key = rollover_key

    payload: dict[str, object] = {}
    payload["attempted"] = True
    payload["rolled_over"] = rollover_exit_code == 0
    payload["rollover_action"] = "rollover"
    payload["attention_status"] = attention_status
    payload["unchanged_reviewer_polls"] = unchanged_polls
    payload["rollover_exit_code"] = rollover_exit_code
    payload["launched"] = bool(rollover_report.get("launched"))
    if rollover_input.rollover_provider:
        payload["rollover_provider"] = rollover_input.rollover_provider
    handoff_ack_observed = rollover_report.get("handoff_ack_observed")
    if isinstance(handoff_ack_observed, dict):
        payload["handoff_ack_observed"] = handoff_ack_observed
    handoff_bundle = rollover_report.get("handoff_bundle")
    if isinstance(handoff_bundle, dict):
        payload["handoff_bundle"] = handoff_bundle
    errors = rollover_report.get("errors")
    if isinstance(errors, list) and errors:
        payload["errors"] = [str(item).strip() for item in errors if str(item).strip()]
    return payload


def _refresh_stall_progress(
    state: ReviewerFollowRecoveryState | ReviewerFollowRolloverState,
    progress_token: str,
    *,
    key_attr: str,
) -> int:
    token = progress_token.strip()
    if token and token != state.last_progress_token:
        state.last_progress_token = token
        state.unchanged_progress_polls = 0
        setattr(state, key_attr, "")
        return 0
    state.unchanged_progress_polls += 1
    return state.unchanged_progress_polls


def _resolve_recovery_terminal(args) -> str:
    """Inherit terminal mode from the parent daemon args for remote-control support.

    When the reviewer-follow daemon runs with ``--terminal none`` (remote/headless),
    recovery and rollover actions must also use headless launch instead of
    requiring Terminal.app via osascript.

    When ``operator_interaction_mode`` is ``remote_control``, always use
    headless (``none``) so recovery never opens a local Terminal window that
    the remote operator cannot see.
    """
    interaction_mode = str(
        getattr(args, "operator_interaction_mode", "") or ""
    ).strip()
    if interaction_mode == "remote_control":
        return "none"
    parent_terminal = str(getattr(args, "terminal", "") or "").strip()
    if parent_terminal in {"terminal-app", "none"}:
        return parent_terminal
    return "terminal-app"


def _build_recover_action_args(args) -> SimpleNamespace:
    payload = vars(args).copy()
    payload.update(
        action="recover",
        follow=False,
        terminal=_resolve_recovery_terminal(args),
        format="json",
        output=None,
        pipe_command=None,
        pipe_args=None,
        dry_run=False,
        recover_provider="claude",
        refresh_bridge_heartbeat_if_stale=True,
    )
    return SimpleNamespace(**payload)


def _build_rollover_action_args(
    args,
    *,
    rollover_provider: str = "",
) -> SimpleNamespace:
    """Build rollover action args with optional same-provider handoff routing."""
    payload = vars(args).copy()
    payload.update(
        action="rollover",
        follow=False,
        terminal=_resolve_recovery_terminal(args),
        format="json",
        output=None,
        pipe_command=None,
        pipe_args=None,
        dry_run=False,
        rollover_trigger="peer-stale",
        await_ack_seconds=max(1, int(getattr(args, "await_ack_seconds", 180) or 180)),
        refresh_bridge_heartbeat_if_stale=True,
    )
    if rollover_provider:
        payload["rollover_provider"] = rollover_provider
    return SimpleNamespace(**payload)
