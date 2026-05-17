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


def _empty_current_session() -> ReviewCurrentSessionState:
    return ReviewCurrentSessionState(
        current_instruction="",
        current_instruction_revision="",
        implementer_status="",
        implementer_ack="",
        implementer_ack_revision="",
        implementer_ack_state="",
    )


def test_duty_proof_unclaimed_review_renders_review_incomplete() -> None:
    """Per rev_pkt_2475/2477: semantic_review_claimed=False MUST render
    duty_proof.state='review_incomplete', not 'healthy'. This is the typed
    counterpart to the bug rev_pkt_2477 flagged where reviewer_worker hash
    freshness was treated as semantic review proof.
    """
    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={},
            current_session=_empty_current_session(),
        )
    )
    assert contract.duty_proof.state == "review_incomplete"
    assert contract.duty_proof.semantic_review_claimed is False
    assert "semantic_review_not_claimed" in contract.duty_proof.stale_reasons


def _full_review_evidence() -> dict:
    """Per rev_pkt_2485 fix #3: concrete diff-review evidence required, not just
    claim bit. Helper for tests that want a fully-evidenced semantic review."""
    return {
        "semantic_review_claimed": True,
        "reviewed_diff_hash": "tree-hash-abc",
        "reviewed_diff_base": "tree-hash-base",
        "reviewed_path_count": 5,
        "last_diff_review_at_utc": "2026-04-30T15:00:00Z",
    }


def test_duty_proof_pending_packets_renders_review_incomplete() -> None:
    """Per rev_pkt_2475 Scope A: pending packet inbox MUST keep the reviewer
    duty proof state at review_incomplete even when other signals look fresh.
    """
    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={"pending_packet_count": 3},
            current_session=_empty_current_session(),
            agent_mind=_full_review_evidence(),
        )
    )
    assert contract.duty_proof.state == "review_incomplete"
    assert contract.duty_proof.pending_packet_count == 3
    assert "pending_packet_inbox_not_consumed" in contract.duty_proof.stale_reasons


def test_duty_proof_agent_mind_semantic_claim_stays_auxiliary() -> None:
    """Per rev_pkt_2475 Scope A + rev_pkt_2485 fix #3: healthy requires both
    semantic_review_claimed=True AND concrete diff evidence (reviewed_diff_hash,
    reviewed_path_count > 0, last_diff_review_at_utc). Claim bit alone is
    insufficient. Agent-mind evidence remains auxiliary and cannot by itself
    satisfy reviewer proof.
    """
    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={"pending_packet_count": 0},
            current_session=_empty_current_session(),
            agent_mind=_full_review_evidence(),
        )
    )
    assert contract.duty_proof.state == "review_incomplete"
    assert contract.duty_proof.semantic_review_claimed is True
    assert contract.duty_proof.semantic_review_source == "agent_mind_auxiliary"
    assert contract.duty_proof.pending_packet_count == 0
    assert contract.duty_proof.reviewed_diff_hash == "tree-hash-abc"
    assert contract.duty_proof.reviewed_path_count == 5
    assert "semantic_review_source_auxiliary" in contract.duty_proof.stale_reasons


def test_duty_proof_claim_only_without_diff_evidence_renders_review_incomplete() -> None:
    """Per rev_pkt_2485 fix #3: a claim bit without reviewed_diff_hash +
    last_diff_review_at_utc + reviewed_path_count > 0 must NOT be marked
    healthy. Stale_reason 'semantic_review_evidence_missing' surfaces the gap.
    """
    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={"pending_packet_count": 0},
            current_session=_empty_current_session(),
            agent_mind={"semantic_review_claimed": True},  # claim only, no evidence
        )
    )
    assert contract.duty_proof.state == "review_incomplete"
    assert "semantic_review_evidence_missing" in contract.duty_proof.stale_reasons


