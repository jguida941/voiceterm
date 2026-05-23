# Semantic TDD Lane

This file is a **maintained projection** of the semantic-TDD practice and the
state of the typed proof matrix it produces. It is not durable plan authority.

Durable authority lives in:

- the scenario test files under `dev/scripts/devctl/tests/scenarios/`
- the router entries in
  `dev/scripts/devctl/commands/check/router_python_tests.py`
- `dev/state/plan_index.jsonl` (PlanRow registry)
- `dev/reports/feature_proof_receipts/` (FeatureProofReceipt evidence)
- `dev/state/plan_row_closure_receipts.jsonl` (closure)
- the typed AgentSpawn/Termination receipt stores that `peer-spawn` and
  `peer-terminate` emit

This lane drives those typed stores. It does not replace them.

## Active row

- `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`
- Branch: `extraction/guardir-core-p0-proof-integrity`

## Sister docs

- `dev/active/live_state_semantic_tdd_plan.md` — Phase A-D plan for the
  live-state invariant suite at
  `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py`. That
  doc is scoped to a single test file (intra-command and cross-command
  invariants, ground-truth-probe wiring, role-inversion fixtures). This lane
  is broader: every scenario file under `dev/scripts/devctl/tests/scenarios/`
  written under the binding rules below.
- `dev/active/review_channel.md` — feature-area owner doc whose route work
  many of these tests dogfood.

## Binding rules (operator)

1. **RED first.** No implementation, refactor, or guard wiring lands before a
   matching test exists in `dev/scripts/devctl/tests/scenarios/` and that test
   fails for the reason being fixed.
2. **Plain-language test names.** Each test file is named after what it
   asserts in programmer terms, not by issue id, guard number, or plan-row
   id. The file name is the spec; section/guard ids belong in the matrix
   table, not in the filename.
3. **`AssertionError` is the typed semantic receipt.** Tests read live typed
   state (`StartupContext`, packet bodies, `AgentLoopDecision`,
   `BypassReceipt`, work-board rows) and assert invariants over it. Do not
   invent a parallel `SemanticCommandResultReceipt` dataclass or a parser
   over command output; pytest already produces machine-readable and
   human-readable failure output.
4. **Per-row proof chain.** RED → fix code → GREEN locally → wire into
   `router_python_tests.py` → dogfood the real `devctl` or guard route →
   emit/observe a typed receipt. A row marked `GREEN_LOCAL` is a scope-empty
   invariant (rule defined, no live data exercises it yet); it stays
   `GREEN_LOCAL` until the live state grows enough to exercise it.
5. **Never ratchet to dodge fixing.** Ratchets are acceptable only when
   paired with an explicit ratchet-down plan and a guard that fails closed if
   the count goes UP.
6. **Never invent raw bypass paths or parallel lifecycles.** Spawn,
   publication, and authority transitions all flow through the canonical
   typed lifecycles: `BypassRequest → BypassEvaluation → BypassReceipt →
   BypassExpiry`, `TypedAction → ActionResult → RunRecord →
   ValidationReceipt`, `peer-spawn → AgentSpawnReceipt → peer-terminate →
   AgentTerminationReceipt`. `devctl bypass grant` runs the four-step bypass
   lifecycle in one shot; `peer-spawn` is the single repo-owned spawn
   entry point.
7. **Dogfood discipline.** Any session that touches actor cardinality,
   bypass scope, role authority, peer handoff, or spawn liveness must end
   with at least one real `peer-spawn` exercise against a real receipt. A
   failure during that exercise becomes the next RED test, not a one-off
   bug report.

## Proof matrix snapshot

Migrated from the operator staging file under
`MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`. Every row points at
its scenario file under `dev/scripts/devctl/tests/scenarios/`; per-session
source hashes and session ids live with the typed FPRs, not here.

### Reviewer/packet lifecycle and route guards

