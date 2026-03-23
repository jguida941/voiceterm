"""Typed delta and trend helpers over saved ContextGraphSnapshot artifacts."""

from __future__ import annotations

from pathlib import Path

from .models import EDGE_KIND_IMPORTS
from .snapshot_payload import ContextGraphSnapshot, SnapshotResolutionError
from .snapshot_store import (
    format_context_graph_snapshot_path,
    list_context_graph_snapshots,
    load_context_graph_snapshot,
    resolve_context_graph_snapshot_ref,
)
from .snapshot_diff_models import (
    CONTEXT_GRAPH_DELTA_CONTRACT_ID,
    CONTEXT_GRAPH_DELTA_SCHEMA_VERSION,
    ContextGraphDelta,
    EdgeSummary,
    NodeChangeSummary,
    NodeSummary,
    SnapshotAnchor,
    SnapshotTrendPoint,
    SnapshotTrendSummary,
    TemperatureShiftSummary,
)


def load_graph_delta(
    *,
    from_ref: str | None,
    to_ref: str | None,
    trend_window: int = 5,
) -> ContextGraphDelta:
    """Resolve saved snapshot refs and compute one typed graph delta."""
    to_path = resolve_context_graph_snapshot_ref(to_ref or "latest")
    from_path = resolve_context_graph_snapshot_ref(from_ref or "previous", exclude=to_path)
    if from_path.resolve() == to_path.resolve():
        raise SnapshotResolutionError("snapshot diff requires distinct --from and --to refs")
    before = load_context_graph_snapshot(from_path)
    after = load_context_graph_snapshot(to_path)
    trend = build_snapshot_trend(to_path=to_path, window_size=trend_window)
    return compute_graph_delta(
        before,
        after,
        from_path=from_path,
        to_path=to_path,
        trend=trend,
    )


def compute_graph_delta(
    before: ContextGraphSnapshot,
    after: ContextGraphSnapshot,
    *,
    from_path: Path,
    to_path: Path,
    trend: SnapshotTrendSummary | None,
) -> ContextGraphDelta:
    """Compute the bounded node/edge/temperature delta between two snapshots."""
    before_nodes = {str(node["node_id"]): node for node in before.nodes if "node_id" in node}
    after_nodes = {str(node["node_id"]): node for node in after.nodes if "node_id" in node}
    before_edges = {_edge_key(edge): edge for edge in before.edges if _edge_key(edge) is not None}
    after_edges = {_edge_key(edge): edge for edge in after.edges if _edge_key(edge) is not None}

    added_node_ids = sorted(set(after_nodes).difference(before_nodes))
    removed_node_ids = sorted(set(before_nodes).difference(after_nodes))
    common_node_ids = sorted(set(before_nodes).intersection(after_nodes))
    changed_nodes = [
        _build_changed_node(before_nodes[node_id], after_nodes[node_id])
        for node_id in common_node_ids
        if before_nodes[node_id] != after_nodes[node_id]
    ]

    added_edge_keys = sorted(set(after_edges).difference(before_edges))
    removed_edge_keys = sorted(set(before_edges).difference(after_edges))
    new_edge_kinds = sorted(set(after.edges_by_kind).difference(before.edges_by_kind))
    dropped_edge_kinds = sorted(set(before.edges_by_kind).difference(after.edges_by_kind))
    temperature_shifts = sorted(
        _build_temperature_shifts(before_nodes, after_nodes),
        key=lambda item: abs(item.delta),
        reverse=True,
    )
    hottest_increases = [item for item in temperature_shifts if item.delta > 0][:10]
    hottest_decreases = [item for item in temperature_shifts if item.delta < 0][:10]

    return ContextGraphDelta(
        schema_version=CONTEXT_GRAPH_DELTA_SCHEMA_VERSION,
        contract_id=CONTEXT_GRAPH_DELTA_CONTRACT_ID,
        from_snapshot=_build_snapshot_anchor(from_path, before),
        to_snapshot=_build_snapshot_anchor(to_path, after),
        added_nodes_count=len(added_node_ids),
        removed_nodes_count=len(removed_node_ids),
        changed_nodes_count=len(changed_nodes),
        added_edges_count=len(added_edge_keys),
        removed_edges_count=len(removed_edge_keys),
        new_edge_kinds=new_edge_kinds,
        dropped_edge_kinds=dropped_edge_kinds,
        added_nodes_sample=[_node_summary(after_nodes[node_id]) for node_id in added_node_ids[:10]],
        removed_nodes_sample=[_node_summary(before_nodes[node_id]) for node_id in removed_node_ids[:10]],
        changed_nodes_sample=changed_nodes[:10],
        added_edges_sample=[_edge_summary(after_edges[key]) for key in added_edge_keys[:10]],
        removed_edges_sample=[_edge_summary(before_edges[key]) for key in removed_edge_keys[:10]],
        hottest_increases=hottest_increases,
        hottest_decreases=hottest_decreases,
        trend=trend,
    )


