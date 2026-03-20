"""Layout helpers for governed doc discovery."""

from __future__ import annotations

from pathlib import Path

from .doc_authority_models import GovernedDocLayout
from .draft import scan_repo_governance
from .repo_policy import load_repo_governance_section


def is_root_markdown_path(relative_path: str) -> bool:
    return "/" not in relative_path and relative_path.lower().endswith(".md")


def path_in_root(relative_path: str, root_path: str) -> bool:
    if not root_path:
        return False
    return relative_path == root_path or relative_path.startswith(f"{root_path}/")


def load_governed_doc_layout(
    repo_root: Path,
    *,
    policy_path: str | Path | None,
) -> GovernedDocLayout:
    """Derive governed-doc scan inputs from ProjectGovernance plus repo policy."""
    governance = scan_repo_governance(repo_root, policy_path=policy_path)
    root_files: set[str] = set()
    for candidate in governance.startup_order:
        if is_root_markdown_path(candidate) and (repo_root / candidate).is_file():
            root_files.add(candidate)
    for candidate in (
        governance.docs_authority,
        governance.bridge_config.bridge_path,
    ):
        if is_root_markdown_path(candidate) and (repo_root / candidate).is_file():
            root_files.add(candidate)
    layout = GovernedDocLayout(
        repo_root=repo_root,
        active_docs_root=governance.path_roots.active_docs,
        guides_root=governance.path_roots.guides,
        index_path=governance.plan_registry.index_path,
        tracker_path=governance.plan_registry.tracker_path,
        docs_authority_path=governance.docs_authority,
        bridge_path=governance.bridge_config.bridge_path,
        root_files=tuple(sorted(root_files)),
    )
    return GovernedDocLayout(
        repo_root=layout.repo_root,
        active_docs_root=layout.active_docs_root,
        guides_root=layout.guides_root,
        index_path=layout.index_path,
        tracker_path=layout.tracker_path,
        docs_authority_path=layout.docs_authority_path,
        bridge_path=layout.bridge_path,
        root_files=_collect_root_governed_docs(repo_root, layout, policy_path),
    )


def registry_managed(relative_path: str, layout: GovernedDocLayout) -> bool:
    if relative_path == layout.index_path:
        return False
    return path_in_root(relative_path, layout.active_docs_root)


def _collect_root_governed_docs(
    repo_root: Path,
    layout: GovernedDocLayout,
    policy_path: str | Path | None,
) -> tuple[str, ...]:
    candidates = set(layout.root_files)
    check_router, _warnings, _resolved = load_repo_governance_section(
        "check_router",
        repo_root=repo_root,
        policy_path=policy_path,
    )
    for key in ("tooling_exact_paths", "docs_exact_paths"):
        for raw_path in check_router.get(key, []):
            candidate = str(raw_path)
            if not is_root_markdown_path(candidate):
                continue
            if "INDEX" not in Path(candidate).name.upper():
                continue
            if (repo_root / candidate).is_file():
                candidates.add(candidate)
    return tuple(sorted(candidates))
