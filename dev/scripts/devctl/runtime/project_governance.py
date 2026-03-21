"""Startup-authority contract for one governed repository.

ProjectGovernance is the canonical typed surface that describes how a repo
declares its governance identity, path layout, plan registry, artifact roots,
memory roots, bridge mode, enabled guards/probes, and bundle overrides. AI
agents, humans, and runtime startup surfaces all consume the same contract
instead of re-deriving this information from prose docs every session.

This module is Phase 1 / Slice A of MP-377 (platform authority loop).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)
from .project_governance_push import PushEnforcement, push_enforcement_from_mapping

PROJECT_GOVERNANCE_CONTRACT_ID = "ProjectGovernance"
PROJECT_GOVERNANCE_SCHEMA_VERSION = 1


# ── Nested records ──────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class RepoIdentity:
    """Stable identity for the governed repository."""

    repo_name: str
    remote_url: str = ""
    default_branch: str = "main"
    current_branch: str = ""


@dataclass(frozen=True, slots=True)
class RepoPackRef:
    """Reference to the repo-pack that configures this repository."""

    pack_id: str
    pack_version: str = ""
    description: str = ""


@dataclass(frozen=True, slots=True)
class PathRoots:
    """Repo-relative path roots for key directory families."""

    active_docs: str = "dev/active"
    reports: str = "dev/reports"
    scripts: str = "dev/scripts"
    checks: str = "dev/scripts/checks"
    workflows: str = ".github/workflows"
    guides: str = "dev/guides"
    config: str = "dev/config"


@dataclass(frozen=True, slots=True)
class PlanRegistryRoots:
    """Paths to plan-registry authority surfaces."""

    registry_path: str = "dev/active/INDEX.md"
    tracker_path: str = "dev/active/MASTER_PLAN.md"
    index_path: str = "dev/active/INDEX.md"


@dataclass(frozen=True, slots=True)
class ArtifactRoots:
    """Repo-relative roots for governance artifacts."""

    audit_root: str = "dev/reports/audits"
    review_root: str = "dev/reports/review_channel/latest"
    governance_log_root: str = "dev/reports/governance"
    probe_report_root: str = "dev/reports/probes/latest"


@dataclass(frozen=True, slots=True)
class MemoryRoots:
    """Repo-relative roots for memory and context stores."""

    memory_root: str = ""
    context_store_root: str = ""


@dataclass(frozen=True, slots=True)
class BridgeConfig:
    """Bridge/reviewer-mode configuration."""

    bridge_mode: str = "single_agent"
    bridge_path: str = "bridge.md"
    review_channel_path: str = "dev/active/review_channel.md"
    bridge_active: bool = False


@dataclass(frozen=True, slots=True)
class EnabledChecks:
    """Guard and probe IDs currently enabled by repo policy."""

    guard_ids: tuple[str, ...] = ()
    probe_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BundleOverrides:
    """Per-bundle configuration overrides from repo policy."""

    overrides: dict[str, object]


# ── Top-level contract ──────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ProjectGovernance:
    """Canonical startup-authority contract for one governed repository.

    Carries every field that runtime, startup, and AI-agent surfaces need to
    know about the repo's governance posture without re-reading prose docs.
    """

    schema_version: int
    contract_id: str
    repo_identity: RepoIdentity
    repo_pack: RepoPackRef
    path_roots: PathRoots
    plan_registry: PlanRegistryRoots
    artifact_roots: ArtifactRoots
    memory_roots: MemoryRoots
    bridge_config: BridgeConfig
    enabled_checks: EnabledChecks
    bundle_overrides: BundleOverrides
    push_enforcement: PushEnforcement = field(default_factory=PushEnforcement)
    startup_order: tuple[str, ...] = ()
    docs_authority: str = ""
    workflow_profiles: tuple[str, ...] = ()
    command_routing_defaults: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["startup_order"] = list(self.startup_order)
        d["workflow_profiles"] = list(self.workflow_profiles)
        d["enabled_checks"]["guard_ids"] = list(
            self.enabled_checks.guard_ids
        )
        d["enabled_checks"]["probe_ids"] = list(
            self.enabled_checks.probe_ids
        )
        return d


# ── Mapping helpers ─────────────────────────────────────────────────────


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
    active = coerce_string(payload.get("active_docs")) or "dev/active"
    return PathRoots(
        active_docs=active,
        reports=coerce_string(payload.get("reports")) or "dev/reports",
        scripts=coerce_string(payload.get("scripts")) or "dev/scripts",
        checks=coerce_string(payload.get("checks")) or "dev/scripts/checks",
        workflows=coerce_string(payload.get("workflows"))
        or ".github/workflows",
        guides=coerce_string(payload.get("guides")) or "dev/guides",
        config=coerce_string(payload.get("config")) or "dev/config",
    )


def plan_registry_roots_from_mapping(
    payload: Mapping[str, object],
) -> PlanRegistryRoots:
    registry = coerce_string(payload.get("registry_path")) or "dev/active/INDEX.md"
    return PlanRegistryRoots(
        registry_path=registry,
        tracker_path=coerce_string(payload.get("tracker_path"))
        or "dev/active/MASTER_PLAN.md",
        index_path=coerce_string(payload.get("index_path"))
        or "dev/active/INDEX.md",
    )


def artifact_roots_from_mapping(
    payload: Mapping[str, object],
) -> ArtifactRoots:
    audit = coerce_string(payload.get("audit_root")) or "dev/reports/audits"
    return ArtifactRoots(
        audit_root=audit,
        review_root=coerce_string(payload.get("review_root"))
        or "dev/reports/review_channel/latest",
        governance_log_root=coerce_string(
            payload.get("governance_log_root")
        )
        or "dev/reports/governance",
        probe_report_root=coerce_string(payload.get("probe_report_root"))
        or "dev/reports/probes/latest",
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
        bridge_path=coerce_string(payload.get("bridge_path"))
        or "bridge.md",
        review_channel_path=coerce_string(
            payload.get("review_channel_path")
        )
        or "dev/active/review_channel.md",
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
        plan_registry=plan_registry_roots_from_mapping(
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
