"""Stale-implementer recovery helpers for reviewer follow loops."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

from .follow_loop import STALL_ESCALATION_POLLS
from .peer_liveness import AttentionStatus, reviewer_mode_is_active

_AUTO_RECOVERY_ATTENTION_STATUSES = frozenset(
    {
        AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED.value,
    }
)


@dataclass
class ReviewerFollowRecoveryState:
    """Mutable state for bounded stale-implementer auto-recovery."""

    last_progress_token: str = ""
    unchanged_progress_polls: int = 0
    last_recovery_key: str = ""


@dataclass(frozen=True)
class ReviewerFollowRecoveryInput:
    """Immutable inputs for one stale-implementer recovery decision."""

    args: object
    repo_root: Path
    paths: dict[str, object]
    report: dict[str, object]
    progress_token: str
    recovery_state: ReviewerFollowRecoveryState


def maybe_auto_recover_stale_implementer(
    *,
    recovery_fn: Callable[..., tuple[dict[str, object], int]] | None,
    recovery_input: ReviewerFollowRecoveryInput,
) -> dict[str, object] | None:
    """Return one recovery payload when the implementer side is stale."""
    if recovery_fn is None:
        return None
    bridge_liveness = recovery_input.report.get("bridge_liveness")
    attention = recovery_input.report.get("attention")
    if not isinstance(bridge_liveness, dict) or not isinstance(attention, dict):
        _refresh_recovery_progress(
            recovery_input.recovery_state,
            recovery_input.progress_token,
        )
        return None
    if not reviewer_mode_is_active(str(bridge_liveness.get("reviewer_mode") or "")):
        _refresh_recovery_progress(
            recovery_input.recovery_state,
            recovery_input.progress_token,
        )
        return None
    if bool(recovery_input.report.get("review_needed")):
        _refresh_recovery_progress(
            recovery_input.recovery_state,
            recovery_input.progress_token,
        )
        return None

    unchanged_polls = _refresh_recovery_progress(
        recovery_input.recovery_state,
        recovery_input.progress_token,
    )
    attention_status = str(attention.get("status") or "")
    if (
        attention_status not in _AUTO_RECOVERY_ATTENTION_STATUSES
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


def _refresh_recovery_progress(
    recovery_state: ReviewerFollowRecoveryState,
    progress_token: str,
) -> int:
    token = progress_token.strip()
    if token and token != recovery_state.last_progress_token:
        recovery_state.last_progress_token = token
        recovery_state.unchanged_progress_polls = 0
        recovery_state.last_recovery_key = ""
        return 0
    recovery_state.unchanged_progress_polls += 1
    return recovery_state.unchanged_progress_polls


def _build_recover_action_args(args) -> SimpleNamespace:
    payload = vars(args).copy()
    payload.update(
        action="recover",
        follow=False,
        terminal="terminal-app",
        format="json",
        output=None,
        pipe_command=None,
        pipe_args=None,
        dry_run=False,
        recover_provider="claude",
        refresh_bridge_heartbeat_if_stale=True,
    )
    return SimpleNamespace(**payload)
