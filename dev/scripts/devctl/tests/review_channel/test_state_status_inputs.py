"""Tests for review-channel status input loading."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.state_status_inputs import (
    _merge_prior_review_state,
)


def test_merge_prior_review_state_preserves_checkpoint_and_continuity_from_local_payload() -> None:
    canonical = {
        "reviewer_runtime": {
            "review_acceptance": {
                "reviewer_accepted_implementer_state_hash": "canonical-hash",
            }
        },
        "packets": [],
    }
    local = {
        "packets": [
            {
                "packet_id": "rev_pkt_3110",
                "status": "applied",
            }
        ],
        "latest_reviewer_checkpoint": {
            "current_instruction": "old checkpoint",
            "event_id": "rev_evt_52534",
        },
        "packet_continuity_index": {
            "rows": [
                {
                    "packet_id": "rev_pkt_3110",
                    "status": "applied",
                    "latest_event_id": "rev_evt_53859",
                }
            ]
        },
    }

    merged = _merge_prior_review_state(canonical, local)

    assert merged["latest_reviewer_checkpoint"]["event_id"] == "rev_evt_52534"
    assert (
        merged["packet_continuity_index"]["rows"][0]["packet_id"]
        == "rev_pkt_3110"
    )
    assert merged["packets"][0]["packet_id"] == "rev_pkt_3110"


def test_merge_prior_review_state_fills_packet_body_observation_fields_by_id() -> None:
    canonical = {
        "packets": [
            {
                "packet_id": "rev_pkt_body",
                "status": "pending",
                "body_observed_by": "",
                "body_observation_events": [],
            }
        ]
    }
    event_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_body",
                "status": "pending",
                "body_observed_by": "codex",
                "body_observed_event_id": "rev_evt_73091",
                "body_observation_events": [
                    {
                        "contract_id": "PacketBodyObservation",
                        "event_id": "rev_evt_73091",
                    }
                ],
            }
        ]
    }

    merged = _merge_prior_review_state(canonical, event_state)

    packet = merged["packets"][0]
    assert packet["body_observed_by"] == "codex"
    assert packet["body_observed_event_id"] == "rev_evt_73091"
    assert packet["body_observation_events"][0]["contract_id"] == (
        "PacketBodyObservation"
    )