def build_snapshot_trend(*, to_path: Path, window_size: int) -> SnapshotTrendSummary | None:
    """Build a rolling trend summary ending at the selected target snapshot."""
    if window_size <= 0:
        return None
    snapshot_paths = _sorted_snapshot_paths_before_or_equal(to_path)
    if len(snapshot_paths) < 2:
        return None
    selected_paths = snapshot_paths[-window_size:]
    snapshots = [(path, load_context_graph_snapshot(path)) for path in selected_paths]
    points = [_trend_point(path, snapshot) for path, snapshot in snapshots]
    first = points[0]
    last = points[-1]
    average_delta = round(last.average_temperature - first.average_temperature, 4)
    return SnapshotTrendSummary(
        window_size=len(points),
        temperature_direction=_temperature_direction(average_delta),
        average_temperature_delta=average_delta,
        node_count_delta=last.node_count - first.node_count,
        edge_count_delta=last.edge_count - first.edge_count,
        import_cycle_delta=last.import_cycle_count - first.import_cycle_count,
        hot_bucket_delta=_hot_bucket_count(snapshots[-1][1]) - _hot_bucket_count(snapshots[0][1]),
        points=points,
    )


def _sorted_snapshot_paths_before_or_equal(target_path: Path) -> list[Path]:
    resolved_target = target_path.resolve()
    all_paths = list_context_graph_snapshots(snapshot_dir=resolved_target.parent)
    for index, path in enumerate(all_paths):
        if path.resolve() == resolved_target:
            return all_paths[: index + 1]
    raise SnapshotResolutionError(
        f"trend target {resolved_target.name!r} is not a valid ContextGraphSnapshot artifact"
    )


def _build_snapshot_anchor(path: Path, snapshot: ContextGraphSnapshot) -> SnapshotAnchor:
    cycle_count, largest_cycle_size = _import_cycle_stats(snapshot)
    return SnapshotAnchor(
        path=format_context_graph_snapshot_path(path),
        commit_hash=snapshot.commit_hash,
        branch=snapshot.branch,
        generated_at_utc=snapshot.generated_at_utc,
        node_count=snapshot.node_count,
        edge_count=snapshot.edge_count,
        average_temperature=round(snapshot.temperature_distribution.average, 4),
        import_cycle_count=cycle_count,
        largest_import_cycle_size=largest_cycle_size,
    )


def _build_changed_node(before: dict[str, object], after: dict[str, object]) -> NodeChangeSummary:
    fields = [
        field_name
        for field_name in (
            "node_kind",
            "label",
            "canonical_pointer_ref",
            "provenance_ref",
            "temperature",
            "metadata",
        )
        if before.get(field_name) != after.get(field_name)
    ]
    return NodeChangeSummary(
        node_id=str(after.get("node_id") or before.get("node_id") or ""),
        label=str(after.get("label") or before.get("label") or ""),
        canonical_pointer_ref=str(
            after.get("canonical_pointer_ref") or before.get("canonical_pointer_ref") or ""
        ),
        changed_fields=fields,
    )


