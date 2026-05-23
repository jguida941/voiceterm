# Live-State Semantic TDD — Plan (v2, corrected per ChatGPT Pro review)

## Context

The operator caught a typed-controller bug: `devctl review-channel --action sync-status` reports `attention_required: False` while ALSO listing `awaiting_reviewer_ack` lane barriers. The same output contradicts itself. AI agents (claude, codex) ran the command, didn't read the contradiction, and moved on. This pattern is repo-wide — agents claim GREEN against output that says RED if anyone reads it.

The operator proposed: **write TDD tests that assert what the output SHOULD say given live system state.** A pytest test that fails with `AssertionError: barrier exists but attention_required=False` IS the structured semantic receipt — pytest already produces machine-readable + human-readable failure output. The bug is caught by reading the invariant, not by parsing prose or dumping raw output.

**Architect verdict**: ChatGPT Pro's first proposal (new `SemanticCommandResultReceipt` dataclass + new gate module) is overengineering. Pytest's `AssertionError` IS already a semantic receipt; pytest's JSON report mode IS machine-readable; the existing `GroundTruthProbeRunReceipt` + `final_response_gate.py` can consume the pytest exit code + report. We do NOT need a new typed dataclass or a new gate module. We MIGHT need a thin adapter inside the existing ground-truth-probe command so pytest exit code maps to `verdict != "satisfied"` — that's wiring, not overengineering.

The plan also has two cleanup phases: revert the rejected-path code from earlier in this session, and revert the over-eager plan amendments.

## ChatGPT Pro corrections incorporated

| Pro's correction | Action |
|---|---|
| Phase C may need a thin adapter so pytest exit code → `GroundTruthProbeRunReceipt.verdict != "satisfied"`. The existing `build_ground_truth_probe_receipt()` doesn't inspect pytest results today. | Adopted. Phase C now explicitly carves a small adapter task; not a new lifecycle. |
| `test_typed_controller_consistency.py` may exist only in local worktree, not pushed branch. Don't base plan on it without verifying. | Adopted. Phase A starts with `git status --short` + `git ls-files | grep test_typed_controller_consistency` to confirm. |
| Don't wire expected-red live tests into check-router. Permanent-red routes become noise. | Adopted. Phase B is local-only until invariants are green; check-router wiring is deferred to Phase D. |
| Start with intra-command invariants (one reducer per test), not cross-command. | Adopted. Phase B1 starts with sync-status's OWN attention_required vs its OWN awaiting_reviewer_ack. Cross-command (sync-status vs develop --launch) becomes Phase B5. |
| Field names must match actual code: `collaboration_topology` (not `coordination_topology`), `active_participant_count` (not `active_actor_count`). | Adopted. Phase B1 reads actual emitted fields after exploring `CoordinationTopologySnapshot`. |
| `orphan_files_large_new_set_must_violate` is a policy threshold, not a semantic contradiction. Better framing: "if `status=ok` then no blocking threshold can be exceeded." | Adopted. Orphan invariant moved to Phase B-second-batch with the corrected framing. |
| Role inversion fixtures isolated under `tests/scenarios/fixtures/role_inversion/`, copied to `tmp_path` per test. Don't mutate live `dev/state/`. | Adopted. Phase D uses fixture-based isolation. |

## Plan

### Phase A — Revert rejected-path code (cleanup before building)

Working-tree-only, no commits. Operator confirmed: ChatGPT Pro didn't have local access; these files are confirmed in the worktree. **Delete directly, no verify-first dance.** Final `git status` after deletion is the verification.

**Delete (rejected paths)**:
- `dev/scripts/checks/check_output_comprehension_hook_coverage.py` (parser-based G59; rejected path)
- `dev/scripts/devctl/tests/checks/test_check_output_comprehension_hook_coverage.py` (its tests)
- `dev/scripts/devctl/commands/absorb_output.py` (injection-shape wrapper; rejected path)
- `dev/scripts/devctl/tests/commands/test_absorb_output.py` (its tests)
- `dev/guides/ABSORB_OUTPUT_TOOLBOX.md` (its doc)
- The 2 router entries + 1 script-catalog entry + 1 quality-policy entry for the above (revert via `git diff` of `router_python_tests.py`, `script_catalog_entries.py`, `quality_policy/defaults.py`)
- The new `dev/reports/command_output_receipts/` directory if created (created by G59 only)

Verification commands BEFORE deletion (read-only):

```
git status --short
git diff --name-only
git diff -- dev/scripts/devctl/commands/check/router_python_tests.py
git diff -- dev/scripts/devctl/governance/script_catalog_entries.py
git diff -- dev/scripts/devctl/quality_policy/defaults.py
git ls-files | grep test_typed_controller_consistency
git ls-files | grep check_output_comprehension_hook_coverage
git ls-files | grep absorb_output
```

**Revert plan amendments A24, A27, A28, A29, A36** in `delete_after_ingest.md` (operator agreed; A26 stays). Single edit that removes those amendment blocks while preserving A25, A26, A30, A31, A32, A33, A34, A35.

