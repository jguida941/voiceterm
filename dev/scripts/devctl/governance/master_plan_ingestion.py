"""Repo-agnostic master-plan ingestion adapters."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from ..runtime.master_plan_contract import (
    ExplainBackReceipt,
    IngestedDoc,
    IngestionDrift,
    IngestionPolicy,
    IngestionProvenance,
    MasterPlan,
    PlanRow,
    SDLCStage,
)
from ..runtime.master_plan_store import plan_revision_for_rows
from ..time_utils import utc_timestamp

_ROW_ID_RE = (
    r"MP[0-9A-Za-z._-]+(?:-P[0-9A-Za-z._-]+)?"
    r"(?:-T[0-9A-Za-z._-]+)?"
)
_CHECKLIST_RE = re.compile(
    r"^\s*-\s*\[(?P<mark>[ xX])\]\s*`?"
    rf"(?P<row_id>{_ROW_ID_RE})`?\s*(?P<title>.*)$"
)


class IngestionAdapter(Protocol):
    adapter_id: str

    def match(self, path: Path, sniff: bytes) -> bool: ...

    def ingest(self, text: str, source_path: str) -> Iterable[PlanRow]: ...


class MarkdownChecklistAdapter:
    """Ingest `- [ ] MP...` markdown checklist rows into PlanRow records."""

    adapter_id = "markdown_checklist"

    def match(self, path: Path, sniff: bytes) -> bool:
        return path.suffix.lower() == ".md" and b"- [" in sniff

    def ingest(self, text: str, source_path: str) -> Iterable[PlanRow]:
        rows, _rejections = self._ingest_with_rejections(text, source_path)
        return rows

    def ingest_doc(self, text: str, source_path: str) -> IngestedDoc:
        rows, rejections = self._ingest_with_rejections(text, source_path)
        observed_at = utc_timestamp()
        if rows:
            status = "accepted"
            reason = ""
        elif rejections:
            status = "rejected_unauthorized_section"
            reason = "; ".join(sorted(set(rejections)))
        else:
            status = "rejected_no_authority"
            reason = "no checklist authority rows found"
        return IngestedDoc(
            source_file=source_path,
            source_kind=self.__class__.__name__,
            status=status,
            reason=reason,
            rows=tuple(rows),
            observed_at_utc=observed_at,
        )

    def _ingest_with_rejections(
        self,
        text: str,
        source_path: str,
    ) -> tuple[tuple[PlanRow, ...], tuple[str, ...]]:
        rows: list[PlanRow] = []
        rejections: list[str] = []
        section = ""
        in_code_block = False
        observed_at = utc_timestamp()
        for index, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code_block = not in_code_block
                continue
            if stripped.startswith("#"):
                section = _section_title(stripped)
                continue
            match = _CHECKLIST_RE.match(line)
            if match is None:
                continue
            if in_code_block:
                rejections.append(f"line {index}: code block is not plan authority")
                continue
            if not _section_has_authority(section):
                section_label = section or "(no section)"
                rejections.append(
                    f"line {index}: section {section_label!r} is not live authority"
                )
                continue
            row_id = _normalize_row_id(match.group("row_id"))
            title = _clean_title(match.group("title"))
            status = "applied" if match.group("mark").lower() == "x" else "open"
            source_hash = _content_hash(line)
            rows.append(PlanRow(
                row_id=row_id,
                title=title or row_id,
                status=status,
                sdlc_stage=SDLCStage.IMPL,
                source_doc_path=source_path,
                source_line=index,
                content_hash=source_hash,
                provenance=IngestionProvenance(
                    source_file=source_path,
                    source_line=index,
                    source_kind=self.__class__.__name__,
                    source_hash=source_hash,
                    observed_at_utc=observed_at,
                    section_authority="owner_doc",
                ),
            ))
        return tuple(rows), tuple(rejections)


class ProseSeedAdapter:
    """Greenfield fallback that asks the operator to explain the repo goal."""

    adapter_id = "prose_seed"

    def match(self, path: Path, sniff: bytes) -> bool:
        return path.suffix.lower() in {"", ".md", ".txt"}

    def ingest(self, text: str, source_path: str) -> Iterable[PlanRow]:
        if text.strip():
            return ()
        observed_at = utc_timestamp()
        return (
            PlanRow(
                row_id="SEED-REPO-PURPOSE",
                title="Describe the repository purpose and first SDLC goal",
                status="proposed",
                sdlc_stage=SDLCStage.IDEA,
                row_kind="seed",
                source_doc_path=source_path,
                source_line=1,
                content_hash=_content_hash(""),
                provenance=IngestionProvenance(
                    source_file=source_path,
                    source_line=1,
                    source_kind=self.__class__.__name__,
                    source_hash=_content_hash(""),
                    observed_at_utc=observed_at,
                    section_authority="greenfield_seed",
                ),
            ),
        )


def ingest_master_plan_markdown(
    *,
    repo_id: str,
    source_path: Path,
    source_rel: str,
    typed_store_rel: str,
    policy: IngestionPolicy | None = None,
) -> MasterPlan:
    """Ingest one markdown plan projection into a typed MasterPlan snapshot."""
    effective_policy = policy or IngestionPolicy()
    text = source_path.read_text(encoding="utf-8", errors="replace")
    rows = tuple(MarkdownChecklistAdapter().ingest(text, source_rel))
    if not rows and "prose_seed" in effective_policy.adapters:
        rows = tuple(ProseSeedAdapter().ingest("", source_rel))
    return MasterPlan(
        repo_id=repo_id,
        rows=rows,
        linked_docs=(),
        status="pending_explainback",
        last_ingested_at_utc=utc_timestamp(),
        plan_revision=plan_revision_for_rows(rows),
        source_path=source_rel,
        typed_store_path=typed_store_rel,
        projection_path=source_rel,
    )


def build_explain_back_receipt(
    *,
    master_plan: MasterPlan,
    repo_pack_id: str,
    receipt_id: str,
    pending_questions: tuple[str, ...] = (),
) -> ExplainBackReceipt:
    """Build a verification receipt for an ingested typed plan snapshot."""
    row_ids = tuple(row.row_id for row in master_plan.rows)
    summary = (
        f"Ingested {len(row_ids)} plan row(s) from "
        f"{master_plan.source_path or master_plan.projection_path} into "
        f"{master_plan.typed_store_path}."
    )
    if not row_ids:
        summary += " No executable rows were found; a seed plan row is expected."
    return ExplainBackReceipt(
        receipt_id=receipt_id,
        repo_pack_id=repo_pack_id,
        ingested_files=(master_plan.source_path or master_plan.projection_path,),
        derived_plan_rows=row_ids,
        nl_summary=summary,
        confidence=0.85 if row_ids else 0.55,
        pending_questions=pending_questions,
    )


def build_ingestion_drift(
    *,
    row_id: str,
    source_doc_path: str,
    expected_hash: str,
    observed_hash: str,
    reason: str,
) -> IngestionDrift:
    """Build the typed drift row emitted when projection and store disagree."""
    return IngestionDrift(
        row_id=row_id,
        source_doc_path=source_doc_path,
        expected_hash=expected_hash,
        observed_hash=observed_hash,
        reason=reason,
    )


def _normalize_row_id(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z._-]+", "-", value).strip("-")


def _clean_title(value: str) -> str:
    title = value.strip()
    return re.sub(r"\s+", " ", title)


def _content_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _section_title(line: str) -> str:
    return re.sub(r"^#+\s*", "", line).strip()


def _section_has_authority(section: str) -> bool:
    normalized = section.strip().lower()
    if not normalized:
        return True
    unauthorized_tokens = (
        "archive",
        "code block",
        "example",
        "fixture",
        "historical",
        "history",
        "reference",
        "retrospective",
        "sample",
        "test",
    )
    if any(token in normalized for token in unauthorized_tokens):
        return False
    authority_tokens = (
        "active",
        "execution",
        "master plan",
        "mp-",
        "owner",
        "plan",
        "roadmap",
        "scope",
        "task",
    )
    return any(token in normalized for token in authority_tokens)


__all__ = [
    "IngestionAdapter",
    "MarkdownChecklistAdapter",
    "ProseSeedAdapter",
    "build_explain_back_receipt",
    "build_ingestion_drift",
    "ingest_master_plan_markdown",
]
