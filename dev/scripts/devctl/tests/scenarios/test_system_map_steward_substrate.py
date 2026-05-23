"""Scenario tests for the typed system-map-steward role substrate (A38.3 S1).

The system-map-steward role is a PLATFORM-COVERAGE audit role (NOT a
TDD-discipline audit role — see ``evidence.md`` Case 11 for the
category-error correction story). Per slice, the audit asks: did this
slice CONNECT to the relevant pieces of the AI governance platform
that exist? The 15 audit dimensions are PLATFORM COMPONENTS (the
guards, probes, contracts, plan registry, INDEX.md, SYSTEM_MAP.md,
ai_governance_platform.md layers, devctl CLI inventory, etc.), not
TDD-ritual observables.

These tests pin the substrate shape (role-id resolution, phase enum,
role-spec factory, dataclass shapes, audit-dimension constants) and
surface the per-slice platform-coverage gap and the maintenance-rule
mechanization gap as visible debt.

Test layout:

- ``test_system_map_steward_role_id_resolves_through_default_role_ids``
  current-safety (2a). GREEN once the role id is in DEFAULT_ROLE_IDS,
  the alias mappings (including the unified ``system_alignment_role``)
  resolve, and ``role_capability_classes`` returns ``governance``.

- ``test_system_map_steward_role_spec_has_six_phases`` — current-safety
  (2a). GREEN once the typed dataclasses + factory are in place. The
  factory must return six typed phase specs covering
  LOAD_PLATFORM_INVENTORY through EMIT_COVERAGE_AUDIT_RECEIPT in order.

- ``test_system_map_steward_has_fifteen_platform_component_ids`` —
  current-safety (2a). GREEN once ``PLATFORM_COMPONENT_IDS`` is the
  canonical 15-entry tuple (the corrected platform-coverage dimensions
  per Case 11, NOT the TDD-discipline dimensions from the rejected
  original proposal).

- ``test_platform_coverage_audit_dataclass_is_frozen_and_slots`` —
  current-safety (2a). GREEN once the receipt + touch + scope-claim
  + row-proposal dataclasses are frozen + slots-enabled (matches the
  shape of ``ReceiptStewardAuditReceipt`` and other typed-state
  dataclasses).

- ``test_platform_coverage_audit_grade_thresholds_well_formed`` —
  current-safety (2a). GREEN once the ``CoverageGrade`` Literal carries
  the three documented grades.

- ``test_every_completed_slice_has_paired_platform_coverage_audit``
  target architecture (2b). xfail-strict ratchet. RED until S2 audit
  invocation lands AND backfill produces ``PlatformCoverageAudit``
  artifacts for completed slices.

- ``test_every_disconnection_surfaced_in_recent_slices_has_system_map_row_proposal``
  target architecture (2b). xfail-strict ratchet. The maintenance-rule
  mechanization — once the audit role surfaces a new disconnection,
  a typed ``SystemMapRowProposal`` must exist.

- ``test_mutation_commits_to_production_runtime_must_link_coverage_audit``
  hunt invariant (2c). xfail-strict. Matches commits touching
  ``dev/scripts/devctl/runtime/**.py`` whose plan rows reach
  ``done``/``applied``/``completed`` and require a linked
  ``PlatformCoverageAudit``.
"""

from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PLATFORM_COVERAGE_AUDIT_DIR = (
    REPO_ROOT / "dev" / "reports" / "platform_coverage_audits"
)
SYSTEM_MAP_PROPOSAL_DIR = (
    REPO_ROOT / "dev" / "reports" / "system_map_row_proposals"
)
PLAN_INDEX_PATH = REPO_ROOT / "dev" / "state" / "plan_index.jsonl"


# ---------------------------------------------------------------------------
# Phase 2a — current-safety quarantines (GREEN once substrate lands)
# ---------------------------------------------------------------------------


