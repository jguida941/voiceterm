# GuardIR v4.2 Unified Ingestable Plan

## Summary

This is the single canonical ingestible plan for GuardIR lifecycle recovery,
plan ingestion, GuardIR push routing, and CI-to-AI proof feedback. It folds in
the operator-reviewed v2, v3, v3.5, v3.6, v4, and v4.1 discussions so later
sessions do not need chat history to continue.

Canonical path:
`dev/audits/plan_intake/2026-05-20-guardir-lifecycle-recovery-ci-proof-bridge-v4.md`

Plan revision id: `guardir-v4.2-2026-05-20`

## Source History

- Supersedes v2 operator-tightened lifecycle, dogfood, and visibility plan.
- Supersedes v3 compact architecture sketch.
- Supersedes v3.5 automation and universal portability plan.
- Supersedes v3.6 PlanAmendmentReceipt and PlanIntakeConfig substrate plan.
- Supersedes v4/v4.1/v4.2 chat drafts. This file is the durable artifact.

## Required Existing-Row Composition Anchors

- `MP-NEW-P195-ASYNC-CLOUD-PROOF-S1`, `MP-NEW-P196-AHEAD-OF-RUNTIME-PROOF-CACHE-S1`, `MP-NEW-P197-CONTINUOUS-PROOF-SCHEDULER-S2`, `MP-NEW-P198-QUALITY-REPAIR-SCHEDULER-S1`

## Required Packet-Binding Citations

- `PKT-BIND-REV-PKT-4071`

## Rows To Ingest From This Plan

- `MP-GUARDIR-V4-LIFECYCLE-RECOVERY-S1` Ingest and govern the unified v4 lifecycle recovery and CI proof bridge plan. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** summary
- `MP-GUARDIR-V4-PHASE-0-CHANNEL-RECOVERY-S1` Recover review-channel lifecycle authority before feature work. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0
- `MP-GUARDIR-V4-SLICE-A-PUSH-ROUTING-S1` Fix GuardIR push routing and stale origin/develop fallback. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** slice-a
- `MP-GUARDIR-V4-SLICE-B-PROOF-INDEX-MVP-S1` Implement CodeIdentity, ProofReceipt, ProofIndex, and startup proof consumption. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** slice-b
- `MP-GUARDIR-V4-SLICE-C-CI-ARTIFACT-INGEST-S1` Ingest typed CI artifacts into ProofIndex and governance review. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** slice-c
- `MP-GUARDIR-V4-SLICE-D-SAFE-CONTINUATION-S1` Implement SafeContinuationDecision and runtime/CI guard tier split. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** slice-d
- `MP411-T01-GUARDIR-PUSH-ROUTING-S1` Create the missing GuardIR push-routing plan row. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-411 **source_section_id:** slice-a
- `MP377-P2-T02-CI-ARTIFACT-LEDGER-INGEST-S1` Create the missing CI artifact ledger-ingest plan row. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** slice-c

## Parser Contract

The current plan-intake parser reads these headings in
`dev/scripts/devctl/commands/development/plan_intake_phase0.py`:

- heading detection and row regex: lines 30-34
- section routing: lines 197-225
- anchor/citation extraction: lines 237-243

The multi-row ingest source of truth is the `Rows to ingest from this plan`
section. The anchor and packet-binding sections are not universally required by
the parser, but this plan includes them so provenance survives compaction.

Portability requirement: replace hardcoded `MP...` row matching with
repo-policy `plan_row_id_patterns`, defaulting to the current `MP` pattern. An
adopter repo may use its own row-id regex, such as Jira-style project keys.

`source_section_id` defaults to the nearest preceding H2/H3 heading slug. Inline
metadata may override it.

## Phase -1: Automated Self-Ingestion

Goal: make this plan canonical typed state before any Phase 0 or slice work
executes. The plan is the first self-test of the typed ingestion substrate.

Command:

```bash
python3 dev/scripts/devctl.py develop ingest-plan \
  --source dev/audits/plan_intake/2026-05-20-guardir-lifecycle-recovery-ci-proof-bridge-v4.md \
  --target-ref plan:MP-377 \
  --canonicalize \
  --operator-approved \
  --emit-amendment-receipt \
  --verify-startup-visible \
  --execute \
  --format md
```

