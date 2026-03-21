# Platform Authority Loop Plan

**Status**: active  |  **Last updated**: 2026-03-21 | **Owner:** Tooling/control plane/product architecture
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under
`MP-377`. It is the current subordinate execution spec for the `P0`
authority-loop closure slice inside the broader standalone governance-product
plan tracked in `dev/active/ai_governance_platform.md`.

Use this file when the work is specifically about closing the executable spine
that turns repo-local prose/process into portable runtime authority:

`ProjectGovernance -> RepoPack -> PlanRegistry -> PlanTargetRef -> WorkIntakePacket -> TypedAction -> ActionResult / RunRecord / Finding -> ContextPack`

This is not a second main product plan. Product-boundary authority remains in
`dev/active/ai_governance_platform.md`.

## Scope

Close the current authority gap between repo startup docs, repo-pack path
resolution, plan/scoped-task discovery, typed runtime execution, evidence
identity, and context/memory handoff so the platform can run on arbitrary
repositories without VoiceTerm-default assumptions.

This plan covers:

1. One reviewed repo-local governance contract surface
   (`project.governance.md` plus generated machine-readable state) that AI and
   humans can both consume safely.
2. One explicit runtime-loaded `RepoPack` / `RepoPathConfig` path instead of
   VoiceTerm fallback globals and import-time frozen defaults.
3. One typed `PlanRegistry` / `PlanTargetRef` / startup-authority path that
   supports multiple active plans/scopes without regex-scraping
   `MASTER_PLAN.md`, `INDEX.md`, bridge prose, or raw line numbers.
4. One first real runtime slice that executes through
   `TypedAction -> ActionResult -> RunRecord` rather than report/file chaining.
5. One unified evidence contract for findings, reviews, and provenance.
6. One portable `ContextPack` contract plus a clear memory/store boundary.
7. One proof path on at least two repositories with no core-engine patching
   between adoptions.

Out of scope until the authority loop is closed:

1. Separate-repo extraction of the platform packages.
2. Broad new feature growth on top of transitional seams.
3. Multi-reviewer cloud/federated coordination as a first implementation
   target.
4. Language-family expansion beyond the existing Python/Rust-first core.

## Locked Decisions

1. Keep `dev/active/ai_governance_platform.md` as the only main product
   architecture plan for `MP-377`; this file is a subordinate execution spec.
2. Monorepo packages first, separate repos later. Do not export unstable seams
   into new repos/packages prematurely.
3. Markdown may remain the human-facing reviewed surface, but machine runtime
   authority must come from typed contracts, generated JSON, or strict schema-
   backed blocks. Runtime must not depend on prose parsing.
4. The cleanup is the feature. Do not treat this work as optional refactoring
   that happens after new platform features land.
5. The goal is not “100% portable guards.” The goal is a clean split between
   portable core contracts and repo-specific add-ons.
6. VoiceTerm remains the first consumer and optional rich shell, but it must
   stop acting as the hidden default authority for repo paths, startup order,
   or runtime identity.
7. The authority-loop closure is not complete until a second repo works
   without core-engine edits.
8. Keep `WorkIntakePacket` and `CollaborationSession` separate through the
   current `P0`/`P1` closure. Intake is the startup/work-routing envelope;
   collaboration session is the live shared-work projection over intake plus
   review/runtime state. Do not collapse them just to simplify prose before
   cross-repo proof says that distinction is unnecessary.
9. Intake-backed writer leases remain the authority model for canonical plan
   mutation and shared-session ownership. `expected_revision`,
   `version_counter`, and `state_hash` checks may supplement freshness and
   conflict detection, but they must not replace designated writer authority.
10. Startup may auto inspect repo state, refresh stale authority artifacts,
    resume exactly one valid or repairable collaboration session,
    auto-demote stale abandoned state, and emit one bounded intake/resume
    packet. Startup must not guess among multiple active plans, launch
    conductors, or auto-enter `active_dual_agent` mode without explicit
    operator/policy choice.

## Cross-Plan Dependencies

1. `dev/active/ai_governance_platform.md` owns the umbrella product boundary,
   extraction sequencing, and completion gates for `MP-377`.
2. `dev/active/portable_code_governance.md` owns the narrower portable-engine,
   policy, export, and multi-repo evaluation companion work under `MP-376`.
3. `dev/active/review_channel.md` and `dev/active/continuous_swarm.md` remain
   subordinate proof harnesses that must migrate onto this closed authority
   loop instead of becoming alternate long-term backends. Planning-review
   packets should reuse that transport instead of introducing a second
   plan-only bridge.
4. `dev/active/memory_studio.md` owns the shipped memory substrate and later
   retrieval/store capabilities; this plan owns the portable contract boundary
   that startup/runtime flows consume from it.
5. `dev/active/operator_console.md` owns the optional desktop shell under
   `MP-359`, but its snapshot/logging/review loaders are also a dependency of
   Phase 2. Before repo-pack activation closes, that lane must migrate off
   `VOICETERM_PATH_CONFIG`, `voiceterm_repo_root()`, and hard-coded
   `dev/reports/...` paths onto injected `RepoPack` / `RepoPathConfig` seams
   so the console does not strand the backend on VoiceTerm-only authority.
6. `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`,
   `dev/scripts/README.md`, and `dev/guides/DEVCTL_AUTOGUIDE.md` must stay
   aligned with any new startup-authority or repo-pack contract surface.

## Execution Checklist

Execution order note:
Treat Phase 5a as an evidence-identity freeze that runs alongside Phases 2 and
3 and must be green before Phase 4 freezes runtime review identity. The
intended execution order is:
`0 -> 1 -> [2, 3, 5a] -> 4 -> 5b -> 6 -> 7 -> 8`.

### Phase 0 - Scope Freeze And Authority Definition

- [ ] Freeze this lane as the current `MP-377` `P0` execution priority in
      `MASTER_PLAN`, `INDEX`, and maintainer discovery docs.
- [ ] Record the authority-loop contract explicitly:
      `ProjectGovernance -> RepoPack -> PlanRegistry -> PlanTargetRef ->
      WorkIntakePacket -> TypedAction -> ActionResult / RunRecord / Finding ->
      ContextPack`.
- [ ] Define the migration rule: monorepo packages first, separate repos only
      after package/runtime boundaries are proven stable on multiple repos.
- [ ] Define the proof rule: no slice in this plan counts as complete until it
      lands with repo-visible docs, tests/guards, and one durable artifact or
      contract surface that a fresh session can consume.

### Phase 1 - Startup Authority

- [ ] Land `governance-draft` as the deterministic repo-scan entrypoint that
      produces a reviewed starter `project.governance.md`.
- [ ] Define the machine-readable companion contract for that surface
      (`project.governance.json` or a generated equivalent) and make runtime
      consume the machine form rather than prose.
- [ ] Define the `ProjectGovernance` schema fields explicitly:
      repo identity, repo-pack id/version, startup order, path roots, active
      plan registry, tracker doc, workflow profiles, artifact roots, memory
      roots, bridge mode, docs authority, documentation-policy refs,
      doc-class/lifecycle rules, hot/warm/cold context budgets,
      startup-token budget, active-plan count budget, and command-routing
      defaults.
- [x] Land the first repo-pack-owned VCS command-routing default: a push policy
      that defines default remote, development/release branches, protected
      branches, preflight command, and post-push bundle, then consume it from
      the canonical `devctl push` surface plus legacy release/sync helpers.
- [ ] Define the repo-pack-owned documentation contract that
      `ProjectGovernance` points at (`DocPolicy`): doc classes
      (`tracker`, `spec`, `runbook`, `guide`, `reference`,
      `generated_report`, `archive`), allowed roots, lifecycle/graduation
      rules, shadow-authority rejection rules, and bounded hot/warm/cold
      context budgets so governed markdown becomes structured authority rather
      than ad hoc prose.
- [ ] Freeze the first markdown-schema split inside that contract:
      plan docs (`tracker`, `spec`, `runbook`) use one canonical metadata
      header plus required execution sections; non-plan governed docs use a
      reduced metadata header that still participates in `DocRegistry`
      without pretending to be mutable execution authority.
- [ ] Freeze the initial closed taxonomies that `DocPolicy` governs:
      status, owner lane, role, authority, and lifecycle values should be
      config-backed closed sets rather than ad hoc prose strings.
- [ ] Freeze class-based doc budgets in the same contract with explicit
      warning/fail/exception behavior so startup and docs-governance can bound
      context deterministically instead of only after large files already
      exist.
- [ ] Define one `DocRegistry` companion to `PlanRegistry` for all governed
      docs: class, owner, authority, lifecycle, scope, summary, token budget,
      and canonical consumer. Keep `PlanRegistry` focused on mutable execution
      docs while `DocRegistry` carries the broader docs system needed for
      bounded AI startup and cross-repo doc governance.
- [ ] Land the first read-only operator/AI entrypoint for that docs system:
      `python3 dev/scripts/devctl.py doc-authority --format md`.
      It should emit governed-doc counts, registry coverage, metadata-format
      drift, budget violations, overlapping authority, and consolidation
      candidates before any write-mode normalization is attempted.
