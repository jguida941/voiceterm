# System Map Steward Lane

This file is a **maintained projection** of the system-map-steward
role's purpose and the audit ritual it performs. It is not durable
plan authority.

Durable authority lives in:

- the typed substrate at `dev/scripts/devctl/runtime/system_map_steward_role.py`
- the role registry in `dev/scripts/devctl/runtime/role_profile.py`
  (`DEFAULT_ROLE_IDS`, `_ROLE_CAPABILITY_CLASSES`, `_ROLE_ID_ALIASES`)
- the scenario tests under `dev/scripts/devctl/tests/scenarios/test_system_map_steward_substrate.py`
- the platform inventory the audit consults:
  `dev/guides/SYSTEM_MAP.md` (Living Connectivity Index),
  `dev/active/ai_governance_platform.md` (Platform Layers),
  `dev/active/INDEX.md` (active-doc registry),
  `dev/state/contract_registry.jsonl` (248 typed contracts),
  `dev/scripts/checks/check_*.py` (158 guards),
  `dev/scripts/coderabbit/probe_*.py` (probe inventory),
  and the `devctl` subcommand list (107 commands at top level)
- the per-slice `PlatformCoverageAudit` artifacts that will land under
  `dev/reports/platform_coverage_audits/` once A38.3 S2 wires audit
  invocation

This lane describes the role; the typed substrate enforces it.

## Active row

- `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`
- Branch: `extraction/guardir-core-p0-proof-integrity`
- Plan-row scope: `A38-SYSTEM-MAP-STEWARD-S1..S3`
  (S1 substrate landed; CLI surface and audit-dimension evaluators in
  S2; SYSTEM_MAP.md write authority + CI integration in S3).

## Purpose

The system-map-steward role audits whether each slice CONNECTED to
the AI governance platform pieces relevant to its scope. The audit
asks: **did the slice connect to the platform components that exist,
or did it leave them dangling?**

This is a PLATFORM-COVERAGE audit role (NOT a TDD-discipline audit
role — see `evidence.md` Case 11 for the category-error correction
story). The 15 audit dimensions are PLATFORM COMPONENTS (the guards,
probes, contracts, plan registry, INDEX.md, SYSTEM_MAP.md,
ai_governance_platform.md layers, devctl CLI inventory, etc.), not
TDD-ritual observables (`red_first`, `green_verify`, `dogfood_proof`,
`receipt`). The two inventories overlap minimally — they are distinct
audit objects.

The role unifies with the previously underdeveloped
`system_alignment_role` already in `DEFAULT_ROLE_IDS`: that legacy id
resolves to `system_map_steward` through `_ROLE_ID_ALIASES`, so the
typed audit surface specializes the unused role rather than
introducing a parallel one.

The role is **audit-only / GOVERNANCE**: it READS evidence and EMITS
a typed `PlatformCoverageAudit`; it never mutates plan or repo state
directly. The SYSTEM_MAP.md write authority that closes the
maintenance-rule loop is a separate edit-only `SystemMapStewardScopeClaim`
delivered in S3.

## Audit ritual (6 phases)

1. `LOAD_PLATFORM_INVENTORY` — load the platform inventory the audit
   will consult: SYSTEM_MAP.md, ai_governance_platform.md, INDEX.md,
   `dev/state/contract_registry.jsonl`, the guard + probe scripts,
   and the `devctl` subcommand inventory.
2. `DETERMINE_SLICE_RELEVANCE` — read the slice's plan row, commit
   diff, and any associated packets to assign relevance per
   dimension using `PlatformComponentRelevance` (high/medium/low/
   irrelevant). File paths touched, capability class, and plan-row
   scope drive the assignment.
3. `AUDIT_CONNECTIONS` — for each platform-component dimension marked
   at least `medium` relevance, audit whether the slice connected to
   the component. Produce a `PlatformComponentTouch` per dimension
   carrying observed_touch (connected/missed/n/a/exempted), evidence
   path or ref id, and a short explanation. The
   `feature_proof_receipt_chain` dimension delegates to
   `receipt_steward`.
4. `SYNTHESIZE_GAPS` — collect missed pieces, detect new
   disconnections (platform pieces the slice surfaced that
   SYSTEM_MAP.md does not yet name), compute the coverage grade
   Literal (complete / partial / incomplete).
5. `PROPOSE_SYSTEM_MAP_UPDATE` — when a new disconnection is
   surfaced, emit a typed `SystemMapRowProposal`. The proposal lands
   directly into SYSTEM_MAP.md when an `edit_only`
   `SystemMapStewardScopeClaim` is in scope; otherwise it stays
   `pending` for operator review.
6. `EMIT_COVERAGE_AUDIT_RECEIPT` — assemble the typed
   `PlatformCoverageAudit` and persist via the governed JSON-mapping
   writer used by other lifecycle stores. The receipt is the single
   observable artifact this role produces per audit.

