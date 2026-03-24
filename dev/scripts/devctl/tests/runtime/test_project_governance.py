"""Tests for the ProjectGovernance startup-authority contract."""

from __future__ import annotations

from dev.scripts.devctl.runtime.project_governance import (
    PROJECT_GOVERNANCE_CONTRACT_ID,
    PROJECT_GOVERNANCE_SCHEMA_VERSION,
    ArtifactRoots,
    BridgeConfig,
    BundleOverrides,
    DocBudget,
    DocPolicy,
    DocRegistry,
    DocRegistryEntry,
    EnabledChecks,
    MemoryRoots,
    PathRoots,
    PlanRegistry,
    PlanRegistryEntry,
    PlanRegistryRoots,
    ProjectGovernance,
    PushEnforcement,
    RepoIdentity,
    RepoPackRef,
    SessionResumeEntry,
    SessionResumeState,
    bridge_config_from_mapping,
    bundle_overrides_from_mapping,
    enabled_checks_from_mapping,
    project_governance_from_mapping,
    repo_identity_from_mapping,
)


def test_project_governance_from_mapping_normalizes_full_payload() -> None:
    payload: dict[str, object] = {
        "schema_version": 1,
        "contract_id": "ProjectGovernance",
        "repo_identity": {
            "repo_name": "codex-voice",
            "remote_url": "git@github.com:owner/codex-voice.git",
            "default_branch": "master",
            "current_branch": "develop",
        },
        "repo_pack": {
            "pack_id": "voiceterm",
            "pack_version": "2.1.0",
            "description": "VoiceTerm governance pack",
        },
        "path_roots": {
            "active_docs": "dev/active",
            "reports": "dev/reports",
            "scripts": "dev/scripts",
            "checks": "dev/scripts/checks",
            "workflows": ".github/workflows",
            "guides": "dev/guides",
            "config": "dev/config",
        },
        "plan_registry": {
            "registry_path": "dev/active/INDEX.md",
            "tracker_path": "dev/active/MASTER_PLAN.md",
            "index_path": "dev/active/INDEX.md",
            "entries": [
                {
                    "path": "dev/active/MASTER_PLAN.md",
                    "role": "tracker",
                    "authority": "canonical",
                    "scope": "all active MP execution state",
                    "when_agents_read": "always",
                    "title": "Master Plan",
                    "owner": "tooling/control plane",
                    "lifecycle": "active",
                    "has_execution_plan_contract": True,
                    "session_resume": {
                        "section_hash": "resume1234",
                        "summary": "Continue the authority loop slice.",
                        "current_goal": "Land the first startup intake packet.",
                        "next_action": "Run bundle.tooling and inspect failures.",
                        "entries": [
                            {
                                "text": "Land the first startup intake packet.",
                                "item_kind": "bullet",
                                "label": "Current goal",
                            }
                        ],
                    },
                }
            ],
        },
        "doc_policy": {
            "docs_authority_path": "AGENTS.md",
            "active_docs_root": "dev/active",
            "guides_root": "dev/guides",
            "governed_doc_roots": ["dev/active", "dev/guides"],
            "tracker_path": "dev/active/MASTER_PLAN.md",
            "index_path": "dev/active/INDEX.md",
            "bridge_path": "bridge.md",
            "allowed_doc_classes": ["tracker", "spec", "runbook", "guide"],
            "allowed_authorities": ["canonical", "mirrored in MASTER_PLAN"],
            "allowed_lifecycles": ["active", "complete", "draft"],
            "required_plan_sections": ["## Scope", "## Session Resume"],
            "budget_limits": [
                {"doc_class": "spec", "soft_limit": 1200, "hard_limit": 2000}
            ],
        },
        "doc_registry": {
            "docs_authority_path": "AGENTS.md",
            "index_path": "dev/active/INDEX.md",
            "tracker_path": "dev/active/MASTER_PLAN.md",
            "entries": [
                {
                    "path": "dev/active/MASTER_PLAN.md",
                    "doc_class": "tracker",
                    "authority": "canonical",
                    "lifecycle": "active",
                    "scope": "all active MP execution state",
                    "owner": "tooling/control plane",
                    "canonical_consumer": "all sessions",
                    "line_count": 4000,
                    "budget_status": "ok",
                    "budget_limit": 0,
                    "registry_managed": True,
                    "in_index": True,
                    "issues": [],
                }
            ],
        },
        "artifact_roots": {
            "audit_root": "dev/reports/audits",
            "review_root": "dev/reports/review_channel/latest",
            "governance_log_root": "dev/reports/governance",
            "probe_report_root": "dev/reports/probes/latest",
        },
        "memory_roots": {
            "memory_root": ".claude/memory",
            "context_store_root": "dev/context",
        },
        "bridge_config": {
            "bridge_mode": "active_dual_agent",
            "bridge_path": "bridge.md",
            "review_channel_path": "dev/active/review_channel.md",
            "bridge_active": True,
        },
        "enabled_checks": {
            "guard_ids": ["code_shape", "function_duplication", "docs_lint"],
            "probe_ids": ["concurrency", "design_smells"],
        },
        "bundle_overrides": {
            "overrides": {"runtime": {"timeout": 30}},
        },
        "push_enforcement": {
            "default_remote": "origin",
            "pre_push_hook_installed": True,
            "raw_git_push_guarded": True,
            "upstream_ref": "origin/feature/demo",
            "ahead_of_upstream_commits": 2,
            "dirty_path_count": 3,
            "untracked_path_count": 1,
            "max_dirty_paths_before_checkpoint": 12,
            "max_untracked_paths_before_checkpoint": 6,
            "checkpoint_required": False,
            "safe_to_continue_editing": True,
            "checkpoint_reason": "within_dirty_budget",
            "worktree_dirty": False,
            "push_ready": True,
            "recommended_action": "use_devctl_push",
        },
        "startup_order": ["bootstrap", "guards", "probes"],
        "docs_authority": "AGENTS.md",
        "workflow_profiles": ["ci", "release"],
        "command_routing_defaults": {"profile": "ci"},
    }

    gov = project_governance_from_mapping(payload)

    assert gov.schema_version == 1
    assert gov.contract_id == "ProjectGovernance"

    assert gov.repo_identity.repo_name == "codex-voice"
    assert gov.repo_identity.remote_url == "git@github.com:owner/codex-voice.git"
    assert gov.repo_identity.default_branch == "master"
    assert gov.repo_identity.current_branch == "develop"

    assert gov.repo_pack.pack_id == "voiceterm"
    assert gov.repo_pack.pack_version == "2.1.0"
    assert gov.repo_pack.description == "VoiceTerm governance pack"

    assert gov.path_roots.active_docs == "dev/active"
    assert gov.path_roots.checks == "dev/scripts/checks"
    assert gov.path_roots.workflows == ".github/workflows"

    assert gov.plan_registry.registry_path == "dev/active/INDEX.md"
    assert gov.plan_registry.tracker_path == "dev/active/MASTER_PLAN.md"
    assert len(gov.plan_registry.entries) == 1
    assert gov.plan_registry.entries[0].title == "Master Plan"
    assert gov.plan_registry.entries[0].has_execution_plan_contract is True
    assert gov.plan_registry.entries[0].session_resume is not None
    assert (
        gov.plan_registry.entries[0].session_resume.current_goal
        == "Land the first startup intake packet."
    )

    assert gov.doc_policy.docs_authority_path == "AGENTS.md"
    assert gov.doc_policy.governed_doc_roots == ("dev/active", "dev/guides")
    assert gov.doc_policy.allowed_doc_classes == (
        "tracker",
        "spec",
        "runbook",
        "guide",
    )
    assert gov.doc_policy.required_plan_sections == (
        "## Scope",
        "## Session Resume",
    )
    assert gov.doc_policy.budget_limits[0].hard_limit == 2000

    assert gov.doc_registry.docs_authority_path == "AGENTS.md"
    assert len(gov.doc_registry.entries) == 1
    assert gov.doc_registry.entries[0].doc_class == "tracker"
    assert gov.doc_registry.entries[0].registry_managed is True

    assert gov.artifact_roots.audit_root == "dev/reports/audits"
    assert gov.artifact_roots.probe_report_root == "dev/reports/probes/latest"

    assert gov.memory_roots.memory_root == ".claude/memory"
    assert gov.memory_roots.context_store_root == "dev/context"

    assert gov.bridge_config.bridge_mode == "active_dual_agent"
    assert gov.bridge_config.bridge_active is True

    assert gov.enabled_checks.guard_ids == (
        "code_shape",
        "function_duplication",
        "docs_lint",
    )
    assert gov.enabled_checks.probe_ids == ("concurrency", "design_smells")

    assert gov.bundle_overrides.overrides == {"runtime": {"timeout": 30}}
    assert gov.push_enforcement.raw_git_push_guarded is True
    assert gov.push_enforcement.ahead_of_upstream_commits == 2
    assert gov.push_enforcement.dirty_path_count == 3
    assert gov.push_enforcement.safe_to_continue_editing is True
    assert gov.push_enforcement.push_ready is True

    assert gov.startup_order == ("bootstrap", "guards", "probes")
    assert gov.docs_authority == "AGENTS.md"
    assert gov.workflow_profiles == ("ci", "release")
    assert gov.command_routing_defaults == {"profile": "ci"}