- [ ] Define the bounded startup/work-intake packet that runtime consumes:
      freeze `WorkIntakePacket` over `PlanTargetRef`, `RepoMapSnapshot`,
      `MapFocusQuery`, `TargetedCheckPlan`, `plan snapshot`, `command map`,
      filtered probe/convention views, filtered doc-registry views,
      designated canonical-write authority,
      writer lease metadata (`writer_id`, lease epoch, expiry, stale-writer
      recovery), role-routing defaults, accepted-outcome sinks, restart packet
      metadata, ready-gate state, and cache invalidation / refresh rules.
- [ ] Define one repo-neutral `CollaborationSession` projection over
      `WorkIntakePacket` + review state + writer lease so Markdown/JSON/status
      surfaces can expose the same shared slice without becoming a second
      authority. Required first fields: lead/review/coding roles,
      reviewer/operator mode, current slice, peer-review ledger,
      disagreement/arbitration state, delegated-worker receipts, restart
      packet, and ready gates.
- [ ] Freeze startup resume rules with fail-closed ambiguity handling:
      startup may auto-resume only when exactly one prior
      `CollaborationSession` is still valid or repairable for the same repo
      identity and target authority; otherwise runtime must emit a typed
      `ambiguous_scope` / `stale_session` intake result and wait for explicit
      operator or policy routing instead of guessing among plans.
- [ ] Add one bounded `startup-context` command/surface over that same intake
      path so AI agents and humans can read the active target, changed scope,
      routed bundle/check plan, convention/probe subset, bounded doc subset,
      and required write-back sinks without cold-reading the full repo every
      session.
- [ ] Make that startup path enforceable instead of advisory: the first typed
      `startup-context` / `WorkIntakePacket` flow must emit a startup receipt
      tied to repo/worktree identity, current tree hash, command goal, and
      bootstrap mode (`full` `bundle.bootstrap` vs slim bounded bootstrap).
      Review-channel, Ralph/autonomy loops, and other agent launchers should
      require that receipt and fail closed on ad hoc partial startup.
- [ ] Define the session-start refresh contract for that same startup surface:
      first run seeds canonical startup artifacts, later sessions refresh only
      the content-hash/git-diff-invalidated slices, and the next
      `startup-context` / `WorkIntakePacket` must come from cached artifacts +
      delta instead of full repo recomputation.
- [ ] Add one repo-pack-owned checkpoint/push packet plus warm-start cache
      layer that enhances the same startup path without creating a second
      authority. It must be generated from canonical git/plan/guard/review
      truth, stored under a managed artifact root, and be safe to delete and
      recompute at any time. Required first fields: repo/worktree identity,
      tree hash or commit sha, touched paths + diff stats, routed plan scope,
      guard/check summary, reviewer verdict summary, checkpoint-budget
      snapshot, invalidation metadata, and rolling batch-size percentiles
      (changed files per checkpoint, LOC per push, guard pass rate per bundle)
      so calibration thresholds become empirical instead of fixed.
      Performance rule: startup may read the packet as a fast path, but it
      must fall back to canonical sources when the packet is missing or stale
      rather than blocking on cache regeneration.
      Sequencing: this item lands after the Phase 1A guard spine (5 items)
      and before broader graph/query expansion.
      Pattern sources: P-18 hash baselines (`astarihope/check_determinism.py`),
      P-17 region sampling (`astarihope/smart_auto_dispatch.py`),
      P-03 relation mapper (`zgraph-scientific-package/relation_mapper.py`),
      P-43 ZRef traces (`ML_Dump_Trace_V2/ARCHITECTURE.md`),
      P-42 dual dispatch (`June17th.../smart_auto_dispatcher.py`),
      P-19 density profiling (`astarihope/density_presets.py`),
      P-02 multi-key cache (`zgraph-scientific-package/cache.py`),
      P-07 metrics tracker (`zgraph-scientific-package/metrics.py`),
      P-35 proof packaging (`justin-prime-engine/complete_proof_package.py`),
      P-15 performance model (`astarihope/create_performance_model.py`).
      Field mapping for this packet is fixed here: tree hash / commit sha
      uses P-18, touched paths + diff stats use P-17, routed plan scope /
      plan refs use P-03, guard/check summary uses P-43, reviewer verdict
      summary uses P-42, checkpoint-budget snapshot uses P-19,
      invalidation metadata uses P-02, rolling calibration uses P-07/P-15,
      and the audit-proof envelope uses P-35.
      Retrieval rule: `context-graph` / `ConceptIndex` / ZGraph-compatible
      outputs may compress or explain nearby scope around the same diff, but
      they do not become checkpoint authority. When graph confidence is low or
      blast radius is unclear, the system must narrow or stop instead of
      widening the candidate checkpoint.
- [ ] Add repo-pack-driven checkpoint-budget fields to that same startup
      receipt/intake contract: dirty-path count, untracked-path count,
      `safe_to_continue_editing`, `checkpoint_required`, checkpoint reason,
      and the repo-policy thresholds that produced the decision. Agents should
      not have to infer "is this slice still bounded enough to keep editing?"
      from raw git status or prompt-local memory.
- [ ] Put one bounded `Why Stack` product thesis at the top of that startup
      surface before SOP/router detail: every fresh session should read the
      mission, proof obligation, and current product priority first so agents
      stop treating the repo as a pile of process without product context.
- [ ] Keep the startup artifact family singular: `startup-context`,
      `WorkIntakePacket`, `CollaborationSession`, and later `ContextPack`
      should be projections of the same typed authority chain. Do not add a
      parallel `bootstrap-context`, second startup manifest, or hand-edited
      session compass outside the tracked plan/bridge surfaces.
- [ ] Freeze the minimal writer-arbitration contract for planning review in
      Phase 1, not Phase 4: `WorkIntakePacket` must define ownership transfer,
      stale-writer recovery, and invalid/expired lease behavior before
      `plan_gap_review` / `plan_patch_review` can mutate canonical plans.
- [ ] Define stable mutable-target anchors for reviewed markdown authority:
      headings, checklist items, session-resume slots, and progress/audit log
      entries must resolve through registry-generated `PlanTargetRef` ids plus
      target revision, not through surrounding prose matches or raw line
      numbers. Freeze the initial anchor grammar as
      `section:<id>|checklist:<id>|session_resume:<id>|progress:<id>|audit:<id>`,
      ordered most-specific to least-specific, with ambiguity or missing
      highest-precedence anchors failing closed.
- [ ] Add strict schema/format validation for the plan/governance docs that
      remain human-authored:
      status-line format, progress-log entry schema, MP-scope cross-validation,
      and required reviewed/machine-block presence where applicable.
- [ ] Add `check_startup_authority_contract.py` to verify that one repo
      declares one startup authority, one active-plan registry, one tracker,
      and valid path roots.
- [ ] Add `devctl bridge-poll` as a typed agent-facing command that returns
      only the changed reviewer-owned bridge sections (verdict, findings,
      instruction, poll status) as structured JSON instead of requiring
      agents to grep/offset-read raw markdown. This replaces ad-hoc prose
      polling with a machine-readable contract that both Codex and Claude
      can consume. Must include: current instruction text + revision,
      open findings list, verdict text, reviewer freshness, and a
      `changed_since_last_ack` flag so agents know whether to act.
      Wire through the existing `review-channel` command surface as a new
      `--action bridge-poll` verb rather than a separate top-level command.
- [ ] Accept the merged Codex/Claude external-research synthesis as the first
      explicit least-effort-first guard/intake follow-on inside Phase 1. Keep
      it sequenced after the blocker tranche and before broader graph widening
      or any ML/ranking work. The five required closures are: explicit
      `UNKNOWN/DEFER` outcomes, decision-path metadata, hash-based
      determinism checking, frozen escalation tiers, and SHA256 proof
      packaging. Use only repo-owned contracts and guards; imported research
      code stays out of scope.

#### Phase 1A - Audit-Promoted Least-Effort-First Guard Spine

- Sequencing rule: the blocker tranche still lands first. Once that tranche is
  green, this five-item batch becomes the first promoted Phase 1 follow-on
  before wider graph/query expansion. Deterministic rule outputs and canonical
  refs remain authoritative; traces, hashes, graph aliases, ML confidence, and
  proof bundles remain generated evidence only. This batch does not replace
  the existing Phase 1 deliverables (`project.governance.json`,
  `PlanRegistry`, `startup-context`, `WorkIntakePacket`,
  `CollaborationSession`); it inserts ahead of them as the first
  post-blocker closure step.
- [ ] 1. Freeze explicit `UNKNOWN/DEFER` outcome states for deterministic
      guard/startup routing.
      Pattern source: `ML_Dump_Trace_V2`, `June17th`, `justin-prime-engine`.
      First file targets: `dev/scripts/devctl/runtime/action_contracts.py`,
      `dev/scripts/devctl/runtime/startup_context.py`,
      `dev/scripts/devctl/runtime/finding_contracts.py`, and
      `dev/scripts/devctl/watchdog/models.py`.
      Guard contract: `platform-contracts` plus
      `check_platform_contract_closure.py` must enumerate the outcome
      semantics, and focused tests in
      `dev/scripts/devctl/tests/runtime/test_action_contracts.py`,
      `dev/scripts/devctl/tests/runtime/test_startup_context.py`, and
      `dev/scripts/devctl/tests/runtime/test_finding_contracts.py` must prove
      fail-closed behavior when cheaper tiers cannot classify.
