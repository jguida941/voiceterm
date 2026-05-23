"""Scenario tests for the typed receipt-steward role substrate (A38.2 S1).

The receipt-steward role is GOVERNANCE / audit-only. These tests pin
the substrate shape (role-id resolution, phase enum, role-spec factory)
and surface the per-slice FeatureProofReceipt coverage gap that
motivates A38.2 as visible debt.

Test layout:

- ``test_receipt_steward_role_id_resolves_through_default_role_ids`` —
  current-safety (2a). GREEN once the role id is in DEFAULT_ROLE_IDS,
  the alias mappings resolve dash-form/spelling variants, and
  ``role_capability_classes`` returns ``governance``.

- ``test_receipt_steward_role_spec_has_six_phases`` — current-safety
  (2a). GREEN once the typed dataclasses + factory are in place. The
  factory must return six typed phase specs covering DISCOVER_SLICE
  through EMIT_AUDIT_RECEIPT in order.

- ``test_every_applied_plan_row_has_paired_feature_proof_receipt`` —
  target architecture (2b). xfail-strict ratchet. RED until every
  applied/completed PlanRow with a commit_anchor_ref has a paired
  ``dev/reports/feature_proof_receipts/{commit_sha}.json``. The gap
  is the operator-admitted receipt-discipline shortfall the audit
  role exists to surface; it ratchets to GREEN when backfill or new
  per-slice receipts close it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]


def test_receipt_steward_role_id_resolves_through_default_role_ids():
    """Phase 2a — current-safety quarantine.

    The typed ``receipt_steward`` role id must be registered in
    ``DEFAULT_ROLE_IDS`` and resolve through ``normalize_role_id`` for
    dash-form and spelling-variant inputs. The capability classes
    function must return ``governance`` as the role's secondary tag.

    RED today (substrate not yet wired); GREEN once the
    ``receipt_steward_role`` module ships and ``role_profile`` is
    extended to include it.
    """
    from dev.scripts.devctl.runtime.role_profile import (
        DEFAULT_ROLE_IDS,
        normalize_role_id,
        role_capability_classes,
    )

    assert "receipt_steward" in DEFAULT_ROLE_IDS, (
        "INVARIANT VIOLATED: receipt_steward_role_id_resolves_through_default_role_ids\n"
        "  receipt_steward must appear in DEFAULT_ROLE_IDS so typed actor\n"
        "  authority can reference it without a custom-role definition.\n"
        "  Fix: in dev/scripts/devctl/runtime/role_profile.py extend\n"
        "  DEFAULT_ROLE_IDS with 'receipt_steward'."
    )

    alias_inputs = (
        "receipt-steward",
        "receipts_steward",
        "receipt_auditor",
        "receiptauditor",
        "ReceiptSteward",
    )
    mismatches: list[tuple[str, str]] = []
    for alias in alias_inputs:
        resolved = normalize_role_id(alias)
        if resolved != "receipt_steward":
            mismatches.append((alias, resolved))
    assert not mismatches, (
        "INVARIANT VIOLATED: receipt_steward alias resolution\n"
        f"  aliases not resolving to receipt_steward: {mismatches}\n"
        "  Fix: extend _ROLE_ID_ALIASES in role_profile.py with each input."
    )

    capabilities = role_capability_classes("receipt_steward")
    assert "governance" in capabilities, (
        "INVARIANT VIOLATED: receipt_steward capability_class\n"
        f"  role_capability_classes returned: {capabilities!r}\n"
        "  Fix: extend _ROLE_CAPABILITY_CLASSES with\n"
        "    'receipt_steward': (RoleCapabilityClass.GOVERNANCE,)."
    )


def test_receipt_steward_role_spec_has_six_phases():
    """Phase 2a — current-safety quarantine.

    ``receipt_steward_role_spec()`` must return a typed role spec whose
    phases tuple has six entries covering the documented audit ritual:
    DISCOVER_SLICE, INVENTORY_EVIDENCE_PATHS, VERIFY_RECEIPT_PRESENT,
    VERIFY_PYTEST_NODE_RESOLVABLE, VERIFY_COMMIT_SHA_LINKED,
    EMIT_AUDIT_RECEIPT.

    RED today (module + factory not yet written); GREEN once the
    typed substrate at ``dev/scripts/devctl/runtime/receipt_steward_role.py``
    is in place.
    """
    from dev.scripts.devctl.runtime.receipt_steward_role import (
        ReceiptStewardPhase,
        ReceiptStewardPhaseSpec,
        ReceiptStewardRoleSpec,
        receipt_steward_role_spec,
    )

    spec = receipt_steward_role_spec()
    assert isinstance(spec, ReceiptStewardRoleSpec), (
        f"receipt_steward_role_spec() must return ReceiptStewardRoleSpec; "
        f"got {type(spec).__name__}"
    )
    assert spec.role_id == "receipt_steward", (
        f"ReceiptStewardRoleSpec.role_id must be 'receipt_steward'; "
        f"got {spec.role_id!r}"
    )
    assert len(spec.phases) == 6, (
        f"ReceiptStewardRoleSpec.phases must have 6 entries; "
        f"got {len(spec.phases)}"
    )

    expected_phase_ids = (
        ReceiptStewardPhase.DISCOVER_SLICE,
        ReceiptStewardPhase.INVENTORY_EVIDENCE_PATHS,
        ReceiptStewardPhase.VERIFY_RECEIPT_PRESENT,
        ReceiptStewardPhase.VERIFY_PYTEST_NODE_RESOLVABLE,
        ReceiptStewardPhase.VERIFY_COMMIT_SHA_LINKED,
        ReceiptStewardPhase.EMIT_AUDIT_RECEIPT,
    )
    actual_phase_ids = tuple(p.phase_id for p in spec.phases)
    assert actual_phase_ids == expected_phase_ids, (
        "INVARIANT VIOLATED: receipt_steward phase ordering\n"
        f"  expected: {tuple(str(p) for p in expected_phase_ids)}\n"
        f"  actual:   {tuple(str(p) for p in actual_phase_ids)}\n"
        "  Fix: update _CANONICAL_PHASES in receipt_steward_role.py."
    )

    for phase_spec in spec.phases:
        assert isinstance(phase_spec, ReceiptStewardPhaseSpec), (
            f"phase entry must be ReceiptStewardPhaseSpec; "
            f"got {type(phase_spec).__name__}"
        )
        assert phase_spec.description, (
            f"phase {phase_spec.phase_id} missing description"
        )
        assert phase_spec.evidence_required, (
            f"phase {phase_spec.phase_id} missing evidence_required"
        )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "A38.2 S1 — target: every applied/completed PlanRow with a "
        "commit_anchor_ref has a paired FeatureProofReceipt at "
        "dev/reports/feature_proof_receipts/{commit_sha}.json. Many "
        "applied rows do not yet have receipts because of the operator-"
        "admitted receipt-discipline gap; receipt_steward S2..S4 closes "
        "it. Ratchets to GREEN when backfill or new slices land paired "
        "receipts."
    ),
)
def test_every_applied_plan_row_has_paired_feature_proof_receipt():
    """Phase 2b — target architecture, xfail-strict ratchet.

    Reads ``dev/state/plan_index.jsonl``; for every PlanRow whose
    status is applied or completed and whose commit_anchor_ref carries a
    commit SHA, asserts that
    ``dev/reports/feature_proof_receipts/{commit_sha}.json`` exists.
    Collects any gaps and fails when the list is non-empty.

    Stays RED as visible debt until the receipt-steward role and the
    backfill it surfaces close the per-slice receipt coverage gap.
    """
    plan_path = REPO_ROOT / "dev" / "state" / "plan_index.jsonl"
    fpr_dir = REPO_ROOT / "dev" / "reports" / "feature_proof_receipts"
    assert plan_path.exists(), (
        f"plan_index.jsonl missing at {plan_path}; cannot run audit"
    )
    assert fpr_dir.exists(), (
        f"FeatureProofReceipt directory missing at {fpr_dir}"
    )

    closing_statuses = {"applied", "completed"}
    gaps: list[tuple[str, str]] = []
    for line in plan_path.read_text(encoding="utf-8").splitlines():
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
        matches = list(fpr_dir.glob(f"{sha}*.json"))
        if not matches:
            gaps.append((str(row.get("row_id") or ""), sha))

    assert not gaps, (
        "INVARIANT VIOLATED: every_applied_plan_row_has_paired_feature_proof_receipt\n"
        f"  {len(gaps)} applied/completed PlanRows have no paired\n"
        "  FeatureProofReceipt under dev/reports/feature_proof_receipts/.\n"
        "  This is the receipt-discipline gap A38.2 receipt_steward audits.\n"
        + "\n".join(f"  - {row_id} (commit {sha})" for row_id, sha in gaps[:10])
    )
