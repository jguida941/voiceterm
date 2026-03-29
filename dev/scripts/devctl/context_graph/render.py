"""Renderers for context-graph query results, bootstrap packets, and concept views.

Concept-view renderers (mermaid, dot) follow the same pattern as
``probe_topology_render.py`` and produce output compatible with the
existing ``dev/reports/probes/latest/`` artifact path.
"""

from __future__ import annotations

from typing import Any

from .concept_render import render_concept_dot, render_concept_mermaid
from .models import QueryResult
from .quality_signal_render import append_quality_signal_lines


def render_query_result_markdown(result: QueryResult) -> str:
    """Render a QueryResult as human-readable markdown."""
    lines: list[str] = []
    lines.append("# Context Graph — Discovery View")
    lines.append("")
    lines.append(f"**Query:** `{result.query or '(empty — hot index)'}`")
    lines.append("")
    lines.append(
        "> This is a discovery graph built from directory structure and import "
        "edges. Plan-to-concept edges are heuristic (keyword-matched from "
        "INDEX.md prose). Verify connections against canonical docs before "
        "treating them as authority."
    )
    lines.append("")

    no_match = not result.matched_nodes and getattr(result, "confidence", "") == "no_match"
    if not no_match:
        summary = result.hot_index_summary
        lines.append("## Hot Index Summary")
        lines.append("")
        lines.append(f"- Total nodes: {summary.total_nodes}")
        lines.append(f"- Total edges: {summary.total_edges}")
        if summary.nodes_by_kind:
            for kind, count in sorted(summary.nodes_by_kind.items()):
                lines.append(f"  - {kind}: {count}")
        lines.append("")

    lines.append("## Evidence")
    lines.append("")
    if no_match:
        lines.append("- **No matches found** for the given query terms.")
    for item in result.evidence:
        lines.append(f"- {item}")
    lines.append("")

    if result.matched_nodes:
        lines.append("## Matched Nodes")
        lines.append("")
        lines.append(
            "| Node | Kind | Temperature | Why Matched | Why Ranked | Canonical Ref |"
        )
        lines.append("|---|---|---|---|---|---|")
        for node in result.matched_nodes[:50]:
            metadata = node.metadata if isinstance(node.metadata, dict) else {}
            lines.append(
                f"| `{node.label}` "
                f"| {node.node_kind} "
                f"| {node.temperature:.3f} "
                f"| {metadata.get('match_summary', '')} "
                f"| {metadata.get('ranking_summary', '')} "
                f"| `{node.canonical_pointer_ref}` "
                f"|"
            )
        lines.append("")

    if result.edges:
        lines.append("## Edges")
        lines.append("")
        lines.append("| Source | Target | Kind |")
        lines.append("|---|---|---|")
        for edge in result.edges[:100]:
            lines.append(
                f"| `{edge.source_id}` | `{edge.target_id}` | {edge.edge_kind} |"
            )
        lines.append("")

    return "\n".join(lines)


