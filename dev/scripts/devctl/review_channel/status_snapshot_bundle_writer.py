"""Status snapshot bundle write coordination."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..runtime.review_state_models import RecoveryAssessmentState, ReviewState
from .core import LaneAssignment
from .status_bundle import (
    StatusProjectionBundleResult,
    StatusProjectionContext,
    StatusProjectionPayload,
    write_status_projection_bundle,
)


@dataclass(frozen=True)
class SnapshotBundleInputs:
    """Grouped inputs for writing the status projection bundle."""

    repo_root: Path
    bridge_path: Path
    review_channel_path: Path
    output_root: Path
    promotion_plan_path: Path | None
    lanes: list[LaneAssignment]
    bridge_liveness: dict[str, object]
    attention: dict[str, object] | None
    current_session: object
    recovery_assessment: RecoveryAssessmentState | None
    prior_review_state: Mapping[str, object] | None
    reviewer_accepted_implementer_state_hash_override: str | None
    reviewer_worker: dict[str, object]
    push_decision: dict[str, object]
    service_identity: dict[str, object]
    attach_auth_policy: dict[str, object]
    warnings: list[str]
    errors: list[str]
    reduced_runtime: dict[str, object]


def write_snapshot_bundle(
    inputs: SnapshotBundleInputs,
) -> tuple[StatusProjectionBundleResult, ReviewState | None]:
    """Write the status projection bundle and parse its ReviewState payload."""
    bundle_result = write_status_projection_bundle(
        context=StatusProjectionContext(
            repo_root=inputs.repo_root,
            bridge_path=inputs.bridge_path,
            review_channel_path=inputs.review_channel_path,
            output_root=inputs.output_root,
            promotion_plan_path=inputs.promotion_plan_path,
            lanes=inputs.lanes,
            bridge_liveness=inputs.bridge_liveness,
            attention=inputs.attention,
            current_session=inputs.current_session,
            recovery_assessment=inputs.recovery_assessment,
            prior_review_state=inputs.prior_review_state,
            reviewer_accepted_implementer_state_hash_override=(
                inputs.reviewer_accepted_implementer_state_hash_override
            ),
        ),
        payload=StatusProjectionPayload(
            reviewer_worker=inputs.reviewer_worker,
            push_decision=inputs.push_decision,
            service_identity=inputs.service_identity,
            attach_auth_policy=inputs.attach_auth_policy,
            warnings=inputs.warnings,
            errors=inputs.errors,
            reduced_runtime=inputs.reduced_runtime,
        ),
    )
    from ..runtime.review_state_parser import review_state_from_payload

    return bundle_result, review_state_from_payload(bundle_result.review_state)


__all__ = [
    "SnapshotBundleInputs",
    "write_snapshot_bundle",
]
