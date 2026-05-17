"""Typed reviewer-runtime contract builders and projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from ..runtime.conductor_capability import authority_reviewer_mode
from ..runtime.review_state_models import (
    CollaborationSessionState, RecoveryAssessmentState, ReviewCurrentSessionState,
)
from ..runtime.reviewer_gate_logic import (
    ReviewerRuntimeBlockInputs,
    reviewer_runtime_block_state,
)
from ..runtime.session_posture import build_session_posture
from ..runtime.reviewer_runtime_models import (
    AgentRuntimeClock, ReviewerAcceptanceState, ReviewerDutyProof,
    ReviewerLastPollState, ReviewerRuntimeContract,
    build_agent_runtime_clock, build_inbox_observation_state,
    build_packet_attention_state, derive_wake_evidence_for_actor,
)
from .bridge_validation_acceptance import review_acceptance_projection
from .handoff import BridgeSnapshot
from .peer_liveness import reviewer_mode_is_active
from .peer_recovery import STALE_PEER_RECOVERY
from .reviewer_runtime_duty_proof import build_reviewer_duty_proof
from .reviewer_runtime_doctor import build_reviewer_doctor_surface
from .reviewer_runtime_rollover import resolve_reviewer_rollover_state
from .reviewer_runtime_session_owner import (
    conductor_visibility,
    resolve_remote_control_attachment,
    resolve_reviewer_session_owner,
)


@dataclass(frozen=True)
class ReviewerRuntimeInputs:
    """Grouped inputs for building the reviewer-runtime authority contract."""

    snapshot: BridgeSnapshot | None
    bridge_liveness: Mapping[str, object]
    current_session: ReviewCurrentSessionState
    recovery_assessment: RecoveryAssessmentState | None = None
    attention: Mapping[str, object] | None = None
    collaboration: CollaborationSessionState | None = None
    session_output_root: Path | None = None
    rollover_dir: Path | None = None
    bridge_text: str | None = None
    rollover_state_override: Mapping[str, object] | None = None
    recovery_action_override: str | None = None
    prior_review_state: Mapping[str, object] | None = None
    repo_root: Path | None = None
    operator_interaction_mode: str = ""
    agent_mind: Mapping[str, object] | None = None
    reviewer_accepted_implementer_state_hash_override: str | None = None
    # Per rev_pkt_2498 (3): typed event log enables wake-evidence derivation.
    # Optional so callers without events still build a valid contract; when events ARE
    # passed, _packet_attention_for_caller derives latest_relevant_event_id
    # from events filtered by actor_id/session_id.
    events: tuple[Mapping[str, object], ...] = ()


@dataclass(frozen=True)
class PublishClearInputs:
    reviewer_mode: str
    effective_reviewer_mode: str
    reviewer_freshness: str
    stale_reason: str
    review_accepted: bool
    rollover_ack_pending: bool
    duty_proof: ReviewerDutyProof


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
    effective_mode = str(
        bridge_liveness.get("effective_reviewer_mode")
        or bridge_liveness.get("reviewer_mode")
        or "single_agent"
    )
    reviewer_mode = authority_reviewer_mode(
        str(bridge_liveness.get("reviewer_mode") or ""),
        effective_mode,
    )
    reviewer_freshness = str(bridge_liveness.get("reviewer_freshness") or "unknown")
    stale_reason = _stale_reason(
        recovery_assessment=inputs.recovery_assessment,
        attention=inputs.attention,
    )
    review_acceptance = _review_acceptance_state(
        snapshot=inputs.snapshot,
        bridge_liveness=bridge_liveness,
        current_session=inputs.current_session,
        prior_review_state=inputs.prior_review_state,
        reviewer_accepted_implementer_state_hash_override=inputs.reviewer_accepted_implementer_state_hash_override,
    )
    implementer_ack_current = inputs.current_session.implementer_ack_state == "current"
    implementation_blocked, implementation_block_reason = reviewer_runtime_block_state(
        ReviewerRuntimeBlockInputs(
            reviewer_mode=reviewer_mode,
            effective_reviewer_mode=effective_mode,
            implementer_ack_current=implementer_ack_current,
            attention_status=stale_reason,
            current_instruction=inputs.current_session.current_instruction,
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
    remote_control_attachment = resolve_remote_control_attachment(
        repo_root=inputs.repo_root, session_output_root=inputs.session_output_root
    )
    duty_proof = build_reviewer_duty_proof(
        bridge_liveness=bridge_liveness,
        collaboration=inputs.collaboration,
        agent_mind=inputs.agent_mind,
        stale_reason=stale_reason,
    )
    return ReviewerRuntimeContract(
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_mode,
        reviewer_freshness=reviewer_freshness,
        stale_reason=stale_reason,
        conductor_visibility=(
            str(bridge_liveness.get("conductor_visibility") or "").strip()
            or conductor_visibility(session_output_root=inputs.session_output_root)
        ),
        implementer_ack_current=implementer_ack_current,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        last_poll=ReviewerLastPollState(
            last_codex_poll_utc=str(bridge_liveness.get("last_codex_poll_utc") or ""),
            last_codex_poll_age_seconds=int(
                bridge_liveness.get("last_codex_poll_age_seconds") or 0
            ),
            last_reviewer_poll_utc=str(
                bridge_liveness.get("last_reviewer_poll_utc")
                or bridge_liveness.get("last_codex_poll_utc")
                or ""
            ),
            last_reviewer_poll_age_seconds=int(
                bridge_liveness.get("last_reviewer_poll_age_seconds")
                or bridge_liveness.get("last_codex_poll_age_seconds")
                or 0
            ),
        ),
        rollover=rollover,
        session_owner=resolve_reviewer_session_owner(
            collaboration=inputs.collaboration, session_output_root=inputs.session_output_root
        ),
        recovery_action_allowed=_recovery_action_allowed(
            recovery_assessment=inputs.recovery_assessment,
            attention=inputs.attention,
            override=inputs.recovery_action_override,
        ),
        review_acceptance=review_acceptance,
        publish_clear=_publish_clear(
            PublishClearInputs(
                reviewer_mode=reviewer_mode,
                effective_reviewer_mode=effective_mode,
                reviewer_freshness=reviewer_freshness,
                stale_reason=stale_reason,
                rollover_ack_pending=rollover.ack_pending,
                review_accepted=review_acceptance.review_accepted,
                duty_proof=duty_proof,
            )
        ),
        remote_control_attachment=remote_control_attachment,
        session_posture=build_session_posture(
            interaction_mode=inputs.operator_interaction_mode,
            reviewer_mode=reviewer_mode,
            effective_reviewer_mode=effective_mode,
            collaboration=inputs.collaboration,
            remote_control_attachment=remote_control_attachment,
            agent_mind=inputs.agent_mind,
        ),
        duty_proof=duty_proof,
        inbox_observation=_inbox_observation_for_caller(
            bridge_liveness=bridge_liveness,
            collaboration=inputs.collaboration,
            agent_mind=inputs.agent_mind,
        ),
        agent_runtime_clock=_agent_runtime_clock_for_runtime(
            bridge_liveness=bridge_liveness,
            events=inputs.events,
        ),
        packet_attention=_packet_attention_for_caller(
            bridge_liveness=bridge_liveness,
            agent_mind=inputs.agent_mind,
            events=inputs.events,
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
    bridge_acceptance = None
    if snapshot is not None:
        current_verdict, open_findings, review_accepted = review_acceptance_projection(
            snapshot
        )
        bridge_acceptance = ReviewerAcceptanceState(
            current_verdict=current_verdict,
            open_findings=open_findings,
            review_accepted=review_accepted,
            reviewer_accepted_implementer_state_hash=accepted_impl_hash,
        )
    if (
        reviewer_accepted_implementer_state_hash_override
        and bridge_acceptance is not None
    ):
        return bridge_acceptance
    if _fresh_bridge_checkpoint_overrides_prior(
        bridge_acceptance=bridge_acceptance,
        bridge_liveness=bridge_liveness,
    ):
        assert bridge_acceptance is not None
        return bridge_acceptance
    prior_acceptance = _prior_review_acceptance_state(prior_review_state)
    if prior_acceptance is not None:
        return ReviewerAcceptanceState(
            current_verdict=prior_acceptance.current_verdict,
            open_findings=prior_acceptance.open_findings
            or current_session.open_findings
            or str(bridge_liveness.get("open_findings") or ""),
            review_accepted=prior_acceptance.review_accepted,
            reviewer_accepted_implementer_state_hash=(
                accepted_impl_hash
                or prior_acceptance.reviewer_accepted_implementer_state_hash
            ),
        )
    if bridge_acceptance is not None:
        return bridge_acceptance
    open_findings = current_session.open_findings or str(
        bridge_liveness.get("open_findings") or ""
    )
    return ReviewerAcceptanceState(
        current_verdict="",
        open_findings=open_findings,
        review_accepted=bool(bridge_liveness.get("review_accepted")),
        reviewer_accepted_implementer_state_hash=accepted_impl_hash,
    )


def _fresh_bridge_checkpoint_overrides_prior(
    *,
    bridge_acceptance: ReviewerAcceptanceState | None,
    bridge_liveness: Mapping[str, object],
) -> bool:
    return bool(
        bridge_acceptance is not None
        and str(bridge_liveness.get("last_checkpoint_action") or "").strip()
        == "reviewer-checkpoint"
        and not bool(bridge_liveness.get("review_needed"))
        and bridge_liveness.get("reviewed_hash_current") is not False
        and (
            bridge_acceptance.current_verdict.strip()
            or bridge_acceptance.open_findings.strip()
        )
    )


def _prior_review_acceptance_state(
    prior_review_state: Mapping[str, object] | None,
) -> ReviewerAcceptanceState | None:
    prior_payload = (
        prior_review_state if isinstance(prior_review_state, Mapping) else {}
    )
    review_state = prior_payload.get("review_state")
    if not isinstance(review_state, Mapping):
        review_state = prior_payload
    reviewer_runtime = review_state.get("reviewer_runtime")
    if not isinstance(reviewer_runtime, Mapping):
        return None
    review_acceptance = reviewer_runtime.get("review_acceptance")
    if not isinstance(review_acceptance, Mapping):
        return None
    return ReviewerAcceptanceState(
        current_verdict=str(review_acceptance.get("current_verdict") or "").strip(),
        open_findings=str(review_acceptance.get("open_findings") or "").strip(),
        review_accepted=bool(review_acceptance.get("review_accepted", False)),
        reviewer_accepted_implementer_state_hash=str(
            review_acceptance.get("reviewer_accepted_implementer_state_hash") or ""
        ).strip(),
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
    nested_review_state = review_state.get("review_state")
    if isinstance(nested_review_state, Mapping):
        review_state = nested_review_state
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
    recovery_assessment: RecoveryAssessmentState | None,
    attention: Mapping[str, object] | None,
    override: str | None,
) -> str:
    if override is not None:
        return override.strip()
    if recovery_assessment is not None:
        command = str(recovery_assessment.decision.command or "").strip()
        if command:
            return command
    attention_status = str((attention or {}).get("status") or "").strip()
    recovery = STALE_PEER_RECOVERY.get(attention_status)
    if not isinstance(recovery, dict):
        return ""
    return str(recovery.get("recommended_command") or "").strip()


def _publish_clear(inputs: PublishClearInputs) -> bool:
    if not reviewer_mode_is_active(inputs.reviewer_mode):
        return True
    if not reviewer_mode_is_active(inputs.effective_reviewer_mode):
        return False
    if inputs.duty_proof.review_conflict_class == "self_attested":
        return False
    return (
        inputs.review_accepted
        and inputs.reviewer_freshness == "fresh"
        and not inputs.stale_reason
        and not inputs.rollover_ack_pending
    )


def _stale_reason(
    *,
    recovery_assessment: RecoveryAssessmentState | None,
    attention: Mapping[str, object] | None,
) -> str:
    status = (
        str(recovery_assessment.diagnosis.status or "").strip()
        if recovery_assessment is not None
        else str((attention or {}).get("status") or "").strip()
    )
    if status in {"", "healthy"}:
        return ""
    return status


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _inbox_observation_for_caller(
    *,
    bridge_liveness: Mapping[str, object],
    collaboration: CollaborationSessionState | None,
    agent_mind: Mapping[str, object] | None,
):
    """Build typed inbox observation for the env-declared caller.

    Per rev_pkt_2486 Scope 3 + Scope 5: surface pivot_required as a machine-
    readable signal threaded through ReviewerRuntimeContract, scoped to the
    current caller's actor_id/session_id when env declares them. Ambiguous
    actor_id (no env, no typed authority match) fails closed via
    actor_identity_ambiguous reason inside the builder.
    """
    import os as _os

    actor_id = str(_os.environ.get("DEVCTL_CALLER_AGENT", "")).strip()
    session_id = str(_os.environ.get("DEVCTL_CALLER_SESSION_ID", "")).strip()
    last_inbox_event_id = str(
        bridge_liveness.get("last_inbox_event_id")
        or bridge_liveness.get("last_packet_event_id")
        or ""
    )
    last_inbox_event_at_utc = str(
        bridge_liveness.get("last_inbox_event_at_utc")
        or bridge_liveness.get("last_codex_poll_utc")
        or ""
    )
    last_inbox_observed_event_id = str(
        (agent_mind or {}).get("last_inbox_observed_event_id") or ""
    )
    last_inbox_observed_at_utc = str(
        (agent_mind or {}).get("last_inbox_observed_at_utc") or ""
    )
    pending_packet_count = int(
        _mapping(bridge_liveness.get("pending_packet_count")).get("total")  # type: ignore[arg-type]
        or bridge_liveness.get("pending_packet_count")
        or 0
    )
    superseded_packet_id = str(
        bridge_liveness.get("superseded_packet_id") or ""
    )
    return build_inbox_observation_state(
        actor_id=actor_id,
        session_id=session_id,
        last_inbox_event_id=last_inbox_event_id,
        last_inbox_event_at_utc=last_inbox_event_at_utc,
        last_inbox_observed_event_id=last_inbox_observed_event_id,
        last_inbox_observed_at_utc=last_inbox_observed_at_utc,
        pending_packet_count=pending_packet_count,
        superseded_packet_id=superseded_packet_id,
    )


def _agent_runtime_clock_for_runtime(
    *,
    bridge_liveness: Mapping[str, object],
    events: "tuple[Mapping[str, object], ...]" = (),
) -> AgentRuntimeClock:
    """Per rev_pkt_2498 (1) + rev_pkt_2550 (Plan 4.1 Scope 1): build the typed
    shared runtime clock from the reduced event log when available, with
    bridge_liveness signals as compatibility fallback. The event-log path is
    authoritative because it lets both agents reason over the same monotonic
    rev_evt_NNNN cursor without depending on bridge.md.
    """
    event_id = ""
    event_at_utc = ""
    if events:
        for event in reversed(events):
            if not isinstance(event, Mapping):
                continue
            candidate_id = str(event.get("event_id") or "").strip()
            if candidate_id:
                event_id = candidate_id
                # Events on disk use ``timestamp_utc``; reviewer-authority
                # events emitted via the inline emit helper use ``timestamp``.
                # Accept both so the runtime clock works regardless of source.
                event_at_utc = str(
                    event.get("timestamp_utc")
                    or event.get("timestamp")
                    or ""
                ).strip()
                break
    if not event_id:
        event_id = str(
            bridge_liveness.get("last_inbox_event_id")
            or bridge_liveness.get("last_packet_event_id")
            or ""
        )
        event_at_utc = str(
            bridge_liveness.get("last_inbox_event_at_utc")
            or bridge_liveness.get("last_codex_poll_utc")
            or ""
        )
    cadence_seconds = int(bridge_liveness.get("cadence_seconds") or 0)
    if event_id and not cadence_seconds:
        cadence_seconds = 30
    last_published_at_utc = str(
        bridge_liveness.get("last_published_at_utc") or ""
    )
    if event_at_utc and not last_published_at_utc:
        last_published_at_utc = event_at_utc
    snapshot_id = str(bridge_liveness.get("snapshot_id") or "")
    if event_id and not snapshot_id:
        snapshot_id = f"agent-runtime-clock:{event_id}"
    return build_agent_runtime_clock(
        source_latest_event_id=event_id,
        source_latest_event_at_utc=event_at_utc,
        cadence_seconds=cadence_seconds,
        last_published_at_utc=last_published_at_utc,
        snapshot_id=snapshot_id,
    )


def _packet_attention_for_caller(
    *,
    bridge_liveness: Mapping[str, object],
    agent_mind: Mapping[str, object] | None,
    events: "tuple[Mapping[str, object], ...]" = (),
):
    """Per rev_pkt_2498 (2,4): build typed PacketAttentionState for the
    env-declared caller. Reads observed-event-id from agent_mind (the
    actor's own claim of what it has seen) and derives wake_required +
    pivot_required + stale_reason. Composes with rev_pkt_2470/2476
    fail-closed semantics on ambiguous actor identity.
    """
    import os as _os

    actor_id = str(_os.environ.get("DEVCTL_CALLER_AGENT", "")).strip()
    session_id = str(_os.environ.get("DEVCTL_CALLER_SESSION_ID", "")).strip()
    # Per rev_pkt_2498 (3): when events are provided, derive the
    # latest_inbox_event_id from typed event-log filtered by actor identity.
    # This produces a per-actor_session view rather than a global cursor —
    # dashboard-claude and coder-claude see different latest-relevant events
    # when target_role/target_session_id discriminators are present.
    wake_evidence = derive_wake_evidence_for_actor(
        events=list(events),
        actor_id=actor_id,
        session_id=session_id,
    ) if events else None
    latest_inbox_event_id = str(
        (wake_evidence.latest_relevant_event_id if wake_evidence else "")
        or bridge_liveness.get("last_inbox_event_id")
        or bridge_liveness.get("last_packet_event_id")
        or ""
    )
    latest_attention_packet_id = str(
        (wake_evidence.latest_relevant_packet_id if wake_evidence else "")
        or bridge_liveness.get("latest_attention_packet_id")
        or bridge_liveness.get("canonical_active_packet_id")
        or ""
    )
    latest_attention_changed_at_utc = str(
        (wake_evidence.latest_relevant_event_at_utc if wake_evidence else "")
        or bridge_liveness.get("latest_attention_changed_at_utc")
        or ""
    )
    last_observed_event_id = str(
        (agent_mind or {}).get("last_inbox_observed_event_id") or ""
    )
    last_observed_at_utc = str(
        (agent_mind or {}).get("last_inbox_observed_at_utc") or ""
    )
    pending_packet_count = int(
        _mapping(bridge_liveness.get("pending_packet_count")).get("total")  # type: ignore[arg-type]
        or bridge_liveness.get("pending_packet_count")
        or 0
    )
    superseded_packet_id = str(
        bridge_liveness.get("superseded_packet_id") or ""
    )
    return build_packet_attention_state(
        observation_actor_id=actor_id,
        observation_session_id=session_id,
        latest_inbox_event_id=latest_inbox_event_id,
        latest_attention_packet_id=latest_attention_packet_id,
        latest_attention_changed_at_utc=latest_attention_changed_at_utc,
        last_observed_event_id=last_observed_event_id,
        last_observed_at_utc=last_observed_at_utc,
        pending_packet_count=pending_packet_count,
        superseded_packet_id=superseded_packet_id,
    )