def test_system_map_steward_role_id_resolves_through_default_role_ids():
    """Phase 2a — current-safety quarantine.

    The typed ``system_map_steward`` role id must be registered in
    ``DEFAULT_ROLE_IDS`` and resolve through ``normalize_role_id`` for
    dash-form, spelling-variant, and legacy ``system_alignment_role``
    inputs. The capability classes function must return ``governance``
    as the role's secondary tag.

    The ``system_alignment_role`` -> ``system_map_steward`` alias is
    the unification path: ``system_alignment_role`` was an
    underdeveloped placeholder in ``DEFAULT_ROLE_IDS`` carrying
    ``(GOVERNANCE, ARCHITECTURE)`` capability classes but no typed
    substrate. The system-map-steward role specializes that placeholder
    into a typed audit surface; the alias preserves backwards
    compatibility for any caller that referenced the legacy id.
    """
    from dev.scripts.devctl.runtime.role_profile import (
        DEFAULT_ROLE_IDS,
        normalize_role_id,
        role_capability_classes,
    )

    assert "system_map_steward" in DEFAULT_ROLE_IDS, (
        "INVARIANT VIOLATED: system_map_steward_role_id_resolves_through_default_role_ids\n"
        "  system_map_steward must appear in DEFAULT_ROLE_IDS so typed actor\n"
        "  authority can reference it without a custom-role definition.\n"
        "  Fix: in dev/scripts/devctl/runtime/role_profile.py extend\n"
        "  DEFAULT_ROLE_IDS with 'system_map_steward'."
    )

    alias_inputs = (
        "system-map-steward",
        "system_map_role",
        "systemmap_steward",
        "system_alignment_role",
        "system-alignment-role",
        "SystemMapSteward",
    )
    mismatches: list[tuple[str, str]] = []
    for alias in alias_inputs:
        resolved = normalize_role_id(alias)
        if resolved != "system_map_steward":
            mismatches.append((alias, resolved))
    assert not mismatches, (
        "INVARIANT VIOLATED: system_map_steward alias resolution\n"
        f"  aliases not resolving to system_map_steward: {mismatches}\n"
        "  Fix: extend _ROLE_ID_ALIASES in role_profile.py with each input."
    )

    capabilities = role_capability_classes("system_map_steward")
    assert "governance" in capabilities, (
        "INVARIANT VIOLATED: system_map_steward capability_class\n"
        f"  role_capability_classes returned: {capabilities!r}\n"
        "  Fix: extend _ROLE_CAPABILITY_CLASSES with\n"
        "    'system_map_steward': (RoleCapabilityClass.GOVERNANCE,)."
    )


def test_system_map_steward_role_spec_has_six_phases():
    """Phase 2a — current-safety quarantine.

    ``system_map_steward_role_spec()`` must return a typed role spec
    whose phases tuple has six entries covering the documented audit
    ritual: LOAD_PLATFORM_INVENTORY, DETERMINE_SLICE_RELEVANCE,
    AUDIT_CONNECTIONS, SYNTHESIZE_GAPS, PROPOSE_SYSTEM_MAP_UPDATE,
    EMIT_COVERAGE_AUDIT_RECEIPT.
    """
    from dev.scripts.devctl.runtime.system_map_steward_role import (
        SystemMapStewardPhase,
        SystemMapStewardPhaseSpec,
        SystemMapStewardRoleSpec,
        system_map_steward_role_spec,
    )

    spec = system_map_steward_role_spec()
    assert isinstance(spec, SystemMapStewardRoleSpec), (
        f"system_map_steward_role_spec() must return SystemMapStewardRoleSpec; "
        f"got {type(spec).__name__}"
    )
    assert spec.role_id == "system_map_steward", (
        f"SystemMapStewardRoleSpec.role_id must be 'system_map_steward'; "
        f"got {spec.role_id!r}"
    )
    assert len(spec.phases) == 6, (
        f"SystemMapStewardRoleSpec.phases must have 6 entries; "
        f"got {len(spec.phases)}"
    )

    expected_phase_ids = (
        SystemMapStewardPhase.LOAD_PLATFORM_INVENTORY,
        SystemMapStewardPhase.DETERMINE_SLICE_RELEVANCE,
        SystemMapStewardPhase.AUDIT_CONNECTIONS,
        SystemMapStewardPhase.SYNTHESIZE_GAPS,
        SystemMapStewardPhase.PROPOSE_SYSTEM_MAP_UPDATE,
        SystemMapStewardPhase.EMIT_COVERAGE_AUDIT_RECEIPT,
    )
    actual_phase_ids = tuple(p.phase_id for p in spec.phases)
    assert actual_phase_ids == expected_phase_ids, (
        "INVARIANT VIOLATED: system_map_steward phase ordering\n"
        f"  expected: {tuple(str(p) for p in expected_phase_ids)}\n"
        f"  actual:   {tuple(str(p) for p in actual_phase_ids)}\n"
        "  Fix: update _CANONICAL_PHASES in system_map_steward_role.py."
    )

    for phase_spec in spec.phases:
        assert isinstance(phase_spec, SystemMapStewardPhaseSpec), (
            f"phase entry must be SystemMapStewardPhaseSpec; "
            f"got {type(phase_spec).__name__}"
        )
        assert phase_spec.description, (
            f"phase {phase_spec.phase_id} missing description"
        )
        assert phase_spec.evidence_required, (
            f"phase {phase_spec.phase_id} missing evidence_required"
        )


