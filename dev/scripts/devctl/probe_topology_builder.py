"""Topology artifact builders for probe reporting."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from .probe_topology_packet import (
    SEVERITY_POINTS,
    bounded_next_slice,
    build_focused_graph,
    lens_counts,
    priority_reason,
    priority_score,
    rank_neighbors,
    severity_counts,
)
from .probe_topology_scan import (
    build_python_module_index,
    build_rust_suffix_index,
    collect_changed_paths,
    collect_python_edges,
    collect_rust_edges,
    iter_source_files,
    owners_for_path,
    parse_codeowners_rules,
    repo_relative,
)


@dataclass(frozen=True)
class HintExcerpt:
    probe: object
    symbol: object
    risk_type: object
    severity: object
    review_lens: object
    ai_instruction: object


def build_node_record(
    *,
    language: str,
    fan_in: int,
    fan_out: int,
    owners: list[str],
    changed: bool,
    hint_count: int,
) -> dict[str, Any]:
    record: dict[str, Any] = {}
    record["language"] = language
    record["fan_in"] = fan_in
    record["fan_out"] = fan_out
    record["owners"] = owners
    record["changed"] = changed
    record["hint_count"] = hint_count
    return record


def build_hint_excerpt(hint: dict[str, Any]) -> HintExcerpt:
    return HintExcerpt(
        probe=hint.get("probe"),
        symbol=hint.get("symbol"),
        risk_type=hint.get("risk_type"),
        severity=hint.get("severity"),
        review_lens=hint.get("review_lens"),
        ai_instruction=hint.get("ai_instruction"),
    )


def build_hotspot_record(
    *,
    file_path: str,
    node: dict[str, Any],
    hints: list[dict[str, Any]],
    neighbors: list[dict[str, Any]],
    score: int,
    connected_hint_neighbors: int,
) -> dict[str, Any]:
    severity_summary = severity_counts(hints)
    lens_summary = lens_counts(hints)
    record: dict[str, Any] = {}
    record["file"] = file_path
    record["language"] = node["language"]
    record["owners"] = node["owners"]
    record["changed"] = node["changed"]
    record["hint_count"] = len(hints)
    record["severity_counts"] = severity_summary
    record["review_lens_counts"] = lens_summary
    record["fan_in"] = node["fan_in"]
    record["fan_out"] = node["fan_out"]
    record["bridge_score"] = min(int(node["fan_in"]), int(node["fan_out"]))
    record["priority_score"] = score
    record["priority_reason"] = priority_reason(
        severity_summary=severity_summary,
        fan_in=int(node["fan_in"]),
        fan_out=int(node["fan_out"]),
        connected_hint_neighbors=connected_hint_neighbors,
        changed=bool(node["changed"]),
    )
    record["connected_files"] = neighbors
    excerpts = [
        asdict(build_hint_excerpt(hint))
        for hint in sorted(
            hints,
            key=lambda row: (
                -SEVERITY_POINTS.get(str(row.get("severity") or "low"), 10),
                str(row.get("probe") or ""),
                str(row.get("symbol") or ""),
            ),
        )[:3]
    ]
    record["representative_hints"] = excerpts
    record["bounded_next_slice"] = bounded_next_slice(file_path, hints)
    return record


def build_probe_topology_artifact(
    *,
    risk_hints: list[dict[str, Any]],
    since_ref: str | None,
    head_ref: str,
) -> dict[str, Any]:
    source_files = iter_source_files()
    python_index = build_python_module_index(source_files["python"])
    rust_index = build_rust_suffix_index(source_files["rust"])
    python_edges, python_warnings = collect_python_edges(
        source_files["python"],
        python_index,
    )
    rust_edges, rust_warnings = collect_rust_edges(source_files["rust"], rust_index)
    changed_paths, git_warnings = collect_changed_paths(since_ref, head_ref)
    rules = parse_codeowners_rules()

    all_paths = {repo_relative(path): "python" for path in source_files["python"]}
    all_paths.update({repo_relative(path): "rust" for path in source_files["rust"]})

    incoming: dict[str, set[str]] = defaultdict(set)
    outgoing: dict[str, set[str]] = defaultdict(set)
    edge_rows = [{"from": src, "to": dst, "kind": kind} for src, dst, kind in sorted(python_edges | rust_edges)]
    for edge in edge_rows:
        outgoing[edge["from"]].add(edge["to"])
        incoming[edge["to"]].add(edge["from"])

    hints_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for hint in risk_hints:
        file_path = str(hint.get("file") or "").strip()
        if file_path:
            hints_by_file[file_path].append(hint)

    hint_counts = {path: len(hints) for path, hints in hints_by_file.items()}
    nodes: dict[str, dict[str, Any]] = {}
    for path, language in sorted(all_paths.items()):
        nodes[path] = build_node_record(
            language=language,
            fan_in=len(incoming.get(path, set())),
            fan_out=len(outgoing.get(path, set())),
            owners=owners_for_path(path, rules),
            changed=path in changed_paths,
            hint_count=hint_counts.get(path, 0),
        )

    hotspots: list[dict[str, Any]] = []
    for file_path, hints in hints_by_file.items():
        node = nodes.get(file_path)
        if node is None:
            node = build_node_record(
                language="unknown",
                fan_in=len(incoming.get(file_path, set())),
                fan_out=len(outgoing.get(file_path, set())),
                owners=owners_for_path(file_path, rules),
                changed=file_path in changed_paths,
                hint_count=len(hints),
            )
        neighbors = rank_neighbors(
            file_path=file_path,
            incoming=incoming,
            outgoing=outgoing,
            hint_counts=hint_counts,
            changed_paths=changed_paths,
        )
        connected_hint_neighbors = sum(1 for row in neighbors if int(row["hint_count"]) > 0)
        score = priority_score(
            hints=hints,
            fan_in=int(node["fan_in"]),
            fan_out=int(node["fan_out"]),
            connected_hint_neighbors=connected_hint_neighbors,
            changed=bool(node["changed"]),
            owners=list(node["owners"]),
        )
        hotspots.append(
            build_hotspot_record(
                file_path=file_path,
                node=node,
                hints=hints,
                neighbors=neighbors,
                score=score,
                connected_hint_neighbors=connected_hint_neighbors,
            )
        )
    hotspots.sort(key=lambda row: (-int(row["priority_score"]), row["file"]))

    summary: dict[str, Any] = {}
    summary["source_files"] = len(all_paths)
    summary["edge_count"] = len(edge_rows)
    summary["changed_files"] = len(changed_paths)
    summary["changed_hint_files"] = sum(1 for row in hotspots if row["changed"])
    summary["focused_files"] = len(hints_by_file)

    payload: dict[str, Any] = {}
    payload["summary"] = summary
    payload["changed_files"] = sorted(changed_paths)
    payload["focused_files"] = sorted(hints_by_file)
    payload["nodes"] = nodes
    payload["edges"] = edge_rows
    payload["hotspots"] = hotspots[:10]
    payload["focused_graph"] = build_focused_graph(
        hotspots=hotspots,
        nodes=nodes,
        edges=edge_rows,
    )
    payload["warnings"] = python_warnings + rust_warnings + git_warnings
    return payload


def build_review_packet(
    *,
    summary: dict[str, Any],
    topology: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    hotspots = topology.get("hotspots", [])
    if not isinstance(hotspots, list):
        hotspots = []
    topology_summary = topology.get("summary", {})

    packet_summary: dict[str, Any] = {}
    packet_summary["risk_hints"] = int(summary.get("risk_hints", 0))
    packet_summary["files_with_hints"] = int(summary.get("files_with_hints", 0))
    packet_summary["probe_count"] = int(summary.get("probe_count", 0))
    packet_summary["top_hotspot"] = hotspots[0] if hotspots else None
    packet_summary["changed_hint_files"] = int(
        topology_summary.get("changed_hint_files", 0) if isinstance(topology_summary, dict) else 0
    )
    packet_summary["topology_edges"] = int(
        topology_summary.get("edge_count", 0) if isinstance(topology_summary, dict) else 0
    )

    verification: dict[str, Any] = {}
    verification["probe_errors"] = errors
    verification["probe_warnings"] = warnings
    verification["verified_by"] = ["devctl probe-report"]

    packet: dict[str, Any] = {}
    packet["summary"] = packet_summary
    packet["hotspots"] = hotspots
    packet["focused_graph"] = topology.get("focused_graph", {})
    packet["verification"] = verification
    packet["recommended_command"] = "python3 dev/scripts/devctl.py probe-report --format md"
    return packet
