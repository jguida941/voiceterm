"""Typed system-map-steward role substrate (A38.3 S1).

This is a PLATFORM-COVERAGE audit role (NOT a TDD-discipline audit role
— see evidence.md Case 11 for the category-error correction story).

Per slice, the audit asks: did this slice CONNECT to the relevant pieces
of the AI governance platform that exist? The inventory is consulted
from SYSTEM_MAP.md + ai_governance_platform.md + contract_registry.jsonl
+ INDEX.md + dev/scripts/checks/ + dev/scripts/coderabbit/ + devctl
subcommand list.

The role unifies with the previously underdeveloped
``system_alignment_role`` already in ``DEFAULT_ROLE_IDS``: that legacy
id resolves to ``system_map_steward`` through ``_ROLE_ID_ALIASES``, so
the typed audit surface specializes the unused role rather than
introducing a parallel one. The category distinction matters: TDD-step
observables (``red_first``, ``green_verify``, ``dogfood_proof``,
``receipt``) describe WHETHER THE DISCIPLINE FIRED; this role's audit
dimensions describe WHETHER THE SLICE CONNECTED TO THE PLATFORM. The
two inventories overlap minimally — they are distinct audit objects.

Shape sibling to ``semantic_tdd_role.py`` and ``receipt_steward_role.py``:
each role spec carries a typed phase enum, per-phase specs with evidence
requirements, and a single-source-of-truth factory function. The
system-map-steward role is agent-agnostic; any actor (claude, codex,
cursor, future) can hold it when a typed grant is in scope.

This module ships the typed substrate only: phase enum, dataclasses,
audit dimensions, scope-claim shape, and the canonical role spec
factory. The CLI surface (``devctl system-map-steward audit``,
``propose-row``, ``coverage-report``, ``connectivity-trend``), the
audit-dimension evaluator implementations, and the SYSTEM_MAP.md write
authority logic are deliberately NOT included here — those land in
subsequent S2/S3 slices.

The role composes with ``receipt_steward`` (delegates the
``feature_proof_receipt_chain`` dimension), ``semantic_tdd`` (loose
coupling — the TDD ritual is one of the audit consumers), and
``plan_steward`` (PlanRow scope is the audit's slice anchor). The
``SystemMapStewardScopeClaim`` lifecycle is substrate-future; this
slice ships the dataclass shape so callers can declare scope.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

from .enum_compat import StrEnum
from .role_profile import RoleCapabilityClass


SYSTEM_MAP_STEWARD_ROLE_ID = "system_map_steward"
SYSTEM_MAP_STEWARD_AUDIT_RECEIPT_CONTRACT_ID = "PlatformCoverageAudit"
SYSTEM_MAP_STEWARD_COMPONENT_TOUCH_CONTRACT_ID = "PlatformComponentTouch"
SYSTEM_MAP_STEWARD_ROLE_SPEC_CONTRACT_ID = "SystemMapStewardRoleSpec"
SYSTEM_MAP_STEWARD_PHASE_SPEC_CONTRACT_ID = "SystemMapStewardPhaseSpec"
SYSTEM_MAP_STEWARD_SCOPE_CLAIM_CONTRACT_ID = "SystemMapStewardScopeClaim"
SYSTEM_MAP_ROW_PROPOSAL_CONTRACT_ID = "SystemMapRowProposal"
SYSTEM_MAP_STEWARD_SCHEMA_VERSION = 1


PLATFORM_COMPONENT_IDS: tuple[str, ...] = (
    "project_governance_authority_chain_consulted",
    "repo_pack_contract_respected",
    "plan_registry_tied",
    "collaboration_session_actor_authority_typed",
    "typed_action_result_chain_emitted",
    "bypass_lifecycle_composed",
    "feature_proof_receipt_chain",
    "relevant_guards_ran",
    "relevant_probes_ran",
    "findings_priority_impact_observable",
    "index_md_active_doc_registry_covered",
    "system_map_maintenance_rule_followed",
    "ai_governance_platform_layer_named",
    "contract_registry_updated",
    "devctl_cli_inventory_current",
)
"""The 15 typed audit dimensions, in canonical order.

