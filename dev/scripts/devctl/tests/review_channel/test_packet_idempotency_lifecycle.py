"""Lifecycle-aware idempotency tests for MP377-P0-T22Y-B.

These regression tests prove that ``append_event`` consults a packet's
lifecycle status before refusing a duplicate semantic post. Packets that
ended in ``dismissed`` or ``expired`` leave the retry slot open; packets
in ``applied`` (terminal-success), ``pending``, or ``acked`` (in-flight)
remain consumed.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from dev.scripts.devctl.review_channel.event_store import append_event


def _packet_post_event(
    *,
    idempotency_key: str,
    summary: str = "Stage verified commit pipeline",
    body: str = "Full guard profile passed.",
) -> dict[str, object]:
    """Return a minimal packet_posted event with a stable semantic shape."""
    return {
        "event_type": "packet_posted",
        "packet_id": "",
        "trace_id": "",
        "from_agent": "codex",
        "to_agent": "claude",
        "kind": "action_request",
        "summary": summary,
        "body": body,
        "requested_action": "stage_commit_pipeline",
        "policy_hint": "safe_auto_apply",
        "idempotency_key": idempotency_key,
    }


def _transition_event(
    *,
    event_type: str,
    packet_id: str,
    event_id: str,
) -> dict[str, object]:
    """Return a minimal lifecycle transition event for the given packet."""
    return {
        "event_id": event_id,
        "event_type": event_type,
        "packet_id": packet_id,
        "idempotency_key": "",
    }


def test_retry_after_dismiss_is_permitted() -> None:
    """A packet that ended in dismissed must NOT block a fresh retry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        original = _packet_post_event(idempotency_key="key_lifecycle_001")
        first = append_event(events_path, original, existing_events=[])

        dismissed_event = _transition_event(
            event_type="packet_dismissed",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_dismiss_001",
        )
        dismissed = append_event(
            events_path,
            dismissed_event,
            existing_events=[first],
        )

        retry = _packet_post_event(idempotency_key="key_lifecycle_001")
        second = append_event(
            events_path,
            retry,
            existing_events=[first, dismissed],
        )

        assert second["packet_id"] != first["packet_id"]
        assert str(second["event_type"]) == "packet_posted"


def test_retry_after_apply_is_refused() -> None:
    """A packet that reached applied must continue blocking duplicate retries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        original = _packet_post_event(idempotency_key="key_lifecycle_002")
        first = append_event(events_path, original, existing_events=[])

        applied_event = _transition_event(
            event_type="packet_applied",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_apply_001",
        )
        applied = append_event(
            events_path,
            applied_event,
            existing_events=[first],
        )

        retry = _packet_post_event(idempotency_key="key_lifecycle_002")
        with pytest.raises(
            ValueError,
            match="Duplicate review-channel idempotency_key",
        ):
            append_event(events_path, retry, existing_events=[first, applied])


def test_retry_after_expired_is_permitted() -> None:
    """A packet that timed out (expired) must leave the retry slot open."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        original = _packet_post_event(idempotency_key="key_lifecycle_003")
        first = append_event(events_path, original, existing_events=[])

        expired_event = _transition_event(
            event_type="packet_expired",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_expire_001",
        )
        expired = append_event(
            events_path,
            expired_event,
            existing_events=[first],
        )

        retry = _packet_post_event(idempotency_key="key_lifecycle_003")
        second = append_event(
            events_path,
            retry,
            existing_events=[first, expired],
        )

        assert second["packet_id"] != first["packet_id"]


def test_retry_while_pending_remains_refused() -> None:
    """No transition yet: the in-flight packet still owns the retry slot."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        original = _packet_post_event(idempotency_key="key_lifecycle_004")
        first = append_event(events_path, original, existing_events=[])

        retry = _packet_post_event(idempotency_key="key_lifecycle_004")
        with pytest.raises(
            ValueError,
            match="Duplicate review-channel idempotency_key",
        ):
            append_event(events_path, retry, existing_events=[first])


def test_retry_after_action_request_execution_failed_is_permitted() -> None:
    """action_request_execution_failed is terminal non-success → slot opens."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        original = _packet_post_event(idempotency_key="key_lifecycle_006")
        first = append_event(events_path, original, existing_events=[])

        acked_event = _transition_event(
            event_type="packet_acked",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_ack_006",
        )
        acked = append_event(
            events_path,
            acked_event,
            existing_events=[first],
        )
        failed_event = _transition_event(
            event_type="action_request_execution_failed",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_failed_006",
        )
        failed = append_event(
            events_path,
            failed_event,
            existing_events=[first, acked],
        )

        retry = _packet_post_event(idempotency_key="key_lifecycle_006")
        second = append_event(
            events_path,
            retry,
            existing_events=[first, acked, failed],
        )

        assert second["packet_id"] != first["packet_id"]
        assert str(second["event_type"]) == "packet_posted"


