"""Builders for typed relaunch-loop events and triggers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from .relaunch_loop_models import (
    DEFAULT_RELAUNCH_WINDOW_SECONDS,
    AgentRelaunchTrigger,
    AuthorityScope,
    RelaunchQuotaExceeded,
    RelaunchQuotaToken,
    RelaunchTriggerInput,
    SliceClosureEvent,
    SliceClosureInput,
    SliceTarget,
    TypedLaunchCommand,
    normalize_relaunch_actor,
)


def build_slice_closure_event(inputs: SliceClosureInput) -> SliceClosureEvent:
    """Build a stable SliceClosureEvent from bounded CLI/runtime inputs."""
    if not isinstance(inputs, SliceClosureInput):
        raise TypeError("build_slice_closure_event requires SliceClosureInput")
    emitted = inputs.emitted_at_utc or utc_now()
    target = SliceTarget(
        slice_id=inputs.next_slice_id,
        owner_actor=normalize_relaunch_actor(inputs.next_owner_actor),
        intent=inputs.next_intent,
        evidence_packet_ids=tuple(
            packet_id.strip()
            for packet_id in inputs.evidence_packet_ids
            if packet_id.strip()
        ),
    )
    emitter = normalize_relaunch_actor(inputs.emitter_actor)
    seed = (
        ("emitted_at_utc", emitted),
        ("emitter_actor", emitter),
        ("plan_ref", inputs.plan_ref),
        ("closed_slice_id", inputs.closed_slice_id),
        ("next_slice_target", target),
        ("push_decision_state", inputs.push_decision_state),
        ("commit_sha", inputs.commit_sha),
        ("source_packet_id", inputs.source_packet_id),
    )
    return SliceClosureEvent(
        slice_closure_event_id="slice_close_"
        + _stable_digest(seed, length=16),
        emitted_at_utc=emitted,
        emitter_actor=emitter,
        commit_sha=inputs.commit_sha,
        plan_ref=inputs.plan_ref,
        closed_slice_id=inputs.closed_slice_id,
        next_slice_target=target,
        push_decision_state=inputs.push_decision_state or "no_push_needed",
        trace_offset=inputs.trace_offset,
        source_packet_id=inputs.source_packet_id,
    )


def build_relaunch_trigger(
    inputs: RelaunchTriggerInput,
) -> tuple[AgentRelaunchTrigger | None, RelaunchQuotaExceeded | None, str]:
    """Convert one closure event into a queue trigger or fail-closed receipt."""
    if not isinstance(inputs, RelaunchTriggerInput):
        raise TypeError("build_relaunch_trigger requires RelaunchTriggerInput")
    event = inputs.event
    target_actor = event.next_slice_target.owner_actor
    if not target_actor or target_actor == event.emitter_actor:
        return None, None, "same_actor_next_slice"
    if _has_existing_trigger(inputs.existing_triggers, event, target_actor):
        return None, None, "duplicate_trigger"

    queued_at = inputs.queued_at_utc or utc_now()
    window_start = _window_start(queued_at, window_seconds=inputs.window_seconds)
    actor_count, shared_count = _quota_counts(
        inputs.existing_triggers,
        target_actor=target_actor,
        window_start=window_start,
        window_seconds=inputs.window_seconds,
    )
    quota_token = RelaunchQuotaToken(
        window_start_utc=window_start,
        window_seconds=inputs.window_seconds,
        actor_count=actor_count + 1,
        actor_threshold=inputs.actor_threshold,
        shared_count=shared_count + 1,
        shared_threshold=inputs.shared_threshold,
    )
    if (
        quota_token.actor_count > inputs.actor_threshold
        or quota_token.shared_count > inputs.shared_threshold
    ):
        offending = tuple(row.parent_closure_id for row in inputs.existing_triggers)
        return (
            None,
            RelaunchQuotaExceeded(
                window_start_utc=quota_token.window_start_utc,
                window_seconds=quota_token.window_seconds,
                actor_count=quota_token.actor_count,
                actor_threshold=inputs.actor_threshold,
                shared_count=quota_token.shared_count,
                shared_threshold=inputs.shared_threshold,
                offending_slice_ids=offending + (event.slice_closure_event_id,),
                suspended_actor=target_actor,
            ),
            "quota_exceeded",
        )

    seed_packet_id = (
        event.next_slice_target.evidence_packet_ids[0]
        if event.next_slice_target.evidence_packet_ids
        else event.source_packet_id
    )
    trigger_seed = (
        ("parent_closure_id", event.slice_closure_event_id),
        ("target_actor", target_actor),
        ("seed_packet_id", seed_packet_id),
    )
    trigger_id = "relaunch_trig_" + _stable_digest(trigger_seed, length=16)
    role = _role_for_actor(target_actor)
    launch = TypedLaunchCommand(
        action="launch",
        role=role,
        target_session_id_template=f"{target_actor}:{trigger_id}",
        bootstrap_seed_packet_id=seed_packet_id,
        terminal_mode="none",
        command_preview=(
            "python3 dev/scripts/devctl.py review-channel --action launch "
            f"--role {role} --terminal none --format md"
        ),
    )
    return (
        AgentRelaunchTrigger(
            trigger_id=trigger_id,
            parent_closure_id=event.slice_closure_event_id,
            target_actor=target_actor,
            launch_command=launch,
            session_seed_packet_id=seed_packet_id,
            authority_scope=AuthorityScope(
                expires_at_utc=_expires_at(queued_at, minutes=30),
                capabilities=("session.launch", "typed_state.read"),
            ),
            expected_instruction_revision=inputs.expected_instruction_revision,
            quota_token=quota_token,
            queued_at_utc=queued_at,
        ),
        None,
        "queued",
    )


def utc_now() -> str:
    """Return current UTC timestamp in whole-second Z form."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _has_existing_trigger(
    triggers: tuple[AgentRelaunchTrigger, ...] | list[AgentRelaunchTrigger],
    event: SliceClosureEvent,
    target_actor: str,
) -> bool:
    return any(
        row.parent_closure_id == event.slice_closure_event_id
        and row.target_actor == target_actor
        for row in triggers
    )


