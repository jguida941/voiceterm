from dev.scripts.devctl.runtime.packet_absorption import (
    build_packet_absorption_receipt,
    build_packet_semantic_ingestion_receipt,
    evaluate_packet_absorption_required,
    packet_absorbed,
    packet_absorption_receipt_from_mapping,
    packet_semantically_ingested,
)


def _actionable_packet() -> dict[str, object]:
    return {
        "packet_id": "rev_pkt_4383",
        "kind": "finding",
        "status": "acked",
        "body_digest": "abc123",
    }


def _observed_actionable_packet(packet_id: str = "rev_pkt_4383") -> dict[str, object]:
    return {
        **_actionable_packet(),
        "packet_id": packet_id,
        "status": "pending",
        "body_observed_at_utc": "2026-05-17T18:45:00Z",
        "body_observed_by": "codex",
        "body_observed_role": "reviewer",
        "body_observed_session_id": "session-1",
        "body_observed_event_id": f"evt-{packet_id}",
    }


def _semantic_action_rows(packet_id: str = "rev_pkt_4383") -> tuple[dict[str, object], ...]:
    return (
        {
            "action_item_id": f"{packet_id}:P86",
            "kind": "finding",
            "disposition": "deferred",
            "target_ref": "plan://P86",
            "packet_ref": f"packet:{packet_id}",
            "reason": "current output-consumption slice is blocking",
            "evidence_refs": ("packet_body_observation:evt",),
            "next_slice_refs": ("MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1",),
        },
    )


def test_ack_does_not_satisfy_absorption_for_actionable_packet() -> None:
    packet = _actionable_packet()

    report = evaluate_packet_absorption_required({"packets": [packet]})

    assert packet_absorbed(packet) is False
    assert report.ok is False
    assert report.violations[0]["reason"] == "ack_without_absorption_disposition"


def test_body_observed_without_semantic_ingestion_fails() -> None:
    packet = _observed_actionable_packet()

    report = evaluate_packet_absorption_required({"packets": [packet]})

    assert packet_semantically_ingested(packet) is False
    assert report.ok is False
    assert any(
        violation["reason"] == "packet_body_observed_without_semantic_ingestion"
        for violation in report.violations
    )


def test_repeated_body_observation_without_ingestion_reports_treadmill() -> None:
    packets = [
        _observed_actionable_packet("rev_pkt_4383"),
        _observed_actionable_packet("rev_pkt_4384"),
    ]

    report = evaluate_packet_absorption_required({"packets": packets})

    assert report.ok is False
    assert any(
        violation["reason"] == "packet_observation_without_semantic_ingestion"
        for violation in report.violations
    )


def test_semantic_ingestion_receipt_removes_observation_violation() -> None:
    packet = _observed_actionable_packet()
    receipt = build_packet_semantic_ingestion_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        ingested_by_actor="codex",
        ingested_by_role="reviewer",
        ingested_by_session_id="session-1",
        ingested_at_utc="2026-05-17T18:46:00Z",
        action_item_rows=_semantic_action_rows(),
        resulting_decision="defer_until_output_consumption_green",
        decision_rationale="current slice remains output-consumption hardening",
    )

    report = evaluate_packet_absorption_required(
        {"packets": [packet], "semantic_ingestion_receipts": [receipt.to_dict()]}
    )

    assert packet_semantically_ingested(
        packet,
        semantic_ingestion_receipts=(receipt.to_dict(),),
    ) is True
    assert report.ok is True


def test_semantic_ingestion_requires_structured_action_item_rows() -> None:
    packet = _observed_actionable_packet()
    receipt = build_packet_semantic_ingestion_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        ingested_by_actor="codex",
        ingested_by_role="reviewer",
        ingested_by_session_id="session-1",
        ingested_at_utc="2026-05-17T18:46:00Z",
        action_items=("P86:verify_hmac_forgery_claim",),
        resulting_decision="defer_until_output_consumption_green",
        decision_rationale="current slice remains output-consumption hardening",
    )

    report = evaluate_packet_absorption_required(
        {"packets": [packet], "semantic_ingestion_receipts": [receipt.to_dict()]}
    )

    assert report.ok is False
    assert any(
        violation["reason"] == "packet_semantic_ingestion_receipt_incomplete"
        and "action_item_rows" in violation["detail"]
        for violation in report.violations
    )


def test_semantic_ingestion_does_not_satisfy_acked_absorption() -> None:
    packet = {
        **_observed_actionable_packet(),
        "status": "acked",
    }
    receipt = build_packet_semantic_ingestion_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        ingested_by_actor="codex",
        ingested_by_role="reviewer",
        ingested_by_session_id="session-1",
        ingested_at_utc="2026-05-17T18:46:00Z",
        action_item_rows=_semantic_action_rows(),
        resulting_decision="defer_until_output_consumption_green",
        decision_rationale="current slice remains output-consumption hardening",
    )

    report = evaluate_packet_absorption_required(
        {"packets": [packet], "semantic_ingestion_receipts": [receipt.to_dict()]}
    )

    assert packet_semantically_ingested(
        packet,
        semantic_ingestion_receipts=(receipt.to_dict(),),
    ) is True
    assert packet_absorbed(packet, absorption_receipts=()) is False
    assert report.ok is False
    assert any(
        violation["reason"] == "ack_without_absorption_disposition"
        for violation in report.violations
    )


