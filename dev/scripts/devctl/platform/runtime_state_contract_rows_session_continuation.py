"""Agent session-continuation runtime-state contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec

AGENT_SESSION_CONTINUATION_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="AgentSessionContinuation",
        owner_layer="governance_runtime",
        purpose=(
            "Typed rehydration state for treating a new agent process as a "
            "runtime restart rather than an authority reset."
        ),
        required_fields=(
            ContractField("continuation_id", "str", "Stable id derived from the bootstrap hash."),
            ContractField("agent_id", "str", "Actor expected to load the continuation."),
            ContractField("provider", "str", "Provider or agent family for the new process."),
            ContractField("role", "str", "Runtime role loaded by the new process."),
            ContractField("working_tree", "str", "Workspace root used for rehydration."),
            ContractField("branch", "str", "Current git branch at bootstrap time."),
            ContractField(
                "session_id_or_transcript_path",
                "str",
                "Provider session id, metadata path, transcript path, or log path when known.",
            ),
            ContractField("last_seen_packet_id", "str", "Latest packet id visible to the actor."),
            ContractField(
                "last_acknowledged_packet_id",
                "str",
                "Latest packet the actor has acknowledged through the typed lifecycle path.",
            ),
            ContractField(
                "current_assignment",
                "str",
                "Current instruction, slice, or assignment loaded into the bootstrap.",
            ),
            ContractField("dirty_paths_count", "int", "Dirty or untracked path count."),
            ContractField("dirty_paths_status", "str", "known or unknown; unknown never means clean."),
            ContractField("current_blockers", "str", "Comma-separated blocker labels."),
            ContractField("resume_command", "str", "Command that writes the matching resume proof."),
            ContractField(
                "continuation_hash",
                "str",
                "Stable hash of the typed continuation state, excluding timestamps.",
            ),
            ContractField(
                "bootstrap_hash",
                "str",
                "Hash of the rendered bootstrap content, when that content is materialized.",
            ),
            ContractField(
                "continuation_mode",
                "str",
                "typed_rehydration unless a provider proves true runtime resume.",
            ),
            ContractField("generated_at_utc", "str", "UTC time this continuation was built."),
            ContractField("authority_result", "str", "allowed or blocked for the rehydrated state."),
            ContractField("result", "str", "Expected state for continuation packets."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.agent_session_continuation:"
            "AgentSessionContinuationState"
        ),
        startup_surface_tokens=("continuation_id", "bootstrap_hash", "continuation_mode"),
    ),
    ContractSpec(
        contract_id="AgentResumeReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed proof that a newly started provider session loaded an "
            "AgentSessionContinuation before acting."
        ),
        required_fields=(
            ContractField("receipt_id", "str", "Stable receipt id for this rehydration proof."),
            ContractField("continuation_id", "str", "Continuation id this receipt loaded."),
            ContractField("agent_id", "str", "Actor that loaded the continuation."),
            ContractField("provider", "str", "Provider or agent family that produced the receipt."),
            ContractField("role", "str", "Runtime role loaded by the provider session."),
            ContractField("working_tree", "str", "Workspace root used for the resumed process."),
            ContractField("branch", "str", "Current git branch at receipt time."),
            ContractField(
                "session_id_or_transcript_path",
                "str",
                "Provider session id, transcript path, metadata path, or log path.",
            ),
            ContractField("last_seen_packet_id", "str", "Latest packet loaded by the actor."),
            ContractField(
                "last_acknowledged_packet_id",
                "str",
                "Latest packet acknowledgement loaded by the actor.",
            ),
            ContractField("current_assignment", "str", "Assignment loaded by the actor."),
            ContractField("dirty_paths_count", "int", "Dirty or untracked path count loaded."),
            ContractField(
                "dirty_paths_status",
                "str",
                "known or unknown dirty-state probe status loaded by the actor.",
            ),
            ContractField("current_blockers", "str", "Blockers loaded by the actor."),
            ContractField("resume_command", "str", "Command used to emit the proof."),
            ContractField("continuation_hash", "str", "Hash of the typed continuation state."),
            ContractField(
                "bootstrap_hash",
                "str",
                "Hash of the rendered bootstrap content, when materialized.",
            ),
            ContractField(
                "continuation_mode",
                "str",
                "typed_rehydration or runtime_resume, never implicit hidden context.",
            ),
            ContractField("started_at_utc", "str", "UTC time the new process bootstrap started."),
            ContractField("observed_at_utc", "str", "UTC time the proof was emitted."),
            ContractField("load_result", "str", "loaded, blocked, or failed state-load result."),
            ContractField("authority_result", "str", "allowed or blocked authority result after loading state."),
            ContractField("result", "str", "loaded, blocked, or failed."),
            ContractField("source", "str", "Surface that emitted the proof."),
            ContractField("source_event_id", "str", "Review-channel event id for the proof."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.agent_session_continuation:"
            "AgentResumeReceiptState"
        ),
        startup_surface_tokens=("receipt_id", "continuation_id", "result"),
    ),
)

__all__ = ["AGENT_SESSION_CONTINUATION_CONTRACTS"]