- [ ] 2. Carry decision-path metadata from the cheapest winning layer through
      the typed action/result path.
      Pattern source: `astarihope` `FilterState`, `justin-prime`
      `layer_path_viewer`, `PredictionLogger`.
      First file targets: `dev/scripts/devctl/commands/check_phases.py`
      (`CheckContext`), `dev/scripts/devctl/commands/check.py`,
      `dev/scripts/devctl/runtime/action_contracts.py`, and the first
      `startup-context` / `WorkIntakePacket` projection that consumes the same
      routing metadata.
      Guard contract: focused tests in
      `dev/scripts/devctl/tests/test_check.py` and
      `dev/scripts/devctl/tests/runtime/test_action_contracts.py` plus
      `check_platform_contract_closure.py` must prove the path is present,
      ordered, and stable for the same input.
- [ ] 3. Add hash-based determinism verification for typed guard/startup
      artifacts before richer routing widens.
      Pattern source: `astarihope-main/tools/check_determinism.py`.
      First file targets: new `dev/scripts/checks/check_determinism.py` (or an
      equivalent repo-owned determinism guard),
      `dev/scripts/devctl/runtime/machine_output.py`,
      `dev/scripts/devctl/commands/check.py`, and the first `ActionResult` /
      `RunRecord` emitters whose canonical JSON must stay byte-stable for the
      same input.
      Guard contract: wire the guard through `script_catalog.py`,
      `quality_policy_defaults.py`, and the relevant bundle; focused tests in
      `dev/scripts/devctl/tests/runtime/test_machine_output.py` plus a new
      determinism test module must prove stable hash output except for
      explicitly allowlisted volatile fields.
- [ ] 4. Freeze least-effort escalation tiers as one typed routing taxonomy:
      `trivial -> quick -> expensive -> ai_fallback`.
      Pattern source: `astarihope` progressive relaxation,
      `ML_Dump_Trace` layered state machine, `June17th` dual dispatch.
      First file targets: `dev/scripts/devctl/commands/check.py`,
      `dev/scripts/devctl/commands/check_phases.py`,
      `dev/scripts/devctl/runtime/startup_context.py`, and the first
      check-router / startup surfaces that need to explain why a task climbed
      tiers.
      Guard contract: focused tests in
      `dev/scripts/devctl/tests/test_check.py`,
      `dev/scripts/devctl/tests/test_check_router.py`, and
      `dev/scripts/devctl/tests/runtime/test_startup_context.py` must prove
      deterministic tier selection and fail-closed escalation when cheaper
      tiers cannot classify.
- [ ] 5. Add proof packaging with SHA256 provenance to `RunRecord` and related
      evidence artifacts.
      Pattern source: `justin-prime-engine`
      `complete_proof_package.py`, `Nasa_Export-main`.
      First file targets: `dev/scripts/devctl/runtime/action_contracts.py`
      (`RunRecord`), `dev/scripts/devctl/runtime/machine_output.py`,
      `dev/scripts/artifacts/sha256.py`, and the first report/evidence writers
      under `dev/reports/**` that materialize typed runtime artifacts.
      Guard contract: `platform-contracts` rows and
      `check_platform_contract_closure.py` must enumerate the proof fields;
      focused tests in `dev/scripts/devctl/tests/runtime/test_action_contracts.py`
      and `dev/scripts/devctl/tests/test_write_sha256_checksum.py` must prove
      artifact-hash packaging is present and reproducible.
- [ ] Treat Phase 1 as done only when this repo can emit reviewed
      `project.governance.md` + generated `project.governance.json`,
      generated `plan_registry.json`, one bounded `startup-context` /
      `WorkIntakePacket`, and one `CollaborationSession` projection from the
      same intake path; ambiguity must fail closed as typed
      `ambiguous_scope` / `stale_session` results and
      `check_startup_authority_contract.py` must be green with focused tests.
- [ ] Treat stable anchor grammar freeze as a Phase 1 deliverable and a
      Phase 3 blocker: `section:<id>|checklist:<id>|session_resume:<id>|progress:<id>|audit:<id>`
      plus collision-free id generation must be frozen before
      `PlanRegistry` / `PlanTargetRef` implementation can count as closed.

### Phase 2 - RepoPack Runtime Activation

- [ ] Replace VoiceTerm fallback globals with one explicit runtime-loaded
      `RepoPack` / `RepoPathConfig` object.
- [ ] Land that runtime-loaded repo-pack accessor in compatibility mode first
      (`get_repo_pack()` or an equivalent runtime seam) so old defaults can
      coexist temporarily while callers migrate.
- [ ] Freeze one dependency-injection pattern for portable runtime code:
      top-level commands, service constructors, and helper entrypoints accept
      `RepoPack` or `RepoPathConfig` explicitly and thread it through;
      module-level frozen defaults and hidden global path lookup are banned.
- [ ] Keep `RepoPathConfig` from becoming a replacement singleton: split it
      into bounded path families (`RepoRoots`, artifact/report roots,
      plan/docs authority paths, memory roots, review/bridge paths, or an
      equivalent grouping) so runtime modules only learn the authority slice
      they actually consume.
- [ ] Thread `RepoPack` / `RepoPathConfig` through function signatures,
      service constructors, and helper entrypoints before removing old
      defaults; do not make the migration depend on one giant all-sites PR.
- [ ] Eliminate module-level frozen `active_path_config()` defaults from the
      portable/runtime surfaces. Current audit baseline: `51` call sites need
      explicit migration, not only the review-channel subset.
- [ ] Replace the `voiceterm_repo_root()` singleton/fallback behavior with a
      repo-pack/provider boundary that callers receive explicitly.
- [ ] Migrate hardcoded `.voiceterm` / `~/.voiceterm` path families onto
      repo-pack-declared artifact and memory roots as part of the same path-
      authority rewrite. Current audit baseline: roughly `15` direct path
      references remain outside the portable contract boundary.
- [ ] Treat the Operator Console snapshot/logging/review loaders as part of
      the same path-authority rewrite so `MP-359` does not keep
      `VOICETERM_PATH_CONFIG`, `voiceterm_repo_root()`, or hard-coded
      `dev/reports/...` paths alive as hidden backend authority.
- [ ] Make repo-pack activation visible in runtime state and command receipts
      so portable runs can prove which pack, policy, and path roots were
      active.
- [ ] Add `check_repo_pack_activation.py` so declared non-VoiceTerm packs fail
      if the runtime still resolves VoiceTerm defaults.
- [ ] Stage `check_frozen_path_config_imports.py` as advisory/report-only
      first while legacy frozen defaults are still being migrated, then
      promote it to a blocking guard only after those call sites are removed
      and covered by tests so CI cannot deadlock on the migration itself.
- [ ] Make the first extensibility step config-driven rather than implied:
      `project.governance.json` / repo-pack policy must be able to declare
      enabled guard/probe ids, bundle overrides, and repo-local routing
      without editing core registries; hardcoded defaults remain only as a
      backward-compatible fallback until later plugin discovery lands.
- [ ] Name the first repo-pack migration batch explicitly and keep it bounded:
      startup/governance bootstrap surfaces, review-channel
      runtime/projection surfaces, Operator Console snapshot/logging/review
      loaders, and the shared path helpers directly used by those surfaces
      move first; untouched callers remain on compatibility mode until later
      batches.
- [ ] Treat that first migration batch as done only when those named surfaces
      run through explicit `RepoPack` / `RepoPathConfig`,
      `check_repo_pack_activation.py` is green for the batch, and later
      batches can continue without reopening hidden VoiceTerm defaults in the
      completed surfaces.
- [ ] Run one ugly second-repo smoke test before Phase 7 packaging polish:
      after the first startup-authority + repo-pack migration batch works in
      VoiceTerm, exercise the same path on a rough adopter repo through
      repo-pack selection, one report-only typed action, one blocking guard,
      one finding/evidence write, and one shared status/report render. Treat
      this as an early hidden-coupling detector, not as the full adoption
      proof.

### Phase 3 - Typed Plan Registry

- [ ] Treat the Phase 1 anchor-grammar freeze as a hard prerequisite for this
      phase, not as an incidental detail discovered during implementation.
- [ ] Define one typed `PlanRegistry` contract that maps active plans, scopes,
      roles, and execution authority without regex-scraping prose tables.
- [ ] Support multiple active plans/scopes at once as a first-class use case.
- [ ] Define one `PlanTargetRef` contract for mutable reviewed targets:
      plan doc, scope, target kind, stable anchor keys, expected revision,
      and canonical target id generation rules so planning-review packets can
      address canonical markdown without hard-coded repo paths or brittle
      block matching.
- [ ] Define the anchor-id normalization/uniqueness contract:
      `PlanRegistry` generates collision-free ids for duplicate headings,
      repeated checklist text, and append-only log rows; clients must not
      invent ids locally from visible prose.
- [ ] Replace markdown/prose scope scraping in review/promotion/startup paths
      with the typed registry.
- [ ] Replace line-number- or context-based plan targeting in bridge/proposal
      flows with `PlanTargetRef` resolution over stable heading/checklist/log
      anchors so adjacent prose edits do not strand the planning loop.
- [ ] Define the allowed mutation operations per target kind:
      `rewrite_section_note`, `set_checklist_state`, `rewrite_session_resume`,
      `append_progress_log`, and `append_audit_evidence` so adopters do not
      claim `PlanTargetRef` support while applying incompatible edits.
