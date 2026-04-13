"""Source-loading and normalization helpers for PlanningIRSnapshot."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import get_repo_root
from ..context_graph.builder import build_context_graph
from ..context_graph.models import (
    EDGE_KIND_SCOPED_BY,
    NODE_KIND_PLAN,
    NODE_KIND_SOURCE,
    GraphEdge,
    GraphNode,
)
from ..runtime.finding_backlog import (
    FindingBacklog,
    build_finding_backlog_from_report,
    load_finding_backlog,
)
from ..runtime.finding_contracts import FindingRecord
from ..runtime.governance_scan import scan_repo_governance_safely
from ..runtime.project_governance import PlanRegistryEntry, ProjectGovernance
from ..runtime.review_state_locator import load_current_review_state
from ..runtime.review_state_models import ReviewState
from ..runtime.work_intake_coordination import build_work_intake_coordination_state
from ..runtime.work_intake_models import (
    PlanTargetRef,
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
)
from ..runtime.work_intake_ownership import build_work_intake_ownership_state
from ..runtime.work_intake_selection import build_target_ref, select_active_plan_entry
from ..triage.findings_priority import (
    accumulated_findings_from_governance_rows,
    rank_accumulated_findings,
)
from ..triage.findings_priority_models import RankedFinding

_HOT_PATH_THRESHOLD = 0.30


@dataclass(frozen=True, slots=True)
class PlanningIRBuildRequest:
    """Typed request surface for building one planning reducer snapshot."""

    repo_root: Path | None = None
    governance: ProjectGovernance | None = None
    review_state: ReviewState | None = None
    ownership: WorkIntakeOwnershipState | None = None
    coordination: WorkIntakeCoordinationState | None = None
    graph_nodes: Sequence[GraphNode] | None = None
    graph_edges: Sequence[GraphEdge] | None = None
    governance_report: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class PlanningIRResolvedInputs:
    """Fully resolved source inputs ready for planning reduction."""

    repo_root: Path
    governance: ProjectGovernance | None
    review_state: ReviewState | None
    ownership: WorkIntakeOwnershipState
    coordination: WorkIntakeCoordinationState
    active_target: PlanTargetRef | None
    plan_lookup: dict[str, PlanRegistryEntry]
    file_to_plan_paths: dict[str, tuple[str, ...]]
    plan_to_file_paths: dict[str, tuple[str, ...]]
    hot_paths: dict[str, float]
    live_findings: tuple[FindingRecord, ...]
    ranked_findings: tuple[RankedFinding, ...]
    scoped_edge_count: int
    governance_report_path: str
    current_branch: str


def resolve_planning_inputs(
    request: PlanningIRBuildRequest | None,
) -> PlanningIRResolvedInputs:
    """Resolve repo/runtime/graph/evidence sources for the planning reducer.

    Callers that already resolved a typed ``review_state`` for the current proof
    tick should provide it on ``PlanningIRBuildRequest`` so this resolver does
    not refresh live review state independently.
    """
    request = request or PlanningIRBuildRequest()
    resolved_root = (request.repo_root or get_repo_root()).resolve()
    resolved_governance = request.governance or scan_repo_governance_safely(resolved_root)
    resolved_review_state = request.review_state or load_current_review_state(
        resolved_root,
        governance=resolved_governance,
    )
    resolved_ownership = request.ownership or build_work_intake_ownership_state(
        repo_root=resolved_root,
        review_state=resolved_review_state,
    )
    resolved_coordination = request.coordination or _build_coordination_state(
        governance=resolved_governance,
        review_state=resolved_review_state,
        ownership=resolved_ownership,
    )
    nodes, edges = _graph_inputs(request)
    file_to_plan_paths, plan_to_file_paths, scoped_edge_count = _plan_scope_maps(
        nodes=nodes,
        edges=edges,
    )
    active_target = _resolve_active_target(
        repo_root=resolved_root,
        governance=resolved_governance,
        review_state=resolved_review_state,
    )
    backlog = _resolve_finding_backlog(
        request=request,
        repo_root=resolved_root,
        governance=resolved_governance,
    )
    ranked_findings = tuple(
        rank_accumulated_findings(
            accumulated_findings_from_governance_rows(backlog.latest_rows),
            graph_nodes=nodes,
            graph_edges=edges,
            include_resolved=False,
            top_n=max(20, len(backlog.open_rows)),
        )
    )
    return PlanningIRResolvedInputs(
        repo_root=resolved_root,
        governance=resolved_governance,
        review_state=resolved_review_state,
        ownership=resolved_ownership,
        coordination=resolved_coordination,
        active_target=active_target,
        plan_lookup=plan_lookup(resolved_governance),
        file_to_plan_paths=file_to_plan_paths,
        plan_to_file_paths=plan_to_file_paths,
        hot_paths=hot_paths(nodes),
        live_findings=backlog.open_findings,
        ranked_findings=ranked_findings,
        scoped_edge_count=scoped_edge_count,
        governance_report_path=backlog.log_path,
        current_branch=current_branch(resolved_governance),
    )


def repo_name(governance: ProjectGovernance | None, repo_root: Path) -> str:
    """Return the repo identity label used in normalized findings."""
    if governance is not None and governance.repo_identity.repo_name:
        return governance.repo_identity.repo_name
    return repo_root.name


def current_branch(governance: ProjectGovernance | None) -> str:
    """Return the current branch from repo governance when known."""
    if governance is None:
        return ""
    return str(governance.repo_identity.current_branch or "").strip()


def plan_lookup(
    governance: ProjectGovernance | None,
) -> dict[str, PlanRegistryEntry]:
    """Return the actionable non-tracker plan registry entries."""
    if governance is None:
        return {}
    return {
        entry.path: entry
        for entry in governance.plan_registry.entries
        if entry.role != "tracker"
    }


def hot_paths(nodes: Sequence[GraphNode]) -> dict[str, float]:
    """Return hot source paths keyed by repo-relative path."""
    return {
        node.canonical_pointer_ref: round(float(node.temperature), 4)
        for node in nodes
        if node.node_kind == NODE_KIND_SOURCE and node.temperature >= _HOT_PATH_THRESHOLD
    }


def _build_coordination_state(
    *,
    governance: ProjectGovernance | None,
    review_state: ReviewState | None,
    ownership: WorkIntakeOwnershipState,
) -> WorkIntakeCoordinationState:
    if governance is None:
        return WorkIntakeCoordinationState(
            work_ownership_mode=_default_work_ownership_mode(ownership.status)
        )
    return build_work_intake_coordination_state(
        governance=governance,
        review_state=review_state,
        ownership=ownership,
        reviewer_gate=None,
    )


def _default_work_ownership_mode(status: str) -> str:
    if status == "concurrent_writer_activity":
        return "concurrent_writer_conflict"
    if status == "outside_scope_dirty_paths":
        return "handoff_pending"
    if status == "scope_unknown_dirty_paths":
        return "scope_unknown"
    return "exclusive_slice"


def _graph_inputs(
    request: PlanningIRBuildRequest,
) -> tuple[tuple[GraphNode, ...], tuple[GraphEdge, ...]]:
    if request.graph_nodes is not None and request.graph_edges is not None:
        return tuple(request.graph_nodes), tuple(request.graph_edges)
    built_nodes, built_edges = build_context_graph()
    return tuple(built_nodes), tuple(built_edges)


def _resolve_active_target(
    *,
    repo_root: Path,
    governance: ProjectGovernance | None,
    review_state: ReviewState | None,
) -> PlanTargetRef | None:
    if governance is None:
        return None
    entry = select_active_plan_entry(governance, review_state)
    return build_target_ref(repo_root, entry)


def _resolve_finding_backlog(
    *,
    request: PlanningIRBuildRequest,
    repo_root: Path,
    governance: ProjectGovernance | None,
) -> FindingBacklog:
    if request.governance_report is not None:
        return build_finding_backlog_from_report(
            report=request.governance_report,
            repo_name=repo_name(governance, repo_root),
            repo_path=str(repo_root),
        )
    return load_finding_backlog(
        repo_root=repo_root,
        governance=governance,
        max_rows=5000,
    )


def _plan_scope_maps(
    *,
    nodes: Sequence[GraphNode],
    edges: Sequence[GraphEdge],
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]], int]:
    plan_by_id = {
        node.node_id: node.canonical_pointer_ref
        for node in nodes
        if node.node_kind == NODE_KIND_PLAN
    }
    file_by_id = {
        node.node_id: node.canonical_pointer_ref
        for node in nodes
        if node.node_kind == NODE_KIND_SOURCE
    }
    file_to_plans: dict[str, list[str]] = defaultdict(list)
    plan_to_files: dict[str, list[str]] = defaultdict(list)
    scoped_edge_count = 0
    for edge in edges:
        if edge.edge_kind != EDGE_KIND_SCOPED_BY:
            continue
        plan_path = plan_by_id.get(edge.source_id)
        file_path = file_by_id.get(edge.target_id)
        if not plan_path or not file_path:
            continue
        scoped_edge_count += 1
        if plan_path not in file_to_plans[file_path]:
            file_to_plans[file_path].append(plan_path)
        if file_path not in plan_to_files[plan_path]:
            plan_to_files[plan_path].append(file_path)
    return (
        {
            path: tuple(sorted(plan_paths))
            for path, plan_paths in file_to_plans.items()
        },
        {
            path: tuple(sorted(file_paths))
            for path, file_paths in plan_to_files.items()
        },
        scoped_edge_count,
    )


__all__ = ["PlanningIRBuildRequest", "PlanningIRResolvedInputs", "resolve_planning_inputs"]