def test_project_governance_from_mapping_with_defaults() -> None:
    payload: dict[str, object] = {
        "repo_identity": {"repo_name": "my-repo"},
        "repo_pack": {"pack_id": "basic"},
    }

    gov = project_governance_from_mapping(payload)

    assert gov.schema_version == PROJECT_GOVERNANCE_SCHEMA_VERSION
    assert gov.contract_id == PROJECT_GOVERNANCE_CONTRACT_ID

    assert gov.repo_identity.repo_name == "my-repo"
    assert gov.repo_identity.remote_url == ""
    assert gov.repo_identity.default_branch == "main"
    assert gov.repo_identity.current_branch == ""

    assert gov.repo_pack.pack_id == "basic"
    assert gov.repo_pack.pack_version == ""
    assert gov.repo_pack.description == ""

    assert gov.path_roots.active_docs == "dev/active"
    assert gov.path_roots.reports == "dev/reports"
    assert gov.path_roots.scripts == "dev/scripts"
    assert gov.path_roots.checks == "dev/scripts/checks"
    assert gov.path_roots.workflows == ".github/workflows"
    assert gov.path_roots.guides == "dev/guides"
    assert gov.path_roots.config == "dev/config"

    assert gov.plan_registry.registry_path == "dev/active/INDEX.md"
    assert gov.plan_registry.tracker_path == "dev/active/MASTER_PLAN.md"
    assert gov.plan_registry.index_path == "dev/active/INDEX.md"
    assert gov.plan_registry.entries == ()

    assert gov.doc_policy.docs_authority_path == "AGENTS.md"
    assert gov.doc_policy.allowed_doc_classes == ()
    assert gov.doc_registry.entries == ()

    assert gov.artifact_roots.audit_root == "dev/reports/audits"
    assert gov.artifact_roots.review_root == "dev/reports/review_channel/latest"
    assert gov.artifact_roots.governance_log_root == "dev/reports/governance"
    assert gov.artifact_roots.probe_report_root == "dev/reports/probes/latest"

    assert gov.memory_roots.memory_root == ""
    assert gov.memory_roots.context_store_root == ""

    assert gov.bridge_config.bridge_mode == "single_agent"
    assert gov.bridge_config.bridge_path == "bridge.md"
    assert gov.bridge_config.review_channel_path == "dev/active/review_channel.md"
    assert gov.bridge_config.bridge_active is False

    assert gov.enabled_checks.guard_ids == ()
    assert gov.enabled_checks.probe_ids == ()

    assert gov.bundle_overrides.overrides == {}
    assert gov.push_enforcement == PushEnforcement()

    assert gov.startup_order == ()
    assert gov.docs_authority == ""
    assert gov.workflow_profiles == ()
    assert gov.command_routing_defaults is None


