"""Typed consolidation of the semantic-TDD ritual into one role with phases.

Previously the TDD work was fragmented across three role ids
(``tdd_discovery``, ``tdd_first_role``, ``dogfood_test``) all carrying
``RoleCapabilityClass.TEST``. The fragmentation made the ritual harder
to reason about: each phase looked like a separate role assignment even
though they're sub-actions of one disciplined workflow.

This module ships the consolidated typed contract: one
``SemanticTDDRoleSpec`` with typed ``SemanticTDDRolePhase`` enum members
for each sub-action. ``role_profile._ROLE_ID_ALIASES`` is extended so the
three legacy ids resolve to ``semantic_tdd`` during migration; the
legacy ids remain in ``DEFAULT_ROLE_IDS`` as visible debt (Phase 0.2b
xfail-strict ratchet) until callsite migration is complete and
retirement is safe.

The phases below match the 9-step ritual documented in the execution
plan's Process section. The live-state invariant
``test_semantic_tdd_role_spec_phases_match_documented_ritual`` catches
any drift between the typed contract and the doc.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .enum_compat import StrEnum
from .role_profile import RoleCapabilityClass


class SemanticTDDRolePhase(StrEnum):
    """Typed sub-actions of the semantic-TDD ritual.

    Order matters: phases run sequentially within each slice. The
    ordering matches the plan's Step 1..9 with the typed-role-only
    columns (steps 1, 6, 8, 9 are owned by other typed roles —
    duplicate_scope_guard / plan_steward / reviewer — and don't appear
    here).
    """

    DISCOVERY = "discovery"
    RED_FIRST = "red_first"
    CODE_APPLY = "code_apply"
    GREEN_VERIFY = "green_verify"
    REINFORCE = "reinforce"
    DOGFOOD_PROOF = "dogfood_proof"
    RECEIPT = "receipt"
    REVIEW = "review"


@dataclass(frozen=True, slots=True)
class SemanticTDDRolePhaseSpec:
    """One phase of the ritual carrying typed evidence requirements."""

    phase_id: SemanticTDDRolePhase
    description: str
    evidence_required: str
    capability_class: RoleCapabilityClass = RoleCapabilityClass.TEST


@dataclass(frozen=True, slots=True)
class SemanticTDDRoleSpec:
    """Typed contract for the single consolidated semantic-TDD role.

    Any agent (claude, codex, cursor, future) can hold this role per
    typed ``actor_authorities`` grants. The role is agent-agnostic; the
    phases describe the work, not the identity of the actor doing it.
    """

    role_id: str = "semantic_tdd"
    capability_class: RoleCapabilityClass = RoleCapabilityClass.TEST
    phases: tuple[SemanticTDDRolePhaseSpec, ...] = field(default_factory=tuple)
    deprecated_aliases: tuple[str, ...] = (
        "tdd_discovery",
        "tdd_first_role",
        "dogfood_test",
    )
    documentation_doc: str = "dev/active/live_state_semantic_tdd_plan.md"
    schema_version: int = 1
    contract_id: str = "SemanticTDDRoleSpec"


_CANONICAL_PHASES: tuple[SemanticTDDRolePhaseSpec, ...] = (
    SemanticTDDRolePhaseSpec(
        phase_id=SemanticTDDRolePhase.DISCOVERY,
        description=(
            "Identify the invariant the slice should enforce. Read live "
            "state, plan rows, packets, and prior receipts. Write down "
            "what the test will assert."
        ),
        evidence_required="invariant statement + scope of consumers it protects",
    ),
    SemanticTDDRolePhaseSpec(
        phase_id=SemanticTDDRolePhase.RED_FIRST,
        description=(
            "Write the scenario or live-state invariant test with a "
            "plain-language file name. Run targeted pytest. Observe RED "
            "for the right reason."
        ),
        evidence_required="failing pytest node id + assertion error text quoted in the matrix row",
    ),
    SemanticTDDRolePhaseSpec(
        phase_id=SemanticTDDRolePhase.CODE_APPLY,
        description=(
            "Apply the minimum-cut fix at named file:line sites. Reuse "
            "existing typed substrate. No workarounds, no `--no-verify`, "
            "no parallel bypass paths."
        ),
        evidence_required="commit SHA or diff range + file:line list",
    ),
    SemanticTDDRolePhaseSpec(
        phase_id=SemanticTDDRolePhase.GREEN_VERIFY,
        description=(
            "Re-run the targeted pytest. Observe GREEN. Structural "
            "confirmation only — not yet the real GREEN."
        ),
        evidence_required="pytest passing output captured to the matrix row",
    ),
    SemanticTDDRolePhaseSpec(
        phase_id=SemanticTDDRolePhase.REINFORCE,
        description=(
            "Apply slice-appropriate A26 reinforcement layers: "
            "property-based, architecture, consumer, differential, "
            "mutation, snapshot, dead-code, branch coverage."
        ),
        evidence_required="list of A26 layers applied + their results",
        capability_class=RoleCapabilityClass.TEST,
    ),
    SemanticTDDRolePhaseSpec(
        phase_id=SemanticTDDRolePhase.DOGFOOD_PROOF,
        description=(
            "Run live devctl / peer-spawn / review-channel. Produce the "
            "observable artifact the slice promised — file on disk, "
            "sha256, typed receipt, JSON field reaching the consumer. "
            "This is the real GREEN."
        ),
        evidence_required="artifact path(s) + sha256 + typed receipt id(s)",
    ),
    SemanticTDDRolePhaseSpec(
        phase_id=SemanticTDDRolePhase.RECEIPT,
        description=(
            "Update matrix row in dev/active/semantic_tdd_lane.md with "
            "evidence refs. Emit FeatureProofReceipt(proven_passed). "
            "Advance plan rows in dev/state/plan_index.jsonl."
        ),
        evidence_required="matrix row diff + FeatureProofReceipt id + advanced plan_row_id",
    ),
    SemanticTDDRolePhaseSpec(
        phase_id=SemanticTDDRolePhase.REVIEW,
        description=(
            "Reviewer reads the receipt + matrix + dogfood artifacts. "
            "Either accepts or sends review_failed back to RED_FIRST."
        ),
        evidence_required="reviewer packet id (review_accepted or review_failed)",
    ),
)


def semantic_tdd_role_spec() -> SemanticTDDRoleSpec:
    """Return the canonical typed instance of the SemanticTDDRoleSpec.

    Single source of truth for the consolidated role. Callers that need
    to inspect the ritual (matrix renderers, dispatch routers, agent
    role authority gates) should consume this rather than re-deriving
    from documentation prose.
    """
    return SemanticTDDRoleSpec(phases=_CANONICAL_PHASES)


__all__ = [
    "SemanticTDDRolePhase",
    "SemanticTDDRolePhaseSpec",
    "SemanticTDDRoleSpec",
    "semantic_tdd_role_spec",
]
