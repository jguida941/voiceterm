# Autonomous Governance Loop V2 Plan

**Status**: active  |  **Last updated**: 2026-05-01 | **Owner:** Tooling/control plane/product architecture
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under
`MP-377`. It is a bounded convergence plan for closing the autonomous
governance loop over existing typed repo authority, not a second backend or a
second product plan.

## Scope

Use this file when the work is specifically about turning the existing
governed surfaces into one closed loop:

`StartupContext / WorkIntakePacket -> PlanningIRSnapshot / findings-priority -> ControlPlaneReadModel / AutoModeState / MonitorSnapshot -> governed commit/push/review actions -> FindingReview / GuardPromotionCandidate / KnowledgeSynthesisRecord -> generated graph/pointer/startup projections -> next-session prompt`

This plan covers:

1. Loop-v2 design and implementation sequencing over the existing typed
   authority/runtime/evidence contracts rather than another bespoke
   controller.
2. Priority ordering between "make the system see correctly" work and actual
   implementation work so the loop selects the right slice before it edits.
3. Graph-backed and contract-backed discoverability so an AI can find the
   right surfaces from typed state and repo-owned commands, not only from
   maintainer filename knowledge.
4. A typed next-slice and next-prompt pipeline that derives from startup,
   planning, findings, and runtime state instead of operator prose.
5. Guard-promotion-by-default closure so repeated or adjudicated issues flow
   into `governance-review` and `GuardPromotionCandidate` instead of ending as
   patch-only work.
6. Research and synthesis closure so local code research, approved external
   research, dogfood evidence, recurring findings, and architecture patterns
   become typed knowledge artifacts that feed plan, guard, `context-graph`,
   system-map, pointer, and startup surfaces with provenance.

Out of scope for this plan:

1. Dashboard implementation details. The dashboard remains a consumer handled
   in a separate session.
2. A provider-specific verdict-file controller.
3. New shadow state stores, loop-local markdown truth, or dashboard-local
   authority.
4. A separate semantic authority store. ZGraph-compatible and pointer surfaces
   remain generated navigation/compression outputs over typed canonical sinks.

## Locked Decisions

1. Loop v2 is a composition layer over existing typed surfaces, not a new
   backend. If a required signal already exists in startup, planning, review,
   graph, or governance state, loop v2 must consume that signal rather than
   recreate it.
2. `dev/active/ai_governance_platform.md` remains the only main `MP-377`
   product plan. This file is a bounded subordinate execution spec.
3. `platform_authority_loop.md` keeps ownership of startup/work-intake/plan
   routing, `remote_commit_pipeline.md` keeps ownership of governed
   commit/push, `review_channel.md` and `continuous_swarm.md` keep ownership
   of review/runtime transport, `autonomous_control_plane.md` keeps ownership
   of the autonomy harness, and `remote_control_runtime.md` keeps ownership of
   remote-control runtime truth. This plan sequences their composition.
4. Operator prose may constrain or override work only through repo-visible
   typed state or approved packets. It must not be the primary next-session
   prompt source.
5. `ContextGraphSnapshot` and `system-picture` are discovery and evidence
   surfaces, not runtime authority. Loop v2 may use them to select, verify,
   and explain work, but never as a replacement for startup/review/runtime
   contracts.
6. The first implementation priority is visibility closure, not more coding
   throughput. A loop that cannot reliably see the system state should fail
   closed before it edits.
7. Guard-promotion and finding disposition are part of the main loop. Repeated
   issues do not count as closed until they route into a prevention surface or
   receive an explicit waiver.
8. `/develop` uses the typed `DevelopmentModeTopology`, not provider defaults
   or a fixed team roster. Any provider or human may occupy any workstream when
   typed authority grants the required capabilities. Research may include
   approved web/vendor/library sources only through a route grant, cited
   provenance, and a synthesis path back into canonical plan/guard/contract
   sinks. `context-graph`, ConceptIndex/ZGraph-compatible outputs, pointer
   refs, and system-map consume the promoted artifacts as generated projections,
   never as runtime authority.
