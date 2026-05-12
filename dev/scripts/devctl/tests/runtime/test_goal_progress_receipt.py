from __future__ import annotations

from dev.scripts.devctl.commands.development.continuation import continuation_signal
from dev.scripts.devctl.commands.development.models import DevelopmentPacketAttention
from dev.scripts.devctl.commands.development.orchestration_models import (
    DevelopmentOrchestrationSnapshot,
    DevelopmentWatcherLease,
)
from dev.scripts.devctl.runtime.goal_progress_receipt import (
    resolve_goal_progress_receipt,
)


def test_goal_progress_receipt_resolves_progress_for_continuation_anchor() -> None:
    receipt = resolve_goal_progress_receipt(
        {
            "packets": [
                _continuation_anchor(),
                _goal_progress(evidence_refs=["goal_progress:4/5"]),
            ]
        },
        actor="codex",
        continuation_goal="rev_pkt_anchor",
    )

    assert receipt.status == "in_progress"
    assert receipt.continuation_anchor_packet_id == "rev_pkt_anchor"
    assert receipt.latest_progress_packet_id == "rev_pkt_progress"
    assert receipt.completed_units == 4
    assert receipt.total_units == 5
    assert receipt.progress_percentage_toward_goal == 80
    assert receipt.plan_row_id == "MP377-GOAL-PROGRESS-RECEIPTS-S1"


def test_goal_progress_receipt_accepts_percentage_evidence() -> None:
    receipt = resolve_goal_progress_receipt(
        {
            "packets": [
                _continuation_anchor(),
                _goal_progress(evidence_refs=["progress_percentage:100"]),
            ]
        },
        actor="codex",
        continuation_goal="rev_pkt_anchor",
    )

    assert receipt.status == "complete"
    assert receipt.progress_percentage_toward_goal == 100


def test_continuation_signal_reports_goal_progress_fields() -> None:
    signal = continuation_signal(
        packet_attention=DevelopmentPacketAttention(),
        orchestration=DevelopmentOrchestrationSnapshot(
            agent_loop_decisions=(),
        ),
        watcher_lease=DevelopmentWatcherLease(),
        review_state={
            "packets": [
                _continuation_anchor(),
                _goal_progress(evidence_refs=["goal_progress:4/5"]),
            ]
        },
        actor="codex",
        current_action="next",
        fallback_commands=("python3 dev/scripts/devctl.py develop next --actor codex",),
    )

    assert signal.continuation_anchor_packet_id == "rev_pkt_anchor"
    assert signal.goal_progress_packet_id == "rev_pkt_progress"
    assert signal.progress_percentage_toward_goal == 80
    assert signal.goal_progress_status == "in_progress"


def _continuation_anchor() -> dict[str, object]:
    return {
        "packet_id": "rev_pkt_anchor",
        "kind": "continuation_anchor",
        "from_agent": "operator",
        "to_agent": "codex",
        "status": "pending",
        "lifecycle_current_state": "pending",
        "posted_at": "2026-05-11T23:10:00Z",
        "latest_event_id": "rev_evt_10",
    }


def _goal_progress(*, evidence_refs: list[str]) -> dict[str, object]:
    return {
        "packet_id": "rev_pkt_progress",
        "kind": "goal_progress",
        "from_agent": "codex",
        "to_agent": "operator",
        "anchor_refs": [
            "packet:rev_pkt_anchor",
            "section:MP377-GOAL-PROGRESS-RECEIPTS-S1",
        ],
        "evidence_refs": evidence_refs,
        "status": "pending",
        "lifecycle_current_state": "goal_progress",
        "posted_at": "2026-05-11T23:11:00Z",
        "latest_event_id": "rev_evt_11",
    }