## The 15 platform-component audit dimensions

These are the typed PLATFORM components the audit walks per slice
(NOT TDD-discipline observables). Listed in canonical order from
`PLATFORM_COMPONENT_IDS`:

1. `project_governance_authority_chain_consulted` — relevant
   `ProjectGovernance` pieces consulted before mutation
2. `repo_pack_contract_respected` — slice respects pack policy
3. `plan_registry_tied` — slice tied to typed `PlanRow`
4. `collaboration_session_actor_authority_typed` — actor held typed
   grant
5. `typed_action_result_chain_emitted` —
   `TypedAction -> ActionResult -> RunRecord -> ValidationReceipt`
6. `bypass_lifecycle_composed` — when `--no-verify` used,
   `BypassReceipt` covered
7. `feature_proof_receipt_chain` — delegates to `receipt_steward`
8. `relevant_guards_ran` — guards matching file paths touched ran in
   BEFORE/AFTER sweep
9. `relevant_probes_ran` — probes matching scope category ran
10. `findings_priority_impact_observable` — slice resolving a finding
    has rank delta
11. `index_md_active_doc_registry_covered` — slice touching
    `dev/active/*.md` has INDEX row
12. `system_map_maintenance_rule_followed` — slice surfacing new
    disconnection has SYSTEM_MAP row
13. `ai_governance_platform_layer_named` — slice touches platform
    layer (Core/Runtime/Frontends/Adapters/RepoPacks) must name it
14. `contract_registry_updated` — slice adding typed contract is
    registered
15. `devctl_cli_inventory_current` — slice adding subcommand is in
    `devctl list`

## Audit output shape

The role emits a single typed `PlatformCoverageAudit` per audit
invocation, carrying:

- `audit_id`, `slice_id`, `plan_row_id`, `commit_sha`,
  `audited_at_utc`
- `components` — ordered tuple of `PlatformComponentTouch` entries
  matching `PLATFORM_COMPONENT_IDS`
- `missed_pieces` — synthesized tuple of dimension ids marked missed
- `new_disconnections_surfaced` — tuple of platform pieces the slice
  exposed that SYSTEM_MAP.md does not yet name
- `system_map_update_proposed` + `system_map_proposal_id` — the
  maintenance-rule mechanization output
- `coverage_grade` — `complete` / `partial` / `incomplete`
- `actor_role` — `system_map_steward`
- `schema_version`, `contract_id` — standard typed-state fields

## Composes-with

The role composes (loose coupling via typed audit contract) with:

- `receipt_steward` — owns the `feature_proof_receipt_chain`
  dimension; the audit records the delegation while the verification
  logic lives in the receipt-steward substrate.
- `semantic_tdd` — one of the disciplines whose coverage the audit
  walks. The audit checks platform-coverage, not TDD-step
  compliance.
- `plan_steward` — owns the PlanRow anchor the audit attaches to;
  audit invocation reads `dev/state/plan_index.jsonl`.
- `system_alignment_role` — legacy id this role specializes; the
  alias `system_alignment_role -> system_map_steward` lives in
  `_ROLE_ID_ALIASES`.

## Substrate scope (this slice, A38.3 S1)

S1 ships ONLY the typed substrate:

- `SystemMapStewardPhase` StrEnum + `SystemMapStewardPhaseSpec`
  dataclass
- `PlatformComponentRelevance` + `PlatformComponentTouchStatus`
  StrEnums
- `PlatformComponentTouch` + `PlatformCoverageAudit` dataclasses
- `SystemMapRowProposal` dataclass (maintenance-rule mechanization
  shape)
- `SystemMapStewardScopeClaim` dataclass (read-only / edit-only
  scope mode)
- `SystemMapStewardRoleSpec` + `system_map_steward_role_spec()`
  factory
- `PLATFORM_COMPONENT_IDS` canonical 15-entry tuple
- Role-id wired into `DEFAULT_ROLE_IDS`, `_ROLE_CAPABILITY_CLASSES`,
  `_ROLE_ID_ALIASES`
- Scenario tests pinning the substrate shape + xfail-strict ratchets
  for per-slice audit pairing, disconnection-to-proposal pairing,
  and runtime hot-zone coverage

NOT in this slice (later S2..S3):

- CLI surface (`devctl system-map-steward audit ...`,
  `propose-row ...`, `coverage-report ...`, `connectivity-trend ...`)
- Audit-dimension evaluator implementations (one per the 15 typed
  dimensions)
- SYSTEM_MAP.md write authority logic
- `SystemMapStewardScopeClaim` lifecycle persistence
- CI integration via `check_system_map_coverage_within_window.py`
- `enforce-final-response-gate` composition