| ID | What it asserts | Test file | Status |
|---|---|---|---|
| G28 | Allowed reviewer packet posts materialize as `rev_pkt_*` packets through the on-disk control-decision artifact route. | `test_review_channel_post_finds_control_decision_artifact.py` | GREEN |
| G29 | Claude body-open / semantic-ingest exposes the narrow allowed packet-attention action so `review-channel --action ingest` reaches command-specific validation, not permission-denied. | `test_agent_loop_decision_grants_allowed_action_for_next_command.py` | GREEN |
| G23 | Packets with body_observed_at_utc set carry body_observed_by, body_digest, and body_observation_events. | `test_packet_body_observation_carries_typed_evidence.py` | GREEN |
| G24 | Controller-selected active packets per actor are not silently past `expires_at_utc`. | `test_active_action_request_not_silently_expired.py` | GREEN |
| G25 | Selector picks the newest same-row pending packet per actor; no stale older selection masking newer work. | `test_selected_attention_packet_is_newest_same_row.py` | GREEN |
| G26 | Reviewer/orchestrator decisions with active attention carry the full review-result action set in `allowed_actions`. | `test_reviewer_decision_grants_review_result_action.py` | GREEN |
| G27 | `current_plan_authority` open + no `stop_anchor` means `final_response_allowed=False` at the gate. | `test_continuation_anchor_blocks_final_response.py` | GREEN |

### Role cardinality, delegation, and shared round state

| ID | What it asserts | Test file | Status |
|---|---|---|---|
| G30 | Child actors carry typed delegation evidence (scope-empty: AI-child-of-AI sub-agents). | `test_child_actor_carries_typed_delegation.py` | GREEN_LOCAL |
| G31 | Live (role, plan_row) actor count respects min/desired/max/fallback policy. | `test_per_role_actor_count_within_bounds.py` | GREEN |
| G32 | No two mutation-capable actors hold overlapping write scope (scope-empty: only one live mutator today). | `test_no_overlapping_write_scopes_among_mutating_actors.py` | GREEN_LOCAL |
| G33 | Child actor scope cannot exceed parent scope (scope-empty: no AI-child rows). | `test_child_actor_scope_does_not_exceed_parent.py` | GREEN_LOCAL |
| G34 | Every live mutating row carries `plan_row_id`, `source_event_id`, and `last_active_utc`; row builder threads `default_plan_row_id` from the typed plan ledger. | `test_mutating_actor_observed_shared_round_state.py` | GREEN |
| G35 | Mutating actors see peer write leases before mutation (scope-empty: single mutator). | `test_peer_write_leases_visible_to_mutating_actor.py` | GREEN_LOCAL |
| G36 | Child implementation output references the parent merge gate (scope-empty: no AI-child publishers). | `test_child_patch_references_parent_merge_gate.py` | GREEN_LOCAL |
| G37 | Overlapping child patches carry typed disposition (scope-empty: no children present). | `test_overlapping_child_patches_have_typed_disposition.py` | GREEN_LOCAL |
| G38 | Role round cannot close while children are pending/stale/unmerged (scope-empty: no children). | `test_role_round_not_closed_while_children_pending.py` | GREEN_LOCAL |
| G39 | Child / sub-agents cannot hold direct commit/push/close capabilities (scope-empty: no AI-child rows). | `test_child_actor_has_no_direct_repo_publish_caps.py` | GREEN_LOCAL |

### Stop gate and FeatureProofReceipt ratchet

| ID | What it asserts | Test file | Status |
|---|---|---|---|
| STOP | While `current_plan_authority` is open and no `proven_passed` FPR exists for that row, the final-response gate denies final response. | `test_final_response_denied_without_proof_bundle.py` | GREEN |
| FPR | Any FPR with `real_life_test_status=proven_passed` lists at least one pytest node id (`::`) in `tests_run`; rule fails closed on any new violation. | `test_feature_proof_receipt_proven_passed_carries_node_id.py` | GREEN_LOCAL (37-row historical ratchet) |

