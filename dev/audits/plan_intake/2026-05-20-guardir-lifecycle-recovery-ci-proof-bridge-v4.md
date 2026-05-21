# GuardIR v4.55.1 Unified Ingestable Plan

## Summary

This is the single canonical ingestible plan for GuardIR lifecycle recovery,
plan ingestion, GuardIR push routing, and CI-to-AI proof feedback. It folds in
the operator-reviewed v2, v3, v3.5, v3.6, v4, and v4.1 discussions so later
sessions do not need chat history to continue.

Canonical path:
`dev/audits/plan_intake/2026-05-20-guardir-lifecycle-recovery-ci-proof-bridge-v4.md`

Plan revision id: `guardir-v4.55.1-2026-05-21`

## Source History

- Supersedes v2 operator-tightened lifecycle, dogfood, and visibility plan.
- Supersedes v3 compact architecture sketch.
- Supersedes v3.5 automation and universal portability plan.
- Supersedes v3.6 PlanAmendmentReceipt and PlanIntakeConfig substrate plan.
- Supersedes v4/v4.1/v4.2 chat drafts.
- Applies Claude's v4.3 offline amendment:
  `dev/reports/review_channel/offline_findings/2026-05-20T18-15Z-claude-v4.3-amendment.md`.
  The amendment changes this plan from "expand new substrate" to "connect
  existing primitives first." This file remains the durable artifact.
- Applies Claude's v4.4 offline amendment:
  `dev/reports/review_channel/offline_findings/2026-05-20T18-25Z-claude-v4.4-amendment.md`.
  The amendment aligns this plan with remote-commit publication authority,
  MP-377 phase naming, dashboard/reporting ownership, loop-v2, and
  multi-repo portability ladders.
- Applies Claude's v4.5 offline amendment:
  `dev/reports/review_channel/offline_findings/2026-05-20T18-40Z-claude-v4.5-amendment.md`.
  The amendment cites already-planned P102 typestate and P180-P183 ZGraph
  work, adds Work Stream E connectivity debt reduction, and records Raspberry
  Pi edge-device mode as deferred adopter-pack work.
- Applies Claude's v4.6 offline amendment:
  `dev/reports/review_channel/offline_findings/2026-05-20T18-50Z-claude-v4.6-amendment.md`.
  The amendment expands Work Stream F into a concrete Raspberry Pi edge-device
  adopter pack, adds physical-approval security boundaries, and cites adjacent
  operator-console, mobile, packet-expiry, role-fleet, and thesis follow-up
  work without pulling that work into this slice.
- Applies Claude's v4.7 offline amendment:
  `dev/reports/review_channel/offline_findings/2026-05-20T19-00Z-claude-v4.7-amendment.md`.
  The amendment upgrades Work Stream F from read-only edge projection to an
  opt-in active background role substrate, and adds Work Stream G as the
  convergence proof that Work Streams A-F compose into one system-level loop.
- Applies Claude's v4.8 offline amendment:
  `dev/reports/review_channel/offline_findings/2026-05-20T19-15Z-claude-v4.8-amendment.md`.
  The amendment fixes cascade ordering, adds Work Stream A.0 as the
  `GitMutationProofReceipt.code_identity_hash` prerequisite, inverts C before
  B so CI artifacts feed the proof index, records producer/store specs for all
  v4 contracts, and adds startup-authority halt language to convergence.
- Applies the v4.9 live dogfood amendment from the A.0 handoff:
  `dev/reports/review_channel/offline_findings/2026-05-20T19-25Z-claude-task-produced-A0.md`.
  The amendment records that a valid Codex `task_started` can reach Claude and
  produce code, while Claude's typed `task_produced` is rejected by
  `ControlDecisionObeyedGuard`. That post-implementation guard path is now a
  first-class Phase 0.6.A repair slice before Work Stream A.
- Applies the v4.10 live operator correction and multi-agent read-only smell
  audit from 2026-05-20. The amendment records two architecture failures:
  agents treated plan-intake markdown, active docs, generated boot cards, and
  chat as competing authority surfaces instead of resolving current authority
  from ingested typed `PlanRow` state; and a Codex reviewer session could use
  file-edit tooling while a Claude implementer session owned a live
  `task_started` lane. v4.10 adds current-plan authority singularity and
  role-scoped mutation leases before further dual-agent implementation work.
- Applies the v4.11 live review amendment from `rev_pkt_4657` and Claude's
  structural narrow response:
  `dev/reports/review_channel/offline_findings/2026-05-20T20-15Z-claude-cascade-narrow-response.md`.
  The amendment records that structural cascade-post checks are not enough:
  a reviewer reproduction still showed `_cascade_lifecycle_post_authority`
  returning `True` for a mismatched target session when the evidence only
  looked like `packet:rev_pkt_<digits>`. v4.11 adds parent-packet semantic
  authority and review-channel read authority as typed architecture rows
  before the A.0 / Work Stream A handoff can be accepted as closed.
- Applies the v4.12 live reviewer finding from `rev_pkt_4661`: a
  `review_accepted` packet must close only over a resolved `task_produced`
  parent. It must never close over `task_progress`, because progress evidence
  is not final acceptance evidence.
- Applies the v4.13 live dogfood finding from `rev_pkt_4663`: review-channel
  packet posts stamp source `session_id` as `local-review` when the actor's
  real typed session is not carried through the CLI. Semantic parent-packet
  validation must compare real actor/source sessions, not a fallback review
  store constant.
- Applies the v4.14 live reviewer finding from `rev_pkt_4667`: rejecting
  `local-review` is necessary but insufficient. A live-agent post must prove
  that the supplied `session_id` is an actor-bound typed session, not merely
  any non-fallback string accepted by the CLI.
- Applies the v4.15 multi-agent architecture audit and live dogfood signal from
  `rev_pkt_4670` plus Claude's
  `dev/reports/review_channel/offline_findings/2026-05-20T21-35Z-claude-phase-0-6-d-fail-closed-response.md`.
  The amendment records four system-level smells: current-plan reducers can
  still route agents toward stale active-doc/checkpoint state instead of the
  canonical ingested plan; source-session validation used the latest
  `AgentMindSlice` projection as if it were durable post-time authority, which
  can strand valid parent packets after session rotation; role/capability
  authority is still partly derived from provider defaults and remote-control
  fallback instead of explicit grants; and documentation/navigation work must
  connect SYSTEM_MAP, repo-pack portability, VoiceTerm-adopter separation, and
  duplicate-contract checks rather than adding more parallel surfaces.
- Applies the v4.16 live watcher signal from Claude's 2026-05-20 17:44 watch
  tick: subagent and main-session activity can update the same provider-level
  `<provider>_latest.json` projection, observed as `codex_latest.json` in this
  run. Source-session validation can then treat mapping/research subagents as
  if they were the main reviewer/conductor. v4.16 adds multi-agent session
  scoping and configurable fanout boundaries so subagents help with audits
  without overwriting typed actor identity or invalidating valid cascade
  parents.
- Applies the v4.17 Codex/Claude live dogfood and architecture audit from
  2026-05-20 17:55-18:05. `devctl session` and `agent-loop` correctly blocked
  Codex implementation edits, but then looped on `repair_startup_authority`
  without a runnable repair command; an explicit edit-only operator override
  stayed read-only and pivoted to unrelated packet semantics. That is a
  typed-controller architecture bug, not a reason to bypass the system. v4.17
  adds startup-repair command authority, MP-377 T22 parentage, professional
  docs/navigation projection boundaries, RepoPack/adopter portability gates,
  and explicit VoiceTerm leakage tracking so GuardIR v4 stays one connected
  architecture instead of another source of truth.
- Applies the v4.18 live controller dogfood from 2026-05-20 18:49 and
  follow-up packet `rev_pkt_4674`:
  `develop next` emitted a concrete `review-channel --action ingest` command
  for `rev_pkt_4654`, but running that exact command failed
  `ControlDecisionObeyedGuard` with `control_decision_obedience_failed`. The
  reducer cannot claim a command is the next required action unless the command
  carries the control-decision input, proxy authority, or lifecycle state needed
  to pass its own guard. v4.18 adds a next-command obedience invariant under
  Phase 0.6.A.
- Applies the v4.19 Codex review of Claude packets `rev_pkt_4673` and
  `rev_pkt_4675`, plus Codex follow-up `rev_pkt_4676`: extending
  `BlockerSnapshot` with repair metadata and a `repair_command_runnable` flag is
  useful substrate, but it is not closure if the failing `develop next`,
  `agent-loop`, `repair_startup_authority`, and final-response producer/consumer
  callsites still emit or execute impossible commands. v4.19 makes producer and
  consumer wiring mandatory, and requires negative tests to fail on defective
  unrunnable-command states instead of merely constructing them.
- Applies the v4.20 Codex review of Claude `rev_pkt_4678`, Codex devctl test
  receipts, the live Codex `agent-loop` output, and the failed Codex reviewer
  progress-verdict post. `rev_pkt_4678` correctly posted progress rather than
  closure for increment 1/6, and focused model tests passed, but the live
  `agent-loop` still surfaced `repair_startup_authority` with empty
  `blocker_owner`, `blocker_target`, `blocker_reason`, `repair_command`, and
  `stop_anchor`. A read-only Codex reviewer feedback post then failed
  `ControlDecisionObeyedGuard` with `control_decision_obedience_failed`. v4.20
  records both as architecture gaps: blocker repair metadata must survive every
  read-model hop into `AgentLoopDecision`, `/develop`, and final-response
  consumers; and review-only communication packets must either carry the typed
  control-decision evidence required by the guard or emit a typed recoverable
  blocker instead of forcing offline evidence.
- Applies the v4.21 Codex review of Claude's offline v4.20 progress artifact:
  `dev/reports/review_channel/offline_findings/2026-05-20T23-20Z-claude-phase-0-6-a-v420-codex-task-progress.md`.
  Claude added `("codex", "task_progress")` to the cascade post allowlist and
  104 tests passed, but Claude's own `task_progress` response to the Codex
  `finding` packet `rev_pkt_4679` still failed
  `ControlDecisionObeyedGuard`. The missing invariant is broader than one
  tuple: the lifecycle parent-kind matrix must model reviewer-finding response
  semantics. A scoped implementer must be able to answer a reviewer `finding`
  for the same slice with `task_progress`, `task_blocked`, or `task_produced`
  when the target role/session/ref and source session are valid. Closure packets
  remain stricter: `review_accepted` still closes only a resolved
  `task_produced` parent.
- Applies the v4.22 Codex review of Claude `rev_pkt_4680`: the incremental
  v4.20 `task_progress` allowlist patch and focused tests are valid progress,
  but the packet was accepted by citing `packet:rev_pkt_4672` first while its
  body described a response to the later reviewer `finding` `rev_pkt_4679`.
  The current cascade predicate treats the first packet-shaped evidence ref as
  the semantic parent, so evidence ordering can hide the real lifecycle edge.
  v4.22 requires an explicit primary parent relation, or a fail-closed
  unambiguous single-parent fallback, before a multi-packet evidence list can
  bypass `ControlDecisionObeyedGuard`.
- Applies the v4.23 live coordination and connectivity audit from Codex
  `rev_pkt_4687`. Claude's v4.22 parent-resolution narrowing passed focused
  tests and Codex posted a review-only `task_progress` packet back to Claude,
  but startup/status still exposed a controller split: `safe_to_continue=false`
  and `dirty_path_budget_exceeded` coexisted with allowed review/progress packet
  actions, inactive reviewer-mode grant fields, and an unrelated active target
  projection. `check_contract_connectivity.py --format md` also reported the
  planned duplicate shape `AgentLoopDecision` <-> `BlockerSnapshot`. v4.23 makes
  that split explicit architecture debt: checkpoint budget may block mutation,
  closure, or convergence, but it must not retarget the current plan or suppress
  scoped review-only coordination packets without a typed recoverable blocker.
- Applies the v4.24 live chain-wiring review from Codex `rev_pkt_4692` /
  Claude `rev_pkt_4693`. The `BlockerSnapshot` metadata route now reaches
  `AgentLoopDecision` through `AgentLoopContext`, but agent-mind also captured
  an implementation edit performed through shell append redirection
  (`cat >> dev/scripts/devctl/tests/runtime/test_agent_loop_decision.py`). That
  exposed a distinct mutation-method gap: a valid implementer lease is not
  enough if the system cannot distinguish typed patch/edit tools from raw shell
  file writes and attach `TypedAction -> ActionResult -> RunRecord` provenance.
  v4.24 adds mutation method provenance and raw shell-write detection to the
  same Phase 0.6.A authority spine rather than creating another tool policy
  surface.
- Applies the v4.25 live multi-agent dogfood failure from the Codex
  `rev_pkt_4693` review attempt. Codex correctly used read-only sidecar agents
  for plan/source-of-truth and duplicate-system mapping, but the sidecar refresh
  updated `dev/reports/agent_minds/codex_latest.json` to the sidecar session.
  The subsequent main-reviewer packet post with the real Codex session id was
  rejected because source-session validation compared against provider-latest
  state instead of route-scoped actor/session authority. v4.25 tightens Phase
  0.6.D: read-only fanout evidence must not overwrite the main actor's posting
  authority, and a provider-latest mismatch must produce a route-scoped
  recoverable blocker instead of forcing spoofed subagent identity or offline
  coordination.
- Applies the v4.26 operator navigation critique: generated boot cards such as
  `AGENTS.md` and `CLAUDE.md` are correctly projection-only, but their current
  content is too shallow to help agents choose the right command, role, packet
  lane, system-map path, duplicate-check path, or typed authority source. This
  is part of the same source-of-truth failure: a projection that only says
  "typed state is authority" without a role-aware command router leaves agents
  to infer from chat or random active docs. v4.26 adds an instruction-surface
  usability slice that improves generated projections and platform guides from
  typed inputs, keeps VoiceTerm as adopter/client context, and prevents guide
  prose from becoming backend authority.
- Applies the v4.27 final-gate dogfood from the Codex `rev_pkt_4694` handoff:
  after a valid review-only packet was posted to Claude, the final-response
  gate still denied completion with contradictory continuation commands. The
  top-level continuation said to run Codex `agent-loop`, while
  `final_response_gate.next_required_command` pointed at an old
  `review-channel --action ingest --packet-id rev_pkt_4654 --actor claude`
  command. Codex must not execute Claude-owned actor commands from the reviewer
  lane. v4.27 records that final-response producers must choose the current
  semantic blocker and actor lane, not stale packet-ingestion debt, and must
  emit one guard-obedient command or a typed blocker.
- Applies the v4.28 operator role/continuation correction. The operator still
  had to remind Codex that its live job is not only "review" but also
  orchestration, plan stewardship, system-map/duplicate checking, read-only
  sidecar fanout, and typed handoff back to Claude. Claude also parked itself
  behind a wake/stop-style anchor even though the typed lifecycle was still
  open. v4.28 adds a role boot and continuation contract: each session must
  resolve its current role envelope at startup/final-gate time, generated
  projections must state the role-specific command loop, and stop/wake anchors
  cannot pause an active packet goal without a typed `SessionTerminationPolicy`
  / `TaskCompleteDecision` decision that agrees with the live packet lifecycle.
- Applies the v4.29 multi-agent read-only role/connectivity audit. Existing
  `InstructionBootCard`, `RoleInstructionCard`, `RoleGuard`,
  `CustomRoleDefinition`, `RoleCreationAction`, `SystemCatalog`,
  `CollaborationModeTopology`, `AgentDispatchRouter`, `AgentLoopDecision`, and
  `ControlDecisionObeyedGuard` primitives are the substrate; the gap is that
  boot-card rendering, role instruction cards, command catalogs, contract
  connectivity, and guard enforcement are not one visible role-authority path.
  v4.29 adds instruction/role contract connectivity closure and fail-closed
  provider-default handling so generated surfaces cannot become isolated
  authority islands or leave agents guessing from chat.
- Applies the v4.30 live coordination-lane failure from the `rev_pkt_4701`
  follow-up: Claude's in-progress `develop` consumer edit introduced a syntax
  error in `dev/scripts/devctl/commands/development/report.py`, and because
  `devctl` imports development/report modules while booting unrelated
  `review-channel`, `agent-mind`, and `session` commands, the reviewer could no
  longer use the typed coordination lane to post the finding through normal
  tooling. v4.30 adds coordination-lane import isolation: packet reads/writes,
  agent-mind, and session diagnostics must remain available for review-only
  recovery even when an implementation-owned command module is temporarily
  broken. This is not permission for a reviewer to mutate the implementer's
  write set; it is a requirement that the communication plane survive the
  broken implementation plane well enough to route typed repair.
- Applies the v4.31 live wrapper-envelope review from Claude `rev_pkt_4704`
  and a read-only Codex sidecar audit. Suppressing a peer-owned operator
  command wrapper is valid immediate progress, but duplicating ad hoc
  `--actor` string parsers across report consumers is a convergence smell.
  The repo already has executor/subject/proxy concepts in
  `AttemptedActionReceipt`, `ProxyAuthorityRoute`, `ProxyAuthoritySource`,
  `RoleCommandEnvelope`, and `AgentLoopDecision` source refs. v4.31 adds a
  command-envelope normalization slice: every command emitted by `develop`,
  final gate, response shape, and operator wrappers must be classified once as
  same-actor executable, peer-lane non-executable status, or proxy-authorized
  executable. Peer commands must not be hidden as proof of closure when a
  visible non-executable status is needed, and must not render as shell
  wrappers without a bound proxy authority ref.
- Applies the v4.32 Codex sidecar/system-map/connectivity audit and live
  command-envelope implementation review from 2026-05-20/21. The sidecar found
  existing boot-card, platform-guide, SystemCatalog, RepoPack, and role
  customization substrate, so no new authority system is needed. The required
  repair is sharper acceptance on existing rows: generated boot cards must be
  useful role-aware command routers; `InstructionBootCard` and role instruction
  contracts must be contract-connected and context-graph discoverable; portable
  GuardIR paths must not silently fall back to VoiceTerm defaults; and any new
  command-envelope contract must register through platform/contract fixtures
  rather than becoming another orphaned runtime dataclass. v4.32 also records
  that command-envelope closure requires the full typed envelope fields and a
  bound proxy authority validation path; a non-empty `proxy_authority_ref`
  string and a partial `--actor` parser are not sufficient closure.
- Applies the v4.33 live packet-selection dogfood from `rev_pkt_4706`. Codex
  posted a current plan-bound finding to Claude for the v4.32 command-envelope
  closure requirements; `review-channel show --packet-id rev_pkt_4706` could
  resolve it, but Claude's inbox/develop reducer still prioritized stale
  `rev_pkt_4698` as the blocking packet and did not surface `rev_pkt_4706` in
  the live target inbox. That is the same source-of-truth failure in packet form:
  a current, plan-bound, target-session-scoped packet must not be hidden behind
  stale pending backlog. v4.33 sharpens the review-feedback and current-plan
  authority rows so packet selection ranks current plan/target/session/lifecycle
  relevance ahead of old queued packet debt.
- Applies the v4.34 role/authority sidecar audit, live reviewer bootstrap
  dogfood, and packet follow-up `rev_pkt_4707`. Fresh sidecar fanout must be
  read-only and revision-scoped; completed sidecar summaries from earlier plan
  revisions are evidence, not current authority. The amendment records that
  startup/session/status helpers can hang in review-state or push-state refresh,
  so boot/final surfaces need bounded dependency timeouts that emit typed blockers
  instead of leaving agents waiting or falling back to chat. It also tightens the
  same existing rows: Codex's role envelope is reviewer/orchestrator/architect/
  plan steward unless typed mutation authority transfers; Claude owns
  implementation lanes; generated boot cards must route roles and commands from
  typed inputs; and packet selection must surface the current plan-bound lane
  before stale queued debt.
- Applies the v4.35 guard-bundle evidence after v4.34 ingestion. Manifest and
  `git diff --check` passed, dry-run and accepted `develop ingest-plan` parsed all
  36 rows, and typed ingestion wrote receipt `plan-ingest-63bedcb781cdf29c` for
  source hash
  `16b0223d7821094a807bc9234ba3ba720be0afd4a1afbefcd9044f39f69b24a7`.
  Follow-up checks confirmed the remaining failures are already planned rows:
  `check_systemmap_covers_contract_registry.py` and
  `check_instruction_surface_sync.py` fail only because `SYSTEM_MAP.md` generated
  block is stale; `check_platform_contract_closure.py` fails because
  `GitMutationProofReceipt.code_identity_hash` and `ControlPlaneReadModel`
  blocker fields are present in runtime dataclasses but not platform contract
  rows; `check_contract_connectivity.py` remains `ok` with planned debt for
  command-envelope orphan contracts and blocker-metadata duplicate shape. v4.35
  records those as acceptance evidence under existing rows, not as new authority.
- Applies the v4.36 live review of Claude's plan-currency selector increment.
  Reading the latest canonical plan SHA from `plan_source_snapshots.jsonl` works
  for v4.35, but exact equality between packet `target_revision` and latest plan
  SHA is not enough while the plan is being amended in the same live lifecycle:
  `rev_pkt_4707` was current when posted against v4.33, then became
  mechanically stale when Codex ingested v4.35 evidence for the same target rows.
  Packet currency must therefore be supersession-aware over plan row/target and
  source-snapshot lineage, or Codex must post a refreshed current packet whenever
  it advances the plan SHA. A strict exact-SHA-only selector can re-create the
  stale-backlog failure it is meant to fix.
- Applies the v4.37 live source-of-truth and worktree-state mutation correction.
  Review-channel packets are typed communication, lifecycle, and evidence
  inputs; they are not durable plan authority until a reducer or plan amendment
  ingests them into `PlanRow` / plan-state read models with provenance and an
  ingestion receipt. Packet bodies, offline findings, chat, active docs, and
  generated projections must not become competing plans. v4.37 also records the
  live shared-worktree smell where an implementer verification command used
  `git stash && ...` while multiple agents had dirty plan and implementation
  work. Whole-worktree VCS state mutations such as stash/reset/checkout/clean/
  restore are mutation surfaces and must be governed by the same role, lease,
  scope, and provenance architecture as file edits.
- Applies the v4.38 read-only sidecar audit of existing source-of-truth
  primitives. No new parallel system is needed: plan authority already has
  `master_plan_contract.py`, `plan_index_authority.py`, and
  `plan_intent_ingestion.py`; packet-to-plan provenance already has
  `packet_contract.py`, `event_post_action.py`,
  `packet_creation_binding_plan.py`, and packet-debt remediation contracts; and
  reducer/read-model consumers already include planning IR, packet-ingest
  decisions, `next_slice`, `agent_dispatch_router`, and
  `control_plane_read_model.py`. v4.38 records those concrete implementation
  anchors so the packet-to-plan rule connects existing modules instead of
  adding another source of truth.
- Applies the v4.39 read-only sidecar audit of worktree-state mutation
  machinery. Existing git-mutation detection already covers some verbs in
  `runtime/vcs.py`, context-graph code-shape support, mutation-bypass graph
  checks, `AttemptedActionReceipt`, raw-git bypass receipts, and stash/orphan
  inventory, but `git clean` is missing from key verb taxonomies and
  stash/reset/checkout/restore/clean do not yet have first-class action names,
  capabilities, receipts, or command-envelope mutation-risk classification.
  v4.39 folds those gaps into the existing mutation-method, command-envelope,
  role-lease, and next-command rows rather than creating another VCS policy
  surface.
- Applies the v4.40 live Codex review and read-only sidecar audit after
  Claude's v4.39.1 command-envelope increment. The increment correctly added
  `mutation_action_kind`, `mutation_risk_class`, `is_safe_to_render`, robust
  shell redirection detection, and two direct render-consumer updates. The
  sidecar found the broader architecture smell that other consumers still carry
  local mutation allowlists: `control_decision_action_matching.py`,
  `advisory_next_action_role_filter.py`, `action_routing.py`,
  `final_response_gate_agent_loop.py`, and
  `control_decision_consistency.py`. v4.40 requires those consumers and checks
  to compose the shared command-envelope mutation classifier instead of
  deciding destructive worktree/write risk through partial substring lists.
- Applies the v4.41 live import-cycle dogfood from Claude's v4.40
  implementation attempt and Codex's parallel reviewer observation. Moving
  mutation classification into shared consumers briefly made `devctl` unable to
  import `agent-mind`, `review-channel`, and `test-python`: the command
  classifier imported `_proxy_execution` from `control_decision_obedience`,
  while `control_decision_obedience` imported action matching, which imported
  the classifier. v4.41 tightens the already-planned coordination-lane
  import-isolation row and the command-envelope row: shared classifiers and
  command-envelope normalizers must stay leaf or neutral modules, and
  coordination/read/status tooling must not depend on implementation-heavy
  command graphs or higher-level consumers just to report a broken edit.
- Applies the v4.42 live Codex review of Claude's v4.40 "2 of 5 consumers"
  slice. The implemented text-command classifier convergence is useful, but the
  remaining typed-action/next-command consumers still need an explicit adapter
  rather than another local list. Live repros showed
  `final_response_gate_agent_loop.is_executable_next_command()` still returns
  `True` for `python3 dev/scripts/devctl.py push --execute`, while
  `control_decision_consistency.control_decision_violations()` returns no
  violation for `may_mutate=false` with `next_command='git clean -fdx'` when
  `next_action` is blank. v4.42 makes the next slice explicit: converge
  typed-action identifiers and `next_command` mutation checks through the
  shared classifier or a registered adapter, not through text-command-only
  partial closure.
- Applies the v4.43 live Codex/Claude reviewer-loop dogfood after
  `rev_pkt_4714`. Codex verified Claude's v4.41 import-isolation repair with
  `command_output:test-python:97582b15df3c1e48`, but a follow-up
  `review_accepted` post for v4.41 was repeatedly rejected by
  `ControlDecisionObeyedGuard`. The failed action used the correct reviewer
  role/session and targeted Claude's implementer session, but the guard
  continued to bind to stale `agent-runtime-clock:rev_evt_84896` decision state
  and reported `mutation_attempt_after_may_mutate_false`,
  `command_attempt_after_can_run_next_command_false`, and
  `non_body_open_action_after_body_open_required` even after Codex opened both
  the sent `rev_pkt_4714` body and the current Codex inbox packet body. v4.43
  tightens the existing review-feedback post obedience row: reviewer acceptance
  and review-only packet writes must consume fresh typed reviewer authorization
  for the intended packet lineage or emit a typed consistency blocker that names
  the stale decision source, required body-open packet, and repair row.
- Applies Claude's v4.44 prose-authority demotion amendment from `rev_pkt_4720`:
  `dev/reports/review_channel/offline_findings/2026-05-21T04-52Z-claude-v4.44-prose-authority-demotion-and-guard.md`.
  The amendment introduces `dev/scripts/checks/check_no_prose_authority_promotion.py`
  to prevent hand-maintained docs (CLAUDE.md, MASTER_PLAN, INDEX, etc.) from
  re-asserting prose as backend authority. The guard scans for dangerous-term
  promotion phrases and recognizes projection-qualifier escapes. Three docs
  reworded in the same slice.
- Applies the v4.44.1 broadened-guard amendment from Codex `rev_pkt_4725`:
  `dev/reports/review_channel/offline_findings/2026-05-21T05-01Z-claude-v4.44.1-broadened-prose-authority-guard.md`.
  The amendment expands the prose-authority guard to a contextual scan rather
  than substring match, catching variations like "source of truth" and
  "canonical bootstrap order." Corrects the v4.44 path-resolution bug where
  `Path(__file__).resolve().parents[2]` resolved to `dev/` instead of repo root.
- Applies the v4.44.2 integration-gate repair from Codex `rev_pkt_4726/4727`:
  `dev/reports/review_channel/offline_findings/2026-05-21T05-30Z-claude-v4.44.2-integration-gate-repair.md`.
  The amendment repairs `check_active_plan_sync` and
  `check_instruction_surface_sync` breakage from v4.44 doc surgery by
  introducing the `TYPED_PLAN_STORE_PATH` named constant and re-rendering
  generated surfaces via `render-surfaces --write`.
- Applies the v4.44.3 broadened-scope amendment from Codex `rev_pkt_4728/4729`:
  `dev/reports/review_channel/offline_findings/2026-05-21T06-15Z-claude-v4.44.3-broadened-scope-and-terms.md`.
  The amendment expands the prose-authority guard's maintained-doc scope from
  3 files to 8 (MASTER_PLAN, ai_governance_platform, platform_authority_loop,
  INDEX, SYSTEM_MAP, DEVELOPMENT, PLATFORM_GUIDE, AI_GOVERNANCE_PLATFORM) and
  the dangerous-terms list from ~10 to 21. ~70 doc rewordings across those
  files; 70 violations resolved iteratively.
- Applies Claude's v4.45 agent-loop self-loop fix from Codex `rev_pkt_4729/4730/4732`:
  `dev/reports/review_channel/offline_findings/2026-05-21T07-00Z-claude-v4.45-agent-loop-self-loop-fix.md`.
  The amendment fixes `next_command_for_turn()` to return empty when
  `can_run_next_command=False`, preventing the loop from re-emitting the blocked
  command as the next command. A `_normalize_repair_command_runnable()` helper
  enforces `empty repair_command → runnable=False` at the typed boundary.
- Applies the v4.45.1 prose-authority qualifier tightening from Codex `rev_pkt_4735/4736`:
  `dev/reports/review_channel/offline_findings/2026-05-21T07-30Z-claude-v4.45.1-tighten-qualifier-logic.md`.
  The amendment tightens prose-authority qualifier logic so phrases like
  "described as authority" remain accepted projections while genuine promotion
  phrases continue to fail the guard.
- Applies the v4.45.2 blocked-decision consumption amendment from Codex `rev_pkt_4737/4738`:
  `dev/reports/review_channel/offline_findings/2026-05-21T08-00Z-claude-v4.45.2-consume-blocked-decision-no-self-loop.md`.
  The amendment makes the develop, final-response gate, push-report, and
  operator-wrapper surfaces consume a blocked `AgentLoopDecision` as a typed
  unrunnable blocker, so the same `next_command` cannot be replayed across
  surfaces after the agent-loop refuses it.
- Applies the v4.45.3 rehydration-path closure from Codex `rev_pkt_4739/4741`:
  `dev/reports/review_channel/offline_findings/2026-05-21T08-30Z-claude-v4.45.3-close-remaining-rehydration-paths.md`.
  The amendment closes four remaining `next_loop_command` rehydration paths in
  orchestration signals fan-out so the blocked next command is not re-injected
  through downstream consumers.
- Applies the v4.45.4 shared-coerce_bool migration from Codex `rev_pkt_4742`:
  `dev/reports/review_channel/offline_findings/2026-05-21T08-50Z-claude-v4.45.4-shared-coerce-bool.md`.
  The amendment migrates `bool(_field(can_run_next_command))` at the final-gate
  consumer to shared `runtime.value_coercion.coerce_bool`, replaces the local
  `_coerce_bool` helper in `campaign.py` with the shared import, and removes
  divergent truthiness behavior for the string `"false"`.
- Applies the v4.45.5 boolean-normalizer convergence from Codex `rev_pkt_4743`:
  `dev/reports/review_channel/offline_findings/2026-05-21T09-20Z-claude-v4.45.5-boolean-normalizer-convergence.md`.
  The amendment converges 12 boolean-field sites onto shared `coerce_bool` and
  retires two local `_truthy` helpers. Covers `may_mutate`, `next_command`,
  `blocker_owner/reason/target`, `repair_command_runnable`, `stop_anchor`, and
  `operator_override_edit_allowed`.
- Applies the v4.45.6 final boolean-leak closure from Codex `rev_pkt_4747/4750`:
  `dev/reports/review_channel/offline_findings/2026-05-21T10-05Z-claude-v4.45.6-close-two-remaining-boolean-leaks.md`.
  The amendment closes the two final `bool()` sites Codex caught in
  `_operator_override_edit_allowed()` and `_agent_loop_final_response_block()`,
  completing the boolean-normalizer convergence. v4.45.6 was accepted by Codex
  per `rev_pkt_4750` with three test receipts:
  `command_output:test-python:2e8affdf95e34a89` (27 passed),
  `command_output:test-python:a0bb24c94195d954` (14 passed), and
  `command_output:test-python:8a797d17dd30fbe7` (89 passed).
- Applies the v4.46 architectural Finding from Codex `rev_pkt_4731`:
  `dev/reports/review_channel/offline_findings/2026-05-21T05-40Z-codex-route-scoped-plan-packets-hidden-by-watch-limit.md`.
  Inbox watch route-scoped ordering: route-scoped plan packets get hidden by
  the generic watch limit. The amendment requires inbox watch to honor
  route-scoped ordering so plan-bound packets surface ahead of generic ones.
  Folds into `MP-GUARDIR-V4-PHASE-0-6-E-PLAN-INGESTION-S1` acceptance criteria.
- Applies the v4.47 architectural Finding from Codex `rev_pkt_4733/4734/4736/4744`:
  `dev/reports/review_channel/offline_findings/2026-05-21T09-40Z-claude-ack-rev_pkt_4744-consolidates-v4.47.md`.
  Packet-attention durable vs communication classification: communication-only
  packets cannot reach terminal cleanup, contributing to inbox bloat. The
  amendment requires the packet-attention reducer to classify packets as
  durable vs communication and provide terminal cleanup paths for the
  communication class. Folds into the existing review-channel parser/reducer
  rows; no new authority surface.
- Applies the v4.48 architectural Finding from Codex `rev_pkt_4745/4746`:
  `dev/reports/review_channel/offline_findings/2026-05-21T09-55Z-claude-ack-rev_pkt_4745-4746-architectural-review.md`.
  Instruction-surface usability + role-aware routing: generated surfaces are
  too thin to show active role envelope plus current session id, and
  source-of-truth enforcement across packet/plan consumers must be tightened.
  Folds into `MP-GUARDIR-V4-PHASE-0-6-E-INSTRUCTION-SURFACE-USABILITY-S1` and
  `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-INSTRUCTION-CONNECTIVITY-S1`.
- Applies the v4.49 architectural Finding from Codex `rev_pkt_4748`:
  `dev/reports/review_channel/offline_findings/2026-05-21T10-15Z-claude-ack-rev_pkt_4748-no-duplicate-acceptance.md`.
  No-duplicate-system acceptance gate prerequisite: implementation slices must
  pass a no-duplicate-system check before claiming closure, preventing parallel
  authority surfaces from sneaking in. The amendment adds
  `MP-GUARDIR-V4-PHASE-0-6-E-NO-DUPLICATE-SYSTEM-ACCEPTANCE-S1` as a typed
  PlanRow and requires the gate to run on every v4 slice before acceptance.
