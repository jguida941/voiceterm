"""Typed startup-authority contract models for governed repositories."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .project_governance_push import PushEnforcement
from .session_resume import SessionResumeEntry, SessionResumeState

PROJECT_GOVERNANCE_CONTRACT_ID = "ProjectGovernance"
PROJECT_GOVERNANCE_SCHEMA_VERSION = 1


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
class DocBudget:
    """Line-budget policy for one governed doc class."""

    doc_class: str
    soft_limit: int = 0
    hard_limit: int = 0

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return payload


@dataclass(frozen=True, slots=True)
class DocPolicy:
    """Typed markdown-governance policy carried by ProjectGovernance."""

    docs_authority_path: str = "AGENTS.md"
    active_docs_root: str = "dev/active"
    guides_root: str = "dev/guides"
    governed_doc_roots: tuple[str, ...] = ()
    tracker_path: str = "dev/active/MASTER_PLAN.md"
    index_path: str = "dev/active/INDEX.md"
    bridge_path: str = "bridge.md"
    allowed_doc_classes: tuple[str, ...] = ()
    allowed_authorities: tuple[str, ...] = ()
    allowed_lifecycles: tuple[str, ...] = ()
    required_plan_sections: tuple[str, ...] = ()
    budget_limits: tuple[DocBudget, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["governed_doc_roots"] = list(self.governed_doc_roots)
        payload["allowed_doc_classes"] = list(self.allowed_doc_classes)
        payload["allowed_authorities"] = list(self.allowed_authorities)
        payload["allowed_lifecycles"] = list(self.allowed_lifecycles)
        payload["required_plan_sections"] = list(self.required_plan_sections)
        payload["budget_limits"] = [
            budget.to_dict() for budget in self.budget_limits
        ]
        return payload


@dataclass(frozen=True, slots=True)
class DocRegistryEntry:
    """One governed markdown document captured in the runtime doc registry."""

    path: str
    doc_class: str
    authority: str
    lifecycle: str
    scope: str
    owner: str = ""
    canonical_consumer: str = ""
    line_count: int = 0
    budget_status: str = "ok"
    budget_limit: int = 0
    registry_managed: bool = False
    in_index: bool = False
    issues: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["issues"] = list(self.issues)
        return payload


@dataclass(frozen=True, slots=True)
class DocRegistry:
    """Typed governed-doc registry used for bounded startup context."""

    docs_authority_path: str = "AGENTS.md"
    index_path: str = "dev/active/INDEX.md"
    tracker_path: str = "dev/active/MASTER_PLAN.md"
    entries: tuple[DocRegistryEntry, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["entries"] = [entry.to_dict() for entry in self.entries]
        return payload


@dataclass(frozen=True, slots=True)
class PlanRegistryEntry:
    """One mutable execution-plan doc captured in the runtime plan registry."""

    path: str
    role: str
    authority: str
    scope: str
    when_agents_read: str
    title: str = ""
    owner: str = ""
    lifecycle: str = "unknown"
    has_execution_plan_contract: bool = False
    session_resume: SessionResumeState | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if self.session_resume is None:
            payload.pop("session_resume", None)
        return payload


@dataclass(frozen=True, slots=True)
class PlanRegistry:
    """Typed plan-registry authority surfaces plus parsed plan entries."""

    registry_path: str = "dev/active/INDEX.md"
    tracker_path: str = "dev/active/MASTER_PLAN.md"
    index_path: str = "dev/active/INDEX.md"
    entries: tuple[PlanRegistryEntry, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["entries"] = [entry.to_dict() for entry in self.entries]
        return payload


PlanRegistryRoots = PlanRegistry


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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def configured(self) -> bool:
        return bool(self.memory_root or self.context_store_root)


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


@dataclass(frozen=True, slots=True)
class ProjectGovernance:
    """Canonical startup-authority contract for one governed repository."""

    schema_version: int
    contract_id: str
    repo_identity: RepoIdentity
    repo_pack: RepoPackRef
    path_roots: PathRoots
    plan_registry: PlanRegistry
    artifact_roots: ArtifactRoots
    memory_roots: MemoryRoots
    bridge_config: BridgeConfig
    enabled_checks: EnabledChecks
    bundle_overrides: BundleOverrides
    doc_policy: DocPolicy = field(default_factory=DocPolicy)
    doc_registry: DocRegistry = field(default_factory=DocRegistry)
    push_enforcement: PushEnforcement = field(default_factory=PushEnforcement)
    startup_order: tuple[str, ...] = ()
    docs_authority: str = ""
    workflow_profiles: tuple[str, ...] = ()
    command_routing_defaults: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["plan_registry"] = self.plan_registry.to_dict()
        if self.memory_roots.configured():
            payload["memory_roots"] = self.memory_roots.to_dict()
        else:
            payload.pop("memory_roots", None)
        payload["doc_policy"] = self.doc_policy.to_dict()
        payload["doc_registry"] = self.doc_registry.to_dict()
        payload["startup_order"] = list(self.startup_order)
        payload["workflow_profiles"] = list(self.workflow_profiles)
        payload["enabled_checks"]["guard_ids"] = list(
            self.enabled_checks.guard_ids
        )
        payload["enabled_checks"]["probe_ids"] = list(
            self.enabled_checks.probe_ids
        )
        return payload


__all__ = [
    "PROJECT_GOVERNANCE_CONTRACT_ID",
    "PROJECT_GOVERNANCE_SCHEMA_VERSION",
    "ArtifactRoots",
    "BridgeConfig",
    "BundleOverrides",
    "DocBudget",
    "DocPolicy",
    "DocRegistry",
    "DocRegistryEntry",
    "EnabledChecks",
    "MemoryRoots",
    "PathRoots",
    "PlanRegistry",
    "PlanRegistryEntry",
    "PlanRegistryRoots",
    "ProjectGovernance",
    "RepoIdentity",
    "RepoPackRef",
    "SessionResumeEntry",
    "SessionResumeState",
]