- [ ] Define the structured plan-doc schema required for registry generation
      and drift detection so runtime does not depend on arbitrary narrative
      phrasing.
- [ ] Freeze the canonical markdown schema/formatter contract for governed
      plan docs too: machine-readable metadata header, standard section order,
      stable anchor generation, and formatter/normalizer compatibility so
      plan markdown stays organized and registry-ready across repos.
- [ ] Land the first bounded enforcement surface for that schema under the
      existing docs-governance path. Start by extending
      `check_active_plan_sync.py` with metadata-header / `Session Resume` /
      section-order parity so the repo self-hosts the contract without a
      second parallel checker; split a dedicated `check_plan_doc_format.py`
      only if that contract outgrows the current active-plan lane. Scope:
      header presence, metadata validity, required sections/order, line-budget
      policy, orphan files, execution-plan marker presence, INDEX coverage,
      and `MASTER_PLAN` / registry linkage.
- [ ] Add the first structured plan-content extraction on top of that schema:
      `PlanRegistry` must expose current phase, unchecked checklist items,
      `Session Resume`, and bounded recent progress/audit rows as typed fields
      so startup/review/context-graph consumers stop treating governed plans
      as opaque file pointers.
- [ ] Implement runtime handlers for the allowed plan mutation operations over
      `PlanTargetRef` resolution:
      `rewrite_section_note`, `set_checklist_state`, `rewrite_session_resume`,
      `append_progress_log`, and `append_audit_evidence` must become real
      reducer/apply paths with typed receipts. Schema-level `mutation_op`
      validation alone is not enough.
- [ ] Add one guard that fails when plan-registry artifacts or target-anchor
      resolution drift from the reviewed markdown authority they are derived
      from.
- [ ] Treat Phase 3 as done only when `PlanRegistry` + `PlanTargetRef`
      artifacts are generated from reviewed markdown authority, duplicate
      headings/checklist/log rows receive collision-free ids, the selected
      startup/review/promotion surfaces stop using prose scraping, and the
      registry-drift guard is green with focused tests.

### Phase 5a - Evidence Identity Freeze

- [ ] Run this phase in parallel with Phases 2 and 3, and do not freeze
      runtime review identity in Phase 4 until this phase is green.
- [ ] Treat this as live parallel work, not a post-Phase-3 tail: start the
      stable repo-identity helper, legacy-row upgrade path, and compatibility
      reader in the same implementation window as the first Phase 2/3 PRs so
      Phase 4 is not blocked by avoidable sequencing drift.
- [ ] Freeze the canonical finding/review identity inputs first:
      stable repo identity, repo-relative paths, schema/version coverage, and
      one explicit mapping from current review-ledger rows to the canonical
      `Finding` family.
- [ ] Backfill existing legacy governance-review rows before any hard
      schema-version checks land. Current audit baseline: `107` rows in
      `dev/reports/governance/finding_reviews.jsonl` currently lack
      `schema_version`.
- [ ] Add one explicit migration/upgrade path for review-ledger rows
      (`upgrade_governance_review_row()` or equivalent) plus a backward-
      compatible reader that can infer legacy v1 rows during the compatibility
      window.
- [ ] Acknowledge the current foundation explicitly: the typed
      `TypedAction`, `ActionResult`, `RunRecord`, `Finding`, and
      decision-packet families already carry schema metadata, so this phase is
      convergence of legacy and canonical evidence families rather than
      versioning from zero.
- [ ] Define the compatibility window, rollback path, and cutover rule for
      legacy evidence readers before Phase 4 freezes portable review identity.

### Phase 4 - First Runtime Slice

- [ ] Choose one bounded first slice and route it fully through
      `TypedAction -> ActionResult -> RunRecord`.
      Preferred candidates: `review-channel status`,
      planning-review gap scan over typed plan targets,
      `swarm_run --report-only`, or `triage-loop --report-only`.
- [ ] Freeze the runtime lifecycle contract for that slice too:
      attach/discover/resume/watch service behavior, degraded modes,
      stop reasons, remote observability, and caller-authority / approval
      rules.
- [ ] Freeze multi-client write arbitration and portable review identity only
      after Phase 5a has unified stable identity inputs so review/control
      state no longer depends on checkout-path-derived identity or a single
      local reviewer pair.
- [ ] Move provider-specific review inference and status naming (`codex`,
      `claude`, and similar labels) behind provider adapters so canonical
      review/runtime state remains provider-neutral.
- [ ] Define the reviewer-topology contract for the future portable review
      layer: local/remote reviewers, multiple reviewers, precedence/quorum,
      and handoff ownership. Keep single-reviewer operation as the first
      implementation, but do not leave the contract shape implicit.
- [ ] Remove `_compat` from that slice's primary runtime path so the first
      end-to-end contract is truly canonical rather than compatibility-first.
- [ ] Freeze and document the review/control state machine that slice needs:
      valid states, transitions, degraded modes, recovery, and receipts.
- [ ] Reuse the same runtime transport for planning review when the target is a
      canonical plan: `plan_gap_review`, `plan_patch_review`, and
      `plan_ready_gate` should ride the review-channel packet path, but the
      canonical plan remains the only authority and only the intake-selected
      writer may patch it. Phase 4 broadens that lease/arbitration contract to
      the whole app, but the minimal planning-writer lease must already be
      frozen in Phase 1.
- [ ] Add `check_runtime_contract_adoption.py` to verify the selected commands
      emit and consume the typed runtime contracts.
- [ ] Schedule operator-visible observability as part of the same runtime
      spine, not as chat habit: heartbeats, next action, findings, stale state,
      and run identity should be publishable from the shared backend.
- [ ] Treat Phase 4 as done only when the chosen slice emits
      `TypedAction -> ActionResult -> RunRecord` with no `_compat` in the
      authoritative path, stale-state and writer-authority decisions match
      the shared collaboration/session projection, planning-review packets
      resolve via `PlanTargetRef`, and
      `check_runtime_contract_adoption.py` plus focused runtime/review-channel
      tests are green.
- [ ] Prefer the early second-repo smoke test to use this same first runtime
      slice so portability pressure hits the real executable seam rather than
      a special-case bootstrap-only demo.

### Phase 5b - Evidence And Provenance Closure

- [ ] Extend the Phase 5a identity freeze across guards, probes, external
      imports, review ledgers, and decision packets so every evidence family
      materializes the same canonical `Finding` contract with
      `schema_version`, stable identity, and portable repo-relative paths.
- [ ] Version the broader platform contracts too, not only findings:
      startup-authority payloads, plan-registry artifacts, runtime actions/
      results/records, and context packs must all carry schema/version fields
      plus documented compatibility checks at load time.
- [ ] Define the contract family matrix explicitly for durable artifacts and
      config/policy surfaces: owner, compatibility window, migration path,
      rollback path, and the enforcing guard/check for each family.
- [ ] Add provenance fields everywhere they are required:
      `rule_id`, `rule_version`, `source_command`, `repo_pack_id`,
      `policy_hash` or policy version, `run_id`, and evidence/artifact refs.
- [ ] Record quality-to-cost telemetry alongside runtime/evidence rows
      wherever the provider/runtime can supply it:
      `provider_id`, `model_id`, `model_version`, `token_count`,
      `context_budget`, and `cost_usd` (or explicit unavailable markers) so
      adoption proof can compare quality delta against context/cost rather
      than quality alone.
- [ ] Add `check_evidence_identity_closure.py` so finding ids, review ledger
      rows, and packet identities converge on one scheme.
- [ ] Keep `check_platform_contract_closure.py` in the Phase 5b closure path
      as contract families expand beyond the current implemented slice; this
      phase is not done while runtime-model rows, durable artifact schemas,
      and startup-surface contract guidance can still drift independently.
- [ ] Define append-only ledger integrity rules:
      malformed-row handling, retention/repair policy, refresh-ledger/storage
      contract for cached repo intelligence, and explicit failure behavior when
      evidence would otherwise be lost silently.
- [ ] Add the aggregate governance-quality surfaces required to prove the
      platform governs itself: `master-report`, `converge`, and meta-findings
      over guard/probe/CI/exception/evidence completeness.
- [ ] Require direct test coverage for authority-loop guards/checks and
      evidence-closure families. New closure guards do not count as complete
      until corresponding `test_check_*.py` coverage lands.
- [ ] Define the multi-repo proof/evidence bundle schema used for adoption
      demonstrations and later evaluation corpora.
- [ ] Treat Phase 5b as done only when guards, probes, imports, review
      ledgers, and decision packets converge on one canonical `Finding`
      identity scheme, provenance + quality/cost telemetry includes provider
      and model version data where available, and both
      `check_evidence_identity_closure.py` and
      `check_platform_contract_closure.py` are green with focused tests.

### Phase 6 - ContextPack And Memory Boundary

- [ ] Define one portable `ContextPack` contract with schema version, stable
      ids, repo identity, provenance, and bounded references.
- [ ] Freeze tiered retrieval semantics for `ContextPack`: every attached ref
      must declare `temperature` (`hot|warm|cold`), `source_kind`,
      `provenance_ref`, `canonical_pointer_ref`, `freshness_state`, and
      `budget_cost`. `hot` = live intake/session authority only
      (`WorkIntakePacket`, `CollaborationSession`, active instruction/current
      slice); `warm` = active plan/doc/map/evidence refs plus deterministic
      `ConceptIndex` expansion; `cold` = broader audit/history/topic-chapter
      refs. `ConceptIndex` / ZGraph traversal may rank warm/cold candidates,
      but every returned node must expand back to cited canonical pointers.