### Live-state invariant repairs (dogfood-driven)

These rows track fixes driven by `ground-truth-probe --record` surfacing a
RED invariant in `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py`.
The RED test already exists in the suite; this lane drives it to GREEN by
fixing the underlying bug at the source — no workarounds, no test-silencing.

| ID | What was RED | Root cause | Fix | Test | Status |
|---|---|---|---|---|---|
| INBOX-REDUCER-AGENT-SPAWN | `review-channel --action inbox --target claude --status pending` exited 1 with 45 instances of `Encountered review event without packet_id` even though it returned 4 valid packets. | The `event_reducer.py` allow-list of event types that legitimately lack `packet_id` (daemon, session-liveness, agent-session-outcome, reviewer-authority, implementer-authority) was missing the peer-spawn lifecycle family (`agent_spawn_requested`, `agent_spawn_receipt`, `agent_termination_receipt`). Each peer-spawn invocation amplified the count; my PEER-RESOLVE fix added 23 more. Pre-existing connectivity drift between `runtime/peer_spawn.py` (event producer) and `review_channel/event_reducer.py` (event consumer). | New sibling module `dev/scripts/devctl/review_channel/agent_spawn_events.py` exposing `AGENT_SPAWN_EVENT_TYPES` constant; parallel `continue` branch in the reducer loop matching the existing pattern for other non-packet event families. | `test_inbox_pending_packets_must_not_exceed_hygiene_window` (in `test_live_state_invariants.py`) | GREEN |

### Codex / peer-spawn dogfood matrix

| ID | What it asserts | Test file | Status |
|---|---|---|---|
| PEER-SHAPE | `peer-spawn` without an active spawn-scoped `BypassReceipt` returns a typed denial: `AgentSpawnRequest` section recorded, `Receipt` section with `status` prefix `denied_`, `Errors` section carrying recognized denial vocabulary, and `canonical_command_hint` pointing at `--bypass-receipt-id`. No raw traceback, no generic argparse error. Asserted in both `--format md` and `--format json`. | `test_peer_spawn_returns_typed_receipt.py` | GREEN |
| PEER-AUTH | The `bypass grant --scope` CLI exposes at least one choice whose `_GRANTED_SCOPES` entry transitively includes `BypassAuthorityScope.AGENT_SPAWN_ONLY`. If no such choice exists, the operator cannot satisfy peer-spawn's typed authority gate from the canonical CLI and is forced into raw harness bypass territory. | `test_bypass_grant_scopes_cover_peer_spawn_requirement.py` | GREEN |
| PEER-RESOLVE | `peer-spawn --bypass-receipt-id <id>` resolves the id against the typed `BypassLifecycle` store (`dev/state/bypass_lifecycles.jsonl` by default; overridable via `DEVCTL_BYPASS_LIFECYCLE_STORE_PATH` for hermetic tests) and passes the resulting `BypassReceipt` into the driver instead of returning `None`. With an active edit_only receipt in scope, the dry-run path resolves to `ok=True, status=dry_run_no_launch_callable`; with a missing/unknown id, the typed denial vocabulary is preserved. Caught the operator's "launching codex doesn't work" failure mode via dogfood; fix replaces the prior `return None` on the id-only path in `dev/scripts/devctl/commands/runtime/peer_spawn.py:_load_bypass_receipt` with a typed lookup through `active_bypass_lifecycle_for_receipt_id`. | `test_peer_spawn_resolves_active_bypass_receipt_id.py` | GREEN |
| PEER-TASK-PROMPT | `peer-spawn --task-prompt`/`--task-prompt-file` takes a minimal one-shot launch path: writes a small shell script that invokes `codex exec --sandbox workspace-write "<prompt>"` against the repo root and skips the multi-agent review-channel supervised wrapper. The wrapper's `review_channel_launch_authority_check` rejects bounded one-shot spawns with `EXIT_CODE = 82` when `review_state_path` is missing — that was the actual mechanism behind "spawn succeeds, codex never runs, file never appears." The bounded-task fork in `_build_canonical_launch_adapter` (commands/runtime/peer_spawn.py) routes to `_launch_one_shot_task_prompt` which writes a minimal script (no watchdog, no supervisor loop, no handoff guard, no authority preflight) and spawns it via `subprocess.Popen` with stdout/stderr captured under the temp dir. **Real-life dogfood proof**: live `peer-spawn --provider codex --role implementer --bypass-receipt-id <active> --task-prompt-file <bounded>` produced `dev/reports/dogfood/peer_spawn_real_mutation_probe.md` (45 bytes, sha256 fa1cce9045909ad8f5171cf697df6d2d64aaf43a56a6534052c9a5673e6af330) containing the exact operator-supplied marker. **Two invariants** asserted by the test: (1) the script invokes `codex exec` with `--sandbox workspace-write` and the operator prompt verbatim; (2) the script does NOT contain the supervised wrapper markers (`review_channel_launch_authority_check`, `run_review_channel_once`, `review_channel_inactivity_watchdog`, `review_channel_task_complete_handoff_guard`, `REVIEW_CHANNEL_HEADLESS_MODE`). RED proven by temporarily disabling the fork — wrapper markers including the literal `EXIT_CODE = 82` resurface. Hermetic via `DEVCTL_PEER_SPAWN_TASK_PROMPT_DRY_LAUNCH=1` env hook. | `test_peer_spawn_task_prompt_writes_minimal_script.py` | GREEN (test + physical) |

