"""Projection helpers for bridge-backed and event-backed review-channel state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..runtime.review_state_models import RecoveryAssessmentState, ReviewState
from ..runtime.review_state_locator import (
    load_current_review_state_payload,
    load_review_state_payload,
)
from .bridge_validation import validate_live_bridge_contract
from .core import LaneAssignment, project_id_for_repo
from .daemon_reducer import build_lifecycle_runtime_state
from .handoff import extract_bridge_snapshot
from .peer_liveness import (
    OverallLivenessState,
    reviewer_mode_is_active,
)
from .projection_bundle import (
    projection_paths_to_dict as projection_paths_to_dict,
    write_projection_bundle as write_projection_bundle,
)
from .status_models import ReviewChannelStatusSnapshot
from .status_snapshot_authority import (
    StatusAuthorityInputs,
    build_status_authority,
)
from .status_push_decision import build_status_push_decision
from .status_bundle import (
    StatusProjectionContext,
    StatusProjectionPayload,
    write_status_projection_bundle,
)
from .status_projection_helpers import (
    attach_conductor_session_state,
    bridge_liveness_warnings,
    build_bridge_push_enforcement_state,
    hybrid_loop_errors,
)
from .session_liveness_events import (
    emit_status_tick_participant_liveness_events,
    summarize_participant_liveness_events,
)
from .session_state_hints import detect_session_state_hints, session_state_hints_to_dict
from . import state_status_inputs as _state_status_inputs_mod
from .state_status_inputs import (
    build_reviewer_worker_snapshot as _build_reviewer_worker_snapshot,
    build_status_bridge_liveness as _build_status_bridge_liveness,
    load_lifecycle_states as _load_lifecycle_states,
    load_prior_review_state as _load_prior_review_state,
    load_status_lanes as _load_status_lanes,
)
from .lifecycle_state import (
    DEFAULT_REVIEW_STATUS_DIR_REL,
    PublisherHeartbeat,
    ReviewerSupervisorHeartbeat,
    read_publisher_state,
    read_reviewer_supervisor_state,
    write_publisher_heartbeat,
    write_reviewer_supervisor_heartbeat,
)
from .attach_auth_policy import build_attach_auth_policy
from .bridge_validation_acceptance import review_acceptance_projection
from .service_identity import build_service_identity
from .status_bundle import StatusProjectionBundleResult


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


compute_non_audit_worktree_hash = _state_status_inputs_mod.compute_non_audit_worktree_hash


def refresh_status_snapshot(
    *,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    output_root: Path,
    promotion_plan_path: Path | None = None,
    execution_mode: str = "markdown-bridge",
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    reviewer_overdue_threshold_seconds: int | None = None,
    reviewer_accepted_implementer_state_hash_override: str | None = None,
) -> ReviewChannelStatusSnapshot:
    """Refresh the latest review-channel projections for read-only consumers."""
    _sync_status_input_hooks()
    lanes = _load_status_lanes(
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        execution_mode=execution_mode,
    )
    bridge_text = bridge_path.read_text(encoding="utf-8")
    bridge_snapshot = extract_bridge_snapshot(bridge_text)
    bridge_liveness = _build_status_bridge_liveness(
        bridge_snapshot=bridge_snapshot,
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    bridge_liveness["push_enforcement"] = build_bridge_push_enforcement_state(
        repo_root
    )
    merged_warnings = list(warnings or [])
    merged_errors = list(errors or [])
    reviewer_worker = _build_reviewer_worker_snapshot(
        repo_root=repo_root,
        bridge_path=bridge_path,
        bridge_text=bridge_text,
    )
    bridge_liveness["review_needed"] = bool(reviewer_worker.get("review_needed"))
    _verdict, _findings, bridge_verdict_accepted = review_acceptance_projection(
        bridge_snapshot
    )
    bridge_liveness["bridge_verdict_accepted"] = bridge_verdict_accepted
    merged_errors.extend(validate_live_bridge_contract(bridge_snapshot))
    publisher_state, reviewer_supervisor_state = _load_lifecycle_states(output_root)
    prior_review_state = _load_prior_review_state(
        repo_root=repo_root,
        output_root=output_root,
    )
    _apply_lifecycle_bridge_liveness(
        bridge_liveness=bridge_liveness,
        publisher_state=publisher_state,
        reviewer_supervisor_state=reviewer_supervisor_state,
        reviewer_overdue_threshold_seconds=reviewer_overdue_threshold_seconds,
    )
    attach_conductor_session_state(
        bridge_liveness=bridge_liveness,
        output_root=output_root,
    )
    emitted_liveness_events = emit_status_tick_participant_liveness_events(
        repo_root=repo_root,
        session_output_root=output_root,
    )
    if emitted_liveness_events:
        bridge_liveness["participant_liveness_expired_events"] = (
            summarize_participant_liveness_events(emitted_liveness_events)
        )
    session_state_hints = detect_session_state_hints(session_output_root=output_root)
    if session_state_hints:
        bridge_liveness["session_state_hints"] = session_state_hints_to_dict(
            session_state_hints
        )
    merged_warnings.extend(bridge_liveness_warnings(bridge_liveness))
    merged_errors.extend(hybrid_loop_errors(bridge_liveness))
    current_session, attention, recovery_assessment, reviewer_runtime = (
        build_status_authority(
            StatusAuthorityInputs(
                repo_root=repo_root,
                output_root=output_root,
                bridge_snapshot=bridge_snapshot,
                bridge_text=bridge_text,
                bridge_liveness=bridge_liveness,
                prior_review_state=prior_review_state,
                merged_warnings=merged_warnings,
                merged_errors=merged_errors,
                reviewer_accepted_implementer_state_hash_override=(
                    reviewer_accepted_implementer_state_hash_override
                ),
            )
        )
    )
    bridge_liveness["review_accepted"] = (
        reviewer_runtime.review_acceptance.review_accepted
    )
    bridge_liveness["publish_clear"] = reviewer_runtime.publish_clear
    push_decision = build_status_push_decision(
        bridge_liveness=bridge_liveness,
        reviewer_runtime=reviewer_runtime,
    )
    service_identity = build_service_identity(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=output_root,
    )
    attach_auth_policy = build_attach_auth_policy(service_identity=service_identity)
    reduced_runtime = _build_reduced_runtime(
        publisher_state=publisher_state,
        reviewer_supervisor_state=reviewer_supervisor_state,
    )
    bundle_result, review_state = _write_snapshot_bundle(
        SnapshotBundleInputs(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=output_root,
            promotion_plan_path=promotion_plan_path,
            lanes=lanes,
            bridge_liveness=bridge_liveness,
            attention=attention,
            current_session=current_session,
            recovery_assessment=recovery_assessment,
            prior_review_state=prior_review_state,
            reviewer_accepted_implementer_state_hash_override=(
                reviewer_accepted_implementer_state_hash_override
            ),
            reviewer_worker=reviewer_worker,
            push_decision=push_decision,
            service_identity=service_identity,
            attach_auth_policy=attach_auth_policy,
            warnings=merged_warnings,
            errors=merged_errors,
            reduced_runtime=reduced_runtime,
        )
    )

    return ReviewChannelStatusSnapshot(
        lanes=lanes,
        bridge_liveness=bridge_liveness,
        attention=attention,
        warnings=merged_warnings,
        errors=merged_errors,
        projection_paths=bundle_result.projection_paths,
        reviewer_worker=reviewer_worker,
        push_decision=push_decision,
        service_identity=service_identity,
        attach_auth_policy=attach_auth_policy,
        review_state=review_state,
    )


def _write_snapshot_bundle(
    inputs: SnapshotBundleInputs,
) -> tuple[StatusProjectionBundleResult, ReviewState | None]:
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


def _apply_lifecycle_bridge_liveness(
    *,
    bridge_liveness: dict[str, object],
    publisher_state: dict[str, object],
    reviewer_supervisor_state: dict[str, object],
    reviewer_overdue_threshold_seconds: int | None,
) -> None:
    bridge_liveness["publisher_running"] = bool(publisher_state.get("running"))
    bridge_liveness["publisher_stop_reason"] = publisher_state.get("stop_reason", "")
    bridge_liveness["reviewer_supervisor_running"] = bool(
        reviewer_supervisor_state.get("running")
    )
    bridge_liveness["reviewer_supervisor_stop_reason"] = reviewer_supervisor_state.get(
        "stop_reason", ""
    )
    if reviewer_overdue_threshold_seconds is not None:
        bridge_liveness["reviewer_overdue_threshold_seconds"] = (
            reviewer_overdue_threshold_seconds
        )
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    if (
        reviewer_mode_is_active(reviewer_mode)
        and not bridge_liveness["publisher_running"]
        and not bridge_liveness["reviewer_supervisor_running"]
    ):
        bridge_liveness["overall_state"] = OverallLivenessState.RUNTIME_MISSING


def _build_reduced_runtime(
    *,
    publisher_state: dict[str, object],
    reviewer_supervisor_state: dict[str, object],
) -> dict[str, object]:
    return build_lifecycle_runtime_state(
        publisher_state=publisher_state,
        reviewer_supervisor_state=reviewer_supervisor_state,
    )


def _sync_status_input_hooks() -> None:
    _state_status_inputs_mod.load_review_state_payload = load_review_state_payload
    _state_status_inputs_mod.load_current_review_state_payload = (
        load_current_review_state_payload
    )
    _state_status_inputs_mod.compute_non_audit_worktree_hash = (
        compute_non_audit_worktree_hash
    )