- [ ] Replace path-only attach-by-ref conventions with a real provider/store
      boundary that review/startup/runtime surfaces consume.
- [ ] Add `check_context_pack_contract.py` so context packs cannot be raw file
      conventions without schema/id/version coverage.
- [ ] Bridge governance evidence into the existing memory substrate through the
      new contract instead of rebuilding a second memory stack.
- [ ] Define the read path back out of that bridge too:
      startup-context, `master-report`, packet-outcome ingestion,
      freshness/quarantine behavior, and the bounded topic-keyed knowledge-base
      exports that feed `ContextPack`.
- [ ] Consume the new structured plan metadata in that same read path:
      `startup-context`, review-channel promotion/event projections, and
      `context-graph` / `ContextPack` packets should be able to read current
      phase, open items, and `Session Resume` / recent progress context
      without reparsing full plan files on every warm start.
- [ ] Freeze the first native repo-understanding graph path as a repo-owned
      `devctl` surface, not an external semantic store: canonical pointer rows
      come from plans/docs/repo-map/report artifacts first, typed edges derive
      from those sources into `ConceptIndex` and optional ZGraph-compatible
      snapshots second, and the first operator/agent implementation stays
      report-only (`context-graph` / hot-index query over existing artifacts)
      until the contract is proven.
- [ ] Freeze the typed context-escalation policy on top of that graph:
      injection is allowed only for unread scope, repeated failed attempt,
      guard-hit scope, or explicit blast-radius uncertainty. Escalation stays
      read-only and generated; packet refs and query hints may guide startup /
      review / fix flows, but they do not become authority over plans,
      findings, or reviewer instructions.
- [ ] Freeze the retrieval/control stack semantics for the same lane:
      hard guards/probes classify cheaply first, `ConceptIndex` /
      ZGraph-compatible outputs only reduce search space over canonical refs,
      `startup-context` / `ContextPack` reconstruct the minimum cited working
      slice second, and reviewer/autonomy/Ralph controller loops consume those
      packets only as the expensive fallback layer when the cheaper paths
      cannot decide or recover safely.
- [ ] Treat the current `context-graph` implementation honestly as a bounded
      discovery helper until the next reducer steps land. Before counting it as
      task routing, close command->handler/source edges against dispatch
      authority, reject orphan semantic edges, emit explicit
      `low_confidence` / `no_edge` states, and keep heuristic plan->concept
      edges suppressed unless the target concept node actually materializes.
- [ ] Land one typed `startup-context` / `WorkIntakePacket` repo-owned command
      before broader graph fan-out. That packet should carry command goal,
      active target refs, changed scope, suggested graph queries, canonical
      warm refs, targeted checks, and fallback/confidence fields so the
      least-effort-first routing contract exists as machine state.
- [ ] Feed live task state into that reducer in the next slice: changed paths,
      recent findings, last failed checks, recent touched files, and current
      plan scope should influence graph ranking instead of every query seeing
      the same static discovery view.
- [ ] Keep the storage fallback explicit while SQLite activation is pending:
      canonical JSON artifacts plus refresh-ledger rows must remain a complete
      warm-start path for repo-pack adopters until the runtime cache is active
      and proven against the same contracts.
- [ ] Require one stronger typed edge path for plan/doc/command queries before
      claiming MP-scoped graph retrieval is ready. Do not treat keyword-only
      isolated plan matches as sufficient evidence that the navigation layer is
      truthful.
- [ ] Add a focused first context-recovery validation bundle: review-channel
      promotion/event views, autonomy checkpoint/swap-in prompts, Ralph fixer
      prompts, and direct `context-graph --query` output must agree on cited
      canonical refs for the same scope.
- [ ] Checkpoint the current green bounded context-escalation slice before
      widening graph capability work again. Richer graph features (transitive
      blast radius, test-to-code edges, self-service graph queries) are later
      Phase-6/7 work, not part of the first proof.
- [ ] Treat Phase 6 as done only when at least one named consumer
      (`startup-context`, `master-report`, or packet-outcome ingestion) reads
      `ContextPack` through the contract instead of path-only attachment
      conventions, and `check_context_pack_contract.py` is green with focused
      tests.

### Phase 7 - Packaging And Cross-Repo Proof

- [ ] Extract the portable runtime/core into monorepo packages first
      (`devctl-core` / repo-pack/product-integration seams), while keeping
      VoiceTerm as one consumer.
- [ ] Create the repo bootstrap/init path that materializes startup authority,
      repo-pack selection, and reviewed starter docs for a new repo.
- [ ] Classify the guard surface into portable/core, language-aware, and
      repo-structure/maintainer-contract families; do not treat VoiceTerm-
      specific docs-governance guards as universal adopter requirements.
- [ ] Define how bootstrap/adoption proof runs choose that surface:
      `--adoption-scan` and repo-pack proof flows must skip or downgrade
      repo-structure-only guards until the adopter explicitly opts into those
      docs/plan contracts.
- [ ] Define the minimum viable pilot-repo shape for Phase 7 proof so success
      does not depend on VoiceTerm-specific files such as `AGENTS.md`,
      `dev/active/MASTER_PLAN.md`, `QUICK_START.md`, or `DEV_INDEX.md`. The
      minimum bootstrap set must be: one reviewed governance contract, one
      active-plan registry export, at least one canonical plan authority doc,
      exported `PlanTargetRef` targets, and one `WorkIntakePacket` /
      startup-intake projection.
- [ ] For non-VoiceTerm adopters, treat a canonical plan authority doc as any
      reviewed markdown authority that is registered in `PlanRegistry`,
      targetable via `PlanTargetRef`, and exposes at least one mutable target
      kind plus progress/audit sinks; do not require `AGENTS.md` or
      `MASTER_PLAN.md` by name.
- [ ] Prove that planning review also survives repo drift in those adopters:
      target plans via `PlanRegistry` / `PlanTargetRef`, not VoiceTerm file
      names or exact surrounding markdown blocks.
- [ ] Prove the authority loop on at least two repositories with different
      layouts and no core-engine patches between them.
- [ ] Freeze Phase 7 success criteria as "all portable and language-
      appropriate guards/probes pass, repo-pack activation is explicit in
      receipts, and no core-engine patches are required between repos", not
      "every VoiceTerm maintainer guard passes everywhere".
- [ ] Record the adoption proof with artifacts, contract receipts, and a
      reviewer-readable summary rather than relying on chat memory.
- [ ] Define the proof-pack/evaluation schema used for public and internal
      before-vs-after comparisons so the platform can prove quality deltas
      instead of asserting them informally.
- [ ] Require the stronger adoption proof inputs too:
      replayable evaluation corpus, benchmark runner, context-cost telemetry,
      adjudicated external findings, cache-first startup artifacts, and
      reviewer-readable quality-to-cost comparisons.
- [ ] Make that proof compare collaboration modes on the same corpus:
      `tools_only`, `single_agent`, `active_dual_agent`, and later swarm
      configurations should report adjudicated findings, severity mix,
      false-positive rate, time-to-disposition, repair-loop count, and
      quality-to-cost telemetry through one reviewer-readable proof packet.
- [ ] Keep the first proof scoreboard compact and comparable across repos:
      time-to-first-governed-run, hard-guard blocked-change count, reviewed
      false-positive rate, quality/cost per successful fix, and a binary
      "no core-engine patches required" result should appear in every
      adoption proof packet.
- [ ] Treat Phase 7 as done only when two repos with different layouts can
      emit the minimum bootstrap set, planning review targets their canonical
      plan authority docs through registry-generated anchors, no core-engine
      patches are required between adoptions, and the proof packet records the
      portable-vs-repo-structure guard split plus quality-to-cost results.

### Phase 8 - Deferred Follow-Ons After Authority Closure

- [ ] After the authority loop is closed, run one self-hosting structure-
      governance tranche over the governance engine itself: extend the
      existing package-layout / compatibility-shim governance into explicit
      policy for `devctl` root budgets, parser/command placement, subsystem
      file-count budgets, source-of-truth ownership, active-doc lifecycle,
      and shim expiry.
- [ ] Freeze the audit-integration retirement rule in that tranche too:
      repo-root audit docs such as `SYSTEM_AUDIT.md` are temporary reference
      evidence, accepted findings must be absorbed into canonical plans/docs,
      and the repo-root copy should be retired once those findings are fully
      integrated or explicitly rejected.
- [ ] Extend docs-governance into the full documentation-authority contract in
      the same tranche: `docs-check`, `check_active_plan_sync`, `hygiene`,
      and `check_architecture_surface_sync` should enforce doc-class
      placement, lifecycle/graduation rules, active-plan/startup-token
      budgets, and shadow-roadmap rejection before a separate
      `check_doc_authority_contract.py` is introduced.
- [ ] Make the first consolidation wave executable in that tranche:
      move reference-only `dev/active` docs out of live authority, graduate
      stable operational docs into guides/runbooks, and split oversized active
      specs by moving historical/comparative/reference material out of the
      mutable execution path once the doc registry and format guard exist.
