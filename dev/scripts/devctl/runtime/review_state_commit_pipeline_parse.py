"""Helpers for parsing review-state commit-pipeline payloads."""

from __future__ import annotations

from collections.abc import Mapping

from .control_state import _mapping
from .remote_commit_pipeline_models import (
    remote_commit_pipeline_contract_from_mapping,
)


def commit_pipeline_from_review_payload(
    *,
    payload: Mapping[str, object],
    review_payload: Mapping[str, object],
):
    """Resolve the commit-pipeline contract from review-state payload shapes."""
    return remote_commit_pipeline_contract_from_mapping(
        _mapping(review_payload.get("commit_pipeline")) or _mapping(payload.get("commit_pipeline"))
    )