def test_bare_absorbed_timestamp_does_not_satisfy_actionable_packet() -> None:
    packet = {
        **_actionable_packet(),
        "absorbed_at_utc": "2026-05-17T18:45:00Z",
    }

    report = evaluate_packet_absorption_required({"packets": [packet]})

    assert packet_absorbed(packet) is False
    assert report.ok is False
    assert any(
        violation["reason"] == "ack_without_absorption_disposition"
        for violation in report.violations
    )


def test_absorption_receipt_satisfies_actionable_ack() -> None:
    packet = _actionable_packet()
    receipt = build_packet_absorption_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        absorbed_by_actor="codex",
        absorbed_by_role="reviewer",
        absorbed_by_session_id="session-1",
        absorbed_at_utc="2026-05-17T18:45:00Z",
        action_item_dispositions=("P86:deferred",),
        resulting_decision="continue_output_consumption_slice",
        decision_rationale="packet action items were classified",
        defer_reason="current output-consumption slice is blocking",
        next_slice_refs=("MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1",),
    )

    report = evaluate_packet_absorption_required(
        {"packets": [packet], "receipts": [receipt.to_dict()]}
    )

    assert packet_absorbed(packet, absorption_receipts=(receipt.to_dict(),)) is True
    assert report.ok is True


def test_accepted_absorption_requires_evidence_refs() -> None:
    packet = _actionable_packet()
    receipt = build_packet_absorption_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        absorbed_by_actor="codex",
        absorbed_by_role="reviewer",
        absorbed_by_session_id="session-1",
        absorbed_at_utc="2026-05-17T18:45:00Z",
        action_item_dispositions=("P235:accepted",),
        resulting_decision="implement_output_consumption_slice",
        decision_rationale="packet action item accepted",
    )

    report = evaluate_packet_absorption_required(
        {"packets": [packet], "receipts": [receipt.to_dict()]}
    )

    assert report.ok is False
    assert any(
        violation["reason"] == "packet_absorption_receipt_incomplete"
        and "accepted:evidence_refs" in violation["detail"]
        for violation in report.violations
    )


def test_accepted_absorption_with_evidence_refs_passes() -> None:
    packet = _actionable_packet()
    receipt = build_packet_absorption_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        absorbed_by_actor="codex",
        absorbed_by_role="reviewer",
        absorbed_by_session_id="session-1",
        absorbed_at_utc="2026-05-17T18:45:00Z",
        action_item_dispositions=("P235:accepted",),
        resulting_decision="implement_output_consumption_slice",
        decision_rationale="packet action item accepted",
        evidence_refs=("test:test_packet_absorption.py",),
    )

    report = evaluate_packet_absorption_required(
        {"packets": [packet], "receipts": [receipt.to_dict()]}
    )

    assert packet_absorbed(packet, absorption_receipts=(receipt.to_dict(),)) is True
    assert report.ok is True


def test_packet_absorption_receipt_round_trips() -> None:
    receipt = build_packet_absorption_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        absorbed_by_actor="codex",
        absorbed_by_role="reviewer",
        absorbed_by_session_id="session-1",
        absorbed_at_utc="2026-05-17T18:45:00Z",
        action_item_dispositions=("P86:deferred",),
        resulting_decision="continue_output_consumption_slice",
        decision_rationale="packet action items were classified",
        defer_reason="current output-consumption slice is blocking",
        next_slice_refs=("MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1",),
    )

    parsed = packet_absorption_receipt_from_mapping(receipt.to_dict())

    assert parsed.receipt_id == receipt.receipt_id
    assert parsed.packet_id == "rev_pkt_4383"
    assert parsed.action_item_dispositions == (
        "P86:deferred",
    )
    assert parsed.defer_reason == "current output-consumption slice is blocking"
    assert parsed.next_slice_refs == ("MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1",)


def test_incomplete_absorption_receipt_does_not_satisfy_packet() -> None:
    packet = _actionable_packet()
    receipt = build_packet_absorption_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        absorbed_by_actor="codex",
        absorbed_by_role="reviewer",
        absorbed_by_session_id="session-1",
        absorbed_at_utc="2026-05-17T18:45:00Z",
        action_item_dispositions=("P86:deferred",),
        resulting_decision="continue_output_consumption_slice",
        decision_rationale="packet action items were classified",
    )

    report = evaluate_packet_absorption_required(
        {"packets": [packet], "receipts": [receipt.to_dict()]}
    )

    assert packet_absorbed(packet, absorption_receipts=(receipt.to_dict(),)) is False
    assert report.ok is False
    assert any(
        violation["reason"] == "packet_absorption_receipt_incomplete"
        and "next_slice_refs" in violation["detail"]
        for violation in report.violations
    )


def test_invalid_absorption_disposition_fails() -> None:
    packet = _actionable_packet()
    receipt = build_packet_absorption_receipt(
        packet_id="rev_pkt_4383",
        body_sha256="abc123",
        absorbed_by_actor="codex",
        absorbed_by_role="reviewer",
        absorbed_by_session_id="session-1",
        absorbed_at_utc="2026-05-17T18:45:00Z",
        action_item_dispositions=("P86:maybe_later",),
        resulting_decision="continue_output_consumption_slice",
        decision_rationale="packet action items were classified",
        defer_reason="current output-consumption slice is blocking",
        next_slice_refs=("MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1",),
    )

    report = evaluate_packet_absorption_required(
        {"packets": [packet], "receipts": [receipt.to_dict()]}
    )

    assert report.ok is False
    assert any(
        violation["reason"] == "packet_absorption_invalid_disposition"
        for violation in report.violations
    )
