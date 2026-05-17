"""Current-session resolution helpers for event-backed projections."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from ..runtime.agent_session_outcome import AgentSessionOutcomeState
from .current_session_attention import (
    codex_packet_attention_requires_clear,
    reviewer_checkpoint_instruction_preservation,
)
from .current_session_projection import (
    build_bridge_current_session,
    build_event_current_session,
)
from .session_probe import ConductorSessionRecord

COMPLETED_HANDOFF_ORPHAN_RELEASE_SECONDS = 900


@dataclass(frozen=True, slots=True)
class CurrentSessionResolvers:
    """Override hooks for event-backed current-session resolution."""

    build_event_current_session_fn: object = build_event_current_session
    build_bridge_current_session_fn: object = build_bridge_current_session


def resolve_current_session(
    review_state: dict[str, object],
    *,
    repo_root: Path | None = None,
    prior_review_state=None,
    context=None,
    bridge_liveness: dict[str, object],
    resolvers: CurrentSessionResolvers | None = None,
):
    """Resolve current-session authority from typed event state only."""
    if context is not None:
        repo_root = context.repo_root
        prior_review_state = context.prior_review_state
    if repo_root is None:
        raise ValueError("resolve_current_session requires repo_root or context")
    active_resolvers = resolvers or CurrentSessionResolvers()

    current_session = active_resolvers.build_event_current_session_fn(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
        prior_review_state=prior_review_state,
    )
    if codex_packet_attention_requires_clear(review_state):
        preserved = reviewer_checkpoint_instruction_preservation(review_state)
        if preserved is not None:
            current_session = replace(
                current_session,
                current_instruction=preserved[0],
                current_instruction_revision=preserved[1],
            )
        else:
            current_session = replace(
                current_session,
                current_instruction="",
                current_instruction_revision="",
            )
    return current_session


def completed_handoff_matches_current_context(
    outcome: AgentSessionOutcomeState,
    sessions: Sequence[ConductorSessionRecord],
    *,
    repo_root: Path,
    expected_target_revision: str = "",
    expected_target_revisions: Sequence[str] = (),
) -> bool:
    """Match a completed handoff against live session metadata or target refs."""
    if _outcome_matches_current_session(outcome, sessions):
        return True
    if _provider_sessions_for_outcome(outcome, sessions):
        return False
    return _outcome_matches_expected_target_revisions(
        outcome,
        repo_root=repo_root,
        expected_target_revision=expected_target_revision,
        expected_target_revisions=expected_target_revisions,
    )


def _provider_sessions_for_outcome(
    outcome: AgentSessionOutcomeState,
    sessions: Sequence[ConductorSessionRecord],
) -> tuple[ConductorSessionRecord, ...]:
    provider = outcome.provider.lower()
    session_name = _text(outcome.session_name)
    rows: list[ConductorSessionRecord] = []
    for session in sessions or ():
        if _text(session.provider).lower() != provider:
            continue
        candidate_name = _text(session.session_name)
        if session_name and candidate_name and session_name != candidate_name:
            continue
        rows.append(session)
    return tuple(rows)


def _outcome_matches_expected_target_revisions(
    outcome: AgentSessionOutcomeState,
    *,
    repo_root: Path,
    expected_target_revision: str,
    expected_target_revisions: Sequence[str],
) -> bool:
    revisions = _normalized_revisions(
        (expected_target_revision, *tuple(expected_target_revisions or ()))
    )
    target_revision = _text(outcome.target_revision)
    if not _revision_matches_any(target_revision, revisions):
        return False
    if outcome.target_kind != "runtime":
        return False
    if outcome.handoff_requested_action != "stage_commit_pipeline":
        return False
    target_ref_revision = _devctl_commit_target_revision(outcome.target_ref)
    if not _revision_matches_any(target_ref_revision, revisions):
        return False
    if not (_text(outcome.handoff_packet_id) and _text(outcome.source_event_id)):
        return False
    if _outcome_has_prepared_session_metadata(outcome):
        return False
    if outcome.workspace_root and not _same_path(outcome.workspace_root, str(repo_root)):
        return False
    return True


def _normalized_revisions(values: Sequence[str]) -> frozenset[str]:
    return frozenset(dict.fromkeys(_text(value) for value in values if _text(value)))


def _devctl_commit_target_revision(target_ref: str) -> str:
    prefix = "devctl_commit:"
    text = _text(target_ref)
    if not text.startswith(prefix):
        return ""
    return text[len(prefix) :].strip()


def _revision_matches_any(revision: str, revisions: frozenset[str]) -> bool:
    text = _text(revision)
    if not text:
        return False
    if text in revisions:
        return True
    if len(text) < 7:
        return False
    return sum(1 for candidate in revisions if candidate.startswith(text)) == 1


def _outcome_has_prepared_session_metadata(
    outcome: AgentSessionOutcomeState,
) -> bool:
    return any(
        _text(value)
        for value in (
            outcome.metadata_path,
            outcome.prepared_at_utc,
            outcome.prepared_session_token,
            outcome.prepared_head_sha,
            outcome.prepared_instruction_revision,
        )
    )


def _outcome_matches_current_session(
    outcome: AgentSessionOutcomeState,
    sessions: Sequence[ConductorSessionRecord],
) -> bool:
    for session in sessions or ():
        provider = _text(session.provider).lower()
        if provider != outcome.provider.lower():
            continue

        session_name = _text(session.session_name)
        if (
            outcome.session_name
            and session_name
            and outcome.session_name != session_name
        ):
            continue

        if not _outcome_not_before_session(outcome, session):
            continue
        if not _session_owner_live_or_recent(session):
            continue

        token = _text(session.prepared_session_token)
        if outcome.prepared_session_token and token:
            return outcome.prepared_session_token == token

        prepared_at = _text(session.prepared_at)
        if outcome.prepared_at_utc and prepared_at:
            return outcome.prepared_at_utc == prepared_at

        metadata_path = _text(session.metadata_path)
        if outcome.metadata_path and metadata_path:
            return _same_path(outcome.metadata_path, metadata_path)

    return False


def _session_owner_live_or_recent(session: ConductorSessionRecord) -> bool:
    """Release completed handoffs whose owning session is dead and stale."""
    if bool(getattr(session, "live", False)):
        return True
    age_seconds = getattr(session, "age_seconds", None)
    if age_seconds is None:
        return True
    return int(age_seconds) <= COMPLETED_HANDOFF_ORPHAN_RELEASE_SECONDS


def _outcome_not_before_session(
    outcome: AgentSessionOutcomeState,
    session: ConductorSessionRecord,
) -> bool:
    prepared_at = _parse_utc(_text(session.prepared_at))
    finished_at = _parse_utc(outcome.finished_at_utc or outcome.observed_at_utc)

    if prepared_at is None or finished_at is None:
        return True

    return finished_at >= prepared_at


def _same_path(left: str, right: str) -> bool:
    try:
        return Path(left).resolve() == Path(right).resolve()
    except OSError:
        return left == right


def _parse_utc(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