**KEEP (operator agreed)**:
- `dev/scripts/devctl/runtime/control_decision_obedience.py` Invariant C extensions (`MissingDecisionRefreshHint`) — fixes a real route bug
- `dev/scripts/devctl/commands/development/packet_attention.py` typed-controller contradiction fix — fixes a real bug
- `dev/scripts/devctl/tests/runtime/test_typed_controller_consistency.py` IF it's tracked or stage-able. If it's only in dirty worktree, stage it as part of Phase B (it's the natural precursor to the new live-state invariant suite).
- All connectivity wins from earlier session (18 contracts registered, 17 guards wired into bundle/quality, 4 topology hardcoding sites typed, 62→0 function-duplicate consolidation)

### Phase B — Live-state TDD, intra-command first, two invariants, manual runs only

**No check-router wiring yet.** Build the tests, run them by hand, observe whether they catch the real contradiction. Tests live at `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py`.

**Field-name verification step (B0)**: read `dev/scripts/devctl/runtime/coordination_topology.py` (and wherever `CoordinationTopologySnapshot` is defined) to confirm exact field names emitted by `sync-status`. ChatGPT Pro flagged that the snapshot uses `collaboration_topology` (not `coordination_topology`) and `active_participant_count` / `active_conductor_count` (not `active_actor_count`). Tests must use the actual emitted field names.

**Two starter invariants (intra-command, single-reducer)**:

| # | Invariant ID | What it asserts |
|---|---|---|
| 1 | `sync_status_awaiting_reviewer_ack_requires_attention` | If `review-channel --action sync-status` JSON output contains a lane barrier with kind=`awaiting_reviewer_ack`, then THE SAME OUTPUT must expose `attention_required=True` OR `attention_status` must indicate review/checkpoint/repair required. No cross-command coupling. |
| 2 | `sync_status_collaboration_topology_implies_participant_evidence` | If `sync-status` reports `collaboration_topology == "multi_agent_active"`, then THE SAME OUTPUT must report `active_participant_count >= 2` OR explicitly state `fanout_safety=blocked` / `recommended_topology=single_agent`. |

**Sequencing (strict)**:
- **B1**: Write the 2 tests against actual emitted fields. Use `subprocess.run` + `json.loads` against `--format json`.
- **B2**: Run pytest manually:
  ```
  python3 -m pytest dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py -v
  ```
  Observe whether failures occur. Failure message must include conflicting field values so a reader understands the bug in one line.
- **B3**: If tests fail, the contradiction is real — DON'T silence the test, fix the contradiction in the reducer (likely `dev/scripts/devctl/commands/development/packet_attention.py` for #1 + topology reducer for #2). The fix from earlier this session already addresses #1; verify it still holds after Phase A reverts.
- **B4**: Rerun until both invariants are green. Only when green does Phase C unlock.

### Phase C — Wire pytest exit code into existing ground-truth-probe receipt

Only after Phase B is green. **No new gate; thin adapter only.**

**Adapter target**: the existing `devctl ground-truth-probe --record` command (find its module). Today `build_ground_truth_probe_receipt()` sets `verdict="satisfied"` based on trigger paths + required probe presence — it does NOT inspect pytest results. The adapter must:

1. Optionally run a configured pytest target (the new `test_live_state_invariants.py`)
2. Capture pytest exit code + JSON report path
3. If pytest exit != 0, set `verdict="unsatisfied"` (or new typed equivalent) with the pytest report sha + failure summary captured into the receipt's existing `probe_report_path` / `probe_report_sha256` / `failure_count` fields
4. If pytest exit == 0, retain the existing `verdict="satisfied"` path

This is additive: an extra "pytest-target" mode of the existing command. No new typed dataclass. No new gate module. The existing `final_response_gate.py` already blocks `final_response_allowed=False` when the receipt is unsatisfied/missing/stale/mismatched.

**Verification commands**:
```
python3 dev/scripts/devctl.py ground-truth-probe --record --format md
python3 dev/scripts/devctl.py develop next --actor agent --enforce-final-response-gate --format json
```

If invariants are red, ground-truth-probe records unsatisfied; develop next + final-response-gate blocks; required-command points back to ground-truth-probe. Loop until green.

### Phase D — Add to check-router + bundle + metamorphic role inversion

Only after Phase B+C are green.

**D1 — Wire into check-router**: add `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py` to `_DEVCTL_TEST_TARGETS` in `router_python_tests.py`. Now CI / quality runs include it.

**D2 — Second batch of invariants** (in same test file or sibling):
- `orphan_files_status_ok_implies_no_threshold_breach` — corrected framing per Pro: if `check_orphan_files --format json` reports `status="ok"`, no policy-encoded blocking threshold is exceeded. Doesn't invent a new threshold; reads it from existing policy.
- `proof_bundle_blocked_implies_no_closure_receipt` — if `check_current_row_proof_bundle` returns `status=blocked`, the row must NOT have a PlanRowClosureReceipt in `dev/state/plan_row_closure_receipts.jsonl`.
- (Add cross-command invariant 3, originally Phase B invariant 1's cross-command form): `sync_status_barriers_match_develop_dry_run_attention` — sync-status's lane barriers and `develop --launch --dry-run` `attention_required` must agree.

**D3 — Metamorphic role inversion**: new file `dev/scripts/devctl/tests/scenarios/test_role_inversion_invariants.py`. Fixtures live under `dev/scripts/devctl/tests/scenarios/fixtures/role_inversion/` (gitignored runtime mutations not allowed). Per test:
- Copy fixture file into `tmp_path`
- Override the role-resolution module's state-store path via env var or fixture monkeypatch
- Fixture A: `codex.role=reviewer, claude.role=implementer` → assert codex mutation claims fail, claude self-review claims fail
- Fixture B: `codex.role=implementer, claude.role=reviewer` → assert codex mutation claims may be allowed, claude review claims may be allowed
- A failing test means a hard-coded provider→role assumption is still present (per A30/A31/topology hardcoding work)

## Critical files to read/modify

**Existing (read-only in Phase B0, modified later)**:
- `dev/scripts/devctl/runtime/coordination_topology.py` — confirm `CoordinationTopologySnapshot` field names before B1
- `dev/scripts/devctl/commands/development/final_response_gate.py` — verify it composes the ground-truth receipt (no edits expected)
- `dev/scripts/checks/review_probes/probe_command_result_contract.py` — envelope/transport probe, keep as-is
- `dev/scripts/devctl/runtime/command_output_receipt.py` (lines 21-45) — reference for existing typed-receipt shape; we DON'T add a new one
- `delete_after_ingest.md` — revert A24/A27/A28/A29/A36

**To-find in Phase C** (Pro's correction):
- The module that owns `devctl ground-truth-probe --record` — Pro flagged it likely needs the pytest-target adapter
- `GroundTruthProbeRunReceipt` definition + `build_ground_truth_probe_receipt()` reducer

**New (Phase B)**:
- `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py` (one new test file, 2 invariants for Phase B)

**New (Phase D)**:
- `dev/scripts/devctl/tests/scenarios/test_role_inversion_invariants.py`
- `dev/scripts/devctl/tests/scenarios/fixtures/role_inversion/fixture_a_codex_reviewer.jsonl`
- `dev/scripts/devctl/tests/scenarios/fixtures/role_inversion/fixture_b_codex_implementer.jsonl`

## What we do NOT build

- No `SemanticCommandResultReceipt` dataclass
- No `semantic_command_receipt.py` module
- No `semantic_command_receipt_gate.py` module
- No new `probe_live_output_invariants.py` review-probe wrapper
- No modifications to `.claude/settings.json` (hooks remain as-is)
- No parallel control plane

## Verification (end-to-end)

1. **Phase A complete**: `git status` shows deleted rejected-path files gone; `delete_after_ingest.md` no longer contains A24/A27/A28/A29/A36 blocks but still contains A25/A26/A30/A31/A32/A33/A34/A35.
2. **Phase B complete**: `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py -v` — 2/2 green. Failure-mode dogfood: temporarily mutate a state file so the contradiction reappears, confirm pytest fails with a clear AssertionError naming the conflicting fields, then revert the mutation.
3. **Phase C complete**:
   - `python3 dev/scripts/devctl.py ground-truth-probe --record --format md` writes a receipt with `verdict="satisfied"` when pytest is green
   - When pytest is red (re-introduce the contradiction), the same command writes `verdict="unsatisfied"` with `failure_count > 0` and `probe_report_sha256` set
   - `python3 dev/scripts/devctl.py develop next --actor agent --enforce-final-response-gate --format json` returns `final_response_allowed=false` when receipt is unsatisfied; `true` when satisfied
4. **Phase D complete**:
   - `_DEVCTL_TEST_TARGETS` includes the new test path
   - `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_role_inversion_invariants.py -v` — both fixtures pass with their respective expected outcomes
   - Mutating the role-resolution code to hardcode `codex == reviewer` should make Fixture B (codex=implementer) fail; reverting fixes it

## Follow-up audit items surfaced during execution

1. **`coordination_state.coordination_topology` naming smell** (operator-flagged 2026-05-23): the sync-status output has a SECTION called `coordination_state` whose value is a dict, and INSIDE that dict is a FIELD ALSO called `coordination_topology`. The reducer in `dev/scripts/devctl/platform/coordination_topology.py:109` returns a `CoordinationTopologySnapshot` whose top-level field is `collaboration_topology` (not `coordination_topology`). After investigation: `coordination_state` is NOT the snapshot — it's a separate `CoordinationStateProjection` (4-field typed projection per `rev_pkt_2273/2278/2281/2298`) at `dev/scripts/devctl/review_channel/coordination_state_projection.py`. The naming collision (section + inner field) is its own smell on top of the shape divergence.

2. **`coordination_topology` enum uses agent-counting labels — TOPOLOGY ARCHITECTURAL BUG** (operator-flagged 2026-05-23, but already documented in plan): the `CoordinationTopology = Literal["multi_agent_active", "single_agent_active", "no_active_agents", "unknown"]` enum at `dev/scripts/devctl/review_channel/coordination_state_projection.py:24-29` counts AGENTS instead of expressing ROLE-BASED topology. Per `delete_after_ingest.md:1366-1370`: *"CollaborationModeTopology still projecting `selected_mode_id=solo` and `selected_role_preset_id=dashboard` while runtime state reports `multi_agent_active` is migration debt."* Per the AntiDumbass amendment (lines 731-870): role_id is primary lane identity; provider/agent count is NOT topology. The architectural fix is to replace agent-count topology with role-based topology (e.g. `roles_present=[reviewer, implementer]`, `mutation_owner_role=implementer`, `multiple_writers=False`). The current enum is migration debt and should be flagged as such anywhere it's emitted.

3. **`active_participant_count=0` while claude is live**: the reducer at `coordination_topology_support.py:74` (participant_records) loops over 3 sources and ALL three returned zero live entries even though claude IS running this session. This is a SEPARATE bug from the topology naming/enum smell. Three places that determine `live=True`: collaboration.participants[].live, role_occupancies[].live, active_provider_roles items. All of those evidently came back empty. Trace: why does live runtime evidence (we ARE here) not propagate to these typed sources? Likely the bridge runtime / runtime_provider_roles reducer isn't observing the live session.

4. **General code-smell pattern**: the typed reducer emits one shape, the projection emits a renamed shape, and tests/agents read the projection. Multiple reducers reading the same data reach different conclusions about who's live. This is the same class of bug as the typed-controller `attention_required: False`-while-`awaiting_reviewer_ack`-present contradiction. Worth a dedicated audit pass after Phase B is green.

## Invariant correction (B3-mid-execution)

Original invariant 2 (`coordination_topology=multi_agent_active implies active_participant_count >= 2`) was wrong-framed because:
- It validated the broken enum's value-side rather than flagging the enum-shape problem
- The plan already documents agent-counting topology labels as migration debt (line 1366-1370)
- Operator: "There should be no single agent. There should be no dual agent. That's the fucking problem."

Replacement invariant 2 (`coordination_topology_must_not_use_deprecated_agent_count_labels`): asserts that the `coordination_state.coordination_topology` field, when emitted, MUST either (a) NOT use the deprecated agent-counting labels (`multi_agent_active`, `single_agent_active`, `no_active_agents`) without a typed migration-debt note in `coordination_state.notes`, OR (b) come from a future role-based topology projection. This catches the architectural smell, not the value mismatch.

## Typed-state confirmation of the topology architectural bug (2026-05-23)

Operator directive: *"It's not just in that MD. It's also in our type state. We've mentioned it multiple times as topology issue."*

Confirmed by grepping `dev/state/`. The typed inventory `dev/state/topology_hardcode_inventory.jsonl` (contract: `TopologyHardcodeInventory`) catalogs **155 entries** of this exact debt:

| count | value | finding_kind |
|---|---|---|
| 44 | `single_agent` | count_coupled_topology |
| 10 | `dual_agent` | count_coupled_topology |
| 10 | `active_dual_agent` | count_coupled_topology |
| 4 | uppercase variants (`SINGLE_AGENT`, `DUAL_AGENT`, `ACTIVE_DUAL_AGENT`) | count_coupled_topology |
| 47 | `codex` | provider_literal |
| 28 | `claude` | provider_literal |
| 3 | `cursor` | provider_literal |

All 155 entries marked `status: "existing_inventory_only"`, `phase: "0.6.C"`, `remediation_phase: 6`. Typed state already knows this is debt; remediation has been scheduled but not executed.

The inventory also captures a docstring fragment from `runtime/topology_facts.py`:

> *"The legacy labels remain visible in projection/migration output for operator continuity, but they MUST NOT grant or block runtime authority on their own. Authority decisions read typed `CollaborationSessionState.role_assignments`."*

So invariant 2's direction is doubly confirmed:
- The MD plan (`delete_after_ingest.md` lines 1345-1370, 1713) says role-based, not agent-counting
- The typed state (`topology_hardcode_inventory.jsonl`) inventories 155 violations and says remediation is phase 6
- The typed reducer (`runtime/topology_facts.py`) docstring says legacy labels MUST NOT grant authority

Invariant 2 turns the typed inventory's STATIC finding into a LIVE-STATE check: every time `sync-status` emits, the test asserts the projection isn't laundering inventoried debt as a current topology answer without flagging it.

## Optional Phase B-extra: typed-inventory regression guard

If Phase B3 fixes reduce the inventory below 155 entries, add a third invariant:

```
test_topology_hardcode_inventory_must_not_grow
```

Reads the row count of `dev/state/topology_hardcode_inventory.jsonl` against a recorded ceiling. Fails closed if the count grows. This is a ratchet, not a contradiction check — it lives in the same test file but is conceptually a regression guard. Defer to Phase D2 unless Phase B3 touches inventoried sites.

## Operator-confirmed path A (2026-05-23) — invariant 2 stays RED as a ratchet

After execution surfaced invariant 2 as RED, operator chose path A:
- Do NOT patch the projection to silence the test
- Do NOT pull the full enum-replacement remediation forward into Phase B (that is phase 6 work per `topology_hardcode_inventory.jsonl`)
- Accept invariant 2 stays RED — it is a permanent visible ratchet against the deprecated agent-counting topology enum

## Phase B revised — TWO-test split per ChatGPT Pro architecture review

ChatGPT Pro proposed a two-test split that combines near-term protection with migration press. Both tests live in `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py` (rename current invariant 2 accordingly).

### Test 2a — `sync_status_agent_count_topology_must_be_quarantined`
Near-term safety invariant. PASSES today, protects against escalation:
- If `coordination_state.coordination_topology` is any of the deprecated agent-counting labels (`single_agent`, `dual_agent`, `single_agent_active`, `multi_agent_active`, `no_active_agents`)
- Then the deprecated label MUST NOT drive `authority_mode`, `recovery_eligibility`, or final-response-gate permission
- Concretely: assert the projection treats the label as compatibility-only (e.g. `legacy_*` field placement, or a typed `migration_debt` flag)
- This catches REGRESSION where a future consumer starts branching on the deprecated label as canonical authority

### Test 2b — `sync_status_does_not_promote_agent_count_topology_as_authority`
Target-architecture invariant. STAYS RED until phase 6 remediation removes the enum:
- `coordination_state.coordination_topology` MUST NOT be any of `{single_agent, dual_agent, single_agent_active, multi_agent_active, no_active_agents}`
- Allowed shapes: role/authority/session-based topology (e.g. `typed_role_topology[reviewer:claude;implementer:codex]` from `runtime/role_topology.py:97-105`), or fail-closed `unknown`
- `active_actor_count` allowed under `observed_runtime` as evidence only; not as topology authority
- Legacy fields may carry old vocabulary but MUST be clearly marked as compatibility (e.g. field name prefix `legacy_`)

Target-state surface shape (from Pro's design, captured here for the migration target):

```json
{
  "coordination_state": {
    "coordination_model": "role_authority_session_graph",
    "authority_mode": "review_gated",
    "runtime_posture": "active",
    "recovery_eligibility": "remote_only",
    "observed_runtime": {
      "active_actor_count": 2,
      "active_runtime_providers": ["claude", "codex"]
    },
    "role_assignments": [
      {"provider": "claude", "role": "implementer"},
      {"provider": "codex", "role": "reviewer"}
    ],
    "legacy_topology_label": "multi_agent_active"
  }
}
```

The count still exists. It just CANNOT be the topology authority.

## Phase E (NEW) — TDD role integration: thin entry point, not chat-mediated

**Operator directive 2026-05-23**: *"shouldn't all this be a role? Like, shouldn't the TDD role run this script, run all this stuff? I mean, that would be a way better system."*

Today the live-state semantic TDD invariants depend on external review (ChatGPT Pro → operator → me → write tests). That is not durable. The repo already has a typed `tdd_first_role` (referenced in `delete_after_ingest.md:1346, 1352-1356`) which today is a TEST role with no mutation or ACK authority. The architectural move is to make the TDD role OWN live-state semantic invariant execution as a typed responsibility.

### E1 — Inventory existing TDD role surface
- Read whatever typed contract defines `tdd_first_role` today (likely `dev/scripts/devctl/runtime/role_profile.py` or sibling)
- Identify the role's current responsibilities, current invocation entry point, and current proof surface
- Do NOT modify it yet — just map what's there

### E2 — Add typed responsibility: live-state invariant execution
- Add a typed responsibility to the TDD role: "run the registered live-state semantic TDD suite and produce a `GroundTruthProbeRunReceipt`"
- Suite registration: a typed list of test paths the TDD role knows to run (start with `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py`)
- The TDD role's invocation IS the bridge between pytest and the receipt — Phase C's adapter becomes the TDD role's responsibility, not a flag on `ground-truth-probe`
- This means new invariants can be added by registering them with the TDD role, without rewiring any command

### E3 — Thin entry point command
- Single typed entry point: `python3 dev/scripts/devctl.py tdd-role --action run-live-state-invariants` (or compose into the existing role activation surface — whichever is canonical)
- Produces a typed receipt with: pytest exit code, failure list, conflicting-field summary per failed invariant
- The final-response-gate already consumes `GroundTruthProbeRunReceipt`; no new gate needed
- Operator does not need to copy-paste from chat; the role runs the suite and produces typed evidence

### E4 — Composition with existing role lanes
- `tdd_first_role` stays a test role: it produces evidence, does NOT grant ACK or mutation authority
- Reviewer/implementer roles READ the TDD role's receipts as authority evidence when making their own decisions
- This is consistent with the AntiDumbass amendment: role_id is primary lane identity; the TDD role has a specific, bounded lane responsibility

### E5 — Iteration loop (what replaces the chat loop)
- Operator + agent surface a candidate invariant (informally, in conversation)
- Agent adds the invariant as a pytest function in the registered file
- TDD role runs the suite, produces receipt
- If RED, the receipt names the conflicting fields; the operator/agent decides path A (ratchet-red) or path B (atomic remediation)
- No external chat-with-Pro round-trip required for each invariant
- Pro-style architecture review can still happen, but it becomes optional commentary, NOT a required step in the loop

## TDD role contract (operator directive 2026-05-23 — STRONGER RULES)

Operator: *"Live-State Semantic TDD is not a ChatGPT/Claude conversation pattern. It is a TDD role responsibility."*

The TDD role MUST own the following workflow. These rules are binding and override any agent's local interpretation:

1. **Run the live-state invariant suite against the actual repo state.**
2. **When an invariant fails, treat the pytest failure as the semantic receipt.** The `AssertionError` message names the conflicting fields. No additional typed receipt dataclass is required.
3. **Before proposing a fix, search existing typed state, active plans, inventories, and migration/debt records for the same issue.** Specifically: `dev/state/topology_hardcode_inventory.jsonl`, `dev/active/`, `delete_after_ingest.md` amendment blocks, contract registries, and existing reducers (e.g. `runtime/role_topology.py`).
4. **Identify the intended replacement contract BEFORE deleting, reverting, or patching the current logic.** No "revert first, design later" — the replacement must be named (file path + symbol) before the broken logic is touched.
5. **If the failure is target-state architecture debt, keep it as manual/red OR `@pytest.mark.xfail(strict=True)` with an explicit migration-reference docstring** (pointing at the inventory entry / phase / amendment id). Do NOT wire expected-red target-state tests into check-router as blocking green proof. They are visible ratchets, not gate inputs.
6. **If the failure is current-safety behavior, fix it immediately and rerun until green.** Current-safety means: the projection is being USED as authority by a downstream consumer right now.
7. **A thin `devctl` entrypoint owns this loop** so the TDD role runs without relying on ChatGPT/Claude conversational context.

### The two stronger rules (operator verbatim)

> *"Do not remove bad logic until the replacement contract is named."*

> *"Do not preserve bad logic as canonical just to make a test pass."*

These are the GUARD against both failure modes I exhibited earlier in this session:
- Failure mode 1 (workaround): adding a `migration_debt` note to make the test green while preserving the broken contract as canonical — violates the second rule
- Failure mode 2 (orphaned revert): reverting broken logic without naming the replacement — violates the first rule

### Topology-specific application of the rules

For the `coordination_topology` enum smell:
- Do NOT validate `multi_agent_active` by checking `active_actor_count >= 2`. That blesses the wrong model.
- The invariant MUST assert: agent-count topology labels are deprecated and cannot be canonical coordination authority. `observed_runtime.active_actor_count` is evidence only. Canonical coordination must be role/authority/session based and agent-agnostic.
- Before editing `coordination_state_projection.py`, inspect existing typed topology sources: `dev/state/topology_hardcode_inventory.jsonl`, `dev/scripts/devctl/runtime/role_topology.py` (`LiveRoleTopology`, `RoleOccupancy`), `runtime/role_profile.py`, and any active-plan references.
- Choose ONE atomic replacement path:
  - **current-safety bridge**: legacy label is quarantined under `legacy_*` and cannot drive authority — emit role-based fields as canonical, legacy enum as compatibility only
  - **target-state migration**: replace canonical topology with role/authority/session graph fields — drops the Literal enum entirely
  - **no partial patch** that makes the old enum look correct

The `migration_debt` note is only acceptable as a temporary bridge if the Phase 6 atomic remediation is NOT being done in this slice. If Phase 6 IS the active slice, the note is the wrong fix.

## Unplanned Failure Protocol (operator directive 2026-05-23)

Operator: *"Not in plan ≠ ignore. Not in plan ≠ start random coding. Not in plan = create evidence and route it."*

This is the missing piece between truth-detection and uncontrolled implementation. The TDD role must NOT freeze when an invariant fails without a matching plan row, AND must NOT freehand a fix.

### Existing typed surfaces the protocol routes into (verified registered, NOT invented)

Connectivity verified by `devctl platform-contracts --format json` (2026-05-23): 230 shared contracts + 22 artifact schemas registered. The finding/intake surfaces below all appear in the registered blueprint:

| registered contract_id | python class / file | purpose |
|---|---|---|
| `Finding` (shared contract) | `FindingRecord` in `runtime/finding_contracts.py` | typed finding contract with identity seed, evidence, severity |
| `DecisionPacket` (shared contract) | `DecisionPacketRecord` in `runtime/finding_contracts.py` | packet emitted from a finding (routed into review channel) |
| `FindingBacklog` (shared contract) | `runtime/finding_backlog.py` | aggregate finding ledger |
| `FindingReview` (shared contract) | review-channel lane | review of pending findings |
| `PlatformFindingIngest` (shared contract) | `runtime/platform_finding_ingest.py` | finding ingestion entry point |
| `FindingTtlEvidence` (shared contract) | freshness/TTL evidence | staleness guard |
| `FindingAffectedScope` (shared contract) | scope classification | scope/blast-radius |
| `NonTrivialOutputProofRemediationFinding` + Ledger (shared) | typed state ledger | existing remediation finding pattern — the TDD role's findings can compose into this |
| `ProbeReport` (artifact schema) | `dev/scripts/devctl/review_probe_report.py` | canonical aggregate probe payload — natural carrier for live-state invariant failures |
| `WorkIntakePacket` (runtime-internal, 13 consumers) | `runtime/work_intake_models.py` | work intake routing — composes with session/plan/coordination state |
| `IntakeRoutingState` (runtime-internal) | `runtime/work_intake_models.py` | routing classification |
| `build_finding_id()` | `runtime/finding_contracts.py` | typed finding-id construction |
| `decision_packet_from_finding()` | `runtime/finding_contracts.py` | converts finding → routable packet |
| `dev/state/*_remediation_findings.jsonl` | typed state | append-only finding ledgers |
| `dev/audits/plan_intake/` | plan-level | plan intake markdown for larger architecture work |

The TDD role's invariant failures should construct `Finding` rows and route them through `decision_packet_from_finding()` to emit `DecisionPacket` records. For batch/summary work, the natural carrier is `ProbeReport` (already the canonical aggregate probe payload).

### Protocol — TDD role behavior on invariant failure

When a live-state invariant fails:

1. **Preserve the failing pytest output as the semantic receipt.** Do not silence, do not refactor the assertion to make it pass. The assertion message IS the typed evidence.
2. **Search existing authority for an owner** (in this order):
   - `dev/state/topology_hardcode_inventory.jsonl` and other typed inventory files
   - `dev/active/*.md` (active plan rows + owner docs)
   - `delete_after_ingest.md` amendment blocks
   - `dev/state/plan_index.jsonl` (typed plan rows)
   - `dev/state/*_remediation_findings.jsonl` (existing finding ledgers)
   - `dev/audits/plan_intake/` (open intake)
   - Review-channel packet kinds
3. **If owner exists** → attach the failing invariant to that owner (extend an existing finding's evidence, or note the invariant in the owner's typed surface) and follow that authority. The TDD role does NOT propose a competing fix.
4. **If no owner exists** → construct a typed `FindingRecord` via `finding_contracts.build_finding_id()` + `decision_packet_from_finding()` with:
   - `invariant_id` — pytest test name
   - `command_run` — the devctl command + args
   - `observed_fields` — the conflicting field paths + values from the assertion message
   - `expected_semantic_contract` — what the invariant asserts
   - `failure_message` — the full AssertionError
   - `suspected_source_files` — files the assertion message points at
   - `severity` — see classification below
   - `safe_to_repair_immediately` — boolean
5. **Classify severity** (one of):
   - `current_safety_blocker` — projection IS being used as authority by a live consumer right now; needs immediate repair
   - `output_truth_contradiction` — same-output fields contradict each other
   - `migration_debt` — known debt already inventoried (e.g. `topology_hardcode_inventory.jsonl` entries)
   - `stale_projection` — projection lags reducer truth
   - `missing_typed_authority` — no typed contract owns this surface yet
   - `unknown_architecture_gap` — none of the above; needs operator-level architecture decision
6. **Decide repair lane**:
   - `current_safety_blocker` with small bounded blast radius → write the minimal failing test (already done by the invariant) and fix it immediately, rerun until green
   - `migration_debt` / `output_truth_contradiction` / `stale_projection` / `unknown_architecture_gap` → keep the test manual or `@pytest.mark.xfail(strict=True, reason="...")` with the typed finding id in the docstring until the owning plan row is accepted; route the `DecisionPacketRecord` to the review channel
7. **NEVER make the test green by weakening the invariant.**

### Lifecycle (the binding sequence)

```
Live-state invariant fails
  → preserve pytest output as semantic receipt
  → search existing authority for owner
  → owner found?
       yes: attach failure to owner; continue that plan
       no:  construct typed FindingRecord
             → classify severity
             → emit DecisionPacketRecord via decision_packet_from_finding()
             → route to review channel
             → decide repair lane based on classification
  → only then patch (or keep red as ratchet)
```

### Two failure modes the protocol explicitly prevents

1. **Sees-smell-forgets-plan**: agent sees a code smell, starts "fixing" without checking that the typed inventory already inventoried it. PREVENTED by step 2 (search owner before acting).
2. **Sees-smell-stays-frozen**: agent sees a smell that's NOT in the plan and does nothing (or just complains in chat). PREVENTED by step 4 (typed intake when no owner exists).

The TDD role's identity: **truth detector + intake generator. NOT uncontrolled implementer.**

## E2-MINIMAL — Pro-corrected current slice (2026-05-23)

**Operator directive (verbatim)**: *"Your idea is not too big. Claude's immediate implementation version is too big."*

ChatGPT Pro reviewed the previous "Full System" build sequence and correctly flagged it as governance theater. The current slice MUST be the smallest proof-bearing path. The "Full System" section below is RETAINED as target architecture (Phase 2+), NOT as immediate scope.

### Current slice boundary

The full TDD role system is the **target architecture**. It is **NOT** the next coding step. The next coding step (E2-minimal) is to prove the live-state pytest suite can drive the existing `GroundTruthProbeRunReceipt` and the existing final-response gate **without creating a parallel lifecycle**.

**Forbidden in current slice** (any one of these makes the slice too big):
- `runtime/tdd_role_responsibility.py` (premature; already written — see "Cleanup before MVP execution" below)
- `runtime/live_state_invariants.py` custom suite runner
- `commands/tdd_role.py` new top-level CLI
- finding/decision-packet auto-routing
- render-surfaces projection (boot card section)
- context-graph node for TDD role
- system-map / system-picture wiring
- connectivity registry entry for `TDDRoleResponsibility`
- contract registry entry (no 230 → 231 bump)
- slice lifecycle receipt integration
- quality-policy / check-router registration of the new suite
- a parallel `build_live_state_invariant_receipt()` builder (smell — ground-truth-probe owns the receipt)

**Allowed in current slice**:
- Keep `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py` as the oracle
- Fix or classify the coordination-state contradiction (invariant 2b stays `xfail(strict=True)` per architecture rule)
- Add an opt-in `--pytest-target` adapter to the existing ground-truth-probe `--record` invocation path
- Map pytest exit code into the existing `GroundTruthProbeRunReceipt.verdict` (`satisfied` / `unsatisfied`)
- Store pytest report path + sha256 in the existing receipt fields (`probe_report_path`, `probe_report_sha256`)
- Verify `develop next --enforce-final-response-gate` blocks when the receipt is unsatisfied

### What the MVP must prove (3 things, verbatim from operator)

1. **The AI missed a contradiction in live output** (already true — invariant 2b RED catches `multi_agent_active` while the architecture says role-based)
2. **The TDD truth-rule caught it** (already true — pytest produced the structured semantic receipt)
3. **The existing ground-truth receipt / final-response gate can block "done" when the truth-rule fails** (THIS IS THE REMAINING WORK)

### Build sequence — E2-minimal (the only sequence to execute right now)

1. **Keep the live-state pytest suite** at `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py` — already exists, already producing 1 PASS / 1 PASS / 1 XFAIL
2. **Resolve the coordination-state contradiction** — either fix the reducer or explicitly classify as `xfail(strict=True)` with migration reference (already done for invariant 2b)
3. **Thread `--pytest-target` through the existing ground-truth-probe receipt path** — see the "Ground-truth-probe command scoping finding" below for what "existing path" means here
4. **Map pytest exit code into `GroundTruthProbeRunReceipt.verdict`** — `0 → satisfied`; non-zero (with at least one FAIL not XFAIL) → `unsatisfied`
5. **Verify the final-response gate blocks** on `unsatisfied`:
   ```
   python3 dev/scripts/devctl.py develop next \
     --actor agent \
     --enforce-final-response-gate \
     --format json
   ```
6. **Write the demo doc** (`dev/guides/live_state_semantic_tdd_demo.md` + mirror to separate release repo — see Demo Repo section)
7. **Stop** — do NOT promote into the full TDD role lifecycle in this slice

### Pro's specific smell to avoid (verbatim)

> *"This is the risky line: `build_live_state_invariant_receipt(result, repo_root) -> GroundTruthProbeRunReceipt`. That implies a separate builder/lifecycle. Better: ground-truth-probe owns `GroundTruthProbeRunReceipt` construction. The pytest target only supplies evidence into the existing ground-truth-probe reducer."*

The E2-minimal slice MUST NOT write a parallel receipt builder. Pytest output is **evidence**; the existing builder in `runtime/ground_truth_probe_receipt.py:build_ground_truth_probe_receipt()` remains the owner.

## Ground-truth-probe command scoping finding (2026-05-23, surfaced during E1 inventory)

**Verified by grep**: `devctl ground-truth-probe` does NOT exist as a top-level command today. The receipt is built/consumed from inside:
- `dev/scripts/devctl/commands/development/design_preflight.py`
- `dev/scripts/devctl/commands/development/design_preflight_probe.py`
- `dev/scripts/devctl/commands/development/design_preflight_provider.py`
- `dev/scripts/devctl/commands/development/final_response_gate.py`
- `dev/scripts/devctl/commands/development/baseline_inventory.py`
- `dev/scripts/devctl/commands/development/report.py`
- `dev/scripts/devctl/commands/development/parser.py`

There is no `commands/ground_truth_probe.py` and no `ground-truth-probe` entry in `commands/listing/__init__.py:COMMANDS`. Pro's "patch the existing `ground-truth-probe --record` path" assumes a top-level command that does not exist on this branch.

### Three scoping paths the operator must pick BEFORE E2-minimal execution

| path | description | size |
|---|---|---|
| **A** | Thread `--pytest-target` through whichever existing `develop` subcommand currently invokes `build_ground_truth_probe_receipt()` (likely `develop` or `develop next` based on `parser.py` references). Smallest scope — touches one parser, one builder call site. | smallest |
| **B** | Add `ground-truth-probe` as a NEW thin top-level command in `commands/ground_truth_probe.py` + register in `commands/listing/__init__.py:COMMANDS` + `cli_parser/entrypoint.py`. This matches Pro's command-shape suggestion verbatim but ADDS a command surface. | thin but additive |
| **C** | Defer the CLI surface entirely; expose the pytest-target functionality only as a Python helper consumed by `final_response_gate.py` and `develop next`. No new command, no new flag — the gate auto-runs the registered suite when the receipt is stale or missing. | invisible to CLI; gate-only |

Operator decides A vs B vs C before execution begins. Path A is the cleanest fit for the "do not expand surface" rule; path B matches Pro's command shape exactly but adds a top-level command (which the slice boundary forbids unless required); path C is the most aggressive minimization but hides the manual invocation surface the demo needs.

## Surface verification rule (Pro, 2026-05-23)

**Operator directive (verbatim)**: *"Before adding any named surface, verify it exists with grep/git ls-files. No speculative contract names."*

Pro searched the pushed branch (snapshot HEAD `90451b8a`, branch HEAD `7a7afa85`) for several surface names I cited and could not find them on the pushed branch. They exist locally (I verified by `grep -rln`), but they may be unpushed worktree state. The rule going forward:

| before referencing in plan | required check |
|---|---|
| Any python class or symbol name | `grep -rn "class FooBar" dev/scripts/devctl --include="*.py"` |
| Any file path | `git ls-files <path>` AND a `Read` to confirm shape |
| Any registered contract id | `python3 dev/scripts/devctl.py platform-contracts --format json` and search the output for the id |
| Any CLI command | `grep -n "<command>" dev/scripts/devctl/commands/listing/__init__.py` (must appear in `COMMANDS`) |
| Any typed state file | `ls dev/state/<file>` (and inspect first row) |

If a check fails, the plan must NOT proceed against the missing surface. Either (a) introduce the surface explicitly as a separate planned task, or (b) reroute to a surface that DOES exist.

## Cleanup before MVP execution

**Premature artifact (created in this session before Pro's correction)**:
- `dev/scripts/devctl/runtime/tdd_role_responsibility.py` — written during E2a before scope was reduced. Per Pro's "no new TDD responsibility contract in current slice" rule, this file MUST be deleted before E2-minimal execution begins. The constants (`TDD_ROLE_ID`, `LIVE_STATE_INVARIANT_PROBE_ID`, `LIVE_STATE_INVARIANT_TEST_PATHS`) can be inlined into the test file or a small helper if E2-minimal needs them; they do NOT need their own typed contract yet.

**Task list to update at execution time**:
- Tasks #3 (E2a), #4 (E2b), #5 (E2c), #6 (E3), #7 (E4-E8) are all **deferred to Phase 2+** — not part of E2-minimal
- One new task to create: `E2-min: thread --pytest-target through existing ground-truth-probe receipt path` (path A/B/C decided by operator first)
- One new task to create: `E2-min-demo: write Live Output Truth Rules demo doc + separate release repo`

## MVP Demo — separate public release repo (operator directive 2026-05-23)

**Operator directive (verbatim)**: *"the demo it needs to be another repo so i can show this off not here... readme mds etc so that way people dont have to go through this huge codebase to use it"*

The demo lives in a **separate public release repo**, not inside the GuardIR worktree. Reasons:
- The GuardIR repo is too large to wade through for a wedge demo
- The release wedge has a different audience (devs + AI/vibe coders) than GuardIR internals (governance engineers)
- A separate repo gives a portable cloneable artifact — `git clone <repo> && cd <repo> && ./demo.sh`
- Operator's career-portfolio angle (CS senior, AI-platform/devtools roles) is served by a focused project repo, not by buried GuardIR docs

### Honest assessment of the portfolio angle

The operator asked: *"could this be tested on a clone of th old repo we had this morning to show all the stuff it catches... it could get my attention/a job in CS"*

My honest read:
- **Strong portfolio piece for specific roles**: AI-platform engineering, devtools, AI-governance, agent-orchestration teams. The wedge — "AI agents pass tests but misread output; this catches it" — is concrete, demoable in 60 seconds, and addresses a real industry pain point that's surfacing in agent rollback / governance discussions.
- **Not a guaranteed signal alone**: portfolio pieces help; they don't bypass the rest of a hiring pipeline. The value is "demonstrated ability to architect typed governance surfaces and ship a usable wedge."
- **The before-state-on-old-clone demo is genuinely strong**: cloning the pre-fix state of GuardIR, running the live-state TDD against it, and showing the contradiction caught BEFORE the fix lands is the most credible "we found a real bug" evidence. Replay-able, reproducible, doesn't depend on internal access.

### Demo repo structure (separate public repo — PROFESSIONAL SHOWPIECE)

**Operator directive 2026-05-23**: *"this needs to look professional... a showpiece of my shit, dude."*

Repo name: `output-contract-tests` (Pro-vetted, professional, says what it does).

Casual doc names removed. Numbered docs read in order. Examples numbered too. Structure matches how mature OSS projects organize themselves:

```
output-contract-tests/
├── README.md                              # Hero pitch + 60s demo + nav into docs/
├── docs/
│   ├── 01-quickstart.md                  # Run the demo in one minute
│   ├── 02-concepts.md                    # Mental model (no jargon)
│   ├── 03-architecture.md                # pytest → receipt → gate (technical)
│   ├── 04-worked-example.md              # Coordination topology case in depth
│   ├── 05-patterns.md                    # 6 contradiction patterns this catches
│   ├── 06-comparison.md                  # vs unit tests / contract tests / property tests
│   └── 07-faq.md                         # Common questions, anti-patterns
├── examples/
│   ├── 01-coordination-topology/          # multi_agent_active case (the hero example)
│   │   ├── README.md                     # What's broken, why it matters
│   │   ├── before.json                   # Pre-fix sync-status output
│   │   ├── after.json                    # Post-fix or xfail-classified state
│   │   ├── invariant.py                  # The truth rule
│   │   └── failure.txt                   # Captured pytest assertion message
│   ├── 02-status-vs-errors/               # status=passed AND errors non-empty
│   ├── 03-barrier-vs-attention/           # awaiting_reviewer_ack vs attention_required=False
│   ├── 04-stale-packet/                   # stale packet shown as active work
│   ├── 05-role-authority/                 # reviewer role claiming mutation authority
│   └── 06-empty-required-field/           # empty required field treated as success
├── benchmark/                             # Reproducible before/after on a cloned old commit
│   ├── README.md                         # How to reproduce on a clean machine
│   └── snapshot.json                     # Pinned commit + observed output
├── bin/
│   └── oct                               # One-command demo runner (alias: output-contract-tests)
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE                                # MIT or Apache-2.0
├── pyproject.toml                         # Library packaging — pip-installable later
└── .github/
    └── workflows/
        └── ci.yml                        # Run the demo as a smoke test on every push
```

**Naming conventions (professional, scannable)**:
- Docs are numbered (`01-quickstart.md`, `02-concepts.md`, ...) so reading order is obvious
- Examples are numbered with the hero example (`01-coordination-topology/`) first
- No "for-vibe-coders" / "for-developers" filenames — those audience splits live INSIDE doc 01-quickstart.md (the simple version) and 03-architecture.md (the technical version), respectively
- The bilingual reference (same example, two views) lives in `04-worked-example.md`
- Binary name is `oct` (short, memorable, expandable as alias)

**What the README hero must contain** (top of repo, first impression):

```markdown
# Output Contract Tests

> Catch AI coding agents that pass their tests but misread the actual output.

[badges: CI status, license, Python version]

## What it does

AI agents often run a command, see "exit 0" or a JSON blob, and move on.
But the output itself can contradict its own claims — a status field says
"passed" while errors are non-empty, a topology label is deprecated, a
reviewer is waiting but the agent thinks nothing needs attention.

Output Contract Tests catches those contradictions BEFORE the agent
declares "done."

## 60-second demo

\`\`\`bash
git clone https://github.com/<user>/output-contract-tests
cd output-contract-tests
./bin/oct examples/01-coordination-topology
\`\`\`

You'll see: pytest fails with a structured assertion naming the
conflicting fields. The same machinery hooks into your existing CI
gate so agents cannot claim green until the contradiction is fixed.

## How it works

1. A pytest suite runs your live tooling and asserts semantic rules
   about the output (not just "did it exit 0").
2. The pytest result is recorded as a typed proof receipt.
3. Your completion gate refuses to allow "done" until the receipt
   says the output's contract was honored.

[diagram: pytest → receipt → gate → block/allow]

## When to use this

| You ship | This catches |
|---|---|
| AI coding agents | Agents passing tests while misreading their own output |
| Multi-agent orchestrators | Status surfaces that contradict each other |
| Devtool platforms | Agents claiming green against red ground truth |
| CI for AI-driven changes | Completion claims unbacked by their own evidence |

[then nav into docs/01-quickstart.md ...]
```

**Why this is a showpiece**:
- Repo name + binary name are short, professional, expandable
- README opens with a one-sentence pitch a recruiter scans in 5 seconds
- 60-second demo is `git clone && one command` — no environment setup story
- Numbered docs prove there's structure (not a random pile of markdown)
- `benchmark/` directory proves the wedge was tested against real before-state
- CI workflow proves the demo itself stays working
- `pyproject.toml` signals "this could become a library"

**What this is NOT** (avoid these — they kill the professional read):
- No emojis in titles
- No "vibe coder" language in filenames (lives inside docs only, framed as "Plain-language version" sub-sections)
- No "as seen in my GuardIR governance platform" boasting in the README
- No 200-contract feature list — the README only mentions one wedge
- No corporate fluff ("revolutionary," "next-gen," "transform your workflow")

### Demo doc — required content (Pro + operator combined)

The demo doc MUST have BOTH tracks. **Naming (Pro-corrected 2026-05-23 — "Live Output Truth Rules" sounded too toy-like)**:

```
Title:    Output Contract Tests for AI Coding Agents
Subtitle: Catching cases where an agent runs a command but misses what
          the output actually means.

Developer name:        Output Contract Tests
GuardIR internal name: Live-State Semantic TDD
Plain-English:         tests that make command output prove it is telling
                       the truth
```

Pro's name ranking (operator picked #1):
1. **Output Contract Tests** (selected)
2. Live Output Integrity
3. Semantic Output Contracts
4. Agent Output Verification
5. Output Comprehension Tests

#### Track 1 — Vibe-coder framing (Pro verbatim)

**Goal**: make the problem obvious without architecture language.

Framing:
> *"AI can run a command and still misunderstand what the command said. This system adds 'truth rules' to the output. If the output contradicts itself, the AI is not allowed to say done."*

Example block:
```
Bad:
Command output says:
- status = passed
- errors = ["missing reviewer approval"]
AI says:
- looks good
Truth rule:
- if status is passed, errors must be empty
Result:
- test fails
- AI cannot claim green
```

Track 1 needs: problem / simple example / before / after / what command to run / what failure means / why this helps them.

Track 1 MUST NOT lead with: invariants, typed receipts, final-response gate, topology projection, role authority lifecycle.

Track 1 translation glossary (for the bilingual section later):
- invariant → truth rule
- receipt → proof record
- gate → blocker
- projection → status output

#### Track 2 — Developer framing (Pro verbatim)

**Goal**: show the actual mechanism and integration.

Framing:
> *"Live-State Semantic TDD treats CLI/status output as a contract. A pytest suite runs live devctl commands, parses JSON output, and asserts semantic consistency rules. The pytest result is adapted into the existing `GroundTruthProbeRunReceipt` path, so the existing final-response gate can block completion claims when semantic truth checks fail."*

Track 2 needs: command flow / file paths / test names / receipt fields / exit-code mapping / gate behavior / integration boundary.

Example flow block:
```
pytest target:
  dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py

run:
  python3 dev/scripts/devctl.py ground-truth-probe \
    --record \
    --pytest-target dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py \
    --format json

mapping:
  pytest exit 0       → GroundTruthProbeRunReceipt.verdict = "satisfied"
  pytest exit nonzero → GroundTruthProbeRunReceipt.verdict = "unsatisfied"

gate:
  python3 dev/scripts/devctl.py develop next \
    --actor agent \
    --enforce-final-response-gate \
    --format json
```

(Note: actual command depends on E2-minimal scoping path A/B/C — see Ground-truth-probe command scoping finding above. If path A is chosen, the command becomes `develop --some-flag --pytest-target ...` instead of `ground-truth-probe --record`.)

### Demo doc structure (single file in the demo repo)

```
# Live Output Truth Rules
# (Developer name: Live-State Semantic TDD)

## 1. For AI/Vibe Coders: The Simple Version
- AI ran command ≠ AI understood command
- truth rules
- before/after example
- what the failure means

## 2. For Developers: The Technical Version
- pytest live-state suite
- JSON field checks
- receipt mapping
- final-response gate
- exact commands

## 3. Same Example, Two Views
- coordination_topology = multi_agent_active
- vibe-coder explanation: "that word is old/bad architecture; the system is supposed to be role-based, not 'single agent / multi agent'"
- developer explanation: "deprecated count-coupled label; canonical model is role/authority/session; active_actor_count is evidence only"

## 4. Use Cases
- status passed but errors exist
- no attention required but barrier exists
- stale packet shown as active
- deprecated topology used as authority
- reviewer role claiming mutation authority
- empty required field treated as success

## 5. What This Is Not
- not a prompt
- not asking AI to read harder
- not a new control plane
- not a full TDD role system yet

## 6. MVP Boundary
- live pytest suite
- existing ground-truth receipt
- existing final-response gate
```

### Bilingual reference example (must appear verbatim in demo)

**Vibe-coder version**:
> *"The AI ran the command and said 'green.' But the command output said: `coordination_topology = "multi_agent_active"`. That sounds okay, but in this repo that word is old/bad architecture. The system is supposed to be role-based, not 'single agent / multi agent.' So the truth rule says: do not treat agent-count labels as real authority. The test fails. That failure stops the AI from claiming the system is clean."*

**Developer version**:
> *"The live sync-status JSON emitted: `coordination_state.coordination_topology = "multi_agent_active"`, `coordination_state.notes = []`. `multi_agent_active` is a deprecated count-coupled topology label. The canonical coordination model is role/authority/session based. `observed_runtime.active_actor_count` is evidence only; it must not define topology authority. The test asserts: `coordination_state.coordination_topology not in {"single_agent", "dual_agent", "single_agent_active", "multi_agent_active", "no_active_agents"}` unless surfaced only through legacy/migration fields. Failure maps to `GroundTruthProbeRunReceipt.verdict = "unsatisfied"`. The final-response gate blocks completion."*

### Acceptance criteria for the demo

- A developer can understand the value in under 3 minutes
- A vibe coder can understand why "the AI ran the command" is not enough
- The before/after includes real command output or a realistic redacted sample
- The demo explains why this is a proof system, not another prompt
- The demo does NOT depend on ChatGPT or Claude context
- One-command demo runs end-to-end (`./scripts/demo.sh`) and shows pytest red → unsatisfied verdict → gate blocks → pytest green → satisfied → gate allows
- The README explains the bug in 60 seconds

### Demo execution order

1. After E2-minimal proves the receipt/gate path on GuardIR (this repo)
2. Operator creates the separate public demo repo (operator picks name; suggestion: `live-output-truth-rules`)
3. Clone or extract the relevant minimal harness (the test file + a thin runner that calls ground-truth-probe or its successor command)
4. Write the demo doc with BOTH tracks per Pro's framing
5. Add the `examples/` directory with 6 use cases — at least the `coordination-topology` one runs end-to-end on first push
6. Add `scripts/demo.sh` as the one-command entry point
7. Publish to GitHub; link from operator portfolio

The demo repo is the wedge release. The GuardIR repo is the deep system behind it. The marketing sentence is: *"A semantic CI layer that catches when AI-agent control surfaces contradict themselves."* — not "AI governance platform with 200 contracts and 70 guards."

### Demo as PART OF the MVP — not Phase 2

Operator: *"The demo is part of the MVP. The full TDD role system is not."*

The demo doc IS required to close E2-minimal. The full-system architecture (everything in the "Target Architecture" section below) is NOT required to close E2-minimal.

## Target Architecture — TDD Role as a Full System (Phase 2+, not current slice)

**SCOPE NOTE (Pro correction, 2026-05-23)**: this section is RETAINED as target architecture but is **NOT** the current implementation slice. See "E2-MINIMAL — Pro-corrected current slice" above. Do NOT execute the build sequence below until E2-minimal is proven AND operator authorizes promotion to Phase 2.

Operator directive (when this section was written, before Pro correction): *"shouldn't it be part of the rest of the system, the governance, the lifecycle, you know, showing proof of what was run, everything. This needs to be a full system for this fucking role."*

A module + a thin CLI is NOT a role. A full-system TDD role composes with every existing typed surface that already carries governance/lifecycle/proof authority. The TDD role does not invent parallel surfaces — it routes through the canonical ones below.

### Composition map — each piece links to an existing typed surface

| TDD role facet | Existing typed surface to compose with | What the TDD role contributes |
|---|---|---|
| **Role registry** | `runtime/role_profile.py` (`tdd_first_role` registered with `RoleCapabilityClass.TEST`) | Add typed `TDDRoleResponsibility` row naming what the role MUST execute; keep capability class as TEST (no mutation/ACK authority) |
| **Typed responsibility contract** | (new file) `runtime/tdd_role_responsibility.py` | Frozen dataclass listing: registered live-state invariant test paths, probe id, required pytest exit-code semantics, finding-routing policy |
| **Live-state invariant suite runner** | (new file) `runtime/live_state_invariants.py` | Subprocess pytest with `--json-report` against registered paths; parse PASS/FAIL/XFAIL counts; classify failures per the Unplanned Failure Protocol |
| **Proof of what was run** | `GroundTruthProbeRunReceipt` (`runtime/ground_truth_probe_receipt.py`) + `dev/state/ground_truth_probe_receipts.jsonl` | Each TDD role run appends a receipt with: probe_id=`live_state_invariants_v1`, observed_probe_ids, verdict (`satisfied` / `unsatisfied` / `missing`), warnings naming failing invariants, `probe_report_path` to the pytest JSON report, `probe_report_sha256` |
| **Finding / intake routing** | `Finding` + `DecisionPacket` (`runtime/finding_contracts.py`) | When invariant fails AND no owner exists in plan/inventory: construct `Finding` via `build_finding_id()`, emit `DecisionPacket` via `decision_packet_from_finding()`, append to `dev/state/*_findings.jsonl` ledger |
| **Lifecycle composition** | `SliceLifecycleReceipt` + `dev/state/slice_lifecycle_receipts.jsonl` | TDD role's ground-truth receipt becomes evidence for slice lifecycle; failing invariants block slice closure if they map to the active slice's scope |
| **Plan-row composition** | `PlanRow` / `dev/state/plan_index.jsonl` | Failing invariants either link to an existing plan row (owner found) or create a plan-intake row via `dev/audits/plan_intake/` |
| **Governance / exception composition** | `GovernedExceptionLifecycle` + `BypassLifecycle` | TDD role NEVER grants bypass authority; it produces evidence consumed by governed-exception flows when an invariant blocks publication |
| **Gate composition (final-response)** | `final_response_gate.py` already consumes `GroundTruthProbeRunReceipt` | No new gate; final-response-gate now also sees live-state invariant failures via the same receipt path |
| **Gate composition (publication preflight)** | `require_recent_ground_truth_receipt()` (`runtime/ground_truth_probe_gate.py`) | Push preflight already requires recent receipt; live-state invariant failures naturally surface here |
| **Quality policy / check-router** | `quality_policy/defaults.py` + `commands/check/router_python_tests.py` | Register the green portion of the suite (invariant 1 + 2a) as a `_DEVCTL_TEST_TARGETS` entry; xfail-strict invariant 2b NOT registered as blocking input |
| **CLI surface (thin entry point)** | (new command) `commands/tdd_role.py` registered in `commands/listing/__init__.py:COMMANDS` and `cli_parser/entrypoint.py` | `devctl tdd-role --action run-live-state-invariants --format json` — runs suite, writes receipt, emits result |
| **Render-surfaces / projection** | `render-surfaces` (existing command) | Add a generated section to `AGENTS.md` / `CLAUDE.md` boot card surfaces showing TDD role status + last-run receipt timestamp + verdict |
| **Context-graph** | `context-graph --mode bootstrap` | TDD role responsibility appears as a node so agents can discover it |
| **System-map / system-picture** | `system-map`, `system-picture` | TDD role lane appears alongside other role lanes |
| **Connectivity registry** | `platform/connectivity_registry.py` | New module exports `TDDRoleResponsibility` contract; connectivity verification can confirm wiring |
| **Contract registry** | `PlatformContractRegistry` | New typed contract appears in `devctl platform-contracts` output (currently 230 registered) |
| **Bypass receipts** | `BypassReceipt` | TDD role's typed evidence is read-only; no spawn or mutation authority |
| **Surface provenance** | `SurfaceProvenance` | Any TDD-role-generated projection carries provenance pointing at the TDD role responsibility contract |

### Build sequence (atomic, composition-first)

Each step composes with at least one existing typed surface. No step invents a parallel system.

1. **E2a — Define typed responsibility** (`runtime/tdd_role_responsibility.py`)
   - `@dataclass(frozen=True) class TDDRoleResponsibility`
   - `LIVE_STATE_INVARIANT_TEST_PATHS: tuple[str, ...]` — registered suite paths
   - `LIVE_STATE_INVARIANT_PROBE_ID = "live_state_invariants_v1"`
   - `TDD_ROLE_ID = "tdd_first_role"` — pulled from `runtime/role_profile.py`
   - Composes with role_profile (existing role_id), finding_contracts (probe semantics), ground_truth_probe_receipt (receipt semantics)

2. **E2b — Suite runner** (`runtime/live_state_invariants.py`)
   - `run_live_state_invariant_suite(repo_root, *, paths=None) -> LiveStateInvariantRunResult`
   - Subprocess pytest with stable args; parse stdout (or `--json-report` if pytest-json-report plugin is available)
   - `LiveStateInvariantRunResult` carries: passed_ids, failed_ids, xfailed_ids, errored_ids, exit_code, raw_stdout_path
   - `build_live_state_invariant_receipt(result, repo_root) -> GroundTruthProbeRunReceipt`
     - Composes with existing `build_ground_truth_probe_receipt(inputs)` builder
     - `verdict = "satisfied" if not failed else "unsatisfied"` (extends existing verdict vocabulary)
     - `warnings` lists failing invariant ids
   - Uses `append_ground_truth_probe_receipt()` to write to `dev/state/ground_truth_probe_receipts.jsonl`

3. **E2c — Finding routing on failure** (extends suite runner)
   - For each failed invariant: search owner (typed inventory + active plan + finding ledger)
   - If no owner: construct `Finding` via `build_finding_id()` and emit `DecisionPacket` via `decision_packet_from_finding()`
   - Composes with existing `finding_contracts.py` — no new finding system

4. **E3 — CLI surface** (`commands/tdd_role.py` + listing/parser wiring)
   - `devctl tdd-role --action run-live-state-invariants [--format json|md] [--paths a,b,c]`
   - Calls E2b runner + E2c finding routing
   - Returns receipt summary; non-zero exit if `verdict=unsatisfied` and `--strict` set
   - Registered in `commands/listing/__init__.py:COMMANDS` and parser entrypoint

5. **E4 — Gate composition (no new gate)**
   - The receipt produced by E3 is automatically read by `final_response_gate.py` (existing wiring)
   - `require_recent_ground_truth_receipt()` (existing wiring) ALREADY blocks if no recent receipt
   - This means: once E3 runs, the final-response-gate naturally enforces live-state invariant freshness

6. **E5 — Quality policy registration**
   - Add green portion of the suite (invariant 1, 2a) to `_DEVCTL_TEST_TARGETS` in `commands/check/router_python_tests.py`
   - XFAIL-strict invariant 2b NOT wired here (per Pro architecture review rule)

7. **E6 — Render-surfaces projection**
   - Add TDD role status section to boot card surfaces via `render-surfaces`
   - Read latest receipt timestamp + verdict from `dev/state/ground_truth_probe_receipts.jsonl`
   - Composes with existing surface provenance — no new projection contract

8. **E7 — Connectivity + contract registry registration**
   - Add `TDDRoleResponsibility` to `platform/blueprint.py` shared contracts
   - Confirm via `devctl platform-contracts --format json` that registered count goes from 230 → 231
   - Composes with existing platform registry — no parallel registry

### Proof chain (what "showing proof of what was run" means)

Per CLAUDE.md: *"`TypedAction -> ActionResult -> RunRecord -> ValidationReceipt` is the proof chain for mutations."*

TDD role proof chain (read-only, no mutations):

```
TDDRoleResponsibility (typed contract)
  → run_live_state_invariant_suite() (typed action)
  → LiveStateInvariantRunResult (action result)
  → GroundTruthProbeRunReceipt (run record + validation receipt — same artifact)
  → [if failed] Finding + DecisionPacket (typed evidence for unplanned issues)
  → dev/state/ground_truth_probe_receipts.jsonl (append-only ledger — durable)
  → final_response_gate consumes the latest receipt
```

Every step writes a typed artifact. The full chain is inspectable by reading the receipt ledger. The TDD role is *not* a black-box runner — it's a typed lane that emits typed proof at every stage.

### What the TDD role explicitly does NOT do

- Does NOT grant mutation authority
- Does NOT grant ACK authority
- Does NOT bypass review (no BypassReceipt issuance)
- Does NOT modify projection state directly (only writes to typed ledgers)
- Does NOT short-circuit governed-exception lifecycle
- Does NOT invent new finding/intake/packet/receipt types
- Does NOT skip step 2 of the Unplanned Failure Protocol (search existing authority first)

## Iteration commitment (2026-05-23)

Operator: *"we will keep doing this until we prove it."*

The plan now has:
- Phase A (cleanup) — DONE
- Phase B1 — DONE (test file created, two invariants)
- Phase B2 — DONE (manual pytest run executed)
- Phase B3 — split per Pro architecture review (above)
- Phase B-extra — typed-inventory regression guard (deferred to D2)
- Phase C — ground-truth-probe adapter (folded into Phase E's TDD role responsibility)
- Phase D — check-router wiring + role inversion fixtures
- Phase E (NEW) — TDD role integration as the durable thin entry point

We iterate until the invariant suite + TDD role integration provably catches the contradictions that started this session (typed-controller `attention_required=False` while `awaiting_reviewer_ack` barrier present; `coordination_topology=multi_agent_active` as authority). The proof is: red invariants block final-response-gate; remediation makes them green; the role surface, not external chat, drives the loop.

## Phase F autonomous-run final report (2026-05-23, ~4h session)

### Headline numbers

- **27 invariants** in `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py` (up from 3 at session start)
- **7 amendments engaged** (A17, A18, A19 ×3, A20, A25, A30/A35, A12 ×2, A4, AntiDumbass, projection-freshness)
- **8 real bugs fixed end-to-end** through the dogfood loop (red → fix → green)
- **7 ratchets locked** at current debt counts (walk-down only, no growth)
- **2 xfail-strict ratchets** retained (A17 multi-layer, A20 G41 infrastructure - operator-flagged major-issue class)
- **3 orphan-test violations cleared** in `check_orphan_files`
- **1 stale active-plan registration cleared** (`check_active_plan_sync`)

### End-to-end fixes deployed in `codex-voice` repo

| # | Fix | Surface |
|---|---|---|
| 1 | Topology architecture migration (agent-count → role-based vocab + legacy audit field) | `coordination_state_projection.py` schema v2 |
| 2 | A19 stale-packet hygiene (--include-stale flag + 24h filter) | `event_reducer_inbox.py` + `parser_query_arguments.py` + `event_watch_support.py` |
| 3 | A19 delivery_emitted_at_utc lifecycle (delivery for all packet kinds) | `event_packet_rows.py:125` |
| 4 | A19 stale_packet_count vs past-expiry warning divergence (single source of truth) | `sync_status_action.py` + `event_reducer.py` |
| 5 | Active plan sync (INDEX.md row for the plan) | `dev/active/INDEX.md` |
| 6 | Silent-block at loop decision layer (top_blocker fallback from required_action) | `agent_loop_decision_builder.py` |
| 7 | Race-safe gate-source self-check (read gate first, then ledger) | `test_live_state_invariants.py` |
| 8 | ground-truth-probe pytest timeout bumped to 600s | `commands/ground_truth_probe.py` |
| 9 | Three orphan-test router entries added | `commands/check/router_python_tests.py` |

### Ratchets locked at current debt counts

| Ratchet | Ceiling | Source amendment |
|---|---|---|
| VoiceTerm platform leakage | 122 files | A4 (delete_after_ingest.md line 4115) |
| FPR proven_passed without pytest node id | 37 receipts | A12 (line 4365) |
| FPR unresolved commit_sha | 2 receipts | A12 (line 4366) |
| SYSTEM_MAP orphan module references | 14 refs | Operator system_map directive |
| plan_rows applied without applied_at_utc | 30 rows | A12 G13 (line 4380) |
| plan_rows applied without commit_anchor_ref | 10 rows | A12 G14 (line 4386) |
| review_state.json projection age | 48h max | Projection-freshness finding |

### Phase F sweep progress through delete_after_ingest.md amendments

| Amendment | Status | Action taken |
|---|---|---|
| A4 VoiceTerm leakage | RATCHET locked | 122-file ceiling |
| A11 Half-built prevention suite (G1-G8) | DEFERRED | architectural scope - G58 docs only, G6 spec only |
| A12 Receipt-schema guards (G11-G14) | 2 RATCHETS locked | FPR pytest-node-id + commit_sha checks |
| A15 Import-route integrity | COVERED via A25 connectivity sweep | check_python_typed_seams green |
| A16 Provider hook coverage / topology liveness | PARTIAL via invariants 5/6 | role-based topology + role drift |
| A17 Packet body-open route | XFAIL ratchet | multi-layer fix deferred (operator-flagged major) |
| A18 Single-writer lease | REGRESSION GUARDS | invariants 5+5-self cover capability leak |
| A19 Stale packet hygiene + delivery_emitted_at_utc + queue/warning divergence | FIXED end-to-end ×3 | actual code changes deployed |
| A20 Operator authority sovereignty | XFAIL ratchet | G41 infrastructure required (deferred) |
| A21 Operational command linkage in boot cards | DEFERRED | requires render-surfaces work |
| A22 No-small-patches architectural agents | NOT INVARIANT-SHAPED | behavioral cross-session check |
| A23 Typed agent-spawn authority (G44) | DEFERRED | no live spawn evidence yet |
| A25 Connectivity-first priority | 5-GUARD META-INVARIANT PASSing | runs all 5 in one assertion |
| A30 / A35 Orphan-guard fake-green | REGRESSION GUARD + 3 violations cleared | router entries added |
| A33 Continuous TDD-first / auto-guard | LIVED (the suite itself) | this whole approach IS A33 |
| A34 Half-built feature detector (G58) | NOT YET BUILT | documented but not implemented |
| AntiDumbass role-boundary | REGRESSION GUARD | declared/authority drift labeled via role_source |

### What's left in the doc

Amendments after A23 (line 2164) that are NOT live-state TDD shaped:
- Required typed persistence (line 2223) - schema/contract work
- Packet classification (line 2305) - taxonomy work
- Selector/preemption inventory (line 2336) - lane definitions
- Other deeper sections - architecture-level changes, not single-output contradictions

These don't fit the live-state semantic TDD pattern (run command → assert truth rule on output). They're architectural specifications or process rules. The TDD-discovery sweep captured the contradictions that DO fit the pattern.

### Stop conditions

The operator's directive: *"If you get through to the end of it and everything is green and working and has been dogfooded by actually running it, you can stop. If you run into major issues, you can stop."*

- All 27 invariants in `test_live_state_invariants.py` are passing or proper-classified (PASS / SKIP-out-of-scope / XFAIL-strict-ratchet)
- 8 real bugs fixed end-to-end with dogfood verification
- 7 ratchets locked at current debt counts (regression protected)
- 2 xfail-strict ratchets retained for multi-layer architectural fixes (A17, A20) per operator's "stop on major issues" rule
- delete_after_ingest.md fully surveyed: 7 amendments engaged with invariants, several deferred for not fitting the live-state TDD shape



18-invariant suite (after ratchet additions). Real bugs fixed end-to-end through the dogfood loop during this autonomous run:

| Smell from delete_after_ingest.md | Status | Fix surface |
|---|---|---|
| Topology architecture (A35.1, line 557) | FIXED | review_channel/coordination_state_projection.py - role-based vocab + legacy_topology_label audit field, schema bumped to v2 |
| A19 stale packet hygiene (line 1746) | FIXED | event_reducer_inbox.py + parser_query_arguments.py - --include-stale flag + 24h filter |
| A19 delivery_emitted_at_utc lifecycle (line 1767) | FIXED | event_packet_rows.py:125 - delivery field set for all packet kinds |
| A19 stale_packet_count vs past-expiry warning divergence | FIXED | sync_status_action.py + event_reducer.py - single computation point for both surfaces |
| A30/A35 orphan-guard fake-green (lines 227, 508) | REGRESSION GUARD + 3 live violations cleared | router_python_tests.py entries added for new test files |
| A18 reviewer-mutation capability (line 1561) | REGRESSION GUARD + self-proving rule-logic test | N/A (no live violations) |
| AntiDumbass declared/authority drift (line 1292) | REGRESSION GUARD | N/A (role_source canonical) |
| A20 operator-mandate ack TTL (line 1905) | XFAIL ratchet | Needs G41 check_operator_mandate_obedience.py + agent-loop operator short-circuit |
| A17 body_open_required vs already-observed (line 4859) | XFAIL ratchet | Needs upstream control_decision_packet_inbox.py rework |
| A25 connectivity sweep (line 102) | 5-guard meta-invariant PASSing | N/A (all 5 sub-guards green) |
| Pending-total cross-surface (queue/agent_sync) | REGRESSION GUARD | N/A (530 across all three surfaces) |
| Blocked-agent-must-name-blocker | REGRESSION GUARD | N/A (codex/operator both name their awaiting_packet_id) |
| A4 VoiceTerm leakage (line 4115) | RATCHET at 122 files | walk-down via repo_packs/voiceterm/ extraction |
| A12 FPR proven_passed without node id (line 4365) | RATCHET at 37 receipts | walk-down by adding pytest node ids to legacy FPRs |
| A12 FPR unresolved commit_sha (line 4366) | RATCHET at 2 receipts | walk-down by cleaning the 2 stale references |
| SYSTEM_MAP orphan module references | RATCHET at 14 references | regenerate SYSTEM_MAP via render-surfaces or fix refs |
| Active plan sync (CLAUDE.md onboarding rule) | FIXED + REGRESSION GUARD | added live_state_semantic_tdd_plan.md row to dev/active/INDEX.md |
| Blocked-loop-state must name top_blocker (silent block) | FIXED end-to-end | agent_loop_decision_builder.py - fallback to required_action when ctx.top_blocker is inactive |
| FPR commit_sha unresolved ratchet (A12 line 4366) | RATCHET at 2 | walk-down via cleaning stale shas |
| review_state.json projection freshness | RATCHET at 48h | refresh via develop launch or sync-status without DEVCTL_NO_ARTIFACT_WRITES |
| Gate-block-source race-safe self-check | refactored to read gate first | eliminates flake on suite runs with ledger updates in flight |
| A12 plan_rows applied status missing applied_at_utc (line 4380) | RATCHET at 30 rows | walk-down by backfilling timestamps |
| A12 plan_rows applied missing commit_anchor_ref (line 4386) | RATCHET at 10 rows | walk-down by linking commits |
| Contract registry owner_path validity | REGRESSION GUARD | N/A (all 248 paths resolve) |

## Open questions for the operator before execution

1. Are the Phase A reverts (G59, absorb_output, A24/A27/A28/A29/A36) all clear to proceed, conditional only on `git status` verifying they're session-introduced?
2. Is the strict B1→B2→B3→B4 sequencing acceptable (no check-router wiring until green), or do you want a "tracked but skipped" pytest marker so the failing tests are visible in CI even while red?
3. For Phase C's adapter: is modifying the existing `ground-truth-probe --record` command acceptable, or should we add a new flag like `--pytest-target` so the existing semantics stay untouched and only the new opt-in path inspects pytest output?