Semantics:

- `--dry-run` renders canonical diff, row diff, planned receipts, registry
  updates, and startup checks without writing.
- `--execute` is required for writes.
- `--operator-approved` is boolean; when present it populates
  `operator_approval_ref` from actor, session id, and UTC. It must never
  serialize as `"true"`.
- `--canonicalize` forces LF line endings, strips trailing whitespace, and
  ensures one final newline before SHA256.
- `--emit-amendment-receipt` writes `PlanAmendmentReceipt` after row upserts
  succeed.
- `--verify-startup-visible` runs child
  `devctl session --role observer --include-review-status always --format json`
  and fails unless expected row ids are visible in startup quality signals.
- `--verify-only` reruns the startup visibility proof after idempotent writes if
  visibility failed.
- `/ingest <file|packet|body>` is a thin wrapper over this command.

Rollback rule: row writes are idempotent upserts. If visibility fails after
writes, do not emit Phase -1 closure. Fix visibility and rerun with
`--verify-only`.

## Phase -1 Startup Visibility

This is explicit implementation work, not an optional verifier note.

- Extend `dev/scripts/devctl/runtime/startup_signals.py` with
  `_load_plan_intake_summary(repo_root)`.
- Read `dev/audits/plan_intake/INDEX.md` and `dev/state/plan_index.jsonl`.
- Emit `quality_signals["plan_intake"]["current_rows"]`, capped at 50 rows, with
  `row_id`, `plan_revision_id`, `source_doc_sha256`, and `status`.
- Include only `spec`, `amended`, and `promoted` rows.
- `--verify-startup-visible` checks:
  `startup.quality_signals.plan_intake.current_rows[*].row_id`.
- Add focused pytest node
  `test_startup_signals_loads_plan_intake_summary`.

## Plan Intake Registry And Graph

Registry path:
`dev/audits/plan_intake/INDEX.md`

Registry schema:
`path | plan_revision_id | source_doc_sha256 | ingested_at_utc | status`

Statuses:
`spec | amended | superseded | promoted`

Context graph additions:

- node kind: `plan_intake_source_doc`
- node kind: `ingested_plan_row`
- edge kind: `plan_intake_includes`
- edge: source doc -> each ingested row

`context-graph --query "MP-GUARDIR-V4"` must find the ingested rows through
`plan_intake_includes`.

## ProjectGovernance Extension

Add `PlanIntakeConfig` to `ProjectGovernance`, loaded from
`dev/config/devctl_repo_policy.json`.

Fields:

- `plan_intake_root`
- `plan_intake_manifest_path`
- `plan_intake_registry_path`
- `plan_row_id_patterns`

Defaults preserve the current GuardIR layout. Adopter repos override these
fields through repo policy.

## Plan Ingestion Contracts

### PlanAmendmentReceipt

File: `dev/scripts/devctl/runtime/plan_amendment_receipt.py`

Store: `dev/state/plan_amendment_receipts.jsonl`

Fields:

- `receipt_id`
- `old_plan_revision_id`
- `new_plan_revision_id`
- `old_source_doc_sha256`
- `new_source_doc_sha256`
- `per_row_prior_source_doc_sha256`
- `changed_sections`
- `affected_plan_row_ids`
- `superseded_plan_row_ids`
- `new_plan_row_ids`
- `reason`
- `operator_approval_ref`
- `verified_at_utc`
- `contract_id`
- `schema_version`

Idempotency: `receipt_id` is deterministic from `new_plan_revision_id`,
`new_source_doc_sha256`, sorted `changed_sections`, sorted affected rows, and
sorted new rows. Do not include wall-clock time in the id. Re-running identical
ingest is duplicate/no-op.

### IngestFailureReceipt

File: `dev/scripts/devctl/runtime/ingest_failure_receipt.py`

Store: `dev/state/ingest_failure_receipts.jsonl`

Fields:

- `receipt_id`
- `plan_revision_id`
- `source_doc_sha256_attempted`
- `failure_reason`
- `failure_detail`
- `occurred_at_utc`
- `retry_count`
- `recovery_action_required`
- `contract_id`
- `schema_version`

Failure reasons:

