"""Shared projections over typed PlanRegistry entries."""

from __future__ import annotations

import re

from .project_governance import PlanRegistry

_MP_RANGE_RE = re.compile(r"MP-(?P<start>\d+)\s*\.\.\s*MP-(?P<end>\d+)")
_MP_TOKEN_RE = re.compile(r"MP-(?P<num>\d+)")


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


__all__ = [
    "plan_index_by_mp",
    "plan_registry_rows",
    "resolve_plan_path_for_scope",
    "scope_cell_matches",
]
