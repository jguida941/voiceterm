"""Typed relaunch-loop data contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .value_coercion import coerce_int, coerce_text

SLICE_CLOSURE_CONTRACT_ID = "SliceClosureEvent"
AGENT_RELAUNCH_TRIGGER_CONTRACT_ID = "AgentRelaunchTrigger"
RELAUNCH_QUEUED_RECEIPT_CONTRACT_ID = "RelaunchQueuedReceipt"
RELAUNCH_QUOTA_EXCEEDED_CONTRACT_ID = "RelaunchQuotaExceeded"
RELAUNCH_DISPATCH_RECEIPT_CONTRACT_ID = "RelaunchDispatchReceipt"
RELAUNCH_LOOP_SCHEMA_VERSION = 1

DEFAULT_RELAUNCH_TRACE_REL = Path("dev/state/relaunch_loop/trace.ndjson")
DEFAULT_RELAUNCH_QUEUE_REL = Path("dev/state/relaunch_loop/queue.jsonl")
DEFAULT_RELAUNCH_RECEIPTS_REL = Path("dev/state/relaunch_loop/receipts.jsonl")
DEFAULT_RELAUNCH_WINDOW_SECONDS = 600
DEFAULT_RELAUNCH_ACTOR_THRESHOLD = 6
DEFAULT_RELAUNCH_SHARED_THRESHOLD = 10


@dataclass(frozen=True, slots=True)
class SliceTarget:
    """Next bounded slice expected after a closure event."""

    slice_id: str
    owner_actor: str
    intent: str
    evidence_packet_ids: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> SliceTarget:
        target = cls(
            slice_id=coerce_text(value.get("slice_id")),
            owner_actor=normalize_relaunch_actor(value.get("owner_actor")),
            intent=coerce_text(value.get("intent")),
            evidence_packet_ids=text_tuple(value.get("evidence_packet_ids")),
        )
        return target


@dataclass(frozen=True, slots=True)
class AuthorityScope:
    """Bounded launch authority carried by a relaunch trigger."""

    expires_at_utc: str
    capabilities: tuple[str, ...] = ()
    source: str = "typed_slice_closure"

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> AuthorityScope:
        scope = cls(
            expires_at_utc=coerce_text(value.get("expires_at_utc")),
            capabilities=text_tuple(value.get("capabilities")),
            source=coerce_text(value.get("source")) or "typed_slice_closure",
        )
        return scope


@dataclass(frozen=True, slots=True)
class TypedLaunchCommand:
    """Provider-neutral launch request selected by the dispatcher."""

    action: str
    role: str
    target_session_id_template: str
    bootstrap_seed_packet_id: str
    terminal_mode: str = "none"
    command_preview: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> TypedLaunchCommand:
        command = cls(
            action=coerce_text(value.get("action")) or "launch",
            role=coerce_text(value.get("role")),
            target_session_id_template=coerce_text(
                value.get("target_session_id_template")
            ),
            bootstrap_seed_packet_id=coerce_text(value.get("bootstrap_seed_packet_id")),
            terminal_mode=coerce_text(value.get("terminal_mode")) or "none",
            command_preview=coerce_text(value.get("command_preview")),
        )
        return command


@dataclass(frozen=True, slots=True)
class RelaunchQuotaToken:
    """Quota window attached to a trigger before dispatch."""

    window_start_utc: str
    window_seconds: int = DEFAULT_RELAUNCH_WINDOW_SECONDS
    actor_count: int = 0
    actor_threshold: int = DEFAULT_RELAUNCH_ACTOR_THRESHOLD
    shared_count: int = 0
    shared_threshold: int = DEFAULT_RELAUNCH_SHARED_THRESHOLD

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> RelaunchQuotaToken:
        token = cls(
            window_start_utc=coerce_text(value.get("window_start_utc")),
            window_seconds=coerce_int(value.get("window_seconds"))
            or DEFAULT_RELAUNCH_WINDOW_SECONDS,
            actor_count=coerce_int(value.get("actor_count")),
            actor_threshold=coerce_int(value.get("actor_threshold"))
            or DEFAULT_RELAUNCH_ACTOR_THRESHOLD,
            shared_count=coerce_int(value.get("shared_count")),
            shared_threshold=coerce_int(value.get("shared_threshold"))
            or DEFAULT_RELAUNCH_SHARED_THRESHOLD,
        )
        return token


@dataclass(frozen=True, slots=True)
class SliceClosureEvent:
    """Typed event emitted when an agent closes one bounded slice."""

    slice_closure_event_id: str
    emitted_at_utc: str
    emitter_actor: str
    plan_ref: str
    closed_slice_id: str
    next_slice_target: SliceTarget
    push_decision_state: str
    commit_sha: str = ""
    trace_offset: int = 0
    source_packet_id: str = ""
    contract_id: str = SLICE_CLOSURE_CONTRACT_ID
    schema_version: int = RELAUNCH_LOOP_SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> SliceClosureEvent | None:
        if coerce_text(value.get("contract_id")) != SLICE_CLOSURE_CONTRACT_ID:
            return None
        target = value.get("next_slice_target")
        if not isinstance(target, Mapping):
            return None
        return cls(
            slice_closure_event_id=coerce_text(
                value.get("slice_closure_event_id")
            ),
            emitted_at_utc=coerce_text(value.get("emitted_at_utc")),
            emitter_actor=normalize_relaunch_actor(value.get("emitter_actor")),
            commit_sha=coerce_text(value.get("commit_sha")),
            plan_ref=coerce_text(value.get("plan_ref")),
            closed_slice_id=coerce_text(value.get("closed_slice_id")),
            next_slice_target=SliceTarget.from_mapping(target),
            push_decision_state=coerce_text(value.get("push_decision_state"))
            or "no_push_needed",
            trace_offset=coerce_int(value.get("trace_offset")),
            source_packet_id=coerce_text(value.get("source_packet_id")),
            schema_version=coerce_int(value.get("schema_version"))
            or RELAUNCH_LOOP_SCHEMA_VERSION,
        )


@dataclass(frozen=True, slots=True)
class AgentRelaunchTrigger:
    """Queue row consumed by the relaunch dispatcher."""

    trigger_id: str
    parent_closure_id: str
    target_actor: str
    launch_command: TypedLaunchCommand
    session_seed_packet_id: str
    authority_scope: AuthorityScope
    expected_instruction_revision: str
    quota_token: RelaunchQuotaToken
    queued_at_utc: str
    status: str = "pending"
    contract_id: str = AGENT_RELAUNCH_TRIGGER_CONTRACT_ID
    schema_version: int = RELAUNCH_LOOP_SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> AgentRelaunchTrigger | None:
        if coerce_text(value.get("contract_id")) != AGENT_RELAUNCH_TRIGGER_CONTRACT_ID:
            return None
        launch = value.get("launch_command")
        authority = value.get("authority_scope")
        quota = value.get("quota_token")
        if not (
            isinstance(launch, Mapping)
            and isinstance(authority, Mapping)
            and isinstance(quota, Mapping)
        ):
            return None
        return cls(
            trigger_id=coerce_text(value.get("trigger_id")),
            parent_closure_id=coerce_text(value.get("parent_closure_id")),
            target_actor=normalize_relaunch_actor(value.get("target_actor")),
            launch_command=TypedLaunchCommand.from_mapping(launch),
            session_seed_packet_id=coerce_text(value.get("session_seed_packet_id")),
            authority_scope=AuthorityScope.from_mapping(authority),
            expected_instruction_revision=coerce_text(
                value.get("expected_instruction_revision")
            ),
            quota_token=RelaunchQuotaToken.from_mapping(quota),
            queued_at_utc=coerce_text(value.get("queued_at_utc")),
            status=coerce_text(value.get("status")) or "pending",
            schema_version=coerce_int(value.get("schema_version"))
            or RELAUNCH_LOOP_SCHEMA_VERSION,
        )


@dataclass(frozen=True, slots=True)
class RelaunchQuotaExceeded:
    """Fail-closed receipt for runaway relaunch loops."""

    window_start_utc: str
    window_seconds: int
    actor_count: int
    actor_threshold: int
    shared_count: int
    shared_threshold: int
    offending_slice_ids: tuple[str, ...]
    suspended_actor: str
    operator_unblock_required: bool = True
    contract_id: str = RELAUNCH_QUOTA_EXCEEDED_CONTRACT_ID
    schema_version: int = RELAUNCH_LOOP_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class SliceClosureInput:
    """Bounded inputs for building a SliceClosureEvent."""

    emitter_actor: object
    plan_ref: str
    closed_slice_id: str
    next_slice_id: str
    next_owner_actor: object
    next_intent: str
    evidence_packet_ids: Sequence[str] = ()
    push_decision_state: str = "no_push_needed"
    commit_sha: str = ""
    source_packet_id: str = ""
    emitted_at_utc: str = ""
    trace_offset: int = 0


@dataclass(frozen=True, slots=True)
class RelaunchTriggerInput:
    """Bounded inputs for turning a closure event into a relaunch trigger."""

    event: SliceClosureEvent
    queued_at_utc: str = ""
    expected_instruction_revision: str = ""
    existing_triggers: Sequence[AgentRelaunchTrigger] = ()
    actor_threshold: int = DEFAULT_RELAUNCH_ACTOR_THRESHOLD
    shared_threshold: int = DEFAULT_RELAUNCH_SHARED_THRESHOLD
    window_seconds: int = DEFAULT_RELAUNCH_WINDOW_SECONDS


def normalize_relaunch_actor(value: object) -> str:
    """Return canonical relaunch-loop actor ids."""
    text = coerce_text(value).lower().replace("-", "_").replace(":", "_")
    if text in {"codex", "reviewer", "codex_reviewer"}:
        return "codex_reviewer"
    if text in {"claude", "implementer", "coder", "claude_implementer"}:
        return "claude_implementer"
    return text


def text_tuple(value: object) -> tuple[str, ...]:
    """Return non-empty text values from strings or iterable values."""
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if not isinstance(value, Sequence):
        return ()
    return tuple(coerce_text(item) for item in value if coerce_text(item))


__all__ = [
    "AGENT_RELAUNCH_TRIGGER_CONTRACT_ID",
    "DEFAULT_RELAUNCH_ACTOR_THRESHOLD",
    "DEFAULT_RELAUNCH_QUEUE_REL",
    "DEFAULT_RELAUNCH_RECEIPTS_REL",
    "DEFAULT_RELAUNCH_SHARED_THRESHOLD",
    "DEFAULT_RELAUNCH_TRACE_REL",
    "DEFAULT_RELAUNCH_WINDOW_SECONDS",
    "RELAUNCH_DISPATCH_RECEIPT_CONTRACT_ID",
    "RELAUNCH_LOOP_SCHEMA_VERSION",
    "RELAUNCH_QUOTA_EXCEEDED_CONTRACT_ID",
    "RELAUNCH_QUEUED_RECEIPT_CONTRACT_ID",
    "SLICE_CLOSURE_CONTRACT_ID",
    "AgentRelaunchTrigger",
    "AuthorityScope",
    "RelaunchQuotaExceeded",
    "RelaunchQuotaToken",
    "RelaunchTriggerInput",
    "SliceClosureEvent",
    "SliceClosureInput",
    "SliceTarget",
    "TypedLaunchCommand",
    "normalize_relaunch_actor",
    "text_tuple",
]
