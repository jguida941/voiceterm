"""Deterministic repo-scan helper that emits a ProjectGovernance payload.

Inspects the current repo for local facts (git state, policy file, filesystem
paths, enabled guards/probes) and builds a ProjectGovernance contract without
network calls or AI inference. This is Phase 1 / Slice B of MP-377.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ..runtime.project_governance import (
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


def _scan_repo_identity(repo_root: Path, policy: dict[str, Any]) -> RepoIdentity:
    """Build RepoIdentity from git config and repo policy."""
    name = str(policy.get("repo_name", "")) or repo_root.name
    remote = _git_output(repo_root, "config", "--get", "remote.origin.url")
    default_branch = _git_output(
        repo_root, "symbolic-ref", "refs/remotes/origin/HEAD", "--short",
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


def _scan_repo_pack(policy: dict[str, Any]) -> RepoPackRef:
    """Build RepoPackRef from policy surface_generation metadata."""
    surface_gen = policy.get("surface_generation") or {}
    meta = surface_gen.get("repo_pack_metadata") or {}
    pack_id = str(meta.get("pack_id", "")) or str(policy.get("repo_name", "")).lower().replace(" ", "_")
    pack_version = str(meta.get("pack_version", ""))
    description = str(meta.get("description", ""))
    return RepoPackRef(
        pack_id=pack_id,
        pack_version=pack_version,
        description=description,
    )


def _scan_path_roots(repo_root: Path) -> PathRoots:
    """Build PathRoots by checking standard directory existence."""
    defaults = PathRoots()
    return PathRoots(
        active_docs=defaults.active_docs if (repo_root / defaults.active_docs).is_dir() else "",
        reports=defaults.reports if (repo_root / defaults.reports).is_dir() else "",
        scripts=defaults.scripts if (repo_root / defaults.scripts).is_dir() else "",
        checks=defaults.checks if (repo_root / defaults.checks).is_dir() else "",
        workflows=defaults.workflows if (repo_root / defaults.workflows).is_dir() else "",
        guides=defaults.guides if (repo_root / defaults.guides).is_dir() else "",
        config=defaults.config if (repo_root / defaults.config).is_dir() else "",
    )


def _scan_plan_registry(repo_root: Path) -> PlanRegistryRoots:
    """Build PlanRegistryRoots by checking authority file existence."""
    defaults = PlanRegistryRoots()
    registry = defaults.registry_path if (repo_root / defaults.registry_path).is_file() else ""
    tracker = defaults.tracker_path if (repo_root / defaults.tracker_path).is_file() else ""
    index = defaults.index_path if (repo_root / defaults.index_path).is_file() else ""
    return PlanRegistryRoots(
        registry_path=registry,
        tracker_path=tracker,
        index_path=index,
    )


def _scan_artifact_roots(repo_root: Path) -> ArtifactRoots:
    """Build ArtifactRoots by checking standard artifact directories."""
    defaults = ArtifactRoots()
    return ArtifactRoots(
        audit_root=defaults.audit_root if (repo_root / defaults.audit_root).is_dir() else "",
        review_root=defaults.review_root if (repo_root / defaults.review_root).is_dir() else "",
        governance_log_root=defaults.governance_log_root
        if (repo_root / defaults.governance_log_root).is_dir()
        else "",
        probe_report_root=defaults.probe_report_root
        if (repo_root / defaults.probe_report_root).is_dir()
        else "",
    )


def _parse_bridge_mode(bridge_text: str) -> str:
    """Extract reviewer mode from bridge markdown, or return single_agent."""
    for line in bridge_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- Reviewer mode:"):
            continue
        parts = stripped.split("`")
        if len(parts) >= 2:
            return parts[1]
        break
    return "single_agent"


def _scan_bridge_config(repo_root: Path) -> BridgeConfig:
    """Build BridgeConfig from bridge file existence and review-channel status."""
    defaults = BridgeConfig()
    bridge_exists = (repo_root / defaults.bridge_path).is_file()
    rc_exists = (repo_root / defaults.review_channel_path).is_file()
    mode = "single_agent"
    if bridge_exists:
        try:
            text = (repo_root / defaults.bridge_path).read_text(encoding="utf-8", errors="replace")
            mode = _parse_bridge_mode(text)
        except OSError:
            pass
    return BridgeConfig(
        bridge_mode=mode,
        bridge_path=defaults.bridge_path,
        review_channel_path=defaults.review_channel_path if rc_exists else "",
        bridge_active=bridge_exists,
    )


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
    """Return empty bundle overrides until a real bundle-level policy surface exists."""
    return BundleOverrides(overrides={})


def _scan_startup_order(repo_root: Path) -> tuple[str, ...]:
    """Derive startup file list from standard bootstrap order."""
    candidates = [
        "AGENTS.md",
        "dev/active/INDEX.md",
        "dev/active/MASTER_PLAN.md",
    ]
    return tuple(c for c in candidates if (repo_root / c).is_file())


def _scan_workflow_profiles() -> tuple[str, ...]:
    """Return available bundle profile names."""
    try:
        from ..bundle_registry import bundle_names

        return bundle_names()
    except ImportError:
        return ()


def scan_repo_governance(
    repo_root: Path,
    *,
    policy: dict[str, Any] | None = None,
    policy_path: str | Path | None = None,
) -> ProjectGovernance:
    """Scan a repo and build a ProjectGovernance contract from local facts.

    If *policy* is None, attempts to load the repo policy from *policy_path*
    (or the standard ``devctl_repo_policy.json`` under *repo_root*).
    """
    resolved_policy_path = policy_path
    if policy is None:
        default_path = repo_root / "dev" / "config" / "devctl_repo_policy.json"
        load_path = Path(policy_path) if policy_path else default_path
        if load_path.is_file():
            try:
                from .repo_policy import load_repo_policy_payload

                policy, _warnings, _resolved = load_repo_policy_payload(
                    repo_root=repo_root,
                    policy_path=load_path,
                )
                resolved_policy_path = str(_resolved)
            except (ImportError, OSError, ValueError):
                policy = {}
        else:
            policy = {}

    docs_authority = "AGENTS.md" if (repo_root / "AGENTS.md").is_file() else ""

    return ProjectGovernance(
        schema_version=PROJECT_GOVERNANCE_SCHEMA_VERSION,
        contract_id=PROJECT_GOVERNANCE_CONTRACT_ID,
        repo_identity=_scan_repo_identity(repo_root, policy),
        repo_pack=_scan_repo_pack(policy),
        path_roots=_scan_path_roots(repo_root),
        plan_registry=_scan_plan_registry(repo_root),
        artifact_roots=_scan_artifact_roots(repo_root),
        memory_roots=MemoryRoots(),
        bridge_config=_scan_bridge_config(repo_root),
        enabled_checks=_scan_enabled_checks(repo_root, resolved_policy_path),
        bundle_overrides=_scan_bundle_overrides(),
        startup_order=_scan_startup_order(repo_root),
        docs_authority=docs_authority,
        workflow_profiles=_scan_workflow_profiles(),
        command_routing_defaults=None,
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
    for field in ("active_docs", "reports", "scripts", "checks", "workflows", "guides", "config"):
        val = getattr(gov.path_roots, field)
        lines.append(f"- {field}: {val or '(not found)'}")
    lines += [
        "",
        "## Plan Registry",
        "",
        f"- registry_path: {gov.plan_registry.registry_path or '(not found)'}",
        f"- tracker_path: {gov.plan_registry.tracker_path or '(not found)'}",
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
    return "\n".join(lines)
