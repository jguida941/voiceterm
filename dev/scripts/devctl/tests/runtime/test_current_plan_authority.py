"""Tests for the v4.55 `CurrentPlanAuthority` resolver per rev_pkt_4789."""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.runtime.current_plan_authority import (
    CURRENT_PLAN_AUTHORITY_CONTRACT_ID,
    CurrentPlanAuthority,
    resolve_current_plan_authority,
)


def _plan_row(
    row_id: str,
    *,
    status: str,
    sourced_from_packets: tuple[str, ...] = (),
    anchor_refs: tuple[str, ...] = (),
    target_ref: str = "",
    source_doc_path: str = "dev/active/MASTER_PLAN.md",
    observed_at_utc: str = "2026-05-20T00:00:00Z",
) -> SimpleNamespace:
    """Build a SimpleNamespace mirror of the runtime PlanRow shape used
    by `next_slice._has_active_child`. Tests assert on `anchor_refs` +
    `target_ref` parent linkage (the canonical semantic), not on a
    `parent_row_id` field which the real PlanRow does not have.
    """
    return SimpleNamespace(
        row_id=row_id,
        status=status,
        sourced_from_packets=sourced_from_packets,
        anchor_refs=anchor_refs,
        target_ref=target_ref,
        source_doc_path=source_doc_path,
        work_evidence_ids=(),
        title=row_id,
        provenance={"observed_at_utc": observed_at_utc},
    )


def test_no_executable_row_returns_empty_authority_with_unbound_packets() -> None:
    """No `in_progress` or `queued` row exists → empty authority. All
    pending packets are unbound (communication/evidence only) per
    rev_pkt_4789's "Packet backlog is communication/evidence only"
    rule.
    """
    rows = (_plan_row("ROW-DONE-1", status="completed"),)
    pending = (
        {"packet_id": "rev_pkt_4698"},
        {"packet_id": "rev_pkt_4788"},
    )
    authority = resolve_current_plan_authority(rows, pending_packets=pending)

    assert authority.plan_row_id == ""
    assert authority.has_executable_plan_row is False
    assert authority.plan_bound_packet_ids == ()
    assert authority.unbound_packet_ids == ("rev_pkt_4698", "rev_pkt_4788")
    assert authority.contract_id == CURRENT_PLAN_AUTHORITY_CONTRACT_ID


def test_in_progress_row_wins_over_queued_and_partitions_packets() -> None:
    """v4.55 invariant: when an `in_progress` leaf row exists, it is
    the executable PlanRow. Pending packets bound to that row via
    `sourced_from_packets` are classified plan_bound; the rest stay
    unbound and cannot outrank the row in selector decisions.
    """
    rows = (
        _plan_row("ROW-IN-PROGRESS", status="in_progress",
                  sourced_from_packets=("rev_pkt_4788",)),
        _plan_row("ROW-QUEUED-LATER", status="queued",
                  sourced_from_packets=("rev_pkt_4789",)),
    )
    pending = (
        {"packet_id": "rev_pkt_4788"},  # bound to ROW-IN-PROGRESS
        {"packet_id": "rev_pkt_4698"},  # unbound — old transport debt
        {"packet_id": "rev_pkt_4789"},  # bound to a different row (queued)
    )
    authority = resolve_current_plan_authority(rows, pending_packets=pending)

    assert authority.plan_row_id == "ROW-IN-PROGRESS"
    assert authority.plan_row_status == "in_progress"
    assert authority.plan_bound_packet_ids == ("rev_pkt_4788",)
    assert authority.unbound_packet_ids == ("rev_pkt_4698", "rev_pkt_4789")


def test_latest_typed_in_progress_row_wins_over_stale_in_progress_rows() -> None:
    """Multiple in-progress leaves are common in the live plan index.

    CurrentPlanAuthority must not select the first stale row in JSONL order.
    The active row is the latest typed in-progress row after plan-ingest
    provenance updates the durable PlanRow.
    """
    rows = (
        _plan_row(
            "GUARDIR-EXTRACTION-MASTER-PLAN-2026-05-18-S1",
            status="in_progress",
            observed_at_utc="2026-05-18T12:00:00Z",
        ),
        _plan_row(
            "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
            status="in_progress",
            observed_at_utc="2026-05-21T20:00:00Z",
        ),
    )

    authority = resolve_current_plan_authority(rows)

    assert (
        authority.plan_row_id
        == "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
    )


