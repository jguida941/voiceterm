"""Stable value helpers for agent-session continuation contracts."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json

from .agent_session_continuation_models import (
    AUTHORITY_RESULT_ALLOWED,
    AUTHORITY_RESULT_BLOCKED,
    CONTINUATION_MODE_RUNTIME_RESUME,
    CONTINUATION_MODE_TYPED_REHYDRATION,
    RESUME_RESULT_BLOCKED,
    RESUME_RESULT_FAILED,
    RESUME_RESULT_LOADED,
)
from .value_coercion import coerce_string

CONTINUATION_MODES = frozenset(
    {
        CONTINUATION_MODE_TYPED_REHYDRATION,
        CONTINUATION_MODE_RUNTIME_RESUME,
    }
)
RESUME_RESULTS = frozenset(
    {
        "expected",
        RESUME_RESULT_LOADED,
        RESUME_RESULT_BLOCKED,
        RESUME_RESULT_FAILED,
    }
)
AUTHORITY_RESULTS = frozenset({AUTHORITY_RESULT_ALLOWED, AUTHORITY_RESULT_BLOCKED})


def continuation_hash(payload: Mapping[str, object]) -> str:
    stable_payload = _stable_payload(
        payload,
        excluded={
            "schema_version",
            "contract_id",
            "continuation_id",
            "continuation_hash",
            "receipt_id",
            "generated_at_utc",
            "observed_at_utc",
            "source_event_id",
        },
    )
    return _sha256_json(stable_payload)


def resume_receipt_hash(payload: Mapping[str, object]) -> str:
    stable_payload = _stable_payload(
        payload,
        excluded={
            "schema_version",
            "contract_id",
            "receipt_id",
            "source_event_id",
        },
    )
    return _sha256_json(stable_payload)


def continuation_mode(value: object) -> str:
    mode = coerce_string(value)
    return mode if mode in CONTINUATION_MODES else CONTINUATION_MODE_TYPED_REHYDRATION


def resume_result(value: object, *, default: str) -> str:
    result = coerce_string(value)
    return result if result in RESUME_RESULTS else default


def dirty_paths_status(value: object, dirty_paths_count: int) -> str:
    status = coerce_string(value)
    if status in {"known", "unknown"}:
        return status
    return "unknown" if dirty_paths_count < 0 else "known"


def authority_result(
    value: object,
    *,
    current_blockers: object,
    dirty_paths_status_value: object,
) -> str:
    result = coerce_string(value)
    blockers = coerce_string(current_blockers)
    if blockers and blockers != "none":
        return AUTHORITY_RESULT_BLOCKED
    if dirty_paths_status(dirty_paths_status_value, 0) == "unknown":
        return AUTHORITY_RESULT_BLOCKED
    if result in AUTHORITY_RESULTS:
        return result
    return AUTHORITY_RESULT_ALLOWED


def _stable_payload(
    payload: Mapping[str, object],
    *,
    excluded: set[str],
) -> dict[str, object]:
    return {key: value for key, value in payload.items() if key not in excluded}


def _sha256_json(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "AUTHORITY_RESULTS",
    "CONTINUATION_MODES",
    "RESUME_RESULTS",
    "authority_result",
    "continuation_hash",
    "continuation_mode",
    "dirty_paths_status",
    "resume_receipt_hash",
    "resume_result",
]
