"""Publication ownership resolution for the portable reviewer loop.

Determines which lane (reviewer or implementer) owns the commit/push step
based on control topology and interaction mode. When the reviewer is
local-terminal and the implementer is remote_control, publication belongs
to the implementer through the governed commit/push path.

This module provides the typed decision surface that lets a controller
emit a publication-ready action_request to the correct lane without
chat relay or bridge-prose assumptions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ..runtime.role_profile import TandemRole, default_provider_for_role


# ── Constants ──────────────────────────────────────────────────

OWNER_IMPLEMENTER = "implementer"
OWNER_REVIEWER = "reviewer"
OWNER_BLOCKED = "blocked"

PUBLICATION_ACTION_PUSH = "push"
PUBLICATION_ACTION_COMMIT = "commit"


# ── Decision model ─────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class PublicationOwnershipDecision:
    """Typed decision: which lane executes commit/push."""

    owner: str
    owner_provider: str
    reason: str
    target_sha: str = ""
    action_kind: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


# ── Resolution ─────────────────────────────────────────────────


def resolve_publication_owner(
    *,
    interaction_mode: str,
    topology: str = "",
    reviewer_provider: str = "",
    implementer_provider: str = "",
) -> PublicationOwnershipDecision:
    """Determine who owns commit/push based on topology and interaction mode.

    Rules:
    - remote_control implementer → implementer owns publication
    - local_terminal with single_agent → same agent owns both
    - dual_implementer → blocked (ambiguous ownership)
    - no_live_agents / reviewer_only → blocked
    - default (local_terminal + reviewer present) → reviewer owns
    """
    resolved_reviewer = (
        reviewer_provider
        or default_provider_for_role(TandemRole.REVIEWER)
    )
    resolved_implementer = (
        implementer_provider
        or default_provider_for_role(TandemRole.IMPLEMENTER)
    )

    if interaction_mode == "remote_control":
        return PublicationOwnershipDecision(
            owner=OWNER_IMPLEMENTER,
            owner_provider=resolved_implementer,
            reason="remote_control_implementer_owns_publication",
        )

    if topology == "dual_implementer":
        return PublicationOwnershipDecision(
            owner=OWNER_BLOCKED,
            owner_provider="",
            reason="dual_implementer_publication_ambiguous",
        )

    if topology in {"no_live_agents", "reviewer_only"}:
        return PublicationOwnershipDecision(
            owner=OWNER_BLOCKED,
            owner_provider="",
            reason=f"publication_blocked_topology_{topology}",
        )

    if topology == "implementer_without_reviewer":
        return PublicationOwnershipDecision(
            owner=OWNER_IMPLEMENTER,
            owner_provider=resolved_implementer,
            reason="solo_implementer_owns_publication",
        )

    return PublicationOwnershipDecision(
        owner=OWNER_REVIEWER,
        owner_provider=resolved_reviewer,
        reason="local_reviewer_owns_publication",
    )


# ── Action request builder ─────────────────────────────────────


def build_implementer_publication_request(
    decision: PublicationOwnershipDecision,
    *,
    approved_head_sha: str,
    pipeline_id: str = "",
    reviewer_provider: str = "",
) -> dict[str, object] | None:
    """Build a typed action_request for implementer-owned publication.

    Returns None if the decision does not assign publication to the
    implementer. The caller posts this through the review-channel
    packet system.
    """
    if decision.owner != OWNER_IMPLEMENTER:
        return None

    from_agent = reviewer_provider or default_provider_for_role(TandemRole.REVIEWER)
    return {
        "kind": "action_request",
        "from_agent": from_agent,
        "to_agent": decision.owner_provider,
        "summary": (
            f"Publication authorized: run governed push for {approved_head_sha[:8]}"
        ),
        "body": (
            f"Reviewer accepted commit {approved_head_sha}. "
            "Execute governed publication through "
            "`python3 dev/scripts/devctl.py push --execute`. "
            "This is a typed turn — the implementer lane owns this step."
        ),
        "requested_action": "execute_publication",
        "publication_owner": decision.owner,
        "publication_owner_provider": decision.owner_provider,
        "approved_head_sha": approved_head_sha,
        "pipeline_id": pipeline_id,
    }


def is_duplicate_publication(
    *,
    pending_packets: tuple[dict, ...],
    approved_head_sha: str,
) -> bool:
    """Check if a publication action_request already exists for this SHA."""
    for pkt in pending_packets:
        if not isinstance(pkt, dict):
            continue
        if str(pkt.get("requested_action") or "") != "execute_publication":
            continue
        if str(pkt.get("approved_head_sha") or "") == approved_head_sha:
            return True
    return False
