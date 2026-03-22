"""Policy-driven governed-markdown discovery helpers for governance-draft."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .draft_policy_parent_paths import common_parent_dir, parent_dir, policy_dir_root
from .draft_policy_paths import (
    coerce_relative_path,
    configured_dir,
    configured_doc_path,
)
from .draft_policy_surface import (
    check_router_payload,
    repo_governance_payload,
    surface_generation_context,
)
from ..runtime.project_governance import BridgeConfig, PathRoots


@dataclass(frozen=True, slots=True)
class GovernedDocDiscovery:
    """Resolved governed-markdown startup surfaces for one repo."""

    docs_authority: str
    index_path: str
    tracker_path: str
    path_roots: PathRoots
    bridge_config: BridgeConfig
    governed_doc_roots: tuple[str, ...]
    startup_order: tuple[str, ...]

def _scan_docs_authority(repo_root: Path, policy: dict[str, Any]) -> str:
    surface_context = surface_generation_context(policy)
    return configured_doc_path(
        repo_root,
        configured=surface_context.get("process_doc"),
        fallback="AGENTS.md",
        allow_missing_fallback=True,
    )


def _scan_plan_registry_paths(
    repo_root: Path,
    policy: dict[str, Any],
) -> tuple[str, str]:
    surface_context = surface_generation_context(policy)
    index_path = configured_doc_path(
        repo_root,
        configured=surface_context.get("active_registry_doc"),
        fallback="dev/active/INDEX.md",
        allow_missing_fallback=True,
    )
    tracker_path = configured_doc_path(
        repo_root,
        configured=surface_context.get("execution_tracker_doc"),
        fallback="dev/active/MASTER_PLAN.md",
        allow_missing_fallback=True,
    )
    return index_path, tracker_path


def _scan_path_roots(
    repo_root: Path,
    *,
    policy: dict[str, Any],
    resolved_policy_path: str | Path | None,
    index_path: str,
    tracker_path: str,
) -> PathRoots:
    defaults = PathRoots()
    surface_context = surface_generation_context(policy)
    python_tooling = configured_dir(
        repo_root,
        configured=surface_context.get("python_tooling"),
    )
    guard_scripts = configured_dir(
        repo_root,
        configured=surface_context.get("guard_scripts"),
    )
    configured_index = coerce_relative_path(
        surface_context.get("active_registry_doc")
    )
    configured_tracker = coerce_relative_path(
        surface_context.get("execution_tracker_doc")
    )
    configured_architecture = coerce_relative_path(
        surface_context.get("architecture_doc")
    )
    configured_development = coerce_relative_path(
        surface_context.get("development_doc")
    )
    scripts = common_parent_dir(python_tooling, guard_scripts)
    if not scripts:
        scripts = parent_dir(python_tooling) or python_tooling
    if not scripts:
        scripts = parent_dir(guard_scripts) or guard_scripts
    if not scripts and (repo_root / defaults.scripts).is_dir():
        scripts = defaults.scripts
    checks = configured_dir(
        repo_root,
        configured=surface_context.get("guard_scripts"),
        fallback=defaults.checks,
    )
    workflows = parent_dir(
        configured_doc_path(
            repo_root,
            configured=surface_context.get("ci_workflows_doc"),
            fallback=".github/workflows/README.md",
        )
    ) or (
        defaults.workflows if (repo_root / defaults.workflows).is_dir() else ""
    )
    guides = common_parent_dir(
        configured_architecture,
        configured_development,
    )
    if not guides:
        candidate_guides = common_parent_dir(
            configured_doc_path(
                repo_root,
                configured=surface_context.get("architecture_doc"),
            ),
            configured_doc_path(
                repo_root,
                configured=surface_context.get("development_doc"),
            ),
        )
        if candidate_guides and (repo_root / candidate_guides).is_dir():
            guides = candidate_guides
        elif (repo_root / defaults.guides).is_dir():
            guides = defaults.guides
    active_docs = common_parent_dir(configured_index, configured_tracker)
    if not active_docs:
        candidate_active_docs = common_parent_dir(index_path, tracker_path)
        if candidate_active_docs and (repo_root / candidate_active_docs).is_dir():
            active_docs = candidate_active_docs
        elif (repo_root / defaults.active_docs).is_dir():
            active_docs = defaults.active_docs
    config = policy_dir_root(repo_root, resolved_policy_path) or (
        defaults.config if (repo_root / defaults.config).is_dir() else ""
    )
    return PathRoots(
        active_docs=active_docs,
        reports=defaults.reports if (repo_root / defaults.reports).is_dir() else "",
        scripts=scripts,
        checks=checks,
        workflows=workflows,
        guides=guides,
        config=config,
    )


def _parse_bridge_mode(bridge_text: str) -> str:
    for line in bridge_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- Reviewer mode:"):
            continue
        parts = stripped.split("`")
        if len(parts) >= 2:
            return parts[1]
        break
    return "single_agent"


def _scan_bridge_config(
    repo_root: Path,
    *,
    policy: dict[str, Any],
    active_docs_root: str,
) -> BridgeConfig:
    defaults = BridgeConfig()
    push_payload = repo_governance_payload(policy).get("push")
    checkpoint_payload = (
        push_payload.get("checkpoint")
        if isinstance(push_payload, dict)
        else {}
    )
    compatibility_paths = (
        checkpoint_payload.get("compatibility_projection_paths")
        if isinstance(checkpoint_payload, dict)
        else ()
    )
    if not isinstance(compatibility_paths, (list, tuple)):
        compatibility_paths = ()
    bridge_path = next(
        (
            coerce_relative_path(candidate)
            for candidate in compatibility_paths
            if coerce_relative_path(candidate).lower().endswith(".md")
        ),
        defaults.bridge_path if (repo_root / defaults.bridge_path).is_file() else "",
    )
    review_channel_candidates = tuple(
        candidate
        for candidate in (
            f"{active_docs_root}/review_channel.md" if active_docs_root else "",
            defaults.review_channel_path,
        )
        if candidate
    )
    review_channel_path = next(
        (
            candidate
            for candidate in review_channel_candidates
            if (repo_root / candidate).is_file()
        ),
        "",
    )
    bridge_exists = bool(bridge_path) and (repo_root / bridge_path).is_file()
    mode = "single_agent"
    if bridge_exists:
        try:
            text = (repo_root / bridge_path).read_text(
                encoding="utf-8",
                errors="replace",
            )
            mode = _parse_bridge_mode(text)
        except OSError:
            pass
    return BridgeConfig(
        bridge_mode=mode,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        bridge_active=bridge_exists,
    )


def _scan_governed_doc_roots(
    repo_root: Path,
    *,
    policy: dict[str, Any],
    docs_authority: str,
    index_path: str,
    tracker_path: str,
    path_roots: PathRoots,
) -> tuple[str, ...]:
    check_router = check_router_payload(policy)
    surface_context = surface_generation_context(policy)
    raw_markdown_roots = check_router.get("tooling_markdown_prefixes")
    if not isinstance(raw_markdown_roots, (list, tuple)):
        raw_markdown_roots = ()
    roots: list[str] = []
    candidates = [
        *raw_markdown_roots,
        path_roots.active_docs,
        path_roots.guides,
        parent_dir(docs_authority),
        parent_dir(index_path),
        parent_dir(tracker_path),
        parent_dir(
            configured_doc_path(
                repo_root,
                configured=surface_context.get("architecture_doc"),
            )
        ),
        parent_dir(
            configured_doc_path(
                repo_root,
                configured=surface_context.get("development_doc"),
            )
        ),
    ]
    for raw in candidates:
        root = coerce_relative_path(raw)
        if not root or root == "." or root in roots:
            continue
        roots.append(root)
    return tuple(roots)


def _scan_startup_order(
    repo_root: Path,
    *,
    docs_authority: str,
    index_path: str,
    tracker_path: str,
) -> tuple[str, ...]:
    candidates = [docs_authority, index_path, tracker_path]
    return tuple(c for c in candidates if (repo_root / c).is_file())


def scan_governed_doc_discovery(
    repo_root: Path,
    *,
    policy: dict[str, Any],
    resolved_policy_path: str | Path | None,
) -> GovernedDocDiscovery:
    """Resolve repo-policy-owned startup markdown surfaces for one repo."""
    docs_authority = _scan_docs_authority(repo_root, policy)
    index_path, tracker_path = _scan_plan_registry_paths(repo_root, policy)
    path_roots = _scan_path_roots(
        repo_root,
        policy=policy,
        resolved_policy_path=resolved_policy_path,
        index_path=index_path,
        tracker_path=tracker_path,
    )
    bridge_config = _scan_bridge_config(
        repo_root,
        policy=policy,
        active_docs_root=path_roots.active_docs,
    )
    startup_order = _scan_startup_order(
        repo_root,
        docs_authority=docs_authority,
        index_path=index_path,
        tracker_path=tracker_path,
    )
    governed_doc_roots = _scan_governed_doc_roots(
        repo_root,
        policy=policy,
        docs_authority=docs_authority,
        index_path=index_path,
        tracker_path=tracker_path,
        path_roots=path_roots,
    )
    return GovernedDocDiscovery(
        docs_authority=docs_authority,
        index_path=index_path,
        tracker_path=tracker_path,
        path_roots=path_roots,
        bridge_config=bridge_config,
        governed_doc_roots=governed_doc_roots,
        startup_order=startup_order,
    )


__all__ = [
    "GovernedDocDiscovery",
    "scan_governed_doc_discovery",
]