def test_project_governance_roundtrip() -> None:
    original = ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=RepoIdentity(
            repo_name="roundtrip-repo",
            remote_url="https://github.com/owner/roundtrip-repo.git",
            default_branch="main",
            current_branch="feature/x",
        ),
        repo_pack=RepoPackRef(
            pack_id="rt-pack",
            pack_version="1.0.0",
            description="roundtrip test pack",
        ),
        path_roots=PathRoots(),
        plan_registry=PlanRegistry(
            entries=(
                PlanRegistryEntry(
                    path="dev/active/MASTER_PLAN.md",
                    role="tracker",
                    authority="canonical",
                    scope="all active MP execution state",
                    when_agents_read="always",
                    title="Master Plan",
                    has_execution_plan_contract=True,
                    session_resume=SessionResumeState(
                        section_hash="resume1234",
                        summary="Continue the authority loop slice.",
                        current_goal="Land the first startup intake packet.",
                        next_action="Run bundle.tooling and inspect failures.",
                        entries=(
                            SessionResumeEntry(
                                text="Land the first startup intake packet.",
                                label="Current goal",
                            ),
                        ),
                    ),
                ),
            )
        ),
        artifact_roots=ArtifactRoots(),
        memory_roots=MemoryRoots(memory_root=".mem", context_store_root=".ctx"),
        bridge_config=BridgeConfig(bridge_active=True, bridge_mode="active_dual_agent"),
        enabled_checks=EnabledChecks(
            guard_ids=("g1", "g2"),
            probe_ids=("p1",),
        ),
        bundle_overrides=BundleOverrides(overrides={"docs": {"strict": True}}),
        doc_policy=DocPolicy(
            allowed_doc_classes=("tracker", "spec"),
            allowed_authorities=("canonical",),
            allowed_lifecycles=("active",),
            required_plan_sections=("## Scope", "## Session Resume"),
            budget_limits=(DocBudget(doc_class="spec", soft_limit=1200, hard_limit=2000),),
        ),
        doc_registry=DocRegistry(
            entries=(
                DocRegistryEntry(
                    path="dev/active/MASTER_PLAN.md",
                    doc_class="tracker",
                    authority="canonical",
                    lifecycle="active",
                    scope="all active MP execution state",
                    registry_managed=True,
                    in_index=True,
                ),
            )
        ),
        push_enforcement=PushEnforcement(
            default_remote="origin",
            raw_git_push_guarded=True,
            ahead_of_upstream_commits=1,
            dirty_path_count=2,
            checkpoint_reason="within_dirty_budget",
            push_ready=True,
        ),
        startup_order=("step_a", "step_b"),
        docs_authority="AGENTS.md",
        workflow_profiles=("ci", "nightly"),
        command_routing_defaults={"profile": "quick"},
    )

    payload = original.to_dict()
    restored = project_governance_from_mapping(payload)

    assert restored.schema_version == original.schema_version
    assert restored.contract_id == original.contract_id
    assert restored.repo_identity == original.repo_identity
    assert restored.repo_pack == original.repo_pack
    assert restored.path_roots == original.path_roots
    assert restored.plan_registry == original.plan_registry
    assert restored.doc_policy == original.doc_policy
    assert restored.doc_registry == original.doc_registry
    assert restored.artifact_roots == original.artifact_roots
    assert restored.memory_roots == original.memory_roots
    assert restored.bridge_config == original.bridge_config
    assert restored.enabled_checks == original.enabled_checks
    assert restored.bundle_overrides.overrides == original.bundle_overrides.overrides
    assert restored.push_enforcement == original.push_enforcement
    assert restored.startup_order == original.startup_order
    assert restored.docs_authority == original.docs_authority
    assert restored.workflow_profiles == original.workflow_profiles
    assert restored.command_routing_defaults == original.command_routing_defaults