- `canonicalize_mismatch`
- `startup_visibility_timeout`
- `parser_rejected`
- `missing_operator_approval`
- `concurrent_ingest_collision`

### PlanPromotionReceipt

File: `dev/scripts/devctl/runtime/plan_promotion_receipt.py`

Store: `dev/state/plan_promotion_receipts.jsonl`

Fields:

- `receipt_id`
- `plan_revision_id`
- `source_doc_sha256`
- `promoted_at_utc`
- `promoted_to_path`
- `prior_status`
- `new_status`
- `criteria_met`
- `operator_approval_ref`
- `contract_id`
- `schema_version`

## Lifecycle And Dogfood Contracts

### SliceClosureReceipt

File: `dev/scripts/devctl/runtime/slice_closure_receipt.py`

Store: `dev/state/slice_closure_receipts.jsonl`

Fields:

- `receipt_id`
- `slice_id`
- `plan_row_ids`
- `closure_proof_refs`
- `dogfood_pre_path`
- `dogfood_post_path`
- `review_packet_id`
- `closed_at_utc`
- `contract_id`
- `schema_version`

### SessionProofReceipt

File: `dev/scripts/devctl/runtime/session_proof_receipt.py`

Store: `dev/reports/session_proof_receipts/<feature_id>.json`

Fields:

- `receipt_id`
- `session_id`
- `feature_id`
- `command_invoked`
- `stdout_digest`
- `stderr_digest`
- `json_parse_status`
- `asserted_fields_present`
- `captured_at_utc`
- `contract_id`
- `schema_version`

### SelfReferentialDogfoodReceipt

File: `dev/scripts/devctl/runtime/self_referential_dogfood_receipt.py`

Store: `dev/reports/self_referential_dogfood/<feature_id>.json`

Fields:

- `receipt_id`
- `source_commit_sha`
- `feature_contract_id`
- `fresh_session_id`
- `field_path_asserted`
- `field_present`
- `captured_at_utc`
- `contract_id`
- `schema_version`

## Slice B Proof Contracts

### CodeIdentity

File: `dev/scripts/devctl/runtime/code_identity.py`

Fields:

- `identity_hash`
- `tree_hash`
- `file_hashes`
- `policy_hash`
- `guard_bundle_hash`
- `repo_pack_id`
- `computed_at_utc`
- `contract_id`
- `schema_version`

### ProofReceipt

File: `dev/scripts/devctl/runtime/proof_receipt.py`

Store and index: `dev/state/proof_index.jsonl`

Fields:

- `receipt_id`
- `code_identity_hash`
- `operation`
- `proof_status`
- `verified_at_utc`
- `expires_at_utc`
- `claimed_sha`
- `verified_local_sha`
- `verified_remote_sha`
- `evidence_refs`
- `contract_id`
- `schema_version`

### StaleProofReceipt

File: `dev/scripts/devctl/runtime/stale_proof_receipt.py`

Store: `dev/state/stale_proof_receipts.jsonl`

Fields:

- `receipt_id`
- `original_proof_receipt_id`
- `reason`
- `detected_at_utc`
- `contract_id`
- `schema_version`

Reasons:

- `code_identity_drift`
- `ttl_expired`
- `artifact_unavailable`

### ProofReceipt And ValidationReceipt Relationship

`ProofReceipt` is the artifact-specific proof row indexed by `CodeIdentity`.
`ValidationReceipt` is the broader existing run-validation concept in the
TypedAction -> ActionResult -> RunRecord -> ValidationReceipt chain. The
`validation_receipt_ledger` surface may summarize both, but the ProofIndex MVP
queries `ProofReceipt`.

## Receipt Examples

### PlanAmendmentReceipt Example

