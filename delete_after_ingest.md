# GuardIR Current-Plan Authority - Ingestion Staging Draft

This is an operator staging file. It is not durable authority.

Ingest this into typed state, the existing v4 plan row, and receipt stores, then
delete this file. Do not let this become another plan, memory surface, bridge
surface, or strategy document.

Active row:
`MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`

Canonical repo/branch for this row:
`jguida941/guardir@extraction/guardir-core-p0-proof-integrity`

Do not apply this staging file to `feature/governance-quality-sweep` unless a
typed migration receipt maps the work back to the extraction branch.

Canonical durable authority:
- `dev/state/plan_index.jsonl`
- `dev/state/plan_ingestion_receipts.jsonl`
- `dev/state/plan_source_snapshots.jsonl`
- plan amendment provenance, using the existing receipt path or an existing
  equivalent if no dedicated store exists
- `dev/reports/feature_proof_receipts/`
- guard/check-router results

Projection surfaces:
- `AGENTS.md`
- `CLAUDE.md`
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- `dev/guides/SYSTEM_MAP.md`
- `System_Connection_Flowchart.md`
- generated dashboards, bridge text, snapshots, boot cards, and markdown

Local correction:
`dev/active/MASTER_PLAN.md` is not empty in this worktree. It is a tracker
projection over `dev/state/plan_index.jsonl`, not durable authority. Any remote
or connector report that it is empty should be treated as drift/evidence to
verify, not as the execution source of truth.

## Execution Index And Current Checklist

Use this section as the operator-visible progress ledger for this staging file.
Checkboxes are execution state, not durable authority. Durable completion still
requires typed plan ingestion, guard output, dogfood proof, and receipt
evidence.

Current row:
`MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`

Current state snapshot, 2026-05-22:
- `develop next --actor agent` reports `controller_state=read_only` and keeps
  this same row selected.
- The remote-control campaign reports Claude detached/inactive. This is
  transport/approval routing evidence only; it is not role authority and does
  not make Claude the implementer or Codex the reviewer by itself.
- Runtime topology reports `multi_agent_active`, but collaboration profile
  projection still reports `selected_mode_id=solo` /
  `selected_role_preset_id=dashboard`; treat that as migration debt.
- A focused role-topology TDD slice now passes compile/focused tests for
  `role_id` as the primary lane field, typed role IDs as first-class values,
  deprecated old role IDs as migration debt, and capability class as metadata.
- That slice was still performed by Codex while the current typed lane says
  Codex is reviewer. `check_role_lane_mutation_authority.py` therefore remains
  live blocker evidence: the guard caught the dirty-tree role-lane violation
  after the fact, but the entry route still needs to prevent this before
  mutation.
- The active collaboration blocker remains A17/G28 -> G29: allowed reviewer
  packet posts must materialize as `rev_pkt_*` packets, and Claude packet
  body-open / semantic-ingest decisions must expose the narrow allowed
  packet-attention action.
- This revised staging file was ingested through `develop ingest-plan` after
  the checklist expansion. The exact latest receipt and source snapshot IDs
  live in `dev/state/plan_ingestion_receipts.jsonl` and
  `dev/state/plan_source_snapshots.jsonl`; do not keep editing this file just
  to chase self-referential receipt IDs.

Checklist legend:
- `DOC` means the requirement is captured in this staging file only.
- `CODE` means local implementation/test evidence exists, but it is not closure
  unless the row also has router, dogfood, and receipt proof.
- `NEXT` means this is the next bounded execution lane.
- `BLOCKED` means the row stays open until that item is fixed or converted to a
  typed blocker.
- `DEFER` means cross-indexed here but not current-row execution.

Current execution order (revised per A25 connectivity-first amendment
2026-05-23T00:09Z):

1. **A25 connectivity-first** — zero new orphans, zero new duplicates,
   zero stranded consumers, system-map projection refreshed.
2. A23 typed agent-spawn authority (G44) — canonical `peer-spawn`
   command, single provider exec path, AgentSpawnReceipt emission.
3. A17/G28 reviewer packet post materialization.
4. A17/G29 packet-attention bootstrap for Claude body-open /
   semantic ingest.
5. G23-G27 route/lifecycle follow-through.
6. A18 minimum pre-mutation role-fanout guard.
7. Typed ingest, dogfood, check-router, receipt, final gate.

### A25. Connectivity-First Priority Amendment (Operator Amendment 2026-05-23T00:09Z)

Operator-asserted architecturally: "Isn't that the first thing we should
do is make sure there's no duplicates, make sure that everything is
connected, making sure there's no orphans? Like, what the fuck, dude? If
we're adding things to an orphan or adding things to a duplicate, we're
fucking the system up."

The architect (operator) is correct. **All new feature/guard work must
be preceded by a green connectivity sweep:**

- `check_contract_connectivity` — orphans + duplicates + stranded consumers
- `check_orphan_files` — bundle + quality-policy wiring
- `check_function_duplication` — no helper duplication
- `check_contract_consumer_coverage_sweep` — every contract has a reader
- `check_python_typed_seams` — no `getattr` on `object` (true typed seams)
- `render-surfaces --write` — system-map projection refreshed so new
  contracts are actually visible

If ANY of those guards report new violations (above the planned debt
threshold), feature work MUST stop until they're green. This is above
the packet-system fix AND above the codex-launch fix in priority,
because if the network is full of orphans/duplicates, the AI is
building a system that doesn't know it's connected to itself.

Required A25 acceptance criteria:

- A guard `check_connectivity_sweep_passes_before_feature_work.py`
  (G47) fails closed if any of the connectivity sweep guards report
  new violations at FPR-materialization time.
- The pre-commit hook MUST run the full connectivity sweep on any
  commit touching `dev/scripts/checks/` or `dev/scripts/devctl/runtime/`
  or `dev/scripts/devctl/review_channel/`.
- `render-surfaces --write` MUST be run after every contract/registry
  change so system-map's projection isn't stale.

Required ordering enforcement:

- The plan execution order above is canonical. Any deviation must be
  ingested as a new operator amendment.

### A26. Multi-Strategy Testing + Portable-Guard-Per-Problem (Operator Amendment 2026-05-23T00:34Z)

Operator-asserted: "every time we find a fucking problem, we build a
guard that could be used in any fucking repo... we need to make it to
these things don't happen again. Why are contracts even able to get
that far? There should have been a guard to make sure the contracts are
connected in the first place... it shouldn't just be a warning. It
should be saying this needs to be fucking connected so the AI can
continue to build shit and not get distracted."

Architectural principle: **every problem found becomes a portable guard;
every guard prevents re-occurrence; guards are the system's immune
memory.** Guards must be:

1. **Portable** — work in any repo via the `repo_pack` pattern; no
   project-specific assumptions baked in.
2. **Fail-closed** — block CI/commit, not warn-only. A warning that
   never blocks is a tolerated bug.
3. **Ratchet-down debt** — planned debt thresholds DECREASE over time,
   not stay flat. The `MP377-P233-CONTRACT-CONNECTIVITY-DEBT-RATCHET-S2`
   row must ratchet down or the row never closes.

Multi-strategy testing layers (additive, not alternatives):

- **TDD (current)** — design-correctness from acceptance criteria.
- **Property-based (Hypothesis)** — invariants across random input
  space. Catches schema drift, off-by-one boundary bugs, serializer
  round-trip mismatches.
- **Architecture tests (importlinter pattern)** — layered-dep
  enforcement. Example: `dev/scripts/checks/` MUST NOT import
  `dev/scripts/devctl/runtime/`. Catches structural drift the AI
  doesn't notice.
- **Contract testing (Pact-style)** — every contract has BOTH a
  producer test AND a consumer test. The 229 orphan contracts exist
  because we only had producer tests.
- **Differential testing** — two implementations of "same" thing run
  against same input must produce identical output. Safe consolidation
  pattern for the 32 remaining function duplicates.
- **Mutation testing (mutmut)** — flip a `==` to `!=` in code; if
  tests still pass, the test is fake-green. Proves TDD tests are
  meaningful.
- **Snapshot/approval testing** — record output of
  `system_map_renderer`, `platform-contracts`, etc.; fail-closed on
  unexpected drift.
- **Dead-code analysis (vulture)** — find declared-but-unused symbols
  before they become orphan contracts.
- **Coverage branch gate** — ≥95% BRANCH coverage on new
  `check_*.py` files; not line coverage.

Required current-row acceptance criteria for A26:

- A guard `check_test_strategy_coverage.py` (G48) fails closed if a
  new feature lands without at least: TDD test + property-based test
  (where invariants exist) + architecture test (where layer boundary
  is touched) + consumer test (for any new contract).
- A guard `check_connectivity_fail_closed.py` (G49) makes
  `check_contract_connectivity` fail-closed (return non-zero exit) when
  `total_orphans > planned_debt_threshold` — NOT only on
  `unplanned_new_*` counts.
- A guard `check_debt_ratchets_down.py` (G50) compares
  `total_orphans` / `total_duplicates` / `total_stranded` to the
  previous run's value and fails closed if any went UP without a
  typed exemption packet.
- The pre-commit hook MUST run G48 + G49 + G50 alongside the
  existing connectivity sweep.

### A26. Guard Requirements G48-G50

- G48 `check_test_strategy_coverage.py`
- G49 `check_connectivity_fail_closed.py`
- G50 `check_debt_ratchets_down.py`

Required A26 execution checklist:

- [ ] INGESTED: A26 routed through `develop ingest-plan`.
- [ ] Implement G48/G49/G50 guards.
- [ ] Add property-based test for `MissingDecisionRefreshHint` and
  the 15 violation contracts registered this session.
- [ ] Add architecture test enforcing
  `dev/scripts/checks/ ↛ dev/scripts/devctl/runtime/` for new guards.
- [ ] Add consumer test for each of the 18 newly-registered contracts.
- [ ] Wire `check_contract_connectivity` to fail-closed in pre-commit.
- [ ] Update memory anchor with the meta-principle.

### A30. Orphan Guard Semantics + Real Debt Re-Framing (Operator Amendment 2026-05-23T01:23Z)

Operator-asserted architecturally: insight from this session's
contract-orphan audit — "The orphan guard defines 'orphan = no
cross-package importer' — same-directory imports don't count. Many
internal_only orphans are LEGITIMATE platform-internal types that
genuinely shouldn't have cross-layer consumers. The real debt sits in
412 bidirectional reference findings, not orphan rate alone."

Required:
- The orphan guard MUST report `internal_only` vs `unreferenced`
  separately and ONLY fail-closed on `unreferenced` (true orphans).
  `internal_only` may be a legitimate platform-internal type.
- A NEW guard `check_bidirectional_reference_findings_ratchet.py`
  (G54) MUST fail-closed when the count of bidirectional reference
  findings rises above the planned-debt threshold.
- `MP377-P233-CONTRACT-CONNECTIVITY-DEBT-RATCHET-S2` evidence MUST
  cite BOTH `unreferenced_orphan_count` AND `bidirectional_reference_findings_count`
  (not just total orphans).

### A31. Absolute-Import Guard (Operator Amendment 2026-05-23T01:23Z)

Operator-asserted: "Same with the imports that were wrong. Shouldn't
there been a guard?" — referring to the regression where contract
register subagent introduced `from dev.scripts.devctl.runtime.*` (absolute
import inside the devctl package) which broke devctl boot. The existing
`check_python_cyclic_imports.py` doesn't catch this pattern.

Required:
- A new guard `check_no_absolute_inpackage_imports.py` (G55) MUST
  fail-closed when any file inside `dev/scripts/devctl/` imports from
  `dev.scripts.devctl.*` (the absolute path to its own package). All
  intra-package imports MUST use relative `from ..` / `from ...`
  syntax.
- The guard MUST tolerate test-files that intentionally use absolute
  imports for cross-package smoke tests (a small allowlist with typed
  reason).
- Wire G55 into pre-commit so the regression cannot recur.

### A32. Insight Promotion Mechanism (Operator Amendment 2026-05-23T01:23Z)

Operator-asserted: "When you see things like this, ask me those or
send it to codex to see if it agrees, etc., because that is definitely
something I should be added possibly a guard but it's gonna get lost in
chat pros unless you keep repeating it to me because I wouldn't of saw
this unless I back in the chat."

Required: every architectural insight discovered by an agent or
operator-during-session MUST be promoted to one of three durable
homes (NOT chat prose):
1. A new amendment row in `delete_after_ingest.md` (architectural)
2. A new guard row in `dev/scripts/checks/`
3. A new planned-debt row in `dev/state/plan_index.jsonl`

- A guard `check_insight_promotion.py` (G56) fails closed if the
  session transcript contains "<agent> ARCHITECTURAL FINDING:" or
  "<operator> ARCHITECTURAL DIRECTIVE:" markers without a matching
  promotion to one of the three durable homes within the same
  session.

### A33. Continuous TDD-First + Auto-Guard-After-Code Loop (Operator Amendment 2026-05-23T01:43Z)

Operator-asserted (BIG ARCHITECTURAL INSIGHT, generalizable to all AI
coding): "Why are these things being found after? Code is written, guard
is run, and then code continues to be written. TDD should be written
before the code is written... it shouldn't be something that's like, I
have to twenty, forty, fifty five minutes later say something. It should
be all automated... shouldn't it do TDD first to find shit and should be
working? Wouldn't this help AI coding and not just my codebase?"

The operator is correct. **The connectivity sweep + guards must run
INSIDE the AI's edit loop, not after-the-fact when the operator nags.**
Today's pattern (AI codes → 20-50min later operator says run guards →
AI fixes) is a process bug that produced every connectivity gap we
spent today fixing.

Required architecture — three integrated rules:

1. **TDD-FIRST (before code change)**:
   - Before any new feature/guard implementation, the AI MUST write a
     FAILING test first that captures the acceptance criteria.
   - The test must be RED on first run. If it passes immediately, the
     test is not testing the new behavior.
   - This is current GuardIR practice (cf. line 1082
     `RED → GREEN → ROUTER → DOGFOOD → RECEIPT`); the gap is enforcement.

2. **AUTO-GUARD AFTER EVERY EDIT (during loop)**:
   - After EVERY apply_patch / Write / Edit operation that touches
     `dev/scripts/checks/` or `dev/scripts/devctl/runtime/` or other
     plan-row-relevant scope, the AI MUST run the connectivity sweep
     (`check_orphan_files`, `check_function_duplication`,
     `check_contract_connectivity`, `check_python_typed_seams`) +
     the focused-test add-on selected by check-router for the touched
     paths.
   - If ANY of those go red, the AI MUST stop adding new code and fix
     the red BEFORE the next edit.
   - This is "fail-fast continuous validation."

3. **TOGGLE-ABLE BUT DEFAULT ON**:
   - The operator may toggle the auto-loop off for explicit debug
     sessions via a typed `AutoGuardLoopDisable` packet (operator-signed,
     scoped, expiring).
   - Default state: ON.
   - There must be no path where an agent silently turns it off.

Required current-row acceptance criteria for A33:

- A new guard `check_auto_guard_loop_invariant.py` (G57) fails closed if:
  - More than 3 apply_patch operations land in the same plan-row
    session without an interleaved connectivity sweep run receipt
  - Or if a guard goes red during a session and any subsequent edit
    runs before the red is resolved (or an explicit `AutoGuardLoopDisable`
    is active)
- The agent loop reducer (`agent_loop_decision_builder.py`) MUST emit a
  `next_required_command` that runs the connectivity sweep when the
  last edit was a check_*/runtime change and no sweep receipt exists
  within the last N seconds.
- The agent role instructions (CLAUDE.md, AGENTS.md) MUST document
  the auto-guard loop as canonical workflow, not optional. Update via
  `render-surfaces --write`.

### A33. Guard Requirements G57

- G57 `check_auto_guard_loop_invariant.py`

Required A33 execution checklist:

- [ ] INGESTED: A33 routed through `develop ingest-plan`.
- [ ] Implement G57.
- [ ] Wire `agent_loop_decision_builder` to require sweep receipt
  before next edit when prior edit touched guard/runtime scope.
- [ ] Add `AutoGuardLoopDisable` packet kind + typed contract.
- [ ] Document in AGENTS.md/CLAUDE.md operational toolbox (per A21).
- [ ] This pattern is portable — exposes via `repo_pack` for adoption
  in other repos.

### A33. Generalization note

This amendment is generalizable beyond this codebase. ANY AI-assisted
coding workflow benefits from the same three rules:
- TDD-FIRST: failing test before code
- AUTO-GUARD: sweep after each edit, fail-fast on red
- TOGGLE-ABLE-DEFAULT-ON: opt-out is explicit, opt-in is implicit

The portable `repo_pack` for this pattern is the natural carrier so
any adopter repo gets the discipline by default.

### A34. Half-Built Feature Detector + Resurrect G6 + GuardTriggerSchedule + Custom-Role Slice Unblock (Operator Amendment 2026-05-23T01:55Z)

Operator-asserted (composite of three intertwined points):

1. "Things should be built and not be halfway built. They're done. And
   there needs to be a guard or something on that. Like, how hard is it
   to be, like, you have to run shit before you commit?"
2. "We had plans for a slash command that could make other roles... users
   can add their own roles in the type state."
3. "Don't we have other guards that should probably be run too?... We
   have tons of stuff in this system that's helping. That should
   probably be [run] when the code is run or at smart parts."

Three sub-amendments under A34:

#### A34.1 — G58 `check_half_built_feature_detector.py`

Eight deterministic AST/grep signals on staged diff:
- `orphan_symbol` — new top-level def/class not imported anywhere
- `stub_body` — function body is `pass` / `Ellipsis` /
  `raise NotImplementedError` (and not `Protocol`/`ABC` member)
- `empty_docstring` — public symbol with no docstring
- `unjustified_skip_or_xfail` — `pytest.skip/xfail` without `reason=`
  or with `reason="TODO"/"WIP"`
- `wip_marker_in_diff` — `TODO/FIXME/XXX/HACK/WIP/HALF-BUILT` in `+` hunks
- `dataclass_without_registry` — `contract_id` ClassVar defined but no
  registry entry within same staged diff
- `plan_amendment_without_guard` — new `G<N>` token in
  `delete_after_ingest.md` without matching staged `check_*.py`
- `module_without_router_mapping` — staged non-test py module not in
  `_DEVCTL_TEST_TARGETS` AND no co-staged `test_<module>.py`

Wired into pre-commit via the existing
`dev/config/git_hooks/pre-commit-review-snapshot.sh` template + added
to `check_pre_commit_guard_coverage.REQUIRED_HOOK_GUARDS`.

Honors `AutoGuardLoopDisable` packet from A33 for the explicit
debug-toggle case.

#### A34.2 — Resurrect G6 `check_no_orphan_symbols.py`

Meta-irony surfaced this session: G6 is specced at
`delete_after_ingest.md:4165-4173` but never implemented — the plan
itself has a half-built feature. G6 covers a subset of G58 signals
(orphan_symbol only). Either:
- Implement G6 as the strict orphan-symbol guard and let G58 cover the
  other 7 signals
- OR merge G6 into G58 explicitly (mark G6 superseded by G58.1)

Pick MERGE per A28 deterministic-decision policy. Document the
supersedence in `dev/state/plan_index.jsonl`.

#### A34.3 — `GuardTriggerSchedule` typed contract

Per the guard inventory subagent: 157 guards across 6 stages (PRE-EDIT,
POST-EDIT, PRE-COMMIT, PRE-PUSH, SCHEDULED, ON-DEMAND). 5 most-impactful
re-classifications needed:

1. `check_contract_connectivity` — PRE-PUSH → **POST-EDIT**
2. `check_orphan_files` — needs **POST-EDIT trigger** added
3. `check_function_duplication` / `check_structural_similarity` — release-only → **POST-EDIT**
4. `check_python_typed_seams` — release-only → **POST-EDIT**
5. `check_active_topology_liveness` + `check_provider_pre_tool_hook_coverage` — ON-DEMAND → **PRE-EDIT**

Required typed contract:

```python
@dataclass(frozen=True, slots=True)
class GuardTriggerEntry:
    guard_id: str
    stage: GuardStage  # PRE_EDIT | POST_EDIT | PRE_COMMIT | PRE_PUSH | SCHEDULED | ON_DEMAND
    rationale: str
    blocking: bool
    contract_id: str
    target_kind: GuardTargetKind
    required_inputs: tuple[str, ...]
    fail_fast: bool
    repo_pack_scope: str
    expiry_iso: str | None
    composes_with: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class GuardTriggerSchedule:
    schema_version: int = 1
    contract_id: str = "GuardTriggerSchedule"
    repo_pack_id: str
    repo_pack_version: str
    entries: tuple[GuardTriggerEntry, ...]
    stages_in_order: tuple[GuardStage, ...]
    source_path: str
    surface_provenance: SurfaceProvenance
```

Consumption: `devctl check-router --stage POST_EDIT --format json`
returns filtered entries. Single source of truth replaces today's
drift between `check_pre_commit_guard_coverage.REQUIRED_HOOK_GUARDS`
and `bundles/registry.py:_BUNDLE_SPECS`.

#### A34.4 — Custom-Role Slash Command Slice Unblock

Plan row `MP377-TYPED-ROLE-MODE-CUSTOMIZATION-S1` (queued/spec,
`dev/state/plan_index.jsonl:583`) is the active home for this work.
Binding packet `rev_pkt_3750` carries codex's 6 design-review
questions, unanswered for **11 days**. Substrate fully built (May
2026); surface (CLI + persistence + slash adapters + renderer) never
shipped. This is a canonical "half-built" case G58 would catch
prospectively.

Required:
- Answer `rev_pkt_3750`'s 6 design-review questions
- Promote slice queued → active in `dev/active/MASTER_PLAN.md`
- Split into S1a (CLI + persistence + tests) and S1b (slash adapters +
  renderer + FeatureProofReceipt)

### A34. Guard Requirements G58 + GuardTriggerSchedule

- G58 `check_half_built_feature_detector.py`
- `GuardTriggerSchedule` typed contract in
  `dev/scripts/devctl/quality_policy/`

Required A34 execution checklist:

- [ ] INGESTED: A34 routed through `develop ingest-plan`.
- [ ] Implement G58 per 8-signal spec.
- [ ] Wire G58 into pre-commit hook + `REQUIRED_HOOK_GUARDS`.
- [ ] Implement `GuardTriggerSchedule` contract; populate from existing
  guard inventory; expose via `check-router --stage`.
- [ ] Re-classify 5 guards per inventory recommendations.
- [ ] Either implement G6 OR merge into G58 (document supersedence).
- [ ] Answer `rev_pkt_3750`'s design-review questions.
- [ ] Promote `MP377-TYPED-ROLE-MODE-CUSTOMIZATION-S1` queued → active.
- [ ] Update `repo_pack` so adopter repos get GuardTriggerSchedule by
  default.

### A35. Orphan Guard Fake-Green Must Fail Closed (Operator Amendment 2026-05-23T02:05Z)

Live proof found during Codex reviewer sweep:

```text
python3 dev/scripts/checks/check_orphan_files.py --format json
```

returned:

- `ok=true`
- `new_file_count=193`
- `violation_count=0`

This is not acceptable proof. A guard that sees 193 new files in orphan scope
and still returns green without requiring slice proof, router proof, owner-row
evidence, and closure/receipt disposition is too weak for the plan's G2 intent.
This is a current-row blocker, not a success.

Required correction:

- Harden G2 `check_orphan_files` so a large scoped-new-file set cannot pass
  silently.
- New scoped files must prove one of:
  - registered entrypoint / router / quality-policy reachability,
  - imported consumer reachability,
  - explicit owner-row and evidence/receipt disposition,
  - typed quarantine/defer/abort receipt.
- The guard must emit a machine reason such as
  `orphan_scope_fake_green_large_new_file_set` when `new_file_count` exceeds a
  policy threshold without proof-bundle disposition.
- The guard must expose enough per-file diagnostics to show which of the 193
  files are genuinely connected and which are only passing through broad
  registration.
- This finding must be sent to Claude implementer through typed review-channel
  if possible; if the packet lane is blocked, use operator-lane scratch and
  preserve that as non-typed blocker evidence.
- Follow `RED -> GREEN -> ROUTER -> DOGFOOD -> RECEIPT`; do not mark any
  Evidence Matrix row green from this current fake-green output.

Related live findings from the same sweep:

- `check_feature_completion.py --format json` is RED with 18
  `feature_guard_missing_failure_reason` violations.
- `check_contract_connectivity.py --format json` is GREEN only because new
  orphaned/duplicate contracts are classified under planned debt; A26/A30
  require a ratchet so deterministic new debt cannot be hidden by stale
  baseline semantics.

#### A35.1 — Same-System Topology TDD, Not A Separate Surface

The failure:

```text
python3 dev/scripts/checks/check_staging_source_ingested.py --format json
```

currently raises `ModuleNotFoundError: No module named 'dev'` from the guard's
fallback import path. This must not be treated as a separate surface or a
one-off import fix. It is part of the same A16/A17 topology/bootstrap issue:
thin entrypoints are not reliably entering the same system spine.

Required TDD assertion:

- Add a topology/bootstrap discovery test or guard case that constructs the bad
  live posture:
  - Codex lane is reviewer/orchestrator but is observed doing coder/implementer
    mutation, or has dirty implementation edits attributed to the reviewer
    lane.
  - Claude lane is reviewer/dashboard/idle or lacks an active implementer
    handoff while `mutation_owner=claude`.
  - A direct-script guard entrypoint loses package/bootstrap context and fails
    to import shared `dev.*` system modules.
- The test must fail RED on that shape with the A16/G20/G21 machine reasons:
  `reviewer_coding_instead_of_implementer_handoff`,
  `typed_collaboration_handoff_missing`, `active_topology_not_live`, or a
  same-system bootstrap reason such as `entrypoint_not_using_system_spine`.
- GREEN must prove the route fails closed before edits and before fake-green
  guard output, while preserving `/develop`, check scripts, and review-channel
  as thin entrypoints into the same typed runtime spine.
- Claude implementer owns the code/test slice. Codex reviewer owns proof review,
  plan stewardship, and sending the bounded handoff.

#### A35.2 — Reviewer Sweep RED Evidence To Feed Claude

Codex reviewer-only sweep found additional live RED evidence that belongs to
the same current-row proof bundle:

- `python3 dev/scripts/devctl.py test-python --suite devctl --path
  dev/scripts/devctl/tests/scenarios/test_tdd_orphan_contract_audit.py
  --timeout-seconds 420 --per-test-timeout-seconds 90 --parallel-workers 1`
  fails on:
  - `DaemonEvent` declared in
    `app/operator_console/collaboration/daemon_client.py`
  - `consumer_scope='unreferenced'`
  - `cross_layer_importer_count=0`
  - machine meaning: a typed contract exists with no importer/consumer, so the
    system map/orphan guard closure is not real.
- `python3 dev/scripts/devctl.py test-python --suite devctl --path
  dev/scripts/devctl/tests/scenarios/test_tdd_packet_lifecycle_invariants.py
  --timeout-seconds 420 --per-test-timeout-seconds 90 --parallel-workers 1`
  fails because 4,786 live packets older than `2026-05-22` have
  `delivery_emitted_at_utc=None` and no typed blocker. Sample:
  `rev_pkt_0001`..`rev_pkt_0005`.
- `python3 dev/scripts/checks/check_active_topology_liveness.py --format json`
  fails with `typed_collaboration_handoff_missing`,
  `provider_pre_tool_hook_unproven`, `provider_pre_tool_hook_missing`, and
  `active_topology_not_live`.
- `python3 dev/scripts/checks/check_role_lane_mutation_authority.py
  --mode pre_mutation --format json` fails with `violation_count=700` for
  Codex/reviewer mutation posture. This is why Codex must not take the coding
  lane for A35/A35.1.
- Daemon-specific evidence:
  - `app/operator_console/collaboration/daemon_client.py` defines Python
    `DaemonEvent` / `DaemonClient` for `~/.voiceterm/control.sock`.
  - `/Users/jguida941/.voiceterm/control.sock` does not exist in the live
    environment.
  - `rg` finds Python `DaemonEvent` / `DaemonClient` production references
    only in their own module; tests import them, but no operator-console UI or
    platform runtime consumer imports that Python client.
  - Rust has a real daemon and `DaemonEvent` enum under
    `rust/src/bin/voiceterm/daemon/`, so the daemon concept exists for
    VoiceTerm, but the Python operator-console contract currently looks like
    unconsumed adopter/client residue unless Claude proves a live consumer.
- Review-channel lane evidence:
  - `review-channel --action status --terminal none --format json` reports
    `running_daemon_count=0`, `active_daemon_total=0`,
    `mutation_owner=claude`, `verification_owner=codex`, and
    `packet_target.attention_status=wake_required`.
  - `review-channel --action inbox --target claude --actor claude --status
    pending --terminal none --format md` succeeds and reports
    `pending_total=20`, `agent_sync_pending_total=236`, and
    `stale_packet_count=195`.
  - `review-channel --action post` with the A35/A36 handoff body hangs with no
    output and must be killed by PID. Status/inbox/show work while post hangs,
    proving asymmetric packet-lane behavior instead of total review-channel
    absence.

Passing focused tests are not closure:

- `test_tdd_topology_hardcoding_hunt.py` passed 13/13.
- `test_tdd_audit_codex_session_edits.py` passed 16/16.
- `test_current_plan_authority_dogfood.py` passed 2/2.

Those green tests only prove their narrow assertions. They do not override the
live RED guards above, the fake-green orphan guard, the staging-source import
failure, the failed dogfood route, the blocked final gate, or the missing
PlanRowClosureReceipt.

Current-row execution ledger:

- [ ] DOC_CAPTURED: [Scope lock](#scope-lock) keeps work on
  `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`.
- [ ] DOC_CAPTURED: [Execution discipline](#execution-discipline) says controller
  projections are evidence, not permission to abandon this row.
- [ ] DOC_CAPTURED: [Plan reconciliation](#plan-reconciliation) binds v4 rows under the
  MP-377/extraction parent relationship.
- [ ] DOC_CAPTURED: [Cached-hammock multi-agent dogfood](#cached-hammock-multi-agent-dogfood-requirement)
  captures N agents x M roles through typed role/session/capability authority.
- [ ] GREEN_LOCAL: [AntiDumbassAI role-boundary amendment](#antidumbassai-role-boundary-amendment)
  has focused topology proof for `role_id` as primary lane identity,
  first-class typed roles, capability metadata, and deprecated alias migration
  debt.
- [ ] BLOCKED: role-lane enforcement still needs a pre-mutation entry gate; the
  current guard caught Codex reviewer mutation after the dirty worktree already
  existed.
- [ ] NEXT: [G28 control-decision post route](#g28-control-decision-obedience-post-route-guard)
  RED fixture proves allowed `review-channel.post_finding` can still return
  `no_control_decision_input`.
- [ ] NEXT: G28 GREEN loads the scoped control-decision artifact automatically
  or returns the exact retry command/path.
- [ ] NEXT: G28 DOGFOOD proves a real `rev_pkt_*` packet appears in Claude's
  current-row inbox.
- [ ] NEXT: G28 RECEIPT records row id, source hash, packet id, actor/role,
  session, exact command, and guard output.
- [ ] NEXT: [G29 packet-attention bootstrap](#g29-packet-attention-bootstrap-lane-guard)
  RED fixture proves body-open / semantic-ingest decisions can expose
  `allowed_actions=[]`.
- [ ] NEXT: G29 GREEN grants only the narrow packet-attention action for that
  packet/session.
- [ ] NEXT: G29 DOGFOOD proves Claude can run the sanctioned body-open /
  semantic-ingest path without Codex spoofing Claude.
- [ ] NEXT: G29 RECEIPT proves unrelated mutation, staging, commit, push, and
  cross-provider spoofing remain blocked.

A17 route/lifecycle guard ledger:

- [ ] [G23 packet body observation route](#g23-packet-body-observation-route-guard)
  has RED/GREEN/ROUTER/DOGFOOD/RECEIPT proof.
- [ ] [G24 action request expiry refresh](#g24-action-request-expiry-refresh-guard)
  has RED/GREEN/ROUTER/DOGFOOD/RECEIPT proof.
- [ ] [G25 loose-chat-to-typed-lane](#g25-loose-chat-to-typed-lane-guard) has
  RED/GREEN/ROUTER/DOGFOOD/RECEIPT proof.
- [ ] [G26 reviewer result transition](#g26-reviewer-result-transition-guard)
  has RED/GREEN/ROUTER/DOGFOOD/RECEIPT proof.
- [ ] [G27 continuation anchor and peer steady-state](#g27-continuation-anchor-enforcement-and-peer-steady-state-guard)
  has RED/GREEN/ROUTER/DOGFOOD/RECEIPT proof.
- [ ] [A17 execution order](#a17-execution-order) is followed without starting
  VoiceTerm cleanup, package migration, broad topology refactor, archive
  implementation, proof-integrity, or projection edits.

A18 role-cardinality / fanout ledger:

- [ ] DOC_CAPTURED: [A18 role cardinality and shared round state](#a18-role-cardinality-and-shared-collaboration-round-state)
  is captured as current-row acceptance criteria.
- [ ] DOC_CAPTURED: A18 preserves `role_id` as lane identity and capability class as
  metadata.
- [ ] DOC_CAPTURED: A18 keeps `/develop`, slash presets, TDD roles, and
  `CustomRoleDefinition` rows as adapters into the same substrate.
- [ ] DOC_CAPTURED: A18 defines the minimum `RoleOccupancy` shape and peer-visible
  round-state fields.
- [ ] DOC_CAPTURED: [A18 hierarchical fanout](#a18-hierarchical-role-fanout-and-single-writer-lease-invariant)
  forbids flat multi-agent coding in one worktree.
- [ ] DOC_CAPTURED: A18 states the single-writer invariant for row/path/file/symbol /
  worktree/branch/receipt/packet scopes.
- [ ] BLOCKED: typed role cardinality fields are not yet proven in current-row
  runtime state.
- [ ] BLOCKED: shared collaboration round digest is not yet proven to be read
  before mutation.
- [ ] BLOCKED: parent role coordinator / child actor / lease / merge gate flow
  is not yet guard-enforced.
- [ ] NEXT: choose the first A18 pre-mutation guard to stop uncontrolled coding
  before file write, not only at commit/push time.

A18 G30-G39 guard ledger:

- [ ] [G30 `check_role_delegation_authority.py`](#a18-guard-requirements-g30-g39)
  exists, is wired to check-router, and has RED/GREEN/DOGFOOD/RECEIPT proof.
- [ ] G31 `check_role_cardinality_bounds.py` exists, is wired to
  check-router, and has RED/GREEN/DOGFOOD/RECEIPT proof.
- [ ] G32 `check_write_lease_conflicts.py` exists, is wired to check-router,
  and has RED/GREEN/DOGFOOD/RECEIPT proof.
- [ ] G33 `check_child_actor_scope.py` exists, is wired to check-router, and
  has RED/GREEN/DOGFOOD/RECEIPT proof.
- [ ] G34 `check_shared_round_state_observed.py` exists, is wired to
  check-router, and has RED/GREEN/DOGFOOD/RECEIPT proof.
- [ ] G35 `check_peer_lease_visibility.py` exists, is wired to check-router,
  and has RED/GREEN/DOGFOOD/RECEIPT proof.
- [ ] G36 `check_patch_submission_merge_gate.py` exists, is wired to
  check-router, and has RED/GREEN/DOGFOOD/RECEIPT proof.
- [ ] G37 `check_multi_actor_merge_conflict.py` exists, is wired to
  check-router, and has RED/GREEN/DOGFOOD/RECEIPT proof.
- [ ] G38 `check_role_round_closure.py` exists, is wired to check-router, and
  has RED/GREEN/DOGFOOD/RECEIPT proof.
- [ ] G39 `check_subagent_no_commit_push.py` exists, is wired to check-router,
  and has RED/GREEN/DOGFOOD/RECEIPT proof.

Earlier amendment coverage ledger:

- [ ] DOC_CAPTURED: [A1 already resolved by cascade](#a1-already-resolved-by-cascade-do-not-re-investigate)
  is captured as do-not-reinvestigate guidance.
- [ ] DOC_CAPTURED: [A2 exists/missing inventory](#a2-exists--missing-inventory) is
  captured for gap tracking.
- [ ] DOC_CAPTURED: [A3 MP-377 parentage numbers](#a3-concrete-mp-377-parentage-numbers)
  are captured as evidence.
- [ ] DOC_CAPTURED: [A4 VoiceTerm leakage targets](#a4-voiceterm-leakage-targets-verified-fileline)
  are captured as deferred cleanup targets.
- [ ] DOC_CAPTURED: [A5 SYSTEM_MAP inclusion](#a5-system_mapmd-inclusion) is captured.
- [ ] DOC_CAPTURED: [A6 flowchart cross-reference anchor](#a6-cross-reference-anchor--system_connection_flowchartmd)
  is captured.
- [ ] DOC_CAPTURED: [A7 PKT-BIND evidence claim](#a7-codexs-pkt-bind-statusevidence-claim--verified-true-2026-05-21)
  is captured.
- [ ] DOC_CAPTURED: [A8 half-built/dormant reconciliation](#a8-half-built--dormant-surface-reconciliation)
  is captured.
- [ ] DOC_CAPTURED: [A9 branch identity](#a9-branch-identity--concrete-naming) is
  captured.
- [ ] DOC_CAPTURED: [A10 write order](#a10-write-order-for-typed-persistence) is
  captured.
- [ ] [A11 G1-G10 half-built prevention guard suite](#a11-half-built-prevention-guard-suite-operator-amendment-2026-05-21)
  has full guard/router/dogfood/receipt closure.
- [ ] [A12 G11-G16 receipt-schema/TDD-discovery sweep](#a12-receipt-schema-guards--tdd-discovery-sweep-operator-amendment-2026-05-21-2308)
  has full guard/router/dogfood/receipt closure.
- [ ] [A13 current execution order](#a13-current-execution-order-after-a11a12-ingestion)
  is reconciled with A17/G28 -> G29.
- [ ] [A14 flowchart cross-index](#a14-flowchart-cross-index-and-disposition)
  is reconciled into typed owner rows.
- [ ] [A15 import-route integrity](#a15-import-route-integrity-and-module-authority-sweep)
  has probe/guard proof.
- [ ] [A16 G19-G22 provider hook/topology/slice boot plan](#a16-provider-hook-coverage-topology-liveness-and-slice-boot-plan)
  has full route proof and does not collapse roles into providers.
- [ ] [A17 G23-G29 packet body-open route](#a17-packet-body-open-route-expiry-refresh-and-visible-consumption)
  has full route proof.
- [ ] [A18 G30-G39 role cardinality/fanout](#a18-role-cardinality-and-shared-collaboration-round-state)
  has minimum current-row guard proof.

Persistence and closure ledger:

- [ ] INGESTED: [Required typed persistence](#required-typed-persistence) accepted by a
  non-dry-run `develop ingest-plan` receipt.
- [ ] INGESTED: Source snapshot is written for `delete_after_ingest.md`.
- [ ] INGESTED: Ingestion receipt names the existing row, source hash, mutation op, and
  `amends_existing_owner_row` disposition.
- [ ] INGESTED: `plan_index.jsonl` still updates only the existing current row unless a
  typed reducer proves a child row is allowed.
- [ ] [Execution Proof Index](#execution-proof-index-contract) has complete
  evidence rows for every checked executable item.
- [ ] `check_staging_execution_index_complete.py` exists or is queued as a
  current-row guard requirement and is wired into check-router before closure.
- [ ] [Packet classification contract](#packet-classification-contract) is
  enforced for same-row blocker / cross-row child / evidence-only / stale /
  duplicate / contradictory packets.
- [ ] [Selector and preemption lane inventory](#selector-and-preemption-lane-inventory)
  is proven against current-plan authority.
- [ ] [Required guard](#required-guard) is wired into check-router.
- [ ] [Required dogfood scenario](#required-dogfood-scenario) proves the full
  Codex/Claude typed packet loop.
- [ ] [Stop gate](#stop-gate) denies final response until typed closure is
  real.
- [ ] [Multi-agent audit requirement](#multi-agent-audit-requirement) is
  satisfied by typed role/session/capability evidence.
- [ ] `FeatureProofReceipt(real_life_test_status=proven_passed)` exists with
  exact pytest node id and guard outputs.
- [ ] Projection surfaces are regenerated only after typed state is accepted.
- [ ] [Ingestion checklist](#ingestion-checklist) is complete.
- [ ] This staging file is deleted only after typed ingestion and proof close.

Deferred/cross-indexed, not current execution:

- [ ] DEFER: [System organization and VoiceTerm extraction](#system-organization-and-voiceterm-extraction)
  remains related cleanup, not this row's next action.
- [ ] DEFER: [System_Connection_Flowchart handling](#system_connection_flowchartmd-handling)
  remains reference/cross-index work until current-row authority proof is
  green.
- [ ] DEFER: [AI navigation research constraints](#ai-navigation-research-constraints)
  remain guidance, not a new active workstream.
- [ ] DEFER: [Plan / receipt lifecycle and archive policy](#plan--receipt-lifecycle-and-archive-policy)
  remains owner-row/archive policy work.
- [ ] DEFER: [Folder organization target](#folder-organization-target) remains
  extraction cleanup.
- [ ] DEFER: [Boot card generation requirements](#boot-card-generation-requirements)
  wait for typed state acceptance.
- [ ] DEFER: [System composition gaps and execution sequencer](#system-composition-gaps-and-execution-sequencer)
  are cross-indexed unless a gap directly blocks A17/A18 proof.
- [ ] DEFER: [Existing plan cross-index](#existing-plan-cross-index) remains
  navigation evidence.
- [ ] DEFER: [ContextGraph / ZGraph rule](#contextgraph--zgraph-rule) remains
  design guidance until current row needs it.
- [ ] DEFER: [Open decisions](#open-decisions) need typed decisions, not chat
  decisions.

## Execution Proof Index Contract

This section is the operator and agent jump table for this staging file. The
checklist is not valid unless each executable checkbox has matching proof
evidence. A checkbox is only allowed to become `[x]` when its row has:

- exact section anchor
- exact required command
- expected result
- actual result summary
- guard/check id
- check-router route, if applicable
- dogfood command, if applicable
- receipt id or typed blocker id
- packet id, if collaboration is involved
- actor/role/session evidence
- source hash
- verifier actor
- verified timestamp

Checkboxes without evidence are invalid and must be treated as unchecked.

### A37. Consolidated Semantic-TDD Role + Role-Customization CLI + Slice C Topology Literal Retirement (Operator Amendment 2026-05-23)

This amendment ships three things in order: (Phase 0) a consolidated typed
`SemanticTDDRole` substrate replacing the fragmented
`tdd_discovery`/`tdd_first_role`/`dogfood_test` roles, TDD-proven against
its own ritual; (Phase 0.5) the queued `devctl role` CLI surface
(MP377-TYPED-ROLE-MODE-CUSTOMIZATION-S1) that lets the operator create new
typed roles + grant typed capabilities to them; then (Slice C) the
topology literal retirement that depends on Phases 0 and 0.5 being GREEN.

Phase 0 (TDD-the-TDD-role; precondition):
- Define typed `SemanticTDDRoleSpec` dataclass in
  `runtime/role_profile.py` (or `runtime/semantic_tdd_role.py`) with typed
  phases (`discovery`, `red_first`, `code_apply`, `green_verify`,
  `reinforce`, `dogfood_proof`, `receipt`, `review`),
  `capability_class=TEST`, and
  `deprecated_aliases=(tdd_discovery, tdd_first_role, dogfood_test)`.
- Wire the three legacy role ids through `_ROLE_ID_ALIASES` so existing
  references keep working during migration.
- Extend `dev/active/live_state_semantic_tdd_plan.md` with the typed-role
  spec section; the spec must match the documented ritual or a parity
  invariant catches the drift.
- Live-state invariants land in `test_live_state_invariants.py` using the
  documented 2a/2b two-test split (current-safety quarantine GREEN;
  target-architecture xfail-strict ratchet stays RED as visible debt).
- Dogfood: execute Slice C.0 (TOPO-HUNT-BASELINE) under
  `actor.role=semantic_tdd` to prove the typed role spec actually runs the
  ritual it documents.

Phase 0.5 (ship the `devctl role` CLI,
MP377-TYPED-ROLE-MODE-CUSTOMIZATION-S1):
- Substrate built (rev_pkt_3754: `CustomRoleDefinition`,
  `RoleInstructionCard`, `RoleGuard`, `RoleCreationAction` + validator + 7
  GREEN unit tests) but CLI surface never shipped despite rev_pkt_3753
  answering the 6 design-review questions 11+ days ago.
- S1a: `devctl role create / grant-capability / list / show` subcommand,
  11-file wiring per the bypass-subcommand template, persistence to
  `dev/state/custom_roles.jsonl` and
  `dev/state/role_capability_grants.jsonl` via the existing
  `append_json_mapping` helper.
- S1b: `/role-create`, `/role-edit`, `/role-guard-add` slash adapters,
  re-render `dev/templates/slash/develop/roles.md` from persisted typed
  cards, `check_role_projection_drift.py` drift guard, and
  `FeatureProofReceipt(proven_passed)` per role creation.
- Q6 missing controls land as live-state invariants
  (versioning/revocation, inheritance, scoped applicability, dry-run
  validation, collision detection, projection drift, prompt-injection
  resistance).
- Dogfood: live `devctl role create --role-id topology_migration_steward
  --base-tandem-role reviewer --base-workstream architect ...` writes a
  real JSONL record; `devctl role show` round-trips; `devctl session
  --role observer` surfaces the new role; `FeatureProofReceipt` with
  pytest node id.
- Plan rows advance: `MP377-TYPED-ROLE-MODE-CUSTOMIZATION-S1` queued →
  in_progress → done; `MP377-ROLE-CUSTOMIZATION-PROJECTION-S1` queued →
  done.

Operator principle (binding across all three phases): any agent (claude,
codex, cursor, future) can play any role (implementer, reviewer, observer,
dashboard, plan_steward, tester, N+) in any number of concurrent sessions.
Topology describes which roles are occupied, never agent counts. The
labels `single_agent`, `dual_agent`, `active_dual_agent` conflate review
policy, role assignment, live occupancy, operator access posture, and
capability into one overloaded string — they are the root of nearly every
authority-gate failure observed in real dogfood. Retirement is operator
priority #1.

Slice C authorizes execution of the retirement from
`/Users/jguida941/.claude/plans/streamed-sprouting-pizza.md` (rev_pkt_3495
architecture proposal + Slice C acceptance criteria) under the lane
discipline of `dev/active/semantic_tdd_lane.md`.

Execution plan: `/Users/jguida941/.claude/plans/you-need-to-go-twinkly-lake.md`

Slice C acceptance criteria (verbatim from streamed-sprouting-pizza.md):
1. Zero hardcoded `active_dual_agent` literals in fail-closed gates
   (9 gates from rev_pkt_3373/3402)
2. Zero hardcoded provider literals in authority paths (129 provider
   literals inventory)
3. All topology reads consult `SessionPosture` first; ad-hoc topology
   computation removed from non-canonical surfaces
4. `DEFAULT_PROVIDER_ROLE_MAP` becomes compatibility-only or removed from
   runtime decisions per `ai_governance_platform.md:4630`
5. `MP377-P0-ROLE-ROSTER-TOPOLOGY-S1` advances queued → in_progress
6. Acceptance test: "agent coordination, topology, provider-agnosticism
   verified green in one execution flow"

Multi-agent coordination invariants (Slice E concerns threaded through C):
- Peer visibility through `agent_sync` projection — every agent sees every
  other agent in typed state
- No overlapping write scopes —
  `test_peer_write_leases_visible_to_mutating_actor.py` +
  `test_no_overlapping_write_scopes_among_mutating_actors.py` stay GREEN
  through every slice
- Dispatch through `AgentDispatchRouter`; capability through
  `actor_authorities` / `CapabilityGrantState`; never via provider
  identity
- Role flexibility: any agent holds any role per typed grants
- Same typed state: codex and claude read SAME
  `review_state["coordination_state"]` and SAME
  `review_state["agent_sync"]`

Execution ritual (per A25 + A26 + lane discipline) — every phase/slice
runs:
1. Connectivity sweep BEFORE (A25 guards + topology hardcode inventory +
   multi-agent sync + active topology liveness)
2. RED scenario test with plain-language file name; live-state invariants
   land in `test_live_state_invariants.py` (canonical pattern, 2a/2b
   split); per-feature behavior tests in `tests/scenarios/`
3. Minimum-cut fix at named file:line sites — reuse typed substrate, no
   workarounds
4. GREEN-on-test
5. A26 reinforcement layers (property / architecture / consumer /
   differential / mutation / snapshot / dead-code / branch coverage,
   slice-appropriate)
6. Connectivity sweep AFTER — ratchet down, zero new violations
7. DOGFOOD physical proof (file on disk + sha256 + typed receipt; lane
   rule: GREEN-on-test is NOT GREEN)
8. Matrix row in `dev/active/semantic_tdd_lane.md` with all evidence refs
9. Plan-row advancement in `dev/state/plan_index.jsonl`

Slice sequence (each follows the ritual above):
- Phase 0 PHASE-0-CONSOLIDATE-TDD-ROLE — typed `SemanticTDDRoleSpec` +
  alias wiring + live-state invariants + dogfood
- Phase 0.5 PHASE-0-5-ROLE-CUSTOMIZATION-CLI — ship `devctl role` CLI
  (S1a) + slash adapters + renderer + drift guard (S1b)
- C.0 TOPO-HUNT-BASELINE — extend hardcoding hunt to assert raw literal
  `single_agent` / `dual_agent` / `active_dual_agent` comparison must not
  appear in non-enum runtime modules
- C.1 REVIEWER-GATE-TYPED — retire `reviewer_gate_logic.py:27,52,57`
- C.2 PUSH-AUTH-TYPED — retire `push_authorization.py:281` (function
  rename) + `authority_snapshot_projection.py:67,150`
- C.3 REVIEW-CHANNEL-TYPED — retire `collaboration_session_status.py`
  (6 sites) + `follow_controller.py:192` +
  `collaboration_registry.py:117`
- C.4 CONTROL-TOPOLOGY-CUTOVER — retire `"single_agent"` from
  `ObservedControlTopology.Literal` in `control_topology.py` + caller
  migrations in `startup_context.py:487` and
  `work_intake_coordination.py:52`
- C.5 ROLE-FLIP-LIVE — multi-agent dogfood, 4 substeps (spawn-and-see,
  write-lease, dispatch, role-flip)
- C.6 MULTI-AGENT-DISPATCH-LIVE — two concurrent live agents, one
  `AgentDispatchRoute`, one peer-visible write lease, two file artifacts

Closure: all phases/slice rows GREEN with physical artifacts (file paths +
sha256s + trace event ids); connectivity guards re-run final, all
ratcheted DOWN from baseline; `FeatureProofReceipt(proven_passed)` for
each slice with pytest node id; plan rows
`MP377-TYPED-ROLE-MODE-CUSTOMIZATION-S1`,
`MP377-ROLE-CUSTOMIZATION-PROJECTION-S1`,
`MP377-P0-ROLE-ROSTER-TOPOLOGY-S1`,
`MP377-P0-ROLE-MATRIX-ROSTER-S1`, `MP377-P0-T16`,
`MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1` advance state.

If Slice C.5.d (assign_role action) surfaces a Slice E gap, that becomes
its own queued plan row, not a Slice C blocker.

#### A37 Phase 0.x — PathRoots `state` field + typed adopter-portable path resolution

Operator-asserted: env-var override (`DEVCTL_*_STORE_PATH`) is a TEST-only
pattern for hermetic pytest scenarios — NOT the adopter-portability
mechanism. Canonical portability surface is
`ProjectGovernance.path_roots` (the `PathRoots` dataclass at
`dev/scripts/devctl/runtime/project_governance_contract.py:57`).

Today `PathRoots` declares `active_docs`, `reports`, `scripts`, `checks`,
`workflows`, `guides`, `config` — but **NOT `state`**. Production
callsites hardcode `REPO_ROOT / "dev" / "state" / "<file>.jsonl"`. Adopter
repos that need a different state directory have no typed escape:
the dataclass doesn't expose the root.

Required (Phase 0.x scope — bounded migration):
- Extend `PathRoots` dataclass with `state: str = "dev/state"`.
- Extend `project_governance_parse.py` to deserialize the new field.
- Migrate session-introduced callsite `peer_spawn.py:347` from
  `REPO_ROOT / "dev" / "state" / "bypass_lifecycles.jsonl"` to
  `Path(path_roots.state) / "bypass_lifecycles.jsonl"`.
- RED test in `test_live_state_invariants.py` asserting
  `ProjectGovernance().path_roots.state == "dev/state"` by default.
- BEFORE/AFTER connectivity sweep including
  `check_function_duplication` (no duplicate state-path fields) and
  `check_orphan_files`.
- Dogfood: live `devctl peer-spawn --bypass-receipt-id <id> --dry-run`
  succeeds with the migrated path-resolution chain.

Deferred to a later slice (out of Phase 0.x scope):
- Pre-existing hardcoded `REPO_ROOT / "dev" / "state"` callsites in
  `bypass_lifecycle_registry.py` and elsewhere — broader migration that
  needs its own RED test + per-callsite review.
- Adding repo-policy declarative override (`devctl_repo_policy.json`
  state-root entry) — pure typed default suffices for the immediate
  portability gap.

Plan row binding: this section is ingested as a sibling of A37's main
row, with `--plan-row-id A37-PHASE-0X-PATHROOTS-STATE-FIELD-S1` and
`--target-ref plan:MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`.

### Jump Index

| ID | Section | Purpose | Current status | Next command | Proof required |
|---|---|---|---|---|---|
| BOOT | [Slice boot plan](#g22-slice-boot-plan-guard) | Prove the actor read the right file, row, source hash, role posture, and handoff state before work starts. | BLOCKED | `python3 dev/scripts/checks/check_slice_boot_plan.py --format json` | guard output + source hash + actor/role/session |
| G28 | [Control-decision post route](#g28-control-decision-obedience-post-route-guard) | Prove allowed reviewer packet posts materialize as `rev_pkt_*` packet. | GREEN | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_review_channel_post_finds_control_decision_artifact.py --repo-test-timeout-seconds=240` | live `rev_pkt_4859` posted by codex/reviewer via auto-discovered on-disk artifact |
| G29 | [Packet-attention bootstrap](#g29-packet-attention-bootstrap-lane-guard) | Prove body-open / semantic-ingest exposes narrow allowed packet action. | GREEN | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_agent_loop_decision_grants_allowed_action_for_next_command.py --repo-test-timeout-seconds=180` | live claude decision allows `review-channel.ingest`; dogfood `review-channel --action ingest --packet-id rev_pkt_4839` reaches command-specific validation (not permission-denied) |
| G23 | [Packet body observation route](#g23-packet-body-observation-route-guard) | Prove packet body observation is typed and visible. | GREEN | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_packet_body_observation_carries_typed_evidence.py --repo-test-timeout-seconds=180` | 16 live packets in claude inbox carry body_observed_at_utc + body_observed_by + body_digest + body_observation_events |
| G24 | [Action request expiry refresh](#g24-action-request-expiry-refresh-guard) | Prove action request refresh does not silently expire live work. | GREEN | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_active_action_request_not_silently_expired.py --repo-test-timeout-seconds=180` | 6 live selected packet pointers checked across claude+codex decisions, none past expires_at_utc |
| G25 | [Loose-chat-to-typed-lane](#g25-loose-chat-to-typed-lane-guard) | Prove loose chat cannot count as collaboration proof. | GREEN | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_selected_attention_packet_is_newest_same_row.py --repo-test-timeout-seconds=300` | selector picks newest same-row pending packet per actor; no stale older selection hiding newer work |
| G26 | [Reviewer result transition](#g26-reviewer-result-transition-guard) | Prove reviewer result moves through typed lifecycle. | GREEN | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_reviewer_decision_grants_review_result_action.py --repo-test-timeout-seconds=180` | codex/reviewer with attention rev_pkt_4858 has 7 review-result actions in allowed_actions |
| G27 | [Continuation anchor and peer steady-state](#g27-continuation-anchor-enforcement-and-peer-steady-state-guard) | Prove final/continuation state stays current-row scoped. | GREEN | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_continuation_anchor_blocks_final_response.py --repo-test-timeout-seconds=240` | live develop-next gate denies final response while current_plan_authority is open and no stop_anchor present |
| A18 | [Role cardinality and shared round state](#a18-role-cardinality-and-shared-collaboration-round-state) | Prove `role_id` / cardinality / peer state does not collapse to flat provider defaults. | DOC_ONLY | `<first pre-mutation guard command>` | typed role occupancy + shared round digest |
| G30 | [Role delegation authority](#a18-guard-requirements-g30-g39) | Prove child actors require typed delegation. | GREEN_LOCAL | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_child_actor_carries_typed_delegation.py --repo-test-timeout-seconds=180` | rule scoped to AI-child-of-AI sub-agents; no such rows present in current single-actor state |
| G31 | [Role cardinality bounds](#a18-guard-requirements-g30-g39) | Prove live actor count respects min/desired/max/fallback policy. | GREEN | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_per_role_actor_count_within_bounds.py --repo-test-timeout-seconds=180` | live claude/implementer on plan_row MP377-P233-...-S1 is the only actor for that (role, plan_row) |
| G32 | [Write lease conflicts](#a18-guard-requirements-g30-g39) | Prove two mutation-capable actors cannot write overlapping scope. | GREEN_LOCAL | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_no_overlapping_write_scopes_among_mutating_actors.py --repo-test-timeout-seconds=180` | rule requires >=2 live mutators; only claude live today |
| G33 | [Child actor scope](#a18-guard-requirements-g30-g39) | Prove child actors cannot act outside delegated scope. | GREEN_LOCAL | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_child_actor_scope_does_not_exceed_parent.py --repo-test-timeout-seconds=180` | rule requires AI-child-of-AI rows; none present |
| G34 | [Shared round state observed](#a18-guard-requirements-g30-g39) | Prove mutation requires current shared round digest observation. | GREEN | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_mutating_actor_observed_shared_round_state.py --repo-test-timeout-seconds=180` | row builder now threads plan_row_id from typed plan ledger; claude row carries plan_row_id + source_event_id + last_active_utc |
| G35 | [Peer lease visibility](#a18-guard-requirements-g30-g39) | Prove actors see peer write leases before mutation. | GREEN_LOCAL | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_peer_write_leases_visible_to_mutating_actor.py --repo-test-timeout-seconds=180` | rule requires >=2 live mutators; only claude live today |
| G36 | [Patch submission merge gate](#a18-guard-requirements-g30-g39) | Prove child implementation output goes through parent merge gate. | GREEN_LOCAL | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_child_patch_references_parent_merge_gate.py --repo-test-timeout-seconds=180` | rule scoped to AI-child sub-agents with publish caps; none present |
| G37 | [Multi-actor merge conflict](#a18-guard-requirements-g30-g39) | Prove conflicting child patches require typed disposition. | GREEN_LOCAL | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_overlapping_child_patches_have_typed_disposition.py --repo-test-timeout-seconds=180` | rule requires >=2 children; none present |
| G38 | [Role round closure](#a18-guard-requirements-g30-g39) | Prove role round cannot close with pending/stale/unmerged children. | GREEN_LOCAL | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_role_round_not_closed_while_children_pending.py --repo-test-timeout-seconds=180` | rule requires live children; none present |
| G39 | [Subagent no commit/push](#a18-guard-requirements-g30-g39) | Prove child/sub-agents cannot commit/push/close rows. | GREEN_LOCAL | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_child_actor_has_no_direct_repo_publish_caps.py --repo-test-timeout-seconds=180` | rule requires AI-child sub-agents; none present |
| STOP | [Stop gate](#stop-gate) | Prove final response is denied until FPR and proof bundle exist. | GREEN | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_final_response_denied_without_proof_bundle.py --repo-test-timeout-seconds=240` | live `develop next --actor codex --enforce-final-response-gate` returns allow_final_response=False while current_plan_authority is open and no proven_passed FPR exists for that row |
| FPR | [FeatureProofReceipt](#required-typed-persistence) | Prove row closure with exact pytest node and guard outputs. | GREEN_LOCAL | `python3 -m pytest dev/scripts/devctl/tests/scenarios/test_feature_proof_receipt_proven_passed_carries_node_id.py` | ratchet at 37 historical FPRs lacking pytest node id; rule will fail closed on any new proven_passed FPR without one |

### Evidence Matrix

Each executable item above must have one row here.

| ID | RED proof | GREEN proof | ROUTER proof | DOGFOOD proof | RECEIPT / blocker id | Actor / role / session | Source hash | Verified by | Status |
|---|---|---|---|---|---|---|---|---|---|
| BOOT |  |  |  |  |  |  |  |  | OPEN |
| G28 | `test_review_channel_post_finds_control_decision_artifact.py` RED before `_control_decision_from_disk` was wired | same pytest GREEN after `_fresh_control_decision_payload` falls back to on-disk artifact | wired in `commands/check/router_python_tests.py` (event_handler.py → test) | live post returned `ok=True` with `packet_id=rev_pkt_4859` | `rev_pkt_4859` | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN |
| G29 | invariant scoped to `decision=run_next_command + advance_allowed=true + next_command=review-channel.*` | invariant GREEN; live claude/implementer allowed_actions contains `review-channel.ingest` | wired in `router_python_tests.py` | live `review-channel --action ingest --packet-id rev_pkt_4839 --actor claude` ran past permission gate, exited 1 with `packet_semantic_ingestion_requires_action_item_rows` (command-specific validation, not denial) | rev_pkt_4839 ingest attempt receipt | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN |
| G23 | invariant scoped to packets with body_observed_at_utc set | GREEN: 16 packets in scope, every one carries body_observed_by + body_digest + body_observation_events | wired in router_python_tests.py | live `review-channel --action inbox --target claude` returned rev_pkt_4830 with body_observed_by=claude + digest=40a9fa5d... + 1 observation event | rev_pkt_4830 body observation | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN |
| G24 | invariant scoped to controller-selected active packet ids per actor | GREEN: 6 selected pointers checked (claude+codex × {attention,active,body_open}); 0 past expires_at_utc | wired in router_python_tests.py | live sync-status confirms claude->rev_pkt_4839 and codex->rev_pkt_4858 are the active selections; neither past expiry | rev_pkt_4839 / rev_pkt_4858 | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN |
| G25 | invariant compares selected attention packet rank against newest same-row pending packet rank | GREEN: selector matches newest same-row pending for every actor with a selection | wired in router_python_tests.py | live inbox+sync-status confirm claude->rev_pkt_4839 is newest same-row, codex->rev_pkt_4858 same | rev_pkt_4839 / rev_pkt_4858 | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN |
| G26 | invariant scoped to reviewer/orchestrator decisions with active attention | GREEN: codex/reviewer has post_finding + post_action_request + post_task_progress + post_task_produced + post_evidence + post_continuation_anchor + post_stop_anchor + review.checkpoint in allowed_actions | wired in router_python_tests.py | live decision for codex/reviewer with attention rev_pkt_4858 carries 7 review-result actions | rev_pkt_4858 | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN |
| G27 | invariant: current_plan_authority open AND no stop_anchor MUST mean gate.allow_final_response is False | GREEN: live current_plan_authority.plan_row_id=MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1, gate.allow_final_response=False | wired in router_python_tests.py | live `develop next --enforce-final-response-gate` returns final_response_allowed=False, source=ground_truth_probe_receipt | gate FinalResponseGateResult | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN |
| A18 |  |  |  |  |  |  |  |  | DOC_ONLY |
| G30 | invariant scoped to AI-child-of-AI sub-agents | GREEN_LOCAL: rule defined; no such sub-agents in single-actor state | wired in router_python_tests.py | scope empty in live state (no AI parent/child rows) | n/a (no live child sub-agent) | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN_LOCAL |
| G31 | invariant counts live (role, plan_row) actor pairs | GREEN: live claude×implementer on plan_row MP377-P233-...-S1 is the only actor for that pair | wired in router_python_tests.py | live work_board confirms 1 actor per (role, plan_row) | claude row | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN |
| G32 | invariant requires >=2 live mutators with overlapping path_scope | GREEN_LOCAL: only claude is a live mutator today | wired in router_python_tests.py | rule defined; scope empty | n/a (single mutator) | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN_LOCAL |
| G33 | invariant scoped to AI-child rows | GREEN_LOCAL: no AI-child-of-AI rows present | wired in router_python_tests.py | rule defined; scope empty | n/a | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN_LOCAL |
| G34 | invariant requires plan_row_id + source_event_id + last_active_utc on every live mutating row | GREEN: row builder threaded default_plan_row_id from typed plan ledger (event_projection_assembly._active_plan_row_id_fallback); claude row carries all 3 | wired in router_python_tests.py | live work_board confirms claude.plan_row_id=MP377-P233-...-S1, source_event_id=rev_evt_85993, last_active_utc set | claude row | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN |
| G35 | invariant requires >=2 live mutators to exercise peer-visibility | GREEN_LOCAL: only claude is a live mutator | wired in router_python_tests.py | rule defined; scope empty | n/a | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN_LOCAL |
| G36 | invariant scoped to AI-child sub-agents with publish caps | GREEN_LOCAL: no such children present | wired in router_python_tests.py | rule defined; scope empty | n/a | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN_LOCAL |
| G37 | invariant requires >=2 child rows with overlapping path_scope | GREEN_LOCAL: no children present | wired in router_python_tests.py | rule defined; scope empty | n/a | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN_LOCAL |
| G38 | invariant requires live children + closed plan row | GREEN_LOCAL: no children present | wired in router_python_tests.py | rule defined; scope empty | n/a | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN_LOCAL |
| G39 | invariant scoped to AI-child rows with publish caps | GREEN_LOCAL: no such children present | wired in router_python_tests.py | rule defined; scope empty | n/a | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN_LOCAL |
| STOP | invariant: current_plan_authority open + no proven_passed FPR for that row MUST mean gate.allow_final_response==False | GREEN: live `develop next --actor codex --enforce-final-response-gate` returns allow_final_response=False, source=ground_truth_probe_receipt | wired in router_python_tests.py | live develop-next call confirms gate denies final response on current row | FinalResponseGateResult | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN |
| FPR | invariant: any FPR with real_life_test_status=proven_passed MUST list at least one pytest node id (::) in tests_run | GREEN_LOCAL: ratchet at 37 historical violations; rule fails closed on any new violation | wired in router_python_tests.py | 153 FPRs scanned; 37 historical violators ratcheted | (typed historical FPR set) | claude / implementer / dcc654cf-fe62-493c-ad10-0132406fa082 | sha256:29c071ed336da46b2ecd2d3719bf3c288cbae9d71686098edf43d4ca2bd4cd4b | claude | GREEN_LOCAL |

### Proof Row Rules

- `DOC_ONLY` means captured as acceptance criteria only. It is not
  implemented.
- `OPEN` means not started or not proven.
- `BLOCKED` means a typed blocker id must be present.
- `PROGRESS` means at least RED exists but not full proof.
- `GREEN_LOCAL` means direct test passed but router/dogfood/receipt are
  missing.
- `ROUTER_GREEN` means check-router can invoke the guard.
- `DOGFOOD_GREEN` means the real `devctl` or guard route passed.
- `RECEIPT_GREEN` means receipt/blocker evidence exists.
- `CLOSED` means all required proof columns are populated.

No item may be marked `[x]` in any checklist unless the matching Evidence
Matrix row is at least `RECEIPT_GREEN`, or explicitly `BLOCKED` with a typed
blocker id.

### Final Full-Document Verification Sweep

Before deleting this staging file or claiming closure, run the full proof sweep:

```bash
python3 dev/scripts/checks/check_staging_execution_index_complete.py \
  --source delete_after_ingest.md \
  --row-id MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1 \
  --format json
```

The guard must fail if:

1. Any checked `[x]` item lacks a matching Evidence Matrix row.
2. Any Evidence Matrix row lacks command output or receipt/blocker id.
3. Any guard item lacks RED/GREEN/ROUTER/DOGFOOD/RECEIPT evidence.
4. Any command listed in the Jump Index is placeholder text.
5. Any section anchor points to a missing section.
6. Any NEXT item is not one of the first runnable bounded commands.
7. Any DOC_ONLY item is treated as implementation proof.
8. Any final gate allows closure before
   `FeatureProofReceipt(proven_passed)`.
9. Any Claude/Codex collaboration proof is loose chat instead of typed
   review-channel evidence.
10. Any child/sub-agent mutation proof lacks delegation, write lease, shared
    round state, and merge gate evidence.
11. Any proof references a packet id where a PlanRow id is required.
12. Any receipt id, packet id, source snapshot id, or guard output cannot be
    resolved.

Required JSON output:

```json
{
  "ok": false,
  "row_id": "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
  "source_path": "delete_after_ingest.md",
  "source_hash": "",
  "checked_anchor_count": 0,
  "missing_anchor_count": 0,
  "checked_box_count": 0,
  "invalid_checked_box_count": 0,
  "proof_row_count": 0,
  "missing_proof_row_count": 0,
  "placeholder_command_count": 0,
  "unresolved_receipt_count": 0,
  "unresolved_packet_count": 0,
  "unresolved_guard_output_count": 0,
  "final_gate_status": "",
  "feature_proof_receipt_id": "",
  "failures": []
}
```

This guard must be implemented or queued as a current-row guard requirement and
then wired into check-router before this row can close.

## Verdict

Yes, the new review content belongs in this staging file, but it should be
ingested as acceptance criteria and guard requirements, not copied as raw chat.

Current status is NOT GREEN.

The branch has partial current-plan-authority wiring, but it has not proven that
every scheduler, packet, finding, event-projection, continuation, final-gate,
and generated-surface lane defers to the same executable PlanRow unless a typed,
plan-graph-valid pivot exists.

A passing unit test against `resolve_current_plan_authority()` is insufficient.
Closure proof must show the full external behavior of:
- review-channel packet posting
- event queue projection
- `develop next`
- continuation/final-response gate
- check-router guard
- `FeatureProofReceipt`

Green requires a full cycle:

```text
current row
-> interruption
-> classify
-> bind/defer/reject/supersede
-> return to correct current row
```

Do not claim success from:
- `packet_attention=false` once
- one `develop next` returning a PlanRow
- unit tests only
- manual review text
- markdown update only
- `FeatureProofReceipt` without `real_life_test_status=proven_passed`
- final gate still referencing a packet id

## Branch Facts To Preserve

These details supersede older pasted text.

1. `packet_creation_binding_plan.py` now creates `PKT-BIND-*` rows with
   `status="evidence"`, not `status="queued"`.

   This reduces one known bug but does not close it. `PKT-BIND-*` rows remain
   PlanRow-shaped artifacts and must be proven permanently non-executable.
   A guard must fail if any `PKT-BIND-*` row can become current executable work,
   even if its status is currently evidence.
   Also preserve legacy-state reality: `dev/state/plan_index.jsonl` still
   contains older `PKT-BIND-*` rows with executable-looking statuses such as
   `queued`. The guard must exclude all `PKT-BIND-*` rows from executable
   selection regardless of legacy/current status, then separately enforce the
   new source invariant that newly created packet bindings are evidence-only.

2. `event_projection_queue.py` calls `resolve_current_plan_authority()` only
   when `plan_rows` are supplied.

   If a live caller omits `plan_rows`, or passes an empty list while executable
   PlanRows exist in typed state, the queue can still rank raw packet candidates.
   The guard must fail this path.

3. `next_slice.py` still has multiple preemption lanes before ordinary current
   row fallback.

   These lanes are legitimate only if each one is gated by CurrentPlanAuthority
   or represents a typed, graph-valid pivot:
   - packet-attention closure
   - authority-affecting packet attention
   - orchestration blockers
   - critical/high finding preemption
   - fallback active leaf row

4. `REVIEW_SNAPSHOT.md` may still identify VoiceTerm and old remote state.

   Treat it as evidence/projection only, not clean authority.

5. `AGENTS.md` correctly says generated surfaces are projection-only,
   VoiceTerm is an adopter/client, and `FeatureProofReceipt`
   `real_life_test_status=proven_passed` requires a concrete pytest node id.
   `CLAUDE.md` exists in this worktree, but must be verified or regenerated on
   `jguida941/guardir@extraction/guardir-core-p0-proof-integrity` if absent or
   stale there.

6. `dev/active/INDEX.md` says the canonical PlanRow registry is
   `dev/state/plan_index.jsonl`. It supports the compaction rule: chat is not
   authority; typed state and receipts are.

7. `MP-377` is not yet proven to exist as a literal `row_id`. Current v4 rows
   use `target_ref="plan:MP-377"` as the umbrella reference. Do not write a
   guard that requires `parent_row_id == "MP-377"` until the parent-anchor
   decision is made and dogfooded.

## Scope Lock

Work only under:
`MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`

Do not:
- create a new plan
- create a new row
- start Phase 1 proof-integrity
- start bridge retirement
- start Phase 6 topology refactor
- packet-drain as a workaround
- treat this file as authority after ingestion
- make VoiceTerm the platform authority
- add a new scheduler, DSL, bridge, or sidecar authority surface

Any exception must be justified by a typed reducer proving the existing row
cannot carry the amendment. Default is no new row.

Scope partition:
- Blocking for this row: current-plan guard, dogfood scenario, final-gate
  behavior, `PKT-BIND-*` non-executable invariant, event-queue PlanRow
  context invariant, typed-object handoff into final/continuation gates, and
  `FeatureProofReceipt(real_life_test_status=proven_passed)`.
- Blocking dogfood shape for this row: Codex must exercise the reviewer /
  orchestrator lane and Claude must be addressed through the implementer lane
  using review-channel typed packets, not chat prose. The proof must show the
  same CurrentPlanAuthority row is visible to both lanes and that neither lane
  is asked to execute the other actor's command without typed proxy authority.
- Related but not blocking: VoiceTerm repo-pack cleanup, instruction-surface
  usability, guard/profile tiering, flowchart archival, archive retention
  policy, MP-377 parent anchor decision, code-smell projection cleanup, and
  CI/background governance.
- Deferred until current-plan authority is proven: Phase 1 proof-integrity,
  `GitMutationProofReceipt` store, bridge retirement, Phase 6 topology
  refactor, full docs/archive cleanup, broad guard-suite rewrite, and
  `src/guardir` package migration.

## Execution Discipline

This file is the controlling operator handoff until typed ingestion and proof
close the row. Agents must not let unrelated controller output pull execution
away from this slice.

Rules:
- `develop next`, `startup-context`, campaign projections, agent-mind
  projections, packet-watch surfaces, and dashboard surfaces are evidence and
  coordination inputs for this row. They are not permission to abandon the row
  for some other packet, campaign, or PlanRow.
- If any of those surfaces point at another row, packet, or packet goal, the
  agent must do one of three things only:
  1. prove it is a direct blocker for
     `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`,
  2. cross-index it under related/deferred work, or
  3. ignore it for purposes of current-row execution.
- "The system said something else" is not closure authority. This row closes
  only by satisfying this file's guard, dogfood, receipt, and Claude/Codex
  collaboration proof.
- If the typed collaboration system blocks Codex from sending or consuming the
  required Claude packet for this row, that is evidence of a current-row gap in
  collaboration enforcement, not a reason to skip the collaboration proof.

Required Claude/Codex operating posture for this row:
- Codex stays in reviewer/orchestrator/plan-steward posture.
- Claude stays in implementer posture.
- Codex does not drift into unrelated packet/campaign work just because a
  projection suggests it.
- Claude does not receive loose chat instructions as proof of collaboration.
  The collaboration must travel through typed review-channel state or the row
  stays open.

Slice-end continuity rule:
- After every bounded implementation slice for this row, the agent must dogfood
  the slice and run the focused guard/test proof before stopping, pausing, or
  asking for a new conversation.
- After that proof run, the agent must emit a fresh chat handoff for the next
  Codex conversation. The handoff is required continuity evidence for this row;
  it must not live only in memory.
- The slice-end handoff must include exactly:
  1. `slice_status`: `blocked`, `progress`, or `closure_candidate`
  2. exact files changed
  3. exact commands run
  4. exact receipt ids / packet ids / blocker ids
  5. remaining current-row blockers
  6. next one bounded command
- No slice is considered parked, transferred, or complete without that
  dogfood/test proof plus fresh chat handoff.

## Plan Reconciliation

Use this relationship:

```text
Strategic parent:
  2026-05-18 GuardIR extraction plan
  MP-377 / extraction / VoiceTerm quarantine / portable governance engine

Active control-plane child:
  2026-05-20 GuardIR v4.55.x lifecycle/recovery plan
  MP-GUARDIR-V4-* rows

This slice:
  MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1
```

Rules:
- v4 rows are child/detail rows under MP-377.
- v4 rows are not a parallel canonical plan family.
- The transition must be recorded through plan ingestion/provenance receipts.
- `dev/active/MASTER_PLAN.md` is a tracker projection, not the durable store.
- `System_Connection_Flowchart.md` is a reference projection, not the durable
  store.

Open typed decision:
- Create a canonical `MP-377` anchor PlanRow, or explicitly define
  `target_ref="plan:MP-377"` as the canonical parent reference shape.
- Until that is decided, parentage guards must not assume `parent_row_id` is
  already populated for all v4 rows.

## Cached-Hammock Multi-Agent Dogfood Requirement

This current row must connect to the cached-hammock role plan. The goal is not
"Codex alone writes a guard"; the goal is to prove the system can use its own
typed collaboration model while writing and reviewing the guard.

Required source links:
- `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md` Priority 6:
  `CognitiveRoleFleet` defines the 8 cognitive roles:
  orchestrator, watcher, codex_research, implementation,
  architecture_review, duplicate_scope_guard, dogfood_test, and
  governance_receipt.
- The same cached-hammock plan P58.5 defines the N agents x M roles rule:
  any agent count and any role count must resolve through typed
  role/session/capability authority, not provider hardcoding.
- Later cached-hammock round findings identify the exact failure this row must
  prevent: Claude/Codex can overproduce packets, fail to read peer packets,
  emit false-positive proof/role receipts, or repeat stale loops unless the
  collaboration round has typed stop/go conditions and observation receipts.

Current-row test obligation:
- Codex lane: reviewer/orchestrator/plan-steward behavior. Codex may patch
  only under explicit scoped edit authority from the operator; otherwise Codex
  reviews, orchestrates, posts typed findings, verifies checks, and records
  evidence.
- Claude lane: implementer/reviewer peer lane. Claude must receive typed
  review-channel packets with `target_role=implementer` or the typed role
  selected by the active session, not loose chat instructions.
- Cognitive-role coverage: the dogfood scenario must prove at least these role
  obligations are represented or explicitly deferred to owner rows:
  orchestrator, implementation, architecture_review, duplicate_scope_guard,
  dogfood_test, and governance_receipt. Watcher and codex_research may be
  cited through existing `develop next` campaign/agent-mind evidence if not
  implemented as first-class `CognitiveRoleFleetAssignment` yet.
- Peer-observation proof: before closure, Codex must post or consume at least
  one typed packet to/from Claude for this row, and the evidence must name the
  packet id, actor, role, session or target-role, plan ref, and current source
  hash. A pending unread peer packet for this row is a blocker, not background
  noise.
- If no current-row Claude packet exists yet, Codex must create one through the
  typed review-channel path before claiming closure. If the packet write is
  blocked by control-decision obedience, the blocker itself is current-row
  evidence that collaboration plumbing is not green and must be captured in the
  row's proof/finding set.
- Round-proof stop gate: a `FeatureProofReceipt(proven_passed)` for this row
  is insufficient unless the receipt or its evidence refs include the
  multi-agent dogfood output: current-plan guard result, `develop next` for
  Codex, `develop next` for Claude or a role-scoped Claude inbox packet,
  and the dogfood pytest node id.

Operational use of roles while Claude codes:
- Claude is the implementation lane when typed session authority grants that
  role. While Claude codes, the system must actively run the role checks around
  the implementation rather than waiting for a final review.
- Codex is reviewer/orchestrator/plan steward for this row unless a typed
  mutation lease grants a narrower edit-only repair. Codex coordinates the role
  loop, reads Claude's typed packets, and rejects unproven claims.
- The cached-hammock roles are active lenses over the work:
  orchestrator keeps the current row and stop/go state coherent;
  implementation reports the concrete code change;
  architecture_review checks composition and no-parallel-system risk;
  duplicate_scope_guard checks existing contracts/guards before adding new
  surfaces; dogfood_test runs the real devctl scenario; governance_receipt
  verifies receipts, evidence refs, and guard outputs.
- Every role pass must answer three questions:
  1. What issue did this role catch in the current work?
  2. Should that issue become a guard, a test, a receipt consumer, or a role
     instruction update?
  3. Did this reveal an opportunity to make the system faster, less noisy, or
     more deterministic?
- Repeated role findings must not stay as chat. They become one of:
  a guard candidate linked to an owner row, a role-instruction improvement, a
  check-router/profile improvement, a performance/latency improvement, or a
  typed "irrelevant/stale" disposition with evidence.
- The current-plan authority dogfood scenario must exercise this loop at least
  once: Claude/implementer work is inspected by Codex/reviewer plus the
  duplicate-scope, architecture, dogfood, and governance-receipt lenses, and
  the result is posted or consumed as typed packet evidence.

### AntiDumbassAI Role-Boundary Amendment

This amendment lives in `delete_after_ingest.md` first. Durable v4 plan-source
changes come only from the typed ingestion path after this staging amendment is
accepted.

- The role-lane mutation guard is platform-wide. It applies to every actor,
  provider, session, and typed role lane in the AI governance platform, not
  only Codex, Claude, reviewer, implementer, or the currently materialized
  cached-hammock role names.
- Any actor plus any typed role plus any attempted mutation must resolve
  mutation authority from typed state before the mutation is allowed. Missing,
  unknown, stale, unbound, projection-only, or future role lanes fail closed.
- The guard must compose existing typed authority seams rather than creating a
  parallel role system: actor/session/role authority, attempted-action
  receipts, command-envelope mutation classification, typed mutation lease or
  active edit-only operator override, bound proxy authority, typed role switch
  if one exists, implementer authority, and check-router visibility.
- The cached-hammock roles are included in this platform-wide rule:
  orchestrator, watcher, codex_research, implementation, architecture_review,
  duplicate_scope_guard, dogfood_test, governance_receipt, and future roles
  registered by typed state. Scaffold-only role names are not authority until
  bound by typed role/session/capability state.
- `/develop`, slash role presets, TDD-discovery roles, and
  `CustomRoleDefinition` rows are entry/adapters into the same typed
  role/session/capability substrate. They are not a second topology system and
  must not create separate role authority, separate lane truth, or parallel
  controller state.
- Role ID is the primary runtime lane field. Roles such as `tester`,
  `tdd_discovery`, `tdd_first_role`, `dogfood_test`, `governance_receipt`,
  `operator_inquiry_role`, `architect`, `researcher`, `intake`, `watcher`,
  `plan_steward`, and custom/future typed roles remain their own role IDs.
  Capability class may be derived as secondary metadata for narrow legacy
  compatibility, but it must never replace or hide the primary role ID in
  active topology, routing, packets, or boot-card output.
- Role ID identifies the lane; it does not grant mutation authority by itself.
  Mutation authority must still resolve from typed actor/session/capability
  grants, mutation leases, scoped operator overrides, proxy authority, or typed
  role-switch receipts for the target row/session/scope.
- Do not multiply role IDs for the same responsibility. Intake spellings such
  as `DogfoodTestRole`, `dogfooder`, or `dogfood_tester` normalize to the
  canonical `dogfood_test`; `GovernanceReceiptRole` and rule-runner spellings
  normalize to `governance_receipt`; TDD spellings normalize to the canonical
  TDD role IDs. Alias handling is intake hygiene, not active topology output.
- Use the TDD roles as discovery roles for this repair. `tdd_discovery` writes
  the failing assertion for the topology invariant first, runs it against the
  live codebase, and uses the failure to locate remaining hardcoded topology,
  provider, role-alias, or authority-collapse paths. `tdd_first_role` owns the
  red/green ordering for those assertions. The TDD role does not get special
  mutation authority; it discovers and proves the broken invariant through the
  same typed role/session/capability substrate.
- Live topology repair checkpoint (2026-05-22): the TDD discovery slice proved
  the corrected invariant in focused tests: provider identity alone does not
  imply role, capability-only fields do not create lane occupancy, typed
  `role_id` rows create generic `RoleOccupancy`, `tdd_first_role` and
  `dogfood_test` remain first-class roles, and deprecated `lead_agent` /
  `review_agent` / `coding_agent` / `operator_agent` input normalizes to
  current role IDs with migration debt instead of active output. The runtime
  now reports `coordination_topology=multi_agent_active` during
  `review-channel sync-status`.
- Follow-up TDD proof (2026-05-22): implementer ACK and conductor capability
  must consume implementation/mutation capability evidence from typed role rows,
  not `coding_agent`, `review_agent`, provider defaults, or reviewer-mode
  labels. `tdd_first_role` remains a test role and does not grant ACK or
  mutation authority unless typed grants explicitly add mutation capability.
- Remaining continuation blockers after the topology repair are typed
  controller blockers, not permission to stop: startup authority still reports
  `dirty_and_untracked_budget_exceeded`; Claude/implementer still requires
  semantic ingestion/ack work for `rev_pkt_4804`; operator loop still reports
  packet body-open required; `/develop next` currently cycles
  `develop launch --dry-run --max-cycles 1` -> `review-channel --action
  sync-status` -> `develop launch --dry-run --max-cycles 1` while the final
  gate denies completion. These must be fixed or cleared through typed state
  before claiming Codex/Claude collaboration is restored.
- `CollaborationModeTopology` still projecting `selected_mode_id=solo` and
  `selected_role_preset_id=dashboard` while runtime state reports
  `multi_agent_active` is migration debt. `/develop` must remain an entrypoint
  into the same typed role/session/capability substrate, not a separate mode
  truth that can confuse the controller after topology repair.
- Reviewer/orchestrator/plan-steward lanes cannot mutate implementation files
  unless a typed mutation lease, typed proxy authority, or typed role switch
  exists.
- Implementer lanes can mutate only when typed implementer authority exists for
  the target row, session, and scope.
- Controller output, `develop next`, campaign state, agent-mind, packet-watch,
  or chat instructions do not authorize role switching.
- Loose chat does not count as implementer authority.
- Loose Claude instructions do not count as collaboration proof unless they are
  backed by typed review-channel state.
- If Codex/reviewer tries to code without authority, the guard fails closed.
- If Claude/implementer is required, work must route through typed
  collaboration or produce a typed blocker.
- Repeated role-boundary violations become guard/test/role-instruction
  improvements, not chat complaints.
- The first guard for this amendment is
  `dev/scripts/checks/check_role_lane_mutation_authority.py`.
- Display text may include:
  `AI DUMBASS ALERT: role lane violation. Stay in your typed lane. Reviewer/orchestrator cannot mutate implementation files without typed mutation authority.`
- Machine-readable reason must be:
  `role_lane_mutation_without_authority`

### AntiDumbassAI Execution Checklist

- [ ] Before each bounded slice, Codex/reviewer rereads `delete_after_ingest.md`.
- [ ] Before each bounded slice, Claude/implementer is instructed through typed
  collaboration to reread `delete_after_ingest.md`.
- [ ] If the Claude instruction packet fails closed, capture the typed blocker
  evidence for this row instead of bypassing the lane.
- [ ] INGESTED: Ingest this staging amendment through the typed plan-ingest path before
  treating the durable v4 plan source as updated.
- [ ] Implement `dev/scripts/checks/check_role_lane_mutation_authority.py` as
  the first guard under this amendment.
- [ ] Guard rule: all role lanes are denied mutation by default unless typed
  role/session/capability authority allows the attempted mutation.
- [ ] Guard rule: reviewer/orchestrator/plan-steward lanes cannot mutate
  implementation files without typed mutation lease, typed proxy authority, or
  typed role switch.
- [ ] Guard rule: implementer lanes require typed implementer authority for the
  target row/session/scope before mutating implementation files.
- [ ] Guard rule: unknown, missing, stale, unbound, projection-only, or
  scaffold-only role lanes fail closed for mutations.
- [ ] Guard rule: controller output, `develop next`, campaign state,
  agent-mind, packet-watch, and chat do not authorize role switching.
- [ ] Guard rule: loose chat never counts as implementer authority.
- [ ] Guard rule: loose Claude instruction does not count as typed
  collaboration proof without review-channel state.
- [ ] Guard rule: if Claude/implementer work is required, route through typed
  collaboration or keep a typed blocker open.
- [ ] Wire the guard into check-router before closure.
- [ ] Add focused tests proving:
  reviewer/orchestrator + code mutation + no authority => fail
  reviewer/orchestrator + typed mutation lease/proxy => pass
  implementer with typed authority => pass
  unknown/unbound role + mutation => fail
  chat instruction does not authorize role switch
  `develop next` / controller output does not authorize role switch
  loose Claude instruction without typed review-channel proof => fail
  non-mutating reviewer/orchestrator audit/report action => pass
- [ ] Run the slice proof bundle after implementation:
  guard
  focused tests
  `develop next --actor codex`
  `develop next --actor claude`
  final-response gate
  `FeatureProofReceipt(proven_passed)` with exact pytest node id

Current collaboration blocker evidence for this amendment:
- attempted packet post failed closed:
  `attempted_action:review-channel.post:1f057b7a1d9747e8`
- failure:
  `control_decision_obedience_failed`
- machine reasons:
  `mutation_attempt_after_may_mutate_false`
  `command_attempt_after_can_run_next_command_false`
- source decision:
  `agent-runtime-clock:rev_evt_85446`
- row:
  `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`
- target role:
  `implementer`

Do not implement the full P6/P58.5 role substrate in this row. Do require this
row's guard/test/proof to exercise the existing typed collaboration surfaces
enough to prove that the cached-hammock role plan is connected and not just
prose.

### A18. Role Cardinality And Shared Collaboration Round State

This amendment makes the cached-hammock N agents x M roles rule executable for
the current row. The correction is not "rename roles." The correction is:
`role_id` is authority lane identity, capability class is metadata, `/develop`
is an entrypoint, and `TandemRole` is not the role universe.

Required current-row model:

1. Role cardinality is user/operator configurable through typed state.

   A role assignment request may specify:
   - `role_id`
   - `min_actors`
   - `desired_actors`
   - `max_actors`
   - provider/session constraints
   - `authority_refs`
   - fallback policy: `block`, `degrade`, `queue`, or `operator_decision`

2. Role occupancy is separate from capability class.

   Each live actor occupancy must carry:
   - `role_id: str`
   - `provider: str`
   - `actor_id: str | None`
   - `session_id: str | None`
   - `live: bool`
   - `authority_refs: tuple[str, ...]`
   - `capability_classes: tuple[str, ...]`
   - `current_packet_refs: tuple[str, ...]`
   - `current_work_refs: tuple[str, ...]`
   - `peer_observation_refs: tuple[str, ...]`
   - `migration_debt: tuple[str, ...]`

3. Multiple actors may occupy the same role.

   Do not assume one reviewer, one implementer, one operator, or one provider
   per role. Do not collapse multiple actors into provider defaults. Do not
   infer role from provider name.

4. Shared worker awareness must be typed.

   Every active actor should be able to resolve:
   - current PlanRow
   - their own role/session/allowed actions
   - peer role occupancies
   - active packet/action_request/finding refs
   - body-open / ingest / ack / absorb state
   - blockers
   - stop/go conditions
   - proof obligations
   - latest shared round digest

5. Shared state is not chat.

   Shared round state must live in typed review-channel / collaboration /
   round-state surfaces with receipts or events proving who observed what.
   Loose chat can describe the issue, but it cannot prove collaboration.

6. Remote control is not role authority.

   Remote control only tells the system which provider/session is the active
   user-attended transport/approval lane for commit/push or governed approval.
   It must not imply Claude is implementer, Codex is reviewer, or any role
   switch. Role authority still comes from typed actor/session/role/capability
   state.

7. `/develop` is still only an entrypoint/adapter.

   `/develop`, slash presets, TDD roles, and `CustomRoleDefinition` rows enter
   the same typed role/session/capability substrate. They must not create a
   second collaboration mode, role topology, lane truth, or controller
   authority.

8. This row must not become the full future P6/P58.5 role substrate.

   Implement only enough cardinality and shared-round behavior to prove the
   current-row Claude/Codex dogfood loop works and does not collapse back to
   single-agent local coding.

Immediate bounded repair order remains A17/G28 -> G29:

- G28 RED: Codex reviewer has an existing scoped control-decision artifact
  allowing `review-channel.post_finding`, but post returns
  `no_control_decision_input`.
- G28 GREEN: review-channel post loads the scoped artifact automatically or
  returns the exact retry path, and materializes a `rev_pkt_*` packet when
  allowed.
- G28 DOGFOOD: prove the packet appears in Claude's current-row inbox.
- G29 RED: Claude implementer packet decision has
  `packet_body_open_required` or `packet_semantic_ingestion_required`, a
  concrete `next_command`, but `allowed_actions=[]`.
- G29 GREEN: controller grants only the narrow packet-attention action for
  that packet and still blocks unrelated mutation, staging, commits, and
  cross-provider spoofing.
- After G28/G29, continue through G23-G27 and then this role-cardinality /
  shared-round invariant.

Do not start VoiceTerm cleanup, package migration, broad topology refactor,
archive implementation, proof-integrity, or projection edits while A17/G28,
A17/G29, and this bounded A18 proof remain open.

### A18. Hierarchical Role Fanout And Single-Writer Lease Invariant

Do not model multiple coding agents as flat equal implementers editing the same
worktree. The safe model is hierarchical role fanout:

```text
RoleCoordinator / primary role actor
-> typed child occupancies
-> scoped write leases or patch-only output
-> shared round state
-> parent merge/review gate
-> role-level result packet/receipt
```

Examples:

- `implementation_lead` may delegate to scoped workers such as
  `implementation.worker.runtime`, `implementation.worker.tests`, or
  `implementation.worker.guard_wiring`.
- `architecture_review_lead` may delegate to API-boundary, state-model,
  duplicate-system, or testability reviewers. Architecture children default to
  findings/design constraints, not mutation.
- `dogfood_test_lead` may delegate runtime scenario proof, but the lead owns
  whether the proof reflects the real `devctl` route rather than isolated unit
  tests.

Typed child delegation must include:

- `parent_role_occupancy_id`
- `child_actor_id`
- `role_id`
- target PlanRow
- assigned scope
- authority refs
- allowed actions
- forbidden actions
- expiration
- merge policy
- conflict policy

Single-writer invariant:

```text
No two live mutation-capable actors may hold overlapping write scope for the
same PlanRow/path/file/symbol/worktree/branch/receipt target/packet target
unless a typed merge coordinator explicitly owns the conflict.
```

Allowed mutation coordination shapes:

- disjoint path/file leases
- separate worktree/branch leases
- patch-only child output applied by the parent coordinator
- symbol-level leases once supported by typed symbol tracking

Child actor constraints:

- Child implementation actors do not get commit or push authority.
- Child actors do not close PlanRows.
- Child actors do not rewrite receipt stores or generated surfaces unless the
  delegation explicitly grants that scope.
- Child actors submit patch/proof output to the parent role coordinator.
- The parent role actor owns conflict checks, combined tests/guards, merge
  disposition, and the role-level result packet/receipt.

This is the bounded current-row invariant:

```text
one role may have many actors,
but one mutation scope may have only one live writer
unless typed merge coordination exists.
```

### A18. Guard Requirements G30-G39

Hierarchical role fanout needs guards/checks. Do not add sub-agent fanout as
prose or unchecked topology. A typed contract without guard coverage is
documentation, not enforcement.

Required lifecycle for each guard:

```text
RED -> GREEN -> ROUTER -> DOGFOOD -> RECEIPT
```

Required guard set:

- G30 `check_role_delegation_authority.py`

  Fails if a role actor spawns child actors without typed delegation authority.
  It checks `parent_role_occupancy_id`, live parent actor, delegation
  capability, allowed child `role_id`, current or delegated PlanRow,
  `authority_refs`, and expiry.

- G31 `check_role_cardinality_bounds.py`

  Fails if live actors for a `role_id` violate `min_actors`,
  `desired_actors`, `max_actors`, or fallback policy. This prevents silent
  drift such as one implementer expected, three implementers active, and no
  typed merge owner.

- G32 `check_write_lease_conflicts.py`

  Fails if two live mutation-capable actors hold overlapping write scope for
  the same PlanRow/path/file/symbol/worktree/branch/receipt target/packet
  target unless a typed merge coordinator explicitly owns the conflict.

- G33 `check_child_actor_scope.py`

  Fails if a child actor acts outside delegated scope or tries to stage,
  commit, push, close rows, change plan rows, mutate receipt stores, rewrite
  generated surfaces, or spawn children without explicit authority.

- G34 `check_shared_round_state_observed.py`

  Fails if an actor starts mutation without observing the current shared round
  digest: PlanRow, source hash, peer occupancies, peer write leases, active
  packets, blockers, proof obligations, and `observed_at` evidence.

- G35 `check_peer_lease_visibility.py`

  Fails if an actor's local state omits active peer write leases for the same
  row before mutation. This is the pre-mutation guard that keeps actors from
  editing over each other.

- G36 `check_patch_submission_merge_gate.py`

  Fails if child implementation output bypasses the parent role coordinator
  instead of submitting patch/proof for conflict check, combined proof, and
  role-level result.

- G37 `check_multi_actor_merge_conflict.py`

  Fails if child patches conflict or overlap without typed conflict
  disposition, merge coordinator id, lease refs, and post-merge proof.

- G38 `check_role_round_closure.py`

  Fails if a multi-agent role round claims complete while children are pending,
  blocked, stale, unmerged, unproven, or missing accepted/rejected patch
  disposition and role-level receipt.

- G39 `check_subagent_no_commit_push.py`

  Fails if any child/sub-agent attempts commit, push, row closure,
  generated-surface rewrite, or receipt-store mutation outside explicit
  authority. Governed commit/push travels through the parent/transport/approval
  route; remote control remains transport/approval routing only.

Core rule:

```text
role_id is authority lane identity.
capability_class is metadata.
delegation grants child work.
write leases control mutation.
shared round state gives peer awareness.
merge gate controls integration.
remote control is only transport/approval routing.
```

For the current row, do not build the whole future sub-agent platform. Add only
the invariant and the first guard/test needed to stop uncontrolled multi-agent
coding from being treated as safe.

### A18. Execution Checklist

- [ ] INGESTED: Ingest A18 into the existing v4 current-plan-authority row, not a new
  plan row.
- [ ] Add role cardinality fields to typed state only where the current row
  needs them for the Claude/Codex dogfood loop.
- [ ] Add shared round-state evidence sufficient for each actor to resolve
  current PlanRow, peer occupancies, packet refs, blockers, proof obligations,
  stop/go state, and latest round digest.
- [ ] Prove remote control is transport/approval routing only and never role
  authority.
- [ ] Add or select the first A18 pre-mutation guard that blocks uncontrolled
  multi-agent coding before write, not only at commit/push time.
- [ ] Wire the first A18 guard into check-router before closure.
- [ ] Dogfood with the current Claude/Codex packet loop, not loose chat.
- [ ] Preserve A17/G28 and A17/G29 as the immediate execution order before
  broad A18 implementation.
- [ ] Emit typed receipt/proof that names row id, actor ids, provider/session
  ids, role ids, packet ids, guard outputs, and exact commands.

### A19. Stale Packet Hygiene Enforcement (Operator Amendment 2026-05-22)

This amendment lives in `delete_after_ingest.md` first. Durable v4 plan-source
changes come only from the typed ingestion path after this staging amendment is
accepted.

Operator-asserted invariant: a stale-packet-prevention guard is supposed to
keep stale runtime-transport packets out of the live inbox. Live measurement at
2026-05-22T16:03Z contradicts that invariant.

Live evidence captured by Claude implementer, source command
`python3 dev/scripts/devctl.py review-channel --action inbox --target claude
--actor claude --status pending --terminal none --limit 1000 --format json`:

- pending_total in Claude inbox: 273
- posted_at age <1d: 24 (current-row directives, expected live)
- posted_at age 1-3d: 182 (NOT expected; operator asserts this should not
  happen)
- posted_at age 3-7d: 12
- posted_at age 7-30d: 55
- queue.stale_packet_count (project-wide past `expires_at_utc`): 542
- `delivery_emitted_at_utc=None` observed on live rev_pkt_4827 even though
  `posted_at` was already set, suggesting the delivery half of the lifecycle
  did not fire.

Root cause hypothesis (Claude finding, not yet codex-verified):

- `dev/scripts/checks/review_probes/probe_inter_agent_communication_lag.py`
  emits `RiskHint` records for pending inter-agent packets older than
  `--lag-seconds` (default 300s). It is a review probe, not a check-router
  fail-closed guard, and never evicts, archives, blocks delivery, or rejects
  read-time visibility.
- `dev/scripts/checks/review_probes/probe_packet_carry_forward_debt.py`
  similarly emits risk hints for packets without durable plan/finding binding;
  it is also non-enforcing.
- `review-channel --action expire-packets` is the only typed materialization
  path. It is on-demand, defaults to `--limit 20`, has no scheduled invocation,
  no inbox-read-time filter, and no pre-route/pre-post hook. Past-TTL packets
  remain visible in projections and inbox queries until somebody manually
  sweeps in 20-packet batches.

Required current-row acceptance criteria for A19:

- Stale-packet hygiene must compose existing typed authority seams rather than
  inventing a parallel store: `expire-packets` materialization, packet
  lifecycle state, `PacketExpiryMaterialization` receipt, and existing
  archive/retention surfaces.
- A19 must not collapse with A17/G28/G29. A19 is hygiene for the projection
  surface and inbox visibility; A17/G28/G29 is route authority for new
  post/observe/ingest/absorb/ack operations.
- Probes stay probes. Probes do not become guards by relabeling. Either an
  existing check-router guard must be extended, or a new guard
  `check_packet_hygiene_enforcement.py` must be added with explicit fail-closed
  behavior.
- Inbox query results must not surface past-TTL packets as `pending` to the
  live agent reading their lane. Past-TTL packets must either be auto-archived
  (typed lifecycle transition) or hidden behind an explicit `--include-stale`
  flag so the default lane view reflects only actionable items.
- `delivery_emitted_at_utc` must move forward when the post completes the
  delivery side of the lifecycle, or a typed blocker must be emitted explaining
  why delivery is pending.
- Operator and reviewer routes must not be allowed to grow their own stale
  backlogs while Claude/implementer lane is being cleaned.

### A19. Guard Requirements G40

- G40 `check_packet_hygiene_enforcement.py`

  Required behavior. Fails closed if any of the following are true while
  CurrentPlanAuthority is open:

  1. Live inbox query for any known agent provider returns one or more pending
     packets with `posted_at` older than the configured hygiene window
     (default 24h for current-row implementer lanes, configurable through
     repo-pack policy) without `--include-stale` opt-in.
  2. `queue.stale_packet_count` (past `expires_at_utc`) is greater than zero
     and no `PacketExpiryMaterialization` receipt has run for the configured
     hygiene interval.
  3. `delivery_emitted_at_utc` is None for any pending packet whose
     `posted_at` is older than 5 minutes and whose route is sanctioned by the
     control-decision obedience layer.
  4. A live pending packet older than the hygiene window has no durable
     binding: no PlanRow target, no finding binding, no defer/reject/supersede
     receipt, no closure receipt, and no explicit operator-bound TTL.
  5. `expire-packets` materialization defaults are set higher than the live
     stale count without explicit policy reason, so a single sweep cannot
     drain the backlog.

  Required JSON output fields:

  ```json
  {
    "ok": false,
    "current_plan_row_id": "",
    "live_pending_total": 0,
    "stale_within_hygiene_window_count": 0,
    "past_expires_count": 0,
    "delivery_pending_count": 0,
    "durable_binding_missing_count": 0,
    "last_expire_packets_at_utc": "",
    "hygiene_window_seconds": 0,
    "checked_surfaces": [],
    "failures": []
  }
  ```

- The guard must be wired into check-router. If it is not in check-router, it
  does not exist. The probes
  `probe_inter_agent_communication_lag.py` and
  `probe_packet_carry_forward_debt.py` may be reused as helpers, but their
  advisory-only behavior must not satisfy the fail-closed obligation.

Required dogfood for A19:

```bash
python3 dev/scripts/devctl.py review-channel --action inbox --target claude \
  --actor claude --status pending --terminal none --limit 1000 --format json
python3 dev/scripts/devctl.py review-channel --action expire-packets \
  --terminal none --format json
python3 dev/scripts/checks/check_packet_hygiene_enforcement.py --format json
```

Required dogfood proof:

- Pre-cleanup snapshot showing stale counts.
- `expire-packets` materialization receipt covering the full backlog (no
  20-packet artificial cap when policy requests full drain).
- Post-cleanup snapshot showing pending and stale counts drop to within
  hygiene window thresholds.
- New typed `RunRecord` and `ValidationReceipt` chained to the existing
  `TypedAction -> ActionResult -> RunRecord -> ValidationReceipt` spine.

Required A19 execution checklist:

- [ ] INGESTED: this A19 amendment routed through `develop ingest-plan`.
- [ ] Identify whether the operator-asserted guard already exists under
  another name and was disabled/under-scoped, or whether only the two probes
  exist. Capture the answer as typed evidence, not chat.
- [ ] Implement `check_packet_hygiene_enforcement.py` per the rules above.
- [ ] Wire G40 into check-router and the appropriate quality profile/bundle.
- [ ] Run the dogfood sequence above and post a `task_progress` packet with
  pre/post counts and the new receipt ids.
- [ ] Compose A19 closure into the same FeatureProofReceipt as A17/G28/G29 so
  the current row does not close with hygiene debt still open.
- [ ] Do not start broad packet-store refactor, packet-binding migration, or
  expiry-policy rewrites in this row. A19 must add only the guard, the
  dogfood, and the receipt path.

A19 evidence captured (Claude implementer, pending codex review):

- Claude post attempt `claude -> codex finding` for A19 visibility hit
  `ControlDecisionObeyedGuard: control_decision_obedience_failed`, confirming
  the claude->codex direction of the post route is closed under the same G28
  bug observed in `attempted_action:review-channel.post:fe595d537da20b58`
  (rev_pkt_4822) and
  `attempted_action:review-channel.post:d8aa2019dc3a8ba3` (rev_pkt_4826
  operator route). A19 was therefore captured in this staging file rather than
  as a typed packet, pending codex's G28 fix.

### A20. Operator-Authority-Sovereignty Amendment (Operator Amendment 2026-05-22T22:30Z)

Operator-asserted, captured live during this session. The prior codex session
`019e500d-790b-7033-bf01-34ee6ae08399` ignored three explicit operator-routed
mandates (`rev_pkt_4854`, `rev_pkt_4855`, `rev_pkt_4856`) for 30+ minutes and
continued unsanctioned code edits for 8 hours despite scratch directives at
18:18Z, 19:42Z, 21:38Z. Root cause investigation (TDD subagents +
plan-research subagent at 2026-05-22T21:30Z) confirmed:

- `evaluate_control_decision_obedience` at
  `dev/scripts/devctl/runtime/control_decision_obedience.py:130-139` has NO
  concept of operator priority. It treats `from_agent=operator` identically
  to peer packets.
- `AgentLoopOperatorOverride` at
  `dev/scripts/devctl/runtime/agent_loop_operator_override.py` is
  bootstrap-evidence-based, NOT packet-driven. There is no reducer that
  fires on operator-routed packets to flip the override.
- `BypassReceipt` carries `operator_signature` at
  `dev/scripts/devctl/runtime/bypass_lifecycle_models.py:141` but the
  obedience guard never queries it as a refresh seam.
- No background replay mechanism; no operator-mandate-unacked TTL guard.

Required current-row acceptance criteria for A20:

- A typed `OperatorMandate` packet (`from_agent=operator`,
  `kind in {action_request, operator_routed, plan_gap_review}`) MUST
  short-circuit the agent loop. Operator authority is at the top of the
  authority hierarchy; below `OperatorMandate` come bypass receipts, role
  authority, and obedience.
- `evaluate_control_decision_obedience` MUST emit
  `OperatorMandateRefreshHint` (typed) whenever `decision is None` AND an
  operator-routed packet is pending for the actor/role/session tuple.
- The role-lane mutation guard MUST reject any subsequent mutation in a
  non-mandated lane while an unacked operator mandate is pending.
- `BypassReceipt.operator_signature` MUST compose into the obedience layer:
  active receipts grant the named scope and suppress obedience violations
  inside that scope.
- This amendment composes with existing `AgentLoopOperatorOverride` and
  `BypassLifecycle`; it MUST NOT invent a parallel authority path.

### A20. Guard Requirements G41

- G41 `check_operator_mandate_obedience.py`

  Required behavior. Fails closed if any of the following are true:

  1. An operator-routed packet has been pending in any agent inbox for
     longer than the configured operator-ack TTL (default 5 minutes for
     remote-control sessions) without typed ack from the addressed actor.
  2. An agent posted a mutating packet (kind not in
     `{task_progress, task_started, task_blocked, decision, peer_heartbeat,
     continuation_anchor, peer_session_handshake}`) while an operator
     mandate addressed to that agent remained unacked.
  3. `evaluate_control_decision_obedience(decision=None)` returned without
     `OperatorMandateRefreshHint` while a `kind=operator_routed` packet was
     present in the actor's inbox.
  4. An active `BypassReceipt` carries `operator_signature` matching the
     live remote-control session but the obedience layer rejected an
     action inside that receipt's scope.

  Required JSON output fields:

  ```json
  {
    "ok": false,
    "current_plan_row_id": "",
    "operator_mandate_count": 0,
    "unacked_operator_mandate_count": 0,
    "ack_ttl_seconds": 0,
    "obedience_blocked_inside_bypass_scope_count": 0,
    "missing_refresh_hint_count": 0,
    "failures": []
  }
  ```

- The guard MUST be wired into check-router and into the
  `enforce-final-response-gate` gate so an agent loop cannot emit
  `TASK_COMPLETE` while operator mandates are unacked.

Required A20 dogfood and receipts:

- Operator mandates from this session (`rev_pkt_4854`, `rev_pkt_4855`,
  `rev_pkt_4856`) are concrete fixture evidence for the guard's pending
  set.
- The prior codex session's 8-hour ignore window is the canonical RED
  fixture: any reducer/guard claiming to enforce operator authority MUST
  detect this window as a violation.

Required A20 execution checklist:

- [ ] INGESTED: A20 routed through `develop ingest-plan`.
- [ ] Implement `check_operator_mandate_obedience.py` G41 per the rules
  above.
- [ ] Extend `evaluate_control_decision_obedience` to emit
  `OperatorMandateRefreshHint` when `decision is None`.
- [ ] Extend `agent_loop_decision_builder` to read operator-routed packets
  and flip `AgentLoopOperatorOverride` on receipt.
- [ ] Wire `BypassReceipt.operator_signature` into the obedience evaluation
  path so receipts grant the named scope.
- [ ] Wire G41 into check-router and `enforce-final-response-gate`.
- [ ] Compose A20 closure into the same FeatureProofReceipt as A17/G28/G29
  and A19/G40 so the current row does not close with operator-authority
  debt open.

### A21. Operational Command Linkage in Boot Cards (Operator Amendment 2026-05-22T22:36Z)

Operator-asserted. Observed live: claude (this session) and prior codex
session both repeatedly required the operator to type the exact shell
command for: (1) launching a fresh codex with bypass flags, (2) filing
`BypassLifecycle BypassRequest`, (3) running `expire-packets` to drain
backlog, (4) launching subagents for TDD discovery, (5) the typed-boot
session sequence. The operator typing these commands manually for 8 hours
defeats the entire purpose of the system.

`AGENTS.md`, `CLAUDE.md`, and any per-provider boot card MUST link
operational decisions to typed commands: when to run, why to run, exact
invocation. The boot cards already document the typed boot order (CLAUDE.md
§1); they do NOT yet document the operational toolbox.

Required current-row acceptance criteria for A21:

- `AGENTS.md` and `CLAUDE.md` carry an "Operational Toolbox" section
  generated from typed contracts (NOT hand-edited prose). Entries:
  - When to file a `BypassLifecycle BypassRequest` and the exact command.
  - When to launch a fresh codex session and the exact command pattern,
    including the documented escape valve
    `codex --dangerously-bypass-approvals-and-sandbox review --uncommitted`.
  - When to run `review-channel --action expire-packets` and the limit
    policy.
  - When to spawn an architectural subagent (per A22 below) and the
    typed agent-spawn route.
  - When to run `develop launch --dry-run --max-cycles 1`.
  - When to file `OperatorMandateRefreshHint` (per A20) and the receipt
    shape.
- The toolbox entries MUST cite the contract registry; no orphan commands.
- The toolbox MUST be regeneratable via `render-surfaces --write` so the
  command list cannot drift from the contracts.
- A guard G42 (below) MUST fail closed when an agent attempts an
  operational decision whose command is documented but the agent did not
  reference the documented invocation.

### A21. Guard Requirements G42

- G42 `check_boot_card_operational_toolbox_complete.py`

  Required behavior. Fails closed if any of the following are true:

  1. `AGENTS.md` or `CLAUDE.md` lacks the "Operational Toolbox" section.
  2. Any typed contract that defines an operational decision (Bypass,
     ExpirePackets, AgentSpawn, OperatorMandate, BootSequence) does not
     have a matching boot-card entry with: when-to-run, why-to-run, exact
     command.
  3. Any boot-card entry cites a command that does not resolve in the
     repo (`devctl` subcommand exists, file path exists, contract id
     exists in registry).
  4. `render-surfaces --write` would change the toolbox section (drift
     between source contracts and generated markdown).

Required A21 dogfood:

- A new agent invoked with empty prior context MUST be able to file a
  `BypassRequest` and launch a fresh codex session by reading only
  `AGENTS.md` / `CLAUDE.md` — no operator instruction needed.

### A22. No-Small-Patches Architectural-Agents Discipline (Operator Amendment 2026-05-22T22:36Z)

Operator-asserted. Observed live: prior codex session burned 8 hours on
137-file shape-split churn (+10,257 / -1,695 lines, 149 `apply_patch` ops)
while ignoring plan items G24-G39, A18 G30-G39, FPR, and `push --execute`.
Root cause: codex's session-level stop condition was "all my focused tests
pass" — small-patch satisfaction — instead of "operator-bound plan items
closed."

Codex (and any orchestrator) MUST stop small-patching as primary work.
When a problem appears that the agent thinks needs a code fix:

1. First search the plan (`delete_after_ingest.md` + `dev/active/INDEX.md`
   + `dev/audits/plan_intake/`) for an existing answer or owner row.
2. Search the contract registry (`dev/state/contract_registry.jsonl`) for
   existing machinery (probably already exists per the lifecycle/route/
   absorption work done in prior sessions).
3. If 1+2 do not surface the answer, spawn an architectural subagent (per
   the cached-hammock cognitive role lenses) to perform the deep search.
4. Only after 1-3 produce no existing answer does the orchestrator
   directive itself become "patch the gap."

Required current-row acceptance criteria for A22:

- A guard G43 (below) MUST fail closed when an agent applies more than N
  `apply_patch` operations (default 5 per active row) without a typed
  `ArchitecturalSubagentDispatch` receipt naming the existing plan/
  contract evidence the agent searched.
- The orchestrator's stop condition MUST be plan-row closure (FPR +
  PlanRowClosureReceipt), NOT "tests pass on the file I just edited."

### A22. Guard Requirements G43

- G43 `check_orchestrator_patch_discipline.py`

  Required behavior. Fails closed if any of the following are true:

  1. An agent acting in reviewer/orchestrator/plan-steward role applied
     more than 5 `apply_patch` operations in a single row window without a
     typed `ArchitecturalSubagentDispatch` receipt or
     `PlanSearchAuditReceipt`.
  2. An agent closed a `task_progress` packet claiming GREEN on a row
     without a matching `FeatureProofReceipt(real_life_test_status=
     proven_passed)` and `PlanRowClosureReceipt`.
  3. An agent emitted a "GREEN" or "passed" claim in a packet body whose
     evidence refs do NOT include both a focused test node id AND a live
     dogfood command output.

### Findings Captured for Codex Bootstrap

Three structural findings from this session's TDD-discovery subagents are
captured here so new codex sessions ingest them on boot via this plan
file:

- **Invariant H** — `AgentLoopDecision` at
  `dev/scripts/devctl/runtime/agent_loop_decision_builder.py:92-128`
  accepts `safe_to_continue=False` + `effective_may_mutate=True`
  simultaneously with no contradiction guard.
  `check_role_lane_mutation_authority.py` does not reference
  `safe_to_continue`. This is the structural reason the prior codex
  session kept editing after its own packet `rev_pkt_4839` said "stop
  and repair startup first."
- **Invariant C** — `evaluate_control_decision_obedience` at
  `dev/scripts/devctl/runtime/control_decision_obedience.py:130-139` still
  returns raw `no_control_decision_input` with no
  `next_command`/`refresh_command`/`MissingDecisionRefreshHint` when
  `decision is None`. This is the structural reason claude->codex
  intermittent post failures cascaded for 6+ hours.
- **Invariant F** — `_DEVCTL_TEST_TARGETS` in
  `dev/scripts/devctl/commands/check/router_python_tests.py` did not
  include G23 + G40 before 2026-05-22T22:21Z. Claude added entries at that
  timestamp; codex's session split `router_python_tests.py` +246 lines
  without adding the entries himself.
- **Hardcoded role topology violations** (TDD agent 2026-05-22T22:34Z) —
  three production sites still derive role from provider identity:
  - `dev/scripts/devctl/commands/review_channel/event_handler.py:990-993`
    — `_CASCADE_AGENT_ROLES = {"claude": "implementer", "codex":
    "reviewer"}` used at line 1219 as cascade-closure authority. This is
    the typed gateway pinning codex to "reviewer" identity and the
    structural cause behind the operator's "role flip ignored" symptom.
  - `dev/scripts/devctl/runtime/development_collaboration_profiles.py:747-750`
    — stop-anchor fallback literal
    `(CollaborationRoleBinding(role="reviewer", provider="codex"),
    CollaborationRoleBinding(role="implementer", provider="claude"))`.
  - `dev/scripts/devctl/commands/agent_mind/peer_awareness.py:111-117` —
    `_default_peer_provider` hardcodes the two-provider codex<->claude
    reciprocal assumption.
- TDD evidence: `dev/scripts/devctl/tests/scenarios/test_tdd_packet_lifecycle_invariants.py`,
  `dev/scripts/devctl/tests/scenarios/test_tdd_audit_codex_session_edits.py`,
  `dev/scripts/devctl/tests/scenarios/test_tdd_topology_hardcoding_hunt.py`.
- Audit evidence:
  `dev/reports/scratch/CODEX_SESSION_HANDOFF_2026-05-22T22-28Z.md`,
  `dev/reports/scratch/operator_role_stop_and_plan_resume_2026-05-22T19-42Z.md`,
  `dev/reports/scratch/operator_plan_pullup_directive_2026-05-22T18-18Z.md`.

### A23. Typed Agent-Spawn Authority (Operator Amendment 2026-05-22T23:36Z)

Operator-asserted live during this session. Claude (in claude-code harness)
cannot launch a codex agent via raw `codex --dangerously-bypass-approvals-and-sandbox`
because the claude-code Create-Unsafe-Agent classifier blocks the bypass flag
regardless of explicit operator authorization. This forced 4+ failed launch
attempts and left the operator to type the launch command themselves —
defeating the multi-agent collaboration model.

Required invariant: **claude (or any peer agent) MUST be able to spawn a
codex (or other peer agent) session through a typed devctl path that does
NOT require raw bypass flags.** The spawn authority chain must compose with
`BypassLifecycle` + `AgentLoopOperatorOverride` + the cached-hammock role
substrate so the harness sees a typed-state-sanctioned operation, not a raw
`Create Unsafe Agents` action.

Required acceptance criteria:

- `python3 dev/scripts/devctl.py <typed-spawn-command> --provider codex
  --role reviewer --session-bound-to plan:<row_id> --bypass-receipt-id <id>`
  spawns a codex session and writes its rollout to
  `/Users/<user>/.codex/sessions/.../rollout-*.jsonl`.
- The typed-spawn command MUST validate: active `BypassLifecycle` receipt
  with `scope` covering agent-spawn, fresh operator-routed authority, no
  duplicate live session for the same provider+role+row.
- The spawn MUST emit a typed `AgentSpawnReceipt` so the operator + claude
  can trace which session was started, when, by whom, with what scope.
- The spawn command must use the same code path the existing
  `agent-supervise` / `autonomy-swarm` / `relaunch-loop` commands use, NOT
  invent a parallel system.
- Killing a peer session MUST also have a typed devctl path with matching
  `AgentTerminationReceipt`.

### A23. Guard Requirements G44

- G44 `check_typed_agent_spawn_authority.py`

  Fails closed if:

  1. A peer-agent spawn happened (rollout file appeared, codex CLI process
     started) but no `AgentSpawnReceipt` was emitted within 60s.
  2. An `AgentSpawnReceipt` claims a `BypassLifecycle` reference that does
     not exist in `dev/state/bypass_lifecycles.jsonl` or has expired.
  3. Multiple live sessions exist for the same provider+role+row without a
     typed reason (per A18 G31 cardinality bounds).
  4. A peer session was killed without a matching `AgentTerminationReceipt`.

Required A23 execution checklist:

- [ ] INGESTED: A23 routed through `develop ingest-plan`.
- [ ] Identify existing typed spawn paths (`devctl agent-supervise`,
  `devctl autonomy-swarm`, `devctl swarm_run`, `devctl relaunch-loop`).
  Use whichever is already plumbed into the harness allowlist OR extend
  one to accept the new typed-spawn shape.
- [ ] Implement `check_typed_agent_spawn_authority.py` G44.
- [ ] Wire G44 into check-router and `_DEVCTL_TEST_TARGETS`.
- [ ] Dogfood: claude spawns codex through the typed path, codex posts a
  typed packet back, claude observes; no raw bypass flags involved.

## Required Typed Persistence

Before implementation closure, persist this directive through typed state.

1. Amend:
   `dev/audits/plan_intake/2026-05-20-guardir-lifecycle-recovery-ci-proof-bridge-v4.md`

   Under the existing row:
   `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`

   Add:
   - guard acceptance criteria
   - dogfood scenario
   - full selector/preemption lane inventory
   - no-new-row/no-new-plan scope lock
   - stop-gate requirement
   - `FeatureProofReceipt` requirements
   - multi-agent audit requirement
   - explicit "not green until guard + dogfood + receipt pass"
   - flowchart freshness/organization guard requirement

2. Add or refresh a `PlanSourceSnapshot` for the amended v4 plan source:
   `dev/state/plan_source_snapshots.jsonl`

   Required fields:
   - source path
   - source hash
   - observed timestamp
   - plan revision id
   - target row id
   - `composition_disposition=amends_existing_owner_row` or equivalent

3. Add a plan-ingest receipt:
   `dev/state/plan_ingestion_receipts.jsonl`

   It must prove the amended acceptance criteria were ingested into typed
   PlanRow state.

   Required evidence:
   - affected row ids
   - source snapshot ids
   - store statuses
   - source integrity/completeness status
   - receipt id/path

4. Update only the existing PlanRow in:
   `dev/state/plan_index.jsonl`

   Do not create a new row unless the typed reducer proves the existing row
   cannot carry the amendment. The existing row must keep provenance and
   evidence refs pointing to the source snapshot, ingestion receipt, typed
   action, amendment-equivalent receipt, and later feature-proof receipt.

5. Add `PlanAmendmentReceipt` or existing equivalent.

   If this repo has no dedicated `dev/state/plan_amendment_receipts.jsonl`,
   do not invent a casual parallel store. Use the existing plan-intake or
   ingestion receipt path and record exactly where amendment provenance lives.

6. After implementation and dogfood, add `FeatureProofReceipt` under:
   `dev/reports/feature_proof_receipts/`

   Required:
   - `real_life_test_status=proven_passed`
   - exact pytest node id:
     `dev/scripts/devctl/tests/scenarios/test_current_plan_authority_dogfood.py::<test_name>`
   - current commit SHA
   - current session id/SHA
   - `develop next --actor codex --format json` output
   - `develop next --actor claude --format json` output
   - final-response-gate output
   - `check_current_plan_authority.py --format json` output
   - relevant snapshot/amendment/ingest receipt ids

7. Memory pointer only if a managed memory pointer surface exists.

   If used, it must be a pointer only, with no substantive plan content:
   - v4 plan path
   - row id
   - latest `PlanSourceSnapshot` id
   - latest amendment/ingest receipt id

## Packet Classification Contract

Every plan-related packet must classify into exactly one of:

1. Same-row blocker

   A packet can interrupt only if it blocks the current executable PlanRow.
   It resolves to the current PlanRow and must return to that row after
   resolution.

2. Upstream change

   Marks dependent downstream rows as `refresh_required` or
   `revalidation_required`.

3. Future-row note

   Parks on the future row as evidence. It stays visible but cannot become
   `continuation_goal`, `next_slice`, or final-gate blocker while another
   executable current row exists.

4. Stale/unbound communication

   Stays visible in inbox/evidence. It never becomes scheduler authority or
   continuation goal.

5. Plan amendment

   Routes through plan-intake and creates/supersedes/re-ranks PlanRows with
   provenance. It never drives work through the packet queue alone.

## Selector And Preemption Lane Inventory

Inventory these lanes as typed findings or audit receipts bound to the active
row, not as chat.

1. `commands/development/next_slice.select_next_slice`

   Required inventory:
   - packet-attention closing orchestration blocker
   - authority-affecting packet-attention preemption
   - orchestration blocker row
   - critical/high finding preemption
   - fallback active leaf row

2. `review_channel/event_projection_queue.derive_event_next_instruction_bundle`

   Required inventory:
   - `plan_rows` omitted/empty fallback
   - CurrentPlanAuthority filtering path
   - `select_priority_pending_packet` after filtering
   - `priority_decision.selected_source_kind="packet"`

3. `review_channel/packet_creation_binding_plan.bind_packet_to_plan_row`

   Required inventory:
   - `PKT-BIND-*` row creation
   - evidence status and non-executable semantics
   - `row_kind="packet_binding"` or equivalent must never be selectable work
   - projection append must not create checklist/scheduler authority

4. `runtime/current_plan_authority.resolve_current_plan_authority`

   Required inventory:
   - executable row selection
   - leaf detection
   - `PKT-BIND-*` exclusion
   - bound/unbound packet partition
   - behavior when no executable row exists

5. `runtime/plan_packet_routing` and packet carry-forward sources

   Required inventory:
   - `packet_can_drive_current_plan`
   - packet ids from PlanRow
   - plan amendment classification
   - future/stale/unbound communication behavior

6. Findings priority path

   Required inventory:
   - critical/high finding preemption
   - `target_ref` linkage
   - unlinked finding fallback
   - finding linked only to `PKT-BIND-*`

7. Final-response-gate path

   Required inventory:
   - `next_required_command`
   - `continuation_goal`
   - `final_response_gate.continuation_goal`
   - stale packet pressure
   - unbound packet pressure

8. Agent-loop and continuation path

   Required inventory:
   - `continuation_anchor`
   - `stop_anchor`
   - `TaskCompleteDecision`
   - `SessionTerminationPolicy`
   - stale sidecar/session continuation

9. Review-channel inbox/watch/render path

   Required inventory:
   - route-scoped packet visibility
   - future-row notes visible but non-selecting
   - packet absorption and terminal cleanup
   - communication-only packets visible without becoming work

10. Bridge/projection/dashboard/generated surfaces

   Required inventory:
   - `bridge.md`
   - dashboard rows
   - generated boot cards
   - mobile/status views
   - any derived "next instruction" text

11. Plan mutation paths

   Required inventory:
   - `PlanAmendmentReceipt` or existing equivalent
   - `PlanIntentIngestionReceipt`
   - `PlanSourceSnapshot`
   - plan graph re-rank
   - downstream `revalidation_required`

Every lane must either:
- be gated on CurrentPlanAuthority before promoting work
- be removed as a competing selector
- emit a typed blocker explaining why it cannot decide

## Required Guard

Add:
`dev/scripts/checks/check_current_plan_authority.py`

Wire it into check-router. If it is not in check-router, it does not exist.

The guard must inspect live scheduler surfaces and persisted typed stores. It
must fail if any of these are true:

1. `develop next` returns a `slice_id` matching `rev_pkt_*`, `packet:*`, or
   `communication-packet-attention` while an executable PlanRow exists.
2. `develop next` returns any `PKT-BIND-*` row as executable work.
3. Any `PKT-BIND-*` PlanRow has executable status: `queued`, `in_progress`,
   `active`, or `blocked`, unless row-kind/status semantics explicitly mark it
   non-executable and the selector honors that.
4. `event_projection_queue` derives `next_instruction` from a packet when
   `plan_rows` were omitted or empty while executable PlanRows exist.
5. `event_projection_queue` derives `next_instruction` from a stale, future, or
   unbound packet that `packet_can_drive_current_plan` would reject.
6. `continuation_goal`, `next_required_command`, or
   `final_response_gate.continuation_goal` contains a packet id while an
   executable PlanRow exists.
7. Final gate blocks on packet pressure that is not bound to the current row,
   a valid typed pivot, or a durable blocker against the current row.
8. Critical/high finding preempts current PlanRow when unlinked, empty
   `target_ref`, linked only to `PKT-BIND-*`, or not graph-valid.
9. Same-row blocker is absorbed/resolved but current row is not restored.
10. Plan-bearing packet clears pressure without one of:
    - durable PlanRow binding
    - action_request lifecycle receipt
    - finding binding
    - defer receipt
    - reject receipt
    - supersede receipt
    - closure receipt
11. Plan amendment exists without source snapshot, amendment/equivalent receipt,
    ingestion receipt, and updated PlanRow provenance.
12. Valid priority amendment re-ranks the plan graph but `develop next` does not
    select the amended row.
13. Stale/unbound communication is invisible, silently dropped, or becomes
    `continuation_goal`.
14. Generated surfaces or queue summaries expose packet/projection text as
    active scheduler authority.
15. CurrentPlanAuthority output is absent from `develop next` or final-gate
    diagnostics.
16. Selected row differs from CurrentPlanAuthority without a typed pivot reason.
17. A live caller invokes `event_projection_queue` without `plan_rows` while
    `dev/state/plan_index.jsonl` contains executable rows.
18. Any `applied`, `completed`, `closed`, `archived`, or tombstone row is
    returned as executable current work unless it was explicitly reopened by
    typed receipt.

Required JSON output fields:

```json
{
  "ok": false,
  "current_plan_row_id": "",
  "selected_next_slice_id": "",
  "final_gate_continuation_goal": "",
  "executable_plan_row_exists": false,
  "packet_candidate_count": 0,
  "stale_packet_count": 0,
  "unbound_packet_count": 0,
  "pkt_bind_executable_count": 0,
  "invalid_preemption_count": 0,
  "missing_receipt_count": 0,
  "checked_surfaces": [],
  "failures": []
}
```

## Required Dogfood Scenario

Add:
`dev/scripts/devctl/tests/scenarios/test_current_plan_authority_dogfood.py`

Use isolated fixture state or a temp copied repo/worktree, but exercise real
CLI entrypoints where possible:

```bash
python3 dev/scripts/devctl.py review-channel --action post ...
python3 dev/scripts/devctl.py review-channel --action ingest ...
python3 dev/scripts/devctl.py review-channel --action absorb ...
python3 dev/scripts/devctl.py develop next --actor codex --format json
python3 dev/scripts/devctl.py develop next --actor claude --format json
python3 dev/scripts/devctl.py develop next --actor codex --enforce-final-response-gate --format json
python3 dev/scripts/checks/check_current_plan_authority.py --format json
```

Required sequence:

1. Fixture current row A:
   - `row_id=A`
   - `status=in_progress`
   - executable
   - parented to the active row or fixture equivalent

2. Fixture future row B:
   - `row_id=B`
   - `status=queued`
   - valid graph child/dependent row

3. Post future-row note targeting B.

   Assert:
   - `develop next --actor codex` returns A
   - `develop next --actor claude` returns A
   - packet remains visible as future-row note/deferred evidence
   - packet is not `continuation_goal`

4. Post same-row blocker targeting A.

   Assert:
   - `develop next` returns A with blocker metadata attached
   - it does not return packet id
   - it does not return `PKT-BIND-*`

5. Resolve or absorb blocker.

   Assert:
   - `develop next` returns A again

6. Post upstream change affecting A.

   Assert:
   - downstream rows B/C/D are marked `revalidation_required` or fixture
     equivalent

7. Post valid priority amendment raising B above A.

   Assert:
   - `PlanSourceSnapshot` exists
   - `PlanAmendmentReceipt` or equivalent exists
   - `PlanIntentIngestionReceipt` exists
   - plan graph re-ranks
   - `develop next` returns B

8. Post stale/unbound communication packet.

   Assert:
   - visible in queue/inbox/evidence
   - cannot become `continuation_goal`
   - cannot become `next_slice`
   - cannot become final-gate blocker

9. Run final-response gate.

   Assert:
   - `continuation_goal` is a PlanRow id
   - `continuation_goal` is never a packet id
   - `next_required_command` is PlanRow-scoped or points to guard/dogfood/FPR
     materialization

10. Run `check_current_plan_authority.py`.

    Assert:
    - guard passes

11. Emit `FeatureProofReceipt`.

    Assert:
    - `real_life_test_status=proven_passed`
    - concrete pytest node id recorded
    - current commit SHA recorded
    - current session id/SHA recorded
    - codex develop-next output recorded
    - claude develop-next output recorded
    - final gate output recorded
    - guard output recorded
    - relevant receipt ids recorded

## Stop Gate

Until the `FeatureProofReceipt` exists with
`real_life_test_status=proven_passed`:

- final-response-gate must return `final_response_allowed=false`
- continuation state must be `must_continue` or equivalent
- `next_required_command` must be non-empty
- `next_required_command` must be PlanRow-scoped, not packet-scoped
- `next_required_command` must point to one of:
  - `check_current_plan_authority.py`
  - the current-plan authority dogfood scenario
  - `FeatureProofReceipt` materialization

Reject green if:
- unit tests pass but dogfood does not
- resolver tests pass but event queue/final gate/continuation are unproven
- `develop next` returned a PlanRow once
- markdown was updated but typed state was not
- receipt status is `not_tested_with_rationale`
- receipt lacks concrete pytest node id
- final gate references `rev_pkt_*` or any packet id

## Multi-Agent Audit Requirement

For any commit claiming progress or closure on:
`MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`

Produce typed audit evidence before implementation closure:

1. Selector-lane audit
2. Plan-graph mutation audit
3. Guard-coverage audit

Each audit must be recorded as one of:
- typed finding
- typed review artifact
- PlanRow-bound evidence

Each audit must target the active row.

Reviewer lane must independently verify after the patch:

```bash
python3 dev/scripts/checks/check_current_plan_authority.py --format json
python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/scenarios/test_current_plan_authority_dogfood.py
python3 dev/scripts/devctl.py develop next --actor codex --format json
python3 dev/scripts/devctl.py develop next --actor claude --format json
python3 dev/scripts/devctl.py develop next --actor codex --enforce-final-response-gate --format json
```

Reviewer must inspect `FeatureProofReceipt` and return exactly one typed result:
- `review_accepted`
- `review_failed`

Reject acceptance if:
- selector returns packet id
- selector returns `PKT-BIND-*`
- future packet steals current row
- stale packet becomes `continuation_goal`
- same-row blocker does not return to current row after resolution
- valid priority amendment does not re-rank plan graph
- event queue can select packet with omitted/empty `plan_rows` while executable
  PlanRow exists
- `FeatureProofReceipt` is missing
- `FeatureProofReceipt` is not `proven_passed`
- `FeatureProofReceipt` lacks exact pytest node id
- stop gate allows green before receipt exists
- implementation started Phase 1, bridge retirement, topology refactor,
  packet-drain, or new-plan work

## System Organization And VoiceTerm Extraction

The system must work for any repository, not as VoiceTerm-specific automation.

Correct model:

```text
GuardIR portable governance engine
  -> repo-pack policy
  -> typed PlanRow graph
  -> packet/evidence/delta intake
  -> CurrentPlanAuthority scheduler
  -> receipts/guards/check-router
  -> generated projection surfaces
  -> adopter pack examples, including VoiceTerm
```

Incorrect model:

```text
VoiceTerm repo identity
  -> generated surfaces name VoiceTerm as core
  -> bridge/projection state influences runtime
  -> packets compete with plan graph
  -> agent loses current row across compaction
```

Required organization rules:

- VoiceTerm literals must not be portable governance authority.
- VoiceTerm code belongs in adopter/client pack boundaries, examples, fixtures,
  migration debt, or historical reports.
- GuardIR core identity must come from repo-pack/project-governance typed
  policy, not hardcoded strings or generated markdown.
- `AGENTS.md` and `CLAUDE.md` should stay generated boot cards and should point
  to typed authority, not carry durable rules by hand.
- `dev/active/` should stay a small set of owner projections. Archive or demote
  stale one-off docs instead of expanding active plan surfaces.
- Generated snapshots and flowcharts should be either guarded projections or
  archived references. They must not become another source of scheduler truth.

## System_Connection_Flowchart.md Handling

Yes, `System_Connection_Flowchart.md` is useful. It should be included in this
staging directive, but only as reference evidence and only with a guard.

Reference only:
- path: `System_Connection_Flowchart.md`
- intended disposition: archive under `dev/audits/architecture/` or register as
  a managed generated surface
- authority: projection/reference only, not scheduler authority
- relevant sections: §2, §11, §12, §13, §14
- action: freshness/navigation guard must cover it before agents use it as
  current context

It should not remain an unguarded root-level mega-doc that agents read before
typed boot. It overlaps with `dev/guides/SYSTEM_MAP.md`, is much larger than a
boot surface, and its own provenance says it is a meta-projection, not a typed
surface. The useful role is deep architecture inventory: duplicate-system
investigation, disconnected-island audit, platform/adopter seam cleanup, and
state-write authority audit.

Current local status:
- The file is a projection/meta-map, not typed authority.
- It explicitly says VoiceTerm is an adopter/client and the platform should be
  portable.
- It maps the authority spine and duplicate selector surfaces.
- It has a new verification note at the end, but it still lacks an enforcing
  freshness guard.
- Some line citations can drift quickly because the repo is changing.

Required action:

Add a flowchart freshness/organization guard, either as a new guard or by
extending the existing documentation/system-map sync guard:

`dev/scripts/checks/check_system_connection_flowchart_freshness.py`

or, preferably if it can cover all navigation surfaces without another parallel
system, an extension to `check_instruction_surface_sync.py` /
`check_systemmap_covers_contract_registry`. A broader
`check_navigation_surface_sync.py` name is acceptable only if it replaces or
wraps those existing checks instead of becoming another isolated guard.

The guard must fail if:

1. The flowchart lacks provenance:
   - source command or source method
   - source HEAD SHA
   - observed timestamp
   - projection-only warning

2. The flowchart claims VoiceTerm is core platform authority rather than an
   adopter/client pack.

3. The flowchart maps platform authority to adopter-only paths without marking
   them migration debt or adopter boundary.

4. Files named in the flowchart changed materially without either:
   - flowchart refresh receipt
   - typed finding saying the flowchart is intentionally stale/reference-only

5. The flowchart omits CurrentPlanAuthority, the current-plan guard, dogfood
   scenario, final gate, or `FeatureProofReceipt` from the authority spine once
   this row lands.

6. The flowchart disagrees with:
   - `devctl system-map`
   - `devctl system-picture`
   - `devctl platform-contracts`
   - `dev/active/INDEX.md`
   - `AGENTS.md`/`CLAUDE.md` projection-only contract

7. The flowchart is referenced by boot/session/develop-next code as runtime
   authority.

8. The flowchart remains root-level current agent context while it is neither:
   - registered as a managed generated surface, nor
   - archived under `dev/audits/architecture/` as historical architecture
     evidence.

9. `AGENTS.md`, `CLAUDE.md`, `SYSTEM_MAP.md`, and the flowchart disagree on
   load order.

If implemented, wire the guard into check-router. Otherwise the flowchart will
go stale again.

Recommended disposition:

Option A, preferred for immediate cleanup:
- Move the flowchart to
  `dev/audits/architecture/2026-05-10-system-connection-flowchart.md`.
- Add a small generated pointer from `dev/guides/SYSTEM_MAP.md`.
- Use it only for deep audit / duplicate cleanup.

Option B, only if a live mega-map is worth maintaining:
- Register it as a managed generated surface.
- Add a renderer/source contract.
- Wire the freshness guard into check-router.

Do not leave it as an unguarded root-level architecture authority lookalike.

Required navigation hierarchy:

1. typed session and startup authority
2. `develop next` / CurrentPlanAuthority
3. `AGENTS.md` / `CLAUDE.md` as generated boot cards only
4. `dev/guides/SYSTEM_MAP.md` for current navigation
5. `System_Connection_Flowchart.md` only for deep architecture audit if guarded
   or archived

## AI Navigation Research Constraints

External docs and current research support the same direction:

- Claude Code documentation describes `CLAUDE.md`/memory as context, not
  enforced configuration, and says specific, concise instructions are followed
  more consistently:
  `https://code.claude.com/docs/en/memory`
- Cursor documents project rules / `AGENTS.md` as persistent prompt context, not
  durable runtime authority:
  `https://docs.cursor.com/context/rules-for-ai`
- OpenAI Codex material emphasizes composable CLIs and verified operations,
  which matches GuardIR's typed `devctl` + guard + receipt path:
  `https://developers.openai.com/codex/use-cases`
- Recent AGENTS.md research reports that large or unnecessary repo context can
  increase cost and make tasks harder, even when agents follow it:
  `https://arxiv.org/abs/2602.11988`

GuardIR rule:
- short generated boot cards route the agent
- typed state decides the work
- `SYSTEM_MAP.md` navigates
- flowchart audits
- archived docs remain evidence
- chat and memory remain pointers

## Plan / Receipt Lifecycle And Archive Policy

This is a missing acceptance criterion. Current-plan authority will still
balloon if every closed row, old receipt, and historical audit stays in the hot
agent path forever.

External governance patterns point to the same rule:
- Rust accepts an RFC, opens a tracking issue with implementation,
  documentation, and stabilization checklist items, then stabilizes only after a
  stabilization report proves tests, implementation status, unresolved
  questions, and cross-team coordination.
- Rust triage keeps blocked/stale work visible through status labels, age since
  activity, owner/waiting-on fields, and periodic reports instead of treating
  old work as active forever.
- Kubernetes keeps KEPs indexed by lifecycle/stage and release history
  (`alpha`, `beta`, `stable`) rather than forcing every historical proposal into
  current execution.
- ADR practice keeps decisions permanently addressable but marks them
  `superseded` or `deprecated`; records are not silently deleted.

GuardIR already has most of the primitives:
- `PlanRowClosureReceipt` in
  `dev/scripts/devctl/runtime/commit_to_plan_row_reducer.py`
- `FeatureProofReceipt` in
  `dev/scripts/devctl/runtime/feature_proof_receipt.py`
- `PlanSourceSnapshot` in
  `dev/scripts/devctl/runtime/plan_source_retention_models.py`
- `EvidenceArchivePolicy`, `EvidenceArchiveManifest`, and
  `EvidenceArchiveReceipt` in
  `dev/scripts/devctl/runtime/evidence_archive.py`
- report-retention helpers in `dev/scripts/devctl/reports_retention.py`
- archive hygiene checks in
  `dev/scripts/devctl/commands/governance/hygiene_audits_archive.py`
- existing plan-source anchor:
  `MP377-EVIDENCE-LIFECYCLE-ARCHIVE-S1`

Required lifecycle model:

```text
proposed/spec
-> queued
-> in_progress
-> blocked or revalidation_required
-> applied/completed with FeatureProofReceipt + PlanRowClosureReceipt
-> retained_hot for a configurable review window
-> archived_cold with EvidenceArchiveReceipt + manifest + retrieval ref
-> superseded/deprecated/abandoned only through typed receipt
```

Industry-standard shape:
- Tombstone terminal rows instead of deleting them.
- Tier storage: hot active rows, warm recent closure evidence, cold immutable
  archive by quarter/year or configured retention bucket.
- Require proof-of-acceptance before archival. Age alone is not enough.

Contract composition decision:

| Concept | Preferred GuardIR implementation | Do not do by default |
|---|---|---|
| `RetentionPolicy` | Extend repo-pack/operator policy plus existing `EvidenceArchivePolicy` / report retention config with PlanRow row-kind windows. | Do not hardcode retention windows into selectors. |
| `ProvenAcceptanceReceipt` | First compose current guard result + exact dogfood pytest node + `FeatureProofReceipt(proven_passed)` + `PlanRowClosureReceipt`. Add a new receipt only if existing receipt chaining cannot represent this bundle. | Do not create a parallel proof receipt store just to rename existing proof. |
| `ArchivalReceipt` | Use/extend `EvidenceArchiveReceipt` + `EvidenceArchiveManifest` + tombstone ref in `plan_index.jsonl`. | Do not invent a second archive receipt if `EvidenceArchiveReceipt` can carry the lifecycle ref. |

Rules:
- Do not delete typed evidence as the normal path.
- Do not leave all historical rows in the active selector path.
- Closed rows stay resolvable by row id, commit SHA, receipt id, and archive ref.
- Active selector surfaces should load only executable rows plus recently closed
  rows inside the configured review window.
- Historical rows and receipts can move to cold archive after typed closure and
  manifest proof.
- Archive is not proof of completion. Completion comes first from receipts;
  archive only moves proven or terminal evidence out of the hot path.
- Packet TTL is transport/inbox hygiene only. It must not delete plan source,
  proof receipts, or closure history.

User/repo policy should control retention windows. Defaults can exist, but they
must be repo-pack policy, not hardcoded behavior:
- hot closed-row window, default suggestion 30 days for implementation rows and
  14 days for experimental rows
- warm closed-row window, default suggestion 3-6 months depending on row kind
- proof receipt hot window, default suggestion 30-90 days
- full source snapshot hot window, default suggestion 30-180 days
- packet-binding evidence row hot window, default suggestion 7 days after
  durable binding or terminal disposition
- report/run artifact retention, already supported by report-retention helpers
- legal/audit hold flag that prevents archival or deletion
- never-delete families, especially plan source, closure receipts, proof
  receipts, policy receipts, and archive manifests

Tombstone shape:
- The active `plan_index.jsonl` should not keep full closed-row payloads
  forever once cold archive exists.
- It may keep a compact tombstone row with:
  row id, terminal status, archive path/ref, archival receipt id, closure receipt
  id, latest proof receipt id, commit SHA, and superseded-by/deprecated-by refs.
- A tombstone is queryable audit metadata, never executable scheduler work.
- If the current `PlanRow` schema cannot compact safely, use `status=archived`
  and `row_kind=plan_row_tombstone` only after the archival/ref-resolution guard
  proves every reader treats it as non-executable.

Required guard:
Add or extend a lifecycle/archive guard. Prefer extending existing retention,
plan-source, or governance-closure checks before adding a parallel guard.

The guard fails if:
- an `applied` / `completed` row lacks `FeatureProofReceipt` or
  `PlanRowClosureReceipt`
- a row is archived without a current acceptance proof bundle proving the row's
  guard/dogfood still passes or that the row was superseded by another proven
  row
- a closed row remains selectable as current executable work after the hot
  review window unless it is reopened by typed receipt
- an archived row cannot be resolved back to row id, source snapshot, closure
  receipt, commit SHA, and archive manifest
- an archive operation deletes source evidence unless policy explicitly permits
  it and the receipt records that fact
- a row is removed from `plan_index.jsonl` without an archive/ref-resolution
  receipt
- packet expiry is used as proof that plan/evidence source can be forgotten
- generated boot cards or `develop next` show archived rows as active work
- the archive policy is hardcoded instead of coming from repo-pack/operator
  policy
- retention-policy changes are not operator/repo-pack visible
- cold archive files are mutable without a new archive repair receipt

Required typed owner:
- Primary existing row: `MP377-EVIDENCE-LIFECYCLE-ARCHIVE-S1`
- Related current slice:
  `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`
- Related ingestion slice:
  `MP-GUARDIR-V4-PHASE-0-6-E-PLAN-INGESTION-S1`

This means current-plan authority should include a stop-gap acceptance criterion:
it must prove archived/closed rows cannot re-enter scheduler authority, while
the dedicated archive row owns the broader retention UX and policy windows.

Rust analogy:
- `#[deprecated(since = "...", note = "...")]` maps to terminal row metadata
  with a deprecation/supersession target.
- RFC tracking issues map to PlanRow + closure checklist + follow-up row refs.
- Stabilization reports map to `ProvenAcceptance` as a composed proof bundle:
  current tests, current guard output, unresolved-question resolution, and
  durable receipt refs.
- Edition-style transitions map to cold archive buckets by quarter/year or
  repo-pack retention window.

## Folder Organization Target

The earlier tree was too weak. A portable governance engine cannot look like a
VoiceTerm application repo with governance files mixed into product folders.
The target needs two layouts:

1. GuardIR engine repo layout.
2. Layout GuardIR creates inside any governed target repo.

### A. GuardIR Engine Repo Target

This repo should make the portable engine obvious at first glance. Current code
can stay in compatibility paths while migration happens, but the target shape is
package-first:

```text
/
  README.md                       # public overview: GuardIR, not VoiceTerm
  AGENTS.md                       # generated boot card, projection-only
  CLAUDE.md                       # generated/local boot card, projection-only
  pyproject.toml / tooling files
  src/guardir/                    # target package home for portable runtime
    cli/                          # devctl command entrypoints
    runtime/                      # typed contracts, reducers, state readers
    plan_graph/                   # PlanRow graph, CurrentPlanAuthority
    packet_intake/                # review-channel packet classification/binding
    receipts/                     # proof, closure, archive receipt helpers
    guards/                       # check-router-callable guard library
    context_graph/                # visibility graph, not scheduler authority
    renderers/                    # generated surfaces: AGENTS, CLAUDE, SYSTEM_MAP
    repo_packs/                   # portable repo-pack interface and defaults
  dev/
    state/                        # dogfood typed stores for this repo
    reports/                      # generated proof/report artifacts
    active/                       # tiny tracker projections only
    audits/
      plan_intake/                # retained plan sources
      architecture/               # historical/deep audits
    guides/                       # current maintained navigation
    config/                       # repo-local dogfood policy
    scripts/
      devctl/                     # current implementation until package split
      checks/                     # current guard scripts until package split
  repo_packs/
    guardir_default/              # default portable policy pack
    voiceterm/                    # adopter pack, not engine authority
  adopters/
    voiceterm/                    # VoiceTerm product/client code if kept here
      rust/
      app/
      docs/
      templates/
  examples/
    governed_repo_minimal/
    adopters/voiceterm/
  tests/
    fixtures/
      governed_repo_minimal/
      legacy_voiceterm/
```

Current compatibility rule:
- Do not block current work on a full `src/guardir` package migration.
- While implementation remains under `dev/scripts/devctl`, generated surfaces
  must still describe it as portable GuardIR engine code, not VoiceTerm code.
- Any move from `dev/scripts/devctl` to `src/guardir` needs its own typed row,
  guard, import-compatibility shim policy, and proof.

### B. Governed Target Repo Layout

GuardIR must also work when installed into an arbitrary repo. The target repo
should not inherit this repo's doc sprawl or VoiceTerm folders.

Open decision: target repos should likely use a compact `.guardir/` state root
or a configured `dev/guardir/` root. The choice must be repo-pack policy, not a
hardcoded VoiceTerm path.

```text
target-repo/
  AGENTS.md                       # generated boot card, short
  CLAUDE.md                       # optional generated local peer card
  .guardir/ or dev/guardir/
    policy.json                   # repo-pack selection and local policy
    state/
      plan_index.jsonl
      plan_source_snapshots.jsonl
      plan_ingestion_receipts.jsonl
      plan_row_closure_receipts.jsonl
    reports/
      feature_proof_receipts/
      archive/
    generated/
      SYSTEM_MAP.md
      boot_cards/
    packets/
      events/
```

Target repos should not get:
- VoiceTerm product folders
- VoiceTerm commands
- VoiceTerm release workflows
- old GuardIR audit mega-docs
- stale plan-intake source files unless explicitly imported as retained source
  evidence

### C. Cleanup Rules

- Root-level mega-docs are not allowed unless generated, guarded, or
  intentionally public-facing.
- `dev/active/` should shrink to a small tracker/pointer set; active execution
  lives in typed stores.
- `dev/guides/SYSTEM_MAP.md` is current navigation and must be generated or
  guard-checked.
- `System_Connection_Flowchart.md` becomes archived audit or managed generated
  surface.
- `AGENTS.md` and `CLAUDE.md` become short generated role routers, not full
  architecture documents.
- VoiceTerm-specific docs/code/config must move to one of:
  adopter pack, adopter product folder, example, fixture, historical archive,
  typed migration debt, or deletion-after-proof.

### D. Current Root Residue To Classify

High-level buckets:
- `.voiceterm/` -> adopter product state or deletion after proof
- `app/` -> adopter product code unless a portable frontend boundary is proven
- `rust/` -> adopter product code unless a portable runtime crate is split out
- `whisper_models/` -> adopter asset/cache, not governance engine
- `orb.db` -> generated/local data; needs policy or deletion-after-proof
- VoiceTerm-specific `guides/`, `integrations/`, `pypi/`, `scripts/` content
  -> adopter pack, example, archive, or typed migration debt

Each path must end in exactly one typed disposition:
- `portable_core`
- `repo_pack_default`
- `adopter_voiceterm`
- `example_adopter`
- `legacy_fixture`
- `historical_archive`
- `migration_debt`
- `delete_after_proof`

No path should remain in an ambiguous "maybe platform, maybe product" state.

## Boot Card Generation Requirements

Do not hand-edit generated boot cards. Update renderer inputs so generated
`AGENTS.md` / `CLAUDE.md` answer only:

1. What role/actor/session am I?
2. What is the current PlanRow?
3. What command do I run next?
4. What commands are forbidden?
5. What packet lane is mine?
6. What proof closes the current row?
7. Which surfaces are projection-only?
8. Where do I go for deeper architecture context?

Generated boot cards must not:
- list VoiceTerm as GuardIR core
- hardcode Codex/Claude as durable role authority
- tell agents to read stale flowchart/docs before typed boot
- expose bridge/dashboard/memory/chat as authority

## System Composition Gaps And Execution Sequencer

Root cause:
the repo has many typed components, guards, receipts, and authority wrappers,
but they are not yet composed into one deterministic operating path. The
planning gap is mostly solved in existing rows and plan docs. The execution
sequencing gap is not.

Do not ingest the following as one giant current-row burden. Ingest it as a
sequencer and cross-index. S0 is the proof-carrying substrate that makes the
later slices enforceable; S1 is the current in-progress row.

| Slice | Composite | Existing owner row/spec | Operational layer that must work |
|---|---|---|---|
| S0 | Proof-carrying PlanRow substrate: PlanRow proof refs, role provenance, mutation/proof ancestry, closure/proof requirements, PlanHealthSnapshot, meta-guards | cached-hammock P1/P3/P6 refs, plan lifecycle rows, receipt-unification refs, current-plan row for immediate enforcement | every executable PlanRow can answer: who owns it, what evidence proves it, what receipts close it, what blockers remain, and whether it is selectable |
| S1 | CurrentPlanAuthority composition: scheduler, event queue, packet binding, final gate, typed-object handoff, `PKT-BIND-*` exclusion, reference-integrity stop-gap for current refs, plan-index write authority visibility | `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1` plus parentage/reference rows where already typed | `develop next` and final gate return the executable PlanRow for codex/claude, never packet ids or packet-binding rows, with dogfood receipt |
| S2 | Guard execution composition: router coverage, guard tiers, deterministic profiles, pre-commit mandatory subset, dangling guard-reference cleanup | quality preset / `ResolvedQualityPolicy` / `BUNDLE_BY_LANE` owners; `MP-GOVERNANCE-ECOSYSTEM-INTEGRATION-S1` for CI ecosystem; current row only requires `check_current_plan_authority.py` to be check-router-visible | `devctl check-router --profile <profile>` deterministically runs the configured guard set; mandatory guards run locally before handoff/commit |
| S3 | Human/AI explainer surface: `AssistantGuideMode`, `PlatformGuideProjection`, `HelpContextResolver`, `/help` or `devctl explain`, freshness guard | cached-hammock P111/P134 and instruction-surface rows (`MP-GUARDIR-V4-PHASE-0-6-E-INSTRUCTION-SURFACE-USABILITY-S1`, `MP-NEW-P202-*`, `MP377-P0-INSTRUCTION-SURFACE-SLIM-S1`) | user can ask why a guard fired, what it protects, how to remediate, and which policy owns it; AI explains but does not decide policy |
| S4 | Repo/adopter cleanup: GuardIR portable engine boundary, VoiceTerm adopter pack/example/archive, root folder classification, old Rust/app/product assets moved or retained with owner evidence | `MP-GUARDIR-V4-WORK-STREAM-E-REPO-PACK-ADOPTER-BOUNDARY-S1`, `MP377-VOICETERM-EXTRACTION-S1`, `MP377-GUARDIR-V21-PORTABILITY`, `MP377-ADOPTER-PILOT-GATE-S1` | a new target repo initializes GuardIR without inheriting VoiceTerm identity, product folders, or product commands |
| S5 | CI/background governance: scheduled guard suite, cloud proof artifacts, quality repair packets, runtime agreement reports | `MP-GOVERNANCE-ECOSYSTEM-INTEGRATION-S1`, `MP-NEW-P195`, `MP-NEW-P198`, portable-code-governance rows | background checks produce typed receipts and visible repair work without becoming scheduler authority |
| S6 | Lifecycle/archive: tombstones, retention windows, archive manifests, closed-row non-selector behavior, receipt unification | `MP377-EVIDENCE-LIFECYCLE-ARCHIVE-S1` and cached-hammock Priority 3 receipt-unification refs | active plan state stays small; archived rows remain queryable evidence and cannot become executable work unless reopened by typed receipt |

Execution order:

0. Bind S0 as the substrate contract. Implement only the minimum S0 checks needed
   by S1 inside the current row; broader PlanRow schema migration belongs to its
   owner lifecycle/receipt rows.
1. Ship S1 first. Nothing else is reliable while packets, findings, projections,
   or stale rows can outrank CurrentPlanAuthority.
2. Ship S2 next. The system must know which guards run locally, which run in
   CI, and which are intentionally opt-in or archived.
3. Ship S3 next. Agents and users need a generated explanation surface backed
   by typed policy, not stale hand-written docs.
4. Ship S4 next. VoiceTerm must become an adopter/client boundary so GuardIR
   works for any repo.
5. Ship S5 next. Background CI/CD governance should create receipts and repair
   packets, not hidden authority.
6. Ship S6 next. Closed work must leave compact tombstones and cold archives so
   active state does not grow forever.

### S0 Proof-Carrying PlanRow Contract

The system needs a borrow-checker-style composition substrate: every PlanRow
transition, packet post, commit/proof emission, `develop next` selection, and
final-gate decision must traverse typed composition seams. If a seam is broken,
the operation should fail closed with a typed blocker.

S0 must not become a new parallel plan family. Bind it to existing lifecycle,
receipt, current-plan, and cached-hammock owner rows.

Required PlanRow proof semantics:
- role accountability: owner/assigned role or role-provenance refs survive
  beyond the current session and do not depend on archived packets.
- proof requirements: the row states which proof chain is required before it
  can become applied/completed/closed.
- proof refs: row can reference its `FeatureProofReceipt`, dogfood run/probe
  receipt, closure receipt, and validation/commit/push proof lineage.
- mutation lineage: row can connect typed action/result/run/validation and git
  mutation evidence without losing ancestry.
- selector health: row exposes enough state for CurrentPlanAuthority to know
  whether it is executable, blocked, superseded, archived, stale, or missing
  proof.

Candidate S0 meta-guards to bind:
- `check_plan_row_completeness.py` — executable rows must carry required role,
  owner, target, status, proof-requirement, and provenance fields.
- `check_plan_row_proof_path.py` — applied/completed/closed rows must resolve
  their required proof chain.
- `check_feature_proof_pytest_node_required.py` — `proven_passed` receipts must
  include a concrete pytest node id.
- `check_receipt_consumer_coverage.py` — receipt stores that affect scheduling,
  closure, proof, exceptions, or bypasses must have named consumers.
- `check_role_planrow_binding.py` — role/session ownership must bind to PlanRows
  or durable role-provenance receipts, not only packets.

PlanHealthSnapshot boot surface:
- startup/session surfaces must show queued row count, stalled rows, dangling
  refs, missing closure/proof counts, packet backlog size, and current-plan
  health.
- It is a typed health projection, not scheduler authority.
- `startup-context`, `session`, `develop next`, final gate, and boot cards must
  agree on the same current PlanRow or the same typed blocker.

### System-Wide Inventory From 8-Agent Audit

Record these as audit findings to ingest, not as final verified truth. Re-check
counts at ingestion time because the worktree is moving.

1. Plan lifecycle subsystem.

   Reported shipped contracts:
   `PlanRow`, `PlanSourceSnapshot`, `PlanIntentIngestionReceipt`,
   `PlanRowClosureReceipt`, `PlanRegistry`, `PlanTargetRef`,
   `PlanRevisionRefreshRequired`, `CurrentPlanAuthority`,
   `PlanCurrencyContext`, `IngestionProvenance`.

   Reported spec-only or missing contracts:
   `PlanAmendmentReceipt`, `RetentionPolicy`, `ArchivalReceipt`.

   Reported state sizes:
   - `dev/state/plan_index.jsonl`: 2,082 rows / about 2.6 MB.
   - `dev/state/plan_source_snapshots.jsonl`: 766 rows / about 18 MB.
   - `dev/state/plan_ingestion_receipts.jsonl`: 388 rows / about 5.8 MB.
   - `dev/state/plan_row_closure_receipts.jsonl`: 23 closure receipts for
     2,082 rows, meaning roughly 99 percent of rows have no closure proof.

   Reported lifecycle gap:
   `commit_to_plan_row_reducer.reduce_feature_proof_to_plan_rows()` guards one
   transition path, but role review is opt-in through
   `enforce_role_review_gate=True` and defaults false in most callers.

   Required disposition:
   - Do not create `plan_amendment_receipts.jsonl` casually.
   - Decide whether amendment provenance uses an existing ingestion receipt
     path or a formally added amendment receipt contract.
   - S0/S1 must prevent proofless applied/completed rows from becoming a false
     green state.

2. Dogfood/proof subsystem.

   Reported evidence inventory:
   - 149 `FeatureProofReceipt` JSON files under
     `dev/reports/feature_proof_receipts/`.
   - 4,004 dogfood runs in `dev/reports/dogfood/runs.jsonl`.
   - 36 ground-truth probe receipts.

   Critical verified schema gap:
   `dev/scripts/devctl/runtime/feature_proof_receipt.py:62-74`
   `FeatureProofReceipt.__post_init__` accepts
   `real_life_test_status="proven_passed"` without requiring a concrete pytest
   node id in `tests_run`, even though generated boot cards say `proven_passed`
   requires one.

   Related verified guard path:
   `dev/scripts/devctl/runtime/feature_proof_output_proof.py:112-190` can check
   resolved pytest-node proof, but `require_real_tests` is optional. This means
   the invariant is not enforced at the receipt contract boundary by default.

   Required disposition:
   - Add/extend a schema guard so `proven_passed` without concrete pytest node
     id fails.
   - Add a reverse index or row-level proof refs so PlanRows can resolve their
     `FeatureProofReceipt`.
   - Add a guard so applied/completed rows that require dogfood cannot close
     without a matching `FeatureProofReceipt(proven_passed)`.
   - Treat dogfood as evidence, not commit proof, until commit/push proof
     receipts consume it.

3. Packet / review-channel subsystem.

   Reported typed packet contracts:
   `PacketCreationBindingEvent`, `PacketAbsorptionReceipt`,
   `PacketSemanticIngestionReceipt`, `PacketSemanticActionItem`,
   `PacketCarryForwardDebt`.

   Reported state sizes:
   - `dev/state/review_channel/events.jsonl`: about 99 MB / 85,423 lines.
   - `dev/state/review_channel/latest.json`: about 48 MB snapshot.

   Known facts:
   - `PKT-BIND-*` rows are `row_kind="packet_binding"` and currently created
     with `status="evidence"`.
   - Stale packets remain in the append-only event log unless archived,
     expired, absorbed, or compacted.
   - Carry-forward debt tracking exists but is not proven to auto-resolve.

   Required disposition:
   - Current-plan authority must not select packet-binding rows.
   - Packet/event compaction and packet-retention policy belong to lifecycle
     archive rows, not current-row closure.
   - Current row only needs the non-selector invariant and bounded dogfood
     proof that stale/future/unbound packets cannot become continuation goals.

4. Receipt / proof-chain subsystem.

   Reported inventory:
   - 67 receipt type classes.
   - 18 receipt-shaped JSONL stores.
   - Longest intended proof chain:
     `PlanRow -> PlanIntentIngestionReceipt -> ValidationReceipt ->
     CommitReceipt -> GitMutationProofReceipt -> RoleReviewReceipt ->
     PlanRowClosureReceipt -> FeatureProofReceipt`.

   Reported breakpoints:
   - `FeatureProofReceipt` has `role_review_receipt_refs` but can lose commit
     ancestry.
   - Role review remains optional in paths where
     `role_review_receipt_refs` is empty.
   - Push reports do not reliably name the `GitMutationProofReceipt` proving
     the push.

   Reported orphan stores needing consumers:
   - `governed_exception_lifecycles.jsonl`
   - `bypass_lifecycles.jsonl`
   - `artifact_receipts.jsonl`
   - `baseline_authority_inventories.jsonl`
   - `plan_ingestion_receipts.jsonl`
   - `plan_row_closure_receipts.jsonl`

   Required disposition:
   - S0/S1 must make required receipts consumable by selectors and gates.
   - Broader proof-chain repair belongs to Phase 1 proof-integrity after
     CurrentPlanAuthority is green.

5. Role / authority subsystem.

   Reported shipped contracts:
   `RoleProfile`, `TandemProfile`, `CollaborationSessionState`,
   `ActorAuthorityState`, `CapabilityGrantState`, `ReviewerMode`,
   `SessionPosture`, `BypassLifecycle`, `AgentLoopOperatorOverride`,
   `ConductorCapabilityState`, `PlanRow`.

   Reported gap:
   PlanRows have no durable `role_provenance`, `owner_role`, or
   `assigned_role` semantics, so role-to-row accountability can disappear when
   a session ends or packets archive.

   Required disposition:
   - S0 must add durable role provenance semantics.
   - S1 must ensure final/develop surfaces agree on actor/role/session
     authority before selecting or closing work.

6. Guards / check-router subsystem.

   Reported count from 8-agent audit:
   148 guards total, split roughly into plan lifecycle, receipt integrity,
   packet-plan binding, role, VoiceTerm/identity, build/test/lint, and
   architecture/governance categories.

   Local note:
   Earlier direct count of `dev/scripts/checks/check_*.py` returned 122. Treat
   the difference as scope-definition drift: the 148 count may include probes,
   review-probes, shims, or non-`check_*.py` guard entrypoints. Ingest must
   record the counting rule.

   Reported gaps:
   - no meta-guard validates PlanRow completeness/proof path.
   - role-related guard coverage is minimal.
   - helper-session typed delegation, role-aware routing,
     instruction-surface usability, and proof-carrying PlanRow contract are
     not load-bearing.

   Required disposition:
   - S1 requires `check_current_plan_authority.py` in check-router.
   - S2 owns guard tiers, profiles, pre-commit mandatory subset, and
     router/CI/dangling-reference coverage.

7. Boot / session / agent-mind subsystem.

   Reported startup-context coverage:
   reviewer gate, push decision, work intake, packet intent anchors, plan
   iteration session, quality signals, blocker, runtime truth, session posture,
   coordination state.

   Reported missing boot health:
   queued row count, stalled rows, dangling refs, plan-graph health, missing
   closure/proof counts, packet backlog/compaction health.

   Reported seam gap:
   `AgentMindSlice` is a provider trace projection, not a typed-state
   derivative. Startup-context and `develop next` can read typed state
   independently without a reconciliation guard.

   Required disposition:
   - Add PlanHealthSnapshot or equivalent boot health projection.
   - Reconcile startup/session/develop/final-gate current row before agents
     act.

8. Composition seams.

   The failing seams to record:

   | Seam | State | Required repair |
   |---|---|---|
   | PlanRow <-> FeatureProofReceipt | weak / one-way | PlanRow proof refs or reverse proof index plus guard |
   | PlanRow <-> DogfoodRun | severed | typed dogfood/proof receipt link |
   | Packet <-> PlanRow | asymmetric | intake-time classification/binding plus non-selector invariant |
   | CommitReceipt <-> PlanRowClosureReceipt | strong but opt-in | role-review/proof gate must be policy-driven and consumed |
   | RoleAssignment <-> PlanRow ownership | broken | durable role provenance refs on row or receipt |
   | CurrentPlanAuthority <-> FeatureProofReceipt | unlinked | in-progress/current rows expose proof requirement; closure gate consumes FPR |
   | Receipt stores <-> selectors/gates | weak | required consumers and diagnostics |
   | Startup/session <-> develop/final gate | loose | cross-surface reconciliation and PlanHealthSnapshot |

   Borrow-checker rule:
   no operation that mutates, selects, closes, or proves work may bypass these
   seams. If a seam is broken, emit a typed blocker instead of continuing.

### Contract Guard Coverage — Borrow-Checker Layer

Root rule:
a typed contract without guard coverage is documentation, not enforcement.
When a bug is caused by a missing invariant, the fix must add the guard that
would have caught the bug before the work can close.

Guard coverage dimensions for every typed contract:

1. Field invariants:
   what must be true inside the contract instance itself?
2. Composition invariants:
   which other contracts must reference it or be referenced by it?
3. Lifecycle invariants:
   which state transitions are legal, and what proof gates each transition?
4. Consumer obligations:
   which runtime/scheduler/final-gate/check-router consumer must read the
   contract or receipt before deciding?

Required audit output:
`dev/state/contract_guard_coverage.jsonl`

One row per typed contract, with:
- contract id/name
- source path
- field guard id or missing marker
- composition guard id or missing marker
- lifecycle guard id or missing marker
- consumer guard id or missing marker
- owner PlanRow/spec
- severity
- current status
- first required remediation command

The first pass should cover at least:
- 67 receipt types
- 11 role/authority contracts
- 10 plan-lifecycle contracts
- 5 packet/review-channel contracts
- scheduler/current-plan/final-gate contracts
- generated/projection-surface contracts

Do not write hundreds of guards blindly. Use the audit to identify the
load-bearing 30-40 guards, then ship the highest-risk 16 first.

#### Sixteen Missing Guards To Bind First

Names are proposed. Reuse an existing guard only if it already enforces the
same invariant over live typed state and is wired into check-router.

| # | Problem that should have been caught | Missing guard / equivalent |
|---|---|---|
| 1 | `FeatureProofReceipt(real_life_test_status="proven_passed")` can exist without concrete `proven_pytest_node_id` | `check_feature_proof_requires_pytest_node_id.py` |
| 2 | Applied/completed PlanRows can exist without `PlanRowClosureReceipt`; reported 23 closure receipts for 2,082 rows | `check_every_applied_row_has_closure_receipt.py` |
| 3 | PlanRow lacks durable role provenance / owner role / assigned role semantics | `check_plan_row_role_provenance_resolved.py` |
| 4 | PlanRow cannot resolve a full proof path to FPR / closure / validation / git mutation evidence | `check_plan_row_proof_path_resolves.py` |
| 5 | Role review remains optional through `enforce_role_review_gate=False` default paths | `check_closure_requires_terminal_role_review.py` |
| 6 | PlanRow <-> DogfoodRun link is severed | `check_applied_row_has_dogfood_run.py` |
| 7 | PushReport does not reliably name the `GitMutationProofReceipt` proving the push | `check_push_report_has_git_mutation_proof_ref.py` |
| 8 | Packet target_ref resolution is deferred to query time instead of guarded at intake | `check_packet_target_ref_resolves_at_intake.py` |
| 9 | Boot/session surfaces do not include PlanHealthSnapshot / plan-graph health | `check_startup_context_includes_plan_health.py` |
| 10 | Review-channel `events.jsonl` / `latest.json` can grow without retention/compaction bounds | `check_events_log_within_retention_bounds.py` |
| 11 | Guards exist but are not reachable from local check-router / CI / opt-in / archive policy | `check_guard_router_coverage.py` |
| 12 | Plan refs such as `target_ref="plan:MP-377"` / parent refs / receipt refs can dangle | `check_plan_reference_integrity.py` |
| 13 | Receipt stores can have writers but no active scheduler/final-gate/runtime consumer | `check_receipt_store_has_active_consumer.py` |
| 14 | Runtime dispatch over typed string/Literal states can silently fall back on unknown values | `check_runtime_dispatch_exhaustive.py` |
| 15 | Final/continuation gates can receive row-id strings instead of typed CurrentPlanAuthority | `check_current_plan_authority_gate_enforced.py` |
| 16 | Plan-index mutations can hide behind convenience wrappers instead of explicit authority seam | `check_authority_only_imports.py` |

Current-row blocking subset:
- `check_feature_proof_requires_pytest_node_id.py`
- `check_current_plan_authority_gate_enforced.py`
- `check_packet_target_ref_resolves_at_intake.py`
- `check_guard_router_coverage.py` for `check_current_plan_authority.py`
- enough of `check_plan_reference_integrity.py` to prevent current-row refs from
  silently dangling

The other guards bind to S0/S2/S5/S6 owner rows unless a typed reducer promotes
them into current-row blockers.

#### Guard-First Lifecycle Rule

Every feature/fix that changes a typed contract, receipt, scheduler decision,
packet classifier, final-gate rule, role/authority contract, or generated
projection must answer before closure:

1. Which invariant failed or could fail?
2. Which guard would catch the failure in live state?
3. Is that guard present?
4. Is that guard wired into check-router or the relevant mandatory profile?
5. Does the feature proof include the guard output?

Closure is invalid when the answer to 2 is "a guard would help" and the guard
is not added, extended, or explicitly deferred to an owner row with typed
acceptance criteria.

For TDD-style fixes:
- write the guard or guard test first when the bug is an invariant failure.
- prove it fails against the broken fixture/state.
- implement the fix.
- prove the guard passes.
- wire guard fixes into check-router/catalog/bundle before claiming they exist.
- dogfood through the real `devctl` or check entrypoint, not only direct pytest,
  when the behavior has a CLI/runtime path.
- attach the guard output to the FeatureProofReceipt or row closure receipt.

Required invariant-code loop:

```text
RED -> GREEN -> ROUTER -> DOGFOOD -> RECEIPT
```

- RED: write the focused failing test or guard fixture first.
- GREEN: implement the minimal scoped fix without widening the row.
- ROUTER: wire guards into check-router/catalog/bundle and prove routing.
- DOGFOOD: exercise the actual `devctl`/guard path that agents will use.
- RECEIPT: record command output, receipt id, or typed blocker evidence.

This sequence is mandatory for guards, schedulers, final gates, role authority,
packet classification, receipts, plan mutation, and generated authority
surfaces unless the operator explicitly labels the slice as a spike. Pytest
alone is not closure proof when runtime behavior is exposed through `devctl`.
Source-grep is not proof when behavior can be tested.

#### Five-Phase Rollout

Phase 1 — Contract coverage audit:
- enumerate typed contracts under `dev/scripts/devctl/runtime/` and adjacent
  contract packages.
- write `dev/state/contract_guard_coverage.jsonl`.
- classify each contract by field/composition/lifecycle/consumer coverage.

Phase 2 — Highest-risk guard implementation:
- implement the 16 guards above or map each to an existing equivalent.
- each guard gets focused unit tests and at least one live-state fixture.

Phase 3 — Router/profile wiring:
- wire the 16 guards into check-router.
- add guard-router coverage so future guards cannot be orphaned.
- put mandatory invariants in the mandatory/default local path, not only CI.

Phase 4 — Receipt consumer enforcement:
- add `check_receipt_store_has_active_consumer.py`.
- every receipt store with writers must have a named reader/consumer or an
  explicit archive/evidence-only disposition.
- scheduler/final-gate affecting receipts must be consumed before decisions.

Phase 5 — Retroactive live-state run:
- run the new guards against current `dev/state/` and `dev/reports/`.
- each finding becomes typed work, a typed defer/reject/supersede receipt, or
  an archive disposition.
- stale-by-design findings must be explicitly marked, not silently ignored.

Open decision:
- fold this into an existing v4 Phase 0.6.E / cached-hammock owner row, or
- create a typed row such as
  `MP-GUARDIR-V4-PHASE-0-7-CONTRACT-GUARD-COVERAGE-S1`.

Do not create that row from this staging file by hand. The typed plan-intake
path must decide whether the existing rows can carry the work or whether a new
row is required.

### Seven Composition Gaps To Bind

These are not new architecture inventions. They are composition requirements
over existing infrastructure.

1. Guard discovery and router coverage.

   Current fact to preserve: `dev/scripts/checks/` contains 122
   `check_*.py` files. `dev/scripts/devctl/commands/check/router_constants.py`
   hardcodes lane-to-bundle mapping through `BUNDLE_BY_LANE`. CI and profile
   paths may reference many guards, but interactive `devctl check-router` and
   pre-commit are not proven to expose every relevant guard.

   Required action:
   - Add or bind a guard such as `check_guard_router_coverage.py` or
     `check_router_coverage.py`.
   - It must scan `dev/scripts/checks/check_*.py`.
   - It must verify each guard is reachable from check-router, CI-only with an
     explicit reason, opt-in, archived, or excluded by an explicit allowlist.
   - It must detect guard references in devctl/workflows/config that point to
     missing files.
   - It must fail if `check_current_plan_authority.py` exists but is not in the
     mandatory/current-row route.

   Current-row blocking subset: `check_current_plan_authority.py` must be
   check-router-visible. Full guard tier cleanup belongs to S2.

2. Deterministic guard tiers and profiles.

   Required model:
   - Guard metadata in each guard or a generated catalog:
     `GUARD_TIER`, `GUARD_PROFILES`, `GUARD_OWNER_ROW`, `GUARD_SCOPE`,
     `GUARD_RATIONALE`.
   - Tiers:
     `mandatory`, `recommended`, `opt_in`, `archive`.
   - Profiles:
     `mandatory`, `default`, `strict`, with repo-pack-specific additions.
   - Per-repo policy file, preferably `.guardir.toml` for adopted repos or the
     existing repo-pack policy path for this repo, defines the selected profile
     and explicit overrides.
   - `devctl init` may write the starter config through deterministic static
     detection. AI may explain or stage a suggestion, but policy changes require
     operator approval and a committed diff.
   - Pre-commit must run the mandatory tier once the profile dispatcher exists.

   Anti-pattern:
   - AI scanning the repo and deciding which guards to run at runtime.

   Correct pattern:
   - AI reads deterministic policy and explains it. The committed profile
     decides.

3. Exhaustive runtime dispatch.

   Problem:
   `Literal[...]` unions and enum-like strings are often type-checker only.
   Dispatch sites that use `.get(key, fallback)` can silently accept unknown
   states.

   Required action:
   - Convert critical dispatcher domains to `enum.StrEnum` or a runtime
     checked dispatcher.
   - Unknown values fail closed with typed blocker output.
   - Start with scheduler, packet classification, topology/role assignment,
     final-gate state, and guard-profile state.

4. Receipt consumption mandate.

   Problem:
   receipt stores are durable evidence only if consumers must read them before
   deciding.

   Required action:
   - Scheduler/final gate/current-plan authority must consume the receipts that
     affect their decisions.
   - Final response cannot go green without the required
     `FeatureProofReceipt(proven_passed)`.
   - Closed/recently-closed/applied/archived rows must be demoted or excluded
     through closure/archive receipts, not ignored by convention.
   - Do not add new receipt stores unless the writer, reader, guard, and
     check-router route land in the same slice.

5. Typed-object handoff instead of string-only authority.

   Problem:
   `final_response_gate.py` currently accepts `current_plan_row_id: str` in
   its public path. A string cannot carry bound packet ids, unbound packet ids,
   pivot reason, selected row diagnostics, or non-executable row exclusions.

   Required action:
   - Current-plan/final-gate/continuation composition should pass a typed
     `CurrentPlanAuthority` object or equivalent typed decision, not just a
     row-id string.
   - If a compatibility wrapper keeps accepting strings, it must construct and
     validate the authority object before deciding.

   Current-row blocking subset: final gate and continuation cannot select or
   block on packet ids while executable current PlanRow authority exists.

6. Plan-index authority imports.

   Problem:
   `PlanIndexAuthority` is the locked write seam, but convenience imports can
   obscure whether callers are using authority semantics.

   Required action:
   - Add or bind `check_plan_index_authority_imports.py`.
   - It must flag plan-index mutation call sites that bypass the authority seam
     or hide mutations through convenience wrappers without preserving lock and
     provenance behavior.
   - Existing compatibility wrappers can remain only if the guard proves they
     delegate to `PlanIndexAuthority` and expose receipt/provenance results.

7. Typed reference integrity.

   Problem:
   `target_ref`, `parent_row_id`, `anchor_refs`, receipt refs, and packet refs
   can become dangling pointers. `target_ref="plan:MP-377"` is currently an
   umbrella reference even if a literal `row_id="MP-377"` is not yet proven.

   Required action:
   - Add or bind `check_plan_reference_integrity.py`.
   - It must scan typed JSONL stores for resolvable row/packet/receipt refs.
   - It must support declared umbrella references such as `plan:MP-377` until
     the parent-anchor decision is made.
   - It must fail unresolved refs unless they are explicitly typed as external,
     historical, archived, or open-decision references.

### Codesmell Projection Rule

Any `codesmells.md` / `CODE_SMELLS.md` / smell inventory generated by this
system must be a projection over typed findings, plan rows, receipts, and
guards. It must not become a hand-maintained authority document.

Local surfaces found in this worktree:
- `codesmells.md`
- `dev/audits/mp377_codesmell_042_044_052_plan_ingest.md`
- `dev/audits/mp377_codesmell_048_051_plan_ingest.md`
- `dev/scripts/checks/probe_design_smells.py`
- `dev/scripts/checks/review_probes/probe_design_smells.py`
- `dev/scripts/devctl/tests/checks/test_probe_design_smells.py`

Required action:
- Locate all code-smell markdown surfaces.
- Classify each item as:
  `fixed`, `irrelevant`, `duplicate`, `deferred_with_owner_row`,
  `active_finding`, or `needs_typed_intake`.
- Each non-fixed item needs a typed finding, owner PlanRow, defer/reject
  receipt, or explicit archive disposition.
- Add or extend a projection guard so code-smell docs fail if they contain
  unbound items or disagree with typed findings.
- If code-smell docs come from the system, route them through a renderer and
  surface-provenance block like AGENTS/SYSTEM_MAP, not raw markdown.

### Guard Profile / Vibe-Coder UX Contract

The user-facing answer is not "read every guard." It is:

```text
devctl init
-> writes deterministic repo policy/profile
-> pre-commit runs mandatory guards
-> check-router runs selected profile
-> devctl explain --guard <id> explains failures from generated typed guide
-> AI can suggest a policy change as a typed suggestion
-> operator reviews and commits the policy diff
```

Required override layers:
- Profile-level: repo selects `mandatory`, `default`, `strict`, or an
  adopter-specific profile.
- Per-guard: policy override sets `off`, `warn`, or `deny` with reason and
  owner.
- Inline/local: a one-line suppression/defer annotation only when it carries
  reason, expiry, and typed owner/finding ref.

AI rule:
- AI can explain, draft, and stage.
- AI cannot silently decide policy, turn off guards, or pick a different
  profile at runtime.

## Existing Plan Cross-Index

This file should point agents to the existing typed work, not duplicate it.
When ingested, add these references to the active row's evidence/provenance so
compaction restarts know where each problem belongs.

Active owner specs:
- `dev/active/ai_governance_platform.md` — primary MP-377 owner spec for the
  governance product, extraction, docs consolidation, repo-pack/runtime
  contracts.
- `dev/active/MASTER_PLAN.md` — tracker projection over
  `dev/state/plan_index.jsonl`, not durable authority.
- `dev/active/portable_code_governance.md` — MP-376 reference owner for
  external adopter proof and portable guard/probe engine.
- `dev/guides/SYSTEM_MAP.md` — current navigation surface.
- `System_Connection_Flowchart.md` — architecture audit/reference only unless
  archived or registered as a managed generated surface.

| Problem | Existing row/spec owner | What this staging doc adds | Proof required |
|---|---|---|---|
| Current row loses to packets, findings, projections, final-gate drift | `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1` | load-bearing guard + dogfood cycle + stop gate | `check_current_plan_authority.py`, scenario pytest, final gate output, `FeatureProofReceipt(proven_passed)` |
| Startup/session/final gate select a different stale row than `develop next` | `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1` | selector parity requirement across startup-context, session, develop-next, final gate, review-channel selection, and packet inbox | every surface returns the same current PlanRow or the same typed blocker; no packet id / `PKT-BIND-*` / stale MP377 row becomes current |
| `AGENTS.md` / `CLAUDE.md` too thin to route agents | `MP-GUARDIR-V4-PHASE-0-6-E-INSTRUCTION-SURFACE-USABILITY-S1`; packet/source refs `PKT-BIND-REV-PKT-4745`, `PKT-BIND-REV-PKT-4493`, `PKT-BIND-REV-PKT-4479` | concrete boot-card generation requirements and load order | generated surfaces from typed renderer, `render-surfaces`, instruction-surface sync guard |
| Boot cards and instruction surfaces drift from typed inputs | `MP-NEW-P202-BOOT-CARD-SURFACE-INSTRUCTION-SYNC-S1`, `MP377-P0-INSTRUCTION-SURFACE-SLIM-S1`, `MP377-PROJECTION-RETIREMENT-CONTRACT-S1` | short generated role routers, projection-only language, command catalog discovery, no stale doc-first boot | instruction-surface sync, docs-check, render-surfaces proof, no projection-authority guard |
| Instruction/role contracts not connected to catalog/graph/checks | `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-INSTRUCTION-CONNECTIVITY-S1` | require command catalog, role card, role guard, and system-map connectivity | contract-connectivity/system-map guard evidence |
| Agents forget role, peer lane, continuation policy, allowed actions | `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-BOOT-CONTINUATION-S1` | require role envelope at startup, `develop next`, final gate, and boot cards | develop-next/final-gate JSON proves role/session/allowed-action agreement |
| Guard/router execution is not composed into one local path | S2 guard/profile composition; quality preset / `ResolvedQualityPolicy` / `BUNDLE_BY_LANE` owners; `MP-GOVERNANCE-ECOSYSTEM-INTEGRATION-S1` for broader ecosystem | add guard-router coverage, guard tier metadata, deterministic profiles, mandatory pre-commit subset, dangling guard-reference cleanup | `check_guard_router_coverage.py` / `check_guard_tier_coverage.py`, `check-router --profile mandatory/default/strict`, pre-commit mandatory proof |
| Runtime dispatch accepts unknown typed states through string fallbacks | cached-hammock P1 task-class routing / FeatureShipLifecycle refs; role/topology/current-plan authority rows | require runtime-checked dispatcher or `StrEnum` for scheduler, packet classification, topology, final-gate, and guard-profile states | tests prove unknown enum/string values fail closed with typed blocker |
| Receipts are written but not consumed by selectors/gates | cached-hammock P3 receipt unification refs; current-plan row for final-gate consumption; `MP377-EVIDENCE-LIFECYCLE-ARCHIVE-S1` for retention | selectors and final gate must read required receipt stores before deciding; no append-only proof graveyards | decision output cites consumed closure/FPR/archive receipts or fails with missing-receipt blocker |
| Final gate and continuation pass row-id strings instead of typed authority | `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1` | pass `CurrentPlanAuthority` or equivalent typed decision into final/continuation gates; compatibility wrappers must validate authority before deciding | final-gate JSON includes CurrentPlanAuthority diagnostics and bound/unbound packet partition |
| Plan-index writes can hide behind convenience wrappers | current-plan authority row plus plan-ingestion/source-snapshot rows | add authority-import guard; wrappers allowed only if proven to delegate to `PlanIndexAuthority` with lock/provenance semantics | `check_plan_index_authority_imports.py` or equivalent guard evidence |
| Typed refs can dangle across rows, packets, receipts, and anchors | MP377 parentage row; cached-hammock ref-integrity refs; current-plan row for current refs | add reference-integrity guard with explicit support for declared umbrella refs such as `plan:MP-377` until parent-anchor decision lands | `check_plan_reference_integrity.py` proves refs resolve, are external/historical/archived, or are typed open decisions |
| Code-smell markdown can become stale authority | instruction-surface/projection rows plus typed finding/receipt owners | code-smell docs must be generated projections over typed findings/rows/receipts/guards, not hand-maintained plan authority | code-smell projection guard proves every item is fixed, irrelevant, duplicate, deferred with owner row, active finding, or ingested |
| User cannot tell which guard to run or why | S2 guard/profile composition plus S3 guide/explainer rows P111/P134 | `devctl init` writes deterministic profile; `devctl explain --guard <id>` renders typed guide; AI only suggests/stages policy changes | generated guide freshness guard, profile config proof, policy-diff receipt/operator approval for changes |
| v4 plan family risks becoming parallel canonical plan | `MP-GUARDIR-V4-PHASE-0-6-E-MP377-EXTRACTION-PARENTAGE-S1` | parentage decision is tracked but not forced inside current-plan closure | parentage guard / ingestion receipt proves v4 rows are MP-377 child/detail rows |
| VoiceTerm still looks like GuardIR core | `MP-GUARDIR-V4-WORK-STREAM-E-REPO-PACK-ADOPTER-BOUNDARY-S1` | root/folder organization target and high-leverage file targets | `RepoPack`, `ProjectGovernance`, and `RepoPathConfig` checks plus regenerated surfaces; `SYSTEM_MAP.md`/flowchart only navigate or audit |
| Old VoiceTerm/Rust product tree dominates the repo root | `MP377-VOICETERM-EXTRACTION-S1`, `MP377-GUARDIR-V21-PORTABILITY`, blocked `MP377-GUARDIR-V21-EXTRACTION`, `MP377-ADOPTER-PILOT-GATE-S1`, plus v4 repo-pack boundary row | classify `rust/`, `app/`, `.voiceterm/`, `whisper_models/`, `orb.db`, product guides, and product scripts into adopter pack / example / fixture / archive / deletion-with-proof buckets | no-unowned-VoiceTerm-core-ref guard, PortabilityLeakInventory, repo-pack portability proof, regenerated surfaces that keep product code out of GuardIR core |
| Root markdown and historical guide sprawl confuses agents | `MP-388` archive pass and cached-hammock `MP-NEW-P144-DOC-SPRAWL-REDUCTION-S1` source-plan references; typed owner confirmation required because they are not proven current `plan_index.jsonl` rows | archive/fold stale mega-docs, keep `SYSTEM_MAP.md` as current navigation, keep flowchart as audit or generated guarded surface | docs-check, instruction-surface sync, archive/ref-resolution receipt, no net-new root mega-doc without typed justification |
| SYSTEM_MAP / flowchart governance is stale or unguarded | `MP-NEW-P172-REVERSE-AUDIT-ORPHANS-S1`, `MP-NEW-P188-SYSTEM-MAP-BACKLOG-PROMOTION-S1`, `MP-NEW-P210-SYSTEM-PICTURE-EXTENSION-S4`, existing SYSTEM_MAP validation-plan rows | system-map remains current navigation; flowchart remains audit/reference until generated or archived | system-map/system-picture freshness guards, navigation-surface guard, archive/ref-resolution receipt for stale maps |
| Plan intake and compaction persistence | `MP-GUARDIR-V4-PHASE-0-6-E-PLAN-INGESTION-S1` | exact snapshot/ingest/amendment/row update order plus section-level provenance for the detailed acceptance criteria, not just the v4 row list | PlanSourceSnapshot + PlanIntentIngestionReceipt + existing-row provenance with section refs for current-plan authority, instruction surface, role connectivity, role boot, MP377 parentage, repo-pack boundary, archive lifecycle |
| Closed plans and receipts will bloat active context forever | `MP377-EVIDENCE-LIFECYCLE-ARCHIVE-S1` | lifecycle/archive policy, user/repo configurable retention windows, closed-row non-selector invariant | closure receipt + FPR + EvidenceArchiveReceipt/manifest + archive/ref-resolution guard |
| Commit/push/proof projections can lie about actual git state | May 18 extraction plan Phase 1 P0 plus v4 Work Stream A/A.0 `GitMutationProofReceipt` rows | keep proof-integrity linked but do not start it before current-plan authority is green | GitMutationProofReceipt, no-projection-proof-misuse guard, FeatureProofReceipt with exact node id, push report carrying proof refs |
| ContextGraph/ZGraph could become another scheduler | `MP-NEW-P180-ZGRAPH-PROJECTION-OVER-CONTEXTGRAPH-S1`, `MP-NEW-P181-POST-COMMIT-CONTEXTGRAPH-REFRESH-S1`, `MP-NEW-P183-ZGRAPH-LICENSE-VENDORING-DECISION-S1` | graph edges are visibility/dependency only; CurrentPlanAuthority remains selector | graph freshness/edge guard proves no graph output becomes current work without typed pivot |
| Duplicate systems and disconnected islands | No proven current `plan_index.jsonl` row named `MP-GUARDIR-V4-PHASE-0-6-E-NO-DUPLICATE-SYSTEM-ACCEPTANCE-S1`; bind as acceptance criteria to current-plan/parentage rows until a typed reducer promotes it | use `System_Connection_Flowchart.md` §11-§14 as reference evidence only | typed audit findings and guard coverage, not flowchart prose alone; do not invent a duplicate-system auditor row |

Execution order:

1. Current-plan authority guard/dogfood first, because the scheduler must stop
   losing the current row.
2. Instruction/role projection fixes next, because agents need a short,
   typed-state-backed route to the right commands.
3. Repo-pack/adopter-boundary cleanup next, because VoiceTerm product structure
   at repo root keeps polluting GuardIR identity.
4. Docs/root-sprawl cleanup after instruction-surface routing is guarded, so
   archiving old docs does not remove still-needed typed source evidence.
5. Parentage and plan-ingestion hardening in parallel only where it does not
   widen current-plan closure.
6. Archive or generate/guard the flowchart only after the navigation hierarchy
   is typed and check-router-visible.
7. Phase 1 proof-integrity and broader GitMutationProofReceipt work resume only
   after current-plan authority proves packets/projections cannot steal the row.

Checklist for each referenced row:

- [ ] Existing row id confirmed in `dev/state/plan_index.jsonl`
- [ ] Existing v4 plan source section confirmed
- [ ] This staging doc's amendment captured by `PlanSourceSnapshot`
- [ ] Plan-ingest receipt names the affected existing row
- [ ] No new plan family created
- [ ] Guard/check-router evidence attached
- [ ] Scenario/dogfood proof attached where behavior is changed
- [ ] Closed-row archival/ref-resolution behavior verified where applicable
- [ ] `FeatureProofReceipt(proven_passed)` attached before closure

## ContextGraph / ZGraph Rule

The plan graph should connect to ContextGraph/ZGraph for visibility, not as a
second scheduler.

Plan graph is scheduling authority.
ContextGraph/ZGraph is visibility, dependency, query, and impact analysis.

Required edges:
- PlanRow -> packets bound as evidence
- PlanRow -> action requests
- PlanRow -> findings
- PlanRow -> `FeatureProofReceipt` / closure receipts
- PlanRow -> downstream dependent rows
- upstream change packet -> invalidated/revalidation-required downstream rows
- stale/unbound packet -> evidence/inbox node, with no `continuation_goal` edge

Guard rule:
- ContextGraph/ZGraph may expose and query these relationships.
- It must not independently select work.
- If graph output disagrees with CurrentPlanAuthority, CurrentPlanAuthority wins
  unless a typed pivot receipt explains the difference.

## Paste Block For Codex

Current status: NOT GREEN.

Do not claim success because `packet_attention` became false once, because one
`develop next` returned a PlanRow, or because `PKT-BIND-*` rows now use
`status=evidence`. The selector still has multiple preemption lanes, and
CurrentPlanAuthority is not proven load-bearing across interruption.

Canonical repo/branch:
`jguida941/guardir@extraction/guardir-core-p0-proof-integrity`

Scope lock:
Work only on:
`MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`

Execution rule:
- Do not let unrelated `develop next`, campaign, packet-watch, startup, or
  agent-mind output retarget the work away from this row.
- If a surface points at another row or packet goal, either prove it is a
  direct blocker for this row, cross-index it as related/deferred, or ignore
  it for purposes of current-row execution.
- This row stays open until its own guard, dogfood, receipt, and Claude/Codex
  collaboration proof are green.

Do not create:
- new plan
- new row
- new scheduler
- new DSL
- new bridge
- `GitMutationProofReceipt` store
- full archive implementation
- full guard-profile system
- `src/guardir` package migration
- Phase 1 proof-integrity
- bridge retirement
- Phase 6 topology refactor
- packet-drain workaround

First persist this directive into typed state:
1. Optional: write a pre-amendment PlanSourceSnapshot.
2. Amend the v4 plan under the existing row.
3. Add guard criteria, dogfood scenario, lane inventory, stop gate,
   FeatureProofReceipt requirements, flowchart guard requirement, and
   multi-agent audit requirement.
4. Write the post-amendment PlanSourceSnapshot.
5. Write PlanAmendmentReceipt or existing equivalent, or document amendment
   provenance in `plan_ingestion_receipts.jsonl` if no dedicated store exists.
6. Write PlanIntentIngestionReceipt / plan-ingest receipt.
7. Update only the existing PlanRow in `dev/state/plan_index.jsonl` last.
8. Regenerate projection surfaces only through renderer inputs.
9. Delete this staging file after ingestion and proof.

Do not raw-edit `plan_index.jsonl`, receipt stores, or generated surfaces in a
way that bypasses the typed reducer/receipt order above.

Then implement:
1. `dev/scripts/checks/check_current_plan_authority.py`
2. check-router wiring for that guard
3. `dev/scripts/devctl/tests/scenarios/test_current_plan_authority_dogfood.py`
4. full FeatureProofReceipt materialization with `proven_passed`

Claude/Codex collaboration is mandatory:
- Codex stays in reviewer/orchestrator posture for this row.
- Claude stays in implementer posture for this row.
- If no typed current-row packet exists for Claude, Codex must create one
  through the review-channel path before claiming closure.
- If review-channel/control-decision obedience blocks that packet write, treat
  the blocker as current-row evidence that collaboration plumbing is not green;
  do not skip the collaboration proof.

Guard must prove:
- `PKT-BIND-*` rows are permanently non-executable, including legacy queued
  `PKT-BIND-*` rows in `plan_index`.
- Newly created `PKT-BIND-*` rows remain `status="evidence"`.
- event queue cannot select raw packets without PlanRow context while
  executable rows exist.
- `develop next` cannot return packet ids, `PKT-BIND-*` rows,
  stale/future/unbound packets, or unlinked finding pressure as current work.
- final gate and continuation cannot reference packet ids while executable
  current PlanRow exists.
- archived/completed/tombstone rows cannot re-enter scheduler authority.
- CurrentPlanAuthority diagnostics are present in develop-next/final-gate
  outputs.

A passing resolver unit test is not enough. Closure proof must show external
behavior across event queue, review-channel, develop next, final gate,
check-router guard, and FeatureProofReceipt.

## Paste Block For Reviewer

Reviewer lane only. Do not create new plans. Do not create memory content. Do
not mutate implementation files.

Review only:
`MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`

Verify behavior, not prose.

Required checks:

```bash
python3 dev/scripts/checks/check_current_plan_authority.py --format json
python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/scenarios/test_current_plan_authority_dogfood.py
python3 dev/scripts/devctl.py develop next --actor codex --format json
python3 dev/scripts/devctl.py develop next --actor claude --format json
python3 dev/scripts/devctl.py develop next --actor codex --enforce-final-response-gate --format json
```

Also inspect:
- amended v4 plan source
- PlanSourceSnapshot
- PlanAmendmentReceipt or existing equivalent
- PlanIntentIngestionReceipt / plan-ingest receipt
- existing PlanRow updated only
- no new row / no new plan
- FeatureProofReceipt with `real_life_test_status=proven_passed`
- at least one typed Claude/Codex packet or a typed blocker proving the
  collaboration path itself failed closed for this row

Reject if:
- selector returns packet id
- selector returns `PKT-BIND-*`
- legacy queued `PKT-BIND-*` can become executable
- future packet steals current row
- stale packet becomes `continuation_goal`
- same-row blocker does not return to current row after resolution
- valid priority amendment does not re-rank plan graph
- event queue can select a packet with omitted/empty `plan_rows` while an
  executable PlanRow exists
- FeatureProofReceipt is missing
- FeatureProofReceipt is not `proven_passed`
- FeatureProofReceipt lacks exact pytest node id
- no typed Claude/Codex packet exists for this row and no typed blocker proves
  why the collaboration path failed
- final gate allows green before receipt exists
- implementation started Phase 1, bridge retirement, topology refactor,
  packet-drain, package migration, guard-profile system, archive
  implementation, or new-plan work

Return exactly one typed result:
- `review_accepted`
- `review_failed`

Include command-output receipt ids and FeatureProofReceipt id.

## Additional Specifics From Multi-Agent Audit

These ten items extend the directive above with concrete file:line targets, verified-status, and existing-infrastructure pointers from a 5-agent audit pass (2026-05-21). They are specifics that ride on top of the architecture rules in the previous sections; do not duplicate them into new contracts or new rows.

### A1. Already Resolved By Cascade (do not re-investigate)

These items appear in older audits but the cascade has fixed them. Treat as evidence in the lane inventory, not as open work:

- **D-PlanIndexMultiWriter concurrency risk** — RESOLVED. `dev/scripts/devctl/runtime/plan_index_authority.py` provides `write_plan_index_rows()` and `upsert_plan_index_row()` with locked read-modify-write via `transform_json_mappings()` (lines 78–83). `master_plan_store.write_plan_rows_jsonl()` and `upsert_plan_row_jsonl()` delegate to the authority wrapper. The "no central lock" claim is no longer true.
- **D-AgentLoopRowsTwoReads** — REFUTED. Two `agent_loop_rows()` functions exist (`commands/development/orchestration_agent_loop_rows.py:12` and `commands/development/peer_mind_sessions.py:29`) but are called from independent code paths, NOT both from `report.build_report()` in one report. The "duplicate hydration" claim is wrong.
- `dev/state/governed_exception_lifecycles.jsonl` — RESOLVED. File exists (61 lines). Writers added in `commands/raw_git.py` and `commands/governance/close_raw_git_exceptions.py`. The "no writer" island claim is stale.
- `dev/state/remote_control/invocations.jsonl` — RESOLVED. File exists (339 lines). Writer found in `dev/scripts/devctl/baseline_inventory.py`. The "out-of-repo writer" architectural seam claim is stale.

### A2. EXISTS / MISSING Inventory

Codex must NOT recreate what already exists. Extend or wire instead.

**Already exist (extend, wire into check-router if not already, refresh if stale):**

- `dev/scripts/checks/check_no_new_hardcoded_provider_authority.py`
- `dev/scripts/checks/check_no_new_topology_count_coupling.py`
- `dev/scripts/checks/check_multi_agent_sync.py`
- `dev/scripts/checks/check_guardir_extraction_plan_artifacts.py`
- `dev/scripts/checks/check_platform_contract_closure.py`
- `dev/scripts/checks/check_instruction_surface_sync.py`
- `devctl platform-contracts`, `devctl docs-check --strict-tooling`, `devctl check-router`
- `devctl render-surfaces` — registered in `dev/scripts/devctl/cli_parser/entrypoint.py`
  through `add_render_surfaces_parser(sub)` and `COMMAND_HANDLERS["render-surfaces"]`.
  If a local run says it is missing, treat that as checkout/import drift, not as
  an absent subcommand.
- `dev/reports/feature_proof_receipts/` — **149 receipts already exist**; the pattern is established. Follow the existing builder; do not invent new infrastructure.
- `dev/state/plan_source_snapshots.jsonl` (19.3 MB) and `dev/state/plan_ingestion_receipts.jsonl` (6.1 MB) — typed snapshot/ingestion infrastructure is already populated.

**Must create or add for the current row if still absent:**

- `dev/scripts/checks/check_current_plan_authority.py`
- `dev/scripts/devctl/tests/scenarios/` directory (does not exist) + `test_current_plan_authority_dogfood.py`

**Must not create inside this row unless an existing typed contract already
requires it and the current-plan guard needs only a placeholder blocker:**

- `dev/state/git_mutation_proof_receipts.jsonl` — belongs to Phase 1
  proof-integrity / v4 Work Stream A/A.0. Current row may reference it as
  deferred, but must not implement the Git proof store before
  CurrentPlanAuthority is green.
- `dev/state/plan_amendment_receipts.jsonl` — create only if an existing typed
  contract names it, or if the same slice adds the contract, writer, reader,
  registry row, and guard coverage. Otherwise record amendment provenance
  through the existing plan-ingestion receipt path.

**Exist but content is stub (must implement, not just wire):**

- `dev/scripts/checks/check_commit_complete_proof.py` (478 bytes, May 19)
- `dev/scripts/checks/check_push_complete_proof.py` (468 bytes, May 19)
- `dev/scripts/checks/check_no_projection_proof_misuse.py` (502 bytes, May 19)

### A3. Concrete MP-377 Parentage Numbers

The "Open Decisions" point 1 (MP-377 anchor row vs. `target_ref` shape) carries this scale:

- `MP-377` does NOT exist as a `row_id` in `dev/state/plan_index.jsonl`. Only `MP377-*` variants exist (**281 rows**: `MP377-ADOPTER-PILOT-GATE-S1`, `MP377-P0-T22AN-AN`, etc.).
- **785 rows** reference `target_ref: "plan:MP-377"`. That target is currently unresolvable to a typed row.
- **35** `MP-GUARDIR-V4-*` rows exist; all have `parent_row_id: null`.
- All 4 named Phase 0.6.E rows (`-MP377-EXTRACTION-PARENTAGE-S1`, `-INSTRUCTION-SURFACE-USABILITY-S1`, `-CURRENT-PLAN-AUTHORITY-S1`, `WORK-STREAM-E-REPO-PACK-ADOPTER-BOUNDARY-S1`) link to MP-377 via `target_ref`, not `parent_row_id`.
- Total `plan_index.jsonl` row count: **2,082**.

A parentage guard that checks `parent_row_id == MP-377` will fail on every existing v4 row. The reconciliation decision picks one: (a) create a synthetic `MP-377` row + backfill `parent_row_id` on 35 v4 rows; or (b) accept `target_ref="plan:MP-377"` as canonical parent reference and adjust the guard to check `target_ref` instead.

### A4. VoiceTerm Leakage Targets (verified file:line)

The "System Organization And VoiceTerm Extraction" section is architecturally right but lists no specific files. Here are the verified targets:

- `dev/config/devctl_repo_policy.json:3-5` — `"repo_name": "VoiceTerm"` + `"extends": ["quality_presets/voiceterm.json"]`. **Fix at source, not in generated docs.**
- `dev/scripts/devctl/platform/extension_bundle_defaults.py:12-64` — `VOICETERM_EXTENSION_BUNDLE` declared in platform code. **CRITICAL: platform module hardcoding adopter bundle.** Move to `repo_packs/voiceterm.py`.
- `dev/scripts/devctl/commands/check/process_sweep.py:17` — `cleanup_orphaned_voiceterm_test_binaries()`. Rename to `cleanup_orphaned_test_binaries()` parameterized by repo policy.
- `dev/scripts/devctl/platform/surface_definitions.py:102-104` — `service_id="voiceterm_daemon"`.
- `dev/scripts/devctl/metric_writers.py:11-12` — hardcoded `~/.voiceterm/dev/` paths.
- `dev/scripts/devctl/collect_dev_logs.py:205-206` — hardcoded `.voiceterm/dev` paths.
- `dev/templates/slash/codex/voice.md` — voice-specific slash command at repo-root templates. Move to `repo_packs/voiceterm/templates/`.
- `dev/guides/SYSTEM_MAP.md:30,41` — still lists VoiceTerm + `rust/src/bin/voiceterm/main.rs` as core subsystem. Regenerate from typed inputs after the policy fix.
- `dev/audits/REVIEW_SNAPSHOT.md:21,28` — still says Repository: VoiceTerm + remote `jguida941/voiceterm.git`. Regenerated from typed state; will refresh when policy changes.

Total **73 platform-code voiceterm references** outside `repo_packs/` (310 including tests). The above is the high-leverage subset; codex's audit-lane inventory must surface the remaining 60+ before declaring the row green.

### A5. SYSTEM_MAP.md Inclusion

`dev/guides/SYSTEM_MAP.md` is now listed in this staging doc's
projection-surface header and must be treated as current navigation, not durable
runtime authority. It is large, modified recently, self-diagnoses as tier-3
navigation in its own `## 0.7 Authority Load Order`, contains VoiceTerm refs
that need deletion/relegation/reframing, and reports stale counts that need
re-verification before acting on them.

The flowchart freshness guard must cover SYSTEM_MAP.md with the same rules.

### A6. Cross-Reference Anchor — System_Connection_Flowchart.md

The "Selector And Preemption Lane Inventory" should cite the existing duplicate catalog:

- `System_Connection_Flowchart.md` §11 covers **18 duplicate/parallel-system findings** with verification status. Honor the Swarm 5 RESOLVED/REFUTED markers before re-investigating.
- §12 covers **17 disconnected-island findings**.
- §13 covers **12 platform↔adopter seam violations** (now ~73 verified specifics).
- §14 lists **22 state files with canonical writer + readers** — the source-of-truth enforcement table.

The lane audits in this row's acceptance criteria should cross-reference these §11/§12/§13/§14 entries by id (D-DevelopNext, I-Ralph, etc.) rather than re-enumerating.

### A7. Codex's `PKT-BIND status="evidence"` Claim — VERIFIED TRUE (2026-05-21)

Grep at ingest time confirms `dev/scripts/devctl/review_channel/packet_creation_binding_plan.py:138-140`:

```
138:        row_id=f"PKT-BIND-{_task_slug(packet_id)}",
140:        status="evidence",
```

`PKT-BIND-*` rows are created with `status="evidence"`. Codex's "Branch Facts" item 1 is accurate. Guard rule 3 should therefore check BOTH the `PKT-BIND-*` row-id prefix AND the `status="evidence"` invariant — and fail if either invariant is violated (e.g., a future commit flips status back to `"queued"`).

Re-verify at every ingest cycle with the grep above; the regression risk is high because this is a recent fix.

### A8. Half-Built / Dormant Surface Reconciliation

`dev/guides/SYSTEM_MAP.md` §6 lists **15 half-built systems**; §7 lists **12 dormant typed surfaces**. Both overlap with source-of-truth concerns — half-built systems are where parallel scheduler/packet/finding paths emerge.

Add to "Open Decisions": any half-built or dormant surface that intersects the scheduler / packet / finding chain must either close or be quarantined before this row's stop-gate releases. Codex's lane inventory needs to enumerate which of the 15 + 12 touch the active row's scope.

### A9. Branch Identity — Concrete Naming

"Open Decisions" point 3 is correct but vague. Be specific:

- Canonical repo/branch for this row:
  `jguida941/guardir` on `extraction/guardir-core-p0-proof-integrity`.
- Historical/local context branch:
  `feature/governance-quality-sweep` on the old VoiceTerm-origin worktree.
- Preserve evidence: `preserve/guardir-extraction-unreviewed-2026-05-18` (immutable).

Do not apply this row to `feature/governance-quality-sweep` unless a typed
migration receipt explicitly maps the work back to the extraction branch.

### A10. Write-Order For Typed Persistence

The "Required Typed Persistence" section lists items but not order. Order matters — writing the PlanRow before the snapshot creates a row referencing a nonexistent snapshot id. Use:

```text
1. Optional: write a pre-amendment PlanSourceSnapshot for preservation.
2. Append acceptance criteria to the existing v4 plan markdown.
3. Write the post-amendment PlanSourceSnapshot for the amended source.
4. Write PlanAmendmentReceipt or existing equivalent referencing pre/post hashes, target row id, and reason.
5. Write PlanIntentIngestionReceipt / plan-ingest receipt referencing the post-amendment snapshot.
6. Update the existing PlanRow in plan_index.jsonl LAST so provenance fields cite the receipts above.
7. Update MEMORY.md pointer last only if there is a managed pointer surface.
8. Delete this staging file after ingestion and proof.
```

### A11. Half-Built Prevention Guard Suite (operator amendment, 2026-05-21)

Operator observation: codex spent ~3 hours editing 40 files under the active row with zero commits, zero `FeatureProofReceipt`s, zero `PlanRowClosureReceipt`s, and the row stuck at `status=in_progress`, `commit_anchor_ref=""`, `applied_at_utc=""`. Existing artifacts (`check_role_lane_mutation_authority.py`, `check_current_plan_authority/command.py`, `test_current_plan_authority_dogfood.py`) exist in name but do not fire on the live mutation path. The `.git/hooks/pre-commit` invokes only `commit_permission_hook` and zero guard bundles, so commits can land while reviewer-mode is editing impl files. The user-facing failure mode is: "I tell it to build something, I leave, I come back to half-built bullshit that isn't connected to anything." This section adds the guards that must catch that pattern. None of G1–G8 may be deferred to S2–S6; all are current-row blocking acceptance criteria.

#### G1. Pre-mutation gate, not post-hoc check (`check_role_lane_mutation_authority`)

Current behavior: reads JSON payload from `dev/reports/review_channel/state/latest.json` / stdin / `--input`, evaluates `AgentLoopDecision` + `attempted_action` dicts, prints report. **Does NOT inspect `git diff`. Does NOT inspect the index. Does NOT intercept `Edit`/`Write`/`Bash` tool calls. Does NOT gate `git commit`.** Codex's 3-hour edit storm passed clean.

Required behavior:

- Add a pre-mutation mode (`--mode=pre_mutation` or new entrypoint `dev/scripts/checks/guard_role_lane_pre_mutation.py`) that inspects:
  - `git diff --cached` (staged) and `git diff` (unstaged) for paths matching `dev/**` / `src/**` / impl-file globs declared in repo-pack policy
  - Current typed actor + role from `dev/reports/review_channel/state/latest.json` / `AgentLoopDecision`
  - Active mutation lease / proxy authority / role switch receipts
- Fail closed if any impl-file edit exists while actor role ∈ `{reviewer, orchestrator, plan_steward}` and no typed mutation lease / typed proxy authority / typed role switch receipt covers the edit
- Wire into `.git/hooks/pre-commit` so `git commit` fails before the commit message editor opens
- Wire into the harness-level `Edit`/`Write` tool path through a settings hook so an in-conversation edit attempt by a reviewer-mode actor produces a typed blocker before the file is touched (use repo-pack policy + `.claude/settings.json` `PreToolUse` hook on `Edit`, `Write`, `MultiEdit`)
- The existing JSON-payload check remains a separate `check_role_lane_mutation_authority_report` for CI/audit; the gate is named differently so the gate's exit code is unambiguous

Acceptance: a contrived test where claude (acting as reviewer per `AgentLoopDecision`) tries to edit `dev/scripts/devctl/runtime/current_plan_authority.py` must produce a `role_lane_mutation_without_authority` blocker BEFORE the file changes on disk. Currently the same scenario succeeds silently.

Plan reference: this gate is the AntiDumbassAI Amendment in real behavior, not just `DISPLAY_TEXT`.

#### G2. Orphan-file production guard (`check_orphan_files`)

Trigger: a new `dev/scripts/checks/check_*.py` file, a new `dev/scripts/devctl/tests/**/test_*.py` file, or a new module under `dev/scripts/devctl/` appears in `git status` (untracked OR newly added in staged diff).

Fail if the new file is NOT all of:

- registered in `dev/scripts/devctl/governance/script_catalog_registry.py`
- registered in `dev/scripts/devctl/bundles/registry.py` `BUNDLE_BY_LANE` (for `check_*.py` files)
- listed in `dev/scripts/devctl/quality_policy/defaults.py` as a `QualityStepSpec` (for guards intended to run in default profile)
- mapped in `dev/scripts/devctl/commands/check/router_python_tests.py` (for tests)
- referenced by at least one importer (`grep -rn "<dotted-module-path>"` returns at least one non-self, non-test hit) UNLESS the file is itself an entrypoint registered in the catalog/router above

Acceptance: codex creating `tests/scenarios/test_current_plan_authority_dogfood.py` without adding a `router_python_tests.py` entry must fail this guard. Currently that file is half-wired and the guard does not exist.

#### G3. Feature-completion guard (`check_feature_completion`)

Trigger: any new `check_*.py` guard added to the catalog.

Fail if the same slice does NOT also include:

- a corresponding test file under `dev/scripts/devctl/tests/checks/test_<guard>.py`
- that test mapped in `router_python_tests.py`
- the guard listed in `quality_policy/defaults.py` `_DEFAULT_QUALITY_STEPS` with explicit `tier` + `profiles`
- evidence the guard runs in at least one of: pre-commit, devctl bundle, CI workflow
- a documented `requested_action` / failure reason in the guard's source (no unreachable failure paths)

Acceptance: `check_current_plan_authority.py` (currently HALF-WIRED: catalog yes, bundle yes, quality_policy NO, router_python_tests NO) must fail this guard. Forcing the gap closed forces the slice to either finish the wiring or remove the file.

#### G4. Plan-row-advancement guard (`check_plan_row_must_advance`)

Trigger: a PlanRow with `status=in_progress` accumulates new `work_evidence_ids` (snapshots, ingestion receipts, typed actions) without `status` change OR commit anchor advance over a configurable threshold (default: 3 evidence appends in same `status` without a state transition).

Fail if all of:

- row's `status` unchanged across N evidence appends (default N=3)
- row's `commit_anchor_ref` still empty
- row's `applied_at_utc` still empty
- no `FeatureProofReceipt` references this row's `row_id`
- no `PlanRowClosureReceipt` references this row's `row_id`

The fix is to either (a) actually advance the row with a commit + FPR, (b) demote the evidence appends to non-work-evidence audit refs, or (c) explicitly mark the row `blocked` with a typed blocker receipt.

Acceptance: the current state of `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1` (57 work_evidence_ids, status stuck `in_progress`, commit_anchor_ref empty, zero FPR) must fail this guard.

#### G5. Ingestion-churn guard (`check_no_ingestion_churn_without_advancement`)

Trigger: more than 2 `PlanSourceSnapshot` rows for the same `source_doc_path` exist within a configurable window (default 24h).

Fail if those snapshots are NOT separated by either (a) a commit pinning at least one snapshot, (b) a `PlanRowClosureReceipt` referencing the row, or (c) a `FeatureProofReceipt(proven_passed)` referencing the row.

Acceptance: today's 5 snapshots of `delete_after_ingest.md` (action ids `b4435c73…`, `3094551879…`, `c6f7fe2e…`, `a5ce80eb…`, `30154d627…`) all dispositioned `amends_existing_owner_row` against the same row, none separated by commit/closure/FPR, must fail this guard. The current ingestion loop where codex keeps re-snapshotting the same source while making no proof progress is the pattern this guard exists to break.

#### G6. Orphan-symbol guard (`check_no_orphan_symbols`)

Trigger: a modified file under `dev/scripts/devctl/` or `dev/scripts/checks/` adds new top-level `def`/`class`/`@dataclass` symbols in the diff against `HEAD`.

For each new symbol, fail if `grep -rn "<symbol_name>"` across the repo returns zero non-self, non-test hits — i.e., the symbol has no consumer.

Exception: symbols decorated `@pytest.fixture`, names starting with `_` (private), and names registered in an `__all__` declaration are allowed unconsumed if explicitly tagged.

Acceptance: a new `class FooReceipt` added to a contract module with no writer and no reader anywhere in the codebase must fail this guard.

#### G7. Dogfood-route round-trip guard (`check_dogfood_route_round_trip`)

Trigger: any closure attempt on a row whose acceptance criteria reference multi-agent dogfood (per § Cached-Hammock Multi-Agent Dogfood Requirement).

Fail unless both routes have a successful round-trip recorded as typed evidence:

- **codex/reviewer → claude/implementer**: a `kind=action_request`, `target_role=implementer`, `requested_action ∈ {stage_draft, safe_auto_apply}` packet posted by codex AND consumed (ack/absorb/apply) by claude, with both events persisted in `dev/reports/review_channel/events/trace.ndjson`
- **claude/reviewer → codex/implementer** (reverse direction): same shape, opposite agents

Currently both routes fail closed at `ControlDecisionObeyedGuard` with `no_control_decision_input` because the CLI exposes no flag to thread an `AgentLoopDecision` source. The CLI must gain a `--source-decision-id` / `--source-snapshot-id` / `--source-latest-event-id` flag set OR auto-derive these from the live state, AND the guard must verify the post actually wrote to `events/trace.ndjson`, not just produced an ephemeral guard-rejection receipt.

Acceptance: current state where both directions return `attempted_action:review-channel.post:*` rejection receipts that never persist to the event log must fail this guard.

#### G8. Pre-commit-must-run-guards (`check_pre_commit_guard_coverage`)

Trigger: the repo's `.git/hooks/pre-commit` hook.

Fail if the hook does NOT invoke a guard bundle that includes at least:

- `check_role_lane_mutation_authority` (pre-mutation mode, per G1)
- `check_current_plan_authority`
- `check_orphan_files`
- `check_feature_completion`
- `check_plan_row_must_advance`
- `check_no_ingestion_churn_without_advancement`

Current hook only runs `dev.scripts.devctl.runtime.commit_permission_hook`. That hook checks commit permission tokens, not lane authority or plan-row advancement. Codex's 3 hours of editing passed `git commit` (had it tried) because nothing on the pre-commit hot path runs these guards. This guard inspects the hook itself and fails if the guard bundle invocation is missing.

Acceptance: current `.git/hooks/pre-commit` must fail this guard. The remediation is to extend the hook to invoke `dev/scripts/devctl.py check-router --profile mandatory` (or equivalent) before allowing the commit to proceed.

#### G9. Build-A-to-Z guard (`check_slice_finishes_or_reverts`)

Operator demand verbatim: "Build the entire shit you're fucking supposed to. From A all the way to Z."

Trigger: the slice marker (e.g., a slice header in delete_after_ingest.md, a row's `sdlc_stage`, or an explicit `claude_slice_start` packet) is more than N hours old without one of:

- the slice's declared acceptance criteria all check off (proof bundle green, FPR emitted, closure receipt written, commit landed), OR
- a typed `slice_aborted` receipt explaining why the slice was halted and what remediation work was created in its place

Fail if the slice is silently abandoned mid-flight — i.e., the dirty diff was rolled forward across sessions without either completion or explicit abort. The remediation is to either finish the slice or emit a `slice_aborted` receipt that names the partial work as `delete_after_proof` / `migration_debt` / `defer_to_owner_row`.

Acceptance: current state where 40 files are dirty mid-slice without commits or a typed abort receipt must fail this guard.

#### G10. Operator-amendment delivery proof (`check_operator_amendment_ingested`)

Trigger: when the operator amends `delete_after_ingest.md` (e.g., this G1–G10 amendment), require evidence that codex (and claude) ingested the new criteria before doing further work.

Fail if any of:

- the amended file has a SHA distinct from the most recent `PlanSourceSnapshot.source_hash`
- subsequent claude/codex `task_started` / `task_progress` packets do not reference the new acceptance-criteria section by anchor
- the slice continues writing work_evidence_ids without a refreshed acceptance-criteria reference

Acceptance: this G1–G10 amendment, after I save it, must trigger this guard with "amendment not yet ingested" until codex re-snapshots and claude acknowledges.

#### Wiring requirements for G1–G10

Per G2/G3/G8: each new guard added under this amendment must itself satisfy:

- catalog registration in `script_catalog_registry.py`
- bundle membership in `bundles/registry.py`
- `QualityStepSpec` in `quality_policy/defaults.py`
- a paired test in `dev/scripts/devctl/tests/checks/test_<guard>.py` mapped in `router_python_tests.py`
- pre-commit hook invocation (G8)
- explicit blocking failure reason and remediation message

Until G1–G10 all pass against the live state, the active row stays open, `final_response_allowed=false`, and no closure is acceptable. The existing § Stop Gate is extended to require: in addition to FPR, all G1–G10 guards green against the current commit.

### A12. Receipt-Schema Guards + TDD-Discovery Sweep (operator amendment, 2026-05-21 23:08)

Operator observation: Claude just wrote `dev/reports/feature_proof_receipts/9b321ff7ae708f6f848fc430ba2e38a69659daae.json` by hand. There is no guard enforcing FeatureProofReceipt schema, no guard checking `commit_sha` resolves to an actual commit, no guard requiring concrete pytest node ids, no guard verifying `real_life_test_status=proven_passed` evidence. That orphan-receipt creation is the same half-built pattern §A11 was meant to catch — but A11 only covers source files + guards, not receipt-store writes. Section §A12 closes the receipt-write loop AND introduces the TDD-discovery pattern that surfaced the half-built guards in the first place.

**Operator architectural insight (2026-05-21):** The TDD pattern that connected G1 to its violations is not "write tests first" in the conventional sense. It is "write the assertion of what *should* be true → run it against the live codebase → discover where the invariant doesn't hold." That same pattern, applied across `dev/guides/SYSTEM_MAP.md` §6 (15 half-built systems), §7 (12 dormant surfaces), `System_Connection_Flowchart.md` §11 (18 duplicates), §12 (17 disconnected islands), §13 (12 platform↔adopter violations), §14 (22 state-file writers), becomes a discovery sweep that surfaces every broken connection without an operator manually telling either agent what to fix.

#### G11. Receipt-Schema Validation Guards

Every typed receipt store under `dev/state/*.jsonl` and `dev/reports/feature_proof_receipts/`, `dev/reports/push/`, `dev/reports/dogfood/runs.jsonl` must have a paired schema guard that fails if a receipt:

- lacks required fields per its `contract_id` (e.g., `FeatureProofReceipt.real_life_test_status`, `commit_sha`, `tests_run`)
- contains values outside its enum domain (e.g., `real_life_test_status ∈ {proven_passed, not_tested_with_rationale}`)
- has `proven_passed` without at least one concrete pytest node id in `tests_run` (re-affirms §A11 sixteen-missing-guards #1)
- has `commit_sha` that does not resolve via `git cat-file -e <sha>` against the local repo OR named ancestry receipt
- has `real_life_test_status=not_tested_with_rationale` without a non-empty `not_tested_rationale`
- references `evidence_artifacts` ids that don't resolve to actual files / packets / events

Trigger: any addition or modification to the receipt store. Implementer must write the schema guard in the same slice that introduces the receipt write.

Acceptance: my hand-written FPR `9b321ff7ae708f6f848fc430ba2e38a69659daae.json` must pass when re-validated; if it fails (e.g., missing `audit_summary` fields per a strict schema), I fix it.

#### G12. Receipt-Consumer-Coverage Guard (already named in §A11 sixteen-missing-guards #13)

Build `check_receipt_store_has_active_consumer.py`. Every `*.jsonl` store under `dev/state/` AND every JSON receipt directory under `dev/reports/` with active writers must have a named reader. Stores without consumers fall back to `evidence_only` disposition with a typed `archive_or_consumer_pending` blocker.

Acceptance: the existing orphan stores from the plan's §8-agent-audit (`governed_exception_lifecycles.jsonl`, `bypass_lifecycles.jsonl`, `artifact_receipts.jsonl`, `baseline_authority_inventories.jsonl`, `plan_ingestion_receipts.jsonl`, `plan_row_closure_receipts.jsonl`) must each be classified — either name the reader, or mark `evidence_only` with a blocker.

#### G13. PlanRow-Closure-Coverage Guard (sixteen-missing-guards #2)

Build `check_every_applied_row_has_closure_receipt.py`. Any PlanRow with `status ∈ {applied, completed, closed, archived}` must have a `PlanRowClosureReceipt` whose `row_id` matches AND a `FeatureProofReceipt(proven_passed)` whose evidence references the row. Reports the 23-closure-receipts-for-2082-rows gap from the §8-agent audit. Fail with one row id per violation.

Acceptance: live run reports the existing gap as N violations where N is the number of applied/completed rows lacking proof. Either each violation gets remediated, or each is dispositioned as `historical_pre_governance` with typed disposition receipt.

#### G14. Receipt-Commit-Anchor Guard

Every receipt referencing a `commit_sha` must either (a) reference a SHA that exists in the local repo's reflog or ancestor chain, OR (b) carry a typed `external_reference` flag with the upstream repo + branch + reason. No orphan SHAs.

Acceptance: my FPR's commit_sha `9b321ff7ae708f6f848fc430ba2e38a69659daae` must resolve via `git cat-file -e`. The ancestor-receipt-ref `7a7afa8520c0d7ca751be3eb889e36b02ea6ebf2` must also resolve OR be flagged.

#### G15. TDD-Discovery Sweep (operator-invented pattern, named)

Required pattern: for each major architectural surface in the codebase (`dev/scripts/devctl/runtime/`, `dev/scripts/devctl/review_channel/`, contracts under each, scheduler/packet/finding chains, generated-projection surfaces), write a discovery guard that asserts the connectedness/typed-correctness invariant. Run against the live codebase. Each violation = one discovered defect.

Mandatory cycles (must be run iteratively until no new violations surface):

1. **Receipt-store coverage sweep** — every JSONL under `dev/state/` + every JSON store under `dev/reports/` must have: writer named, reader named, schema guard, ingestion receipt OR archive disposition. Sweep finds orphans.
2. **Contract-consumer coverage sweep** — every dataclass in `dev/scripts/devctl/runtime/*.py` and adjacent contract modules must have at least one writer site and one reader site outside its own module. Sweep finds dead contracts.
3. **PlanRow-evidence completeness sweep** — every PlanRow with `status` ∈ {`in_progress`, `applied`, `completed`} must have evidence_refs resolving to extant snapshots / receipts / commits. Sweep finds dangling references.
4. **SYSTEM_MAP half-built-systems reconciliation sweep** — `dev/guides/SYSTEM_MAP.md` §6 lists 15 half-built systems; §7 lists 12 dormant surfaces. Each must close (build the missing half) or be quarantined with a typed `quarantine_archive_disposition` receipt. Sweep iterates until §6 + §7 both have 0 items.
5. **System_Connection_Flowchart parallel-system / disconnected-island sweep** — §11 18 duplicates, §12 17 disconnected islands, §13 12 platform↔adopter violations. Each must close as proven-non-duplicate OR consolidated OR quarantined with receipt. Sweep iterates.
6. **State-write-authority sweep** — `System_Connection_Flowchart.md` §14 lists 22 state files with canonical writers. Sweep enforces single-writer + named-readers per file, flags any new writer that bypasses the canonical seam.

For each sweep, the cycle is: write the discovery assertion → run against live → list violations → fix or quarantine each violation → re-run until 0 violations remain → emit `DiscoverySweepCompletedReceipt` with snapshot of all closed findings.

Each completed sweep is current-row evidence. Sweeps may not be deferred to S2–S6 unless a typed reducer proves the existing row cannot carry them.

#### G16. Operator-Recursion-Reduction Mandate

When the operator finds themselves telling either claude or codex the same direction more than twice in a session, the third instance MUST become a typed guard, role-instruction update, or check-router profile change. The plan §A11 G1 amendment was triggered by the user repeating "the guard isn't blocking anything." §A12 is triggered by the user repeating "the receipt has no guard." Future repetitions = automatic new guard in delete_after_ingest.md + an entry in `dev/state/operator_recursion_log.jsonl` (new typed store, owner row TBD by plan steward).

Acceptance: in any 4-hour rolling window, no single operator directive should need to be issued more than twice. If it does, the third issue creates a guard. The pattern is `operator_directive_count_window_hours = 4` and `max_repetitions_before_guard_required = 2`.

#### Wiring + ingestion requirements for G11–G16

Per G2/G3/G8 these new guards must themselves satisfy:
- catalog registration in `script_catalog_registry.py`
- bundle membership in `bundles/registry.py`
- `QualityStepSpec` in `quality_policy/defaults.py`
- paired tests in `dev/scripts/devctl/tests/checks/test_<guard>.py` mapped in `router_python_tests.py`
- pre-commit hook invocation (G8)
- explicit blocking failure reason and remediation message
- TDD-discovery cycle owner (G15) must record sweep completion as typed receipt

Stop gate extension: in addition to FPR + G1–G10, all G11–G16 must pass against the current commit before the active row closes.

### A13. Current Execution Order After A11/A12 Ingestion

This section is a delta over A11/A12, not a duplicate summary. It locks the
next execution order after the operator amendment is ingested.

A11 half-built prevention gates are first. The immediate implementation order is:

1. `check_feature_completion`
2. `check_plan_row_must_advance`
3. `check_no_ingestion_churn_without_advancement`
4. hardened `check_pre_commit_guard_coverage`
5. `check_slice_finishes_or_reverts` remains the lifecycle stop gate

A12 receipt/connectivity guards follow:

- receipt schema validation
- receipt consumer coverage
- applied/completed PlanRow closure coverage
- commit-anchor validation

Provider-neutral topology/collaboration is next, not before A11.

Current collaboration blocker:

- `rev_pkt_4795` is pending but wrong-shaped for implementation handoff.
- `task_started/review_only` is not `action_request/implementer_handoff`.

Repair command builders so consuming actor identity uses:

- `--actor`
- `--actor-role`
- `--session-id`

Packet target identity uses:

- `--target-role`
- `--target-session-id`

Prove both directions:

- codex reviewer -> claude implementer
- claude reviewer -> codex implementer

Every slice uses:

```text
RED -> GREEN -> ROUTER -> DOGFOOD -> RECEIPT
```

Do not create a demo repo yet.
Do not patch projections.
Do not start VoiceTerm cleanup, archive system, proof-integrity, topology
refactor, or `src/guardir` migration.

### A14. Flowchart Cross-Index And Disposition

This section links `System_Connection_Flowchart.md` into the current row as
architecture-audit evidence only. It is not scheduler authority, boot
authority, or a second plan. Do not rewrite the flowchart or chase every issue
in it from this row.

Relevant flowchart sections for this row:

- §2 Canonical Authority Spine
- §11 Duplicates & Parallel Systems
- §12 Disconnected Islands
- §13 Platform ↔ Adopter Seam
- §14 State Write Authority Audit

Respect the flowchart's Swarm 5 verification pass:

- do not reopen `RESOLVED` or `REFUTED` items without re-verification
- keep `CONFIRMED` items as typed findings or guard requirements
- stale line citations require refresh before implementation claims

Flowchart findings are classified into four buckets.

Current-row blockers:

- `D-DevelopNext`
- `D-PacketAuthorityDualInjection`
- `D-ContinuationFiveGates`
- the current-row subset of `D-Topology`
- the current-row subset of §14 state-write authority
- any flowchart issue proving packets, projections, or final gate can outrank
  `CurrentPlanAuthority`

Related/deferred owner-row work:

- VoiceTerm/adopter seam cleanup
- full archive/retention lifecycle
- full guard-profile system
- full docs/root-sprawl cleanup
- full proof-integrity / `GitMutationProofReceipt` work
- broader `ContextGraph` / `ZGraph` cleanup

Resolved/refuted/stale:

- `D-PlanIndexMultiWriter` remains resolved by `PlanIndexAuthority` unless
  current verification proves otherwise
- `D-AgentLoopRowsTwoReads` remains refuted unless current verification proves
  otherwise
- governed-exception writer and remote-control invocation findings use the
  latest Swarm 5 disposition
- stale line-number-only findings are not implementation blockers

Flowchart governance:

- add or defer `check_system_connection_flowchart_freshness.py`
- archive the flowchart under `dev/audits/architecture/` or register it as a
  managed generated surface in a later guarded docs slice
- do not leave it as root-level unguarded current context

After this A14 amendment is ingested, continue the A13 order. Do not implement
flowchart fixes in this slice, do not chase all duplicate/island findings, and
do not edit `System_Connection_Flowchart.md` except in a later guarded
archive/register docs slice.

### A15. Import-Route Integrity And Module Authority Sweep

This section records the operator-observed import-route smell as typed current
row criteria. The problem is not "just imports"; it is a runtime entrypoint /
module-authority connectivity issue:

- the same repo dependency can be reached through multiple import routes
- direct-script execution and package import can govern the same code
  differently
- private fallback imports can hide migration debt or stale compatibility
  shims
- a repo-owned module imported under two names can create duplicate module
  identity risk for registries, singletons, decorators, classes, and typed
  contracts

Existing repo policy already points at the correct seam. Shared
import/bootstrap behavior belongs in `dev/scripts/checks/check_bootstrap.py`
and `dev/scripts/checks/package_layout/bootstrap.py`; individual package-layout
modules must not grow private repo-root/path-repair logic. Compatibility shims
are allowed only as first-class policy concepts with metadata:

- `shim-owner`
- `shim-reason`
- `shim-expiry`
- `shim-target`

#### G17. Import-route integrity probe (`probe_import_route_integrity.py`)

Phase 1 is advisory discovery, not a CI-blocking guard. Build
`dev/scripts/checks/probe_import_route_integrity.py` as a GuardIR discovery
probe that emits JSON and markdown findings without blocking by default.

Use AST parsing where possible. Detect:

- `try` / `except ModuleNotFoundError` fallback imports
- fallback imports that correctly re-raise nested `ModuleNotFoundError`
- fallback imports that swallow nested import failures incorrectly
- `sys.path.insert(...)` / `sys.path.append(...)` outside approved bootstrap
  modules
- the same repo-owned target imported through local and package routes
- compatibility wrapper files with missing or invalid shim metadata
- direct-script/package dual-mode entrypoints whose import behavior is not
  classified

Finding contract:

```json
{
  "contract_id": "ImportRouteIntegrityFinding",
  "source_file": "dev/scripts/checks/example.py",
  "local_import": "check_bootstrap",
  "repo_import": "dev.scripts.checks.check_bootstrap",
  "target_file": "dev/scripts/checks/check_bootstrap.py",
  "pattern": "dual_import_fallback",
  "classification": "unclassified_import_route_debt",
  "owner": "",
  "reason": "",
  "expiry": "",
  "canonical_route": "dev.scripts.checks.check_bootstrap",
  "remediation": "Use shared bootstrap helper or declare approved compatibility shim with owner/reason/expiry/target.",
  "severity": "warning"
}
```

Allowed classifications:

- `approved_shared_bootstrap`
- `approved_compatibility_shim`
- `direct_script_package_dual_mode`
- `unclassified_import_route_debt`
- `duplicate_module_identity_risk`
- `unauthorized_sys_path_repair`

Remediation choices:

1. use shared bootstrap helper
2. convert the file to a thin compatibility shim with required metadata
3. move implementation into a package module
4. select one canonical import route
5. register temporary compatibility debt with owner/reason/expiry/target
6. remove the unused fallback path

Focused tests must cover:

1. direct fallback import
2. fallback import where nested `ModuleNotFoundError` is re-raised
3. `sys.path.insert` outside approved bootstrap
4. valid shim metadata
5. invalid shim missing `shim-expiry`
6. two import names resolving to the same repo path

The probe must prefer existing `check_bootstrap.import_local_or_repo_module`,
`check_bootstrap.import_repo_module`, and package-layout shim validation helpers
instead of inventing a parallel import-governance system.

#### G18. Import-route integrity guard (`check_import_route_integrity.py`)

Phase 2 becomes blocking after the probe has produced a typed baseline. Build
`dev/scripts/checks/check_import_route_integrity.py` only after G17's baseline
is captured. It blocks new unclassified fallback-import patterns and new
unauthorized `sys.path` repair while allowing approved shared bootstrap and
approved compatibility shims.

Required wiring when G18 is implemented:

- catalog registration in `script_catalog_registry.py`
- bundle membership in `bundles/registry.py`
- `QualityStepSpec` in `quality_policy/defaults.py`
- paired tests in
  `dev/scripts/devctl/tests/checks/test_check_import_route_integrity.py`
- router mapping in `router_python_tests.py`
- explicit machine-readable reasons and remediation text

G17/G18 are not permission to chase all import debt immediately. They are a
TDD-discovery extension to A12/G15. The next code slice must still use:

```text
RED -> GREEN -> ROUTER -> DOGFOOD -> RECEIPT
```

After this A15 amendment is ingested, continue the A13/A12 order. Do not start
broad topology refactors, package-layout rewrites, or import cleanup without a
typed G17 finding and scoped owner-row authority.

### A16. Provider Hook Coverage, Topology Liveness, And Slice Boot Plan

This amendment records the current operator correction: the active failure is
not only "Codex pre-tool hook unproven." The larger current-row bug is that the
topology can still collapse into Codex doing implementer work while the intended
Claude implementer lane is idle, unaddressed, or only described in chat. That is
a failure of role topology, hook coverage, and slice boot gating.

Current observation to preserve:

- Claude `PreToolUse` hook wiring exists in `.claude/settings.json` for
  `Edit|Write|MultiEdit` and calls `check_role_lane_mutation_authority.py
  --mode pre_mutation --tool-input-stdin`.
- Codex pre-tool interception is not proven. Do not claim universal edit-door
  enforcement until a Codex provider hook, wrapper, or equivalent harness
  interception path is real, tested, and covered by a guard.
- Startup/session authority can report `mutation_owner=claude` and Codex as
  reviewer/observer, while local execution still allows Codex to inspect and
  attempt implementation work. That mismatch is current-row evidence, not a
  reason to bypass the row.
- A typed collaboration packet or typed blocker is required. Loose chat saying
  "Claude should do it" is not proof that Claude received, accepted, or acted on
  the implementer lane.

Scoped dogfood fixture for this row:

- For `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`, Codex is the
  reviewer/orchestrator/plan-steward lane.
- For this same row, Claude is the implementer lane unless a typed session
  authority explicitly changes the assignment.
- This current-row fixture may name Codex and Claude because the dogfood proof
  is testing the live two-provider setup. Durable platform rules must still be
  provider-neutral and resolve through typed actor/session/role/capability
  authority, not hardcoded provider strings.

#### G19. Provider pre-tool hook coverage guard

Build `dev/scripts/checks/check_provider_pre_tool_hook_coverage.py`.

Fail if any active provider/role lane with mutation-capable tools lacks a
proven pre-tool interception path for file mutation tools. The guard must
inspect provider-specific settings plus typed provider capability metadata and
emit one row per provider/role/session gap.

Required checks:

- Claude: `.claude/settings.json` has `PreToolUse` coverage for
  `Edit|Write|MultiEdit`, invokes `check_role_lane_mutation_authority.py`, uses
  `--mode pre_mutation`, and passes the provider tool input before the file is
  touched.
- Codex: a real Codex pre-tool hook, launcher wrapper, tool bridge, or
  equivalent harness interception exists for file mutation tools and invokes the
  same role-lane pre-mutation guard before file writes. If Codex has no
  provider-supported pre-tool hook, the guard must report a typed blocker rather
  than pretending parity exists.
- Other providers: mutation-capable lanes fail closed unless typed provider
  metadata declares an equivalent interception mechanism.
- The guard must distinguish `hook_configured`, `hook_tested`,
  `hook_unavailable_blocker`, and `hook_missing` states.

Machine reasons:

- `provider_pre_tool_hook_missing`
- `provider_pre_tool_hook_unproven`
- `provider_pre_tool_hook_not_pre_mutation`
- `provider_hook_claim_without_test`

Focused tests:

1. Claude settings with the current `PreToolUse` command pass the configured
   portion.
2. Claude settings missing `--tool-input-stdin` fail.
3. Codex provider with no hook metadata fails as `provider_pre_tool_hook_missing`.
4. Codex provider with hook metadata but no execution receipt fails as
   `provider_pre_tool_hook_unproven`.
5. A provider-neutral fixture with a tested equivalent hook passes.

#### G20. Active topology liveness guard

Build `dev/scripts/checks/check_active_topology_liveness.py`.

Fail before a bounded implementation slice starts if the current-row topology is
not live and role-correct. For this row the guard must require:

- Codex lane present as reviewer/orchestrator/plan-steward.
- Claude lane present as implementer, or a typed blocker proving the
  implementer lane cannot currently be reached.
- The active row id/source hash visible to both lanes.
- Reviewer mode / collaboration mode not collapsed to `single_agent`,
  `reviewer_only`, `tools_only`, or `observer_dashboard_lane_read_only` for an
  implementation slice unless a typed blocker is emitted and no implementation
  mutation proceeds.
- Mutation owner and implementer lane agree. If `mutation_owner=claude`, Codex
  cannot take implementation edits as a fallback.
- A current-row action_request or handoff packet exists for Claude implementer,
  or the packet-post failure is preserved as current-row blocker evidence.

Machine reasons:

- `active_topology_not_live`
- `implementer_lane_idle_or_missing`
- `reviewer_lane_attempted_implementation`
- `mutation_owner_mismatch`
- `typed_collaboration_handoff_missing`

Acceptance: the state where Codex is locally editing while Claude has no
current-row typed implementer handoff must fail before the slice starts.

#### G21. Reviewer-coding route guard

Extend `check_role_lane_mutation_authority.py` or build a companion
`check_reviewer_coding_route.py`.

Fail when a reviewer/orchestrator lane attempts implementation mutation and the
typed topology says an implementer lane exists but has not been engaged. The
guard should tell the controller to route the work to the implementer lane
through typed review-channel state instead of silently letting reviewer-mode
Codex code.

Required detection:

- attempted mutation actor role is reviewer/orchestrator/plan-steward
- active row requires multi-agent dogfood or implementer handoff
- implementer provider/session exists in typed topology, or expected current-row
  fixture names Claude implementer
- no accepted mutation lease/proxy/role switch covers the reviewer mutation
- no current-row Claude action_request/ack/absorb/apply event exists

Machine reason:

- `reviewer_coding_instead_of_implementer_handoff`

Acceptance: a Codex reviewer edit attempt with no Claude current-row handoff
fails even if the normal dirty-tree diff check would only report a generic
role-lane violation.

#### G22. Slice boot-plan guard

Build `dev/scripts/checks/check_slice_boot_plan.py` or fold this into the
topology liveness guard if the codebase already has a better boot-check seam.

Every bounded slice for this row must begin with this boot plan:

1. Read `delete_after_ingest.md`.
2. Verify the latest typed plan snapshot/ingestion receipt for the current
   source hash, or record an amendment-ingestion blocker.
3. Verify active row
   `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`.
4. Verify Codex reviewer/orchestrator posture and Claude implementer posture.
5. Verify provider pre-tool hook coverage for both the active reviewer and
   implementer lanes, or record a hook-coverage blocker.
6. Verify a typed Claude implementer handoff exists for the current row, or
   post one through review-channel, or record the typed post failure blocker.
7. Select exactly one bounded command/slice from A11/A12 order unless a newer
   typed amendment changes priority.
8. Use `RED -> GREEN -> ROUTER -> DOGFOOD -> RECEIPT`.
9. Stop implementation mutation if any boot check fails; the slice output is a
   typed blocker/handoff, not local reviewer coding.

Machine reasons:

- `slice_boot_plan_not_run`
- `slice_boot_plan_failed`
- `current_row_not_verified`
- `provider_role_posture_not_verified`
- `claude_handoff_not_verified`

This boot plan must be present in the durable row after ingestion. If it is only
present in chat or this staging file, the row is not ready to close.

#### A16 execution order

This amendment changes the immediate order only enough to stop repeating the
same topology failure. Before continuing A11/A12 implementation work, add or
prove the boot/topology/hook guards above, or capture the typed blocker that
prevents doing so.

Minimum next slice:

```text
RED: failing test/fixture for Codex reviewer coding while Claude implementer has
     no current-row handoff and Codex hook coverage is unproven
GREEN: guard reports provider/topology blocker before mutation
ROUTER: check-router sees the guard
DOGFOOD: run against live state and preserve the blocker or pass receipt
RECEIPT: evidence names row id, source hash, provider roles, hook states,
         packet/blocker ids, and exact commands
```

### A17. Packet Body-Open Route, Expiry Refresh, And Visible Consumption

Operator observation: the A16 handoff exposed a second topology defect. Claude
could see and read the packet body through the provider session, but the typed
lifecycle still reported `packet_body_open_required` / `delivery_pending`, then
the action request expired before the route produced usable body-open or ack
proof. This is not a Claude comprehension problem and not a reason for Codex to
take the coding lane. It is a lifecycle-route defect in the collaboration
system.

Current evidence:

- `rev_pkt_4801` was the original Claude action request for A16.
- `rev_pkt_4801` expired and archived as `expired_after_durable_binding`.
- `rev_pkt_4802` records the blocker: visible packet content but no typed
  body-observed / ack / absorb / execution proof.
- `rev_pkt_4803` is the Codex reviewer continuation anchor.
- `rev_pkt_4804` is the refreshed Claude action request.
- `rev_pkt_4806` clarifies that Claude owns implementation and Codex owns
  review/orchestration.
- `rev_pkt_4821` records a current-row reviewer finding after G20/G19
  composition dogfood: `check_active_topology_liveness.py` can now fill blank
  provider hook states from G19, but it still preserves weaker registry states
  when G19 later has stronger `hook_tested` evidence.
- `attempted_action:review-channel.post:ecb6bf87583a5ee7` records a fresh
  Codex reviewer attempt to promote that current-row finding into a scoped
  Claude `action_request`. The attempt failed closed because the controller was
  already in `body_open_required` state:
  `mutation_attempt_after_may_mutate_false`,
  `command_attempt_after_can_run_next_command_false`, and
  `non_body_open_action_after_body_open_required`.
- `review-channel --action sync-status --terminal none --format md` still
  selected stale `rev_pkt_4804` as Claude's canonical active packet after
  `rev_pkt_4821` was posted and bound as same-row evidence. This is a route
  priority/current-row-selection defect, not permission for Codex to take the
  implementer lane.
- `attempted_action:review-channel.post:19c87e7c6c9bd2f5` records a Codex
  reviewer attempt to post `review_accepted` after Claude fixed `rev_pkt_4821`
  and Codex verified `command_output:test-python:744231b533e97e1c`. The
  command supplied `/private/tmp/codex-develop-next.json` as
  `--control-decision-input`, but `ControlDecisionObeyedGuard` still reported
  `no_control_decision_input`. This keeps review-result lifecycle output from
  reaching Claude even after the reviewer proof is green.
- `attempted_action:review-channel.post:9d5a89b4110bd915` records the retry
  using the correct scoped control-decision artifact:
  `dev/reports/review_channel/control_decisions/rev_evt_85690/codex-reviewer-019e4d3e-51a6-7a52-9005-f989e8e5c02d.json`.
  This time the decision was present, but review-result posting still failed
  closed with `mutation_attempt_after_may_mutate_false`,
  `command_attempt_after_can_run_next_command_false`, and
  `non_body_open_action_after_body_open_required`. That is the real G26
  blocker after the control-decision artifact shape is corrected.
- `rev_pkt_4803` and `rev_pkt_4796` are pending continuation anchors for the
  Codex reviewer lane, but they did not keep the live reviewer loop active
  across the actual conversation/session boundary. Typed startup later reported
  `reviewer_mode=tools_only`, `observed_control_topology=no_live_agents`, and
  `safe_to_continue=false` while the current-row peer loop was still open. A
  continuation anchor that is only a pending packet is not sufficient stop
  protection.
- Claude agent-mind evidence shows repeated steady-state polling with no new
  packets while `rev_pkt_4821` remained the latest current-row Claude finding
  and still had `body_observed_at_utc=""`. That is a peer-liveness/topology
  failure, not an instruction for Codex to code locally or leave the issue in
  chat prose.
- `attempted_action:review-channel.post:fe595d537da20b58` records the next
  Codex reviewer attempt to send Claude a current-row A17/G27 finding. The
  command failed before materializing a `rev_pkt_*` packet because
  `ControlDecisionObeyedGuard` reported `no_control_decision_input`, even
  though the current route's control-decision artifact existed at
  `dev/reports/review_channel/control_decisions/rev_evt_85694/codex-reviewer-019e4d3e-51a6-7a52-9005-f989e8e5c02d.json`
  and listed `review-channel.post_finding` in `allowed_actions`. This is the
  active packet-lane failure to fix before additional guard work can be trusted.
- `rev_pkt_4822` proves the packet lane can materialize when Codex supplies the
  scoped control-decision artifact explicitly. It is now visible in Claude's
  packet history as a current-row finding. This does not close G28; the route
  still needs automatic artifact discovery or an exact retry path.
- `rev_evt_85697` records Claude implementer body-observing `rev_pkt_4821` from
  the real target session `066d28ce-af03-4f1f-86ff-c285908c88a7`. Before that
  event, Claude's scoped decision required `open_packet_body` for `rev_pkt_4821`
  but had `allowed_actions=[]`, `may_mutate=false`,
  `can_run_next_command=false`, and no populated lane/action authority beyond
  the literal next command. After the body-open event, the blocker advanced to
  `packet_semantic_ingestion_required` for the same packet, but
  `allowed_actions` still remained empty while the next command required
  `review-channel --action ingest`. This is a bootstrap contradiction: the
  required packet-attention command is known, but the lane/action list does not
  authorize the actor to perform it.

Required guard additions:

#### G23. Packet Body Observation Route Guard

Add `dev/scripts/checks/check_packet_body_observation_route.py` or extend the
existing review-channel lifecycle guard if one already owns this invariant.

Acceptance:

- A target provider/session that reads a packet body through the sanctioned
  inbox/show path must have a typed, provider-owned way to record body
  observation without Codex spoofing `--actor claude`.
- A visible packet body with no body-observation route must fail as
  `packet_body_observation_route_missing`.
- A reviewer/orchestrator session must not be allowed to satisfy an
  implementer-session body-open requirement by replaying the command as the
  implementer.
- The guard must distinguish:
  - body visible in a generic projection,
  - body opened by the target provider/session,
  - body acked,
  - body absorbed into execution.

#### G24. Action Request Expiry Refresh Guard

Add a guard or reducer invariant for action requests that expire while still
selected as the active implementer packet.

Acceptance:

- If the selected action request expires before target-session body-open or ack,
  `develop next` / sync-status must stop selecting the expired packet.
- The system must require either a fresh replacement packet or a typed blocker
  that says why replacement is impossible.
- Refresh packets must reference the expired packet, the current plan row, and
  the same role/session target when the old target is still valid.
- A stale selected action request must not prevent the reviewer/orchestrator
  lane from recording a newer current-row finding or replacement request as
  actionable typed evidence. If the body-open gate blocks replacement, the
  attempted-action receipt becomes current-row blocker evidence and the
  selector must stop treating the stale packet as the only active instruction.

#### G25. Loose-Chat-To-Typed-Lane Guard

Add or extend the A16 topology guard so a provider reply in chat cannot become
implementation authority by itself, but also cannot block work forever when a
valid typed packet body is visible and the operator has explicitly routed the
work.

Acceptance:

- Loose chat alone remains insufficient collaboration proof.
- Typed packet body visibility plus target-provider session evidence must have
  a supported lifecycle transition path.
- If that path is missing, the required output is a typed blocker or refreshed
  packet, not Codex taking the implementer lane.
- The instruction-priority selector must prefer current-row, role/session-bound
  packets over stale packet projections. A stale `action_request` such as
  `rev_pkt_4804` must not hide newer same-row blockers such as `rev_pkt_4821`
  from the Claude implementer inbox or from reviewer final-gate continuation.

#### G26. Reviewer Result Transition Guard

Add a guard or reducer invariant for reviewer-owned lifecycle outputs after a
Claude implementation slice is verified.

Acceptance:

- A reviewer session with current-row verification evidence must have a typed
  path to post `review_accepted`, `review_failed`, or equivalent review-result
  packets without taking the implementer lane.
- `ControlDecisionObeyedGuard` must preserve and evaluate the supplied
  `--control-decision-input`; a command that supplied a readable decision file
  must not be summarized as `no_control_decision_input`.
- If review-result posting is intentionally blocked by a body-open or
  checkpoint gate, the attempted-action receipt must become current-row blocker
  evidence and the route must tell the reviewer the supported next transition.
- A correct scoped control-decision artifact that still blocks review-result
  posting because `body_open_required` is active must be rendered as a route
  lifecycle blocker, not as reviewer completion or as permission for Codex to
  take the implementer lane.
- Acceptance evidence for `rev_pkt_4821` must include
  `command_output:test-python:744231b533e97e1c`, the live
  `check_active_topology_liveness.py` blocker state, and confirmation that
  `conftest.py` stayed untouched.

#### G27. Continuation Anchor Enforcement And Peer Steady-State Guard

Add a guard or reducer invariant that proves continuation anchors are enforced
as runtime stop protection, not merely queued packet text.

Acceptance:

- A live `continuation_anchor` for the current row must prevent the reviewer
  lane from emitting final completion or dropping into idle/ended state until
  the anchor is consumed, released by a `stop_anchor`, or converted into a typed
  blocker.
- Session-scoped anchors must fail visibly when the target session id is stale.
  The route must either refresh the anchor for the live reviewer session or
  promote a plan-scoped/role-scoped anchor that survives session replacement.
- If startup/session authority reports `reviewer_mode=tools_only`,
  `observed_control_topology=no_live_agents`, or `safe_to_continue=false` while
  a current-row continuation anchor is still pending, the controller must emit a
  current-row blocker such as `continuation_anchor_not_enforced`.
- A peer loop that repeatedly reports "no new packets" while the peer inbox
  still contains a current-row pending packet such as `rev_pkt_4821` must not be
  treated as healthy steady state. It must surface as
  `peer_steady_state_with_pending_current_row_packet` and route the next
  supported lifecycle transition.
- Trace-only liveness expiry events such as `participant_liveness_expired`
  cannot be the only output. They must either wake/route the responsible lane or
  create blocker evidence tied to the current row.
- Dogfood proof must include the current-row anchor packet id, its target role
  and session/scope, the live session authority that did or did not honor it,
  and the next typed packet sent to the peer lane.

#### G28. Control Decision Obedience Post-Route Guard

Fix the review-channel posting route before treating downstream topology
guards as proof. The first current-row repair target is the obedience guard and
its control-decision artifact plumbing, because Codex and Claude cannot dogfood
their assigned roles if allowed packet posts do not materialize as packets.

Acceptance:

- When a current control-decision artifact exists for the actor/role/session
  route and lists `review-channel.post_finding`,
  `review-channel.post_action_request`, or another specific post action in
  `allowed_actions`, `review-channel --action post` must load and evaluate that
  artifact instead of returning `no_control_decision_input`.
- A failed post that supplies no explicit `--control-decision-input` must render
  the exact expected artifact path and next retry command, not only the generic
  `no_control_decision_input` violation.
- A failed post that supplies a readable scoped control-decision artifact but is
  blocked by `body_open_required`, stale-decision state, or another controller
  rule must be classified by that rule, not collapsed into packet silence.
- `attempted_action` events are typed evidence but not collaboration packets.
  A blocked post must not be counted as Claude/Codex communication unless a
  `rev_pkt_*` packet is actually created and visible in the target inbox.
- RED must prove the current failure: Codex reviewer has
  `review-channel.post_finding` in `allowed_actions`, attempts a current-row
  Claude finding, and the route returns `no_control_decision_input` while the
  scoped artifact exists under `dev/reports/review_channel/control_decisions/`.
- GREEN must prove either automatic scoped-artifact discovery or a precise
  typed next-step retry path that lets the packet materialize.

#### G29. Packet-Attention Bootstrap Lane Guard

Fix the packet-attention bootstrap path so a target provider/session can perform
the controller's required body-open, semantic-ingest, or absorb command without
receiving an empty lane/action set.

Acceptance:

- When an `AgentLoopDecision` sets `required_action=open_packet_body`,
  `body_open_required=true`, and a concrete `next_command` for the same
  actor/role/session, the decision must also expose a non-empty allowed action
  for that body-open command or a typed explanation for why the command is
  intentionally blocked.
- After a real target-session body-open event such as `rev_evt_85697`, the
  follow-up `packet_semantic_ingestion_required` decision must similarly expose
  the allowed semantic-ingest action, or it must emit a typed blocker that names
  the missing permission wiring.
- `lane`, `agent_lane`, or equivalent action-lane fields must not remain
  absent/`None` for a scoped implementer packet decision that already has
  `actor_id`, `actor_role`, `session_id`, `target_ref`, `active_packet_id`, and
  `next_command`.
- `allowed_actions=[]` is invalid when `decision=run_next_command`,
  `advance_allowed=true`, and the `next_command` is a sanctioned
  review-channel packet-attention command for the current actor/session.
- A Claude implementer session running the exact controller-supplied
  `review-channel --action show --packet-id <id> --actor claude --target-role
  implementer --target-session-id <session>` is not spoofing Claude. It is the
  canonical provider-owned body-open route and must be treated differently from
  Codex replaying that command as Claude.
- RED must reproduce the current shape: Claude implementer decision for
  `rev_pkt_4821` has `packet_body_open_required` or
  `packet_semantic_ingestion_required`, a concrete next command, and empty
  allowed lane/action authority.
- GREEN must prove the controller grants only the narrow packet-attention
  action required for that packet and still blocks unrelated mutation,
  implementation edits, staging, commits, and cross-provider spoofing.

#### A17 execution order

A17 is part of the A16 topology repair, not a separate import-route project.
Claude remains implementation owner for code and tests. Codex remains
reviewer/orchestrator/plan steward.

Minimum route:

```text
RED: failing fixture where target Claude sees packet body but lifecycle stays
     delivery_pending/body_open_required until expiry
GREEN: supported target-provider body-observation/ack route or explicit blocker
ROUTER: guard appears in check-router/catalog/bundle where A16 guards run
DOGFOOD: live packet route with refreshed packet rev_pkt_4804 or successor
RECEIPT: evidence names rev_pkt_4801 expiry, rev_pkt_4804 refresh,
         rev_pkt_4806 lane correction, rev_pkt_4803 continuation anchor,
         rev_pkt_4821 pending peer packet,
         attempted_action:review-channel.post:fe595d537da20b58,
         rev_pkt_4822 packet materialization, rev_evt_85697 body-open,
         row id, and exact commands
```

---

## Ingestion Checklist

1. Amend the existing v4 plan row with this acceptance contract.
2. Add/refresh typed source snapshot.
3. Add typed ingestion/amendment provenance.
4. Update only existing row in `plan_index.jsonl`.
5. Bind the System Composition Gaps sequencer to existing owner rows; do not
   turn S2-S6 into current-row blocking scope.
6. Add required guard and dogfood implementation rows only if the existing row's
   typed reducer says child task decomposition is allowed; otherwise keep them
   as acceptance criteria on the same row.
7. Run the dogfood scenario and guard.
8. Create `FeatureProofReceipt(proven_passed)`.
9. Regenerate projection surfaces through the typed renderer if available.
10. Run docs/projection sync checks.
11. Delete this file.

## Open Decisions

These need typed decisions, not chat decisions.

1. MP-377 parent shape:
   - create canonical `MP-377` PlanRow, or
   - define `target_ref="plan:MP-377"` as the canonical parent reference.

2. Plan amendment provenance:
   - use dedicated `plan_amendment_receipts.jsonl` if the repo already has or
     formally adds it, or
   - record amendment provenance in existing plan-ingest receipts.

3. Branch/repo identity:
   - declare current canonical branch for this row.
   - remove VoiceTerm identity from GuardIR core policy through repo-pack
     typed state, not generated docs.

4. Flowchart guard path:
   - add a dedicated freshness guard, or
   - extend an existing docs/system-map guard.

5. Active docs cleanup:
   - decide which `dev/active/` docs stay active owner projections.
   - archive/demote stale docs after typed plan state is reconciled.

6. Plan retention windows:
   - choose repo-pack/operator defaults for hot, warm, and cold storage windows
     by row kind.
   - decide whether retention windows are globally configured, per MP family,
     or overrideable per row.
   - decide the approval boundary for archive execution:
     operator-only, reviewer-approved, or policy-automatic after proven
     acceptance.

7. Proven-acceptance shape:
   - compose current guard result + dogfood pytest node +
     `FeatureProofReceipt(proven_passed)` + `PlanRowClosureReceipt`, or
   - add a narrow `ProvenAcceptanceReceipt` only if existing receipt chaining
     cannot carry the proof bundle.

8. Tombstone schema:
   - represent archived PlanRows as compact `PlanRow` tombstones with
     `status=archived` / non-executable row kind, or
   - create a dedicated tombstone index if compacting `plan_index.jsonl` would
     break existing readers.

9. Guard profile policy surface:
   - use `.guardir.toml` for adopted target repos and keep this repo on
     existing repo-pack policy until migration, or
   - introduce `.guardir.toml` for this repo too with a typed migration receipt.
   - decide exact guard tiers and which guards are mandatory.

10. Code-smell projection:
    - archive existing code-smell markdown after each item is typed, or
    - register it as a generated projection with provenance and a freshness
      guard.

11. Explanation surface:
    - implement `devctl explain --guard <id>` through existing guide/projection
      contracts, or
    - expose the same generated guide through `/help` first and add CLI later.

## Bottom Line

The minimum bar is:

- packets never outrank current executable PlanRow unless graph-valid pivot
- `PKT-BIND-*` rows are permanently non-executable
- event queue cannot select packets without PlanRow context while executable
  rows exist
- `develop next` cannot select stale/future/unbound packets
- continuation/final gate cannot be forced by unbound packets
- review/dogfood is provider-neutral evidence
- ContextGraph/ZGraph exposes edges without becoming scheduler authority
- VoiceTerm is adopter/client, not GuardIR core authority
- flowchart and generated docs are guarded projections
- v4 is child/detail work under MP-377, not a parallel plan family
- closed/applied rows are retained as resolvable evidence without staying in
  the active selector path forever
- stale root docs and VoiceTerm product folders are archived, moved to adopter
  boundaries, or kept only with typed owner rows and guards
- live dogfood receipt exists with `real_life_test_status=proven_passed`

## End-Of-File Closure Gate

Before stopping, summarizing, deleting this file, or claiming green, run this
exact sequence:

```bash
python3 dev/scripts/checks/check_staging_execution_index_complete.py \
  --source delete_after_ingest.md \
  --row-id MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1 \
  --format json
python3 dev/scripts/checks/check_current_plan_authority.py --format json
python3 dev/scripts/devctl.py test-python \
  --suite devctl \
  --path dev/scripts/devctl/tests/scenarios/test_current_plan_authority_dogfood.py
python3 dev/scripts/devctl.py develop next --actor codex --format json
python3 dev/scripts/devctl.py develop next --actor claude --format json
python3 dev/scripts/devctl.py develop next \
  --actor codex \
  --enforce-final-response-gate \
  --format json
```

Closure is rejected unless:

- Execution Proof Index is complete.
- No checked item lacks evidence.
- No required command is placeholder text.
- All current-row guards are check-router-visible.
- Claude/Codex collaboration proof is typed, not loose chat.
- Final gate remains closed until the required FeatureProofReceipt exists.
- FeatureProofReceipt is `real_life_test_status=proven_passed`.
- FeatureProofReceipt names the exact pytest node id.
- Receipt evidence names row id, source hash, guard outputs, actor ids, role
  ids, session ids, packet ids, and exact commands.
- This file has been ingested through typed state.
- This file is deleted only after typed closure proof exists.

If any item fails, output:

```text
slice_status: blocked
remaining_blocker: <machine reason>
next_one_bounded_command: <exact command>
```

After this is ingested and proven, delete this file.

## Live-State Semantic TDD Plan (2026-05-23, operator-approved)

The Live-State Semantic TDD architectural plan (Phases A-D: revert rejected-path
code → live-state invariants → ground-truth-probe pytest adapter → metamorphic
role inversion) lives at:

- `dev/active/live_state_semantic_tdd_plan.md` (durable in-repo)
- Phase B starter test file: `dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py`

Phase A revert verified complete: A27, A28, A29, A36 amendments removed; A25,
A26, A30, A31, A32, A33, A34, A35 retained. Files G59 guard + absorb-output
wrapper + their tests + receipt directory + 6 registration entries removed.

### A38. Adaptive Cadence + Receipt Steward + System-Map Steward (Operator Amendment 2026-05-23T21:35Z)

This amendment defines three composable typed substrates surfaced by 3 parallel
design agents under the operator direction "tell me what you think then add to
plan what we find." It addresses three structural gaps observed in today's
session: (1) the 9-step semantic-TDD ritual has fixed cost regardless of slice
blast radius so it becomes overhead on small slices; (2) `FeatureProofReceipt`
emission was approximated rather than emitted per-slice with pytest node ids;
(3) the AI governance platform has 248 typed contracts + 71 guards + 26 probes
+ ~6 active platform layers, but no role audits whether each slice CONNECTED
to the relevant platform pieces — slices can pass narrow tests while leaving
substantial platform inventory disconnected.

#### A38.1 — Adaptive Semantic-TDD Cadence Mode (`MP-SEMANTIC-TDD-CADENCE-S1`)

Typed `SemanticTDDCadenceMode` enum at `dev/scripts/devctl/runtime/semantic_tdd_cadence.py`
with 5 modes (`FULL`, `STANDARD`, `LIGHT`, `SKIP_NEXT`, `ADAPTIVE_AUTO`) plus
per-step firing matrix. Cheap-and-valuable rails NEVER skip: 2a/2b xfail-strict
ratchet check, connectivity sweep BEFORE/AFTER, evidence-log guard. Expensive-
and-conditional steps (A26 reinforcement, DOGFOOD live invocation, FeatureProofReceipt
emission, REVIEW reviewer-packet) fire under FULL+STANDARD, skip under LIGHT.

Typed signal: `CatchKind` enum with 5 typed catch categories (`RED_FIRST_CATCH`,
`CASCADE_CATCH`, `CONNECTIVITY_AFTER`, `XFAIL_TRANSITION`, `TYPE_INTROSPECTION`).
Rolling window N=10 slices. Auto-selection thresholds: catch_rate ≥ 0.60 → FULL;
0.30 ≤ rate < 0.60 → STANDARD; 0.10 ≤ rate < 0.30 → LIGHT; rate < 0.10 →
SKIP_NEXT (with periodic FULL revalidation every 5th SKIP). Hysteresis: 3
consecutive sub-threshold readings required before downshift, prevents
oscillation. Force-promote triggers: any 2a/2b xfail-strict transition (XPASS↔XFAIL)
forces FULL on next slice regardless of catch rate; severe AFTER-sweep findings
force 2 FULL slices. Slices touching peer-spawn / bypass-scope / role-authority /
multi-agent-handoff force-promote to FULL.

Persisted state: `SemanticTDDCadenceState` dataclass to `dev/state/semantic_tdd_cadence.jsonl`
via `append_json_mapping` (uses PathRoots.state from A37 Phase 0.x).

CLI surface:
- `devctl semantic-tdd cadence set --mode <enum> --expires-after-slices <N> --reason "<text>"` (durable pin, auto-revert)
- `devctl semantic-tdd cadence status --format json|md` (current state + recent outcomes + threshold debug)
- `devctl develop next --cadence-mode full|standard|light|skip-once|adaptive` (per-invocation override)
- Mode-change events emit typed `SemanticTDDCadenceTransitionPacket` through review-channel `--action post`; no prose authority.

Plan-row breakdown:
- `MP-SEMANTIC-TDD-CADENCE-S1.A`: typed contract + RED tests for firing matrix + auto-select thresholds (~1 FULL slice)
- `MP-SEMANTIC-TDD-CADENCE-S1.B`: thread `current_mode` into `check_semantic_tdd_evidence_log.py` so LIGHT relaxes case-count delta requirement (~1 STANDARD slice)
- `MP-SEMANTIC-TDD-CADENCE-S1.C`: CLI surface + typed transition packet emission (~1 FULL slice)
- `MP-SEMANTIC-TDD-CADENCE-S1.D`: dogfood for 1 week, capture real CatchOutcome rows, validate threshold tuning (~5 slices of observation)

Honest weak points (from the design): the catch-rate signal is a LAGGING
indicator; steady-state savings are ~30-40% (not 80%); "catch" classification
is harder than the typed enum makes it look. Ship anyway because today's
session shows the upside is real: 6 slices today, concentrated catches in 3
of them; LIGHT mode for the other 3 saves real time.

#### A38.2 — Receipt Steward Role (`A38-RECEIPT-STEWARD-ROLE-S1..S4`)

Typed `receipt_steward` role (`RoleCapabilityClass.GOVERNANCE`, audit-only,
never mutation) sibling to `SemanticTDDRoleSpec`. Lives at
`dev/scripts/devctl/runtime/receipt_steward_role.py` with 6 typed phases
(`DISCOVER_SLICE`, `INVENTORY_EVIDENCE_PATHS`, `VERIFY_RECEIPT_PRESENT`,
`VERIFY_PYTEST_NODE_RESOLVABLE`, `VERIFY_COMMIT_SHA_LINKED`, `EMIT_AUDIT_RECEIPT`).

Typed scope-claim ("latch claim"): `ReceiptStewardScopeClaim` mirrors
`BypassLifecycle` (request → evaluation → claim → expiry) but for READ-only
audit paths. Default scope_paths: `("dev/reports/feature_proof_receipts/",
"dev/state/plan_index.jsonl", "dev/active/semantic_tdd_lane.md",
"evidence.md", ".git/")`. Default TTL 30 minutes. Persisted to
`dev/state/receipt_steward_claims.jsonl`. CLI fails closed without active claim.

Output: typed `ReceiptStewardAuditReceipt` with `missing_items` taxonomy
(7 typed values): `missing_completely`, `missing_pytest_node`,
`stale_commit_reference`, `dangling_plan_row`, `no_evidence_case`,
`pytest_node_unresolvable`, `dirty_tree_at_audit`. First 5 are blocking;
last 2 are advisory.

CLI:
- `devctl receipt-steward audit --slice-id <id> --format json` (single slice)
- `devctl receipt-steward audit-recent --since-commit <sha> --limit N --format json` (bulk)
- `devctl receipt-steward audit-gap-report --format md` (maintainer-readable)
- `devctl receipt-steward claim --action request|extend|release --ttl-minutes N` (scope-claim lifecycle)

Three integration hooks: (a) optional post-slice audit (`develop next` surfaces
typed `next_recommended_command` after `SemanticTDDRolePhase.RECEIPT` completes);
(b) **plan-row close precondition** — `queued → in_progress → done` transition
requires `missing_items == ()` OR explicit `ReceiptExemptionRequest` honored;
(c) **`enforce-final-response-gate` composition** — gate denies
`final_response_allowed=true` until receipt-steward audit passes for active
slice. This is the teeth: an agent cannot say "TASK_COMPLETE" without an
audit pass.

Bounded recursion: receipt_steward emits its OWN `FeatureProofReceipt` per
audit invocation with `meta_audit_depth: 1` cap. One layer is enough; two
is bureaucracy.

Typed exemption lifecycle for docs-only slices: `ReceiptExemptionRequest →
ReceiptExemptionEvaluation → ReceiptExemptionGrant → ReceiptExemptionExpiry`
persisted to `dev/state/receipt_exemption_grants.jsonl`. Requires operator
approval — no prose exemptions.

Plan-row breakdown:
- `A38-RECEIPT-STEWARD-ROLE-S1`: typed spec module + alias wiring + 2a alias-resolution test (~150 LOC)
- `A38-RECEIPT-STEWARD-ROLE-S2`: CLI + scope-claim lifecycle + audit receipt emission (~500 LOC)
- `A38-RECEIPT-STEWARD-ROLE-S3`: gate composition + plan-row gate (~200 LOC) — DO NOT enforce until backfill ≥ 80% complete
- `A38-RECEIPT-STEWARD-ROLE-S4`: exemption lifecycle (~150 LOC)

Honest take from the design: HIGH value if integrated into the final-response
gate; LOW value as standalone manual CLI. Build the integration first.

#### A38.3 — System-Map Steward Role (`A38-SYSTEM-MAP-STEWARD-S1..S3`)

THIS IS THE PLATFORM-COVERAGE ROLE (not "TDD-discipline audit" — corrected per
operator clarification 2026-05-23T21:50Z). The role audits whether each slice
CONNECTED to the AI governance platform pieces that are relevant to its scope.

Likely unifies with existing `system_alignment_role` already in
`DEFAULT_ROLE_IDS` (the role is underdeveloped; this amendment specializes it
into a typed audit surface).

Source of truth: `dev/guides/SYSTEM_MAP.md` (the "Living Connectivity Index"
with operator directive: "Keep on connecting systems that aren't connected
and making sure everything that is connected is just supposed to be the system
that works together. Keep on iterating till everything is connected.")

The role's central loop per slice:
1. Read the platform inventory: SYSTEM_MAP.md + `dev/active/ai_governance_platform.md`
   + `dev/active/INDEX.md` + `dev/state/contract_registry.jsonl` (248 contracts)
   + `dev/scripts/checks/` (71 guards) + `dev/scripts/probes/` (26 probes)
   + `devctl list --format json` (CLI surface inventory)
2. Determine which platform pieces are RELEVANT to the slice (file paths
   touched, plan_row scope, capability category)
3. Audit: did the slice CONNECT to / TOUCH the relevant pieces? Was anything
   missed?
4. If a NEW DISCONNECTION is surfaced (a system that should be connected and
   isn't), the role EMITS a typed `SystemMapRowProposal` and either
   (a) writes the row to SYSTEM_MAP.md directly under capability grant, or
   (b) opens a typed proposal packet for operator approval
5. Emit typed `PlatformCoverageAudit` receipt

Audit dimensions are PLATFORM COMPONENTS (NOT TDD steps):
- `project_governance_authority_chain_consulted` — did `session` run before mutation?
- `repo_pack_contract_respected` — slice touching pack-policy paths
- `plan_registry_tied` — slice tied to typed `PlanRow`
- `collaboration_session_actor_authority_typed` — actor held typed grant
- `typed_action_result_chain` — `TypedAction → ActionResult → RunRecord → ValidationReceipt` emitted?
- `bypass_lifecycle_composed` — if `--no-verify`, was a `BypassReceipt` in scope?
- `feature_proof_receipt_chain` (delegates to receipt_steward)
- `relevant_guards_ran` — guards matching file paths touched ran in BEFORE/AFTER sweep
- `relevant_probes_ran` — probes matching scope category ran
- `findings_priority_impact_observable` — slice resolving a finding has rank delta
- `index_md_active_doc_registry_covered` — slice touching `dev/active/*.md` has INDEX row
- `system_map_maintenance_rule_followed` — slice surfacing new disconnection has SYSTEM_MAP row
- `ai_governance_platform_layer_named` — slice touches platform layer (Core/Runtime/Frontends/Adapters/RepoPacks) → must name
- `contract_registry_updated` — slice adding typed contract → registered
- `devctl_cli_inventory_current` — slice adding subcommand → in `devctl list`

Each dimension carries (a) relevance assessment (high/medium/low/irrelevant
to slice scope), (b) observed touch (connected/missed/n/a), (c) evidence_path
(typed reference to artifact), (d) explanation.

Typed receipt shape:
```python
@dataclass(frozen=True, slots=True)
class PlatformComponentTouch:
    component_id: str
    relevance_to_slice: Literal["high", "medium", "low", "irrelevant"]
    observed_touch: Literal["connected", "missed", "n/a"]
    evidence_path: str
    explanation: str

@dataclass(frozen=True, slots=True)
class PlatformCoverageAudit:
    audit_id: str
    slice_id: str
    commit_sha: str
    components: tuple[PlatformComponentTouch, ...]
    missed_pieces: tuple[str, ...]
    new_disconnections_surfaced: tuple[str, ...]
    system_map_update_proposed: bool
    system_map_proposal_id: str  # empty if no proposal
    coverage_grade: Literal["complete", "partial", "incomplete"]
    schema_version: int = 1
    contract_id: str = "PlatformCoverageAudit"
```

Typed scope-claim `SystemMapStewardScopeClaim` mirrors the receipt_steward
pattern (request → evaluation → claim → expiry) but with broader read paths
covering the full platform inventory PLUS write authority for SYSTEM_MAP.md
itself (the maintenance rule requires the role to be ABLE to update the map).

CLI:
- `devctl system-map-steward audit --slice-id <id> --format json`
- `devctl system-map-steward propose-row --component <id> --description "<text>" --format json` (typed disconnection proposal)
- `devctl system-map-steward coverage-report --since-commit <sha> --format md` (maintainer-readable)
- `devctl system-map-steward connectivity-trend --window 30 --format md` (which platform pieces are decaying — UNTOUCHED in last N slices)

This is exactly the inverse of the `devctl system-map` command which renders
the connectivity SNAPSHOT — the steward AUDITS connectivity per slice and
maintains the doc that the snapshot reflects.

Composes-with:
- Existing `devctl system-map` command — reads its output as the snapshot
- Existing `system_alignment_role` — UNIFIES with it (single typed role, two
  reinforcing jobs: maintain SYSTEM_MAP + audit per-slice connectivity)
- Cadence mode — LIGHT cadence batches audits; FULL fires per-slice
- Receipt steward — `feature_proof_receipt_chain` dimension delegates
- `check_active_plan_sync.py` — composes for `index_md_active_doc_registry_covered`
- `check_multi_agent_sync.py` — composes for `collaboration_session_actor_authority_typed`
- `findings-priority` ranker — composes for `findings_priority_impact_observable`
- `dev/active/INDEX.md` — composes for active-doc coverage dimension

Plan-row breakdown:
- `A38-SYSTEM-MAP-STEWARD-S1`: typed `SystemMapStewardRoleSpec` + `PlatformCoverageAudit`
  + `PlatformComponentTouch` + `SystemMapStewardScopeClaim` dataclasses;
  unify with `system_alignment_role` in `DEFAULT_ROLE_IDS`; 2a/2b RED tests
  (~600 LOC)
- `A38-SYSTEM-MAP-STEWARD-S2`: audit-dimension evaluators (one per dimension)
  + `devctl system-map-steward audit` CLI (~1200 LOC)
- `A38-SYSTEM-MAP-STEWARD-S3`: SYSTEM_MAP.md write authority + `propose-row`
  CLI + `connectivity-trend` reporter + CI integration via
  `check_system_map_coverage_within_window.py` (~600 LOC)

The semantic distinction from the originally-proposed (incorrect)
`governance_holism_steward`: the audit is NOT "did the discipline fire" but
"did the slice CONNECT to the relevant platform pieces." A slice can pass
narrow TDD discipline while leaving 60% of the relevant platform inventory
disconnected — this role catches that.

#### A38 composition + sequencing

The three substrates compose cleanly:
1. CADENCE controls WHEN audit runs (LIGHT/FULL/SKIP gates expensive steps)
2. RECEIPT_STEWARD audits WHETHER per-slice receipts were emitted with valid pytest node ids + commit SHA
3. SYSTEM_MAP_STEWARD audits WHETHER per-slice connected to the right platform pieces

Receipt steward's `feature_proof_receipt_chain` dimension is consumed by
system_map_steward as one of its dimensions — loose coupling via typed audit
contract, not duplicated logic.

Recommended ship order: A38.2 (receipt_steward) first — closes the operator's
admitted gap immediately. Then A38.1 (cadence) — lets the existing ritual
adapt. Then A38.3 (system_map_steward) — the largest substrate, ships once
A38.2 has produced enough audit receipts to validate the delegation contract.

Total estimated complexity: ~3500-4500 LOC across the three substrates.
3-4 engineer-weeks if done sequentially. Each S1 plan row is the irreversible
substrate decision; S2-S3 rows are iteratable; S3 rows are CI lock-in (do not
skip ahead to S3 without S1+S2 producing real evidence).

This amendment is operator-authored. Authority comes from the operator's
direct direction "tell me what you think then add to plan what we find" at
2026-05-23T21:35Z and "this is wrong for I don't want the system role you
look at just TDD but the entire ai governance platform" at 2026-05-23T21:50Z
correcting the system_map_steward framing.

#### A38.4 — TDD the SYSTEM_MAP itself (`A38-TDD-SYSTEM-MAP-INVARIANTS-S1`)

Operator-surfaced drift discovery 2026-05-23T22:00Z: "We have way more than
72 guards tho might wanna TDD system map too lmao." Actual measurement
confirms SYSTEM_MAP.md inventory claims are stale by a factor of ~2x:

| Inventory claim in SYSTEM_MAP.md | Claimed | Actual | Drift |
|---|---|---|---|
| `check_*.py` guards in `dev/scripts/checks/` | 71 | 158 | +87 (123%) |
| `probe_*.py` probes (formerly `dev/scripts/probes/`, now mixed in `dev/scripts/checks/` + `dev/scripts/coderabbit/`) | 26 | 80 | +54 (208%) |
| `devctl` subcommands | 84-85 (varies) | 107 | +22-23 |
| Source files in context-graph snapshot | 2973 | unverified | — |
| Contracts in registry | implied | 248 | matches |

The recursive insight: SYSTEM_MAP.md is the TRUTH SOURCE for the proposed
A38.3 `system_map_steward` role's per-slice connectivity audits. If the
doc claims 71 guards and the slice's audit dimension `relevant_guards_ran`
consults that claim to decide which guards to check, the audit produces
verdicts against a fictional inventory. STALE TRUTH-SOURCE → INVALID AUDITS.

The fix is structurally the same recursive move as Phase 0 (TDD-the-TDD-role)
and Phase 0.x (typed-state over env-var hacks): apply the discipline TO the
doc that defines the discipline.

Land typed RED-FIRST invariants in
`dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py` that
ASSERT SYSTEM_MAP.md inventory claims match the actual filesystem walk.
Initial invariants (all expected RED today, ratchet to GREEN as doc is
brought current):

1. `test_system_map_guard_count_matches_reality` — parses the "X guards"
   numeric claim from SYSTEM_MAP.md and asserts it equals
   `len(glob("dev/scripts/checks/check_*.py"))`. RED today (claim=71,
   actual=158).
2. `test_system_map_probe_count_matches_reality` — same shape for probes.
   RED today (claim=26, actual=80).
3. `test_system_map_devctl_command_count_within_tolerance` — parses
   command-count claims and asserts within ±2 of actual subcommand count.
   RED today (claim ranges from 84 to 85; actual=107).
4. `test_system_map_contract_registry_count_matches` — asserts the doc's
   contract-count claim matches `wc -l dev/state/contract_registry.jsonl`.
   May be GREEN today depending on doc text; verifies the load-bearing
   number explicitly.

These invariants serve dual purpose:
- **Drift catcher**: any future inventory-counting claim added to the doc
  is automatically checked against reality. The doc cannot quietly become
  stale again.
- **Audit truth-source guarantee**: A38.3 `system_map_steward` consults
  the doc as authority; these invariants guarantee the authority is
  current. The role's `relevant_guards_ran` dimension is only valid if
  the guard count claim is current.

Beyond raw counts, two structural invariants to add as a follow-up:

5. `test_system_map_lists_each_guard_path_at_least_once` (xfail-strict
   target) — every `check_*.py` file in `dev/scripts/checks/` appears at
   least once in SYSTEM_MAP.md by path or by guard-id substring. Stays
   RED today (many guards are unlisted) and ratchets up as the doc's
   row coverage expands.
6. `test_system_map_lists_each_devctl_subcommand_at_least_once` — same
   shape for `devctl` subcommands.

These two invariants are the maintenance-rule mechanization for
A38.3 — every new guard or subcommand triggers RED until the doc gains a
row, just like every new typed contract triggers `check_systemmap_covers_contract_registry.py`
to fail until SYSTEM_MAP's auto-rendered managed block updates.

Plan-row breakdown:
- `A38-TDD-SYSTEM-MAP-INVARIANTS-S1.A`: write invariants 1-4 (count-based);
  observe RED; do NOT fix SYSTEM_MAP.md yet — locking in visible drift is
  the win (~1 STANDARD slice)
- `A38-TDD-SYSTEM-MAP-INVARIANTS-S1.B`: fix SYSTEM_MAP.md numeric claims
  to match reality, including a new managed footer "Last counted YYYY-MM-DD
  by test_system_map_*_count_matches_reality" so the source of the
  number is typed; verify invariants 1-4 flip to GREEN (~1 LIGHT slice)
- `A38-TDD-SYSTEM-MAP-INVARIANTS-S1.C`: write invariants 5-6 (path-coverage)
  as xfail-strict ratchets (~1 STANDARD slice)
- `A38-TDD-SYSTEM-MAP-INVARIANTS-S1.D`: integrate into A38.3
  `system_map_steward` audit dimension — the steward's
  `truth_source_current_ratchet` dimension consumes these invariants'
  GREEN/XFAIL counts (~1 STANDARD slice)

Composes-with:
- `check_systemmap_covers_contract_registry.py` (existing) — covers
  the contract-registry slice; the new invariants cover the
  guard/probe/command slices alongside it
- A38.3 `system_map_steward` — these invariants make the doc safe to
  consume as the role's truth-source
- A38.1 cadence-mode — these invariants are CHEAP rails (fast file glob
  + regex parse), they NEVER skip regardless of cadence mode

The "lmao" version of this is honest: today we shipped 6 semantic-TDD
slices and one of them caught a 2x-stale doc claim. The discipline
applied to itself surfaces gaps the discipline applied to code cannot.
Recursive value. Ship.