def test_retry_while_apply_pending_after_execution_remains_refused() -> None:
    """apply_pending_after_execution is active/in-flight → slot still consumed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        original = _packet_post_event(idempotency_key="key_lifecycle_007")
        first = append_event(events_path, original, existing_events=[])

        acked_event = _transition_event(
            event_type="packet_acked",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_ack_007",
        )
        acked = append_event(
            events_path,
            acked_event,
            existing_events=[first],
        )
        apply_pending_event = _transition_event(
            event_type="action_request_apply_pending_after_execution",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_pending_007",
        )
        apply_pending = append_event(
            events_path,
            apply_pending_event,
            existing_events=[first, acked],
        )

        retry = _packet_post_event(idempotency_key="key_lifecycle_007")
        with pytest.raises(
            ValueError,
            match="Duplicate review-channel idempotency_key",
        ):
            append_event(
                events_path,
                retry,
                existing_events=[first, acked, apply_pending],
            )


# NOTE: a prior test_non_packet_idempotency_duplicate_is_strict_alongside_dismissed_packet
# was retired here. With symmetric non-packet strictness from rev_pkt_2255, the
# scenario it described (a non-packet event sneaking in alongside a dismissed
# packet) is unreachable: the non-packet event append itself now rejects when
# it shares an idempotency_key with any prior matching packet, regardless of
# the packet's lifecycle. The newer tests
# test_non_packet_event_strict_after_dismissed_packet and
# test_non_packet_event_strict_after_failed_action_request cover the same
# contract directly at the rejected append.


def test_non_packet_event_strict_after_dismissed_packet() -> None:
    """Per rev_pkt_2255: non-packet events stay strict even after packet dismissal.

    A current non-packet event must reject any duplicate idempotency_key
    regardless of the prior packet's lifecycle. Packet retry-slot semantics
    only apply when both sides are packet_posted.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        original = _packet_post_event(idempotency_key="key_strict_001")
        first = append_event(events_path, original, existing_events=[])

        dismissed_event = _transition_event(
            event_type="packet_dismissed",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_strict_001",
        )
        dismissed = append_event(
            events_path,
            dismissed_event,
            existing_events=[first],
        )

        # _finalize_packet_posted_identity overwrites the packet's
        # idempotency_key with the canonical SHA-256 of its semantic fields,
        # so the collision key must come from the post-write event.
        canonical_key = str(first.get("idempotency_key") or "")
        assert canonical_key, "packet_posted must carry a canonical key"

        non_packet_event = {
            "event_type": "session_liveness_tick",
            "event_id": "rev_evt_liveness_strict_001",
            "idempotency_key": canonical_key,
        }
        with pytest.raises(
            ValueError,
            match="Duplicate review-channel idempotency_key",
        ):
            append_event(
                events_path,
                non_packet_event,
                existing_events=[first, dismissed],
            )


def test_non_packet_event_strict_after_failed_action_request() -> None:
    """Symmetric strictness across all terminal-non-success packet states."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        original = _packet_post_event(idempotency_key="key_strict_002")
        first = append_event(events_path, original, existing_events=[])

        failed_event = _transition_event(
            event_type="action_request_execution_failed",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_strict_failed_002",
        )
        failed = append_event(
            events_path,
            failed_event,
            existing_events=[first],
        )

        canonical_key = str(first.get("idempotency_key") or "")
        non_packet_event = {
            "event_type": "session_liveness_tick",
            "event_id": "rev_evt_liveness_strict_002",
            "idempotency_key": canonical_key,
        }
        with pytest.raises(
            ValueError,
            match="Duplicate review-channel idempotency_key",
        ):
            append_event(
                events_path,
                non_packet_event,
                existing_events=[first, failed],
            )


def test_packet_retry_after_dismiss_still_permitted_after_strictness_fix() -> None:
    """Regression: packet_posted retries remain lifecycle-aware after the fix."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        original = _packet_post_event(idempotency_key="key_strict_003")
        first = append_event(events_path, original, existing_events=[])

        dismissed_event = _transition_event(
            event_type="packet_dismissed",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_strict_dismiss_003",
        )
        dismissed = append_event(
            events_path,
            dismissed_event,
            existing_events=[first],
        )

        # packet_posted retry MUST still succeed after dismiss — the fix only
        # tightens NON-packet strictness, not packet-retry semantics.
        retry = _packet_post_event(idempotency_key="key_strict_003")
        second = append_event(
            events_path,
            retry,
            existing_events=[first, dismissed],
        )
        assert second["packet_id"] != first["packet_id"]


def test_retry_while_acked_remains_refused() -> None:
    """An acked but not-yet-terminal packet still owns the retry slot."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        original = _packet_post_event(idempotency_key="key_lifecycle_005")
        first = append_event(events_path, original, existing_events=[])

        acked_event = _transition_event(
            event_type="packet_acked",
            packet_id=str(first["packet_id"]),
            event_id="rev_evt_ack_001",
        )
        acked = append_event(
            events_path,
            acked_event,
            existing_events=[first],
        )

        retry = _packet_post_event(idempotency_key="key_lifecycle_005")
        with pytest.raises(
            ValueError,
            match="Duplicate review-channel idempotency_key",
        ):
            append_event(events_path, retry, existing_events=[first, acked])
