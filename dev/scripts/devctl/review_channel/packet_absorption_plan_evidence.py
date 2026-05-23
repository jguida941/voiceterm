"""Plan-evidence checks for packet absorption rows."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.value_coercion import coerce_string, coerce_string_items


def rows_have_required_plan_evidence(
    rows: tuple[Mapping[str, object], ...],
    *,
    packet: Mapping[str, object],
) -> bool:
    for row in rows:
        if not _row_is_plan_affecting(row):
            continue
        if not _row_has_plan_evidence(row, packet=packet):
            return False
    return True


def _row_is_plan_affecting(row: Mapping[str, object]) -> bool:
    kind = coerce_string(row.get("kind")).strip().lower()
    target_ref = coerce_string(row.get("target_ref")).strip().lower()
    slice_ref = coerce_string(row.get("slice_ref")).strip().lower()
    return (
        kind in {"plan_change", "plan_update", "plan_proposal", "plan_integration", "plan_row"}
        or target_ref.startswith(("plan:", "plan_row:"))
        or slice_ref.startswith(("plan:", "plan_row:"))
    )


def _row_has_plan_evidence(
    row: Mapping[str, object],
    *,
    packet: Mapping[str, object],
) -> bool:
    evidence_refs = coerce_string_items(row.get("evidence_refs"))
    if any(ref.startswith(_PLAN_EVIDENCE_PREFIXES) for ref in evidence_refs):
        return True
    return _packet_has_inserted_plan_binding_for_row(row=row, packet=packet)


def _packet_has_inserted_plan_binding_for_row(
    *,
    row: Mapping[str, object],
    packet: Mapping[str, object],
) -> bool:
    binding = packet.get("durable_binding") or packet.get("packet_creation_binding")
    if not isinstance(binding, Mapping):
        return False
    if coerce_string(binding.get("status")) != "inserted":
        return False
    binding_kind = coerce_string(binding.get("binding_target_kind"))
    if binding_kind not in {"plan_row", "plan_row_evidence"}:
        return False
    packet_ref = coerce_string(packet.get("target_ref"))
    row_refs = {
        _normal_plan_ref(row.get("target_ref")),
        _normal_plan_ref(row.get("slice_ref")),
    }
    return bool(packet_ref and _normal_plan_ref(packet_ref) in row_refs)


_PLAN_EVIDENCE_PREFIXES = (
    "plan:",
    "plan_row:",
    "plan_proposal:",
    "packet_plan_integration:",
    "receipt:plan",
    "receipt:PacketPlanIntegration",
)


def _normal_plan_ref(value: object) -> str:
    ref = coerce_string(value)
    if ref.startswith("plan://"):
        return f"plan:{ref.removeprefix('plan://')}"
    return ref
