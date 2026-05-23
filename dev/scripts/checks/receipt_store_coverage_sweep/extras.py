"""Extra coverage data table and default-classification builder for the sweep."""

from __future__ import annotations

try:
    from ..receipt_store_consumer.defaults import (
        DEFAULT_CLASSIFICATIONS as CONSUMER_CLASSIFICATIONS,
    )
except ImportError:
    from receipt_store_consumer.defaults import (  # type: ignore[no-redef]
        DEFAULT_CLASSIFICATIONS as CONSUMER_CLASSIFICATIONS,
    )

from .models import ReceiptStoreCoverage


_EXTRA_COVERAGE_BY_STORE: dict[str, dict[str, tuple[str, ...]]] = {
    "dev/state/plan_index.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_current_plan_authority.py",
            "dev/scripts/checks/check_plan_row_must_advance.py",
            "dev/scripts/checks/check_every_applied_row_has_closure_receipt.py",
        ),
        "provenance_refs": (
            "PlanIndexAuthority",
            "PlanIntentIngestionReceipt",
            "PlanRowClosureReceipt",
        ),
    },
    "dev/state/plan_source_snapshots.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_no_ingestion_churn_without_advancement.py",
        ),
        "provenance_refs": ("PlanSourceSnapshot",),
    },
    "dev/state/plan_ingestion_receipts.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_no_ingestion_churn_without_advancement.py",
        ),
        "provenance_refs": ("PlanIntentIngestionReceipt",),
    },
    "dev/state/plan_row_closure_receipts.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_every_applied_row_has_closure_receipt.py",
            "dev/scripts/checks/check_slice_finishes_or_reverts.py",
        ),
        "provenance_refs": ("PlanRowClosureReceipt",),
    },
    "dev/state/governed_exception_lifecycles.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_mutation_bypass_graph_closure.py",
        ),
        "provenance_refs": ("GovernedExceptionLifecycle",),
    },
    "dev/state/bypass_lifecycles.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_role_lane_mutation_authority.py",
            "dev/scripts/checks/check_mutation_bypass_graph_closure.py",
        ),
        "provenance_refs": ("BypassLifecycle",),
    },
    "dev/state/artifact_receipts.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_receipt_store_has_active_consumer.py",
        ),
        "provenance_refs": ("ArtifactReceipt",),
    },
    "dev/state/baseline_authority_inventories.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_baseline_authority_inventory.py",
        ),
        "provenance_refs": ("BaselineAuthorityInventoryReceipt",),
    },
    "dev/state/contract_registry.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_platform_contract_closure.py",
            "dev/scripts/checks/check_systemmap_covers_contract_registry.py",
        ),
        "provenance_refs": ("ContractRegistryRow",),
    },
    "dev/state/ground_truth_probe_receipts.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_ground_truth_probe_gate.py",
        ),
        "provenance_refs": ("GroundTruthProbeReceipt",),
    },
    "dev/state/topology_hardcode_inventory.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_no_new_hardcoded_provider_authority.py",
            "dev/scripts/checks/check_no_new_topology_count_coupling.py",
        ),
        "provenance_refs": ("TopologyHardcodeInventory",),
    },
    "dev/state/non_trivial_output_proof_remediation_findings.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_non_trivial_output_proof.py",
        ),
        "provenance_refs": ("RemediationFindingLedger",),
    },
    "dev/state/role_review_completed_remediation_findings.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_role_review_completed.py",
        ),
        "provenance_refs": ("RemediationFindingLedger",),
    },
    "dev/state/transition_modules.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_governed_transitions.py",
        ),
        "provenance_refs": ("TransitionModuleManifest",),
    },
    "dev/state/raw_git_bypass_receipts.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_mutation_bypass_graph_closure.py",
        ),
        "provenance_refs": ("RawGitBypassReceipt",),
    },
    "dev/reports/feature_proof_receipts": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_receipt_schema_validation.py",
            "dev/scripts/checks/check_receipt_commit_anchor_refs.py",
        ),
        "provenance_refs": ("FeatureProofReceipt",),
    },
    "dev/reports/push": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_push_complete_proof.py",
        ),
        "provenance_refs": ("PushAuthorizationRecord",),
    },
    "dev/reports/dogfood/runs.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_dogfood_route_round_trip.py",
        ),
        "provenance_refs": ("DogfoodRun",),
    },
    "dev/reports/git_mutation_proof_receipts.jsonl": {
        "schema_guard_refs": (
            "dev/scripts/checks/check_commit_complete_proof.py",
            "dev/scripts/checks/check_push_complete_proof.py",
        ),
        "provenance_refs": ("GitMutationProofReceipt",),
    },
}


def _default_classifications() -> tuple[ReceiptStoreCoverage, ...]:
    coverage: dict[str, ReceiptStoreCoverage] = {}
    for classification in CONSUMER_CLASSIFICATIONS:
        extra = _EXTRA_COVERAGE_BY_STORE.get(classification.store_path, {})
        coverage[classification.store_path] = ReceiptStoreCoverage(
            store_path=classification.store_path,
            writer_refs=classification.writer_refs,
            reader_refs=classification.reader_refs,
            schema_guard_refs=extra.get("schema_guard_refs", ()),
            provenance_refs=extra.get("provenance_refs", ()),
            archive_disposition_refs=extra.get("archive_disposition_refs", ()),
        )
    for store_path, extra in _EXTRA_COVERAGE_BY_STORE.items():
        coverage.setdefault(
            store_path,
            ReceiptStoreCoverage(
                store_path=store_path,
                writer_refs=extra.get("writer_refs", ()),
                reader_refs=extra.get("reader_refs", ()),
                schema_guard_refs=extra.get("schema_guard_refs", ()),
                provenance_refs=extra.get("provenance_refs", ()),
                archive_disposition_refs=extra.get("archive_disposition_refs", ()),
            ),
        )
    return tuple(sorted(coverage.values(), key=lambda item: item.store_path))


DEFAULT_CLASSIFICATIONS: tuple[ReceiptStoreCoverage, ...] = _default_classifications()
