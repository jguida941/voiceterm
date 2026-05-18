"""Load live controller decisions from typed runtime artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .packet_absorption import (
    packet_semantically_ingested as _runtime_packet_semantically_ingested,
)
from .packet_absorption_resolution import absorption_resolves_packet_pressure
from .value_coercion import coerce_bool, coerce_string

DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES = (
    Path("dev/reports/review_channel/state/latest.json"),
)
DEFAULT_STARTUP_AUTHORITY_CANDIDATES = (
    Path("dev/reports/startup/latest/receipt.json"),
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
        return _merge_latest_startup_authority(
            payload,
            repo_root=repo_root,
            actor=actor,
            role=role,
        )
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
            _merge_packet_attention(  # type: ignore[index]
                dict(payload["agent_loop_decision"]),
                payload,
                actor=actor,
            ),
            source_payload=payload,
        )
    if isinstance(payload.get("control_decision"), dict):
        return _validated_decision(
            _merge_packet_attention(  # type: ignore[index]
                dict(payload["control_decision"]),
                payload,
                actor=actor,
            ),
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
            _merge_packet_attention(decision, payload, actor=actor),
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
    if not (actor and role and session_id):
        return {}
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
    result = dict(decision)
    source_head_sha = _source_head_sha(source_payload)
    if source_head_sha:
        result.setdefault("source_head_sha", source_head_sha)
    return result


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


def _source_head_sha(payload: Mapping[str, object]) -> str:
    for path in (
        ("source_identity", "head_sha"),
        ("reviewer_runtime", "source_identity", "head_sha"),
        ("authority_snapshot", "source_identity", "head_sha"),
    ):
        value = _nested_string(payload, path)
        if value:
            return value
    return ""


def _merge_packet_attention(
    decision: Mapping[str, object],
    source_payload: Mapping[str, object],
    *,
    actor: str = "",
) -> dict[str, object]:
    result = dict(decision)
    attention = _packet_attention(source_payload, actor=actor)
    if not attention:
        return _derive_packet_attention_from_decision(result)
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
        "absorption_required": "absorption_required",
        "absorption_packet_id": "absorption_packet_id",
        "absorption_command": "absorption_command",
        "absorption_reason": "absorption_reason",
    }
    for target_key, source_key in merge_map.items():
        if source_key not in attention:
            continue
        result[target_key] = attention[source_key]
    if "attention_packet_id" not in result and "attention_packet_id" in attention:
        result["attention_packet_id"] = attention["attention_packet_id"]
    return _derive_packet_attention_from_decision(result)


def _merge_latest_startup_authority(
    decision: Mapping[str, object],
    *,
    repo_root: Path,
    actor: str,
    role: str,
) -> dict[str, object]:
    result = dict(decision)
    for candidate in DEFAULT_STARTUP_AUTHORITY_CANDIDATES:
        path = repo_root / candidate
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        authority = payload.get("authority_snapshot")
        if not isinstance(authority, Mapping):
            continue
        if not _authority_matches_subject(authority, actor=actor, role=role):
            continue
        if not _authority_fresh_for_decision(authority, result):
            continue
        snapshot_id = coerce_string(authority.get("snapshot_id")).strip()
        if not snapshot_id:
            continue
        _merge_string_sequence_field(result, authority, "allowed_actions")
        _merge_string_sequence_field(result, authority, "blocked_actions")
        result.setdefault("startup_authority_snapshot_id", snapshot_id)
        source_head_sha = _nested_string(authority, ("source_identity", "head_sha"))
        if source_head_sha:
            result.setdefault("startup_authority_source_head_sha", source_head_sha)
        return result
    return result


def _authority_fresh_for_decision(
    authority: Mapping[str, object],
    decision: Mapping[str, object],
) -> bool:
    decision_head = coerce_string(decision.get("source_head_sha")).strip()
    if not decision_head:
        return True
    authority_head = _nested_string(authority, ("source_identity", "head_sha"))
    return bool(authority_head) and authority_head == decision_head


def _authority_matches_subject(
    authority: Mapping[str, object],
    *,
    actor: str,
    role: str,
) -> bool:
    authority_actor = coerce_string(authority.get("actor_identity")).strip().lower()
    authority_role = coerce_string(authority.get("actor_role")).strip().lower()
    if actor and authority_actor and authority_actor != actor.strip().lower():
        return False
    if role and authority_role and authority_role != role.strip().lower():
        return False
    return bool(authority_actor or authority_role)


def _merge_string_sequence_field(
    target: dict[str, object],
    source: Mapping[str, object],
    key: str,
) -> None:
    merged: list[str] = []
    for value in (target.get(key), source.get(key)):
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            continue
        for item in value:
            text = coerce_string(item).strip()
            if text and text not in merged:
                merged.append(text)
    if merged:
        target[key] = merged


def _derive_packet_attention_from_decision(
    decision: Mapping[str, object],
) -> dict[str, object]:
    """Normalize packet-attention fields from an AgentLoopDecision fallback.

    Some live AgentLoopDecision rows carry the controlling packet-open authority
    in ``required_action``/``reason_code`` plus the emitted ``next_command`` but
    omit the convenience booleans consumed by the obedience guard.  Derive only
    the narrow packet-open fields from that same typed decision.
    """

    result = dict(decision)
    if (
        coerce_bool(result.get("body_open_required"))
        or coerce_bool(result.get("semantic_ingestion_required"))
        or coerce_bool(result.get("absorption_required"))
    ):
        return result
    required_action = _norm(result.get("required_action"))
    reason_code = _norm(result.get("reason_code") or result.get("reason"))
    gate_failure = result.get("gate_failure")
    gate_reason = (
        _norm(gate_failure.get("violation_reason"))
        if isinstance(gate_failure, Mapping)
        else ""
    )
    next_command = coerce_string(result.get("next_command"))
    if (
        required_action == "absorb_packet"
        or reason_code == "packet_absorption_required"
        or gate_reason == "packet_absorption_required"
        or "review-channel --action absorb" in next_command
    ):
        packet_id = _decision_packet_id(result, next_command=next_command)
        if packet_id:
            result["absorption_required"] = True
            result["absorption_packet_id"] = packet_id
            result["absorption_command"] = next_command
            result.setdefault("attention_packet_id", packet_id)
            result.setdefault("active_packet_id", packet_id)
        return result
    if (
        required_action == "ingest_packet_semantics"
        or reason_code == "packet_semantic_ingestion_required"
        or gate_reason == "packet_semantic_ingestion_required"
        or "review-channel --action ingest" in next_command
    ):
        packet_id = _decision_packet_id(result, next_command=next_command)
        if packet_id:
            result["semantic_ingestion_required"] = True
            result["semantic_ingestion_packet_id"] = packet_id
            result["semantic_ingestion_command"] = next_command
            result["semantic_ingestion_reason"] = "packet_body_observed_without_semantic_ingestion"
            result.setdefault("attention_packet_id", packet_id)
            result.setdefault("active_packet_id", packet_id)
        return result
    if not (
        required_action == "open_packet_body"
        or reason_code == "packet_body_open_required"
        or gate_reason == "packet_body_open_required"
        or (
            "review-channel --action show" in next_command
            and "--packet-id " in next_command
        )
    ):
        return result
    packet_id = _decision_packet_id(result, next_command=next_command)
    if not packet_id:
        return result
    result["body_open_required"] = True
    result["body_open_packet_id"] = packet_id
    result.setdefault("attention_packet_id", packet_id)
    result.setdefault("active_packet_id", packet_id)
    if not result.get("unopened_body_packet_ids"):
        result["unopened_body_packet_ids"] = [packet_id]
    return result


def _decision_packet_id(
    decision: Mapping[str, object],
    *,
    next_command: str,
) -> str:
    return (
        coerce_string(decision.get("body_open_packet_id")).strip()
        or coerce_string(decision.get("semantic_ingestion_packet_id")).strip()
        or coerce_string(decision.get("absorption_packet_id")).strip()
        or _packet_id_from_command(next_command)
        or coerce_string(decision.get("attention_packet_id")).strip()
        or coerce_string(decision.get("active_packet_id")).strip()
        or _packet_id_from_target_ref(decision.get("target_ref"))
    )


def _packet_id_from_command(command: str) -> str:
    marker = "--packet-id "
    if marker not in command:
        return ""
    return command.split(marker, 1)[1].split()[0].strip("'\"")


def _packet_id_from_target_ref(value: object) -> str:
    target_ref = coerce_string(value).strip()
    if target_ref.startswith("rev_pkt_"):
        return target_ref
    if target_ref.startswith("packet:"):
        return target_ref.split(":", 1)[1].strip()
    return ""


def _norm(value: object) -> str:
    return coerce_string(value).strip().lower().replace("-", "_").replace(" ", "_")


def _packet_attention(
    payload: Mapping[str, object],
    *,
    actor: str = "",
) -> Mapping[str, object]:
    agent_sync_attention = _agent_sync_packet_attention(payload, actor=actor)
    if agent_sync_attention:
        return agent_sync_attention
    direct = payload.get("packet_attention")
    if isinstance(direct, Mapping):
        return direct
    reviewer_runtime = payload.get("reviewer_runtime")
    if isinstance(reviewer_runtime, Mapping):
        nested = reviewer_runtime.get("packet_attention")
        if isinstance(nested, Mapping):
            return nested
    return {}


def _agent_sync_packet_attention(
    payload: Mapping[str, object],
    *,
    actor: str = "",
) -> dict[str, object]:
    """Derive a scoped body-open target from AgentSync when it is unambiguous."""

    if not actor:
        return {}
    agent_sync = payload.get("agent_sync")
    if not isinstance(agent_sync, Mapping):
        return {}
    agents = agent_sync.get("agents")
    if not isinstance(agents, Mapping):
        return {}
    actor_state = agents.get(actor)
    if not isinstance(actor_state, Mapping):
        return {}
    pending_raw = actor_state.get("pending_packets_to_me")
    if not isinstance(pending_raw, Sequence) or isinstance(pending_raw, (str, bytes)):
        return {}
    pending_packet_ids = tuple(
        packet_id
        for packet_id in (coerce_string(item).strip() for item in pending_raw)
        if packet_id
    )
    if len(pending_packet_ids) != 1:
        return {}
    packet_id = pending_packet_ids[0]
    packet = _packet_by_id(payload, packet_id)
    base = {
        "latest_attention_packet_id": packet_id,
        "pending_packet_count": 1,
        "pivot_required": True,
    }
    if packet and _packet_has_absorption_receipt(packet):
        return {}
    if packet and _packet_has_any_absorption_receipt(packet):
        return base
    if packet and _packet_semantically_ingested(packet):
        return {
            **base,
            "absorption_required": True,
            "absorption_packet_id": packet_id,
            "absorption_command": (
                "python3 dev/scripts/devctl.py review-channel --action absorb "
                f"--packet-id {packet_id}"
            ),
            "absorption_reason": "packet_semantically_ingested_without_absorption",
        }
    if packet and _packet_body_observed(packet):
        return {
            **base,
            "semantic_ingestion_required": True,
            "semantic_ingestion_packet_id": packet_id,
            "semantic_ingestion_command": (
                "python3 dev/scripts/devctl.py review-channel --action ingest "
                f"--packet-id {packet_id}"
            ),
            "semantic_ingestion_reason": (
                "packet_body_observed_without_semantic_ingestion"
            ),
        }
    return {
        **base,
        "body_open_required": True,
        "body_open_packet_id": packet_id,
        "unopened_body_packet_ids": [packet_id],
    }


def _packet_by_id(
    payload: Mapping[str, object],
    packet_id: str,
) -> Mapping[str, object]:
    packets = payload.get("packets")
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return {}
    for packet in packets:
        if (
            isinstance(packet, Mapping)
            and coerce_string(packet.get("packet_id")).strip() == packet_id
        ):
            return packet
    return {}


def _packet_body_observed(packet: Mapping[str, object]) -> bool:
    return bool(
        coerce_string(packet.get("body_observed_at_utc")).strip()
        or coerce_string(packet.get("body_observed_event_id")).strip()
        or _sequence_has_rows(packet.get("body_observation_events"))
    )


def _packet_semantically_ingested(packet: Mapping[str, object]) -> bool:
    return _runtime_packet_semantically_ingested(packet)


def _packet_has_absorption_receipt(packet: Mapping[str, object]) -> bool:
    receipts = _packet_absorption_receipts(packet)
    return bool(receipts) and absorption_resolves_packet_pressure(
        packet,
        absorption_receipts=tuple(receipts),
    )


def _packet_has_any_absorption_receipt(packet: Mapping[str, object]) -> bool:
    return bool(_packet_absorption_receipts(packet))


def _packet_absorption_receipts(packet: Mapping[str, object]) -> list[Mapping[str, object]]:
    receipts: list[Mapping[str, object]] = []
    for key in ("packet_absorption_receipt", "absorption_receipt"):
        receipt = packet.get(key)
        if _nonempty_receipt(receipt):
            receipts.append(receipt)  # type: ignore[arg-type]
    events = packet.get("absorption_events")
    if isinstance(events, Sequence) and not isinstance(events, (str, bytes)):
        for item in events:
            if not isinstance(item, Mapping):
                continue
            receipt = item.get("packet_absorption_receipt")
            if _nonempty_receipt(receipt):
                receipts.append(receipt)  # type: ignore[arg-type]
            elif _nonempty_receipt(item):
                receipts.append(item)
    return receipts


def _nonempty_receipt(value: object) -> bool:
    return isinstance(value, Mapping) and bool(
        coerce_string(value.get("packet_id")).strip()
        or coerce_string(value.get("receipt_id")).strip()
        or coerce_string(value.get("contract_id")).strip()
    )


def _sequence_has_rows(value: object) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and bool(value)
    )


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
