"""Remote-control pair-campaign read model for ``devctl develop``."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from ...runtime.value_coercion import coerce_bool as _coerce_bool
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
from .campaign_exception_proof import (
    bypass_posture,
    governed_exception_projection,
    publication_proof_summary,
    push_proof_projection,
)
from .campaign_idris_gate import campaign_typechecker_verdict

CAMPAIGN_CONTRACT_ID = "RemoteControlCollaborationCampaign"
CAMPAIGN_SCHEMA_VERSION = 1
CAMPAIGN_PLAN_ROW_ID = "MP377-P0-RC-PAIR-S1"
EXCEPTION_PLAN_ROW_ID = "MP377-P0-EXC-S1"
ROLE_MATRIX_PLAN_ROW_ID = "MP377-P0-ROLE-MATRIX-DOGFOOD-S1"
PRIMARY_MODE_ID = "dashboard_led"
PROOF_REQUIREMENTS = (
    "RemoteControlAttachmentState attached and identity-bound",
    "CollaborationSession / SessionPosture agree on remote-control posture",
    "current Claude dashboard/reviewer packet goal continued through typed state",
    "GovernedExceptionLifecycle has no open publication exception debt",
    "bypass publication transport retired only after devctl push --execute proof",
    "Pass-C role-matrix dogfood starts from AGENTS.md and records typed evidence",
    "AgentLoopDecision grants mutation before edits",
    "guard bundle green before commit",
    "devctl push --execute with remote-ref proof after new commits",
)
FOLDED_PLAN_ROW_IDS = (
    CAMPAIGN_PLAN_ROW_ID,
    EXCEPTION_PLAN_ROW_ID,
    ROLE_MATRIX_PLAN_ROW_ID,
)


def campaign_report(
    review_state: Mapping[str, object],
    *,
    packet_attention: DevelopmentPacketAttention,
    exception_store_path: Path | None = None,
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
    exception_projection = governed_exception_projection(exception_store_path)
    push_projection = push_proof_projection(review_state)
    posture = bypass_posture(
        exception_projection=exception_projection,
        push_projection=push_projection,
    )
    open_exception_debt = bool(
        exception_projection.pending_count or exception_projection.error_count
    )
    typechecker_verdict = campaign_typechecker_verdict(exception_store_path)
    mode_drift = _mode_drift(
        remote_active=remote_active,
        topology=topology,
        legacy_mode=legacy_mode,
        interaction_mode=interaction_mode,
    )
    fail_closed = bool(
        pending_packet_id
        or remote_stale
        or mode_drift
        or open_exception_debt
        or not typechecker_verdict.allows_mutation
    )
    mutation_allowed = (
        not fail_closed
        and typechecker_verdict.allows_mutation
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
        open_exception_debt=open_exception_debt,
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
        folded_plan_row_ids=FOLDED_PLAN_ROW_IDS,
        governed_exception_store_path=exception_projection.store_path,
        governed_exception_pending_count=exception_projection.pending_count,
        governed_exception_error_count=exception_projection.error_count,
        governed_exception_status=exception_projection.status,
        bypass_posture=posture,
        bypass_publication_transport_retired=posture.startswith(
            "retired_governed_push"
        ),
        latest_push_report_path=push_projection.path,
        latest_push_report_status=push_projection.status,
        latest_push_report_head_commit=push_projection.head_commit,
        latest_push_report_published_remote=push_projection.published_remote,
        latest_push_report_post_push_green=push_projection.post_push_green,
        latest_push_report_matches_current_head=push_projection.matches_current_head,
        publication_proof_summary=_compose_publication_proof_summary(
            posture=posture,
            push_projection=push_projection,
            exception_projection=exception_projection,
            typechecker_verdict=typechecker_verdict,
        ),
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
                # v4.45.5 (rev_pkt_4743): shared coerce_bool so projected
                # ``"false"``/``"0"`` correctly suppress mutation posture.
                may_mutate=_coerce_bool(decision.get("may_mutate")),
                required_action=_normalized_required_action(
                    _text(decision.get("required_action"))
                ),
                user_action=(
                    _text(decision.get("user_action"))
                    or _user_action_for_required_action(
                        _text(decision.get("required_action"))
                    )
                ),
                continuation_goal=(
                    _text(decision.get("continuation_goal"))
                    or _text(decision.get("attention_packet_id"))
                    or _text(decision.get("active_packet_id"))
                ),
                proof_state=_text(decision.get("proof_state")),
                blocker=_text(decision.get("top_blocker")),
                # v4.45.3 (rev_pkt_4739): only emit next_loop_command as
                # the campaign role's next_command when the actor can
                # actually run it. Blocked decisions (can_run_next_command=
                # false from typed policy) previously surfaced
                # next_loop_command unconditionally, which fed
                # codex_next_command / claude_next_command / operator
                # wrappers with the read-only agent-loop self-loop.
                # v4.45.4 (rev_pkt_4742): replaced local _coerce_bool
                # helper with shared ``runtime.value_coercion.coerce_bool``
                # to converge on the typed normalizer. The import is
                # cycle-safe: ``runtime.value_coercion`` only depends on
                # stdlib (``collections.abc``, ``typing``).
                next_command=(
                    _text(decision.get("next_loop_command"))
                    if _coerce_bool(decision.get("can_run_next_command"))
                    else ""
                ),
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
    open_exception_debt: bool,
    mutation_allowed: bool,
) -> str:
    if pending_packet_id:
        return "blocked_pending_packet_goal"
    if remote_stale:
        return "blocked_remote_control_stale"
    if mode_drift:
        return "blocked_mode_drift"
    if open_exception_debt:
        return "blocked_governed_exception_debt"
    if mutation_allowed:
        return "ready_for_codex_build"
    return "observe_only"


def _current_phase(status: str) -> str:
    phases = {
        "blocked_pending_packet_goal": "claude_packet_goal_required",
        "blocked_remote_control_stale": "remote_control_heartbeat_required",
        "blocked_mode_drift": "typed_mode_resync_required",
        "blocked_governed_exception_debt": "governed_exception_repair",
        "ready_for_codex_build": "codex_build_claude_review",
    }
    return phases.get(status, "read_only_observation")


def _summary(status: str) -> str:
    if status == "blocked_pending_packet_goal":
        return "Claude/Codex must continue the active packet goal before claiming review proof."
    if status == "blocked_remote_control_stale":
        return "Remote-control transport exists but lacks fresh typed attachment proof."
    if status == "blocked_mode_drift":
        return "Typed mode fields disagree; mutation remains fail-closed."
    if status == "blocked_governed_exception_debt":
        return "Governed exception debt is open; repair/proof must run before mutation."
    if status == "ready_for_codex_build":
        return "Codex may build under typed gates; Claude remains the review/dashboard lane."
    return "Campaign is read-only until typed authority grants the next lane."


def _compose_publication_proof_summary(
    *,
    posture: str,
    push_projection,
    exception_projection,
    typechecker_verdict,
) -> str:
    """Append the typechecker verdict to the publication-proof summary line.

    The base summary stays compatible with prior projections; the typechecker
    surface makes Idris-style closure-proof failures visible without changing
    the published shape of ``publication_proof_summary`` in
    ``campaign_exception_proof``.
    """
    base = publication_proof_summary(
        posture=posture,
        push_projection=push_projection,
        exception_projection=exception_projection,
    )
    return f"{base}; {typechecker_verdict.summary}"


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


def _normalized_required_action(value: str) -> str:
    if value in {"triage_pending_packet", "triage_packet", "pivot_to_packet"}:
        return "continue_to_goal"
    return value


def _user_action_for_required_action(value: str) -> str:
    normalized = _normalized_required_action(value)
    if normalized == "continue_to_goal":
        return "Continue to goal"
    return normalized


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
