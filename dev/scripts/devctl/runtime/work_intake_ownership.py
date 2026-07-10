"""Typed slice-ownership helpers for startup work-intake."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .dirty_path_filter import (
    ignored_dirty_path_prefixes,
    path_is_ignored_for_dirty_paths,
)
from .review_state_models import ReviewState
from .scope_path_claims import extract_scope_paths, path_matches_scope_claim
from .vcs import run_git_capture
from .work_intake_models import WorkIntakeOwnershipState

_MAX_SCOPE_PATHS = 1
_MAX_DIRTY_PATHS = 1
_MAX_IN_SCOPE_DIRTY_PATHS = 1
_MAX_OUTSIDE_SCOPE_DIRTY_PATHS = 1


@dataclass(frozen=True, slots=True)
class OwnershipPeerContext:
    live_agents: tuple[str, ...] = ()
    live_delegated_agents: tuple[str, ...] = ()
    reviewer_mode: str = ""
    effective_reviewer_mode: str = ""


def build_work_intake_ownership_state(
    *,
    repo_root: Path,
    review_state: ReviewState | None,
) -> WorkIntakeOwnershipState:
    """Classify current dirty paths against the claimed review slice."""
    dirty_paths = dirty_paths_for_repo(repo_root)
    scope_paths, scope_source = _claimed_scope_paths(review_state)
    peer_context = OwnershipPeerContext(
        live_agents=_live_agent_ids(review_state),
        live_delegated_agents=_live_delegated_agent_ids(review_state),
        reviewer_mode=(
            review_state.bridge.reviewer_mode if review_state is not None else ""
        ),
        effective_reviewer_mode=(
            review_state.bridge.effective_reviewer_mode
            if review_state is not None
            else ""
        ),
    )
    return classify_work_ownership_state(
        scope_paths=scope_paths,
        scope_source=scope_source,
        dirty_paths=dirty_paths,
        peer_context=peer_context,
    )


def _claimed_scope_paths(
    review_state: ReviewState | None,
) -> tuple[tuple[str, ...], str]:
    if review_state is None:
        return (), ""

    scope_paths: list[str] = []
    sources: list[str] = []
    current_session = review_state.current_session
    review_candidate = review_state.review_candidate

    if (
        review_candidate is not None
        and review_candidate.scope_paths
        and (
            not current_session.current_instruction_revision
            or review_candidate.instruction_revision
            == current_session.current_instruction_revision
        )
    ):
        for path in review_candidate.scope_paths:
            if path not in scope_paths:
                scope_paths.append(path)
        sources.append("review_candidate.scope_paths")

    instruction_paths = extract_scope_paths(current_session.current_instruction)
    if instruction_paths:
        for path in instruction_paths:
            if path not in scope_paths:
                scope_paths.append(path)
        sources.append("current_session.current_instruction")

    reviewed_scope_paths = extract_scope_paths(current_session.last_reviewed_scope)
    if reviewed_scope_paths:
        for path in reviewed_scope_paths:
            if path not in scope_paths:
                scope_paths.append(path)
        sources.append("current_session.last_reviewed_scope")

    return tuple(scope_paths), ",".join(sources)


def dirty_paths_for_repo(repo_root: Path) -> tuple[str, ...]:
    try:
        code, output, _ = run_git_capture(
            ["status", "--porcelain", "--untracked-files=all"],
            repo_root=repo_root,
        )
    except AttributeError:
        return ()
    if code != 0:
        return ()
    ignored_prefixes = ignored_dirty_path_prefixes()
    dirty_paths: list[str] = []
    for line in output.splitlines():
        if not line:
            continue
        parts = line.split(maxsplit=1)
        path = parts[1] if len(parts) == 2 else ""
        if "->" in path:
            path = path.split("->")[-1].strip()
        normalized = path.strip()
        if not normalized or path_is_ignored_for_dirty_paths(
            normalized,
            ignored_prefixes,
        ):
            continue
        dirty_paths.append(normalized)
    return tuple(dirty_paths)


def _live_agent_ids(review_state: ReviewState | None) -> tuple[str, ...]:
    if review_state is None:
        return ()
    agent_ids: list[str] = []
    for participant in review_state.collaboration.participants:
        if not participant.live:
            continue
        agent_id = participant.agent_id or participant.provider
        if agent_id and agent_id not in agent_ids:
            agent_ids.append(agent_id)
    return tuple(agent_ids)


def _live_delegated_agent_ids(review_state: ReviewState | None) -> tuple[str, ...]:
    if review_state is None:
        return ()
    agent_ids: list[str] = []
    for receipt in review_state.collaboration.delegated_work:
        if not receipt.live:
            continue
        if receipt.agent_id and receipt.agent_id not in agent_ids:
            agent_ids.append(receipt.agent_id)
    return tuple(agent_ids)


def _peer_activity_detected(
    *,
    peer_context: OwnershipPeerContext,
) -> bool:
    if len(peer_context.live_agents) > 1 or bool(peer_context.live_delegated_agents):
        return True
    return peer_context.reviewer_mode == "active_dual_agent" or (
        peer_context.effective_reviewer_mode == "active_dual_agent"
    )


def _limit_paths(paths: tuple[str, ...], *, limit: int) -> tuple[str, ...]:
    if len(paths) <= limit:
        return paths
    return paths[:limit]


def classify_work_ownership_state(
    *,
    scope_paths: tuple[str, ...],
    scope_source: str,
    dirty_paths: tuple[str, ...],
    peer_context: OwnershipPeerContext | None = None,
) -> WorkIntakeOwnershipState:
    """Classify one dirty-path set against the claimed scope and peer activity."""
    resolved_peer_context = peer_context or OwnershipPeerContext()
    peer_activity_detected = _peer_activity_detected(
        peer_context=resolved_peer_context,
    )

    if not dirty_paths:
        return WorkIntakeOwnershipState(
            status="clear",
            summary="No dirty paths were detected in the current worktree.",
            scope_source=scope_source,
            scope_path_count=len(scope_paths),
            scope_paths=_limit_paths(scope_paths, limit=_MAX_SCOPE_PATHS),
            live_agents=resolved_peer_context.live_agents,
            live_delegated_agents=resolved_peer_context.live_delegated_agents,
            peer_activity_detected=peer_activity_detected,
        )

    if not scope_paths:
        return WorkIntakeOwnershipState(
            status="scope_unknown_dirty_paths",
            summary=(
                "Dirty paths are present, but the current slice does not publish "
                "explicit file claims yet."
            ),
            scope_source=scope_source,
            dirty_path_count=len(dirty_paths),
            dirty_paths=_limit_paths(dirty_paths, limit=_MAX_DIRTY_PATHS),
            live_agents=resolved_peer_context.live_agents,
            live_delegated_agents=resolved_peer_context.live_delegated_agents,
            peer_activity_detected=peer_activity_detected,
        )

    in_scope_dirty_paths = tuple(
        path for path in dirty_paths if path_matches_scope_claim(path, scope_paths)
    )
    outside_scope_dirty_paths = tuple(
        path for path in dirty_paths if path not in in_scope_dirty_paths
    )
    if outside_scope_dirty_paths and peer_activity_detected:
        return WorkIntakeOwnershipState(
            status="concurrent_writer_activity",
            summary=(
                "Dirty paths fall outside the claimed slice while typed peer "
                "activity is still present."
            ),
            scope_source=scope_source,
            scope_path_count=len(scope_paths),
            dirty_path_count=len(dirty_paths),
            outside_scope_dirty_path_count=len(outside_scope_dirty_paths),
            scope_paths=_limit_paths(scope_paths, limit=_MAX_SCOPE_PATHS),
            dirty_paths=_limit_paths(dirty_paths, limit=_MAX_DIRTY_PATHS),
            in_scope_dirty_paths=_limit_paths(
                in_scope_dirty_paths,
                limit=_MAX_IN_SCOPE_DIRTY_PATHS,
            ),
            outside_scope_dirty_paths=_limit_paths(
                outside_scope_dirty_paths,
                limit=_MAX_OUTSIDE_SCOPE_DIRTY_PATHS,
            ),
            live_agents=resolved_peer_context.live_agents,
            live_delegated_agents=resolved_peer_context.live_delegated_agents,
            peer_activity_detected=True,
            concurrent_writer_detected=True,
        )
    if outside_scope_dirty_paths:
        return WorkIntakeOwnershipState(
            status="outside_scope_dirty_paths",
            summary=(
                "Dirty paths fall outside the claimed slice, but no typed peer "
                "activity is registered right now."
            ),
            scope_source=scope_source,
            scope_path_count=len(scope_paths),
            dirty_path_count=len(dirty_paths),
            outside_scope_dirty_path_count=len(outside_scope_dirty_paths),
            scope_paths=_limit_paths(scope_paths, limit=_MAX_SCOPE_PATHS),
            dirty_paths=_limit_paths(dirty_paths, limit=_MAX_DIRTY_PATHS),
            in_scope_dirty_paths=_limit_paths(
                in_scope_dirty_paths,
                limit=_MAX_IN_SCOPE_DIRTY_PATHS,
            ),
            outside_scope_dirty_paths=_limit_paths(
                outside_scope_dirty_paths,
                limit=_MAX_OUTSIDE_SCOPE_DIRTY_PATHS,
            ),
            live_agents=resolved_peer_context.live_agents,
            live_delegated_agents=resolved_peer_context.live_delegated_agents,
            peer_activity_detected=peer_activity_detected,
        )
    return WorkIntakeOwnershipState(
        status="in_scope_dirty_paths",
        summary="All dirty paths fall within the claimed slice scope.",
        scope_source=scope_source,
        scope_path_count=len(scope_paths),
        dirty_path_count=len(dirty_paths),
        scope_paths=_limit_paths(scope_paths, limit=_MAX_SCOPE_PATHS),
        dirty_paths=_limit_paths(dirty_paths, limit=_MAX_DIRTY_PATHS),
        in_scope_dirty_paths=_limit_paths(
            in_scope_dirty_paths,
            limit=_MAX_IN_SCOPE_DIRTY_PATHS,
        ),
        live_agents=resolved_peer_context.live_agents,
        live_delegated_agents=resolved_peer_context.live_delegated_agents,
        peer_activity_detected=peer_activity_detected,
    )


__all__ = [
    "build_work_intake_ownership_state",
    "classify_work_ownership_state",
    "dirty_paths_for_repo",
]
