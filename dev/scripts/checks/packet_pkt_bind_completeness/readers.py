"""JSONL readers for packet PKT-BIND completeness."""

from __future__ import annotations

import json
from pathlib import Path

from .constants import (
    PACKET_POSTED_EVENT,
    TASK_PRODUCED_KIND,
    TASK_STARTED_BINDING_MUTATION_OP,
    TASK_STARTED_KIND,
)
from .models import TaskStart
from .time_support import parse_timestamp, text


def read_packet_events(
    path: Path,
) -> tuple[list[TaskStart], list[dict[str, object]], list[str]]:
    task_starts: list[TaskStart] = []
    task_produced: list[dict[str, object]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [], [f"event_log_read_failed:{exc.__class__.__name__}:{path}"]
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid_event_jsonl:{line_number}:{exc.msg}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"non_object_event:{line_number}")
            continue
        if text(payload.get("event_type")) != PACKET_POSTED_EVENT:
            continue
        if text(payload.get("from_agent")) != "codex":
            continue
        kind = text(payload.get("kind"))
        if kind == TASK_STARTED_KIND:
            task_start = _task_start_from_event(line_number, payload)
            if task_start is None:
                errors.append(f"invalid_task_started_event:{line_number}")
            else:
                task_starts.append(task_start)
        elif kind == TASK_PRODUCED_KIND:
            task_produced.append(payload)
    return task_starts, task_produced, errors


def read_bound_packet_ids(path: Path) -> tuple[set[str], list[str]]:
    bound: set[str] = set()
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return set(), [f"plan_index_read_failed:{exc.__class__.__name__}:{path}"]
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid_plan_index_jsonl:{line_number}:{exc.msg}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"non_object_plan_row:{line_number}")
            continue
        packet_id = _binding_packet_id(payload)
        if packet_id:
            bound.add(packet_id)
    return bound, errors


def _task_start_from_event(
    line_number: int,
    payload: dict[str, object],
) -> TaskStart | None:
    packet_id = text(payload.get("packet_id"))
    timestamp = parse_timestamp(text(payload.get("timestamp_utc")))
    if not packet_id or timestamp is None:
        return None
    return TaskStart(
        line_number=line_number,
        packet_id=packet_id,
        timestamp_utc=timestamp,
        summary=text(payload.get("summary")),
        correlation_id=text(payload.get("correlation_id")),
        target_ref=text(payload.get("target_ref")),
    )


def _binding_packet_id(row: dict[str, object]) -> str:
    row_id = text(row.get("row_id"))
    mutation_op = text(row.get("mutation_op"))
    refs = (
        *_refs(row.get("sourced_from_packets")),
        *_refs(row.get("anchor_refs")),
        *_refs(row.get("work_evidence_ids")),
    )
    packet_ids = tuple(_packet_id_from_ref(ref) for ref in refs)
    packet_ids = tuple(packet_id for packet_id in packet_ids if packet_id)
    if row_id.startswith("PKT-BIND-"):
        expected_packet = _packet_id_from_binding_row_id(row_id)
        if expected_packet:
            return expected_packet
    if mutation_op == TASK_STARTED_BINDING_MUTATION_OP and packet_ids:
        return packet_ids[0]
    return ""


def _packet_id_from_binding_row_id(row_id: str) -> str:
    if not row_id.startswith("PKT-BIND-REV-PKT-"):
        return ""
    suffix = row_id.removeprefix("PKT-BIND-REV-PKT-").lower()
    return f"rev_pkt_{suffix}" if suffix else ""


def _packet_id_from_ref(ref: str) -> str:
    if ref.startswith("packet:"):
        ref = ref.removeprefix("packet:")
    if ref.startswith("rev_pkt_"):
        return ref
    return ""


def _refs(value: object) -> tuple[str, ...]:
    if isinstance(value, list | tuple):
        return tuple(text(item) for item in value if text(item))
    return ()
