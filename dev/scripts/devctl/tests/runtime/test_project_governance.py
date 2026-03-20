"""Tests for the ProjectGovernance startup-authority contract."""

from __future__ import annotations

from dev.scripts.devctl.runtime.project_governance import (
    PROJECT_GOVERNANCE_CONTRACT_ID,
    PROJECT_GOVERNANCE_SCHEMA_VERSION,
    ArtifactRoots,
    BridgeConfig,
    BundleOverrides,
    EnabledChecks,
    MemoryRoots,
    PathRoots,
    PlanRegistryRoots,
    ProjectGovernance,
    RepoIdentity,
    RepoPackRef,
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
            "bridge_path": "code_audit.md",
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

    assert gov.artifact_roots.audit_root == "dev/reports/audits"
    assert gov.artifact_roots.review_root == "dev/reports/review_channel/latest"
    assert gov.artifact_roots.governance_log_root == "dev/reports/governance"
    assert gov.artifact_roots.probe_report_root == "dev/reports/probes/latest"

    assert gov.memory_roots.memory_root == ""
    assert gov.memory_roots.context_store_root == ""

    assert gov.bridge_config.bridge_mode == "single_agent"
    assert gov.bridge_config.bridge_path == "code_audit.md"
    assert gov.bridge_config.review_channel_path == "dev/active/review_channel.md"
    assert gov.bridge_config.bridge_active is False

    assert gov.enabled_checks.guard_ids == ()
    assert gov.enabled_checks.probe_ids == ()

    assert gov.bundle_overrides.overrides == {}

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
        plan_registry=PlanRegistryRoots(),
        artifact_roots=ArtifactRoots(),
        memory_roots=MemoryRoots(memory_root=".mem", context_store_root=".ctx"),
        bridge_config=BridgeConfig(bridge_active=True, bridge_mode="active_dual_agent"),
        enabled_checks=EnabledChecks(
            guard_ids=("g1", "g2"),
            probe_ids=("p1",),
        ),
        bundle_overrides=BundleOverrides(overrides={"docs": {"strict": True}}),
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
    assert restored.artifact_roots == original.artifact_roots
    assert restored.memory_roots == original.memory_roots
    assert restored.bridge_config == original.bridge_config
    assert restored.enabled_checks == original.enabled_checks
    assert restored.bundle_overrides.overrides == original.bundle_overrides.overrides
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
            "bridge_path": "code_audit.md",
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
        plan_registry=PlanRegistryRoots(),
        artifact_roots=ArtifactRoots(),
        memory_roots=MemoryRoots(),
        bridge_config=BridgeConfig(),
        enabled_checks=EnabledChecks(
            guard_ids=("g1", "g2"),
            probe_ids=("p1", "p2", "p3"),
        ),
        bundle_overrides=BundleOverrides(overrides={}),
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
