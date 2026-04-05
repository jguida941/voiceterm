"""Build a static SystemCatalog from existing registries and derive AgentDispatchPacket.

SystemCatalog is built once per session from script_catalog, quality_policy,
surface_definitions, and CLI handler registries. It never mutates live state.

AgentDispatchPacket is derived per-request from classify_lane() output, the
resolved quality policy, and the catalog's guard/probe inventory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from ..config import REPO_ROOT
from ..script_catalog import (
    CHECK_SCRIPT_RELATIVE_PATHS,
    PROBE_SCRIPT_RELATIVE_PATHS,
)
from .system_catalog_models import (
    AgentDispatchPacket,
    CatalogCommand,
    CatalogGuard,
    CatalogProbe,
    CatalogSurface,
    SystemCatalog,
)

SYSTEM_CATALOG_SCHEMA_VERSION = 1


def _collect_commands() -> tuple[CatalogCommand, ...]:
    """Build command entries from the CLI handler registry."""
    from ..cli import COMMAND_HANDLERS, READ_ONLY_COMMANDS

    return tuple(
        CatalogCommand(
            name=name,
            handler_module=getattr(handler, "__module__", "") or "",
            read_only=name in READ_ONLY_COMMANDS,
        )
        for name, handler in sorted(COMMAND_HANDLERS.items())
    )


def _collect_guards(
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[CatalogGuard, ...]:
    """Build guard entries from quality policy and script catalog."""
    from ..quality_policy import resolve_quality_policy

    policy = resolve_quality_policy(repo_root=repo_root)
    guards: list[CatalogGuard] = []
    for spec in policy.ai_guard_checks:
        rel_path = CHECK_SCRIPT_RELATIVE_PATHS.get(spec.script_id, "")
        guards.append(
            CatalogGuard(
                script_id=spec.script_id,
                relative_path=rel_path,
                languages=spec.languages,
            )
        )
    return tuple(guards)


def _collect_probes(
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[CatalogProbe, ...]:
    """Build probe entries from quality policy and script catalog."""
    from ..quality_policy import resolve_quality_policy

    policy = resolve_quality_policy(repo_root=repo_root)
    probes: list[CatalogProbe] = []
    for spec in policy.review_probe_checks:
        rel_path = PROBE_SCRIPT_RELATIVE_PATHS.get(spec.script_id, "")
        probes.append(
            CatalogProbe(
                script_id=spec.script_id,
                relative_path=rel_path,
            )
        )
    return tuple(probes)


def _collect_surfaces() -> tuple[CatalogSurface, ...]:
    """Build surface entries from platform surface_definitions."""
    from ..platform.surface_definitions import frontend_surfaces

    return tuple(
        CatalogSurface(
            surface_id=s.surface_id,
            authority=s.authority,
            consumes_contracts=s.consumes_contracts,
        )
        for s in frontend_surfaces()
    )


def build_system_catalog(
    *,
    repo_root: Path = REPO_ROOT,
) -> SystemCatalog:
    """Build a static SystemCatalog from existing registries."""
    commands = _collect_commands()
    guards = _collect_guards(repo_root=repo_root)
    probes = _collect_probes(repo_root=repo_root)
    surfaces = _collect_surfaces()
    return SystemCatalog(
        schema_version=SYSTEM_CATALOG_SCHEMA_VERSION,
        commands=commands,
        guards=guards,
        probes=probes,
        surfaces=surfaces,
        total_commands=len(commands),
        total_guards=len(guards),
        total_probes=len(probes),
        total_surfaces=len(surfaces),
    )


def resolve_agent_dispatch(
    changed_paths: list[str],
    *,
    bundle_by_lane: Mapping[str, str] | None = None,
    enabled_checks: object | None = None,
    repo_root: Path = REPO_ROOT,
) -> AgentDispatchPacket:
    """Derive an AgentDispatchPacket for a bounded change set.

    Composes classify_lane(), quality policy guard/probe filtering, and
    the BUNDLE_BY_LANE mapping to produce a self-contained routing
    recommendation without creating new policy authority.

    When *enabled_checks* is provided (an ``EnabledChecks`` instance from
    ``ProjectGovernance`` or ``StartupContext``), guard and probe IDs are
    intersected with the enabled set so the dispatch only includes checks
    the repo has turned on.
    """
    from ..commands.check.router_support import classify_lane
    from ..commands.check.router_constants import BUNDLE_BY_LANE as DEFAULT_BUNDLE_BY_LANE
    from ..quality_policy import resolve_quality_policy

    effective_bundles = bundle_by_lane or DEFAULT_BUNDLE_BY_LANE

    classification = classify_lane(changed_paths, repo_root=repo_root)
    lane = classification["lane"]
    bundle_name = effective_bundles.get(lane, f"bundle.{lane}")

    policy = resolve_quality_policy(repo_root=repo_root)

    applicable_guards = _filter_guards_for_paths(
        changed_paths, policy, repo_root=repo_root,
    )
    applicable_probes = tuple(
        spec.script_id for spec in policy.review_probe_checks
    )

    applicable_guards, applicable_probes = _apply_enabled_checks_filter(
        applicable_guards, applicable_probes, enabled_checks,
    )

    preflight = (f"python3 dev/scripts/devctl.py check --profile ci",)
    evidence_list = [
        f"lane={lane}",
        f"bundle={bundle_name}",
        f"guards={len(applicable_guards)}",
        f"probes={len(applicable_probes)}",
        f"changed_paths={len(changed_paths)}",
    ]
    if enabled_checks is not None:
        evidence_list.append("enabled_checks_filter=applied")
    evidence = tuple(evidence_list)

    return AgentDispatchPacket(
        lane=lane,
        bundle_name=bundle_name,
        applicable_guards=applicable_guards,
        applicable_probes=applicable_probes,
        preflight_commands=preflight,
        context_level="standard",
        changed_paths=tuple(changed_paths),
        evidence=evidence,
    )


def _apply_enabled_checks_filter(
    guards: tuple[str, ...],
    probes: tuple[str, ...],
    enabled_checks: object | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Intersect guard/probe IDs with EnabledChecks when provided.

    If *enabled_checks* is None or has empty ID tuples, the original
    sets pass through unchanged (open-world default).
    """
    if enabled_checks is None:
        return guards, probes
    guard_ids = getattr(enabled_checks, "guard_ids", ()) or ()
    probe_ids = getattr(enabled_checks, "probe_ids", ()) or ()
    if guard_ids:
        guard_set = set(guard_ids)
        guards = tuple(g for g in guards if g in guard_set)
    if probe_ids:
        probe_set = set(probe_ids)
        probes = tuple(p for p in probes if p in probe_set)
    return guards, probes


