"""Scanner and report helpers for doc-authority."""

from __future__ import annotations

import re
from pathlib import Path

from .doc_authority_layout import load_governed_doc_layout, path_in_root, registry_managed
from .doc_authority_metadata import lifecycle_from_meta, parse_metadata_header
from .doc_authority_models import PLAN_DOC_CLASSES, REQUIRED_SECTIONS, DocRecord, GovernedDocLayout
from .doc_authority_rules import (
    check_budget,
    classify_doc,
    consumer_from_registry,
    parse_index_registry,
)

_MP_SCOPE_RE = re.compile(r"MP-\d+")


def scan_governed_docs(
    repo_root: Path,
    *,
    policy_path: str | Path | None = None,
) -> list[DocRecord]:
    """Scan governed markdown files and build DocRecord instances."""
    layout = load_governed_doc_layout(repo_root, policy_path=policy_path)
    index_path = repo_root / layout.index_path
    registry = parse_index_registry(index_path)
    records: list[DocRecord] = []
    seen: set[str] = set()

    for relative_root, is_active in (
        (layout.active_docs_root, True),
        (layout.guides_root, False),
    ):
        if not relative_root:
            continue
        scan_dir = repo_root / relative_root
        if not scan_dir.is_dir():
            continue
        for md_file in sorted(scan_dir.glob("*.md")):
            rel = md_file.relative_to(repo_root).as_posix()
            if rel in seen:
                continue
            seen.add(rel)
            records.append(_build_record(md_file, rel, registry, layout, is_active))

    for root_file in layout.root_files:
        full_path = repo_root / root_file
        if not full_path.is_file() or root_file in seen:
            continue
        seen.add(root_file)
        records.append(_build_record(full_path, root_file, registry, layout, False))

    return records


def _build_record(
    md_file: Path,
    rel: str,
    registry: dict[str, dict[str, str]],
    layout: GovernedDocLayout,
    is_active: bool,
) -> DocRecord:
    text = md_file.read_text(encoding="utf-8", errors="replace")
    line_count = text.count("\n") + 1
    meta = parse_metadata_header(text)
    reg_entry = registry.get(rel)
    doc_class = classify_doc(
        md_file,
        text,
        is_active,
        rel=rel,
        reg_entry=reg_entry,
        layout=layout,
    )
    budget_status, budget_limit = check_budget(line_count, doc_class)
    missing_sections = (
        tuple(section for section in REQUIRED_SECTIONS if section not in text)
        if doc_class in PLAN_DOC_CLASSES
        else ()
    )
    lifecycle = lifecycle_from_meta(meta)
    managed = registry_managed(rel, layout)
    in_index = reg_entry is not None
    return DocRecord(
        path=rel,
        doc_class=doc_class,
        owner=meta.get("owner", ""),
        authority=reg_entry["authority"] if reg_entry else "",
        lifecycle=lifecycle,
        scope=reg_entry["scope"] if reg_entry else "",
        canonical_consumer=consumer_from_registry(reg_entry),
        line_count=line_count,
        budget_status=budget_status,
        budget_limit=budget_limit,
        has_metadata_header=bool(meta),
        has_required_sections=not missing_sections,
        missing_sections=missing_sections,
        registry_managed=managed,
        in_index=in_index,
        issues=_collect_record_issues(
            meta=meta,
            registration_state=(managed, in_index),
            budget_status=budget_status,
            budget_context=(line_count, budget_limit),
            doc_class=doc_class,
            missing_sections=missing_sections,
        ),
        consolidation_signals=_consolidation_signals(
            rel=rel,
            doc_class=doc_class,
            lifecycle=lifecycle,
            line_count=line_count,
            layout=layout,
        ),
    )


def _collect_record_issues(
    *,
    meta: dict[str, str],
    registration_state: tuple[bool, bool],
    budget_status: str,
    budget_context: tuple[int, int],
    doc_class: str,
    missing_sections: tuple[str, ...],
) -> tuple[str, ...]:
    issues: list[str] = []
    registry_managed, in_index = registration_state
    line_count, budget_limit = budget_context
    if not meta:
        issues.append("missing metadata header")
    if registry_managed and not in_index:
        issues.append("not registered in INDEX.md")
    if budget_status == "exceeded":
        issues.append(f"budget exceeded ({line_count} > {budget_limit})")
    if doc_class in PLAN_DOC_CLASSES and missing_sections:
        issues.append(f"missing sections: {', '.join(missing_sections)}")
    return tuple(issues)


def _consolidation_signals(
    *,
    rel: str,
    doc_class: str,
    lifecycle: str,
    line_count: int,
    layout: GovernedDocLayout,
) -> tuple[str, ...]:
    signals: list[str] = []
    if lifecycle == "complete" and path_in_root(rel, layout.active_docs_root):
        signals.append("lifecycle complete — candidate for archive")
    if doc_class == "reference" and line_count < 50:
        signals.append("tiny reference doc — consider inlining")
    return tuple(signals)


def detect_authority_overlaps(records: list[DocRecord]) -> list[dict[str, object]]:
    """Find docs that share the same MP scope references."""
    mp_to_docs: dict[str, list[str]] = {}
    for record in records:
        for mp_scope in _MP_SCOPE_RE.findall(record.scope):
            mp_to_docs.setdefault(mp_scope, []).append(record.path)
    return [
        {"mp": mp_scope, "docs": docs}
        for mp_scope, docs in sorted(mp_to_docs.items())
        if len(docs) > 1
    ]


def detect_consolidation_candidates(
    records: list[DocRecord],
) -> list[dict[str, object]]:
    """Find docs that are candidates for merge, archive, or inlining."""
    candidates: list[dict[str, object]] = []
    for record in records:
        if not record.consolidation_signals:
            continue
        candidates.append(
            {
                "path": record.path,
                "signals": list(record.consolidation_signals),
                "lifecycle": record.lifecycle,
                "line_count": record.line_count,
            }
        )
    return candidates
