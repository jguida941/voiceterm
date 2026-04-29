"""Tests for typed agent-session continuation and resume receipts."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.review_channel.agent_session_continuation_events import (
    agent_resume_receipts_from_events,
    append_agent_resume_receipt_event,
)
from dev.scripts.devctl.runtime.agent_session_continuation import (
    agent_resume_receipt_from_mapping,
    agent_session_continuation_from_mapping,
    build_agent_resume_receipt,
    build_agent_session_continuation,
    validate_agent_resume_receipt,
    validate_agent_session_continuation,
)


def test_build_agent_session_continuation_uses_stable_continuation_hash() -> None:
    first = build_agent_session_continuation(
        agent_id="claude",
        provider="claude",
        role="implementer",
        working_tree="/repo",
        branch="feature/resume",
        last_seen_packet_id="rev_pkt_2162",
        current_assignment="Continue the dispatcher-first NN slice.",
        dirty_paths_count=105,
        current_blockers="none",
        resume_command="python3 dev/scripts/devctl.py session-resume --role implementer --format json --provider claude --write-resume-receipt",
        generated_at_utc="2026-04-29T01:00:00Z",
    )
    second = build_agent_session_continuation(
        agent_id="claude",
        provider="claude",
        role="implementer",
        working_tree="/repo",
        branch="feature/resume",
        last_seen_packet_id="rev_pkt_2162",
        current_assignment="Continue the dispatcher-first NN slice.",
        dirty_paths_count=105,
        current_blockers="none",
        resume_command="python3 dev/scripts/devctl.py session-resume --role implementer --format json --provider claude --write-resume-receipt",
        generated_at_utc="2026-04-29T01:05:00Z",
    )
    with_bootstrap = build_agent_session_continuation(
        agent_id="claude",
        provider="claude",
        role="implementer",
        working_tree="/repo",
        branch="feature/resume",
        last_seen_packet_id="rev_pkt_2162",
        current_assignment="Continue the dispatcher-first NN slice.",
        dirty_paths_count=105,
        current_blockers="none",
        resume_command="python3 dev/scripts/devctl.py session-resume --role implementer --format json --provider claude --write-resume-receipt",
        bootstrap_hash="rendered-bootstrap-sha256",
        generated_at_utc="2026-04-29T01:05:00Z",
    )

    assert first.continuation_hash == second.continuation_hash
    assert first.continuation_id == second.continuation_id
    assert first.bootstrap_hash == ""
    assert with_bootstrap.continuation_hash != first.continuation_hash
    assert first.continuation_mode == "typed_rehydration"
    restored = agent_session_continuation_from_mapping(first.to_dict())
    assert restored is not None
    assert restored.continuation_hash == first.continuation_hash
    assert validate_agent_session_continuation(first.to_dict()) == first


def test_resume_receipt_roundtrips_from_continuation() -> None:
    continuation = build_agent_session_continuation(
        agent_id="codex",
        provider="codex",
        role="reviewer",
        working_tree="/repo",
        branch="main",
        current_assignment="Review ack dispatcher proof.",
        dirty_paths_count=2,
        current_blockers="review_pending",
        resume_command="python3 dev/scripts/devctl.py session-resume --role reviewer --format json --provider codex --write-resume-receipt",
    )
    receipt = build_agent_resume_receipt(
        continuation,
        observed_at_utc="2026-04-29T02:00:00Z",
    )

    assert receipt.contract_id == "AgentResumeReceipt"
    assert receipt.result == "loaded"
    assert receipt.continuation_hash == continuation.continuation_hash
    assert receipt.load_result == "loaded"
    assert receipt.authority_result == "blocked"
    restored = agent_resume_receipt_from_mapping(receipt.to_dict())
    assert restored is not None
    assert restored.continuation_id == continuation.continuation_id
    assert validate_agent_resume_receipt(receipt.to_dict()) == receipt


def test_authority_result_fails_closed_when_explicit_allowed_conflicts() -> None:
    blocked_continuation = build_agent_session_continuation(
        agent_id="codex",
        provider="codex",
        role="reviewer",
        working_tree="/repo",
        branch="main",
        current_assignment="Review state.",
        dirty_paths_count=3,
        current_blockers="review_pending",
        authority_result="allowed",
    )
    unknown_dirty_continuation = build_agent_session_continuation(
        agent_id="claude",
        provider="claude",
        role="implementer",
        working_tree="/repo",
        branch="main",
        current_assignment="Continue state.",
        dirty_paths_count=-1,
        dirty_paths_status="unknown",
        current_blockers="none",
        authority_result="allowed",
    )
    receipt = build_agent_resume_receipt(
        blocked_continuation,
        authority_result="allowed",
        observed_at_utc="2026-04-29T06:00:00Z",
    )

    assert blocked_continuation.authority_result == "blocked"
    assert unknown_dirty_continuation.authority_result == "blocked"
    assert receipt.load_result == "loaded"
    assert receipt.authority_result == "blocked"
    assert validate_agent_resume_receipt(receipt.to_dict()) == receipt


def test_append_agent_resume_receipt_event_loads_from_event_log(tmp_path: Path) -> None:
    continuation = build_agent_session_continuation(
        agent_id="claude",
        provider="claude",
        role="implementer",
        working_tree=str(tmp_path),
        branch="feature/resume",
        current_assignment="Continue from typed state.",
        resume_command="python3 dev/scripts/devctl.py session-resume --role implementer --format json --provider claude --write-resume-receipt",
    )
    receipt = build_agent_resume_receipt(
        continuation,
        observed_at_utc="2026-04-29T03:00:00Z",
    )
    events_path = tmp_path / "events" / "trace.ndjson"

    event = append_agent_resume_receipt_event(
        events_path=events_path,
        receipt=receipt,
    )
    rows = agent_resume_receipts_from_events([event])

    assert event["event_type"] == "agent_resume_receipt"
    assert event["event_id"] == "rev_evt_0001"
    assert rows[0].receipt_id == receipt.receipt_id
    assert rows[0].continuation_hash == continuation.continuation_hash


def test_strict_continuation_validation_rejects_partial_projection() -> None:
    partial = {
        "contract_id": "AgentSessionContinuation",
        "schema_version": 1,
        "agent_id": "claude",
    }

    assert agent_session_continuation_from_mapping(partial) is not None
    try:
        validate_agent_session_continuation(partial)
    except ValueError as exc:
        assert "missing required authority field" in str(exc)
    else:
        raise AssertionError("partial continuation unexpectedly validated")


def test_strict_validation_rejects_tampered_continuation_hash() -> None:
    continuation = build_agent_session_continuation(
        agent_id="claude",
        provider="claude",
        role="implementer",
        working_tree="/repo",
        branch="main",
        current_assignment="Original assignment",
        generated_at_utc="2026-04-29T05:00:00Z",
    )
    payload = continuation.to_dict()
    payload["current_assignment"] = "Tampered assignment"

    try:
        validate_agent_session_continuation(payload)
    except ValueError as exc:
        assert "continuation_hash mismatch" in str(exc)
    else:
        raise AssertionError("tampered continuation unexpectedly validated")


def test_strict_validation_rejects_tampered_resume_receipt_id() -> None:
    continuation = build_agent_session_continuation(
        agent_id="codex",
        provider="codex",
        role="reviewer",
        working_tree="/repo",
        branch="main",
        current_assignment="Review state.",
        generated_at_utc="2026-04-29T05:00:00Z",
    )
    receipt = build_agent_resume_receipt(
        continuation,
        observed_at_utc="2026-04-29T05:01:00Z",
    )
    payload = receipt.to_dict()
    payload["authority_result"] = "blocked"

    try:
        validate_agent_resume_receipt(payload)
    except ValueError as exc:
        assert "receipt_id mismatch" in str(exc)
    else:
        raise AssertionError("tampered resume receipt unexpectedly validated")
