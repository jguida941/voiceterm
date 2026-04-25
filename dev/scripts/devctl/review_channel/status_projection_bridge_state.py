"""Typed bridge-state helpers for review-state projection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from ..runtime.conductor_capability import (
    authority_reviewer_mode,
    build_conductor_capability_state,
)
from ..runtime.review_state_models import (
    CollaborationSessionState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
    ReviewerRuntimeContract,
)
from ..runtime.review_state_semantics import is_pending_implementer_state
from ..runtime.role_profile import TandemRole, default_provider_for_role
from .collaboration_provider import collaboration_provider
from .handoff import BridgeSnapshot
from .launch_truth import classify_launch_truth, effective_reviewer_mode
from .peer_liveness import resolve_reported_reviewer_mode


def build_typed_bridge_liveness(
    *,
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    collaboration: CollaborationSessionState | None = None,
    snapshot: BridgeSnapshot | None = None,
) -> dict[str, object]:
    typed = dict(bridge_liveness)
    if snapshot is not None:
        typed.setdefault(
            "head_at_push_time",
            str(snapshot.metadata.get("head_at_push_time") or "").strip(),
        )
        if not str(typed.get("last_worktree_hash") or "").strip():
            typed["last_worktree_hash"] = str(
                snapshot.metadata.get("last_non_audit_worktree_hash") or ""
            ).strip()
    reviewer_poll_state = str(
        typed.get("reviewer_poll_state") or typed.get("codex_poll_state") or "unknown"
    )
    reviewer_poll_utc = str(
        typed.get("last_reviewer_poll_utc") or typed.get("last_codex_poll_utc") or ""
    )
    reviewer_poll_age = int(
        typed.get("last_reviewer_poll_age_seconds")
        or typed.get("last_codex_poll_age_seconds")
        or 0
    )
    implementer_status = str(
        typed.get("implementer_status") or typed.get("claude_status") or ""
    )
    implementer_ack = str(typed.get("implementer_ack") or typed.get("claude_ack") or "")
    reviewer_mode = resolve_reported_reviewer_mode(typed)
    live_provider_ids = _live_participant_providers(collaboration)
    if collaboration is not None:
        typed["active_conductor_providers"] = list(live_provider_ids)
        typed["codex_conductor_active"] = "codex" in live_provider_ids
        typed["claude_conductor_active"] = "claude" in live_provider_ids
    typed["declared_reviewer_mode"] = reviewer_mode
    typed["reviewer_mode"] = reviewer_mode
    typed["reviewer_poll_state"] = reviewer_poll_state
    typed["codex_poll_state"] = reviewer_poll_state
    typed["last_reviewer_poll_utc"] = reviewer_poll_utc
    typed["last_codex_poll_utc"] = reviewer_poll_utc
    typed["last_reviewer_poll_age_seconds"] = reviewer_poll_age
    typed["last_codex_poll_age_seconds"] = reviewer_poll_age
    typed["current_instruction"] = current_session.current_instruction
    typed["current_instruction_revision"] = current_session.current_instruction_revision
    typed["claude_ack_revision"] = current_session.implementer_ack_revision
    typed["claude_ack_current"] = current_session.implementer_ack_state == "current"
    typed["implementer_status"] = (
        implementer_status or current_session.implementer_status
    )
    typed["claude_status"] = typed["implementer_status"]
    typed["implementer_ack"] = implementer_ack or current_session.implementer_ack
    typed["claude_ack"] = typed["implementer_ack"]
    typed["implementer_ack_state"] = current_session.implementer_ack_state
    typed["implementer_state_hash"] = current_session.implementer_state_hash
    typed["implementer_ack_revision"] = current_session.implementer_ack_revision
    typed["implementer_ack_current"] = (
        current_session.implementer_ack_state == "current"
    )
    typed["launch_truth"] = classify_launch_truth(typed).value
    typed["effective_reviewer_mode"] = effective_reviewer_mode(typed)
    effective_mode = str(typed.get("effective_reviewer_mode") or reviewer_mode)
    typed["reviewer_mode"] = authority_reviewer_mode(reviewer_mode, effective_mode)
    reviewer_provider = collaboration_provider(
        collaboration,
        role_id="review_agent",
        default=default_provider_for_role(TandemRole.REVIEWER),
    )
    implementer_provider = collaboration_provider(
        collaboration,
        role_id="coding_agent",
        default=default_provider_for_role(TandemRole.IMPLEMENTER),
    )
    typed["reviewer_capability"] = asdict(
        build_conductor_capability_state(
            provider=reviewer_provider,
            reviewer_mode=effective_mode,
        )
    )
    typed["implementer_capability"] = asdict(
        build_conductor_capability_state(
            provider=implementer_provider,
            reviewer_mode=effective_mode,
        )
    )
    typed["implementer_state_pending"] = is_pending_implementer_state(
        implementer_status=current_session.implementer_status,
        implementer_ack=current_session.implementer_ack,
        implementer_ack_state=current_session.implementer_ack_state,
    )
    return typed


def _live_participant_providers(
    collaboration: CollaborationSessionState | None,
) -> tuple[str, ...]:
    if collaboration is None:
        return ()
    providers: list[str] = []
    for participant in collaboration.participants:
        if not participant.live:
            continue
        if participant.role not in {
            TandemRole.REVIEWER.value,
            TandemRole.IMPLEMENTER.value,
        }:
            continue
        provider = str(participant.provider or participant.agent_id).strip().lower()
        if provider and provider not in providers:
            providers.append(provider)
    return tuple(providers)


def build_review_bridge_state(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: Mapping[str, object],
    overall_state: str,
    current_session: ReviewCurrentSessionState,
    collaboration: CollaborationSessionState | None = None,
    reviewer_runtime: ReviewerRuntimeContract | None = None,
) -> ReviewBridgeState:
    reviewed_hash_current = bridge_liveness.get("reviewed_hash_current")
    review_needed = bridge_liveness.get("review_needed")
    declared_mode = resolve_reported_reviewer_mode(bridge_liveness)
    effective_mode = str(
        bridge_liveness.get("effective_reviewer_mode") or declared_mode
    )
    reviewer_mode = authority_reviewer_mode(declared_mode, effective_mode)
    reviewer_provider = collaboration_provider(
        collaboration,
        role_id="review_agent",
        default=default_provider_for_role(TandemRole.REVIEWER),
    )
    implementer_provider = collaboration_provider(
        collaboration,
        role_id="coding_agent",
        default=default_provider_for_role(TandemRole.IMPLEMENTER),
    )
    return ReviewBridgeState(
        overall_state=overall_state,
        codex_poll_state=str(bridge_liveness.get("codex_poll_state") or "unknown"),
        reviewer_freshness=str(bridge_liveness.get("reviewer_freshness") or "unknown"),
        reviewer_mode=reviewer_mode,
        last_codex_poll_utc=str(
            bridge_liveness.get("last_codex_poll_utc")
            or snapshot.metadata.get("last_codex_poll_utc")
            or ""
        ),
        last_codex_poll_age_seconds=int(
            bridge_liveness.get("last_codex_poll_age_seconds") or 0
        ),
        last_worktree_hash=str(
            snapshot.metadata.get("last_non_audit_worktree_hash") or ""
        ),
        current_instruction=current_session.current_instruction,
        open_findings=current_session.open_findings,
        claude_status=current_session.implementer_status,
        claude_ack=current_session.implementer_ack,
        claude_ack_current=bool(bridge_liveness.get("claude_ack_current")),
        current_instruction_revision=current_session.current_instruction_revision,
        claude_ack_revision=current_session.implementer_ack_revision,
        last_reviewed_scope=current_session.last_reviewed_scope,
        reviewer_poll_state=str(
            bridge_liveness.get("reviewer_poll_state")
            or bridge_liveness.get("codex_poll_state")
            or "unknown"
        ),
        last_reviewer_poll_utc=str(
            bridge_liveness.get("last_reviewer_poll_utc")
            or snapshot.metadata.get("last_codex_poll_utc")
            or ""
        ),
        last_reviewer_poll_age_seconds=int(
            bridge_liveness.get("last_reviewer_poll_age_seconds")
            or bridge_liveness.get("last_codex_poll_age_seconds")
            or 0
        ),
        implementer_status=current_session.implementer_status,
        implementer_ack=current_session.implementer_ack,
        implementer_ack_current=bool(
            bridge_liveness.get("implementer_ack_current")
            or bridge_liveness.get("claude_ack_current")
        ),
        implementer_ack_revision=current_session.implementer_ack_revision,
        launch_truth=str(bridge_liveness.get("launch_truth") or ""),
        effective_reviewer_mode=effective_mode,
        implementer_state_hash=current_session.implementer_state_hash,
        reviewed_hash_current=(
            None if reviewed_hash_current is None else bool(reviewed_hash_current)
        ),
        review_needed=None if review_needed is None else bool(review_needed),
        review_accepted=_compute_review_accepted(
            snapshot,
            reviewer_runtime=reviewer_runtime,
        ),
        head_at_push_time=str(snapshot.metadata.get("head_at_push_time") or "").strip(),
        implementer_completion_stall=bool(
            bridge_liveness.get("implementer_completion_stall")
        ),
        publisher_running=bool(bridge_liveness.get("publisher_running")),
        codex_conductor_active=bool(bridge_liveness.get("codex_conductor_active")),
        claude_conductor_active=bool(bridge_liveness.get("claude_conductor_active")),
        reviewer_capability=build_conductor_capability_state(
            provider=reviewer_provider,
            reviewer_mode=effective_mode,
        ),
        implementer_capability=build_conductor_capability_state(
            provider=implementer_provider,
            reviewer_mode=effective_mode,
        ),
    )


def _compute_review_accepted(
    snapshot: BridgeSnapshot,
    *,
    reviewer_runtime: ReviewerRuntimeContract | None = None,
) -> bool:
    """Compute reviewer-owned acceptance as a projection over reviewer runtime."""
    del snapshot
    if reviewer_runtime is None:
        return False
    return bool(reviewer_runtime.review_acceptance.review_accepted)