```json
{
  "contract_id": "PlanAmendmentReceipt",
  "schema_version": 1,
  "receipt_id": "plan-amendment-guardir-v4-2026-05-20-8f31c2a9",
  "old_plan_revision_id": "guardir-v3.6-2026-05-20",
  "new_plan_revision_id": "guardir-v4.2-2026-05-20",
  "old_source_doc_sha256": "sha256:old-v3-source",
  "new_source_doc_sha256": "sha256:new-v4-source",
  "per_row_prior_source_doc_sha256": {
    "MP-NEW-P195-ASYNC-CLOUD-PROOF-S1": "sha256:cached-hammock-source",
    "MP-NEW-P196-AHEAD-OF-RUNTIME-PROOF-CACHE-S1": "sha256:cached-hammock-source"
  },
  "changed_sections": ["phase--1", "phase-0", "slice-a", "slice-b", "contracts"],
  "affected_plan_row_ids": ["MP-NEW-P195-ASYNC-CLOUD-PROOF-S1"],
  "superseded_plan_row_ids": [],
  "new_plan_row_ids": ["MP-GUARDIR-V4-LIFECYCLE-RECOVERY-S1"],
  "reason": "Operator-approved unified GuardIR v4 plan ingestion.",
  "operator_approval_ref": "chat-session:2a5b3528-aaa6-4615-b83b-5b1d3598509b@2026-05-20",
  "verified_at_utc": "2026-05-20T00:00:00Z"
}
```

### IngestFailureReceipt Example

```json
{
  "contract_id": "IngestFailureReceipt",
  "schema_version": 1,
  "receipt_id": "ingest-failure-guardir-v4-startup-visibility",
  "plan_revision_id": "guardir-v4.2-2026-05-20",
  "source_doc_sha256_attempted": "sha256:new-v4-source",
  "failure_reason": "startup_visibility_timeout",
  "failure_detail": "devctl session did not expose MP-GUARDIR-V4 rows in quality_signals.plan_intake.current_rows before timeout.",
  "occurred_at_utc": "2026-05-20T00:00:00Z",
  "retry_count": 1,
  "recovery_action_required": "Run ingest-plan --verify-only after startup_signals plan-intake loader is fixed."
}
```

### PlanPromotionReceipt Example

```json
{
  "contract_id": "PlanPromotionReceipt",
  "schema_version": 1,
  "receipt_id": "plan-promotion-guardir-v4-2026-05-20",
  "plan_revision_id": "guardir-v4.2-2026-05-20",
  "source_doc_sha256": "sha256:new-v4-source",
  "promoted_at_utc": "2026-05-20T00:00:00Z",
  "promoted_to_path": "dev/active/guardir_lifecycle_recovery.md",
  "prior_status": "spec",
  "new_status": "promoted",
  "criteria_met": {
    "source_snapshot_verified": true,
    "plan_amendment_receipt_exists": true,
    "startup_visibility_proven": true,
    "no_open_ingest_failures": true,
    "operator_approval_present": true
  },
  "operator_approval_ref": "chat-session:2a5b3528-aaa6-4615-b83b-5b1d3598509b@2026-05-20"
}
```

## Ingest Failure Handling

- Canonical hash mismatch: emit
  `IngestFailureReceipt(reason=canonicalize_mismatch)` and abort.
- Startup visibility timeout: emit
  `IngestFailureReceipt(reason=startup_visibility_timeout)` and abort closure.
- Parser rejection: emit `IngestFailureReceipt(reason=parser_rejected)` with
  row and line diagnostics; do not write partial rows.
- Missing `--operator-approved` on `--execute`: fail before mutation.
- Concurrent ingest collision: deterministic receipt ids and
  `upsert_plan_index_row()` make duplicate runs no-op.

`IngestFailureReceipt` covers ingest-only failures. The broader slice failure
table below covers runtime, CI, packet, bypass, and closure failures.

## Promotion

Plan-intake is not `dev/active` by default.

Add:

```bash
python3 dev/scripts/devctl.py develop promote-plan \
  --plan-revision-id guardir-v4.2-2026-05-20 \
  --operator-approved \
  --format md
```

Promotion criteria:

- source snapshot verified
- PlanAmendmentReceipt exists
- startup visibility proven
- no open IngestFailureReceipt
- operator approval present

Promotion emits `PlanPromotionReceipt` and updates `dev/active/INDEX.md` only if
the plan becomes an active owner doc.

## Phase 0: Channel Recovery

This must land before Slice A-D.

- Fix `ControlDecisionObeyedGuard` / `control_decision_consistency` paralysis.
- Prove fresh lifecycle packets work:
  `task_started -> task_produced -> review_accepted`.