def render_bootstrap_markdown(ctx: dict[str, Any]) -> str:
    """Render a bootstrap context packet as concise AI-ready markdown."""
    lines: list[str] = []
    lines.append("# Bootstrap Context")
    lines.append("")
    lines.append(f"**Repo:** {ctx.get('repo', '?')} | "
                 f"**Branch:** `{ctx.get('branch', '?')}` | "
                 f"**Bridge:** {'active' if ctx.get('bridge_active') else 'inactive'}")
    lines.append("")

    gs = ctx.get("graph_size", {})
    lines.append(f"**Graph:** {gs.get('source_files', 0)} source files, "
                 f"{gs.get('guards', 0)} guards, {gs.get('probes', 0)} probes, "
                 f"{gs.get('active_plans', 0)} plans, {gs.get('edges', 0)} edges")
    lines.append("")

    snapshot = ctx.get("snapshot", {})
    if snapshot:
        temperature = snapshot.get("temperature_distribution", {})
        lines.append("## Snapshot")
        lines.append("")
        lines.append(f"- **path**: `{snapshot.get('path', 'unknown')}`")
        lines.append(f"- **commit_hash**: `{snapshot.get('commit_hash', 'unknown')}`")
        lines.append(f"- **generated_at_utc**: `{snapshot.get('generated_at_utc', 'unknown')}`")
        lines.append(
            f"- **temperature_average**: {float(temperature.get('average', 0.0)):.3f}"
        )
        lines.append("")

    plans = ctx.get("active_plans", [])
    if plans:
        lines.append("## Active Plans")
        lines.append("")
        lines.append("| Path | Role | Scope |")
        lines.append("|---|---|---|")
        for p in plans:
            lines.append(f"| `{p['path']}` | {p.get('role', '')} | {p.get('scope', '')} |")
        lines.append("")

    hotspots = ctx.get("hotspots", [])
    if hotspots:
        lines.append("## Hotspots (highest temperature)")
        lines.append("")
        lines.append("| File | Temp | Fan-in | Fan-out | Why Ranked |")
        lines.append("|---|---|---|---|---|")
        for h in hotspots:
            lines.append(
                f"| `{h['file']}` | {h['temperature']:.3f} | {h.get('fan_in', 0)} | "
                f"{h.get('fan_out', 0)} | {h.get('ranking_summary', '')} |"
            )
        lines.append("")

    cmds = ctx.get("key_commands", {})
    if cmds:
        lines.append("## Key Commands")
        lines.append("")
        for label, cmd in cmds.items():
            lines.append(f"- **{label}**: `{cmd}`")
        lines.append("")

    push_state = ctx.get("push_enforcement", {})
    if push_state:
        lines.append("## Push State")
        lines.append("")
        lines.append(
            f"- **raw_git_push_guarded**: "
            f"{'yes' if push_state.get('raw_git_push_guarded') else 'no'}"
        )
        lines.append(
            f"- **worktree_dirty**: "
            f"{'yes' if push_state.get('worktree_dirty') else 'no'}"
        )
        lines.append(
            f"- **worktree_clean**: "
            f"{'yes' if push_state.get('worktree_clean', True) else 'no'}"
        )
        lines.append(
            f"- **dirty_path_count**: {push_state.get('dirty_path_count', 0)}"
        )
        lines.append(
            f"- **untracked_path_count**: {push_state.get('untracked_path_count', 0)}"
        )
        lines.append(
            f"- **max_dirty_paths_before_checkpoint**: "
            f"{push_state.get('max_dirty_paths_before_checkpoint', 0)}"
        )
        lines.append(
            f"- **max_untracked_paths_before_checkpoint**: "
            f"{push_state.get('max_untracked_paths_before_checkpoint', 0)}"
        )
        lines.append(
            f"- **checkpoint_required**: "
            f"{'yes' if push_state.get('checkpoint_required') else 'no'}"
        )
        lines.append(
            f"- **safe_to_continue_editing**: "
            f"{'yes' if push_state.get('safe_to_continue_editing', True) else 'no'}"
        )
        lines.append(
            f"- **checkpoint_reason**: "
            f"`{push_state.get('checkpoint_reason', 'clean_worktree')}`"
        )
        ahead = push_state.get("ahead_of_upstream_commits")
        ahead_text = str(ahead) if ahead is not None else "unknown"
        lines.append(f"- **ahead_of_upstream_commits**: {ahead_text}")
        publication_state = str(push_state.get("publication_backlog_state") or "").strip()
        if publication_state:
            lines.append(f"- **publication_backlog_state**: `{publication_state}`")
        publication_summary = str(
            push_state.get("publication_backlog_summary") or ""
        ).strip()
        if publication_summary:
            lines.append(f"- **publication_backlog_summary**: {publication_summary}")
        lines.append(
            f"- **recommended_action**: `{push_state.get('recommended_action', 'use_devctl_push')}`"
        )
        lines.append("")

    append_quality_signal_lines(lines, ctx.get("quality_signals"))

    links = ctx.get("bootstrap_links", {})
    if links:
        lines.append("## Deep Links (load on demand)")
        lines.append("")
        for label, path in links.items():
            if path:
                lines.append(f"- **{label}**: `{path}`")
        lines.append("")

    usage = ctx.get("usage", "")
    if usage:
        lines.append(f"> {usage}")
        lines.append("")

    return "\n".join(lines)
