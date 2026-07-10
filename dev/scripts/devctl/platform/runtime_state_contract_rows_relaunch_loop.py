"""Relaunch-loop runtime-state contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec

RELAUNCH_LOOP_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="SliceClosureEvent",
        owner_layer="governance_runtime",
        purpose=(
            "Typed proof that one bounded AI slice ended and identified the "
            "next slice owner without using packet delivery as launch authority."
        ),
        required_fields=(
            ContractField("slice_closure_event_id", "str", "Stable event id."),
            ContractField("emitted_at_utc", "str", "UTC emission time."),
            ContractField("emitter_actor", "str", "Actor that closed the slice."),
            ContractField("commit_sha", "str", "HEAD after closure, when known."),
            ContractField("plan_ref", "str", "Typed plan row/ref."),
            ContractField("closed_slice_id", "str", "Closed slice id."),
            ContractField("next_slice_target", "SliceTarget", "Next owner and intent."),
            ContractField("push_decision_state", "str", "Typed publication state."),
            ContractField("trace_offset", "int", "JSONL byte offset/idempotency aid."),
            ContractField("source_packet_id", "str", "Packet that seeded the slice."),
        ),
        runtime_model="dev.scripts.devctl.runtime.relaunch_loop_models:SliceClosureEvent",
        startup_surface_tokens=("slice_closure_event_id", "emitter_actor", "next_slice_target"),
    ),
    ContractSpec(
        contract_id="AgentRelaunchTrigger",
        owner_layer="governance_runtime",
        purpose=(
            "Queued scheduler-owned relaunch request derived from a "
            "SliceClosureEvent after quota and idempotency checks."
        ),
        required_fields=(
            ContractField("trigger_id", "str", "Stable trigger id."),
            ContractField("parent_closure_id", "str", "Source SliceClosureEvent id."),
            ContractField("target_actor", "str", "Actor to relaunch."),
            ContractField("launch_command", "TypedLaunchCommand", "Provider-neutral launch preview."),
            ContractField("session_seed_packet_id", "str", "Packet id used for bootstrap seed."),
            ContractField("authority_scope", "AuthorityScope", "Bounded launch authority."),
            ContractField("expected_instruction_revision", "str", "Expected instruction revision."),
            ContractField("quota_token", "RelaunchQuotaToken", "Per-actor/shared quota state."),
            ContractField("queued_at_utc", "str", "UTC queue time."),
            ContractField("status", "str", "pending/dispatched/blocked."),
        ),
        runtime_model="dev.scripts.devctl.runtime.relaunch_loop_models:AgentRelaunchTrigger",
        startup_surface_tokens=("trigger_id", "target_actor", "status"),
    ),
    ContractSpec(
        contract_id="RelaunchQuotaExceeded",
        owner_layer="governance_runtime",
        purpose=(
            "Fail-closed halt receipt for a suspected runaway relaunch loop that "
            "requires explicit operator unblock."
        ),
        required_fields=(
            ContractField("window_start_utc", "str", "Quota window start."),
            ContractField("window_seconds", "int", "Quota window length."),
            ContractField("actor_count", "int", "Target actor count in window."),
            ContractField("actor_threshold", "int", "Per-actor threshold."),
            ContractField("shared_count", "int", "All-actor count in window."),
            ContractField("shared_threshold", "int", "Shared threshold."),
            ContractField("offending_slice_ids", "tuple[str, ...]", "Closure ids in window."),
            ContractField("suspended_actor", "str", "Actor blocked by quota."),
            ContractField("operator_unblock_required", "bool", "Always true for this receipt."),
        ),
        runtime_model="dev.scripts.devctl.runtime.relaunch_loop_models:RelaunchQuotaExceeded",
        startup_surface_tokens=("suspended_actor", "operator_unblock_required"),
    ),
)

__all__ = ["RELAUNCH_LOOP_STATE_CONTRACTS"]
