"""Typed reviewer-authority events: reviewer_heartbeat and reviewer_checkpoint.

Per rev_pkt_2546 (Plan 4.1 Scope 1) and rev_pkt_2552 C-2 review: the reviewer
heartbeat / reviewer checkpoint write paths must be first-class entries in the
event log so the event-backed reducer can populate typed
`current_session.current_instruction`, `current_instruction_revision`,
`open_findings`, reviewer freshness, and runtime-clock cursors WITHOUT parsing
bridge.md as authority. Bridge.md is the projection; the event log is the
source.

Two event types are defined:
- ``review_channel.reviewer_checkpoint`` -- emitted whenever the reviewer
  rotates the current instruction or the open findings via the governed
  ``reviewer-checkpoint`` action. Carries the new instruction text,
  revision, open-findings text, reviewer mode, and worktree hash.
- ``review_channel.reviewer_heartbeat`` -- emitted by the reviewer
  ensure/heartbeat path so freshness and last-poll cursors flow through
  typed events even when no checkpoint is happening.

Both event types deliberately do NOT carry a ``packet_id`` (they are not
packet lifecycle events). The event reducer must skip them out of the
"no packet_id is an error" branch so they can populate non-packet typed
state instead.
"""

from __future__ import annotations

from collections.abc import Mapping


REVIEWER_CHECKPOINT_EVENT_TYPE = "review_channel.reviewer_checkpoint"
REVIEWER_HEARTBEAT_EVENT_TYPE = "review_channel.reviewer_heartbeat"

REVIEWER_AUTHORITY_EVENT_TYPES = frozenset(
    {
        REVIEWER_CHECKPOINT_EVENT_TYPE,
        REVIEWER_HEARTBEAT_EVENT_TYPE,
    }
)


# Per rev_pkt_2558 / rev_pkt_2560: a reviewer-authority event must carry the
# canonical envelope used by packet/daemon writers so the reducer can trust
# its provenance. Events missing any required envelope field are dropped on
# read so a malformed/test row cannot poison typed current_session.
_REQUIRED_ENVELOPE_FIELDS = (
    "event_id",
    "event_type",
    "schema_version",
    "source",
    "session_id",
    "plan_id",
    "project_id",
    "timestamp_utc",
    "idempotency_key",
    "nonce",
)


def _has_canonical_envelope(event: Mapping[str, object]) -> bool:
    for field in _REQUIRED_ENVELOPE_FIELDS:
        value = event.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            return False
    if str(event.get("source") or "").strip() != "review_channel":
        return False
    return True


def latest_reviewer_checkpoint_payload(
    events: list[dict[str, object]] | tuple[dict[str, object], ...],
) -> Mapping[str, object]:
    """Return the payload of the most recent reviewer_checkpoint event.

    The payload mapping carries:
    - ``current_instruction``: the rotated instruction text (str)
    - ``current_instruction_revision``: the new revision id (str)
    - ``open_findings``: open-findings markdown body (str)
    - ``reviewer_mode``: declared reviewer mode at checkpoint time (str)
    - ``worktree_hash``: observed non-audit worktree hash (str)
    - ``reviewer_actor``: actor id who wrote the checkpoint (str)
    - ``reason``: reviewer-checkpoint reason (str)
    - ``event_id``: the event id that carried this checkpoint
    - ``timestamp``: utc timestamp of the event

    Returns ``{}`` when no reviewer_checkpoint event has been observed.
    """
    latest: dict[str, object] = {}
    for event in events:
        if not isinstance(event, Mapping):
            continue
        event_type = str(event.get("event_type") or "").strip()
        if event_type != REVIEWER_CHECKPOINT_EVENT_TYPE:
            continue
        if not _has_canonical_envelope(event):
            # Per rev_pkt_2558: malformed reviewer-authority rows must be
            # quarantined silently rather than poisoning typed current_session.
            continue
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            payload = {}
        latest = {
            "current_instruction": str(payload.get("current_instruction") or ""),
            "current_instruction_revision": str(
                payload.get("current_instruction_revision") or ""
            ),
            "open_findings": str(payload.get("open_findings") or ""),
            "reviewer_mode": str(payload.get("reviewer_mode") or ""),
            "worktree_hash": str(payload.get("worktree_hash") or ""),
            "reviewer_actor": str(payload.get("reviewer_actor") or ""),
            "reason": str(payload.get("reason") or ""),
            "event_id": str(event.get("event_id") or ""),
            "timestamp_utc": str(event.get("timestamp_utc") or ""),
        }
    return latest


def latest_reviewer_heartbeat_payload(
    events: list[dict[str, object]] | tuple[dict[str, object], ...],
) -> Mapping[str, object]:
    """Return the payload of the most recent reviewer_heartbeat event."""
    latest: dict[str, object] = {}
    for event in events:
        if not isinstance(event, Mapping):
            continue
        event_type = str(event.get("event_type") or "").strip()
        if event_type != REVIEWER_HEARTBEAT_EVENT_TYPE:
            continue
        if not _has_canonical_envelope(event):
            continue
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            payload = {}
        latest = {
            "reviewer_mode": str(payload.get("reviewer_mode") or ""),
            "reviewer_actor": str(payload.get("reviewer_actor") or ""),
            "reason": str(payload.get("reason") or ""),
            "event_id": str(event.get("event_id") or ""),
            "timestamp_utc": str(event.get("timestamp_utc") or ""),
        }
    return latest
