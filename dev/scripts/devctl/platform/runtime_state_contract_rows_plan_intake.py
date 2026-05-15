"""Plan-ingestion runtime-state contract rows."""

from __future__ import annotations

from ..runtime.master_plan_contract import IngestionProvenance
from ..runtime.plan_source_retention_models import PlanSourceSnapshot
from .contracts import ContractField, ContractSpec, CrossLinkSpec

PLAN_INTAKE_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="IngestionProvenance",
        owner_layer="governance_runtime",
        purpose=(
            "Typed source-composition evidence recording where a plan row or "
            "other ingested authority signal came from before projection."
        ),
        required_fields=(
            ContractField("source_file", "str", "Source path or packet reference."),
            ContractField("source_line", "int", "Source line when available."),
            ContractField("source_kind", "str", "Source family observed by ingestion."),
            ContractField("source_hash", "str", "Stable hash of the ingested source."),
            ContractField("observed_at_utc", "str", "UTC timestamp when the source was observed."),
            ContractField(
                "section_authority",
                "str",
                "Typed authority or reducer section that accepted the source.",
            ),
        ),
        runtime_model=f"{IngestionProvenance.__module__}:{IngestionProvenance.__qualname__}",
        startup_surface_tokens=("source_file", "source_kind", "section_authority"),
        registry_entry_kind="authority_composition",
        registry_ownership_mode="system",
    ),
    ContractSpec(
        contract_id="BridgeSeparationGuard",
        owner_layer="governance_core",
        purpose=(
            "Typed authority-composition row for the report-only guard that "
            "keeps control-plane modules from depending on bridge projection helpers."
        ),
        required_fields=(
            ContractField("guard_id", "str", "Stable guard identifier used in plan and guard evidence."),
            ContractField("ok", "bool", "Whether the report command executed successfully."),
            ContractField("report_only", "bool", "Whether current violations are advisory instead of failing."),
            ContractField("would_fail", "bool", "Whether strict enforcement would fail on current findings."),
            ContractField("scan_roots", "tuple[str, ...]", "Control-plane roots scanned by the guard."),
            ContractField("checked_paths", "tuple[str, ...]", "Control-plane paths scanned by the guard."),
            ContractField("violation_count", "int", "Number of bridge-projection dependency findings."),
            ContractField("violations", "tuple[dict[str, object], ...]", "Machine-readable guard findings."),
            ContractField("migration_policy", "str", "Policy explaining when the guard can become strict."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_runtime_bridge_projection_separation:"
            "BridgeSeparationGuard"
        ),
        startup_surface_tokens=("guard_id", "report_only", "would_fail"),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="PlanRowContractRefsResolveGuard",
        owner_layer="governance_core",
        purpose=(
            "Report-only guard proving PlanRow contract references resolve "
            "against the repo-owned contract registry."
        ),
        required_fields=(
            ContractField("guard_id", "str", "Stable guard identifier."),
            ContractField("ok", "bool", "Whether the guard executed successfully."),
            ContractField("report_only", "bool", "Whether findings are advisory."),
            ContractField("would_fail", "bool", "Whether strict mode would fail."),
            ContractField("plan_row_count", "int", "PlanRow rows scanned."),
            ContractField(
                "registered_contract_count",
                "int",
                "Registered contract ids available for resolution.",
            ),
            ContractField("orphan_count", "int", "Unresolved contract refs found."),
            ContractField("orphan_rate", "float", "Unresolved contract-ref rate."),
            ContractField("orphans", "tuple[dict[str, object], ...]", "Sample orphan refs."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_plan_row_contract_refs_resolve:"
            "PlanRowContractRefsResolveGuard"
        ),
        startup_surface_tokens=("guard_id", "orphan_count", "orphan_rate"),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="ContextGraphSnapshotFreshnessGuard",
        owner_layer="governance_core",
        purpose=(
            "Report-only guard detecting drift between the latest "
            "ContextGraphSnapshot artifact and current HEAD."
        ),
        required_fields=(
            ContractField("guard_id", "str", "Stable guard identifier."),
            ContractField("ok", "bool", "Whether the guard executed successfully."),
            ContractField("report_only", "bool", "Whether findings are advisory."),
            ContractField("would_fail", "bool", "Whether strict mode would fail."),
            ContractField("head_sha", "str", "Current git HEAD checked."),
            ContractField("latest_snapshot_path", "str", "Latest snapshot artifact path."),
            ContractField(
                "latest_snapshot_commit_hash",
                "str",
                "Commit hash recorded by the latest snapshot.",
            ),
            ContractField("snapshot_count", "int", "Snapshot artifacts found."),
            ContractField("drift", "bool", "Whether the latest snapshot is stale."),
            ContractField("detail", "str", "Human-readable drift detail."),
        ),
        runtime_model=(
            "dev.scripts.checks.context_graph_snapshot_freshness.command:"
            "ContextGraphSnapshotFreshnessGuard"
        ),
        startup_surface_tokens=("guard_id", "drift", "latest_snapshot_commit_hash"),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="ActionResultStatusDomainGuard",
        owner_layer="governance_core",
        purpose=(
            "Report-only guard checking emitted ActionResult.status literals "
            "against the declared ActionOutcome domain."
        ),
        required_fields=(
            ContractField("guard_id", "str", "Stable guard identifier."),
            ContractField("ok", "bool", "Whether the guard executed successfully."),
            ContractField("report_only", "bool", "Whether findings are advisory."),
            ContractField("would_fail", "bool", "Whether strict mode would fail."),
            ContractField("declared_domain", "tuple[str, ...]", "Allowed status literals."),
            ContractField("files_scanned", "int", "Python files scanned."),
            ContractField("violation_count", "int", "Out-of-domain literals found."),
            ContractField("violations", "tuple[dict[str, object], ...]", "Sample findings."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_action_result_status_domain:"
            "ActionResultStatusDomainGuard"
        ),
        startup_surface_tokens=("guard_id", "violation_count", "declared_domain"),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="TaskStartedAdrPrecedentLinkingGuard",
        owner_layer="governance_core",
        purpose=(
            "Report-only guard checking codex task_started packets preserve "
            "ADR precedent, evidence refs, packet anchors, and plan-family links."
        ),
        required_fields=(
            ContractField("guard_id", "str", "Stable guard identifier."),
            ContractField("ok", "bool", "Whether the guard executed successfully."),
            ContractField("report_only", "bool", "Whether findings are advisory."),
            ContractField("would_fail", "bool", "Whether strict mode would fail."),
            ContractField(
                "event_log_path",
                "str",
                "Review-channel event log scanned.",
            ),
            ContractField(
                "task_started_count",
                "int",
                "Codex task_started packets scanned.",
            ),
            ContractField(
                "precedent_linked_count",
                "int",
                "task_started packets that cite a preceding packet.",
            ),
            ContractField(
                "violation_count",
                "int",
                "Packets missing ADR/evidence links.",
            ),
            ContractField(
                "violations",
                "tuple[dict[str, object], ...]",
                "Sample findings.",
            ),
            ContractField("errors", "tuple[str, ...]", "Load or parse errors."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_task_started_adr_precedent_linking:"
            "TaskStartedAdrPrecedentLinkingGuard"
        ),
        startup_surface_tokens=(
            "guard_id",
            "violation_count",
            "precedent_linked_count",
        ),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="TypedNamespaceCompositionGuard",
        owner_layer="governance_core",
        purpose=(
            "Guard requiring typed namespace authority files to import their "
            "canonical authority module or document explicit non-composition "
            "rationale."
        ),
        required_fields=(
            ContractField("guard_id", "str", "Stable guard identifier."),
            ContractField("ok", "bool", "Whether the guard passed."),
            ContractField("report_only", "bool", "Whether findings are advisory."),
            ContractField("would_fail", "bool", "Whether strict mode would fail."),
            ContractField("scanned_file_count", "int", "Namespace files scanned."),
            ContractField("canonical_file_count", "int", "Canonical files skipped."),
            ContractField(
                "composed_file_count",
                "int",
                "Files importing their canonical authority.",
            ),
            ContractField(
                "rationale_file_count",
                "int",
                "Files with explicit non-composition rationale.",
            ),
            ContractField("violation_count", "int", "Composition violations found."),
            ContractField("violations", "tuple[dict[str, object], ...]", "Findings."),
            ContractField("errors", "tuple[str, ...]", "Read or parse errors."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_typed_namespace_composition:"
            "TypedNamespaceCompositionGuard"
        ),
        startup_surface_tokens=("guard_id", "violation_count", "composed_file_count"),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="RuntimeStateIgnorePostureGuard",
        owner_layer="governance_core",
        purpose=(
            "Guard requiring local runtime-state receipt stores to be covered "
            "by git ignore rules and absent from the tracked index."
        ),
        required_fields=(
            ContractField("guard_id", "str", "Stable guard identifier."),
            ContractField("ok", "bool", "Whether the guard passed."),
            ContractField("report_only", "bool", "Whether findings are advisory."),
            ContractField("would_fail", "bool", "Whether strict mode would fail."),
            ContractField("checked_path_count", "int", "Runtime-state paths checked."),
            ContractField("ignored_path_count", "int", "Paths covered by ignore rules."),
            ContractField("tracked_path_count", "int", "Paths still tracked by git."),
            ContractField("violation_count", "int", "Ignore posture violations found."),
            ContractField("violations", "tuple[dict[str, object], ...]", "Findings."),
            ContractField("errors", "tuple[str, ...]", "Git command errors."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_runtime_state_ignore_posture:"
            "RuntimeStateIgnorePostureGuard"
        ),
        startup_surface_tokens=("guard_id", "tracked_path_count", "violation_count"),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="CommitBodyPacketAnchorsGuard",
        owner_layer="governance_core",
        purpose=(
            "Report-only guard checking MP slice commit messages preserve "
            "review-channel packet or task_started provenance anchors."
        ),
        required_fields=(
            ContractField("guard_id", "str", "Stable guard identifier."),
            ContractField("ok", "bool", "Whether the guard executed successfully."),
            ContractField("report_only", "bool", "Whether findings are advisory."),
            ContractField("would_fail", "bool", "Whether strict mode would fail."),
            ContractField("max_count", "int", "Maximum commits scanned."),
            ContractField("scanned_commit_count", "int", "Commits scanned."),
            ContractField(
                "mp_slice_commit_count",
                "int",
                "MP slice commits scanned.",
            ),
            ContractField(
                "violation_count",
                "int",
                "Commits missing packet anchors.",
            ),
            ContractField(
                "violations",
                "tuple[dict[str, object], ...]",
                "Sample findings.",
            ),
            ContractField("errors", "tuple[str, ...]", "Git log errors."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_commit_body_packet_anchors:"
            "CommitBodyPacketAnchorsGuard"
        ),
        startup_surface_tokens=(
            "guard_id",
            "violation_count",
            "mp_slice_commit_count",
        ),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="CommitMessageRowIdResolvesGuard",
        owner_layer="governance_core",
        purpose=(
            "Guard checking commit-message MP row references, packet "
            "decomposition evidence, corrupted persisted titles, and applied "
            "row commit anchors."
        ),
        required_fields=(
            ContractField("guard_id", "str", "Stable guard identifier."),
            ContractField("ok", "bool", "Whether the guard passed."),
            ContractField("scanned_commit_count", "int", "Commits scanned."),
            ContractField("referenced_row_count", "int", "Referenced rows found."),
            ContractField("violation_count", "int", "Violations found."),
            ContractField(
                "violations",
                "tuple[dict[str, object], ...]",
                "Sample findings.",
            ),
            ContractField("errors", "tuple[str, ...]", "Read or git errors."),
            ContractField("warnings", "tuple[str, ...]", "Non-blocking warnings."),
        ),
        runtime_model=(
            "dev.scripts.checks.check_commit_message_row_id_resolves:"
            "CommitMessageRowIdResolvesGuard"
        ),
        startup_surface_tokens=(
            "guard_id",
            "referenced_row_count",
            "violation_count",
        ),
        registry_entry_kind="authority_composition",
    ),
    ContractSpec(
        contract_id="PlanIntentIngestionReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed receipt proving an agent-authored plan source was converted "
            "into PlanRow authority or recorded as an explicit terminal outcome."
        ),
        required_fields=(
            ContractField("receipt_id", "str", "Stable receipt id for this attempt."),
            ContractField("action_id", "str", "TypedAction id for this ingestion attempt."),
            ContractField("source_kind", "str", "Source family such as chat, file, markdown_plan_file, or packet."),
            ContractField("source_ref", "str", "Evidence reference for the source."),
            ContractField("status", "str", "accepted, duplicate, rejected, obsolete, or preview."),
            ContractField("reason", "str", "Bounded outcome reason."),
            ContractField("target_kind", "str", "plan_row or terminal_receipt."),
            ContractField("target_ref", "str", "Typed plan target ref when available."),
            ContractField("correlation_id", "str", "Parent lineage shared with the TypedAction and state-store write."),
            ContractField("causation_id", "str", "Immediate source lineage that triggered ingestion."),
            ContractField("run_id", "str", "Plan-ingestion run lineage for this receipt."),
            ContractField("row_ids", "tuple[str, ...]", "PlanRow ids written or previewed."),
            ContractField("store_statuses", "tuple[str, ...]", "Per-row JSONL upsert statuses."),
            ContractField("terminal_status", "str", "Terminal receipt class when no PlanRow is written."),
            ContractField("packet_id", "str", "Packet evidence id for packet-backed plan sources."),
            ContractField("path", "str", "Typed plan store path."),
            ContractField("receipt_path", "str", "Append-only receipt store path."),
            ContractField("source_hash", "str", "Hash of the ingested plan source."),
            ContractField(
                "source_snapshot_ids",
                "tuple[str, ...]",
                "Durable PlanSourceSnapshot ids written for packet/file/body sources.",
            ),
            ContractField("source_snapshot_path", "str", "Append-only source snapshot store path."),
            ContractField("canonical_source_hash", "str", "Hash of the retained canonical source body."),
            ContractField("source_packet_expires_at_utc", "str", "Packet expiry timestamp when known."),
            ContractField("source_retention_status", "str", "protected, snapshotted, packet_only, missing, or preview."),
            ContractField("source_integrity_status", "str", "ok, packet_expired_snapshot_ok, dangling, or unknown."),
            ContractField(
                "source_completeness_status",
                "str",
                "full_plan_retained, missing_required_anchors, not_required, or unknown.",
            ),
            ContractField(
                "source_required_anchor_count",
                "int",
                "Required full-plan anchor count for this retained source.",
            ),
            ContractField(
                "source_matched_anchor_count",
                "int",
                "Matched required full-plan anchor count for this retained source.",
            ),
            ContractField(
                "source_missing_required_anchors",
                "tuple[str, ...]",
                "Required full-plan anchors absent from the retained source.",
            ),
            ContractField("source_integrity_checked_at_utc", "str", "UTC timestamp of source-integrity classification."),
            ContractField(
                "composition_disposition_matrix",
                "tuple[dict[str, object], ...]",
                "Phase-0 disposition entries describing why each ingested row does not duplicate existing authority.",
            ),
            ContractField(
                "command_manifest_proofs",
                "tuple[dict[str, object], ...]",
                "Registry-backed proof for plan-referenced commands that already exist or remain aspirational.",
            ),
            ContractField(
                "guard_maturity_records",
                "tuple[dict[str, object], ...]",
                "Best-effort GuardMaturity classifications derived from the check catalog and bundle registry.",
            ),
            ContractField(
                "repo_state_fingerprint",
                "dict[str, object]",
                "Best-effort repo/git fingerprint captured alongside the ingestion receipt.",
            ),
            ContractField(
                "receipt_coverage_inventory",
                "dict[str, object]",
                "Inventory of which existing MP-377 rows already have receipts, packet bindings, snapshots, or missing proof.",
            ),
            ContractField(
                "schema_limit_warning",
                "str",
                "Warning that richer dependency/guard semantics remain in receipt and snapshot metadata until schema migration lands.",
            ),
            ContractField(
                "derived_state_invalidated",
                "bool",
                "Whether this ingestion attempt changed durable state that consumers must reload.",
            ),
            ContractField(
                "derived_state_invalidation",
                "dict[str, object]",
                "Derived-state invalidation metadata for plan and work-decision consumers.",
            ),
            ContractField("recorded_at_utc", "str", "UTC receipt timestamp."),
            ContractField("dry_run", "bool", "Whether writes were suppressed."),
        ),
        runtime_model="dev.scripts.devctl.runtime.plan_intent_ingestion:PlanIntentIngestionReceipt",
        startup_surface_tokens=("status", "row_ids", "correlation_id"),
        cross_links=(
            CrossLinkSpec(
                "action_id",
                "TypedAction",
                "receipt_proves",
                target_node_kind="typed_action",
                target_resolver="action_id",
                required=True,
                validation_policy="must_resolve_when_action_store_exists",
            ),
        ),
    ),
    ContractSpec(
        contract_id="PlanSourceSnapshot",
        owner_layer="governance_runtime",
        purpose=(
            "Durable source-body snapshot for a PlanRow so packet-backed plan "
            "authority remains reconstructable after review-channel packet expiry."
        ),
        required_fields=(
            ContractField("snapshot_id", "str", "Stable source snapshot id."),
            ContractField("plan_row_id", "str", "PlanRow preserved by the snapshot."),
            ContractField("source_kind", "str", "Source kind such as packet or chat."),
            ContractField("source_ref", "str", "Original source reference."),
            ContractField("source_hash", "str", "Hash observed by plan ingestion."),
            ContractField("body_hash", "str", "Hash of retained source_text."),
            ContractField("captured_at_utc", "str", "UTC capture timestamp."),
            ContractField("receipt_id", "str", "PlanIntentIngestionReceipt bound to this snapshot."),
            ContractField("action_id", "str", "TypedAction id bound to this snapshot."),
            ContractField("source_packet_id", "str", "Packet id when packet-backed."),
            ContractField("packet_expires_at_utc", "str", "Packet expiry timestamp when known."),
            ContractField("retention_status", "str", "protected, snapshotted, packet_only, or missing."),
            ContractField("source_integrity_status", "str", "ok, packet_expired_snapshot_ok, dangling, or unknown."),
            ContractField(
                "source_completeness_status",
                "str",
                "full_plan_retained, missing_required_anchors, or not_required.",
            ),
            ContractField("required_anchor_count", "int", "Required full-plan anchor count."),
            ContractField("matched_anchor_count", "int", "Matched full-plan anchor count."),
            ContractField(
                "missing_required_anchors",
                "tuple[str, ...]",
                "Required anchors absent from source_text.",
            ),
            ContractField(
                "composition_disposition",
                "str",
                "Phase-0 disposition assigned to the row backed by this source snapshot.",
            ),
            ContractField(
                "owning_mp_family",
                "str",
                "Owning MP family for the source-backed row.",
            ),
            ContractField(
                "existing_owner_row_refs",
                "tuple[str, ...]",
                "Existing owner rows cited so the retained source does not become parallel authority.",
            ),
            ContractField(
                "packet_binding_refs",
                "tuple[str, ...]",
                "Packet-binding citations carried into retained source metadata.",
            ),
            ContractField(
                "why_not_duplicate",
                "str",
                "Human-readable explanation for why this source-backed row is not duplicate authority.",
            ),
            ContractField(
                "phase_allowed_to_block",
                "str",
                "Earliest phase this row may block once implemented.",
            ),
            ContractField(
                "phase_allowed_to_mutate",
                "str",
                "Planned implementation phase for the source-backed row.",
            ),
            ContractField(
                "schema_limit_warning",
                "str",
                "Warning that richer semantics remain in receipt and snapshot metadata until schema migration lands.",
            ),
            ContractField("source_text", "str", "Retained source text/body."),
            ContractField("source_summary", "str", "Compact source summary."),
            ContractField("snapshot_path", "str", "JSONL snapshot store path."),
        ),
        runtime_model=f"{PlanSourceSnapshot.__module__}:{PlanSourceSnapshot.__qualname__}",
        startup_surface_tokens=(
            "plan_row_id",
            "source_packet_id",
            "retention_status",
            "source_integrity_status",
        ),
        cross_links=(
            CrossLinkSpec(
                "plan_row_id",
                "PlanRow",
                "related_to",
                target_node_kind="plan_row",
                target_id_template="plan:{value}",
                required=False,
                required_when="PlanRow is registered as a platform contract",
                validation_policy="deferred_until_plan_row_contract_registered",
            ),
            CrossLinkSpec(
                "receipt_id",
                "PlanIntentIngestionReceipt",
                "related_to",
                target_node_kind="receipt",
                target_resolver="receipt_id",
                required=True,
                validation_policy="must_resolve",
            ),
            CrossLinkSpec(
                "action_id",
                "TypedAction",
                "related_to",
                target_node_kind="typed_action",
                target_resolver="action_id",
                required=True,
                validation_policy="must_resolve_when_action_store_exists",
            ),
        ),
    ),
)

__all__ = ["PLAN_INTAKE_STATE_CONTRACTS"]