- Add `_validate_review_accepted_target_fields()` in
  `dev/scripts/devctl/review_channel/packet_target_validation.py`.
- Wire it into `validate_target_fields()` before the generic target-field
  rejection path.
- Require `target_kind=runtime`, `target_ref=slice:<id>`,
  `target_revision=<commit_sha>`, and
  `evidence_ref=closure_receipt:<id>`.
- Enforce evidence prefixes: `commit:`, `action:`, `proof_receipt:`,
  `pytest_node:`, `feature_proof_receipt:`, `session_proof:`,
  `dogfood_invocation:`, `closure_receipt:`, `governed_exception:`.

## Packet Binding Matrix

Codex -> Claude:

```text
task_started{
  target_kind: runtime,
  target_ref: slice:<slice_id>,
  target_role: implementer,
  target_session_id: <claude_session_id>,
  attention_urgency: blocking,
  attention_class: execution,
  evidence_ref: governed_exception:<id>
}
```

Claude -> Codex:

```text
task_produced{
  target_kind: runtime,
  target_ref: slice:<slice_id>,
  target_role: reviewer,
  target_session_id: <codex_session_id>,
  evidence_ref: feature_proof_receipt:<id>,
  evidence_ref: session_proof:<id>
}
```

Codex closure:

```text
review_accepted{
  target_kind: runtime,
  target_ref: slice:<slice_id>,
  target_revision: <commit_sha>,
  evidence_ref: closure_receipt:<id>,
  evidence_ref: session_proof:<id>
}
```

## Per-Agent Procedure

Codex per slice:

1. Run fresh pre-slice `devctl session`; save
   `dev/reports/dogfood/<slice_id>/pre.json`.
2. Post `task_started`.
3. Wait for `task_produced` with resolvable evidence refs.
4. Run fresh post-slice `devctl session`; save
   `dev/reports/dogfood/<slice_id>/post.json`.
5. Verify expected JSONPath, CLI output, or grep pattern appears.
6. Post `review_accepted`; emit matching closure receipts.

Claude per slice:

1. Read `task_started`; verify `target_session_id` matches Claude session.
2. Implement only assigned scope.
3. Run each pytest node via `devctl test-python`.
4. Run each new CLI; capture separate SHA256 digests for stdout and stderr.
5. Emit `FeatureProofReceipt`, `SessionProofReceipt`, and
   `SelfReferentialDogfoodReceipt` when startup behavior changes.
6. Post `task_produced`.

## Slice A: GuardIR Push Routing

Deliverables:

- File `GovernedExceptionLifecycle` for stale VoiceTerm/origin fallback.
- Make branch upstream win when `--remote` is omitted.
- Block explicit policy/upstream mismatch instead of falling back to
  `origin/develop`.
- Add regression for the current extraction branch using GuardIR refs.
- Dogfood governed `devctl push --remote guardir --execute`.

Closure:

- `FeatureProofReceipt` with resolvable pytest node.
- `SessionProofReceipt` for push command output.
- `SliceClosureReceipt`.
- `PlanRowClosureReceipt` for Slice A rows.
- GovernedExceptionLifecycle resolution refs.

Operator visibility:

- push report shows GuardIR refs and no `origin/develop` range.
- exception report shows routing exception closed.

## Slice B: ProofIndex MVP

Deliverables:

- `CodeIdentity`
- `ProofReceipt`
- `StaleProofReceipt`
- append-only `dev/state/proof_index.jsonl`
- startup proof consumption
- `devctl proof-index --sha <X> --format md|json`

Closure:

- Feature proof cites proof-index tests and session proof.
- Self-referential dogfood proves fresh startup consumes proof summary.

Operator visibility:

- `devctl proof-index --sha HEAD --format md` renders current proof state.
- fresh startup JSON exposes consumed/current proof summary.

## Slice C: CI Artifact Ingest

Deliverables:

- `.github/workflows/governance_cloud_proof.yml`
- typed `proof_receipt.json`
- typed `cloud_findings.json`
- artifact ingest command
- governance-review and FindingBacklog mirror
- `devctl cloud-findings`
- `devctl validation-receipts`
- `devctl proof-lineage`

Closure:

- workflow_dispatch proof on `greenfield_python`
- artifact download and local ingest
- current/stale finding tests

