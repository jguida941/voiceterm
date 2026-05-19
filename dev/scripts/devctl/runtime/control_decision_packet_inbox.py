"""Merge packet attention into live control-decision payloads."""

from __future__ import annotations

from collections.abc import Mapping

from .control_decision_packet_agent_sync import agent_sync_packet_attention
from .control_decision_packet_ids import (
    coerce_flag,
    decision_packet_id,
    normalized_token,
)
from .control_decision_packet_inbox_scope import packet_inbox_attention
from .value_coercion import coerce_string


def merge_packet_attention(
    decision: Mapping[str, object],
    source_payload: Mapping[str, object],
    *,
    actor: str = "",
) -> dict[str, object]:
    result = dict(decision)
    attention = packet_attention(source_payload, actor=actor)
    if not attention:
        return derive_packet_attention_from_decision(result)
    merge_map = (
        ("body_open_required", "body_open_required"),
        ("body_open_packet_id", "body_open_packet_id"),
        ("attention_packet_id", "latest_attention_packet_id"),
        ("active_packet_id", "active_packet_id"),
        ("pending_packet_count", "pending_packet_count"),
        ("unopened_body_packet_ids", "unopened_body_packet_ids"),
        ("pivot_required", "pivot_required"),
        ("semantic_ingestion_required", "semantic_ingestion_required"),
        ("semantic_ingestion_packet_id", "semantic_ingestion_packet_id"),
        ("semantic_ingestion_command", "semantic_ingestion_command"),
        ("semantic_ingestion_reason", "semantic_ingestion_reason"),
        ("absorption_required", "absorption_required"),
        ("absorption_packet_id", "absorption_packet_id"),
        ("absorption_command", "absorption_command"),
        ("absorption_reason", "absorption_reason"),
    )
    for target_key, source_key in merge_map:
        if source_key not in attention:
            continue
        result[target_key] = attention[source_key]
    if "attention_packet_id" not in result and "attention_packet_id" in attention:
        result["attention_packet_id"] = attention["attention_packet_id"]
    return derive_packet_attention_from_decision(result)


def derive_packet_attention_from_decision(
    decision: Mapping[str, object],
) -> dict[str, object]:
    result = dict(decision)
    if (
        coerce_flag(result.get("body_open_required"))
        or coerce_flag(result.get("semantic_ingestion_required"))
        or coerce_flag(result.get("absorption_required"))
    ):
        return result
    required_action = normalized_token(result.get("required_action"))
    reason_code = normalized_token(result.get("reason_code") or result.get("reason"))
    gate_failure = result.get("gate_failure")
    gate_reason = (
        normalized_token(gate_failure.get("violation_reason"))
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
        packet_id = decision_packet_id(result, next_command=next_command)
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
        packet_id = decision_packet_id(result, next_command=next_command)
        if packet_id:
            result["semantic_ingestion_required"] = True
            result["semantic_ingestion_packet_id"] = packet_id
            result["semantic_ingestion_command"] = next_command
            result["semantic_ingestion_reason"] = (
                "packet_body_observed_without_semantic_ingestion"
            )
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
    packet_id = decision_packet_id(result, next_command=next_command)
    if not packet_id:
        return result
    result["body_open_required"] = True
    result["body_open_packet_id"] = packet_id
    result.setdefault("attention_packet_id", packet_id)
    result.setdefault("active_packet_id", packet_id)
    if not result.get("unopened_body_packet_ids"):
        result["unopened_body_packet_ids"] = [packet_id]
    return result


def packet_attention(
    payload: Mapping[str, object],
    *,
    actor: str = "",
) -> Mapping[str, object]:
    inbox_attention = packet_inbox_attention(payload, actor=actor)
    if inbox_attention:
        return inbox_attention
    agent_sync_attention = agent_sync_packet_attention(payload, actor=actor)
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
