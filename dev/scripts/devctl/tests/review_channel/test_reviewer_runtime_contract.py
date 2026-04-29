"""Focused tests for reviewer runtime contract projection."""

from datetime import datetime, timezone

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


def test_reviewer_runtime_contract_folds_agent_mind_liveness_into_posture() -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={
                "reviewer_mode": "tools_only",
                "effective_reviewer_mode": "tools_only",
            },
            current_session=ReviewCurrentSessionState(
                current_instruction="",
                current_instruction_revision="",
                implementer_status="",
                implementer_ack="",
                implementer_ack_revision="",
                implementer_ack_state="missing",
            ),
            agent_mind={
                "agent_provider": "codex",
                "events": [{"timestamp": now, "event_type": "file_change"}],
            },
        )
    )

    actor = contract.session_posture.actors[0]
    assert actor.actor_id == "codex"
    assert actor.live is True
    assert actor.occupied_lane == ""


def test_fresh_checkpoint_bridge_acceptance_overrides_stale_prior_without_hash() -> None:
    bridge_text = """
# Bridge

## Current Verdict

accepted: release preflight passed for current HEAD.

## Open Findings

none

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

- Next scoped plan item.
"""
    prior_review_state = {
        "reviewer_runtime": {
            "review_acceptance": {
                "current_verdict": "",
                "open_findings": "477 expired unresolved review packet(s)",
                "review_accepted": False,
                "reviewer_accepted_implementer_state_hash": "",
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
                "last_checkpoint_action": "reviewer-checkpoint",
                "review_needed": False,
                "reviewed_hash_current": True,
            },
            current_session=ReviewCurrentSessionState(
                current_instruction="- Next scoped plan item.",
                current_instruction_revision="instruction123",
                implementer_status="- pending",
                implementer_ack="- pending",
                implementer_ack_revision="",
                implementer_ack_state="pending",
            ),
            prior_review_state=prior_review_state,
        )
    )

    acceptance = contract.review_acceptance
    assert acceptance.current_verdict == (
        "accepted: release preflight passed for current HEAD."
    )
    assert acceptance.open_findings == "none"
    assert acceptance.review_accepted is True


def test_stale_checkpoint_hash_keeps_prior_acceptance_authority() -> None:
    bridge_text = """
# Bridge

## Current Verdict

accepted

## Open Findings

none
"""
    prior_review_state = {
        "reviewer_runtime": {
            "review_acceptance": {
                "current_verdict": "- prior verdict",
                "open_findings": "- prior finding",
                "review_accepted": False,
                "reviewer_accepted_implementer_state_hash": "prior-hash",
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
                "last_checkpoint_action": "reviewer-checkpoint",
                "review_needed": False,
                "reviewed_hash_current": False,
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
        )
    )

    acceptance = contract.review_acceptance
    assert acceptance.current_verdict == "- prior verdict"
    assert acceptance.open_findings == "- prior finding"
    assert acceptance.review_accepted is False
    assert acceptance.reviewer_accepted_implementer_state_hash == "prior-hash"
