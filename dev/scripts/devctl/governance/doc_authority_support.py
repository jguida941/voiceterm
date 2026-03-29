"""Scanner and report helpers for doc-authority."""

from __future__ import annotations

import re
from pathlib import Path

from .doc_authority_paths import path_in_root, registry_managed as registry_managed_path
from .doc_authority_metadata import lifecycle_from_meta, parse_metadata_header
from .doc_authority_models import (
    PLAN_DOC_CLASSES,
    REQUIRED_SECTIONS,
    DocRecord,
    GovernedDocLayout,
)
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
    from .doc_authority_layout import load_governed_doc_layout

    layout = load_governed_doc_layout(repo_root, policy_path=policy_path)
    return scan_governed_docs_for_layout(repo_root, layout)


def scan_governed_docs_for_layout(
    repo_root: Path,
    layout: GovernedDocLayout,
) -> list[DocRecord]:
    """Scan governed markdown files using an already-resolved layout."""
    index_path = repo_root / layout.index_path
    registry = parse_index_registry(index_path)
    records: list[DocRecord] = []
    seen: set[str] = set()

    for relative_root in _scan_roots(layout):
        if not relative_root:
            continue
        scan_dir = repo_root / relative_root
        if not scan_dir.is_dir():
            continue
        for md_file in sorted(scan_dir.rglob("*.md")):
            rel = md_file.relative_to(repo_root).as_posix()
            if rel in seen:
                continue
            seen.add(rel)
            records.append(_build_record(md_file, rel, registry, layout))

    for root_file in layout.root_files:
        full_path = repo_root / root_file
        if not full_path.is_file() or root_file in seen:
            continue
        seen.add(root_file)
        records.append(_build_record(full_path, root_file, registry, layout))

    return records


def _build_record(
    md_file: Path,
    rel: str,
    registry: dict[str, dict[str, str]],
    layout: GovernedDocLayout,
) -> DocRecord:
    text = md_file.read_text(encoding="utf-8", errors="replace")
    line_count = text.count("\n") + 1
    meta = parse_metadata_header(text)
    reg_entry = registry.get(rel)
    doc_class = classify_doc(
        md_file,
        text,
        path_in_root(rel, layout.active_docs_root),
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
    managed = registry_managed_path(rel, layout.active_docs_root, layout.index_path)
    in_index = reg_entry is not None
    artifact_role = _artifact_role(rel=rel, doc_class=doc_class, layout=layout)
    authority_kind = _authority_kind(
        artifact_role=artifact_role,
        authority=reg_entry["authority"] if reg_entry else "",
        doc_class=doc_class,
    )
    system_scope = _system_scope(
        rel=rel,
        scope=reg_entry["scope"] if reg_entry else "",
        artifact_role=artifact_role,
        layout=layout,
    )
    consumer_scope = _consumer_scope(
        artifact_role=artifact_role,
        system_scope=system_scope,
    )
    return DocRecord(
        path=rel,
        doc_class=doc_class,
        artifact_role=artifact_role,
        authority_kind=authority_kind,
        system_scope=system_scope,
        consumer_scope=consumer_scope,
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


def _artifact_role(*, rel: str, doc_class: str, layout: GovernedDocLayout) -> str:
    if rel == layout.bridge_path:
        return "compatibility_projection"
    if rel == layout.docs_authority_path:
        return "docs_authority"
    if rel == layout.shared_backlog_path:
        return "shared_backlog"
    if rel == layout.index_path:
        return "plan_registry"
    if rel == layout.tracker_path:
        return "execution_tracker"
    if doc_class in PLAN_DOC_CLASSES:
        return "execution_plan"
    if doc_class == "generated_report":
        return "generated_surface"
    return doc_class or "reference"


def _authority_kind(*, artifact_role: str, authority: str, doc_class: str) -> str:
    authority_text = authority.strip().lower()
    if artifact_role == "compatibility_projection":
        return "compatibility_only"
    if artifact_role == "shared_backlog":
        return "shared_intake"
    if authority_text == "canonical":
        return "canonical_markdown"
    if authority_text == "reference-only":
        return "reference_only"
    if authority_text == "supporting":
        return "supporting_context"
    if authority_text.startswith("mirrored"):
        return "mirrored_markdown"
    if artifact_role in {"docs_authority", "plan_registry", "execution_tracker"}:
        return "startup_authority"
    if artifact_role == "execution_plan":
        return "execution_authority"
    if doc_class == "reference":
        return "reference_only"
    return "supporting_context"


def _system_scope(
    *,
    rel: str,
    scope: str,
    artifact_role: str,
    layout: GovernedDocLayout,
) -> str:
    if artifact_role == "compatibility_projection":
        return "repo_pack_client"
    if artifact_role == "docs_authority":
        return "development_self_hosting"
    if artifact_role == "shared_backlog":
        return "repo_local"
    if artifact_role in {"plan_registry", "execution_tracker"}:
        return "platform_core"
    if artifact_role == "execution_plan":
        if rel.endswith("ai_governance_platform.md") or rel.endswith(
            "platform_authority_loop.md"
        ):
            return "platform_core"
        if "MP-376" in scope or "MP-377" in scope:
            return "platform_core"
        return "repo_pack_client"
    if artifact_role == "guide":
        return "development_self_hosting"
    return "repo_local"


def _consumer_scope(*, artifact_role: str, system_scope: str) -> str:
    if artifact_role == "compatibility_projection":
        return "review_runtime"
    if artifact_role == "shared_backlog":
        return "startup_default"
    if artifact_role in {"docs_authority", "plan_registry", "execution_tracker"}:
        return "startup_default"
    if artifact_role == "execution_plan":
        return "startup_default" if system_scope == "platform_core" else "lane_specific"
    if artifact_role == "guide":
        return "development_only"
    return "on_demand"


def _scan_roots(layout: GovernedDocLayout) -> tuple[str, ...]:
    roots: list[str] = []
    for candidate in (
        *layout.governed_doc_roots,
        layout.active_docs_root,
        layout.guides_root,
    ):
        normalized = candidate.strip().rstrip("/")
        if not normalized or normalized in roots:
            continue
        roots.append(normalized)
    return tuple(roots)


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