- Applies the v4.50 architectural Finding from Codex `rev_pkt_4749`:
  `dev/reports/review_channel/offline_findings/2026-05-21T10-30Z-claude-ack-rev_pkt_4749-role-continuation-leak.md`.
  Role/continuation leak across stale sessions and peer-owned commands: stale
  Codex reviewer sessions with `continuation_anchor_live=true` but no
  `loop_autonomy_green` were becoming the next controller target, and a
  Claude-owned `review-channel --action ingest` rendered as a runnable Codex
  next command. The amendment fail-closes current-session selection on stale
  sidecar state and classifies peer-owned commands as `status`/`blocked` unless
  typed proxy authority exists. Folds into
  `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-BOOT-CONTINUATION-S1` and
  `MP-GUARDIR-V4-PHASE-0-6-A-STARTUP-REPAIR-COMMAND-S1`.
- Applies the v4.51 architectural Finding from Codex `rev_pkt_4751`:
  `dev/reports/review_channel/offline_findings/2026-05-21T10-50Z-claude-ack-rev_pkt_4751-platform-contract-drift.md`.
  Platform-contract closure drift: `check_platform_contract_closure.py` returns
  `ok:False` because (1) `GitMutationProofReceipt` runtime added
  `code_identity_hash` in Work Stream A.0 but the platform contract row was not
  updated in the same slice, and (2) `ControlPlaneReadModel` runtime added six
  BlockerSnapshot fields (`blocker_owner`, `blocker_reason`, `blocker_target`,
  `repair_command`, `repair_command_runnable`, `stop_anchor`) across the
  v4.21-v4.45.x chain wiring without contract-row updates. The amendment
  introduces a no-partial-contract-shape acceptance gate: a runtime dataclass
  field addition is not complete until the platform contract row, schema
  fixtures, contract registry closure, and consuming projections/checks are
  all updated in the same typed slice, OR the controller emits a typed blocker
  naming the missing producer. Folds into
  `MP-GUARDIR-V4-WORK-STREAM-A0-CODE-IDENTITY-RECEIPT-S1` and
  `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-BOOT-CONTINUATION-S1`.
- Applies the v4.52 architectural Finding from Codex `rev_pkt_4752`:
  `dev/reports/review_channel/offline_findings/2026-05-21T11-05Z-claude-ack-rev_pkt_4752-review-state-contract-drift.md`.
  ReviewState contract drift unowned: `develop next` surfaces the critical
  finding `audit_review_state_contract_drift` against raw file
  `dev/scripts/devctl/runtime/review_state_parser.py` with reducer message
  "No active plan-row linkage on target_ref; surfaced as finding-priority
  slice for codex review." The drift has documented ownership in
  `MP377-P0-T17` (ReviewState/ActionResult/parser parallel-implementation
  retirement) and `MP377-P1-T06` (collapse reviewer/runtime authority onto one
  canonical producer tick). The amendment binds
  `audit_review_state_contract_drift` to that typed plan spine and requires
  `develop next` + finding-priority + planning IR + startup quality signals to
  surface the owning PlanRow instead of the raw file. No new ReviewState row.
- Applies the v4.53 architectural Finding from Codex `rev_pkt_4753`:
  `dev/reports/review_channel/offline_findings/2026-05-21T11-20Z-claude-ack-rev_pkt_4753-4754-resolver-gates-and-sidecar.md`.
  Packet-to-plan resolver gates not implemented: typed contracts exist
  (`PacketPlanIngestionMapping`, `MandatoryIngestBeforeImplementInvariant`,
  `PacketCreationBinding`, `PacketDurableIngestionReceipt`), but enforcement
  is still planned or prose rather than hard pre-implementation gates. The
  amendment adds a current-plan resolver implementation/parity child row under
  `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`, makes
  `MandatoryIngestBeforeImplementInvariant` a hard gate for implementation
  selection, requires `PKT-BIND-*` rows to remain provenance until a
  `PlanIntentIngestionReceipt` resolves them, and ties lifecycle packet
  deferrals to durable-binding proof before closure effects.
- Applies the v4.54 architectural Finding from Codex `rev_pkt_4754`:
  `dev/reports/review_channel/offline_findings/2026-05-21T11-20Z-claude-ack-rev_pkt_4753-4754-resolver-gates-and-sidecar.md`.
  Closed read-only sidecar sessions promote to controller blockers (fresh
  repro of v4.50/rev_pkt_4749): `develop next` selected
  `agent-supervise --actor codex --provider codex --role reviewer --session-id
  019e4963-7bd5-7120-871f-3521ed74a7d2` as the next required command even
  though the helper sidecar was closed; the command returned `status=blocked`,
  `freeze_detected=true`. The amendment adds explicit subagent/helper session
  typed delegation (`delegation_role`, `parent_session`, `purpose`,
  `authority_class`) in `AgentSessionOutcome`, `AgentDispatchRouter`, and
  agent-mind projections; prevents closed read-only sidecars from owning live
  continuation anchors or current plan selection; and requires `develop next`
  plus the final gate to prioritize the active plan/packet owner over stale
  sidecar `agent-supervise` rows.
- Applies the v4.54.1 codex verification verdict from `rev_pkt_4756`. The
  v4.54 canonical-plan amendment verifies *structurally* — `develop
  ingest-plan --dry-run` parsed 36 row ids, `check_active_plan_sync` ok,
  `check_multi_agent_sync` ok (with topology warning evidence-ref), and
  `git diff --check` ok. Four closure gates remain red and are captured
  here so the canonical plan is the durable record, not the chat:
  (1) `dev/audits/plan_intake/sha256-manifest.txt` was stale at
  `5a4919bc6cbf59df…`; the current file SHA is
  `69abdd340ccca6e31d55894e730846b8709c643800d0ad5c14f283e68c801d72`
  (4685 lines / 289869 bytes) — manifest updated in this slice.
  (2) `check_platform_contract_closure` still fails on
  `GitMutationProofReceipt.code_identity_hash` and the six
  `ControlPlaneReadModel` BlockerSnapshot fields per v4.51 acceptance.
  (3) The topology hardcode guard plus focused topology test fail on a new
  uninventoried provider literal at
  `dev/scripts/devctl/runtime/startup_blocker_decision.py:55` (value
  `"claude"` in the `import_index_atomicity` repair directive tuple). This
  is exactly the label-drift pattern v4.55 targets and folds into that
  slice's acceptance.
  (4) `develop next` still selects the raw `audit_review_state_contract_drift`
  finding with no active plan-row linkage, per v4.52 acceptance.
  Implementation slices for v4.46-v4.55 remain queued for typed
  `task_started`; structural verification is captured but implementation
  closure is not claimed.
- Applies the v4.55 architectural Finding from Codex `rev_pkt_4755`:
  `dev/reports/review_channel/offline_findings/2026-05-21T11-55Z-claude-ack-rev_pkt_4755-topology-labels.md`.
  Topology labels must compile to typed role/cardinality authority, not
  remain controller truth. Current projections still surface overlapping
  scalar labels (`multi_agent_active`, `tools_only`, `solo`, `dashboard`,
  `active_dual_agent`, `single_agent`) as if they were durable authority;
  the v4.54.1 startup_blocker_decision.py:55 violation is a concrete
  example of a hardcoded `"claude"` provider literal that should resolve
  through `RoleCapabilityRegistry`/`AgentDispatchRouter` instead. Existing
  typed contracts already have the right model:
  `CollaborationModeTopology`, `CollaborationSession.role_assignments`,
  `actor_authorities`, `RoleCapabilityRegistry`, `AgentDispatchRouter`,
  `LiveRoleTopology`, `SessionLease`, `MutationLease`. The amendment
  requires a v4 child row that makes durable topology an N-actor × N-role
  graph with role counts, capability grants, review-independence level,
  parent/delegation scope, and mutation lease state; old binary/scalar
  labels become generated compatibility aliases only. Consumers must
  agree (`develop next`, `startup`/`session-resume`, `review-channel`,
  `check_multi_agent_sync`, `AGENTS.md`/`CLAUDE.md` projections,
  `dashboard`/`status`) or emit a typed mismatch blocker. No new topology
  store — composes with `MP377-COLLABORATION-MODE-TOPOLOGY-S1`,
  `MP-NEW-P165-MODEL-AGNOSTIC-TOPOLOGY-S1`, and
  `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-BOOT-CONTINUATION-S1`.
- Applies the v4.55.1 codex tightening from `rev_pkt_4758` (anchors:
  `rev_pkt_4757` + `rev_pkt_4755`; target_revision
  `sha256:cddae621195affc8ebd08f297d6a39fabfabc7334dd69d7a46ae44e44cc76387`).
  Two corrections before any v4.55 implementation can be accepted as closed:

  **Correction 1 — stale continuation anchor handling is priority 1, not
  a later topology cleanup.** Live evidence: `develop show` reports
  multiple closed/read-only Codex reviewer sidecars as `agent-supervise`
  blockers with `continuation_anchor=rev_pkt_4481`. The defect is
  concretely in:
  - `dev/scripts/devctl/runtime/agent_supervise_driver.py` — resolves
    `GoalProgressReceipt` and sets `continuation_anchor_live = bool(anchor_id)`.
    Truthiness on the anchor id is the wrong predicate; an anchor id can
    be live for one session while stale for another.
  - `dev/scripts/devctl/runtime/goal_progress_receipt.py`
    `_latest_continuation_anchor` filters on `active + actor match` only,
    not on supervised session, target role, plan/delegation scope, or
    helper-session outcome.

  Acceptance: `AgentSupervise` must resolve anchors through typed
  actor + role + session + plan + delegation scope, and closed read-only
  helper sessions must retire or ignore anchors that were not issued to
  them. This work is folded into v4.50 / v4.54 acceptance under
  `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-BOOT-CONTINUATION-S1` — promoted from
  later cleanup to priority 1.

  **Correction 2 — v4.55 wording was wrong on "generated compatibility
  aliases."** The v4.55 amendment said legacy labels (`single_agent`,
  `dual_agent`, `multi_agent_active`, `active_dual_agent`, `tools_only`,
  `solo`, `dashboard`) "become generated compatibility aliases only."
  Codex's tightening replaces that: these labels may exist ONLY as
  **(a)** historical input parsed into typed
  role/cardinality/capability/lease fields, OR **(b)** explicit migration
  debt. They must NOT appear as runtime/controller/projection truth in
  `AGENTS.md`, `CLAUDE.md`, `develop next`, `startup`, `dashboard`, or
  guards after migration. If any consumer needs an old string, it must
  emit a typed migration/debt blocker rather than surfacing that label
  as an active mode. The "generated compatibility aliases" phrasing from
  v4.55 is hereby retired; v4.55 acceptance reads as corrected above.

## Required Existing-Row Composition Anchors

- `MP-NEW-P195-ASYNC-CLOUD-PROOF-S1`, `MP-NEW-P196-AHEAD-OF-RUNTIME-PROOF-CACHE-S1`, `MP-NEW-P197-CONTINUOUS-PROOF-SCHEDULER-S2`, `MP-NEW-P198-QUALITY-REPAIR-SCHEDULER-S1`
- `MP-NEW-P180-ZGRAPH-PROJECTION-OVER-CONTEXTGRAPH-S1`, `MP-NEW-P181-POST-COMMIT-CONTEXTGRAPH-REFRESH-S1`, `MP-NEW-P183-ZGRAPH-LICENSE-VENDORING-DECISION-S1`
- `P102-ENFORCE-S1`, `P102-RECEIPT-DBC-S1`
- `MP-NEW-P188-PEER-COMMUNICATION-STATE-SNAPSHOT-S1`, `MP-411`, `MP-379`
- `MP377-GUARDIR-PLANROW-ORACLE`, `MP377-PLAN-INGESTION-RECEIPT-SPINE-S1`, `MP377-PLAN-INGESTION-DRIFT-DETECTION-S1`, `MP377-PLAN-INGESTION-TRANSACTION-S1`, `MP377-PLAN-INGESTION-ROLLBACK-S1`
- `MP377-PROJECTION-RETIREMENT-CONTRACT-S1`, `MP377-GUARDIR-PROJECTION-OWNERSHIP-S1`, `MP377-P233-CONTRACT-CONNECTIVITY-DEBT-RATCHET-S2`
- `MP377-P0-T22`, `MP377-P0-T22A`, `MP377-P0-T22B`, `MP377-P0-T22C`, `MP377-P0-T22D`, `MP377-P0-T22E`
- `MP377-P0-RC-PAIR-S1`, `MP377-P0-ROLE-MATRIX-DOGFOOD-S1`, `MP377-P0-ROLE-MATRIX-ROSTER-S1`, `MP377-P0-ROLE-ROSTER-TOPOLOGY-S1`, `MP377-P0-LIFECYCLE-ROLE-SIGNOFF-S1`
- `MP377-P0-ACTIVE-WORK-ENVELOPE-S1`, `MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1`, `MP377-P0-NEXT-BLOCKER-LIFECYCLE-S1`
- `MP377-MULTI-SESSION-TARGET-DISAMBIGUATION-S1`, `MP377-PACKET-MATCHING-ROLE-SCOPE-S1`
- `SessionPosture`, `SessionLivenessSignal`, `SessionActivityLog`, `AgentMindSlice`, `AgentSessionOutcome`, `ActorAuthorityState`, `CapabilityGrantState`, `CheckpointBudgetShape`, `BlockerSnapshot`, `ControlPlaneReadModel`, `PlanningIRSnapshot`, `SystemPicture`, `InstructionBootCard`, `RoleInstructionCard`, `RoleGuard`, `CustomRoleDefinition`, `RoleCreationAction`, `PlatformGuide`, `SystemCatalog`, `SystemMapSnapshot`, `OperatorCommandWrapper`, `SessionTerminationPolicy`, `TaskCompleteDecision`, `AgentSessionContinuation`
- `TypedAction`, `ActionResult`, `RunRecord`, `ValidationReceipt`, `MutationLease`, `AgentLoopDecision`
- `DevelopmentCollaborationMode`, `CollaborationModeTopology`, `RoleCommandEnvelope`, `AgentDispatchRouter`, `PeerCollaborationEdge`, `AgentSpawnAuthority`

## Required Packet-Binding Citations

- `PKT-BIND-REV-PKT-4071`
- `PKT-BIND-REV-PKT-1428`, `PKT-BIND-REV-PKT-2361`, `PKT-BIND-REV-PKT-2622`
- `PKT-BIND-REV-PKT-4485`, `PKT-BIND-REV-PKT-4651`, `PKT-BIND-REV-PKT-4652`, `PKT-BIND-REV-PKT-4653`, `PKT-BIND-REV-PKT-4654`, `PKT-BIND-REV-PKT-4655`, `PKT-BIND-REV-PKT-4656`, `PKT-BIND-REV-PKT-4657`, `PKT-BIND-REV-PKT-4658`, `PKT-BIND-REV-PKT-4660`, `PKT-BIND-REV-PKT-4661`, `PKT-BIND-REV-PKT-4662`, `PKT-BIND-REV-PKT-4663`, `PKT-BIND-REV-PKT-4667`, `PKT-BIND-REV-PKT-4670`, `PKT-BIND-REV-PKT-4671`, `PKT-BIND-REV-PKT-4674`, `PKT-BIND-REV-PKT-4675`, `PKT-BIND-REV-PKT-4676`
- `PKT-BIND-REV-PKT-4678`, `PKT-BIND-REV-PKT-4680`, `PKT-BIND-REV-PKT-4687`, `PKT-BIND-REV-PKT-4692`, `PKT-BIND-REV-PKT-4693`, `PKT-BIND-REV-PKT-4698`, `PKT-BIND-REV-PKT-4701`, `PKT-BIND-REV-PKT-4704`, `PKT-BIND-REV-PKT-4705`, `PKT-BIND-REV-PKT-4706`, `PKT-BIND-REV-PKT-4707`

## Rows To Ingest From This Plan

- `MP-GUARDIR-V4-PHASE-0-6-E-PLAN-INGESTION-S1` Implement plan-ingestion bootstrap automation, source retention, manifest verification, amendment metadata, and startup visibility for this v4 plan. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-e
- `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1` Resolve current plan authority from ingested typed `PlanRow` state and fail closed when plan-intake markdown, active docs, generated boot cards, dashboards, or chat are not backed by startup-visible typed rows. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-e-current-plan-authority
- `MP-GUARDIR-V4-PHASE-0-6-E-INSTRUCTION-SURFACE-USABILITY-S1` Regenerate `AGENTS.md`, `CLAUDE.md`, slash templates, and platform guides from typed command/catalog inputs so agents get role-aware command routing, current-plan discovery, system-map/duplicate-check guidance, and projection-only boundaries without turning prose into authority. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-e-instruction-surface-usability
- `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-INSTRUCTION-CONNECTIVITY-S1` Register and compose `InstructionBootCard`, `RoleInstructionCard`, `RoleGuard`, role customization contracts, command catalogs, and generated-surface renderers through contract-connectivity, system-map, and guard chokepoints so role guidance is discoverable without becoming backend authority. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-e-role-instruction-connectivity
- `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-BOOT-CONTINUATION-S1` Resolve and display each agent's typed role envelope, peer lane, allowed actions, blocked actions, and keep-working/stop policy at startup, develop-next, final gate, and generated instruction surfaces so Codex/Claude roles and continuation anchors do not depend on operator reminders. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-e-role-boot-continuation
- `MP-GUARDIR-V4-PHASE-0-6-E-MP377-EXTRACTION-PARENTAGE-S1` Bind all `MP-GUARDIR-V4-*` rows as MP-377 T22 child/detail rows with PlanRow parent refs and ingestion provenance, never as a parallel canonical authority family. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-e-mp377-extraction-parentage
- `MP-GUARDIR-V4-PHASE-0-6-A-CHANNEL-RECOVERY-S1` Amend active Phase 0.6.A with review-channel lifecycle recovery, lifecycle polling, and review_accepted target validation. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-a
- `MP-GUARDIR-V4-PHASE-0-6-A-STARTUP-REPAIR-COMMAND-S1` Ensure `startup_authority_failed`, `repair_startup_authority`, and final-response gates emit a typed owner, target, and runnable repair command or a typed stop_anchor, instead of looping read-only with no closure path. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-a-startup-repair-command
- `MP-GUARDIR-V4-PHASE-0-6-A-NEXT-COMMAND-OBEDIENCE-S1` Prove commands emitted as `next_required_command` / `next_step_command` carry the control-decision input, proxy authority, actor/session scope, packet lifecycle state, and command-envelope mutation-safety state needed to pass `ControlDecisionObeyedGuard`; otherwise emit a typed blocker instead of an unrunnable or destructive command. Data-model flags such as `repair_command_runnable` are not closure until the producer and consumer callsites enforce them. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-a-next-command-obedience
- `MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1` Normalize command actor/proxy and mutation-risk classification through one typed envelope that reuses `AttemptedActionReceipt`, `ProxyAuthorityRoute`, `RoleCommandEnvelope`, and `AgentLoopDecision` refs so `develop`, final gate, response shape, operator wrappers, advisory filters, action routing, control-decision matching, and consistency checks cannot copy ad hoc `--actor` parsing or partial mutation token lists, cannot render peer-owned or destructive commands as executable shell without proxy authority plus governed mutation authority, cannot make the shared classifier import higher-level consumers that already depend on it, and cannot leave typed action identifiers or `next_command` mutation checks outside the shared classifier/adapter path. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-a-command-envelope-normalization
- `MP-GUARDIR-V4-PHASE-0-6-A-TASK-PRODUCED-GUARD-REPAIR-S1` Repair the post-implementation `task_produced -> review_accepted` guard path when `ControlDecisionObeyedGuard` rejects a valid downstream packet after a typed `task_started`. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-a-task-produced-guard-repair
- `MP-GUARDIR-V4-PHASE-0-6-A-REVIEW-FEEDBACK-POST-OBEDIENCE-S1` Repair the bilateral review-feedback path so reviewer `finding` / `task_progress` / `review_failed` / eligible `review_accepted` posts and implementer `task_progress` / `task_blocked` / `task_produced` responses to reviewer findings compose with `ActorAuthorityState`, `AgentLoopDecision`, source-session authority, parent-kind semantics, and `ControlDecisionObeyedGuard` instead of failing after the system asks agents to communicate. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-a-review-feedback-post-obedience
- `MP-GUARDIR-V4-PHASE-0-6-A-ROLE-MUTATION-LEASE-S1` Enforce role-scoped live-tree mutation leases so reviewer sessions remain read-only while an implementer-owned `task_started` lane is live unless typed authority transfers or partitions the write set. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-a-role-mutation-lease
- `MP-GUARDIR-V4-PHASE-0-6-A-MUTATION-METHOD-PROVENANCE-S1` Require implementation file mutations to route through typed patch/edit or governed action paths that record actor, role, session, lease, path, and command provenance; detect raw shell redirection/heredoc writes as policy failures or governed exceptions rather than silent code changes. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-a-mutation-method-provenance
- `MP-GUARDIR-V4-PHASE-0-6-B-CASCADE-PARENT-AUTHORITY-S1` Bind cascade lifecycle posts to an explicit primary semantic parent packet and reject wrong target session, wrong target role, stale parent packet, ambiguous multi-packet evidence, or unrelated lineage even when structural packet evidence is present. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-b-cascade-parent-authority
- `MP-GUARDIR-V4-PHASE-0-6-C-REVIEW-READ-AUTHORITY-S1` Keep review-channel `show`, `inbox`, `status`, and history/body-observation reads available to the scoped reviewer without granting mutation or semantic-ingestion bypass authority. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-c-review-read-authority
- `MP-GUARDIR-V4-PHASE-0-6-C-COORDINATION-LANE-IMPORT-ISOLATION-S1` Keep `review-channel`, `agent-mind`, `session`, `test-python` routing, and recovery diagnostics importable through a minimal coordination command surface when implementation-owned command modules or shared runtime classifiers contain syntax/runtime import failures, so reviewers can post typed findings without mutating the implementer's write set or inventing an offline parallel channel. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-c-coordination-lane-import-isolation
- `MP-GUARDIR-V4-PHASE-0-6-D-REVIEW-CHANNEL-SOURCE-SESSION-S1` Ensure review-channel packet posts carry the real actor/source session id so semantic cascade validation does not compare closure targets against fallback `local-review` source sessions. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-d-review-channel-source-session
- `MP-GUARDIR-V4-PHASE-0-6-D-SOURCE-SESSION-AUTHENTICITY-S1` Verify live-agent review-channel source sessions against existing typed session/actor authority so arbitrary non-fallback strings cannot masquerade as real session ids. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-d-source-session-authenticity
- `MP-GUARDIR-V4-PHASE-0-6-D-SOURCE-SESSION-CONTINUITY-S1` Preserve authenticated packet parents across agent session rotation by validating source sessions against post-time typed session attestations and rotation/expiry policy, not only the latest projection. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-d-source-session-continuity
- `MP-GUARDIR-V4-PHASE-0-6-D-AGENT-MIND-SCOPE-S1` Scope agent-mind and subagent projections by provider, role, session, and parent actor so fanout workers cannot overwrite main reviewer/implementer session authority. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** phase-0-6-d-agent-mind-scope
- `MP-GUARDIR-V4-WORK-STREAM-A0-CODE-IDENTITY-RECEIPT-S1` Add `GitMutationProofReceipt.code_identity_hash` as the prerequisite proof-binding field before push-routing, CI artifact, and proof-index work starts. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-a-0
- `MP-GUARDIR-V4-WORK-STREAM-A-PUSH-ROUTING-S1` Fix explicit GuardIR push-routing mismatch validation and dogfood existing push authorization/bypass authority. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-a
- `MP377-P2-T02-CI-ARTIFACT-LEDGER-INGEST-S1` Connect CI artifact ledger ingest into the existing P195/P198 cloud-proof rows and governance-review ledger. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-c
- `MP-GUARDIR-V4-MP379-CLOUD-PROOF-REPORTING-AMENDMENT-S1` Amend MP-379 reporting collectors with cloud proof, CI findings, validation state, and proof lineage surfaces. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-379 **source_section_id:** operator-visibility
- `MP-GUARDIR-V4-WORK-STREAM-E-CONNECTIVITY-DEBT-S1` Reduce typed-state connectivity debt by composing existing classifiers, routing wires, push-enforcement contracts, and governance bootstrap import surfaces. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-e
- `MP-GUARDIR-V4-WORK-STREAM-E-REPO-PACK-ADOPTER-BOUNDARY-S1` Move or mark VoiceTerm/product-specific defaults behind `ProjectGovernance`, `RepoPack`, `RepoPathConfig`, `SurfaceOwnershipMap`, `ExtensionBundle`, or explicit adopter-pack debt before claiming portable GuardIR closure. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-e-repo-pack-adopter-boundary
- `MP-GUARDIR-V4-WORK-STREAM-F-RASPBERRY-PI-EDGE-PACK-S1` Record optional Raspberry Pi edge-device mode as an adopter-pack projection, proof runner, watchdog, physical-approval receipt source, and evidence cache over existing repo-pack policy. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-376 **source_section_id:** work-stream-f
- `MP-GUARDIR-V4-WORK-STREAM-F-ROLE-SUBSTRATE-S1` Upgrade Raspberry Pi mode into an opt-in active cognitive-role substrate with deterministic and light-AI background roles routed through typed packets. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-376 **source_section_id:** work-stream-f-active-role-substrate
- `MP-GUARDIR-V4-WORK-STREAM-G-SYSTEM-CONVERGENCE-S1` Add one system-level convergence loop proving Work Streams A-F compose through typed startup, packet, proof, dashboard, and dogfood evidence. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-g
- `MP-GUARDIR-V4-G1-WORKINTAKE-LOOP-CLOSURE-S1` Wire plan-intake startup evidence into WorkIntakePacket and AutoModeState consumers. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-g-1
- `MP-GUARDIR-V4-G2-STARTUP-SIGNALS-STITCH-S1` Load CodeIdentity and ingest-failure summaries into startup quality signals for next-session consumption. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-g-2
- `MP-GUARDIR-V4-G3-BRIDGE-SEVERANCE-S1` Remove operator-console bridge.md fallback authority paths and guard against projection fallback. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-359 **source_section_id:** work-stream-g-3
- `MP-GUARDIR-V4-G4-ACTION-PROOF-CHAIN-S1` Close TypedAction -> ActionResult -> RunRecord -> ValidationReceipt back-references. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-g-4
- `MP-GUARDIR-V4-G5-CONVERGENCE-LOOP-S1` Define and emit WorkStreamConvergenceReceipt over one end-to-end dogfood run. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-g-5
- `MP-GUARDIR-V4-G6-CONTRACT-BUNDLE-WIRING-S1` Register v4 CodeIdentity and ingest-failure schema fixtures in guard and bundle policy. **status:** spec **sdlc_stage:** plan **mp_scope:** MP-377 **source_section_id:** work-stream-g-6

## v4.26 Cascade Order

Phase 0.6.E plan ingestion / current-plan authority / instruction-surface
usability, Phase 0.6.A channel recovery / role-scoped mutation leases, Phase
0.6.B cascade parent semantics, Phase 0.6.C review read authority, and Phase
0.6.D source-session stamping are prerequisite architecture gates.
They close before the A.0 handoff is accepted as complete or before further
dual-agent implementation begins. Phase 0.6.A watches control packets and
live-tree write leases, Phase 0.6.B validates parent-packet lineage, Phase
0.6.C protects read-only packet observation, Phase 0.6.D preserves and
authenticates the posting actor's real source session id, and Phase 0.6.E owns
plan-source ingestion, startup visibility, current authority resolution from
typed `PlanRow` state, and generated instruction surfaces that route agents to
the correct typed commands without becoming authority.

Phase 0.6.A has two closure checkpoints after the A.0 dogfood run. The
planning and `task_started` path must work before implementation starts. The
post-implementation `task_produced -> review_accepted` path may use A.0 as live
repair evidence, but it closes before Work Stream A begins.

Cascade:

1. Phase 0.6.E plan ingestion automation,
   `CurrentPlanAuthorityResolver`, instruction-surface command routing, and
   Phase 0.6.A planning / handoff recovery close.
2. Phase 0.6.A role-scoped mutation lease enforcement closes for reviewer /
   implementer live-tree ownership.
3. Phase 0.6.A structural cascade-post repair closes for action mapping and
   basic bilateral scope.
4. Phase 0.6.B semantic parent-packet authority rejects wrong session, wrong
   role, stale parent, and unrelated lineage; Phase 0.6.C read authority keeps
   packet inspection available without mutation authority.
5. Phase 0.6.D ensures review-channel posts carry actor/source session ids
   that resolve to existing typed actor/session authority, so valid
   `task_produced -> review_accepted` closure is not blocked by a fallback
   `local-review` parent session and cannot be spoofed by an arbitrary string.
   Phase 0.6.D also preserves post-time session authority across rotation so a
   real parent does not become a ghost solely because the actor's latest
   projection points at a newer session. Multi-agent/subagent projections are
   scoped so helper agents cannot overwrite the main actor's source-session
   authority.
6. Work Stream A.0 extends `GitMutationProofReceipt` with
   `code_identity_hash`.
7. Phase 0.6.A/B/C/D repairs the `task_produced -> review_accepted` guard path using
   A.0 as dogfood evidence.
8. Work Stream A fixes GuardIR push routing and dogfoods push authority.
9. Work Stream C emits CI proof artifacts and cloud findings.
10. Work Stream B indexes Work Stream C outputs through ProofIndex.
11. Work Stream D consumes B/C evidence for SafeContinuationDecision.
12. Work Stream E reduces connectivity debt; it may run after the prerequisites
   whenever it does not block A-D.
13. Work Stream G.1-G.4 stitches intake, startup signals, bridge severance, and
   action proof backrefs.
14. Work Stream F activates only after G.2 exposes startup summaries needed by
   Pi daemons and edge projections.
15. Work Stream G.5 emits the convergence proof last.

## Existing Rows To Amend

Do not create parallel `MP-GUARDIR-V4-SLICE-B/C/D` rows. Amend existing rows so
the context graph connects instead of expanding:

- `MP-NEW-P195-ASYNC-CLOUD-PROOF-S1..S6` for async cloud proof and typed CI
  artifact emission.
- `MP-NEW-P196-AHEAD-OF-RUNTIME-PROOF-CACHE-S1..S6` for CodeIdentity,
  proof-cache lookup, and runtime proof consumption.
- `MP-NEW-P197-CONTINUOUS-PROOF-SCHEDULER-S2` for SafeContinuationDecision and
  path-overlap scheduling.
- `MP-NEW-P198-QUALITY-REPAIR-SCHEDULER-S1..S6` for cloud findings,
  applicability, and repair packet flow.
- Existing `MP411` portability / GuardIR extraction row for push-routing
  consolidation.

The planning handshake and peer-inbox-watch discipline are Phase 0.6.A
requirements. The A.0 dogfood failure creates one bounded Phase 0.6.A repair
row only because downstream closure packets are currently rejected after a valid
typed `task_started`.

## Existing Adjacent Plans To Cite

These rows and findings are related authority or predecessor context. Cite and
compose with them; do not rebuild them inside this plan.

### MP-377 P0 Adjacencies

- GuardIR v4 is a child/detail amendment of the MP-377 extraction and
  ingestion chain, not a second canonical plan family. The parent chain is
  `MP377-P0-T22` plus `MP377-P0-T22A` through `MP377-P0-T22E`, with deeper
  `T22AD`, `T22AE`, and `T22AF` rows providing PlanRow oracle, sync evidence,
  honest status, and agent-sync command ownership. All `MP-GUARDIR-V4-*` rows
  ingested from this file must carry parent refs, ingestion provenance, source
  snapshot refs, and plan-intake manifest evidence back to that MP-377 chain.
- `MP-GUARDIR-V4-PHASE-0-6-E-MP377-EXTRACTION-PARENTAGE-S1` closes only when
  startup, `develop next`, context graph, dashboard/status, and final-response
  gates all resolve the same current plan through `PlanRow` / `PlanRegistry`
  authority rather than through whichever active owner doc, generated boot
  card, bridge projection, or chat recap was most recently read.
- `MP377-P0-T08F` (`dev/active/ai_governance_platform.md:4784`) owns role and
  session packet inbox routing. Phase 0.6.A extends this, it does not fork it.
- `MP377-P0-T22AE-C` (`dev/active/ai_governance_platform.md:5628`) owns
  per-packet sync evidence with explicit correlation. Work Stream A's
  `PushAuthorizationRecord` consumption depends on that correlation model.
- `MP377-P0-T22AE-E` (`dev/active/ai_governance_platform.md:5642`) owns honest
  sync status. Channel recovery must distinguish stale, blocked, and active
  actors through that surface.
- `MP377-P0-T22AD-I` (`dev/active/ai_governance_platform.md:5600`) owns the
  PlanRow and `dev/state/plan_index.jsonl` oracle needed by Phase 0.6.E.
- `MP377-P0-T22AF-A` (`dev/active/ai_governance_platform.md:5663`) owns the
  repo-owned `agent-sync` command and slash adapters. Bilateral polling composes
  with it instead of adding side state.
- Phase 0.6.A live dogfood (`dev/active/ai_governance_platform.md:90-129`)
  landed live-controller and push-controller repairs on 2026-05-19. Work Stream
  A must cite that proof before adding more push-routing behavior.

### MASTER_PLAN Adjacencies And Open Packet Findings

- `MP-NEW-P195-ASYNC-CLOUD-PROOF-S1..S6`
  (`dev/active/MASTER_PLAN.md:8770-8776`) is the keystone for async cloud proof
  and exact-snapshot applicability.
- `MP-NEW-P198-QUALITY-REPAIR-SCHEDULER-S1..S6`
  (`dev/active/MASTER_PLAN.md:8798-8803`) owns CloudFinding,
  FindingApplicability, RepairPacket, and stale-finding handling.
- `MP-NEW-P188-PEER-COMMUNICATION-STATE-SNAPSHOT-S1`
  (`dev/active/MASTER_PLAN.md:8678-8695`) composes directly with bilateral
  peer polling and bridge retirement.
- `MP-411` (`dev/active/MASTER_PLAN.md:1326`) owns portability audit context
  that Work Stream A and Work Stream F must respect.
- `MP-379` (`dev/active/MASTER_PLAN.md:5058-5064`) owns shared reporting
  honesty and is amended by
  `MP-GUARDIR-V4-MP379-CLOUD-PROOF-REPORTING-AMENDMENT-S1`.