9. Packet-carried work ingestion is a first-class `/develop` concern. A
   dedicated Plan Intake Steward workstream classifies packets for plan,
   finding, guard, probe, or architecture intent and promotes that content into
   durable MasterPlan/PlanRow, FindingReview, GuardPromotionQueue, or knowledge
   artifacts with packet ids retained as provenance before TTL expiry. Packets
   are communication and provenance; they are not the source of truth.
10. `/develop` scaling is pressure-driven typed topology, not a vague worker
    count. The named modes are Controller Only, Intake Fanout, Review Fanout,
    Research Fanout, Watcher Fanout, Isolated Builder Fanout, and Leased
    Live-Tree Builder. Packet/work pressure may add read-only, intake, review,
    research, synthesis, and watcher lanes, but mutable fanout requires
    `safe_to_fanout`, disjoint scopes, worktree/orphan clearance, and explicit
    leases. The primary checkout still has one leased live-tree builder.

## Data Contracts

Loop v2 must compose these existing contract families directly:

1. Startup authority:
   `StartupContext`, `WorkIntakePacket`, `PlanTargetRef`,
   `WorkIntakeOwnershipState`, `WorkIntakeCoordinationState`,
   `SessionPacingState`.
2. Planning and intake:
   `PlanningIRSnapshot`, `NextBestSliceRecord`, `findings-priority`,
   `system-picture`.
3. Runtime state:
   `ControlPlaneReadModel`, `AutoModeState`, `MonitorSnapshot`,
   typed `review_state.json`, and review-channel status/doctor projections.
4. Governed mutation:
   `TypedAction`, `ActionResult`, `RunRecord`, the governed commit pipeline,
   and `devctl push --execute`.
5. Learning and absorption:
   `FindingReview`, `QualityFeedbackSnapshot`, and `GuardPromotionCandidate`.
6. Graph evidence:
   `ContextGraphSnapshot` and `ContextGraphDelta`.
7. Development topology and knowledge flow:
   `DevelopmentModeTopology`, `DevelopmentExternalResearchContract`,
   `DevelopmentKnowledgeFlowContract`, `DevelopmentScalingContract`,
   `DevelopmentScaleModeSpec`, `ResearchEvidenceBundle`,
   `ExternalSourceEvidence`, `KnowledgeSynthesisRecord`, `ContextGraphSeed`,
   `PointerRefIndexEntry`, `PacketLifecycleHistory`, `PacketOutcomeLedger`,
   `PacketDurableIngestionReceipt`, `PacketCreationBinding`,
   `PacketDebtRemediationReport`, `PacketContinuityIndex`,
   `PacketBacklogPressure`, `WorkerPacket`, `FanoutPlan`, and
   `OrphanSnapshot`.

Current design-relevant gaps observed in this session:

1. `findings-priority` can rank `LIVE_RUN.md` entries, but most top findings
   still have `(no source-file match)` and `fan_out=0`, so they cannot drive
   precise slice selection yet.
2. `context-graph` resolves concrete file-path queries well, but abstract
   contract-name queries such as `AutoModeState` or `GuardPromotionCandidate`
   currently return no matches.
3. `system-picture` is useful, but the latest saved graph snapshot can be
   stale and may report `plan_count=0`, so loop v2 needs an explicit stale
   graph policy.
4. `SessionPacingState`, `findings-priority`, and `AutoModeState` are all
   emitted today, but they are still mostly advisory projections rather than
   the controller's actual decision inputs.
5. Review-channel projections can carry stale instructions from an inactive
   loop, so loop v2 must treat them as evidence to reconcile, not as the sole
   next-action authority.

## Execution Checklist

Execution order note:
Implement visibility and discoverability closure before automated editing
closure. The correct order is:
`0 visibility -> 1 slice selection -> 2 phase controller -> 3 guard promotion -> 4 governed proof`

### Phase 0 - Visibility And Discoverability Closure

- [ ] Freeze the loop-v2 intake contract: every fresh loop tick must load
      `startup-context`, `review-channel status`, `auto-mode`, `monitor`, and
      `system-picture` before selecting work.
- [ ] Define the stale-evidence policy for loop ticks:
      stale graph snapshots, stale review instructions, and missing current
      runtime evidence must trigger refresh-or-block behavior instead of
      silent best-effort continuation.