def test_system_map_steward_has_fifteen_platform_component_ids():
    """Phase 2a — current-safety quarantine.

    The role exposes 15 PLATFORM-COMPONENT audit dimensions (NOT
    TDD-discipline dimensions). The exact list is the corrected design
    from ``evidence.md`` Case 11 / ``delete_after_ingest.md`` A38.3
    amendment; any drift surfaces as a substrate regression.

    The ``feature_proof_receipt_chain`` dimension is the typed
    delegation boundary to ``receipt_steward``; its presence in this
    list records the audit dimension while the verification logic
    lives in the receipt-steward substrate (loose coupling via typed
    audit contract).
    """
    from dev.scripts.devctl.runtime.system_map_steward_role import (
        PLATFORM_COMPONENT_IDS,
        SystemMapStewardRoleSpec,
        system_map_steward_role_spec,
    )

    expected_components = (
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

    assert len(PLATFORM_COMPONENT_IDS) == 15, (
        "INVARIANT VIOLATED: platform_component_ids_count\n"
        f"  expected: 15 audit dimensions (PLATFORM components, not TDD steps)\n"
        f"  actual:   {len(PLATFORM_COMPONENT_IDS)}\n"
        "  See evidence.md Case 11 for the corrected design."
    )

    assert PLATFORM_COMPONENT_IDS == expected_components, (
        "INVARIANT VIOLATED: platform_component_ids_canonical_order\n"
        f"  expected: {expected_components}\n"
        f"  actual:   {PLATFORM_COMPONENT_IDS}\n"
        "  Fix: update PLATFORM_COMPONENT_IDS in system_map_steward_role.py."
    )

    # The role spec carries the same tuple as its own platform_component_ids
    # field so callers can introspect from the spec without importing the
    # module-level constant.
    spec = system_map_steward_role_spec()
    assert isinstance(spec, SystemMapStewardRoleSpec)
    assert spec.platform_component_ids == PLATFORM_COMPONENT_IDS, (
        "SystemMapStewardRoleSpec.platform_component_ids must reflect the "
        "canonical PLATFORM_COMPONENT_IDS tuple; got drift between the two."
    )


def test_platform_coverage_audit_dataclass_is_frozen_and_slots():
    """Phase 2a — current-safety quarantine.

    The typed substrate dataclasses must be frozen + slots-enabled
    matching the sibling shape used by ``ReceiptStewardAuditReceipt``
    and other typed-state dataclasses. The tested set covers the
    audit receipt, per-component touch, role spec, phase spec,
    scope-claim, and row-proposal types.
    """
    from dev.scripts.devctl.runtime.system_map_steward_role import (
        PlatformComponentTouch,
        PlatformCoverageAudit,
        SystemMapRowProposal,
        SystemMapStewardPhaseSpec,
        SystemMapStewardRoleSpec,
        SystemMapStewardScopeClaim,
    )

    typed_classes = (
        PlatformComponentTouch,
        PlatformCoverageAudit,
        SystemMapRowProposal,
        SystemMapStewardPhaseSpec,
        SystemMapStewardRoleSpec,
        SystemMapStewardScopeClaim,
    )

    for cls in typed_classes:
        params = getattr(cls, "__dataclass_params__", None)
        assert params is not None, (
            f"{cls.__name__} must be a dataclass; missing __dataclass_params__"
        )
        assert params.frozen, (
            f"{cls.__name__} must be frozen=True; got frozen={params.frozen}"
        )
        # `slots=True` removes __dict__ from the class.
        assert "__dict__" not in cls.__dict__, (
            f"{cls.__name__} must be slots=True; __dict__ present"
        )
        # All dataclasses must declare at least one field (no empty shells).
        assert fields(cls), (
            f"{cls.__name__} must declare at least one dataclass field"
        )

    # The per-component touch dataclass must carry the canonical
    # contract_id and schema_version; the substrate ratchet depends on
    # those staying stable. Construct one with sample enum values and
    # assert the typed constants.
    sample_touch = PlatformComponentTouch(
        component_id="plan_registry_tied",
        relevance_to_slice=_sample_relevance(),
        observed_touch=_sample_touch_status(),
    )
    assert sample_touch.contract_id == "PlatformComponentTouch"
    assert sample_touch.schema_version == 1


def test_platform_coverage_audit_grade_thresholds_well_formed():
    """Phase 2a — current-safety quarantine.

    The ``CoverageGrade`` Literal carries exactly three documented
    grades — ``complete``, ``partial``, ``incomplete`` — in canonical
    order. Audit-dimension evaluators in S2 will assign one grade per
    audit based on the per-dimension touches; the substrate must lock
    the Literal so the evaluator output stays stable.
    """
    import typing

    from dev.scripts.devctl.runtime.system_map_steward_role import (
        CoverageGrade,
    )

    grades = typing.get_args(CoverageGrade)
    assert grades == ("complete", "partial", "incomplete"), (
        "INVARIANT VIOLATED: coverage_grade_thresholds_well_formed\n"
        f"  expected CoverageGrade args: ('complete', 'partial', 'incomplete')\n"
        f"  actual:                      {grades}\n"
        "  Fix: update CoverageGrade Literal in system_map_steward_role.py."
    )


# ---------------------------------------------------------------------------
# Helpers used inside the dataclass-shape test
# ---------------------------------------------------------------------------


def _sample_relevance():
    from dev.scripts.devctl.runtime.system_map_steward_role import (
        PlatformComponentRelevance,
    )

    return PlatformComponentRelevance.HIGH


def _sample_touch_status():
    from dev.scripts.devctl.runtime.system_map_steward_role import (
        PlatformComponentTouchStatus,
    )

    return PlatformComponentTouchStatus.CONNECTED


# ---------------------------------------------------------------------------
# Phase 2b — target architecture (xfail-strict ratchets)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "A38.3 S1 — target: every applied/completed PlanRow with a "
        "commit_anchor_ref has a paired PlatformCoverageAudit at "
        "dev/reports/platform_coverage_audits/{commit_sha}*.json. "
        "The audit-invocation logic and backfill land in S2; "
        "this ratchet stays RED until then. Flips to GREEN once S2 "
        "audit invocation produces real PlatformCoverageAudit "
        "receipts for completed slices."
    ),
)
def test_every_completed_slice_has_paired_platform_coverage_audit():
    """Phase 2b — target architecture, xfail-strict ratchet.

    Reads ``dev/state/plan_index.jsonl``; for every PlanRow whose
    status is applied/completed/done and whose ``commit_anchor_ref``
    carries a commit SHA, asserts that
    ``dev/reports/platform_coverage_audits/{commit_sha}*.json`` exists.
    Collects gaps and fails when non-empty.

    Stays RED as visible debt until A38.3 S2 (audit invocation logic)
    + backfill close the platform-coverage gap.
    """
    assert PLAN_INDEX_PATH.exists(), (
        f"plan_index.jsonl missing at {PLAN_INDEX_PATH}; cannot run audit"
    )
    assert PLATFORM_COVERAGE_AUDIT_DIR.exists(), (
        "INVARIANT VIOLATED: platform_coverage_audit_dir_missing\n"
        f"  expected directory: {PLATFORM_COVERAGE_AUDIT_DIR}\n"
        "  The directory is created by A38.3 S2 when the first audit "
        "is emitted; ratchets to GREEN when audits begin landing."
    )

    closing_statuses = {"applied", "completed", "done"}
    gaps: list[tuple[str, str]] = []
    for line in PLAN_INDEX_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        status = str(row.get("status") or "")
        if status not in closing_statuses:
            continue
        commit_ref = str(row.get("commit_anchor_ref") or "")
        if not commit_ref:
            continue
        sha = commit_ref.split(":", 1)[-1] if ":" in commit_ref else commit_ref
        if not sha:
            continue
        matches = list(PLATFORM_COVERAGE_AUDIT_DIR.glob(f"{sha}*.json"))
        if not matches:
            gaps.append((str(row.get("row_id") or ""), sha))

    assert not gaps, (
        "INVARIANT VIOLATED: every_completed_slice_has_paired_platform_coverage_audit\n"
        f"  {len(gaps)} completed PlanRows have no paired\n"
        "  PlatformCoverageAudit under dev/reports/platform_coverage_audits/.\n"
        "  This is the platform-coverage gap A38.3 system_map_steward audits.\n"
        + "\n".join(f"  - {row_id} (commit {sha})" for row_id, sha in gaps[:10])
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "A38.3 S1 — target: every disconnection surfaced in a recent "
        "audit (i.e., every new_disconnections_surfaced entry on a "
        "PlatformCoverageAudit) has a paired SystemMapRowProposal at "
        "dev/reports/system_map_row_proposals/. This is the "
        "maintenance-rule mechanization (auto-emit a proposal when a "
        "new disconnection is found). The mechanism lands in S2..S3; "
        "until then this stays RED as visible debt."
    ),
)
def test_every_disconnection_surfaced_in_recent_slices_has_system_map_row_proposal():
    """Phase 2b — target architecture, xfail-strict ratchet.

    Reads PlatformCoverageAudit receipts from
    ``dev/reports/platform_coverage_audits/``; for each receipt with a
    non-empty ``new_disconnections_surfaced`` tuple, asserts that a
    matching ``SystemMapRowProposal`` exists under
    ``dev/reports/system_map_row_proposals/``. The pairing rule is
    one proposal per surfaced disconnection per slice.

    Stays RED until A38.3 S2..S3 wire the auto-emission path. The
    maintenance-rule mechanization is the role's contribution to the
    SYSTEM_MAP.md freshness contract: surfaced disconnections must
    not silently disappear.
    """
    assert PLATFORM_COVERAGE_AUDIT_DIR.exists(), (
        "INVARIANT VIOLATED: platform_coverage_audit_dir_missing\n"
        f"  expected directory: {PLATFORM_COVERAGE_AUDIT_DIR}\n"
        "  The directory is created by A38.3 S2 when the first audit lands."
    )
    assert SYSTEM_MAP_PROPOSAL_DIR.exists(), (
        "INVARIANT VIOLATED: system_map_proposal_dir_missing\n"
        f"  expected directory: {SYSTEM_MAP_PROPOSAL_DIR}\n"
        "  The directory is created by A38.3 S3 when the first "
        "SystemMapRowProposal is emitted."
    )

    missing_proposals: list[tuple[str, str]] = []
    for audit_path in PLATFORM_COVERAGE_AUDIT_DIR.glob("*.json"):
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        surfaced = audit.get("new_disconnections_surfaced") or []
        if not isinstance(surfaced, list) or not surfaced:
            continue
        slice_id = str(audit.get("slice_id") or "")
        for disconnection in surfaced:
            # Look for a proposal whose surfaced_by_slice_id matches and
            # whose surfaced_disconnection matches the entry.
            found = False
            for proposal_path in SYSTEM_MAP_PROPOSAL_DIR.glob("*.json"):
                try:
                    proposal = json.loads(
                        proposal_path.read_text(encoding="utf-8")
                    )
                except json.JSONDecodeError:
                    continue
                if (
                    str(proposal.get("surfaced_by_slice_id") or "") == slice_id
                    and str(proposal.get("surfaced_disconnection") or "")
                    == str(disconnection)
                ):
                    found = True
                    break
            if not found:
                missing_proposals.append((slice_id, str(disconnection)))

    assert not missing_proposals, (
        "INVARIANT VIOLATED: every_disconnection_has_system_map_row_proposal\n"
        f"  {len(missing_proposals)} surfaced disconnections lack a paired\n"
        "  SystemMapRowProposal. The maintenance rule requires one proposal\n"
        "  per surfaced disconnection per slice.\n"
        + "\n".join(
            f"  - slice {slice_id}: {disconnection}"
            for slice_id, disconnection in missing_proposals[:10]
        )
    )