def _quota_counts(
    triggers: tuple[AgentRelaunchTrigger, ...] | list[AgentRelaunchTrigger],
    *,
    target_actor: str,
    window_start: str,
    window_seconds: int,
) -> tuple[int, int]:
    start = _parse_utc(window_start)
    end = start + timedelta(seconds=window_seconds)
    actor_count = 0
    shared_count = 0
    for row in triggers:
        queued = _parse_utc(row.queued_at_utc)
        if queued < start or queued >= end:
            continue
        shared_count += 1
        if row.target_actor == target_actor:
            actor_count += 1
    return actor_count, shared_count


def _window_start(
    value: str,
    *,
    window_seconds: int = DEFAULT_RELAUNCH_WINDOW_SECONDS,
) -> str:
    observed = _parse_utc(value)
    epoch_seconds = int(observed.timestamp())
    window_epoch = epoch_seconds - (epoch_seconds % window_seconds)
    return (
        datetime.fromtimestamp(window_epoch, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _expires_at(value: str, *, minutes: int) -> str:
    return (
        (_parse_utc(value) + timedelta(minutes=minutes))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _parse_utc(value: str) -> datetime:
    text = value.strip()
    if not text:
        return datetime.now(timezone.utc).replace(microsecond=0)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.now(timezone.utc).replace(microsecond=0)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _role_for_actor(actor: str) -> str:
    if actor == "codex_reviewer":
        return "reviewer"
    if actor == "claude_implementer":
        return "implementer"
    return actor.rsplit("_", 1)[-1] or "agent"


def _stable_digest(items: tuple[tuple[str, object], ...], *, length: int) -> str:
    payload = [(key, _jsonable(value)) for key, value in items]
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def _jsonable(value: object) -> object:
    if isinstance(value, SliceTarget):
        return {
            "slice_id": value.slice_id,
            "owner_actor": value.owner_actor,
            "intent": value.intent,
            "evidence_packet_ids": list(value.evidence_packet_ids),
        }
    return value


__all__ = [
    "build_relaunch_trigger",
    "build_slice_closure_event",
    "utc_now",
]
