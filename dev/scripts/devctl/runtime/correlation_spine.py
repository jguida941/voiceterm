"""Shared lineage identifiers for actions, receipts, events, and projections."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import asdict, dataclass

from .value_coercion import coerce_string

CORRELATION_CONTEXT_CONTRACT_ID = "CorrelationContext"
CORRELATION_CONTEXT_SCHEMA_VERSION = 1
CORRELATION_REF_PREFIX = "correlation_ref:"
CAUSATION_REF_PREFIX = "causation_ref:"
RUN_REF_PREFIX = "run_ref:"


@dataclass(frozen=True, slots=True)
class CorrelationContext:
    """Typed parent-link context threaded through runtime evidence."""

    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""
    schema_version: int = CORRELATION_CONTEXT_SCHEMA_VERSION
    contract_id: str = CORRELATION_CONTEXT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def correlation_id_for_ref(ref_kind: object, ref_value: object) -> str:
    """Return a deterministic correlation id for a typed evidence ref."""
    return _lineage_id("corr", ref_kind, ref_value)


def causation_id_for_ref(ref_kind: object, ref_value: object) -> str:
    """Return a deterministic causation id for a typed trigger ref."""
    return _lineage_id("cause", ref_kind, ref_value)


def run_id_for_ref(ref_kind: object, ref_value: object) -> str:
    """Return a deterministic run id for a bounded orchestration ref."""
    return _lineage_id("run", ref_kind, ref_value)


def correlation_ref(correlation_id: object) -> str:
    """Return the canonical evidence ref for a correlation id."""
    value = coerce_string(correlation_id)
    return f"{CORRELATION_REF_PREFIX}{value}" if value else ""


def causation_ref(causation_id: object) -> str:
    """Return the canonical evidence ref for a causation id."""
    value = coerce_string(causation_id)
    return f"{CAUSATION_REF_PREFIX}{value}" if value else ""


def run_ref(run_id: object) -> str:
    """Return the canonical evidence ref for a run id."""
    value = coerce_string(run_id)
    return f"{RUN_REF_PREFIX}{value}" if value else ""


def correlation_context_from_mapping(
    payload: Mapping[str, object] | object,
) -> CorrelationContext:
    """Deserialize optional lineage fields from an existing typed payload."""
    if not isinstance(payload, Mapping):
        return CorrelationContext()
    return CorrelationContext(
        correlation_id=coerce_string(payload.get("correlation_id")),
        causation_id=coerce_string(payload.get("causation_id")),
        run_id=coerce_string(payload.get("run_id")),
    )


def correlation_context_for_ref(
    ref_kind: object,
    ref_value: object,
    *,
    causation_kind: object = "",
    causation_ref_value: object = "",
    run_kind: object = "",
    run_ref_value: object = "",
) -> CorrelationContext:
    """Build deterministic lineage ids from a primary ref plus optional parents."""
    correlation_id = correlation_id_for_ref(ref_kind, ref_value)
    return CorrelationContext(
        correlation_id=correlation_id,
        causation_id=(
            causation_id_for_ref(causation_kind, causation_ref_value)
            if coerce_string(causation_ref_value)
            else ""
        ),
        run_id=(
            run_id_for_ref(run_kind, run_ref_value)
            if coerce_string(run_ref_value)
            else ""
        ),
    )


def merge_correlation_context(
    primary: Mapping[str, object] | object,
    fallback: Mapping[str, object] | object = None,
    *,
    seed_kind: object = "",
    seed_ref: object = "",
) -> CorrelationContext:
    """Merge explicit lineage fields and fill a deterministic correlation id."""
    primary_context = correlation_context_from_mapping(primary)
    fallback_context = correlation_context_from_mapping(fallback)
    correlation_id = primary_context.correlation_id or fallback_context.correlation_id
    if not correlation_id and coerce_string(seed_ref):
        correlation_id = correlation_id_for_ref(seed_kind, seed_ref)
    return CorrelationContext(
        correlation_id=correlation_id,
        causation_id=primary_context.causation_id or fallback_context.causation_id,
        run_id=primary_context.run_id or fallback_context.run_id,
    )


def lineage_fields(context: CorrelationContext) -> dict[str, str]:
    """Return the stable field trio used by existing typed contracts."""
    return {
        "correlation_id": context.correlation_id,
        "causation_id": context.causation_id,
        "run_id": context.run_id,
    }


def _lineage_id(prefix: str, ref_kind: object, ref_value: object) -> str:
    kind = coerce_string(ref_kind)
    value = coerce_string(ref_value)
    if not value:
        return ""
    digest = hashlib.sha256(f"{kind}\n{value}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


__all__ = [
    "CAUSATION_REF_PREFIX",
    "CORRELATION_CONTEXT_CONTRACT_ID",
    "CORRELATION_CONTEXT_SCHEMA_VERSION",
    "CORRELATION_REF_PREFIX",
    "RUN_REF_PREFIX",
    "CorrelationContext",
    "causation_id_for_ref",
    "causation_ref",
    "correlation_context_for_ref",
    "correlation_context_from_mapping",
    "correlation_id_for_ref",
    "correlation_ref",
    "lineage_fields",
    "merge_correlation_context",
    "run_id_for_ref",
    "run_ref",
]
