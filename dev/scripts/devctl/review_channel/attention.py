"""Attention-state policy for bridge-backed review-channel projections."""

from __future__ import annotations

from .recovery_assessment import (
    build_recovery_assessment,
    recovery_assessment_to_attention_payload,
)


def derive_bridge_attention(
    bridge_liveness: dict[str, object],
    *,
    push_state: dict[str, object] | None = None,
    contract_errors: list[str] | None = None,
) -> dict[str, object]:
    """Translate bridge liveness into the legacy attention projection."""
    assessment = build_recovery_assessment(
        bridge_liveness=bridge_liveness,
        push_state=push_state,
        contract_errors=contract_errors,
    )
    return recovery_assessment_to_attention_payload(assessment)