def test_repo_identity_from_mapping_coerces_types() -> None:
    identity = repo_identity_from_mapping(
        {
            "repo_name": 42,
            "remote_url": 100,
            "default_branch": None,
            "current_branch": True,
        }
    )
    assert identity.repo_name == "42"
    assert identity.remote_url == "100"
    assert identity.default_branch == "main"
    assert identity.current_branch == "True"


def test_enabled_checks_from_mapping_filters_empty() -> None:
    checks = enabled_checks_from_mapping(
        {
            "guard_ids": ["code_shape", "", None, "docs_lint", ""],
            "probe_ids": [None, "", "concurrency"],
        }
    )
    assert checks.guard_ids == ("code_shape", "docs_lint")
    assert checks.probe_ids == ("concurrency",)


def test_bridge_config_from_mapping_coerces_bool() -> None:
    config = bridge_config_from_mapping(
        {
            "bridge_mode": "active_dual_agent",
            "bridge_path": "bridge.md",
            "review_channel_path": "dev/active/review_channel.md",
            "bridge_active": "true",
        }
    )
    assert config.bridge_active is True


def test_project_governance_schema_constants() -> None:
    assert PROJECT_GOVERNANCE_CONTRACT_ID == "ProjectGovernance"
    assert PROJECT_GOVERNANCE_SCHEMA_VERSION == 1


