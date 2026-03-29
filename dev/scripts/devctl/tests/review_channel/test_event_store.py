"""Focused tests for review-channel event store integrity."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from dev.scripts.devctl.review_channel.event_store import (
    append_event,
    next_event_id,
    next_packet_id,
)


def test_next_event_id_from_empty_list() -> None:
    assert next_event_id([]) == "rev_evt_0001"


def test_next_event_id_sequential() -> None:
    events = [
        {"event_id": "rev_evt_0001"},
        {"event_id": "rev_evt_0002"},
        {"event_id": "rev_evt_0003"},
    ]
    assert next_event_id(events) == "rev_evt_0004"


def test_next_event_id_survives_gaps() -> None:
    """If events are missing (e.g., corruption), use the max index, not count."""
    events = [
        {"event_id": "rev_evt_0001"},
        {"event_id": "rev_evt_0005"},  # gap: 2,3,4 missing
    ]
    # Should be 6, not 3 (which len-based would produce)
    assert next_event_id(events) == "rev_evt_0006"


def test_next_event_id_concurrent_stale_snapshot() -> None:
    """Two writers with overlapping stale snapshots must not collide.

    Simulate: Writer A has events [1,2,3], Writer B has events [1,2,3,4].
    Writer A would get 0004, Writer B would get 0005.
    With the old len-based approach, Writer A would also get 0004 if
    it only counted its own snapshot. The max-based approach prevents this
    because Writer A reads the highest existing ID from its snapshot.
    """
    snapshot_a = [
        {"event_id": "rev_evt_0001"},
        {"event_id": "rev_evt_0002"},
        {"event_id": "rev_evt_0003"},
    ]
    snapshot_b = [
        {"event_id": "rev_evt_0001"},
        {"event_id": "rev_evt_0002"},
        {"event_id": "rev_evt_0003"},
        {"event_id": "rev_evt_0004"},
    ]
    id_a = next_event_id(snapshot_a)
    id_b = next_event_id(snapshot_b)
    assert id_a == "rev_evt_0004"
    assert id_b == "rev_evt_0005"
    assert id_a != id_b  # no collision when snapshots diverge


def test_next_event_id_ignores_malformed_ids() -> None:
    events = [
        {"event_id": "rev_evt_0001"},
        {"event_id": "bad_id"},
        {"event_id": "rev_evt_0003"},
        {},  # missing event_id
    ]
    assert next_event_id(events) == "rev_evt_0004"


def test_append_event_single_write_atomicity() -> None:
    """Verify append writes JSON+newline in a single call."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        event = {
            "event_id": "rev_evt_0001",
            "idempotency_key": "key_001",
            "event_type": "packet_posted",
        }
        append_event(events_path, event, existing_events=[])

        content = events_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["event_id"] == "rev_evt_0001"


def test_append_event_allocates_id_from_disk_not_snapshot() -> None:
    """Two writers with stale snapshots must get unique event_ids.

    Simulates: Writer A has snapshot [evt_1,evt_2], Writer B has same snapshot.
    Both append. Writer A should get evt_3 (from its append). Writer B should
    get evt_4 (re-reading the disk after A's write).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"

        # Seed the log with 2 events
        seed_events = [
            {"event_id": "rev_evt_0001", "idempotency_key": "seed_1"},
            {"event_id": "rev_evt_0002", "idempotency_key": "seed_2"},
        ]
        for e in seed_events:
            events_path.parent.mkdir(parents=True, exist_ok=True)
            with events_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(e, sort_keys=True) + "\n")

        # Both writers have the same stale snapshot
        stale_snapshot = list(seed_events)

        # Writer A appends
        event_a = {"idempotency_key": "key_a", "event_type": "test"}
        append_event(events_path, event_a, existing_events=stale_snapshot)

        # Writer B appends with the SAME stale snapshot
        event_b = {"idempotency_key": "key_b", "event_type": "test"}
        append_event(events_path, event_b, existing_events=stale_snapshot)

        # Read back and verify unique event_ids
        lines = events_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 4
        event_ids = [json.loads(line)["event_id"] for line in lines]
        assert len(set(event_ids)) == 4, f"Duplicate event_ids: {event_ids}"
        assert event_ids[2] == "rev_evt_0003"
        assert event_ids[3] == "rev_evt_0004"


def test_append_event_returns_written_event_with_correct_id() -> None:
    """Caller must receive the event with the serialized (possibly reallocated) event_id."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"

        # Seed with one event
        seed = {"event_id": "rev_evt_0001", "idempotency_key": "seed_1"}
        with events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(seed, sort_keys=True) + "\n")

        # Caller passes a stale event_id that will be reallocated
        event_in = {"event_id": "rev_evt_9999", "idempotency_key": "key_new", "event_type": "test"}
        written = append_event(events_path, event_in, existing_events=[seed])

        # The returned event should have the serialized event_id, not the stale one
        assert written["event_id"] == "rev_evt_0002"
        assert written["event_id"] != "rev_evt_9999"


def test_append_event_rejects_malformed_trace() -> None:
    """Malformed trace rows must cause append to fail closed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"

        # Write a valid row then a malformed row
        events_path.write_text(
            '{"event_id": "rev_evt_0001", "idempotency_key": "k1"}\n'
            'THIS IS NOT JSON\n',
            encoding="utf-8",
        )

        event = {"idempotency_key": "key_new", "event_type": "test"}
        try:
            append_event(events_path, event, existing_events=[])
            assert False, "Should have raised ValueError on malformed trace"
        except ValueError as exc:
            assert "Malformed event log" in str(exc)


def test_append_event_rejects_duplicate_idempotency_key() -> None:
    """Duplicate idempotency keys must be rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"
        event = {
            "event_id": "rev_evt_0001",
            "idempotency_key": "key_001",
        }
        append_event(events_path, event, existing_events=[])

        try:
            append_event(
                events_path,
                {"event_id": "rev_evt_0002", "idempotency_key": "key_001"},
                existing_events=[event],
            )
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "Duplicate" in str(exc)


def test_caller_sees_written_event_id_not_stale() -> None:
    """Caller must see the serialized event_id, not the precomputed stale one.

    Simulates: caller computes event_id from a stale snapshot, but append_event
    reallocates from the on-disk log. The returned event must have the correct ID.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        events_path = Path(tmpdir) / "trace.ndjson"

        # Seed: 3 events on disk
        for i in range(1, 4):
            with events_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "event_id": f"rev_evt_{i:04d}",
                    "idempotency_key": f"seed_{i}",
                }) + "\n")

        # Caller has stale snapshot with only 2 events → precomputes evt_0003
        stale_snapshot = [
            {"event_id": "rev_evt_0001", "idempotency_key": "seed_1"},
            {"event_id": "rev_evt_0002", "idempotency_key": "seed_2"},
        ]
        caller_event = {
            "event_id": next_event_id(stale_snapshot),  # would be rev_evt_0003
            "idempotency_key": "caller_key",
            "event_type": "test",
        }
        assert caller_event["event_id"] == "rev_evt_0003"  # stale precomputed

        # append_event should reallocate to rev_evt_0004 (disk has 3 events)
        written = append_event(events_path, caller_event, existing_events=stale_snapshot)
        assert written["event_id"] == "rev_evt_0004"  # serialized from disk
        assert written["event_id"] != "rev_evt_0003"  # NOT the stale one
