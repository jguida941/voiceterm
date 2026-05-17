"""Tests for `/develop` packet-pressure read models."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dev.scripts.devctl.runtime.development_packet_pressure import (
    packet_pressure_report,
)
from dev.scripts.devctl.runtime.master_plan_contract import PlanRow
from dev.scripts.devctl.runtime.plan_intent_ingestion import (
    terminal_packet_receipt_by_packet,
)


def test_below_budget_communication_continues_current_work() -> None:
    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [_packet("rev_pkt_1", kind="system_notice")]},
        rows=(),
        actor="codex",
    )

    assert pressure["live_total"] == 1
    assert pressure["actionable_total"] == 0
    assert pressure["pressure_state"] == "below_budget"
    assert classifications[0]["classification"] == "communication-only"
    assert decision["decision"] == "continue_current_work"


def test_workflow_receipts_are_lifecycle_only_even_with_plan_words() -> None:
    packet = _packet("rev_pkt_receipt", kind="task_produced")
    packet["summary"] = "Fix produced for MP-377"
    packet["body"] = "The task produced reviewable evidence for a plan fix."

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(),
        actor="codex",
    )

    assert pressure["durable_owner_gap_total"] == 0
    assert classifications[0]["classification"] == "lifecycle-only"
    assert classifications[0]["action_required"] is False
    assert decision["decision"] == "continue_current_work"
    assert packet_ingest_decisions[0]["decision"] == "ack"


def test_soft_budget_pivots_to_packet_review() -> None:
    packets = [_packet(f"rev_pkt_{index}") for index in range(12)]

    pressure, _classifications, decision, _packet_ingest_decisions = packet_pressure_report(
        {"packets": packets},
        rows=(),
        actor="codex",
    )

    assert pressure["live_total"] == 12
    assert pressure["pressure_state"] == "soft_attention_budget_crossed"
    assert decision["decision"] == "continue_to_packet_review"
    assert "review-channel --action show" in decision["next_command"]


def test_hard_budget_fails_closed() -> None:
    packets = [_packet(f"rev_pkt_{index}") for index in range(15)]

    pressure, _classifications, decision, _packet_ingest_decisions = packet_pressure_report(
        {"packets": packets},
        rows=(),
        actor="claude",
    )

    assert pressure["live_total"] == 15
    assert pressure["pressure_state"] == "hard_attention_budget_crossed"
    assert decision["decision"] == "fail_closed"
    assert decision["fail_closed"] is True


def test_durable_intent_requests_ingestion_receipt_without_ttl_pressure() -> None:
    packet = _packet(
        "rev_pkt_20",
        kind="plan_patch_review",
        target_kind="plan",
        target_ref="plan:MP-377",
        expires_at_utc=_stamp(minutes=5),
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(),
        actor="codex",
    )

    assert pressure["near_ttl_total"] == 0
    assert pressure["durable_owner_gap_total"] == 1
    assert classifications[0]["classification"] == "durable plan"
    assert classifications[0]["action_required"] is True
    assert decision["decision"] == "ingest_durable_intent"
    assert "develop ingest-intent --packet-id rev_pkt_20" in decision["next_command"]
    assert packet_ingest_decisions[0]["decision"] == "ingest"
    assert (
        "develop ingest-intent --packet-id rev_pkt_20"
        in packet_ingest_decisions[0]["next_command"]
    )


def test_clock_elapsed_communication_continues_current_work() -> None:
    packet = _packet("rev_pkt_30", expires_at_utc=_stamp(minutes=-5))

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(),
        actor="codex",
    )

    assert pressure["expired_unresolved_total"] == 0
    assert classifications[0]["classification"] == "communication-only"
    assert decision["decision"] == "continue_current_work"
    assert packet_ingest_decisions[0]["decision"] == "ack"


def test_archived_expired_packets_do_not_drive_packet_pressure() -> None:
    packet = _packet(
        "rev_pkt_archived",
        status="expired",
        lifecycle_current_state="archived",
        expires_at_utc=_stamp(minutes=-5),
        disposition={"sink": "archived"},
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(),
        actor="codex",
    )

    assert pressure["live_total"] == 0
    assert pressure["actionable_total"] == 0
    assert pressure["expired_unresolved_total"] == 0
    assert classifications == []
    assert decision["decision"] == "continue_current_work"


def test_durable_archived_pending_packets_do_not_drive_packet_pressure() -> None:
    packet = _packet(
        "rev_pkt_durable_archive",
        lifecycle_current_state="archived",
        expires_at_utc=_stamp(minutes=-5),
        disposition={
            "sink": "archived",
            "archive_classification": "expired_after_durable_binding",
            "resolution_anchor": "archive_classification:expired_after_durable_binding",
        },
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(),
        actor="codex",
    )

    assert pressure["live_total"] == 0
    assert pressure["actionable_total"] == 0
    assert pressure["expired_unresolved_total"] == 0
    assert classifications == []
    assert decision["decision"] == "continue_current_work"


def test_duplicate_and_obsolete_packets_are_terminal_classifications() -> None:
    packets = [
        _packet(
            "rev_pkt_40",
            expires_at_utc=_stamp(minutes=-5),
            disposition={"classification": "duplicate"},
        ),
        _packet(
            "rev_pkt_41",
            expires_at_utc=_stamp(minutes=-5),
            disposition={"classification": "obsolete"},
        ),
    ]

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": packets},
        rows=(),
        actor="codex",
    )

    assert pressure["durable_owner_gap_total"] == 0
    assert [item["classification"] for item in classifications] == [
        "duplicate",
        "obsolete",
    ]
    assert all(item["action_required"] is False for item in classifications)
    assert decision["decision"] == "continue_current_work"


def test_existing_plan_row_owner_removes_durable_owner_gap() -> None:
    packet = _packet(
        "rev_pkt_50",
        kind="plan_patch_review",
        target_kind="plan",
        target_ref="plan:MP-377",
        expires_at_utc=_stamp(minutes=5),
    )
    row = PlanRow(
        row_id="MP377-P0-T22AN-X",
        title="Packet-aware develop closure",
        status="in_progress",
        sdlc_stage="impl",
        sourced_from_packets=("rev_pkt_50",),
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(row,),
        actor="codex",
    )

    assert pressure["durable_owner_gap_total"] == 0
    assert classifications[0]["durable_owner"] == "MP377-P0-T22AN-X"
    assert classifications[0]["action_required"] is False
    assert decision["decision"] == "continue_current_work"


def test_existing_anchor_owner_removes_packet_from_next_pressure() -> None:
    packet = _packet(
        "rev_pkt_51",
        kind="plan_patch_review",
        target_kind="plan",
        target_ref="plan:MP-377",
        expires_at_utc=_stamp(minutes=5),
    )
    row = PlanRow(
        row_id="MP377-P0-T22AN-X",
        title="Packet-aware develop closure",
        status="in_progress",
        sdlc_stage="impl",
        anchor_refs=("packet:rev_pkt_51",),
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(row,),
        actor="codex",
    )

    assert pressure["actionable_total"] == 0
    assert classifications[0]["durable_owner"] == "MP377-P0-T22AN-X"
    assert classifications[0]["action_required"] is False
    assert decision["decision"] == "continue_current_work"


def test_durable_owned_findings_do_not_trip_attention_budget() -> None:
    packets = [
        _packet(f"rev_pkt_{index}", kind="finding")
        for index in range(20)
    ]
    row = PlanRow(
        row_id="MP377-P0-T22AN-X",
        title="Packet-aware develop closure",
        status="in_progress",
        sdlc_stage="impl",
        sourced_from_packets=tuple(
            f"rev_pkt_{index}" for index in range(20)
        ),
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": packets},
        rows=(row,),
        actor="codex",
    )

    assert pressure["live_total"] == 0
    assert pressure["pressure_state"] == "below_budget"
    assert pressure["durable_owner_gap_total"] == 0
    assert all(item["durable_owner"] == row.row_id for item in classifications)
    assert decision["decision"] == "continue_current_work"


def test_expired_archived_packet_with_plan_owner_is_provenance_not_pressure() -> None:
    packet = _packet(
        "rev_pkt_3111",
        kind="action_request",
        status="expired",
        lifecycle_current_state="archived",
        expires_at_utc=_stamp(minutes=-5),
        disposition={
            "sink": "archived",
            "archive_classification": "clock_expired_without_disposition",
            "resolution_anchor": "archive_classification:clock_expired_without_disposition",
        },
    )
    row = PlanRow(
        row_id="MP377-P0-EXC-S1",
        title="Governed exception receipt contracts",
        status="in_progress",
        sdlc_stage="impl",
        anchor_refs=("packet:rev_pkt_3111",),
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(row,),
        actor="codex",
    )

    assert pressure["expired_unresolved_total"] == 0
    assert classifications[0]["durable_owner"] == "MP377-P0-EXC-S1"
    assert classifications[0]["action_required"] is False
    assert decision["decision"] == "continue_current_work"


def test_terminal_archived_action_request_is_provenance_not_attention() -> None:
    packet = _packet(
        "rev_pkt_action_archived",
        kind="action_request",
        status="expired",
        lifecycle_current_state="archived",
        expires_at_utc=_stamp(minutes=-5),
        disposition={
            "sink": "archived",
            "archive_classification": "dismissed_with_actor",
        },
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(),
        actor="codex",
    )

    assert pressure["expired_unresolved_total"] == 0
    assert classifications == []
    assert decision["decision"] == "continue_current_work"


def test_clock_expired_without_disposition_still_requires_intake_without_owner() -> None:
    packet = _packet(
        "rev_pkt_unowned_clock_expired",
        kind="action_request",
        status="expired",
        lifecycle_current_state="archived",
        expires_at_utc=_stamp(minutes=-5),
        disposition={
            "sink": "archived",
            "archive_classification": "clock_expired_without_disposition",
            "resolution_anchor": "archive_classification:clock_expired_without_disposition",
        },
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(),
        actor="codex",
    )

    assert pressure["expired_unresolved_total"] == 1
    assert classifications[0]["terminal_receipt"] == ""
    assert decision["decision"] == "continue_to_packet_review"


def test_plan_ingestion_terminal_receipt_removes_expired_packet_pressure() -> None:
    packet = _packet(
        "rev_pkt_3121",
        kind="action_request",
        status="expired",
        lifecycle_current_state="archived",
        expires_at_utc=_stamp(minutes=-5),
        disposition={
            "sink": "archived",
            "archive_classification": "clock_expired_without_disposition",
            "resolution_anchor": "archive_classification:clock_expired_without_disposition",
        },
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(),
        actor="codex",
        terminal_receipt_by_packet={"rev_pkt_3121": "obsolete"},
    )

    assert pressure["expired_unresolved_total"] == 0
    assert classifications[0]["classification"] == "obsolete"
    assert classifications[0]["terminal_receipt"] == "obsolete"
    assert classifications[0]["action_required"] is False
    assert decision["decision"] == "continue_current_work"


def test_class_owner_removes_clock_expired_packet_pressure() -> None:
    packet = _packet(
        "rev_pkt_3130",
        kind="action_request",
        status="expired",
        lifecycle_current_state="archived",
        expires_at_utc=_stamp(minutes=-5),
        disposition={
            "sink": "archived",
            "archive_classification": "clock_expired_without_disposition",
            "resolution_anchor": "archive_classification:clock_expired_without_disposition",
        },
    )
    row = PlanRow(
        row_id="MP377-P0-PACKET-INTAKE-SCHEDULER-S1",
        title="Make packet intake resolve before next-action selection",
        status="in_progress",
        sdlc_stage="impl",
        target_ref="plan:MP377-GUARDIR-PACKET-DURABLE-INGESTION",
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(row,),
        actor="codex",
    )

    assert pressure["expired_unresolved_total"] == 0
    assert pressure["durable_owner_gap_total"] == 0
    assert classifications[0]["durable_owner"] == row.row_id
    assert classifications[0]["action_required"] is False
    assert decision["decision"] == "continue_current_work"


def test_plan_ingestion_receipt_index_uses_source_packet_terminal_status() -> None:
    terminal = terminal_packet_receipt_by_packet(
        (
            {
                "source_ref": "packet:rev_pkt_3121",
                "status": "obsolete",
                "target_kind": "terminal_receipt",
                "terminal_status": "obsolete",
            },
            {
                "packet_id": "rev_pkt_3155",
                "status": "accepted",
                "target_kind": "plan_row",
            },
        )
    )

    assert terminal == {"rev_pkt_3121": "obsolete"}


def test_pending_action_request_pivots_even_with_durable_owner() -> None:
    packet = _packet(
        "rev_pkt_60",
        kind="action_request",
        target_kind="plan",
        target_ref="plan:MP-377",
    )
    row = PlanRow(
        row_id="PKT-BIND-REV-PKT-60",
        title="Packet action request",
        status="queued",
        sdlc_stage="impl",
        sourced_from_packets=("rev_pkt_60",),
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(row,),
        actor="claude",
    )

    assert pressure["pressure_state"] == "below_budget"
    assert classifications[0]["durable_owner"] == "PKT-BIND-REV-PKT-60"
    assert decision["decision"] == "continue_to_packet_review"
    assert decision["reason_code"] == "pending_packet_requires_review"
    assert "review-channel --action show" in decision["next_command"]


def test_expired_action_request_with_class_owner_is_not_live_review_pressure() -> None:
    packet = _packet(
        "rev_pkt_3138",
        kind="action_request",
        status="expired",
        lifecycle_current_state="archived",
        expires_at_utc=_stamp(minutes=-5),
        disposition={
            "sink": "archived",
            "archive_classification": "clock_expired_without_disposition",
            "resolution_anchor": "archive_classification:clock_expired_without_disposition",
        },
    )
    row = PlanRow(
        row_id="MP377-P0-PACKET-INTAKE-SCHEDULER-S1",
        title="Make packet intake resolve before next-action selection",
        status="in_progress",
        sdlc_stage="impl",
        target_ref="plan:MP377-GUARDIR-PACKET-DURABLE-INGESTION",
    )

    pressure, classifications, decision, packet_ingest_decisions = packet_pressure_report(
        {"packets": [packet]},
        rows=(row,),
        actor="codex",
    )

    assert pressure["pressure_state"] == "below_budget"
    assert classifications[0]["durable_owner"] == row.row_id
    assert decision["decision"] == "continue_current_work"


def _packet(
    packet_id: str,
    *,
    kind: str = "system_notice",
    status: str = "pending",
    lifecycle_current_state: str = "",
    target_kind: str = "",
    target_ref: str = "",
    expires_at_utc: str | None = None,
    disposition: dict[str, object] | None = None,
) -> dict[str, object]:
    packet = {
        "packet_id": packet_id,
        "kind": kind,
        "status": status,
        "to_agent": "codex",
        "summary": "packet pressure test",
        "requested_action": "review_only",
        "policy_hint": "review_only",
        "plan_id": "MP-377",
        "anchor_refs": ["section:MP-377"],
        "target_kind": target_kind,
        "target_ref": target_ref,
        "expires_at_utc": expires_at_utc or "2999-01-01T00:00:00Z",
    }
    if lifecycle_current_state:
        packet["lifecycle_current_state"] = lifecycle_current_state
    if disposition is not None:
        packet["disposition"] = disposition
    return packet


def _stamp(*, minutes: int) -> str:
    return (
        datetime.now(timezone.utc) + timedelta(minutes=minutes)
    ).isoformat().replace("+00:00", "Z")
