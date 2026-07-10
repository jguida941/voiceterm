"""Reviewer-duty actor/session identity and conflict classification."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..runtime.review_state_collaboration_models import (
    ActorAuthorityState,
    CollaborationSessionState,
)


@dataclass(frozen=True, slots=True)
class ReviewActorIdentity:
    actor_id: str = ""
    provider: str = ""
    session_id: str = ""
    worktree_identity: str = ""


@dataclass(frozen=True, slots=True)
class ReviewIdentityPair:
    reviewer: ReviewActorIdentity
    mutation: ReviewActorIdentity


@dataclass(frozen=True, slots=True)
class ReviewConflict:
    classification: str
    reasons: tuple[str, ...]


def resolve_review_identities(
    collaboration: CollaborationSessionState | None,
) -> ReviewIdentityPair:
    if collaboration is None:
        return ReviewIdentityPair(
            reviewer=ReviewActorIdentity(),
            mutation=ReviewActorIdentity(),
        )
    authorities = tuple(collaboration.actor_authorities or ())
    return ReviewIdentityPair(
        reviewer=_reviewer_identity(authorities),
        mutation=_mutation_identity(
            authorities,
            mutation_owner=str(getattr(collaboration, "mutation_owner", "") or ""),
        ),
    )


def classify_review_conflict(identities: ReviewIdentityPair) -> ReviewConflict:
    reviewer = identities.reviewer
    mutation = identities.mutation
    if not reviewer.actor_id or not mutation.actor_id:
        return ReviewConflict("unknown", ())
    comparison = _identity_comparison(reviewer, mutation)
    reasons = _base_reasons(comparison)
    if _self_attested(comparison):
        reasons.extend(
            _self_review_reasons(
                same_actor=comparison.same_actor,
                same_provider=comparison.same_provider,
                same_session=comparison.same_session,
            )
        )
        return ReviewConflict("self_attested", tuple(_dedupe(reasons)))
    if comparison.same_provider:
        return ReviewConflict("same_provider_distinct_runtime", tuple(reasons))
    return ReviewConflict("independent", tuple(reasons))


def caller_identity_mismatch(reviewer: ReviewActorIdentity) -> bool:
    caller_agent = str(os.environ.get("DEVCTL_CALLER_AGENT", "")).strip()
    caller_session = str(os.environ.get("DEVCTL_CALLER_SESSION_ID", "")).strip()
    if reviewer.actor_id and caller_agent and caller_agent != reviewer.actor_id:
        return True
    return bool(
        reviewer.session_id
        and caller_session
        and caller_session != reviewer.session_id
    )


@dataclass(frozen=True, slots=True)
class _IdentityComparison:
    same_actor: bool
    same_provider: bool
    same_session: bool
    same_worktree: bool


def _identity_comparison(
    reviewer: ReviewActorIdentity,
    mutation: ReviewActorIdentity,
) -> _IdentityComparison:
    return _IdentityComparison(
        same_actor=_same_identity(reviewer.actor_id, mutation.actor_id),
        same_provider=_same_identity(reviewer.provider, mutation.provider),
        same_session=bool(
            reviewer.session_id
            and mutation.session_id
            and _same_identity(reviewer.session_id, mutation.session_id)
        ),
        same_worktree=bool(
            reviewer.worktree_identity
            and mutation.worktree_identity
            and reviewer.worktree_identity == mutation.worktree_identity
        ),
    )


def _base_reasons(comparison: _IdentityComparison) -> list[str]:
    reasons: list[str] = []
    if comparison.same_session:
        reasons.append("same_session")
    if comparison.same_worktree:
        reasons.append("same_worktree")
    return reasons


def _self_attested(comparison: _IdentityComparison) -> bool:
    distinct_runtime = not comparison.same_session and not comparison.same_worktree
    if comparison.same_actor and not distinct_runtime:
        return True
    if comparison.same_provider and not distinct_runtime:
        return True
    return False


def _self_review_reasons(
    *,
    same_actor: bool,
    same_provider: bool,
    same_session: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if same_actor:
        reasons.append("same_actor")
    if same_provider and not same_actor:
        reasons.append("same_provider_without_runtime_separation")
    if same_session:
        reasons.append("same_session")
    return tuple(reasons)


def _reviewer_identity(
    authorities: tuple[ActorAuthorityState, ...],
) -> ReviewActorIdentity:
    for authority in authorities:
        if str(authority.role or "").lower() == "reviewer":
            return _actor_identity(authority)
    return ReviewActorIdentity()


def _mutation_identity(
    authorities: tuple[ActorAuthorityState, ...],
    *,
    mutation_owner: str,
) -> ReviewActorIdentity:
    for authority in authorities:
        actor_id = str(authority.actor_id or authority.provider or "")
        provider = str(authority.provider or authority.actor_id or "")
        role = str(authority.role or "").lower()
        if (
            _same_identity(actor_id, mutation_owner)
            or _same_identity(provider, mutation_owner)
            or role == "implementer"
        ):
            return _actor_identity(authority)
    return ReviewActorIdentity()


def _actor_identity(authority: ActorAuthorityState) -> ReviewActorIdentity:
    return ReviewActorIdentity(
        actor_id=str(authority.actor_id or authority.provider or ""),
        provider=str(authority.provider or authority.actor_id or ""),
        session_id=str(getattr(authority, "session_id", "") or ""),
        worktree_identity=str(getattr(authority, "worktree_identity", "") or ""),
    )


def _same_identity(left: str, right: str) -> bool:
    return bool(left and right and left.strip().lower() == right.strip().lower())


def _dedupe(values: list[str]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return tuple(result)


__all__ = [
    "ReviewConflict",
    "ReviewIdentityPair",
    "caller_identity_mismatch",
    "classify_review_conflict",
    "resolve_review_identities",
]