- [ ] Add contract and command discoverability strong enough that abstract AI
      queries can resolve `AutoModeState`, `GuardPromotionCandidate`,
      `SessionPacingState`, `PlanningIRSnapshot`, and the relevant `devctl`
      commands without already knowing the file paths.
- [ ] Ground `LIVE_RUN.md` findings into repo paths, plan targets, or typed
      issue clusters so `findings-priority` stops returning mostly zero-fanout
      rankings.
- [ ] Add one canonical `FindingBacklog` reader/writer and route
      `review-channel` finding intake plus `LIVE_RUN.md` compatibility import
      through it so `findings-priority`, dashboard, startup, monitor, and
      bridge projections stop ranking different open-finding sets.
- [ ] Converge the launch-critical visibility stack before controller work:
      `StartupContext`, `ControlPlaneReadModel`, dashboard/status/monitor/
      mobile/phone, and packet queue surfaces must agree on `top_blocker`,
      `next_action`, `implementation_permission`, and open findings from one
      reducer-backed snapshot rather than four vocabularies.
- [ ] Freeze one shared packet lifecycle and wake contract for loop ticks:
      posted -> delivered -> observed/acked/applied -> execution receipt ->
      resolved/expired, with all agent/dashboard lanes waking on event-backed
      state change instead of timer polling.
- [ ] Surface live tool-call and mutation progress through typed
      `agent-mind` / current-session state so observer lanes do not infer
      "idle" from message silence.
- [ ] Make graph freshness and coverage visible in the same startup-facing
      packet the loop consumes, not only in a sidecar report.
- [ ] Wire knowledge artifacts into generated graph/pointer surfaces:
      promoted `KnowledgeSynthesisRecord`, `ContextGraphSeed`, and
      `PointerRefIndexEntry` rows must rebuild `ContextGraphSnapshot`,
      system-map connectivity, ConceptIndex/ZGraph-compatible views, ContextPack,
      and startup-context from canonical sinks rather than from chat notes.

### Phase 1 - Next Slice Selection

- [ ] Compose one canonical slice selector from
      `WorkIntakePacket.active_target`,
      `SessionPacingState.focus_slice_id`,
      `PlanningIRSnapshot.next_best_slices`,
      `findings-priority`, and open `governance-review` findings.
- [ ] Define one deterministic priority rule:
      visibility and authority blockers first, then stale review/runtime
      blockers, then the highest-ranked bounded implementation slice, then
      cleanup/promotions.
- [ ] Derive the loop's next-session prompt from typed slice-selection output
      instead of operator prose or bridge-local instruction text.
- [ ] Treat Phase 1 as blocked until the highest-ranked Phase 0 findings have
      file/plan owners and non-zero fanout. No prompt derivation, controller
      widening, or `devctl develop` rollout while the top `findings-priority`
      rows remain ungrounded visibility debt.
- [ ] Keep worker fanout gated by the selected plan target, ownership state,
      and coordination posture. No loop tick may infer "parallelize" from
      stale planned topology alone.
- [ ] Compile packet/work pressure into the named `DevelopmentScalingContract`
      modes before launching extra lanes. Intake/review/research/watcher
      fanout is allowed only when each lane has a `WorkerPacket`, owner,
      scope, evidence contract, reply target, and TTL; mutable fanout also
      needs `safe_to_fanout`, `OrphanSnapshot` clearance, disjoint path scopes,
      and a session-bound lease.

### Phase 2 - Phase Controller Over Existing Runtime

- [ ] Make loop v2 consume `ControlPlaneReadModel`, `AutoModeState`, monitor
      self-audit, and review/runtime state to choose between review, implement,
      test, commit, push, resync, or observe-only phases.
- [ ] Define `devctl develop` as the single self-driving entrypoint that
      composes startup authority, plan selection, `FindingBacklog` /
      `findings-priority`, packet lifecycle, and governed commit/push over the
      existing deterministic runtime layer rather than creating a new
      controller root.
