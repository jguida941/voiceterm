"""Remote-control pair-campaign read model for ``devctl develop``."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ...runtime.remote_control_attachment_models import (
    remote_control_attachment_from_mapping,
)
from ...runtime.remote_control_attachment_status import (
    remote_attachment_active,
    remote_attachment_age_seconds,
    remote_attachment_has_physical_identity,
    remote_attachment_status,
)
from .models import (
    DevelopmentCampaignReport,
    DevelopmentCampaignRoleState,
    DevelopmentPacketAttention,
)

CAMPAIGN_CONTRACT_ID = "RemoteControlCollaborationCampaign"
CAMPAIGN_SCHEMA_VERSION = 1
CAMPAIGN_PLAN_ROW_ID = "MP377-P0-RC-PAIR-S1"
PRIMARY_MODE_ID = "dashboard_led"
PROOF_REQUIREMENTS = (
    "RemoteControlAttachmentState attached and identity-bound",
    "CollaborationSession / SessionPosture agree on remote-control posture",
    "current Claude dashboard/reviewer packet debt triaged through typed state",
    "AgentLoopDecision grants mutation before edits",
    "guard bundle green before commit",
    "devctl push --execute with remote-ref proof after new commits",
)


def campaign_report(
    review_state: Mapping[str, object],
    *,
    packet_attention: DevelopmentPacketAttention,
) -> DevelopmentCampaignReport:
    """Build the read-only campaign report from existing typed surfaces."""
    reviewer_runtime = _mapping(review_state.get("reviewer_runtime"))
    session_posture = _mapping(reviewer_runtime.get("session_posture"))
    coordination_state = _mapping(review_state.get("coordination_state"))
    authority = _mapping(review_state.get("authority_snapshot"))
    attachment = remote_control_attachment_from_mapping(
        reviewer_runtime.get("remote_control_attachment")
    )
    remote_status = remote_attachment_status(attachment)
    remote_active = remote_attachment_active(attachment)
    remote_identity_bound = remote_attachment_has_physical_identity(attachment)
    roles = _campaign_roles(review_state)
    pending_packet_id = _pending_packet_id(packet_attention, authority)
    pending_packet_command = (
        packet_attention.required_command
        or _text(_mapping(authority.get("packet_target")).get("required_command"))
    )
    topology = _text(coordination_state.get("coordination_topology"))
    legacy_mode = _text(coordination_state.get("legacy_reviewer_mode")) or _text(
        review_state.get("reviewer_mode")
    )
    effective_mode = _text(review_state.get("effective_reviewer_mode")) or _text(
        reviewer_runtime.get("effective_reviewer_mode")
    )
    interaction_mode = _text(session_posture.get("interaction_mode"))
    remote_stale = attachment is not None and not remote_active
    mode_drift = _mode_drift(
        remote_active=remote_active,
        topology=topology,
        legacy_mode=legacy_mode,
        interaction_mode=interaction_mode,
    )
    fail_closed = bool(pending_packet_id or remote_stale or mode_drift)
    mutation_allowed = (
        not fail_closed
        and any(
            role.actor_id == "codex" and role.role == "implementer" and role.may_mutate
            for role in roles
        )
    )
    publication_allowed = False
    status = _campaign_status(
        pending_packet_id=pending_packet_id,
        remote_stale=remote_stale,
        mode_drift=mode_drift,
        mutation_allowed=mutation_allowed,
    )
    attachment_age_seconds = remote_attachment_age_seconds(attachment)
    return DevelopmentCampaignReport(
        plan_row_id=CAMPAIGN_PLAN_ROW_ID,
        mode_id=PRIMARY_MODE_ID,
        status=status,
        current_phase=_current_phase(status),
        summary=_summary(status),
        remote_control_provider=_attachment_field(attachment, "provider"),
        remote_control_status=remote_status,
        remote_control_active=remote_active,
        remote_control_identity_bound=remote_identity_bound,
        remote_control_session_id=_attachment_field(attachment, "remote_session_id"),
        remote_control_age_seconds=(
            attachment_age_seconds if attachment_age_seconds is not None else -1
        ),
        physical_remote_control_confirmed=bool(
            getattr(attachment, "physical_remote_control_confirmed", False)
        ),
        coordination_topology=topology,
        legacy_reviewer_mode=legacy_mode,
        effective_reviewer_mode=effective_mode,
        operator_interaction_mode=interaction_mode,
        mode_drift=mode_drift,
        fail_closed=fail_closed,
        mutation_allowed=mutation_allowed,
        publication_allowed=publication_allowed,
        pending_packet_id=pending_packet_id,
        pending_packet_required_command=pending_packet_command,
        codex_next_command=_next_command_for(roles, "codex"),
        claude_next_command=_next_command_for(roles, "claude") or pending_packet_command,
        roles=roles,
        proof_requirements=PROOF_REQUIREMENTS,
    )


def _campaign_roles(
    review_state: Mapping[str, object],
) -> tuple[DevelopmentCampaignRoleState, ...]:
    decisions = {
        (
            _text(row.get("actor_id")),
            _text(row.get("actor_role")),
            _text(row.get("session_id")),
        ): row
        for row in _mapping_rows(review_state.get("agent_loop_decisions"))
    }
    rows: list[DevelopmentCampaignRoleState] = []
    for row in _mapping_rows(_mapping(review_state.get("agent_work_board")).get("rows")):
        key = (
            _text(row.get("actor_id")),
            _text(row.get("role")),
            _text(row.get("session_id")),
        )
        decision = _mapping(decisions.get(key))
        rows.append(
            DevelopmentCampaignRoleState(
                actor_id=key[0],
                role=key[1],
                session_id=key[2],
                status=_text(row.get("status")),
                mutation_mode=_text(row.get("mutation_mode")),
                active_packet_id=_text(row.get("active_packet_id"))
                or _text(row.get("attention_packet_id"))
                or _text(row.get("executing_packet_id")),
                may_mutate=bool(decision.get("may_mutate")),
                required_action=_text(decision.get("required_action")),
                proof_state=_text(decision.get("proof_state")),
                blocker=_text(decision.get("top_blocker")),
                next_command=_text(decision.get("next_loop_command")),
            )
        )
    return tuple(rows)


def _mode_drift(
    *,
    remote_active: bool,
    topology: str,
    legacy_mode: str,
    interaction_mode: str,
) -> bool:
    if topology == "multi_agent_active" and legacy_mode == "single_agent":
        return True
    if remote_active and interaction_mode != "remote_control":
        return True
    return False


def _campaign_status(
    *,
    pending_packet_id: str,
    remote_stale: bool,
    mode_drift: bool,
    mutation_allowed: bool,
) -> str:
    if pending_packet_id:
        return "blocked_pending_packet_triage"
    if remote_stale:
        return "blocked_remote_control_stale"
    if mode_drift:
        return "blocked_mode_drift"
    if mutation_allowed:
        return "ready_for_codex_build"
    return "observe_only"


def _current_phase(status: str) -> str:
    phases = {
        "blocked_pending_packet_triage": "claude_dashboard_ack_triage",
        "blocked_remote_control_stale": "remote_control_heartbeat_required",
        "blocked_mode_drift": "typed_mode_resync_required",
        "ready_for_codex_build": "codex_build_claude_review",
    }
    return phases.get(status, "read_only_observation")


def _summary(status: str) -> str:
    if status == "blocked_pending_packet_triage":
        return "Claude must triage the active packet before Codex claims review proof."
    if status == "blocked_remote_control_stale":
        return "Remote-control transport exists but lacks fresh typed attachment proof."
    if status == "blocked_mode_drift":
        return "Typed mode fields disagree; mutation remains fail-closed."
    if status == "ready_for_codex_build":
        return "Codex may build under typed gates; Claude remains the review/dashboard lane."
    return "Campaign is read-only until typed authority grants the next lane."


def _pending_packet_id(
    packet_attention: DevelopmentPacketAttention,
    authority: Mapping[str, object],
) -> str:
    return (
        packet_attention.latest_attention_packet_id
        or packet_attention.latest_finding_packet_id
        or _text(_mapping(authority.get("packet_target")).get("current_instruction_packet_id"))
        or _text(_mapping(authority.get("packet_target")).get("latest_finding_packet_id"))
    )


def _next_command_for(
    roles: tuple[DevelopmentCampaignRoleState, ...],
    actor_id: str,
) -> str:
    for role in roles:
        if role.actor_id == actor_id and role.next_command:
            return role.next_command
    return ""


def _attachment_field(attachment: object, field_name: str) -> str:
    return _text(getattr(attachment, field_name, ""))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_rows(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(row for row in value if isinstance(row, Mapping))


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "CAMPAIGN_CONTRACT_ID",
    "CAMPAIGN_PLAN_ROW_ID",
    "CAMPAIGN_SCHEMA_VERSION",
    "campaign_report",
]
