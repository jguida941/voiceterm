"""Focused tests for startup work-intake routing."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from dev.scripts.devctl.context_graph.snapshot_payload import (
    ContextGraphSnapshot,
    TemperatureDistributionSummary,
)
from dev.scripts.devctl.governance.draft import scan_repo_governance
from dev.scripts.devctl.platform.planning_ir_models import (
    NextBestSliceRecord,
    PlanningIRSnapshot,
)
from dev.scripts.devctl.runtime.project_governance import (
    PROJECT_GOVERNANCE_CONTRACT_ID,
    PROJECT_GOVERNANCE_SCHEMA_VERSION,
    ArtifactRoots,
    BridgeConfig,
    BundleOverrides,
    DocPolicy,
    DocRegistry,
    DocRegistryEntry,
    EnabledChecks,
    MemoryRoots,
    PathRoots,
    PlanRegistry,
    PlanRegistryEntry,
    ProjectGovernance,
    PushEnforcement,
    RepoIdentity,
    RepoPackRef,
    SessionResumeEntry,
    SessionResumeState,
)
from dev.scripts.devctl.runtime.work_intake import (
    WorkIntakeStateInputs,
    build_work_intake_packet,
)
from dev.scripts.devctl.runtime.work_intake_models import (
    PlanTargetRef,
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
)
from dev.scripts.devctl.runtime.work_intake_selection import build_target_ref


def _mock_governance_subprocess_run(*_args, **_kwargs):
    class _FakeResult:
        returncode = 1
        stdout = ""

    return _FakeResult()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _init_git_repo(path: Path) -> None:
    subprocess.run(
        ["git", "init", "-q"],
        cwd=path,
        check=True,
    )


def _commit_repo_snapshot(path: Path, *, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Tests",
            "-c",
            "user.email=tests@example.com",
            "commit",
            "-q",
            "-m",
            message,
        ],
        cwd=path,
        check=True,
    )


def _governance(
    *,
    review_root: str = "dev/reports/review_channel/latest",
    include_shared_backlog: bool = False,
    include_system_map: bool = False,
) -> ProjectGovernance:
    tracker_entry = PlanRegistryEntry(
        path="dev/active/MASTER_PLAN.md",
        role="tracker",
        authority="canonical",
        scope="all active MP execution state",
        when_agents_read="always",
        artifact_role="execution_tracker",
        authority_kind="startup_authority",
        system_scope="platform_core",
        consumer_scope="startup_default",
        title="Master Plan",
        session_resume=SessionResumeState(
            section_hash="tracker1234",
            summary="Tracker fallback summary.",
            entries=(SessionResumeEntry(text="Tracker fallback summary."),),
        ),
    )
    authority_entry = PlanRegistryEntry(
        path="dev/active/platform_authority_loop.md",
        role="spec",
        authority="MP-377",
        scope="MP-377",
        when_agents_read="matching MP scope is in play",
        artifact_role="execution_plan",
        authority_kind="execution_authority",
        system_scope="platform_core",
        consumer_scope="startup_default",
        title="Platform Authority Loop",
        session_resume=SessionResumeState(
            section_hash="resume1234",
            summary="Land the first startup intake packet.",
            current_goal="Land the first startup intake packet.",
            next_action="Run bundle.tooling and inspect failures.",
            entries=(
                SessionResumeEntry(
                    text="Land the first startup intake packet.",
                    label="Current goal",
                ),
                SessionResumeEntry(
                    text="Run bundle.tooling and inspect failures.",
                    label="Next action",
                ),
            ),
        ),
    )
    doc_registry_entries = [
        DocRegistryEntry(
            path="AGENTS.md",
            doc_class="guide",
            authority="canonical",
            lifecycle="active",
            scope="startup contract",
            artifact_role="docs_authority",
            authority_kind="startup_authority",
            system_scope="development_self_hosting",
            consumer_scope="startup_default",
        ),
        DocRegistryEntry(
            path="dev/active/INDEX.md",
            doc_class="reference",
            authority="canonical",
            lifecycle="active",
            scope="plan registry",
            artifact_role="plan_registry",
            authority_kind="startup_authority",
            system_scope="platform_core",
            consumer_scope="startup_default",
        ),
        DocRegistryEntry(
            path="dev/active/MASTER_PLAN.md",
            doc_class="tracker",
            authority="canonical",
            lifecycle="active",
            scope="all active MP execution state",
            artifact_role="execution_tracker",
            authority_kind="startup_authority",
            system_scope="platform_core",
            consumer_scope="startup_default",
        ),
        DocRegistryEntry(
            path="dev/active/platform_authority_loop.md",
            doc_class="spec",
            authority="mirrored in MASTER_PLAN",
            lifecycle="active",
            scope="MP-377",
            artifact_role="execution_plan",
            authority_kind="execution_authority",
            system_scope="platform_core",
            consumer_scope="startup_default",
        ),
        DocRegistryEntry(
            path="bridge.md",
            doc_class="generated_report",
            authority="reference-only",
            lifecycle="active",
            scope="review compatibility",
            artifact_role="compatibility_projection",
            authority_kind="compatibility_only",
            system_scope="repo_pack_client",
            consumer_scope="review_runtime",
        ),
    ]
    startup_order = [
        "AGENTS.md",
        "dev/active/INDEX.md",
        "dev/active/MASTER_PLAN.md",
    ]
    if include_shared_backlog:
        doc_registry_entries.append(
            DocRegistryEntry(
                path="backlog.md",
                doc_class="reference",
                authority="reference-only",
                lifecycle="active",
                scope="shared repo backlog",
                artifact_role="shared_backlog",
                authority_kind="shared_intake",
                system_scope="repo_local",
                consumer_scope="startup_default",
            )
        )
        startup_order.append("backlog.md")
    if include_system_map:
        doc_registry_entries.append(
            DocRegistryEntry(
                path="dev/guides/SYSTEM_MAP.md",
                doc_class="guide",
                authority="reference-only",
                lifecycle="active",
                scope="connectivity index",
                artifact_role="connectivity_index",
                authority_kind="generated_navigation",
                system_scope="platform_core",
                consumer_scope="startup_default",
            )
        )

    return ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=RepoIdentity(
            repo_name="codex-voice",
            current_branch="feature/demo",
        ),
        repo_pack=RepoPackRef(pack_id="voiceterm"),
        path_roots=PathRoots(),
        plan_registry=PlanRegistry(
            tracker_path="dev/active/MASTER_PLAN.md",
            index_path="dev/active/INDEX.md",
            entries=(tracker_entry, authority_entry),
        ),
        doc_policy=DocPolicy(
            docs_authority_path="AGENTS.md",
            tracker_path="dev/active/MASTER_PLAN.md",
            index_path="dev/active/INDEX.md",
        ),
        doc_registry=DocRegistry(entries=tuple(doc_registry_entries)),
        artifact_roots=ArtifactRoots(review_root=review_root),
        memory_roots=MemoryRoots(),
        bridge_config=BridgeConfig(
            bridge_mode="active_dual_agent",
            bridge_path="bridge.md",
            bridge_active=True,
        ),
        enabled_checks=EnabledChecks(),
        bundle_overrides=BundleOverrides(overrides={}),
        push_enforcement=PushEnforcement(upstream_ref="origin/feature/demo"),
        startup_order=tuple(startup_order),
        docs_authority="AGENTS.md",
        workflow_profiles=("bundle.bootstrap", "bundle.tooling", "bundle.post-push"),
        command_routing_defaults={
            "push": {
                "default_remote": "origin",
                "development_branch": "develop",
                "release_branch": "master",
                "preflight": {
                    "command": "check-router",
                    "since_ref_template": "{remote}/{development_branch}",
                    "execute": True,
                },
                "post_push": {"bundle": "bundle.post-push"},
                "bypass": {
                    "allow_skip_preflight": False,
                    "allow_skip_post_push": False,
                },
            }
        },
    )


@patch(
    "dev.scripts.devctl.governance.draft.subprocess.run",
    _mock_governance_subprocess_run,
)
def test_build_target_ref_uses_persisted_plan_registry_artifact(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "# Master Plan\n")
    _write(tmp_path / "dev/reports/.keep", "")

    governance = scan_repo_governance(tmp_path, policy={})
    tracker_entry = next(
        entry
        for entry in governance.plan_registry.entries
        if entry.path == "dev/active/MASTER_PLAN.md"
    )

    with patch(
        "dev.scripts.devctl.runtime.work_intake_selection._file_revision",
        side_effect=AssertionError(
            "persisted target ref should avoid rereading markdown"
        ),
    ):
        target = build_target_ref(
            tmp_path,
            tracker_entry,
            reports_root=governance.path_roots.reports,
        )

    assert target is not None
    assert target.plan_path == tracker_entry.path
    assert target.plan_title == tracker_entry.title


def test_build_work_intake_packet_prefers_mp_scoped_spec_and_reconciles_review_state(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "bridge.md", "# Bridge\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "# Tracker\n")
    _write(tmp_path / "dev/active/platform_authority_loop.md", "# Authority Loop\n")
    _write(
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json",
        json.dumps(
            {
                "bridge": {"reviewer_mode": "active_dual_agent"},
                "review": {"plan_id": "MP-377"},
                "current_session": {
                    "last_reviewed_scope": "MP-377",
                    "current_instruction": "Run bundle.tooling and inspect failures.",
                    "open_findings": "none",
                    "implementer_status": "coding",
                    "implementer_ack_state": "current",
                },
            }
        ),
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.active_target is not None
    assert packet.active_target.plan_path == "dev/active/platform_authority_loop.md"
    assert packet.continuity.alignment_status == "aligned"
    assert packet.routing.selected_workflow_profile == "bundle.tooling"
    assert "bundle.tooling" in packet.routing.rule_summary
    assert packet.routing.match_evidence
    assert packet.routing.rejected_rule_traces
    assert (
        packet.routing.preflight_command
        == "python3 dev/scripts/devctl.py check-router --since-ref origin/feature/demo --execute --keep-going"
    )
    assert packet.writeback_sinks == (
        "dev/active/platform_authority_loop.md",
        "dev/active/MASTER_PLAN.md",
    )
    assert "AGENTS.md" in packet.warm_refs
    assert "dev/reports/review_channel/projections/latest/review_state.json" in packet.warm_refs
    assert "bridge.md" not in packet.warm_refs


def test_build_work_intake_packet_includes_connectivity_index_warm_ref(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "# Tracker\n")
    _write(tmp_path / "dev/guides/SYSTEM_MAP.md", "# SYSTEM_MAP\n")

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(include_system_map=True),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert "dev/guides/SYSTEM_MAP.md" in packet.warm_refs


def test_build_work_intake_packet_falls_back_to_tracker_without_review_state(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "# Tracker\n")

    governance = _governance()
    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=governance,
        advisory_action="checkpoint_allowed",
        advisory_reason="worktree_dirty_within_budget",
    )

    assert packet.active_target is not None
    assert packet.active_target.plan_path == "dev/active/MASTER_PLAN.md"
    assert packet.continuity.alignment_status == "plan_only"
    assert packet.confidence == "medium"
    assert packet.fallback_reason == "no_review_state"


def test_build_work_intake_packet_uses_resolved_review_state_candidate_for_warm_refs(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "bridge.md", "# Bridge\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "# Tracker\n")
    _write(tmp_path / "dev/active/platform_authority_loop.md", "# Authority Loop\n")
    _write(
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json",
        json.dumps(
            {
                "bridge": {"reviewer_mode": "active_dual_agent"},
                "review": {"plan_id": "MP-377"},
                "current_session": {
                    "last_reviewed_scope": "MP-377",
                    "current_instruction": "Run bundle.tooling and inspect failures.",
                    "open_findings": "none",
                    "implementer_status": "coding",
                    "implementer_ack_state": "current",
                },
            }
        ),
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(
            review_root="dev/reports/review_channel/projections/latest",
        ),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert (
        "dev/reports/review_channel/projections/latest/review_state.json"
        in packet.warm_refs
    )
    assert "bridge.md" not in packet.warm_refs


def test_build_work_intake_packet_uses_develop_base_for_dirty_worktree_preflight(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "bridge.md", "# Bridge\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "# Tracker\n")
    _write(tmp_path / "dev/active/platform_authority_loop.md", "# Authority Loop\n")
    _write(
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json",
        json.dumps(
            {
                "bridge": {"reviewer_mode": "active_dual_agent"},
                "review": {"plan_id": "MP-377"},
                "current_session": {
                    "last_reviewed_scope": "MP-377",
                    "current_instruction": "Run bundle.tooling and inspect failures.",
                    "open_findings": "none",
                    "implementer_status": "coding",
                    "implementer_ack_state": "current",
                },
            }
        ),
    )

    base = _governance()
    governance = ProjectGovernance(
        schema_version=base.schema_version,
        contract_id=base.contract_id,
        repo_identity=base.repo_identity,
        repo_pack=base.repo_pack,
        path_roots=base.path_roots,
        plan_registry=base.plan_registry,
        doc_policy=base.doc_policy,
        doc_registry=base.doc_registry,
        artifact_roots=base.artifact_roots,
        memory_roots=base.memory_roots,
        bridge_config=base.bridge_config,
        enabled_checks=base.enabled_checks,
        bundle_overrides=base.bundle_overrides,
        push_enforcement=PushEnforcement(
            default_remote="origin",
            development_branch="develop",
            release_branch="master",
            upstream_ref="origin/feature/demo",
            checkpoint_required=True,
            safe_to_continue_editing=False,
            checkpoint_reason="dirty_and_untracked_budget_exceeded",
            worktree_dirty=True,
            worktree_clean=False,
        ),
        startup_order=base.startup_order,
        docs_authority=base.docs_authority,
        workflow_profiles=base.workflow_profiles,
        command_routing_defaults=base.command_routing_defaults,
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=governance,
        advisory_action="checkpoint_before_continue",
        advisory_reason="dirty_and_untracked_budget_exceeded",
    )

    assert (
        packet.routing.preflight_command
        == "python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute --keep-going"
    )


def test_build_work_intake_packet_suppresses_lane_specific_plan_refs_from_default_warm_refs(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "bridge.md", "# Bridge\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "# Tracker\n")
    _write(tmp_path / "dev/active/review_channel.md", "# Review Channel\n")
    _write(
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json",
        json.dumps(
            {
                "bridge": {"reviewer_mode": "active_dual_agent"},
                "review": {"plan_id": "MP-355"},
                "current_session": {
                    "last_reviewed_scope": "MP-355",
                    "current_instruction": "Stay on the current review channel slice.",
                    "open_findings": "none",
                    "implementer_status": "coding",
                    "implementer_ack_state": "current",
                },
            }
        ),
    )

    base = _governance()
    review_entry = PlanRegistryEntry(
        path="dev/active/review_channel.md",
        role="spec",
        authority="mirrored in MASTER_PLAN",
        scope="MP-355",
        when_agents_read="when review-channel work is in scope",
        artifact_role="execution_plan",
        authority_kind="execution_authority",
        system_scope="repo_pack_client",
        consumer_scope="lane_specific",
        title="Review Channel",
        session_resume=SessionResumeState(
            section_hash="review355",
            summary="Current review-channel follow-up.",
            entries=(SessionResumeEntry(text="Current review-channel follow-up."),),
        ),
    )
    governance = ProjectGovernance(
        schema_version=base.schema_version,
        contract_id=base.contract_id,
        repo_identity=base.repo_identity,
        repo_pack=base.repo_pack,
        path_roots=base.path_roots,
        plan_registry=PlanRegistry(
            tracker_path=base.plan_registry.tracker_path,
            index_path=base.plan_registry.index_path,
            entries=(*base.plan_registry.entries, review_entry),
        ),
        artifact_roots=base.artifact_roots,
        memory_roots=base.memory_roots,
        bridge_config=base.bridge_config,
        enabled_checks=base.enabled_checks,
        bundle_overrides=base.bundle_overrides,
        doc_policy=base.doc_policy,
        doc_registry=DocRegistry(
            entries=(
                *base.doc_registry.entries,
                DocRegistryEntry(
                    path="dev/active/review_channel.md",
                    doc_class="spec",
                    authority="mirrored in MASTER_PLAN",
                    lifecycle="active",
                    scope="MP-355",
                    artifact_role="execution_plan",
                    authority_kind="execution_authority",
                    system_scope="repo_pack_client",
                    consumer_scope="lane_specific",
                ),
            )
        ),
        push_enforcement=base.push_enforcement,
        startup_order=base.startup_order,
        docs_authority=base.docs_authority,
        workflow_profiles=base.workflow_profiles,
        command_routing_defaults=base.command_routing_defaults,
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=governance,
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.active_target is not None
    assert packet.active_target.plan_path == "dev/active/review_channel.md"
    assert "dev/active/review_channel.md" not in packet.warm_refs
    assert "bridge.md" not in packet.warm_refs


def test_build_work_intake_packet_surfaces_shared_backlog_refs_and_sink(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "bridge.md", "# Bridge\n")
    _write(tmp_path / "backlog.md", "# Shared Backlog\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "# Tracker\n")
    _write(tmp_path / "dev/active/platform_authority_loop.md", "# Authority Loop\n")
    _write(
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json",
        json.dumps(
            {
                "bridge": {"reviewer_mode": "active_dual_agent"},
                "review": {"plan_id": "MP-377"},
                "current_session": {
                    "last_reviewed_scope": "MP-377",
                    "current_instruction": "Keep backlog and plan in sync.",
                    "open_findings": "none",
                    "implementer_status": "coding",
                    "implementer_ack_state": "current",
                },
            }
        ),
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(include_shared_backlog=True),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert "backlog.md" in packet.warm_refs
    assert packet.writeback_sinks == (
        "dev/active/platform_authority_loop.md",
        "dev/active/MASTER_PLAN.md",
        "backlog.md",
    )


def test_build_work_intake_packet_emits_session_pacing_from_planning_and_graph_evidence(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    governance = _governance()
    review_state = SimpleNamespace(
        current_session=SimpleNamespace(
            last_reviewed_scope="MP-377",
            current_instruction="Land the pacing packet.",
            open_findings="Q64",
            implementer_status="working",
        ),
        review=SimpleNamespace(plan_id=""),
        review_candidate=SimpleNamespace(
            scope_paths=("dev/scripts/devctl/runtime/work_intake.py",),
            changed_paths=("dev/scripts/devctl/runtime/work_intake.py",),
        ),
    )
    planning_snapshot = PlanningIRSnapshot(
        repo_name="codex-voice",
        repo_root=str(tmp_path),
        current_branch="feature/demo",
        active_target=PlanTargetRef(
            target_id="plan_target:test",
            plan_path="dev/active/platform_authority_loop.md",
            plan_title="Platform Authority Loop",
            plan_scope="MP-377",
            target_kind="plan_doc",
            anchor_ref="section:root",
            expected_revision="abc12345",
        ),
        next_best_slices=(
            NextBestSliceRecord(
                slice_id="slice:pacing",
                plan_path="dev/active/platform_authority_loop.md",
                plan_title="Platform Authority Loop",
                plan_scope="MP-377",
                file_paths=(
                    "dev/scripts/devctl/runtime/work_intake.py",
                    "dev/scripts/devctl/runtime/startup_context.py",
                ),
                hot_path_count=1,
                live_finding_count=2,
                summary="2 live findings and 1 hot path across the intake slice.",
            ),
        ),
    )
    graph_snapshot = ContextGraphSnapshot(
        schema_version=1,
        contract_id="ContextGraphSnapshot",
        repo="codex-voice",
        branch="feature/demo",
        commit_hash="head",
        generated_at_utc="2026-04-10T20:00:00Z",
        source_mode="bootstrap",
        node_count=3,
        edge_count=2,
        nodes_by_kind={"source_file": 3},
        edges_by_kind={"imports": 1, "calls": 1},
        temperature_distribution=TemperatureDistributionSummary(
            minimum=0.2,
            maximum=0.7,
            average=0.5,
            buckets={
                "0.00-0.24": 1,
                "0.25-0.49": 0,
                "0.50-0.74": 2,
                "0.75-1.00": 0,
            },
        ),
        nodes=[
            {
                "node_id": "src:work_intake",
                "node_kind": "source_file",
                "label": "work_intake.py",
                "canonical_pointer_ref": "dev/scripts/devctl/runtime/work_intake.py",
                "provenance_ref": "snapshot",
                "temperature": 0.7,
                "metadata": {},
            },
            {
                "node_id": "src:startup_context",
                "node_kind": "source_file",
                "label": "startup_context.py",
                "canonical_pointer_ref": "dev/scripts/devctl/runtime/startup_context.py",
                "provenance_ref": "snapshot",
                "temperature": 0.6,
                "metadata": {},
            },
            {
                "node_id": "src:planning_ir",
                "node_kind": "source_file",
                "label": "planning_ir.py",
                "canonical_pointer_ref": "dev/scripts/devctl/platform/planning_ir.py",
                "provenance_ref": "snapshot",
                "temperature": 0.55,
                "metadata": {},
            },
        ],
        edges=[
            {
                "source_id": "src:work_intake",
                "target_id": "src:planning_ir",
                "edge_kind": "imports",
            },
            {
                "source_id": "src:startup_context",
                "target_id": "src:planning_ir",
                "edge_kind": "calls",
            },
        ],
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=governance,
        advisory_action="continue_editing",
        advisory_reason="research_scope_ready",
        state_inputs=WorkIntakeStateInputs(
            review_state=review_state,
            ownership=WorkIntakeOwnershipState(status="clear"),
            coordination=WorkIntakeCoordinationState(
                collaboration_topology="single_agent",
                authority_mode="self_directed",
                work_ownership_mode="exclusive_slice",
                sync_cadence_mode="checkpointed",
            ),
            planning_snapshot=planning_snapshot,
            graph_snapshot=graph_snapshot,
        ),
    )

    assert packet.session_pacing.source == "state_inputs.current_graph_snapshot"
    assert packet.session_pacing.complexity_band == "high"
    assert packet.session_pacing.dependency_edge_count == 2
    assert packet.session_pacing.research_ref_budget == 7
    assert packet.session_pacing.authority_refs == (
        "dev/active/platform_authority_loop.md",
        "AGENTS.md",
        "dev/active/INDEX.md",
        "dev/active/MASTER_PLAN.md",
    )
    assert packet.session_pacing.implementation_refs == (
        "dev/scripts/devctl/runtime/work_intake.py",
        "dev/scripts/devctl/runtime/startup_context.py",
        "dev/scripts/devctl/platform/planning_ir.py",
    )


def test_build_work_intake_packet_projects_typed_plan_routing(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    _write(
        tmp_path / "dev/active/ai_governance_platform.md",
        "\n".join(
            (
                "# AI Governance Platform",
                "",
                "## Execution Checklist",
                "",
                "### Phase P0 - Findings Spine And Plan Authority",
                "Phase metadata: phase_id=MP377-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=in_progress; depends_on=none; summary=Collapse execution authority.",
                "- [ ] `MP377-P0-T01` Implement the canonical backlog reader/writer.",
                "      owner_doc: `dev/active/platform_authority_loop.md`",
                "      status: `in_progress`",
                "      depends_on: none",
                "- [ ] `MP377-P0-T02` Reduce the active execution-doc registry.",
                "      owner_doc: `dev/active/ai_governance_platform.md`",
                "      status: `pending`",
                "      depends_on: `MP377-P0-T01`",
            )
        ),
    )

    governance = _governance()
    umbrella_entry = PlanRegistryEntry(
        path="dev/active/ai_governance_platform.md",
        role="spec",
        authority="mirrored in MASTER_PLAN",
        scope="MP-377",
        when_agents_read="platform work",
        artifact_role="execution_plan",
        authority_kind="execution_authority",
        system_scope="platform_core",
        consumer_scope="startup_default",
        title="AI Governance Platform",
    )
    governance = replace(
        governance,
        plan_registry=replace(
            governance.plan_registry,
            entries=(
                governance.plan_registry.entries[0],
                umbrella_entry,
                governance.plan_registry.entries[1],
            ),
        ),
    )

    review_state = SimpleNamespace(
        current_session=SimpleNamespace(
            last_reviewed_scope="AI Governance Platform",
            current_instruction="continue AI Governance Platform",
            open_findings="F1",
            implementer_status="working",
        ),
        review=SimpleNamespace(plan_id="AI Governance Platform"),
        review_candidate=None,
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=governance,
        advisory_action="continue_editing",
        advisory_reason="research_scope_ready",
        state_inputs=WorkIntakeStateInputs(
            review_state=review_state,
            ownership=WorkIntakeOwnershipState(status="clear"),
            coordination=WorkIntakeCoordinationState(
                collaboration_topology="single_agent",
                authority_mode="self_directed",
                work_ownership_mode="exclusive_slice",
                sync_cadence_mode="checkpointed",
            ),
        ),
    )

    assert packet.active_target is not None
    assert packet.active_target.plan_path == "dev/active/ai_governance_platform.md"
    assert packet.plan_routing.phase_id == "MP377-P0"
    assert (
        packet.plan_routing.phase_owner_doc
        == "dev/active/ai_governance_platform.md"
    )
    assert packet.plan_routing.task_id == "MP377-P0-T01"
    assert (
        packet.plan_routing.task_owner_doc
        == "dev/active/platform_authority_loop.md"
    )
    assert packet.plan_routing.task_status == "in_progress"
    assert packet.plan_routing.dependencies == ()


def test_build_work_intake_packet_routes_plan_phase_from_pacing_focus_slice(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    _write(
        tmp_path / "dev/active/ai_governance_platform.md",
        "\n".join(
            (
                "# AI Governance Platform",
                "",
                "## Execution Checklist",
                "",
                "### Phase P0 - Findings Spine And Plan Authority",
                "Phase metadata: phase_id=MP377-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=in_progress; depends_on=none; summary=Collapse execution authority.",
                "- [ ] `MP377-P0-T01` Implement the canonical backlog reader/writer.",
                "      owner_doc: `dev/active/platform_authority_loop.md`",
                "      status: `in_progress`",
                "      depends_on: none",
            )
        ),
    )
    _write(tmp_path / "dev/active/review_channel.md", "# Review Channel\n")

    governance = _governance()
    umbrella_entry = PlanRegistryEntry(
        path="dev/active/ai_governance_platform.md",
        role="spec",
        authority="mirrored in MASTER_PLAN",
        scope="MP-377",
        when_agents_read="platform work",
        artifact_role="execution_plan",
        authority_kind="execution_authority",
        system_scope="platform_core",
        consumer_scope="startup_default",
        title="AI Governance Platform",
    )
    review_entry = PlanRegistryEntry(
        path="dev/active/review_channel.md",
        role="spec",
        authority="mirrored in MASTER_PLAN",
        scope="MP-355",
        when_agents_read="review channel work",
        artifact_role="execution_plan",
        authority_kind="execution_authority",
        system_scope="platform_core",
        consumer_scope="startup_default",
        title="Review Channel",
        session_resume=SessionResumeState(
            section_hash="review1234",
            summary="Resume review-channel continuity.",
            entries=(SessionResumeEntry(text="Resume review-channel continuity."),),
        ),
    )
    governance = replace(
        governance,
        plan_registry=replace(
            governance.plan_registry,
            entries=(
                governance.plan_registry.entries[0],
                governance.plan_registry.entries[1],
                umbrella_entry,
                review_entry,
            ),
        ),
    )

    review_state = SimpleNamespace(
        current_session=SimpleNamespace(
            last_reviewed_scope="MP-355",
            current_instruction="Continue the stale review-channel lane.",
            open_findings="F1",
            implementer_status="working",
        ),
        review=SimpleNamespace(plan_id="MP-355"),
        review_candidate=None,
    )
    planning_snapshot = PlanningIRSnapshot(
        repo_name="codex-voice",
        repo_root=str(tmp_path),
        current_branch="feature/demo",
        next_best_slices=(
            NextBestSliceRecord(
                slice_id="slice:platform",
                plan_path="dev/active/ai_governance_platform.md",
                plan_title="AI Governance Platform",
                plan_scope="MP-377",
                file_paths=("dev/scripts/devctl/runtime/work_intake.py",),
                hot_path_count=1,
                live_finding_count=2,
                summary="2 live findings and 1 hot path across the platform slice.",
            ),
        ),
    )
    graph_snapshot = ContextGraphSnapshot(
        schema_version=1,
        contract_id="ContextGraphSnapshot",
        repo="codex-voice",
        branch="feature/demo",
        commit_hash="head",
        generated_at_utc="2026-04-10T20:00:00Z",
        source_mode="bootstrap",
        node_count=1,
        edge_count=0,
        nodes_by_kind={"source_file": 1},
        edges_by_kind={},
        temperature_distribution=TemperatureDistributionSummary(
            minimum=0.5,
            maximum=0.5,
            average=0.5,
            buckets={
                "0.00-0.24": 0,
                "0.25-0.49": 0,
                "0.50-0.74": 1,
                "0.75-1.00": 0,
            },
        ),
        nodes=[
            {
                "node_id": "src:work_intake",
                "node_kind": "source_file",
                "label": "work_intake.py",
                "canonical_pointer_ref": "dev/scripts/devctl/runtime/work_intake.py",
                "provenance_ref": "snapshot",
                "temperature": 0.5,
                "metadata": {},
            },
        ],
        edges=[],
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=governance,
        advisory_action="continue_editing",
        advisory_reason="research_scope_ready",
        state_inputs=WorkIntakeStateInputs(
            review_state=review_state,
            ownership=WorkIntakeOwnershipState(status="clear"),
            coordination=WorkIntakeCoordinationState(
                collaboration_topology="single_agent",
                authority_mode="self_directed",
                work_ownership_mode="exclusive_slice",
                sync_cadence_mode="checkpointed",
            ),
            planning_snapshot=planning_snapshot,
            graph_snapshot=graph_snapshot,
        ),
    )

    assert packet.active_target is not None
    assert packet.active_target.plan_path == "dev/active/ai_governance_platform.md"
    assert packet.continuity.source_plan_path == "dev/active/ai_governance_platform.md"
    assert packet.session_pacing.focus_plan_path == "dev/active/ai_governance_platform.md"
    assert packet.plan_routing.phase_id == "MP377-P0"
    assert packet.plan_routing.task_id == "MP377-P0-T01"


def _seed_minimal_repo(tmp_path: Path) -> None:
    """Drop the standard plan/doc fixture into ``tmp_path``."""
    _init_git_repo(tmp_path)
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "bridge.md", "# Bridge\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "# Tracker\n")
    _write(tmp_path / "dev/active/platform_authority_loop.md", "# Authority Loop\n")
    _commit_repo_snapshot(tmp_path, message="seed repo")


def _write_review_state(
    tmp_path: Path,
    *,
    last_reviewed_scope: str,
    current_instruction: str,
    plan_id: str = "MP-377",
) -> None:
    """Drop a review_state.json projection with the requested resume fields."""
    _write(
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json",
        json.dumps(
            {
                "bridge": {"reviewer_mode": "active_dual_agent"},
                "review": {"plan_id": plan_id},
                "current_session": {
                    "last_reviewed_scope": last_reviewed_scope,
                    "current_instruction": current_instruction,
                    "open_findings": "none",
                    "implementer_status": "coding",
                    "implementer_ack_state": "current",
                },
            }
        ),
    )


def test_build_work_intake_packet_emits_scope_aligned_when_only_scope_matches(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    _write_review_state(
        tmp_path,
        last_reviewed_scope="MP-377",
        current_instruction="Chase an unrelated backlog item nobody has scoped yet.",
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.continuity.alignment_status == "scope_aligned"
    assert packet.continuity.alignment_reason == "review_scope_matches_plan_target"


def test_build_work_intake_packet_fails_closed_when_review_scope_uses_unresolved_plan_reference(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    # Scope deliberately points at an MP that is not in the plan registry.
    # Startup must not silently fall back to instruction heuristics when
    # review-state plan authority itself is unresolved.
    _write_review_state(
        tmp_path,
        last_reviewed_scope="MP-999",
        current_instruction="Run bundle tooling and inspect failures in detail.",
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.active_target is None
    assert packet.confidence == "low"
    assert packet.fallback_reason == "unresolved_review_plan_reference"
    assert packet.continuity.alignment_status == "needs_review"
    assert packet.continuity.alignment_reason == "unresolved_review_plan_reference"
    assert packet.continuity.unresolved_plan_references == ("MP-999",)


def test_build_work_intake_packet_emits_needs_review_when_neither_matches(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    _write_review_state(
        tmp_path,
        last_reviewed_scope="MP-999",
        current_instruction="Completely unrelated prose with no overlap whatsoever.",
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.active_target is None
    assert packet.continuity.alignment_status == "needs_review"
    assert packet.continuity.alignment_reason == "unresolved_review_plan_reference"
    assert packet.continuity.unresolved_plan_references == ("MP-999",)
    assert packet.fallback_reason == "unresolved_review_plan_reference"


def test_build_work_intake_packet_emits_review_only_when_session_resume_missing(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    _write_review_state(
        tmp_path,
        last_reviewed_scope="MP-377",
        current_instruction="Some instruction the reviewer cares about.",
        plan_id="MP-377",
    )

    # Strip session_resume off every plan entry so build_continuity sees a
    # typed-resolved plan target with no resume but a live review state.
    base = _governance()
    stripped_entries = tuple(
        PlanRegistryEntry(
            path=entry.path,
            role=entry.role,
            authority=entry.authority,
            scope=entry.scope,
            when_agents_read=entry.when_agents_read,
            artifact_role=entry.artifact_role,
            authority_kind=entry.authority_kind,
            system_scope=entry.system_scope,
            consumer_scope=entry.consumer_scope,
            title=entry.title,
            session_resume=None,
        )
        for entry in base.plan_registry.entries
    )
    governance = ProjectGovernance(
        schema_version=base.schema_version,
        contract_id=base.contract_id,
        repo_identity=base.repo_identity,
        repo_pack=base.repo_pack,
        path_roots=base.path_roots,
        plan_registry=PlanRegistry(
            tracker_path=base.plan_registry.tracker_path,
            index_path=base.plan_registry.index_path,
            entries=stripped_entries,
        ),
        doc_policy=base.doc_policy,
        doc_registry=base.doc_registry,
        artifact_roots=base.artifact_roots,
        memory_roots=base.memory_roots,
        bridge_config=base.bridge_config,
        enabled_checks=base.enabled_checks,
        bundle_overrides=base.bundle_overrides,
        push_enforcement=base.push_enforcement,
        startup_order=base.startup_order,
        docs_authority=base.docs_authority,
        workflow_profiles=base.workflow_profiles,
        command_routing_defaults=base.command_routing_defaults,
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=governance,
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.continuity.alignment_status == "review_only"
    assert packet.continuity.alignment_reason == "no_plan_session_resume"


def test_build_work_intake_packet_emits_missing_when_no_plan_or_review_state(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")

    # Empty plan registry: no plan target at all, and no review_state.json
    # projection on disk. This must land on the `missing` branch.
    base = _governance()
    governance = ProjectGovernance(
        schema_version=base.schema_version,
        contract_id=base.contract_id,
        repo_identity=base.repo_identity,
        repo_pack=base.repo_pack,
        path_roots=base.path_roots,
        plan_registry=PlanRegistry(
            tracker_path=base.plan_registry.tracker_path,
            index_path=base.plan_registry.index_path,
            entries=(),
        ),
        doc_policy=base.doc_policy,
        doc_registry=base.doc_registry,
        artifact_roots=base.artifact_roots,
        memory_roots=base.memory_roots,
        bridge_config=base.bridge_config,
        enabled_checks=base.enabled_checks,
        bundle_overrides=base.bundle_overrides,
        push_enforcement=base.push_enforcement,
        startup_order=base.startup_order,
        docs_authority=base.docs_authority,
        workflow_profiles=base.workflow_profiles,
        command_routing_defaults=base.command_routing_defaults,
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=governance,
        advisory_action="checkpoint_allowed",
        advisory_reason="clean_worktree",
    )

    assert packet.continuity.alignment_status == "missing"
    assert packet.continuity.alignment_reason == "no_plan_resume_or_review_state"


def test_build_continuity_does_not_falsely_match_mp3_to_mp377(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    # `MP-3` substring-leaks into `MP-377` under the old heuristic. The
    # token-aware gate must refuse that and fall out of `scope_aligned`.
    _write_review_state(
        tmp_path,
        last_reviewed_scope="MP-3",
        current_instruction="Completely unrelated instruction with no overlap.",
        plan_id="MP-3",
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.continuity.alignment_status != "scope_aligned"
    assert packet.continuity.alignment_status != "aligned"
    # MP-3 and MP-377 are disjoint MP tokens, and the instruction prose
    # shares no meaningful keywords, so the only admissible state is the
    # explicit mismatch branch.
    assert packet.continuity.alignment_status == "needs_review"


def test_build_work_intake_packet_handles_empty_review_state_as_plan_only(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    # Review state exists on disk but carries no scope or instruction text.
    # The old ladder collapsed this to `needs_review`; the fix re-routes it
    # to `plan_only` with an explicit `empty_review_state` reason.
    _write_review_state(
        tmp_path,
        last_reviewed_scope="   ",
        current_instruction="",
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.continuity.alignment_status == "plan_only"
    assert packet.continuity.alignment_reason == "empty_review_state"


def test_build_work_intake_packet_marks_in_scope_dirty_paths_when_claims_match(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    _write_review_state(
        tmp_path,
        last_reviewed_scope="MP-377",
        current_instruction=(
            "Stay on `dev/scripts/devctl/runtime/work_intake.py` and "
            "`dev/scripts/devctl/runtime/work_intake_models.py` only."
        ),
    )
    _write(tmp_path / "dev/scripts/devctl/runtime/work_intake.py", "# dirty\n")

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.ownership.status == "in_scope_dirty_paths"
    assert packet.ownership.dirty_paths == (
        "dev/scripts/devctl/runtime/work_intake.py",
    )
    assert packet.ownership.outside_scope_dirty_paths == ()


def test_build_work_intake_packet_marks_concurrent_writer_activity_for_outside_scope_dirty_paths(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    _write(
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json",
        json.dumps(
            {
                "bridge": {
                    "reviewer_mode": "active_dual_agent",
                    "effective_reviewer_mode": "active_dual_agent",
                },
                "review": {"plan_id": "MP-377"},
                "current_session": {
                    "last_reviewed_scope": "MP-377",
                    "current_instruction": (
                        "Stay on `dev/scripts/checks/platform_contract_closure/"
                        "field_routes_parity.py` and "
                        "`dev/scripts/checks/platform_contract_closure/"
                        "field_routes_parity_compare.py`."
                    ),
                    "open_findings": "none",
                    "implementer_status": "coding",
                    "implementer_ack_state": "current",
                },
                "collaboration": {
                    "participants": [
                        {
                            "agent_id": "codex",
                            "provider": "codex",
                            "role": "reviewer",
                            "live": True,
                            "status": "live",
                        },
                        {
                            "agent_id": "claude",
                            "provider": "claude",
                            "role": "implementer",
                            "live": True,
                            "status": "live",
                        },
                    ]
                },
            }
        ),
    )
    _write(
        tmp_path / "dev/scripts/devctl/review_channel/session_state_hints.py",
        "# unrelated dirty path\n",
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.ownership.status == "concurrent_writer_activity"
    assert packet.ownership.concurrent_writer_detected is True
    assert packet.ownership.outside_scope_dirty_paths == (
        "dev/scripts/devctl/review_channel/session_state_hints.py",
    )
    assert packet.ownership.live_agents == ("codex", "claude")
    assert packet.coordination.collaboration_topology == "dual_agent"
    assert packet.coordination.authority_mode == "reviewer_gated"
    assert packet.coordination.work_ownership_mode == "concurrent_writer_conflict"
    assert packet.coordination.sync_cadence_mode == "before_scope_change"
    assert packet.coordination.active_implementation_owner == "claude"
    assert packet.coordination.active_roles == ("reviewer", "implementer")
    assert packet.coordination.active_participants == (
        "codex:reviewer",
        "claude:implementer",
    )
    assert packet.coordination.resync_required is True


def test_build_work_intake_packet_marks_multi_agent_orchestrated_when_live_workers_exist(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    _write(
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json",
        json.dumps(
            {
                "bridge": {
                    "reviewer_mode": "active_dual_agent",
                    "effective_reviewer_mode": "active_dual_agent",
                },
                "review": {"plan_id": "MP-377"},
                "current_session": {
                    "last_reviewed_scope": "MP-377",
                    "current_instruction": (
                        "Stay on `dev/scripts/devctl/runtime/work_intake.py` only."
                    ),
                    "implementer_ack_state": "current",
                },
                "collaboration": {
                    "participants": [
                        {
                            "agent_id": "codex",
                            "provider": "codex",
                            "role": "reviewer",
                            "live": True,
                            "status": "live",
                        },
                        {
                            "agent_id": "claude",
                            "provider": "claude",
                            "role": "implementer",
                            "live": True,
                            "status": "live",
                        },
                    ],
                    "delegated_work": [
                        {
                            "receipt_id": "worker-1",
                            "agent_id": "codex-worker-1",
                            "provider": "codex",
                            "role": "implementer",
                            "owner_session": "codex",
                            "status": "live",
                            "live": True,
                            "lane": "AGENT-1",
                            "worktree": "../codex-voice-wt-a1",
                            "branch": "feature/a1",
                        }
                    ],
                },
            }
        ),
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.coordination.collaboration_topology == "multi_agent_orchestrated"
    assert packet.coordination.live_delegated_worker_count == 1
    assert packet.coordination.work_ownership_mode == "shared_slice"
    assert packet.coordination.active_implementation_owner == "claude"
    assert packet.coordination.delegated_agents == ("codex-worker-1",)
    assert packet.coordination.delegated_worktrees == ("../codex-voice-wt-a1",)
    assert packet.coordination.resync_required is False


def test_build_work_intake_packet_flags_duplicate_delegated_worktrees_before_dirty_overlap(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    _write(
        tmp_path / "dev/reports/review_channel/projections/latest/review_state.json",
        json.dumps(
            {
                "bridge": {
                    "reviewer_mode": "active_dual_agent",
                    "effective_reviewer_mode": "active_dual_agent",
                },
                "review": {"plan_id": "MP-377"},
                "current_session": {
                    "last_reviewed_scope": "MP-377",
                    "current_instruction": (
                        "Stay on `dev/scripts/devctl/runtime/work_intake.py` only."
                    ),
                    "implementer_ack_state": "current",
                },
                "collaboration": {
                    "participants": [
                        {
                            "agent_id": "codex",
                            "provider": "codex",
                            "role": "reviewer",
                            "live": True,
                            "status": "live",
                        },
                        {
                            "agent_id": "claude",
                            "provider": "claude",
                            "role": "implementer",
                            "live": True,
                            "status": "live",
                        },
                    ],
                    "delegated_work": [
                        {
                            "receipt_id": "worker-1",
                            "agent_id": "codex-worker-1",
                            "provider": "codex",
                            "role": "implementer",
                            "owner_session": "codex",
                            "status": "live",
                            "live": True,
                            "lane": "AGENT-1",
                            "worktree": "../codex-voice-wt-a1",
                            "branch": "feature/a1",
                        },
                        {
                            "receipt_id": "worker-2",
                            "agent_id": "claude-worker-1",
                            "provider": "claude",
                            "role": "implementer",
                            "owner_session": "claude",
                            "status": "live",
                            "live": True,
                            "lane": "AGENT-2",
                            "worktree": "../codex-voice-wt-a1",
                            "branch": "feature/a2",
                        },
                    ],
                },
            }
        ),
    )

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.coordination.collaboration_topology == "multi_agent_orchestrated"
    assert packet.coordination.work_ownership_mode == "concurrent_writer_conflict"
    assert packet.coordination.concurrent_writer_conflict_detected is True
    assert packet.coordination.duplicate_delegated_worktrees == (
        "../codex-voice-wt-a1",
    )


def test_build_work_intake_packet_marks_scope_unknown_when_dirty_paths_lack_file_claims(
    tmp_path: Path,
) -> None:
    _seed_minimal_repo(tmp_path)
    _write_review_state(
        tmp_path,
        last_reviewed_scope="MP-377",
        current_instruction="Keep working on the current lane.",
    )
    _write(tmp_path / "dev/scripts/devctl/runtime/work_intake.py", "# dirty\n")

    packet = build_work_intake_packet(
        repo_root=tmp_path,
        governance=_governance(),
        advisory_action="continue_editing",
        advisory_reason="clean_worktree",
    )

    assert packet.ownership.status == "scope_unknown_dirty_paths"
    assert packet.ownership.scope_paths == ()
