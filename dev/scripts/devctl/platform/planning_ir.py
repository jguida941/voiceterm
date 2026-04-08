"""Builder for the scheduler-facing planning reducer snapshot."""

from __future__ import annotations

from ..governance.push_state import current_head_commit_sha
from ..time_utils import utc_timestamp
from .planning_ir_models import PlanningIRSnapshot
from .planning_ir_reduction import (
    PlanningReductionContext,
    build_conflicts,
    build_next_best_slices,
    build_plan_finding_mismatches,
    build_unowned_hot_paths,
)
from .planning_ir_sources import (
    PlanningIRBuildRequest,
    repo_name,
    resolve_planning_inputs,
)


def build_planning_ir_snapshot(
    request: PlanningIRBuildRequest | None = None,
) -> PlanningIRSnapshot:
    """Build the bounded planning reducer over plans, findings, graph, and runtime."""
    inputs = resolve_planning_inputs(request)
    conflicts = build_conflicts(
        ownership=inputs.ownership,
        coordination=inputs.coordination,
    )
    reduction = PlanningReductionContext(
        plan_lookup=inputs.plan_lookup,
        active_target=inputs.active_target,
        live_findings=inputs.live_findings,
        hot_paths=inputs.hot_paths,
        plan_to_file_paths=inputs.plan_to_file_paths,
        file_to_plan_paths=inputs.file_to_plan_paths,
        review_state=inputs.review_state,
        conflicts=conflicts,
        coordination=inputs.coordination,
    )
    return PlanningIRSnapshot(
        generated_at_utc=utc_timestamp(),
        repo_name=repo_name(inputs.governance, inputs.repo_root),
        repo_root=str(inputs.repo_root),
        current_branch=inputs.current_branch,
        head_commit_sha=current_head_commit_sha(repo_root=inputs.repo_root) or "",
        graph_source="dev.scripts.devctl.context_graph.builder:build_context_graph",
        governance_report_path=inputs.governance_report_path,
        active_target=inputs.active_target,
        ownership_status=inputs.ownership.status,
        collaboration_topology=inputs.coordination.collaboration_topology,
        authority_mode=inputs.coordination.authority_mode,
        work_ownership_mode=inputs.coordination.work_ownership_mode,
        sync_cadence_mode=inputs.coordination.sync_cadence_mode,
        plan_count=len(inputs.plan_lookup),
        scoped_edge_count=inputs.scoped_edge_count,
        hot_path_count=len(inputs.hot_paths),
        live_finding_count=len(inputs.live_findings),
        next_best_slices=build_next_best_slices(reduction),
        concurrent_writer_conflicts=conflicts,
        unowned_hot_paths=build_unowned_hot_paths(reduction),
        plan_finding_mismatches=build_plan_finding_mismatches(reduction),
    )


__all__ = ["PlanningIRBuildRequest", "build_planning_ir_snapshot"]