These are PLATFORM COMPONENTS (the pieces of the AI governance platform
that exist in this repo), NOT TDD-ritual observables. The distinction
matters: a slice can pass narrow TDD discipline while leaving 60% of
the relevant platform inventory disconnected — this role catches that.

One entry delegates: ``feature_proof_receipt_chain`` is the boundary
where ``receipt_steward`` owns the verification logic. The audit
dimension records the delegation; the underlying check lives in the
receipt-steward substrate.
"""


class SystemMapStewardPhase(StrEnum):
    """Typed sub-actions of the system-map-steward audit ritual.

    The phases run sequentially within a single audit invocation. Each
    one carries a single read-only responsibility — load inventory,
    determine slice relevance, audit per-dimension connections,
    synthesize gaps, propose a SYSTEM_MAP row when a new disconnection
    is surfaced, then emit the typed coverage-audit receipt. The role
    never mutates plan or repo state directly (the SYSTEM_MAP write
    authority is a separate scope-claim path delivered in S3).
    """

    LOAD_PLATFORM_INVENTORY = "load_platform_inventory"
    DETERMINE_SLICE_RELEVANCE = "determine_slice_relevance"
    AUDIT_CONNECTIONS = "audit_connections"
    SYNTHESIZE_GAPS = "synthesize_gaps"
    PROPOSE_SYSTEM_MAP_UPDATE = "propose_system_map_update"
    EMIT_COVERAGE_AUDIT_RECEIPT = "emit_coverage_audit_receipt"


class PlatformComponentRelevance(StrEnum):
    """Relevance assessment of one platform component to a slice.

    ``high`` — the slice's scope intersects this component directly.
    ``medium`` — the slice touches an adjacent path; the component is
    a soft consumer or producer.
    ``low`` — the component is far from the slice; relevance is mostly
    formal coverage.
    ``irrelevant`` — the component does not apply to this slice; no
    audit is required.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    IRRELEVANT = "irrelevant"


class PlatformComponentTouchStatus(StrEnum):
    """Outcome of one platform-component audit observation.

    ``connected`` — the slice referenced or invoked the component as
    expected for its relevance level.
    ``missed`` — the slice should have connected to the component (per
    its relevance) but did not.
    ``n/a`` — the component is not applicable for this slice scope.
    ``exempted`` — the operator explicitly exempted the component with
    a typed reason; the exemption is recorded for audit replay.
    """

    CONNECTED = "connected"
    MISSED = "missed"
    NOT_APPLICABLE = "n/a"
    EXEMPTED = "exempted"


CoverageGrade = Literal["complete", "partial", "incomplete"]
"""Coverage-grade Literal kept on the audit receipt.

``complete`` — every ``high``-relevance dimension is ``connected``.
``partial`` — at least one ``high``-relevance dimension is ``missed``
or ``exempted`` but the audit has actionable evidence.
``incomplete`` — multiple ``high``-relevance dimensions are ``missed``
or the audit could not collect required evidence.
"""


SystemMapRowProposalStatus = Literal["pending", "approved", "rejected"]
"""Status Literal for a typed SYSTEM_MAP row proposal."""


SystemMapStewardScopeMode = Literal["read_only", "edit_only"]
"""Scope mode for the SystemMapStewardScopeClaim.

``read_only`` — covers the platform-inventory read paths only; the
default for audit invocations.
``edit_only`` — adds write authority for SYSTEM_MAP.md (the role's
maintenance-rule mechanization). Requires explicit operator approval;
this slice ships the dataclass shape only.
"""


@dataclass(frozen=True, slots=True)
class SystemMapStewardPhaseSpec:
    """One phase of the system-map-steward audit ritual.

    Carries the evidence the phase produces and the secondary capability
    class. Every phase is ``RoleCapabilityClass.GOVERNANCE`` because the
    role is audit-only; it never holds ``MUTATION``, ``IMPLEMENTATION``,
    or ``CONTROL`` capabilities. The SYSTEM_MAP.md write authority that
    closes the maintenance-rule loop is a separate edit-only scope-claim
    (substrate-future).
    """

    phase_id: SystemMapStewardPhase
    description: str
    evidence_required: str
    capability_class: RoleCapabilityClass = RoleCapabilityClass.GOVERNANCE
    schema_version: int = SYSTEM_MAP_STEWARD_SCHEMA_VERSION
    contract_id: str = SYSTEM_MAP_STEWARD_PHASE_SPEC_CONTRACT_ID


