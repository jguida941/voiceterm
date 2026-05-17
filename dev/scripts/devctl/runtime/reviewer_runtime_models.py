"""Typed reviewer-runtime models shared by review-channel runtime surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .remote_control_attachment_status import (
    ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES,
    DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS,
    remote_attachment_active,
)
from .session_posture import SessionPosture


@dataclass(frozen=True, slots=True)
class ReviewerLastPollState:
    last_codex_poll_utc: str = ""
    last_codex_poll_age_seconds: int = 0
    last_reviewer_poll_utc: str = ""
    last_reviewer_poll_age_seconds: int = 0


@dataclass(frozen=True, slots=True)
class ReviewerRolloverState:
    rollover_id: str = ""
    ack_pending: bool = False
    trigger: str = ""


@dataclass(frozen=True, slots=True)
class ReviewerSessionOwnerState:
    provider: str = ""
    session_name: str = ""
    session_pid: int | None = None
    terminal_window_id: int | None = None
    script_path: str = ""
    session_visibility: str = "unknown"


@dataclass(frozen=True, slots=True)
class ReviewerAcceptanceState:
    current_verdict: str = ""
    open_findings: str = ""
    review_accepted: bool = False
    reviewer_accepted_implementer_state_hash: str = ""


@dataclass(frozen=True, slots=True)
class AgentRuntimeClock:
    """Shared event-log-backed tick/cursor for all active actor sessions.

    Per rev_pkt_2498 (1): one shared clock binds Codex, Claude, dashboard, and
    future agents to the same source_latest_event_id, so wake/attention
    decisions render from one tick rather than separate voluntary polling
    loops. The clock is computed from the canonical review-channel event log.
    """

    source_latest_event_id: str = ""
    source_latest_event_at_utc: str = ""
    cadence_seconds: int = 0
    last_published_at_utc: str = ""
    snapshot_id: str = ""


@dataclass(frozen=True, slots=True)
class InboxObservationState:
    """Typed per-actor inbox observation + pivot-required signal.

    Per rev_pkt_2486: agent inbox-watching and pivot-speed cannot rely on
    voluntary polling + memory-rule discipline. This contract records, per
    actor, the latest packet event seen by the runtime and the latest event
    that actor has explicitly observed/ACKed. When ``last_inbox_event_id`` is
    ahead of ``last_inbox_observed_event_id``, ``pivot_required`` is True and
    pre-mutation/pre-work-batch gates fail closed until the actor catches up.

    Per rev_pkt_2470/2476 actor/session compatibility: ``actor_id`` and
    ``session_id`` pin the observation to a specific role-tagged session.
    Until typed routing is fully enforced, ambiguous-actor observations
    fail closed (``pivot_required=True``) rather than satisfy any session.
    """

    actor_id: str = ""
    session_id: str = ""
    last_inbox_event_id: str = ""
    last_inbox_event_at_utc: str = ""
    last_inbox_observed_event_id: str = ""
    last_inbox_observed_at_utc: str = ""
    pending_packet_count: int = 0
    superseded_packet_id: str = ""
    pivot_required: bool = False
    pivot_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PacketAttentionState:
    """Typed per-actor_session attention contract for shared wake/attention runtime.

    Per rev_pkt_2498 (2): supersedes the env-var pivot workaround as the
    durable typed contract. Derived from review-channel packet events,
    lifecycle/ACK/apply/dismiss events, and delivery receipts. Composes with
    ``AgentRuntimeClock``: ``latest_inbox_event_id`` is read from the shared
    clock, while ``last_observed_event_id`` is per-actor_session.

    Per rev_pkt_2498 (5) actor/session routing: ``observation_actor_id``
    and ``observation_session_id`` pin the attention state. Two roles on the
    same provider cannot both satisfy the same wake; ambiguous provider/session
    identity fails closed via ``actor_identity_ambiguous`` stale_reason.
    """

    observation_actor_id: str = ""
    observation_session_id: str = ""
    latest_inbox_event_id: str = ""
    latest_attention_packet_id: str = ""
    latest_attention_changed_at_utc: str = ""
    last_observed_event_id: str = ""
    last_observed_at_utc: str = ""
    pending_packet_count: int = 0
    unopened_body_packet_count: int = 0
    unopened_body_packet_ids: tuple[str, ...] = ()
    body_open_required: bool = False
    body_open_packet_id: str = ""
    body_open_command: str = ""
    semantic_ingestion_required: bool = False
    semantic_ingestion_packet_id: str = ""
    semantic_ingestion_command: str = ""
    semantic_ingestion_reason: str = ""
    superseded_packet_id: str = ""
    pivot_required: bool = False
    wake_required: bool = False
    stale_reason: str = ""
    pivot_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewerDutyProof:
    """Typed proof that a reviewer session has done BOTH packet review AND code review.

    Per rev_pkt_2475: a healthy reviewer_mode requires both inputs proven, not
    one or the other. ``last_packet_event_id`` and ``pending_packet_count`` track
    the packet-inbox side; ``reviewed_diff_hash`` against the live tree hash
    tracks the code-review side. A reviewer that has consumed packets but not
    reviewed the live diff renders ``review_incomplete`` / ``reviewer_diff_stale``
    rather than ``healthy``.

    Per rev_pkt_2477: this contract supersedes the misleading existing pattern
    where ``reviewer_worker.state == 'up_to_date'`` was treated as semantic
    review proof when it was only a hash-freshness signal.

    Per rev_pkt_2470/2471: ``reviewer_actor_id`` and ``reviewer_session_id``
    pin the proof to a specific actor/session so a dashboard role posing as an
    implementer/reviewer role (or vice versa) cannot satisfy reviewer duty.
    """

    reviewer_actor_id: str = ""
    reviewer_session_id: str = ""
    last_packet_event_id: str = ""
    last_packet_observed_at_utc: str = ""
    pending_packet_count: int = 0
    current_head_sha: str = ""
    staged_tree_hash: str = ""
    worktree_hash: str = ""
    changed_path_count: int = 0
    reviewed_diff_hash: str = ""
    reviewed_diff_base: str = ""
    reviewed_path_count: int = 0
    last_diff_review_at_utc: str = ""
    semantic_review_source: str = ""
    semantic_review_claimed: bool = False
    review_conflict_class: str = ""
    review_conflict_reasons: tuple[str, ...] = ()
    state: str = "unknown"
    stale_reasons: tuple[str, ...] = ()


# RemoteControlAttachmentState + deserialization helpers extracted to
# remote_control_attachment_models.py to keep this module under the shape
# budget. Re-exported below for backward-compatible imports; new consumers
# should import directly from .remote_control_attachment_models.
from .remote_control_attachment_models import (
    RemoteControlAttachmentState,
    has_active_remote_control_attachment,
    remote_control_attachment_from_mapping,
)


@dataclass(frozen=True, slots=True)
class ReviewerRuntimeContract:
    reviewer_mode: str = "single_agent"
    effective_reviewer_mode: str = "single_agent"
    reviewer_freshness: str = "unknown"
    stale_reason: str = ""
    conductor_visibility: str = "unknown"
    implementer_ack_current: bool = False
    implementation_blocked: bool = False
    implementation_block_reason: str = ""
    last_poll: ReviewerLastPollState = field(default_factory=ReviewerLastPollState)
    rollover: ReviewerRolloverState = field(default_factory=ReviewerRolloverState)
    session_owner: ReviewerSessionOwnerState = field(
        default_factory=ReviewerSessionOwnerState
    )
    recovery_action_allowed: str = ""
    review_acceptance: ReviewerAcceptanceState = field(
        default_factory=ReviewerAcceptanceState
    )
    publish_clear: bool = False
    remote_control_attachment: RemoteControlAttachmentState | None = None
    session_posture: SessionPosture = field(default_factory=SessionPosture)
    duty_proof: ReviewerDutyProof = field(default_factory=ReviewerDutyProof)
    inbox_observation: InboxObservationState = field(
        default_factory=InboxObservationState
    )
    agent_runtime_clock: AgentRuntimeClock = field(
        default_factory=AgentRuntimeClock
    )
    packet_attention: PacketAttentionState = field(
        default_factory=PacketAttentionState
    )


def build_packet_attention_state(
    *,
    observation_actor_id: str,
    observation_session_id: str,
    latest_inbox_event_id: str,
    latest_attention_packet_id: str,
    latest_attention_changed_at_utc: str,
    last_observed_event_id: str,
    last_observed_at_utc: str,
    pending_packet_count: int,
    unopened_body_packet_ids: tuple[str, ...] = (),
    body_open_packet_id: str = "",
    body_open_command: str = "",
    semantic_ingestion_required: bool = False,
    semantic_ingestion_packet_id: str = "",
    semantic_ingestion_command: str = "",
    semantic_ingestion_reason: str = "",
    superseded_packet_id: str = "",
) -> PacketAttentionState:
    """Derive typed per-actor_session attention state.

    Per rev_pkt_2498 (4): mutation/work-batch gates read this typed state
    instead of env-only DEVCTL_PIVOT_REQUIRED. wake_required fires when
    the shared clock has advanced past the observer's last_observed_event_id,
    OR when the latest_attention_packet_id changed and the observer hasn't
    caught up. pivot_required fires when wake_required is set OR when the
    actor identity is ambiguous (rev_pkt_2470/2476 fail-closed semantics).
    """
    pivot_reasons: list[str] = []
    wake_required = False
    if _event_id_unobserved(
        latest_inbox_event_id=latest_inbox_event_id,
        last_observed_event_id=last_observed_event_id,
    ):
        pivot_reasons.append("inbox_event_unobserved")
        wake_required = True
    if pending_packet_count > 0:
        pivot_reasons.append("pending_packets_unconsumed")
        wake_required = True
    unopened_ids = tuple(str(row).strip() for row in unopened_body_packet_ids if str(row).strip())
    body_open_required = bool(unopened_ids or body_open_packet_id)
    if body_open_required:
        pivot_reasons.append("packet_bodies_unread")
        wake_required = True
    if semantic_ingestion_required:
        pivot_reasons.append("packet_semantic_ingestion_required")
        wake_required = True
    if superseded_packet_id:
        pivot_reasons.append("active_packet_superseded")
        wake_required = True
    if not observation_actor_id:
        # Per rev_pkt_2498 (5): ambiguous provider must mark pivot_required +
        # actor_identity_ambiguous; cannot satisfy any session as if all
        # claude-named sessions had observed.
        pivot_reasons.append("actor_identity_ambiguous")
    pivot_required = bool(pivot_reasons)
    stale_reason = ""
    if semantic_ingestion_required:
        stale_reason = "packet_semantic_ingestion_required"
    elif body_open_required:
        stale_reason = "packet_body_open_required"
    elif wake_required and not observation_actor_id:
        stale_reason = "actor_identity_ambiguous_with_pending_wake"
    elif wake_required:
        stale_reason = "wake_required"
    elif "actor_identity_ambiguous" in pivot_reasons:
        stale_reason = "actor_identity_ambiguous"
    return PacketAttentionState(
        observation_actor_id=observation_actor_id,
        observation_session_id=observation_session_id,
        latest_inbox_event_id=latest_inbox_event_id,
        latest_attention_packet_id=latest_attention_packet_id,
        latest_attention_changed_at_utc=latest_attention_changed_at_utc,
        last_observed_event_id=last_observed_event_id,
        last_observed_at_utc=last_observed_at_utc,
        pending_packet_count=pending_packet_count,
        unopened_body_packet_count=len(unopened_ids),
        unopened_body_packet_ids=unopened_ids,
        body_open_required=body_open_required,
        body_open_packet_id=body_open_packet_id or (unopened_ids[0] if unopened_ids else ""),
        body_open_command=body_open_command,
        semantic_ingestion_required=semantic_ingestion_required,
        semantic_ingestion_packet_id=semantic_ingestion_packet_id,
        semantic_ingestion_command=semantic_ingestion_command,
        semantic_ingestion_reason=semantic_ingestion_reason,
        superseded_packet_id=superseded_packet_id,
        pivot_required=pivot_required,
        wake_required=wake_required,
        stale_reason=stale_reason,
        pivot_reasons=tuple(pivot_reasons),
    )


def _event_id_unobserved(
    *,
    latest_inbox_event_id: str,
    last_observed_event_id: str,
) -> bool:
    if not latest_inbox_event_id:
        return False
    latest_rank = _event_id_rank(latest_inbox_event_id)
    observed_rank = _event_id_rank(last_observed_event_id)
    if latest_rank >= 0 or observed_rank >= 0:
        return latest_rank > observed_rank
    return latest_inbox_event_id != last_observed_event_id


def _event_id_rank(event_id: str) -> int:
    prefix = "rev_evt_"
    if not event_id.startswith(prefix):
        return -1
    try:
        return int(event_id[len(prefix):])
    except ValueError:
        return -1


def build_agent_runtime_clock(
    *,
    source_latest_event_id: str,
    source_latest_event_at_utc: str,
    cadence_seconds: int = 0,
    last_published_at_utc: str = "",
    snapshot_id: str = "",
) -> AgentRuntimeClock:
    """Build the shared agent runtime clock from typed event-log evidence."""
    return AgentRuntimeClock(
        source_latest_event_id=source_latest_event_id,
        source_latest_event_at_utc=source_latest_event_at_utc,
        cadence_seconds=cadence_seconds,
        last_published_at_utc=last_published_at_utc,
        snapshot_id=snapshot_id,
    )


@dataclass(frozen=True, slots=True)
class WakeEvidence:
    """Typed wake-evidence derived from review-channel events for one actor_session.

    Per rev_pkt_2498 (3): when a packet becomes relevant to an actor/session,
    derive packet_arrival or active_packet_changed evidence. The agent loop
    must observe it before continuing old work.

    ``latest_relevant_event_id`` is the most recent event id that targets the
    actor's identity (matching to_agent + optional target_role/target_session_id
    discriminator). ``arrival_kind`` ∈ {packet_arrival, active_packet_changed,
    none} surfaces what changed.
    """

    actor_id: str = ""
    session_id: str = ""
    latest_relevant_event_id: str = ""
    latest_relevant_event_at_utc: str = ""
    latest_relevant_packet_id: str = ""
    arrival_kind: str = "none"


def derive_wake_evidence_for_actor(
    *,
    events: "list[Mapping[str, object]]",
    actor_id: str,
    session_id: str,
) -> WakeEvidence:
    """Scan typed events and derive the latest wake-relevant event for an actor.

    Per rev_pkt_2498 (3): typed derivation, not voluntary polling. Filters
    by ``to_agent`` and optionally ``target_role`` / ``target_session_id``
    when those discriminators are set on the event. Empty actor_id is a
    runtime contract violation — fail closed by returning empty WakeEvidence
    so the consumer (PacketAttentionState) marks pivot_required.
    """
    if not actor_id:
        return WakeEvidence()
    relevant_kinds = {"packet_posted", "active_packet_changed"}
    latest: Mapping[str, object] | None = None
    latest_kind = "none"
    for event in events:
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("event_type") or "").strip()
        if event_type not in relevant_kinds:
            continue
        to_agent = str(event.get("to_agent") or "").strip()
        # Allow provider+role match for legacy packets without the
        # target_role discriminator: actor_id='coder-claude' has provider
        # 'claude' (last segment) and role 'coder' (first segment); a packet
        # with to_agent='claude' matches because they share provider.
        actor_provider = actor_id.split("-")[-1] if "-" in actor_id else actor_id
        actor_role = actor_id.split("-")[0] if "-" in actor_id else ""
        if to_agent and to_agent != actor_id and to_agent != actor_provider:
            continue
        target_role = str(event.get("target_role") or "").strip()
        if target_role:
            if target_role != actor_role and target_role != actor_id:
                continue
        target_session_id = str(event.get("target_session_id") or "").strip()
        if target_session_id and target_session_id != session_id:
            continue
        latest = event
        latest_kind = (
            "active_packet_changed"
            if event_type == "active_packet_changed"
            else "packet_arrival"
        )
    if latest is None:
        return WakeEvidence(
            actor_id=actor_id,
            session_id=session_id,
        )
    return WakeEvidence(
        actor_id=actor_id,
        session_id=session_id,
        latest_relevant_event_id=str(latest.get("event_id") or ""),
        latest_relevant_event_at_utc=str(latest.get("timestamp_utc") or ""),
        latest_relevant_packet_id=str(latest.get("packet_id") or ""),
        arrival_kind=latest_kind,
    )


def build_inbox_observation_state(
    *,
    actor_id: str,
    session_id: str,
    last_inbox_event_id: str,
    last_inbox_event_at_utc: str,
    last_inbox_observed_event_id: str,
    last_inbox_observed_at_utc: str,
    pending_packet_count: int,
    superseded_packet_id: str = "",
) -> InboxObservationState:
    """Derive typed inbox observation + pivot_required signal.

    Per rev_pkt_2486: pivot_required fires when:
    - Latest inbox event id is ahead of the actor's observed event id, OR
    - There are pending packets the actor hasn't processed, OR
    - A superseding packet displaced the actor's prior active packet.

    Pivot_reasons surfaces the specific cause(s) so consumers (claude-loop,
    sync-status, dashboard) can render machine-readable intent rather than
    prose. Pre-mutation gates fail closed when pivot_required is True.
    """
    pivot_reasons: list[str] = []
    if (
        last_inbox_event_id
        and last_inbox_event_id != last_inbox_observed_event_id
    ):
        pivot_reasons.append("inbox_event_unobserved")
    if pending_packet_count > 0:
        pivot_reasons.append("pending_packets_unconsumed")
    if superseded_packet_id:
        pivot_reasons.append("active_packet_superseded")
    if not actor_id:
        # Fail closed when actor identity is unknown — per rev_pkt_2486
        # compatibility note with actor/session discriminator.
        pivot_reasons.append("actor_identity_ambiguous")
    pivot_required = bool(pivot_reasons)
    return InboxObservationState(
        actor_id=actor_id,
        session_id=session_id,
        last_inbox_event_id=last_inbox_event_id,
        last_inbox_event_at_utc=last_inbox_event_at_utc,
        last_inbox_observed_event_id=last_inbox_observed_event_id,
        last_inbox_observed_at_utc=last_inbox_observed_at_utc,
        pending_packet_count=pending_packet_count,
        superseded_packet_id=superseded_packet_id,
        pivot_required=pivot_required,
        pivot_reasons=tuple(pivot_reasons),
    )
