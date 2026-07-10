"""Coverage for instruction authority decisions and transition receipts."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.review_channel.event_projection_queue import (
    build_event_queue_state,
)
from dev.scripts.devctl.review_channel.instruction_transitions import (
    maybe_record_instruction_transition,
)
from dev.scripts.devctl.runtime.instruction_authority import (
    DEFAULT_INSTRUCTION_TRANSITIONS_REL,
    InstructionPriorityDecision,
)


def _packet(packet_id: str, *, status: str = "pending") -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "kind": "action_request",
        "summary": f"Run {packet_id}",
        "status": status,
        "to_agent": "claude",
        "requested_action": "stage_commit_pipeline",
        "posted_at": "2026-04-29T03:00:00Z",
        "expires_at_utc": "2099-04-29T03:30:00Z",
    }


def test_queue_projection_emits_priority_decision_and_provenance() -> None:
    queue = build_event_queue_state(
        {"codex": 0, "claude": 1, "cursor": 0, "operator": 0},
        0,
        [_packet("rev_pkt_a")],
    )

    source = queue.derived_next_instruction_source
    decision = queue.instruction_priority_decision
    provenance = source["provenance"]

    assert queue.derived_next_instruction.startswith("Priority action_request")
    assert decision["contract_id"] == "InstructionPriorityDecision"
    assert decision["selected_instruction_id"] == "rev_pkt_a"
    assert decision["rule_id"] == "action_request_priority"
    assert provenance["contract_id"] == "IngestionProvenance"
    assert provenance["source_kind"] == "ReviewPacketEvent"
    assert provenance["source_file"].endswith("trace.ndjson")
    assert provenance["source_hash"].startswith("sha256:")


def test_instruction_transition_receipt_appends_once(tmp_path: Path) -> None:
    prior_decision = InstructionPriorityDecision(
        selected_instruction_id="rev_pkt_a",
        selected_source_kind="packet",
        rule_id="action_request_priority",
        decided_at_utc="2026-04-29T03:00:00Z",
    ).to_dict()
    current_decision = InstructionPriorityDecision(
        selected_instruction_id="rev_pkt_b",
        selected_source_kind="packet",
        rule_id="action_request_priority",
        rejected_alternatives=("rev_pkt_a",),
        rejection_reasons=("rev_pkt_a:applied",),
        decided_at_utc="2026-04-29T03:05:00Z",
    ).to_dict()
    provenance = {
        "schema_version": 1,
        "contract_id": "IngestionProvenance",
        "source_file": "dev/reports/review_channel/events/trace.ndjson",
        "source_line": 0,
        "source_kind": "ReviewPacketEvent",
        "source_hash": "sha256:abc",
        "observed_at_utc": "2026-04-29T03:05:00Z",
        "section_authority": "review_packet",
    }
    prior = {
        "queue": {
            "derived_next_instruction_source": {
                "packet_id": "rev_pkt_a",
                "provenance": provenance,
                "priority_decision": prior_decision,
            },
            "instruction_priority_decision": prior_decision,
        },
        "packets": [_packet("rev_pkt_a", status="acked")],
    }
    current = {
        "queue": {
            "derived_next_instruction_source": {
                "packet_id": "rev_pkt_b",
                "provenance": provenance,
                "priority_decision": current_decision,
            },
            "instruction_priority_decision": current_decision,
        },
        "packets": [_packet("rev_pkt_a", status="applied"), _packet("rev_pkt_b")],
    }

    first = maybe_record_instruction_transition(
        repo_root=tmp_path,
        prior_review_state=prior,
        review_state=current,
    )
    second = maybe_record_instruction_transition(
        repo_root=tmp_path,
        prior_review_state=prior,
        review_state=current,
    )

    path = tmp_path / DEFAULT_INSTRUCTION_TRANSITIONS_REL
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    assert first is not None
    assert second is None
    assert len(rows) == 1
    assert rows[0]["contract_id"] == "InstructionTransitionReceipt"
    assert rows[0]["closed_instruction_id"] == "rev_pkt_a"
    assert rows[0]["close_reason"] == "packet_applied"
    assert rows[0]["new_instruction_id"] == "rev_pkt_b"
    assert rows[0]["new_instruction_provenance"]["source_hash"] == "sha256:abc"
