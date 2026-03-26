"""Projection helpers for bridge-backed and event-backed review-channel state."""

from __future__ import annotations

from pathlib import Path

from .attention import derive_bridge_attention
from .bridge_validation import validate_live_bridge_contract
from .core import (
    LaneAssignment,
    ensure_launcher_prereqs,
    project_id_for_repo,
)
from .daemon_reducer import build_lifecycle_runtime_state
from .handoff import (
    bridge_liveness_to_dict,
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from .heartbeat import compute_non_audit_worktree_hash
from .heartbeat import bridge_excluded_rel_paths
from .peer_liveness import (
    OverallLivenessState,
    reviewer_mode_is_active,
)
from .projection_bundle import (
    build_agent_registry_from_lanes,
    projection_paths_to_dict as projection_paths_to_dict,
    write_projection_bundle as write_projection_bundle,
)
from .reviewer_worker import check_review_needed, reviewer_worker_tick_to_dict
from .status_models import ReviewChannelStatusSnapshot
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
from .service_identity import build_service_identity


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
) -> ReviewChannelStatusSnapshot:
    """Refresh the latest review-channel projections for read-only consumers."""
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
    merged_errors.extend(validate_live_bridge_contract(bridge_snapshot))
    publisher_state, reviewer_supervisor_state = _load_lifecycle_states(output_root)
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
    merged_warnings.extend(bridge_liveness_warnings(bridge_liveness))
    merged_errors.extend(hybrid_loop_errors(bridge_liveness))
    attention = derive_bridge_attention(
        bridge_liveness, contract_errors=merged_errors,
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

    projection_paths = write_status_projection_bundle(
        context=StatusProjectionContext(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=output_root,
            promotion_plan_path=promotion_plan_path,
            lanes=lanes,
            bridge_liveness=bridge_liveness,
            attention=attention,
        ),
        payload=StatusProjectionPayload(
            reviewer_worker=reviewer_worker,
            service_identity=service_identity,
            attach_auth_policy=attach_auth_policy,
            warnings=merged_warnings,
            errors=merged_errors,
            reduced_runtime=reduced_runtime,
        ),
    )

    return ReviewChannelStatusSnapshot(
        lanes=lanes,
        bridge_liveness=bridge_liveness,
        attention=attention,
        warnings=merged_warnings,
        errors=merged_errors,
        projection_paths=projection_paths,
        reviewer_worker=reviewer_worker,
        service_identity=service_identity,
        attach_auth_policy=attach_auth_policy,
    )


def _load_status_lanes(
    *,
    review_channel_path: Path,
    bridge_path: Path,
    execution_mode: str,
) -> list[LaneAssignment]:
    _, lanes = ensure_launcher_prereqs(
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        execution_mode=execution_mode,
    )
    return lanes


def _build_status_bridge_liveness(
    *,
    bridge_snapshot,
    repo_root: Path,
    bridge_path: Path,
) -> dict[str, object]:
    return bridge_liveness_to_dict(
        summarize_bridge_liveness(
            bridge_snapshot,
            current_worktree_hash=_current_worktree_hash(
                repo_root=repo_root,
                bridge_path=bridge_path,
            ),
        )
    )


def _current_worktree_hash(*, repo_root: Path, bridge_path: Path) -> str | None:
    try:
        return compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=bridge_excluded_rel_paths(
                repo_root=repo_root,
                bridge_path=bridge_path,
            ),
        )
    except (ValueError, OSError):
        return None


def _load_lifecycle_states(output_root: Path) -> tuple[dict[str, object], dict[str, object]]:
    return (
        read_publisher_state(output_root),
        read_reviewer_supervisor_state(output_root),
    )


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


def _build_reviewer_worker_snapshot(
    *,
    repo_root: Path,
    bridge_path: Path,
    bridge_text: str,
) -> dict[str, object]:
    return reviewer_worker_tick_to_dict(
        check_review_needed(
            repo_root=repo_root,
            bridge_path=bridge_path,
            bridge_text=bridge_text,
            current_hash=_current_worktree_hash(
                repo_root=repo_root,
                bridge_path=bridge_path,
            ),
        )
    )


def _build_reduced_runtime(
    *,
    publisher_state: dict[str, object],
    reviewer_supervisor_state: dict[str, object],
) -> dict[str, object]:
    return build_lifecycle_runtime_state(
        publisher_state=publisher_state,
        reviewer_supervisor_state=reviewer_supervisor_state,
    )