def filter_guards_for_file(
    file_path: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[str, ...]:
    """Return deterministic guard IDs applicable to a single file path.

    Checks file extension against guard language scopes from the quality
    policy. Used by ``discover --filter guards-for-file:<path>``.
    """
    from ..quality_policy import resolve_quality_policy

    policy = resolve_quality_policy(repo_root=repo_root)
    path_languages = _detect_languages([file_path])
    applicable: list[str] = []
    for spec in policy.ai_guard_checks:
        if spec.languages and not path_languages.intersection(spec.languages):
            continue
        applicable.append(spec.script_id)
    return tuple(applicable)


def _filter_guards_for_paths(
    changed_paths: list[str],
    policy,
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[str, ...]:
    """Return guard script IDs applicable to the given changed paths.

    Uses the quality policy's language filters and guard root prefixes to
    narrow the full guard set to those relevant for the change set.
    """
    if not changed_paths:
        return tuple(spec.script_id for spec in policy.ai_guard_checks)

    path_languages = _detect_languages(changed_paths)
    applicable: list[str] = []
    for spec in policy.ai_guard_checks:
        if spec.languages and not path_languages.intersection(spec.languages):
            continue
        applicable.append(spec.script_id)
    return tuple(applicable)


def _detect_languages(paths: list[str]) -> set[str]:
    """Detect languages present in a list of repo-relative paths."""
    languages: set[str] = set()
    for path in paths:
        if path.endswith(".py"):
            languages.add("python")
        elif path.endswith(".rs"):
            languages.add("rust")
    return languages
