"""Read-only command that ranks accumulated findings from LIVE_RUN.md."""

from __future__ import annotations

import json
from pathlib import Path

from ...common import emit_output, pipe_output, write_output
from ...config import REPO_ROOT
from ...context_graph.builder import build_context_graph
from ...triage.findings_priority import (
    DEFAULT_FINDINGS_LOG_PATH,
    build_priority_payload,
    load_accumulated_findings,
    rank_accumulated_findings,
    render_priority_markdown,
    render_priority_text,
)


def run(args) -> int:
    """Rank accumulated findings by triage severity plus graph fan-out."""
    source_path = _resolve_source_path(getattr(args, "findings_file", None))
    findings = load_accumulated_findings(source_path)
    graph_nodes, graph_edges = build_context_graph()
    ranked = rank_accumulated_findings(
        findings,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        include_resolved=bool(getattr(args, "include_resolved", False)),
        top_n=max(0, int(getattr(args, "top_n", 20))),
    )
    payload = build_priority_payload(
        source_path=source_path,
        findings=findings,
        ranked=ranked,
        include_resolved=bool(getattr(args, "include_resolved", False)),
    )
    if args.format == "json":
        output = json.dumps(payload, indent=2)
    elif args.format == "md":
        output = render_priority_markdown(payload)
    else:
        output = render_priority_text(payload)
    return emit_output(
        output,
        output_path=args.output,
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
        piper=pipe_output,
    )


def _resolve_source_path(raw_path: str | None) -> Path:
    relative = str(raw_path or DEFAULT_FINDINGS_LOG_PATH).strip() or DEFAULT_FINDINGS_LOG_PATH
    path = Path(relative).expanduser()
    return path if path.is_absolute() else REPO_ROOT / path
