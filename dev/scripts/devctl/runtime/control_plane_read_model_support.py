"""Helper assembly support for the control-plane read model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, NamedTuple

from ..platform.coordination_snapshot_models import CoordinationSnapshot
from .auto_mode import AutoModeInputs, AutoModeState, resolve_auto_mode_phase
from .control_plane_loop_wake import (
    ControlPlaneLoopWakeState,
    resolve_control_plane_loop_wake,
)
from .control_plane_pending_packets import resolve_pending_packets
from .control_plane_resolve import (
    resolve_blocker_and_action,
    resolve_daemon_state,
    resolve_implementation_blocked,
    resolve_quality,
    resolve_reviewer_state,
    utc_now_iso,
)
from .operator_context import derive_operator_interaction_mode
from .reviewer_observation import ReviewerObservation, resolve_reviewer_observation
from .reviewer_runtime_models import (
    RemoteControlAttachmentState,
    remote_control_attachment_from_mapping,
)
from .value_coercion import coerce_string

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .review_state_models import ReviewState


@dataclass(frozen=True, slots=True)
class ControlPlaneReadModelOptions:
    """Optional frozen inputs shared by control-plane read-model callers."""

    governance: "ProjectGovernance | None" = None
    review_state: "ReviewState | None" = None
    review_status_dir: Path | None = None
    caller_role: object = ""


class ResolvedControlPlaneContext(NamedTuple):
    reviewer: dict[str, Any]
    daemons: dict[str, Any]
    quality: dict[str, Any]
    pending: int
    blocker: dict[str, Any]
    implementation_blocked: bool
    operator_interaction_mode: str
    auto_state: AutoModeState
    reviewer_observation: ReviewerObservation | None
    coordination: CoordinationSnapshot | None
    remote_control_attachment: RemoteControlAttachmentState | None
    snapshot_id: str
    loop_wake: ControlPlaneLoopWakeState


class ControlPlaneContextInputs(NamedTuple):
    sources: dict[str, Any]
    git: dict[str, Any]
    governance: "ProjectGovernance | None"
    review_state: "ReviewState | None"
    review_state_payload: Mapping[str, Any] | None
    receipt: object
    push_report: object
    compact: object
    full_json: object


def resolve_control_plane_context(
    *,
    repo_root: Path,
    inputs: ControlPlaneContextInputs,
    extract_coordination_fn: Callable[..., CoordinationSnapshot | None] | None = None,
) -> ResolvedControlPlaneContext:
    reviewer = resolve_reviewer_state(
        inputs.review_state_payload,
        inputs.compact,
        inputs.full_json,
    )
    daemons = resolve_daemon_state(inputs.sources)
    quality = resolve_quality(inputs.push_report)
    pending = resolve_pending_packets(inputs.review_state_payload)
    blocker = resolve_blocker_and_action(
        inputs.receipt,
        inputs.review_state_payload,
        quality,
        pending_count=pending,
    )
    implementation_blocked = resolve_implementation_blocked(
        inputs.receipt,
        inputs.review_state_payload,
    )
    operator_interaction_mode = derive_operator_interaction_mode(
        governance=inputs.governance,
        review_state_payload=inputs.review_state_payload,
        receipt=inputs.receipt if isinstance(inputs.receipt, Mapping) else None,
        reviewer_mode=reviewer["reviewer_mode"],
    )
    push_action = coerce_string((inputs.receipt or {}).get("push_action")) if isinstance(
        inputs.receipt, Mapping
    ) else ""
    auto_state = resolve_auto_mode_phase(
        AutoModeInputs(
            push_decision_action=push_action,
            worktree_clean=inputs.git.get("clean", True),
            review_gate_allows_push=reviewer["review_accepted"],
            reviewer_mode=reviewer["reviewer_mode"],
            implementation_blocked=implementation_blocked,
            last_guard_ok=quality["last_guard_ok"],
            current_head_commit=inputs.git.get("head", ""),
            last_reviewed_sha=reviewer.get("last_reviewed_sha", ""),
            pending_action_requests=pending,
            operator_interaction_mode=operator_interaction_mode,
            timestamp_utc=utc_now_iso(),
        )
    )
    reviewer_observation = _build_reviewer_observation(
        head_sha=inputs.git.get("head", "unknown"),
        reviewer=reviewer,
        review_state=inputs.review_state_payload,
    )
    extract_coordination = extract_coordination_fn or _extract_coordination
    coordination = extract_coordination(
        repo_root=repo_root,
        sources=inputs.sources,
        governance=inputs.governance,
        allow_startup_fallback="review_state" not in inputs.sources,
        review_state=inputs.review_state,
    )
    remote_control_attachment = remote_control_attachment_from_mapping(
        _nested_get(
            inputs.review_state_payload,
            "reviewer_runtime",
            "remote_control_attachment",
        )
    )
    snapshot_id = coerce_string(
        _nested_get(inputs.review_state_payload, "snapshot_id")
    )
    loop_wake = resolve_control_plane_loop_wake(
        review_state_payload=inputs.review_state_payload,
        reviewer_mode=reviewer["reviewer_mode"],
        remote_control_attachment=remote_control_attachment,
        codex_conductor_alive=daemons["codex_conductor_alive"],
        claude_conductor_alive=daemons["claude_conductor_alive"],
    )
    return ResolvedControlPlaneContext(
        reviewer=reviewer,
        daemons=daemons,
        quality=quality,
        pending=pending,
        blocker=blocker,
        implementation_blocked=implementation_blocked,
        operator_interaction_mode=operator_interaction_mode,
        auto_state=auto_state,
        reviewer_observation=reviewer_observation,
        coordination=coordination,
        remote_control_attachment=remote_control_attachment,
        snapshot_id=snapshot_id,
        loop_wake=loop_wake,
    )


def _nested_get(d: Mapping[str, Any] | None, *keys: str) -> Any:
    cur: Any = d
    for key in keys:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(key)
    return cur


def _build_reviewer_observation(
    *,
    head_sha: str,
    reviewer: dict[str, Any],
    review_state: Mapping[str, Any] | None,
) -> ReviewerObservation | None:
    bridge: dict[str, Any] = {}
    if review_state:
        bridge = dict(review_state.get("bridge", {}) or {})
    poll_utc = coerce_string(
        bridge.get("last_reviewer_poll_utc") or bridge.get("last_codex_poll_utc")
    )
    review_needed = bool(bridge.get("review_needed", True))
    reviewed_hash_current = bool(bridge.get("reviewed_hash_current", False))
    head_at_push_time = coerce_string(bridge.get("head_at_push_time"))
    return resolve_reviewer_observation(
        head_sha=head_sha,
        last_codex_poll_utc=poll_utc,
        reviewer_freshness=reviewer["reviewer_freshness"],
        review_needed=review_needed,
        reviewed_hash_current=reviewed_hash_current,
        last_reviewed_sha=reviewer.get("last_reviewed_sha", ""),
        head_at_push_time=head_at_push_time,
        review_accepted=reviewer["review_accepted"],
    )


def _extract_coordination(
    *,
    repo_root: Path,
    sources: dict[str, Any],
    governance: "ProjectGovernance | None",
    allow_startup_fallback: bool,
    review_state: "ReviewState | None" = None,
) -> CoordinationSnapshot | None:
    from .coordination_loader import load_coordination_snapshot

    fresh = load_coordination_snapshot(
        repo_root=repo_root,
        sources=sources,
        governance=governance,
        review_state=review_state,
    )
    if fresh is not None:
        return fresh
    if not allow_startup_fallback:
        return None
    try:
        from .startup_context import build_startup_context
    except ImportError:
        return None
    startup_context = build_startup_context(repo_root=repo_root)
    return startup_context.coordination
