"""Session-pacing helpers for bounded research-to-code startup guidance."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..context_graph.models import (
    EDGE_KIND_CALLS,
    EDGE_KIND_CONTAINS,
    EDGE_KIND_IMPORTS,
    EDGE_KIND_ROUTES_TO,
    NODE_KIND_SOURCE,
    GraphEdge,
    GraphNode,
)
from ..context_graph.snapshot_payload import ContextGraphSnapshot
from ..context_graph.snapshot_store import (
    list_context_graph_snapshots,
    load_context_graph_snapshot,
)
from ..platform.planning_ir_models import NextBestSliceRecord, PlanningIRSnapshot
from .project_governance import ProjectGovernance
from .review_state_models import ReviewState
from .work_intake_models import PlanTargetRef, SessionPacingState, WorkIntakeCoordinationState, WorkIntakeOwnershipState

_DEPENDENCY_EDGE_KINDS = frozenset({EDGE_KIND_IMPORTS, EDGE_KIND_CALLS, EDGE_KIND_ROUTES_TO, EDGE_KIND_CONTAINS})
_MAX_AUTHORITY_REFS = 4
_MAX_DEPENDENCY_REFS = 3


@dataclass(frozen=True, slots=True)
class _PacingFocus:
    active_target: PlanTargetRef | None
    warm_refs: Sequence[str]


@dataclass(frozen=True, slots=True)
class _PacingInputs:
    review_state: ReviewState | None
    planning_snapshot: PlanningIRSnapshot | None = None
    graph_snapshot: ContextGraphSnapshot | None = None


PacingEvidence = tuple[PlanningIRSnapshot, tuple[GraphNode, ...], tuple[GraphEdge, ...], str, str]


def build_session_pacing_state(
    *,
    repo_root: Path,
    governance: ProjectGovernance,
    ownership: WorkIntakeOwnershipState,
    coordination: WorkIntakeCoordinationState,
    focus: _PacingFocus,
    inputs: _PacingInputs,
) -> SessionPacingState:
    """Derive one bounded research-to-code pacing state from repo evidence."""
    authority_refs = _authority_refs(focus)
    planning_snapshot, graph_nodes, graph_edges, source, confidence = _resolve_pacing_evidence(
        repo_root=repo_root,
        governance=governance,
        ownership=ownership,
        coordination=coordination,
        inputs=inputs,
    )
    focus_slice = _select_focus_slice(planning_snapshot=planning_snapshot, active_target=focus.active_target)
    if focus_slice is None:
        research_ref_budget = len(authority_refs)
        return SessionPacingState(
            source=source,
            confidence=confidence,
            research_ref_budget=research_ref_budget,
            authority_ref_count=len(authority_refs),
            authority_refs=authority_refs,
            summary="No bounded next-slice evidence is available yet; finish the authority refs, then narrow the implementation slice before patching.",
        )

    focus_paths = tuple(path for path in focus_slice.file_paths if path)
    dependency_refs, dependency_edge_count = _dependency_refs(
        focus_paths=focus_paths,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
    )
    implementation_refs = _dedupe_paths((*focus_paths, *dependency_refs))
    research_ref_budget = len(authority_refs) + len(implementation_refs)
    complexity_score = _complexity_score(
        authority_ref_count=len(authority_refs),
        focus_file_count=len(focus_paths),
        dependency_edge_count=dependency_edge_count,
        hot_path_count=focus_slice.hot_path_count,
        live_finding_count=focus_slice.live_finding_count,
        schedule_state=focus_slice.schedule_state,
    )
    complexity_band = _complexity_band(complexity_score)
    summary = (
        f"Review {len(authority_refs)} authority refs and {len(implementation_refs)} implementation refs around "
        f"{len(focus_paths)} focus file(s) with {dependency_edge_count} dependency edge(s), "
        f"{focus_slice.live_finding_count} live finding(s), and {focus_slice.hot_path_count} hot path(s), then patch or escalate."
    )
    return SessionPacingState(
        source=source,
        confidence=confidence,
        complexity_band=complexity_band,
        complexity_score=complexity_score,
        research_ref_budget=research_ref_budget,
        authority_ref_count=len(authority_refs),
        focus_file_count=len(focus_paths),
        dependency_edge_count=dependency_edge_count,
        hot_path_count=focus_slice.hot_path_count,
        live_finding_count=focus_slice.live_finding_count,
        focus_slice_id=focus_slice.slice_id,
        focus_plan_path=focus_slice.plan_path,
        focus_summary=focus_slice.summary,
        authority_refs=authority_refs,
        implementation_refs=implementation_refs,
        summary=summary,
    )

def _resolve_pacing_evidence(
    *,
    repo_root: Path,
    governance: ProjectGovernance,
    ownership: WorkIntakeOwnershipState,
    coordination: WorkIntakeCoordinationState,
    inputs: _PacingInputs,
) -> PacingEvidence:
    if inputs.planning_snapshot is not None and inputs.graph_snapshot is not None:
        return (
            inputs.planning_snapshot,
            _snapshot_nodes(inputs.graph_snapshot),
            _snapshot_edges(inputs.graph_snapshot),
            "state_inputs.current_graph_snapshot",
            "high",
        )

    graph_nodes, graph_edges, source, confidence = _resolve_graph_inputs(repo_root)
    planning_snapshot = inputs.planning_snapshot
    if planning_snapshot is None:
        from ..platform.planning_ir import (
            PlanningIRBuildRequest,
            build_planning_ir_snapshot,
        )

        planning_snapshot = build_planning_ir_snapshot(
            PlanningIRBuildRequest(
                repo_root=repo_root,
                governance=governance,
                review_state=inputs.review_state,
                ownership=ownership,
                coordination=coordination,
                graph_nodes=graph_nodes,
                graph_edges=graph_edges,
            )
        )
    return planning_snapshot, graph_nodes, graph_edges, source, confidence


def _resolve_graph_inputs(
    repo_root: Path,
) -> tuple[tuple[GraphNode, ...], tuple[GraphEdge, ...], str, str]:
    """Prefer the newest saved context-graph snapshot on the Step 0 hot path.

    Startup-context is the first command every session runs, and repo policy
    runs it *before* `context-graph --mode bootstrap`. A live graph rebuild
    from that hot path makes fresh commits look like a hung bootstrap, so
    the saved snapshot is accepted regardless of HEAD match and tagged with
    a typed freshness marker (`saved_graph_snapshot_current` vs
    `saved_graph_snapshot_stale_head`). Only when no snapshot exists at all
    does the live builder run, and callers can observe that via the
    `no_snapshot`-to-`live_context_graph_build` fall-through source value.
    """
    from ..context_graph.builder import build_context_graph
    from ..governance.push_state import current_head_commit_sha

    head_commit = current_head_commit_sha(repo_root=repo_root) or ""
    snapshot_paths = list_context_graph_snapshots(repo_root=repo_root)
    if snapshot_paths:
        snapshot = load_context_graph_snapshot(snapshot_paths[-1])
        if not head_commit or snapshot.commit_hash == head_commit:
            source = "saved_graph_snapshot_current"
            confidence = "high"
        else:
            source = "saved_graph_snapshot_stale_head"
            confidence = "medium"
        return (
            _snapshot_nodes(snapshot),
            _snapshot_edges(snapshot),
            source,
            confidence,
        )
    nodes, edges = build_context_graph()
    return tuple(nodes), tuple(edges), "live_context_graph_build", "medium"


def _snapshot_nodes(snapshot: ContextGraphSnapshot) -> tuple[GraphNode, ...]:
    return tuple(
        GraphNode(
            node_id=str(row.get("node_id") or ""),
            node_kind=str(row.get("node_kind") or ""),
            label=str(row.get("label") or ""),
            canonical_pointer_ref=str(row.get("canonical_pointer_ref") or ""),
            provenance_ref=str(row.get("provenance_ref") or ""),
            temperature=float(row.get("temperature") or 0.0),
            metadata=dict(row.get("metadata")) if isinstance(row.get("metadata"), dict) else {},
        )
        for row in snapshot.nodes
    )


def _snapshot_edges(snapshot: ContextGraphSnapshot) -> tuple[GraphEdge, ...]:
    return tuple(
        GraphEdge(
            source_id=str(row.get("source_id") or ""),
            target_id=str(row.get("target_id") or ""),
            edge_kind=str(row.get("edge_kind") or ""),
        )
        for row in snapshot.edges
    )


def _select_focus_slice(
    *,
    planning_snapshot: PlanningIRSnapshot,
    active_target: PlanTargetRef | None,
) -> NextBestSliceRecord | None:
    if not planning_snapshot.next_best_slices:
        return None
    active_path = active_target.plan_path if active_target is not None else ""
    if active_path:
        for row in planning_snapshot.next_best_slices:
            if row.plan_path == active_path:
                return row
    return planning_snapshot.next_best_slices[0]


def _authority_refs(focus: _PacingFocus) -> tuple[str, ...]:
    refs: list[str] = []
    if focus.active_target is not None and focus.active_target.plan_path:
        refs.append(focus.active_target.plan_path)
    for ref in focus.warm_refs:
        text = str(ref).strip()
        if not text or text in refs:
            continue
        refs.append(text)
        if len(refs) >= _MAX_AUTHORITY_REFS:
            break
    return tuple(refs[:_MAX_AUTHORITY_REFS])


def _dependency_refs(
    *,
    focus_paths: Sequence[str],
    graph_nodes: Sequence[GraphNode],
    graph_edges: Sequence[GraphEdge],
) -> tuple[tuple[str, ...], int]:
    if not focus_paths:
        return (), 0
    nodes_by_id = {node.node_id: node for node in graph_nodes}
    focus_ids = {
        node.node_id
        for node in graph_nodes
        if node.node_kind == NODE_KIND_SOURCE and node.canonical_pointer_ref in focus_paths
    }
    if not focus_ids:
        return (), 0

    dependency_edge_count = 0
    neighbor_scores: dict[str, float] = {}
    for edge in graph_edges:
        if edge.edge_kind not in _DEPENDENCY_EDGE_KINDS:
            continue
        other_side = ""
        if edge.source_id in focus_ids:
            other_side = edge.target_id
        elif edge.target_id in focus_ids:
            other_side = edge.source_id
        else:
            continue
        dependency_edge_count += 1
        other_node = nodes_by_id.get(other_side)
        if other_node is None or other_node.node_kind != NODE_KIND_SOURCE:
            continue
        path = other_node.canonical_pointer_ref
        if not path or path in focus_paths:
            continue
        neighbor_scores[path] = max(neighbor_scores.get(path, 0.0), other_node.temperature)

    ordered_paths = sorted(
        neighbor_scores.items(),
        key=lambda item: (-item[1], item[0]),
    )
    return (
        tuple(path for path, _score in ordered_paths[:_MAX_DEPENDENCY_REFS]),
        dependency_edge_count,
    )


def _dedupe_paths(paths: Sequence[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for path in paths:
        text = str(path).strip()
        if text and text not in deduped:
            deduped.append(text)
    return tuple(deduped)


def _complexity_score(
    *,
    authority_ref_count: int,
    focus_file_count: int,
    dependency_edge_count: int,
    hot_path_count: int,
    live_finding_count: int,
    schedule_state: str,
) -> int:
    score = authority_ref_count
    score += focus_file_count * 2
    score += min(dependency_edge_count, 6)
    score += min(hot_path_count, 3) * 2
    score += min(live_finding_count, 3) * 3
    if schedule_state and schedule_state != "ready":
        score += 2
    return score


def _complexity_band(score: int) -> str:
    if score <= 6:
        return "low"
    if score <= 12:
        return "medium"
    if score <= 18:
        return "high"
    return "deep"


__all__ = ["build_session_pacing_state"]