def _build_temperature_shifts(
    before_nodes: dict[str, dict[str, object]],
    after_nodes: dict[str, dict[str, object]],
) -> list[TemperatureShiftSummary]:
    result: list[TemperatureShiftSummary] = []
    for node_id in sorted(set(before_nodes).intersection(after_nodes)):
        before_temp = float(before_nodes[node_id].get("temperature") or 0.0)
        after_temp = float(after_nodes[node_id].get("temperature") or 0.0)
        delta = round(after_temp - before_temp, 4)
        if delta == 0.0:
            continue
        result.append(
            TemperatureShiftSummary(
                node_id=node_id,
                label=str(after_nodes[node_id].get("label") or before_nodes[node_id].get("label") or ""),
                canonical_pointer_ref=str(
                    after_nodes[node_id].get("canonical_pointer_ref")
                    or before_nodes[node_id].get("canonical_pointer_ref")
                    or ""
                ),
                before=before_temp,
                after=after_temp,
                delta=delta,
            )
        )
    return result


def _node_summary(node: dict[str, object]) -> NodeSummary:
    return NodeSummary(
        node_id=str(node.get("node_id") or ""),
        node_kind=str(node.get("node_kind") or ""),
        label=str(node.get("label") or ""),
        canonical_pointer_ref=str(node.get("canonical_pointer_ref") or ""),
        temperature=float(node.get("temperature") or 0.0),
    )


def _edge_summary(edge: dict[str, object]) -> EdgeSummary:
    return EdgeSummary(
        source_id=str(edge.get("source_id") or ""),
        target_id=str(edge.get("target_id") or ""),
        edge_kind=str(edge.get("edge_kind") or ""),
    )


def _edge_key(edge: dict[str, object]) -> tuple[str, str, str] | None:
    source_id = edge.get("source_id")
    target_id = edge.get("target_id")
    edge_kind = edge.get("edge_kind")
    if not source_id or not target_id or not edge_kind:
        return None
    return str(source_id), str(target_id), str(edge_kind)


def _trend_point(path: Path, snapshot: ContextGraphSnapshot) -> SnapshotTrendPoint:
    cycle_count, _largest_cycle_size = _import_cycle_stats(snapshot)
    return SnapshotTrendPoint(
        path=format_context_graph_snapshot_path(path),
        commit_hash=snapshot.commit_hash,
        generated_at_utc=snapshot.generated_at_utc,
        average_temperature=round(snapshot.temperature_distribution.average, 4),
        node_count=snapshot.node_count,
        edge_count=snapshot.edge_count,
        import_cycle_count=cycle_count,
    )


def _temperature_direction(delta: float) -> str:
    if delta > 0.005:
        return "hotter"
    if delta < -0.005:
        return "cooler"
    return "stable"


def _hot_bucket_count(snapshot: ContextGraphSnapshot) -> int:
    return int(snapshot.temperature_distribution.buckets.get("0.75-1.00", 0))


def _import_cycle_stats(snapshot: ContextGraphSnapshot) -> tuple[int, int]:
    adjacency: dict[str, set[str]] = {}
    for edge in snapshot.edges:
        if edge.get("edge_kind") != EDGE_KIND_IMPORTS:
            continue
        source = str(edge.get("source_id") or "")
        target = str(edge.get("target_id") or "")
        if not source or not target:
            continue
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set())
    if not adjacency:
        return 0, 0
    components = _strongly_connected_components(adjacency)
    real_cycles = [component for component in components if len(component) > 1]
    largest = max((len(component) for component in real_cycles), default=0)
    return len(real_cycles), largest


def _strongly_connected_components(adjacency: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def strongconnect(node_id: str) -> None:
        nonlocal index
        indices[node_id] = index
        lowlinks[node_id] = index
        index += 1
        stack.append(node_id)
        on_stack.add(node_id)

        for neighbor in adjacency.get(node_id, ()):
            if neighbor not in indices:
                strongconnect(neighbor)
                lowlinks[node_id] = min(lowlinks[node_id], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node_id] = min(lowlinks[node_id], indices[neighbor])

        if lowlinks[node_id] == indices[node_id]:
            component: list[str] = []
            while stack:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node_id:
                    break
            components.append(sorted(component))

    for node_id in sorted(adjacency):
        if node_id not in indices:
            strongconnect(node_id)
    return components
