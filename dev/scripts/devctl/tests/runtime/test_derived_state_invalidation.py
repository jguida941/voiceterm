"""Coverage for shared derived-state invalidation payload helpers."""

from __future__ import annotations

from dev.scripts.devctl.runtime.derived_state_invalidation import (
    PLAN_INGESTION_DERIVED_STATE_CONSUMERS,
    PLAN_INGESTION_INVALIDATION_SOURCE,
    derived_state_invalidation_payload,
)


def test_derived_state_invalidation_payload_normalizes_optional_fields() -> None:
    payload = derived_state_invalidation_payload(
        source="packet_lifecycle_transition",
        producer_id="review_channel.packet_lifecycle_transition",
        producer_kind="review_channel_event",
        invalidated_consumers=("develop.next", "develop.next", "startup_context"),
        next_consumer_action="reload",
        packet_id=" rev_pkt_1 ",
        row_ids=("MP377-A", "", "MP377-A"),
        extra={"actor": " codex ", "empty": ""},
    )

    assert payload["contract_id"] == "DerivedStateInvalidation"
    assert payload["invalidated"] is True
    assert payload["packet_id"] == "rev_pkt_1"
    assert payload["row_ids"] == ["MP377-A"]
    assert payload["invalidated_consumers"] == ["develop.next", "startup_context"]
    assert payload["actor"] == " codex "
    assert "empty" not in payload


def test_plan_ingestion_invalidation_names_plan_and_work_consumers() -> None:
    payload = derived_state_invalidation_payload(
        source=PLAN_INGESTION_INVALIDATION_SOURCE,
        producer_id="develop.plan_ingestion",
        producer_kind="typed_receipt",
        invalidated_consumers=PLAN_INGESTION_DERIVED_STATE_CONSUMERS,
        next_consumer_action=(
            "reload_plan_authority_and_ingestion_receipts_before_work_decision"
        ),
        source_ref="packet:rev_pkt_1",
        packet_id="rev_pkt_1",
        receipt_id="plan-ingest-1",
        action_id="plan-action-1",
        row_ids=("MP377-A",),
        target_ref="plan:MP-377",
        status="accepted",
        store_statuses=("inserted",),
    )

    assert payload["source"] == "plan_ingestion_event"
    assert payload["producer_id"] == "develop.plan_ingestion"
    assert payload["receipt_id"] == "plan-ingest-1"
    assert payload["row_ids"] == ["MP377-A"]
    assert payload["invalidated_consumers"] == list(
        PLAN_INGESTION_DERIVED_STATE_CONSUMERS
    )