- `PKT-BIND-REV-PKT-4156` (`dev/active/MASTER_PLAN.md:8865`) reports
  FeatureProofReceipt proof weakness. v4.8 FeatureProofReceipt dogfood fields
  must close, not mask, that gap.
- `PKT-BIND-REV-PKT-4152` (`dev/active/MASTER_PLAN.md:8861`) reports orphaned
  BypassLifecycle receipts. Work Stream A must reuse BypassLifecycle without
  increasing orphan count.
- `PKT-BIND-REV-PKT-4564` (`dev/active/MASTER_PLAN.md:9121`) reports
  GitMutationProofReceipt / CorrelationContext duplication. Any
  `code_identity_hash` extension must reduce duplication and builder shape
  debt.

### P102 Typestate Alignment

P102 already landed the Idris-like typed-state foundation. v4.8 must inherit and
cite it; it must not add a new typestate work stream.

- P102 Phase C algebraic result cases landed in
  `dev/active/ai_governance_platform.md:14741`.
- P102 Phase 1.5 nominal governance IDs landed in
  `dev/active/ai_governance_platform.md:14764`.
- P102 Phase 7 governed-transition graph verifier landed in
  `dev/active/ai_governance_platform.md:14784`.
- P102 Idris-ST enforcement follow-up is queued in
  `dev/active/ai_governance_platform.md:14807`.
- Evidence files include
  `dev/scripts/devctl/commands/vcs/push_result_typestate.py`,
  `dev/scripts/devctl/runtime/typed_ids.py`,
  `dev/scripts/checks/check_governed_transitions.py`, and
  `dev/scripts/devctl/runtime/governed_transition_typechecker_models.py`.
- Queued follow-ups `P102-ENFORCE-S1` and `P102-RECEIPT-DBC-S1` remain the
  canonical runtime pre/postcondition and receipt-evidence path.
- `THESIS_EVIDENCE.md:515-625` describes the abstract-interpretation substrate:
  deterministic transfer functions, widening/narrowing, and fixpoint
  convergence.

### ZGraph Adjacencies

ZGraph is already planned as secondary advisory graph projection over canonical
typed context graph state. v4.8 must cite that work; it must not create a
parallel graph guard or graph authority.

- `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md:3171`
  defines P180 ZGraphProjection over `ContextGraphSnapshot` with the rule that
  deterministic guards remain authority.
- `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md:3202`
  defines P181 ContextGraph auto-refresh.
- `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md:3221`
  defines P183 ZGraph affected-test selection.
- `dev/active/MASTER_PLAN.md:8645-8648` carries the queued P180-P183 rows.
- `dev/active/ai_governance_platform.md:340-341` records the hybrid decision:
  do not build a parallel ZGraph; use it over existing `ContextGraphSnapshot`.
- `dev/active/ai_governance_platform.md:540` records `GraphAuthorityRole` and
  `GraphContradictionIndex` as graph authority-health metadata.
- v4.8's only graph implementation obligation is the
  `plan_intake_includes` context-graph edge. Full ZGraph promotion remains
  deferred to P180-P183.

### Professional Docs, Navigation, And Repo-Pack Boundaries

- `dev/guides/README.md` and `dev/guides/AI_GOVERNANCE_PLATFORM.md` are
  professional/operator-facing guide projections over typed authority. Root
  product README surfaces remain adopter-facing. None of these prose surfaces
  may become backend authority unless a typed contract, PlanRow, receipt, or
  guard owns the rule.
- `dev/guides/SYSTEM_MAP.md`, `system-map`, `system-picture`,
  `context-graph`, `graph-walk`, and proof-of-navigation regressions are
  discovery/read-model surfaces. Work Stream E may improve their registry and
  edge inputs, but closure still comes from typed rows, contracts, receipts,
  and guards.
- GuardIR portability depends on explicit `RepoPack`, `RepoPathConfig`,
  `SurfaceOwnershipMap`, `ExtensionBundle`, `ProjectGovernance`, and
  non-VoiceTerm pilot-repo proof. A portable closure claim must prove these
  surfaces can select the right repo pack and path config without falling back
  to product-shell constants.
- Generated boot-card and instruction-surface changes must run
  `render-surfaces`, `docs-check --strict-tooling`,
  `check_instruction_surface_sync.py`, and the bridge projection-only checks.
  Projections may route agents to typed state; they must not override it.

### Sibling Plan Citations

- `dev/active/review_probes.md:48-73`: v4.8 proof/finding payloads should
  reuse the `ai_instruction` and `review_lens` schema rather than inventing
  another review-guidance shape.
- `dev/active/agent_substrate_architecture_review.md:46`: Phase 0.6.A does
  not mutate `OperatorInteractionMode`; it keeps operator interaction mode
  separate from reviewer mode.
- `dev/active/pre_release_architecture_audit.md:93-103`: v4.8 pytest
  scaffolding and proof-field enforcement address the policy-engine test
  coverage gap noted there.

### v4.8 Additional Architectural Adjacencies

These are adjacent scopes discovered during the v4.6 through v4.8 reviews. They are cited so
the plan remains connected, but they are not implemented by Work Stream F.

- P180/P181/P183 ZGraph promotion remains the graph-advisory owner
  (`dev/active/MASTER_PLAN.md:8645-8648`).
- Cognitive Role Fleet and orchestrator authority remain broader MP-377 work
  (`dev/active/MASTER_PLAN.md:9054-9078`) and cached-hammock P56/P58 work
  (`dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md:155`,
  `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md:1333`).
  Work Stream F may add `RoleExecutionTarget` / `deployment_location` over
  existing `CognitiveRoleFleetAssignment`; it must not create a parallel
  `CognitiveRoleFleetConfig` authority.
- MP-359 Operator Console remains the desktop cockpit owner
  (`dev/active/MASTER_PLAN.md:5751-5829`). Pi LED/status projection is a second
  read-only form factor over typed state, not a replacement UI.
- MP-330/MP-331 Mobile Control-Plane remains the phone/off-LAN owner
  (`dev/active/MASTER_PLAN.md:5233-5234`, `dev/active/MASTER_PLAN.md:5242`).
  Pi mode is the embedded-device counterpart and must share typed projection
  semantics.
- P185 Packet Lifecycle and Silent-Expiry Guards remain the packet-expiry owner
  (`dev/active/MASTER_PLAN.md:8650-8657`). Pi daemons may observe and alert on
  silent expiry; they do not repair packet lifecycle state directly.
- P188 Bridge Runtime Coordination remains the bridge-retirement owner
  (`dev/active/MASTER_PLAN.md:8670`, `dev/active/MASTER_PLAN.md:8716`). Work
  Stream G.3 is a P188 S6/S7 integration checkpoint and reader inventory, not a
  broad parallel bridge-removal lane.

### v4.8 Thesis Deferrals

The following thesis concepts are relevant but explicitly deferred:

- `THESIS_EVIDENCE.md:515-625` / section 3.5 widening and narrowing beyond
  agent count: defer to MP-338 loop coordination follow-up.
- `THESIS_EVIDENCE.md:732` temperature formula evolution: defer to ZGraph P180
  advisory graph work.
- Typed lane authority enforcement: defer to MP-355 review-channel follow-up.
- `THESIS_EVIDENCE.md:873` GuardedCodingEpisode multi-round chains: defer to
  MP-358 continuous swarm follow-up.
- Proof-carrying execution beyond push decisions: keep in view for v4.8+ after
  Work Stream F can emit typed proof for LED and daemon decisions.

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

## Phase 0.6.E: Plan Ingestion Bootstrap

Goal: make this plan canonical typed state before any Phase 0.6.A continuation
or work-stream implementation executes. The plan is the first self-test of the
typed ingestion substrate.

Command:

```bash
python3 dev/scripts/devctl.py develop ingest-plan \
  --source dev/audits/plan_intake/2026-05-20-guardir-lifecycle-recovery-ci-proof-bridge-v4.md \
  --target-ref plan:MP-377 \
  --format md
```

Semantics:

- The current parser exposes `--dry-run`, `--source`, `--source-kind`,
  `--target-ref`, `--anchor-ref`, `--mutation-op`, `--sdlc-stage`, and
  `--plan-status`. The v4 plan must not require flags that do not exist.
- `--dry-run` renders the row parse / planned write result without mutating
  typed state.
- Canonicalization, operator-approval metadata, amendment receipt emission, and
  startup-visibility verification are Phase 0.6.E implementation deliverables,
  not already-supported CLI flags. If these are exposed as flags later, they
  must be added through the existing parser and covered by help-output tests.
- `PlanIntentIngestionReceipt` writes amendment metadata after row upserts
  succeed; `PlanSourceSnapshot` records source bytes/hash retention; neither
  creates a parallel plan tracker.
- `/ingest <file|packet|body>` is a thin wrapper over this command.

Rollback rule: row writes are idempotent upserts. If visibility fails after
writes, do not emit Phase 0.6.E closure. Fix visibility, rerun the same
supported `develop ingest-plan` command, and rerun startup/context visibility
checks.

## Phase 0.6.E Startup Visibility

This is explicit implementation work, not an optional verifier note.

- Extend `dev/scripts/devctl/runtime/startup_signals.py` with
  `_load_plan_intake_summary(repo_root)`.
- Read `dev/audits/plan_intake/INDEX.md` and `dev/state/plan_index.jsonl`.
- Emit `quality_signals["plan_intake"]["current_rows"]`, capped at 50 rows, with
  `row_id`, `plan_revision_id`, `source_doc_sha256`, and `status`.
- Include only `spec`, `amended`, and `promoted` rows.
- The startup-visibility verifier checks
  `startup.quality_signals.plan_intake.current_rows[*].row_id`. If exposed as
  a CLI flag later, the parser/help-output test must prove the flag exists.
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

## Existing Contract Extensions

Phase 0.6.E adds no new contract beyond the plan-ingest primitives below.
Work streams compose existing primitives first, then add the bounded v4.8
runtime and edge contracts listed in the producer matrix.

- Extend `PlanIntentIngestionReceipt`
  (`dev/scripts/devctl/runtime/plan_intent_ingestion.py`) with optional
  `operator_approval_actor_id`, `operator_approval_at_utc`,
  `old_plan_revision_id`, `superseded_plan_row_ids`, and
  `per_row_prior_source_doc_sha256`.
- Extend `PlanSourceSnapshot`
  (`dev/scripts/devctl/runtime/plan_source_retention_models.py`) with
  backward-compatible aliases: `source_doc_path` -> `source_ref`,
  `source_doc_sha256` -> `source_hash`, and `plan_revision_id`.
- Extend `GitMutationProofReceipt`
  (`dev/scripts/devctl/runtime/git_mutation_proof_receipt.py`) with
  `code_identity_hash` and an operation/mutation value for cloud artifacts.
  This replaces the proposed `ProofReceipt`.
- Extend `FeatureProofReceipt`
  (`dev/scripts/devctl/runtime/feature_proof_receipt.py`) with session/CLI
  dogfood fields: `session_id`, `command_invoked`, `stdout_digest`,
  `stderr_digest`, `json_parse_status`, `asserted_fields_present`, and
  `adoption_profiles_tested`. This replaces the proposed
  `SessionProofReceipt`.
- Extend `DogfoodSelfCheckReceipt`
  (`dev/scripts/devctl/runtime/evidence_receipts.py`) with
  `feature_contract_id`, `field_path_asserted`, and `field_present`. This
  replaces the proposed `SelfReferentialDogfoodReceipt`.
- Extend existing `PlanRowClosureReceipt` handling with optional
  `slice_id`. Slice closure becomes a query view over existing plan-row
  closures, not a new `SliceClosureReceipt` contract.
- Extend `LifecycleReceipt` for plan promotion criteria if promotion needs a
  durable receipt. Do not add a standalone `PlanPromotionReceipt`.
- Extend existing stale-finding/proof-ref handling with `proof_receipt_id` if a
  proof row goes stale. Do not add a standalone `StaleProofReceipt`.

## New Contracts That Survive v4.3 Consolidation

### CodeIdentity

File: `dev/scripts/devctl/runtime/code_identity.py`

Purpose: specialize existing repo identity evidence for proof applicability.

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

### IngestFailureReceipt

File: `dev/scripts/devctl/runtime/ingest_failure_receipt.py`

Store: `dev/state/ingest_failure_receipts.jsonl`

Purpose: record plan-ingest failure paths and link them to
`GovernedExceptionLifecycle` where recovery needs operator action.

Fields:

- `receipt_id`
- `plan_revision_id`
- `source_doc_sha256_attempted`
- `failure_reason`
- `failure_detail`
- `occurred_at_utc`
- `retry_count`
- `recovery_action_required`
- `governed_exception_lifecycle_id`
- `contract_id`
- `schema_version`

Failure reasons:

- `canonicalize_mismatch`
- `startup_visibility_timeout`
- `parser_rejected`
- `missing_operator_approval`
- `concurrent_ingest_collision`

## Phase 0.6.E Schema Fixtures

Required fixtures for truly-new contracts:

- `dev/test_data/schema_fixtures/CodeIdentity/1/valid/registry-row.json`
- `dev/test_data/schema_fixtures/CodeIdentity/1/invalid/missing-required-field.json`
- `dev/test_data/schema_fixtures/CodeIdentity/1/invalid/schema-version-mismatch.json`
- `dev/test_data/schema_fixtures/IngestFailureReceipt/1/valid/registry-row.json`
- `dev/test_data/schema_fixtures/IngestFailureReceipt/1/invalid/missing-required-field.json`
- `dev/test_data/schema_fixtures/IngestFailureReceipt/1/invalid/schema-version-mismatch.json`

Do not add `LifecyclePollingReceipt` fixtures unless a later amendment rejects
the v4.8 decision to extend `AgentPacketAttention` / `PeerAwarenessPolicy`
instead of adding a new polling contract.

## v4.8 Contract Producer And Store Matrix

Every v4.8 contract must have an emitter, a call site, and a store before it is
treated as implementation-ready. Contracts without producers are inert schema
debt.

### Net-New Contracts

| Contract | Producer function | Call site | Output store |
|---|---|---|---|
| `CodeIdentity` | `build_code_identity(repo_root, head_sha)` | `dev/scripts/devctl/runtime/code_identity.py` | inline in `PushAuthorizationRecord` and `GitMutationProofReceipt` |
| `WatcherEpisode` | `build_watcher_episode(observation, repo_root)` | `dev/scripts/devctl/runtime/watcher_episode.py`; Pi `pi-codex-poll-watcher.timer` | `dev/state/watcher_episodes.jsonl` |
| `OrchestratorDecision` | `build_orchestrator_decision(active_findings, plan_state)` | `dev/scripts/devctl/runtime/orchestrator_decision.py`; Pi `pi-orchestrator.timer` | `dev/state/orchestrator_decisions.jsonl` |
| `CodexResearchFinding` | `build_codex_research_finding(artifact_ref, claim_text, verdict)` | `dev/scripts/devctl/runtime/codex_research_finding.py`; `PlatformFindingIngest.record_review_input()` | `dev/reports/governance/finding_reviews.jsonl` |
| `DuplicateScopeGuardReport` | `build_duplicate_scope_guard_report(connectivity_report, function_dup_report, jscpd_report)` | `dev/scripts/devctl/runtime/duplicate_scope_guard_report.py`; daily Pi duplicate-scope check | `dev/state/duplicate_scope_guard_reports.jsonl` |
| `WorkStreamConvergenceReceipt` | `build_work_stream_convergence_receipt(closure_receipt_ids)` | `dev/scripts/devctl/runtime/work_stream_convergence_receipt.py`; `devctl develop converge --emit-receipt` | `dev/state/work_stream_convergence_receipts.jsonl` and audit receipt JSON |
| `IngestFailureReceipt` | `build_ingest_failure_receipt(plan_revision_id, source_doc_sha256, failure_reason, failure_detail)` | `dev/scripts/devctl/runtime/ingest_failure_receipt.py`; `devctl develop ingest-plan` failure path | `dev/state/ingest_failure_receipts.jsonl` plus `governed_exception_lifecycles.jsonl` link |
| `LifecycleLEDState` | `build_lifecycle_led_state(typed_system_state)` | `dev/scripts/devctl/runtime/lifecycle_led_state.py`; Pi LED projection daemon | `dev/reports/edge_device/<device_id>/led_state_latest.json` |
| `OperatorPhysicalApprovalReceipt` | `build_operator_physical_approval_receipt(device_id, button_press_at_utc, target_packet_id, device_secret)` | `dev/scripts/devctl/runtime/operator_physical_approval_receipt.py`; Pi button handler and dev-machine verifier | `dev/state/operator_physical_approval_receipts.jsonl` |
| `EdgeDeviceCapability` | `build_edge_device_capability(host, gpio_info)` | `dev/scripts/devctl/runtime/edge_device_capability.py`; Pi boot and `devctl edge status` | `dev/state/edge_device_capabilities.jsonl` |
| `EdgeFindingReceipt` | `build_edge_finding_receipt(finding_payload, device_signature)` | `dev/scripts/devctl/runtime/edge_finding_receipt.py`; any Pi daemon emitting findings | `dev/reports/edge_device/<device_id>/findings.jsonl`, then `PlatformFindingIngest` |

Audit receipt JSON for `WorkStreamConvergenceReceipt` lives under
`dev/reports/governance/audit_receipts/YYYY-MM-DDTHH-MMZ_workstream_convergence_<id>.json`.
`LifecycleLEDState` remains projection-only and is never typed authority.

### Extension Producers

| Extension | Parent | Added fields | Emitter |
|---|---|---|---|
| `GitMutationProofReceipt` proof binding | `dev/scripts/devctl/runtime/git_mutation_proof_receipt.py` | `code_identity_hash: str = ""`, `operation: Literal["commit", "push", "cloud_artifact"]` | extend `build_commit_git_mutation_proof_receipt()` and cloud-artifact receipt builders |
| stale proof applicability | `StaleFindingReceipt` / quality repair scheduler | `proof_receipt_id: str = ""` | extend existing stale-finding emitter |
| plan amendment metadata | `PlanIntentIngestionReceipt` | `old_plan_revision_id`, `new_plan_revision_id`, `superseded_plan_row_ids`, `per_row_prior_source_doc_sha256` | extend `append_plan_intent_ingestion_receipt()` |
| plan promotion criteria | `LifecycleReceipt` | `prior_status`, `new_status`, `criteria_met` | `devctl develop promote-plan` |
| work-stream closure aggregation | `PlanRowClosureReceipt` | `slice_id`, `plan_row_ids`, `closure_proof_refs` where supported | existing plan-row closure reducer/query view |
| session proof dogfood fields | `FeatureProofReceipt` | `session_id`, `command_invoked`, `stdout_digest`, `stderr_digest`, `json_parse_status`, `asserted_fields_present` | extend `build_feature_proof_receipt()` |
| self-referential dogfood proof | `DogfoodSelfCheckReceipt` | `feature_contract_id`, `field_path_asserted`, `field_present` | extend existing dogfood self-check emitter |
| role deployment target | existing cognitive-role assignment/config path | `RoleExecutionTarget` / `deployment_location` | `devctl edge --action toggle-role` or existing role policy writer |

### Platform Registration Pattern

For each net-new contract, follow the proven platform registration recipe:

1. Add a `dev/state/contract_registry.jsonl` row with
   `entry_kind: "artifact_schema"`, `python_owner_path`, and `fixture_path`.
2. Add the schema to
   `dev/scripts/devctl/platform/artifact_schema_rows_platform.py`.
3. Add schema fixtures under
   `dev/test_data/schema_fixtures/<Contract>/1/{valid,invalid}/`.
4. Let `check_platform_contract_closure.py` discover the registry row and fail
   if the contract is declared but not consumed.
5. Add a `SYSTEM_MAP` entry only when the contract becomes load-bearing
   authority.

## Receipt Examples

### PlanIntentIngestionReceipt Amendment Example

```json
{
  "contract_id": "PlanIntentIngestionReceipt",
  "schema_version": 3,
  "receipt_id": "plan-ingest-guardir-v48-2026-05-20",
  "source_doc_path": "dev/audits/plan_intake/2026-05-20-guardir-lifecycle-recovery-ci-proof-bridge-v4.md",
  "source_doc_sha256": "sha256:v48-source",
  "ingested_plan_row_ids": [
    "MP-GUARDIR-V4-PHASE-0-6-E-PLAN-INGESTION-S1",
    "MP-GUARDIR-V4-PHASE-0-6-A-CHANNEL-RECOVERY-S1",
    "MP-GUARDIR-V4-WORK-STREAM-A0-CODE-IDENTITY-RECEIPT-S1",
    "MP-GUARDIR-V4-WORK-STREAM-A-PUSH-ROUTING-S1",
    "MP-GUARDIR-V4-MP379-CLOUD-PROOF-REPORTING-AMENDMENT-S1",
    "MP377-P2-T02-CI-ARTIFACT-LEDGER-INGEST-S1",
    "MP-GUARDIR-V4-WORK-STREAM-E-CONNECTIVITY-DEBT-S1",
    "MP-GUARDIR-V4-WORK-STREAM-F-RASPBERRY-PI-EDGE-PACK-S1",
    "MP-GUARDIR-V4-WORK-STREAM-F-ROLE-SUBSTRATE-S1",
    "MP-GUARDIR-V4-WORK-STREAM-G-SYSTEM-CONVERGENCE-S1",
    "MP-GUARDIR-V4-G1-WORKINTAKE-LOOP-CLOSURE-S1",
    "MP-GUARDIR-V4-G2-STARTUP-SIGNALS-STITCH-S1",
    "MP-GUARDIR-V4-G3-BRIDGE-SEVERANCE-S1",
    "MP-GUARDIR-V4-G4-ACTION-PROOF-CHAIN-S1",
    "MP-GUARDIR-V4-G5-CONVERGENCE-LOOP-S1",
    "MP-GUARDIR-V4-G6-CONTRACT-BUNDLE-WIRING-S1"
  ],
  "affected_plan_row_ids": [
    "MP-NEW-P195-ASYNC-CLOUD-PROOF-S1",
    "MP-NEW-P196-AHEAD-OF-RUNTIME-PROOF-CACHE-S1"
  ],
  "old_plan_revision_id": "guardir-v4.7-2026-05-20",
  "new_plan_revision_id": "guardir-v4.8-2026-05-20",
  "superseded_plan_row_ids": [
    "MP-GUARDIR-V4-SLICE-B-PROOF-INDEX-MVP-S1"
  ],
  "per_row_prior_source_doc_sha256": {
    "MP-NEW-P195-ASYNC-CLOUD-PROOF-S1": "sha256:cached-hammock-source"
  },
  "operator_approval_actor_id": "operator:chat-session",
  "operator_approval_at_utc": "2026-05-20T00:00:00Z"
}
```

### IngestFailureReceipt Example

```json
{
  "contract_id": "IngestFailureReceipt",
  "schema_version": 1,
  "receipt_id": "ingest-failure-guardir-v48-startup-visibility",
  "plan_revision_id": "guardir-v4.8-2026-05-20",
  "source_doc_sha256_attempted": "sha256:v48-source",
  "failure_reason": "startup_visibility_timeout",
  "failure_detail": "devctl session did not expose v4.8 rows in quality_signals.plan_intake.current_rows before timeout.",
  "occurred_at_utc": "2026-05-20T00:00:00Z",
  "retry_count": 1,
  "recovery_action_required": "Fix startup_signals plan-intake loading, rerun develop ingest-plan, then rerun startup/context visibility checks.",
  "governed_exception_lifecycle_id": ""
}
```

## Ingest Failure Handling

- Canonical hash mismatch: emit
  `IngestFailureReceipt(reason=canonicalize_mismatch)` and abort.
- Startup visibility timeout: emit
  `IngestFailureReceipt(reason=startup_visibility_timeout)` and abort closure.
- Parser rejection: emit `IngestFailureReceipt(reason=parser_rejected)` with
  row and line diagnostics; do not write partial rows.
- Missing operator approval metadata for a future mutating ingest path: fail
  before mutation.
- Concurrent ingest collision: deterministic receipt ids and
  `upsert_plan_index_row()` make duplicate runs no-op.

`IngestFailureReceipt` covers ingest-only failures. The broader work-stream
failure table below covers runtime, CI, packet, bypass, and closure failures.

## Promotion

Plan-intake is not `dev/active` by default.

Future promotion action is explicit Phase 0.6.E implementation work. Do not use
an unimplemented `promote-plan` command or undeclared approval flags as current
acceptance evidence.

Promotion criteria:

- source snapshot verified
- PlanIntentIngestionReceipt carries the amendment metadata
- startup visibility proven
- no open IngestFailureReceipt
- operator approval present

Promotion emits a `LifecycleReceipt` with promotion criteria and updates
`dev/active/INDEX.md` only if the plan becomes an active owner doc.

## Lifecycle Polling Discipline

This is the architecture for the operator's required "Codex and Claude go back
and forth until nothing is left, then implementation starts" loop without adding
new receipt contracts.

Implementation work is blocked until both agents have posted `plan_ready_gate`
packets for the same plan SHA and peer awareness shows both inbox lanes were
polled within the freshness window.

Extend existing `AgentPacketAttention`
(`dev/scripts/devctl/review_channel/agent_packet_attention.py`) with:

- `peer_inbox_poll_receipt`
- `peer_inbox_poll_overdue`

Extend existing `PeerAwarenessPolicy`
(`dev/scripts/devctl/runtime/peer_awareness_policy.py`) so it applies
symmetrically to `implementer` and `reviewer` roles, not only one side.

Add `check_inbox_poll_freshness.py` as a guard over these existing peer
awareness fields. It blocks plan readiness, task handoff, and closure packets
when either peer lane is overdue.

Planning packet sequence:

1. Codex polls Claude's implementer lane:
   `python3 dev/scripts/devctl.py review-channel --action inbox --target-role implementer --limit 20 --format md`
   and records the observation in `AgentPacketAttention`.
2. Codex posts `plan_gap_review` to Claude with `target_kind=plan`,
   `target_ref=plan://MP-GUARDIR-V4-PHASE-0-6-A-CHANNEL-RECOVERY-S1`,
   `target_revision=sha256:<current-plan-sha>`, at least one `anchor_ref`, and
   `intake_ref=plan-intake://guardir-v4`.
3. Claude polls Codex's reviewer lane:
   `python3 dev/scripts/devctl.py review-channel --action inbox --target-role reviewer --limit 20 --format md`
   and records the observation in `AgentPacketAttention`.
4. Claude replies with either:
   - `plan_gap_review` carrying concrete remaining gaps, or
   - `plan_ready_gate` carrying `open_gap_count=0`, the plan SHA, and fresh
     peer-awareness evidence.
5. Codex incorporates any accepted gaps into the canonical plan and posts
   `plan_patch_review` with the new plan SHA and changed section anchors.
6. Repeat steps 1-5 until both sides post `plan_ready_gate` for the same plan
   SHA and both have fresh peer awareness.
7. Only then may Codex post the first implementation `task_started`.

Freshness rule: peer inbox observation is fresh for 15 minutes or until a newer
packet appears in the watched lane, whichever happens first. Stale peer
awareness cannot satisfy `plan_ready_gate`, `task_started`, `task_produced`, or
`review_accepted`.

If either side finds a gap after a `plan_ready_gate`, it must post a new
`plan_gap_review`; the previous agreement round is invalidated and a new
`round_id` begins. Plan patching continues until both sides agree again.

## Plan Agreement Packet Matrix

Codex -> Claude plan review:

```text
plan_gap_review{
  target_kind: plan,
  target_ref: plan://MP-GUARDIR-V4-PHASE-0-6-A-CHANNEL-RECOVERY-S1,
  target_revision: sha256:<plan_sha>,
  target_role: implementer,
  attention_urgency: blocking,
  attention_class: review,
  anchor_ref: section:<section_id>,
  intake_ref: plan-intake://guardir-v4,
  evidence_ref: peer_awareness:<attention_revision>
}
```

Claude -> Codex plan gap or readiness:

```text
plan_ready_gate{
  target_kind: plan,
  target_ref: plan://MP-GUARDIR-V4-PHASE-0-6-A-CHANNEL-RECOVERY-S1,
  target_revision: sha256:<plan_sha>,
  target_role: reviewer,
  attention_urgency: blocking,
  attention_class: decision,
  evidence_ref: peer_awareness:<attention_revision>,
  evidence_ref: plan_review:<packet_id>,
  requested_action: ready_to_implement
}
```

Codex plan patch:

```text
plan_patch_review{
  target_kind: plan,
  target_ref: plan://MP-GUARDIR-V4-PHASE-0-6-A-CHANNEL-RECOVERY-S1,
  target_revision: sha256:<new_plan_sha>,
  target_role: implementer,
  attention_urgency: blocking,
  attention_class: review,
  mutation_op: rewrite_section_note,
  anchor_ref: section:<changed_section_id>,
  intake_ref: plan-intake://guardir-v4,
  evidence_ref: peer_awareness:<attention_revision>
}
```

Codex implementation start after agreement:

```text
task_started{
  target_kind: runtime,
  target_ref: slice:<slice_id>,
  target_role: implementer,
  target_session_id: <claude_session_id>,
  attention_urgency: blocking,
  attention_class: execution,
  evidence_ref: plan_ready_gate:<codex_packet_id>,
  evidence_ref: plan_ready_gate:<claude_packet_id>,
  evidence_ref: peer_awareness:<attention_revision>
}
```

## Phase 0.6.A Continuation: Channel Recovery

This is not a new phase. It amends the active Phase 0.6.A scope and must land
before Work Stream A.0 and Work Stream A-E implementation. Work Stream F remains opt-in edge-mode
planning/execution and is non-blocking unless explicitly activated by repo
policy.

- Fix `ControlDecisionObeyedGuard` / `control_decision_consistency` paralysis.
- Restore planning-channel mutation first: `plan_gap_review`,
  `plan_patch_review`, and `plan_ready_gate` must post successfully before any
  implementation packet is allowed. Live failure evidence:
  `review-channel --action post --kind plan_patch_review` currently fails with
  `control_decision_obedience_failed`.
- Repair downstream closure mutation next: the A.0 dogfood run proves
  `task_started` can be accepted while Claude's valid `task_produced` is still
  rejected by `ControlDecisionObeyedGuard`. Treat this as
  `MP-GUARDIR-V4-PHASE-0-6-A-TASK-PRODUCED-GUARD-REPAIR-S1`, not as a reason
  to keep using offline reports.
- Repair startup-authority continuation output as a first-class architecture
  slice. Live v4.17 dogfood showed `agent-loop` returning
  `repair_startup_authority` / `startup_authority_failed` with
  `may_mutate=false`, no allowed actions, and no runnable repair command; an
  operator-scoped edit-only override did not become an active override and the
  reducer pivoted to an unrelated packet. This must close as
  `MP-GUARDIR-V4-PHASE-0-6-A-STARTUP-REPAIR-COMMAND-S1`: every startup or
  final-response blocker must resolve to exactly one typed owner, target,
  reason, and next command, or to a typed stop_anchor. It must never spin the
  same read-only command forever and must never retarget the current plan based
  only on stale active-doc or checkpoint projections.
- Restore lane-watch usability: `review-channel --action inbox --target-role
  implementer` and `--target-role reviewer` must return bounded results and
  must update `AgentPacketAttention` / `PeerAwarenessPolicy`.
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
  `pytest_node:`, `feature_proof_receipt:`, `dogfood_invocation:`,
  `closure_receipt:`, `governed_exception:`, `peer_awareness:`,
  `plan_ready_gate:`.

Startup repair command acceptance:

- `devctl session`, `develop next`, `agent-loop`, and the final-response gate
  must agree on the same blocker id, owner role, target ref, target session,
  and runnable next command for `startup_authority_failed`.
- If a repair requires mutation, the emitted command must carry a live typed
  `AgentLoopOperatorOverride`, `BypassLifecycle`, `MutationLease`, or
  role-scoped packet authority; otherwise the reducer must emit a typed
  `task_blocked` / `action_request` packet and a stop anchor.
- `--operator-override --override-scope edit-only` must either materialize in
  `AgentLoopOperatorOverride.active=true` for the scoped reducer pass or fail
  with an explicit typed reason. Silent downgrade to read-only is not closure.
- Regression tests cover the v4.17 loop: `repair_startup_authority` cannot
  return the same self-referential `agent-loop` command as the only next step
  for two consecutive passes without a changed blocker, command, or stop
  anchor.
- Next-command obedience is part of the same closure. If `develop next`,
  `agent-loop`, or the final-response gate emits a `next_required_command` or
  `next_step_command`, the emitted command must include the actor/session scope,
  target role, target session, packet id, control-decision input, executor/proxy
  authority, and lifecycle evidence required by `ControlDecisionObeyedGuard`.
  If the command cannot be made runnable, the reducer must emit a typed
  blocker packet or stop anchor instead of an impossible command. Regression
  tests cover the v4.18 failure: running the exact emitted
  `review-channel --action ingest --packet-id rev_pkt_4654 ...` command cannot
  fail `control_decision_obedience_failed` without the reducer classifying the
  command as unrunnable first.
- Final-response producer agreement is part of the same closure. The
  `DevelopmentLoopReport.continuation.next_required_command`,
  `FinalResponseGateResult.next_required_command`, `ReviewerResponseShape`, and
  `OperatorCommandWrapper` entries must select the same current semantic
  blocker, actor, role, session, target, and command. They must not mix the
  current Codex reviewer continuation with stale Claude packet-ingestion debt,
  and a Codex reviewer must not be told to run `--actor claude` commands unless
  a typed proxy authority says so.
- v4.19 closes the classification-only loophole. A field such as
  `BlockerSnapshot.repair_command_runnable` is only acceptable if all producers
  that emit startup/final/agent-loop commands set it correctly, all consumers
  refuse to execute `repair_command_runnable=false` commands, and focused
  negative tests fail on an unrunnable command that lacks owner, target,
  stop_anchor, or guard-obedience evidence. Tests that merely construct a
  defective snapshot and assert that it is defective are review evidence, not
  closure evidence.
- The first producer/consumer targets are
  `dev/scripts/devctl/runtime/control_plane_resolve.py`,
  `dev/scripts/devctl/runtime/control_plane_read_model.py`,
  `dev/scripts/devctl/runtime/agent_loop_context_builder.py`,
  `dev/scripts/devctl/runtime/agent_loop_decision_sources.py`,
  `dev/scripts/devctl/runtime/agent_loop_decision_builder.py`,
  `dev/scripts/devctl/commands/development/orchestration_models.py`,
  `dev/scripts/devctl/commands/development/orchestration_agent_loop_parse.py`,
  `dev/scripts/devctl/commands/development/final_response_gate_agent_loop.py`,
  `dev/scripts/devctl/commands/development/final_response_gate.py`, and the
  startup blocker reducer. Those callsites must share one typed action shape so
  `develop next`, `agent-loop`, session startup, and final-response gating do
  not drift.
