"""Typed receipt-steward role substrate (A38.2 S1).

The receipt-steward role is GOVERNANCE / audit-only. It verifies that
per-slice `FeatureProofReceipt` emission happens with a valid pytest
node id, commit SHA, and real-life test status. The role NEVER mutates
plan or repo state; it READS evidence and EMITS a typed audit receipt.

This module is the typed substrate for the role: dataclasses, phase
enum, audit-targets, audit-receipt shape, and the canonical role spec
factory. The CLI surface, scope-claim lifecycle persistence, gate
composition, and exemption lifecycle are deliberately NOT included
here — those land in subsequent S2..S4 slices.

Shape sibling to `semantic_tdd_role.py`: each role spec carries a
typed phase enum, per-phase specs with evidence requirements, and a
single-source-of-truth factory function. The receipt-steward role is
agent-agnostic; any actor (claude, codex, cursor, future) can hold it
when a typed grant is in scope.

The role composes with the `BypassLifecycle` pattern through a future
`ReceiptStewardScopeClaim` (S2) that mirrors request → evaluation →
claim → expiry for READ-only audit-scope authority. That latch is
substrate-future and is NOT in this module.

Output of one audit invocation:

- `ReceiptStewardAuditReceipt` — typed audit-receipt payload carrying
  the audited slice id, plan row id, commit SHA, audit-targets boolean
  matrix, `missing_items` taxonomy, evidence path, actor role, and
  schema_version + contract_id.

The 7-value `missing_items` taxonomy (`missing_completely`,
`missing_pytest_node`, `stale_commit_reference`, `dangling_plan_row`,
`no_evidence_case`, `pytest_node_unresolvable`, `dirty_tree_at_audit`)
is normalized as plain strings on the receipt for portability across
adopter repos.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .enum_compat import StrEnum
from .role_profile import RoleCapabilityClass


RECEIPT_STEWARD_ROLE_ID = "receipt_steward"
RECEIPT_STEWARD_AUDIT_RECEIPT_CONTRACT_ID = "ReceiptStewardAuditReceipt"
RECEIPT_STEWARD_AUDIT_TARGETS_CONTRACT_ID = "ReceiptStewardAuditTargets"
RECEIPT_STEWARD_ROLE_SPEC_CONTRACT_ID = "ReceiptStewardRoleSpec"
RECEIPT_STEWARD_SCHEMA_VERSION = 1


class ReceiptStewardPhase(StrEnum):
    """Typed sub-actions of the receipt-steward audit ritual.

    The phases run sequentially within a single audit invocation. Each
    one carries a single read-only responsibility — discovery, then
    evidence-path inventory, then four targeted verifications, then
    emission of the typed audit receipt. The role never mutates state;
    every phase produces typed observations only.
    """

    DISCOVER_SLICE = "discover_slice"
    INVENTORY_EVIDENCE_PATHS = "inventory_evidence_paths"
    VERIFY_RECEIPT_PRESENT = "verify_receipt_present"
    VERIFY_PYTEST_NODE_RESOLVABLE = "verify_pytest_node_resolvable"
    VERIFY_COMMIT_SHA_LINKED = "verify_commit_sha_linked"
    EMIT_AUDIT_RECEIPT = "emit_audit_receipt"


@dataclass(frozen=True, slots=True)
class ReceiptStewardPhaseSpec:
    """One phase of the receipt-steward audit ritual.

    Carries the evidence the phase produces and the secondary capability
    class. Every phase is `RoleCapabilityClass.GOVERNANCE` because the
    role is audit-only; it never holds `MUTATION`, `IMPLEMENTATION`, or
    `CONTROL` capabilities.
    """

    phase_id: ReceiptStewardPhase
    description: str
    evidence_required: str
    capability_class: RoleCapabilityClass = RoleCapabilityClass.GOVERNANCE


@dataclass(frozen=True, slots=True)
class ReceiptStewardAuditTargets:
    """Typed boolean matrix recording per-target audit outcome.

    Each field captures one verification result. ``status`` is a
    plain-language summary (``passed``/``failed``/``partial``); it is
    derived from the booleans by the auditing implementation and
    persisted on the receipt for reviewers who want one-line context
    without expanding the matrix.
    """

    receipt_present: bool
    pytest_node_resolvable: bool
    commit_sha_linked: bool
    plan_row_linked: bool
    evidence_path_resolvable: bool
    real_life_test_status_valid: bool
    status: str = "pending"
    schema_version: int = RECEIPT_STEWARD_SCHEMA_VERSION
    contract_id: str = RECEIPT_STEWARD_AUDIT_TARGETS_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReceiptStewardAuditReceipt:
    """Typed output of one receipt-steward audit invocation.

    The receipt is the single observable artifact the role emits. It
    carries the audited slice id, plan row id, commit SHA, the typed
    audit-targets matrix, a `missing_items` taxonomy capturing any
    blocking or advisory gaps, the resolved `FeatureProofReceipt` path
    (empty when the FPR is missing entirely), the actor role that ran
    the audit, and the standard schema_version + contract_id fields.

    The 7-value `missing_items` taxonomy is normalized as plain strings
    so adopters can consume the receipt without importing this module.
    First five values (`missing_completely`, `missing_pytest_node`,
    `stale_commit_reference`, `dangling_plan_row`, `no_evidence_case`)
    are blocking; last two (`pytest_node_unresolvable`,
    `dirty_tree_at_audit`) are advisory only.
    """

    audit_id: str
    slice_id: str
    plan_row_id: str
    commit_sha: str
    audited_at_utc: str
    targets: ReceiptStewardAuditTargets
    missing_items: tuple[str, ...]
    feature_proof_receipt_path: str
    actor_role: str = RECEIPT_STEWARD_ROLE_ID
    schema_version: int = RECEIPT_STEWARD_SCHEMA_VERSION
    contract_id: str = RECEIPT_STEWARD_AUDIT_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["missing_items"] = list(self.missing_items)
        payload["targets"] = self.targets.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class ReceiptStewardRoleSpec:
    """Typed contract for the single receipt-steward role.

    Any actor (claude, codex, cursor, future) holds this role per typed
    `actor_authorities` grants. The role is agent-agnostic; the phases
    describe the audit work, not the identity of the auditor.
    """

    role_id: str = RECEIPT_STEWARD_ROLE_ID
    capability_class: RoleCapabilityClass = RoleCapabilityClass.GOVERNANCE
    phases: tuple[ReceiptStewardPhaseSpec, ...] = field(default_factory=tuple)
    documentation_doc: str = "dev/active/receipt_steward_lane.md"
    audit_receipt_contract_id: str = RECEIPT_STEWARD_AUDIT_RECEIPT_CONTRACT_ID
    schema_version: int = RECEIPT_STEWARD_SCHEMA_VERSION
    contract_id: str = RECEIPT_STEWARD_ROLE_SPEC_CONTRACT_ID


_CANONICAL_PHASES: tuple[ReceiptStewardPhaseSpec, ...] = (
    ReceiptStewardPhaseSpec(
        phase_id=ReceiptStewardPhase.DISCOVER_SLICE,
        description=(
            "Resolve the typed slice under audit from the requested "
            "slice_id. Read `dev/state/plan_index.jsonl` for the "
            "PlanRow; cross-check that the slice is the one the "
            "FeatureProofReceipt is expected to attest."
        ),
        evidence_required="plan_row_id + plan_index.jsonl row + slice scope summary",
    ),
    ReceiptStewardPhaseSpec(
        phase_id=ReceiptStewardPhase.INVENTORY_EVIDENCE_PATHS,
        description=(
            "Enumerate the on-disk paths that should carry evidence "
            "for the slice: the `FeatureProofReceipt` JSON under "
            "`dev/reports/feature_proof_receipts/{commit_sha}.json`, "
            "the dogfood-invocation evidence ref, scenario test "
            "node ids declared in `tests_run`, and any related lane "
            "matrix rows. The phase produces a typed path-inventory "
            "summary; it does not yet decide pass/fail."
        ),
        evidence_required="ordered list of evidence paths + per-path exists/missing tag",
    ),
    ReceiptStewardPhaseSpec(
        phase_id=ReceiptStewardPhase.VERIFY_RECEIPT_PRESENT,
        description=(
            "Confirm a `FeatureProofReceipt` exists for the slice's "
            "commit_sha. A missing receipt is the strongest blocking "
            "signal and contributes `missing_completely` to the "
            "`missing_items` taxonomy."
        ),
        evidence_required="receipt path resolution + presence boolean",
    ),
    ReceiptStewardPhaseSpec(
        phase_id=ReceiptStewardPhase.VERIFY_PYTEST_NODE_RESOLVABLE,
        description=(
            "Read the receipt's `tests_run` field; assert at least one "
            "entry is a concrete pytest node id (contains `::`). Best "
            "effort verify the node is resolvable in the test tree; "
            "non-resolvable is advisory only."
        ),
        evidence_required="tests_run entries + node-id detected boolean + resolvability tag",
    ),
    ReceiptStewardPhaseSpec(
        phase_id=ReceiptStewardPhase.VERIFY_COMMIT_SHA_LINKED,
        description=(
            "Confirm `commit_sha` on the receipt matches the slice's "
            "committed work; check the SHA exists in the local git "
            "history. A mismatched or unknown SHA contributes "
            "`stale_commit_reference` to the taxonomy."
        ),
        evidence_required="commit_sha + git rev-parse outcome",
    ),
    ReceiptStewardPhaseSpec(
        phase_id=ReceiptStewardPhase.EMIT_AUDIT_RECEIPT,
        description=(
            "Assemble the typed `ReceiptStewardAuditReceipt` from the "
            "verified targets, attach the `missing_items` taxonomy, "
            "and persist via the governed JSON-mapping writer used by "
            "other lifecycle stores. The receipt is the single "
            "observable artifact this role produces."
        ),
        evidence_required="ReceiptStewardAuditReceipt id + persisted path + write fingerprint",
    ),
)


def receipt_steward_role_spec() -> ReceiptStewardRoleSpec:
    """Return the canonical typed instance of `ReceiptStewardRoleSpec`.

    Single source of truth for the audit-only role. Callers that need
    to inspect the ritual (matrix renderers, dispatch routers, agent
    role-authority gates, gate-composition wiring) should consume this
    rather than re-deriving from documentation prose.
    """
    return ReceiptStewardRoleSpec(phases=_CANONICAL_PHASES)


__all__ = [
    "RECEIPT_STEWARD_AUDIT_RECEIPT_CONTRACT_ID",
    "RECEIPT_STEWARD_AUDIT_TARGETS_CONTRACT_ID",
    "RECEIPT_STEWARD_ROLE_ID",
    "RECEIPT_STEWARD_ROLE_SPEC_CONTRACT_ID",
    "RECEIPT_STEWARD_SCHEMA_VERSION",
    "ReceiptStewardAuditReceipt",
    "ReceiptStewardAuditTargets",
    "ReceiptStewardPhase",
    "ReceiptStewardPhaseSpec",
    "ReceiptStewardRoleSpec",
    "receipt_steward_role_spec",
]