Operator visibility:

- `devctl cloud-findings --status current --format md`
- `devctl proof-lineage --sha <HEAD> --format mermaid`
- GitHub Actions run URL cited as dogfood invocation evidence.

## Slice D: Safe Continuation And Tier Split

Deliverables:

- `SafeContinuationDecision`
- path-overlap detector
- runtime/CI/both guard tier map
- check-router consumption
- `devctl runtime-tier-map`
- `devctl safe-continuation`

Closure:

- long-CI-pending scenario dogfood returns safe/wait/divert.
- runtime tier map promoted to typed authority.

Operator visibility:

- `devctl runtime-tier-map --format md`
- `devctl safe-continuation --format json`

## Cross-Slice Failure Modes

| Failure | Detection | Recovery |
|---|---|---|
| CI artifact missing | ingest returns `artifact_missing` | emit IngestFailureReceipt/StaleProofReceipt; local fallback |
| CodeIdentity drift | ProofIndex tree/file hash mismatch | emit StaleProofReceipt; suppress startup consumption |
| Stale plan snapshot | source hash mismatch | block slice start |
| Channel blocked mid-handoff | ControlDecisionObeyedGuard violation | post task_blocked and return to Phase 0 |
| Bypass expires | BypassExpiry before closure | pause mutation and request renewal |
| Exception never closes | open lifecycle exceeds policy age | stale exception guard escalates |
| Bridge/memory conflicts typed state | projection-only guard | typed state wins |
| Push before artifact ingest | no current ProofIndex row | block with await-proof-ingestion |
| Closure ref missing proof | closure ref guard fails | reject closure |
| Competing bypass requests | same scope+target active | first approved wins |

## Mandatory Reads

1. `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md:3640`
2. `dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md:864`
3. `dev/scripts/devctl/runtime/plan_source_retention_models.py`
4. `dev/scripts/devctl/runtime/feature_proof_receipt.py`
5. `dev/scripts/devctl/runtime/startup_signals.py`
6. `dev/scripts/devctl/review_channel/packet_target_validation.py`
7. `dev/scripts/devctl/runtime/control_decision_obedience.py`
8. `dev/scripts/devctl/runtime/bypass_lifecycle_models.py`
9. `dev/scripts/devctl/runtime/governed_exception_lifecycle.py`
10. `dev/scripts/devctl/commands/dashboard_builders.py`
11. `dev/config/devctl_repo_policy.json`
12. `.github/workflows/adopter_portability.yml`
13. `dev/test_data/adopter_repo_fixtures/`

## Operator Visibility

Dashboard sections:

- `proof_index_state`
- `cloud_findings_intake`
- `startup_proof_consumption`
- `validation_receipt_summary`
- `repair_authorization_audit`

Surface registry:

- `proof_index_ledger -> dev/reports/proof_index/latest/index.md`
- `cloud_findings_manifest -> dev/reports/cloud_findings/latest/findings.md`
- `validation_receipt_ledger -> dev/reports/validation_receipts/latest/receipts.md`

No slice closes unless its operator CLI/dashboard surface renders the evidence
created by that slice.

## Hard Constraints

1. Phase -1 closes before Phase 0.
2. Phase 0 closes before Slice A-D.
3. No CI artifact without CodeIdentity binding.
4. No raw `--no-verify` without active BypassReceipt.
5. `FeatureProofReceipt.real_life_test_status=proven_passed` requires resolvable
   pytest nodes.
6. Codex and Claude dogfood every slice.
7. Operator CLI/dashboard evidence required before closure.
8. CI authority is typed JSON only.
9. Extend P195-P198; no parallel cloud-proof plan.
10. Closure receipt type must match the closed object.

## Phase -1 Closure

Close `MP-GUARDIR-V4-LIFECYCLE-RECOVERY-S1` only after:

- `PlanSourceSnapshot` exists.
- `PlanIntentIngestionReceipt` exists.
- `PlanAmendmentReceipt` exists.
- plan-intake INDEX includes this v4 plan.
- context graph finds `MP-GUARDIR-V4` through `plan_intake_includes`.
- fresh startup exposes v4 rows in `quality_signals.plan_intake.current_rows`.

Closure cites all evidence refs.