- Read-model propagation is part of closure. `BlockerSnapshot` repair metadata
  must survive `derive_blocker_decision -> resolve_blocker_and_action ->
  ControlPlaneReadModel -> dashboard.control_plane -> AgentLoopContext ->
  AgentLoopDecision -> develop/final_response consumers`. A field that is
  produced in the reducer but dropped by any projection/read-model hop is not
  closure. Focused integration tests must fail when `agent-loop` reports
  `repair_startup_authority` while `blocker_owner`, `blocker_target`,
  `blocker_reason`, `repair_command` / `stop_anchor`, or
  `repair_command_runnable` are absent.

## Phase 0.6.A Command Envelope Normalization

Goal: converge command routing, operator wrappers, final-response output, and
proxy authority into one typed command envelope instead of scattered string
parsers or prose-only warnings.

Live trigger:

- Claude `rev_pkt_4704` suppressed `campaign.claude_next_command` from the
  Codex operator wrapper list when `current_actor=codex`, and focused tests
  proved the exact wrapper regression is no longer rendered as executable
  shell.
- A Codex read-only sidecar audit found the next architecture risk: the
  current patch duplicates `--actor` parsing in multiple consumers and does
  not yet expose a first-class non-executable peer-command status or
  proxy-positive path.

Existing substrate to reuse:

- `AttemptedActionReceipt` already models `executor_actor`, `subject_actor`,
  `proxy_execution`, and `proxy_authority_ref`.
- `ProxyAuthorityRoute` / `ProxyAuthoritySource` already model
  executor-vs-subject routing for review-channel attempted actions.
- `RoleCommandEnvelope` already models role-specific command availability and
  enforcement mode, but it must not become a second authority store.
- `AgentLoopDecision.source_latest_event_id` and `source_snapshot_id` can serve
  as command-source/proxy authority refs when a command is derived from an
  authenticated decision.

Required behavior:

- Add one shared command-envelope classifier that extracts actor, role,
  session, target role/session, packet id, source ref, proxy ref, and
  runnable/non-runnable status for command candidates.
- The shared classifier returns a typed envelope, not only a boolean or partial
  actor verdict. The envelope carries, at minimum: `executor_actor`,
  `executor_role`, `executor_session_id`, `subject_actor`, `subject_role`,
  `subject_session_id`, `target_role`, `target_session_id`, `packet_id`,
  `source_ref`, `proxy_execution`, `proxy_authority_ref`,
  `repair_command_runnable`, `classification`, `classification_reason`,
  `mutation_risk_class`, and `mutation_action_kind`.
  Fields may be empty only when the command source truly does not provide that
  dimension, and missing fields must be visible in tests/receipts rather than
  hidden by legacy defaults.
- Mutation-risk classification is part of the command envelope, not a later
  string filter. `git stash`, `git reset`, `git checkout`, `git restore`,
  `git clean`, `git apply`, shell redirection, heredoc, herestring, and `tee`
  write forms must classify as mutation attempts even when actor/proxy routing
  is otherwise valid.
- Command parsing must use a tokenized command-envelope source or safe
  shell/argument parser when possible. A substring search such as
  `text.find("--actor")` is not durable authority because it can misread
  adjacent flags and cannot extract role, session, packet, target, or source
  refs consistently.
- Classify every emitted command as exactly one of:
  `same_actor_executable`, `peer_lane_status_only`,
  `proxy_authorized_executable`, or `unrunnable_typed_blocker`.
- `develop next`, final-response gate, response shape, and
  `OperatorCommandWrapper` must consume the same classifier output. They must
  not copy private `_command_is_cross_actor_to_current` helpers.
- Peer-lane commands may remain visible as status with owner, subject actor,
  blocker reason, and target ref, but they must not render inside executable
  `sh` fences or operator wrapper objects unless a bound proxy authority ref is
  present.
- Proxy-positive behavior must be explicit: a Codex reviewer may only receive
  an executable Claude command when the envelope carries
  `executor_actor=codex`, `subject_actor=claude`, `proxy_execution=true`, and a
  valid `proxy_authority_ref` that passes the existing proxy guard.
- A non-empty `proxy_authority_ref` string is not sufficient by itself. The
  executable proxy path must validate that the ref is bound to the active
  decision/snapshot/latest-event authority for that executor/subject route, or
  return a typed peer-lane/blocker result.
- Stop Gate and Response Shape must render or serialize the same six blocker
  fields from the shared envelope/read model: `blocker_owner`,
  `blocker_target`, `blocker_reason`, `repair_command`, `stop_anchor`, and
  `repair_command_runnable`.
- `CommandEnvelopeClassification` or any successor command-envelope contract is
  a platform/runtime contract. It must be registered in `contract_registry.jsonl`
  or the platform contract row generator, have schema fixtures where this repo's
  contract policy requires them, and appear in `platform-contracts`,
  `system-map`, context-graph/contract-connectivity evidence, and generated
  closure receipts. Planned connectivity debt may explain an interim finding,
  but closure cannot leave the command-envelope contract as an unconnected
  orphan/bidirectional finding.

Acceptance tests:

- Same-actor wrapper stays executable:
  `campaign.codex_next_command` with `--actor codex` renders for Codex.
- Cross-actor wrapper is not executable:
  `campaign.claude_next_command` with `--actor claude` does not render as an
  operator `sh` wrapper for Codex without proxy authority.
- Proxy-positive wrapper becomes executable only with a valid bound
  `proxy_authority_ref`.
- Report assembly regression constructs the `rev_pkt_4703` shape and proves
  `report.operator_command_wrappers` contains no executable `--actor claude`
  command for `current_actor=codex`.
- Markdown render regression proves `develop next --actor codex` does not
  include an executable `campaign.claude_next_command` block, while same-actor
  wrappers still render.
- Stop Gate and Response Shape render/model tests prove the six blocker fields
  survive JSON and markdown projection.
- Duplicate-code guard or focused unit test fails if command actor extraction
  is reimplemented in report consumers instead of imported from the shared
  classifier.
- Full-envelope tests prove role, session, target role/session, packet id,
  source ref, executor/subject route, proxy ref, and runnable status all survive
  classification and serialization.
- Mutation-risk tests prove destructive VCS verbs and raw shell write forms are
  exposed through the same envelope fields, and a peer-owned command with
  mutation risk renders as status/blocker unless a typed lease/proxy authority
  covers it.
- Proxy-negative tests prove a cross-actor command with a non-empty but unbound
  `proxy_authority_ref` does not become executable.
- Parser edge tests prove adjacent flags such as `--actorial`, missing values,
  equals-form values, and quoted/tokenized arguments do not produce false actor
  authority.
- Platform/connectivity tests prove the command-envelope contract is registered
  or explicitly connected, and `check_contract_connectivity.py --format md`
  does not show a new unplanned orphan or bidirectional-reference finding for
  the contract.

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
  evidence_ref: governed_exception:<id>,
  evidence_ref: plan_ready_gate:<codex_packet_id>,
  evidence_ref: plan_ready_gate:<claude_packet_id>,
  evidence_ref: peer_awareness:<attention_revision>
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
  evidence_ref: peer_awareness:<attention_revision>
}
```

Codex closure:

```text
review_accepted{
  target_kind: runtime,
  target_ref: slice:<slice_id>,
  target_revision: <commit_sha>,
  evidence_ref: closure_receipt:<id>,
  evidence_ref: feature_proof_receipt:<id>,
  evidence_ref: peer_awareness:<attention_revision>
}
```

## Per-Agent Procedure

Codex per work stream:

1. Poll Claude's implementer inbox, update peer awareness, and confirm dual
   `plan_ready_gate` packets still apply to the current plan SHA.
2. Run fresh pre-work-stream `devctl session`; save
   `dev/reports/dogfood/<work_stream_id>/pre.json`.
3. Post `task_started` with both `plan_ready_gate:<packet_id>` refs and
   `peer_awareness:<attention_revision>`.
4. Poll Codex's reviewer inbox before waiting and before reviewing; do not rely
   on chat history or stale packet projections.
5. Wait for `task_produced` with resolvable evidence refs.
6. Run fresh post-work-stream `devctl session`; save
   `dev/reports/dogfood/<work_stream_id>/post.json`.
7. Verify expected JSONPath, CLI output, or grep pattern appears.
8. Poll Claude's implementer inbox again, then post `review_accepted`; emit
   matching closure receipts.

Claude per work stream:

1. Poll Codex's reviewer inbox, update peer awareness, and read the latest
   plan-gap, plan-patch, or task packet before acting.
2. Read `task_started`; verify `target_session_id` matches Claude session and
   that both `plan_ready_gate:<packet_id>` refs are current for the plan SHA.
3. Implement only assigned scope.
4. Run each pytest node via `devctl test-python`.
5. Run each new CLI; capture separate SHA256 digests for stdout and stderr.
6. Emit `FeatureProofReceipt` with session/CLI dogfood fields and
   `DogfoodSelfCheckReceipt` evidence when startup behavior changes.
7. Poll Codex's reviewer inbox again, then post `task_produced`.

## Phase 0.6.E Current Plan Authority Singularity

Goal: remove the multi-source-of-truth failure before more v4 implementation
work starts. The GuardIR v4 markdown file is the canonical intake source, but
implementation authority comes from ingested typed `PlanRow` state plus its
`PlanSourceSnapshot` and `PlanIntentIngestionReceipt` evidence. Chat, generated
boot cards, active docs, dashboards, bridge text, and un-ingested markdown are
provenance or projections; they are not current work-selection authority.

Live failure:

- Agents treated the v4 plan-intake markdown, active owner docs, generated
  `AGENTS.md`, chat instructions, and typed state as competing authority
  sources.
- Live packet coordination created the same risk in a smaller form: packet
  bodies and offline findings contained valid architecture corrections, but
  those corrections must be promoted through plan amendment and ingestion before
  they can select implementation work. A `finding`, `task_progress`,
  `task_blocked`, or `task_produced` packet is typed lifecycle evidence, not a
  second canonical plan.
- The read-only audit found that `MP-GUARDIR-V4-*` rows listed in this intake
  file must be present in `dev/state/plan_index.jsonl` and startup-visible
  before they can authorize implementation selection.
- Startup/session authority is currently degraded: `session` can hang inside
  review-channel status, and startup fallback can stop on dirty worktree
  checkpoint state. These failures must be typed blockers, not reasons to pick
  work from a lower-authority surface.
- A v4.34 `devctl session --role reviewer --include-review-status always
  --format json` dogfood run hung for more than one minute while a child
  `session-resume --role reviewer --format json` process ran. A concurrent
  sidecar observed the same class of hang in `review_state_refresh ->
  push_state -> git status`. Startup/session/final-gate dependency refreshes
  must be time-bounded typed inputs, not unbounded blockers that require manual
  process cleanup or operator memory.
- A live `devctl session --role reviewer` run routed `active_target_path` to
  `dev/active/ai_governance_platform.md` and checkpoint/dirty-worktree state
  while the operator and typed packets were actively iterating this canonical
  GuardIR plan. That reducer mismatch is a source-of-truth bug: startup
  blockers may stop implementation, but they must not silently replace the
  current plan target.
- A later `devctl session --role observer --include-review-status always
  --format json` and `review-channel --action status --terminal none
  --format json` run during the `rev_pkt_4686` / `rev_pkt_4687` handoff again
  reported `safe_to_continue=false`, `required_action=cut_checkpoint`, and
  `dirty_path_budget_exceeded` while `allowed_actions` still included
  review-channel post actions such as `review-channel.post_task_progress`.
  The same snapshot showed Codex reviewer grant fields marked false and an
  unrelated `active_target_path=dev/active/ai_governance_platform.md`. That is
  not a request for Codex to checkpoint or mutate Claude's dirty worktree; it is
  a reducer consistency bug between `CheckpointBudgetShape`, `AuthoritySnapshot`,
  current-plan routing, and review-only packet authority.
- A fresh `check_contract_connectivity.py --format md` run found no unplanned
  new orphan/stranded contract debt, but it did report the planned new duplicate
  shape `AgentLoopDecision` <-> `BlockerSnapshot` over blocker fields such as
  `top_blocker`, `blocker_owner`, `blocker_reason`, `blocker_target`,
  `repair_command`, `repair_command_runnable`, and `stop_anchor`. This confirms
  the blocker-metadata chain must be one composed contract path, not copied
  shapes that drift independently.
- A v4.35 `check_platform_contract_closure.py --format md` run failed
  `runtime_contract::ControlPlaneReadModel` because runtime dataclass fields
  `blocker_owner`, `blocker_reason`, `blocker_target`, `repair_command`,
  `repair_command_runnable`, and `stop_anchor` are not yet represented in the
  platform contract row. This is the same blocker-metadata composition debt: do
  not remove fields to make the check green; wire the platform row and parity
  route so `ControlPlaneReadModel` remains a projection of `BlockerSnapshot`.

Required invariant:

- Exactly one current-plan authority resolver exists for the repo. It resolves
  current work from typed `PlanRow` rows first, then typed ingestion receipts
  and source snapshots. Intake markdown is a source candidate until ingested;
  active docs and generated surfaces are citations/projections unless bound to
  an existing typed row.
- `CurrentPlanAuthorityResolver` is a read adapter over `PlanRow`,
  `PlanIntentIngestionReceipt`, `PlanSourceSnapshot`, `PlanRegistry`, and
  `PlanTargetRef` state. It is not a new JSONL store, not a shadow active-plan
  index, and not a bridge/dashboard heuristic.
- If a plan-intake file claims canonicality but its rows are not present in
  typed state and visible through startup quality signals, the resolver returns
  `not_current_authority` and allows only ingestion, amendment, review, and
  recovery work for that plan.
- Active owner docs are owner-doc/projection surfaces unless backed by
  `PlanRegistry` / `PlanRow` authority. `dev/active/INDEX.md` may list and
  navigate owner docs, but its registry prose cannot select implementation work
  without typed row backing.
- Checkpoint budget and dirty-worktree authority are mutation/closure gates, not
  current-plan selectors. They may suspend edits, staging, commit, push,
  convergence closure, or implementation `task_started`, but they cannot retarget
  the active plan away from the typed plan row under review.
- Review-only coordination packets are lifecycle writes, so they still require
  typed authority, source-session proof, and guard obedience. When checkpoint
  budget blocks implementation but a scoped reviewer packet is allowed, the
  authority snapshot, capability grants, and `AgentLoopDecision` must agree on
  that narrow coordination lane. If they disagree, the controller emits a typed
  `authority_snapshot_inconsistent` / `checkpoint_coordination_conflict` blocker
  with owner, target, and repair row instead of raw stop prose.
- Packets are event and evidence authority, not plan authority. A packet can
  request a plan change, cite a defect, or carry proof for a lifecycle edge, but
  durable work selection changes only after the packet is reduced into the
  canonical plan graph, lifecycle state, or finding-review state with explicit
  provenance. Until then, packet bodies remain pending evidence bound to their
  source session, target ref, plan revision, and parent packet.
- There is one plan graph. `PlanRow`, `PlanSourceSnapshot`,
  `PlanIntentIngestionReceipt`, lifecycle receipts, and registered read models
  may reference packet ids as provenance, but packet ids, packet body markdown,
  offline finding files, bridge text, dashboards, or chat excerpts cannot own a
  competing implementation plan.
- `BlockerSnapshot` is the canonical blocker metadata contract. `AgentLoopDecision`,
  `ControlPlaneReadModel`, `/develop`, final-response gates, dashboards, and
  mobile/status views may project the same fields, but they must consume or
  compose the canonical snapshot and prove field-route parity. They must not own
  duplicate blocker state.
- Startup, session, review-state, push-state, dashboard, and final-response
  refreshes are bounded dependency calls. If a child command or refresh stage
  exceeds its budget, the caller emits a typed
  `startup_surface_dependency_timeout` / `coordination_dependency_timeout`
  blocker with command, dependency name, actor, role, session, target row when
  known, elapsed time, and repair row. It must not wait forever, silently skip the
  dependency, retarget the current plan, or ask the reviewer to mutate.

Deliverables:

- Implement or connect a `CurrentPlanAuthorityResolver` through existing
  `PlanRow`, `IngestionProvenance`, `PlanSourceSnapshot`, and
  `PlanIntentIngestionReceipt` state. Do not create a parallel plan tracker.
- Resolver output must include `row_id`, `status`, `plan_revision_id`,
  `source_doc_path`, `source_hash`, `superseded_by_row`, `authority_source`,
  and `startup_visible`.
- `startup-context`, `session`, `develop next`, `context-graph`, dashboard,
  review-channel packet selection, and final-response gate consumers must use
  the same resolver instead of ranking markdown, generated surfaces, bridge
  state, active docs, and chat independently.
- Packet selection must call a shared current-plan-aware selector. Queue order,
  "latest finding" heuristics, startup inbox count summaries, peer attention
  relevance scores, and final-gate agent-loop fields may project the selector's
  answer; they must not each implement a separate current-work ranking.
- Packet currency is supersession-aware. Exact `target_revision == latest plan
  SHA` is sufficient for currentness, but exact mismatch is not automatically
  stale when the packet targets the same row/lane and the later plan revision
  only amends or sharpens that row. The selector must resolve row id, target ref,
  plan source hash, ingestion receipt, supersession/amendment lineage, and
  packet post time before deciding whether an older packet remains current,
  requires a refreshed packet, or is truly stale.
- Packet-to-plan promotion must be explicit. When a packet changes scope,
  ordering, role authority, or acceptance criteria, the next current-state
  transition is `PlanAmendmentReceipt` / plan-intake edit / `develop ingest-plan`
  or an equivalent typed reducer over existing plan state, followed by a
  `PlanIntentIngestionReceipt`. Reducers may then surface the updated plan row
  and cite the packet as evidence; they must not execute directly from packet
  prose.
- Active-doc citations are admissible only when tied to an existing row id in
  `dev/state/plan_index.jsonl` or a pending typed ingestion receipt for this
  plan.
- `session`, `startup-context`, `develop next`, and final-response gate output
  must distinguish `startup_blocked`, `checkpoint_required`, and
  `current_plan_target`. A startup blocker may suspend work, but it cannot
  retarget active work away from the selected typed plan row.
- `CheckpointBudgetShape` must feed the same typed decision chain as
  `BlockerSnapshot` and `AuthoritySnapshot`: checkpoint-required state blocks
  mutation/closure lanes and supplies a repair owner, but scoped review-only
  packet posting remains governed by the review-feedback lane from Phase 0.6.A.
- Add bounded watchdogs around `session`, `startup-context`, `session-resume`,
  review-state refresh, push-state refresh, dashboard/status refresh, and
  final-response child invocations. The watchdog result is typed evidence and
  preserves the coordination lane when a nonessential projection refresh hangs.
- v4 rows named in "Rows To Ingest From This Plan" must be present in typed
  state and visible in `quality_signals.plan_intake.current_rows` before any v4
  work-stream implementation packet is selected.
- Acceptance uses the current `develop ingest-plan` CLI shape unless Phase
  0.6.E explicitly implements new options. Help-output tests must fail if this
  plan names required flags that the parser does not expose.
- The implementation must reuse existing duplicate/parallel-system guards:
  `check_contract_connectivity.py`, `check_typed_namespace_composition.py`,
  `check_contract_registry_composite_key_uniqueness.py`,
  `check_plan_row_contract_refs_resolve.py`,
  `check_bridge_projection_only.py`, `check_no_projection_proof_misuse.py`,
  `check_state_store_authority.py`, `check_review_surface_consistency.py`,
  `check_active_plan_sync.py`, `check_instruction_surface_sync.py`, and
  `check_multi_agent_sync.py`.
- New contract or check wiring must register through existing
  `contract_registry.jsonl`, `SystemMapSnapshot`, and
  `ConnectivityRegistrySnapshot` surfaces. The read-only audit's
  `system-map --format md` run observed the existing connectivity registry
  rather than finding a need for a new duplicate-system auditor.
- Existing implementation anchors to connect first:
  `dev/scripts/devctl/runtime/master_plan_contract.py`,
  `dev/scripts/devctl/runtime/plan_index_authority.py`,
  `dev/scripts/devctl/runtime/plan_intent_ingestion.py`,
  `dev/scripts/devctl/review_channel/packet_contract.py`,
  `dev/scripts/devctl/commands/review_channel/event_post_action.py`,
  `dev/scripts/devctl/review_channel/packet_creation_binding_plan.py`,
  `dev/scripts/devctl/review_channel/packet_debt_remediation_contracts.py`,
  `dev/scripts/devctl/runtime/development_packet_ingest_decision.py`,
  `dev/scripts/devctl/commands/development/next_slice.py`,
  `dev/scripts/devctl/runtime/development_scaling_defaults.py`,
  `dev/scripts/devctl/runtime/agent_dispatch_router.py`,
  `dev/scripts/devctl/platform/planning_ir.py`,
  `dev/scripts/devctl/platform/planning_ir_sources.py`, and
  `dev/scripts/devctl/runtime/control_plane_read_model.py`.
- Existing guard anchors to reuse:
  `check_packet_pkt_bind_completeness`,
  `probe_packet_carry_forward_debt`,
  `check_plan_index_commit_continuity.py`,
  `check_systemmap_covers_contract_registry.py`,
  `check_contract_connectivity.py`,
  `check_duplicate_types.py`, and `check_platform_contract_closure.py`.
  The packet-to-plan rule closes only by wiring through these checks or their
  registered successors, not by adding a new plan store, packet ledger, or docs
  authority surface.

Closure:

- One focused test proves that un-ingested v4 markdown rows cannot authorize
  implementation while ingestion/amendment work remains allowed.
- One parity test proves startup, `develop next`, context graph, dashboard, and
  review-channel selection report the same current-plan answer for the same
  target row.
- One selector-parity test proves review-channel inbox, `develop next`,
  startup packet inbox, peer attention window, watcher lease, agent-loop, and
  final-response gate select the same current plan-bound packet for the same
  actor/role/session lane or report the same typed stale-backlog conflict.
- One supersession test proves a packet posted against v4.33 for the same target
  row is not blindly demoted after v4.35/v4.36 plan ingestion unless the later
  plan revision supersedes its requested action or a fresh packet is required and
  emitted as a typed refresh blocker.
- One packet-promotion test proves a reviewer `finding` that changes plan scope
  remains non-executable evidence until the amendment is ingested into
  `PlanRow` state with a receipt; after ingestion, the selected work cites the
  packet id as provenance instead of reading authority from the packet body.
- One reducer test proves checkpoint/dirty-worktree/startup failures suspend
  implementation without changing the selected current-plan target to an
  unrelated active owner doc.
- One reducer test proves checkpoint/dirty-worktree state can block mutation and
  convergence while still returning an explicit, guard-obedient scoped
  review-only packet lane when peer coordination must continue; if grant fields
  and allowed actions disagree, the test must see a typed recoverable blocker.
- One connectivity/parity test proves `AgentLoopDecision` blocker fields are
  sourced from or parity-checked against `BlockerSnapshot`, closing the planned
  `AgentLoopDecision` <-> `BlockerSnapshot` duplicate reported by
  `check_contract_connectivity.py --format md`.
- `check_platform_contract_closure.py --format md` no longer reports
  `ControlPlaneReadModel` blocker-field drift; the added fields are present in
  the platform row and field-route parity proves they compose with
  `BlockerSnapshot`.
- One watchdog regression simulates a hanging review-state / push-state refresh
  and proves `session` and final-response gate return a typed dependency-timeout
  blocker in bounded time while preserving the current plan target and any
  allowed scoped review-only packet lane.
- `develop ingest-plan --help` parity proves every required Phase 0.6.E CLI
  option is implemented, or else the plan explicitly marks it as future
  implementation work rather than current acceptance.
- `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before further v4
  work-stream implementation starts.

## Phase 0.6.E Instruction Surface Usability And Command Routing

Goal: make generated AI-facing projections useful enough that agents can find
the typed system without relying on chat, stale memory, or random active docs.
`AGENTS.md`, `CLAUDE.md`, slash command templates, platform guides, and
`SYSTEM_MAP.md` remain projection/read-model surfaces, but they must explain
which typed command to run, when to run it, and how to route back to authority.

Live failure:

- The current generated boot cards correctly warn that projections are not
  authority, but they barely teach an agent which `devctl` command discovers
  work, which command posts packets, which command reads system topology, which
  checks detect duplicate systems, or which surface is safe for a given role.
- Both current generated boot cards still render fallback examples such as
  `--role observer` / `--actor agent`, because the renderer falls back to a
  generic surface role instead of consuming the live role envelope. That is useful
  as first-boot discovery only; it is not acceptable current-session guidance for
  Codex reviewer/orchestrator or Claude implementer lanes.
- The repo has hundreds of commands, checks, contracts, and active docs. A thin
  projection that only says "typed state wins" leaves agents to infer from chat
  or whichever owner doc they most recently read.
- This contributed to the repeated failures where the current GuardIR plan,
  active docs, generated boot cards, dashboard state, and chat all appeared to
  be competing sources of truth.
- The v4.34 operator correction repeated the same symptom in practical form:
  Codex had to be reminded to keep working with Claude, use read-only sidecars,
  amend the canonical plan, post typed findings, and avoid implementation edits.
  A boot card that does not make that loop concrete is not usable enough even if
  it correctly says "projection-only."
- v4.35 guard checks confirmed the projection drift is live, not theoretical:
  `check_systemmap_covers_contract_registry.py --format md` and
  `check_instruction_surface_sync.py --format md` failed because the managed
  `SYSTEM_MAP.md` generated block is stale while the boot cards themselves still
  report in sync. Instruction-surface closure must treat system-map drift as a
  role/navigation regression, not as a harmless docs detail.
- Platform-guide work and VoiceTerm cleanup are connected: portable GuardIR
  docs should describe the governance/runtime system through `ProjectGovernance`
  and `RepoPack`, while VoiceTerm-specific paths, names, and defaults stay in an
  adopter/client pack or explicit adopter debt.

Required invariant:

- Generated instruction surfaces are command routers and typed-authority
  locators. They may show examples and "when to use" tables, but every command
  family must point back to the typed contract, plan row, guard, or repo-policy
  source that owns the behavior.
- `AGENTS.md` and `CLAUDE.md` must be role-aware projections. A reviewer,
  implementer, observer, dashboard, sidecar researcher, and watcher should see
  the first commands, allowed actions, blocked actions, packet lane, and
  escalation path relevant to that role without reading the whole repo.
- Provider/session-specific boot-card loops must replace generic examples when a
  typed role envelope is available. `--role observer` / `--actor agent` examples
  are allowed only as clearly labeled fallback discovery commands.
- Command discovery must come from existing parser/help/catalog inputs such as
  `devctl --help`, command registries, `check-router`, `system-map`,
  `context-graph`, `platform-contracts`, `OperatorCommandWrapper`, and
  repo-pack policy. Do not hardcode a second command registry into markdown.
- Projection quality is testable. A generated surface that omits current-plan
  discovery, packet lifecycle commands, system-map/context-graph navigation,
  duplicate/connectivity checks, instruction-surface sync checks, and
  projection-only warnings is stale or incomplete.
- VoiceTerm is adopter context. Portable GuardIR instruction surfaces should
  use GuardIR/governance terms first and route VoiceTerm-specific instructions
  through `ProjectGovernance`, `RepoPack`, `RepoPathConfig`,
  `SurfaceOwnershipMap`, `ExtensionBundle`, or explicit adopter-pack debt.

Deliverables:

- Extend the `InstructionBootCard` / `RoleInstructionCard` renderer inputs so
  `AGENTS.md` and `CLAUDE.md` include a bounded command router:
  startup/session, current-plan selection, review-channel read/post, develop
  reducer, system-map/system-picture/context-graph, platform-contracts,
  duplicate/connectivity checks, generated-surface sync, plan ingestion, test
  routing, and final gate.
- Render role-specific "when to use this" guidance for reviewer,
  implementer, observer, dashboard, sidecar researcher, and watcher roles from
  typed collaboration-mode and repo-pack policy.
- Render provider/session-specific loops for current Codex and Claude sessions:
  Codex sees reviewer/orchestrator/architect/plan-steward actions and blocked
  implementation writes; Claude sees implementer actions, verification duties,
  and packet response rules. These loops are generated projections over typed
  inputs, not hardcoded provider authority.
- Add platform-guide or `dev/guides` inputs that explain GuardIR as the
  portable governance system, with VoiceTerm documented as one adopter/client.
- Add sync/coverage checks that fail when generated boot cards omit required
  command families or point at prose authority without a typed owner.
- Include `check_guide_contract_sync.py`, `check_instruction_surface_sync.py`,
  `check_systemmap_covers_contract_registry.py`, `docs-check --strict-tooling`,
  and the relevant `render-surfaces --surface agents_boot_card --surface
  claude_boot_card --surface system_map_index` proof in the acceptance bundle.
- Wire command examples through existing `OperatorCommandWrapper` output when a
  reducer already emits a wrapped command block.
- Keep generated surfaces concise enough for startup, but link to typed command
  and guide surfaces for deeper navigation.
- Generated role loops must include stale-evidence handling: completed sidecar
  summaries, old agent-mind projections, active docs, and chat excerpts may be
  cited as evidence only with plan revision / source hash / packet binding. They
  cannot replace a fresh current-plan resolver answer.

Closure:

- `python3 dev/scripts/devctl.py render-surfaces --write --format md` produces
  `AGENTS.md`, `CLAUDE.md`, and slash/template outputs with the new command
  router sections.
- `check_instruction_surface_sync.py --format md` and
  `docs-check --strict-tooling --format json` pass.
- `check_agents_contract` / instruction-surface coverage validates both
  `AGENTS.md` and `CLAUDE.md`, role-specific loops, read/write command
  classification, final-gate continuation rules, and reviewer mutation denial.
- A focused instruction-surface coverage test proves all required command
  families are present in the renderer inputs and generated surfaces.
- A projection-only test proves the new guidance cannot grant mutation,
  packet-disposition, staging, commit, push, or bypass authority.
- A role-loop usability test proves Codex sees the reviewer/orchestrator/plan
  steward loop and Claude sees the implementer loop from generated surfaces
  without relying on operator chat.
- A guide/navigation test proves VoiceTerm-specific strings are either adopter
  context or routed through repo-pack/project-governance configuration.
- `render-surfaces --surface agents_boot_card --surface claude_boot_card
  --surface system_map_index --format md` is clean; `system_map_index` drift is
  not allowed to hide role/command guidance regressions while boot cards appear
  in sync.
- `check_guide_contract_sync.py --format md` and
  `check_systemmap_covers_contract_registry.py --format md` pass or emit typed
  planned debt owned by the relevant v4 row.
- `check_instruction_surface_sync.py --format md` passes with
  `system_map_index` in sync, not merely `AGENTS.md` and `CLAUDE.md` in sync.
- `MP-GUARDIR-V4-PHASE-0-6-E-INSTRUCTION-SURFACE-USABILITY-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before GuardIR v4
  claims portable multi-agent usability.

## Phase 0.6.E Role Instruction Contract Connectivity

Goal: make role guidance a connected projection of typed authority instead of
another local docs island. The existing instruction and role primitives must be
wired into the same contract-connectivity, system-map, command-catalog, and
guard chain that decides what an agent may do.

Live failure:

- The multi-agent read-only audit found that `InstructionBootCard` renders
  `AGENTS.md` / `CLAUDE.md`, but `context-graph --query InstructionBootCard`
  did not expose it as a connected role-guidance contract and
  contract-connectivity can still classify instruction/role cards as orphaned.
- `RoleInstructionCard`, `RoleGuard`, `CustomRoleDefinition`, and
  `RoleCreationAction` exist, but generated boot-card rendering and
  enforcement chokepoints do not yet make them one visible path from typed
  role assignment to command guidance to guard enforcement.
- Role identity is split across role cards, collaboration topology, role
  profiles, review-channel cascade maps, dispatch router session nodes, and
  session-route aliases. Provider defaults such as `codex=reviewer` and
  `claude=implementer` are useful startup hints, but they keep leaking into
  decisions as if they were typed role authority.
- Command authority is spread across CLI parser registries, `SystemCatalog`,
  boot-card hardcoded examples, bootstrap command metadata, and slash catalogs.
  That spread makes it easy for generated projections to show stale or
  over-broad commands, including read/write ambiguity around review-channel
  packet posts.

Required invariant:

- There is one role-authority flow:
  `ActorAuthorityState` / `CapabilityGrantState` / typed session role ->
  `CollaborationModeTopology` -> `AgentDispatchRouter` ->
  `AgentLoopDecision` -> `ControlDecisionObeyedGuard` / mutation lease guards.
  `InstructionBootCard`, `RoleInstructionCard`, `RoleGuard`, `SystemCatalog`,
  `AGENTS.md`, `CLAUDE.md`, slash templates, dashboards, and bridge/status text
  may only project or validate that flow.
- `InstructionBootCard` and role customization contracts are registered and
  connected through `contract_registry.jsonl`, `SystemMapSnapshot`,
  `ConnectivityRegistrySnapshot`, and context-graph edges. A generated surface
  cannot be considered usable if its source contract is invisible to these
  discovery and duplicate checks.
- Role-specific command examples come from `SystemCatalog`, argparse/parser
  metadata, command classifications, `OperatorCommandWrapper`, and repo-policy
  typed inputs. Do not maintain a parallel markdown command registry.
- Unknown provider, missing role state, missing scoped mutation row, or
  provider-default-only role assignment fails closed for mutation, closure,
  staging, commit, push, bypass, and actor-proxy authority. It may still allow
  explicitly scoped read-only observation when the read authority path is
  present.
- Review-channel command classification distinguishes read-only reads
  (`show`, `inbox`, `status`, history) from lifecycle writes (`post`,
  disposition/ingest/recovery actions) so boot cards and guards do not present
  packet mutation as a generic read-only command family.

Deliverables:

- Register or reconnect `InstructionBootCard`, `RoleInstructionCard`,
  `RoleGuard`, `CustomRoleDefinition`, `RoleCreationAction`, and
  role-command-envelope contracts so `platform-contracts`, `system-map`,
  `context-graph`, and contract-connectivity checks can find their producer,
  consumer, and projection edges.
- Remove hardcoded boot-card role examples that render every surface as
  `--role observer` / `--actor agent` when a typed role envelope is available.
  Examples must derive from the resolved role/session surface or clearly label
  themselves as fallback discovery commands.
- Ensure `InstructionBootCard` itself is registered and discoverable. A
  renderer-owned contract that produces `AGENTS.md` / `CLAUDE.md` but is absent
  from `contract_registry.jsonl`, `context-graph`, or `SYSTEM_MAP.md` is not
  acceptable closure.
- Feed generated boot-card role loops from the role-authority flow and command
  catalog inputs instead of hardcoded provider assumptions or free-form prose.
- Add role connectivity checks proving boot-card renderer inputs cite typed
  roles, capabilities, command owners, command read/write class, and projection
  boundaries.
- Add fail-closed role-default tests for unknown provider, missing role,
  provider-default-only assignment, and missing mutation lease rows.
- Add a command-classification test proving review-channel read commands and
  packet-write commands are separately surfaced and separately guarded.

Closure:

- `context-graph --query InstructionBootCard --format md`,
  `platform-contracts --format md`, and
  `check_contract_connectivity.py --format md` show instruction/role contracts
  connected or explicitly classified `internal_only` with owner and consumer
  rationale.
- `check_platform_contract_closure.py --format md`,
  `check_contract_connectivity.py --format md`, and
  `check_duplicate_types.py --format md` show no unplanned instruction/role
  duplicate, orphan, or stranded-consumer debt.
- `check_contract_connectivity.py --format md` may report `RoleInstructionCard`
  and `RoleGuard` as planned disconnected debt until this row closes, but it must
  remain `ok` with no unplanned instruction/role debt. Closure requires converting
  that planned debt into connected producer/consumer edges or explicit
  `internal_only` rationale.
- `SYSTEM_MAP.md` shows real consumers for `RoleInstructionCard` /
  `InstructionBootCard` through renderer or guard chokepoints, not `none`, and
  context-graph can discover those contracts by name.
- `render-surfaces --write --format md` produces boot cards whose role loops
  come from typed role and command-catalog inputs, and
  `check_instruction_surface_sync.py --format md` passes.
- Focused tests prove provider defaults cannot grant mutation, closure,
  staging, commit, push, bypass, or actor-proxy authority.
- Focused tests prove review-channel read and write commands carry distinct
  authority classifications through boot cards, command catalog, and guards.
- `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-INSTRUCTION-CONNECTIVITY-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before the system can
  claim agents know what to run without operator reminders.