- [ ] Load `DevelopmentModeTopology` at controller start and route work through
      user-facing workstreams: Coordinator, Builder, Reviewer, Plan Intake
      Steward, Researcher, Knowledge Synthesizer, Architect, Quality Engineer,
      Dogfood Tester, Runtime Watcher, and Operator. These names are UX labels
      only; runtime authority still comes from `AuthoritySnapshot`,
      `AgentDispatchRouter`, packet scope, and mutation leases.
- [ ] Make packet intent ingestion part of the controller loop: packets near
      expiry, packets archived as `clock_expired_without_disposition`, outcome
      rows claiming `promoted_to_finding`, and ambiguous actor/session packet
      ownership must route to Plan Intake Steward for durable plan/finding/
      guard/knowledge ownership before the packet leaves the live queue.
- [ ] Make pressure scaling observable in controller reports: show the active
      scaling mode, pressure inputs, lane budget, worker packet ids, safety
      gates, scale-in reason, and whether live-tree mutation is leased or
      unavailable.
- [ ] Make the controller state-driven and event-woken: valid next actions
      come from typed state plus ownership posture, and polling survives only
      as a degraded fallback when the event stream is unavailable.
- [ ] Reuse existing autonomy harnesses (`autonomy-loop`, `swarm_run`,
      review-channel runtime, governed commit/push) instead of inventing a
      provider-specific verdict-file controller.
- [ ] Fail closed when implementation authority is blocked, the reviewer loop
      is inactive/stale, or commit/push approval state is unavailable.
- [ ] Make phase selection explainable through typed fields that can be shown
      in startup, monitor, and system-picture surfaces.

### Phase 3 - Guard Promotion And Learning Closure

- [ ] Route repeated, confirmed, or observer-detected issues through
      `governance-review --record` and the `GuardPromotionCandidate` queue by
      default.
- [ ] Make monitor self-audit reasons and repeated phase failures eligible
      inputs for the same promotion path rather than separate operator notes.
- [ ] Thread prior adjudication, queue state, and relevant guidance into the
      next-slice prompt so the loop learns from typed evidence, not memory.
- [ ] Keep guard/probe promotion approval-bound; loop v2 may recommend and
      queue promotions, but not silently harden the blocking guard set.
- [ ] Route approved external research and recurring architecture patterns
      through `ResearchEvidenceBundle` -> `KnowledgeSynthesisRecord` ->
      `GuardPromotionCandidate` / `PlanRow` / `ContextGraphSeed` /
      `PointerRefIndexEntry`, with source URL or repo ref, retrieval time,
      confidence, claim summary, and affected contract/plan ref recorded before
      promotion.

### Phase 4 - Governed Proof

- [ ] Run a read-only loop-v2 dry run that proves slice selection and phase
      routing over current repo state without edits.
- [ ] Run one bounded governed implementation slice through the existing
      commit/push pipeline with the loop deriving the next step from typed
      state at each phase boundary.
- [ ] Record the residual blind spots as plan-visible debt or guard/probe
      follow-up before widening the loop.

## Progress Log

- 2026-05-01: Added the typed `/develop` topology contract in
  `dev/scripts/devctl/runtime/development_team.py`. The default topology is
  provider-neutral and names the user-facing workstreams above, including a
  Plan Intake Steward for durable packet-to-plan/state ingestion. It adds
  explicit external-research and knowledge-flow contracts so web/vendor/library
  research is route-granted and cited, while packet-carried and synthesized
  knowledge feeds canonical plan/finding/guard/contract sinks and then
  generated context-graph/system-map/ConceptIndex/ZGraph-compatible/pointer/
  startup projections. Graph and pointer outputs remain navigation/projection
  surfaces, not authority stores.
- 2026-05-01: Added `DevelopmentScalingContract` to that topology so packet
  backlog, near-TTL intent, review/probe pressure, graph/system-map gaps,
  independent next slices, stale runtime windows, and safe-fanout evidence
  compile into named modes rather than ambiguous worker counts. The modes are
  Controller Only, Intake Fanout, Review Fanout, Research Fanout, Watcher
  Fanout, Isolated Builder Fanout, and Leased Live-Tree Builder; every extra
  lane needs a `WorkerPacket` and durable evidence path, and live-tree writes
  still require one session-bound `MutationLease`.
