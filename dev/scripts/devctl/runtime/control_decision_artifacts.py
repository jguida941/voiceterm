"""Load live controller decisions from typed runtime artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .value_coercion import coerce_string

DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES = (
    Path("dev/reports/review_channel/state/latest.json"),
)


def load_control_decision_payload(
    args: Any,
    *,
    repo_root: Path,
    candidate_paths: Sequence[Path] = DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES,
) -> dict[str, object]:
    """Load a controller decision from inline, explicit, or default artifacts."""

    inline_payload = getattr(args, "control_decision_payload", None)
    if isinstance(inline_payload, dict):
        return inline_payload
    path_value = coerce_string(getattr(args, "control_decision_input", "")).strip()
    actor = coerce_string(getattr(args, "actor", ""))
    role = coerce_string(getattr(args, "role", ""))
    session_id = coerce_string(getattr(args, "session_id", ""))
    if path_value:
        path = _resolve_repo_path(path_value, repo_root=repo_root)
        return control_decision_payload_from_path(
            path,
            actor=actor,
            role=role,
            session_id=session_id,
        )
    payload = load_latest_agent_loop_decision(
        repo_root=repo_root,
        actor=actor,
        role=role,
        session_id=session_id,
        candidate_paths=candidate_paths,
    )
    if payload:
        return payload
    return {}


def load_latest_agent_loop_decision(
    *,
    repo_root: Path,
    actor: str = "",
    role: str = "",
    session_id: str = "",
    candidate_paths: Sequence[Path] = DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES,
) -> dict[str, object]:
    """Resolve the canonical latest AgentLoopDecision artifact for a scoped actor."""

    for candidate in candidate_paths:
        path = repo_root / candidate
        if not path.exists():
            continue
        payload = control_decision_payload_from_path(
            path,
            actor=actor,
            role=role,
            session_id=session_id,
        )
        if payload:
            return payload
    return {}


def control_decision_payload_from_path(
    path: Path,
    *,
    actor: str = "",
    role: str = "",
    session_id: str = "",
) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return control_decision_payload_from_mapping(
            payload,
            actor=actor,
            role=role,
            session_id=session_id,
        )
    return {}


def control_decision_payload_from_mapping(
    payload: Mapping[str, object],
    *,
    actor: str = "",
    role: str = "",
    session_id: str = "",
) -> dict[str, object]:
    if isinstance(payload.get("agent_loop_decision"), dict):
        return _validated_decision(
            _merge_packet_attention(dict(payload["agent_loop_decision"]), payload),  # type: ignore[index]
            source_payload=payload,
        )
    if isinstance(payload.get("control_decision"), dict):
        return _validated_decision(
            _merge_packet_attention(dict(payload["control_decision"]), payload),  # type: ignore[index]
            source_payload=payload,
        )
    if coerce_string(payload.get("contract_id")) == "AgentLoopDecision":
        return _validated_decision(dict(payload), source_payload=payload)
    rows = payload.get("agent_loop_decisions")
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
        decision = _select_agent_loop_decision(
            tuple(item for item in rows if isinstance(item, Mapping)),
            actor=actor,
            role=role,
            session_id=session_id,
        )
        return _validated_decision(
            _merge_packet_attention(decision, payload),
            source_payload=payload,
        )
    return {}


def _select_agent_loop_decision(
    rows: Sequence[Mapping[str, object]],
    *,
    actor: str,
    role: str,
    session_id: str,
) -> dict[str, object]:
    candidates = tuple(rows)
    if actor:
        candidates = tuple(row for row in candidates if _matches(row, "actor_id", actor))
    if role:
        candidates = tuple(
            row for row in candidates if _matches(row, "actor_role", role)
        )
    if session_id:
        candidates = tuple(
            row for row in candidates if _matches(row, "session_id", session_id)
        )
    if len(candidates) == 1:
        return dict(candidates[0])
    return {}


def _matches(row: Mapping[str, object], key: str, expected: str) -> bool:
    return coerce_string(row.get(key)).strip().lower() == expected.strip().lower()


def _validated_decision(
    decision: Mapping[str, object],
    *,
    source_payload: Mapping[str, object],
) -> dict[str, object]:
    if not decision:
        return {}
    if not _decision_has_source(decision):
        return {}
    latest_event_id = _source_latest_event_id(source_payload)
    if latest_event_id and not _decision_matches_latest_event(decision, latest_event_id):
        return {}
    return dict(decision)


def _decision_has_source(decision: Mapping[str, object]) -> bool:
    return bool(
        coerce_string(decision.get("source_latest_event_id")).strip()
        or coerce_string(decision.get("source_snapshot_id")).strip()
    )


def _decision_matches_latest_event(
    decision: Mapping[str, object],
    latest_event_id: str,
) -> bool:
    decision_event_id = coerce_string(decision.get("source_latest_event_id")).strip()
    if decision_event_id:
        return decision_event_id == latest_event_id
    snapshot_id = coerce_string(decision.get("source_snapshot_id")).strip()
    return snapshot_id.endswith(latest_event_id)


def _source_latest_event_id(payload: Mapping[str, object]) -> str:
    for path in (
        ("agent_runtime_clock", "source_latest_event_id"),
        ("typed_snapshot_freshness", "source_latest_event_id"),
        ("agent_sync", "source_latest_event_id"),
        ("reviewer_runtime", "agent_runtime_clock", "source_latest_event_id"),
        ("reviewer_runtime", "source_latest_event_id"),
        ("source_latest_event_id",),
    ):
        value = _nested_string(payload, path)
        if value:
            return value
    return ""


def _merge_packet_attention(
    decision: Mapping[str, object],
    source_payload: Mapping[str, object],
) -> dict[str, object]:
    result = dict(decision)
    attention = _packet_attention(source_payload)
    if not attention:
        return result
    merge_map = {
        "body_open_required": "body_open_required",
        "body_open_packet_id": "body_open_packet_id",
        "attention_packet_id": "latest_attention_packet_id",
        "active_packet_id": "active_packet_id",
        "pending_packet_count": "pending_packet_count",
        "unopened_body_packet_ids": "unopened_body_packet_ids",
        "pivot_required": "pivot_required",
        "semantic_ingestion_required": "semantic_ingestion_required",
        "semantic_ingestion_packet_id": "semantic_ingestion_packet_id",
        "semantic_ingestion_command": "semantic_ingestion_command",
        "semantic_ingestion_reason": "semantic_ingestion_reason",
    }
    for target_key, source_key in merge_map.items():
        if source_key not in attention:
            continue
        result[target_key] = attention[source_key]
    if "attention_packet_id" not in result and "attention_packet_id" in attention:
        result["attention_packet_id"] = attention["attention_packet_id"]
    return result


def _packet_attention(payload: Mapping[str, object]) -> Mapping[str, object]:
    direct = payload.get("packet_attention")
    if isinstance(direct, Mapping):
        return direct
    reviewer_runtime = payload.get("reviewer_runtime")
    if isinstance(reviewer_runtime, Mapping):
        nested = reviewer_runtime.get("packet_attention")
        if isinstance(nested, Mapping):
            return nested
    return {}


def _nested_string(payload: Mapping[str, object], path: Sequence[str]) -> str:
    current: object = payload
    for key in path:
        if not isinstance(current, Mapping):
            return ""
        current = current.get(key)
    return coerce_string(current).strip()


def _resolve_repo_path(value: str, *, repo_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


__all__ = [
    "DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES",
    "control_decision_payload_from_mapping",
    "control_decision_payload_from_path",
    "load_latest_agent_loop_decision",
    "load_control_decision_payload",
]