@dataclass(frozen=True, slots=True)
class PlatformComponentTouch:
    """One audit observation about a single platform component.

    Each touch records: the canonical component id, how relevant the
    component is to the slice scope, whether the slice connected to it,
    a typed evidence path or reference id, and a short explanation.

    ``evidence_path`` carries an on-disk path when the audit consults a
    file; ``evidence_ref_id`` carries a packet/receipt/contract id when
    the evidence is non-file (e.g., a ``FeatureProofReceipt`` row).
    ``exempted_with_reason`` is populated when the touch status is
    ``exempted`` and stays empty otherwise.
    """

    component_id: str
    relevance_to_slice: PlatformComponentRelevance
    observed_touch: PlatformComponentTouchStatus
    evidence_path: str = ""
    evidence_ref_id: str = ""
    exempted_with_reason: str = ""
    explanation: str = ""
    schema_version: int = SYSTEM_MAP_STEWARD_SCHEMA_VERSION
    contract_id: str = SYSTEM_MAP_STEWARD_COMPONENT_TOUCH_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["relevance_to_slice"] = self.relevance_to_slice.value
        payload["observed_touch"] = self.observed_touch.value
        return payload


@dataclass(frozen=True, slots=True)
class PlatformCoverageAudit:
    """Typed output of one system-map-steward audit invocation.

    The audit is the single observable artifact the role emits per
    slice. It carries the audit identity, slice + plan-row anchors, the
    commit SHA the slice produced, the ordered tuple of per-component
    touches, the synthesized list of missed pieces, any new
    disconnections surfaced during the audit, whether a SYSTEM_MAP row
    proposal was emitted, the proposal id (empty when no proposal), the
    coverage grade Literal, and the standard schema-version +
    contract-id fields.

    ``components`` is ordered to match ``PLATFORM_COMPONENT_IDS``; the
    audit-dimension evaluators (S2) are responsible for producing one
    entry per id (or marking ``n/a`` when irrelevant).
    """

    audit_id: str
    slice_id: str
    plan_row_id: str
    commit_sha: str
    audited_at_utc: str
    components: tuple[PlatformComponentTouch, ...]
    missed_pieces: tuple[str, ...]
    new_disconnections_surfaced: tuple[str, ...]
    system_map_update_proposed: bool
    system_map_proposal_id: str
    coverage_grade: CoverageGrade
    actor_role: str = SYSTEM_MAP_STEWARD_ROLE_ID
    schema_version: int = SYSTEM_MAP_STEWARD_SCHEMA_VERSION
    contract_id: str = SYSTEM_MAP_STEWARD_AUDIT_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["components"] = [touch.to_dict() for touch in self.components]
        payload["missed_pieces"] = list(self.missed_pieces)
        payload["new_disconnections_surfaced"] = list(
            self.new_disconnections_surfaced
        )
        return payload


@dataclass(frozen=True, slots=True)
class SystemMapStewardScopeClaim:
    """Typed scope claim for a system-map-steward audit invocation.

    Mirrors the request → evaluation → claim → expiry pattern from
    ``ReceiptStewardScopeClaim`` but with broader read coverage spanning
    the full platform inventory PLUS optional write authority for
    SYSTEM_MAP.md itself. The maintenance-rule mechanization requires
    the role to be ABLE to update the map when a new disconnection is
    surfaced; that write authority is gated by ``scope_mode=edit_only``
    and explicit operator approval (substrate-future lifecycle).

    Default ``scope_mode`` is ``read_only`` so audit invocations need
    no operator approval; only the row-write path requires the elevated
    edit-only scope.
    """

    claim_id: str
    actor_role: str
    scope_paths: tuple[str, ...]
    scope_mode: SystemMapStewardScopeMode
    requested_at_utc: str
    expiry_utc: str
    schema_version: int = SYSTEM_MAP_STEWARD_SCHEMA_VERSION
    contract_id: str = SYSTEM_MAP_STEWARD_SCOPE_CLAIM_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scope_paths"] = list(self.scope_paths)
        return payload


