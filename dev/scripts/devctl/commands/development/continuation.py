"""Continuation and watcher-lease state for `/develop`."""

from __future__ import annotations

import shlex
from collections.abc import Mapping

from ...runtime.goal_progress_receipt import resolve_goal_progress_receipt
from .continuation_commands import next_required_command, watcher_report_needed
from .models import (
    DevelopmentContinuationRequiredSignal,
    DevelopmentOrchestrationSnapshot,
    DevelopmentPacketAttention,
    DevelopmentWatcherLease,
)
from .watcher import watcher_lease_status


def continuation_signal(
    *,
    packet_attention: DevelopmentPacketAttention,
    orchestration: DevelopmentOrchestrationSnapshot,
    watcher_lease: DevelopmentWatcherLease,
    packet_pressure: object | None = None,
    review_state: Mapping[str, object] | None = None,
    actor: str = "",
    current_action: str,
    fallback_commands: tuple[str, ...],
) -> DevelopmentContinuationRequiredSignal:
    """Return whether `/develop` has authority to stop."""
    reasons = _continuation_reasons(
        packet_attention=packet_attention,
        orchestration=orchestration,
        watcher_lease=watcher_lease,
        packet_pressure=packet_pressure,
    )
    next_command = next_required_command(
        packet_attention=packet_attention,
        orchestration=orchestration,
        watcher_lease=watcher_lease,
        packet_pressure=packet_pressure,
        current_action=current_action,
        fallback_commands=fallback_commands,
    )
    required = bool(reasons)
    continuation_goal = _continuation_goal(
        packet_attention=packet_attention,
        orchestration=orchestration,
    )
    goal_progress = resolve_goal_progress_receipt(
        review_state,
        actor=actor,
        continuation_goal=continuation_goal,
    )
    if goal_progress.continuation_anchor_packet_id and not _has_stop_anchor(
        review_state,
        actor=actor,
    ):
        reasons = tuple(
            dict.fromkeys(
                (
                    *reasons,
                    "continuation_anchor_active:"
                    f"{goal_progress.continuation_anchor_packet_id}",
                )
            )
        )
        required = True
        next_command = (
            "python3 dev/scripts/devctl.py develop next "
            f"--actor {shlex.quote(actor or 'codex')} --format md"
        )
    final_response_action = _required_final_response_action(
        reasons=reasons,
        orchestration=orchestration,
    )
    packet_kind = _required_packet_kind(orchestration=orchestration)
    return DevelopmentContinuationRequiredSignal(
        continuation_required=required,
        status="continue_required" if required else "closed",
        final_response_allowed=not required,
        final_response_gate_allowed=not required,
        user_continue_state="must_continue" if required else "may_stop",
        user_action=final_response_action,
        continuation_goal=continuation_goal,
        continuation_anchor_packet_id=goal_progress.continuation_anchor_packet_id,
        goal_progress_packet_id=goal_progress.latest_progress_packet_id,
        progress_percentage_toward_goal=goal_progress.progress_percentage_toward_goal,
        goal_progress_status=goal_progress.status,
        why_not_done=(
            "; ".join(reasons)
            if required
            else "Typed controller closure allows a terminal response."
        ),
        required_final_response_action=final_response_action,
        required_packet_kind=packet_kind,
        required_packet_command=_required_packet_command(
            orchestration=orchestration,
            packet_kind=packet_kind,
            next_command=next_command,
        ),
        reasons=reasons,
        next_required_command=next_command if required else "",
        stop_policy="stop_only_when_typed_controller_closed",
        summary=_continuation_summary(required=required, next_command=next_command),
    )


