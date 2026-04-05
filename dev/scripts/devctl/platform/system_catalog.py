"""Generated SystemCatalog built from existing registries, plus AgentDispatchPacket routing.

SystemCatalog scans the repo's command listing, guard/probe script catalog,
surface definitions, and runtime contract rows to produce a frozen typed
inventory. Nothing is hardcoded -- every entry comes from an existing registry.

AgentDispatchPacket derives per-request routing from classify_lane() output
and the catalog's guard/probe inventory, recommending what to run for a
bounded change set.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .system_catalog_models import (
    AgentDispatchPacket,
    CommandEntry,
    ContractEntry,
    GuardEntry,
    ProbeEntry,
    SurfaceEntry,
    SystemCatalog,
)

__all__ = [
    "AgentDispatchPacket",
    "CommandEntry",
    "ContractEntry",
    "GuardEntry",
    "ProbeEntry",
    "SurfaceEntry",
    "SystemCatalog",
    "build_system_catalog",
    "resolve_agent_dispatch",
]


# ---------------------------------------------------------------------------
# Collector functions -- read from existing registries
# ---------------------------------------------------------------------------


def _collect_commands() -> tuple[CommandEntry, ...]:
    """Build command entries from the listing registry."""
    try:
        from ..commands.listing import COMMANDS
    except Exception:  # broad-except: allow reason=optional-registry fallback=empty-tuple
        return ()

    return tuple(
        CommandEntry(
            name=cmd_name,
            path=f"dev/scripts/devctl.py {cmd_name}",
            category="devctl",
            description=f"devctl {cmd_name}",
        )
        for cmd_name in COMMANDS
    )


def _collect_guards(repo_root: Path) -> tuple[GuardEntry, ...]:
    """Build guard entries from quality-policy defaults and script catalog."""
    try:
        from ..quality_policy.defaults import DEFAULT_AI_GUARD_SPECS
        from ..script_catalog import CHECK_SCRIPT_RELATIVE_PATHS
    except Exception:  # broad-except: allow reason=optional-registry fallback=filesystem-scan
        return _collect_guards_from_filesystem(repo_root)

    entries: list[GuardEntry] = []
    for spec in DEFAULT_AI_GUARD_SPECS:
        rel_path = CHECK_SCRIPT_RELATIVE_PATHS.get(spec.script_id, "")
        entries.append(
            GuardEntry(
                name=spec.step_name,
                path=rel_path,
                category="hard_guard",
                description=f"Guard: {spec.step_name}",
                languages=spec.languages,
            )
        )
    return tuple(entries)


def _collect_guards_from_filesystem(repo_root: Path) -> tuple[GuardEntry, ...]:
    """Fallback: scan dev/scripts/checks/ for check_*.py files."""
    checks_dir = repo_root / "dev" / "scripts" / "checks"
    if not checks_dir.is_dir():
        return ()
    entries: list[GuardEntry] = []
    for script_path in sorted(checks_dir.glob("check_*.py")):
        script_id = script_path.stem.removeprefix("check_")
        rel_path = str(script_path.relative_to(repo_root))
        entries.append(
            GuardEntry(
                name=script_id,
                path=rel_path,
                category="hard_guard",
                description=f"Guard: {script_id}",
            )
        )
    return tuple(entries)


def _collect_probes(repo_root: Path) -> tuple[ProbeEntry, ...]:
    """Build probe entries from quality-policy defaults and script catalog."""
    try:
        from ..quality_policy.defaults import DEFAULT_REVIEW_PROBE_SPECS
        from ..script_catalog import PROBE_SCRIPT_RELATIVE_PATHS
    except Exception:  # broad-except: allow reason=optional-registry fallback=filesystem-scan
        return _collect_probes_from_filesystem(repo_root)

    entries: list[ProbeEntry] = []
    for spec in DEFAULT_REVIEW_PROBE_SPECS:
        rel_path = PROBE_SCRIPT_RELATIVE_PATHS.get(spec.script_id, "")
        entries.append(
            ProbeEntry(
                name=spec.step_name,
                path=rel_path,
                category="review_probe",
                description=f"Probe: {spec.step_name}",
                languages=spec.languages,
            )
        )
    return tuple(entries)


def _collect_probes_from_filesystem(repo_root: Path) -> tuple[ProbeEntry, ...]:
    """Fallback: scan dev/scripts/checks/ for probe_*.py files."""
    checks_dir = repo_root / "dev" / "scripts" / "checks"
    if not checks_dir.is_dir():
        return ()
    entries: list[ProbeEntry] = []
    for script_path in sorted(checks_dir.glob("probe_*.py")):
        script_id = script_path.stem
        rel_path = str(script_path.relative_to(repo_root))
        entries.append(
            ProbeEntry(
                name=script_id,
                path=rel_path,
                category="review_probe",
                description=f"Probe: {script_id}",
            )
        )
    return tuple(entries)


def _collect_surfaces() -> tuple[SurfaceEntry, ...]:
    """Build surface entries from platform surface definitions."""
    try:
        from .surface_definitions import (
            discovery_surfaces,
            frontend_surfaces,
        )
    except Exception:  # broad-except: allow reason=optional-registry fallback=empty-tuple
        return ()

    entries: list[SurfaceEntry] = []
    for spec in frontend_surfaces():
        entries.append(
            SurfaceEntry(
                name=spec.surface_id,
                path="",
                category="frontend",
                description=spec.notes,
            )
        )
    for spec in discovery_surfaces():
        entries.append(
            SurfaceEntry(
                name=spec.surface_id,
                path="",
                category="discovery",
                description=spec.notes,
            )
        )
    return tuple(entries)


def _collect_contracts() -> tuple[ContractEntry, ...]:
    """Build contract entries from runtime state contract rows."""
    try:
        from .runtime_state_contract_rows import RUNTIME_STATE_CONTRACTS
    except Exception:  # broad-except: allow reason=optional-registry fallback=empty-tuple
        return ()

    entries: list[ContractEntry] = []
    for spec in RUNTIME_STATE_CONTRACTS:
        field_names = tuple(f.name for f in spec.required_fields)
        entries.append(
            ContractEntry(
                name=spec.contract_id,
                path=spec.runtime_model,
                category=spec.owner_layer,
                description=spec.purpose,
                fields=field_names,
            )
        )
    return tuple(entries)


# ---------------------------------------------------------------------------
# build_system_catalog -- the primary entry point
# ---------------------------------------------------------------------------


def build_system_catalog(repo_root: Path | None = None) -> SystemCatalog:
    """Build a static SystemCatalog from existing Python registries.

    When *repo_root* is None, resolves it from ``config.REPO_ROOT``.
    Registry imports that fail (because a module is absent in a sparse
    checkout or adopted repo) degrade to empty tuples or filesystem scans
    so the catalog is always buildable.
    """
    if repo_root is None:
        from ..config import REPO_ROOT
        repo_root = REPO_ROOT

    return SystemCatalog(
        commands=_collect_commands(),
        guards=_collect_guards(repo_root),
        probes=_collect_probes(repo_root),
        surfaces=_collect_surfaces(),
        contracts=_collect_contracts(),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# AgentDispatchPacket builder -- derives routing for changed paths
# ---------------------------------------------------------------------------


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
