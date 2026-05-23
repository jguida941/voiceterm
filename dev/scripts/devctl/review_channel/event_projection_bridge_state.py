"""Bridge-state compatibility projection for event-backed review state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from ..runtime.conductor_capability import (
    authority_reviewer_mode,
    build_conductor_capability_state,
)
from ..runtime.review_state_models import ReviewerRuntimeContract
from ..runtime.role_profile import TandemRole
from .collaboration_provider import collaboration_provider_for_capability
from .current_session_projection import current_session_mapping
from .peer_liveness import resolve_reported_reviewer_mode


def build_event_bridge_state_projection(
    *,
    review_state: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    reviewer_runtime: ReviewerRuntimeContract | None = None,
) -> dict[str, object]:
    """Build the compatibility bridge-state projection for event-backed flows."""
    current_session = current_session_mapping(review_state)
    collaboration = _mapping(review_state.get("collaboration"))
    runtime_posture = (
        reviewer_runtime.session_posture if reviewer_runtime is not None else None
    )
    effective_mode = _effective_mode(
        runtime_posture=runtime_posture,
        reviewer_runtime=reviewer_runtime,
        bridge_liveness=bridge_liveness,
    )
    reviewer_mode = _reviewer_mode(
        runtime_posture=runtime_posture,
        reviewer_runtime=reviewer_runtime,
        bridge_liveness=bridge_liveness,
        effective_mode=effective_mode,
    )
    implementer_status = str(
        current_session.get("implementer_status")
        or bridge_liveness.get("implementer_status")
        or ""
    )
    implementer_ack = str(
        current_session.get("implementer_ack")
        or bridge_liveness.get("implementer_ack")
        or ""
    )
    implementer_ack_revision = str(
        current_session.get("implementer_ack_revision")
        or bridge_liveness.get("implementer_ack_revision")
        or ""
    )
    implementer_ack_current = (
        str(current_session.get("implementer_ack_state") or "").strip() == "current"
        or bool(bridge_liveness.get("implementer_ack_current"))
        or bool(bridge_liveness.get("claude_ack_current"))
    )
    bridge_state = _base_bridge_state(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
        reviewer_mode=reviewer_mode,
        effective_mode=effective_mode,
    )
    bridge_state.update(
        _session_bridge_fields(
            current_session=current_session,
            bridge_liveness=bridge_liveness,
            implementer_status=implementer_status,
            implementer_ack=implementer_ack,
            implementer_ack_revision=implementer_ack_revision,
            implementer_ack_current=implementer_ack_current,
            reviewer_runtime=reviewer_runtime,
        )
    )
    reviewer_provider = collaboration_provider_for_capability(
        collaboration,
        capability_classes={
            "review",
            "test",
            "architecture",
            "governance",
            "research",
            "intake",
        },
    )
    implementer_provider = collaboration_provider_for_capability(
        collaboration,
        capability_classes={"implementation", "mutation"},
    )
    bridge_state["reviewer_capability"] = asdict(
        build_conductor_capability_state(
            provider=reviewer_provider,
            role=TandemRole.REVIEWER.value,
            reviewer_mode=effective_mode,
        )
    )
    bridge_state["implementer_capability"] = asdict(
        build_conductor_capability_state(
            provider=implementer_provider,
            role=TandemRole.IMPLEMENTER.value,
            reviewer_mode=effective_mode,
        )
    )
    return bridge_state


def _effective_mode(
    *,
    runtime_posture: object,
    reviewer_runtime: ReviewerRuntimeContract | None,
    bridge_liveness: Mapping[str, object],
) -> str:
    runtime_mode = str(
        getattr(runtime_posture, "effective_reviewer_mode", "")
        or getattr(reviewer_runtime, "effective_reviewer_mode", "")
        if reviewer_runtime is not None
        else ""
    ).strip()
    return runtime_mode or str(
        bridge_liveness.get("effective_reviewer_mode")
        or bridge_liveness.get("reviewer_mode")
        or "tools_only"
    )


def _reviewer_mode(
    *,
    runtime_posture: object,
    reviewer_runtime: ReviewerRuntimeContract | None,
    bridge_liveness: Mapping[str, object],
    effective_mode: str,
) -> str:
    runtime_mode = str(
        getattr(runtime_posture, "reviewer_mode", "")
        or getattr(reviewer_runtime, "reviewer_mode", "")
        if reviewer_runtime is not None
        else ""
    ).strip()
    return authority_reviewer_mode(
        runtime_mode or str(bridge_liveness.get("reviewer_mode") or ""),
        effective_mode,
    )


def _base_bridge_state(
    *,
    review_state: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    reviewer_mode: str,
    effective_mode: str,
) -> dict[str, object]:
    declared_reviewer_mode = resolve_reported_reviewer_mode(
        {"reviewer_mode": bridge_liveness.get("declared_reviewer_mode") or reviewer_mode}
    )
    return {
        "overall_state": str(bridge_liveness.get("overall_state") or "unknown"),
        "codex_poll_state": str(
            bridge_liveness.get("codex_poll_state") or "missing"
        ),
        "reviewer_freshness": str(
            bridge_liveness.get("reviewer_freshness") or "missing"
        ),
        "reviewer_mode": reviewer_mode,
        "declared_reviewer_mode": declared_reviewer_mode,
        "last_codex_poll_utc": str(review_state.get("timestamp") or ""),
        "last_codex_poll_age_seconds": int(
            bridge_liveness.get("last_codex_poll_age_seconds") or 0
        ),
        "last_worktree_hash": "",
        "implementer_completion_stall": bool(
            bridge_liveness.get("implementer_completion_stall")
        ),
        "publisher_running": bool(bridge_liveness.get("publisher_running")),
        "launch_truth": str(bridge_liveness.get("launch_truth") or ""),
        "effective_reviewer_mode": effective_mode,
        "reviewed_hash_current": bridge_liveness.get("reviewed_hash_current"),
        "review_needed": bridge_liveness.get("review_needed"),
        "head_at_push_time": str(bridge_liveness.get("head_at_push_time") or ""),
        "codex_conductor_active": bool(
            bridge_liveness.get("codex_conductor_active")
        ),
        "claude_conductor_active": bool(
            bridge_liveness.get("claude_conductor_active")
        ),
        "pending_total": int(_mapping(review_state.get("queue")).get("pending_total") or 0),
        "session_liveness_signals": tuple(
            row
            for row in bridge_liveness.get("session_liveness_signals") or ()
            if isinstance(row, Mapping)
        ),
    }


def _session_bridge_fields(
    *,
    current_session: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    implementer_status: str,
    implementer_ack: str,
    implementer_ack_revision: str,
    implementer_ack_current: bool,
    reviewer_runtime: ReviewerRuntimeContract | None,
) -> dict[str, object]:
    return {
        "open_findings": str(current_session.get("open_findings") or ""),
        "current_instruction": str(current_session.get("current_instruction") or ""),
        "claude_status": implementer_status,
        "claude_ack": implementer_ack,
        "claude_ack_current": implementer_ack_current,
        "current_instruction_revision": str(
            current_session.get("current_instruction_revision") or ""
        ),
        "claude_ack_revision": implementer_ack_revision,
        "last_reviewed_scope": str(current_session.get("last_reviewed_scope") or ""),
        "reviewer_poll_state": str(
            bridge_liveness.get("reviewer_poll_state")
            or bridge_liveness.get("codex_poll_state")
            or "missing"
        ),
        "last_reviewer_poll_utc": str(
            bridge_liveness.get("last_reviewer_poll_utc") or ""
        ),
        "last_reviewer_poll_age_seconds": int(
            bridge_liveness.get("last_reviewer_poll_age_seconds")
            or bridge_liveness.get("last_codex_poll_age_seconds")
            or 0
        ),
        "implementer_status": implementer_status,
        "implementer_ack": implementer_ack,
        "implementer_ack_current": implementer_ack_current,
        "implementer_ack_revision": implementer_ack_revision,
        "implementer_state_hash": str(
            current_session.get("implementer_state_hash") or ""
        ),
        "review_accepted": bool(
            reviewer_runtime.review_acceptance.review_accepted
            if reviewer_runtime is not None
            else False
        ),
    }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


__all__ = ["build_event_bridge_state_projection"]
