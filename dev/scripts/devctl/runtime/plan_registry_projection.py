"""Shared projections over typed plan/doc registry entries."""

from __future__ import annotations

from pathlib import Path
import re

from .project_governance import DocRegistry, PlanRegistry, PlanRegistryEntry, ProjectGovernance

_MP_RANGE_RE = re.compile(r"MP-(?P<start>\d+)\s*\.\.\s*MP-(?P<end>\d+)")
_MP_TOKEN_RE = re.compile(r"MP-(?P<num>\d+)")
_SCOPED_DOC_CLASSES = frozenset({"tracker", "spec", "runbook", "reference"})
_SKIPPED_SCOPED_ARTIFACT_ROLES = frozenset(
    {
        "compatibility_projection",
        "docs_authority",
        "generated_surface",
        "plan_registry",
        "shared_backlog",
    }
)


def plan_registry_rows(
    plan_registry: PlanRegistry | None,
) -> dict[str, dict[str, str]]:
    """Project plan-registry entries into the legacy row shape."""
    if plan_registry is None:
        return {}
    rows: dict[str, dict[str, str]] = {}
    for entry in plan_registry.entries:
        path = str(entry.path or "").strip()
        if not path:
            continue
        rows[path] = {
            "role": str(entry.role or "").strip(),
            "authority": str(entry.authority or "").strip(),
            "scope": str(entry.scope or "").strip(),
            "when": str(entry.when_agents_read or "").strip(),
        }
    return rows


def plan_index_by_mp(
    plan_registry: PlanRegistry | None,
) -> dict[str, tuple[str, ...]]:
    """Return ``{MP-id: (plan_doc_path, ...)}`` from typed plan-registry state."""
    mapping: dict[str, list[str]] = {}
    for path, row in plan_registry_rows(plan_registry).items():
        for mp_id in _iter_mp_ids(str(row.get("scope") or "")):
            bucket = mapping.setdefault(mp_id, [])
            if path not in bucket:
                bucket.append(path)
    return {mp_id: tuple(paths) for mp_id, paths in mapping.items()}


def resolve_plan_path_for_scope(
    plan_registry: PlanRegistry | None,
    scope_token: str,
) -> str:
    """Return the first plan path whose scope matches the given MP token."""
    for path, row in plan_registry_rows(plan_registry).items():
        if scope_cell_matches(scope_token=scope_token, scope_cell=row.get("scope", "")):
            return path
    return ""


def resolve_governed_doc_path_for_scope(
    governance: ProjectGovernance | None,
    scope_token: str,
) -> str:
    """Return the best typed governed-doc path for a scoped MP token."""
    if governance is None:
        return ""

    governed_path = resolve_plan_path_for_scope(governance.plan_registry, scope_token)
    if governed_path:
        return governed_path

    return resolve_doc_registry_path_for_scope(
        governance.doc_registry,
        scope_token,
        exclude_paths=(
            governance.plan_registry.index_path,
            governance.plan_registry.registry_path,
        ),
    )


def resolve_doc_registry_path_for_scope(
    doc_registry: DocRegistry | None,
    scope_token: str,
    *,
    exclude_paths: tuple[str, ...] = (),
) -> str:
    """Return the first typed governed-doc companion path for a scoped MP token."""
    if doc_registry is None:
        return ""

    excluded_paths = {
        str(path or "").strip()
        for path in exclude_paths
        if str(path or "").strip()
    }
    active_root = _active_docs_root(doc_registry)
    for entry in doc_registry.entries:
        path = str(entry.path or "").strip()
        if not path or path in excluded_paths:
            continue
        if active_root and not _path_in_root(path, active_root):
            continue
        if str(entry.doc_class or "").strip() not in _SCOPED_DOC_CLASSES:
            continue
        if str(entry.artifact_role or "").strip() in _SKIPPED_SCOPED_ARTIFACT_ROLES:
            continue
        if str(entry.authority_kind or "").strip() == "compatibility_only":
            continue
        if scope_cell_matches(scope_token=scope_token, scope_cell=str(entry.scope or "")):
            return path
    return ""


def scope_cell_matches(*, scope_token: str, scope_cell: str) -> bool:
    """Return whether an MP token is present in one plan-registry scope cell."""
    token_match = _MP_TOKEN_RE.fullmatch(scope_token.strip())
    if token_match is None:
        return False
    target = int(token_match.group("num"))
    for range_match in _MP_RANGE_RE.finditer(scope_cell):
        start = int(range_match.group("start"))
        end = int(range_match.group("end"))
        if start <= target <= end:
            return True
    for token in _MP_TOKEN_RE.finditer(scope_cell):
        if int(token.group("num")) == target:
            return True
    return False


def _iter_mp_ids(scope_cell: str) -> tuple[str, ...]:
    mp_ids: list[str] = []
    for token in _MP_TOKEN_RE.finditer(scope_cell):
        mp_id = token.group(0)
        if mp_id not in mp_ids:
            mp_ids.append(mp_id)
    return tuple(mp_ids)


