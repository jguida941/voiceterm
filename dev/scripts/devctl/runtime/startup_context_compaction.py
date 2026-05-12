"""Startup-context compact projection helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from .runtime_truth_snapshot import RuntimeTruthSnapshot
from .session_posture import SessionPosture


class ReviewerGateLike(Protocol):
    """Startup reviewer gate fields needed for compact projection."""

    operator_interaction_mode: str


def startup_runtime_truth_dict(
    runtime_truth: RuntimeTruthSnapshot,
) -> dict[str, object]:
    payload = runtime_truth.to_dict()
    return {key: payload.get(key) for key in _RUNTIME_TRUTH_FIELDS}


def startup_interaction_mode(
    *,
    runtime_truth: RuntimeTruthSnapshot | None,
    session_posture: SessionPosture | None,
    reviewer_gate: ReviewerGateLike,
) -> str:
    for value in (
        runtime_truth.interaction_mode if runtime_truth is not None else "",
        session_posture.interaction_mode if session_posture is not None else "",
        reviewer_gate.operator_interaction_mode,
    ):
        text = str(value or "").strip()
        if text and text != "unresolved":
            return text
    return "unresolved"


def compact_product_thesis(value: str, limit: int = 300) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def compact_connectivity_registry(
    value: dict[str, object],
    *,
    contract_limit: int = 8,
) -> dict[str, object]:
    payload = dict(value)
    contract_ids = [
        str(item)
        for item in (payload.get("connected_contract_ids") or ())
        if str(item).strip()
    ]
    if len(contract_ids) <= contract_limit:
        return payload
    payload["connected_contract_ids"] = contract_ids[:contract_limit]
    payload["connected_contract_ids_truncated"] = len(contract_ids) - contract_limit
    return payload


def compact_packet_continuity_index(
    value: dict[str, object],
    *,
    row_limit: int = 2,
) -> dict[str, object]:
    payload = dict(value)
    rows = [dict(row) for row in (payload.get("rows") or ()) if isinstance(row, dict)]
    if len(rows) <= row_limit:
        return payload
    payload["rows"] = rows[:row_limit]
    payload["rows_truncated"] = len(rows) - row_limit
    return payload


def compact_packet_carry_forward_debt(
    rows: tuple[dict[str, object], ...],
    *,
    row_limit: int = 2,
) -> list[dict[str, object]]:
    bounded = [dict(row) for row in rows[:row_limit]]
    if len(rows) > row_limit:
        bounded.append(
            {
                "contract_id": "PacketCarryForwardDebtSummary",
                "truncated_count": len(rows) - row_limit,
            }
        )
    return bounded


_RUNTIME_TRUTH_FIELDS = (
    "contract_id",
    "generated_at_utc",
    "interaction_mode",
    "reviewer_mode",
    "effective_reviewer_mode",
    "packet_attention_required",
    "pending_packet_count",
    "active_actor_count",
    "remote_control_active",
    "remote_control_method",
    "remote_control_session_id",
    "connectivity_contract_count",
    "connectivity_warning_count",
    "routing_decision",
)


__all__ = [
    "compact_connectivity_registry",
    "compact_packet_carry_forward_debt",
    "compact_packet_continuity_index",
    "compact_product_thesis",
    "startup_interaction_mode",
    "startup_runtime_truth_dict",
]