def test_duty_proof_diff_drift_after_review_renders_reviewer_diff_stale() -> None:
    """Per rev_pkt_2475 Scope A + rev_pkt_2485 fix #2: if reviewer claimed
    semantic review with a reviewed_diff_hash but the live staged_tree_hash
    diverges from that reviewed hash, the proof goes stale. The comparison
    is staged_tree_hash vs reviewed_diff_hash (same shape), NOT vs commit SHA.
    """
    evidence = _full_review_evidence()
    evidence["reviewed_diff_hash"] = "reviewed-tree-hash-old"
    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={
                "pending_packet_count": 0,
                "staged_tree_hash": "live-tree-hash-new",
            },
            current_session=_empty_current_session(),
            agent_mind=evidence,
        )
    )
    assert contract.duty_proof.state == "reviewer_diff_stale"
    assert contract.duty_proof.staged_tree_hash == "live-tree-hash-new"
    assert contract.duty_proof.reviewed_diff_hash == "reviewed-tree-hash-old"


def test_contract_populates_packet_attention_from_env_caller() -> None:
    """Per rev_pkt_2498 (2,4) integration: build_reviewer_runtime_contract
    must populate contract.packet_attention with the env-declared caller's
    observation. New packet event ⇒ wake_required + pivot_required True.
    """
    import os
    from unittest.mock import patch

    with patch.dict(
        os.environ,
        {
            "DEVCTL_CALLER_AGENT": "coder-claude",
            "DEVCTL_CALLER_SESSION_ID": "session-coder-abc",
        },
    ):
        contract = build_reviewer_runtime_contract(
            ReviewerRuntimeInputs(
                snapshot=None,
                bridge_liveness={
                    "last_inbox_event_id": "evt-101",
                    "pending_packet_count": 0,
                    "canonical_active_packet_id": "rev_pkt_2498",
                    "latest_attention_changed_at_utc": "2026-04-30T16:00:00Z",
                },
                current_session=_empty_current_session(),
                agent_mind={"last_inbox_observed_event_id": "evt-100"},
            )
        )
    assert contract.packet_attention.observation_actor_id == "coder-claude"
    assert contract.packet_attention.observation_session_id == "session-coder-abc"
    assert contract.packet_attention.wake_required is True
    assert contract.packet_attention.pivot_required is True
    assert "inbox_event_unobserved" in contract.packet_attention.pivot_reasons
    assert contract.packet_attention.latest_inbox_event_id == "evt-101"
    assert contract.packet_attention.last_observed_event_id == "evt-100"


def test_contract_packet_attention_consumes_events_when_provided() -> None:
    """Per rev_pkt_2498 (3): when events are passed via ReviewerRuntimeInputs,
    packet_attention.latest_inbox_event_id is derived from the typed event
    log filtered by actor identity, NOT from the global bridge_liveness
    cursor. Per-actor_session view ⇒ dashboard-claude and coder-claude can
    see different latest-relevant events.
    """
    import os
    from unittest.mock import patch

    events = [
        {
            "event_type": "packet_posted",
            "event_id": "evt-200",
            "timestamp_utc": "2026-04-30T16:00:00Z",
            "to_agent": "claude",
            "target_session_id": "session-coder-abc",
            "packet_id": "rev_pkt_coder_only",
        },
        {
            "event_type": "packet_posted",
            "event_id": "evt-201",
            "timestamp_utc": "2026-04-30T16:00:30Z",
            "to_agent": "codex",
            "packet_id": "rev_pkt_codex",
        },
    ]
    with patch.dict(
        os.environ,
        {
            "DEVCTL_CALLER_AGENT": "coder-claude",
            "DEVCTL_CALLER_SESSION_ID": "session-coder-abc",
        },
    ):
        contract = build_reviewer_runtime_contract(
            ReviewerRuntimeInputs(
                snapshot=None,
                bridge_liveness={"pending_packet_count": 0},
                current_session=_empty_current_session(),
                events=tuple(events),
                agent_mind={"last_inbox_observed_event_id": ""},
            )
        )
    # Coder-claude with matching session_id sees the targeted packet event.
    assert contract.packet_attention.latest_inbox_event_id == "evt-200"
    assert contract.packet_attention.latest_attention_packet_id == "rev_pkt_coder_only"


