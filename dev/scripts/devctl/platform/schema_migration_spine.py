"""Schema-migration policy spine for durable governance stores."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .blueprint import build_platform_blueprint
from .contracts import ContractSpec, PlatformBlueprint

DURABLE_SCHEMA_POLICY_CONTRACT_ID = "DurableSchemaPolicy"
SCHEMA_MIGRATION_SPINE_CONTRACT_ID = "SchemaMigrationSpine"
SCHEMA_MIGRATION_SPINE_SCHEMA_VERSION = 1

REGISTERED_STORE_AUTHORITY_STATUSES = frozenset(
    {
        "planned",
        "registered_advisory",
        "registered_blocking",
        "retired",
    }
)
NON_BLOCKING_STORE_AUTHORITY_STATUSES = frozenset({"planned", "retired"})

_DURABLE_STATE_FIELD_NAMES = frozenset(
    {
        "event_log_path",
        "governed_exception_store_path",
        "log_path",
        "receipt_path",
        "registry_path",
        "snapshot_path",
        "source_snapshot_path",
        "state_path",
    }
)


@dataclass(frozen=True, slots=True)
class DurableSchemaPolicy:
    """Migration and store-authority policy for one durable contract family."""

    contract_id: str
    store_path: str
    store_authority: str
    schema_version_field: str
    compatibility_window: str
    migration_path: str
    rollback_path: str
    store_authority_status: str = "registered_advisory"
    owning_row: str = "MP377-SCHEMA-MIGRATION-SPINE-S1"
    notes: str = ""
    schema_version: int = SCHEMA_MIGRATION_SPINE_SCHEMA_VERSION
    policy_contract_id: str = DURABLE_SCHEMA_POLICY_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SchemaMigrationSpine:
    """Reducer coverage report for durable schema-migration policy."""

    durable_contract_count: int
    policy_count: int
    artifact_schema_count: int
    planned_policy_count: int
    planned_policy_contract_ids: tuple[str, ...]
    ok: bool
    command: str = "check_schema_migration_spine"
    contract_id: str = SCHEMA_MIGRATION_SPINE_CONTRACT_ID
    schema_version: int = SCHEMA_MIGRATION_SPINE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["planned_policy_contract_ids"] = list(
            self.planned_policy_contract_ids
        )
        return payload


def durable_schema_policies() -> tuple[DurableSchemaPolicy, ...]:
    """Return repo-owned policy rows for durable state-like contracts."""
    return (
        DurableSchemaPolicy(
            contract_id="FindingBacklog",
            store_path="dev/reports/governance/finding_reviews.jsonl",
            store_authority=(
                "dev.scripts.devctl.runtime.platform_finding_ingest:"
                "ingest_platform_finding"
            ),
            schema_version_field="schema_version",
            compatibility_window="Additive row fields only until FindingBacklog reducer and governance-review importers are migrated together.",
            migration_path="Route new finding fields through PlatformFindingIngest, then refresh FindingBacklog projections and focused reducer tests.",
            rollback_path="Keep old governance-review row fields readable; disable new projection fields before removing persisted data.",
            store_authority_status="planned",
            owning_row="MP377-FINDING-INGEST-CANONICAL-S1",
            notes="Current finding log still has legacy writers; canonicalization is tracked separately.",
        ),
        DurableSchemaPolicy(
            contract_id="PlatformFindingIngest",
            store_path="dev/reports/governance/finding_reviews.jsonl",
            store_authority=(
                "dev.scripts.devctl.runtime.platform_finding_ingest:"
                "ingest_platform_finding"
            ),
            schema_version_field="schema_version",
            compatibility_window="Ingest result fields stay additive while review-channel and governance-review vocabularies are unified.",
            migration_path="Add fields through the ingest result model, persist through the canonical finding seam, and update backlog/dogfood projections together.",
            rollback_path="Leave persisted rows readable and stop emitting new optional fields until consumers are restored.",
            store_authority_status="planned",
            owning_row="MP377-FINDING-INGEST-CANONICAL-S1",
        ),
        DurableSchemaPolicy(
            contract_id="PlatformContractRegistryRow",
            store_path="dev/state/contract_registry.jsonl",
            store_authority=(
                "dev.scripts.devctl.platform.contract_registry:"
                "write_contract_registry_rows"
            ),
            schema_version_field="registry_row_schema_version",
            compatibility_window="Registry fields must be additive until fixture handshake and closure checks pass on both old and new rows.",
            migration_path="Update ContractRegistryRow, regenerate schema fixtures, run registry closure, then consume new fields from checks.",
            rollback_path="Restore previous registry row shape and fixture expectations before reverting consumers.",
            store_authority_status="registered_advisory",
            owning_row="MP377-SCHEMA-MIGRATION-SPINE-S1",
        ),
        contract_registry_composite_key_policy(),
        DurableSchemaPolicy(
            contract_id="RemoteControlCollaborationCampaign",
            store_path="dev/state/governed_exception_lifecycles.jsonl",
            store_authority=(
                "dev.scripts.devctl.runtime.governed_exception_store:"
                "write_governed_exception_lifecycle"
            ),
            schema_version_field="schema_version",
            compatibility_window="Read-only compatibility remains allowed until the governed-exception lifecycle writer lands.",
            migration_path="Add the governed-exception lifecycle writer, then route campaign exception proof through it.",
            rollback_path="Keep readers tolerant of absent lifecycle rows and re-open MP377-GOVERNED-EXCEPTION-LIFECYCLE-WRITER-S1.",
            store_authority_status="planned",
            owning_row="MP377-GOVERNED-EXCEPTION-LIFECYCLE-WRITER-S1",
            notes="The writer is intentionally planned, not blocking, in the current tree.",
        ),
        DurableSchemaPolicy(
            contract_id="BaselineAuthorityInventoryReceipt",
            store_path="dev/state/baseline_authority_inventories.jsonl",
            store_authority=(
                "dev.scripts.devctl.runtime.baseline_authority_inventory:"
                "append_baseline_authority_inventory_receipt"
            ),
            schema_version_field="schema_version",
            compatibility_window="Baseline receipt rows are append-only and additive during Phase 1 inventory hardening.",
            migration_path="Add fields additively, update baseline-inventory command/tests, and preserve prior receipt readers.",
            rollback_path="Keep older receipt rows readable and stop emitting new optional fields until consumers are restored.",
            store_authority_status="registered_advisory",
            owning_row="MP377-REPO-BASELINE-INVENTORY-S1",
        ),
        DurableSchemaPolicy(
            contract_id="PlanIntentIngestionReceipt",
            store_path="dev/state/plan_ingestion_receipts.jsonl",
            store_authority=(
                "dev.scripts.devctl.runtime.plan_intent_ingestion:"
                "append_plan_intent_ingestion_receipt"
            ),
            schema_version_field="schema_version",
            compatibility_window="Receipt fields remain additive until PlanIndexAuthority and rollback receipts are accepted.",
            migration_path="Add fields to PlanIntentIngestionReceipt, retain source snapshots, update ingest-plan tests, and verify dry-run/write receipts.",
            rollback_path="Leave previous receipt rows readable and gate new field consumption behind presence checks.",
            store_authority_status="registered_advisory",
            owning_row="MP377-PLAN-INGESTION-RECEIPT-SPINE-S1",
        ),
        DurableSchemaPolicy(
            contract_id="PlanSourceSnapshot",
            store_path="dev/state/plan_source_snapshots.jsonl",
            store_authority=(
                "dev.scripts.devctl.runtime.plan_source_retention_store:"
                "write_plan_source_snapshots_jsonl"
            ),
            schema_version_field="schema_version",
            compatibility_window="Snapshot rows stay append/replace compatible until dependency graph fields become first-class PlanRow schema.",
            migration_path="Add source metadata additively, update retention validation, and regenerate fixture coverage before consumers require it.",
            rollback_path="Keep older snapshots readable and classify missing new metadata as unknown rather than invalid.",
            store_authority_status="registered_advisory",
            owning_row="MP377-PLAN-INGESTION-RECEIPT-SPINE-S1",
        ),
        DurableSchemaPolicy(
            contract_id="TaskStartedAdrPrecedentLinkingGuard",
            store_path="dev/reports/review_channel/events/trace.ndjson",
            store_authority=(
                "dev.scripts.devctl.review_channel.event_store:append_event"
            ),
            schema_version_field="schema_version",
            compatibility_window="Review-channel event rows remain append-only while task-start guard fields are additive and report-only.",
            migration_path="Add task_started packet evidence fields through review-channel event writers, update guard parsing, and preserve older rows as legacy gaps.",
            rollback_path="Keep older event rows readable; classify missing new evidence as legacy/report-only until strict enforcement is selected.",
            store_authority_status="planned",
            owning_row="MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1",
            notes="Existing event writer is lock-based; shared state-store authority migration is planned separately.",
        ),
        DurableSchemaPolicy(
            contract_id="AgentSessionOutcome",
            store_path="provider-session-log-path",
            store_authority=(
                "dev.scripts.devctl.runtime.agent_session_outcome:"
                "record_agent_session_outcome"
            ),
            schema_version_field="schema_version",
            compatibility_window="Provider session outcome metadata must stay additive across live/recovered sessions.",
            migration_path="Add outcome fields through the session outcome model and update liveness/session-resume consumers together.",
            rollback_path="Ignore unknown optional fields in outcome readers and keep process-death classification conservative.",
            store_authority_status="planned",
            owning_row="MP377-SESSION-LIVENESS-WATCHDOG-S1",
        ),
        DurableSchemaPolicy(
            contract_id="WorkPublicationLedgerHeader",
            store_path="work-publication-ledger:event_log_path,state_path",
            store_authority=(
                "dev.scripts.devctl.runtime.work_publication_ledger:"
                "record_work_publication_event"
            ),
            schema_version_field="schema_version",
            compatibility_window="Publication ledger event/state fields must remain additive until push/release receipt bridge lands.",
            migration_path="Add ledger fields, replay existing events into derived state, and reconcile with push/release receipts.",
            rollback_path="Replay old event rows into the previous state projection and mark new fields advisory.",
            store_authority_status="planned",
            owning_row="MP377-PUSH-PATH-RECONCILE-S1",
        ),
    )


def contract_registry_composite_key_policy() -> DurableSchemaPolicy:
    """Return migration policy for registry composite-key guard output."""
    return DurableSchemaPolicy(
        contract_id="ContractRegistryCompositeKeyUniqueness",
        store_path="dev/state/contract_registry.jsonl",
        store_authority=(
            "dev.scripts.devctl.platform.contract_registry:"
            "write_contract_registry_rows"
        ),
        schema_version_field="schema_version",
        compatibility_window="Guard report fields remain additive while registry duplicate policy TODOs are retired through explicit operator decisions.",
        migration_path="Add registry fields through ContractRegistryRow, write through the shared registry writer, refresh fixtures, and keep guard parsing backward-compatible.",
        rollback_path="Keep prior registry rows readable and classify new duplicate metadata as advisory until consumers are restored.",
        store_authority_status="registered_advisory",
        owning_row="MP-NEW-P230-OUTPUT-TRUTH-SPINE-S1",
    )


@dataclass(frozen=True, slots=True)
class SchemaMigrationViolation:
    """One migration-spine policy violation."""

    rule: str
    contract_id: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def evaluate_schema_migration_spine(
    *,
    blueprint: PlatformBlueprint | None = None,
    policies: tuple[DurableSchemaPolicy, ...] | None = None,
) -> tuple[dict[str, object], tuple[SchemaMigrationViolation, ...]]:
    """Validate durable contracts and artifact schemas have migration policy."""
    blueprint = blueprint or build_platform_blueprint()
    policies = policies or durable_schema_policies()
    violations: list[SchemaMigrationViolation] = []

    durable_contract_ids = _durable_contract_ids(blueprint.shared_contracts)
    policy_by_contract: dict[str, DurableSchemaPolicy] = {}
    for policy in policies:
        if policy.contract_id in policy_by_contract:
            violations.append(
                SchemaMigrationViolation(
                    rule="duplicate-durable-schema-policy",
                    contract_id=policy.contract_id,
                    detail="Only one DurableSchemaPolicy is allowed per contract.",
                )
            )
            continue
        policy_by_contract[policy.contract_id] = policy
        violations.extend(_policy_violations(policy))

    for contract_id in sorted(durable_contract_ids):
        if contract_id in policy_by_contract:
            continue
        violations.append(
            SchemaMigrationViolation(
                rule="missing-durable-schema-policy",
                contract_id=contract_id,
                detail=(
                    "Durable state-like contracts must declare migration, "
                    "rollback, compatibility, schema-version, and store-authority policy."
                ),
            )
        )

    known_contract_ids = {contract.contract_id for contract in blueprint.shared_contracts}
    for policy in policies:
        if policy.contract_id in known_contract_ids:
            continue
        violations.append(
            SchemaMigrationViolation(
                rule="policy-contract-not-in-blueprint",
                contract_id=policy.contract_id,
                detail="DurableSchemaPolicy references a contract absent from the platform blueprint.",
            )
        )

    for artifact in blueprint.artifact_schemas:
        missing = [
            field_name
            for field_name in (
                "compatibility_window",
                "migration_path",
                "rollback_path",
                "schema_version_attr",
            )
            if not str(getattr(artifact, field_name, "") or "").strip()
        ]
        if missing:
            violations.append(
                SchemaMigrationViolation(
                    rule="artifact-schema-migration-metadata-missing",
                    contract_id=artifact.contract_id,
                    detail="ArtifactSchemaSpec missing fields: " + ", ".join(missing),
                )
            )

    planned = tuple(
        policy
        for policy in policies
        if policy.store_authority_status in NON_BLOCKING_STORE_AUTHORITY_STATUSES
    )
    coverage = SchemaMigrationSpine(
        durable_contract_count=len(durable_contract_ids),
        policy_count=len(policies),
        artifact_schema_count=len(blueprint.artifact_schemas),
        planned_policy_count=len(planned),
        planned_policy_contract_ids=tuple(policy.contract_id for policy in planned),
        ok=not violations,
    ).to_dict()
    return coverage, tuple(violations)


def _durable_contract_ids(contracts: tuple[ContractSpec, ...]) -> set[str]:
    durable: set[str] = set()
    for contract in contracts:
        field_names = {field.name for field in contract.required_fields}
        if field_names & _DURABLE_STATE_FIELD_NAMES:
            durable.add(contract.contract_id)
    return durable


def _policy_violations(
    policy: DurableSchemaPolicy,
) -> tuple[SchemaMigrationViolation, ...]:
    violations: list[SchemaMigrationViolation] = []
    for field_name in (
        "store_path",
        "schema_version_field",
        "compatibility_window",
        "migration_path",
        "rollback_path",
        "owning_row",
    ):
        if str(getattr(policy, field_name, "") or "").strip():
            continue
        violations.append(
            SchemaMigrationViolation(
                rule="durable-schema-policy-field-missing",
                contract_id=policy.contract_id,
                detail=f"DurableSchemaPolicy.{field_name} is required.",
            )
        )
    if policy.store_authority_status not in REGISTERED_STORE_AUTHORITY_STATUSES:
        violations.append(
            SchemaMigrationViolation(
                rule="invalid-store-authority-status",
                contract_id=policy.contract_id,
                detail=(
                    "store_authority_status must be one of "
                    + ", ".join(sorted(REGISTERED_STORE_AUTHORITY_STATUSES))
                ),
            )
        )
    if (
        policy.store_authority_status not in NON_BLOCKING_STORE_AUTHORITY_STATUSES
        and not policy.store_authority.strip()
    ):
        violations.append(
            SchemaMigrationViolation(
                rule="registered-store-authority-missing",
                contract_id=policy.contract_id,
                detail="Registered store-authority policies must name a writer ref.",
            )
        )
    return tuple(violations)


__all__ = [
    "DURABLE_SCHEMA_POLICY_CONTRACT_ID",
    "SCHEMA_MIGRATION_SPINE_CONTRACT_ID",
    "SCHEMA_MIGRATION_SPINE_SCHEMA_VERSION",
    "DurableSchemaPolicy",
    "SchemaMigrationSpine",
    "SchemaMigrationViolation",
    "durable_schema_policies",
    "evaluate_schema_migration_spine",
]