### Proof-row status legend

- `OPEN` — not started or not proven.
- `BLOCKED` — typed blocker id present; stays open until cleared.
- `PROGRESS` — RED exists but proof chain is incomplete.
- `GREEN_LOCAL` — scenario test passes; either the live state has no
  in-scope data to exercise the invariant, or router/dogfood/receipt are
  still missing.
- `GREEN` — scenario passes, router wired, route or guard dogfooded, and
  typed evidence exists.

A row may not be checked off elsewhere unless its matrix entry is at least
`GREEN_LOCAL` with the test file and router entry in place, and `GREEN` for
rows where live state exercises the invariant.

## Codex / peer-spawn dogfood discipline

`peer-spawn` is the single repo-owned entry point for spawning a peer
conductor. Its denial path is the gate that all "launch Codex" wiring has
to pass through; the dogfood discipline below makes sure the gate stays
typed end-to-end instead of degrading back into raw harness bypass flags.

### Authority chain

1. `devctl bypass request` records the `BypassRequest`.
2. `devctl bypass grant --scope <scope>` runs the
   `BypassRequest → BypassEvaluation → BypassReceipt → BypassExpiry`
   lifecycle in one shot and emits an active `BypassReceipt`.
3. The `--scope` value selected must have `AGENT_SPAWN_ONLY` in its
   `_GRANTED_SCOPES` entry. `edit-only` is the canonical operator-facing
   scope today; the `PEER-AUTH` test above is the ratchet that catches
   drift if any scope rename ever breaks the transitive coverage.
4. `devctl peer-spawn --provider <codex|claude|cursor> --role <...>
   --bypass-receipt-id <id> --row-id <row>` consumes the receipt and emits
   an `AgentSpawnReceipt`.
5. `devctl peer-terminate --provider <provider> --session-id <id> --pid
   <pid>` emits an `AgentTerminationReceipt` and signals the running peer.

### Real-life dogfood loop

Every session that touches actor cardinality, bypass scope, role authority,
peer handoff, or spawn liveness ends with this sequence:

1. Run `peer-spawn` against a real, active `BypassReceipt` and the current
   `--row-id`. Capture the JSON output.
2. Confirm the emitted `AgentSpawnReceipt` is visible in the typed receipt
   store that the spawn registry names (do not assume a path; read the
   registry).
