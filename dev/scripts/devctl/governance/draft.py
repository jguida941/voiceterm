"""Deterministic repo-scan helper that emits a ProjectGovernance payload."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .draft_governed_docs import (
    GovernedMarkdownScanInputs,
    scan_governed_markdown_contracts,
)
from .draft_policy_surface import scan_repo_pack_ref
from .draft_policy_scan import scan_governed_doc_discovery
from .draft_push import scan_command_routing_defaults, scan_push_enforcement
from ..runtime.project_governance import (
    PROJECT_GOVERNANCE_CONTRACT_ID,
    PROJECT_GOVERNANCE_SCHEMA_VERSION,
    ArtifactRoots,
    BundleOverrides,
    EnabledChecks,
    MemoryRoots,
    ProjectGovernance,
    RepoIdentity,
)


def _git_output(repo_root: Path, *cmd: str) -> str:
    """Run a git command and return stripped stdout, or empty on failure."""
    try:
        result = subprocess.run(
            ["git", *cmd],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _scan_repo_identity(
    repo_root: Path,
    policy: dict[str, Any],
) -> RepoIdentity:
    """Build RepoIdentity from git config and repo policy."""
    name = str(policy.get("repo_name", "")) or repo_root.name
    remote = _git_output(repo_root, "config", "--get", "remote.origin.url")
    default_branch = _git_output(
        repo_root,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "--short",
    )
    if default_branch.startswith("origin/"):
        default_branch = default_branch[len("origin/"):]
    current = _git_output(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    return RepoIdentity(
        repo_name=name,
        remote_url=remote,
        default_branch=default_branch or "main",
        current_branch=current,
    )


def _scan_artifact_roots(repo_root: Path) -> ArtifactRoots:
    """Build ArtifactRoots by checking standard artifact directories."""
    defaults = ArtifactRoots()
    return ArtifactRoots(
        audit_root=_existing_dir(repo_root, defaults.audit_root),
        review_root=_existing_dir(repo_root, defaults.review_root),
        governance_log_root=_existing_dir(
            repo_root,
            defaults.governance_log_root,
        ),
        probe_report_root=_existing_dir(
            repo_root,
            defaults.probe_report_root,
        ),
    )


def _existing_dir(repo_root: Path, relative_path: str) -> str:
    return relative_path if relative_path and (repo_root / relative_path).is_dir() else ""


def _scan_enabled_checks(
    repo_root: Path,
    policy_path: str | Path | None,
) -> EnabledChecks:
    """Build EnabledChecks from the resolved quality-policy for this repo."""
    try:
        from ..quality_policy import resolve_quality_policy

        resolved = resolve_quality_policy(
            repo_root=repo_root,
            policy_path=policy_path,
        )
        guard_ids = tuple(spec.script_id for spec in resolved.ai_guard_checks)
        probe_ids = tuple(spec.script_id for spec in resolved.review_probe_checks)
        return EnabledChecks(guard_ids=guard_ids, probe_ids=probe_ids)
    except (ImportError, OSError, ValueError):
        return EnabledChecks()


def _scan_bundle_overrides() -> BundleOverrides:
    """Return empty bundle overrides until a real bundle-level policy exists."""
    return BundleOverrides(overrides={})


def _scan_workflow_profiles() -> tuple[str, ...]:
    """Return available bundle profile names."""
    try:
        from ..bundle_registry import bundle_names

        return bundle_names()
    except ImportError:
        return ()


def _scan_memory_roots(repo_root: Path) -> MemoryRoots:
    """Discover repo-relative memory roots when they actually exist."""
    memory_root = ".claude/memory" if (repo_root / ".claude" / "memory").is_dir() else ""
    context_store_root = "dev/context" if (repo_root / "dev" / "context").is_dir() else ""
    return MemoryRoots(
        memory_root=memory_root,
        context_store_root=context_store_root,
    )


def _load_policy(
    repo_root: Path,
    *,
    policy: dict[str, Any] | None,
    policy_path: str | Path | None,
) -> tuple[dict[str, Any], str | Path | None]:
    if policy is not None:
        return policy, policy_path
    default_path = repo_root / "dev" / "config" / "devctl_repo_policy.json"
    load_path = Path(policy_path) if policy_path else default_path
    if not load_path.is_file():
        return {}, policy_path
    try:
        from .repo_policy import load_repo_policy_payload

        payload, _warnings, resolved = load_repo_policy_payload(
            repo_root=repo_root,
            policy_path=load_path,
        )
        return payload, str(resolved)
    except (ImportError, OSError, ValueError):
        return {}, policy_path


def _governed_markdown_inputs(
    discovery,
) -> GovernedMarkdownScanInputs:
    return GovernedMarkdownScanInputs(
        path_roots=discovery.path_roots,
        bridge_config=discovery.bridge_config,
        docs_authority=discovery.docs_authority,
        index_path=discovery.index_path,
        tracker_path=discovery.tracker_path,
        governed_doc_roots=discovery.governed_doc_roots,
        startup_order=discovery.startup_order,
    )


def scan_repo_governance(
    repo_root: Path,
    *,
    policy: dict[str, Any] | None = None,
    policy_path: str | Path | None = None,
) -> ProjectGovernance:
    """Scan a repo and build a ProjectGovernance contract from local facts."""
    resolved_policy, resolved_policy_path = _load_policy(
        repo_root,
        policy=policy,
        policy_path=policy_path,
    )
    discovery = scan_governed_doc_discovery(
        repo_root,
        policy=resolved_policy,
        resolved_policy_path=resolved_policy_path,
    )
    plan_registry, doc_policy, doc_registry = scan_governed_markdown_contracts(
        repo_root,
        _governed_markdown_inputs(discovery),
    )
    return ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=_scan_repo_identity(repo_root, resolved_policy),
        repo_pack=scan_repo_pack_ref(resolved_policy),
        path_roots=discovery.path_roots,
        plan_registry=plan_registry,
        artifact_roots=_scan_artifact_roots(repo_root),
        memory_roots=_scan_memory_roots(repo_root),
        bridge_config=discovery.bridge_config,
        enabled_checks=_scan_enabled_checks(repo_root, resolved_policy_path),
        bundle_overrides=_scan_bundle_overrides(),
        doc_policy=doc_policy,
        doc_registry=doc_registry,
        push_enforcement=scan_push_enforcement(
            resolved_policy,
            repo_root=repo_root,
            resolved_policy_path=resolved_policy_path,
        ),
        startup_order=discovery.startup_order,
        docs_authority=discovery.docs_authority,
        workflow_profiles=_scan_workflow_profiles(),
        command_routing_defaults=scan_command_routing_defaults(
            resolved_policy,
            repo_root=repo_root,
            resolved_policy_path=resolved_policy_path,
        ),
    )


def render_governance_draft_markdown(gov: ProjectGovernance) -> str:
    """Render a human-readable markdown summary of a ProjectGovernance payload."""
    lines = [
        "# governance-draft",
        "",
        "## Repo Identity",
        "",
        f"- repo_name: {gov.repo_identity.repo_name}",
        f"- remote_url: {gov.repo_identity.remote_url or '(not set)'}",
        f"- default_branch: {gov.repo_identity.default_branch}",
        f"- current_branch: {gov.repo_identity.current_branch or '(detached)'}",
        "",
        "## Repo Pack",
        "",
        f"- pack_id: {gov.repo_pack.pack_id}",
        f"- pack_version: {gov.repo_pack.pack_version or '(not set)'}",
        f"- description: {gov.repo_pack.description or '(not set)'}",
        "",
        "## Path Roots",
        "",
    ]
    for field in (
        "active_docs",
        "reports",
        "scripts",
        "checks",
        "workflows",
        "guides",
        "config",
    ):
        lines.append(f"- {field}: {getattr(gov.path_roots, field) or '(not found)'}")
    lines += [
        "",
        "## Plan Registry",
        "",
        f"- registry_path: {gov.plan_registry.registry_path or '(not found)'}",
        f"- tracker_path: {gov.plan_registry.tracker_path or '(not found)'}",
        f"- entries: {len(gov.plan_registry.entries)}",
        "",
        "## Doc Policy",
        "",
        f"- docs_authority_path: {gov.doc_policy.docs_authority_path or '(not found)'}",
        f"- active_docs_root: {gov.doc_policy.active_docs_root or '(not found)'}",
        f"- guides_root: {gov.doc_policy.guides_root or '(not found)'}",
        f"- required_plan_sections: {len(gov.doc_policy.required_plan_sections)}",
        f"- budget_classes: {len(gov.doc_policy.budget_limits)}",
        "",
        "## Doc Registry",
        "",
        f"- entries: {len(gov.doc_registry.entries)}",
        "",
        "## Bridge Config",
        "",
        f"- bridge_mode: {gov.bridge_config.bridge_mode}",
        f"- bridge_active: {gov.bridge_config.bridge_active}",
        f"- bridge_path: {gov.bridge_config.bridge_path}",
        "",
        "## Enabled Checks",
        "",
        f"- guards: {len(gov.enabled_checks.guard_ids)}",
        f"- probes: {len(gov.enabled_checks.probe_ids)}",
        "",
        "## Push Enforcement",
        "",
        f"- default_remote: {gov.push_enforcement.default_remote}",
        f"- raw_git_push_guarded: {gov.push_enforcement.raw_git_push_guarded}",
        f"- worktree_dirty: {gov.push_enforcement.worktree_dirty}",
        f"- dirty_path_count: {gov.push_enforcement.dirty_path_count}",
        f"- untracked_path_count: {gov.push_enforcement.untracked_path_count}",
        f"- max_dirty_paths_before_checkpoint: "
        f"{gov.push_enforcement.max_dirty_paths_before_checkpoint}",
        f"- max_untracked_paths_before_checkpoint: "
        f"{gov.push_enforcement.max_untracked_paths_before_checkpoint}",
        f"- checkpoint_required: {gov.push_enforcement.checkpoint_required}",
        f"- safe_to_continue_editing: {gov.push_enforcement.safe_to_continue_editing}",
        f"- checkpoint_reason: {gov.push_enforcement.checkpoint_reason}",
        f"- ahead_of_upstream_commits: "
        f"{gov.push_enforcement.ahead_of_upstream_commits if gov.push_enforcement.ahead_of_upstream_commits is not None else '(unknown)'}",
        f"- recommended_action: {gov.push_enforcement.recommended_action}",
        "",
        "## Startup Order",
        "",
    ]
    for path in gov.startup_order:
        lines.append(f"- {path}")
    if not gov.startup_order:
        lines.append("- (none detected)")
    lines += [
        "",
        f"- docs_authority: {gov.docs_authority or '(not set)'}",
        f"- workflow_profiles: {len(gov.workflow_profiles)}",
    ]
    if gov.command_routing_defaults:
        lines += [
            "",
            "## Command Routing Defaults",
            "",
            f"- keys: {', '.join(sorted(gov.command_routing_defaults.keys()))}",
        ]
    return "\n".join(lines)
