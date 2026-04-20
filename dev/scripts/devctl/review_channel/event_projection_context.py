"""Context helpers for event-backed review-channel projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from ..context_graph.escalation import (
    ContextEscalationPacket,
    build_context_escalation_packet,
    collect_query_terms,
)
from ..context_graph.escalation_render import append_compact_context_packet_markdown
from ..context_graph.cache_adapter import load_cached_context_graph

from .core import DEFAULT_BRIDGE_REL
from .handoff import extract_bridge_snapshot


@dataclass(frozen=True, slots=True)
class EventProjectionBaseState:
    repo_root: object
    projections_root: object
    session_output_root: object
    review_channel_path: object
    plan_id: str
    session_id: str
    bridge_text: str
    bridge_snapshot: object


@dataclass(frozen=True, slots=True)
class EventProjectionIdentityState:
    raw_service_identity: object
    raw_attach_auth_policy: object


def build_projection_base(
    review_state: dict[str, object],
    context,
    deps,
) -> EventProjectionBaseState:
    """Resolve the shared path/session state for one event projection refresh."""
    repo_root = context.repo_root
    projections_root = context.projections_root
    session_output_root = deps.resolve_session_output_root(projections_root)
    plan_id, session_id = deps.review_identifiers(review_state)
    bridge_text, bridge_snapshot = load_bridge_inputs(repo_root)
    return EventProjectionBaseState(
        repo_root=repo_root,
        projections_root=projections_root,
        session_output_root=session_output_root,
        review_channel_path=context.review_channel_path,
        plan_id=plan_id,
        session_id=session_id,
        bridge_text=bridge_text,
        bridge_snapshot=bridge_snapshot,
    )


def build_projection_identity(
    base: EventProjectionBaseState,
    deps,
) -> EventProjectionIdentityState:
    """Resolve service/attach-identity projections shared by compat emitters."""
    raw_service_identity = deps.build_service_identity(
        repo_root=base.repo_root,
        bridge_path=base.repo_root / DEFAULT_BRIDGE_REL,
        review_channel_path=base.review_channel_path,
        output_root=base.projections_root,
    )
    raw_attach_auth_policy = deps.build_attach_auth_policy(
        service_identity=raw_service_identity
    )
    return EventProjectionIdentityState(
        raw_service_identity=raw_service_identity,
        raw_attach_auth_policy=raw_attach_auth_policy,
    )


def load_bridge_inputs(repo_root):
    """Load the compatibility bridge text and parsed snapshot when present."""
    try:
        bridge_text = (repo_root / DEFAULT_BRIDGE_REL).read_text(encoding="utf-8")
    except OSError:
        return "", None
    return bridge_text, extract_bridge_snapshot(bridge_text)


def build_event_context_packet(
    packet: Mapping[str, object],
) -> ContextEscalationPacket | None:
    """Build a bounded context packet from one pending review packet."""
    query_terms = collect_query_terms(
        [
            packet.get("plan_id"),
            packet.get("summary"),
            packet.get("body"),
            packet.get("kind"),
        ],
        max_terms=4,
    )
    cached_graph = load_cached_context_graph()
    return build_context_escalation_packet(
        trigger="review-channel-event",
        query_terms=query_terms,
        options={"max_chars": 1200},
        graph=cached_graph,
    )


def append_event_instruction_context(
    summary: str,
    context_packet: ContextEscalationPacket | None,
) -> str:
    """Render event-backed instructions as flat markdown safe for projections."""
    return append_compact_context_packet_markdown(summary, context_packet)


def build_instruction_source(
    packet: Mapping[str, object],
    context_packet: ContextEscalationPacket | None,
) -> dict[str, object]:
    """Return queue-source metadata for the derived next instruction."""
    packet_id = str(packet.get("packet_id") or "").strip()
    summary = str(packet.get("summary") or "").strip()
    if not packet_id or not summary:
        return {}
    source: dict[str, object] = {
        "source_type": "review_packet",
        "packet_id": packet_id,
        "from_agent": packet.get("from_agent"),
        "to_agent": packet.get("to_agent"),
    }
    if context_packet is not None:
        source["context_packet"] = asdict(context_packet)
        if context_packet.guidance_refs:
            source["guidance_refs"] = list(context_packet.guidance_refs)
    return source