def test_contract_populates_agent_runtime_clock_from_bridge_liveness() -> None:
    """Per rev_pkt_2498 (1): build_reviewer_runtime_contract must populate
    contract.agent_runtime_clock with the typed shared cursor that all
    agents read.
    """
    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={
                "last_inbox_event_id": "evt-555",
                "last_inbox_event_at_utc": "2026-04-30T16:30:00Z",
                "cadence_seconds": 30,
                "snapshot_id": "snap-xyz",
            },
            current_session=_empty_current_session(),
        )
    )
    assert contract.agent_runtime_clock.source_latest_event_id == "evt-555"
    assert contract.agent_runtime_clock.cadence_seconds == 30
    assert contract.agent_runtime_clock.snapshot_id == "snap-xyz"


def test_contract_publishes_agent_runtime_clock_from_events() -> None:
    """Event-backed projections must not expose an empty runtime clock."""
    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={"pending_packet_count": 0},
            current_session=_empty_current_session(),
            events=(
                {
                    "event_id": "rev_evt_200",
                    "timestamp_utc": "2026-04-30T16:31:00Z",
                },
            ),
        )
    )
    assert contract.agent_runtime_clock.source_latest_event_id == "rev_evt_200"
    assert (
        contract.agent_runtime_clock.source_latest_event_at_utc
        == "2026-04-30T16:31:00Z"
    )
    assert contract.agent_runtime_clock.cadence_seconds > 0
    assert (
        contract.agent_runtime_clock.last_published_at_utc
        == "2026-04-30T16:31:00Z"
    )
    assert contract.agent_runtime_clock.snapshot_id == (
        "agent-runtime-clock:rev_evt_200"
    )


def test_duty_proof_does_not_use_implementer_ack_as_reviewer_actor() -> None:
    """Per rev_pkt_2485 fix #4: implementer_ack content is not reviewer
    identity. When collaboration has no actor_authorities row with role=reviewer,
    reviewer_actor_id MUST stay empty (fail closed), not silently inherit
    from current_session.implementer_ack.
    """
    cs = ReviewCurrentSessionState(
        current_instruction="",
        current_instruction_revision="",
        implementer_status="",
        implementer_ack="claude-implementer-ack-text",
        implementer_ack_revision="",
        implementer_ack_state="current",
    )
    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={"pending_packet_count": 0},
            current_session=cs,
            collaboration=None,
            agent_mind=_full_review_evidence(),
        )
    )
    assert contract.duty_proof.reviewer_actor_id == ""
    assert contract.duty_proof.reviewer_session_id == ""


def test_duty_proof_dashboard_caller_cannot_satisfy_coder_reviewer() -> None:
    """Per rev_pkt_2475 Scope D + rev_pkt_2470/2476: when the env-declared
    caller agent does not match the proof's expected reviewer_actor_id,
    semantic_review_claimed must be downgraded and state must surface
    actor_session_mismatch. Dashboard-claude cannot satisfy reviewer duty
    on behalf of a different actor.
    """
    import os
    from dataclasses import dataclass, field as dataclass_field
    from unittest.mock import patch

    @dataclass(frozen=True)
    class _StubAuthority:
        actor_id: str = ""
        provider: str = ""
        role: str = ""
        session_id: str = ""

    @dataclass(frozen=True)
    class _StubCollaboration:
        actor_authorities: tuple = ()

    collab = _StubCollaboration(
        actor_authorities=(
            _StubAuthority(
                actor_id="coder-claude",
                provider="claude",
                role="reviewer",
                session_id="session-coder-abc",
            ),
        )
    )

    with patch.dict(
        os.environ,
        {
            "DEVCTL_CALLER_AGENT": "dashboard-claude",
            "DEVCTL_CALLER_SESSION_ID": "session-dashboard-xyz",
        },
    ):
        contract = build_reviewer_runtime_contract(
            ReviewerRuntimeInputs(
                snapshot=None,
                bridge_liveness={"pending_packet_count": 0},
                current_session=_empty_current_session(),
                collaboration=collab,
                agent_mind=_full_review_evidence(),
            )
        )

    assert contract.duty_proof.state == "actor_session_mismatch"
    assert "actor_session_mismatch" in contract.duty_proof.stale_reasons
    # The dashboard caller's claim of semantic review is REFUSED — even though
    # agent_mind reported it, the env caller doesn't match the proof's expected
    # reviewer, so semantic_review_claimed is downgraded to False.
    assert contract.duty_proof.semantic_review_claimed is False


