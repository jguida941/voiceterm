# Receipt Steward Lane

This file is a **maintained projection** of the receipt-steward role's
purpose and the audit ritual it performs. It is not durable plan
authority.

Durable authority lives in:

- the typed substrate at `dev/scripts/devctl/runtime/receipt_steward_role.py`
- the role registry in `dev/scripts/devctl/runtime/role_profile.py`
  (`DEFAULT_ROLE_IDS`, `_ROLE_CAPABILITY_CLASSES`, `_ROLE_ID_ALIASES`)
- the scenario tests under `dev/scripts/devctl/tests/scenarios/`
- the per-slice `FeatureProofReceipt` artifacts under
  `dev/reports/feature_proof_receipts/`
- `dev/state/plan_index.jsonl` (PlanRow registry the role audits against)

This lane describes the role; the typed substrate enforces it.

## Active row

- `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`
- Branch: `extraction/guardir-core-p0-proof-integrity`
- Plan-row scope: `A38-RECEIPT-STEWARD-ROLE-S1..S4` (S1 substrate landed; CLI,
  scope-claim lifecycle, gate composition, and exemption lifecycle remain).

## Purpose

The receipt-steward role audits whether per-slice `FeatureProofReceipt`
emission happens with a valid pytest node id, commit SHA, and real-life
test status. The role is **audit-only / GOVERNANCE**: it READS evidence
and EMITS a typed `ReceiptStewardAuditReceipt`; it never mutates plan or
repo state. The role closes the operator-admitted receipt-discipline gap
where applied PlanRows ship without a paired FeatureProofReceipt.

## Audit ritual (6 phases)

1. `DISCOVER_SLICE` — resolve the typed slice from a requested slice id.
   Read `dev/state/plan_index.jsonl` for the matching PlanRow.
2. `INVENTORY_EVIDENCE_PATHS` — enumerate on-disk paths that should carry
   evidence: the FPR JSON, the dogfood evidence ref, scenario tests
   declared in `tests_run`, related lane matrix rows.
3. `VERIFY_RECEIPT_PRESENT` — confirm a `FeatureProofReceipt` exists at
   `dev/reports/feature_proof_receipts/{commit_sha}.json`. A missing
   receipt is the strongest blocking signal.
4. `VERIFY_PYTEST_NODE_RESOLVABLE` — read the receipt's `tests_run` field
   and assert at least one entry is a concrete pytest node id (contains
   `::`). Non-resolvable is advisory only.
5. `VERIFY_COMMIT_SHA_LINKED` — confirm the `commit_sha` matches the
   slice's committed work and exists in local git history. Mismatched or
   unknown SHA contributes `stale_commit_reference` to the taxonomy.
6. `EMIT_AUDIT_RECEIPT` — assemble the typed
   `ReceiptStewardAuditReceipt` and persist via the governed
   JSON-mapping writer used by other lifecycle stores.

## Audit output shape

The role emits a single typed `ReceiptStewardAuditReceipt` per audit
invocation, carrying:

- `audit_id`, `slice_id`, `plan_row_id`, `commit_sha`, `audited_at_utc`
- `targets` — typed `ReceiptStewardAuditTargets` boolean matrix
- `missing_items` — 7-value taxonomy (5 blocking + 2 advisory):
  `missing_completely`, `missing_pytest_node`, `stale_commit_reference`,
  `dangling_plan_row`, `no_evidence_case` (blocking);
  `pytest_node_unresolvable`, `dirty_tree_at_audit` (advisory)
- `feature_proof_receipt_path` — path to the audited FPR (empty when
  the FPR is missing entirely)
- `actor_role` — `receipt_steward` (the role identity that ran the audit)
- `schema_version`, `contract_id` — standard typed-state fields

## Substrate scope (this slice, A38.2 S1)

S1 ships ONLY the typed substrate:

- `ReceiptStewardPhase` StrEnum + `ReceiptStewardPhaseSpec` dataclass
- `ReceiptStewardAuditTargets` + `ReceiptStewardAuditReceipt` dataclasses
- `ReceiptStewardRoleSpec` + `receipt_steward_role_spec()` factory
- Role-id wired into `DEFAULT_ROLE_IDS`, `_ROLE_CAPABILITY_CLASSES`,
  `_ROLE_ID_ALIASES`
- Scenario tests pinning the substrate shape + the FPR coverage gap

NOT in this slice (later S2..S4):

- CLI surface (`devctl receipt-steward audit ...`)
- `ReceiptStewardScopeClaim` lifecycle persistence
- `enforce-final-response-gate` composition
- `ReceiptExemptionRequest` lifecycle
