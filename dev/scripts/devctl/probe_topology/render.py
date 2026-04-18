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
        metric_explanations = hotspot.get("metric_explanations")
        if isinstance(metric_explanations, dict):
            for key in ("fan_in", "fan_out", "bridge_score", "hotspot_rank"):
                text = str(metric_explanations.get(key) or "").strip()
                if text:
                    lines.append(f"- {key}_explanation: {text}")
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
            for row in hints:
                if not isinstance(row, dict):
                    continue
                practice_title = str(row.get("practice_title") or "").strip()
                if not practice_title:
                    continue
                lines.append(
                    f"- practice: {practice_title} -> {row.get('practice_explanation', '')}"
                )
        lines.append("")
    decision_packets = packet.get("decision_packets", [])
    if isinstance(decision_packets, list) and decision_packets:
        lines.extend(
            [
                "## Decision Packets",
                "",
                (
                    "These packets describe intentional design boundaries using "
                    "the same evidence stack for AI agents and human reviewers. "
                    "`decision_mode` controls whether the agent may auto-apply, "
                    "should recommend, or must wait for approval."
                ),
                "",
            ]
        )
        for index, decision in enumerate(decision_packets[:HOTSPOT_LIMIT], start=1):
            if not isinstance(decision, dict):
                continue
            lines.append(f"### {index}. {decision.get('file')}::{decision.get('symbol')}")
            lines.append("")
            lines.append(f"- decision_mode: {decision.get('decision_mode')}")
            lines.append(f"- severity: {decision.get('severity')}")
            lines.append(f"- detected_by: {decision.get('probe')}")
            lines.append(f"- rationale: {decision.get('rationale')}")
            rule_summary = str(decision.get("rule_summary") or "").strip()
            if rule_summary:
                lines.append(f"- rule_summary: {rule_summary}")
            match_evidence = decision.get("match_evidence")
            if isinstance(match_evidence, list):
                for row in match_evidence[:2]:
                    if not isinstance(row, dict):
                        continue
                    lines.append(
                        f"- match_evidence: {row.get('summary', '')}"
                    )
            rejected_rule_traces = decision.get("rejected_rule_traces")
            if isinstance(rejected_rule_traces, list):
                for row in rejected_rule_traces[:2]:
                    if not isinstance(row, dict):
                        continue
                    lines.append(
                        f"- rejected_rule: {row.get('summary', '')} -> {row.get('rejected_because', '')}"
                    )
            invariants = decision.get("invariants", [])
            if isinstance(invariants, list) and invariants:
                lines.append(f"- invariants: {' | '.join(str(item) for item in invariants)}")
            if decision.get("precedent"):
                lines.append(f"- precedent: {decision.get('precedent')}")
            validation_plan = decision.get("validation_plan", [])
            if isinstance(validation_plan, list) and validation_plan:
                lines.append(f"- validation_plan: {' | '.join(str(item) for item in validation_plan)}")
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
