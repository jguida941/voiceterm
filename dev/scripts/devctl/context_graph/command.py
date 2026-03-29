"""devctl context-graph command implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..runtime.machine_output import ArtifactOutputOptions, emit_machine_artifact_output
from .builder import build_context_graph
from .query import build_bootstrap_context, query_context_graph
from .snapshot_diff import load_graph_delta
from .snapshot_diff_render import render_snapshot_delta_markdown
from .snapshot import SnapshotResolutionError
from .snapshot import ContextGraphSnapshotCapture, write_context_graph_snapshot
from ..common_io import emit_output, pipe_output, write_output
from .render import (
    render_bootstrap_markdown,
    render_concept_dot,
    render_concept_mermaid,
    render_query_result_markdown,
)


@dataclass(frozen=True, slots=True)
class ContextGraphQueryPayload:
    """Typed query payload for the machine-readable context-graph packet."""

    query: str
    confidence: str
    matched_nodes: list[dict[str, object]]
    edges: list[dict[str, object]]
    hot_index_summary: dict[str, object]
    evidence: list[str]


@dataclass(frozen=True, slots=True)
class ContextGraphDiffSummary:
    """Compact typed summary for snapshot-diff machine output."""

    mode: str
    from_commit: str
    to_commit: str
    added_nodes: int
    removed_nodes: int
    changed_nodes: int
    added_edges: int
    removed_edges: int
    trend_direction: str


def _run_bootstrap(args, nodes, edges, snapshot: dict[str, object] | None) -> int:
    """Emit the slim AI bootstrap context packet."""
    ctx = build_bootstrap_context(nodes, edges)
    payload = asdict(ctx)
    if snapshot:
        payload["snapshot"] = snapshot
    return emit_machine_artifact_output(
        args,
        command="context-graph",
        json_payload=payload,
        human_output=render_bootstrap_markdown(payload),
        options=ArtifactOutputOptions(
            summary=_with_snapshot_summary(
                {
                "mode": "bootstrap",
                "active_plans": len(ctx.active_plans),
                "hotspots": len(ctx.hotspots),
                },
                snapshot,
            )
        ),
    )


def _run_query(args, nodes, edges, snapshot: dict[str, object] | None) -> int:
    """Query the graph and emit a targeted subgraph."""
    query = getattr(args, "query", None) or ""
    result = query_context_graph(query, nodes, edges)

    payload_dict = _build_query_payload_dict(result)
    if snapshot:
        payload_dict["snapshot"] = snapshot
    summary = _with_snapshot_summary(_build_query_summary(result), snapshot)

    return emit_machine_artifact_output(
        args,
        command="context-graph",
        json_payload=payload_dict,
        human_output=_render_query_output(result, snapshot),
        options=ArtifactOutputOptions(
            summary=summary
        ),
    )


def _run_concept_view(args, nodes, edges) -> int:
    """Emit concept graph as mermaid or dot."""
    fmt = getattr(args, "format", "mermaid")
    if fmt == "dot":
        output = render_concept_dot(nodes, edges)
    else:
        output = render_concept_mermaid(nodes, edges)
    return emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
        piper=pipe_output,
    )


def _run_diff(args) -> int:
    """Load two saved graph snapshots and emit a typed delta."""
    try:
        delta = load_graph_delta(
            from_ref=getattr(args, "from_snapshot", "") or None,
            to_ref=getattr(args, "to_snapshot", "") or None,
            trend_window=max(0, int(getattr(args, "trend_window", 5) or 0)),
        )
    except SnapshotResolutionError as exc:
        return emit_machine_artifact_output(
            args,
            command="context-graph",
            json_payload={
                "schema_version": 1,
                "contract_id": "ContextGraphDeltaError",
                "ok": False,
                "error": str(exc),
                "mode": "diff",
            },
            human_output=f"# Context Graph Snapshot Delta\n\n- error: {exc}\n",
            options=ArtifactOutputOptions(
                ok=False,
                summary={"mode": "diff", "error": str(exc)},
            ),
        )

    payload = asdict(delta)
    summary = asdict(
        ContextGraphDiffSummary(
            mode="diff",
            from_commit=delta.from_snapshot.commit_hash,
            to_commit=delta.to_snapshot.commit_hash,
            added_nodes=delta.added_nodes_count,
            removed_nodes=delta.removed_nodes_count,
            changed_nodes=delta.changed_nodes_count,
            added_edges=delta.added_edges_count,
            removed_edges=delta.removed_edges_count,
            trend_direction=delta.trend.temperature_direction if delta.trend else "unknown",
        )
    )
    return emit_machine_artifact_output(
        args,
        command="context-graph",
        json_payload=payload,
        human_output=render_snapshot_delta_markdown(delta),
        options=ArtifactOutputOptions(summary=summary),
    )


def run(args) -> int:
    """Build the context graph and dispatch to the requested mode."""
    mode = getattr(args, "mode", "query")
    if mode == "diff":
        return _run_diff(args)

    nodes, edges = build_context_graph()
    snapshot = _maybe_write_snapshot(args, nodes, edges, mode)

    if mode == "concept-view":
        return _run_concept_view(args, nodes, edges)

    if mode == "bootstrap":
        return _run_bootstrap(args, nodes, edges, snapshot)

    return _run_query(args, nodes, edges, snapshot)


def _build_query_payload_dict(result) -> dict[str, object]:
    payload = ContextGraphQueryPayload(
        query=result.query,
        confidence=result.confidence,
        matched_nodes=[asdict(node) for node in result.matched_nodes],
        edges=[asdict(edge) for edge in result.edges],
        hot_index_summary=asdict(result.hot_index_summary),
        evidence=result.evidence,
    )
    return asdict(payload)


def _build_query_summary(result) -> dict[str, object]:
    return {
        "matched_nodes": len(result.matched_nodes),
        "edges": len(result.edges),
        "query": result.query,
    }


def _maybe_write_snapshot(
    args,
    nodes,
    edges,
    mode: str,
) -> dict[str, object] | None:
    if mode != "bootstrap" and not getattr(args, "save_snapshot", False):
        return None
    snapshot = write_context_graph_snapshot(
        nodes,
        edges,
        capture=ContextGraphSnapshotCapture(source_mode=mode),
    )
    return asdict(snapshot)


def _with_snapshot_summary(
    summary: dict[str, object],
    snapshot: dict[str, object] | None,
) -> dict[str, object]:
    if not snapshot:
        return summary
    merged = dict(summary)
    merged["snapshot_path"] = snapshot.get("path")
    merged["snapshot_commit"] = snapshot.get("commit_hash")
    merged["snapshot_nodes"] = snapshot.get("node_count")
    merged["snapshot_edges"] = snapshot.get("edge_count")
    return merged


def _render_query_output(result, snapshot: dict[str, object] | None) -> str:
    output = render_query_result_markdown(result)
    if not snapshot:
        return output
    lines = [
        output.rstrip(),
        "",
        "## Snapshot",
        "",
        f"- Path: `{snapshot.get('path', 'unknown')}`",
        f"- Commit: `{snapshot.get('commit_hash', 'unknown')}`",
        f"- Nodes: {snapshot.get('node_count', 0)}",
        f"- Edges: {snapshot.get('edge_count', 0)}",
    ]
    return "\n".join(lines)
