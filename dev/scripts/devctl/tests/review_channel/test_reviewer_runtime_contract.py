"""Focused tests for reviewer runtime contract projection."""

from dev.scripts.devctl.review_channel.handoff import extract_bridge_snapshot
from dev.scripts.devctl.review_channel.reviewer_runtime_contract import (
    ReviewerRuntimeInputs,
    build_reviewer_runtime_contract,
)
from dev.scripts.devctl.runtime.review_state_models import ReviewCurrentSessionState


def test_checkpoint_override_uses_fresh_bridge_acceptance_over_stale_prior() -> None:
    bridge_text = """
# Bridge

## Current Verdict

- accepted

## Open Findings

- none

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

- Await reviewer instruction refresh.
"""
    prior_review_state = {
        "review_state": {
            "reviewer_runtime": {
                "review_acceptance": {
                    "current_verdict": "",
                    "open_findings": "475 expired unresolved review packet(s)",
                    "review_accepted": False,
                    "reviewer_accepted_implementer_state_hash": "",
                }
            }
        }
    }

    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=extract_bridge_snapshot(bridge_text),
            bridge_liveness={
                "reviewer_mode": "active_dual_agent",
                "effective_reviewer_mode": "active_dual_agent",
                "reviewer_freshness": "fresh",
            },
            current_session=ReviewCurrentSessionState(
                current_instruction="",
                current_instruction_revision="",
                implementer_status="",
                implementer_ack="",
                implementer_ack_revision="",
                implementer_ack_state="missing",
            ),
            prior_review_state=prior_review_state,
            reviewer_accepted_implementer_state_hash_override="fresh-checkpoint-hash",
        )
    )

    acceptance = contract.review_acceptance
    assert acceptance.current_verdict == "- accepted"
    assert acceptance.open_findings == "- none"
    assert acceptance.review_accepted is True
    assert (
        acceptance.reviewer_accepted_implementer_state_hash
        == "fresh-checkpoint-hash"
    )