## Phase 0.6.E Role Boot And Continuation Discipline

Goal: stop relying on the operator to remind agents what role they occupy and
whether they should keep working. Startup, `develop next`, final-response
gates, generated boot cards, and packet/status surfaces must all expose the
same typed role envelope and continuation state.

Live failure:

- The operator repeatedly had to restate that Codex is not only a narrow code
  reviewer. In this plan Codex is the reviewer/orchestrator/architect/plan
  steward: it polls packet lanes, reads and amends the canonical plan, runs
  system-map and duplicate/connectivity checks, uses read-only sidecars for
  bounded audits, reviews Claude's implementation packets, and posts the next
  typed slice. Claude owns implementation unless typed authority transfers or
  partitions the write set.
- Generated projections and final gates did not make that role envelope
  obvious enough. The system kept presenting stale work, old packet debt, or
  generic reviewer posture instead of the current typed collaboration loop.
- Claude scheduled a wake / stop-style anchor after posting progress even
  though the live packet lifecycle still required Codex review and another
  handoff. Codex also stopped after a final-gate denial instead of keeping the
  plan/review loop moving.
- v4.34 dogfood showed another variant: completed sidecar outputs from older
  revisions were easy to confuse with fresh multi-agent audit authority, and the
  main reviewer loop still depended on the operator reminding Codex to keep
  communicating with Claude. Sidecar fanout must be represented as bounded
  auxiliary evidence with route-back requirements, not as a replacement main
  actor or a reason to stop.

Required invariant:

- Every live agent session has a resolved `RoleBootEnvelope` or equivalent view
  over existing `CollaborationSession`, `SessionPosture`, `ActorAuthorityState`,
  `CapabilityGrantState`, `AgentDispatchRouter`, `AgentLoopDecision`,
  `SessionTerminationPolicy`, `TaskCompleteDecision`, and
  `AgentSessionContinuation` state. This can be a read model, not a new
  authority store.
- The role envelope includes: actor id, provider, role, session id, current
  plan row/target, peer lane, mutation owner, verification owner, watcher
  owner, allowed actions, blocked actions, current packet goal, stop policy,
  continuation anchor, stop anchor, and next typed command.
- `RoleBootEnvelope` is the named read-model contract for this view. Compatibility
  adapters may project it, but startup, `develop next`, final gate, `agent-loop`,
  generated boot cards, and status surfaces must consume the same envelope shape
  rather than ad hoc role fields.
- When sidecars or watcher roles are active, the envelope also includes
  delegated role, delegation id, source plan revision/hash, read/write scope,
  stale-output policy, and the route by which their evidence returns to the main
  actor's packet/plan loop.
- Generated projections may say "Codex reviewer" or "Claude implementer" only
  as the current resolved assignment for this repo/session. Provider defaults
  remain compatibility hints and never grant mutation, closure, staging,
  commit, push, bypass, or actor-proxy authority.
- A stop anchor, scheduled wake, `TASK_COMPLETE`, or "nothing more to do" text
  is invalid while a continuation anchor, current packet goal, pending peer
  packet, or active work-stream lifecycle requires action. The controller must
  either continue, post a typed progress/blocked packet, or emit a typed
  conflict such as `stop_anchor_conflicts_with_live_lifecycle`.
- Final-response gates must never demand that one actor run another actor's
  command unless an explicit typed proxy authority exists. A Codex reviewer
  cannot be told to run `--actor claude`; Claude cannot be told to close Codex's
  review lane.

Deliverables:

- Build or connect a role boot read model from existing typed role/session
  surfaces. Do not create a parallel role registry.
- Register `RoleBootEnvelope` or an explicitly equivalent contract through the
  platform/contract registry, with producer and consumer edges for startup,
  develop reducers, final gate, `agent-loop`, generated boot-card rendering, and
  status projections.
- Include the role envelope in `session`, `startup-context`, `develop next`,
  final-response gate output, `agent-loop`, `AGENTS.md`, `CLAUDE.md`, and
  system/status projections.
- Add a continuation-vs-stop conflict check that consumes
  `SessionTerminationPolicy`, `TaskCompleteDecision`, continuation anchors,
  stop anchors, packet inbox state, and current work-stream lifecycle state.
- Add role-loop instructions to generated surfaces: Codex reviewer/orchestrator
  loop, Claude implementer loop, observer/dashboard loop, sidecar researcher
  loop, and watcher loop. Each loop lists what to run, what not to run, and
  what packet to post next.
- Add a stale-sidecar evidence check: a completed helper summary from a previous
  plan revision may inform the main actor, but the role boot surface must require
  a fresh current-plan check before treating it as current guidance.
- Connect stop/wake anchor behavior to packet lifecycle state so a wake timer
  is a scheduling projection, not permission to stop while work remains.

Closure:

- Focused tests prove startup/session/final-gate surfaces render the same role
  envelope for Codex and Claude on the same typed snapshot.
- `session --role reviewer`, `session --role implementer`, `develop next --actor
  codex --enforce-final-response-gate`, and `develop next --actor claude
  --enforce-final-response-gate` expose the same `RoleBootEnvelope` fields for
  current plan target, peer lane, allowed/blocked actions, packet goal, mutation
  owner, and stop policy.
- Focused tests prove generated boot cards include the role-specific command
  loop and cannot grant backend authority.
- Focused tests prove a live packet goal plus continuation anchor rejects
  `TASK_COMPLETE`, stop anchors, or wake-only parking unless a typed
  `SessionTerminationPolicy` / `TaskCompleteDecision` authorizes stop.
- Focused tests prove stale sidecar output cannot overwrite the main actor's
  current role envelope, packet lane, current plan target, or continuation
  decision.
- Focused tests prove final gates reject cross-actor commands such as Codex
  being told to run `--actor claude` without proxy authority.
- Final-gate actor consistency tests prove `develop next --actor codex
  --enforce-final-response-gate` cannot emit a Claude-owned `--actor claude`
  command, and the Claude equivalent cannot emit a Codex-owned command, unless a
  typed proxy authority ref is present and validated by command-envelope logic.
- `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-BOOT-CONTINUATION-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before the system can
  claim agents know their roles without operator reminders.

## Phase 0.6.A Role-Scoped Mutation Lease

Goal: close the reviewer/implementer authority leak discovered during live
dogfood. A reviewer session must not be able to mutate implementation files
while an implementer-owned `task_started` lane is live merely because the local
tooling exposes file-edit commands.

Live failure:

- Codex, acting as reviewer/orchestrator, was able to start editing
  `dev/scripts/devctl/runtime/review_channel_post_actions.py` while Claude
  owned the Phase 0.6.A guard-repair implementation lane from `rev_pkt_4652`.
- That reviewer edit was reverted, but the important failure is architectural:
  tool access was not checked against role, live task ownership, target
  session, and write-set authority before mutation.
- This composes with the A.0 / Phase 0.6.A packets `rev_pkt_4651` through
  `rev_pkt_4654`, the prior role-flip/control-decision finding
  `PKT-BIND-REV-PKT-4485`, and MP-377 role-matrix / lifecycle-signoff rows.
- The multi-agent role audit found that role assignment is still partly
  derived from session records, reviewer mode, remote-control fallback, and
  provider defaults such as "codex reviewer / claude implementer." Those
  defaults are navigation hints only; durable role authority must be explicit
  typed state.

Required invariant:

- A live implementer `task_started` creates or references exactly one
  session-bound live-tree `MutationLease` for its target refs and claimed write
  set. While that lease is active, reviewer sessions are read-only for that
  write set.
- Reviewer identity, Codex provider identity, chat direction, generated boot
  cards, dashboards, or available tools such as `apply_patch` never grant
  mutation authority.
- A reviewer can mutate implementation files only if typed state explicitly
  transfers the lease, closes or voids the implementer lease, or grants a
  disjoint write-set lease with non-overlap proof. Raw bypass and operator
  prose are not sufficient.
- Whole-worktree VCS state changes require authority even when the command does
  not name an individual file path. `git stash`, `git stash pop/apply`,
  `git reset`, `git checkout`, `git restore`, `git clean`, and similar commands
  can hide, rewrite, remove, or replay another session's dirty work. They are
  mutation attempts against the affected worktree scope and must be blocked
  unless a typed lease covers the full affected scope or the actor uses an
  isolated clean worktree.
- The verb taxonomy itself is part of the guard. Existing mutating-git sets in
  `dev/scripts/devctl/runtime/vcs.py`,
  `dev/scripts/devctl/context_graph/_codeshape_support.py`, and
  `dev/scripts/devctl/governance_graph/mutation_bypass.py` must converge on the
  same destructive worktree verbs, including `clean`. Missing one verb is a
  policy hole, not a harmless implementation detail.
- Role assignment and capability grants come from typed role/capability
  authority, not provider-name defaults. A missing actor identity fails closed;
  `SessionPosture` may project capabilities for display, but cannot grant
  mutation by itself.
- Lifecycle packet posting authority is not implementation authority. A session
  can be allowed to post `finding`, `task_started`, `task_progress`,
  `task_blocked`, `task_produced`, `review_failed`, or `review_accepted`
  packets without being allowed to edit, stage, commit, push, or apply patches.

Reviewer actions allowed while another session owns the mutation lease:

- Read files, inspect diffs, run read-only status/context/system-map commands,
  and run validation commands that do not rewrite implementation files.
- Poll inboxes, record peer-awareness evidence, and post typed findings,
  `task_blocked`, `review_failed`, or `review_accepted` packets when
  target/session/evidence validation passes.
- Amend plan-intake source and manifest only when the operator's current task
  is plan iteration rather than implementation, and only with evidence that the
  plan source remains candidate/intake authority until ingested.

Reviewer actions forbidden while another session owns the mutation lease:

- `apply_patch` or direct file edits inside the implementer's write set.
- Staging, commit, push, generated-state rewrites, generated surface rewrites,
  shared-worktree `git stash` / reset / checkout / clean / restore operations,
  or "helpful" implementation repairs.
- Offline findings as a parallel lifecycle ledger.

Deliverables:

- Extend `AuthoritySnapshot`, `SessionPosture`, `CollaborationSession`,
  `AgentDispatchRouter`, `AgentLoopDecision`, and
  `ControlDecisionObedience` consumers so mutation decisions check role,
  actor, session id, active `task_started`, target session, target refs, write
  set, and active `MutationLease`.
- Amend existing role rows rather than creating a parallel role authority:
  `MP377-P0-ROLE-MATRIX-ROSTER-S1`,
  `MP377-P0-LIFECYCLE-ROLE-SIGNOFF-S1`,
  `MP377-P0-ACTIVE-WORK-ENVELOPE-S1`,
  `MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1`, and
  `MP377-P0-NEXT-BLOCKER-LIFECYCLE-S1`.
- Add governed `assign_role` / `unassign_role` receipts or equivalent typed
  role-assignment events, explicit multi-role policy, capability regrant on
  role change, and a `role_drift` / `unauthorized_mutation` blocker category.
- Replace hardcoded cascade role maps such as `claude=implementer` and
  `codex=reviewer` with typed role resolution from the same authority used by
  `ActorAuthorityState` / `CapabilityGrantState`. Provider-pair constants may
  remain only as compatibility defaults that fail closed for mutation.
- `devctl commit`, `devctl push`, stage handoff, review checkpoint, and approval
  flows must gate on explicit `ActorAuthorityState` capabilities. If `repo.push`
  is required by a flow, it must be modeled as a real grant rather than implied
  by `repo.commit`.
- Add a pre-edit / pre-apply guard that fails closed for reviewer mutation when
  an implementer lease covers the path. The guard returns typed failure
  evidence naming the lease, actor, role, session, attempted path, and required
  recovery action.
- Add a worktree-state mutation guard for VCS commands that can move, hide,
  delete, or replay dirty work. The guard returns typed failure evidence naming
  the actor, role, session, command, affected scope, active peer leases, required
  clean-worktree alternative, and recovery action.
- Extend command/action taxonomy so whole-worktree VCS mutations have
  first-class action names and capabilities rather than being hidden under
  generic shell execution. At minimum the taxonomy covers
  `vcs.worktree_state_mutation` and destructive verb subclasses for
  stash/reset/checkout/restore/clean/apply.
- Connect this to existing `ActorAuthorityState`, `CapabilityGrantState`,
  `SessionLease`, `WorkPublicationLedger`, and typed action proof contracts
  instead of adding a parallel authority store.
- Preserve the reviewer packet path: a blocked reviewer edit must become a
  typed finding or `task_blocked` packet targeted at the active implementer
  lane, not a local code patch.

Closure:

- Focused tests prove reviewer mutation is rejected while an implementer lease
  is active, accepted only after typed lease transfer or disjoint write-set
  authority, and still permits read-only review and typed finding packets.
- Focused tests prove shared-worktree `git stash`, `git reset`,
  `git checkout`, `git restore`, and `git clean` are rejected without a typed
  worktree-scope lease when peer dirty work or active peer leases exist.
- Focused tests prove all VCS mutation verb sets include the same destructive
  worktree verbs, including `clean`, and command/action routing exposes them as
  mutation actions rather than generic validation commands.
- Focused tests prove missing actor identity fails closed, `SessionPosture`
  alone cannot grant mutation, provider-pair cascade defaults do not authorize
  edits, and remote-control operator fallback cannot become mutation owner
  without an explicit capability grant.
- `MP-GUARDIR-V4-PHASE-0-6-A-ROLE-MUTATION-LEASE-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before any further
  Codex/Claude dual-agent implementation lane starts.

## Phase 0.6.A Mutation Method Provenance

Goal: make mutation authority apply to the method of mutation, not only to the
actor's high-level role. An implementer with a valid live-tree lease may edit
the leased write set, but the runtime still needs to know whether the change
came from a typed patch/edit path, a governed action, a generated-surface
renderer, or raw shell text such as redirection and heredoc writes.

Live failure:

- During the `rev_pkt_4692` / `rev_pkt_4693` AgentLoopContext wiring slice,
  agent-mind observed Claude appending a regression test through shell
  redirection:
  `cat >> dev/scripts/devctl/tests/runtime/test_agent_loop_decision.py << 'EOF'`.
- The resulting test was valid and passed, but the system did not classify the
  write method as a mutation surface requiring typed provenance. That means a
  future actor could mutate files through shell syntax without the same
  path-level proof collected for patch/edit tools.
- During the later `rev_pkt_4708` plan-currency review cycle, agent-mind also
  observed a verification command using `git stash && ...` to isolate test
  behavior while the shared worktree contained Codex plan edits and Claude
  implementation edits. Even if the stash was not persisted, this command shape
  is a whole-worktree mutation method: it can temporarily hide or replay dirty
  work outside the actor's assigned slice.
- Existing policy already distinguishes raw `git` / raw push and raw shell
  idling from governed lanes. The missing piece is a repo-wide write-method
  classifier that treats file-writing shell constructs as mutation attempts,
  even when the actor is otherwise allowed to implement.
- The read-only worktree audit found partial substrate but inconsistent verb
  coverage: `runtime/vcs.py` tracks mutating git verbs including `stash` but not
  `clean`; context-graph code-shape support detects checkout/reset/restore/stash
  but not clean; mutation-bypass graph hooks catch reset/stash but not checkout,
  restore, or clean; `raw_git_bypass_receipts.py` only models commit/push; and
  `control_decision_action_matching.py` does not recognize destructive
  worktree verbs or raw shell writes as mutation tokens.

Required invariant:

- Every file mutation has actor, role, session, target path, write method,
  lease/ref authority, and provenance evidence. The minimum mutation proof path
  is `TypedAction -> ActionResult -> RunRecord`, or an explicitly registered
  patch/edit adapter that emits equivalent path evidence.
- Shell commands containing output redirection, append redirection, heredocs,
  herestrings, `tee` writes, or inline scripts that open repo files for writing
  are mutation commands. They require the same path/lease authority as
  `apply_patch` or editor-tool edits.
- VCS commands that alter worktree or index state are mutation commands even
  when they are framed as verification setup. `git stash`, `git stash push`,
  `git stash pop/apply`, `git reset`, `git checkout`, `git restore`,
  `git clean`, and `git apply` require typed actor/session/lease/scope
  provenance, an explicit restore/recovery plan when allowed, and proof that no
  active peer-owned dirty work can be hidden or overwritten.
- Command envelopes classify both actor/proxy authority and mutation risk. A
  command such as `git clean -fd`, `git reset --hard`, `git checkout`, or
  `git stash && test` must not pass through as an unclassified shell validation
  command simply because it lacks `apply_patch`, `commit`, or `push` tokens.
- Read-only validation commands may execute freely inside the current reviewer
  authority, but commands that can write repo files must be classified before
  execution or captured after execution as governed exception debt. Silent raw
  shell writes are not acceptable proof.
- Agent-mind and session logs are auxiliary evidence only. Detection must land
  in repo-owned typed state or guard receipts so it survives compaction,
  provider rotation, and subagent fanout.

Deliverables:

- Add a write-method classifier to the existing command/control path rather
  than creating a new policy surface. It should compose with
  `ControlDecisionObeyedGuard`, `AgentDispatchRouter`, `MutationLease`,
  `TypedAction`, `ActionResult`, `RunRecord`, `ValidationReceipt`, and
  agent-mind action extraction.
- Extend agent-mind or its reducer inputs to surface shell redirection/heredoc
  file writes as candidate mutation events with target path evidence.
- Add guard coverage proving a reviewer cannot write through shell redirection
  when an implementer owns the lease, and an implementer write through raw shell
  either emits typed method provenance or a governed exception.
- Extend the same classifier to VCS worktree-state mutations. A shared dirty
  worktree must route verification isolation through a separate clean worktree,
  a governed checkpoint, or a typed worktree-scope mutation receipt; it must not
  use ad hoc `git stash && test` as a local convenience.
- Reconcile existing VCS mutation machinery:
  `dev/scripts/devctl/runtime/vcs.py`,
  `dev/scripts/devctl/context_graph/_codeshape_support.py`,
  `dev/scripts/devctl/governance_graph/mutation_bypass.py`,
  `dev/scripts/checks/mutation_bypass_graph_closure/command.py`,
  `dev/scripts/devctl/commands/raw_git.py`,
  `dev/scripts/devctl/runtime/raw_git_bypass_receipts.py`,
  `dev/scripts/devctl/runtime/control_decision_obedience.py`,
  `dev/scripts/devctl/runtime/control_decision_action_matching.py`,
  `dev/scripts/devctl/runtime/command_envelope_classification.py`,
  `dev/scripts/devctl/runtime/action_routing.py`,
  `dev/scripts/devctl/runtime/worktree_orphan_inventory_stashes.py`, and
  `dev/scripts/devctl/runtime/worktree_orphan_inventory_stash_source.py`.
  These modules should share one destructive-worktree verb taxonomy and one
  action/receipt path rather than each carrying partial knowledge.
- Reconcile existing command-consumer allowlists:
  `dev/scripts/devctl/runtime/control_decision_action_matching.py`,
  `dev/scripts/devctl/runtime/advisory_next_action_role_filter.py`,
  `dev/scripts/devctl/runtime/action_routing.py`,
  `dev/scripts/devctl/commands/development/final_response_gate_agent_loop.py`,
  and `dev/scripts/devctl/runtime/control_decision_consistency.py` must consume
  the same command-envelope mutation classifier or a registered adapter over it.
  They must not each decide mutation risk through local substring markers such
  as commit/push/git-add-only lists. A command that the envelope classifies as
  `git_clean`, `git_reset`, `git_stash`, `git_restore`, `git_apply`,
  `shell_redirect`, `shell_heredoc`, `shell_herestring`, or `tee_write` remains
  governed at every render, route, action-match, consistency, and final-gate
  hop.
- Generated-surface writers such as `render-surfaces --write` remain allowed
  only through their registered commands and generated-surface sync guards.
  They must not become a generic raw shell write bypass.

Closure:

- Focused tests prove `cat >> path`, `cmd > path`, heredoc, and `tee path`
  mutations are classified as write attempts with extracted target paths.
- Focused tests prove `git stash`, `git reset`, `git checkout`, `git restore`,
  `git clean`, and `git apply` are classified as worktree/index mutation
  attempts, and `git stash && test` is rejected in a shared dirty multi-agent
  worktree without explicit lease/provenance.
- Focused tests prove `git clean` is present in all mutating-git verb taxonomies
  and mutation-bypass graph closure catches checkout/restore/clean in addition
  to reset/stash.
- Focused tests prove command envelopes carry a mutation-risk classification
  for destructive VCS verbs and raw shell write forms, independent of proxy
  actor classification.
- Focused tests prove `control_decision_action_matching.action_mutates()`,
  advisory next-action role filtering, action routing, final-response
  `is_executable_next_command`, and `control_decision_consistency` all refuse or
  mark governed destructive commands through the shared classifier rather than
  stale local token lists.
- Focused tests prove allowed patch/edit adapters and governed writer commands
  emit equivalent path provenance.
- Focused tests prove read-only commands are not falsely blocked.
- The plan cites existing typed action and mutation lease contracts; no
  parallel write-policy store is introduced.

## Phase 0.6.A Task Produced Guard Repair

Goal: repair the specific post-implementation lifecycle break discovered by the
Work Stream A.0 dogfood run. Codex posted `rev_pkt_4651` as a typed
`task_started`, Claude implemented the slice, and Claude could not post the
typed `task_produced` because `ControlDecisionObeyedGuard` rejected the
downstream packet for the Claude actor. The offline report is temporary
evidence, not a durable alternate channel.

Live evidence:

- Codex `task_started`: `rev_pkt_4651`.
- Claude offline `task_produced`:
  `dev/reports/review_channel/offline_findings/2026-05-20T19-25Z-claude-task-produced-A0.md`.
- Local Codex verification receipts include the focused A.0 pytest run and
  broader `check_git_mutation_proof` / `commit_receipt` regressions.
- Codex `devctl session --role observer --include-review-status always
  --format json` produced no output for more than 60 seconds during the same
  handoff attempt; startup/final-gate hangs must become typed failure evidence,
  not silent loop blockers.

Deliverables:

- Fix `control_decision_obedience.py` /
  `control_decision_consistency` so a valid downstream
  `task_started -> task_produced -> review_accepted` transition is not rejected
  as an illegal control-decision divergence.
- Extend `review_channel_post_actions.required_review_channel_post_action()`
  so `review_accepted` has an explicit controller action name. Without this,
  even an AgentLoopDecision that intends to allow A.0 closure cannot authorize
  `review-channel --action post --kind review_accepted`.
- Preserve the guard's blocking behavior for wrong actor, wrong role, wrong
  target session, stale source session, missing target fields, missing evidence
  refs, and unrelated packet kinds.
- Teach the review-channel path to return a typed `task_blocked` or
  `ChannelRecoveryFailureReceipt` when closure packets cannot be accepted; do
  not force agents into offline report files as the only evidence carrier.
- Add a bounded watchdog around startup/final-gate child invocations used in
  dogfood proof. A no-output hang must emit typed failure evidence with command,
  timeout, actor, session id, and target slice.
- Add regression tests for:
  `task_started` from Codex to Claude, `task_produced` from Claude to Codex,
  `review_accepted` from Codex to Claude, explicit
  `review-channel.post_review_accepted` action mapping, invalid actor
  rejection, invalid session rejection, and stale packet rejection.
- Promote the existing A.0 offline report into typed recovery evidence after
  the repair lands, then post the missing `task_produced` or a typed
  replacement closure packet that references `rev_pkt_4651`.

Constraints:

- This repair is not a bypass, staging, commit, push, or release authority.
- Offline findings are admissible only as transition evidence for this repair;
  they must not become a parallel lifecycle ledger.
- The active continuation/stop anchor keeps Codex and Claude working, but does
  not override target-session, role, evidence, or closure validation.

Closure:

- `devctl review-channel --action post --kind task_produced` succeeds for the
  A.0 envelope or emits a typed recoverable blocker instead of raw
  `ControlDecisionObeyedGuard` failure.
- Codex can post `review_accepted` for A.0 with resolvable evidence refs.
- Focused tests cover the accepted and rejected packet paths.
- `MP-GUARDIR-V4-PHASE-0-6-A-TASK-PRODUCED-GUARD-REPAIR-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before Work Stream A
  starts.

## Phase 0.6.A Review Feedback Post Obedience

Goal: repair the reviewer communication path discovered during v4.20 dogfood.
After Codex opened Claude `rev_pkt_4678`, reran focused devctl tests, and
attempted to post a review-only progress verdict back to Claude,
`review-channel --action post --kind task_progress` failed
`ControlDecisionObeyedGuard` with `control_decision_obedience_failed`. The
system had already routed Codex into review of `rev_pkt_4678`; blocking the
review packet without a typed repair is another lifecycle loop.

Live evidence:

- Claude progress packet: `rev_pkt_4678`.
- Codex devctl test receipts:
  `command_output:test-python:7a2938cd124067c7`,
  `command_output:test-python:d7da52af84bcebf4`, and
  `command_output:test-python:5a577245eaa74477`.
- Codex `agent-loop --actor codex --role reviewer` still returned
  `repair_startup_authority` / `dirty_path_budget_exceeded` with empty blocker
  repair fields.
- Codex attempted a review-only `task_progress` packet to Claude with
  `target_role=implementer`,
  `target_session_id=2a5b3528-aaa6-4615-b83b-5b1d3598509b`,
  `target_ref=MP-GUARDIR-V4-PHASE-0-6-A-STARTUP-REPAIR-COMMAND-S1`, and
  review/test evidence refs; the post failed
  `control_decision_obedience_failed`.
- Claude then implemented the smallest v4.20 patch to allow Codex
  `task_progress`, but Claude's own `task_progress` response to Codex
  `rev_pkt_4679` failed the same guard because the semantic parent-kind matrix
  does not allow `finding -> task_progress`. That is not a reason to loosen
  closure rules; it is a missing non-closure response edge.
- After v4.22 parent-resolution narrowing, Codex verified Claude `rev_pkt_4686`
  with focused pytest receipts and posted `rev_pkt_4687` as a review-only
  `task_progress` response to Claude. That proves the narrow post path can
  succeed, but it is not full closure because startup/status still reported a
  checkpoint/dirty-budget stop, stale reviewer-mode posture, and contradictory
  review-output grants during the same handoff.
- During v4.32/v4.33, Codex posted `rev_pkt_4706`, a current plan-bound finding
  for the command-envelope slice, with target role/session, plan SHA
  `3b300f7266fde69940a996210be83cbecbc4b9415b0e8ebdf7aaf00a12ecf81a`, and
  plan ingest receipt `plan-ingest-5fd860b2c7fde861`. `review-channel history`
  and `show --packet-id rev_pkt_4706` could resolve the packet, but
  `review-channel inbox --target claude` and `develop next --actor claude`
  continued to select stale `rev_pkt_4698` as the blocking packet. Current
  target/session-scoped packet relevance is therefore not yet driving the
  inbox/develop selection path.
- Codex then posted `rev_pkt_4707` against the v4.33 ingested plan SHA
  `c31a8b20a8ac6cbd6f98f23a370b1c5605dc70d0e436bf3b2fe3aceb65cc08b9` with
  parent `rev_pkt_4706` and requested action
  `repair_packet_selection_current_plan_priority`. The post succeeded and
  invalidated `review_channel.packet_inbox`, `agent_work_board`,
  `agent_loop_decisions`, `startup_context`, and `develop.next`, but packet
  delivery remained typed-attention-only; runtime controllers still have to
  consume the current packet instead of waiting for operator chat.
- After v4.42, Codex posted `rev_pkt_4714` to route the next typed-action
  adapter scope and then attempted to accept Claude's v4.41 import-isolation
  repair. Codex opened `rev_pkt_4714`, opened the current Codex inbox/body for
  `rev_pkt_4704`, and reran the focused envelope suite with receipt
  `command_output:test-python:97582b15df3c1e48`; nevertheless the
  `review_accepted` post remained blocked by `ControlDecisionObeyedGuard` with
  stale source decision `agent-runtime-clock:rev_evt_84896`. This proves the
  review-feedback post path still lacks a fresh-decision/body-observation
  handshake for reviewer acceptance packets.

Required invariant:

- A scoped reviewer must be able to post review-only findings, progress
  verdicts, review failures, and eligible review acceptances when typed
  authority already routes the reviewer to that packet/slice.
- A scoped implementer must be able to answer a reviewer `finding` for the same
  target slice with `task_progress`, `task_blocked`, or `task_produced` while the
  work remains open. These are non-closure response edges and must not be
  confused with `review_accepted` closure.
- Review-only communication posts are still state-changing lifecycle writes, so
  they must carry or resolve a valid `AgentLoopDecision`, source-session
  authority, target role/session, packet lineage, and guard-obedience evidence.
- If checkpoint budget or inactive reviewer-mode state is present, the review
  packet authority decision must explicitly state why the packet is permitted as
  scoped coordination while implementation remains blocked. A successful packet
  post is not enough if adjacent authority surfaces still disagree.
- If those proofs are missing, the post path must emit a typed recoverable
  blocker (`task_blocked`, `ChannelRecoveryFailureReceipt`, or stop_anchor)
  naming the missing proof and repair row. A raw guard failure or offline report
  is not closure.
- `review_accepted` remains stricter than progress/finding packets: it may
  close only over a resolved `task_produced` parent and must still reject
  `task_progress` parents per v4.12.
- Packet selection is part of review-feedback obedience. For an actor/role/
  session-targeted lane, `inbox`, `develop next`, agent-loop, watcher lease, and
  final-response gates must rank the current plan-bound packet for that lane
  ahead of stale queued packet debt. A packet such as `rev_pkt_4706` that has a
  matching target role/session/ref and fresh plan revision must be visible as
  current work, or the reducer must return a typed
  `packet_selection_stale_backlog_conflict` blocker naming the older packet
  that is suppressing it.
- The selector is shared, not duplicated. Implementations such as
  `packet_attention_actionable.py`, `packet_attention_support.py`,
  `startup_packet_inbox.py`, `peer_attention_window.py`, agent-loop reducers, and
  final-response gates must consume or compose the same current-plan-aware packet
  selection result. Local queue order, newest-pending heuristics, peer relevance
  scores, or count summaries cannot independently decide the active packet.
- Packet arrival invalidation is not enough. A successful post that invalidates
  derived state must be followed by consumers reloading event-backed state and
  selecting the current packet, or by a typed reload/selection failure that names
  the stale consumer.
- Current-plan ranking must tolerate live plan amendment. A packet such as
  `rev_pkt_4707` with an older target SHA may remain the current lane if the
  latest plan revision amends the same row/request without superseding the
  packet. If exact SHA mismatch means the packet should be refreshed, the
  selector emits a typed `packet_plan_revision_refresh_required` blocker with the
  old packet id, old SHA, latest SHA, target row, and requested refreshed post.
- Reviewer acceptance cannot reuse stale control decisions. A scoped
  `review_accepted` post over a completed implementer slice must bind to the
  current reviewer decision, observed packet body requirements, source session,
  target session, parent packet, and plan row. If any body-open or decision
  dependency is stale, ambiguous, or still references an old
  `agent-runtime-clock` event, the post path emits a typed consistency blocker
  naming the stale decision source, required packet body, and repair row.

Deliverables:

- Extend `review_channel_post_actions.required_review_channel_post_action()`
  so `finding`, `task_progress`, `review_failed`, and `review_accepted` map to
  explicit guard actions with review-only vs closure semantics.
- Teach review-channel post to consume an existing `AgentLoopDecision` or
  resolve one from current typed session/packet authority before
  `ControlDecisionObeyedGuard` runs. Do not add a raw bypass flag.
- Connect this to the source-session authority resolver from Phase 0.6.D so the
  reviewer post records the real Codex session and rejects spoofed source
  sessions.
- Add focused positive tests for a reviewer `task_progress` response to
  `rev_pkt_4678`-shaped input and a reviewer `finding` response to a
  `task_produced` or `task_progress` packet.
- Add focused positive tests for implementer `task_progress`, `task_blocked`,
  and `task_produced` responses to a reviewer `finding` packet when
  target-role, target-session, target-ref, source session, and peer direction
  match.
- Add negative tests for missing source session, wrong target session, missing
  parent packet, unrelated `finding` target-ref, closure attempt over
  `task_progress`, `review_accepted` over `finding`, and missing
  control-decision/proxy authority.
- Add a repair-surface test proving a blocked reviewer feedback post returns a
  typed recoverable blocker with owner, target, reason, and next repair row.
- Add a consistency test for the `rev_pkt_4687` shape: checkpoint budget blocks
  mutation and convergence, but a scoped reviewer `task_progress` packet can pass
  only when `AuthoritySnapshot.allowed_actions`,
  `CapabilityGrantState` / `ActorAuthorityState`, `AgentLoopDecision`, and
  `ControlDecisionObeyedGuard` agree on the narrow review-only lane.
- Add packet-selection tests for the `rev_pkt_4706` shape: with stale
  `rev_pkt_4698` still queued, Claude's target-session inbox, `develop next`,
  watcher lease, and final-response gate select the fresher plan-bound
  `rev_pkt_4706` or emit a typed stale-backlog conflict. The old packet may
  remain auditable history, but it cannot hide current targeted work.
- Add split-selector regression coverage: queue-order, latest-pending,
  startup-inbox, peer-attention, agent-loop, watcher, and final-gate selector
  paths all consume the shared current-plan-aware result and cannot diverge on
  `rev_pkt_4706` versus `rev_pkt_4698`.
- Add plan-supersession regression coverage: after a v4.35/v4.36 ingest for the
  same target row, `rev_pkt_4707`-shaped packets are either still selected by
  row/lineage relevance or produce `packet_plan_revision_refresh_required`; they
  do not silently lose to stale backlog due to exact-SHA mismatch alone.
- Add packet-arrival invalidation tests for the `rev_pkt_4707` shape: after a
  packet post invalidates `review_channel.packet_inbox`, `agent_work_board`,
  `agent_loop_decisions`, `startup_context`, and `develop.next`, each consumer
  reloads event-backed state before selecting work and cannot continue from a
  stale projection without a typed stale-consumer blocker.
- Add reviewer-acceptance freshness tests for the `rev_pkt_4714` / v4.41
  acceptance shape: after Codex opens the sent packet body and the current Codex
  inbox packet body, `review-channel --action post --kind review_accepted` must
  consume fresh reviewer authority or return a typed
  `review_acceptance_decision_stale` blocker. It must not keep reporting
  `non_body_open_action_after_body_open_required` against a stale
  `agent-runtime-clock` event.

Closure:

- Codex can post a review-only progress/finding packet to Claude for the live
  Phase 0.6.A slice with devctl test receipts and current session authority.
- Claude can post `task_progress` or `task_blocked` back to Codex for a resolved
  reviewer `finding` parent without raw guard failure, while `review_accepted`
  over that same `finding` parent remains rejected.
- The same path rejects invalid closure or spoofed-session packets before
  bypassing `ControlDecisionObeyedGuard`.
- The raw `control_decision_obedience_failed` observed during v4.20/v4.21 is covered
  by a focused regression and no longer forces offline communication.
- The v4.23 authority-split observation is covered by a focused regression:
  `safe_to_continue=false` / `dirty_path_budget_exceeded` cannot be interpreted
  as permission for reviewer mutation, cannot retarget current work, and cannot
  silently suppress required review-only packet coordination.
- The v4.33 packet-selection regression is covered: a fresh, current,
  plan-bound, target-session-scoped packet such as `rev_pkt_4706` is visible in
  the target lane and selected before stale queued packet debt such as
  `rev_pkt_4698`, unless a typed stale-backlog conflict blocker is emitted.
- The v4.34 invalidation regression is covered: `rev_pkt_4707`-style arrival
  invalidation forces all named consumers to reload or emit a typed stale
  consumer blocker; packet delivery may remain non-launching typed attention, but
  it cannot disappear from the current lane.
- The v4.36 supersession regression is covered: plan amendments during an open
  packet lifecycle either preserve the packet's current lane by target-row
  lineage or demand a refreshed packet through typed blocker/packet flow, never
  by silently demoting the current packet behind old debt.
- The v4.43 reviewer-acceptance regression is covered: Codex can post
  `review_accepted` for a completed Claude slice only after fresh reviewer
  authority, body observation, parent lineage, and target role/session evidence
  agree; otherwise the system returns a typed stale-decision/body-observation
  blocker instead of raw `ControlDecisionObeyedGuard` failure.
- `MP-GUARDIR-V4-PHASE-0-6-A-REVIEW-FEEDBACK-POST-OBEDIENCE-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before Work Stream A
  starts.

