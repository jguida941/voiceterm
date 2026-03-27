"""Focused tests for startup work-intake routing."""

from __future__ import annotations

import json
from pathlib import Path

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
from dev.scripts.devctl.runtime.work_intake import build_work_intake_packet


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _governance(
    *,
    review_root: str = "dev/reports/review_channel/latest",
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
        doc_registry=DocRegistry(
            entries=(
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
            )
        ),
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
        startup_order=("AGENTS.md", "dev/active/INDEX.md", "dev/active/MASTER_PLAN.md"),
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


def test_build_work_intake_packet_prefers_mp_scoped_spec_and_reconciles_review_state(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "AGENTS.md", "# Agents\n")
    _write(tmp_path / "bridge.md", "# Bridge\n")
    _write(tmp_path / "dev/active/INDEX.md", "# Index\n")
    _write(tmp_path / "dev/active/MASTER_PLAN.md", "# Tracker\n")
    _write(tmp_path / "dev/active/platform_authority_loop.md", "# Authority Loop\n")
    _write(
        tmp_path / "dev/reports/review_channel/latest/review_state.json",
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
        == "python3 dev/scripts/devctl.py check-router --since-ref origin/feature/demo --execute"
    )
    assert packet.writeback_sinks == (
        "dev/active/platform_authority_loop.md",
        "dev/active/MASTER_PLAN.md",
    )
    assert "AGENTS.md" in packet.warm_refs
    assert "dev/reports/review_channel/latest/review_state.json" in packet.warm_refs
    assert "bridge.md" not in packet.warm_refs


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
        tmp_path / "dev/reports/review_channel/latest/review_state.json",
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
        == "python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute"
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
        tmp_path / "dev/reports/review_channel/latest/review_state.json",
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