def test_bundle_overrides_from_mapping_handles_nested_dict() -> None:
    nested = {
        "overrides": {
            "runtime": {"timeout": 60, "retries": 3},
            "docs": {"strict": True, "sections": ["api", "guide"]},
        }
    }
    result = bundle_overrides_from_mapping(nested)
    assert result.overrides["runtime"] == {"timeout": 60, "retries": 3}
    assert result.overrides["docs"] == {"strict": True, "sections": ["api", "guide"]}


def test_project_governance_to_dict_converts_tuples_to_lists() -> None:
    gov = ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=RepoIdentity(repo_name="list-test"),
        repo_pack=RepoPackRef(pack_id="lp"),
        path_roots=PathRoots(),
        plan_registry=PlanRegistry(
            entries=(
                PlanRegistryEntry(
                    path="dev/active/MASTER_PLAN.md",
                    role="tracker",
                    authority="canonical",
                    scope="all active MP execution state",
                    when_agents_read="always",
                    title="Master Plan",
                ),
            )
        ),
        artifact_roots=ArtifactRoots(),
        memory_roots=MemoryRoots(),
        bridge_config=BridgeConfig(),
        enabled_checks=EnabledChecks(
            guard_ids=("g1", "g2"),
            probe_ids=("p1", "p2", "p3"),
        ),
        bundle_overrides=BundleOverrides(overrides={}),
        doc_policy=DocPolicy(
            allowed_doc_classes=("tracker", "spec"),
            allowed_authorities=("canonical", "mirrored in MASTER_PLAN"),
            allowed_lifecycles=("active", "complete"),
            required_plan_sections=("## Scope", "## Session Resume"),
            budget_limits=(DocBudget(doc_class="spec", soft_limit=1200, hard_limit=2000),),
        ),
        doc_registry=DocRegistry(
            entries=(
                DocRegistryEntry(
                    path="dev/active/MASTER_PLAN.md",
                    doc_class="tracker",
                    authority="canonical",
                    lifecycle="active",
                    scope="all active MP execution state",
                    registry_managed=True,
                    in_index=True,
                ),
            )
        ),
        push_enforcement=PushEnforcement(
            default_remote="origin",
            dirty_path_count=14,
            checkpoint_required=True,
            safe_to_continue_editing=False,
            checkpoint_reason="dirty_path_budget_exceeded",
            recommended_action="use_devctl_push",
        ),
        startup_order=("alpha", "beta"),
        workflow_profiles=("ci", "release"),
    )

    d = gov.to_dict()

    assert isinstance(d["startup_order"], list)
    assert d["startup_order"] == ["alpha", "beta"]

    assert isinstance(d["workflow_profiles"], list)
    assert d["workflow_profiles"] == ["ci", "release"]

    assert isinstance(d["enabled_checks"]["guard_ids"], list)
    assert d["enabled_checks"]["guard_ids"] == ["g1", "g2"]

    assert isinstance(d["enabled_checks"]["probe_ids"], list)
    assert d["enabled_checks"]["probe_ids"] == ["p1", "p2", "p3"]
    assert isinstance(d["plan_registry"]["entries"], list)
    assert d["plan_registry"]["entries"][0]["title"] == "Master Plan"
    assert isinstance(d["doc_policy"]["allowed_doc_classes"], list)
    assert d["doc_policy"]["budget_limits"][0]["hard_limit"] == 2000
    assert isinstance(d["doc_registry"]["entries"], list)
    assert d["doc_registry"]["entries"][0]["doc_class"] == "tracker"
    assert d["push_enforcement"]["default_remote"] == "origin"
    assert d["push_enforcement"]["dirty_path_count"] == 14
    assert d["push_enforcement"]["checkpoint_required"] is True
    assert d["push_enforcement"]["recommended_action"] == "use_devctl_push"


def test_project_governance_to_dict_omits_empty_memory_roots() -> None:
    gov = ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=RepoIdentity(repo_name="memory-test"),
        repo_pack=RepoPackRef(pack_id="lp"),
        path_roots=PathRoots(),
        plan_registry=PlanRegistry(),
        artifact_roots=ArtifactRoots(),
        memory_roots=MemoryRoots(),
        bridge_config=BridgeConfig(),
        enabled_checks=EnabledChecks(),
        bundle_overrides=BundleOverrides(overrides={}),
    )

    payload = gov.to_dict()

    assert "memory_roots" not in payload
