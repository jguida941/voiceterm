"""Tests for `/develop` packet-pressure read models."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dev.scripts.devctl.runtime.development_packet_pressure import (
    packet_pressure_report,
)
from dev.scripts.devctl.runtime.master_plan_contract import PlanRow


def test_below_budget_communication_continues_current_work() -> None:
    pressure, classifications, decision = packet_pressure_report(
        {"packets": [_packet("rev_pkt_1", kind="system_notice")]},
        rows=(),
        actor="codex",
    )

    assert pressure["live_total"] == 1
    assert pressure["actionable_total"] == 0
    assert pressure["pressure_state"] == "below_budget"
    assert classifications[0]["classification"] == "communication-only"
    assert decision["decision"] == "continue_current_work"


def test_soft_budget_pivots_to_packet_review() -> None:
    packets = [_packet(f"rev_pkt_{index}") for index in range(12)]

    pressure, _classifications, decision = packet_pressure_report(
        {"packets": packets},
        rows=(),
        actor="codex",
    )

    assert pressure["live_total"] == 12
    assert pressure["pressure_state"] == "soft_attention_budget_crossed"
    assert decision["decision"] == "pivot_to_packet_review"
    assert "review-channel --action show" in decision["next_command"]


def test_hard_budget_fails_closed() -> None:
    packets = [_packet(f"rev_pkt_{index}") for index in range(15)]

    pressure, _classifications, decision = packet_pressure_report(
        {"packets": packets},
        rows=(),
        actor="claude",
    )

    assert pressure["live_total"] == 15
    assert pressure["pressure_state"] == "hard_attention_budget_crossed"
    assert decision["decision"] == "fail_closed"
    assert decision["fail_closed"] is True


def test_near_ttl_durable_intent_requests_ingestion_receipt() -> None:
    packet = _packet(
        "rev_pkt_20",
        kind="plan_patch_review",
        target_kind="plan",
        target_ref="plan:MP-377",
        expires_at_utc=_stamp(minutes=5),
    )

    pressure, classifications, decision = packet_pressure_report(
        {"packets": [packet]},
        rows=(),
        actor="codex",
    )

    assert pressure["near_ttl_total"] == 1
    assert pressure["durable_owner_gap_total"] == 1
    assert classifications[0]["classification"] == "durable plan"
    assert classifications[0]["action_required"] is True
    assert decision["decision"] == "ingest_durable_intent"
    assert "develop ingest-intent --packet-id rev_pkt_20" in decision["next_command"]


def test_expired_unresolved_communication_pivots_without_autodrain() -> None:
    packet = _packet("rev_pkt_30", expires_at_utc=_stamp(minutes=-5))

    pressure, classifications, decision = packet_pressure_report(
        {"packets": [packet]},
        rows=(),
        actor="codex",
    )

    assert pressure["expired_unresolved_total"] == 1
    assert classifications[0]["classification"] == "communication-only"
    assert decision["decision"] == "pivot_to_packet_review"


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

    pressure, classifications, decision = packet_pressure_report(
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
    assert decision["decision"] == "pivot_to_packet_review"


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

    pressure, classifications, decision = packet_pressure_report(
        {"packets": [packet]},
        rows=(row,),
        actor="codex",
    )

    assert pressure["durable_owner_gap_total"] == 0
    assert classifications[0]["durable_owner"] == "MP377-P0-T22AN-X"
    assert classifications[0]["action_required"] is False
    assert decision["decision"] == "pivot_to_packet_review"


def _packet(
    packet_id: str,
    *,
    kind: str = "system_notice",
    target_kind: str = "",
    target_ref: str = "",
    expires_at_utc: str | None = None,
    disposition: dict[str, object] | None = None,
) -> dict[str, object]:
    packet = {
        "packet_id": packet_id,
        "kind": kind,
        "status": "pending",
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
    if disposition is not None:
        packet["disposition"] = disposition
    return packet


def _stamp(*, minutes: int) -> str:
    return (
        datetime.now(timezone.utc) + timedelta(minutes=minutes)
    ).isoformat().replace("+00:00", "Z")