# ---------------------------------------------------------------------------
# Phase 2c — hunt invariant (xfail-strict)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "A38.3 S1 — hunt invariant target: every commit touching a "
        "production runtime module (dev/scripts/devctl/runtime/**.py) "
        "whose plan row reaches done/applied/completed must link a "
        "PlatformCoverageAudit. Today many runtime commits ship with "
        "no audit; the hunt ratchets when audit-invocation wiring (S2) "
        "lands and the existing runtime commits are backfilled. Flips "
        "to GREEN as backfill closes the gap."
    ),
)
def test_mutation_commits_to_production_runtime_must_link_coverage_audit():
    """Phase 2c — hunt invariant, xfail-strict ratchet.

    Cross-references plan rows whose status is done/applied/completed,
    whose ``commit_anchor_ref`` is populated, and whose touched paths
    intersect ``dev/scripts/devctl/runtime/**.py`` (the production
    runtime hot zone). For each such commit, asserts that a
    ``PlatformCoverageAudit`` exists at
    ``dev/reports/platform_coverage_audits/{commit_sha}*.json``.

    The hunt is deliberately narrow: only the runtime hot zone is
    audited at this ratchet level. S2/S3 can broaden the scope. The
    invariant gives reviewers a single typed dial to ratchet
    platform-coverage discipline upward without rewriting test logic.
    """
    assert PLAN_INDEX_PATH.exists(), (
        f"plan_index.jsonl missing at {PLAN_INDEX_PATH}"
    )
    assert PLATFORM_COVERAGE_AUDIT_DIR.exists(), (
        "INVARIANT VIOLATED: platform_coverage_audit_dir_missing\n"
        f"  expected directory: {PLATFORM_COVERAGE_AUDIT_DIR}\n"
        "  The directory is created by A38.3 S2 when the first audit lands."
    )

    closing_statuses = {"applied", "completed", "done"}
    runtime_prefix = "dev/scripts/devctl/runtime/"
    unaudited: list[tuple[str, str]] = []
    for line in PLAN_INDEX_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        status = str(row.get("status") or "")
        if status not in closing_statuses:
            continue
        commit_ref = str(row.get("commit_anchor_ref") or "")
        if not commit_ref:
            continue
        sha = commit_ref.split(":", 1)[-1] if ":" in commit_ref else commit_ref
        if not sha:
            continue
        # Touch heuristic: look across multiple known fields that carry
        # touched-paths information on a PlanRow. A runtime-touching row
        # must have at least one entry under runtime_prefix.
        candidate_paths: list[str] = []
        for field_name in (
            "touched_paths",
            "evidence_paths",
            "evidence_artifacts",
            "work_evidence_paths",
        ):
            value = row.get(field_name)
            if isinstance(value, list):
                candidate_paths.extend(str(v) for v in value)
            elif isinstance(value, str) and value:
                candidate_paths.append(value)
        touched_runtime = any(
            path.startswith(runtime_prefix) for path in candidate_paths
        )
        if not touched_runtime:
            continue
        matches = list(PLATFORM_COVERAGE_AUDIT_DIR.glob(f"{sha}*.json"))
        if not matches:
            unaudited.append((str(row.get("row_id") or ""), sha))

    assert not unaudited, (
        "INVARIANT VIOLATED: mutation_commits_to_production_runtime_must_link_coverage_audit\n"
        f"  {len(unaudited)} runtime-touching closed PlanRows lack a paired\n"
        "  PlatformCoverageAudit. The hunt covers dev/scripts/devctl/runtime/**.\n"
        + "\n".join(
            f"  - {row_id} (commit {sha})" for row_id, sha in unaudited[:10]
        )
    )
