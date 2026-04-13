"""Focused tests for the scheduler-facing planning reducer."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.context_graph.models import (
    EDGE_KIND_SCOPED_BY,
    NODE_KIND_PLAN,
    NODE_KIND_SOURCE,
    GraphEdge,
    GraphNode,
)
from dev.scripts.devctl.platform.planning_ir import (
    PlanningIRBuildRequest,
    build_planning_ir_snapshot,
)
from dev.scripts.devctl.runtime.project_governance import PlanRegistryEntry
from dev.scripts.devctl.runtime.work_intake_models import (
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
)


def _governance() -> SimpleNamespace:
    tracker = PlanRegistryEntry(
        path="dev/active/MASTER_PLAN.md",
        role="tracker",
        authority="canonical",
        scope="all active MP execution state",
        when_agents_read="always",
        title="Master Plan",
    )
    platform = PlanRegistryEntry(
        path="dev/active/ai_governance_platform.md",
        role="spec",
        authority="mirrored in MASTER_PLAN",
        scope="MP-377",
        when_agents_read="platform work",
        title="AI Governance Platform",
    )
    review = PlanRegistryEntry(
        path="dev/active/review_channel.md",
        role="spec",
        authority="mirrored in MASTER_PLAN",
        scope="MP-355",
        when_agents_read="review channel work",
        title="Review Channel",
    )
    return SimpleNamespace(
        repo_identity=SimpleNamespace(
            repo_name="codex-voice",
            current_branch="feature/planning-ir",
        ),
        plan_registry=SimpleNamespace(
            entries=(tracker, platform, review),
            tracker_path="dev/active/MASTER_PLAN.md",
        ),
    )


def _review_state(
    *,
    scope: str = "MP-377",
    review_candidate_paths: tuple[str, ...] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        current_session=SimpleNamespace(
            last_reviewed_scope=scope,
            current_instruction="continue MP-377",
        ),
        review=SimpleNamespace(plan_id=""),
        review_candidate=SimpleNamespace(
            scope_paths=review_candidate_paths,
            changed_paths=review_candidate_paths,
        )
        if review_candidate_paths
        else None,
    )


def _plan_node(path: str, *, scope: str) -> GraphNode:
    return GraphNode(
        node_id=f"plan:{path}",
        node_kind=NODE_KIND_PLAN,
        label=path,
        canonical_pointer_ref=path,
        provenance_ref="dev/active/INDEX.md",
        temperature=0.6,
        metadata={"scope": scope},
    )


def _source_node(path: str, *, temperature: float) -> GraphNode:
    return GraphNode(
        node_id=f"src:{path}",
        node_kind=NODE_KIND_SOURCE,
        label=path,
        canonical_pointer_ref=path,
        provenance_ref="probe_topology_scan",
        temperature=temperature,
        metadata={},
    )


def _scoped_by(plan_path: str, file_path: str) -> GraphEdge:
    return GraphEdge(
        source_id=f"plan:{plan_path}",
        target_id=f"src:{file_path}",
        edge_kind=EDGE_KIND_SCOPED_BY,
    )


def _finding(
    *,
    finding_id: str,
    check_id: str,
    file_path: str,
    severity: str = "medium",
) -> dict[str, object]:
    return {
        "finding_id": finding_id,
        "verdict": "confirmed_issue",
        "signal_type": "probe",
        "check_id": check_id,
        "file_path": file_path,
        "severity": severity,
        "source_command": "probe-report",
    }


def _report(*rows: dict[str, object]) -> dict[str, object]:
    return {
        "command": "governance-review",
        "generated_at_utc": "2026-04-08T18:00:00Z",
        "log_path": "dev/reports/governance/finding_reviews.jsonl",
        "recent_findings": list(rows),
    }


def test_build_planning_ir_snapshot_prioritizes_active_plan_findings_and_hot_paths(
    tmp_path,
) -> None:
    platform_path = "dev/active/ai_governance_platform.md"
    review_path = "dev/active/review_channel.md"
    platform_file = "dev/scripts/devctl/platform/planning_ir.py"
    platform_hot_file = "dev/scripts/devctl/runtime/work_intake.py"
    review_file = "dev/scripts/devctl/review_channel/status_projection.py"
    nodes = (
        _plan_node("dev/active/MASTER_PLAN.md", scope="all active MP execution state"),
        _plan_node(platform_path, scope="MP-377"),
        _plan_node(review_path, scope="MP-355"),
        _source_node(platform_file, temperature=0.84),
        _source_node(platform_hot_file, temperature=0.57),
        _source_node(review_file, temperature=0.61),
    )
    edges = (
        _scoped_by(platform_path, platform_file),
        _scoped_by(platform_path, platform_hot_file),
        _scoped_by(review_path, review_file),
    )

    snapshot = build_planning_ir_snapshot(
        PlanningIRBuildRequest(
            repo_root=tmp_path,
            governance=_governance(),
            review_state=_review_state(
                review_candidate_paths=(platform_file,),
            ),
            ownership=WorkIntakeOwnershipState(status="clear"),
            coordination=WorkIntakeCoordinationState(
                collaboration_topology="single_agent",
                authority_mode="self_directed",
                work_ownership_mode="exclusive_slice",
                sync_cadence_mode="checkpointed",
            ),
            graph_nodes=nodes,
            graph_edges=edges,
            governance_report=_report(
                _finding(
                    finding_id="f-platform",
                    check_id="probe_platform_hot",
                    file_path=platform_file,
                    severity="high",
                ),
                _finding(
                    finding_id="f-review",
                    check_id="probe_review_hot",
                    file_path=review_file,
                ),
            ),
        )
    )

    assert snapshot.active_target is not None
    assert snapshot.active_target.plan_path == platform_path
    assert snapshot.next_best_slices
    assert snapshot.next_best_slices[0].plan_path == platform_path
    assert platform_file in snapshot.next_best_slices[0].file_paths
    assert snapshot.next_best_slices[0].live_finding_count == 1
    assert snapshot.next_best_slices[0].prioritized_finding_rank == 1
    assert snapshot.next_best_slices[0].finding_severity_band == "high"
    assert snapshot.next_best_slices[0].hot_path_count == 2
    assert snapshot.next_best_slices[0].summary.startswith("1 live finding")


def test_build_planning_ir_snapshot_promotes_active_target_when_ranked_finding_outranks_stale_review_scope(
    tmp_path,
) -> None:
    platform_path = "dev/active/ai_governance_platform.md"
    review_path = "dev/active/review_channel.md"
    platform_file = "dev/scripts/devctl/platform/planning_ir.py"
    review_file = "dev/scripts/devctl/review_channel/status_projection.py"
    nodes = (
        _plan_node("dev/active/MASTER_PLAN.md", scope="all active MP execution state"),
        _plan_node(platform_path, scope="MP-377"),
        _plan_node(review_path, scope="MP-355"),
        _source_node(platform_file, temperature=0.91),
        _source_node(review_file, temperature=0.41),
    )
    edges = (
        _scoped_by(platform_path, platform_file),
        _scoped_by(review_path, review_file),
    )
    stale_review_state = SimpleNamespace(
        current_session=SimpleNamespace(
            last_reviewed_scope="MP-355",
            current_instruction="continue review channel",
        ),
        review=SimpleNamespace(plan_id="MP-355"),
        review_candidate=None,
    )

    snapshot = build_planning_ir_snapshot(
        PlanningIRBuildRequest(
            repo_root=tmp_path,
            governance=_governance(),
            review_state=stale_review_state,
            ownership=WorkIntakeOwnershipState(status="clear"),
            coordination=WorkIntakeCoordinationState(
                collaboration_topology="single_agent",
                authority_mode="self_directed",
                work_ownership_mode="exclusive_slice",
                sync_cadence_mode="checkpointed",
            ),
            graph_nodes=nodes,
            graph_edges=edges,
            governance_report=_report(
                _finding(
                    finding_id="f-platform",
                    check_id="startup_active_target_stale_plan_route",
                    file_path=platform_file,
                    severity="high",
                ),
            ),
        )
    )

    assert snapshot.active_target is not None
    assert snapshot.active_target.plan_path == platform_path
    assert snapshot.next_best_slices
    assert snapshot.next_best_slices[0].plan_path == platform_path
    assert snapshot.next_best_slices[0].prioritized_finding_rank == 1


def test_build_planning_ir_snapshot_surfaces_concurrent_writer_conflicts(
    tmp_path,
) -> None:
    platform_path = "dev/active/ai_governance_platform.md"
    platform_file = "dev/scripts/devctl/platform/planning_ir.py"
    snapshot = build_planning_ir_snapshot(
        PlanningIRBuildRequest(
            repo_root=tmp_path,
            governance=_governance(),
            review_state=_review_state(),
            ownership=WorkIntakeOwnershipState(
                status="concurrent_writer_activity",
                summary="outside-scope dirt overlaps live peer activity",
                dirty_paths=(platform_file,),
                outside_scope_dirty_paths=(platform_file,),
                live_agents=("claude:implementer",),
                concurrent_writer_detected=True,
            ),
            coordination=WorkIntakeCoordinationState(
                collaboration_topology="multi_agent_orchestrated",
                authority_mode="push_locked",
                work_ownership_mode="concurrent_writer_conflict",
                sync_cadence_mode="before_scope_change",
                active_participants=("codex:reviewer", "claude:implementer"),
                duplicate_delegated_worktrees=("shared-worktree",),
                concurrent_writer_conflict_detected=True,
            ),
            graph_nodes=(
                _plan_node("dev/active/MASTER_PLAN.md", scope="all active MP execution state"),
                _plan_node(platform_path, scope="MP-377"),
                _source_node(platform_file, temperature=0.72),
            ),
            graph_edges=(
                _scoped_by(platform_path, platform_file),
            ),
            governance_report=_report(
                _finding(
                    finding_id="f-platform",
                    check_id="probe_platform_hot",
                    file_path=platform_file,
                )
            ),
        )
    )

    assert tuple(conflict.conflict_kind for conflict in snapshot.concurrent_writer_conflicts) == (
        "ownership_conflict",
        "duplicate_worktree",
    )
    assert snapshot.next_best_slices
    assert snapshot.next_best_slices[0].schedule_state == "blocked_by_conflict"
    assert snapshot.next_best_slices[0].recommended_topology == "single_agent"


def test_build_planning_ir_snapshot_flags_unowned_hot_paths_and_plan_mismatches(
    tmp_path,
) -> None:
    platform_path = "dev/active/ai_governance_platform.md"
    review_path = "dev/active/review_channel.md"
    review_file = "dev/scripts/devctl/review_channel/status_projection.py"
    unowned_file = "dev/scripts/devctl/platform/system_picture.py"
    snapshot = build_planning_ir_snapshot(
        PlanningIRBuildRequest(
            repo_root=tmp_path,
            governance=_governance(),
            review_state=_review_state(scope="MP-377"),
            ownership=WorkIntakeOwnershipState(status="clear"),
            coordination=WorkIntakeCoordinationState(
                collaboration_topology="single_agent",
                authority_mode="self_directed",
                work_ownership_mode="exclusive_slice",
                sync_cadence_mode="checkpointed",
            ),
            graph_nodes=(
                _plan_node("dev/active/MASTER_PLAN.md", scope="all active MP execution state"),
                _plan_node(platform_path, scope="MP-377"),
                _plan_node(review_path, scope="MP-355"),
                _source_node(review_file, temperature=0.66),
                _source_node(unowned_file, temperature=0.78),
            ),
            graph_edges=(
                _scoped_by(review_path, review_file),
            ),
            governance_report=_report(
                _finding(
                    finding_id="f-unowned",
                    check_id="probe_unowned_hot",
                    file_path=unowned_file,
                    severity="high",
                ),
                _finding(
                    finding_id="f-review",
                    check_id="probe_review_hot",
                    file_path=review_file,
                ),
            ),
        )
    )

    assert snapshot.unowned_hot_paths
    assert snapshot.unowned_hot_paths[0].file_path == unowned_file
    assert snapshot.active_target is not None
    assert snapshot.active_target.plan_path == review_path
    mismatch_kinds = {item.mismatch_kind for item in snapshot.plan_finding_mismatches}
    assert "unowned_finding" in mismatch_kinds
    assert "active_target_not_owner" not in mismatch_kinds


def test_build_planning_ir_snapshot_uses_request_review_state_without_refresh(
    tmp_path,
) -> None:
    request = PlanningIRBuildRequest(
        repo_root=tmp_path,
        governance=_governance(),
        review_state=_review_state(scope="MP-377"),
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="single_agent",
            authority_mode="self_directed",
            work_ownership_mode="exclusive_slice",
            sync_cadence_mode="checkpointed",
        ),
        graph_nodes=(
            _plan_node("dev/active/MASTER_PLAN.md", scope="all active MP execution state"),
            _plan_node("dev/active/ai_governance_platform.md", scope="MP-377"),
            _source_node("dev/scripts/devctl/platform/planning_ir.py", temperature=0.61),
        ),
        graph_edges=(
            _scoped_by("dev/active/ai_governance_platform.md", "dev/scripts/devctl/platform/planning_ir.py"),
        ),
        governance_report=_report(),
    )

    with patch(
        "dev.scripts.devctl.platform.planning_ir_sources.load_current_review_state",
        side_effect=AssertionError("should not refresh review state"),
    ):
        snapshot = build_planning_ir_snapshot(request)

    assert snapshot.active_target is not None
    assert snapshot.active_target.plan_scope == "MP-377"
