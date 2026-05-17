"""PlanRow coercion for plan-intent ingestion."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from ...governance.master_plan_ingestion import MarkdownChecklistAdapter
from ...runtime.master_plan_contract import (
    PlanRow,
    SDLCStage,
    hydrate_plan_row_commit_anchor_ref,
)
from .plan_intake_decomposition import decomposed_packet_rows
from .plan_intake_evidence import anchor_refs, dedupe, work_evidence_refs
from .plan_intake_phase0 import ParsedPlanAuthoritySections
from .plan_intake_provenance import provenance
from .plan_intake_sources import PlanIntentSource
from .plan_intake_support import target_ref_from_source, text
from .plan_intake_titles import packet_slug, source_title


def rows_from_source(
    args: Any,
    *,
    source: PlanIntentSource,
    source_hash: str,
    observed_at: str,
    authority_sections: ParsedPlanAuthoritySections | None = None,
) -> tuple[PlanRow, ...]:
    """Return PlanRows derived from an explicit row, checklist, or packet."""
    explicit_row_id = text(getattr(args, "plan_row_id", ""))
    if explicit_row_id:
        return (
            _explicit_plan_row(
                args,
                source=source,
                source_hash=source_hash,
                observed_at=observed_at,
            ),
        )

    parsed_sections = authority_sections or ParsedPlanAuthoritySections()
    if parsed_sections.rows_to_ingest:
        return tuple(
            _plan_section_row(
                row_id=item.row_id,
                title=item.title,
                source_line=item.source_line,
                args=args,
                source=source,
                source_hash=source_hash,
                observed_at=observed_at,
            )
            for item in parsed_sections.rows_to_ingest
        )

    rows = tuple(MarkdownChecklistAdapter().ingest(source.body, source.ref))
    if rows:
        return tuple(
            _row_with_intent_defaults(
                row,
                args=args,
                source=source,
                source_hash=source_hash,
                observed_at=observed_at,
            )
            for row in rows
        )

    if source.packet_payload:
        decomposed_rows = decomposed_packet_rows(source.body)
        if decomposed_rows:
            return tuple(
                _decomposed_packet_row(
                    row_id=item.row_id,
                    title=item.title,
                    source_line=item.source_line,
                    args=args,
                    source=source,
                    source_hash=source_hash,
                    observed_at=observed_at,
                )
                for item in decomposed_rows
            )
        return (
            _explicit_plan_row(
                args,
                source=source,
                source_hash=source_hash,
                observed_at=observed_at,
                fallback_row_id=f"PKT-BIND-{packet_slug(text(source.packet_payload.get('packet_id')))}",
            ),
        )
    return ()


def _decomposed_packet_row(
    *,
    row_id: str,
    title: str,
    source_line: int,
    args: Any,
    source: PlanIntentSource,
    source_hash: str,
    observed_at: str,
) -> PlanRow:
    packet = source.packet_payload
    packet_id = text(packet.get("packet_id"))
    return PlanRow(
        row_id=row_id,
        title=title or row_id,
        status=text(getattr(args, "plan_status", "")) or "queued",
        sdlc_stage=SDLCStage.normalize(
            getattr(args, "sdlc_stage", ""),
            default=SDLCStage.SPEC,
        ),
        sourced_from_packets=(packet_id,) if packet_id else (),
        work_evidence_ids=work_evidence_refs(source, packet_id=packet_id),
        source_doc_path=source.ref,
        source_line=source_line,
        content_hash=source_hash,
        provenance=provenance(
            source,
            source_hash=source_hash,
            observed_at=observed_at,
            source_line=source_line,
        ),
        anchor_refs=anchor_refs(args, packet_id=packet_id),
        target_ref=target_ref_from_source(args, source),
        mutation_op=_mutation_op(args, source),
    )


def _plan_section_row(
    *,
    row_id: str,
    title: str,
    source_line: int,
    args: Any,
    source: PlanIntentSource,
    source_hash: str,
    observed_at: str,
) -> PlanRow:
    packet = source.packet_payload
    packet_id = text(packet.get("packet_id"))
    return PlanRow(
        row_id=row_id,
        title=title or row_id,
        status=text(getattr(args, "plan_status", "")) or "queued",
        sdlc_stage=SDLCStage.normalize(
            getattr(args, "sdlc_stage", ""),
            default=SDLCStage.SPEC,
        ),
        sourced_from_packets=(packet_id,) if packet_id else (),
        work_evidence_ids=work_evidence_refs(source, packet_id=packet_id),
        source_doc_path=source.ref,
        source_line=source_line,
        content_hash=source_hash,
        provenance=provenance(
            source,
            source_hash=source_hash,
            observed_at=observed_at,
            source_line=source_line,
        ),
        anchor_refs=anchor_refs(args, packet_id=packet_id),
        target_ref=target_ref_from_source(args, source),
        mutation_op=_mutation_op(args, source),
    )


def _explicit_plan_row(
    args: Any,
    *,
    source: PlanIntentSource,
    source_hash: str,
    observed_at: str,
    fallback_row_id: str = "",
) -> PlanRow:
    packet = source.packet_payload
    packet_id = text(packet.get("packet_id"))
    return PlanRow(
        row_id=text(getattr(args, "plan_row_id", "")) or fallback_row_id,
        title=text(getattr(args, "title", "")) or source_title(source),
        status=text(getattr(args, "plan_status", "")) or "queued",
        sdlc_stage=SDLCStage.normalize(
            getattr(args, "sdlc_stage", ""),
            default=SDLCStage.SPEC,
        ),
        sourced_from_packets=(packet_id,) if packet_id else (),
        work_evidence_ids=work_evidence_refs(source, packet_id=packet_id),
        source_doc_path=source.ref,
        source_line=1,
        content_hash=source_hash,
        provenance=provenance(source, source_hash=source_hash, observed_at=observed_at),
        anchor_refs=anchor_refs(args, packet_id=packet_id),
        target_ref=target_ref_from_source(args, source),
        mutation_op=_mutation_op(args, source),
    )


def _row_with_intent_defaults(
    row: PlanRow,
    *,
    args: Any,
    source: PlanIntentSource,
    source_hash: str,
    observed_at: str,
) -> PlanRow:
    row_anchor_refs = dedupe(
        list(row.anchor_refs) + list(getattr(args, "anchor_refs", ()) or ())
    )
    return hydrate_plan_row_commit_anchor_ref(
        replace(
            row,
            source_doc_path=source.ref,
            content_hash=source_hash,
            provenance=provenance(
                source,
                source_hash=source_hash,
                observed_at=observed_at,
                source_line=row.source_line,
            ),
            anchor_refs=row_anchor_refs,
            target_ref=text(getattr(args, "target_ref", "")) or row.target_ref,
            mutation_op=(
                text(getattr(args, "mutation_op", ""))
                or row.mutation_op
                or "ingest_plan_intent"
            ),
        )
    )


def _mutation_op(args: Any, source: PlanIntentSource) -> str:
    packet = source.packet_payload
    return (
        text(getattr(args, "mutation_op", ""))
        or text(packet.get("mutation_op"))
        or text(packet.get("requested_action"))
        or "ingest_plan_intent"
    )

__all__ = ["rows_from_source"]
