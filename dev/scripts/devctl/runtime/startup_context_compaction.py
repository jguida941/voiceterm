"""Startup-context compact projection helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from .runtime_truth_snapshot import RuntimeTruthSnapshot
from .session_posture import SessionPosture


class ReviewerGateLike(Protocol):
    """Startup reviewer gate fields needed for compact projection."""

    operator_interaction_mode: str


def compact_bypass_lifecycles(lifecycles: tuple[object, ...]) -> list[dict[str, object]]:
    """Project active bypass authority without embedding the full lifecycle graph."""
    return [_compact_bypass_lifecycle(lifecycle) for lifecycle in lifecycles]


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


def _compact_bypass_lifecycle(lifecycle: object) -> dict[str, object]:
    request = getattr(lifecycle, "request", None)
    evaluation = getattr(lifecycle, "evaluation", None)
    receipt = getattr(lifecycle, "receipt", None)
    expiry = getattr(lifecycle, "expiry", None)
    payload: dict[str, object] = {
        "contract_id": _text(getattr(lifecycle, "contract_id", "BypassLifecycle")),
        "schema_version": getattr(lifecycle, "schema_version", 1),
        "lifecycle_id": _text(getattr(lifecycle, "lifecycle_id", "")),
        "state": _text(getattr(lifecycle, "state", "")),
    }
    if request is not None:
        _put(payload, "scope", getattr(request, "scope", ""))
        _put(payload, "actor", getattr(request, "actor", ""))
        _put(payload, "target_role", getattr(request, "target_role", ""))
        _put(payload, "target_session_id", getattr(request, "target_session_id", ""))
        _put(payload, "target_surface", getattr(request, "target_surface", ""))
    if evaluation is not None:
        _put(payload, "approved_scope", getattr(evaluation, "approved_scope", ""))
    if receipt is not None:
        _put(payload, "receipt_id", getattr(receipt, "receipt_id", ""))
        _put(payload, "granted_at_utc", getattr(receipt, "granted_at_utc", ""))
        _put(payload, "expires_at_utc", getattr(receipt, "expires_at_utc", ""))
        _put(payload, "revoked_at_utc", getattr(receipt, "revoked_at_utc", ""))
    if expiry is not None:
        _put(payload, "expiry_id", getattr(expiry, "expiry_id", ""))
        _put(payload, "expired_at_utc", getattr(expiry, "expired_at_utc", ""))
        _put(payload, "expiry_source", getattr(expiry, "source", ""))
    return payload


def _put(payload: dict[str, object], key: str, value: object) -> None:
    text = _text(value)
    if text:
        payload[key] = text


def _bounded_strings(values: object, *, limit: int = 3) -> list[str]:
    items = [_text(item) for item in (values or ()) if _text(item)]
    bounded = items[:limit]
    if len(items) > limit:
        bounded.append(f"...{len(items) - limit} more")
    return bounded


def _text(value: object) -> str:
    enum_value = getattr(value, "value", None)
    if enum_value is not None:
        return str(enum_value)
    return str(value or "")


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
    "compact_bypass_lifecycles",
    "compact_connectivity_registry",
    "compact_packet_carry_forward_debt",
    "compact_packet_continuity_index",
    "compact_product_thesis",
    "startup_interaction_mode",
    "startup_runtime_truth_dict",
]