- [ ] Add plugin/entrypoint-based extension discovery for guard/probe/bundle
      families once the core runtime and repo-pack activation contract is
      stable.
- [ ] Evaluate optional MCP server exposure for portable guard/probe/report
      surfaces after authority-loop closure, but keep MCP additive to the
      `devctl` / repo-pack authority path rather than promoting it into the
      primary control plane.
- [ ] Define extension/adopter conformance packs so every new provider/client/
      hook/wrapper/plugin declares supported actions, modes, projections,
      approvals, and parity tests before it counts as supported.
- [ ] Generalize the review/coordination layer for remote/cloud reviewers,
      multiple reviewers, skill routing, and push/webhook wakeups after the
      local single-reviewer path is closed on typed runtime authority.
- [ ] Define the language-plugin contract for non-Python/Rust ecosystems once
      the existing evidence/runtime contracts are frozen.
- [ ] Define the cross-repo/federated governance model only after single-repo
      authority closure and multi-repo adoption proof are green.
- [ ] Use the proof-pack/evaluation schema to measure governed AI coding
      quality deltas: finding count change, severity distribution,
      false-positive rate, repair-loop count, and context cost.

## Session Resume

- Current goal: clear the blocker tranche that protects the authority loop,
  then finish making the authority loop the top `MP-377` priority before
  broader platform growth continues.
- Current architecture verdict from multi-agent audit: the target abstraction
  is correct, but runtime authority is still split across VoiceTerm defaults,
  prose parsing, transitional markdown bridges, and compatibility reducers.
- Current live reviewer/coder status: `ProjectGovernance` and
  `governance-draft` have landed on the dirty tree; the bounded Phase 1 guard
  slice is `check_startup_authority_contract.py`, and Codex still owes a
  fresh re-review on the current tree before promoting the next closure item.
- Current external-research intake status: local comparison repos now live
  under `dev/repo_example_temp/` (gitignored on purpose) and should be treated
  as calibration material for the `MP-377` least-effort-first retrieval /
  authority stack, not as alternate authority or copy-paste source.
- Session compass for fresh reviewer/coder sessions:
  - Product: VoiceTerm is being extracted into a portable AI governance
    platform that improves AI coding quality through deterministic
    enforcement, evidence capture, and closed feedback loops.
  - Startup rule: the bounded startup packet should begin with the repo's
    short product thesis (`Why Stack`) before procedural/router detail.
  - Current priority: blocker tranche first, then `MP-377` `P0` / Phase 1
    startup-authority closure.
  - Authority spine:
    `ProjectGovernance -> RepoPack -> PlanRegistry -> PlanTargetRef -> WorkIntakePacket -> CollaborationSession -> TypedAction -> ActionResult / RunRecord / Finding -> ContextPack`.
  - Blocker tranche scope: daemon attach/auth hardening, autonomy authority
    hardening, JSONL/evidence-integrity closure, and self-governance
    coverage. Finish those before promoting the next startup-authority slice.
  - After that blocker set closes, the first promoted Phase 1 follow-on is the
    least-effort-first guard spine now recorded in this file:
    `UNKNOWN/DEFER` outcomes, decision-path metadata, determinism checking,
    escalation tiers, and SHA256 proof packaging.
  - After that five-item batch closes, the next broader Phase 1 closure items
    remain generated `project.governance.json`, `PlanRegistry`,
    `startup-context`, `WorkIntakePacket`, and `CollaborationSession`
    projection materialization.
  - Do not widen the current slice into anchor-grammar implementation,
    frontend cleanup, or broader review-channel simplification.
  - Context-loading rule: hot = this session compass plus the live bridge
    instruction, warm = only the plan/runbook sections for the active slice,
    cold = broad reference docs such as `SYSTEM_AUDIT.md`. Cold docs do not
    override the active plan chain.
  - ZGraph / `ConceptIndex` is generated navigation for bounded retrieval over
    canonical pointer refs; it does not replace the typed startup/authority
    chain or create a second semantic authority store.
  - Accepted native path for that graph work: first freeze repo-owned pointer
    rows and typed edges, then add a report-only `devctl` query surface over
    existing artifacts before any heavier storage/index acceleration.
  - Accepted next graph rollout order: checkpoint the current bounded
    context-escalation proof first, then widen the same packet shape through
    backend instruction emitters (review-channel promotion/event surfaces and
    fresh `swarm_run` prompts), then run the cross-surface validation bundle,
    then evaluate richer graph capabilities such as transitive blast radius,
    test-to-code, and self-service queries.
  - Checkpoint-boundary rule: graph/context compression may explain candidate
    scope, but push/checkpoint truth remains canonical git/plan/guard/review
    evidence and must fail closed by narrowing the batch when graph confidence
    is weak.

## Progress Log

- 2026-03-21: Finished retiring `temp_leftoff.md` as execution state for this
  lane. The remaining packet field mapping and graph/query intake conclusions
  were verified against the governed plans and kept in canonical plan state
  here / `MASTER_PLAN` instead of leaving a scratch markdown dependency in the
  push path. The temporary scratch file is now disposable rather than a hidden
  source of sequencing truth.
- 2026-03-21: Audited the fresh plan-format and N-agent follow-up claims
  against the current repo instead of older scratch notes. The discovery /
  enforcement part of the plan-doc contract is now genuinely wired: active-plan
  sync and doc-authority both require metadata headers plus `Session Resume`,
  and the newer execution-plan docs are already inside the blocking contract.
  The remaining gaps are narrower but real: only `## Execution Checklist` is
  consumed as structured plan state today, plan mutation ops are still
  contract-only without runtime apply handlers, and the future `PlanRegistry`
  / `ContextPack` read path still needs to ingest `Session Resume`, progress,
  and audit context without treating governed plans as opaque files.
- 2026-03-21: Corrected the plan-self-hosting audit against the actual code
  surface. The repo already has meaningful typed governance/runtime contracts
  in code (`ProjectGovernance`, `TypedAction`, `ActionResult`, `Finding`,
  `DecisionPacket`, `ReviewState`, packet target fields, doc-authority
  scanning, and multiple contract guards), so the main gap is no longer "build
  plan infrastructure from zero." The active self-hosting gap is narrower and
  more concrete: freeze one governed plan markdown format, extend the existing
  active-plan/docs-governance path instead of inventing a parallel checker,
  migrate `Session Resume` into the execution-plan baseline, and then let the
  future `PlanRegistry` / `PlanTargetRef` loader consume a repo that already
  follows its own contract.
- 2026-03-21: Connected the checkpoint/push packet spec to research repo
  pattern sources. Added rolling batch-size percentiles field (changed files
  per checkpoint, LOC per push, guard pass rate per bundle) so calibration
  becomes empirical — pattern sources: P-07 metrics tracker, P-15 performance
  model, P-19 density profiling. Added explicit sequencing: Phase 1A guard
  spine → packet contract → calibration → broader graph work. Added pattern
  source cross-references plus the field-to-pattern mapping directly to the
  packet checklist item. The accepted order from Codex's design is now kept
  in governed plan state: (1) checkpoint current slice, (2) fail-closed
  checkpoint-budget enforcement, (3) packet + cache layer, (4) calibrate from
  telemetry instead of fixed 12/6 thresholds.
- 2026-03-21: Promoted the merged Codex/Claude external-research synthesis
  from temporary Codex/Claude scratch planning into the canonical Phase 1
  execution spec. Added the five-item least-effort-first guard spine with
  concrete file targets and guard contracts: explicit `UNKNOWN/DEFER`
  outcomes, decision-path metadata, hash-based determinism verification,
  frozen escalation tiers, and SHA256 proof packaging. Sequencing is now
  locked as post-blocker / pre-graph-widening, and the
  authority/generated-only split remains explicit: deterministic rule outputs
  plus canonical refs stay authoritative, while traces, hashes, graph
  aliases, ML confidence, and proof bundles stay generated evidence only.
- 2026-03-21: While the first `UNKNOWN/DEFER` slice was in flight, the live
  review bridge exposed a real coordination bug: the reviewer-owned current
  instruction remained authoritative, but `Claude Ack` regressed to an older
  instruction token. The canonical plan and the in-progress code edits were
  not lost, but a started slice can be stranded or duplicated if markdown
  bridge state moves backward during active coding. Preserve the current slice
  first; then treat the next reviewer-owned structural fix as mandatory:
  heartbeat/checkpoint/projection paths must stop rewriting live instruction
  state, and the bridge must converge on one monotonic, lease-owned typed
  `CollaborationSession` authority path.
- 2026-03-21: Landed the first bridge-backed checkpoint-budget read path for
  the authority-loop follow-up. `review-channel --action status` now loads the
  repo-governance `push_enforcement` snapshot, projects that state into the
  generated review-channel payloads, and escalates attention to
  `checkpoint_required` when the worktree is over the continuation budget.
  `implementer-wait` now treats that status as loop-blocking so the live
  Codex/Claude bridge stops widening an over-budget dirty tree before a
  checkpoint is cut. The same docs-governance pass hardened
  `check_markdown_metadata_header.py` to ignore directories named `*.md`, so
  local comparison repos under `dev/repo_example_temp/` do not create false
  markdown-header scan targets.
