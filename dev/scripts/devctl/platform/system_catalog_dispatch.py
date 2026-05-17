"""AgentDispatchPacket routing derived from SystemCatalog and lane classification.

Produces per-request dispatch packets that recommend which guards, probes,
and bundles to run for a bounded change set.
"""

from __future__ import annotations

from pathlib import Path

from .system_catalog_models import (
    AgentDispatchPacket,
    GuardEntry,
    ProbeEntry,
)

_BUNDLE_BY_LANE = {
    "docs": "bundle.docs",
    "runtime": "bundle.runtime",
    "tooling": "bundle.tooling",
    "release": "bundle.release",
}

_EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".rs": "rust",
}


def _detect_languages(paths: list[str]) -> set[str]:
    """Map file extensions to language tags across a path list."""
    languages: set[str] = set()
    for path in paths:
        suffix = Path(path).suffix.lower()
        lang = _EXTENSION_TO_LANGUAGE.get(suffix)
        if lang:
            languages.add(lang)
    return languages


def _classify_lane_simple(changed_paths: list[str]) -> str:
    """Lightweight lane classification when the full router is unavailable.

    Uses path-prefix heuristics matching the task router contract:
    rust/src/** -> runtime, dev/** -> tooling, docs/** -> docs, else tooling.
    """
    if not changed_paths:
        return "tooling"

    has_runtime = any(
        p.startswith("rust/src/") or p.endswith(".rs") for p in changed_paths
    )
    if has_runtime:
        return "runtime"

    has_tooling = any(
        p.startswith("dev/") or p.startswith(".github/") for p in changed_paths
    )
    if has_tooling:
        return "tooling"

    has_docs = any(p.startswith("docs/") or p.endswith(".md") for p in changed_paths)
    if has_docs:
        return "docs"

    return "tooling"


def _filter_by_languages(
    entries: tuple[GuardEntry, ...] | tuple[ProbeEntry, ...],
    languages: set[str],
) -> tuple[str, ...]:
    """Return entry names whose language scope intersects the change set."""
    applicable: list[str] = []
    for entry in entries:
        if not entry.languages or languages.intersection(entry.languages):
            applicable.append(entry.name)
    return tuple(applicable)


def resolve_agent_dispatch(
    changed_paths: list[str],
    repo_root: Path | None = None,
) -> AgentDispatchPacket:
    """Derive an AgentDispatchPacket for a bounded change set.

    Tries the full classify_lane() router first, falling back to
    simple path-prefix heuristics if the router module is unavailable.
    Builds the catalog to filter guards/probes by language scope.
    """
    if repo_root is None:
        from ..config import REPO_ROOT
        repo_root = REPO_ROOT

    try:
        from ..commands.check.router_support import classify_lane
        classification = classify_lane(changed_paths, repo_root=repo_root)
        lane = classification["lane"]
    except Exception:  # broad-except: allow reason=router-unavailable fallback=simple-heuristic
        lane = _classify_lane_simple(changed_paths)

    from .system_catalog import build_system_catalog

    bundle_name = _BUNDLE_BY_LANE.get(lane, f"bundle.{lane}")
    catalog = build_system_catalog(repo_root)
    languages = _detect_languages(changed_paths)
    applicable_guards = _filter_by_languages(catalog.guards, languages)
    applicable_probes = _filter_by_languages(catalog.probes, languages)

    preflight = "python3 dev/scripts/devctl.py check --profile ci"
    context_level = "full" if lane == "runtime" else "standard"

    return AgentDispatchPacket(
        changed_paths=tuple(changed_paths),
        applicable_guards=applicable_guards,
        applicable_probes=applicable_probes,
        recommended_bundle=bundle_name,
        preflight_command=preflight,
        context_level=context_level,
        lane=lane,
        evidence=(
            f"lane={lane}",
            f"bundle={bundle_name}",
            f"guards={len(applicable_guards)}",
            f"probes={len(applicable_probes)}",
            f"changed_paths={len(changed_paths)}",
        ),
    )
