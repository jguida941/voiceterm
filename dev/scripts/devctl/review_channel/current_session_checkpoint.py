"""Reviewer-checkpoint suppression helpers for current-session state."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from .timestamp_parse import parse_utc_value as _parse_utc

_CHECKPOINT_SUPERSEDING_PACKET_KINDS = {"instruction", "action_request"}
_CHECKPOINT_SUPERSEDING_STATES = {"applied", "archived", "dismissed", "expired"}


def reviewer_checkpoint_instruction_preservation(
    review_state: Mapping[str, object],
) -> tuple[str, str] | None:
    """Return (instruction, revision) from `latest_reviewer_checkpoint` if live."""
    checkpoint = review_state.get("latest_reviewer_checkpoint")
    if not isinstance(checkpoint, Mapping):
        return None
    revision = str(
        checkpoint.get("current_instruction_revision") or ""
    ).strip()
    instruction = str(checkpoint.get("current_instruction") or "").strip()
    if not (revision and instruction):
        return None
    if _reviewer_checkpoint_superseded(review_state, checkpoint):
        return None
    return instruction, revision


def _reviewer_checkpoint_superseded(
    review_state: Mapping[str, object],
    checkpoint: Mapping[str, object],
) -> bool:
    checkpoint_time = _latest_timestamp(checkpoint)
    checkpoint_event_sequence = _event_sequence(checkpoint.get("event_id"))
    if checkpoint_time is None and checkpoint_event_sequence is None:
        return False
    packets = review_state.get("packets")
    if isinstance(packets, list) and any(
        _terminal_instruction_packet_newer_than(packet, checkpoint_time)
        for packet in packets
        if isinstance(packet, Mapping)
    ):
        return True
    return _continuity_row_supersedes_checkpoint(
        review_state.get("packet_continuity_index"),
        checkpoint_event_sequence=checkpoint_event_sequence,
    )


def _terminal_instruction_packet_newer_than(
    packet: Mapping[str, object],
    checkpoint_time: datetime | None,
) -> bool:
    kind = str(packet.get("kind") or "").strip()
    if kind not in _CHECKPOINT_SUPERSEDING_PACKET_KINDS:
        return False
    if not _is_terminal_packet(packet):
        return False
    packet_time = _latest_timestamp(packet)
    return (
        checkpoint_time is not None
        and packet_time is not None
        and packet_time > checkpoint_time
    )


def _is_terminal_packet(packet: Mapping[str, object]) -> bool:
    if str(packet.get("status") or "").strip() in _CHECKPOINT_SUPERSEDING_STATES:
        return True
    if (
        str(packet.get("lifecycle_current_state") or "").strip()
        in _CHECKPOINT_SUPERSEDING_STATES
    ):
        return True
    disposition = packet.get("disposition")
    return isinstance(disposition, Mapping) and str(
        disposition.get("sink") or ""
    ).strip() in _CHECKPOINT_SUPERSEDING_STATES


def _continuity_row_supersedes_checkpoint(
    packet_continuity_index: object,
    *,
    checkpoint_event_sequence: int | None,
) -> bool:
    if checkpoint_event_sequence is None or not isinstance(
        packet_continuity_index, Mapping
    ):
        return False
    rows = packet_continuity_index.get("rows")
    if not isinstance(rows, list):
        return False
    return any(
        _continuity_row_newer_terminal(row, checkpoint_event_sequence)
        for row in rows
        if isinstance(row, Mapping)
    )


def _continuity_row_newer_terminal(
    row: Mapping[str, object],
    checkpoint_event_sequence: int,
) -> bool:
    if not _continuity_row_terminal(row):
        return False
    latest_event_sequence = _event_sequence(row.get("latest_event_id"))
    return (
        latest_event_sequence is not None
        and latest_event_sequence > checkpoint_event_sequence
    )


def _continuity_row_terminal(row: Mapping[str, object]) -> bool:
    return any(
        str(row.get(field) or "").strip() in _CHECKPOINT_SUPERSEDING_STATES
        for field in ("status", "lifecycle_state", "disposition_sink", "sink")
    )


def _event_sequence(value: object) -> int | None:
    text = str(value or "").strip()
    if not text.startswith("rev_evt_"):
        return None
    suffix = text.removeprefix("rev_evt_")
    return int(suffix) if suffix.isdigit() else None


def _latest_timestamp(record: Mapping[str, object]) -> datetime | None:
    stamps = tuple(
        stamp
        for stamp in (
            _parse_utc(record.get(field))
            for field in (
                "applied_at_utc",
                "dismissed_at_utc",
                "archived_at_utc",
                "expired_at_utc",
                "acted_at_utc",
                "updated_at_utc",
                "latest_event_at_utc",
                "event_at_utc",
                "timestamp_utc",
                "timestamp",
                "posted_at_utc",
                "posted_at",
                "created_at_utc",
            )
        )
        if stamp is not None
    )
    return max(stamps) if stamps else None
