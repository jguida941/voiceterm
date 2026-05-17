"""Provenance helpers for plan-intent rows."""

from __future__ import annotations

from ...runtime.master_plan_contract import IngestionProvenance
from .plan_intake_sources import PlanIntentSource


def provenance(
    source: PlanIntentSource,
    *,
    source_hash: str,
    observed_at: str,
    source_line: int = 1,
) -> IngestionProvenance:
    """Build source provenance for a plan-intent row."""
    return IngestionProvenance(
        source_file=source.ref,
        source_line=source_line,
        source_kind=f"PlanIntentIngestion:{source.kind}",
        source_hash=source_hash,
        observed_at_utc=observed_at,
        section_authority="plan_intent_ingest",
    )


__all__ = ["provenance"]
