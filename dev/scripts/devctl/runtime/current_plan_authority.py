"""Typed `CurrentPlanAuthority` resolver — one authority for next-slice selection.

v4.55 continuation (rev_pkt_4789): `develop next`, startup, and the
final-response gate must resolve ONE typed authority that names the
current executable PlanRow. Pending packets become *evidence* or
*communication*, not selectors. Stale or unbound packets MUST NOT
become continuation_goal or next_slice ahead of the current PlanRow.

This resolver composes:

* `dev/state/plan_index.jsonl` — typed PlanRow store (passed in by
  caller as `plan_rows`)
* Packet bindings — `packet_carry_forward_sources.packet_ids_from_plan_row`
  decides which pending packets are durably bound to a given PlanRow

The resolver returns `CurrentPlanAuthority`, a typed dataclass naming
the executable PlanRow plus the bound/unbound packet partition.
Consumers (e.g. `commands/development/next_slice.select_next_slice`)
rank the PlanRow above unbound packets, and may surface bound packets
as evidence for the same PlanRow.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Protocol

from .packet_carry_forward_sources import packet_ids_from_plan_row

CURRENT_PLAN_AUTHORITY_CONTRACT_ID = "CurrentPlanAuthority"
CURRENT_PLAN_AUTHORITY_SCHEMA_VERSION = 1


class _RowWithProvenance(Protocol):
    provenance: object


class _ProvenanceWithObservedAt(Protocol):
    observed_at_utc: object


@dataclass(frozen=True, slots=True)
class CurrentPlanAuthority:
    """One typed authority over next-work selection.

    ``plan_row_id`` is the current executable PlanRow's id (empty
    string when no executable row exists). ``plan_bound_packet_ids``
    are pending packet ids whose target binds to this row via the
    PlanRow's ``sourced_from_packets`` / ``anchor_refs`` /
    ``target_ref`` fields. ``unbound_packet_ids`` are the remaining
    pending packets — they are communication/evidence only and MUST
    NOT outrank ``plan_row_id`` in selector decisions.

    ``resolution_evidence`` is an audit trace describing how the
    resolver picked the row, for ``ValidationReceipt``-style
    inspection.
    """

    plan_row_id: str = ""
    plan_row_source_path: str = ""
    plan_row_status: str = ""
    plan_row_target_ref: str = ""
    plan_bound_packet_ids: tuple[str, ...] = ()
    unbound_packet_ids: tuple[str, ...] = ()
    resolution_evidence: tuple[str, ...] = ()
    contract_id: str = CURRENT_PLAN_AUTHORITY_CONTRACT_ID
    schema_version: int = CURRENT_PLAN_AUTHORITY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["plan_bound_packet_ids"] = list(self.plan_bound_packet_ids)
        payload["unbound_packet_ids"] = list(self.unbound_packet_ids)
        payload["resolution_evidence"] = list(self.resolution_evidence)
        return payload

    @property
    def has_executable_plan_row(self) -> bool:
        return bool(self.plan_row_id)


def resolve_current_plan_authority(
    plan_rows: tuple[object, ...] | Iterable[object],
    *,
    pending_packets: Iterable[Mapping[str, object]] | None = None,
) -> CurrentPlanAuthority:
    """Resolve the current executable PlanRow + packet binding partition.

    Selection rule (in priority order):
      1. First ``in_progress`` leaf row — work already started.
      2. First ``queued`` leaf row — work scheduled next.
      3. Empty authority — no executable row exists.

    A row counts as a "leaf" when no other row in ``plan_rows`` lists
    it as a parent (matches the existing
    ``next_slice._active_leaf_row`` semantics so the resolver and the
    selector agree on which row is "current").

    ``pending_packets`` is an iterable of pending packet payloads
    (mappings with at least a ``packet_id`` field). Packets whose ids
    appear in the executable row's ``packet_ids_from_plan_row`` set are
    classified ``plan_bound_packet_ids``; the rest are
    ``unbound_packet_ids`` (communication/evidence only).
    """
    rows_tuple = tuple(plan_rows)
    packet_tuple = tuple(pending_packets or ())
    pending_ids = tuple(
        _packet_id(packet)
        for packet in packet_tuple
        if isinstance(packet, Mapping) and _packet_id(packet)
    )

    executable = _select_executable_row(rows_tuple)
    if executable is None:
        evidence = (
            f"no_executable_plan_row plan_row_count={len(rows_tuple)} "
            f"pending_packet_count={len(pending_ids)}",
        )
        return CurrentPlanAuthority(
            unbound_packet_ids=pending_ids,
            resolution_evidence=evidence,
        )

    # v4.55 rev_pkt_4790: bound packets come from the executable row
    # itself PLUS any PKT-BIND row whose `target_ref` points at the
    # executable row. PKT-BIND rows are evidence carriers — they
    # bind packets to their owning row without becoming selectable
    # work themselves.
    executable_row_id = _row_attr(executable, "row_id")
    executable_refs = {executable_row_id, f"plan:{executable_row_id}"}
    bound_ids_set: set[str] = set(packet_ids_from_plan_row(executable))
    for row in rows_tuple:
        if not _is_packet_binding_row(row):
            continue
        if _row_attr(row, "target_ref") in executable_refs:
            bound_ids_set.update(packet_ids_from_plan_row(row))
    bound_ids_set = {pid for pid in bound_ids_set if pid}

    bound_pending = tuple(pid for pid in pending_ids if pid in bound_ids_set)
    unbound_pending = tuple(pid for pid in pending_ids if pid not in bound_ids_set)

    evidence = (
        f"executable_plan_row_id={executable_row_id}",
        f"plan_row_status={_row_attr(executable, 'status')}",
        f"plan_bound_packet_count={len(bound_pending)}",
        f"unbound_packet_count={len(unbound_pending)}",
    )
    return CurrentPlanAuthority(
        plan_row_id=executable_row_id,
        plan_row_source_path=_row_attr(executable, "source_doc_path"),
        plan_row_status=_row_attr(executable, "status"),
        plan_row_target_ref=_row_attr(executable, "target_ref"),
        plan_bound_packet_ids=bound_pending,
        unbound_packet_ids=unbound_pending,
        resolution_evidence=evidence,
    )


def _select_executable_row(rows: tuple[object, ...]) -> object | None:
    """Mirror `next_slice._active_leaf_row` semantics exactly so resolver +
    selector agree on the current row.

    Canonical semantic (per rev_pkt_4790): leaf = not named by any OTHER
    active non-PKT-BIND row's ``anchor_refs`` or ``target_ref`` as a
    parent (via ``row_id`` or ``plan:row_id``). PKT-BIND rows are
    skipped from "is a parent" detection because they're packet
    bindings, not workflow children. Selection priority among leaves:
    in_progress > queued; fallback to any in_progress, then any queued.
    """
    active = tuple(
        row
        for row in rows
        if _row_attr(row, "status") in {"in_progress", "queued"}
    )
    if not active:
        return None
    non_pkt_bind_active = tuple(
        row for row in active if not _is_packet_binding_row(row)
    )
    leaves = tuple(
        row
        for row in non_pkt_bind_active
        if not _has_active_child(row, non_pkt_bind_active)
    )
    selected = _latest_row_with_status(leaves, "in_progress")
    if selected is not None:
        return selected
    selected = _latest_row_with_status(leaves, "queued")
    if selected is not None:
        return selected
    # Fallback to any active row (non-PKT-BIND first; matches
    # next_slice fallback ordering at lines 99-102).
    selected = _latest_row_with_status(non_pkt_bind_active, "in_progress")
    if selected is not None:
        return selected
    return _latest_row_with_status(non_pkt_bind_active, "queued")


def _latest_row_with_status(rows: tuple[object, ...], status: str) -> object | None:
    """Return the newest typed row with ``status`` while preserving old tie order.

    Live plan_index state contains multiple stale ``in_progress`` leaves. JSONL
    order is not authority; the latest typed plan-ingest provenance is the
    durable freshness signal until the dependency graph gets richer sequencing.
    """
    selected: object | None = None
    selected_observed_at = ""
    for row in rows:
        if _row_attr(row, "status") != status:
            continue
        observed_at = _row_observed_at_utc(row)
        if selected is None or observed_at > selected_observed_at:
            selected = row
            selected_observed_at = observed_at
    return selected


def _has_active_child(row: object, rows: tuple[object, ...]) -> bool:
    """True when another active non-PKT-BIND row references ``row`` via
    its ``anchor_refs`` or ``target_ref`` (matching ``row_id`` or
    ``plan:row_id``). Direct port of `next_slice._has_active_child` so
    the resolver and the selector use one canonical rule.
    """
    row_id = _row_attr(row, "row_id")
    if not row_id:
        return False
    row_refs = {row_id, f"plan:{row_id}"}
    for candidate in rows:
        if _row_attr(candidate, "row_id") == row_id:
            continue
        if _is_packet_binding_row(candidate):
            continue
        anchor_refs = _row_seq(candidate, "anchor_refs")
        if row_refs.intersection(anchor_refs):
            return True
        target_ref = _row_attr(candidate, "target_ref")
        if target_ref and target_ref in row_refs:
            return True
    return False


def _is_packet_binding_row(row: object) -> bool:
    """PKT-BIND rows are typed packet bindings, not executable work.
    They surface bound packets as evidence for their owning row but
    are never selected as next_slice themselves.
    """
    return _row_attr(row, "row_id").startswith("PKT-BIND-")


def _row_attr(row: object, attr: str) -> str:
    if isinstance(row, Mapping):
        value = row.get(attr, "")
    else:
        value = getattr(row, attr, "")
    return str(value or "").strip()


def _row_seq(row: object, attr: str) -> set[str]:
    if isinstance(row, Mapping):
        value = row.get(attr, ())
    else:
        value = getattr(row, attr, ())
    if not isinstance(value, (list, tuple, set, frozenset)):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def _row_observed_at_utc(row: Mapping[str, object] | _RowWithProvenance) -> str:
    if isinstance(row, Mapping):
        provenance = row.get("provenance", {})
    else:
        try:
            provenance = row.provenance
        except AttributeError:
            provenance = {}
    if isinstance(provenance, Mapping):
        value = provenance.get("observed_at_utc", "")
    else:
        try:
            value = provenance.observed_at_utc
        except AttributeError:
            value = ""
    return str(value or "").strip()


def _packet_id(packet: Mapping[str, object]) -> str:
    value = packet.get("packet_id", "")
    return str(value or "").strip()


__all__ = [
    "CURRENT_PLAN_AUTHORITY_CONTRACT_ID",
    "CURRENT_PLAN_AUTHORITY_SCHEMA_VERSION",
    "CurrentPlanAuthority",
    "resolve_current_plan_authority",
]