## Phase 0.6.B Cascade Parent Semantic Authority

Goal: close the second-order guard failure found during review of the Phase
0.6.A structural repair. A cascade-post predicate that accepts
`packet:rev_pkt_<digits>` as "parent lineage" is still unsafe unless it
resolves that packet and proves the lifecycle edge matches the live typed
assignment.

Live failure:

- Claude narrowed `_cascade_lifecycle_post_authority()` so the closure path
  required `to_agent`, `target_role`, `target_session_id`, and packet-shaped
  evidence.
- Codex reviewer verification still reproduced the critical bypass:
  `task_produced` from Claude to Codex with
  `target_session_id="wrong-session"` and
  `evidence_ref=("packet:rev_pkt_4652",)` returned `True`.
- Codex reviewer verification then reproduced a second critical bypass:
  `review_accepted` over a `task_progress` parent returned `True`. That
  treats in-progress evidence as final acceptance evidence and lets a reviewer
  close a lane before the implementer has posted `task_produced`.
- Codex review of `rev_pkt_4680` found a third lineage ambiguity: the packet
  body and evidence described a response to the reviewer `finding`
  `rev_pkt_4679`, but `_cascade_lifecycle_post_authority()` accepted the post
  by selecting the first packet-shaped evidence ref, `packet:rev_pkt_4672`, as
  the parent. A multi-packet evidence list can therefore pass by ordering an
  older compatible parent before the actual response target.
- Therefore structural checks alone can still authorize a closure packet for
  the wrong receiving session, stale parent, or unrelated packet lineage.

Required invariant:

- Every cascade lifecycle post must resolve its parent packet from typed
  review-channel state before bypassing `ControlDecisionObeyedGuard`.
- A cascade post with multiple packet evidence refs must name exactly one
  primary semantic parent through a typed field such as
  `parent_packet_id` / `semantic_parent_packet`, or through an equivalent
  structured evidence relation. Additional packet refs are supporting evidence,
  not alternate parents. If no primary parent is supplied, fallback is allowed
  only when exactly one packet-shaped evidence ref exists and it satisfies the
  edge matrix; ambiguous multi-packet evidence fails closed with a typed
  recoverable blocker.
- Evidence order must not determine parentage. Reordering `evidence_ref`
  entries cannot change the resolved lifecycle edge or make an otherwise
  invalid response valid.
- `task_produced` must cite the initiating `task_started` packet. The post is
  valid only when `from_agent` matches the parent target agent, `to_agent`
  matches the parent source agent, `target_session_id` matches the parent
  source session, `target_role` matches the parent source role, and the parent
  packet is still live for the same target ref / slice.
- `review_accepted` must cite the returned `task_produced` packet and, where
  required, the initiating `task_started` packet. It must reject
  `task_progress`, `task_blocked`, `review_failed`, and any other non-final
  parent kind. The post is valid only when the direction, target session,
  target role, target ref, and evidence lineage close the same lifecycle lane.
- `review_failed` may cite `task_produced` or `task_progress` when issuing a
  rework finding, but it must still resolve the parent packet and prove the
  direction, role, session, target ref, and lineage are the same lane.
- Wrong session, wrong role, wrong peer, stale parent, missing parent body,
  expired packet, unrelated parent kind, and mismatched target ref all fail
  closed before the cascade post authority returns `True`.

Deliverables:

- Add a typed parent-packet resolver for review-channel cascade posts. Reuse
  the existing packet reducer / event log state; do not create a new lifecycle
  store.
- Replace packet-regex-only parent acceptance with a semantic validation result
  that names parent packet id, parent kind, parent source / target agents,
  source / target sessions, target role, target ref, status, expiry, and
  decision.
- Extend the typed post schema / CLI with an explicit primary-parent relation
  or structured evidence relation, then update the reducer so
  `primary_parent_packet_id`, `candidate_parent_refs`,
  `supporting_evidence_refs`, and parent-resolution decision are recorded in
  guard evidence. Do not infer the parent from whichever packet ref appears
  first.
- Add negative tests for the exact reviewer reproduction:
  structurally valid `packet:rev_pkt_4652` evidence plus a wrong
  `target_session_id` must return `False`.
- Add negative tests for wrong `target_role`, wrong `to_agent`, stale/expired
  parent packet, unrelated parent packet kind, and target-ref mismatch.
- Add the v4.12 negative test from `rev_pkt_4661`: `review_accepted` with a
  resolved `task_progress` parent must return `False`.
- Add the v4.22 negative tests from `rev_pkt_4680`: a packet whose body/action
  is responding to a reviewer `finding` cannot be authorized by placing an
  older compatible `task_started` packet first in `evidence_ref`; and reversing
  the order of packet refs must not change the authorization result.
- Add a positive test that uses a realistic `task_started -> task_produced ->
  review_accepted` packet chain and proves the resolved semantics authorize the
  closure without raw bypass.

Closure:

- The direct wrong-session reproduction returns `False`.
- The direct `review_accepted` over `task_progress` reproduction returns
  `False`.
- The direct `rev_pkt_4680`-shaped multi-evidence ambiguity returns a typed
  recoverable blocker until a primary semantic parent is explicit and valid.
- The valid `review_accepted` over `task_produced` reproduction returns `True`.
- The focused Phase 0.6.A guard-repair test suite includes semantic parent
  fixtures, not only structural predicate tests.
- `MP-GUARDIR-V4-PHASE-0-6-B-CASCADE-PARENT-AUTHORITY-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before any A.0
  `review_accepted` closure is accepted.

## Phase 0.6.C Review-Channel Read Authority

Goal: keep reviewers able to inspect typed packets while still forbidding
unauthorized mutation. A reviewer blocked from `show` / `inbox` / `status`
falls back to offline files, which recreates the parallel-ledger failure this
plan is trying to eliminate.

Live failure:

- Codex could not read `rev_pkt_4655` through
  `review-channel --action show` after the v4.10 finding because
  `ControlDecisionObeyedGuard` blocked the read path.
- The body was reviewed through local event-log inspection and Claude's
  offline response instead. That is admissible as recovery evidence, but not
  a durable operating mode.

Required invariant:

- Non-mutating review-channel reads are authorized by target role/session and
  packet visibility, not by mutation authority.
- `show`, `inbox`, `status`, `history`, and packet-body observation may record
  `PacketBodyObservation` / semantic-ingestion requirements, but they must not
  grant edit, stage, commit, push, apply, or packet-ack authority.
- Reading a packet body does not count as semantic ingestion or closure. If the
  body creates an actionable item, the existing packet semantic ingestion gate
  remains responsible for forcing the typed disposition.

Deliverables:

- Add a read-only review-channel authority path for scoped packet observation.
  It must compose with existing target-session / target-role matching and
  `PacketBodyObservation` state.
- Ensure `ControlDecisionObeyedGuard` applies to state-changing review-channel
  actions while non-mutating reads return typed observation evidence instead of
  startup-authority failure.
- Add tests that `show`, `inbox`, `status`, and `history` work for the scoped
  reviewer lane and still reject wrong-session or unauthorized visibility.
- Add tests proving read authorization does not permit `post`, `ack`, `apply`,
  `dismiss`, edit, stage, commit, push, or semantic-ingestion bypass.

Closure:

- `review-channel --action show --packet-id rev_pkt_4655` works for the
  correct reviewer/session and records body observation evidence.
- Wrong-session reads fail closed with typed evidence.
- `MP-GUARDIR-V4-PHASE-0-6-C-REVIEW-READ-AUTHORITY-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before offline
  findings are treated as anything beyond temporary recovery evidence.

## Phase 0.6.C Coordination-Lane Import Isolation

Goal: keep the typed communication and recovery plane alive when an
implementation-owned command module is temporarily broken. A reviewer must be
able to read packets, post findings, inspect agent-mind/session state, and
route a repair request through typed state without editing the implementer's
write set or falling back to a parallel offline lifecycle.

Live failure:

- During the `rev_pkt_4701` follow-up, Claude's in-progress consumer patch
  added the intended cross-actor command checks in
  `dev/scripts/devctl/commands/development/report.py` and started plumbing
  `current_actor` through `report_assembly.py`.
- The same in-progress edit left a duplicated empty
  `_final_gate_repair_command_runnable()` definition in `report.py`, producing
  `IndentationError: expected an indented block after function definition`.
- Because `dev/scripts/devctl.py` imports the development command package while
  booting the CLI, unrelated commands such as `session`, `agent-mind`, and
  `review-channel --action post` fail before they can route a typed finding.
- That failure tempts the reviewer to either patch the implementer's code or
  write offline side-channel evidence. Both are exactly the role/mutation and
  parallel-channel smells this plan is closing.

Required invariant:

- `review-channel` reads/posts, `agent-mind`, `session` diagnostics,
  `startup-context`, and narrowly scoped recovery/status commands have a
  minimal import path that does not import implementation-heavy command modules
  such as `develop report`, dashboard renderers, or optional provider/adopter
  surfaces before dispatch.
- A syntax error or import-time runtime error in one command family must
  degrade that command family only. It must not take down the typed
  coordination lane needed to report, review, and repair the failure.
- Import isolation does not grant mutation authority. If the broken module is
  in an implementer-owned write set, Codex reviewer behavior remains
  review-only: post a typed finding/task_progress/task_blocked packet, name the
  owning plan row and artifact, and let the implementer repair unless typed
  mutation authority transfers.
- The CLI must return a typed recoverable blocker for the broken command family
  with owner, target, reason, stack/import diagnostic, and repair row. It must
  not emit a raw Python traceback as the only machine-readable evidence.
- The isolated coordination path must still consume the same
  `ActorAuthorityState`, `CapabilityGrantState`, `AgentLoopDecision`,
  source-session authority, and `ControlDecisionObeyedGuard` checks. It is not
  a raw bypass, not a second event writer, and not a duplicate packet store.
- Shared runtime classifiers used by the coordination lane, such as
  command-envelope mutation classification, must be leaf or neutral modules.
  They may depend on low-level parsing/coercion helpers, but must not import
  higher-level consumers such as `control_decision_obedience` when those
  consumers already import the classifier through action matching.

Deliverables:

- Refactor `devctl` command registration so command-family imports are lazy or
  guarded. The top-level CLI can discover and dispatch `review-channel`,
  `agent-mind`, `session`, `startup-context`, and recovery/status commands
  without importing `devctl.commands.development.report`.
- Add an import-health wrapper for command families that converts import
  failures into typed diagnostics. The diagnostic must include command family,
  exception class, file path, line where available, current actor/role/session
  when available, and repair plan row.
- Add focused tests that inject or simulate a broken `develop report` import
  and prove `review-channel --action show`, `review-channel --action post`
  with scoped review-only authority, `agent-mind`, and `session` diagnostics
  remain importable.
- Add a focused circular-import regression proving
  `command_envelope_classification`, `control_decision_action_matching`,
  `control_decision_obedience`, `review-channel`, `agent-mind`, and
  `test-python` routing can import in isolation after mutation-classifier
  consumers are wired.
- Add negative tests proving the isolated coordination lane cannot edit files,
  stage, commit, push, bypass lifecycle, or post closure packets without the
  same typed authority required by the normal path.
- Add generated-surface guidance so `AGENTS.md`, `CLAUDE.md`, and platform
  guide projections tell agents that a broken implementation module is a typed
  coordination blocker, not permission to hand-edit another role's write set or
  invent a new ledger.

Closure:

- With a deliberately broken `dev/scripts/devctl/commands/development/report.py`
  fixture, `review-channel` read/post recovery commands, `agent-mind`, and
  `session` diagnostics still run through the isolated command surface and emit
  typed diagnostics.
- The same broken fixture makes `develop next` fail closed with a typed
  command-family import blocker instead of a raw traceback.
- A reviewer can post a finding naming the broken implementer-owned file and
  plan row without mutation authority, while direct reviewer edits to that file
  remain blocked by `MP-GUARDIR-V4-PHASE-0-6-A-ROLE-MUTATION-LEASE-S1`.
- `MP-GUARDIR-V4-PHASE-0-6-C-COORDINATION-LANE-IMPORT-ISOLATION-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before the system can
  claim typed coordination survives broken implementation modules.

## Phase 0.6.D Review-Channel Source Session Authority

Goal: preserve the real typed source session on review-channel packet posts so
semantic parent-packet validation can distinguish a true wrong-session closure
from a packet emitted through the local review-store fallback.

Live failure:

- Claude's `rev_pkt_4663` correctly posted `task_produced` after tightening
  `review_accepted` to final `task_produced` parents only.
- The packet source session was still stamped as `local-review` because
  `review-channel --action post` does not expose or infer the posting actor's
  real session id.
- A valid Codex `review_accepted` targeted at Claude's actual implementer
  session would compare against parent `session_id="local-review"` and fail
  the Phase 0.6.B semantic parent check for an artifact of the transport, not
  for a real session mismatch.

Required invariant:

- `Packet.session_id` on `review-channel --action post` is the source actor's
  real typed session id when the actor is a live agent session.
- `local-review` remains a store/runtime fallback only when the caller has no
  resolvable typed source session. It must not silently masquerade as the
  source session for live agent packets.
- Cascade validation continues to fail closed for real wrong-session parents;
  it does not add a broad wildcard for `local-review`.

Deliverables:

- Add a governed way for review-channel post callers to provide or resolve
  source `session_id`, preferably through a CLI flag, typed executor/session
  context, or actor-session resolver already used by session/agent-mind
  commands.
- Add regression tests proving `task_produced` from Claude carries Claude's
  source session and a Codex `review_accepted` can close it only when the
  target session matches that resolved parent session.
- Add negative tests proving wrong session still fails and `local-review` is
  not accepted as a wildcard for live agent closure.
- Record the source-session id in packet body observation / show output so
  reviewers can inspect the session edge without reading raw event logs.

Closure:

- `rev_pkt_4663`-equivalent `task_produced` can be followed by a typed
  `review_accepted` whose `target_session_id` is the real Claude session,
  without using `local-review` as a bypass.
- Existing wrong-session and `review_accepted` over `task_progress` probes
  still return `False`.
- `MP-GUARDIR-V4-PHASE-0-6-D-REVIEW-CHANNEL-SOURCE-SESSION-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before A.0 closure is
  accepted as fully typed.

## Phase 0.6.D Source-Session Authenticity

Goal: tighten Phase 0.6.D from "not fallback" to "actor-bound typed session."
The review-channel post path must prove the supplied source `session_id`
belongs to the posting live agent according to existing session and actor
authority. A non-empty string is not proof.

Live failure:

- Claude's `rev_pkt_4667` correctly proved that `local-review` and empty
  sessions are rejected for live-agent posts.
- Codex reviewer verification then called
  `require_real_session_for_live_agent_post()` with
  `session_id="not-a-real-session"` and the gate accepted it.
- A fake non-fallback session can become the parent packet `session_id`; a
  downstream closure can then target the same fake value and satisfy the
  equality check without proving that either side used a real typed session.

Required invariant:

- Live-agent `review-channel --action post` validates source `session_id`
  against existing typed session/actor authority before the packet is written.
- Valid sources may include `SessionPosture`, `SessionLivenessSignal`,
  `SessionActivityLog`, `AgentMindSlice`, `AgentSessionOutcome`,
  `ActorAuthorityState`, `CapabilityGrantState`, or the same governed
  session resolver already used by `session`, `session-resume`, `agent-mind`,
  startup, and review-channel collaboration state.
- `AgentMindSlice` is a projection of recent agent activity. It may be an input
  to the resolver only when freshness, provenance, repo scope, and actor binding
  are explicit. The review-channel post path and cascade predicate must not
  each implement their own projection parser.
- Validation must bind actor, role where available, provider, session id,
  project/repo scope, and freshness/liveness when those fields exist. It must
  fail closed for a live-agent source session that is unknown, stale, from a
  different actor, or outside the current repo scope.
- `local-review` remains a non-live fallback for operator/system/dashboard
  store actions only. It is never a live-agent session, never a wildcard, and
  never a substitute for missing actor/session authority.

Deliverables:

- Add or connect a `SourceSessionAuthorityResolver` in the review-channel post
  path. Reuse existing session/actor contracts and projections; do not add a
  parallel session registry.
- Centralize the resolver so write-time post validation and verifier-time
  cascade validation consume the same authority result and diagnostics.
- Change `require_real_session_for_live_agent_post()` so it rejects arbitrary
  non-fallback strings unless the resolver proves the actor/session binding.
- Add tests proving:
  - Claude and Codex real session ids accepted when backed by typed session
    authority.
  - `local-review`, empty, malformed, unknown, stale, wrong-actor, and
    wrong-repo session ids rejected for live agents.
  - Non-live actors retain their documented fallback path without becoming
    parents for live-agent cascade closure.
  - A valid `task_produced -> review_accepted` closure still succeeds only
    when the review target matches the authenticated parent source session.
- Ensure packet `show`, body-observation evidence, and lifecycle predicate
  diagnostics expose the authority source used for source-session validation.

Closure:

- The direct Codex reviewer probe
  `require_real_session_for_live_agent_post(session_id="not-a-real-session")`
  returns a typed rejection.
