"""State runtime contract rows for the platform blueprint."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


RUNTIME_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="ControlState",
        owner_layer="governance_runtime",
        purpose=(
            "Machine-readable status snapshot for runs, queue state, "
            "approvals, warnings, and errors across clients."
        ),
        required_fields=(
            ContractField("timestamp", "str", "UTC timestamp for the snapshot."),
            ContractField(
                "approvals",
                "ApprovalPolicyState",
                "Approval/waiver state projected into every frontend.",
            ),
            ContractField(
                "active_runs",
                "tuple[ActiveRunState, ...]",
                "Current governed runs visible to CLI/UI clients.",
            ),
            ContractField(
                "review_bridge",
                "ReviewBridgeState",
                "Shared review-channel liveness and heartbeat state.",
            ),
            ContractField(
                "agents",
                "tuple[ReviewAgentState, ...]",
                "Visible review/loop agents participating in the control plane.",
            ),
            ContractField(
                "sources",
                "ControlStateSources",
                "Bounded source paths used to derive the control snapshot.",
            ),
            ContractField(
                "warnings",
                "tuple[str, ...]",
                "Non-blocking warnings carried with the control snapshot.",
            ),
            ContractField(
                "errors",
                "tuple[str, ...]",
                "Blocking errors carried with the control snapshot.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.control_state:ControlState",
    ),
    ContractSpec(
        contract_id="ReviewState",
        owner_layer="governance_runtime",
        purpose=(
            "Machine-readable review-channel snapshot for session metadata, "
            "queue state, packets, bridge status, and agent registry."
        ),
        required_fields=(
            ContractField("action", "str", "Review-channel action that produced the snapshot."),
            ContractField("timestamp", "str", "UTC timestamp for the snapshot."),
            ContractField(
                "ok",
                "bool",
                "Whether the review snapshot resolved without blocking errors.",
            ),
            ContractField(
                "review",
                "ReviewSessionState",
                "Typed review session metadata shared by CLI/UI clients.",
            ),
            ContractField(
                "queue",
                "ReviewQueueState",
                "Pending packet counts and derived next-instruction state.",
            ),
            ContractField(
                "bridge",
                "ReviewBridgeState",
                "Review bridge lifecycle and freshness state.",
            ),
            ContractField(
                "attention",
                "ReviewAttentionState | None",
                "Current top-priority attention state, if any.",
            ),
            ContractField(
                "packets",
                "tuple[ReviewPacketState, ...]",
                "Typed review-channel packets, including approval state.",
            ),
            ContractField(
                "registry",
                "AgentRegistryState",
                "Current agent-registry snapshot for the review surface.",
            ),
            ContractField(
                "warnings",
                "tuple[str, ...]",
                "Non-blocking warnings carried with the review snapshot.",
            ),
            ContractField(
                "errors",
                "tuple[str, ...]",
                "Blocking errors carried with the review snapshot.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.review_state_models:ReviewState",
    ),
)
