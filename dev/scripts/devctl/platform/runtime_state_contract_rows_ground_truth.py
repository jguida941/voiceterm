"""Runtime-truth and ground-truth probe contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec

GROUND_TRUTH_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="RuntimeTruthSnapshot",
        owner_layer="governance_runtime",
        purpose=(
            "Derived reducer over the current ReviewState-centered runtime "
            "tick so design, startup, and `/develop` consumers reuse one "
            "observed-truth view instead of inventing sidecar authority."
        ),
        required_fields=(
            ContractField("generated_at_utc", "str", "UTC generation timestamp."),
            ContractField("source_contract", "str", "Typed source contract reduced."),
            ContractField("source_command", "str", "Command/source that produced the tick."),
            ContractField("interaction_mode", "str", "Resolved operator interaction mode."),
            ContractField("reviewer_mode", "str", "Declared reviewer mode."),
            ContractField("effective_reviewer_mode", "str", "Effective reviewer mode."),
            ContractField("current_instruction", "str", "Current instruction text."),
            ContractField("packet_attention_required", "bool", "Whether packet attention is pending."),
            ContractField("pending_packet_count", "int", "Pending/actionable packet count."),
            ContractField("active_actor_count", "int", "Live actor count."),
            ContractField("live_actor_ids", "tuple[str, ...]", "Live actor ids."),
            ContractField("remote_control_active", "bool", "Whether remote-control proof is active."),
            ContractField("remote_control_method", "str", "Physical proof method."),
            ContractField("remote_control_session_id", "str", "Provider remote session id."),
            ContractField("agent_mind_providers", "tuple[str, ...]", "Agent-mind projections found."),
            ContractField("quality_signal_keys", "tuple[str, ...]", "Startup quality signals present."),
            ContractField("connectivity_contract_count", "int", "Contract rows observed."),
            ContractField("connectivity_warning_count", "int", "Connectivity warning count."),
            ContractField("routing_decision", "str", "Default design routing posture."),
            ContractField("observed_sources", "tuple[RuntimeTruthSource, ...]", "Sources reduced into this tick."),
            ContractField("warnings", "tuple[str, ...]", "Reducer warnings."),
        ),
        runtime_model="dev.scripts.devctl.runtime.runtime_truth_snapshot:RuntimeTruthSnapshot",
        startup_surface_tokens=("interaction_mode", "observed_sources"),
    ),
    ContractSpec(
        contract_id="GroundTruthProbeRunReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Evidence that architecture or proof-channel design ran bounded "
            "ground-truth probes against existing upstream/runtime surfaces "
            "before proposing new typed authority."
        ),
        required_fields=(
            ContractField("created_at_utc", "str", "UTC receipt timestamp."),
            ContractField("base_ref", "str", "Git base ref used for the design pass."),
            ContractField("head_ref", "str", "Git head ref used for the design pass."),
            ContractField("changed_paths_digest", "str", "Digest of trigger paths."),
            ContractField("trigger_kind", "str", "Trigger family for the receipt."),
            ContractField("trigger_paths", "tuple[str, ...]", "Authority/proof paths covered."),
            ContractField("design_ids", "tuple[str, ...]", "Topic or design ids covered."),
            ContractField("required_probe_ids", "tuple[str, ...]", "Required probe ids."),
            ContractField("observed_probe_ids", "tuple[str, ...]", "Probe ids actually observed."),
            ContractField("probe_report_path", "str", "Evidence artifact or command."),
            ContractField("probe_report_sha256", "str", "Evidence digest."),
            ContractField("verdict", "str", "satisfied, missing, stale, or failed."),
            ContractField("warnings", "tuple[str, ...]", "Receipt warnings."),
        ),
        runtime_model="dev.scripts.devctl.runtime.ground_truth_probe_receipt:GroundTruthProbeRunReceipt",
        startup_surface_tokens=("trigger_paths", "verdict"),
    ),
)

__all__ = ["GROUND_TRUTH_STATE_CONTRACTS"]