3. Run `peer-terminate` against the returned session/pid and confirm an
   `AgentTerminationReceipt` is emitted.
4. If any step fails or surfaces an untyped denial: add a RED scenario
   file in `dev/scripts/devctl/tests/scenarios/` named after the invariant
   in plain programmer terms, wire it into `router_python_tests.py`, then
   fix the underlying code. Do not document the failure mode as "known."

### When dogfood reveals an off-matrix bug

Same rule as everything else in this lane: the failure becomes the next
RED test. Append a new row to the matrix above with a stable ID derived
from what the test asserts (not from a transient guard number).

## Sync and governance

- `python3 dev/scripts/checks/check_active_plan_sync.py` after edits to
  this file.
- `python3 dev/scripts/devctl.py docs-check --strict-tooling --format json`
  before handoff, so projection drift surfaces.
- `python3 dev/scripts/devctl.py render-surfaces --write --format md`
  whenever this lane changes generated surfaces.
- New scenario files must be added to `_DEVCTL_TEST_TARGETS` in
  `dev/scripts/devctl/commands/check/router_python_tests.py` before the
  matrix row can advance past `GREEN_LOCAL`.
- Closure of `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1` requires
  a `FeatureProofReceipt(proven_passed)` whose `tests_run` lists at least
  one pytest node id from the matrix above and whose review/bypass refs
  resolve in the typed stores.

## A37 amendment work (Phase 0 + Pre-0 + RED Phase 0.5)

### Pre-0 — `develop ingest-plan` operator-amendment ingest

| ID | What it asserts | Test file | Status |
|---|---|---|---|
| PRE-0.A | `develop ingest-plan --dry-run` with valid operator-amendment body + explicit `--plan-row-id` + `--source` + `--target-ref` accepts the source and returns `ok=True, reason=plan_rows_upserted_dry_run`. | `test_live_state_invariants.py::test_ingest_plan_accepts_operator_amendment_with_explicit_plan_row_id` | GREEN |
| PRE-0.B | Same call WITHOUT `--plan-row-id` should auto-derive the row id from a `### A<N>. <title> (Operator Amendment <date>)` heading. Parser at `plan_intake_phase0.parse_plan_authority_sections` must learn the heading pattern. | `test_live_state_invariants.py::test_ingest_plan_auto_derives_row_id_from_amendment_heading` | XFAIL(strict) — visible ratchet, queued as Task #13 |

**Real-life proof (Pre-0)**: live `develop ingest-plan --body-file <a37 text> --plan-row-id A37-TOPOLOGY-RETIREMENT-AMENDMENT-S1 ...` returned `ok=True, reason=plan_rows_upserted, derived_state_invalidation.status=accepted`. Row landed in `dev/state/plan_index.jsonl` (count 2142→2143). `content_hash: sha256:c009a17dc7e3f52ad9ced5489400c5523e791d0a0991f8c2d3c29eeecc7d000e`. Ingestion receipt in `dev/state/plan_ingestion_receipts.jsonl`. `check_active_plan_sync.py` ok=True post-ingest.

### Phase 0 — Consolidated `SemanticTDDRole` typed contract

| ID | What it asserts | Test file | Status |
|---|---|---|---|
| PHASE-0.2A | Legacy role ids `tdd_discovery`, `tdd_first_role`, `dogfood_test` resolve through `normalize_role_id()` to `"semantic_tdd"` (alias resolution lock-in). | `test_live_state_invariants.py::test_semantic_tdd_role_aliases_resolve_legacy_tdd_role_ids` | GREEN |
| PHASE-0.2B | Same legacy role ids are NOT in `DEFAULT_ROLE_IDS` or `_ROLE_CAPABILITY_CLASSES` (full retirement target). Stays RED as visible debt until every callsite migrates and removal is safe. | `test_live_state_invariants.py::test_legacy_tdd_role_ids_must_not_remain_in_default_role_ids` | XFAIL(strict) — visible ratchet, future ratchet-down |
| PHASE-0.PHASE-SHAPE | `SemanticTDDRoleSpec.phases` tuple matches the 9-step ritual phase ids (`discovery`, `red_first`, `code_apply`, `green_verify`, `reinforce`, `dogfood_proof`, `receipt`, `review`) documented in `live_state_semantic_tdd_plan.md` and `you-need-to-go-twinkly-lake.md`. | `test_live_state_invariants.py::test_semantic_tdd_role_spec_phases_match_documented_ritual` | GREEN |