@dataclass(frozen=True, slots=True)
class SystemMapRowProposal:
    """Typed proposal to add one row to SYSTEM_MAP.md.

    Emitted when the audit surfaces a new disconnection that the doc
    does not yet record. The proposal is the maintenance-rule
    mechanization: rather than letting reviewers hand-edit the doc when
    a slice surfaces a new platform piece, the role emits a typed
    proposal carrying the suggested row text, target section, and
    surfacing slice id. An ``edit_only`` ``SystemMapStewardScopeClaim``
    grants the role authority to land the row directly (auto-approval
    path); without it the proposal stays ``pending`` for operator
    review.
    """

    proposal_id: str
    surfaced_disconnection: str
    suggested_row_text: str
    suggested_section: str
    surfaced_by_slice_id: str
    surfaced_at_utc: str
    status: SystemMapRowProposalStatus = "pending"
    schema_version: int = SYSTEM_MAP_STEWARD_SCHEMA_VERSION
    contract_id: str = SYSTEM_MAP_ROW_PROPOSAL_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SystemMapStewardRoleSpec:
    """Typed contract for the single system-map-steward role.

    Any actor (claude, codex, cursor, future) holds this role per typed
    ``actor_authorities`` grants. The role is agent-agnostic; the
    phases describe the audit work, not the identity of the auditor.

    ``composes_with`` records the typed role ids the audit work loosely
    couples to: ``receipt_steward`` owns the
    ``feature_proof_receipt_chain`` dimension (delegation boundary);
    ``semantic_tdd`` is one of the consumed disciplines (the audit
    checks platform-coverage, not TDD-step compliance);
    ``plan_steward`` owns the PlanRow anchor the audit attaches to;
    and ``system_alignment_role`` is the legacy id this role
    specializes (resolved through ``_ROLE_ID_ALIASES``).
    """

    role_id: str = SYSTEM_MAP_STEWARD_ROLE_ID
    capability_class: RoleCapabilityClass = RoleCapabilityClass.GOVERNANCE
    phases: tuple[SystemMapStewardPhaseSpec, ...] = field(default_factory=tuple)
    documentation_doc: str = "dev/active/system_map_steward_lane.md"
    audit_receipt_contract_id: str = SYSTEM_MAP_STEWARD_AUDIT_RECEIPT_CONTRACT_ID
    composes_with: tuple[str, ...] = (
        "receipt_steward",
        "semantic_tdd",
        "plan_steward",
        "system_alignment_role",
    )
    platform_component_ids: tuple[str, ...] = PLATFORM_COMPONENT_IDS
    schema_version: int = SYSTEM_MAP_STEWARD_SCHEMA_VERSION
    contract_id: str = SYSTEM_MAP_STEWARD_ROLE_SPEC_CONTRACT_ID


