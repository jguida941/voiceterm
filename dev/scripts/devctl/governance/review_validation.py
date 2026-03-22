"""Validation helpers for governance-review rows and CLI inputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .ledger_helpers import optional_text, required_text
from ..governance_review_models import (
    FINDING_REVIEW_CONTRACT_ID,
    FINDING_REVIEW_SCHEMA_VERSION,
    VALID_FINDING_CLASSES,
    VALID_PREVENTION_SURFACES,
    VALID_RECURRENCE_RISKS,
)

VALID_FINDING_CLASS_SET = frozenset(VALID_FINDING_CLASSES)
VALID_RECURRENCE_RISK_SET = frozenset(VALID_RECURRENCE_RISKS)
VALID_PREVENTION_SURFACE_SET = frozenset(VALID_PREVENTION_SURFACES)


def normalize_schema_version(value: object) -> int | None:
    """Normalize a schema version field from a JSONL row."""
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def require_choice(value: str, allowed: frozenset[str], *, field_name: str) -> str:
    """Normalize and validate a bounded string choice."""
    text = required_text(value, field_name=field_name).lower()
    if text not in allowed:
        joined = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {joined}")
    return text


def governance_review_row_disposition_errors(
    row: Mapping[str, Any],
) -> tuple[str, ...]:
    """Return schema/disposition problems for one governance-review row."""
    schema_version = normalize_schema_version(row.get("schema_version"))
    if schema_version is None or schema_version < FINDING_REVIEW_SCHEMA_VERSION:
        return ()

    errors: list[str] = []
    contract_id = optional_text(row.get("contract_id"))
    if contract_id != FINDING_REVIEW_CONTRACT_ID:
        errors.append(
            f"contract_id must be {FINDING_REVIEW_CONTRACT_ID!r} for schema v{schema_version}"
        )
    verdict = optional_text(row.get("verdict")) or "unknown"
    finding_class = optional_text(row.get("finding_class"))
    recurrence_risk = optional_text(row.get("recurrence_risk"))
    prevention_surface = optional_text(row.get("prevention_surface"))
    waiver_reason = optional_text(row.get("waiver_reason"))

    if finding_class not in VALID_FINDING_CLASS_SET:
        errors.append("finding_class must be one of: " + ", ".join(VALID_FINDING_CLASSES))
    if recurrence_risk not in VALID_RECURRENCE_RISK_SET:
        errors.append("recurrence_risk must be one of: " + ", ".join(VALID_RECURRENCE_RISKS))
    if prevention_surface not in VALID_PREVENTION_SURFACE_SET:
        errors.append(
            "prevention_surface must be one of: " + ", ".join(VALID_PREVENTION_SURFACES)
        )
    if prevention_surface == "none" and not waiver_reason:
        errors.append("waiver_reason is required when prevention_surface is 'none'")
    if verdict in {"waived", "deferred"} and not waiver_reason:
        errors.append("waiver_reason is required for waived or deferred verdicts")
    return tuple(errors)
