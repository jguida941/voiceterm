"""Derived runtime-truth reducer for design and startup consumers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..time_utils import utc_timestamp
from .agent_mind_projection_read import read_agent_mind_projection
from .session_posture import SessionPosture, session_posture_from_mapping
from .startup_signals import load_startup_quality_signals

RUNTIME_TRUTH_SNAPSHOT_CONTRACT_ID = "RuntimeTruthSnapshot"
RUNTIME_TRUTH_SNAPSHOT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RuntimeTruthSource:
    """One observed upstream or typed source in the runtime-truth tick."""

    source_id: str
    source_kind: str
    status: str
    summary: str = ""
    evidence_ref: str = ""
    observed_fields: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["observed_fields"] = list(self.observed_fields)
        return payload


@dataclass(frozen=True, slots=True)
class RuntimeTruthSnapshot:
    """Compact reducer over the current ReviewState-centered runtime tick."""

    schema_version: int = RUNTIME_TRUTH_SNAPSHOT_SCHEMA_VERSION
    contract_id: str = RUNTIME_TRUTH_SNAPSHOT_CONTRACT_ID
    generated_at_utc: str = ""
    source_contract: str = "ReviewState"
    source_command: str = "review-channel status"
    interaction_mode: str = "unresolved"
    reviewer_mode: str = ""
    effective_reviewer_mode: str = ""
    current_instruction: str = ""
    packet_attention_required: bool = False
    pending_packet_count: int = 0
    active_actor_count: int = 0
    live_actor_ids: tuple[str, ...] = ()
    remote_control_active: bool = False
    remote_control_method: str = ""
    remote_control_session_id: str = ""
    agent_mind_providers: tuple[str, ...] = ()
    quality_signal_keys: tuple[str, ...] = ()
    connectivity_contract_count: int = 0
    connectivity_warning_count: int = 0
    routing_decision: str = "observe_existing_runtime_truth"
    observed_sources: tuple[RuntimeTruthSource, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["live_actor_ids"] = list(self.live_actor_ids)
        payload["agent_mind_providers"] = list(self.agent_mind_providers)
        payload["quality_signal_keys"] = list(self.quality_signal_keys)
        payload["observed_sources"] = [
            source.to_dict() for source in self.observed_sources
        ]
        payload["warnings"] = list(self.warnings)
        return payload


def build_runtime_truth_snapshot(
    *,
    repo_root: Path,
    review_state: Mapping[str, object] | object | None,
    connectivity_registry: Mapping[str, object] | object | None = None,
    quality_signals: Mapping[str, object] | None = None,
    agent_mind_providers: tuple[str, ...] = ("codex", "claude"),
) -> RuntimeTruthSnapshot:
    """Build one derived runtime-truth view without creating new authority."""
    state = _mapping_from_object(review_state)
    runtime = _mapping(state.get("reviewer_runtime"))
    posture = _session_posture_payload(
        runtime.get("session_posture") or state.get("session_posture")
    )
    attachment = _mapping(
        runtime.get("remote_control_attachment") or state.get("remote_control_attachment")
    )
    inbox = _mapping(state.get("packet_inbox"))
    queue = _mapping(state.get("queue"))
    current_session = _mapping(state.get("current_session"))
    observed_quality = dict(quality_signals or load_startup_quality_signals(repo_root))
    connectivity = _mapping_from_object(connectivity_registry)

    live_actors = _live_actor_ids(posture)
    agent_minds = _agent_mind_providers(repo_root, agent_mind_providers)
    remote_active = _remote_control_active(attachment)
    observed_sources = [
        _source_row(
            "review_state",
            "typed_runtime",
            "present" if state else "missing",
            state.get("snapshot_id") if state else "",
            ("reviewer_runtime", "packet_inbox", "current_session"),
        ),
        _source_row(
            "session_posture",
            "typed_runtime",
            "present" if posture else "missing",
            posture.get("source") if posture else "",
            ("interaction_mode", "actors"),
        ),
        _source_row(
            "remote_control_attachment",
            "typed_runtime",
            "active" if remote_active else "inactive",
            attachment.get("source_proof_channel") if attachment else "",
            ("remote_session_id", "physical_confirmation_method"),
        ),
        _source_row(
            "agent_mind",
            "provider_projection",
            "present" if agent_minds else "missing",
            ",".join(agent_minds),
            ("session_id", "latest_events"),
        ),
        _source_row(
            "connectivity_registry",
            "typed_registry",
            "present" if connectivity else "missing",
            connectivity.get("contract_id") if connectivity else "",
            ("connected_contracts", "warnings"),
        ),
    ]
    return RuntimeTruthSnapshot(
        generated_at_utc=utc_timestamp(),
        source_contract=str(state.get("contract_id") or "ReviewState"),
        source_command=str(state.get("source_command") or "review-channel status"),
        interaction_mode=_resolved_interaction_mode(
            posture=posture,
            runtime=runtime,
            remote_active=remote_active,
        ),
        reviewer_mode=_text(posture.get("reviewer_mode") or runtime.get("reviewer_mode")),
        effective_reviewer_mode=_text(
            posture.get("effective_reviewer_mode")
            or runtime.get("effective_reviewer_mode")
        ),
        current_instruction=_text(current_session.get("current_instruction")),
        packet_attention_required=_packet_attention_required(inbox),
        pending_packet_count=_pending_packet_count(inbox, queue),
        active_actor_count=len(live_actors),
        live_actor_ids=live_actors,
        remote_control_active=remote_active,
        remote_control_method=_text(attachment.get("physical_confirmation_method")),
        remote_control_session_id=_text(attachment.get("remote_session_id")),
        agent_mind_providers=agent_minds,
        quality_signal_keys=tuple(sorted(str(key) for key in observed_quality)),
        connectivity_contract_count=_connectivity_count(connectivity),
        connectivity_warning_count=_warning_count(connectivity),
        observed_sources=tuple(observed_sources),
        warnings=_warnings(state, connectivity),
    )


def _mapping_from_object(value: Mapping[str, object] | object | None) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    return {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _session_posture_payload(value: object) -> dict[str, Any]:
    posture = session_posture_from_mapping(value)
    if isinstance(posture, SessionPosture):
        return dict(posture.to_dict())
    return _mapping(value)


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _text(value: object) -> str:
    return str(value or "").strip()


def _resolved_interaction_mode(
    *,
    posture: Mapping[str, object],
    runtime: Mapping[str, object],
    remote_active: bool,
) -> str:
    mode = _text(posture.get("interaction_mode"))
    if mode and mode != "unresolved":
        return mode
    if remote_active:
        return "remote_control"
    return _text(runtime.get("operator_interaction_mode")) or mode or "unresolved"


def _source_row(
    source_id: str,
    source_kind: str,
    status: str,
    evidence_ref: object,
    fields: tuple[str, ...],
) -> RuntimeTruthSource:
    return RuntimeTruthSource(
        source_id=source_id,
        source_kind=source_kind,
        status=status,
        evidence_ref=_text(evidence_ref),
        observed_fields=fields,
    )


def _live_actor_ids(posture: Mapping[str, object]) -> tuple[str, ...]:
    actors = _sequence(posture.get("actors"))
    ids: list[str] = []
    for item in actors:
        if not isinstance(item, Mapping) or not bool(item.get("live")):
            continue
        actor_id = _text(item.get("actor_id") or item.get("provider"))
        if actor_id and actor_id not in ids:
            ids.append(actor_id)
    return tuple(ids)


def _remote_control_active(attachment: Mapping[str, object]) -> bool:
    if not attachment:
        return False
    status = _text(attachment.get("status"))
    method = _text(attachment.get("physical_confirmation_method"))
    remote_session_id = _text(attachment.get("remote_session_id"))
    return status == "attached" and bool(remote_session_id) and method != "none"


def _agent_mind_providers(repo_root: Path, providers: tuple[str, ...]) -> tuple[str, ...]:
    present: list[str] = []
    for provider in providers:
        if read_agent_mind_projection(repo_root, provider=provider):
            present.append(provider)
    return tuple(present)


def _packet_attention_required(inbox: Mapping[str, object]) -> bool:
    for item in _sequence(inbox.get("agents")):
        if isinstance(item, Mapping) and _text(item.get("attention_status")) not in {
            "",
            "none",
            "idle",
        }:
            return True
    return False


def _pending_packet_count(
    inbox: Mapping[str, object],
    queue: Mapping[str, object],
) -> int:
    total = 0
    for item in _sequence(inbox.get("agents")):
        if not isinstance(item, Mapping):
            continue
        try:
            total += int(item.get("pending_actionable_total") or 0)
        except (TypeError, ValueError):
            continue
    if total:
        return total
    try:
        return int(queue.get("pending_total") or queue.get("live_total") or 0)
    except (TypeError, ValueError):
        return 0


def _connectivity_count(connectivity: Mapping[str, object]) -> int:
    rows = _sequence(connectivity.get("connected_contracts"))
    if rows:
        return len(rows)
    try:
        return int(connectivity.get("connected_contract_count") or 0)
    except (TypeError, ValueError):
        return 0


def _warning_count(connectivity: Mapping[str, object]) -> int:
    warnings = _sequence(connectivity.get("warnings"))
    if warnings:
        return len(warnings)
    try:
        return int(connectivity.get("warning_count") or 0)
    except (TypeError, ValueError):
        return 0


def _warnings(
    state: Mapping[str, object],
    connectivity: Mapping[str, object],
) -> tuple[str, ...]:
    warnings: list[str] = []
    if not state:
        warnings.append("review_state_missing")
    if _warning_count(connectivity):
        warnings.append("connectivity_registry_warnings")
    return tuple(warnings)


__all__ = [
    "RUNTIME_TRUTH_SNAPSHOT_CONTRACT_ID",
    "RUNTIME_TRUTH_SNAPSHOT_SCHEMA_VERSION",
    "RuntimeTruthSnapshot",
    "RuntimeTruthSource",
    "build_runtime_truth_snapshot",
]