_CANONICAL_PHASES: tuple[SystemMapStewardPhaseSpec, ...] = (
    SystemMapStewardPhaseSpec(
        phase_id=SystemMapStewardPhase.LOAD_PLATFORM_INVENTORY,
        description=(
            "Load the platform inventory the audit will consult: "
            "`dev/guides/SYSTEM_MAP.md` (Living Connectivity Index), "
            "`dev/active/ai_governance_platform.md` (Platform Layers), "
            "`dev/active/INDEX.md` (active-doc registry), "
            "`dev/state/contract_registry.jsonl` (248 typed contracts), "
            "`dev/scripts/checks/check_*.py` (guards), "
            "`dev/scripts/coderabbit/probe_*.py` + sibling probe dirs, "
            "and the `devctl` subcommand inventory. The phase produces "
            "a snapshot of what platform pieces currently exist."
        ),
        evidence_required="inventory snapshot id + source paths + counts per category",
    ),
    SystemMapStewardPhaseSpec(
        phase_id=SystemMapStewardPhase.DETERMINE_SLICE_RELEVANCE,
        description=(
            "Read the slice's plan row, commit diff, and any associated "
            "packets to determine which platform components are RELEVANT "
            "to this slice scope. Relevance is assigned per dimension "
            "using `PlatformComponentRelevance` (high/medium/low/"
            "irrelevant). File paths touched, capability class, and "
            "plan-row scope drive the assignment."
        ),
        evidence_required="per-dimension relevance assignment + driver evidence",
    ),
    SystemMapStewardPhaseSpec(
        phase_id=SystemMapStewardPhase.AUDIT_CONNECTIONS,
        description=(
            "For each platform-component dimension marked at least "
            "`medium` relevance, audit whether the slice CONNECTED to "
            "the component. Produce a `PlatformComponentTouch` per "
            "dimension carrying observed_touch (connected/missed/n/a/"
            "exempted), evidence path or ref id, and a short "
            "explanation. The `feature_proof_receipt_chain` dimension "
            "delegates to receipt_steward."
        ),
        evidence_required="ordered tuple of PlatformComponentTouch entries + delegation refs",
    ),
    SystemMapStewardPhaseSpec(
        phase_id=SystemMapStewardPhase.SYNTHESIZE_GAPS,
        description=(
            "Collect missed pieces across the touches into a `missed_"
            "pieces` tuple; detect any NEW DISCONNECTIONS (platform "
            "pieces the slice surfaced that SYSTEM_MAP.md does not yet "
            "name); compute the coverage grade Literal (complete / "
            "partial / incomplete) from the per-dimension touches."
        ),
        evidence_required="missed_pieces list + new_disconnections list + coverage_grade",
    ),
    SystemMapStewardPhaseSpec(
        phase_id=SystemMapStewardPhase.PROPOSE_SYSTEM_MAP_UPDATE,
        description=(
            "When a new disconnection is surfaced, emit a typed "
            "`SystemMapRowProposal` carrying suggested row text, "
            "target section, and the surfacing slice id. The proposal "
            "lands directly into SYSTEM_MAP.md when an edit-only "
            "`SystemMapStewardScopeClaim` is in scope; otherwise it "
            "stays `pending` for operator review. No proposal emits "
            "when the audit finds no new disconnections."
        ),
        evidence_required="proposal id (empty when none) + status + target section",
    ),
    SystemMapStewardPhaseSpec(
        phase_id=SystemMapStewardPhase.EMIT_COVERAGE_AUDIT_RECEIPT,
        description=(
            "Assemble the typed `PlatformCoverageAudit` from the "
            "ordered touches, missed pieces, surfaced disconnections, "
            "and coverage grade. Persist via the governed JSON-mapping "
            "writer used by other lifecycle stores. The receipt is the "
            "single observable artifact this role produces per audit."
        ),
        evidence_required="PlatformCoverageAudit id + persisted path + write fingerprint",
    ),
)


def system_map_steward_role_spec() -> SystemMapStewardRoleSpec:
    """Return the canonical typed instance of ``SystemMapStewardRoleSpec``.

    Single source of truth for the platform-coverage audit role.
    Callers that need to inspect the ritual (matrix renderers, dispatch
    routers, agent role-authority gates, gate-composition wiring)
    should consume this rather than re-deriving from documentation
    prose.
    """
    return SystemMapStewardRoleSpec(phases=_CANONICAL_PHASES)


__all__ = [
    "PLATFORM_COMPONENT_IDS",
    "SYSTEM_MAP_ROW_PROPOSAL_CONTRACT_ID",
    "SYSTEM_MAP_STEWARD_AUDIT_RECEIPT_CONTRACT_ID",
    "SYSTEM_MAP_STEWARD_COMPONENT_TOUCH_CONTRACT_ID",
    "SYSTEM_MAP_STEWARD_PHASE_SPEC_CONTRACT_ID",
    "SYSTEM_MAP_STEWARD_ROLE_ID",
    "SYSTEM_MAP_STEWARD_ROLE_SPEC_CONTRACT_ID",
    "SYSTEM_MAP_STEWARD_SCHEMA_VERSION",
    "SYSTEM_MAP_STEWARD_SCOPE_CLAIM_CONTRACT_ID",
    "CoverageGrade",
    "PlatformComponentRelevance",
    "PlatformComponentTouch",
    "PlatformComponentTouchStatus",
    "PlatformCoverageAudit",
    "SystemMapRowProposal",
    "SystemMapRowProposalStatus",
    "SystemMapStewardPhase",
    "SystemMapStewardPhaseSpec",
    "SystemMapStewardRoleSpec",
    "SystemMapStewardScopeClaim",
    "SystemMapStewardScopeMode",
    "system_map_steward_role_spec",
]
