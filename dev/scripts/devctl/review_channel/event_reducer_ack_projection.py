"""Reducer-side ACK projection for applied stage-commit handoff packets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from ..runtime.agent_session_outcome import (
    AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF,
    AgentSessionOutcomeState,
)
from ..runtime.completed_handoff_authority import handoff_target_revisions
from ..runtime.review_state_models import ReviewCurrentSessionState
from .agent_session_outcome_events import agent_session_outcomes_from_events
from .event_projection_current_session import (
    _devctl_commit_target_revision,
    _parse_utc,
    completed_handoff_matches_current_context,
)
from .packet_contract import (
    ACTION_REQUEST_PACKET_KIND,
    STAGE_PIPELINE_ACTION_REQUEST_ACTIONS,
)


@dataclass(frozen=True, slots=True)
class StageCommitPipelineAckProjection:
    """Matched applied packet plus completed-handoff outcome."""

    packet: Mapping[str, object]
    outcome: AgentSessionOutcomeState
    ack_revision: str
    applied_at_utc: str


@dataclass(frozen=True, slots=True)
class StageCommitPipelineAckMatcher:
    """Match applied stage-commit packets to typed completed handoffs."""

    packet_rows: Sequence[Mapping[str, object]]
    events: Sequence[Mapping[str, object]]
    repo_root: Path
    accepted_revisions: tuple[str, ...]

    def latest_projection(self) -> StageCommitPipelineAckProjection | None:
        """Return the newest applied packet with a matching handoff outcome."""
        if not self.accepted_revisions:
            return None

        outcomes = self.completed_handoff_outcomes()
        for packet in self.applied_stage_commit_packets():
            projection = self.projection_for_packet(packet, outcomes)
            if projection is not None:
                return projection

        return None

    def applied_stage_commit_packets(self) -> list[Mapping[str, object]]:
        """Return applied runtime stage-commit action-request packets."""
        return sorted(
            (
                packet
                for packet in self.packet_rows
                if self.is_applied_stage_commit_packet(packet)
            ),
            key=lambda packet: _text(packet.get("applied_at_utc")),
            reverse=True,
        )

    def completed_handoff_outcomes(self) -> list[AgentSessionOutcomeState]:
        """Return completed-handoff outcomes newest first."""
        return sorted(
            agent_session_outcomes_from_events(self.events),
            key=lambda outcome: (
                outcome.finished_at_utc or outcome.observed_at_utc,
                outcome.source_event_id,
            ),
            reverse=True,
        )

    def projection_for_packet(
        self,
        packet: Mapping[str, object],
        outcomes: Sequence[AgentSessionOutcomeState],
    ) -> StageCommitPipelineAckProjection | None:
        """Return the matching ACK projection for one applied packet."""
        for outcome in outcomes:
            if not self.outcome_matches_packet(outcome, packet):
                continue

            ack_revision = self.ack_revision_for_outcome(outcome)
            if not ack_revision:
                continue

            return StageCommitPipelineAckProjection(
                packet=packet,
                outcome=outcome,
                ack_revision=ack_revision,
                applied_at_utc=_text(packet.get("applied_at_utc")),
            )

        return None

    def is_applied_stage_commit_packet(
        self,
        packet: Mapping[str, object],
    ) -> bool:
        """Return whether a packet row can participate in ACK projection."""
        return (
            _text(packet.get("status")) == "applied"
            and _text(packet.get("kind")) == ACTION_REQUEST_PACKET_KIND
            and _text(packet.get("requested_action"))
            in STAGE_PIPELINE_ACTION_REQUEST_ACTIONS
            and _text(packet.get("target_kind")) == "runtime"
            and bool(_text(packet.get("full_guard_bundle_evidence")))
        )

    def outcome_matches_packet(
        self,
        outcome: AgentSessionOutcomeState,
        packet: Mapping[str, object],
    ) -> bool:
        """Return whether a typed outcome proves one applied packet."""
        if not self.outcome_matches_packet_identity(outcome, packet):
            return False

        if not self.outcome_matches_stage_commit_scope(outcome, packet):
            return False

        if not self.outcome_not_after_applied(outcome, packet):
            return False

        return self.outcome_matches_revision_authority(outcome, packet)

    def outcome_matches_packet_identity(
        self,
        outcome: AgentSessionOutcomeState,
        packet: Mapping[str, object],
    ) -> bool:
        """Return whether outcome identity and provider bind to the packet."""
        packet_id = _text(packet.get("packet_id"))
        if not packet_id or _text(outcome.handoff_packet_id) != packet_id:
            return False

        if outcome.outcome != AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF:
            return False

        return outcome.provider.lower() == _text(packet.get("from_agent")).lower()

    def outcome_matches_stage_commit_scope(
        self,
        outcome: AgentSessionOutcomeState,
        packet: Mapping[str, object],
    ) -> bool:
        """Return whether outcome and packet both describe the runtime action."""
        if _text(outcome.handoff_requested_action) not in (
            STAGE_PIPELINE_ACTION_REQUEST_ACTIONS
        ):
            return False

        return (
            _text(outcome.target_kind) == "runtime"
            and _text(packet.get("target_kind")) == "runtime"
        )

    def outcome_not_after_applied(
        self,
        outcome: AgentSessionOutcomeState,
        packet: Mapping[str, object],
    ) -> bool:
        """Return whether the outcome timestamp is not after packet apply."""
        outcome_timestamp = _parse_utc(
            outcome.finished_at_utc or outcome.observed_at_utc
        )
        applied_timestamp = _parse_utc(_text(packet.get("applied_at_utc")))

        if outcome_timestamp is None or applied_timestamp is None:
            return False

        return outcome_timestamp <= applied_timestamp

    def outcome_matches_revision_authority(
        self,
        outcome: AgentSessionOutcomeState,
        packet: Mapping[str, object],
    ) -> bool:
        """Return whether packet and handoff-chain revisions both match."""
        packet_revisions = packet_target_revisions(packet)
        if not completed_handoff_matches_current_context(
            outcome,
            (),
            repo_root=self.repo_root,
            expected_target_revisions=packet_revisions,
        ):
            return False

        return completed_handoff_matches_current_context(
            outcome,
            (),
            repo_root=self.repo_root,
            expected_target_revisions=self.accepted_revisions,
        )

    def ack_revision_for_outcome(self, outcome: AgentSessionOutcomeState) -> str:
        """Return the commit revision that should be projected as ACK."""
        return (
            _devctl_commit_target_revision(outcome.target_ref)
            or _text(outcome.target_revision)
        )


def project_stage_commit_pipeline_ack(
    current_session: ReviewCurrentSessionState,
    *,
    packet_rows: Sequence[Mapping[str, object]],
    events: Sequence[Mapping[str, object]],
    repo_root: Path,
) -> ReviewCurrentSessionState:
    """Project a validated applied stage-commit handoff into ACK fields."""
    projection = latest_stage_commit_pipeline_ack_projection(
        packet_rows=packet_rows,
        events=events,
        repo_root=repo_root,
    )

    if projection is None:
        return current_session

    return replace(
        current_session,
        implementer_status=(
            current_session.implementer_status
            or "stage_commit_pipeline_applied"
        ),
        implementer_ack=ack_text(projection),
        implementer_ack_revision=projection.ack_revision,
        implementer_ack_state="current",
    )


def latest_stage_commit_pipeline_ack_projection(
    *,
    packet_rows: Sequence[Mapping[str, object]],
    events: Sequence[Mapping[str, object]],
    repo_root: Path,
) -> StageCommitPipelineAckProjection | None:
    """Return the latest applied stage-commit ACK proven by typed events."""
    matcher = StageCommitPipelineAckMatcher(
        packet_rows=packet_rows,
        events=events,
        repo_root=repo_root,
        accepted_revisions=accepted_handoff_target_revisions(repo_root),
    )

    return matcher.latest_projection()


def packet_target_revisions(packet: Mapping[str, object]) -> tuple[str, ...]:
    """Return unique packet target revisions, including devctl_commit refs."""
    revisions: list[str] = []

    for value in (
        packet.get("target_revision"),
        _devctl_commit_target_revision(_text(packet.get("target_ref"))),
    ):
        text = _text(value)
        if text and text not in revisions:
            revisions.append(text)

    return tuple(revisions)


def accepted_handoff_target_revisions(repo_root: Path) -> tuple[str, ...]:
    """Return accepted completed-handoff revisions, fail-closed on read errors."""
    try:
        return handoff_target_revisions(repo_root)
    except (OSError, ValueError):
        return ()


def ack_text(projection: StageCommitPipelineAckProjection) -> str:
    """Return the typed ACK text projected into current-session state."""
    return (
        "- stage_commit_pipeline handoff applied; "
        f"packet: `{_text(projection.packet.get('packet_id'))}`; "
        f"target-revision: `{projection.ack_revision}`; "
        f"applied-at: `{projection.applied_at_utc}`"
    )


def _text(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip()


__all__ = [
    "StageCommitPipelineAckMatcher",
    "StageCommitPipelineAckProjection",
    "latest_stage_commit_pipeline_ack_projection",
    "project_stage_commit_pipeline_ack",
]