- 2026-05-01: Claude beta testing found the executable `/develop` gap after
  the typed contracts landed. Added `devctl develop` as a read-only command
  that renders `DevelopmentLoopReport` for `status`, `next`, `pause`,
  `resume`, `audit-guards`, and `launch --max-cycles 1` previews, plus the
  thin `.claude/commands/develop.md` adapter. Launch remains a report-only
  cycle until the typed controller-state writer and worker spawn path land.
- 2026-05-01: Added `PacketCreationBinding` as the creation-time durability
  receipt for plan-scoped packet kinds. `post_packet` finalization now upserts
  a `PlanRow` before packet TTL can erase durable intent, records a binding
  event into the review-channel reducer, and suppresses carry-forward debt for
  packets that later expire after a durable binding. Live Claude dashboard
  packet `rev_pkt_2710` auto-created `PKT-BIND-REV-PKT-2710`; prior packet
  `rev_pkt_2708` was backfilled through the same typed helper. The remaining
  Phase 1 work is a `PacketDebtRemediationReport` pipeline that clusters old
  carry-forward rows and produces typed merge/dismiss/archive/operator-review
  receipts.
- 2026-04-10: Bootstrapped the repo with `startup-context --format summary`
  and `context-graph --mode bootstrap --format md`, then verified live repo
  state with `git status --short`. The worktree is currently clean, so older
  handoff notes about nine dirty files are no longer authoritative.
- 2026-04-10: Read the current architectural review at
  `dev/audits/reviews/q40_q67_codex_review_2026-04-10.md`. Accepted its main
  loop-v2 premise as execution state: reuse `StartupContext`,
  `WorkIntakePacket`, `AutoModeState`, `findings-priority`, `MonitorSnapshot`,
  and governed commit/push instead of building a verdict-file controller.
- 2026-04-10: Exercised the live read-only surfaces as if the loop were a
  fresh AI session. `auto-mode` reports `reviewing`, `monitor` reports
  `blocked` plus self-audit reasons
  `coordination_resync_required, remote_control_publisher_missing`, and
  `review-channel status` shows `single_agent`, no live participants, stale
  instruction content, and `resync_required=true`.
- 2026-04-10: Confirmed the current observability/value split: typed runtime
  state exists and is rich, but the controller path is still open. The same
  session showed `findings-priority` ranking the right issue families while
  failing to ground most of them to source files, which blocks precise
  autonomous slice selection.
- 2026-04-10: Verified that graph-backed discoverability is currently
  file-path-centric. Abstract `context-graph` queries for
  `AutoModeState`, `GuardPromotionCandidate`, and related contract names
  returned no matches, while a concrete file-path query for
  `dev/scripts/devctl/runtime/startup_context.py` returned the expected
  neighbors and owner-plan edge.
- 2026-04-10: Verified `system-picture` and `platform-contracts` as useful
  reducer surfaces for loop v2. `system-picture` currently flags a stale graph
  snapshot and shows `plan_count=0` in that saved graph artifact, which is an
  important visibility gap to close before the loop trusts graph-derived plan
  routing.
- 2026-04-11: Landed the first bounded Q78 follow-up inside
  `dev/scripts/devctl/context_graph/`: the graph now indexes typed-contract
  and dataclass-field nodes from repo-owned runtime/platform/governance
  dataclasses, `context-graph --query 'AutoModeState GuardPromotionCandidate
  SessionPacingState PlanningIRSnapshot'` returns the four requested contract
  nodes with `confidence: high`, and `context-graph --query
  'research_ref_budget'` resolves the field back to `SessionPacingState`.
  This closes symbol-level discoverability without adding a new authority
  store, but it does not yet add consumer/gates-on edges.
- 2026-04-11: Re-ran `findings-priority` after the graph-discoverability
  slice. The ranking surface still reports the highest-ranked LIVE_RUN rows
  with `(no source-file match)` and `fan_out=0`, so the next Phase 0 slice is
  still grounding, not controller logic: use Q77 stranded consumers and/or
  contract-consumer edges so typed priority can point at concrete files.
