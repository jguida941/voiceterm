"""Tests for deterministic packet carry-forward debt remediation."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.review_channel.event_reducer import reduce_events
from dev.scripts.devctl.review_channel.events import resolve_artifact_paths
from dev.scripts.devctl.review_channel.packet_debt_remediation import (
    PacketDebtRemediationInputs,
    packet_debt_remediation_report,
)
from dev.scripts.devctl.review_channel.packet_debt_remediation_contracts import (
    PacketDurableIngestionReceipt,
    durable_ingestion_event,
)
from dev.scripts.devctl.runtime.master_plan_store import read_plan_rows_jsonl
from dev.scripts.devctl.runtime.packet_carry_forward import packet_carry_forward_debts


def _review_channel_path(root: Path) -> Path:
    path = root / "dev/active/review_channel.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "# Review Channel\n\n"
            "| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |\n"
            "|---|---|---|---|---|---|\n"
            "| `codex` | reviewer | `dev/active/ai_governance_platform.md` | MP-377 | . | feature/test |\n"
            "| `claude` | dashboard | `dev/active/ai_governance_platform.md` | MP-377 | . | feature/test |\n"
        ),
        encoding="utf-8",
    )
    return path


def _master_plan(root: Path) -> None:
    path = root / "dev/active/MASTER_PLAN.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Master Plan\n", encoding="utf-8")


def _review_state(root: Path, packet: dict[str, object]) -> Path:
    path = root / "dev/reports/review_channel/projections/latest/review_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"packets": [packet]}), encoding="utf-8")
    return path


def test_packet_debt_remediation_report_names_plan_ingestion_route(
    tmp_path: Path,
) -> None:
    _master_plan(tmp_path)
    packet = {
        "packet_id": "rev_pkt_42",
        "kind": "finding",
        "status": "acked",
        "lifecycle_current_state": "acknowledged",
        "from_agent": "claude",
        "to_agent": "codex",
        "summary": "Guard issue should become durable",
        "body": "Architecture finding needs a guard/probe follow-up.",
        "plan_id": "MP-377",
        "anchor_refs": ["MP377-P0-T22AN-F"],
        "acted_on_events": [],
    }

    report = packet_debt_remediation_report(
        PacketDebtRemediationInputs(
            repo_root=tmp_path,
            artifact_paths=resolve_artifact_paths(repo_root=tmp_path),
            review_state_path=_review_state(tmp_path, packet),
            plan_store_path=tmp_path / "dev/state/plan_index.jsonl",
            limit=5,
        )
    )

    payload = report.to_dict()
    assert payload["debt_count"] == 1
    assert payload["total_debt_count"] == 1
    assert payload["omitted_debt_count"] == 0
    assert payload["action_counts"] == {"ingest_plan_row": 1}
    assert payload["rows"][0]["packet_id"] == "rev_pkt_42"
    assert payload["rows"][0]["target_ref"] == "MP-377"
    assert not (tmp_path / "dev/state/plan_index.jsonl").exists()


def test_packet_debt_remediation_reports_total_debt_beyond_limit(
    tmp_path: Path,
) -> None:
    _master_plan(tmp_path)
    first = {
        "packet_id": "rev_pkt_51",
        "kind": "finding",
        "status": "acked",
        "lifecycle_current_state": "acknowledged",
        "from_agent": "claude",
        "to_agent": "codex",
        "summary": "First durable issue",
        "body": "Architecture finding needs durable plan state.",
        "plan_id": "MP-377",
        "anchor_refs": ["MP377-P0-T22AN-F"],
        "acted_on_events": [],
    }
    second = {
        **first,
        "packet_id": "rev_pkt_52",
        "summary": "Second durable issue",
    }
    review_state_path = tmp_path / "dev/reports/review_channel/projections/latest/review_state.json"
    review_state_path.parent.mkdir(parents=True, exist_ok=True)
    review_state_path.write_text(
        json.dumps({"packets": [first, second]}),
        encoding="utf-8",
    )

    report = packet_debt_remediation_report(
        PacketDebtRemediationInputs(
            repo_root=tmp_path,
            artifact_paths=resolve_artifact_paths(repo_root=tmp_path),
            review_state_path=review_state_path,
            plan_store_path=tmp_path / "dev/state/plan_index.jsonl",
            limit=1,
        )
    )

    payload = report.to_dict()
    assert payload["debt_count"] == 1
    assert payload["total_debt_count"] == 2
    assert payload["omitted_debt_count"] == 1


def test_packet_debt_remediation_prioritizes_newest_debt_with_limit(
    tmp_path: Path,
) -> None:
    _master_plan(tmp_path)
    old_packet = {
        "packet_id": "rev_pkt_9",
        "kind": "finding",
        "status": "acked",
        "lifecycle_current_state": "acknowledged",
        "from_agent": "claude",
        "to_agent": "codex",
        "summary": "Older durable issue",
        "body": "Architecture finding needs durable plan state.",
        "plan_id": "MP-377",
        "anchor_refs": ["MP377-P0-T22AN-F"],
        "acted_on_events": [],
    }
    new_packet = {
        **old_packet,
        "packet_id": "rev_pkt_10",
        "summary": "Newer durable issue",
    }
    review_state_path = tmp_path / "dev/reports/review_channel/projections/latest/review_state.json"
    review_state_path.parent.mkdir(parents=True, exist_ok=True)
    review_state_path.write_text(
        json.dumps({"packets": [old_packet, new_packet]}),
        encoding="utf-8",
    )

    report = packet_debt_remediation_report(
        PacketDebtRemediationInputs(
            repo_root=tmp_path,
            artifact_paths=resolve_artifact_paths(repo_root=tmp_path),
            review_state_path=review_state_path,
            plan_store_path=tmp_path / "dev/state/plan_index.jsonl",
            limit=1,
        )
    )

    payload = report.to_dict()
    assert payload["debt_count"] == 1
    assert payload["rows"][0]["packet_id"] == "rev_pkt_10"


def test_packet_debt_remediation_groups_decided_packet_debt(
    tmp_path: Path,
) -> None:
    _master_plan(tmp_path)
    base_packet = {
        "kind": "finding",
        "status": "acked",
        "lifecycle_current_state": "acknowledged",
        "from_agent": "claude",
        "to_agent": "codex",
        "body": "Architecture finding needs durable plan state.",
        "plan_id": "MP-377",
        "anchor_refs": ["MP377-P0-T22AN-F"],
        "acted_on_events": [],
    }
    first = {
        **base_packet,
        "packet_id": "rev_pkt_61",
        "summary": "First decided packet",
    }
    second = {
        **base_packet,
        "packet_id": "rev_pkt_62",
        "summary": "Second decided packet",
    }
    pending = {
        **base_packet,
        "packet_id": "rev_pkt_63",
        "status": "pending",
        "summary": "Pending packet",
    }
    review_state_path = tmp_path / "dev/reports/review_channel/projections/latest/review_state.json"
    review_state_path.parent.mkdir(parents=True, exist_ok=True)
    review_state_path.write_text(
        json.dumps({"packets": [first, second, pending]}),
        encoding="utf-8",
    )

    report = packet_debt_remediation_report(
        PacketDebtRemediationInputs(
            repo_root=tmp_path,
            artifact_paths=resolve_artifact_paths(repo_root=tmp_path),
            review_state_path=review_state_path,
            plan_store_path=tmp_path / "dev/state/plan_index.jsonl",
            limit=1,
        )
    )

    payload = report.to_dict()
    detector = payload["decided_packet_debt"]
    assert detector["contract_id"] == "DecidedPacketDebtDetector"
    assert detector["total_count"] == 2
    assert detector["sample_packet_ids"] == ["rev_pkt_61", "rev_pkt_62"]
    assert detector["kind_counts"] == {"finding": 2}
    assert detector["status_counts"] == {"acked": 2}
    triage = payload["batch_triage"]
    assert triage["contract_id"] == "PacketBatchTriage"
    assert triage["total_cluster_count"] == 2
    assert triage["largest_batch_size"] == 2
    assert triage["rows"][0]["packet_count"] == 2
    assert triage["rows"][0]["recommended_action"] == "ingest_plan_row"
    assert triage["rows"][0]["sample_packet_ids"] == ["rev_pkt_61", "rev_pkt_62"]


def test_packet_debt_remediation_write_inserts_plan_row_and_receipt(
    tmp_path: Path,
) -> None:
    _master_plan(tmp_path)
    packet = {
        "event_id": "rev_evt_1000",
        "packet_id": "rev_pkt_43",
        "trace_id": "trace_43",
        "timestamp_utc": "2026-05-01T00:00:00Z",
        "kind": "finding",
        "status": "acked",
        "lifecycle_current_state": "acknowledged",
        "from_agent": "claude",
        "to_agent": "codex",
        "summary": "Packet carried guard intent",
        "body": "A recurring issue should promote a guard candidate.",
        "plan_id": "MP-377",
        "anchor_refs": ["MP377-P0-T22AN-F"],
        "acted_on_events": [],
    }

    report = packet_debt_remediation_report(
        PacketDebtRemediationInputs(
            repo_root=tmp_path,
            artifact_paths=resolve_artifact_paths(repo_root=tmp_path),
            review_state_path=_review_state(tmp_path, packet),
            plan_store_path=tmp_path / "dev/state/plan_index.jsonl",
            limit=5,
            write=True,
        )
    )

    rows = read_plan_rows_jsonl(tmp_path / "dev/state/plan_index.jsonl")
    receipt = report.rows[0].receipt
    assert rows[0].sourced_from_packets == ("rev_pkt_43",)
    assert rows[0].row_id == "PKT-BIND-REV-PKT-43"
    assert receipt is not None
    assert receipt.status == "inserted"
    assert receipt.binding_target == "PKT-BIND-REV-PKT-43"
    assert receipt.event_id == "rev_evt_0001"
    assert "rev_pkt_43" in (
        tmp_path / "dev/active/MASTER_PLAN.md"
    ).read_text(encoding="utf-8")


def test_durable_ingestion_event_clears_archived_carry_forward_debt(
    tmp_path: Path,
) -> None:
    posted = {
        "schema_version": 1,
        "event_id": "rev_evt_0001",
        "session_id": "local-review",
        "project_id": "test",
        "packet_id": "rev_pkt_44",
        "trace_id": "trace_44",
        "timestamp_utc": "2000-01-01T00:00:00Z",
        "source": "review_channel",
        "plan_id": "MP-377",
        "event_type": "packet_posted",
        "from_agent": "claude",
        "to_agent": "codex",
        "kind": "finding",
        "summary": "Expired but durably ingested",
        "body": "Durable ingestion should survive packet TTL.",
        "evidence_refs": [],
        "guidance_refs": [],
        "context_pack_refs": [],
        "confidence": 1.0,
        "requested_action": "review_only",
        "policy_hint": "review_only",
        "approval_required": False,
        "status": "pending",
        "expires_at_utc": "2000-01-01T00:30:00Z",
    }
    receipt = PacketDurableIngestionReceipt(
        packet_id="rev_pkt_44",
        status="inserted",
        reason="packet_debt_remediated",
        target_kind="plan_row",
        target_ref="MP-377",
        binding_target_kind="plan_row",
        binding_target="PKT-BIND-REV-PKT-44",
    )
    binding_event = durable_ingestion_event(
        packet=posted,
        receipt=receipt,
        event_type="packet_durable_ingestion_recorded",
        timestamp_utc="2000-01-01T00:00:01Z",
    )
    binding_event["event_id"] = "rev_evt_0002"

    review_state, _ = reduce_events(
        events=[posted, binding_event],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )

    packet = review_state["packets"][0]
    assert packet["durable_binding"]["contract_id"] == "PacketDurableIngestionReceipt"
    assert packet["disposition"]["archive_classification"] == (
        "expired_after_durable_binding"
    )
    assert packet_carry_forward_debts([packet]) == ()