def _active_docs_root(doc_registry: DocRegistry) -> str:
    index_path = str(doc_registry.index_path or "").strip()
    if not index_path:
        return ""
    parent = Path(index_path).parent.as_posix().strip("/")
    return parent


def _path_in_root(path: str, root: str) -> bool:
    normalized_path = path.strip().strip("/")
    normalized_root = root.strip().strip("/")
    if not normalized_root:
        return True
    return normalized_path == normalized_root or normalized_path.startswith(
        f"{normalized_root}/"
    )


def render_index_projection(plan_registry: PlanRegistry) -> str:
    """Render INDEX.md content as a bounded projection from PlanRegistry.

    Produces a markdown registry table matching the existing INDEX.md format
    so the markdown file becomes a deterministic rendering over typed state
    rather than hand-edited mutable authority.
    """
    lines: list[str] = [
        "# Active Docs Index",
        "",
        "<!-- Generated projection from PlanRegistry. Do not hand-edit. -->",
        "",
        "## Registry",
        "",
        "| Path | Role | Execution authority | MP scope | When agents read |",
        "|---|---|---|---|---|",
    ]
    for entry in plan_registry.entries:
        path = str(entry.path or "").strip()
        if not path:
            continue
        lines.append(_index_row(entry))
    lines.append("")
    return "\n".join(lines)


def _index_row(entry: PlanRegistryEntry) -> str:
    """Format one PlanRegistryEntry as an INDEX.md table row."""
    path = f"`{entry.path}`"
    role = f"`{entry.role}`" if entry.role else ""
    authority = f"`{entry.authority}`" if entry.authority else ""
    scope = str(entry.scope or "")
    when = str(entry.when_agents_read or "")
    return f"| {path} | {role} | {authority} | {scope} | {when} |"


_LIFECYCLE_ORDER = ("active", "complete", "deferred", "unknown")


def render_master_plan_projection(plan_registry: PlanRegistry) -> str:
    """Render MASTER_PLAN.md plan-entry listing from PlanRegistry.

    Groups entries by lifecycle and renders each with title, scope, role,
    and path so the plan tracker becomes a bounded projection over typed
    state rather than hand-edited prose.
    """
    lines: list[str] = [
        "# Master Plan (Active, Unified)",
        "",
        "<!-- Generated projection from PlanRegistry. Do not hand-edit. -->",
        "",
    ]
    grouped = _group_by_lifecycle(plan_registry)
    for lifecycle in _LIFECYCLE_ORDER:
        entries = grouped.get(lifecycle)
        if not entries:
            continue
        heading = _lifecycle_heading(lifecycle)
        lines.append(f"## {heading}")
        lines.append("")
        for entry in entries:
            lines.extend(_master_plan_entry_lines(entry))
        lines.append("")
    leftover = sorted(set(grouped) - set(_LIFECYCLE_ORDER))
    for lifecycle in leftover:
        entries = grouped[lifecycle]
        heading = _lifecycle_heading(lifecycle)
        lines.append(f"## {heading}")
        lines.append("")
        for entry in entries:
            lines.extend(_master_plan_entry_lines(entry))
        lines.append("")
    return "\n".join(lines)


def _group_by_lifecycle(
    plan_registry: PlanRegistry,
) -> dict[str, list[PlanRegistryEntry]]:
    """Group plan-registry entries by lifecycle for MASTER_PLAN rendering."""
    grouped: dict[str, list[PlanRegistryEntry]] = {}
    for entry in plan_registry.entries:
        lifecycle = str(entry.lifecycle or "unknown").strip() or "unknown"
        grouped.setdefault(lifecycle, []).append(entry)
    return grouped


def _lifecycle_heading(lifecycle: str) -> str:
    """Map a lifecycle value to a human-readable MASTER_PLAN section heading."""
    headings = {
        "active": "Active Plans",
        "complete": "Completed Plans",
        "deferred": "Deferred Plans",
        "unknown": "Uncategorized Plans",
    }
    return headings.get(lifecycle, f"Plans ({lifecycle})")


def _master_plan_entry_lines(entry: PlanRegistryEntry) -> list[str]:
    """Render one PlanRegistryEntry as MASTER_PLAN bullet lines."""
    title = str(entry.title or "").strip() or Path(entry.path).stem
    path = str(entry.path or "").strip()
    scope = str(entry.scope or "").strip()
    role = str(entry.role or "").strip()
    parts = [f"- **{title}** (`{path}`)"]
    details: list[str] = []
    if scope:
        details.append(f"Scope: {scope}")
    if role:
        details.append(f"Role: {role}")
    if entry.authority:
        details.append(f"Authority: {entry.authority}")
    if details:
        parts.append(f"  - {' | '.join(details)}")
    return parts


__all__ = [
    "render_index_projection",
    "render_master_plan_projection",
    "resolve_doc_registry_path_for_scope",
    "resolve_governed_doc_path_for_scope",
    "plan_index_by_mp",
    "plan_registry_rows",
    "resolve_plan_path_for_scope",
    "scope_cell_matches",
]
