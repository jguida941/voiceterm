"""Governed-markdown registry builders for governance-draft."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .doc_authority_models import (
    BUDGET_LIMITS,
    PLAN_DOC_CLASSES,
    REQUIRED_SECTIONS,
    GovernedDocLayout,
)
from .doc_authority_support import scan_governed_docs_for_layout
from ..runtime.project_governance import (
    BridgeConfig,
    DocBudget,
    DocPolicy,
    DocRegistry,
    DocRegistryEntry,
    PathRoots,
    PlanRegistry,
    PlanRegistryEntry,
)
from ..runtime.session_resume import extract_session_resume_state


@dataclass(frozen=True, slots=True)
class GovernedMarkdownScanInputs:
    """Typed inputs for the first governed-markdown registry scan."""

    path_roots: PathRoots
    bridge_config: BridgeConfig
    docs_authority: str
    index_path: str
    tracker_path: str
    governed_doc_roots: tuple[str, ...]
    startup_order: tuple[str, ...]


def _is_root_markdown_path(relative_path: str) -> bool:
    return "/" not in relative_path and relative_path.lower().endswith(".md")


def _build_governed_doc_layout(
    repo_root: Path,
    inputs: GovernedMarkdownScanInputs,
) -> GovernedDocLayout:
    root_files: set[str] = set()
    for candidate in (
        *inputs.startup_order,
        inputs.docs_authority,
        inputs.bridge_config.bridge_path,
    ):
        if not candidate:
            continue
        if not _is_root_markdown_path(candidate):
            continue
        if (repo_root / candidate).is_file():
            root_files.add(candidate)
    return GovernedDocLayout(
        repo_root=repo_root,
        active_docs_root=inputs.path_roots.active_docs,
        guides_root=inputs.path_roots.guides,
        governed_doc_roots=inputs.governed_doc_roots,
        index_path=inputs.index_path,
        tracker_path=inputs.tracker_path,
        docs_authority_path=inputs.docs_authority,
        bridge_path=(
            inputs.bridge_config.bridge_path
            if inputs.bridge_config.bridge_active
            else ""
        ),
        root_files=tuple(sorted(root_files)),
    )


def _scan_doc_policy(
    inputs: GovernedMarkdownScanInputs,
    *,
    plan_registry: PlanRegistry,
) -> DocPolicy:
    budget_limits = tuple(
        DocBudget(
            doc_class=doc_class,
            soft_limit=soft or 0,
            hard_limit=hard or 0,
        )
        for doc_class, (soft, hard) in sorted(BUDGET_LIMITS.items())
    )
    return DocPolicy(
        docs_authority_path=inputs.docs_authority,
        active_docs_root=inputs.path_roots.active_docs,
        guides_root=inputs.path_roots.guides,
        governed_doc_roots=inputs.governed_doc_roots,
        tracker_path=plan_registry.tracker_path,
        index_path=plan_registry.index_path,
        bridge_path=(
            inputs.bridge_config.bridge_path
            if inputs.bridge_config.bridge_active
            else ""
        ),
        allowed_doc_classes=tuple(sorted(BUDGET_LIMITS.keys())),
        allowed_authorities=(
            "canonical",
            "mirrored in MASTER_PLAN",
            "supporting",
            "reference-only",
        ),
        allowed_lifecycles=("active", "complete", "draft", "deferred", "unknown"),
        required_plan_sections=tuple(REQUIRED_SECTIONS),
        budget_limits=budget_limits,
    )


def _doc_title(text: str, fallback_path: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        return stripped.lstrip("#").strip() or fallback_path
    return fallback_path


def _scan_plan_registry(
    repo_root: Path,
    inputs: GovernedMarkdownScanInputs,
    *,
    records: list[object],
) -> PlanRegistry:
    entries: list[PlanRegistryEntry] = []
    for record in records:
        if getattr(record, "doc_class", "") not in PLAN_DOC_CLASSES:
            continue
        record_path = str(getattr(record, "path", ""))
        text = (repo_root / record_path).read_text(encoding="utf-8", errors="replace")
        entries.append(
            PlanRegistryEntry(
                path=record_path,
                role=str(getattr(record, "doc_class", "")),
                authority=str(getattr(record, "authority", "")),
                scope=str(getattr(record, "scope", "")),
                when_agents_read=str(getattr(record, "canonical_consumer", "")),
                title=_doc_title(text, record_path),
                owner=str(getattr(record, "owner", "")),
                lifecycle=str(getattr(record, "lifecycle", "unknown")),
                has_execution_plan_contract="Execution plan contract: required" in text,
                session_resume=extract_session_resume_state(text),
            )
        )
    return PlanRegistry(
        registry_path=inputs.index_path,
        tracker_path=inputs.tracker_path,
        index_path=inputs.index_path,
        entries=tuple(entries),
    )


def _scan_doc_registry(
    inputs: GovernedMarkdownScanInputs,
    *,
    plan_registry: PlanRegistry,
    records: list[object],
) -> DocRegistry:
    entries = tuple(
        DocRegistryEntry(
            path=str(getattr(record, "path", "")),
            doc_class=str(getattr(record, "doc_class", "")),
            authority=str(getattr(record, "authority", "")),
            lifecycle=str(getattr(record, "lifecycle", "")),
            scope=str(getattr(record, "scope", "")),
            owner=str(getattr(record, "owner", "")),
            canonical_consumer=str(getattr(record, "canonical_consumer", "")),
            line_count=int(getattr(record, "line_count", 0)),
            budget_status=str(getattr(record, "budget_status", "ok")),
            budget_limit=int(getattr(record, "budget_limit", 0)),
            registry_managed=bool(getattr(record, "registry_managed", False)),
            in_index=bool(getattr(record, "in_index", False)),
            issues=tuple(getattr(record, "issues", ())),
        )
        for record in records
    )
    return DocRegistry(
        docs_authority_path=inputs.docs_authority,
        index_path=plan_registry.index_path,
        tracker_path=plan_registry.tracker_path,
        entries=entries,
    )


def scan_governed_markdown_contracts(
    repo_root: Path,
    inputs: GovernedMarkdownScanInputs,
) -> tuple[PlanRegistry, DocPolicy, DocRegistry]:
    """Build the first typed plan/doc runtime contracts from governed markdown."""
    layout = _build_governed_doc_layout(repo_root, inputs)
    governed_docs = scan_governed_docs_for_layout(repo_root, layout)
    plan_registry = _scan_plan_registry(repo_root, inputs, records=governed_docs)
    doc_policy = _scan_doc_policy(inputs, plan_registry=plan_registry)
    doc_registry = _scan_doc_registry(
        inputs,
        plan_registry=plan_registry,
        records=governed_docs,
    )
    return plan_registry, doc_policy, doc_registry


__all__ = ["scan_governed_markdown_contracts"]
