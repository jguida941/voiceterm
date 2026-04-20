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
from ..context_graph.models import GraphEdge, GraphNode
from ..context_graph.snapshot_store import load_context_graph_snapshot
from dataclasses import dataclass

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
    cached_graph = _load_cached_graph()
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


def _load_cached_graph():
    """Load the latest cached context-graph snapshot when it still matches HEAD."""
    try:
        from ..context_graph.snapshot_payload import (
            _SNAPSHOT_DIR,
            resolve_head_sha,
            snapshot_cache_is_fresh,
        )
        from ..config import get_repo_root

        repo_root = get_repo_root()
        snapshot_dir = repo_root / _SNAPSHOT_DIR
        if not snapshot_dir.is_dir():
            return None
        snapshot_files = list(snapshot_dir.glob("*.json"))
        if not snapshot_files:
            return None
        snapshot_files.sort(
            key=lambda path: path.stem.split("_", 1)[-1]
            if "_" in path.stem
            else path.stem
        )
        latest_path = snapshot_files[-1]
        head_sha = resolve_head_sha(repo_root)
        if not snapshot_cache_is_fresh(latest_path, head_sha):
            return None
        latest = load_context_graph_snapshot(latest_path)
        if latest.nodes and latest.edges:
            return (
                _coerce_cached_nodes(latest.nodes),
                _coerce_cached_edges(latest.edges),
            )
    except Exception:
        pass
    return None


def _coerce_cached_nodes(rows: list[object]) -> list[GraphNode]:
    """Rehydrate snapshot payload rows into typed graph nodes."""
    nodes: list[GraphNode] = []
    for row in rows:
        if isinstance(row, GraphNode):
            nodes.append(row)
            continue
        if not isinstance(row, Mapping):
            continue
        metadata = row.get("metadata")
        nodes.append(
            GraphNode(
                node_id=str(row.get("node_id") or ""),
                node_kind=str(row.get("node_kind") or ""),
                label=str(row.get("label") or ""),
                canonical_pointer_ref=str(row.get("canonical_pointer_ref") or ""),
                provenance_ref=str(row.get("provenance_ref") or ""),
                temperature=float(row.get("temperature") or 0.0),
                metadata=dict(metadata) if isinstance(metadata, Mapping) else {},
            )
        )
    return nodes


def _coerce_cached_edges(rows: list[object]) -> list[GraphEdge]:
    """Rehydrate snapshot payload rows into typed graph edges."""
    edges: list[GraphEdge] = []
    for row in rows:
        if isinstance(row, GraphEdge):
            edges.append(row)
            continue
        if not isinstance(row, Mapping):
            continue
        edges.append(
            GraphEdge(
                source_id=str(row.get("source_id") or ""),
                target_id=str(row.get("target_id") or ""),
                edge_kind=str(row.get("edge_kind") or ""),
            )
        )
    return edges