- 2026-04-12: Reprioritized loop-v2 after the dashboard architecture review
  and packet synthesis. Discoverability improved, but the real Phase 0 gate is
  now broader and explicit: one `FindingBacklog`, one reducer-backed
  visibility stack across startup/status/dashboard/monitor/mobile/phone, one
  shared packet lifecycle/event wake contract, and one live tool-call
  projection for observer lanes. `devctl develop` stays Phase 2 work and
  remains blocked until those inputs are consumed.

## Session Resume

- Current status: the bounded loop-v2 convergence design is now registered as
  an active `MP-377` execution spec. The first Phase 0 discoverability slice
  is now landed: abstract contract and field queries resolve through the
  existing `context-graph` surface instead of returning `no_match`.
- Next action: stay in Phase 0 and finish consumer wiring before any
  controller widening. `findings-priority` still returns ungrounded top rows,
  the status surfaces still split blocker vocabulary, and packet wake is still
  partially timer-driven, so the next bounded order is:
  `FindingBacklog -> four-surface convergence -> packet lifecycle/event wake -> stranded-consumer grounding`.
  Do not widen into `devctl develop`, rollout-tail prompt derivation, or
  broader autonomy work yet.
- Context rule: on the next session, load `dev/active/ai_governance_platform.md`,
  `dev/active/platform_authority_loop.md`, this file, and the 2026-04-10
  Codex review, then rerun `startup-context`, `review-channel status`,
  `monitor`, `auto-mode`, `findings-priority`, and `system-picture` before
  editing code.

## Audit Evidence

- `python3 dev/scripts/devctl.py startup-context --format summary`
  - `blockers=coordination_resync_required,implementation_permission_blocked`
  - `session_pacing=deep/10refs/3files/72deps`
- `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`
  - graph built successfully; active-plan registry present in the bootstrap
    packet
- `python3 dev/scripts/devctl.py auto-mode --format md`
  - phase=`reviewing`
  - next transition=`HEAD moved past last reviewed commit; review the new commits`
- `python3 dev/scripts/devctl.py monitor --format md`
  - state=`blocked`
  - self-audit reasons=`coordination_resync_required, remote_control_publisher_missing`
- `python3 dev/scripts/devctl.py findings-priority --format md`
  - 20 ranked findings rendered
  - most top findings still showed `(no source-file match)` and `fan_out=0`
