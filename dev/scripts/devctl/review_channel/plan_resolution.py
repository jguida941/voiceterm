"""Resolve scoped promotion plans from explicit, bridge, or tracker state."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..markdown_sections import parse_markdown_sections
from ..repo_packs import active_path_config

_BACKTICK_PATH_RE = re.compile(r"`(?P<path>[^`]+?\.md)`")
_PLAIN_PATH_RE = re.compile(r"\bdev/active/[A-Za-z0-9._/-]+\.md\b")
_NEXT_SCOPED_RE = re.compile(
    r"(?i)next scoped plan item\s*\((?P<path>[^)]+?\.md)\)"
)
_MASTER_MAIN_SCOPE_RE = re.compile(
    r"(?im)^-\s*Current main product lane:\s*`(?P<scope>MP-\d+)`"
)
_MASTER_EXEC_SCOPE_RE = re.compile(
    r"(?im)^-\s*Current\s+`(?P<scope>MP-\d+)`\s+execution branch:"
)
_INDEX_ROW_RE = re.compile(
    r"^\|\s*`(?P<path>[^`]+)`\s*\|\s*`(?P<role>[^`]+)`\s*\|\s*`(?P<authority>[^`]+)`\s*\|\s*`(?P<scope>[^`]+)`\s*\|"
)
_MP_RANGE_RE = re.compile(r"MP-(?P<start>\d+)\s*\.\.\s*MP-(?P<end>\d+)")
_MP_TOKEN_RE = re.compile(r"MP-(?P<num>\d+)")


@dataclass(frozen=True)
class PlanResolution:
    path: Path | None
    source: str
    detail: str = ""


def resolve_promotion_plan_path(
    *,
    repo_root: Path,
    bridge_path: Path | None,
    explicit_plan_path: Path | None,
) -> PlanResolution:
    """Resolve one scoped plan path without default-file guessing."""
    if explicit_plan_path is not None:
        if explicit_plan_path.exists():
            return PlanResolution(
                path=explicit_plan_path,
                source="explicit",
            )
        return PlanResolution(
            path=None,
            source="explicit_missing",
            detail=f"Explicit promotion plan path does not exist: {explicit_plan_path}",
        )

    bridge_path_resolution = _resolve_from_bridge(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    if bridge_path_resolution.path is not None:
        return bridge_path_resolution

    tracker_resolution = _resolve_from_master_tracker(repo_root=repo_root)
    if tracker_resolution.path is not None:
        return tracker_resolution

    if bridge_path_resolution.detail:
        return bridge_path_resolution
    return tracker_resolution


def _resolve_from_bridge(
    *,
    repo_root: Path,
    bridge_path: Path | None,
) -> PlanResolution:
    if bridge_path is None or not bridge_path.exists():
        return PlanResolution(path=None, source="bridge_missing", detail="Bridge file missing.")
    try:
        bridge_text = bridge_path.read_text(encoding="utf-8")
    except OSError as exc:
        return PlanResolution(path=None, source="bridge_read_error", detail=str(exc))
    sections = parse_markdown_sections(bridge_text)
    current_instruction = sections.get("Current Instruction For Claude", "")
    instruction_match = _NEXT_SCOPED_RE.search(current_instruction)
    if instruction_match is not None:
        candidate = _normalize_repo_path(
            repo_root=repo_root,
            raw=instruction_match.group("path"),
        )
        if candidate is not None:
            return PlanResolution(path=candidate, source="bridge_instruction")

    for section_name in ("Plan Alignment", "Last Reviewed Scope"):
        section_body = sections.get(section_name, "")
        for raw in _iter_section_plan_candidates(section_body):
            candidate = _normalize_repo_path(repo_root=repo_root, raw=raw)
            if candidate is not None:
                return PlanResolution(path=candidate, source=f"bridge_{section_name.lower().replace(' ', '_')}")
    return PlanResolution(
        path=None,
        source="bridge_scope_missing",
        detail="Bridge does not declare a resolvable scoped plan path.",
    )


def _resolve_from_master_tracker(*, repo_root: Path) -> PlanResolution:
    path_config = active_path_config()
    master_path = (repo_root / path_config.active_master_plan_doc_rel).resolve()
    index_path = (repo_root / path_config.active_index_doc_rel).resolve()
    if not master_path.exists():
        return PlanResolution(
            path=None,
            source="tracker_missing",
            detail=f"Tracker missing: {master_path}",
        )
    if not index_path.exists():
        return PlanResolution(
            path=None,
            source="index_missing",
            detail=f"Active index missing: {index_path}",
        )
    try:
        master_text = master_path.read_text(encoding="utf-8")
        index_text = index_path.read_text(encoding="utf-8")
    except OSError as exc:
        return PlanResolution(path=None, source="tracker_read_error", detail=str(exc))
    scope = _active_scope_token(master_text)
    if scope is None:
        return PlanResolution(
            path=None,
            source="tracker_scope_missing",
            detail="Tracker does not expose a current active MP scope token.",
        )
    for line in index_text.splitlines():
        row_match = _INDEX_ROW_RE.match(line.strip())
        if row_match is None:
            continue
        scope_cell = row_match.group("scope")
        if not _mp_scope_cell_matches(scope_token=scope, scope_cell=scope_cell):
            continue
        candidate = _normalize_repo_path(
            repo_root=repo_root,
            raw=row_match.group("path"),
        )
        if candidate is not None:
            return PlanResolution(path=candidate, source="tracker_scope")
    return PlanResolution(
        path=None,
        source="tracker_scope_unmapped",
        detail=f"Active scope {scope} is not mapped to a plan path in INDEX.md.",
    )


def _iter_section_plan_candidates(section_body: str) -> list[str]:
    candidates: list[str] = []
    for match in _BACKTICK_PATH_RE.finditer(section_body or ""):
        candidates.append(match.group("path").strip())
    for match in _PLAIN_PATH_RE.finditer(section_body or ""):
        candidates.append(match.group(0).strip())
    return candidates


def _normalize_repo_path(*, repo_root: Path, raw: str) -> Path | None:
    raw_stripped = str(raw or "").strip()
    if not raw_stripped:
        return None
    candidate = Path(raw_stripped)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (repo_root / candidate).resolve()
    if not resolved.exists() or resolved.suffix.lower() != ".md":
        return None
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return resolved


def _active_scope_token(master_text: str) -> str | None:
    main_match = _MASTER_MAIN_SCOPE_RE.search(master_text)
    if main_match is not None:
        return main_match.group("scope")
    exec_match = _MASTER_EXEC_SCOPE_RE.search(master_text)
    if exec_match is not None:
        return exec_match.group("scope")
    return None


def _mp_scope_cell_matches(*, scope_token: str, scope_cell: str) -> bool:
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
