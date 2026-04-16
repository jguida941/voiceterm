"""Context-packet helpers for event-backed review-channel projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from ..context_graph.escalation import (
    ContextEscalationPacket,
    build_context_escalation_packet,
    collect_query_terms,
)
from ..context_graph.models import GraphEdge, GraphNode
from ..context_graph.escalation_render import append_compact_context_packet_markdown
from ..context_graph.snapshot_store import (
    list_context_graph_snapshots,
    load_context_graph_snapshot,
)


def build_event_context_packet(
    packet: Mapping[str, object],
) -> ContextEscalationPacket | None:
    """Build a bounded context packet from one pending review packet.

    Uses a cached context graph snapshot when available to avoid the
    expensive full AST scan (~191K LOC) that blocks session-resume and
    other fast-path callers.
    """
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


def _load_cached_graph():
    """Load the latest cached context graph snapshot, or None to rebuild.

    Finds the most recent snapshot by filename sort (timestamps embedded
    in filenames) and loads only that one file. Does NOT use
    list_context_graph_snapshots() which deserializes all 362+ files.
    """
    try:
        from ..context_graph.snapshot_payload import _SNAPSHOT_DIR
        from ..config import get_repo_root

        snapshot_dir = get_repo_root() / _SNAPSHOT_DIR
        if not snapshot_dir.is_dir():
            return None
        snapshot_files = sorted(snapshot_dir.glob("*.json"))
        if not snapshot_files:
            return None
        latest = load_context_graph_snapshot(snapshot_files[-1])
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
