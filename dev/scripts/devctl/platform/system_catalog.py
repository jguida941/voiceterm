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

from .system_catalog_dispatch import (
    _classify_lane_simple,
    _detect_languages,
    _filter_by_languages,
    resolve_agent_dispatch,
)
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
    """Build contract entries from runtime and surface state contract rows."""
    all_specs: list = []

    try:
        from .runtime_state_contract_rows import RUNTIME_STATE_CONTRACTS
        all_specs.extend(RUNTIME_STATE_CONTRACTS)
    except Exception:  # broad-except: allow reason=optional-registry fallback=skip
        pass

    try:
        from .surface_state_contract_rows import surface_state_contracts
        all_specs.extend(surface_state_contracts())
    except Exception:  # broad-except: allow reason=optional-registry fallback=skip
        pass

    entries: list[ContractEntry] = []
    for spec in all_specs:
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