- `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
  - `reviewer_mode=single_agent`
  - `resync_required=true`
  - planned lanes remain visible while live participants are `0`
- `python3 dev/scripts/devctl.py platform-contracts --format md`
  - 23 shared contracts and 5 frontend surfaces rendered from the current
    platform blueprint
- `python3 dev/scripts/devctl.py system-picture --format md`
  - context graph section stale
  - saved graph snapshot summary reported `plan_count=0`
- `python3 dev/scripts/devctl.py context-graph --query 'AutoModeState GuardPromotionCandidate' --format md`
  - now returns typed-contract nodes for `AutoModeState` and
    `GuardPromotionCandidate`
- `python3 dev/scripts/devctl.py context-graph --query 'AutoModeState GuardPromotionCandidate SessionPacingState PlanningIRSnapshot' --format md`
  - matched 4 direct typed-contract nodes
  - expanded to source-file and dataclass-field neighbors with
    `confidence=high`
- `python3 dev/scripts/devctl.py context-graph --query 'research_ref_budget' --format md`
  - resolved `research_ref_budget` back to `SessionPacingState`
- `python3 dev/scripts/devctl.py context-graph --query 'dev/scripts/devctl/runtime/startup_context.py' --format md`
  - matched node plus runtime/plan neighbors and a `scoped_by` edge to
    `dev/active/ai_governance_platform.md`

## Addendum 2026-04-11 — Synthesis And Self-Improvement Closure

Added after an operator-driven architectural retrospective on the
Q40-Q75 session. The plan above is correct and load-bearing. This
addendum names what's still missing from the loop so that self-improvement
becomes measurable, not aspirational. Every item here must compose over the
existing typed substrate — no new top-level backends, no adjacent stores.

### Operator insight

The 2026-04-11 retrospective named a failure pattern that repeated
across Q65, Q64, Q55, Q42, and Q75: **new typed contracts stop at
projection/reporting and never become load-bearing**. The existing
architectural review at `dev/audits/reviews/q40_q67_codex_review_2026-04-10.md`
documents it in one sentence: "several new contracts stop at
projection/reporting: coordination truth is still split, session pacing
is advisory only, findings priority is unconsumed, and recovery authority
is not yet the executor's source of truth."

That sentence is the most important output of the previous review. But
nothing in the repo captured it as **typed state**. The insight lives as
prose in a reviews markdown file. The next session starts cold and
re-derives the pattern from raw findings. This is the scatter bug at the
meta level: synthesis is lost between sessions the same way scatter loses
integration between contracts.

Self-improvement is the same problem looked at from the other direction.
A codebase self-improves when the next cycle is measurably better than
the last because something learned in the last cycle is wired into the
next one. Scatter = learning doesn't persist. Self-improvement = learning
becomes typed state, becomes a guard/probe, becomes a prompt input for
the next session, becomes measurable via `context-graph --mode diff`.

### Design questions the loop must answer

Each answer must name the existing contract or command it extends.
Creating a new top-level contract is only allowed when no existing one
covers 80% of the need. Every new contract must name its consumer before
it ships. If the consumer isn't named, the contract is deferred.

1. **`PatternObservation` contract.** A typed record that captures a
   cross-finding root-cause pattern. Candidate home: extend
   `governance-review --record` to accept `signal_type=pattern` the same
   way it already accepts `observer/guard/probe`. Fields beyond
   `FindingReview`: `pattern_id`, `observed_across_findings: tuple[str, ...]`
   (e.g. `(Q65, Q64, Q55, Q42)`), `pattern_statement: str`,
   `proposed_guard_id: str | None`, `proposed_probe_id: str | None`.
   Consumer: the next-session prompt-derivation step in Phase 1.
   Storage: reuse `dev/reports/governance/finding_reviews.jsonl` rather
   than a new ledger.

2. **Findings-priority cluster mode.** Extend
   `dev/scripts/devctl/commands/reporting/findings_priority.py` so its
   output can group findings into clusters by shared root cause. Input:
   existing severity ordering plus `context-graph` edges plus any open
   `PatternObservation` records. Output: clusters become the unit
   assigned to a session, not individual findings. Consumer: Phase 1
   slice selector.

3. **`GuardPromotionCandidate` activation.** The contract exists in
   `dev/active/ai_governance_platform.md`. Nothing currently uses it.
   Required change: every implementer session's completion contract
   must include "for each finding class you fixed, also emit a
   `GuardPromotionCandidate` record through `governance-review --record`
   or document why promotion is not applicable." The session is not
   done until both the fix and the promotion record land. No new
   storage — this lands in the same `finding_reviews.jsonl`.

4. **`rollout-tail` insight extraction.** The Codex session rollout
   JSONL at `~/.codex/sessions/**/rollout-*.jsonl` already contains
   thinking messages that are often more architecturally useful than
   the verdict file. Proof: the 2026-04-10 reviewer's verdict file said
   "I wrote the verdict" (2 lines) while its thinking messages contained
   "the plan already has a `FindingReview -> GuardPromotionCandidate`
   concept" and "latent capability vs operational behavior" — the actual
   insights. Required change: extend `devctl rollout-tail` (already
   scoped as a cheap MVP in the rollout JSONL integration memory) to
   project thinking messages into typed `PatternObservation` or
   `FindingReview` candidates. Consumer: Phase 3 guard promotion input.

5. **Next-session prompt derivation.** Loop v2's next-session prompt
   must come from `findings-priority` cluster output + most recent
   `PatternObservation` records + pending `GuardPromotionCandidate`
   records + `WorkIntakePacket.active_target` + `SessionPacingState`.
   It must not be operator prose. Candidate surface: a new `devctl
   next-session-prompt` command, or extend `autonomy-run` to emit the
   prompt text as a typed field on its cycle report. Consumer: the
   provider-adapter layer that actually launches the implementer (Codex
   exec, Claude Code, future providers).

### Measurement — making "better" provable

`context-graph --mode diff --from previous --to latest` already computes
deltas across saved graph snapshots. Extend it with one additional diff
family: the count of `PatternObservation` records with status
`unconsumed` vs `addressed`. The claim "this cycle is better than last
cycle" must be backed by: fewer unconsumed patterns, fewer repeated
findings of the same pattern class, and at least one new
`GuardPromotionCandidate` that landed as a real guard in the period.

If that metric cannot be produced, the loop did not improve.

### Prevention — don't repeat the emitted-but-not-consumed trap

For each addendum item above, the consumer must be wired before the
producer ships. This is the same discipline the main plan already
captured under "Locked Decisions" #1 and #4. Violating it would turn
synthesis into another Q74-style half-built contract. Concrete rule:
`PatternObservation` records are only allowed to land after the
findings-priority cluster mode reads them. `rollout-tail` insight
extraction is only allowed to land after the next-session prompt
derivation consumes them. `GuardPromotionCandidate` activation is only
allowed after `governance-review --record` gains the session-completion
check that enforces it.

### Loop-V2 Proof Sequence (renamed to avoid LIVE_RUN Q-ID collisions)

Use `LIVE_RUN Q76-Q80` as the evidence namespace and the `LV2-*` labels below
as the implementation sequence inside this plan.

LV2-1: `findings-priority` cluster mode — the first consumer. Before this
lands, there is no downstream slot for `PatternObservation`.

LV2-2: `PatternObservation` contract (extension of `signal_type` enum and
`FindingReview` schema) — lands only after `LV2-1` gives it a reader.

LV2-3: `governance-review --record` session-completion check for
`GuardPromotionCandidate` — the forcing function that makes guard promotion
mandatory on every implementer session.

LV2-4: `devctl rollout-tail --extract-insights` — projects Codex thinking
messages into typed records. Lands after `LV2-2` gives them a home.

LV2-5: next-session prompt derivation as a typed pipeline — composes
`LV2-1` + `LV2-2` + `LV2-3` + `LV2-4` into the loop-v2
`next_session_prompt` typed field that the provider-adapter layer consumes.

LV2-6 (optional): `context-graph --mode diff` extension for pattern
convergence metric. Validates the claim that the loop is improving.
Gated behind `LV2-1` through `LV2-5` so there's real data to measure.

### Honest risks

1. **Synthesis overhead.** If every session has to produce
   `PatternObservation` + `GuardPromotionCandidate` + cluster-aware
   output on top of fixing code, session throughput drops. Mitigation:
   keep the session-completion check minimal — one `GuardPromotionCandidate`
   per finding class, not per finding. One `PatternObservation` per
   session only when the session observed a cross-finding pattern, not
   every time.

2. **Cluster quality.** Bad clusters are worse than no clusters. If
   `findings-priority` groups unrelated findings because of weak graph
   data, the loop wastes sessions chasing false patterns. Mitigation:
   require a minimum confidence threshold on cluster edges, and let
   the operator split clusters via `governance-review --record` with a
   split verdict.

3. **Prompt derivation stickiness.** If the derived prompt is wrong
   once, there must be a repo-owned escape hatch. Mitigation: allow
   operator to emit a typed override record (not operator prose in the
   prompt itself) that becomes an input to the next derivation step.
   The override is typed, it's auditable, it's not prose drift.

4. **Measurement gaming.** If "better this cycle" means fewer patterns
   with status `unconsumed`, the loop can cheat by marking patterns
   addressed without shipping real prevention. Mitigation: tie the
   metric to `GuardPromotionCandidate` records that successfully became
   guards in the same period, not to self-reported status transitions.

### Wiring order for the first proof

1. Land Q76 cluster mode in `findings-priority` — one consumer exists.
2. Land Q77 `PatternObservation` extension — first producer fills the
   slot Q76 made.
3. Run one implementer session with Q78 session-completion check active.
4. Observe that `GuardPromotionCandidate` records actually land and that
   at least one becomes a real guard.
5. Only then land Q79 rollout-tail projection and Q80 prompt derivation.

This is the minimal proof that the synthesis-and-self-improvement chain
is load-bearing. If any step in this order produces an emitted-but-not-
consumed contract, stop the sequence and reopen the design. The whole
point is that the trap we documented in Q70-Q75 does not recur at the
meta layer.
