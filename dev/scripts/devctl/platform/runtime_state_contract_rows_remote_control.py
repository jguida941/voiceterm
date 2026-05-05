"""Remote-control runtime contract rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contracts import ContractField, ContractSpec

if TYPE_CHECKING:
    from ..runtime.remote_control_attachment_models import RemoteControlAttachmentState
    from ..runtime.remote_control_invocation_receipt import (
        RemoteControlInvocationReceipt,
    )

    _RUNTIME_MODEL_REFS: tuple[
        type[RemoteControlAttachmentState],
        type[RemoteControlInvocationReceipt],
    ]


REMOTE_CONTROL_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="RemoteControlAttachmentState",
        owner_layer="governance_runtime",
        purpose=(
            "Provider-scoped typed attachment artifact for an external "
            "remote-control operator session, shared by reviewer runtime, "
            "startup, dashboard, and remote-control command surfaces."
        ),
        required_fields=(
            ContractField("provider", "str", "Provider adapter attached to the remote-control session."),
            ContractField("role", "str", "Actor role represented by the attachment."),
            ContractField("attachment_id", "str", "Stable attachment identity for the provider-scoped session."),
            ContractField("session_name", "str", "Human-readable provider session label."),
            ContractField("remote_session_id", "str", "Provider-native remote session id."),
            ContractField("session_url", "str", "Provider-native remote session URL."),
            ContractField("status", "str", "Attachment lifecycle status."),
            ContractField("transport", "str", "Transport or artifact family carrying the attachment."),
            ContractField("attached_at_utc", "str", "UTC timestamp when this attachment was first bound."),
            ContractField("last_seen_utc", "str", "UTC timestamp of the latest observed attachment heartbeat."),
            ContractField("metadata_path", "str", "Path to the provider-scoped attachment metadata artifact."),
            ContractField("launcher_source", "str", "Declared launcher source for compatibility and diagnostics."),
            ContractField("host_pid", "int | None", "Local host process id when one is visible."),
            ContractField("host_session_label", "str", "Local host session label when one is visible."),
            ContractField("heartbeat_ttl_seconds", "int", "Heartbeat TTL used to classify attachment freshness."),
            ContractField("previous_operator_mode", "str", "Operator mode that should be restored after detach."),
            ContractField("entrypoint", "str", "Remote-control entrypoint used to bind the session."),
            ContractField("physical_remote_control_confirmed", "bool", "Whether runtime evidence confirmed physical remote-control attachment."),
            ContractField("physical_confirmation_method", "str", "Evidence class used to classify physical remote-control confirmation."),
            ContractField("source_hook_event_name", "str", "Claude hook event that observed the remote-control prompt."),
            ContractField("source_hook_prompt", "str", "Prompt text observed by the Claude hook."),
            ContractField("source_hook_command_name", "str", "Slash command name observed by the Claude hook when available."),
            ContractField("source_hook_session_id", "str", "Claude session id carried by the hook payload."),
            ContractField("source_hook_transcript_path", "str", "Claude transcript path carried by the hook payload."),
            ContractField("source_hook_dedupe_key", "str", "Stable key used to dedupe multiple hook events for one activation."),
            ContractField("source_proof_channel", "str", "Proof channel used to bind source evidence."),
            ContractField("source_proof_observed_at_utc", "str", "UTC timestamp of the proof source observation."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.remote_control_attachment_models:"
            "RemoteControlAttachmentState"
        ),
        startup_surface_tokens=(
            "provider",
            "attachment_id",
            "status",
            "last_seen_utc",
            "entrypoint",
        ),
    ),
    ContractSpec(
        contract_id="RemoteControlInvocationReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Append-only typed audit row for one remote-control lifecycle "
            "command invocation, proving command reachability and receipt "
            "emission without making lifecycle/source-proof claims."
        ),
        required_fields=(
            ContractField("invocation_at_utc", "str", "UTC timestamp when the lifecycle invocation was recorded."),
            ContractField("action", "str", "Remote-control lifecycle action invoked."),
            ContractField("provider", "str", "Provider adapter targeted by the invocation."),
            ContractField("entrypoint", "str", "Remote-control entrypoint invoked."),
            ContractField("launcher_source", "str", "Declared launcher source carried by the invocation."),
            ContractField("target_status_dir", "str", "Status directory targeted by the invocation."),
            ContractField("attachment_id", "str", "Attachment id observed after the invocation."),
            ContractField("attachment_status", "str", "Backward-compatible post-invocation attachment status."),
            ContractField("operator_interaction_mode", "str", "Backward-compatible post-invocation operator interaction mode."),
            ContractField("before_attachment_status", "str", "Attachment status before invocation."),
            ContractField("after_attachment_status", "str", "Attachment status after invocation."),
            ContractField("before_operator_interaction_mode", "str", "Operator interaction mode before invocation."),
            ContractField("after_operator_interaction_mode", "str", "Operator interaction mode after invocation."),
            ContractField("state_change", "str", "Typed state-change classifier emitted by the invocation recorder."),
            ContractField("claimed_source_kind", "str", "Declared source kind supplied by the caller or classifier."),
            ContractField("proven_source_kind", "str", "Proof-backed source kind when available, otherwise unspecified."),
            ContractField("invocation_origin", "str", "Resolved invocation origin recorded with the receipt."),
            ContractField("ok", "bool", "Whether the lifecycle invocation reported success."),
            ContractField("dry_run", "bool", "Whether the invocation ran without mutating state."),
            ContractField("invocation_source", "str", "Raw invocation source string retained for diagnostics."),
            ContractField("error_message", "str", "Failure message recorded for unsuccessful invocations."),
            ContractField("proof_channel", "str", "Proof channel carried by the invocation when available."),
            ContractField("physical_confirmation_method", "str", "Evidence class used to classify physical remote-control confirmation."),
            ContractField("hook_event_name", "str", "Claude hook event that observed the invocation when available."),
            ContractField("hook_prompt", "str", "Prompt text observed by the Claude hook."),
            ContractField("hook_command_name", "str", "Slash command name observed by the Claude hook when available."),
            ContractField("hook_session_id", "str", "Claude session id carried by the hook payload."),
            ContractField("hook_transcript_path", "str", "Claude transcript path carried by the hook payload."),
            ContractField("hook_dedupe_key", "str", "Stable key used to dedupe multiple hook events for one activation."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.remote_control_invocation_receipt:"
            "RemoteControlInvocationReceipt"
        ),
        startup_surface_tokens=(
            "invocation_at_utc",
            "action",
            "provider",
            "ok",
            "state_change",
        ),
    ),
)


__all__ = ["REMOTE_CONTROL_STATE_CONTRACTS"]
