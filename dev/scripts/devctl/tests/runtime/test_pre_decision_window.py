from __future__ import annotations

from dev.scripts.devctl.runtime.collaboration_packet_kinds import (
    REVIEW_ACCEPTED_PACKET_KIND,
    TASK_STARTED_PACKET_KIND,
)
from dev.scripts.devctl.runtime.pre_decision_window import (
    PRE_DECISION_OBJECTION_TOKEN,
    resolve_pre_decision_window,
)


def test_pre_decision_window_blocks_while_open_waiting_for_reviewer() -> None:
    evidence = resolve_pre_decision_window(
        {"packets": [_task_started()]},
        actor="codex",
        reviewer="claude",
        plan_row_id="MP377-PRE-DECISION-COMPOSABILITY-WINDOW-S1",
        now_utc="2026-05-11T22:35:00Z",
        window_seconds=900,
    )

    assert evidence.status == "open_waiting_for_reviewer"
    assert evidence.commit_blocked is True
    assert evidence.task_started_packet_id == "rev_pkt_task"
    assert evidence.duplicate_hunt_ref == "duplicate_hunt:section-11-no-overlap"


def test_pre_decision_window_ack_allows_commit() -> None:
    evidence = resolve_pre_decision_window(
        {
            "packets": [
                _task_started(),
                _response(
                    packet_id="rev_pkt_ack",
                    kind=REVIEW_ACCEPTED_PACKET_KIND,
                    summary="pre_decision_ack accepted",
                ),
            ]
        },
        actor="codex",
        reviewer="claude",
        plan_row_id="MP377-PRE-DECISION-COMPOSABILITY-WINDOW-S1",
        now_utc="2026-05-11T22:35:00Z",
    )

    assert evidence.status == "acknowledged"
    assert evidence.commit_blocked is False
    assert evidence.ack_packet_id == "rev_pkt_ack"


def test_pre_decision_objection_blocks_commit() -> None:
    evidence = resolve_pre_decision_window(
        {
            "packets": [
                _task_started(),
                _response(
                    packet_id="rev_pkt_objection",
                    kind="finding",
                    summary=f"{PRE_DECISION_OBJECTION_TOKEN}: duplicate risk",
                    evidence_refs=[f"{PRE_DECISION_OBJECTION_TOKEN}:cluster-7"],
                ),
            ]
        },
        actor="codex",
        reviewer="claude",
        plan_row_id="MP377-PRE-DECISION-COMPOSABILITY-WINDOW-S1",
        now_utc="2026-05-11T22:35:00Z",
    )

    assert evidence.status == "blocked_by_objection"
    assert evidence.commit_blocked is True
    assert evidence.objection_packet_id == "rev_pkt_objection"


def test_elapsed_pre_decision_window_allows_commit_without_objection() -> None:
    evidence = resolve_pre_decision_window(
        {"packets": [_task_started()]},
        actor="codex",
        reviewer="claude",
        plan_row_id="MP377-PRE-DECISION-COMPOSABILITY-WINDOW-S1",
        now_utc="2026-05-11T22:50:01Z",
        window_seconds=900,
    )

    assert evidence.status == "elapsed_without_objection"
    assert evidence.commit_blocked is False


def test_pre_decision_window_requires_three_anchors_and_duplicate_hunt() -> None:
    missing_anchor_evidence = resolve_pre_decision_window(
        {
            "packets": [
                _task_started(
                    anchor_refs=["section:MP377-PRE-DECISION-COMPOSABILITY-WINDOW-S1"],
                )
            ]
        },
        actor="codex",
        reviewer="claude",
        plan_row_id="MP377-PRE-DECISION-COMPOSABILITY-WINDOW-S1",
        now_utc="2026-05-11T22:35:00Z",
    )
    missing_duplicate_evidence = resolve_pre_decision_window(
        {"packets": [_task_started(evidence_refs=["contract:ReviewState"])]},
        actor="codex",
        reviewer="claude",
        plan_row_id="MP377-PRE-DECISION-COMPOSABILITY-WINDOW-S1",
        now_utc="2026-05-11T22:35:00Z",
    )

    assert missing_anchor_evidence.status == "invalid_missing_composability_anchors"
    assert missing_anchor_evidence.commit_blocked is True
    assert missing_duplicate_evidence.status == "invalid_missing_duplicate_hunt"
    assert missing_duplicate_evidence.commit_blocked is True


def _task_started(
    *,
    anchor_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, object]:
    return {
        "packet_id": "rev_pkt_task",
        "kind": TASK_STARTED_PACKET_KIND,
        "from_agent": "codex",
        "to_agent": "claude",
        "anchor_refs": anchor_refs
        if anchor_refs is not None
        else [
            "section:MP377-PRE-DECISION-COMPOSABILITY-WINDOW-S1",
            "audit:ReviewState",
            "audit:AgentLoopDecision",
            "audit:PacketCreationBinding",
        ],
        "evidence_refs": evidence_refs
        if evidence_refs is not None
        else ["duplicate_hunt:section-11-no-overlap"],
        "posted_at": "2026-05-11T22:35:00Z",
        "latest_event_id": "rev_evt_10",
        "status": "pending",
        "lifecycle_current_state": "task_started",
    }


def _response(
    *,
    packet_id: str,
    kind: str,
    summary: str,
    evidence_refs: list[str] | None = None,
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "kind": kind,
        "from_agent": "claude",
        "to_agent": "codex",
        "summary": summary,
        "body": summary,
        "anchor_refs": ["packet:rev_pkt_task"],
        "evidence_refs": evidence_refs or [],
        "posted_at": "2026-05-11T22:36:00Z",
        "latest_event_id": "rev_evt_11",
        "status": "pending",
        "lifecycle_current_state": kind,
    }
