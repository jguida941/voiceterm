"""Tests for the ACKed packet carry-forward debt probe."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.checks.review_probes.probe_packet_carry_forward_debt import (
    packet_carry_forward_debt_hints,
)
from dev.scripts.devctl.runtime.master_plan_contract import PlanRow, SDLCStage
from dev.scripts.devctl.runtime.master_plan_store import write_plan_rows_jsonl
from dev.scripts.devctl.runtime.packet_carry_forward import (
    durable_packet_ids_from_finding_rows,
    durable_packet_ids_from_plan_rows,
    packet_carry_forward_debts,
)


def test_packet_carry_forward_debts_flag_acked_unowned_packet() -> None:
    debts = packet_carry_forward_debts(
        (
            {
                "packet_id": "rev_pkt_10",
                "kind": "finding",
                "status": "acked",
                "from_agent": "claude",
                "to_agent": "codex",
                "summary": "scope finding",
                "acted_on_events": [],
            },
            {
                "packet_id": "rev_pkt_11",
                "kind": "finding",
                "status": "acked",
                "acted_on_events": [{"action": "dismissed"}],
            },
        ),
        durable_packet_ids=(),
    )

    assert len(debts) == 1
    assert debts[0].packet_id == "rev_pkt_10"
    assert debts[0].reason == "acked_without_terminal_or_durable_owner"


def test_packet_carry_forward_debts_accept_plan_row_owner() -> None:
    row = PlanRow(
        row_id="PKT-REV-PKT-10",
        title="scope finding",
        status="applied",
        sdlc_stage=SDLCStage.IMPL,
        sourced_from_packets=("rev_pkt_10",),
    )

    debts = packet_carry_forward_debts(
        (
            {
                "packet_id": "rev_pkt_10",
                "kind": "plan_gap_review",
                "status": "acked",
                "acted_on_events": [],
            },
        ),
        durable_packet_ids=durable_packet_ids_from_plan_rows((row,)),
    )

    assert debts == ()


def test_packet_carry_forward_debts_ignore_acked_communication_notice() -> None:
    debts = packet_carry_forward_debts(
        (
            {
                "packet_id": "rev_pkt_communication",
                "kind": "system_notice",
                "status": "acked",
                "summary": "Plan status only",
                "body": "Mentions guard and plan progress but carries no work item.",
                "acted_on_events": [],
            },
        ),
        durable_packet_ids=(),
    )

    assert debts == ()


def test_packet_carry_forward_debts_ignore_bound_review_only_status_notice() -> None:
    debts = packet_carry_forward_debts(
        (
            {
                "packet_id": "rev_pkt_status",
                "kind": "system_notice",
                "status": "acked",
                "summary": "Codex status: architecture slice landed",
                "body": "Mentions remaining guard and probe work already owned by plan.",
                "requested_action": "review_only",
                "policy_hint": "review_only",
                "plan_id": "MP-377",
                "intake_ref": "work_intake://plan_target/example",
                "anchor_refs": ["section:MP-377"],
                "acted_on_events": [],
                "packet_creation_binding": {
                    "contract_id": "PacketCreationBinding",
                    "status": "skipped",
                    "reason": "communication_only_or_no_durable_plan_context",
                    "binding_target_kind": "communication_only",
                },
            },
        ),
        durable_packet_ids=(),
    )

    assert debts == ()


def test_packet_carry_forward_debts_flag_pending_unbound_finding() -> None:
    debts = packet_carry_forward_debts(
        (
            {
                "packet_id": "rev_pkt_pending",
                "kind": "finding",
                "status": "pending",
                "summary": "Fresh architecture finding",
                "acted_on_events": [],
            },
        ),
        durable_packet_ids=(),
    )

    assert len(debts) == 1
    assert debts[0].reason == "pending_durable_intent_without_creation_binding"


def test_packet_carry_forward_debts_flag_misclassified_durable_notice() -> None:
    debts = packet_carry_forward_debts(
        (
            {
                "packet_id": "rev_pkt_notice_bug",
                "kind": "system_notice",
                "status": "pending",
                "summary": "Architecture bug needs plan ingestion",
                "packet_creation_binding": {
                    "contract_id": "PacketCreationBinding",
                    "status": "skipped",
                    "reason": "communication_only_or_no_durable_plan_context",
                    "binding_target_kind": "communication_only",
                },
            },
        ),
        durable_packet_ids=(),
    )

    assert len(debts) == 1
    assert debts[0].reason == "durable_intent_classified_communication_only"


def test_packet_carry_forward_debts_flag_promoted_finding_without_owner() -> None:
    debts = packet_carry_forward_debts(
        (
            {
                "packet_id": "rev_pkt_12",
                "kind": "finding",
                "status": "pending",
                "packet_outcome": {"outcome": "promoted_to_finding"},
            },
        ),
        durable_packet_ids=(),
    )

    assert len(debts) == 1
    assert debts[0].packet_id == "rev_pkt_12"
    assert debts[0].reason == "promoted_to_finding_without_durable_owner"


def test_packet_carry_forward_debts_accept_finding_row_owner() -> None:
    debts = packet_carry_forward_debts(
        (
            {
                "packet_id": "rev_pkt_13",
                "kind": "finding",
                "status": "pending",
                "packet_outcome": {"outcome": "promoted_to_finding"},
            },
        ),
        durable_packet_ids=durable_packet_ids_from_finding_rows(
            (
                {
                    "contract_id": "FindingReview",
                    "finding_id": "packet_transition_session_disambiguation_gap",
                    "source_packet_ids": ["rev_pkt_13"],
                },
            )
        ),
    )

    assert debts == ()


def test_probe_hints_include_only_unowned_acked_packets(tmp_path: Path) -> None:
    review_state = tmp_path / "review_state.json"
    plan_store = tmp_path / "plan_index.jsonl"
    finding_log = tmp_path / "finding_reviews.jsonl"
    review_state.write_text(
        json.dumps(
            {
                "packets": [
                    {
                        "packet_id": "rev_pkt_20",
                        "kind": "finding",
                        "status": "acked",
                        "lifecycle_current_state": "acknowledged",
                        "from_agent": "claude",
                        "to_agent": "codex",
                        "plan_id": "MP-377",
                        "intake_ref": "work_intake://plan_target/example",
                        "acted_on_events": [],
                    },
                    {
                        "packet_id": "rev_pkt_21",
                        "kind": "finding",
                        "status": "acked",
                        "acted_on_events": [],
                    },
                    {
                        "packet_id": "rev_pkt_22",
                        "kind": "finding",
                        "status": "pending",
                        "packet_outcome": {"outcome": "promoted_to_finding"},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    write_plan_rows_jsonl(
        plan_store,
        (
            PlanRow(
                row_id="PKT-REV-PKT-21",
                title="owned packet",
                status="applied",
                sdlc_stage=SDLCStage.IMPL,
                sourced_from_packets=("rev_pkt_21",),
            ),
        ),
    )
    finding_log.write_text(
        json.dumps(
            {
                "contract_id": "FindingReview",
                "finding_id": "packet_expiry_consumes_urgent_findings",
                "notes": "source_packet_ids=rev_pkt_22",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    hints = packet_carry_forward_debt_hints(
        review_state_path=review_state,
        plan_store_path=plan_store,
        finding_log_path=finding_log,
    )

    assert len(hints) == 1
    assert hints[0].symbol == "rev_pkt_20"
    assert "reason=acked_without_terminal_or_durable_owner" in hints[0].signals
    assert "kind=finding" in hints[0].signals
    assert "plan_id=MP-377" in hints[0].signals
