"""devctl graph-walk command implementation."""

from __future__ import annotations

from ..runtime.machine_output import ArtifactOutputOptions, emit_machine_artifact_output
from .builder import build_context_graph
from .graph_walk import render_graph_walk_markdown, walk_context_graph


def run(args) -> int:
    """Build the context graph and return one bounded cited walk."""
    nodes, edges = build_context_graph()
    result = walk_context_graph(
        getattr(args, "from_node", "") or "",
        getattr(args, "to_node", "") or "",
        nodes,
        edges,
        strategy=getattr(args, "strategy", "cost-ranked") or "cost-ranked",
        max_depth=max(1, int(getattr(args, "max_depth", 6) or 6)),
    )
    payload = result.to_dict()
    return emit_machine_artifact_output(
        args,
        command="graph-walk",
        json_payload=payload,
        human_output=render_graph_walk_markdown(result),
        options=ArtifactOutputOptions(
            ok=result.confidence != "no_match",
            summary={
                "confidence": result.confidence,
                "path_length": max(len(result.path) - 1, 0),
                "from": result.from_query,
                "to": result.to_query,
            },
        ),
    )


__all__ = ["run"]
