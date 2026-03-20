"""Classification and registry helpers for doc-authority."""

from __future__ import annotations

import re
from pathlib import Path

from .doc_authority_layout import path_in_root
from .doc_authority_metadata import parse_metadata_header
from .doc_authority_models import BUDGET_LIMITS, ROLE_TO_DOC_CLASS, GovernedDocLayout

_INDEX_ROW_RE = re.compile(
    r"\|\s*`(?P<path>[^`]+)`\s*\|"
    r"\s*`(?P<role>[^`]+)`\s*\|"
    r"\s*`(?P<authority>[^`]+)`\s*\|"
    r"\s*(?P<scope>[^|]+)\|"
    r"\s*(?P<when>[^|]+)\|",
)


def classify_doc(
    path: Path,
    text: str,
    in_active: bool,
    *,
    rel: str | None = None,
    reg_entry: dict[str, str] | None = None,
    layout: GovernedDocLayout | None = None,
) -> str:
    """Return the doc class based on registry role, layout, and content."""
    role_class = _doc_class_from_role(reg_entry)
    if role_class:
        return role_class

    relative = rel or path.as_posix()
    if layout is not None:
        root_class = _doc_class_from_layout(path, relative, layout)
        if root_class:
            return root_class
    if "dev/guides/" in path.as_posix():
        return "guide"
    if in_active:
        return _active_doc_class(path, text)
    return "reference"


def _doc_class_from_role(reg_entry: dict[str, str] | None) -> str:
    role = (reg_entry or {}).get("role", "").strip().lower()
    return ROLE_TO_DOC_CLASS.get(role, "")


def _doc_class_from_layout(
    path: Path,
    relative: str,
    layout: GovernedDocLayout,
) -> str:
    name_upper = path.name.upper()
    if relative == layout.bridge_path:
        return "generated_report"
    if relative == layout.docs_authority_path:
        return "guide"
    if path.parent == layout.repo_root and "INDEX" in name_upper:
        return "guide"
    if path_in_root(relative, layout.guides_root):
        return "guide"
    if relative == layout.tracker_path:
        return "tracker"
    if relative == layout.index_path:
        return "reference"
    return ""


def _active_doc_class(path: Path, text: str) -> str:
    status = parse_metadata_header(text).get("status", "").lower()
    name_upper = path.name.upper()
    has_scope = "## Scope" in text
    has_checklist = "## Execution Checklist" in text or "- [" in text
    if "reference" in status or name_upper == "README.MD":
        return "reference"
    if has_scope or has_checklist:
        return "spec"
    if text.count("\n") + 1 < 80:
        return "reference"
    return "spec"


def check_budget(line_count: int, doc_class: str) -> tuple[str, int]:
    """Return (budget_status, applicable_limit) for the given line count."""
    soft, hard = BUDGET_LIMITS.get(doc_class, (None, None))
    if hard is not None and line_count > hard:
        return "exceeded", hard
    if soft is not None and line_count > soft:
        return "warning", soft
    return "ok", soft or 0


def parse_index_registry(index_path: Path) -> dict[str, dict[str, str]]:
    """Parse INDEX.md table rows into a dict keyed by relative path."""
    registry: dict[str, dict[str, str]] = {}
    if not index_path.is_file():
        return registry
    text = index_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        match = _INDEX_ROW_RE.match(line)
        if not match:
            continue
        registry[match.group("path")] = {
            "role": match.group("role").strip(),
            "authority": match.group("authority").strip(),
            "scope": match.group("scope").strip(),
            "when": match.group("when").strip(),
        }
    return registry


def consumer_from_registry(reg_entry: dict[str, str] | None) -> str:
    if not reg_entry:
        return ""
    return reg_entry.get("when", "").strip()
