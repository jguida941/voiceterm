"""Typed master-plan authority contracts for portable governance repos."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .value_coercion import coerce_string

MASTER_PLAN_CONTRACT_ID = "MasterPlan"
MASTER_PLAN_SCHEMA_VERSION = 1
PLAN_ROW_CONTRACT_ID = "PlanRow"
LINKED_DOC_CONTRACT_ID = "LinkedDoc"
PLAN_PROPOSAL_CONTRACT_ID = "PlanProposal"
INGESTION_PROVENANCE_CONTRACT_ID = "IngestionProvenance"
INGESTED_DOC_CONTRACT_ID = "IngestedDoc"
INGESTION_POLICY_CONTRACT_ID = "IngestionPolicy"
INGESTION_DRIFT_CONTRACT_ID = "IngestionDrift"
EXPLAIN_BACK_RECEIPT_CONTRACT_ID = "ExplainBackReceipt"
DEFAULT_MASTER_PLAN_STORE_REL = "dev/state/plan_index.jsonl"


class SDLCStage:
    """Bounded SDLC stage vocabulary for plan rows and linked docs."""

    IDEA = "idea"
    SPEC = "spec"
    DESIGN = "design"
    IMPL = "impl"
    TEST = "test"
    RELEASE = "release"
    RETIRE = "retire"

    ALL = frozenset({IDEA, SPEC, DESIGN, IMPL, TEST, RELEASE, RETIRE})

    @classmethod
    def normalize(cls, value: object, *, default: str = IMPL) -> str:
        text = coerce_string(value)
        return text if text in cls.ALL else default


@dataclass(frozen=True, slots=True)
class IngestionProvenance:
    """Typed proof of where one ingested authority signal came from."""

    source_file: str = ""
    source_line: int = 0
    source_kind: str = ""
    source_hash: str = ""
    observed_at_utc: str = ""
    section_authority: str = ""
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = INGESTION_PROVENANCE_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return payload

    def complete(self) -> bool:
        required_values = (
            self.source_file,
            self.source_kind,
            self.source_hash,
            self.observed_at_utc,
            self.section_authority,
        )
        return all(required_values)


@dataclass(frozen=True, slots=True)
class LinkedDoc:
    """One governed doc linked back to a master-plan row."""

    path: str
    role: str
    sdlc_stage: str
    links_to_plan_row: str
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = LINKED_DOC_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return payload


@dataclass(frozen=True, slots=True)
class AffectedTestSelection:
    selection_id: str
    changed_paths: tuple[str, ...]
    contract_refs: tuple[str, ...]
    local_test_refs: tuple[str, ...]
    connected_test_refs: tuple[str, ...]
    selection_reason: str
    selected_at_utc: str
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = "AffectedTestSelection"


@dataclass(frozen=True, slots=True)
class PlanRow:
    """One typed master-plan row.

    Markdown can project this row for humans, but runtime mutation authority is
    the stable row id plus the JSONL payload.
    """

    row_id: str
    title: str
    status: str
    sdlc_stage: str
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = PLAN_ROW_CONTRACT_ID
    row_kind: str = "task"
    sourced_from_packets: tuple[str, ...] = ()
    contradicts_packets: tuple[str, ...] = ()
    work_evidence_ids: tuple[str, ...] = ()
    superseded_by_row: str = ""
    plan_revision_at_write: str = ""
    source_doc_path: str = ""
    source_line: int = 0
    content_hash: str = ""
    provenance: IngestionProvenance = field(default_factory=IngestionProvenance)
    anchor_refs: tuple[str, ...] = ()
    target_ref: str = ""
    mutation_op: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["provenance"] = self.provenance.to_dict()
        payload["sourced_from_packets"] = list(self.sourced_from_packets)
        payload["contradicts_packets"] = list(self.contradicts_packets)
        payload["work_evidence_ids"] = list(self.work_evidence_ids)
        payload["anchor_refs"] = list(self.anchor_refs)
        return payload


@dataclass(frozen=True, slots=True)
class MasterPlan:
    """Typed master-plan authority for one governed repository."""

    repo_id: str = ""
    rows: tuple[PlanRow, ...] = ()
    linked_docs: tuple[LinkedDoc, ...] = ()
    status: str = "pending_explainback"
    last_ingested_at_utc: str = ""
    plan_revision: str = ""
    source_path: str = "dev/active/MASTER_PLAN.md"
    typed_store_path: str = DEFAULT_MASTER_PLAN_STORE_REL
    projection_path: str = "dev/active/MASTER_PLAN.md"
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = MASTER_PLAN_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [row.to_dict() for row in self.rows]
        payload["linked_docs"] = [doc.to_dict() for doc in self.linked_docs]
        return payload


@dataclass(frozen=True, slots=True)
class PlanProposal:
    """Typed plan mutation carried by proposal-class packets."""

    target_ref: str = ""
    anchor_refs: tuple[str, ...] = ()
    mutation_op: str = ""
    proposed_row: PlanRow | None = None
    proposed_links: tuple[LinkedDoc, ...] = ()
    plan_revision_at_propose: str = ""
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = PLAN_PROPOSAL_CONTRACT_ID

    def has_values(self) -> bool:
        return any(
            (
                self.target_ref,
                self.anchor_refs,
                self.mutation_op,
                self.proposed_row is not None,
                self.proposed_links,
                self.plan_revision_at_propose,
            )
        )

    def collision_key(self) -> tuple[str, tuple[str, ...], str]:
        return (
            self.target_ref,
            tuple(sorted(ref for ref in self.anchor_refs if ref)),
            self.mutation_op,
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["anchor_refs"] = list(self.anchor_refs)
        payload["proposed_row"] = (
            self.proposed_row.to_dict() if self.proposed_row is not None else None
        )
        payload["proposed_links"] = [link.to_dict() for link in self.proposed_links]
        return payload


@dataclass(frozen=True, slots=True)
class IngestedDoc:
    """One ingestion attempt over a source document."""

    source_file: str
    source_kind: str
    status: str
    reason: str = ""
    rows: tuple[PlanRow, ...] = ()
    observed_at_utc: str = ""
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = INGESTED_DOC_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [row.to_dict() for row in self.rows]
        return payload


@dataclass(frozen=True, slots=True)
class IngestionPolicy:
    """Repo-pack policy for discovering plan authority in arbitrary repos."""

    scan_roots: tuple[str, ...] = ("dev/active", "docs", "plans")
    exclude_globs: tuple[str, ...] = ()
    adapters: tuple[str, ...] = ("markdown_checklist", "prose_seed")
    max_file_bytes: int = 1_000_000
    drift_mode: str = "surface_finding"
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = INGESTION_POLICY_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scan_roots"] = list(self.scan_roots)
        payload["exclude_globs"] = list(self.exclude_globs)
        payload["adapters"] = list(self.adapters)
        return payload


@dataclass(frozen=True, slots=True)
class IngestionDrift:
    """Typed mismatch between a human projection and JSONL plan authority."""

    row_id: str
    source_doc_path: str
    expected_hash: str
    observed_hash: str
    reason: str
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = INGESTION_DRIFT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return payload


@dataclass(frozen=True, slots=True)
class ExplainBackReceipt:
    """AI explain-back receipt for first ingestion or drift review."""

    receipt_id: str
    repo_pack_id: str
    ingested_files: tuple[str, ...]
    derived_plan_rows: tuple[str, ...]
    nl_summary: str
    confidence: float
    pending_questions: tuple[str, ...]
    status: str = "pending"
    operator_signature: str = ""
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = EXPLAIN_BACK_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["ingested_files"] = list(self.ingested_files)
        payload["derived_plan_rows"] = list(self.derived_plan_rows)
        payload["pending_questions"] = list(self.pending_questions)
        return payload

__all__ = [
    "DEFAULT_MASTER_PLAN_STORE_REL",
    "EXPLAIN_BACK_RECEIPT_CONTRACT_ID",
    "INGESTED_DOC_CONTRACT_ID",
    "INGESTION_DRIFT_CONTRACT_ID",
    "INGESTION_POLICY_CONTRACT_ID",
    "INGESTION_PROVENANCE_CONTRACT_ID",
    "LINKED_DOC_CONTRACT_ID",
    "MASTER_PLAN_CONTRACT_ID",
    "MASTER_PLAN_SCHEMA_VERSION",
    "PLAN_PROPOSAL_CONTRACT_ID",
    "PLAN_ROW_CONTRACT_ID",
    "ExplainBackReceipt",
    "IngestedDoc",
    "IngestionDrift",
    "IngestionPolicy",
    "IngestionProvenance",
    "LinkedDoc",
    "MasterPlan",
    "PlanProposal",
    "PlanRow",
    "SDLCStage",
]
