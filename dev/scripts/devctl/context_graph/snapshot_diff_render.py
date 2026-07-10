"""Markdown renderer for typed context-graph snapshot deltas."""

from __future__ import annotations

from .snapshot_diff_models import (
    ContextGraphDelta,
    EdgeSummary,
    NodeChangeSummary,
    NodeSummary,
    TemperatureShiftSummary,
)


def render_snapshot_delta_markdown(delta: ContextGraphDelta) -> str:
    """Render one typed snapshot delta as concise markdown."""
    lines: list[str] = []
    lines.append("# Context Graph Snapshot Delta")
    lines.append("")
    lines.append(
        f"**From:** `{delta.from_snapshot.commit_hash[:12]}` ({delta.from_snapshot.generated_at_utc})  "
        f"**To:** `{delta.to_snapshot.commit_hash[:12]}` ({delta.to_snapshot.generated_at_utc})"
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"- Nodes: {delta.from_snapshot.node_count} -> {delta.to_snapshot.node_count} "
        f"({delta.to_snapshot.node_count - delta.from_snapshot.node_count:+d})"
    )
    lines.append(
        f"- Edges: {delta.from_snapshot.edge_count} -> {delta.to_snapshot.edge_count} "
        f"({delta.to_snapshot.edge_count - delta.from_snapshot.edge_count:+d})"
    )
    lines.append(f"- Added nodes: {delta.added_nodes_count}")
    lines.append(f"- Removed nodes: {delta.removed_nodes_count}")
    lines.append(f"- Changed nodes: {delta.changed_nodes_count}")
    lines.append(f"- Added edges: {delta.added_edges_count}")
    lines.append(f"- Removed edges: {delta.removed_edges_count}")
    lines.append(
        f"- Average temperature: {delta.from_snapshot.average_temperature:.4f} -> "
        f"{delta.to_snapshot.average_temperature:.4f} "
        f"({delta.to_snapshot.average_temperature - delta.from_snapshot.average_temperature:+.4f})"
    )
    lines.append(
        f"- Import-cycle groups: {delta.from_snapshot.import_cycle_count} -> "
        f"{delta.to_snapshot.import_cycle_count} "
        f"({delta.to_snapshot.import_cycle_count - delta.from_snapshot.import_cycle_count:+d})"
    )
    if delta.new_edge_kinds:
        lines.append(
            f"- New edge kinds: {', '.join(f'`{item}`' for item in delta.new_edge_kinds)}"
        )
    if delta.dropped_edge_kinds:
        lines.append(
            f"- Dropped edge kinds: {', '.join(f'`{item}`' for item in delta.dropped_edge_kinds)}"
        )
    lines.append("")
    _append_node_table(lines, "Added Nodes", delta.added_nodes_sample)
    _append_node_table(lines, "Removed Nodes", delta.removed_nodes_sample)
    _append_changed_node_table(lines, "Changed Nodes", delta.changed_nodes_sample)
    _append_edge_table(lines, "Added Edges", delta.added_edges_sample)
    _append_edge_table(lines, "Removed Edges", delta.removed_edges_sample)
    _append_temperature_table(lines, "Hottest Increases", delta.hottest_increases)
    _append_temperature_table(lines, "Hottest Decreases", delta.hottest_decreases)
    if delta.trend is not None:
        lines.append("## Trend")
        lines.append("")
        lines.append(f"- Window size: {delta.trend.window_size}")
        lines.append(f"- Temperature direction: `{delta.trend.temperature_direction}`")
        lines.append(f"- Average temperature delta: {delta.trend.average_temperature_delta:+.4f}")
        lines.append(f"- Node count delta: {delta.trend.node_count_delta:+d}")
        lines.append(f"- Edge count delta: {delta.trend.edge_count_delta:+d}")
        lines.append(f"- Import-cycle delta: {delta.trend.import_cycle_delta:+d}")
        lines.append(f"- Hot-bucket delta: {delta.trend.hot_bucket_delta:+d}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _append_node_table(lines: list[str], title: str, nodes: list[NodeSummary]) -> None:
    if not nodes:
        return
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| Node | Kind | Temp | Ref |")
    lines.append("|---|---|---:|---|")
    for node in nodes:
        lines.append(
            f"| `{node.node_id}` | {node.node_kind} | {node.temperature:.3f} | `{node.canonical_pointer_ref}` |"
        )
    lines.append("")


def _append_changed_node_table(
    lines: list[str],
    title: str,
    nodes: list[NodeChangeSummary],
) -> None:
    if not nodes:
        return
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| Node | Changed Fields | Ref |")
    lines.append("|---|---|---|")
    for node in nodes:
        lines.append(
            f"| `{node.node_id}` | {', '.join(node.changed_fields)} | `{node.canonical_pointer_ref}` |"
        )
    lines.append("")


def _append_edge_table(lines: list[str], title: str, edges: list[EdgeSummary]) -> None:
    if not edges:
        return
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| Source | Target | Kind |")
    lines.append("|---|---|---|")
    for edge in edges:
        lines.append(f"| `{edge.source_id}` | `{edge.target_id}` | {edge.edge_kind} |")
    lines.append("")


def _append_temperature_table(
    lines: list[str],
    title: str,
    shifts: list[TemperatureShiftSummary],
) -> None:
    if not shifts:
        return
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| Node | Before | After | Delta | Ref |")
    lines.append("|---|---:|---:|---:|---|")
    for shift in shifts:
        lines.append(
            f"| `{shift.node_id}` | {shift.before:.3f} | {shift.after:.3f} | {shift.delta:+.3f} | `{shift.canonical_pointer_ref}` |"
        )
    lines.append("")
