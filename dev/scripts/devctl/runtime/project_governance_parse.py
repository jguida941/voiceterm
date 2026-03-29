"""Mapping helpers for the ProjectGovernance runtime contract."""

from __future__ import annotations

from collections.abc import Mapping

from .project_governance_contract import (
    PROJECT_GOVERNANCE_CONTRACT_ID,
    PROJECT_GOVERNANCE_SCHEMA_VERSION,
    ArtifactRoots,
    BridgeConfig,
    BundleOverrides,
    EnabledChecks,
    MemoryRoots,
    PathRoots,
    ProjectGovernance,
    RepoIdentity,
    RepoPackRef,
)
from .project_governance_doc_parse import (
    doc_budget_from_mapping,
    doc_policy_from_mapping,
    doc_registry_entry_from_mapping,
    doc_registry_from_mapping,
)
from .project_governance_plan_parse import (
    plan_registry_entry_from_mapping,
    plan_registry_from_mapping,
    plan_registry_roots_from_mapping,
)
from .project_governance_push import push_enforcement_from_mapping
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)


def repo_identity_from_mapping(
    payload: Mapping[str, object],
) -> RepoIdentity:
    name = coerce_string(payload.get("repo_name"))
    branch = coerce_string(payload.get("default_branch")) or "main"
    return RepoIdentity(
        repo_name=name,
        remote_url=coerce_string(payload.get("remote_url")),
        default_branch=branch,
        current_branch=coerce_string(payload.get("current_branch")),
    )


def repo_pack_ref_from_mapping(
    payload: Mapping[str, object],
) -> RepoPackRef:
    pack_id = coerce_string(payload.get("pack_id"))
    return RepoPackRef(
        pack_id=pack_id,
        pack_version=coerce_string(payload.get("pack_version")),
        description=coerce_string(payload.get("description")),
    )


def path_roots_from_mapping(
    payload: Mapping[str, object],
) -> PathRoots:
    return PathRoots(
        active_docs=coerce_string(payload.get("active_docs")),
        reports=coerce_string(payload.get("reports")),
        scripts=coerce_string(payload.get("scripts")),
        checks=coerce_string(payload.get("checks")),
        workflows=coerce_string(payload.get("workflows")),
        guides=coerce_string(payload.get("guides")),
        config=coerce_string(payload.get("config")),
    )


def artifact_roots_from_mapping(
    payload: Mapping[str, object],
) -> ArtifactRoots:
    return ArtifactRoots(
        audit_root=coerce_string(payload.get("audit_root")),
        review_root=coerce_string(payload.get("review_root")),
        governance_log_root=coerce_string(payload.get("governance_log_root")),
        probe_report_root=coerce_string(payload.get("probe_report_root")),
    )


def memory_roots_from_mapping(
    payload: Mapping[str, object],
) -> MemoryRoots:
    mem = coerce_string(payload.get("memory_root"))
    return MemoryRoots(
        memory_root=mem,
        context_store_root=coerce_string(payload.get("context_store_root")),
    )


def bridge_config_from_mapping(
    payload: Mapping[str, object],
) -> BridgeConfig:
    mode = coerce_string(payload.get("bridge_mode")) or "single_agent"
    return BridgeConfig(
        bridge_mode=mode,
        bridge_path=coerce_string(payload.get("bridge_path")),
        review_channel_path=coerce_string(payload.get("review_channel_path")),
        bridge_active=coerce_bool(payload.get("bridge_active")),
    )


def enabled_checks_from_mapping(
    payload: Mapping[str, object],
) -> EnabledChecks:
    guards = coerce_string_items(payload.get("guard_ids"))
    return EnabledChecks(
        guard_ids=guards,
        probe_ids=coerce_string_items(payload.get("probe_ids")),
    )


def bundle_overrides_from_mapping(
    payload: Mapping[str, object],
) -> BundleOverrides:
    raw = dict(coerce_mapping(payload.get("overrides")))
    return BundleOverrides(overrides=raw)


def project_governance_from_mapping(
    payload: Mapping[str, object],
) -> ProjectGovernance:
    """Parse a ProjectGovernance contract from a JSON-like mapping."""
    version = (
        coerce_int(payload.get("schema_version"))
        or PROJECT_GOVERNANCE_SCHEMA_VERSION
    )
    contract = (
        coerce_string(payload.get("contract_id"))
        or PROJECT_GOVERNANCE_CONTRACT_ID
    )
    return ProjectGovernance(
        schema_version=version,
        contract_id=contract,
        repo_identity=repo_identity_from_mapping(
            coerce_mapping(payload.get("repo_identity"))
        ),
        repo_pack=repo_pack_ref_from_mapping(
            coerce_mapping(payload.get("repo_pack"))
        ),
        path_roots=path_roots_from_mapping(
            coerce_mapping(payload.get("path_roots"))
        ),
        plan_registry=plan_registry_from_mapping(
            coerce_mapping(payload.get("plan_registry"))
        ),
        artifact_roots=artifact_roots_from_mapping(
            coerce_mapping(payload.get("artifact_roots"))
        ),
        memory_roots=memory_roots_from_mapping(
            coerce_mapping(payload.get("memory_roots"))
        ),
        bridge_config=bridge_config_from_mapping(
            coerce_mapping(payload.get("bridge_config"))
        ),
        enabled_checks=enabled_checks_from_mapping(
            coerce_mapping(payload.get("enabled_checks"))
        ),
        bundle_overrides=bundle_overrides_from_mapping(
            coerce_mapping(payload.get("bundle_overrides"))
        ),
        doc_policy=doc_policy_from_mapping(
            coerce_mapping(payload.get("doc_policy"))
        ),
        doc_registry=doc_registry_from_mapping(
            coerce_mapping(payload.get("doc_registry"))
        ),
        push_enforcement=push_enforcement_from_mapping(
            coerce_mapping(payload.get("push_enforcement"))
        ),
        startup_order=coerce_string_items(payload.get("startup_order")),
        docs_authority=coerce_string(payload.get("docs_authority")),
        workflow_profiles=coerce_string_items(
            payload.get("workflow_profiles")
        ),
        command_routing_defaults=dict(
            coerce_mapping(payload.get("command_routing_defaults"))
        )
        or None,
    )


__all__ = [
    "artifact_roots_from_mapping",
    "bridge_config_from_mapping",
    "bundle_overrides_from_mapping",
    "doc_budget_from_mapping",
    "doc_policy_from_mapping",
    "doc_registry_entry_from_mapping",
    "doc_registry_from_mapping",
    "enabled_checks_from_mapping",
    "memory_roots_from_mapping",
    "path_roots_from_mapping",
    "plan_registry_entry_from_mapping",
    "plan_registry_from_mapping",
    "plan_registry_roots_from_mapping",
    "project_governance_from_mapping",
    "repo_identity_from_mapping",
    "repo_pack_ref_from_mapping",
]
