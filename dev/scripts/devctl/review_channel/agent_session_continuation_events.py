"""Event-backed AgentResumeReceipt helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from ..runtime.agent_session_continuation_models import AgentResumeReceiptState
from ..runtime.agent_session_continuation_parse import (
    agent_resume_receipt_from_mapping,
)
from ..time_utils import utc_timestamp


AGENT_RESUME_RECEIPT_EVENT_TYPES = frozenset({"agent_resume_receipt"})


def append_agent_resume_receipt_event(
    *,
    events_path: Path,
    receipt: AgentResumeReceiptState,
    existing_events: Sequence[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Append one typed rehydration proof event to the review-channel log."""
    from .event_store import append_event, load_events

    events = (
        list(existing_events)
        if existing_events is not None
        else load_events(events_path)
    )
    event = receipt.to_dict()
    event["event_type"] = "agent_resume_receipt"
    event["timestamp_utc"] = receipt.observed_at_utc or utc_timestamp()
    event["source"] = receipt.source or "session-resume"
    event["metadata"] = {
        "source_contract": "AgentSessionContinuation",
        "continuation_id": receipt.continuation_id,
        "continuation_hash": receipt.continuation_hash,
        "bootstrap_hash": receipt.bootstrap_hash,
    }
    return append_event(events_path, event, existing_events=events)


def load_agent_resume_receipts(
    *,
    events_path: Path,
) -> tuple[AgentResumeReceiptState, ...]:
    from .event_store import load_events

    return agent_resume_receipts_from_events(load_events(events_path))


def agent_resume_receipts_from_events(
    events: Iterable[Mapping[str, object]],
) -> tuple[AgentResumeReceiptState, ...]:
    rows: list[AgentResumeReceiptState] = []
    for event in events:
        if str(event.get("event_type") or "").strip() not in (
            AGENT_RESUME_RECEIPT_EVENT_TYPES
        ):
            continue
        receipt = agent_resume_receipt_from_mapping(event)
        if receipt is not None:
            rows.append(receipt)
    return tuple(rows)


__all__ = [
    "AGENT_RESUME_RECEIPT_EVENT_TYPES",
    "agent_resume_receipts_from_events",
    "append_agent_resume_receipt_event",
    "load_agent_resume_receipts",
]
