"""Keystone plan-runtime guard contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec

PLAN_KEYSTONE_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="ContractRegistryCompositeKeyUniqueness",
        owner_layer="governance_core",
        purpose=(
            "Guard report proving contract_registry rows are unique by "
            "contract id and schema version, with known divergent-owner "
            "exceptions surfaced as policy decisions."
        ),
        required_fields=(
            ContractField("ok", "bool", "Whether no blocking duplicate rows were found."),
            ContractField("registry_path", "str", "Registry JSONL path scanned."),
            ContractField("scan_count", "int", "Registry rows scanned."),
            ContractField(
                "duplicate_cluster_count",
                "int",
                "Duplicate contract/schema clusters found.",
            ),
            ContractField("warning_count", "int", "Same-owner duplicate warnings."),
            ContractField(
                "policy_decision_required_count",
                "int",
                "Known policy TODO duplicate clusters.",
            ),
            ContractField("violation_count", "int", "Blocking duplicate violations."),
            ContractField("warnings", "tuple[dict[str, object], ...]", "Warning rows."),
            ContractField(
                "policy_todos",
                "tuple[dict[str, object], ...]",
                "Known policy-decision rows.",
            ),
            ContractField("violations", "tuple[dict[str, object], ...]", "Violation rows."),
        ),
        runtime_model=(
            "dev.scripts.checks.contract_registry_composite_key_uniqueness.command:"
            "ContractRegistryCompositeKeyUniqueness"
        ),
        startup_surface_tokens=("scan_count", "duplicate_cluster_count", "violation_count"),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="CheckNonTrivialOutputProofCommand",
        owner_layer="governance_core",
        purpose=(
            "Guard report for FeatureProofReceipt evidence quality, proving "
            "proven receipts cite resolved, non-circular pytest-node output proof."
        ),
        required_fields=(
            ContractField("ok", "bool", "Whether no unledgered proof violations remain."),
            ContractField("receipt_root", "str", "FeatureProofReceipt artifact root scanned."),
            ContractField("scan_count", "int", "FeatureProofReceipt files scanned."),
            ContractField("proven_passed_count", "int", "Proven-passed receipts checked."),
            ContractField("assertions_evaluated_count", "int", "Proof assertions evaluated."),
            ContractField("violation_count", "int", "Unledgered proof violations."),
            ContractField("failure_reasons", "tuple[str, ...]", "Distinct proof failure reasons."),
            ContractField("violations", "tuple[dict[str, object], ...]", "Machine-readable proof violations."),
            ContractField("ledgered_violation_count", "int", "Baseline violations covered by ledger."),
            ContractField("remediation_ledger_path", "str", "JSONL remediation ledger path."),
            ContractField("remediation_findings_written", "int", "New ledger rows written."),
            ContractField("warnings", "tuple[str, ...]", "Invalid or unreadable receipt warnings."),
        ),
        runtime_model=(
            "dev.scripts.checks.non_trivial_output_proof.command:"
            "NonTrivialOutputProofGuardReport"
        ),
        startup_surface_tokens=("proven_passed_count", "violation_count"),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="ContractRegistryCompositeKeyUniquenessCommand",
        owner_layer="governance_core",
        purpose=(
            "Stable backward-compatible command shim for the modular contract "
            "registry composite-key uniqueness guard."
        ),
        required_fields=(
            ContractField("shim_path", "str", "Compatibility shim path."),
            ContractField("target_path", "str", "Canonical modular command path."),
        ),
        runtime_model=(
            "dev.scripts.checks.contract_registry_composite_key_uniqueness.command:"
            "ContractRegistryCompositeKeyUniquenessCommand"
        ),
        startup_surface_tokens=("shim_path", "target_path"),
        registry_entry_kind="authority_composition",
    ),
)

__all__ = ["PLAN_KEYSTONE_STATE_CONTRACTS"]
