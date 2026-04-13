"""Tests for the bounded coordination-posture reducer."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.platform.coordination_snapshot import (
    build_coordination_snapshot,
)
from dev.scripts.devctl.runtime.work_intake_models import (
    PlanTargetRef,
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
)


def _startup_context(
    *,
    repo_root: Path,
    ownership: WorkIntakeOwnershipState,
    coordination: WorkIntakeCoordinationState,
    continuity: object | None = None,
    active_target: PlanTargetRef | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        governance=SimpleNamespace(
            repo_identity=SimpleNamespace(
                repo_name="codex-voice",
                current_branch="feature/coordination-snapshot",
            )
        ),
        work_intake=SimpleNamespace(
            active_target=active_target
            or PlanTargetRef(
                target_id="plan-target-1",
                plan_path="dev/active/platform_authority_loop.md",
                plan_title="Platform Authority Loop",
                plan_scope="MP-377",
                target_kind="plan_doc",
                anchor_ref="section:scope",
                expected_revision="rev-1",
            ),
            ownership=ownership,
            coordination=coordination,
            continuity=continuity,
        ),
    )


def _participant(
    provider: str,
    role: str,
    *,
    live: bool,
    requested_worker_budget: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        agent_id=provider,
        provider=provider,
        role=role,
        live=live,
        requested_worker_budget=requested_worker_budget,
        session_name=f"{provider}-conductor",
    )


def _receipt(
    agent_id: str,
    *,
    live: bool,
    worktree: str,
    branch: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        agent_id=agent_id,
        provider="codex",
        role="implementer",
        live=live,
        owner_session="codex-conductor",
        lane=agent_id,
        mp_scope="MP-377",
        worktree=worktree,
        branch=branch,
        status="planned" if not live else "live",
    )


def _registry_agent(
    agent_id: str,
    *,
    provider: str,
    current_job: str,
    job_state: str,
    waiting_on: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        agent_id=agent_id,
        provider=provider,
        lane=provider,
        lane_title=current_job.title(),
        current_job=current_job,
        job_state=job_state,
        waiting_on=waiting_on,
        worktree="",
        branch="",
    )


def _review_state(
    *,
    topology_mode: str,
    participants: tuple[SimpleNamespace, ...],
    delegated_work: tuple[SimpleNamespace, ...],
    ready_gates: tuple[SimpleNamespace, ...],
    attention_status: str,
    reviewer_freshness: str,
    registry_agents: tuple[SimpleNamespace, ...],
) -> SimpleNamespace:
    return SimpleNamespace(
        collaboration=SimpleNamespace(
            topology_mode=topology_mode,
            current_slice="Tighten startup coordination",
            participants=participants,
            delegated_work=delegated_work,
            ready_gates=ready_gates,
        ),
        attention=SimpleNamespace(status=attention_status),
        reviewer_runtime=SimpleNamespace(reviewer_freshness=reviewer_freshness),
        registry=SimpleNamespace(agents=registry_agents),
        current_session=SimpleNamespace(
            current_instruction="Tighten startup coordination",
        ),
    )


def test_build_coordination_snapshot_demotes_planned_but_inactive_fanout(
    tmp_path: Path,
) -> None:
    startup = _startup_context(
        repo_root=tmp_path,
        ownership=WorkIntakeOwnershipState(
            status="clear",
            scope_paths=("dev/scripts/devctl/runtime/work_intake.py",),
        ),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="single_agent",
            authority_mode="self_directed",
            work_ownership_mode="exclusive_slice",
            sync_cadence_mode="before_publish",
            active_participant_count=1,
            active_participants=("claude:implementer",),
        ),
    )
    review_state = _review_state(
        topology_mode="multi_agent_orchestrated",
        participants=(
            _participant("codex", "reviewer", live=False),
            _participant("claude", "implementer", live=False),
        ),
        delegated_work=(
            _receipt(
                "AGENT-1",
                live=False,
                worktree="../codex-voice-wt-a1",
                branch="feature/a1",
            ),
        ),
        ready_gates=(
            SimpleNamespace(gate_id="runtime_truth", status="blocked"),
            SimpleNamespace(gate_id="review_truth", status="blocked"),
        ),
        attention_status="inactive",
        reviewer_freshness="overdue",
        registry_agents=(
            _registry_agent(
                "codex",
                provider="codex",
                current_job="reviewer",
                job_state="review_needed",
                waiting_on="worktree",
            ),
            _registry_agent(
                "claude",
                provider="claude",
                current_job="implementer",
                job_state="implementing",
                waiting_on="reviewer",
            ),
        ),
    )

    snapshot = build_coordination_snapshot(
        repo_root=tmp_path,
        startup_context=startup,
        review_state=review_state,
    )

    assert snapshot.declared_topology == "multi_agent_orchestrated"
    assert snapshot.observed_topology == "single_agent"
    assert snapshot.recommended_topology == "single_agent"
    assert snapshot.fanout_posture == "planned_scaffolding_only"
    assert snapshot.safe_to_fanout is False
    assert snapshot.worktree_strategy == "isolated_worker_worktrees"
    assert snapshot.resync_required is True
    assert "attention:inactive" in snapshot.resync_reasons
    assert any(actor.actor_id == "AGENT-1" for actor in snapshot.actors)


def test_build_coordination_snapshot_allows_safe_live_fanout(
    tmp_path: Path,
) -> None:
    startup = _startup_context(
        repo_root=tmp_path,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="multi_agent_orchestrated",
            authority_mode="reviewer_gated",
            work_ownership_mode="shared_slice",
            sync_cadence_mode="continuous",
            active_participant_count=2,
            live_delegated_worker_count=1,
            active_participants=("codex:reviewer", "claude:implementer"),
            delegated_agents=("AGENT-1",),
            delegated_worktrees=("../codex-voice-wt-a1",),
        ),
    )
    review_state = _review_state(
        topology_mode="multi_agent_orchestrated",
        participants=(
            _participant("codex", "reviewer", live=True, requested_worker_budget=1),
            _participant("claude", "implementer", live=True),
        ),
        delegated_work=(
            _receipt(
                "AGENT-1",
                live=True,
                worktree="../codex-voice-wt-a1",
                branch="feature/a1",
            ),
        ),
        ready_gates=(
            SimpleNamespace(gate_id="runtime_truth", status="ready"),
            SimpleNamespace(gate_id="review_truth", status="ready"),
        ),
        attention_status="clear",
        reviewer_freshness="fresh",
        registry_agents=(
            _registry_agent(
                "codex",
                provider="codex",
                current_job="reviewer",
                job_state="reviewing",
            ),
            _registry_agent(
                "claude",
                provider="claude",
                current_job="implementer",
                job_state="implementing",
            ),
        ),
    )

    snapshot = build_coordination_snapshot(
        repo_root=tmp_path,
        startup_context=startup,
        review_state=review_state,
    )

    assert snapshot.fanout_posture == "active_fanout"
    assert snapshot.safe_to_fanout is True
    assert snapshot.recommended_topology == "multi_agent_orchestrated"
    assert snapshot.resync_required is False
    assert snapshot.live_delegated_worker_count == 1


def test_build_coordination_snapshot_allows_sanctioned_local_single_agent_takeover(
    tmp_path: Path,
) -> None:
    startup = _startup_context(
        repo_root=tmp_path,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="single_agent",
            authority_mode="self_directed",
            work_ownership_mode="exclusive_slice",
            sync_cadence_mode="checkpointed",
            active_participant_count=1,
            active_participants=("codex:reviewer",),
        ),
    )
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            topology_mode="multi_agent_orchestrated",
            current_slice="Local takeover",
            participants=(),
            delegated_work=(),
            ready_gates=(
                SimpleNamespace(gate_id="runtime_truth", status="not_required"),
                SimpleNamespace(gate_id="review_truth", status="blocked"),
                SimpleNamespace(gate_id="implementer_state", status="pending"),
            ),
        ),
        attention=SimpleNamespace(status="inactive"),
        reviewer_runtime=SimpleNamespace(
            reviewer_freshness="poll_due",
            reviewer_mode="single_agent",
            effective_reviewer_mode="single_agent",
            remote_control_attachment=SimpleNamespace(status="detached"),
        ),
        registry=SimpleNamespace(agents=()),
        current_session=SimpleNamespace(current_instruction="Local takeover"),
    )

    snapshot = build_coordination_snapshot(
        repo_root=tmp_path,
        startup_context=startup,
        review_state=review_state,
    )

    assert snapshot.observed_topology == "single_agent"
    assert snapshot.recommended_topology == "single_agent"
    assert snapshot.resync_required is False
    assert "attention:inactive" not in snapshot.resync_reasons
    assert "review_truth:blocked" not in snapshot.resync_reasons
    assert "reviewer_freshness:poll_due" not in snapshot.resync_reasons
    assert "declared_topology:multi_agent_orchestrated" not in snapshot.resync_reasons


def test_build_coordination_snapshot_flags_duplicate_worktrees(
    tmp_path: Path,
) -> None:
    startup = _startup_context(
        repo_root=tmp_path,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="multi_agent_orchestrated",
            authority_mode="reviewer_gated",
            work_ownership_mode="concurrent_writer_conflict",
            sync_cadence_mode="before_scope_change",
            active_participant_count=2,
            live_delegated_worker_count=2,
            active_participants=("codex:reviewer", "claude:implementer"),
            duplicate_delegated_worktrees=("../codex-voice-wt-a1",),
            concurrent_writer_conflict_detected=True,
        ),
    )
    review_state = _review_state(
        topology_mode="multi_agent_orchestrated",
        participants=(
            _participant("codex", "reviewer", live=True, requested_worker_budget=2),
            _participant("claude", "implementer", live=True),
        ),
        delegated_work=(
            _receipt(
                "AGENT-1",
                live=True,
                worktree="../codex-voice-wt-a1",
                branch="feature/a1",
            ),
            _receipt(
                "AGENT-2",
                live=True,
                worktree="../codex-voice-wt-a1",
                branch="feature/a2",
            ),
        ),
        ready_gates=(
            SimpleNamespace(gate_id="runtime_truth", status="ready"),
            SimpleNamespace(gate_id="review_truth", status="ready"),
        ),
        attention_status="clear",
        reviewer_freshness="fresh",
        registry_agents=(),
    )

    snapshot = build_coordination_snapshot(
        repo_root=tmp_path,
        startup_context=startup,
        review_state=review_state,
    )

    assert snapshot.fanout_posture == "unsafe_duplicate_worktrees"
    assert snapshot.worktree_strategy == "duplicate_worker_worktree"
    assert snapshot.safe_to_fanout is False
    assert snapshot.duplicate_worktrees == ("../codex-voice-wt-a1",)
    assert snapshot.recommended_topology == "single_agent"


def test_build_coordination_snapshot_falls_back_to_current_instruction(
    tmp_path: Path,
) -> None:
    startup = _startup_context(
        repo_root=tmp_path,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="single_agent",
            authority_mode="self_directed",
            work_ownership_mode="exclusive_slice",
            sync_cadence_mode="before_publish",
            active_participant_count=1,
            active_participants=("claude:implementer",),
        ),
        continuity=SimpleNamespace(current_goal="", next_action="", summary=""),
    )
    review_state = _review_state(
        topology_mode="single_agent",
        participants=(),
        delegated_work=(),
        ready_gates=(),
        attention_status="inactive",
        reviewer_freshness="overdue",
        registry_agents=(),
    )
    review_state.collaboration.current_slice = ""
    review_state.current_session.current_instruction = (
        "Drive the shared coordination read model first."
    )

    snapshot = build_coordination_snapshot(
        repo_root=tmp_path,
        startup_context=startup,
        review_state=review_state,
    )

    assert snapshot.current_slice == "Drive the shared coordination read model first."


def test_build_coordination_snapshot_prefers_typed_coordination_current_slice(
    tmp_path: Path,
) -> None:
    startup = _startup_context(
        repo_root=tmp_path,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="single_agent",
            authority_mode="self_directed",
            work_ownership_mode="exclusive_slice",
            sync_cadence_mode="before_publish",
            active_participant_count=1,
            active_participants=("codex:reviewer",),
        ),
        continuity=SimpleNamespace(current_goal="", next_action="", summary=""),
    )
    review_state = _review_state(
        topology_mode="single_agent",
        participants=(),
        delegated_work=(),
        ready_gates=(),
        attention_status="inactive",
        reviewer_freshness="overdue",
        registry_agents=(),
    )
    review_state.collaboration.current_slice = "MP-355"
    review_state.current_session.current_instruction = ""
    review_state.coordination = SimpleNamespace(
        current_slice="Use the latest typed packet summary as the live slice."
    )

    snapshot = build_coordination_snapshot(
        repo_root=tmp_path,
        startup_context=startup,
        review_state=review_state,
    )

    assert snapshot.current_slice == (
        "Use the latest typed packet summary as the live slice."
    )


def test_build_coordination_snapshot_uses_provided_review_state_without_refresh(
    tmp_path: Path,
) -> None:
    startup = _startup_context(
        repo_root=tmp_path,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="single_agent",
            authority_mode="self_directed",
            work_ownership_mode="exclusive_slice",
            sync_cadence_mode="before_publish",
            active_participant_count=1,
            active_participants=("claude:implementer",),
        ),
    )
    review_state = _review_state(
        topology_mode="single_agent",
        participants=(),
        delegated_work=(),
        ready_gates=(),
        attention_status="clear",
        reviewer_freshness="fresh",
        registry_agents=(),
    )

    with patch(
        "dev.scripts.devctl.platform.coordination_snapshot.load_current_review_state",
        side_effect=AssertionError("should not refresh review state"),
    ):
        snapshot = build_coordination_snapshot(
            repo_root=tmp_path,
            startup_context=startup,
            review_state=review_state,
        )

    assert snapshot.current_slice == "Tighten startup coordination"


def test_build_coordination_snapshot_falls_back_to_continuity_next_action(
    tmp_path: Path,
) -> None:
    startup = _startup_context(
        repo_root=tmp_path,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="single_agent",
            authority_mode="self_directed",
            work_ownership_mode="exclusive_slice",
            sync_cadence_mode="before_publish",
            active_participant_count=1,
            active_participants=("claude:implementer",),
        ),
        continuity=SimpleNamespace(
            current_goal="",
            next_action="Show reviewer/coder state in remote control.",
            summary="",
        ),
    )
    review_state = _review_state(
        topology_mode="single_agent",
        participants=(),
        delegated_work=(),
        ready_gates=(),
        attention_status="inactive",
        reviewer_freshness="overdue",
        registry_agents=(),
    )
    review_state.collaboration.current_slice = ""
    review_state.current_session.current_instruction = ""

    snapshot = build_coordination_snapshot(
        repo_root=tmp_path,
        startup_context=startup,
        review_state=review_state,
    )

    assert snapshot.current_slice == "Show reviewer/coder state in remote control."


def test_build_coordination_snapshot_prefers_continuity_over_scope_only_slice(
    tmp_path: Path,
) -> None:
    startup = _startup_context(
        repo_root=tmp_path,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="single_agent",
            authority_mode="self_directed",
            work_ownership_mode="exclusive_slice",
            sync_cadence_mode="before_publish",
            active_participant_count=1,
            active_participants=("codex:reviewer",),
        ),
        continuity=SimpleNamespace(
            current_goal="",
            next_action="Use the live typed startup action instead of a bare MP scope token.",
            summary="",
        ),
    )
    review_state = _review_state(
        topology_mode="single_agent",
        participants=(),
        delegated_work=(),
        ready_gates=(),
        attention_status="inactive",
        reviewer_freshness="overdue",
        registry_agents=(),
    )
    review_state.collaboration.current_slice = "MP-355"
    review_state.current_session.current_instruction = ""
    review_state.coordination = SimpleNamespace(current_slice="MP-355")

    snapshot = build_coordination_snapshot(
        repo_root=tmp_path,
        startup_context=startup,
        review_state=review_state,
    )

    assert snapshot.current_slice == (
        "Use the live typed startup action instead of a bare MP scope token."
    )


def test_build_coordination_snapshot_falls_back_to_active_target_title(
    tmp_path: Path,
) -> None:
    startup = _startup_context(
        repo_root=tmp_path,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="single_agent",
            authority_mode="self_directed",
            work_ownership_mode="exclusive_slice",
            sync_cadence_mode="before_publish",
            active_participant_count=1,
            active_participants=("claude:implementer",),
        ),
        continuity=SimpleNamespace(current_goal="", next_action="", summary=""),
        active_target=PlanTargetRef(
            target_id="plan-target-2",
            plan_path="dev/active/remote_control_runtime.md",
            plan_title="Remote Control Runtime Closure Plan",
            plan_scope="MP-380..MP-387",
            target_kind="plan_doc",
            anchor_ref="section:execution-checklist",
            expected_revision="rev-2",
        ),
    )
    review_state = _review_state(
        topology_mode="single_agent",
        participants=(),
        delegated_work=(),
        ready_gates=(),
        attention_status="inactive",
        reviewer_freshness="overdue",
        registry_agents=(),
    )
    review_state.collaboration.current_slice = ""
    review_state.current_session.current_instruction = ""

    snapshot = build_coordination_snapshot(
        repo_root=tmp_path,
        startup_context=startup,
        review_state=review_state,
    )

    assert snapshot.current_slice == "Remote Control Runtime Closure Plan"
