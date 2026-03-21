"""devctl context-graph command implementation."""

from __future__ import annotations

from dataclasses import asdict

from ..runtime.machine_output import ArtifactOutputOptions, emit_machine_artifact_output
from .builder import build_context_graph
from .query import build_bootstrap_context, query_context_graph
from ..common_io import emit_output, pipe_output, write_output
from .render import (
    render_bootstrap_markdown,
    render_concept_dot,
    render_concept_mermaid,
    render_query_result_markdown,
)


def _run_bootstrap(args, nodes, edges) -> int:
    """Emit the slim AI bootstrap context packet."""
    ctx = build_bootstrap_context(nodes, edges)
    payload = asdict(ctx)
    return emit_machine_artifact_output(
        args,
        command="context-graph",
        json_payload=payload,
        human_output=render_bootstrap_markdown(payload),
        options=ArtifactOutputOptions(
            summary={
                "mode": "bootstrap",
                "active_plans": len(ctx.active_plans),
                "hotspots": len(ctx.hotspots),
            }
        ),
    )


def _run_query(args, nodes, edges) -> int:
    """Query the graph and emit a targeted subgraph."""
    query = getattr(args, "query", None) or ""
    result = query_context_graph(query, nodes, edges)
    payload = {
        "query": result.query,
        "matched_nodes": [asdict(n) for n in result.matched_nodes],
        "edges": [asdict(e) for e in result.edges],
        "hot_index_summary": asdict(result.hot_index_summary),
        "evidence": result.evidence,
    }
    return emit_machine_artifact_output(
        args,
        command="context-graph",
        json_payload=payload,
        human_output=render_query_result_markdown(result),
        options=ArtifactOutputOptions(
            summary={
                "matched_nodes": len(result.matched_nodes),
                "edges": len(result.edges),
                "query": result.query,
            }
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


def run(args) -> int:
    """Build the context graph and dispatch to the requested mode."""
    nodes, edges = build_context_graph()
    mode = getattr(args, "mode", "query")
    if mode == "concept-view":
        return _run_concept_view(args, nodes, edges)
    if mode == "bootstrap":
        return _run_bootstrap(args, nodes, edges)
    return _run_query(args, nodes, edges)
