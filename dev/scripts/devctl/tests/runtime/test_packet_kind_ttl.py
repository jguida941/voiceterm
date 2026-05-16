from __future__ import annotations

from dev.scripts.devctl.runtime.packet_kind_ttl import (
    DECISION_TTL_EVIDENCE_CONTRACT_ID,
    FINDING_TTL_EVIDENCE_CONTRACT_ID,
    QUESTION_TTL_EVIDENCE_CONTRACT_ID,
    TASK_PRODUCED_TTL_EVIDENCE_CONTRACT_ID,
    resolve_decision_ttl,
    resolve_finding_ttl,
    resolve_question_ttl,
    resolve_task_produced_ttl,
)


def test_task_produced_ttl_evidence_expires_after_thirty_days() -> None:
    evidence = resolve_task_produced_ttl(
        {
            "packets": [
                _packet(
                    packet_id="rev_pkt_task",
                    kind="task_produced",
                    posted_at="2026-05-01T00:00:00Z",
                )
            ]
        },
        now_utc="2026-05-31T00:00:01Z",
    )

    assert evidence.contract_id == TASK_PRODUCED_TTL_EVIDENCE_CONTRACT_ID
    assert evidence.status == "expired"
    assert evidence.expired is True
    assert evidence.ttl_seconds == 30 * 24 * 60 * 60
    assert evidence.expires_at_utc == "2026-05-31T00:00:00Z"


def test_question_ttl_evidence_uses_seven_day_window() -> None:
    evidence = resolve_question_ttl(
        {
            "packets": [
                _packet(
                    packet_id="rev_pkt_question",
                    kind="question",
                    posted_at="2026-05-01T00:00:00Z",
                )
            ]
        },
        now_utc="2026-05-07T23:59:59Z",
    )

    assert evidence.contract_id == QUESTION_TTL_EVIDENCE_CONTRACT_ID
    assert evidence.status == "alive"
    assert evidence.expired is False
    assert evidence.ttl_seconds == 7 * 24 * 60 * 60


def test_decision_ttl_evidence_ignores_resolved_packet() -> None:
    evidence = resolve_decision_ttl(
        {
            "packets": [
                _packet(
                    packet_id="rev_pkt_decision_old",
                    kind="decision",
                    posted_at="2026-05-01T00:00:00Z",
                    status="applied",
                    lifecycle_current_state="applied",
                    latest_event_id="rev_evt_5",
                ),
                _packet(
                    packet_id="rev_pkt_decision_new",
                    kind="decision",
                    posted_at="2026-05-10T00:00:00Z",
                    latest_event_id="rev_evt_6",
                ),
            ]
        },
        now_utc="2026-05-12T00:00:00Z",
    )

    assert evidence.contract_id == DECISION_TTL_EVIDENCE_CONTRACT_ID
    assert evidence.packet_id == "rev_pkt_decision_new"
    assert evidence.status == "alive"
    assert evidence.ttl_seconds == 14 * 24 * 60 * 60


def test_finding_ttl_evidence_reports_missing_when_no_unresolved_packet() -> None:
    evidence = resolve_finding_ttl(
        {"packets": []},
        now_utc="2026-05-12T00:00:00Z",
    )

    assert evidence.contract_id == FINDING_TTL_EVIDENCE_CONTRACT_ID
    assert evidence.status == "missing"
    assert evidence.packet_id == ""
    assert evidence.ttl_seconds == 7 * 24 * 60 * 60


def _packet(
    *,
    packet_id: str,
    kind: str,
    posted_at: str,
    status: str = "pending",
    lifecycle_current_state: str = "pending",
    latest_event_id: str = "rev_evt_1",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "kind": kind,
        "posted_at": posted_at,
        "status": status,
        "lifecycle_current_state": lifecycle_current_state,
        "latest_event_id": latest_event_id,
    }
