"""Shared report-attachment helpers for reviewer-runtime projections."""

from __future__ import annotations

from dataclasses import asdict
from collections.abc import Mapping

from ...runtime.review_state_models import ReviewState
from ...review_channel.reviewer_runtime_contract import (
    build_reviewer_doctor_surface,
    reviewer_runtime_contract_to_dict,
)


def attach_reviewer_runtime_snapshot(
    report: dict[str, object],
    *,
    review_state: ReviewState | None,
    attention: Mapping[str, object] | None,
) -> None:
    """Attach reviewer-runtime and doctor projections from one typed review state."""
    if review_state is None:
        return
    recovery_assessment = getattr(review_state, "recovery_assessment", None)
    review_attention = getattr(review_state, "attention", None)
    derived_attention = asdict(review_attention) if review_attention is not None else None
    effective_attention = derived_attention or (
        dict(attention) if isinstance(attention, Mapping) else None
    )
    report["reviewer_runtime"] = reviewer_runtime_contract_to_dict(
        review_state.reviewer_runtime
    )
    report["commit_pipeline"] = asdict(review_state.commit_pipeline)
    if effective_attention is not None:
        report["attention"] = effective_attention
    report["recovery_assessment"] = (
        asdict(recovery_assessment)
        if recovery_assessment is not None
        else None
    )
    bridge_liveness = (
        report.get("bridge_liveness")
        if isinstance(report.get("bridge_liveness"), Mapping)
        else None
    )
    report["doctor"] = build_reviewer_doctor_surface(
        contract=review_state.reviewer_runtime,
        collaboration=asdict(getattr(review_state, "collaboration", None))
        if getattr(review_state, "collaboration", None) is not None
        else None,
        recovery_assessment=recovery_assessment,
        attention=effective_attention,
        commit_pipeline=review_state.commit_pipeline,
        push_enforcement=(
            bridge_liveness.get("push_enforcement")
            if isinstance(bridge_liveness, Mapping)
            else None
        ),
        runtime_state={
            "publisher": report.get("publisher"),
            "reviewer_supervisor": report.get("reviewer_supervisor"),
        },
    )
