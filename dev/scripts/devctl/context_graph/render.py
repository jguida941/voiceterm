"""Renderers for context-graph query results, bootstrap packets, and concept views.

Concept-view renderers (mermaid, dot) follow the same pattern as
``probe_topology_render.py`` and produce output compatible with the
existing ``dev/reports/probes/latest/`` artifact path.
"""

from __future__ import annotations

from typing import Any

from .concept_render import render_concept_dot, render_concept_mermaid
from .models import QueryResult


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
    for item in result.evidence:
        lines.append(f"- {item}")
    lines.append("")

    if result.matched_nodes:
        lines.append("## Matched Nodes")
        lines.append("")
        lines.append(
            "| Node | Kind | Temperature | Canonical Ref | Provenance |"
        )
        lines.append("|---|---|---|---|---|")
        for node in result.matched_nodes[:50]:
            lines.append(
                f"| `{node.label}` "
                f"| {node.node_kind} "
                f"| {node.temperature:.3f} "
                f"| `{node.canonical_pointer_ref}` "
                f"| {node.provenance_ref} |"
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
        lines.append("| File | Temp | Fan-in | Fan-out |")
        lines.append("|---|---|---|---|")
        for h in hotspots:
            lines.append(f"| `{h['file']}` | {h['temperature']:.3f} | {h.get('fan_in', 0)} | {h.get('fan_out', 0)} |")
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


def append_quality_signal_lines(
    lines: list[str],
    quality_signals: object,
) -> None:
    """Append one bounded quality-signal section when startup data is present."""
    if not isinstance(quality_signals, dict) or not quality_signals:
        return
    lines.append("## Quality Signals")
    lines.append("")
    _append_probe_report_summary(lines, quality_signals.get("probe_report"))
    _append_governance_review_summary(
        lines,
        quality_signals.get("governance_review"),
    )
    _append_guidance_hotspots(lines, quality_signals.get("guidance_hotspots"))
    _append_watchdog_summary(lines, quality_signals.get("watchdog"))
    _append_command_reliability_summary(
        lines,
        quality_signals.get("command_reliability"),
    )
    lines.append("")


def _append_probe_report_summary(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    lines.append(
        "- **probe-report** ({generated_at}): {risk_hints} hints across {files_with_hints} files".format(
            generated_at=payload.get("generated_at", "unknown"),
            risk_hints=payload.get("risk_hints", 0),
            files_with_hints=payload.get("files_with_hints", 0),
        )
    )
    top_files = payload.get("top_files")
    if isinstance(top_files, list) and top_files:
        rendered = ", ".join(
            "`{file}` ({hint_count})".format(
                file=row.get("file", "unknown"),
                hint_count=row.get("hint_count", 0),
            )
            for row in top_files
            if isinstance(row, dict)
        )
        if rendered:
            lines.append(f"- top hinted files: {rendered}")


def _append_governance_review_summary(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    lines.append(
        "- **governance-review** ({generated_at}): {total_findings} findings, {open_findings} open, {fixed_count} fixed, cleanup {cleanup_rate}%".format(
            generated_at=payload.get("generated_at_utc", "unknown"),
            total_findings=payload.get("total_findings", 0),
            open_findings=payload.get("open_finding_count", 0),
            fixed_count=payload.get("fixed_count", 0),
            cleanup_rate=payload.get("cleanup_rate_pct", 0),
        )
    )


def _append_guidance_hotspots(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, list) or not payload:
        return
    hotspot = payload[0]
    if not isinstance(hotspot, dict):
        return
    lines.append(
        "- **guidance hotspot**: `{file}` ({hint_count} hints)".format(
            file=hotspot.get("file", "unknown"),
            hint_count=hotspot.get("hint_count", 0),
        )
    )
    bounded_next_slice = str(hotspot.get("bounded_next_slice") or "").strip()
    if bounded_next_slice:
        lines.append(f"- next slice: {bounded_next_slice}")
    guidance = hotspot.get("guidance")
    if isinstance(guidance, list):
        for row in guidance[:2]:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- guidance: `{probe}` on `{symbol}` [{severity}] -> {instruction}".format(
                    probe=row.get("probe", "unknown"),
                    symbol=row.get("symbol", "(file-level)"),
                    severity=row.get("severity", "unknown"),
                    instruction=row.get("ai_instruction", ""),
                )
            )


def _append_watchdog_summary(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    lines.append(
        "- **watchdog** ({generated_at}): {episodes} episodes, success {success_rate}%, false positives {false_positive_rate}%, top family `{top_family}`".format(
            generated_at=payload.get("generated_at", "unknown"),
            episodes=payload.get("total_episodes", 0),
            success_rate=payload.get("success_rate_pct", 0),
            false_positive_rate=payload.get("false_positive_rate_pct", 0),
            top_family=payload.get("top_guard_family", "unknown"),
        )
    )


def _append_command_reliability_summary(lines: list[str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    lines.append(
        "- **command reliability** ({generated_at}): {events} events, success {success_rate}%, p95 runtime {p95}s".format(
            generated_at=payload.get("generated_at", "unknown"),
            events=payload.get("total_events", 0),
            success_rate=payload.get("success_rate_pct", 0),
            p95=payload.get("p95_duration_seconds", 0),
        )
    )
    commands = payload.get("commands")
    if not isinstance(commands, list):
        return
    rendered = ", ".join(
        "`{command}` {success_rate}%/{duration}s".format(
            command=row.get("command", "unknown"),
            success_rate=row.get("success_rate_pct", 0),
            duration=row.get("avg_duration_seconds", 0),
        )
        for row in commands
        if isinstance(row, dict)
    )
    if rendered:
        lines.append(f"- command slice: {rendered}")