def test_duty_proof_same_session_self_review_blocks_publish_clear() -> None:
    """A live review claim from the same concrete mutation session is
    self-attested, not independent review proof.
    """
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _StubAuthority:
        actor_id: str = ""
        provider: str = ""
        role: str = ""
        session_id: str = ""
        worktree_identity: str = ""

    @dataclass(frozen=True)
    class _StubCollaboration:
        mutation_owner: str = ""
        actor_authorities: tuple = ()

    collab = _StubCollaboration(
        mutation_owner="codex",
        actor_authorities=(
            _StubAuthority(
                actor_id="codex",
                provider="codex",
                role="reviewer",
                session_id="session-one",
                worktree_identity="/repo",
            ),
            _StubAuthority(
                actor_id="codex",
                provider="codex",
                role="implementer",
                session_id="session-one",
                worktree_identity="/repo",
            ),
        ),
    )

    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={
                "reviewer_mode": "active_dual_agent",
                "effective_reviewer_mode": "active_dual_agent",
                "reviewer_freshness": "fresh",
                "pending_packet_count": 0,
            },
            current_session=_empty_current_session(),
            collaboration=collab,
            agent_mind=_full_review_evidence(),
            prior_review_state={
                "reviewer_runtime": {
                    "review_acceptance": {
                        "review_accepted": True,
                        "reviewer_accepted_implementer_state_hash": "impl-hash",
                    }
                }
            },
        )
    )

    assert contract.duty_proof.review_conflict_class == "self_attested"
    assert "same_session" in contract.duty_proof.review_conflict_reasons
    assert "same_worktree" in contract.duty_proof.review_conflict_reasons
    assert "self_review_requires_independent_or_override" in (
        contract.duty_proof.stale_reasons
    )
    assert contract.duty_proof.state == "self_review_blocked"
    assert contract.publish_clear is False


def test_duty_proof_same_provider_distinct_runtime_is_not_self_attested() -> None:
    """A provider can occupy both roles when typed actors/runtimes differ."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _StubAuthority:
        actor_id: str = ""
        provider: str = ""
        role: str = ""
        session_id: str = ""
        worktree_identity: str = ""

    @dataclass(frozen=True)
    class _StubCollaboration:
        mutation_owner: str = ""
        actor_authorities: tuple = ()

    collab = _StubCollaboration(
        mutation_owner="coder-claude",
        actor_authorities=(
            _StubAuthority(
                actor_id="reviewer-claude",
                provider="claude",
                role="reviewer",
                session_id="review-session",
                worktree_identity="/repo-review",
            ),
            _StubAuthority(
                actor_id="coder-claude",
                provider="claude",
                role="implementer",
                session_id="code-session",
                worktree_identity="/repo-code",
            ),
        ),
    )

    contract = build_reviewer_runtime_contract(
        ReviewerRuntimeInputs(
            snapshot=None,
            bridge_liveness={
                "reviewer_mode": "active_dual_agent",
                "effective_reviewer_mode": "active_dual_agent",
                "reviewer_freshness": "fresh",
                "pending_packet_count": 0,
            },
            current_session=_empty_current_session(),
            collaboration=collab,
            agent_mind=_full_review_evidence(),
        )
    )

    assert (
        contract.duty_proof.review_conflict_class
        == "same_provider_distinct_runtime"
    )
    assert "self_review_requires_independent_or_override" not in (
        contract.duty_proof.stale_reasons
    )
