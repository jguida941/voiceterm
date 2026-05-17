"""Compatibility bundle for review/pipeline runtime-state contract rows."""

from __future__ import annotations

from ..runtime.evidence_receipts import TokenOptimizationDogfoodReceipt
from ..runtime.master_plan_contract import AffectedTestSelection
from ..runtime.role_customization import RoleCommandEnvelope
from .runtime_state_contract_rows_governance_proposed import _spec as _proposal_spec
from .runtime_state_contract_rows_pipeline import PIPELINE_STATE_CONTRACTS
from .runtime_state_contract_rows_review import REVIEW_STATE_CONTRACTS


GOVERNANCE_EXTENSION_STATE_CONTRACTS = (
    _proposal_spec(
        RoleCommandEnvelope,
        "role_id",
        "available_commands",
        "enforcement_mode",
        "fleet_review_toggle",
        "operator_toggle_receipt",
        purpose="Role-as-command-envelope contract with typed enforcement modes.",
    ),
    _proposal_spec(
        AffectedTestSelection,
        "selection_id",
        "changed_paths",
        "contract_refs",
        "local_test_refs",
        "connected_test_refs",
        "selection_reason",
        "selected_at_utc",
        purpose="Contract-linked affected-test selection for slice validation and closure proof.",
    ),
    _proposal_spec(
        TokenOptimizationDogfoodReceipt,
        "receipt_id",
        "optimization_id",
        "feature_lifecycle_proof_id",
        "dogfood_record_id",
        "dogfood_round_ref",
        "before_token_count",
        "after_token_count",
        "capability_preserved_checks",
        "context_preserved_checks",
        "actor_ids",
        "status",
        purpose="Dogfood receipt proving a token optimization preserved capability and context.",
    ),
)


REVIEW_PIPELINE_STATE_CONTRACTS = REVIEW_STATE_CONTRACTS + PIPELINE_STATE_CONTRACTS
