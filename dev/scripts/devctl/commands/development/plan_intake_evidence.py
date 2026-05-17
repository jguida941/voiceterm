"""Evidence and anchor helpers for plan-intent rows."""

from __future__ import annotations

from typing import Any

from .plan_intake_sources import PlanIntentSource
from .plan_intake_support import text


def anchor_refs(args: Any, *, packet_id: str) -> tuple[str, ...]:
    """Return CLI anchor refs plus the packet anchor when present."""
    return dedupe(
        list(getattr(args, "anchor_refs", ()) or ())
        + ([f"packet:{packet_id}"] if packet_id else [])
    )


def work_evidence_refs(
    source: PlanIntentSource,
    *,
    packet_id: str,
) -> tuple[str, ...]:
    """Return evidence refs for the source and packet."""
    evidence = [_evidence_ref(source)]
    if packet_id:
        evidence.insert(0, f"packet:{packet_id}")
    return dedupe(evidence)


def dedupe(values: list[str]) -> tuple[str, ...]:
    """Preserve order while dropping blank and duplicate refs."""
    seen: list[str] = []
    for value in values:
        item = text(value)
        if item and item not in seen:
            seen.append(item)
    return tuple(seen)


def _evidence_ref(source: PlanIntentSource) -> str:
    if ":" in source.ref:
        return source.ref
    return f"{source.kind}:{source.ref}"


__all__ = ["anchor_refs", "dedupe", "work_evidence_refs"]
