"""Remote-control campaign runtime-state contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


REMOTE_CONTROL_CAMPAIGN_FIELDS: tuple[ContractField, ...] = (
    ContractField("plan_row_id", "str", "Typed plan row that owns the campaign."),
    ContractField("mode_id", "str", "Requested collaboration mode lens."),
    ContractField("status", "str", "Campaign state."),
    ContractField("current_phase", "str", "Current campaign phase."),
    ContractField("summary", "str", "Human-readable summary."),
    ContractField("remote_control_provider", "str", "Remote-control provider."),
    ContractField("remote_control_status", "str", "Attachment status."),
    ContractField("remote_control_active", "bool", "Fresh active attachment."),
    ContractField(
        "remote_control_identity_bound",
        "bool",
        "Whether attachment has physical remote identity.",
    ),
    ContractField("remote_control_session_id", "str", "Remote-control session id."),
    ContractField("remote_control_age_seconds", "int", "Attachment age, or -1."),
    ContractField(
        "physical_remote_control_confirmed",
        "bool",
        "Whether physical remote control was observed.",
    ),
    ContractField("coordination_topology", "str", "Typed coordination topology."),
    ContractField("legacy_reviewer_mode", "str", "Compatibility reviewer mode."),
    ContractField("effective_reviewer_mode", "str", "Effective reviewer mode."),
    ContractField("operator_interaction_mode", "str", "Typed operator mode."),
    ContractField("mode_drift", "bool", "Whether typed mode fields disagree."),
    ContractField("fail_closed", "bool", "Whether campaign blocks mutation."),
    ContractField("mutation_allowed", "bool", "Whether typed gates allow mutation."),
    ContractField("publication_allowed", "bool", "Whether typed gates allow publish."),
    ContractField(
        "folded_plan_row_ids",
        "tuple[str, ...]",
        "Plan rows folded into this read-only campaign lane.",
    ),
    ContractField(
        "governed_exception_store_path",
        "str",
        "Read-only governed-exception lifecycle store consumed by the campaign.",
    ),
    ContractField(
        "governed_exception_pending_count",
        "int",
        "Open governed-exception lifecycle rows blocking the campaign.",
    ),
    ContractField(
        "governed_exception_error_count",
        "int",
        "Parse/validation errors while loading governed-exception lifecycle rows.",
    ),
    ContractField(
        "governed_exception_status",
        "str",
        "Governed-exception debt summary.",
    ),
    ContractField(
        "bypass_posture",
        "str",
        "Publication posture derived from exception debt and push proof.",
    ),
    ContractField(
        "bypass_publication_transport_retired",
        "bool",
        "Whether raw bypass publication transport is retired by normal push proof.",
    ),
    ContractField("latest_push_report_path", "str", "Governed push proof report."),
    ContractField("latest_push_report_status", "str", "Governed push proof status."),
    ContractField(
        "latest_push_report_head_commit",
        "str",
        "Head commit covered by governed push proof.",
    ),
    ContractField(
        "latest_push_report_published_remote",
        "bool",
        "Whether push proof shows remote publication.",
    ),
    ContractField(
        "latest_push_report_post_push_green",
        "bool",
        "Whether push proof passed post-push verification.",
    ),
    ContractField(
        "latest_push_report_matches_current_head",
        "bool",
        "Whether selected push proof applies to current HEAD.",
    ),
    ContractField(
        "publication_proof_summary",
        "str",
        "Compact explain-back of exception debt and push proof.",
    ),
    ContractField("pending_packet_id", "str", "Blocking packet id, if any."),
    ContractField("pending_packet_required_command", "str", "Required packet command."),
    ContractField("codex_next_command", "str", "Codex actor next command."),
    ContractField("claude_next_command", "str", "Claude actor next command."),
    ContractField("roles", "tuple[DevelopmentCampaignRoleState, ...]", "Role rows."),
    ContractField("proof_requirements", "tuple[str, ...]", "Campaign proof gates."),
)


DEVELOPMENT_CAMPAIGN_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="RemoteControlCollaborationCampaign",
        owner_layer="governance_commands",
        purpose=(
            "Read-only `/develop campaign` report for Codex/Claude remote-control "
            "dogfood. It makes remote-control transport proof, role lanes, "
            "pending packet blockers, and fail-closed mutation/publication state "
            "visible without becoming an executor."
        ),
        required_fields=REMOTE_CONTROL_CAMPAIGN_FIELDS,
        runtime_model="dev.scripts.devctl.commands.development.models:DevelopmentCampaignReport",
        startup_surface_tokens=(
            "remote_control_active",
            "mode_drift",
            "governed_exception_status",
            "bypass_posture",
            "latest_push_report_status",
            "mutation_allowed",
            "publication_allowed",
            "pending_packet_id",
        ),
    ),
    ContractSpec(
        contract_id="DevelopmentCampaignRoleState",
        owner_layer="governance_commands",
        purpose=(
            "One read-only actor lane projected inside the remote-control "
            "campaign report."
        ),
        required_fields=(
            ContractField("actor_id", "str", "Actor id."),
            ContractField("role", "str", "Role lane."),
            ContractField("session_id", "str", "Provider session id."),
            ContractField("status", "str", "Runtime row status."),
            ContractField("mutation_mode", "str", "Runtime mutation mode."),
            ContractField("active_packet_id", "str", "Active packet for the lane."),
            ContractField("may_mutate", "bool", "Agent-loop mutation decision."),
            ContractField("required_action", "str", "Agent-loop required action."),
            ContractField(
                "user_action",
                "str",
                "Operator-readable action label derived from required_action.",
            ),
            ContractField(
                "continuation_goal",
                "str",
                "Readable goal summary when the lane must continue instead of stop.",
            ),
            ContractField("proof_state", "str", "Agent-loop proof state."),
            ContractField("blocker", "str", "Current blocker."),
            ContractField("next_command", "str", "Role-scoped next command."),
        ),
        runtime_model="dev.scripts.devctl.commands.development.models:DevelopmentCampaignRoleState",
        startup_surface_tokens=("actor_id", "role", "may_mutate", "next_command"),
    ),
)


__all__ = ["DEVELOPMENT_CAMPAIGN_STATE_CONTRACTS"]