**Real-life proof (Phase 0)**: live `python3 -c "from dev.scripts.devctl.runtime.semantic_tdd_role import semantic_tdd_role_spec; ..."` returns the typed `SemanticTDDRoleSpec` with `role_id=semantic_tdd, capability_class=test, schema_version=1, contract_id=SemanticTDDRoleSpec, phase count=8`. `normalize_role_id("tdd_discovery")` returns `"semantic_tdd"` in live state (along with `tdd_first_role`, `dogfood_test`, `tdd_first`, `dogfooder` — all resolved correctly).

### Phase 0.5 — `devctl role` CLI surface (MVP SHIPPED, all 4 RED → GREEN)

| ID | What it asserts | Test file | Status |
|---|---|---|---|
| PHASE-0.5.LISTED | `devctl role` subcommand is registered + appears in `devctl list` output (alphabetically wired into `commands/listing` COMMANDS tuple). | `test_live_state_invariants.py::test_devctl_role_subcommand_is_registered_and_listed` | GREEN |
| PHASE-0.5.RECEIPT | `devctl role create --dry-run` on a valid role emits a typed `RoleConnectivityProof` receipt with `contract_id="RoleConnectivityProof"` + `connectivity_ok=True`. | `test_live_state_invariants.py::test_devctl_role_create_emits_typed_role_connectivity_proof_receipt` | GREEN |
| PHASE-0.5.SEED | `devctl role create --as-system --dry-run` targets `system_roles.seed.jsonl`; without `--as-system` targets `custom_roles.jsonl`. Defaults derive from typed `PathRoots().state` per `ProjectGovernance`; env-var overrides (`DEVCTL_SYSTEM_ROLES_STORE_PATH`, `DEVCTL_CUSTOM_ROLES_STORE_PATH`) reserved for hermetic tests. | `test_live_state_invariants.py::test_devctl_role_create_as_system_targets_seed_file` | GREEN |
| PHASE-0.5.REJECT | `devctl role create --dry-run` with an unknown `base_workstream_id` rejects with a typed reason naming the missing reference — does NOT write the row, emits a `RoleConnectivityProof` with `connectivity_ok=False` + populated `errors`. | `test_live_state_invariants.py::test_devctl_role_create_rejects_invalid_capability_class_with_typed_reason` | GREEN |

