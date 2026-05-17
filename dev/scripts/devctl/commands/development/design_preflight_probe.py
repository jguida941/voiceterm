"""Shared ground-truth probe row helpers for develop design-preflight."""

from __future__ import annotations

from .models import DevelopmentGroundTruthProbe


def ground_truth_probe(
    probe_id: str,
    status: str,
    summary: str,
    evidence_ref: str,
    fields: tuple[str, ...],
) -> DevelopmentGroundTruthProbe:
    return DevelopmentGroundTruthProbe(
        probe_id=probe_id,
        status=status,
        summary=summary,
        evidence_ref=evidence_ref,
        observed_fields=fields,
    )


__all__ = ["ground_truth_probe"]
