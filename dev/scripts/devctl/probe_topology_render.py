"""Rendering helpers for topology-backed probe review packets."""

from __future__ import annotations

from typing import Any

HOTSPOT_LIMIT = 5
VISUAL_HOTSPOT_LIMIT = 3
VISUAL_NEIGHBOR_LIMIT = 2


def render_review_packet_markdown(
    packet: dict[str, Any],
    *,
    rich_report_markdown: str,
) -> str:
    summary = packet.get("summary", {})
    hotspots = packet.get("hotspots", [])
    lines = ["# Probe Review Packet", ""]
    lines.append(f"- risk_hints: {summary.get('risk_hints', 0)}")
    lines.append(f"- files_with_hints: {summary.get('files_with_hints', 0)}")
    lines.append(f"- changed_hint_files: {summary.get('changed_hint_files', 0)}")
    lines.append(f"- topology_edges: {summary.get('topology_edges', 0)}")
    lines.append(f"- recommended_command: {packet.get('recommended_command')}")
    lines.extend(["", "## Ranked Hotspots", ""])
    if not isinstance(hotspots, list) or not hotspots:
        lines.append("- No hotspot packet available.")
        lines.extend(["", "## Detailed Probe Findings", "", rich_report_markdown])
        return "\n".join(lines)
    for index, hotspot in enumerate(hotspots[:HOTSPOT_LIMIT], start=1):
        if not isinstance(hotspot, dict):
            continue
        lines.append(f"### {index}. {hotspot.get('file')}")
        lines.append("")
        lines.append(f"- priority_score: {hotspot.get('priority_score')}")
        lines.append(f"- why_now: {hotspot.get('priority_reason')}")
        lines.append(
            f"- coupling: fan-in={hotspot.get('fan_in')}, fan-out={hotspot.get('fan_out')}, bridge={hotspot.get('bridge_score')}"
        )
        lines.append(f"- owners: {', '.join(hotspot.get('owners', [])) or 'unowned'}")
        lines.append(f"- changed: {hotspot.get('changed')}")
        lines.append(f"- bounded_next_slice: {hotspot.get('bounded_next_slice')}")
        neighbors = hotspot.get("connected_files", [])
        if isinstance(neighbors, list) and neighbors:
            formatted = ", ".join(
                f"{row.get('file')}[{row.get('direction')}]" for row in neighbors[:4] if isinstance(row, dict)
            )
            if formatted:
                lines.append(f"- connected_files: {formatted}")
        hints = hotspot.get("representative_hints", [])
        if isinstance(hints, list) and hints:
            formatted_hints = ", ".join(
                f"{row.get('probe')}:{row.get('symbol')}({row.get('severity')})"
                for row in hints
                if isinstance(row, dict)
            )
            if formatted_hints:
                lines.append(f"- representative_hints: {formatted_hints}")
        lines.append("")
    lines.extend(["## Detailed Probe Findings", "", rich_report_markdown])
    return "\n".join(lines)


def render_hotspot_mermaid(packet: dict[str, Any]) -> str:
    graph = packet.get("focused_graph", {})
    nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
    edges = graph.get("edges", []) if isinstance(graph, dict) else []
    node_ids: dict[str, str] = {}
    lines = ["graph LR"]
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue
        file_path = str(node.get("file") or "")
        node_id = f"n{index}"
        node_ids[file_path] = node_id
        lines.append(f'  {node_id}["{file_path.replace(chr(34), chr(39))}"]')
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = node_ids.get(str(edge.get("from") or ""))
        target = node_ids.get(str(edge.get("to") or ""))
        if source and target:
            lines.append(f"  {source} --> {target}")
    lines.append("  classDef hotspot fill:#f8d7da,stroke:#842029;")
    lines.append("  classDef changed fill:#dbeafe,stroke:#1d4ed8;")
    for hotspot in packet.get("hotspots", [])[:VISUAL_HOTSPOT_LIMIT]:
        if not isinstance(hotspot, dict):
            continue
        node_id = node_ids.get(str(hotspot.get("file") or ""))
        if node_id:
            lines.append(f"  class {node_id} hotspot;")
    for node in nodes:
        if not isinstance(node, dict) or not node.get("changed"):
            continue
        node_id = node_ids.get(str(node.get("file") or ""))
        if node_id:
            lines.append(f"  class {node_id} changed;")
    return "\n".join(lines) + "\n"


def render_hotspot_dot(packet: dict[str, Any]) -> str:
    graph = packet.get("focused_graph", {})
    nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
    edges = graph.get("edges", []) if isinstance(graph, dict) else []
    hotspot_files = {
        str(hotspot.get("file") or "")
        for hotspot in packet.get("hotspots", [])[:VISUAL_HOTSPOT_LIMIT]
        if isinstance(hotspot, dict)
    }
    lines = ["digraph ProbeHotspots {", '  graph [rankdir="LR"];']
    for node in nodes:
        if not isinstance(node, dict):
            continue
        attrs = ['shape="box"']
        file_path = str(node.get("file") or "")
        if file_path in hotspot_files:
            attrs.extend(['style="filled"', 'fillcolor="#f8d7da"'])
        elif node.get("changed"):
            attrs.extend(['style="filled"', 'fillcolor="#dbeafe"'])
        lines.append(f'  "{file_path.replace(chr(34), chr(39))}" [{", ".join(attrs)}];')
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = str(edge.get("from") or "").replace('"', "'")
        target = str(edge.get("to") or "").replace('"', "'")
        if source and target:
            lines.append(f'  "{source}" -> "{target}";')
    lines.append("}")
    return "\n".join(lines) + "\n"
