import json

from dev.scripts.checks.packet_absorption_required import command as guard_command
from dev.scripts.checks.packet_absorption_required.command import (
    build_report,
    render_markdown,
)
from dev.scripts.devctl.runtime.packet_absorption import (
    build_packet_absorption_receipt,
    build_packet_semantic_ingestion_receipt,
)


def test_packet_absorption_guard_fails_ack_only_actionable_packet() -> None:
    report = build_report(
        report_override={
            "packets": [
                {
                    "packet_id": "rev_pkt_4383",
                    "kind": "finding",
                    "status": "acked",
                }
            ]
        }
    )

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "ack_without_absorption_disposition"


def test_packet_absorption_guard_accepts_matching_receipt() -> None:
    receipt = build_packet_absorption_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        absorbed_by_actor="codex",
        absorbed_by_role="reviewer",
        absorbed_by_session_id="session-1",
        absorbed_at_utc="2026-05-17T18:45:00Z",
        source_semantic_ingestion_receipt_id="packet_semantic_ingestion:rev_pkt_4383:test",
        action_item_dispositions=("P86:deferred",),
        resulting_decision="continue_output_consumption_slice",
        decision_rationale="packet action item deferred behind current blocker",
        defer_reason="current output-consumption slice is blocking",
        next_slice_refs=("MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1",),
    )
    report = build_report(
        report_override={
            "packets": [
                {
                    "packet_id": "rev_pkt_4383",
                    "kind": "finding",
                    "status": "acked",
                }
            ],
            "packet_absorption_receipts": [receipt.to_dict()],
        }
    )

    assert report["ok"] is True


def test_packet_absorption_guard_markdown_lists_violation() -> None:
    report = build_report(
        report_override={
            "packets": [
                {
                    "packet_id": "rev_pkt_4383",
                    "kind": "finding",
                    "status": "acked",
                }
            ]
        }
    )

    rendered = render_markdown(report)

    assert "# check_packet_absorption_required" in rendered
    assert "ack_without_absorption_disposition" in rendered


def test_packet_absorption_guard_reports_observation_without_ingestion() -> None:
    report = build_report(
        report_override={
            "packets": [
                {
                    "packet_id": "rev_pkt_4383",
                    "kind": "finding",
                    "status": "pending",
                    "body_digest": "abc123",
                    "body_observed_at_utc": "2026-05-17T18:45:00Z",
                    "body_observed_by": "codex",
                }
            ]
        }
    )

    assert report["ok"] is False
    assert any(
        violation["reason"] == "packet_body_observed_without_semantic_ingestion"
        for violation in report["violations"]
    )


def test_packet_absorption_guard_accepts_semantic_ingestion_for_observation() -> None:
    ingestion = build_packet_semantic_ingestion_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        ingested_by_actor="codex",
        ingested_by_role="reviewer",
        ingested_by_session_id="session-1",
        ingested_at_utc="2026-05-17T18:46:00Z",
        action_item_rows=(
            {
                "action_item_id": "rev_pkt_4383:P86",
                "kind": "finding",
                "disposition": "deferred",
                "target_ref": "plan://P86",
                "packet_ref": "packet:rev_pkt_4383",
                "reason": "current output-consumption slice is blocking",
                "evidence_refs": ("packet_body_observation:evt",),
                "next_slice_refs": ("MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1",),
            },
        ),
        resulting_decision="defer_until_output_consumption_green",
        decision_rationale="current slice remains output-consumption hardening",
    )
    report = build_report(
        report_override={
            "packets": [
                {
                    "packet_id": "rev_pkt_4383",
                    "kind": "finding",
                    "status": "pending",
                    "body_digest": "abc123",
                    "body_observed_at_utc": "2026-05-17T18:45:00Z",
                    "body_observed_by": "codex",
                }
            ],
            "semantic_ingestion_receipts": [ingestion.to_dict()],
        }
    )

    assert report["ok"] is True


def test_packet_absorption_guard_default_loads_review_channel_state(
    tmp_path,
    monkeypatch,
) -> None:
    state_path = tmp_path / "dev/reports/review_channel/state/latest.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps(
            {
                "packets": [
                    {
                        "packet_id": "rev_pkt_4383",
                        "kind": "finding",
                        "status": "pending",
                        "body_digest": "abc123",
                        "body_observed_at_utc": "2026-05-17T18:45:00Z",
                        "body_observed_by": "codex",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(guard_command, "REPO_ROOT", tmp_path)

    report = build_report()

    assert report["ok"] is False
    assert any(
        violation["reason"] == "packet_body_observed_without_semantic_ingestion"
        for violation in report["violations"]
    )


def test_packet_absorption_guard_empty_input_fails() -> None:
    report = build_report(report_override={})

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "no_packet_absorption_input"