def test_queued_leaf_selected_when_no_in_progress_row_exists() -> None:
    """Selection priority: in_progress beats queued. With no
    in_progress row, the first queued leaf wins.

    Leaf semantic per `next_slice._has_active_child`: a row is "named
    as parent" when another active non-PKT-BIND row's `anchor_refs`
    or `target_ref` references it as `row_id` or `plan:row_id`.
    """
    rows = (
        _plan_row("ROW-PARENT", status="queued"),
        _plan_row("ROW-LEAF-1", status="queued",
                  anchor_refs=("plan:ROW-PARENT",),
                  sourced_from_packets=("rev_pkt_4788",)),
        _plan_row("ROW-LEAF-2", status="queued",
                  target_ref="plan:ROW-PARENT"),
    )
    pending = ({"packet_id": "rev_pkt_4788"},)
    authority = resolve_current_plan_authority(rows, pending_packets=pending)

    # The selector picks a leaf row (not the parent, which is named
    # by ROW-LEAF-1's anchor_refs and ROW-LEAF-2's target_ref).
    assert authority.plan_row_id in {"ROW-LEAF-1", "ROW-LEAF-2"}
    assert authority.plan_row_status == "queued"


def test_v4790_pkt_bind_row_target_ref_resolves_to_owning_active_row() -> None:
    """v4.55 (rev_pkt_4790): PKT-BIND rows are evidence carriers, not
    selectable work. A pending packet bound through a PKT-BIND row's
    `target_ref` to the active executable row surfaces as evidence
    for THAT row, not as a competing selector. The PKT-BIND row
    itself is skipped from leaf detection.
    """
    rows = (
        _plan_row("MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
                  status="in_progress",
                  sourced_from_packets=("rev_pkt_4789",)),
        _plan_row("PKT-BIND-MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
                  status="queued",
                  target_ref="plan:MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
                  sourced_from_packets=("rev_pkt_4788",)),
    )
    pending = (
        {"packet_id": "rev_pkt_4788"},  # bound through PKT-BIND
        {"packet_id": "rev_pkt_4789"},  # bound directly to executable row
        {"packet_id": "rev_pkt_4698"},  # unbound (old transport debt)
    )
    authority = resolve_current_plan_authority(rows, pending_packets=pending)

    # PKT-BIND row is NOT selected as the executable row.
    assert authority.plan_row_id == "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
    # Both packets bound through PKT-BIND and direct binding surface
    # as plan_bound for the executable row.
    assert set(authority.plan_bound_packet_ids) == {"rev_pkt_4788", "rev_pkt_4789"}
    # Old transport debt stays unbound.
    assert authority.unbound_packet_ids == ("rev_pkt_4698",)


def test_resolver_handles_dict_shaped_plan_rows() -> None:
    """Plan rows may be loaded as dicts from `plan_index.jsonl`, not
    dataclass instances. The resolver must handle both shapes (dict
    `.get` and attribute access).
    """
    rows = (
        {
            "row_id": "ROW-DICT-IN-PROGRESS",
            "status": "in_progress",
            "sourced_from_packets": ["rev_pkt_4788"],
            "target_ref": "runtime://test",
            "source_doc_path": "dev/active/MASTER_PLAN.md",
            "anchor_refs": [],
            "work_evidence_ids": [],
            "parent_row_id": "",
        },
    )
    pending = ({"packet_id": "rev_pkt_4788"},)
    authority = resolve_current_plan_authority(rows, pending_packets=pending)

    assert authority.plan_row_id == "ROW-DICT-IN-PROGRESS"
    assert authority.plan_bound_packet_ids == ("rev_pkt_4788",)
    assert authority.plan_row_target_ref == "runtime://test"


def test_to_dict_serializes_with_list_collections_for_json() -> None:
    """`to_dict` must coerce the tuple fields into lists so the typed
    authority can be JSON-encoded into a startup-context payload.
    """
    authority = CurrentPlanAuthority(
        plan_row_id="ROW-EXAMPLE",
        plan_bound_packet_ids=("rev_pkt_a", "rev_pkt_b"),
        unbound_packet_ids=("rev_pkt_c",),
        resolution_evidence=("executable_plan_row_id=ROW-EXAMPLE",),
    )
    payload = authority.to_dict()

    assert payload["plan_row_id"] == "ROW-EXAMPLE"
    assert payload["plan_bound_packet_ids"] == ["rev_pkt_a", "rev_pkt_b"]
    assert payload["unbound_packet_ids"] == ["rev_pkt_c"]
    assert payload["resolution_evidence"] == ["executable_plan_row_id=ROW-EXAMPLE"]
    assert payload["contract_id"] == CURRENT_PLAN_AUTHORITY_CONTRACT_ID
    assert payload["schema_version"] == 1
