"""Shared report-attachment helpers for reviewer-runtime projections."""

from __future__ import annotations

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
    report["reviewer_runtime"] = reviewer_runtime_contract_to_dict(
        review_state.reviewer_runtime
    )
    report["doctor"] = build_reviewer_doctor_surface(
        contract=review_state.reviewer_runtime,
        attention=attention,
    )
