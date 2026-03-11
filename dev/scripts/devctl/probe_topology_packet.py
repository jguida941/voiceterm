"""Hotspot scoring helpers for probe topology artifacts."""

from __future__ import annotations

from collections import Counter
from typing import Any

SEVERITY_POINTS = {"high": 100, "medium": 40, "low": 10}


def severity_counts(hints: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for hint in hints:
        counts[str(hint.get("severity") or "unknown")] += 1
    return dict(counts)


def lens_counts(hints: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for hint in hints:
        counts[str(hint.get("review_lens") or "unknown")] += 1
    return dict(counts)


def rank_neighbors(
    *,
    file_path: str,
    incoming: dict[str, set[str]],
    outgoing: dict[str, set[str]],
    hint_counts: dict[str, int],
    changed_paths: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    neighbors = incoming.get(file_path, set()) | outgoing.get(file_path, set())
    for neighbor in sorted(neighbors):
        both = neighbor in incoming.get(file_path, set()) and neighbor in outgoing.get(
            file_path, set()
        )
        direction = "both" if both else "inbound"
        if not both and neighbor in outgoing.get(file_path, set()):
            direction = "outbound"
        weight = hint_counts.get(neighbor, 0) * 10
        weight += 5 if neighbor in changed_paths else 0
        weight += len(incoming.get(neighbor, set())) + len(outgoing.get(neighbor, set()))
        row: dict[str, Any] = {}
        row["file"] = neighbor
        row["direction"] = direction
        row["hint_count"] = hint_counts.get(neighbor, 0)
        row["changed"] = neighbor in changed_paths
        row["weight"] = weight
        rows.append(row)
    rows.sort(key=lambda row: (-int(row["weight"]), row["file"]))
    return rows[:5]


def priority_score(
    *,
    hints: list[dict[str, Any]],
    fan_in: int,
    fan_out: int,
    connected_hint_neighbors: int,
    changed: bool,
    owners: list[str],
) -> int:
    score = sum(
        SEVERITY_POINTS.get(str(hint.get("severity") or "low"), 10) for hint in hints
    )
    bridge_score = min(fan_in, fan_out)
    score += min(fan_in, 8) * 7
    score += min(fan_out, 8) * 5
    score += min(bridge_score, 6) * 8
    score += min(connected_hint_neighbors, 5) * 6
    score += len({str(hint.get("review_lens") or "unknown") for hint in hints}) * 4
    if changed:
        score += 15
    if not owners:
        score += 10
    return score


def priority_reason(
    *,
    severity_summary: dict[str, int],
    fan_in: int,
    fan_out: int,
    connected_hint_neighbors: int,
    changed: bool,
) -> str:
    parts: list[str] = []
    if severity_summary.get("high", 0):
        parts.append(f"{severity_summary['high']} high-severity hint(s)")
    elif severity_summary.get("medium", 0):
        parts.append(f"{severity_summary['medium']} medium-severity hint(s)")
    parts.append(f"fan-in={fan_in}, fan-out={fan_out}")
    if connected_hint_neighbors:
        parts.append(f"{connected_hint_neighbors} connected file(s) also flagged")
    if changed:
        parts.append("currently changed")
    return "; ".join(parts)


def bounded_next_slice(file_path: str, hints: list[dict[str, Any]]) -> str:
    symbols = [
        str(hint.get("symbol") or "").strip()
        for hint in hints
        if str(hint.get("symbol") or "").strip()
    ]
    focus = ", ".join(dict.fromkeys(symbols)) or "the top hinted functions"
    dominant_lens = Counter(
        str(hint.get("review_lens") or "unknown") for hint in hints
    ).most_common(1)
    lens = dominant_lens[0][0] if dominant_lens else "quality"
    action_map = {
        "concurrency": "reduce shared-state scope before touching adjacent modules",
        "ownership": "remove conversion or cloning indirection before wider cleanup",
        "design_quality": "extract one clearer helper or typed model and stop there",
        "architecture": "split one responsibility boundary without widening the slice",
    }
    action = action_map.get(
        lens,
        "fix the strongest hint in one file and only pull one direct neighbor if needed",
    )
    return (
        f"Start in {file_path}; focus on {focus}; {action}; then rerun "
        "`python3 dev/scripts/devctl.py probe-report --format md`."
    )


def build_focused_graph(
    *,
    hotspots: list[dict[str, Any]],
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, str]],
) -> dict[str, Any]:
    focus_nodes = {row["file"] for row in hotspots[:3]}
    for hotspot in hotspots[:3]:
        for neighbor in hotspot.get("connected_files", [])[:2]:
            if isinstance(neighbor, dict):
                focus_nodes.add(str(neighbor.get("file") or ""))
    focus_nodes.discard("")
    edge_rows = [
        edge
        for edge in edges
        if edge["from"] in focus_nodes and edge["to"] in focus_nodes
    ]
    node_rows: list[dict[str, Any]] = []
    for file_path in sorted(focus_nodes):
        node = nodes.get(file_path, {})
        row: dict[str, Any] = {}
        row["file"] = file_path
        row["language"] = node.get("language", "unknown")
        row["fan_in"] = node.get("fan_in", 0)
        row["fan_out"] = node.get("fan_out", 0)
        row["changed"] = node.get("changed", False)
        row["owners"] = node.get("owners", [])
        node_rows.append(row)
    graph: dict[str, Any] = {}
    graph["nodes"] = node_rows
    graph["edges"] = edge_rows
    return graph
