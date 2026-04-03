"""Typed reviewer-runtime contract builders and projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from ..runtime.review_state_models import (
    CollaborationSessionState,
    ReviewCurrentSessionState,
)
from ..runtime.reviewer_runtime_models import (
    ReviewerAcceptanceState,
    ReviewerLastPollState,
    ReviewerRuntimeContract,
)
from ..runtime.reviewer_gate_logic import (
    ReviewerRuntimeBlockInputs,
    reviewer_runtime_block_state,
)
from .bridge_validation_acceptance import review_acceptance_projection
from .handoff import BridgeSnapshot
from .peer_liveness import reviewer_mode_is_active
from .peer_recovery import STALE_PEER_RECOVERY
from .reviewer_runtime_doctor import build_reviewer_doctor_surface
from .reviewer_runtime_rollover import resolve_reviewer_rollover_state
from .reviewer_runtime_session_owner import resolve_reviewer_session_owner


@dataclass(frozen=True)
class ReviewerRuntimeInputs:
    """Grouped inputs for building the reviewer-runtime authority contract."""

    snapshot: BridgeSnapshot | None
    bridge_liveness: Mapping[str, object]
    current_session: ReviewCurrentSessionState
    attention: Mapping[str, object] | None = None
    collaboration: CollaborationSessionState | None = None
    session_output_root: Path | None = None
    rollover_dir: Path | None = None
    bridge_text: str | None = None
    rollover_state_override: Mapping[str, object] | None = None
    recovery_action_override: str | None = None
    prior_review_state: Mapping[str, object] | None = None
    reviewer_accepted_implementer_state_hash_override: str | None = None


def reviewer_runtime_contract_to_dict(
    contract: ReviewerRuntimeContract | None,
) -> dict[str, object] | None:
    """Convert a reviewer-runtime contract into report-friendly JSON."""
    if contract is None:
        return None
    return asdict(contract)


def build_reviewer_runtime_contract(
    inputs: ReviewerRuntimeInputs,
) -> ReviewerRuntimeContract:
    """Build the reviewer lifecycle owner from typed review-channel inputs."""
    bridge_liveness = inputs.bridge_liveness
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "single_agent")
    effective_mode = str(
        bridge_liveness.get("effective_reviewer_mode") or reviewer_mode
    )
    reviewer_freshness = str(
        bridge_liveness.get("reviewer_freshness") or "unknown"
    )
    stale_reason = _stale_reason(inputs.attention)
    review_acceptance = _review_acceptance_state(
        snapshot=inputs.snapshot,
        bridge_liveness=bridge_liveness,
        current_session=inputs.current_session,
        prior_review_state=inputs.prior_review_state,
        reviewer_accepted_implementer_state_hash_override=(
            inputs.reviewer_accepted_implementer_state_hash_override
        ),
    )
    implementer_ack_current = inputs.current_session.implementer_ack_state == "current"
    implementation_blocked, implementation_block_reason = reviewer_runtime_block_state(
        ReviewerRuntimeBlockInputs(
            reviewer_mode=reviewer_mode,
            effective_reviewer_mode=effective_mode,
            implementer_ack_current=implementer_ack_current,
            attention_status=stale_reason,
            implementer_status=inputs.current_session.implementer_status,
            implementer_ack=inputs.current_session.implementer_ack,
            implementer_ack_state=inputs.current_session.implementer_ack_state,
        )
    )
    rollover = resolve_reviewer_rollover_state(
        rollover_dir=inputs.rollover_dir,
        bridge_text=inputs.bridge_text,
        attention=inputs.attention,
        override=inputs.rollover_state_override,
    )
    return ReviewerRuntimeContract(
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_mode,
        reviewer_freshness=reviewer_freshness,
        stale_reason=stale_reason,
        implementer_ack_current=implementer_ack_current,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        last_poll=ReviewerLastPollState(
            last_codex_poll_utc=str(bridge_liveness.get("last_codex_poll_utc") or ""),
            last_codex_poll_age_seconds=int(
                bridge_liveness.get("last_codex_poll_age_seconds") or 0
            ),
        ),
        rollover=rollover,
        session_owner=resolve_reviewer_session_owner(
            collaboration=inputs.collaboration,
            session_output_root=inputs.session_output_root,
        ),
        recovery_action_allowed=_recovery_action_allowed(
            attention=inputs.attention,
            override=inputs.recovery_action_override,
        ),
        review_acceptance=review_acceptance,
        publish_clear=_publish_clear(
            reviewer_mode=reviewer_mode,
            effective_reviewer_mode=effective_mode,
            reviewer_freshness=reviewer_freshness,
            stale_reason=stale_reason,
            rollover=rollover,
            review_accepted=review_acceptance.review_accepted,
        ),
    )


def _review_acceptance_state(
    *,
    snapshot: BridgeSnapshot | None,
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    prior_review_state: Mapping[str, object] | None,
    reviewer_accepted_implementer_state_hash_override: str | None,
) -> ReviewerAcceptanceState:
    accepted_impl_hash = _accepted_implementer_state_hash(
        prior_review_state=prior_review_state,
        reviewer_accepted_implementer_state_hash_override=(
            reviewer_accepted_implementer_state_hash_override
        ),
    )
    if snapshot is not None:
        current_verdict, open_findings, review_accepted = review_acceptance_projection(
            snapshot
        )
        return ReviewerAcceptanceState(
            current_verdict=current_verdict,
            open_findings=open_findings,
            review_accepted=review_accepted,
            reviewer_accepted_implementer_state_hash=accepted_impl_hash,
        )
    open_findings = (
        current_session.open_findings
        or str(bridge_liveness.get("open_findings") or "")
    )
    return ReviewerAcceptanceState(
        current_verdict="",
        open_findings=open_findings,
        review_accepted=bool(bridge_liveness.get("review_accepted")),
        reviewer_accepted_implementer_state_hash=accepted_impl_hash,
    )


def _accepted_implementer_state_hash(
    *,
    prior_review_state: Mapping[str, object] | None,
    reviewer_accepted_implementer_state_hash_override: str | None,
) -> str:
    override = (reviewer_accepted_implementer_state_hash_override or "").strip()
    if override:
        return override
    review_state = prior_review_state if isinstance(prior_review_state, Mapping) else {}
    reviewer_runtime = review_state.get("reviewer_runtime")
    if not isinstance(reviewer_runtime, Mapping):
        return ""
    review_acceptance = reviewer_runtime.get("review_acceptance")
    if not isinstance(review_acceptance, Mapping):
        return ""
    return str(
        review_acceptance.get("reviewer_accepted_implementer_state_hash") or ""
    ).strip()


def _recovery_action_allowed(
    *,
    attention: Mapping[str, object] | None,
    override: str | None,
) -> str:
    if override is not None:
        return override.strip()
    attention_status = str((attention or {}).get("status") or "").strip()
    recovery = STALE_PEER_RECOVERY.get(attention_status)
    if not isinstance(recovery, dict):
        return ""
    return str(recovery.get("recommended_command") or "").strip()


def _publish_clear(
    *,
    reviewer_mode: str,
    effective_reviewer_mode: str,
    reviewer_freshness: str,
    stale_reason: str,
    review_accepted: bool,
    rollover: ReviewerRolloverState,
) -> bool:
    if not reviewer_mode_is_active(reviewer_mode):
        return True
    if not reviewer_mode_is_active(effective_reviewer_mode):
        return False
    return (
        review_accepted
        and reviewer_freshness == "fresh"
        and not stale_reason
        and not rollover.ack_pending
    )


def _stale_reason(attention: Mapping[str, object] | None) -> str:
    status = str((attention or {}).get("status") or "").strip()
    if status in {"", "healthy"}:
        return ""
    return status