def _continuation_reasons(
    *,
    packet_attention: DevelopmentPacketAttention,
    orchestration: DevelopmentOrchestrationSnapshot,
    watcher_lease: DevelopmentWatcherLease,
    packet_pressure: object | None = None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if packet_attention.attention_required:
        reasons.append(f"packet_attention:{packet_attention.wake_reason or 'required'}")
    if orchestration.action_required_count:
        reasons.append(f"orchestration_action_required:{orchestration.action_required_count}")
    if orchestration.stale_projection_count:
        reasons.append(f"stale_orchestration_inputs:{orchestration.stale_projection_count}")
    if orchestration.missing_projection_count:
        reasons.append(f"missing_orchestration_inputs:{orchestration.missing_projection_count}")
    if watcher_report_needed(
        packet_attention=packet_attention,
        watcher_lease=watcher_lease,
        packet_pressure=packet_pressure,
    ):
        reasons.append(f"watcher_{watcher_lease.status}:{watcher_lease.watched_actor}")
    return tuple(reasons)


def _continuation_summary(*, required: bool, next_command: str) -> str:
    if not required:
        return "Typed controller closure allows a terminal response."
    return f"Do not stop here; run `{next_command}` next."


def _has_stop_anchor(
    review_state: Mapping[str, object] | None,
    *,
    actor: str,
) -> bool:
    if not isinstance(review_state, Mapping):
        return False
    rows = review_state.get("packets")
    if not isinstance(rows, (list, tuple)):
        return False
    actor_id = str(actor or "").strip()
    for packet in rows:
        if not isinstance(packet, Mapping):
            continue
        if str(packet.get("kind") or "").strip() != "stop_anchor":
            continue
        if str(packet.get("to_agent") or "").strip() not in {"", actor_id}:
            continue
        if str(packet.get("status") or "").strip() in {
            "applied",
            "archived",
            "dismissed",
            "expired",
        }:
            continue
        if str(packet.get("lifecycle_current_state") or "").strip() in {
            "applied",
            "archived",
            "dismissed",
            "expired",
        }:
            continue
        return True
    return False


def _required_final_response_action(
    *,
    reasons: tuple[str, ...],
    orchestration: DevelopmentOrchestrationSnapshot,
) -> str:
    if not reasons:
        return "allow_final"
    for decision in orchestration.agent_loop_decisions:
        if decision.required_action == "post_continuation_anchor":
            return "post_continuation"
        if decision.required_action in {
            "triage_pending_packet",
            "continue_to_goal",
        }:
            return "continue_to_goal"
        if decision.required_action:
            return "run_next_command"
    if any(reason.startswith("packet_attention:") for reason in reasons):
        return "continue_to_goal"
    if any(reason.startswith("watcher_") for reason in reasons):
        return "check_watcher"
    return "run_next_command"


def _continuation_goal(
    *,
    packet_attention: DevelopmentPacketAttention,
    orchestration: DevelopmentOrchestrationSnapshot,
) -> str:
    if packet_attention.latest_attention_packet_id:
        return packet_attention.latest_attention_packet_id
    for decision in orchestration.agent_loop_decisions:
        if decision.continuation_goal:
            return decision.continuation_goal
        if decision.attention_packet_id or decision.active_packet_id:
            return decision.attention_packet_id or decision.active_packet_id
    return "typed controller goal"


def _required_packet_kind(
    *,
    orchestration: DevelopmentOrchestrationSnapshot,
) -> str:
    if any(
        decision.required_action == "post_continuation_anchor"
        for decision in orchestration.agent_loop_decisions
    ):
        return "continuation_anchor"
    return ""


def _required_packet_command(
    *,
    orchestration: DevelopmentOrchestrationSnapshot,
    packet_kind: str,
    next_command: str,
) -> str:
    if packet_kind != "continuation_anchor":
        return ""
    for decision in orchestration.agent_loop_decisions:
        if decision.required_action != "post_continuation_anchor":
            continue
        actor = decision.actor_id or "agent"
        role = decision.actor_role or ""
        session_id = decision.session_id or ""
        summary = (
            f"CONTINUATION_ANCHOR: {actor}"
            + (f" {role}" if role else "")
            + (f" session {session_id}" if session_id else "")
            + " must continue before final response"
        )
        body = (
            "Typed continuation required before final response. "
            f"Run next command: {next_command}"
        )
        command = [
            "python3",
            "dev/scripts/devctl.py",
            "review-channel",
            "--action",
            "post",
            "--from-agent",
            actor,
            "--to-agent",
            actor,
            "--kind",
            packet_kind,
            "--summary",
            summary,
            "--body",
            body,
            "--requested-action",
            "review_only",
            "--policy-hint",
            "review_only",
            "--terminal",
            "none",
            "--format",
            "md",
        ]
        if role:
            command.extend(["--target-role", role])
        if session_id:
            command.extend(["--target-session-id", session_id])
        return shlex.join(command)
    return ""


__all__ = ["continuation_signal", "watcher_lease_status"]
