"""State runtime contract rows for the platform blueprint."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec
from .runtime_state_contract_rows_review_pipeline import (
    REVIEW_PIPELINE_STATE_CONTRACTS,
)


RUNTIME_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="CheckResult",
        owner_layer="governance_runtime",
        purpose="Typed check-output envelope carrying step results, enriched status, and ViolationRecords for renderers and downstream consumers.",
        required_fields=(
            ContractField("timestamp", "str", "UTC timestamp for the run."),
            ContractField("success", "bool", "Whether all steps passed."),
            ContractField("total", "int", "Total step count."),
            ContractField("passed", "int", "Passed step count."),
            ContractField("failed", "int", "Failed step count."),
            ContractField("skipped", "int", "Skipped step count."),
            ContractField("steps", "tuple[dict, ...]", "Enriched step dicts with status and violation_summary."),
            ContractField("violations", "tuple[ViolationRecord, ...]", "Typed violation records from failed steps."),
        ),
        runtime_model="dev.scripts.devctl.runtime.check_result_models:CheckResult",
        startup_surface_tokens=("success", "total", "failed"),
    ),
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
                "operator_context",
                "OperatorContext",
                "Typed operator-presence metadata for mode-aware governance decisions.",
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
        startup_surface_tokens=("approvals", "active_runs", "review_bridge"),
    ),
    *REVIEW_PIPELINE_STATE_CONTRACTS,
)
