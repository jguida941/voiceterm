"""Hotspot scoring helpers for probe topology artifacts."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .context_graph.models import GraphNode

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
        both = neighbor in incoming.get(file_path, set()) and neighbor in outgoing.get(file_path, set())
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
    score = sum(SEVERITY_POINTS.get(str(hint.get("severity") or "low"), 10) for hint in hints)
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


def metric_explanations(*, fan_in: int, fan_out: int, bridge_score: int, **context: Any) -> dict[str, str]:
    priority_score = int(context.get("priority_score", 0) or 0)
    connected_hint_neighbors = int(context.get("connected_hint_neighbors", 0) or 0)
    changed = bool(context.get("changed", False))
    owners = context.get("owners", [])
    owner_count = len(owners) if isinstance(owners, list) else 0
    return {
        "fan_in": (
            f"`fan_in` is `{fan_in}`: this many repo files point into the hotspot, "
            "so higher values mean more callers or dependents can feel a change here."
        ),
        "fan_out": (
            f"`fan_out` is `{fan_out}`: this many repo files the hotspot points to, "
            "so higher values mean the file orchestrates more downstream behavior."
        ),
        "bridge_score": (
            f"`bridge_score` is `{bridge_score}` (`min(fan_in, fan_out)`), which highlights files "
            "that both depend on other files and are depended on in return."
        ),
        "hotspot_rank": (
            f"`priority_score` is `{priority_score}` because severity, coupling, "
            f"{connected_hint_neighbors} connected hinted neighbor(s), "
            f"{'current edits' if changed else 'no current edits'}, and "
            f"{'known ownership' if owner_count else 'missing ownership'} all feed the hotspot ranking."
        ),
    }


def record_query_match_reason(
    match_reasons: dict[str, list[str]],
    node_id: str,
    reason: str,
) -> None:
    reasons = match_reasons.setdefault(node_id, [])
    if reason not in reasons:
        reasons.append(reason)


def query_match_summary(
    node: GraphNode,
    *,
    direct_match: bool,
    reasons: list[str],
) -> str:
    if direct_match and reasons:
        return reasons[0]
    return f"Included because `{node.label}` is directly connected to a matched node."


def query_match_evidence(
    node: GraphNode,
    *,
    direct_match: bool,
    reasons: list[str],
) -> tuple[str, ...]:
    if direct_match and reasons:
        return tuple(reasons[:3])
    return (f"`{node.label}` stayed in the result because one matched edge touches it.",)


def query_ranking_summary(
    node: GraphNode,
    *,
    direct_match: bool,
    connected_edge_count: int,
) -> str:
    fan_in = int(node.metadata.get("fan_in", 0) or 0)
    fan_out = int(node.metadata.get("fan_out", 0) or 0)
    changed = bool(node.metadata.get("changed", False))
    direct_text = "direct query match" if direct_match else "connected neighbor"
    return (
        f"Ranked as a {direct_text} with temperature {node.temperature:.3f}, "
        f"fan-in {fan_in}, fan-out {fan_out}, and {connected_edge_count} visible edge(s)"
        + (" while the file is currently changed." if changed else ".")
    )


def query_hot_index_ranking_summary(node: GraphNode) -> str:
    fan_in = int(node.metadata.get("fan_in", 0) or 0)
    fan_out = int(node.metadata.get("fan_out", 0) or 0)
    return (
        f"Ranked by hotspot temperature {node.temperature:.3f} from the hot index, "
        f"with fan-in {fan_in} and fan-out {fan_out} contributing to that score."
    )


def enrich_query_node(
    node: GraphNode,
    *,
    match_summary: str,
    match_evidence: tuple[str, ...],
    ranking_summary: str,
) -> GraphNode:
    metadata = dict(node.metadata)
    metadata["match_summary"] = match_summary
    metadata["match_evidence"] = list(match_evidence)
    metadata["ranking_summary"] = ranking_summary
    return GraphNode(
        node_id=node.node_id,
        node_kind=node.node_kind,
        label=node.label,
        canonical_pointer_ref=node.canonical_pointer_ref,
        provenance_ref=node.provenance_ref,
        temperature=node.temperature,
        metadata=metadata,
    )


def bounded_next_slice(file_path: str, hints: list[dict[str, Any]]) -> str:
    symbols = [str(hint.get("symbol") or "").strip() for hint in hints if str(hint.get("symbol") or "").strip()]
    focus = ", ".join(dict.fromkeys(symbols)) or "the top hinted functions"
    dominant_lens = Counter(str(hint.get("review_lens") or "unknown") for hint in hints).most_common(1)
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
    edge_rows = [edge for edge in edges if edge["from"] in focus_nodes and edge["to"] in focus_nodes]
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