- 2026-03-21: Accepted the next startup-acceleration direction for the same
  authority-loop lane: emit a repo-pack-owned checkpoint/push packet into a
  managed artifact/cache root, then let `startup-context` and later
  `ContextPack` consume it as an optional warm-start accelerator. This cache
  must remain generated-only and disposable: it is invalidated by tree-hash /
  content-hash drift, never hand-edited, and never authoritative over git
  state, active plans, repo policy, or guard/review truth. Performance target
  is "read the packet when fresh, recompute from canonical sources when not"
  so startup gets faster without adding a second memory authority or a hard
  dependency on cache regeneration.
- 2026-03-21: Claude completed full parallel audit of all 11 external research
  repos using 4 domain-specialized agents (ZGraph, A-star/Dijkstra, prime
  engines, ML/trace). Catalogued 55 reusable patterns in raw form
  (`dev/repo_example_temp/CLAUDE_AUDIT_FINDINGS.md`), then merged the
  synthesis into governed planning state using Codex's 7-question framework
  and expected output shape. Key convergent finding across both agents:
  deterministic least-effort-first is the universal
  pattern in every research repo and maps directly onto the guard/probe/startup
  escalation stack accepted for `MP-377`. Agreed first local fix: add explicit
  UNKNOWN/DEFER guard states, decision-path metadata, hash-based determinism
  checking, formalized escalation tiers, and proof packaging — all from
  architectural patterns only, no imported code. Strongest portable signals:
  `astarihope-main` for staged escalation/proof/telemetry contracts,
  `June17th` + `ML_Dump_Trace_V2` for layered dispatch + ZRef traces +
  dual deterministic-ML routing, `zgraph-scientific-package` for reversible
  relation/inference/transformer stacks (generated-only, never authority).
  `Nasa_Export-main` confirmed as packaged evidence/export only.
- 2026-03-21: Staged the first external research-intake lane for the
  authority-loop work under local-only `dev/repo_example_temp/` and verified
  the intake root is gitignored so imported repos do not leak into product
  history. The next shared Codex/Claude slice should audit those repos as
  calibration material for the same deterministic least-effort-first stack
  already accepted here: canonical evidence/contracts stay authoritative,
  cheap deterministic guards/probes classify first, generated ConceptIndex /
  ZGraph layers reduce search space second, bounded `startup-context` /
  `ContextPack` reconstruction follows third, and expensive AI loops remain
  fallback/controller layers only. First confirmed signal from the intake:
  `dev/repo_example_temp/June17th******** 2 copy 2/` contains a real reusable
  staged dispatcher with explicit decision-path output (`utils.py`,
  `optimized_primes.py`, `universal_benchmark.py`, `smart_auto_dispatcher.py`);
  `Nasa_Export-main` looks mostly like packaged evidence/export surfaces rather
  than reusable bounded-search implementation. Treat the imported repos as a
  source for minimal typed scheduler/query ideas, proof/eval patterns, and
  confidence/fallback rules that can strengthen this repo's graph/query stack
  without turning generated graph artifacts into a second authority store.
- 2026-03-21: Landed the first repo-pack-owned push-routing slice under the
  authority-loop plan. `repo_governance.push` is now the single policy surface
  for default remote, development/release branches, protected branches,
  preflight routing, and post-push bundle selection; `devctl push` consumes it
  as the canonical short-lived branch push surface with `TypedAction(action_id:
  vcs.push)` plus `ActionResult` output; `sync` and `ship` now read the same
  policy instead of hardcoding `origin/develop/master`; and starter repo policy
  generation plus starter hook surfaces now seed the same push contract for
  adopters.
- 2026-03-21: Folded the deeper context-graph runtime audit into `MP-377`
  Phase-6 scope. The graph is still intentionally bounded, but the missing
  runtime gaps are now tracked explicitly: command nodes need closure to real
  handlers, heuristic/orphan semantic edges need fail-closed honesty rules,
  the first typed `startup-context` / `WorkIntakePacket` reducer must replace
  prose-only least-effort guidance, and later graph widening must cover live
  routing inputs plus symbol/test/finding/workflow/config/iOS surfaces.
- 2026-03-21: Added the missing warm-start/session-delta rule to the same
  authority-loop lane. First startup seeds canonical artifacts, later
  sessions refresh only the invalidated slices by content hash + git diff, and
  the same startup family must still work from JSON artifacts when the SQLite
  runtime cache is not active yet.
- 2026-03-21: Named the accepted retrieval/control stack explicitly for
  `MP-377` Phase 6 and later controller work. Cheap deterministic
  guards/probes classify first, `ConceptIndex` / ZGraph reduces the candidate
  scope second, `startup-context` / `ContextPack` reconstruct the bounded
  cited working slice third, and the review/autonomy/Ralph loops are the
  expensive fallback/controller layer on top. This keeps graph/context
  surfaces generated-only and prevents the live controller path from sliding
  back into whole-repo bootstrap blobs as implicit authority.
- 2026-03-21: Accepted the next bounded Phase-6 graph order after landing the
  first repo-owned context-escalation slice. The current green/docs-synced
  packet path should be checkpointed before widening scope again. Immediate
  next backend slice: attach the same generated packet to review-channel
  promotion/event instructions and fresh `swarm_run` prompts, then validate
  that review-channel, autonomy, Ralph, and direct `context-graph --query`
  outputs cite the same canonical refs for the same scope. Richer graph
  capabilities such as transitive blast radius, test-to-code edges, and
  self-service queries remain explicitly later work.
- 2026-03-20: Accepted the native `devctl` context-graph direction as the
  right `MP-377` Phase-6 shape instead of introducing an external semantic
  store first. The architecture rule is now explicit here: canonical plans,
  docs, repo-map/report artifacts, and future evidence rows remain pointer
  authority; `ConceptIndex` and any ZGraph-compatible encoding are generated
  navigation/compression layers over those pointers; and every hot/warm/cold
  retrieval result must expand back to cited canonical refs. The first
  implementation path should stay report-only and repo-owned.
- 2026-03-20: Landed the first real `MP-377` Slice-1 `doc-authority`
  correction pass against the repo code, not just the plan text. The command
  now derives governed-doc scan roots from `ProjectGovernance` plus repo
  policy instead of a hardcoded VoiceTerm path list, uses `dev/active/INDEX.md`
  roles as the primary classifier (`tracker` / `spec` / `runbook` /
  `reference`), applies the accepted class budgets (`guide` hard limit
  `1500`), scopes registry coverage to active docs that `INDEX.md` is
  actually responsible for, and treats root governance / bridge docs as
  distinct non-plan governed surfaces. The implementation was also split into
  `doc_authority_{models,metadata,layout,rules,support}.py` so the new slice
  self-hosts under the repo's own Python shape / dict-schema / complexity
  guards instead of shipping as one oversized blob.
- 2026-03-20: Tightened the docs-authority mechanics from high-level idea into
  executable startup/governance steps. `ProjectGovernance` now needs
  doc-policy refs plus class/lifecycle/budget fields, `DocRegistry` is a
  first-class companion to `PlanRegistry`, `startup-context` must expose a
  bounded doc subset, and the first command for this work is now explicit:
  `devctl doc-authority --format md` as a read-only authority/format/budget
  scan for reviewer/coder sessions before write-mode normalization lands.
- 2026-03-20: Closed the `governance-draft` discovery/docs drift on the repo
  command surface. The command now appears in `devctl list`, the maintainer
  command reference and quick-start surface mention the deterministic
  repo-scan entrypoint, and the development guide now states that any added or
  renamed `devctl` command must keep the CLI inventory and maintainer docs in
  sync in the same change.
- 2026-03-20: Promoted the docs system from implicit background concern to
  explicit authority-loop architecture. The current repo has pieces of a docs
  system (`INDEX` roles, `PlanRegistry` direction, `docs-check`, active-plan
  sync, hygiene), but not one unified documentation contract. This plan now
  requires `ProjectGovernance` to carry a repo-pack-owned `DocPolicy`,
  introduces a broader `DocRegistry` companion to `PlanRegistry`, adds
  bounded doc subsets to `startup-context`, and freezes markdown
  schema/formatter expectations so governed docs can become structured,
  consistent, and guardable across repos.
- 2026-03-20: Accepted one more architecture-governance follow-up from the
  repo-root `SYSTEM_AUDIT.md` intake. The audit should not remain a second
  living roadmap after review. Once blocker-tranche findings are integrated
  into canonical plan/docs, later self-hosting cleanup should extend the
  existing package-layout / compatibility-shim direction into a broader
  structure-policy layer and retire the repo-root audit copy after its
  accepted items are fully absorbed or explicitly rejected.
- 2026-03-20: Corrected the authority-loop order after the code-backed
  multi-agent audit review. `SYSTEM_AUDIT.md` remains reference evidence, but
  its confirmed blocker tranche now precedes the remaining Phase 1 spine:
  daemon attach/auth hardening, autonomy authority boundaries,
  JSONL/evidence-integrity closure, and self-governance coverage land before
  the next startup-authority closure slice. The same review also froze the
  startup-family rule here: `startup-context`, `WorkIntakePacket`,
  `CollaborationSession`, and later `ContextPack` are the only startup/session
  packet family; `ConceptIndex` / ZGraph remains a later generated navigation
  layer above canonical artifacts, not a replacement authority surface.
