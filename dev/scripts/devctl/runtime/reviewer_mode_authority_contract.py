"""Typed authority contract resolving reviewer_mode overwrite TOCTOU race.

Chronic defect (rev_pkt_1335 family): three sources (`launch_authority.py:265-268`
and six overwrite sites in `collaboration_session.py`) silently promote
`effective_mode` over `declared_mode` without typed transition evidence.

This contract makes the authority decision typed and inspectable:
the *declared* mode remains authority unless a transition is accompanied
by typed evidence references that justify promoting an `effective_mode`.

Closure proof composition expects callers to route through
`resolve_reviewer_mode_authority()` instead of overwriting directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .reviewer_mode import (
    ACTIVE_REVIEWER_MODES,
    ReviewerMode,
    normalize_reviewer_mode,
)


_AUTHORIZED_TRANSITIONS: frozenset[tuple[ReviewerMode, ReviewerMode]] = frozenset(
    {
        # Activation transitions require typed evidence (handshake / launch receipt).
        (ReviewerMode.TOOLS_ONLY, ReviewerMode.ACTIVE_DUAL_AGENT),
        (ReviewerMode.TOOLS_ONLY, ReviewerMode.SINGLE_AGENT),
        (ReviewerMode.SINGLE_AGENT, ReviewerMode.ACTIVE_DUAL_AGENT),
        # Deactivation transitions require typed evidence (stop / pause receipt).
        (ReviewerMode.ACTIVE_DUAL_AGENT, ReviewerMode.SINGLE_AGENT),
        (ReviewerMode.ACTIVE_DUAL_AGENT, ReviewerMode.PAUSED),
        (ReviewerMode.ACTIVE_DUAL_AGENT, ReviewerMode.OFFLINE),
        (ReviewerMode.SINGLE_AGENT, ReviewerMode.PAUSED),
        (ReviewerMode.SINGLE_AGENT, ReviewerMode.OFFLINE),
        (ReviewerMode.PAUSED, ReviewerMode.OFFLINE),
        (ReviewerMode.PAUSED, ReviewerMode.TOOLS_ONLY),
        (ReviewerMode.OFFLINE, ReviewerMode.TOOLS_ONLY),
    }
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class ReviewerModeAuthorityState:
    """Typed reviewer-mode authority decision with composed evidence refs."""

    declared_mode: ReviewerMode
    effective_mode: ReviewerMode
    authority_source: str
    transitioned_at_utc: str
    transition_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    contract_id: str = "ReviewerModeAuthorityContract"
    schema_version: int = 1


def is_transition_authorized(
    from_mode: ReviewerMode,
    to_mode: ReviewerMode,
    evidence_refs: tuple[str, ...],
) -> bool:
    """Return True when transition has both an allowed edge and typed evidence."""
    if from_mode == to_mode:
        return True
    if (from_mode, to_mode) not in _AUTHORIZED_TRANSITIONS:
        return False
    return any(str(ref).strip() for ref in evidence_refs)


def resolve_reviewer_mode_authority(
    declared: object,
    current_effective: object,
    *,
    evidence_refs: tuple[str, ...] = (),
    default: ReviewerMode = ReviewerMode.TOOLS_ONLY,
    observed_at_utc: str | None = None,
) -> ReviewerModeAuthorityState:
    """Resolve typed reviewer-mode authority without silent overwrite.

    The declared mode is authoritative unless a transition to the proposed
    `current_effective` carries typed evidence (handshake, launch receipt,
    bypass receipt, etc.). Without typed evidence the effective mode is
    pinned to the declared mode and the authority source records the
    fallback for auditability.
    """
    declared_mode = normalize_reviewer_mode(declared, default=default)
    proposed_effective = normalize_reviewer_mode(
        current_effective or declared, default=declared_mode
    )
    refs = tuple(str(r).strip() for r in evidence_refs if str(r).strip())
    timestamp = observed_at_utc or _utcnow_iso()

    if proposed_effective == declared_mode:
        return ReviewerModeAuthorityState(
            declared_mode=declared_mode,
            effective_mode=declared_mode,
            authority_source="declared_mode",
            transitioned_at_utc=timestamp,
            transition_evidence_refs=refs,
        )

    if is_transition_authorized(declared_mode, proposed_effective, refs):
        return ReviewerModeAuthorityState(
            declared_mode=declared_mode,
            effective_mode=proposed_effective,
            authority_source="authorized_transition",
            transitioned_at_utc=timestamp,
            transition_evidence_refs=refs,
        )

    # Unauthorized transition: fall back to declared, record the rejection.
    return ReviewerModeAuthorityState(
        declared_mode=declared_mode,
        effective_mode=declared_mode,
        authority_source="declared_mode_fallback_unauthorized_transition",
        transitioned_at_utc=timestamp,
        transition_evidence_refs=refs,
    )


def authoritative_effective_mode(
    declared: object,
    current_effective: object,
    *,
    evidence_refs: tuple[str, ...] = (),
    default: ReviewerMode = ReviewerMode.TOOLS_ONLY,
) -> str:
    """Return the typed authoritative effective mode string for runtime consumers."""
    return resolve_reviewer_mode_authority(
        declared,
        current_effective,
        evidence_refs=evidence_refs,
        default=default,
    ).effective_mode.value


def effective_mode_is_active(state: ReviewerModeAuthorityState) -> bool:
    """Return True when the resolved effective mode is in the active set."""
    return state.effective_mode in ACTIVE_REVIEWER_MODES
