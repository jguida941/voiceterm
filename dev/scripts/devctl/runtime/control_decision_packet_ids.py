"""Packet id extraction helpers for control-decision packet attention."""

from __future__ import annotations

from collections.abc import Mapping

from .value_coercion import coerce_string


def decision_packet_id(
    decision: Mapping[str, object],
    *,
    next_command: str,
) -> str:
    return (
        coerce_string(decision.get("body_open_packet_id")).strip()
        or coerce_string(decision.get("semantic_ingestion_packet_id")).strip()
        or coerce_string(decision.get("absorption_packet_id")).strip()
        or packet_id_from_command(next_command)
        or coerce_string(decision.get("attention_packet_id")).strip()
        or coerce_string(decision.get("active_packet_id")).strip()
        or packet_id_from_target_ref(decision.get("target_ref"))
    )


def packet_id_from_command(command: str) -> str:
    marker = "--packet-id "
    if marker not in command:
        return ""
    return command.split(marker, 1)[1].split()[0].strip("'\"")


def packet_id_from_target_ref(value: object) -> str:
    target_ref = coerce_string(value).strip()
    if target_ref.startswith("rev_pkt_"):
        return target_ref
    if target_ref.startswith("packet:"):
        return target_ref.split(":", 1)[1].strip()
    return ""


def normalized_token(value: object) -> str:
    return coerce_string(value).strip().lower().replace("-", "_").replace(" ", "_")


def coerce_flag(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = coerce_string(value).strip().lower()
    return text in {"1", "true", "yes", "on"}