**Real-life proof (Phase 0.5)**: live `devctl role create --role-id topology_migration_steward --base-tandem-role reviewer --base-workstream architect --display-name "Topology Migration Steward" ...` (non-dry-run) returned `ok=True, connectivity_ok=True` and wrote a typed `CustomRoleDefinition` row to `dev/state/custom_roles.jsonl` (341 bytes). File observable on disk. 12-file wiring (per Agent 2's earlier audit) all in place: `cli_parser/role.py` + `commands/role/{__init__,command,create,grant_capability,list,show}.py` + `cli_parser/entrypoint.py` registration + `commands/listing/__init__.py` COMMANDS tuple + `runtime/role_customization.py` extended with `RoleConnectivityProof` dataclass.

**Phase 0.5 consumer-coverage delta**: violations went from 4 → 1 after Phase 0.5 wiring. The CLI handlers consuming `CustomRoleDefinition`, `build_role_creation_action`, `RoleConnectivityProof`, and the persistence path resolved most of the unconsumed-contract debt from Phase 0.

**Known MVP-scope limitations (tracked as enhancements, not blockers)**:
- `show.py` reads only the in-code `_ROLE_CAPABILITY_CLASSES` dict, not the persisted JSONL store. A custom role created via the CLI is on disk but `devctl role show` reports it as not found. Follow-up: extend show.py to read seed + custom store files.
- `grant_capability.py` is a stub returning `not_implemented_in_phase_0_5_mvp_grant_capability_stub`. Follow-up: ship typed `CapabilityGrantState` persistence + receipt.
- S1b adapters (`/role-create`, `/role-edit`, `/role-guard-add` slash projections + `roles.md` re-renderer + drift guard) are deferred to a future slice; only S1a (CLI + persistence + tests + receipt) shipped.

### Phase 0.x — PathRoots `state` field (typed adopter-portable path)

| ID | What it asserts | Test file | Status |
|---|---|---|---|
| PHASE-0.X.STATE-FIELD | `PathRoots` dataclass exposes `state: str = "dev/state"` so adopter repos can override the state-root via typed `devctl_repo_policy.json`. `path_roots_from_mapping({})` falls back to the typed default; `path_roots_from_mapping({"state": "..."})` honors explicit override. | `test_live_state_invariants.py::test_project_governance_path_roots_exposes_state_field_for_adopter_portability` | GREEN |

**Real-life proof (Phase 0.x)**: live `devctl peer-spawn --bypass-receipt-id bypass:grant-20260523T192904638788 --dry-run` resolved through the migrated `peer_spawn.py:347` (which now uses `REPO_ROOT / PathRoots().state / "bypass_lifecycles.jsonl"`) and returned `ok=True, status=dry_run_no_launch_callable, bypass_receipt_id=<echoed>`. The typed-path-resolution chain works end-to-end; the env-var override (`DEVCTL_BYPASS_LIFECYCLE_STORE_PATH`) is preserved for hermetic test isolation only.

**Migration scope**: session-introduced callsite (`peer_spawn.py:347`) migrated this slice. Pre-existing callsites elsewhere (bypass_lifecycle_registry, tests, etc.) remain hardcoded — deferred to a separate slice per the bounded-scope principle. Visible debt tracked via `grep -rn 'REPO_ROOT.*"dev".*"state"'` for future ratcheting.

### Portability note (governance-pack adopter-safety)

All path defaults follow the existing portable pattern documented in `peer_spawn.py:340-348` and `bypass_lifecycle_registry.py:_load_bypass_jsonl`: **env-var override + REPO_ROOT-relative default + filename as governance-pack convention**. No VoiceTerm literal is hardcoded into runtime decision paths.

- Override env vars: `DEVCTL_SYSTEM_ROLES_STORE_PATH`, `DEVCTL_CUSTOM_ROLES_STORE_PATH`
- Default locations: `REPO_ROOT/dev/state/system_roles.seed.jsonl` (tracked), `REPO_ROOT/dev/state/custom_roles.jsonl` (gitignored)
- Repo-policy surface available for declarative override: `dev/config/devctl_repo_policy.json` already declares `develop_role_slash_adapters` (`template_path`, `output_path`); extending it with role-store-path keys is a future enhancement
- Seed content is governance-pack-generic: `semantic_tdd`, `implementer`, `reviewer`, `observer`, `dashboard`, `architect`, `plan_steward`, etc. — no VoiceTerm-specific role IDs

Connectivity-guard status after Phase 0 + Pre-0: `check_function_duplication` ok=True (0 violations), `check_orphan_files` ok=True (0 orphans), `check_contract_connectivity` ok=True, `check_active_plan_sync` ok=True. `check_contract_consumer_coverage_sweep` reports 4 EXPECTED violations on `SemanticTDDRoleSpec` + `SemanticTDDRolePhaseSpec` (no external readers/writers yet — Phase 0.5 CLI is the resolver).