- A focused test covers fake non-fallback session spoofing end to end.
- `MP-GUARDIR-V4-PHASE-0-6-D-SOURCE-SESSION-AUTHENTICITY-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before
  `review_accepted` on `rev_pkt_4667` or equivalent can close Phase 0.6.D.

## Phase 0.6.D Source-Session Continuity

Goal: preserve strict source-session authenticity without stranding legitimate
packets when an agent session rotates mid-cascade. The resolver must answer two
different questions: "is this live post being stamped by the actor's current
session?" and "was this parent packet stamped by a real session for that actor
at the time the packet was written?"

Live failure:

- After `rev_pkt_4670`, Claude fixed the verifier so a missing source-session
  projection fails closed and added the direct reproduction as a test.
- Claude then could not post the typed response through the cascade lane
  because Codex's live projection had rotated from
  `019e46cb-dd3c-7121-bf2f-eff8cc5fc815` to
  `019e474b-e803-7dc0-9689-aa77f82bf5d0`.
- Existing Codex packets from the older real session became stale under a
  "latest projection only" interpretation, even though the packets were valid
  at post time. That is a dogfood signal that authenticity needs post-time
  attestation and rotation policy, not just a latest-session equality check.

Required invariant:

- A new live-agent packet must still require the actor's current authenticated
  source session.
- A previously written parent packet is valid only if its source session can be
  proven by post-time typed evidence for that actor, repo, role, and packet
  event. Current projection mismatch is a rotation/expiry condition, not
  automatically proof of spoofing.
- Unknown, fallback, wrong-actor, wrong-repo, unproven, revoked, or explicitly
  expired sessions still fail closed. Continuity is not a wildcard.
- Session rotation must emit or expose typed continuity evidence such as a
  `SessionRotationReceipt`, `SessionActivityLog` entry, `AgentSessionOutcome`,
  or equivalent existing session-liveness record that lets the verifier
  distinguish "real old session" from "fake arbitrary string."

Deliverables:

- Extend `SourceSessionAuthorityResolver` with modes for `current_live_post`
  and `historical_parent_packet`.
- For historical parent packets, resolve against the review-channel event time,
  packet id, actor, session id, repo scope, and any recorded session activity /
  liveness / outcome evidence.
- Add cascade diagnostics that report `current_session_match`,
  `post_time_session_match`, `rotation_observed`, `expired`, and
  `authority_source`.
- Add tests proving:
  - a fake parent session with no projection or history fails closed;
  - a real parent from a prior session remains valid when post-time authority
    exists and rotation policy has not expired it;
  - a revoked/expired prior session fails closed;
  - a new live post cannot stamp an old session after rotation.
- If historical session records are not yet materialized, the resolver must
  return a typed recoverable blocker that asks for a fresh `task_started` or
  session-continuity receipt instead of forcing offline findings as the only
  response channel.

Closure:

- Claude can answer `rev_pkt_4670` or a refreshed Codex task packet with a
  typed packet, not only an offline file, while fake non-fallback session probes
  still reject.
- Focused tests cover session rotation, fake session spoofing, and missing
  history fail-closed behavior.
- `MP-GUARDIR-V4-PHASE-0-6-D-SOURCE-SESSION-CONTINUITY-S1` has a
  `PlanRowClosureReceipt` or explicit governed exception before Phase 0.6.D
  closure is accepted.

## Phase 0.6.D Agent-Mind And Subagent Scope

Goal: make multi-agent support useful without letting helper sessions become
authority for the main actor. Agent-mind projections are attention and
navigation evidence. They are not source-session authority unless a typed
resolver binds the projection to the requested actor, role, session, parent
delegator, repo scope, and packet route.

Existing system alignment:

- `DevelopmentCollaborationModeSpec(agent_sync)` already treats agent-mind
  polling as advisory attention context and blocks
  `agent_mind_claim_used_as_authority`, `unbounded_role_fanout`, and
  `provider_label_grants_mutation`.
- `AgentSpawnAuthority` already gates dead-agent spawn on staleness, live
  continuation anchor, and a scoped bypass receipt.
- `session_route_scope` already recognizes `subagent` as a route role. v4 must
  build on that routing shape instead of creating a new worker/session store.
- Repo portability comes from `ProjectGovernance`, `RepoPack`, and typed
  collaboration mode policy. A repo can configure fanout budgets, role names,
  and allowed worker kinds without changing the core authority model.

Live failure:

- The provider-level `dev/reports/agent_minds/<provider>_latest.json`
  projection can be refreshed by the main session or by a subagent of the same
  provider.
- During v4.16 dogfood, a Codex subagent refresh made Claude observe a new
  provider-latest Codex session while the cascade parent packets still belonged
  to the main Codex reviewer session.
- During the v4.25 live `rev_pkt_4693` review attempt, Codex queued read-only
  sidecar agents for plan-role and duplicate-system mapping. That refreshed
  `codex_latest.json` to sidecar session
  `019e474d-4ce3-7e33-ba02-2883920f9bbd`, after which a main-reviewer
  `review-channel --action post` using the real Codex session
  `019e46cb-dd3c-7121-bf2f-eff8cc5fc815` was rejected as stale/spoofed. The
  guard was right to reject spoofing, but wrong to rely on provider-latest as
  the only live-source oracle when a route-scoped main actor session was the
  intended poster.
- A source-session resolver that reads only provider-latest projection cannot
  distinguish main reviewer, delegated researcher, explorer, watcher, or
  subagent output.
- v4.34 dogfood added a second evidence-quality issue: when the subagent pool was
  already full, completed helper summaries from prior plan revisions were easy to
  retrieve as if they were fresh current audits. Agent-mind and subagent outputs
  must carry plan revision/source hash and completion time, and consumers must
  mark stale summaries as historical evidence rather than current authority.

Required invariant:

- Provider-latest files are convenience projections only. They may help a human
  or dashboard see recent activity, but they cannot identify the authoritative
  session when more than one session/provider worker exists.
- Provider-latest mismatch is not proof that a main actor packet is spoofed
  when route-scoped session evidence exists. The resolver must first bind the
  requested actor, role, session id, parent/delegation route, repo scope, and
  target ref; only then may it reject stale, spoofed, or ambiguous sessions.
- Authority lookup uses a route key such as
  `(actor_id, actor_role, session_id, target_ref, parent_actor_id,
  delegation_id, repo_scope)` plus typed grants.
- Subagents default to read-only auxiliary evidence roles. They cannot mutate,
  close review, approve bypass, act as operator, or become source-session
  authority for a parent actor unless a typed role/capability grant explicitly
  says so.
- Subagent evidence is revision-scoped. A helper result generated against an
  older plan SHA or before a packet arrival invalidation may be cited only as
  historical evidence unless the current-plan resolver confirms it still applies.
- Mutable fanout requires existing `safe_to_fanout`, disjoint write scopes,
  registered worktrees, and live mutation leases. Read-only audit fanout may run
  sooner, but its output routes back as findings/evidence, not implementation.

Deliverables:

- Extend `AgentMindSlice` projection or its writer with route metadata:
  `actor_id`, `actor_role`, `session_id`, `parent_actor_id`, `parent_session_id`,
  `delegation_id`, `runtime_role`, `repo_scope`, and `authority_scope`.
- Include `plan_revision_id`, `plan_source_hash`, `target_ref`, `started_at`,
  `completed_at`, and `freshness_state` in sidecar/agent-mind evidence that is
  used for plan or packet decisions.
- Preserve provider-latest projections for dashboards, but write or derive
  route-scoped projections so source-session validation can ask for the main
  actor/session rather than "latest provider."
- Teach `SourceSessionAuthorityResolver` to reject provider-latest ambiguity
  when multiple route-scoped candidates exist.
- Teach review-channel post validation to authenticate the explicit posting
  session through the same route-scoped resolver. If only provider-latest data
  exists and it points at a sidecar/subagent while the caller claims the main
  reviewer, return a typed `agent_mind_route_ambiguous` blocker naming the
  repair row instead of accepting the sidecar id or rejecting the main session
  as a final spoof verdict.
- Add tests proving:
  - a subagent `AgentMindSlice` cannot overwrite main reviewer session
    authority;
  - a provider-latest projection is rejected as ambiguous when route metadata is
    missing;
  - a route-scoped main actor projection can authenticate the source session;
  - read-only subagent evidence can be cited by the reviewer without granting
    mutation or closure authority.
  - a read-only subagent refresh of `<provider>_latest.json` does not prevent
    the main reviewer from posting a scoped review packet when route-scoped
    actor/session evidence proves the main session.
  - stale sidecar summaries from an older plan revision cannot become current
    plan authority or override a fresher packet-arrival invalidation.
- Keep all fanout policy under existing collaboration mode / repo-pack
  contracts. Do not add a parallel subagent registry.

Closure:

- `MP-GUARDIR-V4-PHASE-0-6-D-AGENT-MIND-SCOPE-S1` has tests and a
  `PlanRowClosureReceipt` or explicit governed exception before agent-mind
  projection can be used by source-session authority.
- `devctl develop collaboration-profile --role-count <role>=<n>` or equivalent
  profile output shows bounded fanout, route-scoped sessions, and blocked
  mutable fanout when leases/worktrees are absent.

## Work Stream A.0: CodeIdentity Receipt Prerequisite

Goal: unblock Work Streams A, C, and B by adding the proof-binding field that
lets push receipts, CI artifact receipts, and ProofIndex rows describe the same
code snapshot.

Live evidence:

- Claude's A.0 implementation added `GitMutationProofReceipt.code_identity_hash`
  to the runtime dataclass, but a v4.35
  `check_platform_contract_closure.py --format md` run still failed
  `runtime_contract::GitMutationProofReceipt` with extra field
  `code_identity_hash`. This is expected live evidence that A.0 is not closed
  until the platform contract row, registry/fixtures, emitters, and tests compose
  with the new field.

Deliverables:

- Add backward-compatible `code_identity_hash: str = ""` to
  `GitMutationProofReceipt` in
  `dev/scripts/devctl/runtime/git_mutation_proof_receipt.py`.
- Extend `build_commit_git_mutation_proof_receipt()` and any push/cloud-artifact
  receipt helper signatures to accept the value without breaking old callers.
- Bind the field to `CodeIdentity.identity_hash` when a `CodeIdentity` is
  available; emit the empty default only for legacy receipt reads.
- Add valid and invalid schema fixtures that prove the field is accepted and
  remains string-typed.
- Add a focused regression proving legacy receipt JSON still loads and new
  receipts carry `code_identity_hash`.
- Update the platform contract row and schema/fixture surfaces so
  `GitMutationProofReceipt.code_identity_hash` is a registered field, not runtime
  drift.

Closure:

- `FeatureProofReceipt.real_life_test_status=proven_passed` cites the focused
  pytest node.
- `PlanRowClosureReceipt` closes
  `MP-GUARDIR-V4-WORK-STREAM-A0-CODE-IDENTITY-RECEIPT-S1`.
- Work Stream A cannot start until this field exists on disk and the builder
  accepts it.
- `check_platform_contract_closure.py --format md` no longer reports
  `GitMutationProofReceipt` runtime-field drift for `code_identity_hash`.

## Work Stream A: GuardIR Push Routing

Deliverables:

- Do not implement branch-upstream-wins behavior again. It already ships in
  `dev/scripts/devctl/governance/push_routing.py:116-129`; keep a regression
  test so it does not regress.
- Block explicit policy/upstream mismatch instead of falling back to
  `origin/develop`.
- Dogfood push must consume the current `PushAuthorizationRecord` as controller
  authority per `dev/active/remote_commit_pipeline.md:247`; reject push if
  `pipeline_id` is absent or expired.
- Dogfood push must exercise `GitMutationProofReceipt` end to end:
  `claimed_sha -> verified_local_sha -> verified_remote_sha`.
- Dogfood push must populate `GitMutationProofReceipt.code_identity_hash` when
  a `CodeIdentity` was built for the same HEAD.
- Use existing `BypassLifecycle` for emergency push-routing bypass:
  `BypassRequest(reason="stale_origin_routing_emergency") -> BypassEvaluation
  -> BypassReceipt(authority_scope=EDIT_COMMIT_AND_PUSH)`. If `--no-verify` is
  necessary, emit `RawGitBypassReceipt`.
- Add regression for the current extraction branch using GuardIR refs.
- Dogfood governed `devctl push --remote guardir --execute`.

Closure:

- `FeatureProofReceipt` with resolvable pytest node.
- `FeatureProofReceipt` session/CLI dogfood fields for push command output.
- Plan-row closure query view grouped by `slice_id`.
- `PlanRowClosureReceipt` for Work Stream A rows.
- Active `BypassReceipt` ref if the no-verify emergency path is used.
- Active `PushAuthorizationRecord.pipeline_id`.
- `GitMutationProofReceipt` proving the push reached the verified remote SHA.

Operator visibility:

- push report shows GuardIR refs and no `origin/develop` range.
- bypass lifecycle / raw-git bypass report shows scoped emergency bypass if
  used.
- push authorization state shows the consumed `PushAuthorizationRecord`.

## Work Stream B: ProofIndex MVP

Work Stream B starts after Work Stream C has emitted at least one typed proof
artifact or local equivalent. B indexes proof receipts and cloud findings; it
does not invent their artifact contract.

Deliverables:

- `CodeIdentity`
- `GitMutationProofReceipt.code_identity_hash`
- stale-finding/proof-ref extension for stale proof applicability
- append-only `dev/state/proof_index.jsonl`
- startup proof consumption
- `devctl context-graph --concept proof --query <sha> --format md|json`

Closure:

- Feature proof cites proof-index tests and session/CLI dogfood fields.
- DogfoodSelfCheckReceipt proves fresh startup consumes proof summary.

Operator visibility:

- `devctl context-graph --concept proof --query HEAD --format md` renders
  current proof state.
- fresh startup JSON exposes consumed/current proof summary.

## Work Stream C: CI Artifact Ingest

Work Stream C precedes Work Stream B in the v4.8 cascade because CI artifacts
feed the ProofIndex. A local artifact-equivalent path is acceptable for dogfood
when remote CI is unavailable, but it must emit the same typed JSON shape.

Deliverables:

- `.github/workflows/governance_cloud_proof.yml`
- typed `proof_receipt.json`
- typed `cloud_findings.json`
- artifact ingest command
- governance-review and FindingBacklog mirror
- `devctl review-channel --action ingest --ingest-type cloud-findings`
- `devctl dashboard --view findings-status`
- `devctl context-graph --concept validation`
- `devctl graph-walk --to proof`
- The workflow must emit receipts that satisfy existing
  `check_feature_has_proof_receipt.py --require-proven-passed` enforcement in
  release/tooling CI.
- Reuse the downstream `workflow_run` chain pattern from
  `.github/workflows/coderabbit_ralph_loop.yml`.
- Match the typed-JSON artifact contract pattern from
  `.github/workflows/adopter_portability.yml`.
- Parameterize by `PlanIntakeConfig` so second and third adopter repos require
  zero workflow patches. This is required for Second-Repo Proof Ladder gates 6
  and 7 in `dev/active/portable_code_governance.md`.
- `proof_receipt.json` is a post-mutation CI artifact indexed by
  `CodeIdentity`. It is complementary to ADR-013 `RuntimeAgreementReport`,
  which is a pre-mutation gate indexed by `pipeline_id`; neither replaces the
  other.

Closure:

- workflow_dispatch proof on `greenfield_python`
- artifact download and local ingest
- current/stale finding tests

Operator visibility:

- `devctl dashboard --view findings-status --findings-filter status=current`
- `devctl graph-walk --from <HEAD> --to proof --format mermaid`
- GitHub Actions run URL cited as dogfood invocation evidence.

## Work Stream D: Safe Continuation And Tier Split

Deliverables:

- `SafeContinuationDecision`
- path-overlap detector
- runtime/CI/both guard tier map
- check-router consumption
- `devctl dashboard --view runtime-tiers`
- `devctl develop next --include-safety-decision`

Closure:

- long-CI-pending scenario dogfood returns safe/wait/divert.
- runtime tier map promoted to typed authority.

Operator visibility:

- `devctl dashboard --view runtime-tiers --format md`
- `devctl develop next --include-safety-decision --format json`

## Work Stream E: Connectivity Debt Reduction

Goal: reduce the measured connectivity backlog before adding more substrate.
Current baseline from `check_contract_connectivity --absolute`: 223 orphans,
131 duplicates, 33 stranded consumers, and 405 bidirectional findings. v4.8
must shrink that number by composing existing contracts and policies, not by
adding a new connectivity framework.

This work stream also owns the "connect and condense" rule for system growth:
new v4 authority must register through existing contract, system-map,
context-graph, repo-pack, and active-plan surfaces. It does not create another
source-of-truth document, duplicate-system auditor, or parallel role/session
store.

Deliverables:

- Enable `scope=internal_only` as an acceptable policy classification for
  contract-connectivity findings when the classifier proves the contract has
  only internal importers. This is a policy decision, not a schema fork.
- Wire the `ActionRoutingDecision`, `AgentLaneDecision`, and
  `LaneEditGateDecision` cluster through `authority_snapshot_build.py` and
  `startup_context.py` so startup authority consumes the existing typed routing
  results instead of raw dict rebuilds.
- Consolidate the `PushEnforcementSnapshot` / `PushEnforcement` duplicate
  cluster by choosing one canonical contract plus a snapshot/runtime variant, or
  by deprecating the lower-authority copy with importer migration metadata.
- Add typed import facades for governance bootstrap result contracts such as
  `StarterSetupGuideResult`, `StarterRepoPolicyResult`, and
  `GovernanceBootstrapResult` so one-shot adoption outputs are discoverable by
  connectivity scans.
- Wire new v4.8 contracts immediately: `CodeIdentity` must be consumed by proof
  summary/startup proof paths, and `IngestFailureReceipt` must be consumed by
  the ingest CLI and failure reporting. New contracts cannot enter the orphan
  pool.
- Run existing duplicate and authority-store checks before adding any new store
  or contract family: `check_contract_connectivity.py`,
  `check_typed_namespace_composition.py`,
  `check_contract_registry_composite_key_uniqueness.py`,
  `check_state_store_authority.py`, and
  `check_systemmap_covers_contract_registry.py`.
- `SYSTEM_MAP.md` and `context-graph` are navigation/discovery projections over
  typed inputs. Work Stream E may add registry/connectivity inputs that improve
  those projections, but it must not make prose in SYSTEM_MAP an authority
  source.
- VoiceTerm-specific literals discovered in portable/runtime layers must be
  either moved behind `ProjectGovernance`, `RepoPack`, `RepoPathConfig`, or an
  adopter-pack boundary, or marked as explicit product-shell debt with an owner
  row. VoiceTerm remains one adopter/client, not portable governance authority.

Repo-pack / adopter-boundary evidence to track under
`MP-GUARDIR-V4-WORK-STREAM-E-REPO-PACK-ADOPTER-BOUNDARY-S1`:

| Surface | Current smell | Required resolution |
|---|---|---|
| `dev/config/devctl_repo_policy.json` | mixed `guardir` pack identity with VoiceTerm names, Rust commands, and `quality_presets/voiceterm.json` inheritance | split product/adopter policy from portable GuardIR policy or mark each compatibility entry as adopter-pack debt |
| `dev/scripts/devctl/platform/extension_bundle_defaults.py` | `GUARDIR_EXTENSION_BUNDLE` reuses VoiceTerm bundle defaults | make reuse an explicit compatibility shim with migration owner, or define portable defaults |
| `dev/scripts/devctl/repo_packs/__init__.py` | `active_path_config()` can default to `VOICETERM_PATH_CONFIG` | portable mode requires explicit `RepoPack` / `RepoPathConfig` selection |
| `app/operator_console/*` path config imports | operator-console surfaces import VoiceTerm path config directly | keep as product-client wiring or route through typed surface ownership |
| `daemon_client.py` socket default | `~/.voiceterm/control.sock` is product-specific | keep only in VoiceTerm client boundary; never use as shared GuardIR lifecycle authority |
| `dev/config/templates/claude_instructions.template.md` | bridge prose fallback can read as live authority | route to typed state and projection-only boot-card language |
| portable hook stubs | some generated stubs hardcode a repo-pack label | `.template.sh` variants are canonical; generated hooks must prove selected pack provenance |

Closure:

- `check_contract_connectivity.py --absolute` returns `ok: true`, or returns
  only explicitly accepted policy exemptions with stable counts and rationale.
- `check_state_store_authority.py`, `check_active_plan_sync.py`,
  `check_systemmap_covers_contract_registry.py`, and any selected portability
  check for repo-pack / VoiceTerm leakage pass or emit typed findings routed
  through `PlatformFindingIngest`.
- A focused repo-pack portability test proves portable GuardIR consumers do not
  silently fall back to `VOICETERM_PATH_CONFIG`; missing repo-pack/path config
  must resolve through `ProjectGovernance` / `RepoPack` or fail closed with a
  typed adopter-boundary blocker.
- `FeatureProofReceipt.real_life_test_status=proven_passed` cites focused
  pytest nodes for each importer/policy change.
- `PlanRowClosureReceipt` closes
  `MP-GUARDIR-V4-WORK-STREAM-E-CONNECTIVITY-DEBT-S1`.

Operator visibility:

- Contract-connectivity report shows internal-only accepted counts separately
  from true orphans.
- Dashboard or context-graph surface can show before/after counts for orphan,
  duplicate, stranded, and bidirectional findings.

## Work Stream F: Raspberry Pi Edge Device Pack

Goal: add Raspberry Pi as the first embedded-device adopter pack and optional
role-execution target for GuardIR. The Pi is an always-on edge helper for
solo-dev workflow: LED projection, background checks, edge proof runs, evidence
cache, physical button assertions, and opt-in deterministic/light-AI role
execution. It is never a parallel authority. It reads typed state, projects
typed state, and emits typed evidence through existing ingest paths.

Operator hardware target:

- Raspberry Pi 4, 4GB RAM.
- Ubuntu Server 24.04 LTS 64-bit.
- Pimoroni Blinkt! 8 RGB LED HAT on GPIO 23/24.
- USB 3.0 SSD recommended over microSD for check/report I/O.
- `gpiozero` plus `lgpio` backend for Ubuntu 24.04; `RPi.GPIO` is not the
  target path.
- SSH-only inbound, no public ports, mDNS `pi.local` through `avahi-daemon`.

### F.0 Active Role Substrate Boundary

The Pi does not own CognitiveRoleFleet authority. It is a deployment target for
existing MP-377 / cached-hammock CognitiveRoleFleet assignments.

Implementation rule:

- Extend existing role assignment/config shapes with `RoleExecutionTarget` /
  `deployment_location`.
- Do not create a parallel `CognitiveRoleFleetConfig` authority if the existing
  P56 config path can be extended.
- Default enabled roles: `watcher` and `governance_receipt_aggregator`.
- Optional light-AI roles remain disabled until explicitly toggled by operator
  policy.
- Heavy-AI roles always route to dev-machine agents through typed packets.

Role classification:

| Role | Tier | Where it runs | Receipt contract | Existing devctl primitive |
|---|---|---|---|---|
| Governance Receipt Aggregator | deterministic | Pi systemd | existing receipt rollups | aggregate typed JSONL receipts |
| Watcher | light_ai | Pi + local LLM | `WatcherEpisode` | agent-mind / peer-awareness reads |
| Round Orchestrator | light_ai | Pi + local LLM | `OrchestratorDecision` | `develop next --actor <agent>` |
| Codex Research | light_ai | Pi + local LLM for local summaries only | `CodexResearchFinding` | plan-index / git-log summaries |
| Duplicate Scope Guard | light_ai | Pi + local LLM for classification only | `DuplicateScopeGuardReport` | connectivity, duplication, jscpd reports |
| Dogfood Test | light_ai routing over existing test execution | `DogfoodRecord` | `devctl test-python --suite devctl` |
| Implementation Command | heavy_ai | dev machine | existing `FeatureProofReceipt` | code, stage, commit, proof |
| Architecture Review | heavy_ai | dev machine | existing architecture-review receipt path | ARCHITECT workstream |

Local LLM constraints are advisory deployment constraints, not authority:
Llama 3.2 1B Instruct Q4_K_M through ollama may classify, summarize, and route
bounded evidence only. It must not generate code, mutate state, approve bypass,
or act as operator. The budget is max 128 output tokens, temperature 0.2, one
concurrent request, and a 30 second hard timeout.

### F.1 Slash Entry Point And Thin Adapter

Deliverables:

- Add `.claude/commands/raspberry-pi.md`, mirroring the existing slash-command
  adapter pattern in `.claude/commands/agent-spawn.md`,
  `.claude/commands/develop.md`, `.claude/commands/goal.md`, and siblings.
- The slash command is a projection/adapter only. It must not contain policy.
- Route all actions to
  `python3 dev/scripts/devctl.py edge --device raspberry-pi <args>`.
- Add `dev/scripts/devctl/commands/edge/` with actions:
  `status`, `led-state`, `cache-sync`, `watchdog`, and `approve`.
- Wire the command through the existing devctl command parser/handler path.
- Add `raspberry-pi.md` to slash-command entry-point tests.

Operator visibility:

- `/raspberry-pi status` renders device state, LED projection state, daemon
  freshness, cache freshness, and last emitted findings.
- `/raspberry-pi led-state` renders the projected LED state without writing to
  hardware.

### F.2 LED Projection

Add `LifecycleLEDState` as a projection-only contract.

File: `dev/scripts/devctl/runtime/lifecycle_led_state.py`

Store: latest projection at
`dev/reports/edge_device/<device_id>/led_state_latest.json`

Fields:

- `led_index`
- `color_hex`
- `blink_pattern`
- `projected_state_kind`
- `projected_state_value`
- `computed_at_utc`
- `contract_id`
- `schema_version`

LED projection inputs must cite typed sources such as `AgentPacketAttention`,
`PeerAwarenessPolicy`, `BypassLifecycle`, `GitMutationProofReceipt`,
`FeatureProofReceipt`, guard reports, review-channel state, and plan-source
freshness evidence.

Initial signal set:

- channel paralysis
- bypass expiry approaching
- agent alive / agent stale
- plan-row stalled
- test or guard failure
- push authority ready
- inbox poll overdue
- CI / cloud proof in flight
- untyped git mutation detected
- stale plan source
- multiple concurrent blockers
- bypass active
- healthy baseline

The LED daemon may use `blinkt` when available. If `blinkt` or GPIO backends are
missing, the command must still render the JSON projection and report hardware
capability unavailable.

### F.3 Background Daemons

Implement as systemd timer templates installed only when the Raspberry Pi repo
pack is enabled. Each timer wraps an existing devctl primitive; it must not
write directly to typed state.

| Timer | Schedule | Existing primitive | Output |
|---|---|---|---|
| `pi-bypass-expiry.timer` | every 5 min | bypass status / lifecycle read | LED amber if TTL < 5 min |
| `pi-codex-poll-watcher.timer` | every 3 min | agent-mind / peer awareness read | finding if peer inbox overdue |
| `pi-worktree-drift.timer` | every 30 min | `git status --short` | finding if drift exceeds policy |
| `pi-plan-source-freshness.timer` | every 10 min | `shasum -c dev/audits/plan_intake/sha256-manifest.txt` | finding on drift |
| `pi-agent-mind-poller.timer` | every 3 min | agent-mind for Codex and Claude | typed delta event |
| `pi-jscpd-refresher.timer` | daily | jscpd duplication audit | refresh stale duplication report |
| `pi-connectivity-check.timer` | every 30 min | `check_contract_connectivity --absolute` | connectivity delta finding |
| `pi-push-authority-ttl.timer` | every 5 min | push/bypass receipt TTL read | LED amber if expiring |
| `pi-watchdog-rollup.timer` | hourly | watchdog episode aggregation | hourly rollup JSONL |
| `pi-channel-paralysis.timer` | every 1 min | `review-channel --action status --terminal none` | LED red if blocked > policy |

All timer findings write to
`dev/reports/edge_device/<device_id>/findings.jsonl` and reduce through the
existing governance-review ingest path. There is no Pi-specific shortcut into
`dev/state`.

### F.4 Routing And Edge Proof Use Cases

This phase is deferred until F.1-F.3 are stable.

Use cases:

- self-hosted CI runner that executes a local equivalent of
  `governance_cloud_proof.yml` and emits `proof_receipt.json` /
  `cloud_findings.json` bound to `CodeIdentity`
- evidence cache mirroring `dev/state/proof_index.jsonl`,
  `dev/state/plan_index.jsonl`, schema fixtures, and selected reports
- background heavy-check runner invoked by SSH from the dev machine
- offline ProofIndex cache for local-network use
- GitHub Actions status aggregator using a read-only token or no GitHub token

Pi-to-agent routing:

- Pi may post routing packets with `from_agent="system"` only as a compatibility
  label already accepted by packet-agent validation.
- `from_agent="system"` is not capability authority and never grants mutation
  permission.
- Actor authority resolves from typed `CollaborationSession`,
  `target_role`, `target_session_id`, and the relevant lifecycle receipt.
- Pi packets target dev-machine sessions for heavy-AI work and cite the
  role-output receipt as evidence, for example
  `evidence_ref=orchestrator_decision:<receipt_id>`.
- Operator visibility mirrors pending role assignments at
  `dev/reports/edge_device/<device_id>/pending_role_assignments.jsonl`.

Swarm integration:

- Phase F.4.a: Pi as findings aggregator through cron/systemd; no swarm changes.
- Phase F.4.b: Pi as remote worker through SSH dispatcher; add
  `AgentTask.device_id` and caller-supplied repo root/worktree identity.
- Phase F.4.c: dynamic Pi allocation in swarm feedback sizing, after remote
  dispatch is stable.
- Replace `swarm_core` `cwd=REPO_ROOT` assumptions with caller-supplied repo
  root / worktree identity before remote-dispatch mode can be enabled.

Trust model:

- Pi credentials are separate from the dev machine.
- Pi may have its own SSH key and optional read-only GitHub token.
- Pi cannot push to the repo.
- Pi cannot mutate `dev/state` directly.
- Pi emits typed edge findings and proof artifacts only.

### F.5 Active Role Receipts

New receipts are role-output evidence only; they are not authority systems.

- `WatcherEpisode`: observed source refs, cursor, findings emitted, freshness
  status, and evidence refs.
- `OrchestratorDecision`: proposed assignment, target role/session, reason
  digest, confidence, and evidence refs.
- `CodexResearchFinding`: local claim investigated, source refs, verdict, and
  uncertainty.
- `DuplicateScopeGuardReport`: duplicate-scope candidates, classifier output,
  and accepted/rejected resolution refs.

Reuse existing `DogfoodRecord` for Dogfood Test instead of adding a new
`DogfoodRun` contract.

### F.6 Security And Physical Approval

Add `OperatorPhysicalApprovalReceipt` as a scoped physical-button assertion
contract. It proves a device-bound button press; it does not grant operator
identity and it does not grant edit, commit, or push authority.

File: `dev/scripts/devctl/runtime/operator_physical_approval_receipt.py`

Fields:

- `receipt_id`
- `button_press_at_utc`
- `device_id`
- `device_manufacturer_serial`
- `signed_assertion`
- `approval_target_packet_id`
- `approval_scope`
- `ttl_seconds`
- `contract_id`
- `schema_version`

Signature rule:

- `signed_assertion` is an HMAC-SHA256 hex digest over
  `device_id | button_press_at_utc | approval_target_packet_id | approval_scope
  | nonce`.
- Device secret lives at `/etc/guardir/device.key` with `0600` permissions.
- Device identity lives at `/etc/guardir/device.id`.
- Dev machine verifies signatures against `.guardir/device_registry.json`.
- `dev/config/revoked_devices.json` rejects compromised or retired devices.

Approval scopes:

- allowed: `read_only`, `findings_ingest`
- forbidden: `edit_only`, `edit_commit`, `edit_commit_push`, raw git push,
  raw commit, raw bypass

Physical approval can be evidence for promoting an edge finding into an
existing ingest action. It cannot approve a `BypassReceipt` for mutation.
Mutation bypass authority remains the existing typed
`BypassRequest -> BypassEvaluation -> BypassReceipt -> BypassExpiry` chain.

### F.7 Repo-Pack Registration

Add repo pack `dev/scripts/devctl/repo_packs/raspberry_pi.py`, mirroring the
existing `voiceterm.py` pattern but declaring edge-device capabilities.

Add `EdgeDeviceCapability` as the repo-pack capability contract.

Fields:

- `device_kind`
- `os_identifier`
- `gpio_available`
- `led_pin_count`
- `usb_serial_available`
- `storage_path`
- `log_path`
- `network_addresses`
- `contract_id`
- `schema_version`

Add policy `dev/config/devctl_policies/raspberry_pi.json` with
`edge_devices.raspberry_pi.enabled: false` by default.

### F.8 Edge Findings

Prefer existing `Finding`, `FindingBacklog`, `governance_review`, and
FeatureProofReceipt paths. If an edge-specific source envelope is required,
define `EdgeFindingReceipt` only as a source envelope that reduces into the
existing findings pipeline.

`EdgeFindingReceipt` must include:

- `receipt_id`
- `device_id`
- `finding_id`
- `finding_kind`
- `source_command`
- `source_digest`
- `emitted_at_utc`
- `target_ref`
- `severity`
- `governance_review_ingest_ref`
- `contract_id`
- `schema_version`

It is not authority and is not a parallel finding store.

### F.9 Closure

Closure receipts:

- `PlanRowClosureReceipt` for
  `MP-GUARDIR-V4-WORK-STREAM-F-RASPBERRY-PI-EDGE-PACK-S1`.
- `FeatureProofReceipt.real_life_test_status=proven_passed` with concrete
  pytest nodes.
- Session/CLI dogfood fields on `FeatureProofReceipt` for actual
  `/raspberry-pi status` or `devctl edge --device raspberry-pi status`
  invocation.
- Existing plan-row closure query view grouped by work stream. Do not add a
  standalone `SliceClosureReceipt`.
- Active role substrate closure cites `MP-GUARDIR-V4-WORK-STREAM-F-ROLE-SUBSTRATE-S1`
  only when the Pi role runner is enabled by policy. When disabled, convergence
  records `disabled_optional` for Work Stream F role-runner status.

Required pytest nodes:

- `test_raspberry_pi_slash_command_translates_to_devctl_edge`
- `test_edge_device_capability_repo_pack_loads`
- `test_lifecycle_led_state_projection_no_authority_mutation`
- `test_pi_background_daemons_emit_findings_only_no_mutations`
- `test_operator_physical_approval_receipt_hmac_verify_round_trip`
- `test_operator_physical_approval_receipt_scope_read_only_or_findings_ingest`
- `test_revoked_devices_allowlist_rejects_signatures`

Recommended rollout order:

1. F.1 slash command and read-only `devctl edge` skeleton.
2. F.2 LED projection JSON, then optional hardware writer.
3. F.3 background timers emitting findings only.
4. F.4 edge proof/cache/routing use cases.
5. F.5 physical approval after HMAC and revocation tests pass.

## v4.8 Finding Routing Discipline

All v4.8 findings route through the canonical governance review path. Do not add
parallel finding ledgers.

| Finding source | Routing path |
|---|---|
| Pi `WatcherEpisode` | `EdgeFindingReceipt` -> `PlatformFindingIngest.record_review_input()` -> `dev/reports/governance/finding_reviews.jsonl` |
| Pi `DuplicateScopeGuardReport` | `EdgeFindingReceipt` -> `PlatformFindingIngest.record_review_input()` -> `dev/reports/governance/finding_reviews.jsonl` |
| Pi `CodexResearchFinding` | `PlatformFindingIngest.record_review_input()` -> `dev/reports/governance/finding_reviews.jsonl` |
| Phase 0.6.E ingest failure | `IngestFailureReceipt` plus `governed_exception_lifecycles.jsonl` link; no duplicate ledger |
| Work Stream C cloud finding | existing `PlatformFindingIngest` mirror into `dev/reports/governance/finding_reviews.jsonl` |
| Audit receipts | typed JSON under `dev/reports/governance/audit_receipts/`; they are proof evidence, not finding queues |

`PlatformFindingIngest` remains the only reducer that promotes v4.8 findings
into governance review state.

## Cross-Work-Stream Failure Modes

| Failure | Detection | Recovery |
|---|---|---|
| CI artifact missing | ingest returns `artifact_missing` | emit IngestFailureReceipt and stale-finding proof ref; local fallback |
| CodeIdentity drift | ProofIndex tree/file hash mismatch | mark GitMutationProofReceipt stale via stale-finding proof ref; suppress startup consumption |
| Stale plan snapshot | source hash mismatch | block work-stream start |
| Channel blocked mid-handoff | ControlDecisionObeyedGuard violation | post task_blocked and return to Phase 0.6.A |
| Startup repair loops without command | `agent-loop` reports `repair_startup_authority` / `startup_authority_failed` with no allowed actions, no active override, and only the same self-referential loop command | repair `MP-GUARDIR-V4-PHASE-0-6-A-STARTUP-REPAIR-COMMAND-S1`; emit a typed owner/target/command or stop_anchor before further handoff |
| Emitted next command fails its own guard | `develop next`, `agent-loop`, or final-response gate emits a concrete command, but running it returns `ControlDecisionObeyedGuard` / `control_decision_obedience_failed` | repair `MP-GUARDIR-V4-PHASE-0-6-A-NEXT-COMMAND-OBEDIENCE-S1`; command emitters must include needed control-decision/proxy authority or mark the command unrunnable |
| Final gate emits conflicting or stale actor command | continuation, final gate, reviewer response shape, and operator command wrappers disagree; or a Codex reviewer is told to execute `--actor claude` for old packet debt | repair `MP-GUARDIR-V4-PHASE-0-6-A-NEXT-COMMAND-OBEDIENCE-S1`; select one current semantic blocker or emit typed `final_gate_command_conflict` |
| Command actor parsing forks across consumers | `develop`, final gate, response shape, or operator wrappers each parse `--actor` / proxy state with separate helpers, or peer commands are hidden instead of classified as non-executable status | repair `MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1`; centralize command-envelope classification over existing proxy/attempted-action contracts and render peer commands only as status unless proxy-authorized |
| Command mutation risk unclassified | command-envelope/action matching sees `git stash`, `git reset`, `git checkout`, `git restore`, `git clean`, `git apply`, shell redirection, heredoc, herestring, or `tee` writes as generic shell/validation commands | repair `MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1` and `MP-GUARDIR-V4-PHASE-0-6-A-MUTATION-METHOD-PROVENANCE-S1`; classify mutation risk before rendering/executing |
| Command mutation allowlist forks across consumers | command envelope has mutation-risk classification but `control_decision_action_matching`, advisory role filters, `action_routing`, final-response executable checks, or consistency guards still use local substring lists that miss `git clean`, `git reset`, `git restore`, `git apply`, shell redirects, or `tee` writes | repair `MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1`, `MP-GUARDIR-V4-PHASE-0-6-A-NEXT-COMMAND-OBEDIENCE-S1`, and `MP-GUARDIR-V4-PHASE-0-6-A-MUTATION-METHOD-PROVENANCE-S1`; make those consumers use the shared classifier or a registered adapter |
| Text-command-only convergence leaves typed-action consumers behind | `classify_command_mutation()` covers shell command text, but final-gate executable checks, typed action routing, or consistency guards still inspect `next_action` / action identifiers through local token lists and ignore destructive `next_command` values | extend the shared classifier through a registered typed-action/next-command adapter; prove `may_mutate=false` plus destructive `next_command` fails consistency and final gate does not call governed mutation commands executable without mutation authority |
| Shared command classifier imports higher-level consumer | wiring a consumer to the shared classifier creates an import cycle such as `control_decision_obedience -> control_decision_action_matching -> command_envelope_classification -> control_decision_obedience`, breaking `review-channel`, `agent-mind`, `session`, or `test-python` before typed findings can be posted | repair `MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1` and `MP-GUARDIR-V4-PHASE-0-6-C-COORDINATION-LANE-IMPORT-ISOLATION-S1`; move shared helpers to neutral leaf modules and keep coordination commands import-isolated |
| Closure packet blocked after valid handoff | `task_started` is accepted but implementer `task_produced` or reviewer `review_accepted` is rejected by `ControlDecisionObeyedGuard` | repair `MP-GUARDIR-V4-PHASE-0-6-A-TASK-PRODUCED-GUARD-REPAIR-S1`; promote offline evidence into typed recovery packet; do not start Work Stream A |
| Closure packet structurally valid but semantically wrong | cascade predicate accepts packet-shaped evidence while target session, target role, parent status, parent kind, source/target peer, or target ref does not match the parent packet; includes `review_accepted` accepting `task_progress` instead of final `task_produced` | reject through `MP-GUARDIR-V4-PHASE-0-6-B-CASCADE-PARENT-AUTHORITY-S1`; do not accept packet-regex-only lineage |
| Reviewer packet read blocked | `review-channel show`, `inbox`, `status`, or `history` is rejected by `ControlDecisionObeyedGuard` for a scoped read-only reviewer | repair `MP-GUARDIR-V4-PHASE-0-6-C-REVIEW-READ-AUTHORITY-S1`; record PacketBodyObservation; do not promote offline files into a parallel lifecycle channel |
| Coordination lane import-coupled to broken implementation command | a syntax/import-time failure in an implementation-owned command module such as `devctl.commands.development.report` prevents unrelated `review-channel`, `agent-mind`, `session`, or recovery/status commands from importing | repair `MP-GUARDIR-V4-PHASE-0-6-C-COORDINATION-LANE-IMPORT-ISOLATION-S1`; isolate command-family imports, emit typed command-family import blockers, and preserve review-only packet coordination without reviewer mutation |
| Packet source session stamped as fallback | live agent `review-channel --action post` records source `session_id="local-review"` instead of the actor's typed session | repair `MP-GUARDIR-V4-PHASE-0-6-D-REVIEW-CHANNEL-SOURCE-SESSION-S1`; do not fake closure by targeting `local-review` |
| Packet source session spoofed | live agent `review-channel --action post` accepts an arbitrary non-fallback `session_id` with no typed actor/session proof | reject through `MP-GUARDIR-V4-PHASE-0-6-D-SOURCE-SESSION-AUTHENTICITY-S1`; resolve session authority from existing typed session/actor contracts, not a new registry |
| Valid parent stranded by session rotation | latest agent projection no longer matches the real source session on an older parent packet | repair `MP-GUARDIR-V4-PHASE-0-6-D-SOURCE-SESSION-CONTINUITY-S1`; verify post-time session authority or request a fresh parent packet, but do not weaken spoof rejection |
| Read-only subagent refresh blocks main actor post | `<provider>_latest.json` points at a sidecar/subagent session and `review-channel --action post` rejects the main actor's explicit session as stale/spoofed without checking route-scoped authority | repair `MP-GUARDIR-V4-PHASE-0-6-D-AGENT-MIND-SCOPE-S1`; authenticate by route key and typed grants, or emit `agent_mind_route_ambiguous` with owner/target/repair row |
| Bypass expires | BypassExpiry before closure | pause mutation and request renewal |
| Exception never closes | open lifecycle exceeds policy age | stale exception guard escalates |
| Bridge/memory conflicts typed state | projection-only guard | typed state wins |
| Push before artifact ingest | no current ProofIndex row | block with await-proof-ingestion |
| Closure ref missing proof | closure ref guard fails | reject closure |
| Competing bypass requests | same scope+target active | first approved wins |
| Plan agreement missing | missing dual `plan_ready_gate` packets for plan SHA | block implementation task_started |
| Peer inbox not watched | stale `AgentPacketAttention` / `PeerAwarenessPolicy` state | block plan_ready_gate or handoff packet |
| One-sided readiness | only Codex or Claude posted plan_ready_gate | continue plan review loop |
| Agent role forgotten mid-loop | startup, boot card, final gate, or agent response treats Codex as only a passive reviewer, Claude as not-current implementer, or a sidecar as main actor despite typed collaboration state | repair `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-BOOT-CONTINUATION-S1`; render role boot envelope and continue the typed packet loop |
| Stop/wake anchor pauses live lifecycle | `ScheduleWakeup`, `TASK_COMPLETE`, stop_anchor, or "nothing more to do" appears while a continuation anchor, packet goal, or peer response requires action | reject as `stop_anchor_conflicts_with_live_lifecycle`; continue, post typed progress/blocked packet, or require explicit `SessionTerminationPolicy` / `TaskCompleteDecision` authority |
| Pi role emits mutation request | role-output packet asks for edit/commit/push or operator authority | reject packet; reroute to dev-machine heavy-AI task with evidence refs only |
| Current plan authority ambiguous | `CurrentPlanAuthorityResolver` cannot bind the requested work to startup-visible typed `PlanRow` state | allow only ingestion, amendment, review, or recovery work; block implementation selection |
| Packet body treated as plan authority | a reducer, boot card, dashboard, agent loop, or agent selects implementation work directly from packet/offline-finding prose without an ingested `PlanRow` / plan-state update | treat the packet as evidence only; route to plan amendment or typed reducer ingestion, then select from the resulting plan row and cite the packet id as provenance |
| Reducer selects unrelated active target | startup/session/final gate reports checkpoint or active owner doc state that does not match the typed plan row under active packet/operator work | suspend implementation, keep the typed plan target, and repair `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1`; do not edit unrelated owner docs |
| Checkpoint budget suppresses coordination | `safe_to_continue=false` / `dirty_path_budget_exceeded` is treated as a blanket stop even though peer review/progress packets are needed to keep the typed lifecycle moving | block mutation/closure, but allow only scoped review-only coordination packets when role/session/parent/target proof and guard obedience agree; otherwise emit typed `checkpoint_coordination_conflict` |
| Authority snapshot action/grant split | `allowed_actions` includes a review-channel post action while `ActorAuthorityState` / `CapabilityGrantState` denies the same reviewer output lane | reject ambiguous execution, emit typed `authority_snapshot_inconsistent` blocker, and repair `MP-GUARDIR-V4-PHASE-0-6-A-REVIEW-FEEDBACK-POST-OBEDIENCE-S1` / `MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1` |
| Blocker metadata duplicated across reducers | `check_contract_connectivity.py` reports `AgentLoopDecision` <-> `BlockerSnapshot` or consumers drop blocker owner/target/reason/repair fields | compose `AgentLoopDecision`, `ControlPlaneReadModel`, `/develop`, final gate, dashboard, and status consumers from canonical `BlockerSnapshot`; add field-route parity tests instead of owning duplicate state |
| Reviewer mutates implementer-owned write set | reviewer edit/write/stage/commit targets a path covered by another session's live `MutationLease` | reject or revert reviewer mutation, emit typed finding, preserve implementer lease, return to `MP-GUARDIR-V4-PHASE-0-6-A-ROLE-MUTATION-LEASE-S1` |
| Shared-worktree VCS state mutation hides peer work | `git stash`, `git reset`, `git checkout`, `git restore`, `git clean`, `git apply`, or similar worktree/index mutation runs while peer dirty work or active peer leases exist | reject unless a typed worktree-scope lease/provenance receipt covers the full affected scope; use a clean worktree or governed checkpoint for verification isolation |
| Role/capability derived from provider default | provider label, reviewer mode, or remote-control fallback grants mutation or closure capability without typed role assignment/capability evidence | reject as `role_drift` / `unauthorized_mutation`; amend existing MP377 role rows and regrant capabilities through typed authority |
| Parallel authority system appears | new plan tracker, lifecycle store, finding ledger, duplicate-system auditor, projection authority, or mutation store bypasses registered contracts | reject the new store; extend existing PlanRow, lifecycle, finding, contract-connectivity, typed-namespace, and system-map surfaces |
| Generated instruction surface cannot route an agent | `AGENTS.md`, `CLAUDE.md`, slash templates, platform guides, or SYSTEM_MAP projections lack role-aware command discovery, current-plan routing, duplicate/system-map checks, packet lifecycle examples, or projection-only boundaries | repair `MP-GUARDIR-V4-PHASE-0-6-E-INSTRUCTION-SURFACE-USABILITY-S1`; regenerate from typed renderer inputs and sync guards rather than hand-editing projections |
| Instruction/role contract invisible to system graph | `InstructionBootCard`, `RoleInstructionCard`, `RoleGuard`, role customization contracts, or command classifications are rendered into projections but missing from contract-connectivity, system-map, context-graph, or guard chokepoints | repair `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-INSTRUCTION-CONNECTIVITY-S1`; connect existing contracts and command catalogs instead of adding another docs authority |
| Provider default acts as role authority | `codex=reviewer`, `claude=implementer`, unknown provider fallback, or role-profile defaults grant mutation, closure, packet-write, staging, commit, push, bypass, or proxy authority without typed session/capability proof | fail closed as `role_authority_missing`; allow only scoped read-only observation if read authority exists, then repair role-authority flow |
| Command catalog read/write class ambiguous | generated boot cards, slash templates, `SystemCatalog`, or parser metadata classify review-channel writes as generic read-only commands or omit the authority needed for packet writes | split read and write command classifications; route packet writes through `AgentLoopDecision` / `ControlDecisionObeyedGuard` and repair `MP-GUARDIR-V4-PHASE-0-6-E-ROLE-INSTRUCTION-CONNECTIVITY-S1` |
| VoiceTerm literal leaks into portable authority | shared governance/runtime/doc surfaces treat VoiceTerm path, product name, bridge, or repo-pack default as portable policy | move behind `ProjectGovernance` / `RepoPack` / `RepoPathConfig` or mark as adopter-pack debt; do not make VoiceTerm a global authority |
| GuardIR v4 becomes parallel plan authority | `MP-GUARDIR-V4-*` rows are consumed without parent refs to MP377-P0-T22/T22A-T22E or ingestion provenance | reject closure until `MP-GUARDIR-V4-PHASE-0-6-E-MP377-EXTRACTION-PARENTAGE-S1` binds the rows under MP-377 |
| Guide/navigation prose drives backend behavior | generated guides, SYSTEM_MAP, boot cards, or dashboard rows are cited as final authority without typed row/contract/receipt support | treat as projection drift; update typed inputs and sync guards, not backend behavior from prose |
| Work stream convergence missing | A-F have individual closures but no convergence receipt/status | keep system closure open; emit convergence blocker |
| Optional Pi disabled | Work Stream F role runner disabled by repo policy | record `disabled_optional` in convergence status; do not block A-E |
| Startup signal compact path drops v4 data | full startup has plan/proof data but compact projection omits it | block G.1/G.2 closure until full and compact startup paths expose bounded summaries |
| Proof chain backref missing | ActionResult, RunRecord, or ValidationReceipt lacks explicit reciprocal refs | reject closure and route to P102 receipt-DBC follow-up |
| Operator console bridge fallback remains | reader inventory finds bridge.md authority fallback | keep G.3 open under P188 checkpoint; bridge remains display-only until removed |
| Swarm remote worker assumes repo root | remote worker uses hardcoded `REPO_ROOT` instead of supplied worktree identity | disable Pi remote-dispatch mode; keep findings-aggregator mode only |

## Work Stream G: System-Level Integration Closure

Goal: prove that Work Streams A-F converge into one typed system rather than six
independent threads. G work is the operator's whole-system closure layer.
It is an aggregate proof and map/edge closure over existing authorities; it
does not independently approve or close any stream.

Required context-graph / system-map edges:

- `quality_signals.plan_intake -> WorkIntakePacket`
- `WorkIntakePacket -> ControlPlaneReadModel`
- `ControlPlaneReadModel -> AutoModeState`
- `AutoModeState -> develop next`
- `CodeIdentity -> startup_signals -> StartupContext quality_signals`
- `IngestFailureReceipt -> startup_signals -> StartupContext quality_signals`
- `TypedAction -> ActionResult -> RunRecord -> ValidationReceipt`
- `FeatureProofReceipt -> ActionResult`
- `WorkStreamConvergenceReceipt -> PlanRowClosureReceipt`
- `WorkStreamConvergenceReceipt -> FeatureProofReceipt`
- `WorkStreamConvergenceReceipt -> DogfoodSelfCheckReceipt`
- `operator_console typed-state-required source -> ControlPlaneReadModel`
- `bridge.md -> projection-only display`
- `CognitiveRoleFleetAssignment -> RoleExecutionTarget -> Pi edge pack`
- `WatcherEpisode / OrchestratorDecision -> review-channel packet evidence`

The current known visibility gap is that `context-graph --query MP-GUARDIR-V4`
and `system-picture` may not see plan-intake rows until Phase 0.6.E lands
`plan_intake_includes`; G depends on that edge rather than papering over it.

### G.1 WorkIntakePacket And AutoModeState Loop

- Make `WorkIntakePacket` a first-class input/backref on
  `ControlPlaneReadModel`.
- Persist the resolved `AutoModeState` loop state with the same intake /
  control-plane snapshot id.
- Wire `quality_signals["plan_intake"]` into WorkIntake and AutoMode decision
  points.
- Add focused proof `test_workintake_packet_consumes_plan_intake_summary`.
- Closure: `devctl develop next --actor <agent> --format json` includes the
  plan-intake context that shaped the next work decision.

### G.2 Startup Signals Stitch

- Add full startup loaders for plan intake, CodeIdentity, and ingest failures:
  `_load_plan_intake_summary()`, `_load_code_identity_summary()`, and
  `_load_ingest_failure_summary()`.
- Add compact startup propagation for the same summaries so compaction does not
  drop the evidence.
- Emit bounded `quality_signals["plan_intake"]`,
  `quality_signals["code_identity"]`, and
  `quality_signals["ingest_failures"]` projections.
- Add focused proof `test_startup_signals_loads_v4_new_contracts`.
- Closure: fresh session startup and compact startup both expose the bounded
  v4 rows/summaries.

### G.3 Bridge Severance Checkpoint

This composes with P188 bridge/runtime coordination. It is not a parallel bridge
retirement lane.

- Inventory operator-console readers that still consume `bridge.md` or bridge
  prose as authority.
- Prioritize the top fallback paths first, including snapshot and review-state
  loading.
- Move operator-console state consumers toward `ControlPlaneReadModel` as the
  primary source while keeping bridge text display-only.
- Add `check_no_operator_console_bridge_fallback.py` for authority fallback
  reads.
- Defer mobile MP-330/MP-331 bridge severance to its own owner.
- Closure: P188 S6/S7 checkpoint cites the reader inventory and the guard
  result.

### G.4 Action Proof Chain Backrefs

This composes with P102 receipt-DBC. It does not create a new proof authority.

- Add explicit reciprocal refs across existing stores:
  `TypedAction -> ActionResult -> RunRecord -> ValidationReceipt`.
- Add `validation_receipt_ids: tuple[str, ...]` to `RunRecord`.
- Add `typed_action_ref`, `run_record_ref`, and
  `feature_proof_receipt_ids: tuple[str, ...]` to `ActionResult` where the
  existing models permit extension.
- Add `run_record_ref` / reciprocal lookup support for `ValidationReceipt`.
- Bind FeatureProofReceipt and ValidationReceipt backrefs at emission time.
- Add focused proof `test_action_result_carries_validation_receipt_ids`.
- Closure: `devctl push --dry-run --format json` can traverse the full proof
  chain without bridge prose.

### G.5 WorkStreamConvergenceReceipt

File: `dev/scripts/devctl/runtime/work_stream_convergence_receipt.py`

Store: `dev/state/work_stream_convergence_receipts.jsonl`

Fields:

- `receipt_id`
- `plan_revision_id`
- `work_stream_statuses`
- `work_stream_a_closure_receipt_id`
- `work_stream_b_closure_receipt_id`
- `work_stream_c_closure_receipt_id`
- `work_stream_d_closure_receipt_id`
- `work_stream_e_closure_receipt_id`
- `work_stream_f_closure_receipt_id`
- `end_to_end_dogfood_session_proof_id`
- `converged_at_utc`
- `contract_id`
- `schema_version`

`work_stream_statuses` maps each stream to one of:
`closed`, `deferred_by_policy`, `disabled_optional`, or `blocked`.

Work Stream F edge/role closure is required only when the Raspberry Pi pack or
role runner is enabled by repo policy. Otherwise the convergence receipt records
`disabled_optional` or `deferred_by_policy` for F and still proves A-E.

End-to-end dogfood sequence:

1. Phase 0.6.E plan ingest fires.
2. Phase 0.6.A channel recovery allows packet flow.
3. Work Stream A.0 extends `GitMutationProofReceipt.code_identity_hash`.
4. Work Stream A push routing validates GuardIR refs.
5. Work Stream C ingests CI artifact or local equivalent.
6. Work Stream B indexes CodeIdentity-bound proof evidence from C.
7. Work Stream D SafeContinuationDecision routes next slice.
8. Work Stream E connectivity report is accepted by policy.
9. Work Stream G.2 exposes startup summaries for edge consumers.
10. Work Stream F observes the loop if enabled, or records disabled/deferred
   policy status.
11. `WorkStreamConvergenceReceipt` cites all stream closure statuses and the
   end-to-end dogfood proof.

Startup-authority halt rule:

- If startup authority blocks with `final.safe_to_continue=false`, if
  `final.next_command` requires checkpoint or repair, or if
  `ControlDecisionObedience` is dirty, do not emit
  `WorkStreamConvergenceReceipt`.
- The agent halts convergence, remediates the startup-authority blocker, reruns
  startup, and resumes only after `safe_to_continue=true` and all required
  work-stream closure receipt ids are present.

### G.6 Contract Bundle And Guard Wiring

- Register `CodeIdentity` and `IngestFailureReceipt` schema fixtures in the
  command bundle / platform-contract registry.
- Add the closure guard that proves these contracts are both declared and
  consumed.
- Bind the registration through existing DurableSchemaPolicy patterns.
- Closure: `check_platform_contract_closure.py --format md` passes across v4
  contracts, and bundle output names the consuming guard.

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
14. `dev/scripts/devctl/runtime/git_mutation_proof_receipt.py`
15. `dev/scripts/devctl/runtime/plan_intent_ingestion.py`
16. `dev/scripts/devctl/runtime/peer_awareness_policy.py`
17. `dev/scripts/devctl/review_channel/agent_packet_attention.py`
18. `dev/scripts/devctl/runtime/evidence_receipts.py`
19. `dev/active/remote_commit_pipeline.md`
20. `dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`
21. `dev/active/autonomous_governance_loop_v2.md`
22. `dev/active/devctl_reporting_upgrade.md`
23. `dev/active/portable_code_governance.md`
24. `.github/workflows/coderabbit_ralph_loop.yml`
25. `.github/workflows/release_preflight.yml`
26. `.github/workflows/tooling_control_plane.yml`
27. `dev/active/MASTER_PLAN.md:8645-8803`
28. `dev/active/MASTER_PLAN.md:8861-8865`
29. `dev/active/MASTER_PLAN.md:9121`
30. `dev/active/ai_governance_platform.md:90-129`
31. `dev/active/ai_governance_platform.md:4784`
32. `dev/active/ai_governance_platform.md:5600-5663`
33. `dev/active/ai_governance_platform.md:14741-14835`
34. `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md:3171-3225`
35. `dev/scripts/devctl/commands/vcs/push_result_typestate.py`
36. `dev/scripts/devctl/runtime/typed_ids.py`
37. `dev/scripts/checks/check_governed_transitions.py`
38. `dev/scripts/devctl/runtime/governed_transition_typechecker_models.py`
39. `dev/active/review_probes.md:48-73`
40. `dev/active/agent_substrate_architecture_review.md:46`
41. `dev/active/pre_release_architecture_audit.md:93-103`
42. `dev/scripts/devctl/repo_packs/voiceterm.py`
43. `.claude/commands/agent-spawn.md`
44. `.claude/commands/develop.md`
45. `.claude/commands/goal.md`
46. `dev/config/devctl_policies/launcher.json`
47. `dev/scripts/devctl/runtime/raw_git_bypass_receipts.py`
48. `dev/active/portable_code_governance.md:56-73`
49. `dev/active/MASTER_PLAN.md:5233-5242`
50. `dev/active/MASTER_PLAN.md:5751-5829`
51. `dev/active/MASTER_PLAN.md:8650-8657`
52. `dev/active/MASTER_PLAN.md:9054-9078`
53. `THESIS_EVIDENCE.md:732`
54. `THESIS_EVIDENCE.md:873`
55. `dev/scripts/devctl/commands/autonomy/swarm.py:50-74`
56. `dev/scripts/devctl/commands/autonomy/swarm_core.py:16-92`
57. `dev/scripts/devctl/autonomy/run_feedback.py:267-296`
58. `dev/scripts/devctl/review_channel/packet_agents.py:12-22`
59. `dev/scripts/devctl/runtime/dev_learning_workstreams.py:163-186`
60. `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md:17-25`
61. `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md:159-200`
62. `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md:1334-1389`
63. `dev/scripts/devctl/runtime/work_intake.py:48`
64. `dev/scripts/devctl/runtime/control_plane_read_model.py:63`
65. `dev/scripts/devctl/commands/reporting/auto_mode_status.py:71`
66. `app/operator_console/state/snapshots/snapshot_builder.py:43`
67. `app/operator_console/state/review/review_state.py:23`
68. `dev/scripts/devctl/runtime/action_contracts.py:17-150`
69. `dev/scripts/devctl/runtime/validation_contracts.py:57`

## Operator Visibility

No new top-level operator commands except `develop promote-plan`. Extend
existing commands/views:

- `devctl context-graph --concept proof --query <sha>`
- `devctl context-graph --concept validation --query <code_identity_hash>`
- `devctl dashboard --view findings-status`
- `devctl dashboard --view runtime-tiers`
- `devctl graph-walk --from <sha> --to proof --format mermaid`
- `devctl develop next --include-safety-decision --format json`
- contract-connectivity before/after report for Work Stream E
- `devctl edge --device raspberry-pi status` after Work Stream F is activated
- `/raspberry-pi status` slash wrapper after Work Stream F.1 lands
- `/raspberry-pi roles --toggle <role_id> <enabled|disabled>` as a thin
  adapter over the existing role-execution target policy path
- LED projection JSON at
  `dev/reports/edge_device/<device_id>/led_state_latest.json` after F.2 lands
- `devctl context-graph --query MP-GUARDIR-V4 --format md` must show
  plan-intake rows through `plan_intake_includes` after Phase 0.6.E
- `devctl system-picture --format md` must include non-zero plan-intake
  visibility once the v4 plan is ingested
- convergence status surface showing A-F status values from
  `WorkStreamConvergenceReceipt.work_stream_statuses`

Dashboard extensions:

- extend existing review-channel/status dashboard with `plan_ready_gate_state`
- extend existing peer-awareness dashboard with `peer_inbox_poll_state`
- extend existing findings views with `cloud_ci_findings` to disambiguate from
  bridge-derived findings
- extend existing quality/proof views with `ci_validation_state` to
  disambiguate from generic quality status
- extend existing proof/validation views with proof index, startup proof
  consumption, and repair authorization audit
- extend existing connectivity/reporting views with accepted internal-only
  counts, true orphan counts, duplicate counts, stranded-consumer counts, and
  bidirectional finding counts
- extend existing edge/reporting views with Raspberry Pi device capability,
  daemon freshness, LED projection state, finding ingest refs, and physical
  approval receipt verification state
- extend existing system-map/context-graph views with the G.1-G.6 edges listed
  in Work Stream G
- amend `dev/active/devctl_reporting_upgrade.md` / MP-379 through
  `MP-GUARDIR-V4-MP379-CLOUD-PROOF-REPORTING-AMENDMENT-S1` so reporting
  collectors own proof, cloud CI findings, validation state, and proof lineage

Console widget integration for v4 surfaces is deferred to an MP-359 follow-up.
This plan commits only to read-only typed surfaces via existing snapshot schema;
mobile and desktop consumers inherit backward-compatible JSON additions.

No work stream closes unless its existing CLI/dashboard surface renders the
evidence created by that work stream.

## Hard Constraints

1. Phase 0.6.E and Phase 0.6.A are parallel prerequisites. Both close before
   Work Stream A.0; neither waits on the other.
2. Dual `plan_ready_gate` packets from Codex and Claude for the same plan SHA
   close before any implementation `task_started`.
3. Fresh peer-awareness inbox-poll state is required before every planning,
   handoff, review, and closure packet.
4. Work Stream A.0 closes before Work Stream A, C, B, D, or G proof consumers.
5. Work Stream C emits proof artifacts before Work Stream B indexes them.
6. Phase 0.6.A continuation closes before Work Stream A-E task starts.
7. No CI artifact without CodeIdentity binding.
8. No raw `--no-verify` without active BypassReceipt.
9. `FeatureProofReceipt.real_life_test_status=proven_passed` requires resolvable
   pytest nodes.
10. Codex and Claude dogfood every work stream.
11. Operator CLI/dashboard evidence required before work-stream closure.
12. CI authority is typed JSON only.
13. Extend P195-P198; no parallel cloud-proof plan.
14. Closure receipt type must match the closed object.
15. Raspberry Pi / edge-device mode is projection/adopter-pack work only until
    explicitly activated; no LED or edge runner may become authority.
16. Pi mode is opt-in only:
    `edge_devices.raspberry_pi.enabled: false` by default.
17. Pi is read-only by default: no direct mutation to `dev/state`, no operator
    actor packets, no commits, and no pushes.
18. Pi findings flow through existing ingest:
  `dev/reports/edge_device/<device_id>/findings.jsonl` reduces through the
  governance-review pipeline.
19. `OperatorPhysicalApprovalReceipt` scope is limited to `read_only` and
  `findings_ingest`; it never grants edit, commit, push, or raw bypass
  authority.
20. Pi credentials are separate from the dev machine, with their own SSH key
  and optional read-only GitHub token.
21. Device revocation is mandatory: `dev/config/revoked_devices.json` or the
  active device registry must be able to reject future signatures immediately.
22. Work Stream G is the convergence proof. Individual Work Stream A-F
   closure receipts are necessary evidence, but system closure requires a
   `WorkStreamConvergenceReceipt` or an explicit per-stream
   `disabled_optional` / `deferred_by_policy` status.
23. Pi active-role execution is opt-in per role. Light-AI roles may classify,
   summarize, and route only; they cannot generate code, mutate typed state,
   approve bypass, or act as operator.
24. Pi packets may use `from_agent="system"` only as a routing label. Authority
   comes from typed session, role, target, and lifecycle receipts.
25. Heavy-AI role work always routes back to dev-machine agents through typed
   packets and must carry role-output evidence refs.
26. `WorkStreamConvergenceReceipt` is aggregate evidence only. It cannot close
   a stream without that stream's own PlanRowClosureReceipt, FeatureProofReceipt,
   guard receipts, and dogfood evidence.
27. Work Stream G must reduce visibility gaps in context-graph/system-picture;
   it must not create a parallel graph, finding, dashboard, or closure system.
28. Startup authority halt wins over convergence. No G.5 convergence receipt is
   emitted while `safe_to_continue=false`, while checkpoint/repair is required,
   or while control-decision obedience is dirty.
29. After A.0, no further work-stream implementation packet starts until the
   `task_produced -> review_accepted` guard path either succeeds with typed
   packets or emits a scoped governed exception that names
   `MP-GUARDIR-V4-PHASE-0-6-A-TASK-PRODUCED-GUARD-REPAIR-S1`.
30. Current work authority resolves from ingested typed `PlanRow` state plus
   ingestion receipts and source snapshots. Plan-intake markdown, active docs,
   generated boot cards, dashboards, bridge text, memory, and chat cannot
   authorize implementation unless bound to startup-visible typed rows.
31. Reviewer sessions are read-only while another session owns a live-tree
   `MutationLease` for the target write set. Tool availability, provider name,
   role label, or operator prose cannot grant implementation mutation.
32. v4 must reuse existing PlanRow, lifecycle, finding, contract-connectivity,
   typed-namespace, projection-only, and system-map guards. Do not create a
   parallel plan tracker, lifecycle ledger, finding store, duplicate-system
   auditor, or mutation authority.
33. Cascade lifecycle post authority must bind to resolved parent-packet
   semantics, not just packet-shaped evidence. Wrong session, wrong role,
   stale parent, wrong peer direction, unrelated parent kind, or target-ref
   mismatch rejects the closure before any control-decision bypass.
   `review_accepted` is a final closure packet and may close only a resolved
   `task_produced` parent; it must reject `task_progress`.
34. Review-channel read authority is read-only observation. It may record
   `PacketBodyObservation` and trigger semantic-ingestion requirements, but it
   cannot grant mutation, packet disposition, post/ack/apply/dismiss, staging,
   commit, push, or bypass authority.
35. Review-channel post authority must preserve the real source actor session
   for live agent packets. `local-review` is a fallback store session, not a
   valid live-agent source session and not a wildcard for cascade closure.
36. A live-agent source session is valid only when existing typed session and
   actor authority binds that session id to the posting actor in the current
   repo/project scope. Non-empty, UUID-shaped, or operator-supplied strings are
   not authority by themselves.
37. Source-session validation uses one central resolver for write-time posts and
   verifier-time cascade checks. `AgentMindSlice` latest projection is not
   durable authority by itself unless the resolver binds it to typed session,
   actor, freshness, and repo-scope evidence.
38. Session rotation must not convert a real post-time parent packet into an
   unclosable ghost. Historical parent validation must prove post-time session
   authority or return a typed recoverable blocker; it must still reject unknown
   or spoofed session ids.
39. Provider-role defaults such as `codex=reviewer` and `claude=implementer`
   are compatibility hints only. Mutation, review, stage, commit, push,
   approval, and closure authority come from typed role assignment and
   `ActorAuthorityState` / `CapabilityGrantState` grants.
40. Missing actor identity fails closed for mutating decisions. `SessionPosture`
   and generated boot cards may project role/capability information, but they
   cannot grant mutation by themselves.
41. `SYSTEM_MAP.md`, generated boot cards, dashboards, mobile/status views, and
   bridge text are navigation/projection surfaces. Improve their typed inputs
   and sync guards; do not let their prose become authority.
42. VoiceTerm is an adopter/product shell. Portable governance code and docs
   must route product-specific paths/names/defaults through
   `ProjectGovernance`, `RepoPack`, `RepoPathConfig`, or explicit adopter-pack
   debt rows.
43. Provider-level agent-mind latest projections are not actor authority when
   multiple sessions, subagents, or delegated workers exist. Source-session and
   mutation authority resolve through typed route keys, role/session grants,
   delegation metadata, and repo-pack policy.
44. Subagent/fanout roles are configurable per repo through existing
   collaboration-mode and repo-pack policy. Read-only fanout produces evidence;
   mutable fanout additionally requires `safe_to_fanout`, disjoint write
   scopes, registered worktrees, and live mutation leases.
45. `startup_authority_failed`, `repair_startup_authority`, and final-response
   blockers must emit a typed owner, target, reason, and runnable repair
   command or a typed stop_anchor. A self-referential read-only loop is a
   controller bug, not an acceptable continuation state.
46. GuardIR v4 plan rows are MP-377 T22 child/detail rows. They may refine
   MP-377 extraction and ingestion work, but they cannot supersede MP-377,
   active owner docs, or `PlanRow` authority without explicit parent refs and
   ingestion provenance.
47. Professional docs, SYSTEM_MAP, generated boot cards, dashboards, and
   context-graph views are projection/read-model surfaces. They must help
   agents find typed authority; they must not become another backend authority
   source.
48. Portable GuardIR closure requires repo-pack/adopter separation evidence.
   VoiceTerm defaults may remain product-client compatibility only when routed
   through `ProjectGovernance`, `RepoPack`, `RepoPathConfig`,
   `SurfaceOwnershipMap`, `ExtensionBundle`, or explicit adopter-pack debt.
49. Typed next-command emitters must be guard-obedient. Any command surfaced as
   `next_required_command`, `next_step_command`, or final-response continuation
   work must already carry the decision/proxy/lifecycle inputs needed to pass
   `ControlDecisionObeyedGuard`, or it must be represented as an unrunnable
   typed blocker with an explicit owner and repair row.
50. Reviewer feedback posts are lifecycle writes, but they are required for the
   review loop to function. A scoped reviewer `finding`, `task_progress`,
   `review_failed`, or eligible `review_accepted` packet must either pass
   `ControlDecisionObeyedGuard` with typed decision, source-session, lineage,
   and target-scope proof, or return a typed recoverable blocker. Raw guard
   failure after a routed review task is architecture debt, not an acceptable
   stop condition.
51. Reviewer-finding response edges are first-class lifecycle edges. A scoped
   implementer may answer a reviewer `finding` for the same slice with
   `task_progress`, `task_blocked`, or `task_produced`; those edges require the
   same parent resolution, source-session, role/session, and target-ref proof as
   other cascade posts. They do not grant closure authority, and
   `review_accepted` over a `finding` parent remains invalid.
52. Multi-packet evidence does not imply multi-parent authority. A lifecycle
   post must resolve one explicit primary semantic parent, and supporting
   evidence refs cannot be ordered to choose a more convenient parent. Ambiguous
   or contradictory parent refs fail closed with typed recovery evidence.
53. Checkpoint and dirty-worktree budgets block mutation, closure, convergence,
   staging, commit, push, and implementation `task_started`; they do not select a
   different current plan and they do not automatically block scoped review-only
   coordination packets that have valid role/session/parent/target proof.
54. `AuthoritySnapshot.allowed_actions`, `ActorAuthorityState`,
   `CapabilityGrantState`, `AgentLoopDecision`, and
   `ControlDecisionObeyedGuard` must agree on any review-channel post lane. If
   they disagree, the result is a typed consistency blocker, not agent discretion.
55. `BlockerSnapshot` is the single blocker metadata contract. `AgentLoopDecision`
   and read models may mirror blocker fields only as projections with field-route
   parity tests; connectivity duplicate findings for this pair remain planned
   debt until the composition path is proven.
56. File mutation authority must cover both actor and write method. Raw shell
   redirection, append redirection, heredocs, herestrings, `tee` writes, or
   inline scripts that write repo files are mutation attempts and must either
   pass the same typed path/lease/provenance checks as patch/edit adapters or
   emit governed exception debt.
57. Source-session validation for live packet posts must not use
   `<provider>_latest.json` as the decisive actor oracle when subagents or
   delegated workers exist. It must authenticate the explicit posting session
   through route-scoped typed actor/session/delegation evidence, or return a
   typed recoverable blocker that preserves the intended main actor identity.
58. Generated instruction surfaces must be useful command routers over typed
   state. `AGENTS.md`, `CLAUDE.md`, slash templates, guides, dashboards, and
   SYSTEM_MAP projections must expose role-aware "what to run when" guidance
   from typed inputs, while remaining unable to grant backend authority.
59. Role and continuation state must be boot-visible and gate-enforced. A live
   session must not require operator reminders to know its current role,
   peer lane, allowed actions, blocked actions, and stop policy; stop/wake
   anchors cannot pause an open typed lifecycle without explicit termination
   authority.
60. Instruction and role guidance must be contract-connected. If
   `InstructionBootCard`, `RoleInstructionCard`, `RoleGuard`, role
   customization contracts, or command read/write classifications are missing
   from contract-connectivity, system-map, context-graph, or guard chokepoints,
   generated boot cards are incomplete projections, not role authority.
61. Provider-role defaults are compatibility hints only. Unknown provider,
   missing role state, provider-default-only assignments, and missing scoped
   mutation lease rows fail closed for mutation, closure, packet-write,
   staging, commit, push, bypass, and actor-proxy authority.
62. Startup/session/final-gate dependency refreshes are time-bounded typed
   inputs. A hang in review-state, push-state, dashboard/status, or optional
   projection refresh must emit a typed dependency-timeout blocker with owner,
   target, command, and repair row; it must not silently wait forever, retarget
   the current plan, grant reviewer mutation, or force a chat/offline fallback.
63. Sidecar and agent-mind outputs are evidence, not current authority. They
   must carry route, role, session, plan revision/hash, and freshness metadata
   before any reducer uses them; stale helper summaries cannot overwrite the
   main actor's role envelope, packet lane, current plan target, or continuation
   decision.
64. Reviewer acceptance is a typed lifecycle write, but a routed reviewer must
   be able to complete it when fresh authority proves the parent slice,
   source session, target role/session, packet body observations, and plan row.
   `ControlDecisionObeyedGuard` must not keep reusing stale
   `AgentLoopDecision` or `agent-runtime-clock` state after the required bodies
   have been opened. If freshness cannot be proven, the result is a typed
   stale-decision/body-observation blocker, not silent offline evidence or an
   unclassified raw guard failure.
64. Packet selection is a shared current-plan-aware reducer. Review-channel
   inbox, `develop next`, startup packet inbox, peer attention windows, watcher
   leases, agent-loop, and final-response gate may project the selected packet,
   but they must not fork queue-order, latest-pending, or relevance heuristics
   that can hide a fresh plan-bound packet behind stale backlog.
65. `RoleBootEnvelope` is the canonical role/continuation read model for live
   agent sessions. Startup, `develop next`, final gate, `agent-loop`, generated
   boot cards, and status surfaces consume the same envelope or an explicitly
   registered equivalent; provider labels and generic boot-card examples remain
   compatibility/discovery hints only.
66. Packet plan currency is lineage-aware, not exact-latest-SHA-only. During live
   plan iteration, a packet posted for the same target row may remain current
   across later amendments, or the system must require a refreshed packet through
   typed state. Exact SHA mismatch by itself must not hide the packet behind old
   backlog.
67. Packets are typed event/evidence inputs, not competing plans. A packet can
   request or prove a change, but durable implementation authority must come from
   the canonical ingested plan graph, lifecycle read models, or finding-review
   reducers with packet ids recorded as provenance.
68. Whole-worktree VCS state mutations are governed mutations. Commands such as
   `git stash`, `git reset`, `git checkout`, `git restore`, `git clean`, and
   `git apply` require typed actor/session/lease/scope provenance or an isolated
   clean worktree; they are not read-only verification commands in a shared dirty
   multi-agent worktree.
69. Packet-to-plan authority must reuse the existing plan-index, packet-binding,
   packet-debt, planning-IR, agent-dispatch, and control-plane read-model
   modules. A new queue, ledger, plan tracker, docs index, or source-of-truth
   file for packet-derived plan authority is a duplicate-system finding unless
   it is registered as a projection over those existing contracts.
70. Destructive worktree verb taxonomies must be unified. `git clean` is as
   dangerous as stash/reset/checkout/restore in a dirty shared worktree; if one
   detector, command envelope, bypass graph, or raw-git receipt path knows a
   destructive verb, the corresponding guards and action taxonomy must know it
   too.
71. Mutation-risk classification must be consumed, not merely attached. If
   `CommandEnvelopeClassification` can classify a command as a governed
   mutation, downstream renderers, advisory role filters, action-routing,
   control-decision action matching, consistency guards, and final-response
   executable checks must either consume that classification or explicitly route
   through a registered adapter over it. Local substring allowlists are planned
   debt until they are removed or proven equivalent by tests.
72. Shared classifiers and typed normalizers must be leaf-safe. A module that
   exists so multiple consumers can converge, such as command-envelope mutation
   classification, must not import higher-level consumers that already depend on
   it. Import cycles that break `review-channel`, `agent-mind`, `session`, or
   `test-python` are coordination-lane failures, not ordinary test failures.
73. Mutation classification must cover both command text and typed action
   identifiers. A reducer that decides executable status, consistency, routing,
   or blocked permissions may consume a registered adapter over the shared
   classifier, but it must not stay on a separate token list for `next_action`
   while ignoring destructive `next_command` values.

## Phase 0.6.E Closure

Close Phase 0.6.E only after:

- `PlanSourceSnapshot` exists.
- `PlanIntentIngestionReceipt` exists.
- `PlanIntentIngestionReceipt` carries current amendment metadata.
- plan-intake INDEX includes this v4 plan.
- context graph finds `MP-GUARDIR-V4` through `plan_intake_includes`.
- fresh startup exposes v4 rows in `quality_signals.plan_intake.current_rows`.
- `CurrentPlanAuthorityResolver` returns the same v4 current-plan answer across
  startup, `develop next`, context graph, dashboard, review-channel selection,
  and final-response gate surfaces.
- Generated `AGENTS.md`, `CLAUDE.md`, slash templates, and platform-guide
  projections include role-aware command routing from typed renderer inputs and
  pass instruction-surface sync/coverage guards.
- `InstructionBootCard`, `RoleInstructionCard`, `RoleGuard`, role customization
  contracts, and command read/write classifications are visible through
  contract-connectivity, system-map/context-graph, platform-contracts, and
  role guard tests.
- Reducer tests prove startup/checkpoint blockers do not retarget the current
  plan to an unrelated active owner doc.
- Help-output parity proves required `develop ingest-plan` flags exist or are
  marked in this plan as future Phase 0.6.E implementation work.
- Dependency-watchdog proof shows startup/session/final gate return typed
  blockers instead of hanging on review-state or push-state refresh.
- Sidecar freshness proof shows stale helper outputs remain historical evidence
  and cannot replace the current-plan resolver or packet-arrival invalidation.
- Packet-selector parity proof shows all packet consumers select the same
  current plan-bound packet or emit the same typed stale-backlog conflict.
- Packet-supersession proof shows open packets survive same-row plan amendments
  by lineage or trigger a typed refresh requirement instead of silently becoming
  stale.
- Packet-promotion proof shows packet/offline-finding prose cannot select work
  directly; scope-changing packet findings become authority only after a typed
  plan or lifecycle reducer ingests them and records the packet id as provenance.
- RoleBootEnvelope proof shows Codex reviewer/orchestrator and Claude
  implementer surfaces expose the same role/continuation facts and reject
  cross-actor final-gate commands without typed proxy authority.
- Worktree-mutation proof shows shared-worktree VCS state commands such as
  `git stash` are blocked or routed through typed worktree-scope mutation
  provenance while peer dirty work or peer leases exist.
- Verb-taxonomy proof shows `clean`, `stash`, `reset`, `checkout`, `restore`,
  and `apply` are consistently classified across VCS helpers, context graph,
  mutation-bypass checks, command envelopes, action routing, and receipt paths.
- Import-isolation proof shows mutation-classifier convergence does not create
  circular imports and that `review-channel`, `agent-mind`, `session`, and
  focused test routing remain importable while an implementation command family
  is broken.
- Typed-action adapter proof shows final gate, action routing, and
  control-decision consistency classify mutation consistently for both
  `next_action` / action identifiers and `next_command` shell text.

Closure cites all evidence refs.
