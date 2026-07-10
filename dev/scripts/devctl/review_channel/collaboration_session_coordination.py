"""Topology and ownership helpers for collaboration-session state."""

from __future__ import annotations

from pathlib import Path

from ..runtime.review_state_models import (
    CollaborationParticipantState,
    DelegatedWorkReceiptState,
    ReviewCurrentSessionState,
)
from ..runtime.role_profile import TandemRole
from ..runtime.scope_path_claims import extract_scope_paths
from ..runtime.work_intake_models import WorkIntakeOwnershipState
from ..runtime.work_intake_ownership import (
    OwnershipPeerContext,
    classify_work_ownership_state,
    dirty_paths_for_repo,
)


def build_collaboration_ownership(
    *,
    repo_root: Path | None,
    current_session: ReviewCurrentSessionState,
    participants: tuple[CollaborationParticipantState, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
    reviewer_mode: str,
    effective_mode: str,
) -> WorkIntakeOwnershipState:
    """Project live work ownership for collaboration/session consumers."""
    scope_paths = _scope_paths(current_session)
    scope_source = _scope_source(current_session, scope_paths=scope_paths)
    dirty_paths = dirty_paths_for_repo(repo_root) if repo_root is not None else ()
    peer_context = OwnershipPeerContext(
        live_agents=_live_agents(participants),
        live_delegated_agents=_live_delegated_agents(delegated_work),
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_mode,
    )
    return classify_work_ownership_state(
        scope_paths=scope_paths,
        scope_source=scope_source,
        dirty_paths=dirty_paths,
        peer_context=peer_context,
    )


def collaboration_topology_mode(
    *,
    reviewer_mode: str,
    participants: tuple[CollaborationParticipantState, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
) -> str:
    """Return the bounded live collaboration topology.

    Per Codex rev_pkt_2298/2313/2346: this returns the typed observed
    topology, NOT the legacy authority/review-gate label. When evidence
    is missing, returns ``"unknown"`` (fail-closed per rev_pkt_2298) so
    consumers don't silently get ``single_agent`` as observed runtime.
    The explicit ``single_agent`` reviewer mode is preserved as a bounded
    topology when no live multi-agent evidence is present; missing mode
    evidence still falls through to ``unknown``.
    """
    requested_budget = sum(
        max(participant.requested_worker_budget or 0, 0)
        for participant in participants
    )
    live_delegated_work = any(receipt.live for receipt in delegated_work)
    if live_delegated_work or requested_budget > 0:
        return "multi_agent_orchestrated"

    live_roles = {
        participant.role for participant in participants if participant.live
    }
    if (
        TandemRole.REVIEWER.value in live_roles
        and TandemRole.IMPLEMENTER.value in live_roles
    ):
        return "dual_agent"

    if reviewer_mode == "active_dual_agent":
        return "dual_agent"

    if reviewer_mode == "single_agent":
        return "single_agent"

    # Per rev_pkt_2298: no observable evidence -> fail-closed to "unknown".
    # Producers that previously returned single_agent as a bare default were
    # the source of operator-facing contradictions Codex flagged in
    # rev_pkt_2326/2346.
    return "unknown"


def work_ownership_mode(ownership: WorkIntakeOwnershipState) -> str:
    """Normalize raw ownership status into a smaller scheduling mode family."""
    if ownership.concurrent_writer_detected:
        return "concurrent_writer_conflict"
    if ownership.status == "scope_unknown_dirty_paths":
        return "scope_unknown"
    if ownership.status == "outside_scope_dirty_paths":
        return "shared_slice"
    return "exclusive_slice"


def _scope_paths(
    current_session: ReviewCurrentSessionState,
) -> tuple[str, ...]:
    return extract_scope_paths(
        current_session.current_instruction,
        current_session.last_reviewed_scope,
    )


def _scope_source(
    current_session: ReviewCurrentSessionState,
    *,
    scope_paths: tuple[str, ...],
) -> str:
    if not scope_paths:
        return ""

    sources: list[str] = []
    if extract_scope_paths(current_session.current_instruction):
        sources.append("current_session.current_instruction")
    if extract_scope_paths(current_session.last_reviewed_scope):
        sources.append("current_session.last_reviewed_scope")
    return ",".join(sources)


def _live_agents(
    participants: tuple[CollaborationParticipantState, ...],
) -> tuple[str, ...]:
    live_agents: list[str] = []
    for participant in participants:
        if not participant.live:
            continue
        agent_id = participant.agent_id or participant.provider
        if agent_id and agent_id not in live_agents:
            live_agents.append(agent_id)
    return tuple(live_agents)


def _live_delegated_agents(
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
) -> tuple[str, ...]:
    live_agents: list[str] = []
    for receipt in delegated_work:
        if not receipt.live:
            continue
        if receipt.agent_id and receipt.agent_id not in live_agents:
            live_agents.append(receipt.agent_id)
    return tuple(live_agents)


__all__ = [
    "build_collaboration_ownership",
    "collaboration_topology_mode",
    "work_ownership_mode",
]