- 2026-03-20: Reconciled the repo-root `SYSTEM_AUDIT.md` against the current
  authority-loop lane instead of treating it as a new execution plan. Accepted
  its four headline gaps as corroboration, not redirect: (1) the closed AI
  feedback loop remains the highest-leverage missing behavior and must land
  through `startup-context` / `ContextPack` plus automatic governance-quality
  intake, not a sidecar note; (2) bootstrap bloat should be reduced with a
  hot/warm/cold session-compass model rather than repeated cold reads of the
  whole doc stack; (3) portability remains the repo-pack/path-authority
  closure already tracked in Phases 1-2; and (4) review-channel / guard
  boilerplate simplification remains follow-up cleanup after the authority
  loop is closed. The stale `dev/scripts/here.md` handoff file is retired in
  favor of the session-resume/bridge chain.
- 2026-03-19: Validated the post-contradiction final review against the
  repo-visible plans and accepted only the confirmed follow-ups into the
  execution spec. Later phases now have explicit closure gates for Phase 3,
  Phase 4, Phase 5b, Phase 6, and Phase 7; `check_platform_contract_closure.py`
  is now named as a Phase 5b dependency as the contract surface expands;
  non-VoiceTerm adopters now have a concrete definition for what counts as a
  canonical plan authority doc; and Phase 6 now names `startup-context`,
  `master-report`, and packet-outcome ingestion as the first `ContextPack`
  consumers. Also added one non-blocking Phase 8 follow-up to evaluate
  optional MCP exposure as an adoption vector while preserving the existing
  `devctl`-first authority model.
- 2026-03-19: Tightened the execution slice after external review confirmed
  the architecture call was right but a few Phase 1/2/5a mechanics were still
  too implicit. The plan now makes Phase 1 closure criteria explicit
  (`project.governance.md` + generated machine form + `plan_registry.json` +
  `startup-context` / `WorkIntakePacket` + `CollaborationSession`
  projection + guard/tests), promotes anchor-grammar freeze into an explicit
  Phase 1 deliverable and Phase 3 prerequisite, bounds the first repo-pack
  migration batch to startup/review-channel/operator-console surfaces instead
  of leaving the first batch undefined, and states Phase 5a as live parallel
  work that must begin alongside the first Phase 2/3 implementation slice.
- 2026-03-19: Final architecture review reconciled the validated runtime
  slice with the broader architecture draft and froze the remaining `P0`
  choices in repo-visible plan state. Accepted: keep `WorkIntakePacket` and
  `CollaborationSession` separate for now, keep intake-backed writer leases
  as authority, keep startup auto behavior limited to inspect/refresh /
  resume-one / auto-demote / emit-intake, and make single-agent vs
  multi-agent benchmarking part of Phase 7 proof rather than an informal
  claim. The next execution slice remains generated governance + plan
  registry artifacts, `startup-context`, `CollaborationSession`
  projections, repo-pack activation, and Phase 5a identity freeze.
- 2026-03-19: Ran a portable-planning-loop proof pass after the first doc
  patch and tightened the missing execution details instead of leaving them as
  convention. `WorkIntakePacket` now has to freeze writer-lease semantics for
  planning review before Phase 4, `PlanTargetRef` now requires registry-
  generated collision-free anchor ids plus a fail-closed anchor grammar,
  allowed plan mutation ops are explicit, the minimum non-VoiceTerm bootstrap
  artifact set is now part of Phase 7 proof, and the headline authority spine
  now includes `PlanTargetRef` plus `WorkIntakePacket`.
- 2026-03-19: Accepted the portable planning-review loop as part of the
  authority spine instead of treating it as a repo-specific workflow trick.
  The plan now requires repo-neutral `PlanTargetRef` and `WorkIntakePacket`
  contracts, reuses review-channel packets for `plan_gap_review`,
  `plan_patch_review`, and `plan_ready_gate`, and resolves mutable plan
  targets by stable heading/checklist/progress anchors plus target revision
  instead of brittle block-context matching or raw line numbers. Canonical
  plan docs remain single-writer authority; bridge artifacts stay
  coordination-only.
- 2026-03-19: Accepted an additional transition-mechanics validator pass and
  tightened the authority-loop plan where the architecture was right but the
  cutover path was underspecified. The plan now splits evidence work into a
  Phase 5a identity freeze before Phase 4 and a Phase 5b provenance/ledger
  closure after it, stages Phase 2 as a compatibility-first repo-pack rollout
  instead of a one-shot cutover, makes legacy governance-review backfill /
  upgrade work explicit before hard schema enforcement, names `MP-359`
  Operator Console path migration as a Phase 2 dependency, and defines Phase
  7 proof criteria around portable versus repo-structure-only guards.
- 2026-03-19: Added this subordinate `MP-377` execution spec after repeated
  architecture audits converged on the same missing spine: the repo has
  partial startup docs, repo packs, runtime contracts, evidence ledgers, and
  context references, but they do not yet form one closed authority loop.
  Captured the accepted order explicitly: startup authority first, repo-pack
  activation second, typed plan registry third, one runtime slice fourth,
  evidence/provenance closure fifth, context contract sixth, and cross-repo
  proof seventh. Also recorded the extra audit follow-ups that were missing
  from the first draft: full `active_path_config()` rewrite scope, bundle/
  plugin extensibility, provenance tracing, structured plan schema, and
  observability as backend-owned state rather than chat habit.
- 2026-03-19: Tightened the same plan after a second multi-agent review pass
  found a few remaining architecture gaps. The authority-loop spec now also
  names the startup cache/repo-intelligence layer, runtime lifecycle and
  caller-authority contract, portable review identity plus reviewer-topology
  closure, contract-family compatibility matrices, ledger integrity/repair
  rules, aggregate `master-report` / `converge` governance-quality surfaces,
  bidirectional memory/context bridge requirements, stronger proof-pack inputs,
  and extension/adopter conformance packs.
- 2026-03-19: Accepted one more validator pass and made the remaining tactical
  commitments explicit in the execution spec: the repo-pack rewrite now names
  the dependency-injection pattern, `.voiceterm` path-family migration, and
  config-driven guard/probe/bundle overrides; the first runtime slice now
  explicitly pushes provider-specific review inference into adapters; the
  evidence layer now requires quality-to-cost telemetry (`model_id`,
  `token_count`, `context_budget`, `cost_usd` where available); and the lane
  now requires direct test coverage for authority-loop closure guards.

## Audit Evidence

- External-research intake archive (2026-03-21): the raw scratch synthesis
  that originally lived in `temp_leftoff.md` is now preserved as governed
  reference evidence in
  `dev/archive/2026-03-21-external-research-intake.md`; execution-affecting
  conclusions remain promoted into this plan, `MASTER_PLAN`, and the related
  review/push portability plans.
- Push-governance slice verification (2026-03-21): targeted unit coverage now
  includes `dev/scripts/devctl/tests/test_push.py`,
  `dev/scripts/devctl/tests/test_ship_release_steps.py`,
  `dev/scripts/devctl/tests/governance/test_governance_draft.py`, and
  `dev/scripts/devctl/tests/governance/test_governance_bootstrap.py`. The
  implementation also updates the repo policy, CLI inventory, maintainer docs,
  and starter hook surfaces so the new command is governed by the same
  policy-driven path as `check-router`, `docs-check`, and `render-surfaces`.
- Docs-authority slice verification (2026-03-20): `python3 -m pytest
  dev/scripts/devctl/tests/governance/test_doc_authority.py -q --tb=short`
  passed (`30/30`). `python3 dev/scripts/devctl.py doc-authority --format md`
  now reports `42` governed docs with `100.0%` active-doc registry coverage
  (`25/25`) instead of the earlier misleading all-doc denominator, and
  `dev/active/loop_chat_bridge.md` is now classified as `runbook` from the
  `INDEX.md` role rather than a fake `execution_plan`. Sync/governance checks
  `check_active_plan_sync.py`, `check_multi_agent_sync.py`, and
  `check_instruction_surface_sync.py` passed. Targeted Python guard reruns
  `check_python_dict_schema.py`, `check_python_design_complexity.py`, and
  `check_parameter_count.py` passed after the refactor. `check_code_shape.py`
  and `python3 dev/scripts/devctl.py check --profile ci` remain red only for
  the unrelated pre-existing soft-limit regression in
  `dev/scripts/devctl/governance/parser.py`. `docs-check --strict-tooling` and
  `hygiene` remain unchanged with the existing bundle/AGENTS drift and
  README/publication drift outside this slice.
- Transition-mechanics validator pass (2026-03-19): confirmed that the main
  authority-loop abstraction is correct but the current repo state needs
  explicit migration handling. Current audited baselines: `17` modules still
  freeze `active_path_config()` at import time, `107` legacy governance-
  review rows currently lack `schema_version`, and the Operator Console tree
  has `161` Python files with `23` direct `devctl` imports.
- Multi-agent architecture audit (2026-03-19): accepted the authority-loop
  abstraction and confirmed that the main remaining blockers are startup
  authority, repo-pack activation, plan-registry typing, runtime/evidence
  closure, and portable context boundaries rather than missing feature ideas.
- Static code audit of current seams (2026-03-19): confirmed that portability
  is currently blocked less by business logic than by hidden defaults and
  transitional authority paths:
  `active_path_config()` import-time freezes, VoiceTerm-default repo packs,
  markdown/prose plan scraping, split finding identities, and path-based
  context refs.
