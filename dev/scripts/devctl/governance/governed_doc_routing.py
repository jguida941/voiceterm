"""Shared governed-doc routing helpers for docs-check and check-router."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import REPO_ROOT
from .draft_policy_surface import surface_generation_context
from .repo_policy import load_repo_policy_payload


@dataclass(frozen=True, slots=True)
class GovernedDocRouting:
    """Resolved doc-routing hints derived from governance plus surface context."""

    process_doc: str
    development_doc: str
    scripts_readme_doc: str
    architecture_doc: str
    tracker_path: str
    index_path: str
    governed_tooling_docs: tuple[str, ...]
    governed_tooling_prefixes: tuple[str, ...]
    tooling_change_prefixes: tuple[str, ...]


def _append_unique(values: list[str], candidate: str) -> None:
    text = candidate.strip().rstrip("/")
    if text and text not in values:
        values.append(text)


def _existing_file(repo_root: Path, candidate: object) -> str:
    text = str(candidate or "").strip()
    if not text:
        return ""
    return text if (repo_root / text).is_file() else ""


def _existing_dir_prefix(repo_root: Path, candidate: object) -> str:
    text = str(candidate or "").strip().rstrip("/")
    if not text:
        return ""
    return f"{text}/" if (repo_root / text).is_dir() else ""


def resolve_governed_doc_routing(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> GovernedDocRouting:
    """Resolve governed/tooling doc routing from repo policy and governance."""
    payload, _warnings, _resolved = load_repo_policy_payload(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    context = surface_generation_context(payload)
    governance = None
    try:
        from .draft import scan_repo_governance

        governance = scan_repo_governance(
            repo_root,
            policy_path=policy_path,
        )
    except (ImportError, OSError, ValueError):
        governance = None

    process_doc = _existing_file(repo_root, context.get("process_doc"))
    development_doc = _existing_file(repo_root, context.get("development_doc"))
    scripts_readme_doc = _existing_file(repo_root, context.get("scripts_readme_doc"))
    architecture_doc = _existing_file(repo_root, context.get("architecture_doc"))

    tracker_path = ""
    index_path = ""
    governed_tooling_docs: list[str] = []
    governed_tooling_prefixes: list[str] = []
    tooling_change_prefixes: list[str] = []
    if governance is not None:
        tracker_path = _existing_file(repo_root, governance.plan_registry.tracker_path)
        index_path = _existing_file(repo_root, governance.plan_registry.index_path)
        for entry in governance.doc_registry.entries:
            _append_unique(
                governed_tooling_docs,
                _existing_file(repo_root, entry.path),
            )
        for candidate in (
            governance.doc_policy.governed_doc_roots,
            (governance.doc_policy.active_docs_root, governance.doc_policy.guides_root),
            (
                governance.path_roots.active_docs,
                governance.path_roots.guides,
                governance.path_roots.config,
            ),
        ):
            for item in candidate:
                _append_unique(
                    governed_tooling_prefixes,
                    _existing_dir_prefix(repo_root, item),
                )
        for item in (
            governance.path_roots.scripts,
            governance.path_roots.workflows,
            ".github/scripts",
            "scripts/macro-packs",
        ):
            _append_unique(
                tooling_change_prefixes,
                _existing_dir_prefix(repo_root, item),
            )

    for item in (
        process_doc,
        development_doc,
        scripts_readme_doc,
        architecture_doc,
        tracker_path,
        index_path,
    ):
        _append_unique(governed_tooling_docs, item)

    return GovernedDocRouting(
        process_doc=process_doc,
        development_doc=development_doc,
        scripts_readme_doc=scripts_readme_doc,
        architecture_doc=architecture_doc,
        tracker_path=tracker_path,
        index_path=index_path,
        governed_tooling_docs=tuple(governed_tooling_docs),
        governed_tooling_prefixes=tuple(governed_tooling_prefixes),
        tooling_change_prefixes=tuple(tooling_change_prefixes),
    )


__all__ = ["GovernedDocRouting", "resolve_governed_doc_routing"]
