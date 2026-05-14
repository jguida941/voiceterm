# Master Plan (Active, Unified)

## Canonical Plan Rule

- This file is the single active plan for strategy, execution, and release tracking.
- `dev/active/INDEX.md` is the canonical active-doc registry and read-order map for agents.
- Execution-owner budget: keep repo-wide execution authority at five or fewer
  active docs total (`MASTER_PLAN.md` plus 3-4 owner specs). Narrower or
  completed lanes remain as reference-only owner docs until archived.
- `dev/active/theme_upgrade.md`, `dev/active/memory_studio.md`,
  `dev/active/devctl_reporting_upgrade.md`,
  `dev/active/autonomous_control_plane.md`,
  `dev/active/loop_chat_bridge.md`, `dev/active/naming_api_cohesion.md`,
  `dev/active/ide_provider_modularization.md`,
  `dev/active/pre_release_architecture_audit.md`,
  `dev/active/platform_authority_loop.md`,
  `dev/active/autonomous_governance_loop_v2.md`,
  `dev/active/remote_commit_pipeline.md`,
  `dev/active/remote_control_runtime.md`, and other narrower lane docs remain
  owner references only unless the typed phase/task registry in
  `dev/active/ai_governance_platform.md` promotes them back into the active
  execution-owner set.
- `dev/active/review_channel.md` now carries the reusable review/runtime
  contract slice for MP-355 plus the temporary markdown-swarm operating mode
  used by the current Codex/Claude cycle; implementation tasks stay in that
  file under MP-355 and must preserve the broader shared-backend boundary.
- Within that MP-355 slice, the markdown lane table is planned topology only;
  the live participant registry is provider/session-backed typed state, the
  default requested worker fanout is zero unless explicitly requested, and
  `bridge.md` remains a compatibility projection until native
  `CollaborationSession` topology lands.
- 2026-05-11 slice 18 fix arc + bilateral protocol consolidation (MP-377):
  claude reviewer-role's session arc identified 7 bugs in slice 18 via two
  codex-review passes (5 findings from 17:16:09Z + 2 additional findings from
  17:51:17Z plan-review pass) and 3 architectural smells (#058
  TaskCompleteDecision ignores live `_active_continuation_anchor()`; #059
  wake-packets cannot wake dead agent processes / no typed spawn authority;
  bash-permission-stopgap as bypass-launch path). Operator-mandated ingest
  of 15 plan-row anchors as first step before any slice 18 commit:
  `MP377-P0-SLICE-18-P1A-FALLBACK-BODY-OPEN-S1` preserves fallback body-open
  fields when packet rows absent (closes consumption-gap bypass at
  `agent_packet_attention.py:209-215`);
  `MP377-P0-SLICE-18-P1B-AUTHORIZED-RECEIPT-PUSH-S1` guards receipt-head
  refresh for minimal git checkouts (unblocks
  `test_governed_push_allows_managed_receipt_child_of_authorized_head` at
  `push_preflight_projection.py:58-64`);
  `MP377-P0-SLICE-18-P1C-SESSION-SCOPE-BODY-OPEN-S1` includes role+session
  in body-observation match (closes session-scope bypass at
  `agent_packet_attention.py:385`);
  `MP377-P0-SLICE-18-P1D-URGENT-PACKET-PREEMPTION-S1` invokes
  `_attention_priority_key()` BEFORE the early rank check at
  `agent_packet_focus.py:171-174` so urgent/blocking pending packets with
  lower event_ids preempt newer active packet (NEW finding from codex
  review subagent 019e1851-a6c9-7931 emitted 2026-05-11T18:43:38Z);
  `MP377-P0-SLICE-18-P2A-SHOW-WRITE-RECONCILE-S1` reconciles `review-channel
  show` typed write with `DEVCTL_NO_ARTIFACT_WRITES=1` read-only suppression
  contract at `event_handler.py:244-245`;
  `MP377-P0-SLICE-18-P2B-INGESTION-STATUS-CHECK-S1` requires successful
  receipt status before suppressing body-open at
  `agent_packet_attention.py:387-388`;
  `MP377-P0-SLICE-18-P2C-ACTOR-MATCH-OBSERVATION-S1` requires matching
  actor+observation in multi_agent_sync runtime-truth check at
  `runtime_truth_agent_loop_instruction.py:240-245`;
  `MP377-P0-SLICE-18-P2D-DEFERRED-RECOVERY-RUN-S1` runs deferred recovery
  before returning receipt-head preflight at
  `push_preflight_projection.py:65`;
  `MP377-CONTINUATION-ANCHOR-CONSOLIDATION-S1` makes
  `TaskCompleteDecision` in `session_termination_policy.py` consult
  `_active_continuation_anchor()` before allowing TASK_COMPLETE — the
  primary fix for smell #058 (empirically confirmed by two dead codex
  sessions 019e1436 and 019e17fa-3745 emitting TASK_COMPLETE despite live
  anchor `rev_pkt_3685`);
  `MP377-CODEX-SPAWN-AUTHORITY-S1` adds typed `SpawnDeadAgentAction`
  composing with `LifetimeBypassMode` so dead-agent resurrection becomes a
  typed-pipeline-native action instead of bash-permission grants;
  `MP377-AGENT-SUPERVISE-DRIVER-S1` wires that authority into
  `agent-supervise --execute`: the default report remains read-only, while
  the explicit execute path emits `AgentSuperviseLaunchResult` and starts the
  existing headless review-channel launch command only after a live
  `continuation_anchor`, active `BypassReceipt`, and green `LoopAutonomyState`
  produce `SpawnDeadAgentAction`;
  `MP377-LIFETIME-BYPASS-MODE-S1` adds `LifetimeBypassMode` typed authority
  with `BypassReceipt(receipt_id, reason, operator_signature,
  ai_approval_evidence, requested_authority_scope, expires_at_utc_optional)`
  composing with `governed_exception_lifecycle.py` (operator's 2026-05-11
  proposal — no parallel system, all bypass authority lives in existing
  lifetime governance lifecycle);
  `MP377-PEER-SESSION-HANDSHAKE-S1` adds typed `peer_session_handshake`
  packet kind that fires when claude or codex boots; session_resync
  evidence required if session_id mismatch detected;
  `MP377-PEER-HEARTBEAT-CONTRACT-S1` adds heartbeat packet TTL contract
  with `peer_offline` evidence surfaced when heartbeat past expiry;
  `MP377-PRE-DECISION-COMPOSABILITY-WINDOW-S1` adds typed pre-decision
  window requiring claude reviewer ack or `pre_decision_objection` finding
  before codex commits architectural slice;
  `MP377-COMMIT-RECEIPT-EVIDENCE-CHAIN-S1` adds typed
  `CommitReceipt(commit_sha, plan_row_id, reviewer_ack_packet_id,
  audit_synthesis_ref)` bundling reviewer's audit chain into commit-level
  typed evidence;
  `MP377-GOAL-PROGRESS-RECEIPTS-S1` adds typed `goal_progress` event after
  each slice; continuation_anchor reducer updates
  `progress_percentage_toward_goal` field surfaced via `develop next`;
  `MP377-AGENT-LOOP-BILATERAL-PROTOCOL-S1` adds the seven-property
  `AgentLoopBilateralProtocol` runtime contract and regression tests as a
  policy foundation only: chat/projections remain non-authority, serious
  actions and handoffs require typed state, provider-neutral lane resumption
  evidence is explicit, commands consume typed evidence, and receipts bind
  repo state, actor, guard result, command, and proof. Eventbus and
  session-trigger automation remain later MP-377 rows.
  Execution priority per operator-mandated 25.13 sequencing:
  continuation_anchor enforcement FIRST (so codex cannot die mid-arc),
  then lifetime-bypass-mode + codex-spawn authority (so codex relaunch is
  typed-state-native), then slice 18 P1 fixes + commit, then slice 19 P2
  fixes, then bilateral protocol enhancements, then resume MP-377 Phase 0
  per `develop next`. See plan section 25 of
  `/Users/jguida941/.claude/plans/yes-anytime-it-doesn-t-lazy-sunset.md`
  for full architectural detail + dogfood-verification protocol (25.14).
- 2026-05-14 launch-bootstrap repair family (MP-378): after the relaunch
  incident log recorded the P102 bootstrap deadlock, add
  `MP-378-LAUNCH-BOOTSTRAP-FIX-S1` through
  `MP-378-LAUNCH-BOOTSTRAP-FIX-S7` as the typed repair queue. S1 is the first
  commit and promotes the temporary bootstrap helper into
  `devctl bypass grant`, a governed command that evaluates
  `BypassRequest -> BypassEvaluation -> BypassReceipt` and persists an active
  `BypassLifecycle` before review-channel launch/recover consumes
  `--bypass-receipt-id`. S2 adds `SessionStatusProjection`, a derived
  read model over `SessionLivenessSignal`, `AgentSessionOutcome`,
  `AgentMindSlice.latest_task_complete_at`, collaboration participants,
  HEAD, and worktree identity so operators can ask one typed surface whether
  a session task-completed or died mid-task. S3 adds
  `ClassifierSafetyAttestation`, a projection from active `BypassLifecycle`
  receipts into Claude classifier-readable permission rules in
  `.claude/settings.local.json` without treating that gitignored local file as
  authority; the projection marks `classifier_dominated_by_bash_wildcard` when
  an existing `Bash(*)` rule dominates the generated receipt-scoped rules.
  S4 adds `SessionLivenessReconciler` plus
  `devctl session reconcile --kill-stale`.
  Why: incidents #7/#8 were stale persisted remote-control attachment files
  and stale session counts surviving the real process exit path. The fix runs
  at the attachment layer, upstream of `session_liveness_*` signal/count
  projections, because the attachment JSON carries PID identity and the
  existing detach-write authority.
  How: the reconciler scans persisted remote-control attachment artifacts,
  checks expiry, heartbeat, physical identity, and process liveness, then
  reports a typed row per artifact. Dry-run mode is report-only; `--kill-stale`
  detaches stale artifacts through the existing attachment writer, optionally
  terminates a still-live stale PID, and refreshes the existing review-channel
  status projection rather than introducing another liveness surface.
  Acceptance: `SessionLivenessSignal` and `SessionLivenessReconciler` are both
  registered platform contracts, schema fixtures pass, status projection carries
  a dry-run reconciliation report, and the shipped CLI has a live
  `session reconcile --kill-stale` dogfood run. Later rows cover role reset,
  runtime-state ignore posture, and long-command wrappers.
- 2026-05-14 architectural self-improvement charter
  (`MP-378-ARCH-SELF-IMPROVEMENT-LOOP-S1`): `rev_pkt_4017` elevates the
  recurring-class finding into a durable guard-discovery-and-build loop. Every
  reviewer round scans recent packets, typed state, and fleet observations for
  unguarded architectural invariants; when one appears, the loop proposes a
  typed guard/probe and Codex builds it inline or distributes it across the
  next MP-378 slices. Guard P1 is `check_plan_index_commit_continuity.py`;
  Guard P2 is `check_packet_pkt_bind_completeness.py`, which blocks new Codex
  `task_started` packets that miss durable `PKT-BIND-REV-PKT-*` plan rows
  after the grace window or paired `task_produced` closure. P3-P5 are
  distributed across S6/S7 and the next contract-registry/sidebar updates.
  `rev_pkt_4019` widened P1 from lexical MP-378 matching to mutation
  semantics for task-start bindings and guard charters, and added P6/P7 as
  live-validated follow-on guards to distribute with the remaining launch
  bootstrap slices. This rule lives in typed plan state so it does not depend
  on memory or chat attention.
- 2026-04-20 persistence-loop unblock (subordinate to
  `dev/active/autonomous_governance_loop_v2.md` MP-377): headless
  `review-channel --action launch | recover` now auto-elevate
  `--approval-mode` to `trusted` when typed `interaction_mode ==
  "remote_control"` (shared helper at
  `dev/scripts/devctl/approval_mode.py::auto_elevated_approval_mode`),
  so headless conductors no longer silently wedge on local sandbox-
  escalation prompts. The rendered launch prompt also includes an
  inbox-drain section after the canonical Step 0 bootstrap chain so
  codex sessions ack pending operator-authority packets before any
  reviewer-bootstrap. Typed conductor-stall observations live in
  `dev/scripts/devctl/review_channel/stall_diagnostics.py`. Wiring the
  diagnostic into a runtime consumer (dashboard render or `devctl
  stall-check`) remains follow-up scope.
- 2026-04-20 follow-up closure (also under MP-377): the ensure-follow
  reviewer-wake path
  (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py::launch_waiting_reviewer_conductor`)
  now routes through the same `auto_elevated_approval_mode` seam so a
  remote-control reviewer relaunched after a wake also avoids the
  sandbox-escalation deadlock. The typed `ConductorStallDiagnosis`
  reader now accepts the real codex rollout JSONL envelope shape
  (`payload.type == "task_complete"`, `payload.is_escalation`) and
  surfaces `escalation_deadlock` regardless of whether the session
  previously emitted task-complete events.
- 2026-04-21 `rev_pkt_1529` stall-diagnostic follow-up (also under
  MP-377): explicit caller-supplied replacement-session rollout evidence now
  clears a prior conductor before stale `escalation_deadlock` classification,
  so a wedged session that was successfully relaunched no longer keeps
  reporting deadlock forever.
- 2026-04-21 `rev_pkt_1503` review-state loader follow-up (also under
  MP-377): event-backed `projections/latest/review_state.json` payloads now
  stay authoritative before bridge-contract-drift repair runs, so
  startup/status/session-resume/dashboard consumers cannot silently downgrade
  to bridge-backed compatibility state when the event-backed reducer has
  already emitted typed authority.
- 2026-04-21 Phase 0.a producer-provenance follow-up (also under MP-377):
  `AuthoritySnapshot` and `CoordinationSnapshot` now carry the shared
  proof-tick provenance tuple (`snapshot_id`, `zref`, `source_identity`,
  `source_contract`, `source_command`, `observed_fields`, and
  `inferred_fields`) from their producer paths instead of leaving
  downstream parity tests to reconstruct source identity after the fact.
- 2026-04-22 Phase 0.b proof-tick parity follow-up (also under MP-377):
  `ControlPlaneReadModel`, `SessionCachePacket`, and review-channel derived
  projections now preserve producer-owned `SurfaceProvenance`, and
  `check_review_surface_consistency.py` freezes the same proof tick across
  coordination, authority, control-plane, startup-context, session-resume,
  review-channel status, persisted review-state, registry, and bridge-compat
  surfaces. Dual-agent fanout remains blocked until runtime truth reports
  `safe_to_fanout=true` and `resync_required=false`. The proof tick keeps
  explicit `observed_control_topology` separate from coordination
  `observed_topology`, so planned/live topology evidence cannot overwrite the
  active remote-control posture.
- 2026-04-27 Plan 4.1 proof-tick authority repair (MP-377):
  `dev/active/agent_substrate_architecture_review.md` records the validated
  architecture decision for mode-axis separation, proof-tick authority, and
  future any-agent-any-role migration. `check_review_surface_consistency.py`
  now chooses expected proof-tick values through explicit field authority
  priority instead of first-populated surface order, and compares
  `operator_interaction_mode` separately from `reviewer_mode`.
- 2026-04-29 Plan 4.1 rescue Slice A typed posture / plan-anchor closure
  (MP-377): `SessionPosture` is the shared runtime producer for
  `interaction_mode`, `reviewer_mode`, and `actors[].occupied_lane`; status,
  startup, dashboard, and session-resume consume that posture rather than
  recomputing mode/lane values. `agent_lane.lane` remains a compatibility alias
  while `occupied_lane` is the current-seat field, and actor capability grants
  stay separate from lane occupancy. Startup/session bootstrap renders the
  remote-control no-GUI/no-kill/no-local-commit boundary only when posture says
  `interaction_mode=remote_control`. Pending or expired planning packets now
  project as `PacketIntentAnchor` / `PlanIterationSession` continuity hints;
  only explicit applied planning packets enter typed MasterPlan authority.
- 2026-05-03 review-channel priority action-request projection follow-up
  (MP-377): queue-selected priority `action_request` packets now remain
  `current_session.current_instruction` authority ahead of stale reviewer
  checkpoints and across packet-truth clear paths, including single-agent
  lanes where the handoff packet targets the implementer while Codex is the
  active coding provider. This keeps `check_review_surface_consistency.py`
  aligned with the action-request-first queue contract after final
  `stage_commit_pipeline` packet posts.
- 2026-05-04 relaunch-loop guard-quality calibration follow-up (MP-377):
  `dev/active/ai_governance_platform.md` now carries
  `MP377-P0-T22AN-AK` so the relaunch-loop dogfood does not stop at green
  syntax checks. The next guard slice must distinguish real typed-design
  improvements (model/builder/store split, named input contracts, validating
  constructors) from shallow AST appeasement (mutable registry rewrites or
  temporary variables around constructor returns), then route those design
  findings through typed `/develop` and review-channel work packets.
- 2026-05-06 generated boot-card authority/projection split (MP-377):
  `AGENTS.md` is now the tracked generated `InstructionBootCard`, and
  `CODEX.md` is not a repo surface. `CLAUDE.md` remains an ignored local-only
  peer projection. Durable startup/process
  authority stays in typed plan rows, repo-pack policy, contracts, receipts,
  startup-context, session-resume, context-graph, `/develop`, and guards;
  generated markdown only routes agents to those typed surfaces.
- 2026-05-06 ReviewSnapshot hook timeout (MP-377): the managed post-commit
  ReviewSnapshot receipt hook now bounds
  `review-snapshot --write --receipt-commit` with
  `DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS` (default 90 seconds) and preserves
  the existing fail-open warning policy so ordinary commits do not hang while
  receipt freshness remains enforced by guards. The 2026-05-11 follow-up made
  pre-commit read-only over `commit_permission` so projection writers no longer
  run while git owns the commit index.
- 2026-05-06 remote-control campaign read model (MP-377): `MP377-P0-RC-PAIR-S1`
  is the typed owner row for the Codex/Claude remote-control dogfood campaign.
  `devctl develop campaign` now projects role lanes, remote-control attachment
  proof, packet blockers, interaction-mode drift, and mutation/publication
  gates from typed state without waking agents or granting authority. The
  follow-up remote-control repair keeps archived packet-history rows as audit
  evidence instead of live attention blockers, and prevents stale reviewer
  checkpoint prose from overriding newer terminal instruction/action-request
  packet truth. The
  current campaign is intentionally fail-closed until packet debt,
  remote-control freshness, and interaction-mode/reviewer-mode drift are
  repaired.
- 2026-05-06 remote-control packet/current-session scope fix (MP-377):
  dashboard-targeted instruction packets now stay visible through
  `current_session.current_instruction` even when markdown canonicalization adds
  bullets, and runtime AgentLoopDecision parity compares actor, role, and
  session before flagging packet-id drift. Remote-control packet truth remains
  fail-closed: stale TTLs do not promote remote-control mode, and current
  packet debt still requires checkpoint/repair before mutable fanout.
- 2026-05-07 typed next-selector/checkpoint automation (MP-377):
  `/develop next` is being tightened into an authority-first selector over
  typed plan, lifecycle, blocker, and bypass state. Packets are communication
  and provenance after disposition; unresolved packet intake can block
  authoritative selection, but packet ids do not become implementation work
  directly. Current owner rows are `MP377-P0-CHECKPOINT-AUTOMATION-S1`,
  `MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1`,
  `MP377-P0-NEXT-BLOCKER-LIFECYCLE-S1`,
  `MP377-P0-DEVELOP-NEXT-DECISION-SCHEMA-S1`,
  `MP377-P0-PACKET-DISPOSITION-LEDGER-S1`, and
  `MP377-P0-COMMAND-MANIFEST-LOOP-S1`, and
  `MP377-P0-PIPELINE-SCOPE-VALIDATION-S1`. The immediate implementation slice
  auto-includes managed projection dirt in governed checkpoint scope, preserves
  `.git/index.lock` as a retryable typed action result, and prevents
  receipt-only or stale partial staged indexes from hiding dirty source work.
  `MP377-P0-CHECKPOINT-STAGED-SNAPSHOT-RESTAGE-S1` owns the same-file
  staged-plus-unstaged retry case caught during dogfood checkpoint.
- 2026-05-08 typed TASK_COMPLETE continuation gate (MP-377):
  the keep-awake behavior that had been expressed through packet body prose now
  lives in `SessionTerminationPolicy`, `TaskCompleteDecision`,
  `continuation_anchor`, and `stop_anchor`. This extends existing owner rows
  `MP377-P0-T22AN-H`, `MP377-GUARDIR-LIFECYCLE-IDEMPOTENCY-AUTOMATION`, and
  `MP377-P0-DEVELOP-NEXT-DECISION-SCHEMA-S1`; it does not create a new
  top-level lane. The agent loop may continue after a completed handoff only
  when the typed policy and pending anchor still match the actor/session, and
  anchor packet kinds remain non-actionable inbox records.
- 2026-05-06 universal GovernanceLifecycle typed intake (MP-377):
  `rev_pkt_3114` was ingested as a narrowed typed correction, not a new
  top-level plan row. `MP377-GUARDIR-V21-A5` remains the packet/action-request
  lifecycle checkpoint and commit-seam proof, while existing queued rows now
  carry the generalized lifecycle expansion: graph materialization
  (`MP377-P0-EXC-S1B`), graph-walk lineage (`MP377-P0-EXC-S1C`), live role-lane
  dogfood (`MP377-P0-EXC-S1D`), lifecycle-aware guard cadence
  (`MP377-P0-GUARD-CADENCE-S1`), and lifecycle-linked deferral receipts
  (`MP377-P0-GUARD-DEFERRAL-S1`). `GovernedExceptionLifecycle` stays the first
  exception specialization under the broader future `GovernanceLifecycle`;
  lifecycle-relevant typed actions must eventually emit a lifecycle event or an
  explicit out-of-scope/noop reason.
- 2026-05-06 packet-expiry lifecycle audit (MP-377): `rev_pkt_3119` confirmed
  packet-expiry carry-forward as real architecture debt: substantial packet
  bodies currently skew toward expired/archived or stale-pending state versus
  typed apply. The correction is folded into existing rows, not a parallel
  slice: `MP377-P0-EXC-S1` owns the go-forward `SmartExpiryClassification`
  foundation, `MP377-P0-EXC-S1B` owns the one-time retroactive classification
  sweep and `RetroactiveSweepReceipt`, `MP377-P0-EXC-S1C` owns graph-walk
  lineage over classification outcomes, `MP377-P0-EXC-S1D` owns live
  no-content-lost dogfood, `MP377-P0-GUARD-CADENCE-S1` consumes lifecycle
  history for cadence, and `MP377-P0-GUARD-DEFERRAL-S1` owns
  `DeferredPacketReceipt` as the packet counterpart to `DeferredGuardReceipt`.
- 2026-05-06 governed-push report naming (MP-377): the repo-pack canonical
  latest push report is now `dev/reports/push/latest_push_report.json`, with
  `dev/reports/push/latest.json` accepted only as a legacy read fallback.
  Already-published no-op reruns now surface `published_remote` /
  `branch_already_pushed` truth without pretending post-push validation is
  green.
- 2026-05-06 boot-card memory authority guard closure (MP-377): the generated
  `InstructionBootCard` now carries the canonical "memory is short-term
  continuity" rule, and the legacy push-report fallback has an explicit
  broad-exception rationale so governed push preflight can distinguish real
  blockers from source-owned guard policy.
- 2026-04-29 Plan 4.1 Graph Intelligence safe slice (MP-377):
  `dev/active/ai_governance_platform.md` now carries `MP377-P0-T13A` as the
  owner row for widening the existing generated context graph, not a new graph
  authority. `ContextGraphSnapshot` is the ZGraph-compatible read model over
  typed truth: plan rows, packets, handoffs, findings, dogfood receipts, tests,
  workflows, configs, concept-intent anchors, and contract read/write evidence
  point back to canonical refs, while `devctl graph-walk --from ... --to ...`
  gives AI and humans a bounded cited traversal surface. Graph evidence may rank, compress, and
  explain what to read next; it must not remove required deterministic
  commands, guards, probes, packet lifecycle checks, or typed runtime
  authority from `ProjectGovernance`, `ReviewState`, `SessionPosture`,
  `DashboardSnapshot`, `ControlPlaneReadModel`, or the master-plan store.
- 2026-05-01 Typed `/develop` topology and knowledge-flow intake (MP-377):
  `dev/active/autonomous_governance_loop_v2.md` now owns the durable execution
  spec for `DevelopmentModeTopology`. `/develop` is a typed composition layer
  over startup, planning, review-channel, graph, guard, and governed mutation
  state, not a provider-default team roster or Plan 4.1 dogfood loop. Any
  provider/human can occupy Coordinator, Builder, Reviewer, Plan Intake
  Steward, Researcher, Knowledge Synthesizer, Architect, Quality Engineer,
  Dogfood Tester, Runtime Watcher, or Operator workstreams when typed
  authority grants the required capabilities. Plan Intake Steward owns the
  promotion of packet-carried plan, finding, guard, probe, and architecture
  intent into durable MasterPlan/PlanRow, FindingReview, GuardPromotionQueue,
  and knowledge artifacts with packet ids retained as provenance before TTL
  expiry, so packets stay a communication lane instead of becoming the source
  of truth. Approved external research routes through cited
  `ResearchEvidenceBundle` / `ExternalSourceEvidence`, then synthesis promotes
  durable `KnowledgeSynthesisRecord`, `ContextGraphSeed`,
  `PointerRefIndexEntry`, plan, and guard-candidate artifacts back into
  canonical sinks. `context-graph`, ConceptIndex/ZGraph-compatible views,
  pointer refs, system-map, ContextPack, and startup-context consume those
  artifacts as generated projections, never as runtime authority.
  The same topology now carries a pressure-based `DevelopmentScalingContract`
  with user/developer-facing modes: Controller Only, Intake Fanout, Review
  Fanout, Research Fanout, Watcher Fanout, Isolated Builder Fanout, and Leased
  Live-Tree Builder. Packet pressure, near-TTL packet intent, review/probe
  backlog, graph/system-map coverage gaps, independent next slices, stale
  runtime windows, and `AgentDispatchRouter.safe_to_fanout` decide whether
  extra read-only/intake/review/research/watcher lanes are useful. Mutable
  fanout remains gated by disjoint path scopes, registered worktree identity,
  `OrphanSnapshot`, and explicit `MutationLease`; only the leased live-tree
  builder may edit the primary checkout. Every spawned lane receives a
  `WorkerPacket` with mode, owner, scope, evidence, reply target, and TTL, and
  handoff/progress must flow back through correlated packets plus durable
  plan/finding/run/ingestion artifacts.
  Claude beta testing then found the first executable gap: the typed contracts
  existed, but `devctl develop` itself was not registered as a CLI command.
  The current slice adds the read-only CLI entrypoint, shared
  `development_role_adapters.py` Codex/Claude role matrix, generated
  `dev/templates/slash/develop/roles.md` catalog, and thin provider command
  consumers so `/develop` role lenses no longer create a second scheduler,
  grant mutation, or introduce independent dashboard polling.
  Current Claude packet findings from `rev_pkt_2705` and expired source
  packets `rev_pkt_2691`, `rev_pkt_2696`, `rev_pkt_2697`, `rev_pkt_2699`,
  `rev_pkt_2700`, `rev_pkt_2701`, `rev_pkt_2702`, and `rev_pkt_2704` are
  durable MP-377 intake, not queue-only work: transition disambiguation,
  expiry/apply-gap, ambiguity projection, carry-forward debt, command hangs,
  and work-board duplication remain linked under `MP377-P0-T22AN-D/F` until
  guard/probe or implementation closure.
  Claude dashboard packet `rev_pkt_2708` then proved the missing
  creation-time binding layer: durable packets should become typed plan,
  finding, guard, or lifecycle state when posted, not only after manual
  triage. `PacketCreationBinding` now binds plan-scoped durable packets to
  `PlanRow` ownership during post finalization, and the live follow-up
  `rev_pkt_2710` auto-created `PKT-BIND-REV-PKT-2710` in
  `dev/state/plan_index.jsonl` plus the generated MASTER_PLAN projection.
  `PacketDebtRemediationReport` and `PacketDurableIngestionReceipt` now give
  the old carry-forward rows a typed remediation path: `/develop
  audit-packets` clusters bounded debt, names whether each packet should be
  plan-ingested, lifecycle-linked, or manually triaged, and the reducer treats
  durable ingestion receipts as real ownership instead of queue state. The
  remaining follow-up is the guarded production drain/freshness policy for
  legacy communication packets.
  Claude slash-flow packet `rev_pkt_2725` then validated the user-facing
  packet-attention path by running `/develop` as an agent would. The controller
  now mirrors the packet-attention command as top-level `next_step_command`,
  lists the triggering packet in `pending_actionable_packet_ids`, and
  prioritizes durable packet row `PKT-BIND-REV-PKT-2725` before ordinary next
  slices. The 2026-05-06 dogfood follow-up closed the `audit-packets` self-loop:
  once packet pressure is classified, `PacketAttentionIngestionDecision.next_command`
  becomes the continuation command, top-level `next_step_command`, and first
  `next_commands` row instead of sending the caller back to the audit reducer.
  `review-channel --action show --packet-id <id>` is the typed
  packet-body read surface, and `history --packet-id <id>` now resolves the
  exact packet row instead of forcing raw artifact grep. Remaining Bundle FF
  follow-up stays in MP-377: caller-aware required-command rendering,
  sibling packet-count conservation, inbox previews, acked-but-queued queue
  visibility, and unambiguous archived-with-durable-owner disposition names.
  Claude Bundles HH/JJ/KK then proved the broader orchestration gap through
  real slash-command dogfood and a multi-session spawn test. `/develop watch`
  now renders authoritative runtime rows from `AgentWorkBoardProjection` /
  `AgentSyncProjection`, auxiliary `agent-mind` summaries with
  `authority_policy=auxiliary_context_only`, and raw provider session-discovery
  diagnostics that name sessions visible in provider JSONL streams but not yet
  registered on the typed work board. `/develop audit-packets --drain-packets`
  exposes the existing deterministic packet-debt writer for eligible
  plan-row ingestion receipts, keeping packet transport as provenance rather
  than source-of-truth work state. Remaining Bundle JJ/KK closure is the
  orchestrator action loop: consume these packet debt, peer-mind,
  session-discovery, smartness-input, and fanout-pressure signals and write
  bounded `OrchestratorAction` / `WorkerPacket` decisions instead of relying on
  each agent to rate-limit and triage manually. Bundle LL (`rev_pkt_2732`)
  narrowed the multi-session finding from "never detected" to a real
  spawn-to-typed-registration lag, added `AckQueueAgingSignal` to that same
  orchestration input set, and recorded separate UX debts for misleading
  preview-only pause/resume verbs, noisy `tandem-validate` rendering, and the
  `view --surface ai` default-mode mismatch. Bundle MM (`rev_pkt_2733`)
  further corrects the implementation target: `agent-loop` already exposes the
  closest existing orchestrator substrate, including loop identity, wake,
  proof, topology, authority, and action-request surfaces. The next
  orchestration slice should extend `agent-loop` with event refresh,
  packet-attention/audit-packet inputs, proof generators for
  `reviewer_semantic_review` and `round_proof`, and writer-driving
  `OrchestratorAction` / `WorkerPacket` outputs instead of creating a parallel
  daemon. The same live status post exposed a communication-contract follow-up:
  provider-to-provider `system_notice` packets currently cannot carry
  `target_role` / `target_session_id`, so session-scoped status delivery still
  needs a typed non-plan packet targeting path. Follow-up dogfood then proved
  the stop-after-status smell as a controller invariant: agents must not decide
  to stop from local completion while typed continuation signals, watcher
  leases, stale projections, pending packets, or closure checks still require
  action. `/develop` now carries `ContinuationRequiredSignal`,
  `WatcherLease`, watcher status, and final-response guard inputs so the next
  command and the Claude-lane watcher are typed state, not chat memory.
- 2026-04-27 Plan 4.1 Slice C/D zref + enum-connectivity repair (MP-377):
  governed push now refreshes `commit_pipeline.json` proof identity from the
  current review-state tick after push-result synchronization, so stale
  pipeline `snapshot_id`/`zref` values cannot block publication after a
  managed receipt refresh. The same slice adds warning-only
  `check_typed_enum_connectivity.py`, registers it in the shared governance
  bundle, and centralizes `OperatorInteractionMode` launch/approval policy in
  `operator_context.py` so enum values connect to runtime decisions before
  later Slice C enforcement promotion.
- 2026-04-27 startup push-state managed receipt classification (MP-377):
  startup authority now uses the same managed receipt artifact set as
  governed push when counting dirty paths, so live `REVIEW_SNAPSHOT.md` or
  `bridge.md` projection refreshes do not masquerade as authored source edits
  after a local checkpoint. `push_enforcement` also separates unpublished
  source commits from managed receipt commits so publication-backlog pressure
  stays visible without turning receipt accumulation into a source-work
  blocker.
- 2026-04-27 governed-push typed `next=` recovery-loop automation (MP-377):
  `devctl push` now has a `pre_validation_recovery_loop_repair` phase between
  managed projection sync and routed validation. Recoverable startup-context
  failures are no longer a manual AI/operator checklist: the phase emits
  `TypedAction(action_id="vcs.recovery_loop_repair")`, follows only
  allowlisted headless review-channel `next=` commands, stops after five steps
  or 180 seconds, and fails closed when the cascade reaches operator scope.
  `check_review_surface_consistency.py` also treats
  `startup_context.reviewer_gate.reviewer_mode` as the reviewer-mode authority
  and projects bridge/coordination/registry values through that source.
- 2026-04-28 completed-handoff session-outcome closure (MP-377):
  `stage_commit_pipeline` packets with full guard-bundle evidence now emit
  `AgentSessionOutcome(outcome=completed_handoff)` through the existing
  review-channel event log, and `CollaborationSession.session_outcomes`
  projects the receipt for status/startup/push readers. Governed push may
  skip `pre_validation_recovery_loop_repair` only when that receipt matches
  the current prepared-session token, or when provider-matching conductor
  metadata is absent and the packet target is bound to the current
  `devctl_commit:<head>` / full managed-receipt source chain back to the
  content commit's handoff parent. Startup-context must still report
  `runtime_missing` / `no_live_agents`; stale or mismatched receipts still run
  the existing bounded recovery loop. The remaining T20 scope is
  `process_died` / `unresolved` producer coverage plus Codex-stall /
  flip-mode convergence.
- 2026-04-28 hook-time generated-surface receipt extension (MP-377):
  the same completed-handoff publication authority now reaches the raw-git
  pre-commit permission boundary for push-owned generated-surface receipts.
  The hook only accepts `DEVCTL_MANAGED_PROJECTION_RECEIPT_COMMIT=1` as
  read-only authority evidence when the staged paths are managed projection
  artifacts and the completed-handoff target resolves
  through the full managed receipt/source chain back to the packet's
  `devctl_commit:<head>` parent; source commits, stale handoff targets, and
  mismatched providers still fail closed through `commit_permission`.
- 2026-04-28 DashboardSnapshot v3 / typed-next / bridge-freshness slice
  (MP-377 Plan 4.1): CLI dashboard, `claude-loop`, `mobile-status`, and the
  Operator Console now share `DashboardSnapshot` v3 sections for agent-mind,
  session outcomes, ACK freshness, active Codex sessions, and system topology.
  `dashboard --follow` is live, Codex watchdog launches refresh the
  `agent-mind` projection on new rollout activity, bridge freshness checks use
  typed `ReviewState.bridge.last_codex_poll_*`, and implementer ACK checks use
  `ack_freshness_authority.is_implementer_ack_current` rather than
  compatibility prose. System-authored `stage_commit_pipeline` packets now
  auto-ACK/apply only under the safe runtime allowlist with full guard-bundle
  evidence, and repeat stage handoffs dedupe by target agent plus
  `devctl_commit:<HEAD>`.
- 2026-04-28 typed handoff/liveness closure (MP-377 Plan 4.1): Codex
  launcher scripts now run a session-end `task_complete` guard that emits the
  missing `stage_commit_pipeline` action_request to Claude when a completed
  Codex session forgot the typed handoff packet. `SessionLivenessSignal` now
  owns the portable `alive` / `degraded` / `detached_runtime_only` / `dead`
  provider signal in `devctl.runtime`; status projects it as
  `session_liveness_signals`, dashboard/mobile receive it through
  `DashboardSnapshot.session_liveness`, and startup/control-plane counts prefer
  the typed signal over bridge conductor booleans.
- 2026-04-28 Plan 4.1 dogfood cleanup (MP-377): the Finding F/G/H/J/K/L/M/N/O/P/Q
  bundle now collapses reviewer-mode, packet queue, Action Requests,
  packet-post, context-graph, tandem-validate, triage, and `check` quick
  surfaces back onto typed authority. Effective reviewer mode renders as the
  compatibility bridge authority while declared mode stays visible, packet
  inbox counts only live pending work, Action Requests ignore delivery
  receipts, packet posting has semantic idempotency plus uniform kind schema,
  bootstrap graph summaries no longer claim false zero-edge evidence,
  tandem dry-run starts at its markdown report header, mutation outcome shims
  work in package/direct modes, process-sweep cleanup is opt-in, and dead
  sessions without terminal outcomes project typed
  `AgentSessionOutcome(outcome=unresolved)` rows.
- 2026-04-29 Plan 4.1 packet lifecycle/disposition hook (MP-377): review
  packets now reduce per-packet `acknowledged_events`, `acted_on_events`,
  `PacketLifecycleHistory`, and `PacketDisposition` state. Clock-expired
  pending packets are archived with
  `archive_classification:clock_expired_without_disposition` instead of
  remaining invisible lost-work candidates, plan-targeted `apply` transitions
  can append idempotent generated `PacketPlanIntegration` rows, and the
  deferred Finding CC/II/R/S/T/V/W/X/Y/Z/AA/BB/FF/GG/HH queue is now routed into
  `MP377-P0-T08A..T08E`, `MP377-P0-T14A..T14B`, `MP377-P0-T19A`,
  `MP377-P0-T21A`, and existing `MP394-A` plan rows for follow-up execution.
- 2026-04-29 dashboard/control-plane read-model parity follow-up (MP-377):
  dashboard now threads repo governance plus the current typed review state
  into `build_control_plane_read_model` through the shared builder API instead
  of constructing a separate bridge-derived view. `ControlPlaneReadModel`
  treats typed bridge conductor-active rows as liveness hints only when
  reviewer mode and fresh poll/session evidence bound them, keeping dashboard,
  startup, and control-plane daemon rows aligned during remote-control
  sessions.
- 2026-04-29 GuardIR Plan 4.1+ V2.1 ingestion and priority lock (MP-377):
  `dev/active/ai_governance_platform.md` now preserves the V2.1 superset as
  the scope-preserving ingestion source, while `dev/state/plan_index.jsonl`
  carries typed `PlanRow` rows for the live priority gates. Execution remains
  bounded to A.5 checkpoint through packet authority, then ADR-013
  `RuntimeAgreementReport`, then `PortabilityLeakInventory`, then typed
  swarm-readiness/worker-packet planning. GuardIR extraction, push, and mutable
  fanout remain blocked until those gates are green; Claude stays watcher /
  verification owner through typed review-channel authority.
- 2026-04-29 GuardIR invariant-review intake (MP-377): queued follow-up rows
  now lock the accepted hardening deltas without widening the active A.5 slice:
  governance event-log timebase, predictive transition simulation/dead-end
  guards, graph constraint explanations, bounded AI query plans with
  action-grade explain-back, exact-one packet terminal outcomes, resource-aware
  swarm scheduling, semantic portability golden replay, and authority-leak /
  temporal multi-writer drift detection. These remain blocked behind
  checkpoint/runtime agreement/readiness gates.
- 2026-04-29 GuardIR intelligence-delta refinement (MP-377): concrete queued
  row targets now name the first implementation seams for that evidence spine:
  `check_packet_lifecycle_single_authority.py`, `GuardSpec`,
  `check_contract_value_domains.py`, `check_authority_source_integrity.py`,
  `GraphAuthorityRole`, `GraphContradictionIndex`,
  `GuardFailureRemediationPacket`, `GuardEffectivenessReport`,
  `GraphScopeProof`, and `RuntimeAgreementReport.quorum_fingerprint`.
- 2026-04-29 GuardIR Rust shadow contract oracle intake (MP-377): queued
  `MP377-P0-T22X` adds a post-A.5 read-only Rust oracle that deserializes
  Python-emitted governance JSON into strict Rust contract models for
  `ActionResult`, packet lifecycle, packet disposition, and oracle reports.
  Rust may block as guard evidence through a Python wrapper, but it may not
  write packets, apply packets, mutate plan rows, commit, push, fanout, or
  replace Python lifecycle authority.
- 2026-04-29 GuardIR automation-opportunity catalog (MP-377): Claude's
  checkpoint retry evidence is now queued as `MP377-P0-T22Y-A..T22Y-J`.
  The top priority is auto-deriving safe action-request role/identity/pipeline
  capability evidence from typed state and emitting remediation packets when
  evidence is missing. Follow-ups cover retry idempotency, managed projection
  pre-push handling, stale-process evidence-cycle exemptions, mutation-badge
  refresh scheduling, finding target metadata, dogfood CLI discoverability,
  dogfood-to-remediation packet conversion, plan-index freshness, and
  `/remote-control` typed attach identity.
- 2026-05-04 remote-control lifecycle slice (MP-377): `MP377-P0-T22Y-J` is
  now in progress through typed plan ingestion receipt
  `plan-ingest-610c2d0bf9fb4a3b`. The implementation target is one
  `devctl remote-control` backend for `start`, `enter`, `heartbeat`, `exit`,
  `status`, `doctor`, and `dry-run`; generated `/project:typed-remote-control`
  stays as the only manual/recovery project slash, retired
  `/project:remote-control` and `/project:bridge-loop` no longer collide with
  Claude built-ins, `~/.claude/sessions/<pid>.json` `bridgeSessionId` is now
  the live on/off proof for Claude's built-in Remote Control state, and
  `remote-bridge-loop.sh` is wrapper glue only.
- 2026-05-05 ground-truth design preflight slice (MP-377): `MP377-P0-T22AN-AO`
  now owns the connected architecture pipeline exposed as
  `devctl develop design-preflight`. The flow reduces `ReviewState` into
  `RuntimeTruthSnapshot`, probes agent-mind/provider session state,
  connectivity, command registry, startup quality signals, and existing
  contracts, records `GroundTruthProbeRunReceipt`, and lets
  `check_ground_truth_probe_gate.py` block runtime/proof-channel edits that
  skipped upstream ground truth before adding or extending authority surfaces.
- 2026-04-29 GuardIR Rust closed-domain/oracle catalog (MP-377): Claude's
  two-agent Rust survey is queued as `MP377-P0-T22Z-A..T22Z-J`. The rule is:
  closed-domain values get enums, open-domain values stay strings/JSON with
  explicit exemption evidence. Rows cover Python-governance oracle expansion,
  daemon provider and memory artifact enums, a shadow daemon-event validator,
  persistent-config mode deserializers, banner fallback cleanup, Rust tooling
  hardening, open-domain skip records, and a final Claude/Codex beta proof
  gate before any done/extraction/fanout claim.
- 2026-04-29 GuardIR graph-oracle + bilateral contract parity catalog
  (MP-377): graph snapshots and Rust/Python shared contracts are queued as
  `MP377-P0-T22AA-A..T22AA-H`. Rows cover strict Rust graph models, a
  shadow graph oracle, shared `contract_registry.jsonl`, canonical schema
  fixtures, bilateral Rust/Python schema parity, schema-version monotonicity,
  contract-parity bundle wiring, and a Claude/Codex beta proof gate. The
  target is two languages, one registry, one fixture set, and preflight Rust
  oracle evidence before extraction, push, fanout, or graph-backed routing.
- 2026-04-29 GuardIR Rust contract-compiler sharpening (MP-377): the
  `MP377-P0-T22AC-A..T22AC-E` rows sharpen the Rust plan so oracles act as
  read-only contract compilers, not alternate runtimes. Stable shared
  governance JSON must pass Rust oracle/parity proof before it can be trusted
  as guard, graph-routing, push, extraction, or fanout evidence. The rows also
  make touched-surface preflight mandatory for shared-contract edits, require
  graph-oracle proof before graph-backed routing, define bilateral
  contract-stability/migration evidence, and preserve the hybrid boundary:
  Rust validates deterministic contracts while Python remains the operational
  writer/orchestrator until per-contract migration is proven.
- 2026-04-30 GuardIR Rust graph-oracle ADR intake (MP-377): the
  `MP377-P0-T22AD-A..T22AD-J` rows add the detailed read-only Rust validation
  plan behind Slice 4.1. Rows sharpen strict graph snapshot invariants,
  graph-domain manifests/proptest, graph authority-taint and health facts,
  bilateral schema fingerprints/fixture parity, packet lifecycle replay,
  packet attestation, `ActionResult` / `CheckResult` validation, daemon/config
  validators, plan-index validation, open-domain exemption records, and Rust
  tooling preflight. Python remains the operational writer/orchestrator; Rust
  supplies strict JSON-over-subprocess preflight evidence only.
- 2026-04-30 Plan 4.1 agent-sync reducer projection intake (MP-377): queued
  `MP377-P0-T22AE-A..T22AE-G` accepts the `agent_sync` direction as design
  intake while requiring implementation to inspect the actual reducer, packet
  lifecycle, event model, evidence, and projection-write seams first. The
  target is reducer-derived `review_state.agent_sync` with projection
  freshness metadata, per-packet scoped evidence rows, explicit
  `responds_to_packet_id` / `causal_packet_ids` correlation, ACK as
  lower-bound receipt evidence only, status derived from actor activity rather
  than partner wait state, a `sync-status` surface for dashboard/`claude-loop`,
  T22Y-A positive/negative fallback-proof tests, and swarm/Rust-oracle gating
  only after stable queryable projection evidence exists.
- 2026-04-30 Plan 4.1 agent-sync developer command and swarm UX intake
  (MP-377): queued `MP377-P0-T22AF-A..T22AF-H` so the chat-only command ideas
  do not get lost. The slice keeps UX narrow and typed: `/agent-sync` and
  `devctl agent-sync` are adapters over reducer-derived `sync-status`;
  reviewer/conductor/architect/research/dogfood/remote flags normalize through
  `CollaborationSession`, `AuthoritySnapshot`, packet targets, and repo-pack
  policy; `/swarm --max-workers ... --iterations ...` produces a bounded
  fanout plan with one live-tree integrator; development mode flags become
  named guard profiles plus waiver or `BypassReceipt` evidence rather than raw
  `--skip`; and workflow commands such as `/handoff`, `/review-now`,
  `/blocked`, and `/negative-control` emit typed review-channel packets with
  explicit correlation.
- 2026-04-30 Plan 4.1 system-wide command/mode compiler intake (MP-377):
  queued `MP377-P0-T22AG-A..T22AG-H` to broaden the same idea across the
  whole governance stack. Current inventory shows the need: `devctl list`
  exposes check profiles such as `ci`, `quick`, `fast`, and `ai-guard`, while
  `devctl discover` reports 88 commands, 37 guards, 28 probes, 5 surfaces,
  and 20 bootstrap commands. The new slice defines `CommandModeRequest` /
  `CommandRunPlan` as the shared compiler target for slash, CLI, MCP, mobile,
  dashboard, and Operator Console frontends; feeds it from `discover`,
  `quality-policy`, `check-router`, packet lifecycle, and repo-pack policy;
  adds shared role/profile grammar and flag parity checks; makes guard/probe
  profiles typed with waiver/defer evidence; projects command status to
  dashboard/`claude-loop`/mobile/MCP; wires dogfood coverage into command
  modes; and lets context-graph explain command-to-contract-to-guard edges.
- 2026-04-30 Plan 4.1 typed override receipt intake (MP-377): queued
  `MP377-P0-T22AH-A..T22AH-G` as the controlled-deviation layer for active
  plan scope, role assignment, priority route, guard profile, mutation lease,
  and swarm budget. Overrides must be event-log visible, reducer-projected,
  command-mode compatible, and surfaced in `agent_sync` / `sync-status`.
  Required fields include override type, reason, scope, requester, reviewer or
  approver, affected plan/packet/agent/guard/path refs, expiry, risk level,
  closure requirements, and docs-debt behavior. Expired overrides render as
  stale/blocking; closure requires `override_id` plus packet correlation; role
  overrides never imply mutation authority without an explicit lease or
  integrator grant; guard overrides record deferred guard evidence instead of
  permitting raw `--skip`. V1 is intentionally packet-carried through
  review-channel override packets and existing packet lifecycle; dedicated
  override event families are deferred until the projection is proven.
- 2026-04-30 Plan 4.1 lane barrier, session handoff, and auto-wake intake
  (MP-377): queued `MP377-P0-T22AI-A..T22AI-I` as the typed automation layer
  that keeps Claude, Codex, subagents, and future frontends on the same
  timeline. Lane advancement becomes reducer-projected: completion packets and
  ACKs do not advance a lane without reviewer acceptance, blocker dismissal,
  accepted corrected completion, or an explicit `OverrideReceipt`. The slice
  also adds `sync-status` / `/agent-sync --can-start-next-lane` barrier
  surfaces, session rollover proof for old-session cleanup, new-session launch,
  and accepted handoff, configurable finish-file/scope/lane reviewer wake
  pings, blocker-pivot task allocation, a typed agent work-board projection,
  lifecycle-aware idempotency for pings and retries, and optional
  worktree-backed lanes behind leases plus orphan-inventory evidence.
- 2026-04-30 Plan 4.1 agent-mind auxiliary fallback and final-response guard
  intake (MP-377): queued `MP377-P0-T22AJ-A..T22AJ-F` so `agent-mind` becomes
  backup diagnostics rather than hidden sync authority. The slice adds
  auxiliary mind hints to `agent_sync` / the work board with cursor,
  staleness, confidence, and conflict metadata; final/progress-response
  preflights that block "done" answers while reducer state shows open packets,
  lane barriers, stale awaited actors, unclosed delegated work, overrides,
  handoff/launch proof gaps, guard debt, bypass debt, or checkpoint gates;
  uncertainty reports when reducer state and mind hints disagree; bounded
  fallback reads for command modes; and tests proving ACKs, uncorrelated
  completions, and agent-mind task-complete hints cannot close work.
- 2026-04-30 Plan 4.1 dashboard/operator typed packet authoring intake
  (MP-377): queued `MP377-P0-T22AK-A..T22AK-F` to close the two-way dashboard
  comms gap without adding dashboard chat or a second control plane.
  Dashboard, Operator Console, mobile, and MCP become frontends that compile
  operator actions into `CommandModeRequest` / `CommandRunPlan` and the
  existing review-channel packet authoring backend. The slice adds an
  `Author Packet` UX over `review-channel --action post`, preserves
  `responds_to_packet_id` / `causal_packet_ids`, idempotency, lifecycle, and
  `agent_sync` projection, enforces the same caller authority and mutation
  guardrails as CLI writes, returns typed diagnostics, and tests inbox,
  history, `agent_sync`, correlation, authority rejection, and no-terminal-hop
  behavior.
- 2026-04-30 Plan 4.1 agentic governance standards crosswalk intake
  (MP-377): queued `MP377-P0-T22AL-A..T22AL-H` to map current external
  agentic-governance references into repo-owned controls without claiming
  certification. The slice adds `AgenticGovernanceControl` /
  `AgenticRiskControl` rows for NIST AI RMF, ISO/IEC 42001, FINOS AIGF v2.0,
  Singapore IMDA/WEF Agentic AI MGF, and OWASP Agentic Applications; an
  action-space boundary catalogue for tools, files, terminal, git, network,
  dashboard, MCP/mobile, subagents, worktrees, and release surfaces; a HITL
  checkpoint taxonomy for high-impact actions; unique agent identity and
  privilege traceability; OWASP/FINOS-aligned monitoring and red-team probes;
  standards-aware graph/dashboard/audit reports; framework-interoperability
  evaluation for LangGraph/AutoGen/Mastra concepts; and tests that prevent
  unmapped controls, missing evidence, or implied certification claims.
- 2026-04-30 Plan 4.1 DevPack session handoff intake (MP-377): queued
  `MP377-P0-T22AM-A..T22AM-H` so a Codex/Claude session can be turned into a
  senior-dev-readable and machine-readable development pack. The slice keeps
  event log / reducer / `review_state` authority as the source of truth,
  excludes private chain-of-thought, and exports recorded rationale from
  packets, findings, decisions, evidence refs, checks, overrides, guard
  deferrals, agent-mind auxiliary events, and git diff summaries. It adds
  `/dev-pack` and `review-channel --action dev-pack`, decision-graph and
  architecture-lesson sections, strict-mode governance gap detection,
  audience-specific render modes, optional summary packet posting, and tests
  that catch unaccepted completions, lane advancement without acceptance or
  override, missing packet correlation, unevidenced checks, prose-only
  architecture decisions, and dirty files not mapped to packets.
- 2026-05-06 governed exception lifecycle correction (MP-377): the earlier
  raw `BypassReceipt` direction is superseded by `MP377-P0-EXC-S1`, with
  follow-up typed rows `MP377-P0-EXC-S1B`, `MP377-P0-EXC-S1C`, and
  `MP377-P0-EXC-S1D` for generated lifecycle context-graph materialization,
  focused lineage traversal, and live registered-agent role-lane acceptance.
  The related
  `MP377-P0-T08F` packet-lifecycle row is the role/session inbox prerequisite:
  packets route to reviewer/implementer/operator roles plus exact sessions
  when scoped, not to provider names as authority.
  Bypass is not the feature; exception -> repair -> proof -> learning is the
  feature. Slice 1 stays read-only for execution and only adds typed
  contracts, validation, registry/SYSTEM_MAP visibility, durable plan-source
  retention, and read-only `devctl exceptions pending/validate` surfaces.
  Semantic-link metadata belongs in typed `ContractSpec.cross_links`; comments,
  `typing.Annotated`, generated graph outputs, bridge text, dashboards, and
  markdown remain documentation/projections rather than authority. Green unit
	  tests do not prove the collaboration loop: end-to-end acceptance requires
	  live registered-agent dogfood across role lanes, with provider labels such
	  as Codex and Claude treated as runtimes only. `MP377-P0-ROLE-MATRIX-DOGFOOD-S1`
	  now owns the future proof matrix: registered agents must enter typed session
	  posture as implementer, reviewer, operator, or observer; role and authority
	  state decide allowed actions; handoff routes through typed packets or plan
	  rows; mutation requires `TypedAction`; and proof requires `ActionResult`,
	  `RunRecord`, or `ValidationReceipt`. If boot-card dogfood hits
	  `authority_result=blocked` for coordination resync or code-shape debt, record
	  fail-closed evidence and continue only read-only reducers instead of claiming
	  multi-agent automation is green.
- 2026-05-06 guard cadence / physical dogfood correction (MP-377): green
  unit tests are regression evidence, not sufficient physical proof for major
  governance features. `MP377-P0-GUARD-CADENCE-S1` is queued as the typed owner
  for graph-scoped guard scheduling: run safety/proof/authority checks
  immediately, feature-local checks after coherent chunks, subsystem
  architecture checks at stabilization points, full closure checks before plan
  status/checkpoint/push, and whole-system cleanup as separate follow-up rows.
  Once the typed lifecycle ledger exists, guard cadence must also consume
  `GovernanceLifecycle` history for run timing, bottlenecks, retry frequency,
  and proof latency. `MP377-P0-GUARD-DEFERRAL-S1` remains the child slice for
  deferrable quality-debt receipts linked to lifecycle event ids; open
  deferrals block checkpoint, push, resolution, slice close, and success claims
  until rerun proof closes them. This is not a bypass: security, command
  exposure, mutation authority, raw bypass,
  generated-markdown authority, stale-HEAD, missing receipt, and missing push
  proof gates cannot be deferred. The cadence slice must physically compare
  always-run versus staged-cadence dogfood and
  record elapsed time, failures caught, refactor churn, late failures, false
  positives, out-of-scope file churn, and final quality.
- 2026-05-06 operator-correction intake failure (MP-377): a Codex process
  failure was observed when operator architecture feedback was initially folded
  into broad cadence/plan prose instead of immediately refining a scoped typed
  row with its own `PlanIntentIngestionReceipt` and `PlanSourceSnapshot`.
  `MP377-P0-OPERATOR-CORRECTION-INTAKE-S1` is queued to close that process gap:
  operator corrections that add or modify governance rules, acceptance gates,
  closure blockers, or agent-process invariants must be typed first, projected
  second. Broad markdown summaries cannot be the first durable authority.
- 2026-04-27 governed-push execution-truth invariant (MP-377):
  the `rev_pkt_2027` / `rev_pkt_2029` regression proved a Class-A trust
  break: a push report could claim `published_remote` with a fixture branch
  and stale approved target while the live remote ref did not advance. The
  push action/report path now forces `TypedAction.parameters.branch` from
  `git rev-parse --abbrev-ref HEAD`, binds approved target identity to live
  publication authorization plus current worktree and HEAD, fails stale
  authorization proof older than one hour, and downgrades any execute=true
  publication claim without fetch/preflight/push subprocess evidence or matching
  remote-ref proof to `SilentPushFailure`. Terminal post-push states add the
  separate `post_push_steps` evidence requirement so an in-flight
  `post_push_bundle_pending` snapshot does not masquerade as post-push green.
- 2026-04-27 Plan 4.1 rev_pkt_2035 architectural bundle placement (MP-377):
  the consolidated Claude/Explore bundle is now durable plan scope, not chat
  memory. `ai_governance_platform.md` tracks `MP377-P0-T13` through
  `MP377-P0-T21` for SYSTEM_MAP-as-typed-state, Codex self-dogfood
  verification before `stage_commit_pipeline`, semantic/canonical-seam guard
  coverage, Slice E role command-gating and `DEFAULT_PROVIDER_ROLE_MAP`
  retirement, ReviewState/ActionResult/parser parallel-system retirement, and
  agent-proof-of-navigation tests, plus the 2026-04-28 additions for generated
  instruction-surface wedges, agent-session outcomes, and command capability
  evidence over the existing system catalog. The slice order is warning-first
  guards plus the bounded push-finding seam now, Slice E before broad Slice D
  refactors, and typed `system-spine` work folded into the existing
  context-graph/system-map projection chain rather than a parallel system.
- 2026-04-27 governed-commit self-resolution and structured errors (MP-377):
  `devctl commit` now extends the existing commit pipeline instead of asking an
  agent/operator to retry mechanical blockers. Guard replay auto-runs one
  bounded host-process age-out retry when `host-process-cleanup-post` is the
  blocker, shared git helpers back off transient `.git/index.lock` contention
  for index writers, and `ActionResult` carries structured `errors`,
  `reason_chain`, `remediation`, and `auto_executable` fields for stage,
  guard, and commit reports.
- 2026-04-23 session-resume bootstrap repair (also under MP-377):
  `session-resume --role reviewer|implementer` now calls
  `ControlPlaneReadModel` through `ControlPlaneReadModelOptions` for
  governance and frozen review-state inputs, keeping the canonical new-session
  bootstrap path aligned with the shared control-plane API.
- 2026-04-22 worktree-orphan architecture slice (also under MP-377): the
  orphan-prevention design now has typed slice-one runtime contracts for
  `OrphanSnapshot`, `OrphanSource`, `OrphanReconciliationDecision`,
  `CheckoutInventory`, `WorkPublicationLedger`, `SessionLease`,
  `WorktreeBaseline`, and `AcceptAllOrphansAction` / receipt payloads, plus
  platform `ContractSpec` registration so the contract-connectivity and
  platform-contract closure guards prove these are not orphan dataclasses.
  This is the foundation for mode-invariant launch/push/fanout gates that
  classify current checkout, registered worktrees, planned worker roots,
  sibling repo copies, deep-scan repos, prunable/missing worktrees, stashes,
  CI roots, and latent state before accepting more work.
- 2026-04-22 worktree-orphan inventory slice (also under MP-377):
  `python3 dev/scripts/devctl.py orphan-inventory --format md` now emits a
  report-only `OrphanInventoryReport` for the bounded local scan. It covers
  the current checkout, registered/prunable git worktrees, planned worker
  lanes, bounded same-parent same-origin sibling clones, and stash entries
  including untracked-section evidence, while explicitly leaving
  `gates_evaluated=false` until the later launch/push/fanout gate slice.
- 2026-04-22 worktree-orphan projection slice (also under MP-377):
  `compute_orphan_snapshot()` now derives a deterministic `OrphanSnapshot`
  from the bounded inventory report, `startup-context` emits that projection
  as typed startup evidence, and governed commit/push preflight consult it as
  advisory-only warning state before any later hard gate lands.
- 2026-04-22 worktree-orphan portability dogfood (MP-377 with MP-376 proof):
  `orphan-inventory` now accepts `--repo-path` for report-only external
  checkout scans. A fresh `/tmp/pre-commit-hooks-governance-proof` rerun
  passed the orphan inventory cleanly with zero unresolved sources; the
  companion `probe-report --repo-path --adoption-scan` and
  `check --profile quick --repo-path --adoption-scan` runs surfaced only
  adopter/startup evidence, not an orphan-scanner engine blocker.
- 2026-04-22 stale-pipeline recovery automation (also under MP-377):
  `devctl pipeline --action auto-recover` now classifies the current
  remote commit/push pipeline into no-op, recover, refresh-authorization,
  abandon, or fail-closed ambiguous, dispatches the existing explicit
  recovery action when safe, and writes `PipelineAutoRecoveryReceipt`.
  This closes the ADR-007 manual abandon/recover/refresh selection loop while
  preserving the existing audit receipts for the sub-action it invoked.
- 2026-04-23 remote-control sandbox prompt routing (MP-377):
  `devctl commit` now converts pre-pipeline `.git/index.lock` denial into a
  typed `action_request` with `requested_action=stage_commit_pipeline` targeted
  at the active remote-control attachment provider. The live proof emitted
  `rev_pkt_1691` to Claude for the current checkpoint instead of requiring a
  local approval prompt.
- 2026-04-23 read-only advisory next-command projection (ADR-005 partial
  closure under MP-377): `advisory_next_action_role_filter.py` now provides
  the shared projection used by startup action routing, `AuthoritySnapshot`,
  `ControlPlaneReadModel`, `session-resume`, and
  `dashboard --role dashboard|observer`, so observer/dashboard surfaces
  render the read-only review-channel status command instead of mutating
  commit/push/pipeline commands. The dedicated probe remains follow-up scope.
- 2026-04-23 managed bridge projection drift classification and receipt
  cleanup (ADR-008 closure under MP-377): push/checkpoint state now records excluded generated
  projection dirt as `managed_projection_drift` plus
  `managed_projection_dirty_paths`, and startup-context, context-graph,
  dashboard/control-plane, and push-decision surfaces render that state
  separately from authored source dirt. `devctl push` now commits any
  bridge/ReviewSnapshot-only projection drift as a governed receipt before
  publication so green pushes end with a clean worktree.
- 2026-04-23 pipeline receipt-head movement classification (ADR-008 follow-up
  under MP-377): `pipeline --action status`, `auto-recover`,
  `recover`, and `refresh-authorization` now treat governed receipt commits
  whose parent is the authorized pipeline commit as
  `head_movement_classification=managed_receipt` instead of actionable HEAD
  drift. This keeps completed push pipelines truthful after the push-time
  bridge/ReviewSnapshot receipt commit advances HEAD.
- 2026-04-23 stage_commit_pipeline projection + role-aware stage handoff
  (MP-355 + MP-377 follow-up): `ActionKind.STAGE_COMMIT_PIPELINE` is now a
  first-class bridge action-kind, so `action_requests_from_packets()` projects
  pre-pipeline staging handoffs into `## Action Requests` instead of silently
  dropping them. `resolve_commit_stage_target()` now reads the typed
  `remote_control_attachment.role` alongside `provider`: when the attached
  provider is the reviewer-bound agent and a separate implementer is bound,
  the stage handoff routes to the implementer instead of recirculating back
  to the blocked reviewer queue. The reviewer/operator polling prompt now
  passes `--actor <provider_id>` so live `action_request` packets stamp
  `delivery_observed_at_utc` instead of staying `unseen`. Maintainer surfaces
  (`AGENTS.md`, `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`,
  `dev/scripts/devctl/review_channel/prompt_guards.py`) advertise the new
  action kind so generated instructions agree with the typed contract.
- 2026-04-24 actor-authority grant slice (MP-355 + MP-377 follow-up):
  `CollaborationSession` now emits typed `ActorAuthorityState` rows with
  explicit `CapabilityGrantState` grants for repo mutation, stage handoff,
  review/checkpoint, observation, and approval. `AuthoritySnapshot` and
  session-resume preserve those grants, and governed commit target selection
  prefers the live mutation owner's `repo.commit` grant before compatibility
  fallbacks. `approval.commit` stays separate from repo mutation, and
  startup-context now projects orphan-work evidence as a bounded summary so
  the added typed authority does not break the slim bootstrap budget.
- 2026-04-25 SYSTEM_MAP typed connectivity authority slice (MP-377 S0.5):
  `ConnectivityRegistrySnapshot` is now the shared A->B->C source for contract
  writers, fields, readers, and generated surfaces. `context-graph` consumes
  it for contract/field reader edges, `startup-context` and `session-resume`
  carry the same bounded summary, `render-surfaces` reports it beside the
  generated SYSTEM_MAP block, and `check_platform_contract_closure.py` fails
  closed when required consumers or field readers disappear.
- 2026-05-14 SYSTEM_MAP contract-registry coverage closure:
  `render-surfaces` now renders every `dev/state/contract_registry.jsonl`
  `contract_id` into the generated SYSTEM_MAP block as a compact coverage
  index, and `check_systemmap_covers_contract_registry.py` gates tooling and
  release bundles so platform contracts cannot remain invisible while registry
  closure passes.
- 2026-04-25 S4 SYSTEM_MAP freshness gate slice (rev_pkt_1824 / rev_pkt_1839):
  `context-graph --mode bootstrap` now persists its managed graph snapshot
  during normal dispatcher runs, `BootstrapContext.key_surfaces` shares the
  startup registry source, `check_system_picture_freshness.py` gates stale
  startup/graph evidence, and `devctl push` refreshes ReviewSnapshot plus
  managed projection receipts before routed preflight.
- 2026-05-03 governed-push managed-projection parser closure (MP-377):
  live dogfood found that `devctl push` could report `post_push_green` while
  `dev/audits/REVIEW_SNAPSHOT.md` stayed dirty because the shared git helper
  trimmed the leading space from an unstaged porcelain row. The receipt path
  now parses that trimmed form, splits dirty-status/path/staging helpers out
  of the receipt orchestrator, and covers the case with a regression test so
  managed `bridge.md` / ReviewSnapshot drift cannot hide behind a green push.
- 2026-04-26 Connected AI Platform Plan 4.1 Slice 0/A start (MP-377):
  commit/push reports now carry explicit diagnostics for git commit failure,
  landed-commit receipt/projection pending state, review-gated publication,
  remote publication, and post-push state. `PlatformFindingIngest` is the
  shared FindingBacklog/governance-review seam for dogfood findings,
  `devctl dogfood --record-governance` routes through it, and the dispatcher
  initially gained an opt-in fail-open finalization hook for failed
  non-read-only devctl commands while excluding read-only,
  dogfood/governance-recursive, and artifact-only commands. ADR-011 through
  ADR-013 track the remaining per-guard/post-commit/runtime-agreement
  automation before enforcement. The same Slice 0 runtime agreement work now
  treats attached remote-control liveness as launch authority: status/doctor
  recommend headless `--terminal none`, and explicit visible Terminal.app
  launch/recover requests fail closed before any local prompt or profile lookup
  the remote operator cannot see. Governed stage/commit preflight also now
  refreshes the existing startup receipt before failing on
  `attention_revision_stale`, so typed dogfood finding packets do not stale the
  commit path they are meant to protect.
- 2026-04-26 Plan 4.1 Slice 0 governed-push closeout (MP-377):
  `devctl push` now treats a contiguous chain of managed bridge/ReviewSnapshot
  and generated-surface receipt commits as authorized movement when any
  ancestor matches the `PushAuthorizationRecord` commit, skips new
  ReviewSnapshot receipts when HEAD already matches the shared managed
  receipt-prefix registry, and refreshes event-backed
  review-channel projections after receipt commits before preflight or
  publication authorization reads them. This closes the live
  `head_changed_after_authorization` / proof-tick zref cascade that left the
  branch 66 commits ahead, while still requiring a fresh governed approval when
  the authorization window itself expires. The same closeout now splits
  pre-validation managed projection sync from post-validation repair and
  auto-transitions non-destructive push failures to
  `delivered_locally_pending_publish`, so a landed local commit cannot leave
  the state machine stuck in `push_blocked`; destructive remote
  rejection/conflict evidence still requires explicit reconciliation. Queue
  the remaining Plan 4.1
  additions through existing surfaces: FindingBacklog/governance-review/
  findings-priority/AutoModeState/dashboard/startup-context for
  finding-durability without distraction, `CodexAgentPollLoop` as a Slice A
  consumer of review-channel packets and dogfood ticks, and remote-control
  launch/recover/mode switching as caller-class + `review-channel --action
  launch` typed-contract work rather than a parallel automation launcher.
- 2026-04-27 governed-push generated-surface receipt closure (MP-377):
  `devctl push` now runs `render-surfaces --write` before routed preflight,
  then commits any tracked, non-local repo-pack output drift as a managed
  generated-surface receipt before `docs-check` can fail on stale policy-owned
  surfaces. The receipt chain accepts those generated-surface commits above the
  authorized content commit, selected receipt commits use pathspecs so
  staged-only next-commit intent stays out of machine receipts, and the
  follow-up runtime refresh keeps review-state/startup/context-graph evidence
  on the new receipt HEAD before publication checks run. This closes
  `rev_pkt_1983` / ADR-018 and removes the recurring SYSTEM_MAP manual
  regeneration gap from the push cascade.
- 2026-04-27 Plan 4.1 Slice A report-only dogfood automation (MP-377):
  `PlatformFindingIngest` auto-recording is now default-on and fail-open for
  failed non-read-only devctl commands. The dispatcher appends the dogfood
  ledger row and the stable `signal_type=dogfood` governance-review /
  `FindingBacklog` row after audit emission, refreshes dogfood and governance
  summaries, and keeps the command result unchanged if report-only ingest
  fails. Read-only commands, recursive dogfood/governance paths, and
  artifact-only commands stay excluded; `DEVCTL_PLATFORM_FINDING_INGEST_AUTO_RECORD=0`
  is the compatibility opt-out and `DEVCTL_PLATFORM_FINDING_INGEST_DISABLE=1`
  remains the hard kill switch. Regression coverage now proves duplicate
  command failures collapse to one latest FindingBacklog identity while the
  dogfood ledger keeps both run rows and startup `quality_signals` reads the
  deduped backlog. The same closeout registers `FindingReview`,
  `FindingBacklog`, and `PlatformFindingIngest` in the platform blueprint and
  records ADR-019 for the remaining Slice C connectivity-enforcement
  promotion.
- 2026-04-27 Plan 4.1 Slice C/D proof-tick authority repair (MP-377):
  Codex 11 validated `rev_pkt_2001` against the repo and corrected the
  `rev_pkt_2000` framing: the live failure was declared/effective
  reviewer-mode authority drift plus first-found-wins expected-value selection,
  not a missing `remote_control` reviewer enum. The bounded implementation
  keeps `StartupContext` as turn-level proof authority for reviewer posture and
  operator channel, adds `operator_interaction_mode` to the proof tick, and
  leaves dynamic role flipping for Slice E capability migration.
- 2026-04-27 governed-push execution-truth invariant (MP-377):
  `devctl push` now fails closed at action-build/report time when the configured
  branch or templated approved target identity diverges from live git and
  publication authorization. `published_remote` requires a successful
  `git push` subprocess, populated fetch/preflight/push evidence, and remote ref
  equality with current `HEAD`; terminal post-push states separately require
  `post_push_steps`. Missing proof emits `SilentPushFailure` instead of a green
  push report. Plan 4.1 resumes after
  this repair with Slice B packet lifecycle reduction, Slice D projection-spine
  consolidation over existing typed surfaces, and Slice E role reassignment on
  the existing capability contracts.
- 2026-04-27 rev_pkt_2035 bundle intake and slice placement (MP-377):
  Plan 4.1 now owns the consolidated SYSTEM_MAP, self-dogfood, platform-spine,
  duplicate-system, guard-coverage, role-enforcement, and proof-of-navigation
  findings. The umbrella registry adds `MP377-P0-T13` through `MP377-P0-T18`;
  `agent_substrate_architecture_review.md` holds the Slice E sub-scope for
  command gates and provider-role-default retirement; and
  `AUTOMATION_DEBT_REGISTER.md` carries ADR-024 through ADR-027 for the
  warning-first guard family. This keeps the work in existing typed authority
  surfaces and leaves compatibility projections as projections.
- 2026-04-28 Plan 4.1 Layer H governed-push receipt-chain follow-up
  (MP-377): the approved-target identity finding path now consumes the same
  managed receipt-chain decision emitted by `publication_authorization_decision`.
  Preflight-created generated-surface / bridge / ReviewSnapshot receipt commits
  no longer self-invalidate an otherwise current authorization, while stale,
  fixture, unmanaged, or wrong-worktree authorization still fails closed.
- 2026-05-02 Plan r3 Slice 1 governed-commit failure routing (MP-377):
  `_commit_failure_result` now passes eligible failed `ActionResult` envelopes
  through `failure_packet_router`, which writes the same event-backed
  `action_request` plus safe-auto-apply transitions already used by the review
  channel. This starts consuming `auto_executable` / `remediation` evidence in
  the commit failure path instead of leaving the next command as prose-only
  operator guidance; non-allowlisted failures still return fail-closed.
- 2026-04-27 Plan 4.1 N1 governed-push heartbeat automation (MP-377):
  `devctl push` now extends the existing pre-validation projection sync rather
  than adding another recovery surface. When the bridge liveness projection
  says `reviewer_mode=active_dual_agent` and `Last Codex poll` is beyond the
  five-minute freshness threshold, push pre-validation runs one headless
  repo-owned `reviewer-heartbeat` with
  `reason=auto-refresh-during-publication`, records the phase result in the
  managed projection sync payload, and then continues into the existing
  ReviewSnapshot/receipt/router cascade. This closes the current
  compatibility-only push blocker and advances the typed `next=` automation
  rule; the follow-up commit-pipeline slice now projects those reason chains
  through the existing `ActionResult` envelope instead of a new result system.
- 2026-04-27 Plan 4.1 governed-commit self-resolution (MP-377):
  `rev_pkt_2055` is closed as an architectural extension on the existing commit
  pipeline. `commit_guard_bundle.py` recognizes the host-cleanup age-out
  warning, runs one bounded process-watch retry, and replays the guard bundle;
  `runtime/vcs.py` retries transient `.git/index.lock` busy failures for
  index-writing git commands; and stage/commit failure reports now include
  structured `ActionResult.errors`, `reason_chain`, `remediation`, and
  `auto_executable` fields. This unblocks the pending N1 publication without
  making Claude or Codex run a manual workaround.
- 2026-04-24 remote-control liveness split-brain closure (MP-355 + MP-377
  follow-up): `review-channel status --refresh-bridge-heartbeat-if-stale`
  now treats a live typed `remote_control_attachment` as continuity evidence
  when a stale compatibility bridge has drifted to `tools_only`. The status
  path may refresh the Codex heartbeat, mark that refresh as typed reviewer
  activity for the remote-control continuity case, and reproject `bridge.md`
  back to `active_dual_agent`; launch/rollover remain fail-closed on the
  regular live-bridge contract. Remaining red health stays visible through
  `attention`, `errors`, and final `bridge_liveness` instead of changing the
  command-level `ok` contract.
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- `dev/active/portable_code_governance.md` is the narrower engine/adoption
  companion under `MP-376`, not a second main product plan; implementation
  tasks stay in that file while product-level authority routes through
  `dev/active/ai_governance_platform.md`.
- `dev/active/ai_governance_platform.md` is the only main active product
  architecture plan for the extracted AI-governance system under `MP-377`.
  Repo-wide strategy, extraction, PyQt6, phone/mobile, and shared-backend
  questions must route from this tracker to that document before any narrower
  domain spec.
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b evidence gates pass.
- `dev/audits/architecture_hardening_plan.md` is ReviewSnapshot hardening
  audit intake, not a new active execution plan. Accepted items route into
  the existing MP-377 / MP-376 owner chain: `platform_authority_loop.md` for
  path/doc-authority and repo-pack diagnostics, `remote_commit_pipeline.md`
  for commit/push and override integrity, `ai_governance_platform.md` for
  contract/ecosystem surfaces, and `portable_code_governance.md` for adopter
  proof.
- `dev/audits/REVIEW_SNAPSHOT.md` is a generated review-snapshot projection.
  Do not hand-edit it and do not treat it as active plan authority; regenerate
  it through `devctl review-snapshot --write` when the projection must move.
- Deferred work lives in `dev/deferred/` and must be explicitly reactivated here before implementation.

## Status Snapshot (2026-04-13)
- Last tagged release: `v1.2.3` (2026-04-01)
- Current release target: `post-v1.2.3 planning`
- Active development branch: `develop`
- Current `MP-377` execution branch: `feature/governance-quality-sweep`
- Release branch: `master`
- Current main product lane: `MP-377` AI governance platform extraction. Treat
  `dev/active/ai_governance_platform.md` as the main scoped plan for the
  system that improves AI coding quality and is being pulled out of VoiceTerm.
- Active execution-owner set (2026-04-13 consolidation): tracker
  `dev/active/MASTER_PLAN.md` plus owner specs
  `dev/active/ai_governance_platform.md`,
  `dev/active/review_channel.md`,
  and `dev/active/review_probes.md`. Other `dev/active/*.md` docs, including
  `dev/active/portable_code_governance.md`, stay reference-only owner/context
  surfaces until the umbrella plan promotes them.
- Required companion lane: `MP-376` portable code-governance engine/adoption
  work. It is subordinate to `MP-377`, not a peer product strategy.
- Current `MP-377` execution authority now routes through the typed phase/task
  registry at the top of `dev/active/ai_governance_platform.md`: each phase
  declares owner doc, task ids, dependencies, and status, and startup/work-
  intake may only treat those typed phase tasks as live execution authority.
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
  scope: fail closed if the managed ReviewSnapshot refresh ever drops
  preexisting staged user paths, and make governed commit reporting explicit
  about the staged/content commit versus any trailing snapshot-only receipt
  commit so operators stop mistaking the receipt for lost staged work.
- 2026-04-28 Plan 4.1 Finding I governed commit path selection in `MP-377`
  scope: `devctl commit --paths <path>...` now feeds selected repo-relative
  paths into the existing typed `vcs.stage` action, preserving the
  ReviewSnapshot refresh and dirty-outside-scope gates without requiring raw
  `git add` as a remote-control workaround.
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
  relocate crowded `dev/scripts/devctl/` root modules into topical
  subpackages, retire extracted root shims that no longer carry authority,
  and bring the strict package-layout guard back under the 60-file root cap
  so multi-file governance slices can land without waivers.
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
  scope: treat staged-only next-commit content as allowed "on deck" state,
  not push-blocking worktree dirt, and apply the same exclusion to the
  preflight auto-commit path so publication cannot sweep staged user intent
  into a machine commit.
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
  archive `move.md`, `loop_chat_bridge.md`, `phase2.md`, and
  `RUST_AUDIT_FINDINGS.md` out of `dev/active/`, update discovery pointers,
  and reduce the active-doc count from 30 to 26 so the live set matches the
  one-umbrella-plan policy.
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:
  extract bounded scope paths, checklist state, and typed phase/task routing
  from governed plan markdown into `PlanRegistry` so plans stop being
  registration-only inputs.
- 2026-04-18 `MP-390` plan-mutation and anchor authority in `MP-377` scope:
  auto-populate stable anchor refs and apply accepted `plan_patch_review`
  `mutation_op` packets back to markdown with typed receipts instead of
  leaving plan writes as advisory-only packets.
- 2026-04-18 `MP-391` plan-target cutover and tracker demotion in
  `MP-377` scope: make `WorkIntakePacket.plan_target_path` /
  `PlanTargetRef` the primary routing source and demote `MASTER_PLAN.md`
  from live task authority to bounded tracker/reference projection.
- 2026-04-18 `MP-392` role vocabulary and ownership in `MP-377` scope:
  extend `TandemRole` with `PLANNER`, `AUDITOR`, `RESEARCHER`, and
  `COORDINATOR`, then bind packet kinds, command families, and write
  authority to typed roles.
- 2026-04-18 `MP-393` role-aware runtime routing in `MP-377` scope:
  wire the expanded role model through `startup-context`, `session-resume`,
  `commit --role`, and review-channel actor validation without regressing the
  existing reviewer/implementer/operator lanes.
- 2026-04-18 `MP-394A` current-role assistant-command registry in `MP-377`
  scope: add canonical `repo_governance.assistant_commands` rows in
  `dev/config/devctl_repo_policy.json`, keep the registry current-role-only
  before role expansion, and render the already-materialized provider assets
  (`bridge-loop`, `voice`) as projections instead of prose-only ownership.
- 2026-04-18 `MP-394B` role-aware assistant-command ownership in `MP-377`
  scope: after `MP-392`/`MP-393`, widen command ownership/guards to the
  expanded role model without creating command-only exceptions or restoring
  provider-local registries as authority.
- 2026-04-18 `MP-395` structured checklist migration in `MP-377` scope:
  convert `operator_console.md` and the remaining `remote_control_runtime.md`
  closure items into typed checklist/task state so half-done work stops
  hiding inside long prose docs.
- 2026-04-18 `MP-396` generator and module-ownership closure in `MP-377`
  scope: implement `extension_bundle.py` generators with round-trip tests and
  add orphan-module detection so unfinished scaffolds fail closed.
- 2026-04-18 `MP-397` CLI/runtime parity closure in `MP-377` scope:
  finish or truthfully deprecate `rollout-tail --follow`, require every help
  flag to be implemented/deprecated/experimental, and close the typed
  contract vs prose drift on remaining runtime surfaces.
- 2026-04-18 `MP-400..MP-404` hygiene-gate separation in `MP-377` scope:
  split checkpoint/publication/packet-debt/projection-drift/next-command
  routing into explicit typed blocker families so collaboration and repo
  hygiene stop collapsing into one generic red state.
- 2026-04-18 `MP-405` guard expansion in `MP-377` scope:
  add repo-owned coverage for packet-to-plan promotion gaps and the
  packet-only architectural decision trail surfaced by dogfood, starting
  with the `rev_pkt_1221` look-first + half-built-typed-state directive.
- 2026-04-18 `MP-406` guard/probe generator path in `MP-377` scope:
  generate recurring guard/probe scaffolds from typed findings metadata so
  new architectural checks stop depending on chat memory.
- 2026-04-18 `MP-407..MP-409` higher-order probe/guard/coherence closure in
  `MP-377` scope: teach probes and guards to catch cross-surface plan/runtime
  drift and then restore docs/runtime/generated-surface coherence on top of
  that smarter detection lane, including the `rev_pkt_1222` stress-
  abstraction / polymorphism / architectural-decision probe classes.
- 2026-04-18 `MP-411` portability audit in `MP-377` scope:
  audit remaining repo-specific leakage in portable layers and thread
  `ProjectGovernance.path_roots` / repo-pack seams through the offenders.
- 2026-04-18 `MP-412` HarnessAuthContract in `MP-377` scope:
  define one typed harness-authorization seam so automation can trust the
  current authority snapshot instead of waiting on ad hoc operator chat.
- 2026-04-18 `MP-413` staged-intent and worker-output closure in `MP-377`
  scope: preserve worker-created files and staged user intent through the
  governed mutation path without manual `git add` cleanup.
- 2026-04-18 `MP-414` typed decision policy in `MP-377` scope:
  route unresolved A/B/C architecture choices into one repo-owned typed
  decision surface instead of letting them remain packet prose, including
  `rev_pkt_1221/1222/1223/1234` before those packets leave the live queue.
- 2026-04-18 `MP-415` / `MP-416` collaboration-role and reviewer-wake
  closure in `MP-377` scope: keep mutation/verifier/watcher ownership derived
  from typed runtime state and make packet-post reviewer wake repo-owned and
  visible in typed receipts.
- 2026-04-18 `MP-417` snapshot-drift ordering fix in `MP-377` scope:
  make stage approval, review-state refresh, and compatibility projection
  writes idempotent so the worktree does not re-dirty after approval, and
  treat `attention_revision_stale` as its own prior slice when peer packet
  traffic advances attention without changing staged slice integrity.
- 2026-04-18 `MP-418` process-lifecycle ownership in `MP-377` scope:
  emit one typed lifecycle contract for reviewer, implementer, publisher, and
  watchers so silent death becomes runtime state instead of lore.
- 2026-04-19 wake-continuity truth follow-up in `MP-377` scope:
  carry per-lane host wake capability through typed collaboration and
  authority state, and fail closed whenever `active_dual_agent` is still
  tick-based, manual, or unknown on the mutation/verification/watcher lanes.
- 2026-04-19 loop-autonomy follow-up in `MP-377` scope:
  project one typed loop-autonomy answer across single-agent, multi-agent,
  local, and remote-control modes so control-plane surfaces and reviewer wake
  logic stop treating wake scheduling as a remote-only split or a
  dual-agent-only concern.
- 2026-04-18 collaboration-role contract follow-up in `MP-377` scope:
  keep mutation/verifier/watcher posture on typed collaboration authority
  instead of letting dev dogfood status imply who should code. Dogfood stays
  the development evidence ledger layered on top of that runtime truth.
- 2026-04-09 branch reviewer-follow-up cycle on
  `feature/governance-quality-sweep`: Codex's full-range review pass
  promoted verdict from "accepted: hygiene fix landed" (`696f4772`) to
  "follow-up required before acceptance" with three findings. F1
  (`devctl commit` auto-approving in `remote_control`), F2
  (`process_sweep` protection gap when `session_pid` is missing), and
  F3 (`rollout-tail` Claude auto-discovery too broad) now close in six
  files scoped to `commands/vcs/commit.py`,
  `commands/check/process_sweep.py`,
  `commands/rollout_tail/discovery.py`, and the three paired test
  files. Full closure trace lives in the 2026-04-09
  "Remote-control commit now waits for typed approval" entry of
  `dev/history/ENGINEERING_EVOLUTION.md`.
- 2026-04-10 startup-gate repair-launch fix in `MP-355` scope:
  `startup_gate.py:_is_repair_launch` was treating `StartupReceipt` as a
  dict (`.get("action", "")`), crashing review-channel `launch`/`rollover`
  with `AttributeError`. Final fix: removed the `_is_repair_allowed` bypass
  entirely — the `reviewer_bootstrap` intent in the authority system already
  relaxes the reviewer-loop check (line 341 of `runtime_checks.py`), so no
  separate repair bypass is needed. Receipt freshness, checkpoint, and all
  non-reviewer-loop authority checks always apply. 12 regression tests pass.
- 2026-04-10 Q47/Q45/Q43 action-routing closure in `MP-377` scope:
  `startup-context` now projects typed action routing and `agent_lane`
  permissions, and `devctl commit` evaluates `CommitPermissionDecision`
  before staging or guards so blocked/suspended implementation authority
  blocks governed commit attempts.
- 2026-04-10 Q40/Q42 follow-up in `MP-377` scope:
  the next slice splits destructive runtime recovery authority from
  non-destructive control-flow hints and projects a lane edit gate so
  dashboard/observer callers stay on findings/packets when a live implementer
  owns the active implementation lane.
- 2026-04-10 Q64/Q54 intake-governance follow-up in `MP-377` scope:
  `WorkIntakePacket` now computes a bounded `session_pacing` projection from
  planning IR plus current graph adjacency so startup can emit a typed
  research-to-first-patch budget, and `governance-review` now accepts
  `signal_type=observer` plus optional `finding_type` so observer/self-audit
  findings reuse the canonical ledger instead of living only in audit prose.
- 2026-04-10 Q67 contract-connectivity follow-up in `MP-377` scope:
  `check_contract_connectivity.py` now scans `app/operator_console/` in
  addition to the governance/runtime/platform layers, duplicate detection now
  combines semantic field aliases with purpose/docstring tokens so parallel
  `SystemCatalog` contracts do not hide behind generic field names, and
  orphaned-contract findings now surface `internal_only` consumers when a
  contract is only imported inside its own package.
- 2026-04-13 dogfood + dead-type closure follow-up in `MP-377` scope:
  a live observer finding proved the new findings spine works end-to-end
  (`governance-review -> startup-context quality_signals -> findings-priority`)
  while also exposing the remaining stale target-selection gap
  (`active_target=dev/active/review_channel.md` even when
  `plan_routing=MP377-P0/MP377-P0-T01`). The same slice expanded
  `check_platform_contract_closure.py` so `PlanPhase`, `PlanTask`, and
  `FindingBacklog` now carry AST-backed consumer-route proofs, and
  `check_governance_closure.py` now fails on newly orphaned typed contracts
  surfaced by `check_contract_connectivity.py`.
- 2026-04-13 dogfood walkthrough parity follow-up in `MP-377` scope:
  startup-context, session-resume, dashboard, review-channel status, and
  context-graph now converge on the same promoted `active_target` and typed
  findings spine. `WorkIntakePacket` / coordination reducers now let live
  plan routing plus finding pressure outrank stale continuity targets,
  startup `quality_signals` now exposes `finding_backlog` beside
  `probe_report` and `governance_review`, status refresh may reproject
  `bridge.md` from typed `_compat.bridge_projection` state even while pending
  reviewer packets still exist, and context-graph plan nodes now answer
  `PlanPhase` / `PlanTask` contract queries plus direct task-id aliases such
  as `MP377-P0-T01`.
- 2026-04-13 bridge portability + preflight refresh follow-up in `MP-377`
  scope: markdown bridge guard/read paths no longer hardcode a fixed
  Codex-reviewer / Claude-implementer pair for implementer status/ack
  semantics, legacy `Claude Status` / `Claude Ack` headings remain explicit
  compatibility aliases, and governed push plus the managed pre-commit hook
  now refresh typed review-state/status truth before they reproject or stage
  the compatibility bridge.
- 2026-04-13 dogfood engine + push preflight follow-up in `MP-377` scope:
  `devctl dogfood` now persists repo-owned coverage rows for live commands,
  guards, probes, and roles under `dev/reports/dogfood/`, writes refreshed
  `summary.{md,json}` projections for later sessions, and
  `governance-review` now accepts `signal_type=dogfood` so system-test
  failures can close out in the canonical findings ledger. The same slice
  hardened publication truth by making governed push preflight reproject the
  active `bridge.md` compatibility surface from typed review status before
  the blocking checks run, closing the stale role-marker push blocker.
- 2026-04-13 findings writer + dogfood closeout follow-up in `MP-377` scope:
  `governance-review --record` now routes through the canonical
  `FindingBacklog` writer, `devctl dogfood --record --record-governance` can
  auto-record linked `signal_type=dogfood` rows with stable ids plus
  refreshed summary artifacts using live target-path defaults and optional
  overrides, and the governance/dogfood ledger helpers now resolve against
  the runtime repo root so portable adopters do not silently write back into
  the packaged VoiceTerm root.
- 2026-04-13 typed architecture-review ingest in `MP-377` scope: Claude
  review packets `rev_pkt_0375` through `rev_pkt_0378` are now mirrored by
  canonical `governance-review` findings for the remaining architecture gaps
  (`dogfood_finding_id_instability`, `dogfood_read_only_registration_missing`,
  `plan_markdown_projection_missing`, `plan_authority_gap`,
  `bridge_authority_conflict`, `bridge_metadata_parsed_as_authority`,
  `authority_snapshot_3_fields_missing`, `agents_md_dual_purpose_conflict`).
  The next closure order stays repo-visible: authority snapshot reduction
  first, bridge-authority demotion second, persisted `PlanRegistry` +
  markdown projection third, then multi-agent dogfood/scenario widening.
- 2026-04-14 remote-control wake + dashboard parity follow-up in `MP-377`
  scope: `pending_action_requests` now counts only live pending
  `kind="action_request"` packets, dashboard terminal/markdown projections keep
  repo-owned conductor rows in `RUNNING` when typed session state says
  `alive=true` even if a PID is unavailable, and `ensure --follow` can
  relaunch one waiting Codex reviewer conductor for the newest unseen
  action-request packet instead of leaving that wake-up dependent on a
  separate watcher.
- 2026-04-15 reviewer-runtime attention convergence follow-up in `MP-377`
  scope: bridge-backed `review-channel status` and the event-backed
  `startup-context` / `session-resume` / `dashboard` lane now attach the same
  typed conductor session state before recovery assessment, so all four
  surfaces agree on runtime diagnosis (`review_loop_relaunch_required` on the
  live repo state) while checkpoint sequencing remains in
  `advisory_action` / `push_decision`. The authoritative bundle for the
  current 74-path slice is still `bundle.tooling -> docs-check
  --strict-tooling`, so the matching maintainer-doc updates stay part of the
  closure criteria for this runtime-convergence slice.
- 2026-04-15 review-surface snapshot-parity follow-up in `MP-377` scope:
  event-backed `projections/latest/review_state.json` now backfills
  `_compat.bridge_projection` from typed bridge/current-session/runtime state
  when the persisted compat payload is missing, so
  `check_review_surface_consistency.py` no longer reports
  `review_state_bridge_projection: missing` after a bridge-backed status tick.
  That keeps bridge-backed status, event-backed review-state, compact,
  startup-context, and turn-authority on one shared `snapshot_id` family
  during governed push preflight instead of relying on a previous
  bridge-backed refresh to materialize the compat bridge payload.
- 2026-04-17 current-session authority hardening follow-up in `MP-377` /
  `MP-355` scope: event-backed `current_session` now requires explicit packet
  truth before blank queue state can clear a prior typed instruction, ignores
  queue instructions whose `derived_next_instruction_source.to_agent` is not
  `claude`, and refuses to let bridge-backed authority override persisted
  typed state when the live bridge contributes no authority signal. The same
  slice makes missing/empty typed `implementation_permission` a hard
  `ImplementationAdmissibility` block and marks
  `relaunch_review_loop` auto-fixable so reviewer-follow auto-relaunch only
  fires when the typed recovery decision explicitly allows it. Focused proof
  is green on `test_current_session_projection.py`,
  `test_implementation_admissibility.py`, and
  `test_reviewer_follow_restore_policy.py`.
- 2026-04-17 checkpoint-first detached-runtime follow-up in `MP-377` scope:
  detached `active_dual_agent` runtime no longer outranks stronger checkpoint
  authority when the review proof is already current. When
  `reviewed_hash_current=true`, `review_needed=false`, and typed
  `push_enforcement` already says the tree is over budget, shared attention
  now emits `checkpoint_required`, status/doctor/startup all converge on
  `cut_checkpoint` plus
  `python3 dev/scripts/devctl.py commit -m "<descriptive message>"`, and the
  reduced `authority_snapshot` / startup action router allow `vcs.stage` and
  `vcs.commit` while still blocking `implementation.edit`. Focused proof is
  green on `test_recovery_assessment.py`, `test_action_routing.py`,
  `test_startup_context.py`, and the checkpoint-routing status regressions in
  `test_review_channel.py`.
- 2026-04-17 remote-control commit approval automation follow-up in
  `MP-377` scope: the repo now exposes
  `python3 dev/scripts/devctl.py commit --approve-pending` as the explicit
  operator-owned resume path for remote-control checkpoints. The helper
  reuses the current governed pipeline, posts/applies the matching typed
  `commit_approval` decision, and continues the same `vcs.commit` without
  manual packet field reconstruction. The approval helper and commit-phase
  packet loader now read reduced packet rows directly instead of forcing a
  full event-bundle enrichment pass just to match approval packets. Focused
  proof is green, and the remaining latency hotspot sits in the first-stage
  remote-control `devctl commit -m ...` preflight/context-graph path.
- 2026-04-18 remote-control delegated approval follow-up in `MP-377` scope:
  governed commit no longer treats `remote_control` as one blanket approval
  rule. The preflight lane now resolves a typed approval-authority decision
  from `interaction_mode` plus active `remote_control_attachment` evidence, so
  `remote_control` only auto-satisfies approval when runtime proves an active
  operator-role delegate for the current lane. Plain `remote_control` still
  fails closed at `operator_approval_pending`, and
  `python3 dev/scripts/devctl.py commit --approve-pending` remains the
  explicit resume path when that typed delegation is absent. Focused proof is
  green on the delegate-backed auto-approval, no-delegate fail-closed,
  explicit resume, explicit approval sync, pending-phase reporting, and
  interaction-mode resolution regressions.
- 2026-04-17 operator-inbox Phase-1 follow-up in `MP-377` / `MP-355` scope:
  the first operator-facing packet read surface now rides the existing
  review-channel transport instead of inventing a second lane.
  `review-channel --action operator-inbox` fixes `target=operator`,
  defaults to `status=pending`, and deliberately does not stamp
  `delivery_observed_*` on live `action_request` packets, so operator reads
  stay packet-native but read-only. Focused proof is green on the new
  operator-inbox regression plus `check_code_shape.py`; the next expansion is
  dogfood/ledger integration and only then a decision on whether a later
  top-level `devctl operator-inbox` wrapper is worth the extra surface area.
- 2026-04-17 commit/push next-command convergence follow-up in `MP-377`
  scope: the repo now uses typed `next_command` as the active publish
  pipeline authority instead of leaving commit/push surfaces to reconstruct
  prose. `pipeline --action status` already projects
  `next_command=python3 dev/scripts/devctl.py push --execute` for the live
  same-HEAD expired `push_blocked` pipeline, `commit_pipeline_blocking.py`
  now auto-refreshes that authorization window before it emits the block
  report, and commit-preflight blocks for no pending pipeline, stale
  pipeline, or missing operator approval now project exact next commands
  instead of free-form guidance. The same slice promotes
  `CommitPermissionDecision` recovery fields to top-level commit reports and
  fixes the `--amend` support text drift. Proof is green on the narrowed
  commit-gate regressions, the full `test_push.py` /
  `test_pipeline_command.py` bundle, and `check_code_shape.py`.
- 2026-04-17 push-status truth-split follow-up in `MP-377` / `MP-355`
  scope: `push_enforcement` now projects raw latest push-artifact truth and
  separately selected current-target truth instead of conflating them under
  `latest_push_report_*`. The reducer emits
  `selected_push_report_*` plus `selected_push_report_source` for startup and
  governed push decisions, while `latest_push_report_*` stays truthful to the
  on-disk `dev/reports/push/latest.json` artifact. The same slice also closes
  the stale bridge compat seam: bridge-backed `review_state.json`
  `_compat` payloads now include `push_enforcement`, and review projection
  cache freshness paths now invalidate on latest-push artifact changes so
  read-only/mobile consumers do not lag after push-state updates. Proof is
  green on the narrowed push-state/startup regressions, the new compat/cache
  tests, and `check_code_shape.py`.
- 2026-04-17 checkpoint-recovery projection follow-up in `MP-377` /
  `MP-355` scope: direct pipeline recovery actions now refresh the shared
  review-channel projections immediately after they write canonical pipeline
  state, so a live `pipeline --action abandon|recover|refresh-authorization`
  result cannot be overwritten by a stale `latest/commit_pipeline.json`
  mirror on the very next status or commit read. The 2026-05-02 `/develop`
  checkpoint dogfood extended that conservation rule to
  `mark-delivered-local`: a matching `PipelineRecoveryReceipt` is now
  load-bearing read-side evidence for `pipeline --action status`, remote
  pipeline contract loading, and governed commit gates, and the action
  re-materializes the receipt-backed state after projection refresh so stale
  event projections cannot revive the active pipeline blocker. The same checkpoint-repair
  slice also types the expanded pending-reviewer commit gate against
  `ReviewState`, keeping `check_python_typed_seams.py` green after the helper
  extraction. Focused proof is green on
  `test_pipeline_command.py`, `test_commit_pending_reviewer_gate.py`,
  `check_python_typed_seams.py`, and `check_code_shape.py`; the next live
  step is the governed checkpoint retry, then the same-class
  `guards_failed` next-command gap Claude reported in `rev_pkt_0949`.
- 2026-04-15 governed publication follow-up in `MP-377` scope:
  `devctl commit` now stops at `operator_approval_pending` before the commit
  phase when `remote_control` or another non-auto-approved lane still has an
  outstanding `commit_approval` request, and the ReviewSnapshot publication
  path now treats a governed receipt commit as `REVIEW_SNAPSHOT.md` plus the
  optional governed `bridge.md` projection bound to the parent code commit.
  That keeps `check_review_snapshot_freshness.py`, persisted push
  authorization, and live `devctl push --execute` preflight on one receipt
  model instead of self-staling as soon as the post-commit receipt advances
  `HEAD`. The same governed-publication lane now also normalizes bridge
  compatibility poll metadata on repair: repo-owned `review-channel`
  status/render rebuilds recover blank `Last Codex poll` fields from typed
  bridge state and canonicalize fractional-second typed timestamps back to the
  whole-second UTC/local bridge format so `check_review_channel_bridge.py`
  cannot keep blocking governed push on compatibility-only timestamp drift.
- 2026-04-15 dogfood campaign contract follow-up in `MP-377` / `MP-376`
  scope: the repo-owned system-test path now records the metadata needed for
  real multi-surface proof instead of depending on chat memory. `devctl
  dogfood --record` now persists campaign/scenario/repo/topology/lane linkage
  and mirrors that linkage into auto-recorded dogfood governance notes, while
  `governance-import-findings` can ingest `LIVE_RUN.md` as compatibility
  evidence with repo-scoped `repo_name:Q-ID` sync ids. The active owner docs
  now lock the execution order explicitly: VoiceTerm full live loop first
  (`Codex reviewer/conductor + Claude remote implementer + permanent Claude
  watcher`), external repo matrix second in waves of `3`, and no mutating
  fanout widening while startup receipts still report
  `safe_to_fanout=False` / `resync_required=True`.
- 2026-04-15 startup-authority bounded-import follow-up in `MP-377` scope:
  the live `startup-context` stall was traced to the startup-authority
  import-index atomicity scan, not the startup reducer. The guard was walking
  the entire committed Python tree from `HEAD` and reading importer files
  one-by-one on every bootstrap. It is now bounded to the local package scope
  touched by current Python worktree paths, which preserves split/atomicity
  protection for the active slice while restoring fast startup receipts on the
  live repo.
- 2026-04-15 startup-repair authority parity follow-up in `MP-377` scope:
  `startup-context --repair` now consumes the same blocker-driven advisory
  coherence as normal startup receipts and treats
  `AuthoritySnapshot.safe_to_continue=false` from coordination resync as a
  real manual-follow-up issue. That closes the live contradiction where
  `startup-context --format summary` blocked on
  `coordination_resync_required` while `startup-context --repair` still
  claimed the startup state was healthy.
- 2026-04-15 review-channel launch/remote-control bootstrap follow-up in
  `MP-355` / `MP-377` scope: `build_launch_sessions()` now freezes one shared
  prepared launch authority per visible launch batch so sibling Codex/Claude
  conductors cannot diverge on `prepared_session_token` while
  `review_state.bridge.last_codex_poll_utc` advances mid-launch, and the
  implementer `session-resume --format bootstrap` surface now treats
  `Pending Inbox` / typed packet `required_command` as the next bounded action
  for remote-control Claude sessions instead of leaving "continue the probe?"
  to operator chat. Focused launch/session-resume regressions plus
  `check_code_shape.py`, `check_active_plan_sync.py`, and
  `check_multi_agent_sync.py` are green on the live tree.
- 2026-04-13 authority-snapshot closure follow-up in `MP-377` scope:
  startup-context, session-resume, and review-channel status/doctor now all
  project the same reduced `AuthoritySnapshot` contract from
  `runtime/authority_snapshot.py`, so callers get one typed
  `coordination_state` / `root_cause` / `required_action` / `next_command` /
  `safe_to_continue` packet instead of reconciling coordination, doctor,
  current-session ACK, and packet-target fields by hand. Active dual-agent
  instruction-revision drift with a stale implementer ACK now reduces to the
  first-class `handshake_stale` state instead of collapsing into the generic
  blocked label.
- 2026-04-11 bootstrap/client-boundary + mutation-admissibility follow-up in
  `MP-377` scope: generated instruction/setup surfaces now say explicitly that
  VoiceTerm is a first-party client/product integration over the portable
  governance platform, while repo packs and typed runtime contracts remain the
  backend authority for arbitrary repos. The same closure also tightened
  startup mutability truth: `startup-context` now resolves
  `implementation_permission` from observed control topology, action routing
  keeps `allowed_actions` as the effective post-gate set, and
  `implementation_admissibility` is the shared reducer used by startup/monitor
  consumers when checkpoint budget, resync, or blocked implementation
  authority temporarily stop mutation.
- 2026-04-11 local-takeover authority follow-up in `MP-377` scope: the repo
  policy for the current session is back on `local_terminal`, and the startup
  / coordination reducers no longer treat sanctioned `single_agent` local
  takeover as `remote_control` or as blocked implementation authority merely
  because no live dual-agent pair is running.
- 2026-04-11 governed-push visibility follow-up in `MP-377` scope:
  `devctl push --execute` now writes phase-aware latest-push snapshots from
  push start (`push_preflight_running`) through validated execution
  (`push_pending`) and remote publication, while startup treats a current-head
  in-flight push receipt as "wait for the running governed push" instead of
  telling the operator to launch a second push from stale artifact state.
- 2026-04-20 governed-push no-op rerun heal follow-up in `MP-377` scope
  (superseded by the 2026-04-21 tightening below): the first follow-up treated
  `reason=branch_already_pushed` plus `published_remote=true` as
  `push_completed` so already-published heads could heal pre-fix
  `push_blocked` pipeline artifacts.
- 2026-04-21 governed-push no-op rerun tightening in `MP-377` scope:
  `branch_already_pushed` receipts no longer reconstruct stale
  `push_blocked` commit-pipeline artifacts into `push_completed`. Pipeline
  completion now requires `published_remote=true` and `post_push_green=true`,
  while startup/status recover already-published truth from the current
  persisted push artifact.
- 2026-04-11 remote-participant visibility follow-up in `MP-380..MP-387`
  scope: active `attach-remote-control` artifacts now feed the typed
  collaboration roster/role-assignment path, so dashboard/status/coordination
  surfaces can treat a live external Claude remote-control session as a live
  implementer instead of dead prepared-session metadata. The bounded closure
  is still provider-scoped attachment truth, not yet the final same-provider
  multi-worker registry/fanout model.
- 2026-04-11 remote-control parity follow-up in `MP-380..MP-387` scope:
  repo-owned reviewer checkpoint/status writes no longer fail on the
  remote-role roster helper seam, and top-level `review-channel status`
  runtime counts now use the typed collaboration participant roster instead of
  stale bridge-only conductor booleans when that typed state exists. The
  attached Claude remote-control session now shows up consistently as one live
  implementer / one active conductor across `status`, `doctor`, and
  `startup-context`; removing static planned-lane capacity scaffolding remains
  a later follow-up.
- 2026-04-11 remote dashboard observer follow-up in `MP-380..MP-387` scope:
  `agent-mind` now surfaces `apply_patch` target files from rollout traces,
  and the tracked remote Claude dashboard prompt requires cursor-based
  `agent-mind` polling plus target-file diff/mtime verification before it can
  declare a no-edit stall or kill/relaunch Codex. New dashboard discoveries
  must be posted as typed findings first, with bridge/LIVE_RUN prose treated
  as secondary compatibility projections.
- 2026-04-11 single-agent reviewer visibility follow-up in `MP-380..MP-387`
  scope: recent typed `review-channel` activity from `codex`
  (`packet_posted/acked/applied/dismissed`) now promotes local reviewer
  presence in the collaboration-session/runtime-count path until that evidence
  is actually overdue, so `review-channel status` can show the active local
  Codex reviewer as live without requiring a repo-owned conductor artifact or
  process/home-dir watcher fallback.
- 2026-04-11 dashboard/control-plane parity follow-up in `MP-380..MP-387`
  scope: dashboard health now prefers typed daemon/conductor authority over
  stale heartbeat/session artifacts, and the shared control-plane liveness
  reducer also treats fresh single-agent local reviewer packet activity as
  positive repo-owned reviewer evidence before falling back to raw
  `*-conductor.json` metadata. `review-channel status`, `doctor`, and
  `dashboard --view health` now converge again on the same daemon/conductor
  truth during the remote-dashboard beta loop.
- 2026-04-11 remote-dashboard beta follow-up in `MP-380..MP-387` scope:
  single-agent local reviewer liveness now also falls back to fresh local
  rollout JSONL mtime when typed packet activity goes quiet, so long-running
  Codex edit/test turns stay visible through `status`, `doctor`, runtime
  counts, and dashboard health instead of dropping out after the old
  packet-only freshness window.
- 2026-04-11 remote-control attachment parity follow-up in `MP-380..MP-387`
  scope: bridge-backed `review-channel status` now merges active typed
  `remote_control_attachment` providers into single-agent conductor truth, and
  `ControlPlaneReadModel` treats an attached remote-control provider as live
  single-agent implementer authority before falling back to stale
  `*-conductor.json` metadata. That keeps Claude visible across status,
  doctor, and dashboard health even when its last typed packet is older than
  the session-probe freshness window.
- 2026-04-12 worker-lane portability follow-up in `MP-380..MP-387` scope:
  launch/session metadata now carry one resolved workspace root per launched
  provider session, the generated conductor scripts `cd` into that worker
  worktree instead of silently mutating the shared control lane, prompts and
  collaboration/session metadata now project lane/worktree identity forward
  into coordination/dashboard surfaces, and the single-agent attention
  classifier no longer downgrades a live typed `single_agent_active` lane to
  fake `inactive`. The same status receipt now reports the real blocker
  (`checkpoint_required` in the current dirty-tree proof) instead of telling
  the operator to relaunch a healthy single-agent dashboard lane.
- 2026-04-12 role-portability + governed-push identity follow-up in
  `MP-380..MP-387` / `MP-377` scope: review/runtime read models now prefer
  provider-neutral reviewer/implementer aliases
  (`reviewer_poll_state`, `last_reviewer_poll_*`, `implementer_ack*`) while
  keeping `codex_*` / `claude_*` bridge fields as compatibility projection
  only. The governed commit/push path now also records `worktree_identity` in
  the remote commit pipeline, blocks commit/push approval drift onto a
  different checkout, and projects current/approved worktree identity through
  latest-push status so the primary control lane cannot accidentally reuse a
  worker-lane publication approval.
- 2026-04-12 remote-control topology correction follow-up in
  `MP-377` / `MP-380..MP-387` scope: the six-hour dogfood session confirmed
  the governed default is still `worktree_strategy=shared_primary_worktree`
  when requested worker fanout is zero. Concurrent Claude dashboard/operator
  plus Codex coding/review activity should share the primary checkout and the
  same governed commit/push path until an explicit delegated worker is
  launched. Isolated worker worktrees remain opt-in fanout with their own
  typed `worktree_identity`; the linked-worktree/shadow-gitdir detour was a
  workaround caused by checkpoint/authority confusion, not part of the
  intended architecture. The next closure is to teach this shared-primary
  default through bootstrap, dashboard, and runtime read models so agents do
  not improvise extra checkouts.
- 2026-04-12 checkpoint-commit + event-backed review-state follow-up in
  `MP-377` / `MP-380..MP-387` scope: `review_state_locator` now prefers the
  sibling `projections/latest/review_state.json` bundle when governance still
  points at the legacy `.../latest` compatibility root, and live-refresh
  callers keep that event-backed path authoritative instead of silently
  falling back to stale bridge-era projections. The governed commit boundary
  also now distinguishes checkpoint authority from new implementation
  authority: when startup explicitly routes the lane to
  `advisory_action=checkpoint_allowed` / `push_decision=await_checkpoint`
  with `reviewer_gate.checkpoint_permitted=true`, `devctl commit` may still
  advance the governed checkpoint path while raw `git commit` stays blocked.
  The next closure stays on shared status/doctor wording plus Q55 findings
  convergence, not another commit-on-behalf exception.
- 2026-04-21 `rev_pkt_1503` follow-up in the same `MP-377` /
  `MP-380..MP-387` scope: the shared loader now branches event-backed
  projections before bridge-contract-drift repair, preserving
  `projections/latest/review_state.json` as typed authority even when the
  bridge compatibility contract drifts. Bridge-backed cached projections still
  refresh through the repair path; event-backed consumers do not downgrade.
- 2026-04-12 Q55/Q84 findings-convergence planning follow-up in
  `MP-377` / `MP-380..MP-387` scope: dogfood across `dashboard`, `monitor`,
  `review-channel`, and `findings-priority` confirmed that live findings
  still split across packet queues, bridge/session markdown, `LIVE_RUN.md`,
  and an empty governance-review ledger. The next closure is one canonical
  typed findings-backlog reader/writer: `review-channel --action post --kind
  finding` and historical `LIVE_RUN.md` import feed the same ledger with
  stable `finding_id` plus human `Q-ID` projection, dashboard/startup/
  monitor/bridge/findings-priority render from that snapshot,
  `governance-review` stays the disposition sink, and `LIVE_RUN.md` becomes a
  compatibility projection instead of the source of truth.
- 2026-04-11 action-request delivery follow-up in `MP-380..MP-387` scope:
  event-backed `action_request` packets now carry typed delivery receipts too:
  post seeds `delivery_emitted_at_utc`, actor-matched `inbox|watch` polls stamp
  `delivery_observed_at_utc` / `delivery_observed_by`, and `ack|apply` stamp
  `execution_started_at_utc` / `execution_started_by`. The same receipt fields
  now project through typed packet rows into `review-channel status`, inbox,
  and dashboard pending-packet surfaces so remote-dashboard beta tests can
  prove packet delivery/start instead of inferring from queue depth alone.
- 2026-04-11 action-request priority follow-up in `MP-380..MP-387` scope:
  the event-backed queue no longer lets later commentary hide a still-live
  `action_request`. `queue.derived_next_instruction` now prefers live action
  requests first, and `derived_next_instruction_source` carries
  `selection_policy`, `control_state`, and `wake_required` /
  `delivery_required` hints from the typed packet receipt state. Queue
  derivation is recomputed after receipt hydration too, so a fresh inbox poll
  can immediately advance the same packet from `delivery_pending` to
  `execution_pending` in repo-owned status truth. The same selection now feeds
  `current_session.current_instruction`, keeping dashboard/status clients on
  the action-request-first control path during remote beta polls.
- Current highest-priority subordinate `MP-377` lane:
  `dev/active/platform_authority_loop.md`. This is the execution spec for
  closing the portable authority loop:
- The bundle.tooling hygiene step in check-router now ignores the long-standing publications drift warning alongside mutation_badge so unrelated slices are not blocked by external-site drift on terminal-as-interface.
  `ProjectGovernance -> RepoPack -> PlanRegistry -> PlanTargetRef ->
  WorkIntakePacket -> TypedAction -> ActionResult / RunRecord / Finding ->
  ContextPack`.
- Current 2026-04-10 loop-v2 convergence intake inside that same `MP-377`
  owner chain: `dev/active/autonomous_governance_loop_v2.md` now owns the
  bounded design for composing existing typed startup/planning/runtime/evidence
  surfaces into one autonomous controller. Priority order is visibility and
  discoverability closure first, slice selection second, phase/controller
  routing third, then guard-promotion default writeback and governed mutation
  proof. Dashboard work remains a separate consumer session.
- Current 2026-04-12 architecture-synthesis priority inside that same
  `MP-377` owner chain: Phase 0 visibility closure must finish before Phase 1
  autonomy. The concrete owner order is now explicit:
  `platform_authority_loop.md` closes the single governed snapshot / blocker /
  decision-basis spine (`Q96-Q99`), `remote_control_runtime.md` closes
  four-surface status convergence plus one `FindingBacklog`, packet
  lifecycle/event wake, and live tool-call visibility (`Q83-Q85`, `Q90`),
  `continuous_swarm.md` owns the standing dogfood rerun plus inbox-first
  wait/role proof, and `autonomous_governance_loop_v2.md` may only widen into
  `devctl develop` after those consumers are live and `findings-priority`
  stops returning ungrounded Phase-0 rows.
- Current 2026-04-08 typed-authority convergence absorption rule inside that
  same `MP-377` owner chain: do not promote a separate "Typed Authority
  Convergence" tracker. Treat that synthesis as an execution-order map only
  and absorb it into the existing plans: `remote_commit_pipeline.md` owns
  Phase 0 governed mutation / push cutover plus hook and approval semantics;
  `platform_authority_loop.md` owns review-state producer cutover, canonical
  artifact-path and identity minting rules, and the plan/doc authority spine;
  `remote_control_runtime.md` owns queue/read-side/bootstrap/prompt
  convergence plus remote-control proof; and
  `portable_code_governance.md` owns the second-repo/custom-layout proof
  pressure. `MASTER_PLAN.md` plus those owner docs remain the only execution
  trackers; audit/evidence docs stay intake-only unless promoted.
- Current 2026-04-09 convergence-guard layering rule inside that same lane:
  the live defect is duplicated and partially-connected typed architecture,
  not missing typed models. Keep `check_package_layout.py` plus
  compatibility-shim governance as the coarse self-hosting backstop for
  crowded roots, but do not treat layout pressure as the primary architecture
  proof. Blocking closure must move toward governed-mutation anti-bypass,
  authoritative `review_state` production, minted identity-tuple parity,
  read-model-first consumers, schema-first `SystemCatalog` /
  `AgentDispatchPacket` convergence, and prompt/bootstrap field-route parity.
- Current 2026-04-09 graph-backed review rule inside that same lane:
  `context-graph` / `ConceptIndex` / ZGraph-style reducers remain generated
  search and review helpers, not new authority stores. Use them first as
  graph-backed probes for duplicate producers/readers, stale bridge fallback
  edges, guard-coverage gaps, dead topology, and plan/prompt drift; only
  promote those signals into blocking guards after replay or corpus evidence
  proves the false-positive rate is low enough for merge-time enforcement.
- Current 2026-04-09 graph-backed convergence routing note inside that same
  lane: the concrete intake is now routed through the existing owner docs
  instead of floating as audit prose. `remote_commit_pipeline.md` owns the
  first codeshape-hop mutation-bypass proof and its permanent guard;
  `platform_authority_loop.md` owns minted identity-tuple parity, ZRef
  projection, and authority-lineage evidence; `remote_control_runtime.md`
  owns read-side schema diff, raw-bridge-reader regression closure,
  duplicate-authority probes, recurring-finding clustering, and cross-surface
  snapshot parity; `portable_code_governance.md` owns the non-VoiceTerm
  import fence, config-diff repo-pack defaults proof, and the second-repo
  isomorphism pressure.
- Current 2026-04-09 graph-backed convergence triage note inside that same
  lane: the accepted framing is query work over the existing
  `ContextGraphSnapshot` plus a small codeshape ingestion pass, not a new
  semantic-graph backend. Immediate/high-value intake is the small
  query/guard tranche already aligned to active gaps (mutation-bypass proof,
  identity-tuple parity, bridge-reader closure, `zref_*`, tuple validation);
  schema-diff, lineage, and schema-union work stay sequenced behind their
  substrate prerequisites; speculative graph features stay deferred until the
  smaller proofs are stable.
- Current 2026-04-09 graph-proof guardrail note inside that same lane: a
  graph-backed signal may fail closed only when it is bound to the current
  snapshot, compatible graph-schema version, and a cached or replay-stable
  reducer. Historical trend queries, corpus comparisons, and retrospective
  topology scans stay advisory until their precision is proven.
- Current 2026-04-09 post-A1 graph ordering note inside that same lane: the
  first bounded proof is now real and already found one escaped governed-
  mutation path on this repo, so the graph direction is validated. The next
  approved graph work stays narrow and authority-adjacent: freeze the minted
  identity tuple plus `zref_*`/tuple validation in
  `platform_authority_loop.md`, then close raw bridge-reader regression in
  `remote_control_runtime.md`. Defer dispatcher-policy ports, broad
  codeshape-helper unification, schema-union work, and other graph
  generalization until the current writer/producer closure gates stop failing
  closed on missing or placeholder pipeline truth.
- Current 2026-04-09 guard-registration self-hosting note inside that same
  lane: public `dev/scripts/checks/check_*.py` entrypoints are part of the
  governed authority surface, not stray utilities. Any new guard or
  compatibility shim must land with same-change registration in
  `dev/scripts/devctl/script_catalog.py` plus maintainer-facing documentation
  in `dev/scripts/README.md`, or hygiene / governed push preflight should fail
  before publication instead of letting an undiscoverable guard drift into the
  tree.
- Current 2026-04-09 producer-order cutover inside that same lane: the shared
  live review-state loader no longer defaults to bridge refresh when typed
  authority already exists. `load_current_review_state*` now prefers
  canonical event-backed state first, then an already-written typed
  projection, and only then falls back to bridge-backed status refresh. The
  remaining owner work stays where the chain already says it belongs:
  `platform_authority_loop.md` owns the canonical review-state path + minted
  identity closure, while `remote_control_runtime.md` keeps the downstream
  read-side/bootstrap parity proof.
- Current 2026-04-09 staged-index and bundle-selection closure inside that
  same lane: startup/push authority now treats the index as first-class state
  instead of collapsing everything into anonymous dirty-path counts.
  `push_enforcement`/startup receipts now carry staged-vs-unstaged counts,
  the managed git-hook install path includes a blocking `pre-push` hook that
  forces raw publication back through governed `devctl push`, and the
  snapshot/approval path refreshes `REVIEW_SNAPSHOT.md` before the staged
  tree hash is bound. The same closure also threads caller-selected
  `review_status_dir` authority through mobile/dashboard/startup/session-
  resume reads and only reuses cached `full.json` / `review_state.json`
  projections when they are at least as fresh as live `bridge.md` +
  `review_channel.md` sources.
- Current 2026-04-10 closed-loop guard-promotion intake inside that same lane:
  the PyQt/resource-lifecycle escape routes through existing owners instead of
  a new tracker. `remote_commit_pipeline.md` owns the stale
  `push_completed` pipeline reuse fix, `ai_governance_platform.md` owns the
  `FindingReview -> GuardPromotionCandidate` closeout seam, and
  `portable_code_governance.md` owns the repo-pack-resolved promotion queue
  path so later guard/probe validation and registration can work outside
  VoiceTerm.
- Current 2026-04-09 command-boundary freeze closure inside that same lane:
  the reopened MP-384/MP-387 F1 parity flake is now narrowed at the CLI edge
  instead of only in helper tests. `session-resume` cache misses now force one
  live `load_current_review_state(... prefer_cached_projection=False)` read,
  and dashboard resolves governance plus current review state once per
  snapshot before reusing that same typed payload for both `load_sources()` and
  `ControlPlaneReadModel`. The focused parity bundle is green on consecutive
  runs; the remaining read-side consumer inventory is now mobile/helper/repo-
  pack fallbacks plus the live remote-control proof, not another abstract
  coordination-model pass.
- Current 2026-04-09 checkpoint-gate recovery note inside that same lane:
  stale `active_dual_agent` runtime must fail closed instead of quietly
  widening the slice. The sanctioned local repair path is now explicit too:
  when the reviewer loop is overdue or missing, downgrade through the
  repo-owned `review-channel --action reviewer-heartbeat --reviewer-mode
  single_agent` takeover path, cut the bounded checkpoint the startup packet is
  already requiring, then resume the live reviewer loop before starting any new
  mutating fanout. That recovery does not change the owner order: the next
  write slice remains the mobile/helper/repo-pack read-side closure already
  tracked above, followed by the live remote-control proof.
- Current 2026-04-01 architecture-absorption follow-up inside that same lane:
  fold the accepted external integration review into canonical owner plans
  instead of carrying `dev/intrgrate_analysis.md` as shadow authority. The
  absorbed gaps are now explicit and phased: typed onboarding/ratification +
  inference provenance, derived session capability projection, surface-
  ownership routing for product-vs-engine-vs-integration changes, explicit
  second-repo proof gates, and review-channel provider/terminal-host
  abstraction under singular reviewer/writer authority.
- Current same-lane focus inside that `MP-377` execution spec: finish the
  current truth-source hardening / ReviewSnapshot evidence slice already in
  the worktree, checkpoint it, and relaunch reviewer-first from that bounded
  state before widening again. That checkpoint is now landed, and the next
  same-lane scheduler artifact is live too: `dev/scripts/devctl/platform/
  planning_ir.py` now builds one typed `PlanningIRSnapshot` beside
  `SystemPicture`, joining `PlanRegistry` / `PlanTargetRef`, bounded live
  governance-review findings, context-graph `scoped_by` ownership, and the
  current work-intake ownership/coordination state. The first bounded outputs
  stay operational: `next_best_slices`, `concurrent_writer_conflicts`,
  `unowned_hot_paths`, and `plan_finding_mismatches`. The immediate follow-up
  is projection work, not another raw-state pass: feed that reducer into
  startup/dashboard/bridge surfaces and validate it against one more live
  multi-agent launch before widening beyond bounded simulation coverage. That
  projection tranche has now started too: `dev/scripts/devctl/platform/
  coordination_snapshot.py` builds one typed `CoordinationSnapshot` over the
  existing startup/work-intake packet, `CollaborationSession`, delegated
  worktree receipts, ready gates, and the shared conflict helper. The first
  consumer is `system-picture`, which now exposes one bounded coordination
  section for declared-vs-observed topology, fanout posture, worktree
  isolation strategy, and resync requirement instead of leaving those facts
  scattered across status/startup/runtime packets. Live proof still shows the
  repair target clearly: planned multi-agent scaffolding with isolated worker
  worktrees, but observed `single_agent` runtime and inactive reviewer-loop
  resync, so the next slice should be real remote-control/runtime validation
  rather than another theory-only reducer. That convergence slice is now live
  too: `StartupContext`, `ReviewState`, `SessionCachePacket`, dashboard, and
  remote-control/Claude bootstrap all read the same `CoordinationSnapshot`
  packet, and single-agent remote-control fallback now comes from
  startup/work-intake coordination authority instead of stale reviewer-only
  bridge fields.
- Current 2026-04-05 self-hardening boundary correction inside that same lane:
  keep the platform self-hardening, not self-redefining. Predeclared
  invariants may auto-enforce when repo-owned authority already defines the
  canonical result, but new invariants must route through typed candidate rule
  capture, replay/corpus validation, FP/FN evaluation, approval, and only then
  promotion. The same review confirmed the runtime loop is still partial, not
  closed: typed startup/work-intake/finding/review/quality-feedback surfaces
  exist, but `PlanExpectationPacket`, generalized `RunRecord`, and candidate
  invariant promotion remain open authority-loop work.
- Current 2026-04-05 developer-surface closure correction inside that same
  lane: typed truth existing in artifacts is not enough. The visible
  developer-facing surface should render one explicit stack:
  `source_command -> typed fact packet/projection -> readable summary`.
  Repo-owned startup/review/launch/chat/dashboard/mobile output must make it
  easy to answer what command ran, what exact fields were observed, what next
  command is required, and what was inferred vs observed. Concrete next
  closure is now explicit too: move `startup-context` / `session-resume` /
  later `explain-latest` onto one shared developer-view packet, stop parsing
  compatibility markdown as structured dashboard/review data where typed state
  already exists, and add parity guards across startup/session/status/
  dashboard/mobile projections.
- Current 2026-04-08 coordination read-model closure inside that same lane:
  the live defect is now projection divergence, not missing typed state. The
  next bounded closure order is explicit: add `CoordinationSnapshot` to
  `ControlPlaneReadModel`, make `startup-context` summary/machine-summary
  surfaces load-bearing on coordination/resync truth, demote dashboard local
  topology/fanout guesses to telemetry under typed coordination authority, and
  then prove the same answer through a governed remote-control
  Codex-reviewer/Claude-coder launch. The same slice should also decide
  whether retargeting that launch from typed plan + coordination state can be
  automated repo-owned instead of remaining a manual operator rewrite.
- Current 2026-04-08 coordination loader closure inside that same lane
  (MP-384/MP-387 F1 + F4): the earlier slice added
  `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical
  resolution path and wired it into `session_resume_support` and
  `control_plane_read_model`, but `build_startup_context` still built its
  `CoordinationSnapshot` directly via `build_coordination_snapshot(startup_
  context=SimpleNamespace(work_intake=...))`. That left three proof surfaces
  running through two reducers and allowed `observed_topology`/
  `ownership_status`/`resync_reasons` to silently disagree on the same
  tree. `build_startup_context` now delegates its coordination snapshot to
  `load_coordination_snapshot` with the same governance + review-state +
  reviewer-gate already derived higher in the function, keeping the old
  direct build only as a bare-repo / legacy-fixture fallback. The same
  slice closes F4 by making `draft_policy_scan._scan_bridge_config` read
  `operator_interaction_mode` from `repo_governance.bridge_config` and
  resolve it through `resolve_operator_interaction_mode`, so
  `scan_repo_governance(policy={}).bridge_config.operator_interaction_mode`
  now fails closed to `unresolved` instead of silently inheriting the
  dataclass `local_terminal` default. Parity coverage landed in
  `dev/scripts/devctl/tests/runtime/test_coordination_loader_wiring.py`
  and `dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py`.
- Current 2026-04-10 observed control-topology slice inside that same lane
  (Q38 first closure): startup now projects live `observed_control_topology`
  and `implementation_permission` from supervised conductor counts, bridge
  liveness, and runtime counts via
  `dev/scripts/devctl/runtime/control_topology.py`. This deliberately
  treats planned review-channel topology as insufficient for implementation
  authority when the live reviewer/implementer topology has collapsed. Remaining
  Q38 work is to wire these fields into hard launch/edit gates plus mandatory
  pack/worktree lane binding.
- Current 2026-04-08 governed mutation / dashboard queue closure inside that
  same lane: the remaining drift is now specific, not abstract. `devctl commit`
  must fail closed on unresolved operator mode instead of silently
  self-approving, active-pipeline `devctl push` must reuse the policy remote
  plus exact approved target instead of defaulting to `origin`, declared
  dual-agent review must keep publication authorization required even when the
  live reviewer runtime degrades to `tools_only`, and review-channel queue
  cleanup must only clear `commit_approval` requests on applied decisions
  instead of collapsing `acked` rows or unrelated packet history. Dashboard
  now also has to load review-state through the shared fresh source path so
  instruction/findings parity matches startup/session-resume instead of
  replaying stale `state/latest.json`.
- Current 2026-04-08 layered-proof rule inside that same lane: do not call
  the authority convergence closed from docs or partial parity alone. The
  required proof set is explicit and shared across the owner docs:
  snapshot-identified remote-control live proof, post-approval publish smoke
  harness, read-only blocked-fanout review proof, fresh-AI bootstrap proof,
  and second-repo proof. Those proofs must route through the existing owner
  chain rather than into a new shadow "acceptance plan."
- Current 2026-04-05 portable typed-structure correction inside that same
  lane: keep this as governed-boundary doctrine, not a repo-wide style rule.
  For platform-owned governance/control paths that any adopter repo may use,
  prefer typed contracts and closed transition vocabularies over free strings,
  boolean bundles, fixed-shape `dict[str, Any]`, and comment-only policy.
  The next closure slice is to treat those seams as real authority debt in the
  active runtime, while repo-pack/governance policy still decides where the
  governed boundary starts for each adopter.
- Current 2026-04-05 governed semantic-doc follow-up inside that same lane:
  accept the stronger docstring/indexing idea only as checked projection over
  typed authority. The next product-owned closure is one typed
  `SemanticSymbolRecord` / `SemanticDocRecord` family for selected
  governance/runtime symbols, wired into `DocRegistry` / doc-authority,
  `context-graph` / ZGraph-style retrieval, `SystemCatalog` / `discover`,
  and bootstrap surfaces, with CI drift guards so semantic docs cannot become
  shadow policy.
- Current 2026-04-05 semantic-routing correction inside that same lane:
  accept the deeper ZGraph/code-shape thesis, but keep the integration point
  precise for this codebase. Semantics are first-class as the repo's
  search-space reducer and dispatch planner, not as a new truth owner. The
  staged order is now explicit: `session-resume` / typed startup continuity
  first, deterministic changed-path/lane/policy narrowing second,
  `SystemCatalog` + `AgentDispatchPacket` as the bounded routing seam third,
  optional ZGraph ranking fourth, and proof/parity fallback around all of it.
  Promotion past deterministic dispatch now requires measured evals on real
  repo tasks. The graph shape stays coarse-to-fine on purpose: lane/subsystem/
  contract/command/guard/projection nodes first, then descend to file/symbol
  detail only inside the bounded frontier instead of traversing the whole repo
  at full fidelity on every turn.
- Current 2026-04-05 truth-source convergence correction inside that same
  lane: the target remains one shared backend truth with projections only
  rendering it, but the active repo is still mid-migration. Track the
  remaining overlap explicitly as product-owned closure: `ControlPlaneReadModel`
  and reduced packet contracts must become the canonical read-side source,
  `ControlState` plus legacy `controller_payload` / `review_payload` inputs
  stay compatibility/fallback-only, `session-resume` must stop doing local
  side reduction that already belongs in shared state, and markdown bridge
  surfaces must remain projection-only instead of sneaking back in as data
  sources.
- Current 2026-04-04 architecture-audit follow-up inside that same lane:
  freeze the extension/adopter closure tranche before broader packaging or
  client-migration claims. The accepted deliverables are explicit: true
  no-write-safe read-only control surfaces (separate audit/telemetry writeback
  from read-only command execution — now implemented: `startup-context` always
  attempts the receipt write because the launcher validates it, but degrades
  gracefully on `OSError` when `DEVCTL_NO_ARTIFACT_WRITES=1` signals an
  intentional read-only context; `context-graph` suppresses its bootstrap
  snapshot write only when the flag is set explicitly; normal bootstrap
  dispatch persists the graph snapshot; `observe_launch_state()` uses a
  lightweight bridge-metadata path instead of full status refresh), Phase-2 repo-pack/runtime activation that
  fails closed instead of silently falling back to VoiceTerm defaults, one
  repo-pack-owned `ExtensionBundle` that renders project-scoped Codex/Claude/
  MCP surfaces from typed governance state, and one typed `AutomationSpec`
  that lets the same governed task run through local scheduler, GitHub
  workflow, Codex Automation, or Claude-facing command/agent surfaces without
  creating a second authority layer.
- Current bounded Phase-0 design follow-up inside that same lane:
  `dev/active/remote_commit_pipeline.md` freezes the typed remote-session
  commit/push pipeline
  (`stage -> guard -> operator approval packet -> commit -> governed push ->
  recover`) needed to close the Codex sandbox-commit blocker without manual
  shell steps or prose approval. The next bounded extension in that same owner
  lane is one typed `PushAuthorizationRecord` keyed to exact head/check/review
  proof plus a typed operator `override_push` receipt for publish exceptions
  so publication authority stops reusing startup/edit gates and human
  authority stays inside the governed pipeline instead of falling back to raw
  `git push`.
- Current 2026-04-04 architecture-review closure inside that same lane:
  `dev/active/remote_control_runtime.md` owns `MP-380..MP-387` for typed
  operator interaction mode, universal check/violation contracts, headless
  rollover closure, packet-backed action requests, dashboard typed-state
  convergence, repo-owned remote-control auto-poll/update cadence,
  discoverability/system-map closure through `SystemCatalog`,
  `AgentDispatchPacket`, a thin `view` adapter, and slim reviewer bootstrap /
  session-resume cache truth. The
  bridge remains compatibility-only; any new operator surface must consume
  typed runtime, packet, and check artifacts instead of regex-scraping
  bridge markdown or `format_steps_text()` output.
- Current 2026-04-05 reviewer-handoff closure inside that same lane: `MP-387`
  now also owns the missing dirty-tree review target. The active closure is
  one typed `ReviewCandidateRecord` emitted through the review-state/status
  path, preferred by `session-resume` / reviewer bootstrap over raw
  `last_reviewed_sha..head_sha`, and invalidated fail-closed when worktree
  drift or scope mismatch makes the candidate stale. The remaining parity gate
  in this lane is explicit too: implementer-complete bridge/runtime state must
  not claim a finished slice unless a matching valid review candidate exists.
- Current 2026-04-06 field-route contract-closure fix inside that same lane:
  the `MP-381` field-route proof helper
  (`dev/scripts/checks/platform_contract_closure/field_routes_surface_state.py::_source_contains_any`)
  no longer accepts docstring or package-token coincidences as proof of
  executable consumption. The helper now parses each candidate module with
  `ast.parse`, strips module/class/function docstrings, and walks the
  remaining tree for exact identifier, attribute, dotted-chain, or
  string-literal references. `check_push_eligible_dashboard_route` now
  enumerates both `push_eligible` and `push_eligible_now` as accepted token
  forms so the receipt projection is explicit rather than implicit via
  substring overlap. The dashboard route for `ControlPlaneReadModel.top_blocker`
  passes against the real `dashboard_render` package because its submodules
  use `snapshot.get("top_blocker", ...)`, which the AST walk matches as an
  executable string-literal key. Regression locked by one focused test in
  `test_check_platform_contract_closure.py` plus the new helper unit suite
  in `test_field_routes_ast_helper.py`.
- Current 2026-04-06 self-hosting cleanup inside that same lane: the next
  bounded code-shape closure for the review handoff seam is now local-helper
  extraction, not new behavior. `review_candidate.py`,
  `recovery_assessment.py`, and `review_state_models.py` shrink back under the
  soft limit by delegating command/path parsing, recovery decision/evidence
  mapping, and collaboration dataclasses to dedicated helper modules. When a
  live dual-agent reviewer session is interrupted mid-slice, the sanctioned
  recovery path is explicit too: stop detached daemons, cut back to
  `single_agent` via repo-owned reviewer heartbeat, then continue the bounded
  slice locally instead of trusting stale dual-agent bridge state.
- Current 2026-04-05 architecture-absorption follow-up inside that same lane:
  the pushed-branch review through `b819efa` narrowed the remaining separation
  to fail-closed execution gaps, not missing ideas. The active closure order is
  explicit: operator mode must stop defaulting to `local_terminal`, terminal-
  none launch must require live conductor proof instead of detached daemon
  heartbeats, `ControlPlaneReadModel` / `AutoModeState` /
  `SessionCachePacket` must join the platform contract-closure catalog, stale
  review verdict text must demote to stale-review truth when
  `reviewed_hash_current=false`, queue metrics must separate pending packets
  from actionable requests, and the cross-plan remote-commit lane must make
  raw `git commit` structurally impossible without the governed guard path.
- Current 2026-04-05 live-loop execution order inside that same lane:
  treat the reviewer-follow relaunch defect as a symptom of the broader
  remote-control closure, not as a loop-local special case. The next bounded
  worker slice is `MP-380` + `MP-382`: fail-closed operator-mode propagation
  plus terminal-none proof-of-life. Only after that should the loop widen into
  `MP-383` / `MP-381` packet-backed action-request and shared
  `ViolationRecord` convergence, then `MP-384` / `MP-385` / `MP-387`
  dashboard, auto-poll, and reviewer-bootstrap/session-resume convergence.
  Apply the 2026-04-05 Python contract-shape audit to touched files in that
  slice only: explicit type hints, typed/dataclass boundaries, closed variant
  types, minimal `NewType` use where swap risk is real, owner-side
  construction helpers, and typed lifecycle/typestate over loose booleans.
- Current 2026-04-06 bounded `MP-381` follow-up inside that same lane:
  sanctioned local takeover is now explicit too. After recording
  `review-channel --action reviewer-heartbeat --reviewer-mode single_agent`,
  the next local slice is the first thin `ViolationRecord` convergence seam,
  not the whole frontend rewrite: `dev/scripts/devctl/runtime/probe_report_violations.py`
  maps enriched probe hints into `tuple[ViolationRecord, ...]` and focused
  tests pin that contract without changing probe-report's own JSON/markdown
  output or the existing check pipeline. Keep the next widening steps bounded:
  consume that shared row contract in remaining probe/governance/startup
  surfaces before treating `MP-381` as complete.
- Current 2026-04-06 review-channel blocker inside that same lane:
  reviewer-follow auto-promotion must not infer slice resolution from
  substring hits inside reviewer prose. Promotion/readiness now needs one
  explicit primary state marker (for example the first verdict bullet or
  explicit idle findings) or typed `current_session` truth; text such as
  `--terminal none`, `unresolved`, or a later explanatory `Accepted:` line is
  not sufficient authority to overwrite a live rejected instruction.
- Current 2026-04-07 `MP-382` / `MP-387` launch-authority closure inside that
  same lane: live launch/rollover now resolves operator interaction mode once
  through governance/startup authority and threads that value through session
  preparation plus the pre-spawn dispatcher gate; the unowned
  `--allow-headless-override` surface is removed. Prepared conductor metadata
  and generated scripts carry prepared HEAD, current instruction revision, and
  a typed turn/session token; direct script replay re-reads `review_state.json`
  and exits with a non-restartable stale-authority code before provider start
  when any value drifts. Follow-up restart-policy closure: governed
  `manual_stop` / `completed` reviewer-supervisor state is now honored by the
  repo-owned `ensure` / reviewer-heartbeat auto-start path, and the launchd
  publisher wrapper treats launch-authority exit `82` as a no-restart service
  exit.
- Current 2026-04-07 `MP-381` parity-guard landing inside that same lane: the
  hard control-plane parity guard
  (`dev/scripts/checks/platform_contract_closure/field_routes_parity.py`) is
  now wired into `check_platform_contract_closure`. One deterministic
  `ControlPlaneReadModel` fixture flows through dashboard `_assemble`,
  `inputs_from_read_model`, `build_from_sources`, and the pure
  phone/mobile `_control_plane_section` helpers; the comparator fails the
  closure aggregator on any cross-surface disagreement. `PARITY_FIELDS` now
  also covers the remote-control mode signals `reviewer_mode` and
  `operator_interaction_mode` so a surface drifting to `single_agent` /
  `unresolved` while the rest stay correct can no longer pass the
  "all 5 surfaces agree" proof. The `_extract_from_auto_mode` helper no
  longer falls back to `model.next_action`, and a new regression test in
  `dev/scripts/devctl/tests/checks/platform_contract_closure/test_field_routes_parity.py`
  proves a broken `inputs_from_read_model` mapping (`push_decision_action=""`)
  surfaces as a typed `next_action` divergence instead of a silent green
  pass. The `SessionCachePacket` projection used by session-resume
  intentionally omits `reviewer_mode` because it has no direct slot for it
  (only an internal `mode` derivation); the comparator already skips
  absent fields. Owner-plan tracking stays in
  `dev/active/remote_control_runtime.md` Priority 3 (LANDED 2026-04-07);
  this entry mirrors that landing into the master tracker so the bootstrap
  packet stops advertising the `ViolationRecord` convergence seam as the
  only current `MP-381` slice. The 2026-04-06 ViolationRecord-seam entry
  above remains active because that is a separate `MP-381` deliverable
  still in progress.
- Current 2026-04-08 `MP-381` observability closure inside that same lane:
  dashboard/control-plane conductor liveness now prefers the shared
  review-channel `session_probe` owner before falling back to static
  conductor metadata, event-backed `current_session` preserves
  `implementer_session_state` / `implementer_session_hint`, and queue
  projections now count only unexpired pending packets while surfacing
  `stale_packet_count`. That keeps inbox, status, doctor, and dashboard
  aligned on the same repo-owned runtime truth before the broader
  `DecisionTrace` / `explain-latest` chain lands.
- Current 2026-04-08 `MP-381` startup-coordination closure inside that same
  lane: `WorkIntakePacket` now reduces live collaboration into one bounded
  coordination packet (`collaboration_topology`, `authority_mode`,
  `work_ownership_mode`, `sync_cadence_mode`) instead of making fresh
  sessions infer those answers from overloaded reviewer-mode strings and
  dirty-tree prose. The same reducer also fails closed when live delegated
  workers share one worktree, so multi-agent startup can block on typed
  worktree-collision evidence before overlapping edits land.
- Current 2026-04-08 coordination read-model closure inside that same lane:
  the remaining gap is projection divergence, not missing typed state.
  `CoordinationSnapshot` already reaches startup markdown/json,
  session-resume, review-state projections, and the dashboard coordination
  section, but the load-bearing operator/bootstrap surfaces still split
  truth: `startup-context --format summary` and machine-summary omit
  coordination, `ControlPlaneReadModel` still carries no coordination field,
  dashboard still mixes typed coordination with local loop heuristics, and
  scoped launch targeting still falls back to stale checklist order. The next
  bounded slice is therefore to carry `coordination` on
  `ControlPlaneReadModel`, project the same packet through startup
  summary/machine-summary/dashboard/session-resume, treat local heuristics as
  telemetry only, and let repo-owned launch/promotion consume the
  coordination-owned slice so remote-control sessions stop rebooting into the
  stale MP-381 instruction.
- Current 2026-04-07 `MP-383` bridge Action Requests closure inside that same
  lane: the markdown `## Action Requests` section is projection-only over
  event-backed `PacketPostRequest(kind="action_request")` rows, not a second
  queue. `render-bridge` now reconstructs missing fixed sections from typed
  review-state fallbacks, compacts packet bodies before rendering, and only
  projects executable runtime action requests that carry target binding. New
  `commit` / `push` action requests require remote-commit pipeline binding
  (`runtime` target, generation, staged snapshot hash, guard summary), while
  `run_check` / `kill_process` requests require runtime target ref/revision.
- Current 2026-04-07 ReviewSnapshot receipt-hook closure inside that same
  lane: the external-review snapshot publication path is now explicitly
  two-phase. Fresh evidence now includes probe-run output plus push-receipt
  records, and typed `current_session` / `reviewer_runtime` authority stays
  ahead of stale bridge prose when those sources disagree. `review-snapshot
  --write --receipt-commit` refuses non-snapshot dirty state and creates a
  governed receipt commit bound to the current code HEAD; that receipt may
  carry `dev/audits/REVIEW_SNAPSHOT.md` alone or atomically with `bridge.md`,
  and freshness/push authorization both bind it back to the parent code commit
  or another ancestor in a contiguous managed receipt chain instead of treating
  the receipt as a fresh approval target, while
  `install-git-hooks` installs the read-only pre-commit permission hook, the
  post-commit receipt hook that invokes that typed path with hook recursion
  disabled, and a blocking pre-push hook that forces raw publication back
  through `devctl push --execute`. Next follow-ups are fresh open-finding
  recomputation from the renewed snapshot inputs and a distinct
  external-agent authority-drift detector.
- Current 2026-04-12 provider-neutral bootstrap/read-model follow-up inside
  that same lane: reviewer/implementer ownership is tracked as role-first
  launch state instead of fixed Codex/Claude identity, and typed review/status
  reads now prefer provider-neutral reviewer/implementer aliases while legacy
  `codex_*` / `claude_*` bridge fields remain compatibility projections only.
  Planned lane parsing, conductor launch specs, prompts, status/doctor
  surfaces, bridge start rules, and narrow recover flows must resolve the
  active reviewer/implementer provider from typed lane role data and
  repo-owned collaboration/runtime state, while the canonical bootstrap
  commands remain `startup-context --role <role>` and
  `session-resume --role <role> --format bootstrap`.
- Current clean-tree operational blocker inside that same lane: the repo is not
  blocked on plan/doc drift, it is blocked on live reviewer cadence.
  `startup-context` currently fails closed on `reviewer_overdue`, and detached
  publisher / reviewer-supervisor heartbeats are not sufficient proof the loop
  is healthy. The missing operational link remains a repo-owned persistent
  Codex reviewer worker/service path that keeps semantic review, checkpoint
  emission, and operator-visible updates moving between Claude passes.
- Current proof-gate framing for `MP-377`: self-hosting honesty is necessary
  but not sufficient; `Gate 2` remains the real POC bar and requires a
  second-repo governed bootstrap/startup/check path with no core-engine
  patches between adoptions before broader packaging or productizing claims
  count.
- Current owner chain for the blocking separation tranche:

| Concern | Owner doc | Why |
|---|---|---|
| Repo-wide product boundary, docs split, and priority order | `dev/active/ai_governance_platform.md` | main `MP-377` architecture authority |
| Startup authority, `DocPolicy` / `DocRegistry`, fail-closed defaults, and push packet truth | `dev/active/platform_authority_loop.md` | current subordinate `MP-377` execution spec |
| Adopter proof, optional capability gating, organization proof, and non-VoiceTerm push semantics | `dev/active/portable_code_governance.md` | narrower `MP-376` companion |
| Review-channel producer cutover and bridge compatibility retirement | `dev/active/review_channel.md` | subordinate `MP-355` producer lane |
- Execution order: freeze and extract shared governance/runtime contracts
  first, converge CLI/VoiceTerm/PyQt6/phone on the same backend second,
  rebind VoiceTerm as a first consumer third, then resume broader Theme,
  Memory, and later product lanes.
- Current blocking separation tranche: do not answer this with one giant
  directory move or more VoiceTerm user-doc churn. The target repo shape
  stays layer-based: `governance_core`, `governance_runtime`,
  `governance_adapters`, `governance_frontends`, `repo_packs`, and
  `product_integrations`, with VoiceTerm only as the first product
  integration. The immediate closure bar is fourfold:
  `DocPolicy` / `DocRegistry` plus artifact-role/scope classification keep
  VoiceTerm product docs separate from self-hosting/adopter/generated
  surfaces; portable runtime/startup/docs-check stop reviving VoiceTerm
  filenames from partial payloads; governed push reports `published`
  separately from `post-push green` with no unrestricted bypass path; and
  custom-layout plus optional-capability adopter proof stays green without
  core patches. Current measured self-hosting baseline: `doc-authority`
  reports `50` governed docs / `45,484` lines, `19` budget violations,
  `4` authority overlaps, and `8` consolidation candidates, while
  `check_package_layout` still reports four crowded roots and seven crowded
  namespace families, with repo policy now treating touched files inside
  those `devctl` self-hosting hotspots as `strict` layout debt instead of
  ordinary freeze-only edits. The same package-layout report now also emits
  canonical compatibility redirects from valid `shim-target` metadata so
  moved entrypoints advertise their new home through one portable guard
  surface.
- Current immediate `P0` execution order inside that authority-loop lane:
  first clear the blocking pre-spine hardening tranche (daemon attach/auth
  security, autonomy authority boundaries, JSONL/evidence integrity, and
  self-governance closure), then resume startup authority
  (`governance-draft` + reviewed `project.governance`), repo-pack activation
  and the full `active_path_config()` rewrite, typed plan registry, an
  evidence-identity freeze in parallel with the repo-pack/plan-registry work,
  one runtime slice through `TypedAction -> ActionResult -> RunRecord`,
  evidence/provenance/ledger closure, portable `ContextPack`, and then the
  two-repo proof with no core patches between adoptions.
- Active sequencing exception on the dirty branch: a bounded docs-authority /
  publish-truth tranche is already in flight ahead of the blocker queue.
  Checkpoint and validate that tranche explicitly, then return to the blocker
  tranche before widening into Phase 1A/5b or broader graph/startup work.
  Latest validation on 2026-03-27: the bounded tranche is green on targeted
  runtime tests and local router-driven guards, but the full dirty-branch
  router still widens to `bundle.release` because existing branch history
  includes release-sensitive workflow changes; the remaining blocker there is
  the `master` CodeRabbit release gate, not a new local code failure.
- Latest same-lane closure on 2026-03-31: typed review-channel status now
  carries `effective_reviewer_mode` beside declared bridge `reviewer_mode` so
  startup/wait consumers can demote dead `active_dual_agent` runtime to an
  inactive read-only authority state without mutating the bridge metadata or
  review-gate provenance.
- Latest same-lane closure on 2026-04-01: the next review-channel runtime
  truth follow-up landed behind that `CollaborationSession` contract. Launch
  session metadata now derives from typed provider/lane specs and records
  conductor roles, event-backed packet actors/targets validate against typed
  collaboration/runtime state or repo-owned session metadata instead of
  parser-hardcoded provider ids, and `check_multi_agent_sync.py` now blocks
  planned `AGENT-*` rows from leaking into runtime truth when typed
  `review_state` exists. The remaining honest gap is native worker-session /
  delegated-work execution, plus the last recovery/CLI surfaces that still
  assume a fixed implementer provider.
- Latest same-lane closure on 2026-04-15: governed commit fallback now prefers
  `bridge.effective_reviewer_mode` before declared collaboration
  `reviewer_mode` when `resolve_commit_execution_target()` has to synthesize
  writable conductor capabilities. That keeps local `single_agent` takeover
  authoritative for checkpoint commits even when typed collaboration topology
  still advertises `active_dual_agent` provenance.
- Latest same-lane closure on 2026-04-15: governed markdown startup now
  persists `PlanRegistry` plus per-plan `PlanTargetRef` authority under
  `dev/reports/governance/plan_registry.json`. The governed markdown scan
  reuses that artifact while the doc set is unchanged, and
  `build_target_ref()` now consumes the persisted target metadata before
  rehashing plan markdown. That closes `MP377-P1-T04` and leaves
  `MP377-P1-T05` as the next projection-layer task.
- Latest same-lane progress on 2026-04-15: the first `MP377-P1-T05`
  authority-reader pass is now live. Context-graph plan nodes, reviewer
  tracker-plan resolution, scoped promotion MP lookup, and `ReviewSnapshot`
  plan indexing prefer the persisted `PlanRegistry` / `ProjectGovernance`
  artifact and only fall back to raw `INDEX.md` parsing when typed governance
  is unavailable. Remaining `T05` scope is the docs-governance/reporting side
  that still scans markdown for registry metadata before markdown can be
  treated as bounded projection-only state.
- Latest same-lane progress on 2026-04-15: docs-governance routing now closes
  the first maintainer-doc read-side gap on that remaining `T05` scope.
  `governed_doc_routing.py` prefers typed `ProjectGovernance` doc paths
  (`docs_authority`, guide roots, scripts README, tracker/index roots) before
  surface-generation context fallbacks, and the docs-check policy defaults
  are covered by focused governance/docs regressions plus a clean
  `devctl check --profile ci` run.
- Latest same-lane progress on 2026-04-15: the next `MP377-P1-T05`
  follow-up keeps `plan_registry` bounded to execution-authority docs while
  closing two more read-side gaps. Scoped plan readers now resolve execution
  plans first and then typed `doc_registry` companion docs before any raw
  `INDEX.md` compatibility path, and packet-inbox merge no longer revives
  evicted expired findings in `open_findings`/attention when the live reducer
  has already dropped those packet ids. Focused proof is green; full
  `check --profile ci` is still blocked by baseline package-layout debt and
  the branch's over-budget dirty startup state.
- Latest same-lane progress on 2026-04-15: the commands-root baseline-debt
  publish blocker is now burned down without hiding the larger layout debt.
  `loop-packet` and its helper moved into
  `dev/scripts/devctl/commands/packets/`, the flat `commands/loop_packet*.py`
  paths now stay as metadata-bearing alias shims, and the scoped gate
  `check_package_layout.py --fail-on-baseline-debt --baseline-debt-root dev/scripts/devctl/commands`
  now passes again while the broader crowded-root report remains truthful
  about `dev/scripts/checks`, `dev/scripts/devctl`, and
  `dev/scripts/devctl/tests`.
- Latest same-lane closure on 2026-04-02: the dirty-branch
  `dev/scripts/checks/**` modularization/layout blocker is closed. The
  remaining flat helpers for bundle workflow parity, duplication audit,
  naming consistency, and mutation Ralph loop now live behind documented
  package seams with compatibility shims at the root entrypoints, the
  `coderabbit_gate_core` package now re-exports through a legacy-module loader
  instead of duplicating helpers, and the branch-wide
  `python3 dev/scripts/devctl.py check --profile ci` bundle is green again.
- Latest same-lane closure on 2026-04-02: cross-repo proof is now honest on
  two real adopters for engine-run `probe-report --repo-path` and
  `check --repo-path`, but that is still only an adversarial sample, not a
  broad portability claim. The authority-loop lane closed two escaped
  portability defects in the same slice: valid Python headers with inline
  comments or indented method signatures no longer crash the shared function
  scanner, and external code-shape runs no longer import VoiceTerm-only
  `app/operator_console/**` override debt when those files do not exist in the
  target repo. `MP-376` now keeps an explicit external Python repo matrix plus
  failure-classification/rerun protocol so future claims widen the same honest
  adoption path. Remaining honest `Gate 2` gap: `startup-context` still needs
  a target-local/exported governance stack for Step-0 proof because it has no
  `--repo-path` mode yet.
- Latest same-lane closure on 2026-04-02: the follow-on self-hosting proof for
  that same portability slice exposed one more compatibility-seam miss. The
  new `python_function_scan` root shim now exists, and the affected
  `code_shape_*` / `rust_*` root shims now fall back cleanly in repo-package
  mode as well as direct script mode, so packaged guards loaded through
  `check_bootstrap.import_attr()` no longer depend on `dev/scripts/checks`
  being on `sys.path`.
- Latest same-lane closure on 2026-04-02: reviewer lifecycle truth now has one
  typed owner. `ReviewState.reviewer_runtime` and the new
  `ReviewerRuntimeContract` row/model now own reviewer mode/effective mode,
  freshness, stale reason, last poll, rollover state, session owner, allowed
  recovery action, review acceptance, and publish-clear state. Bridge
  `review_accepted` plus doctor output are projections over that contract, and
  the current 14 implemented platform contract rows now all declare
  `startup_surface_tokens` so startup/bootstrap surfaces project the same
  contract inventory that `platform-contracts` and the closure guard enforce.
- Latest same-lane closure on 2026-04-03: Phase-0 Slice 1 of the remote
  commit/push pipeline is now live as a read-only authority seam. The new
  `CommitIntentState` and `RemoteCommitPipelineContract` flow through typed
  `review_state` parsing, bridge/event-backed review-channel projections, a
  dedicated `review-channel --action doctor` surface, and the managed
  `commit_pipeline.json` artifact path. Recovery stays a governed action
  instead of a durable pipeline state, `approval_expires_at_utc` and
  `approved_target_identity` are required contract fields, and startup push
  truth still routes through `reviewer_runtime.publish_clear` /
  `push_decision.review_gate_allows_push` instead of a second evaluator.
- Latest same-lane closure on 2026-04-03: Phase-0 Slice 2 of that same remote
  commit/push lane is now wired through the existing review-channel packet
  system. `PacketPostRequest` accepts the dedicated `commit_approval` runtime
  packet kind with typed `pipeline_generation`, `staged_snapshot_hash`, and
  `guard_results_summary` fields, `review-channel --action post|ack|apply`
  preserves those fields through the event log and reduced packet rows, and
  typed review-state/action projections expose the approval payload without
  inventing a second publish-readiness evaluator. Maintainer discovery for
  that slice now stays aligned across `AGENTS.md`,
  `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`, and the owning
  `MP-377` plan docs instead of leaving the runtime approval vocabulary in one
  narrow surface.
- Latest same-lane closure on 2026-04-05: review-channel terminal-policy and
  visibility truth now share one owned contract. Launch/recovery/follow paths
  resolve terminal mode through one helper so explicit `--terminal` still wins,
  governed `remote_control` stays headless, already-headless parent sessions
  keep recovery headless, and otherwise local relaunch defaults back to visible
  `Terminal.app`; the CLI help text now says plainly that `--terminal none`
  means a real headless background conductor. The same slice extends
  `ReviewerRuntimeContract` with typed `conductor_visibility`, keeps reviewer
  `session_visibility` explicit in status/doctor payloads, and updates the
  platform-contract row/docs so AI and operators do not have to infer hidden
  headless state from raw `terminal_window_id` nulls. Remaining honest
  `MP-382` closure is lifecycle cleanup/orphan refusal/startup preflight
  cleanup, not another round of terminal-mode wording.
- Latest same-lane closure on 2026-04-09: visible local launch now also
  refuses transient temp clones/worktrees before any Terminal.app window or
  repo-owned runtime daemon starts. The shared launcher-discipline gate now
  treats temp-root trust prompts as an authority problem rather than an
  operator surprise: visible `launch` / `recover` require a stable
  repo-managed root, while governed `remote_control` remains the explicit
  headless lane. The focused proof also re-locked the attention split for
  automation-only polls so loop relaunch only wins over implementer reset when
  Claude still advertises a current ACK under a resettable live session hint.
- Latest same-lane closure on 2026-04-05: the bootstrap/authority surfaces now
  make launch and push interpretation explicit instead of leaving it to fresh
  AI inference. The owner docs and rendered AI bootstrap surface now direct
  new sessions to read `startup-context` `action` / `reason`,
  `interaction_mode`, `push_decision`, and typed reviewer visibility before
  any launch/recover choice, while the active `MP-377` owner docs now reserve
  a governed `override_push` receipt so future human publish overrides stay
  inside canonical `vcs.push` instead of raw shell fallback.
- Current accepted same-lane follow-up on 2026-04-06: publication authority
  must stop reusing startup/edit receipts. The next `MP-377` closure slice is
  one typed `PushAuthorizationRecord` bound to exact approved HEAD/check
  bundle identity so `devctl push --execute` consumes persisted publish proof
  instead of `startup-context` freshness or live reviewer-heartbeat state.
- Current accepted same-lane follow-up on 2026-04-07: commit/push latency must
  be improved by typed validation routing, not by weakening safeguards or
  asking agents to choose a "fast path" from memory. `check-router` already
  reports selected bundle, risk add-ons, changed paths, and reasons, while the
  governed stage pipeline already scopes paths and records staged tree hash;
  the gap is the missing tree-bound `ValidationPlan` / `ValidationReceipt`
  consumed by checkpoint/stage/commit/push. The first implementation order is:
  make missing quality evidence `unknown` / `stale` instead of green, emit the
  validation plan/receipt from repo-owned routing, bind VCS mutation and
  governed push to a fresh matching receipt, then project bundle/add-on/
  escalation reasons plus checkpoint/push sufficiency in doctor/status/
  dashboard. Keep strict full proof at push/release boundaries, but let the
  repo select targeted checkpoint proof deterministically.
- Latest same-lane closure on 2026-04-11: the first bounded slice of that
  validation/liveness order is now in repo code. The governed commit pipeline
  carries typed `ValidationPlan` / `ValidationReceipt` state bound to the
  staged tree, `vcs.commit` fails closed when that receipt is absent or stale,
  the nested governed push bypass moved off the exported env seam and onto an
  internal git config flag, and `refresh_status_snapshot()` now owns
  participant-liveness event emission instead of delegating it to a projection
  helper side effect.
- Current 2026-04-07 phase-order review inside that same lane: keep the next
  coding order architecture-first. The narrow VCS `ValidationPlan` /
  `ValidationReceipt` is a Phase-1/P0 mutation-proof prerequisite for the
  commit gate and smarter checkpoint/push cadence, while the broader
  `DecisionPacket.validation_plan` lane remains Phase 5b evidence/provenance
  generalization. `MP-376` multi-repo matrix work is still primary proof for
  VoiceTerm leakage, but Step-0/startup/repo-pack/governed-push failures from
  that matrix must route back to `MP-377` blockers before wider adopter waves
  or frontend/operator expansion. Do not build dashboard, automation,
  operator-console, or future review-loop features as new authority surfaces
  before their typed contracts and repo-pack capability gates exist.
- Current 2026-04-07 portability-by-default review inside that same lane: the
  platform is portable by architecture but not yet portable by default. The
  next execution order is explicit: remove hidden VoiceTerm defaults from
  shared runtime/tooling layers, add a static portability guard for forbidden
  shared-layer literals and import-time path captures, prove the controlled
  repo matrix first (Python-only, Rust CLI, mixed Python/Rust, and custom
  docs/layout/no-tandem shapes), and only then widen into broader external
  repo trials. Review-channel, autonomy, operator-console, bridge/tandem, and
  local-terminal assumptions must become typed repo-pack capabilities instead
  of implied infrastructure, and `SystemCatalog` / contract-closure checks
  must block missing repo-pack/capability bindings across generated
  dashboard/session-resume/phone/CI projections.
- Current 2026-04-07 ReviewSnapshot audit-intake routing inside that same
  lane: `dev/audits/architecture_hardening_plan.md` is accepted as
  reference intake, not as another active plan. The next execution order from
  that audit is now absorbed into owner docs: Tier 1 path/default/doc-policy
  and diagnostics findings belong to `platform_authority_loop.md`; raw
  raw commit hook proof, override receipt enforcement, remaining hook-family
  follow-ups, and `PushAuthorizationRecord` integrity belong to
  `remote_commit_pipeline.md`; cross-surface consistency, contract
  registration, suggested-command/WhyRecord production consumers, generated
  artifact integrity, MCP, and Agent SDK surfaces belong to
  `ai_governance_platform.md`; fresh-adopter proof and repo-pack distribution
  belong to `portable_code_governance.md`. `dev/audits/REVIEW_SNAPSHOT.md`
  stays generated evidence only. The same intake also locks the hook stance:
  git/session/provider hooks may force entry into typed `devctl` commands and
  close bypasses, but they must not become a second governance engine; typed
  contracts, receipts, and guards remain the decision authority.
- Latest same-lane closure on 2026-04-03: the workflow-enforcement parity for
  the Phase 3/4 remote-commit proof guards is now explicit.
  `.github/workflows/tooling_control_plane.yml` and
  `.github/workflows/release_preflight.yml` both run
  `check_audit_status_sync.py` and
  `check_review_surface_consistency.py`, so the bundle registry, maintainer
  docs, and CI lanes now advertise the same required proof surface.
- Latest same-lane closure on 2026-04-03: the first Phase-1 daemon-liveness
  follow-up is now in place for the same remote session lane. Live
  `review-channel --action launch|rollover` starts the persistent
  ensure-follow publisher from the actual launch router instead of hiding
  daemon ownership in the terminal helper, the checked-in launchd
  template/wrapper pair under `dev/config/launchd/` maps publisher stop
  reasons into restart-vs-stop exit classes for login-time remote-control
  sessions, and the compact doctor projection now carries publisher/supervisor
  running state plus last heartbeat/stop-reason fields so phone dashboards can
  read daemon readiness from the same reduced surface as `commit_pipeline`.
- Latest same-lane closure on 2026-04-03: the follow-on Phase-2 authority
  cleanup is now in place for that same remote session lane. Reviewer-runtime
  state now owns implementer ACK-current plus implementation-block truth, the
  status/startup push gates read those typed fields instead of bridge-liveness
  `reviewer_mode` / `claude_ack_current`, `bridge_review_accepted()` no longer
  falls back to prose parsing, and governed push recovery now matches the
  reviewer-approved `tree-receipt-<timestamp>:<staged_tree_hash>` identity from
  the remote commit pipeline instead of raw `HEAD` equality.
- Latest same-lane closure on 2026-04-04: `ReviewState.attention` is now a
  deterministic projection of the typed `recovery_assessment` diagnosis/decision
  pair when both are present, instead of an independently authored field.
  `review_state_parse_support.py` projects `status`, `owner`, `summary`,
  `recommended_action`, and `recommended_command` from the assessment's
  `diagnosis` and `decision` objects. Reviewer runtime doctor snapshots
  (`reviewer_runtime_snapshot.py`) prefer the typed `ReviewState.attention`
  over the raw attention parameter. `check_review_surface_consistency.py` now
  enforces the projection contract: field drift between raw attention and the
  canonical projection is a CI-blocking error. Evidence:
  `dev/scripts/devctl/runtime/review_state_parse_support.py`,
  `dev/scripts/devctl/runtime/review_state_parser.py`,
  `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`,
  `dev/scripts/checks/review_surface_consistency/parity.py`,
  `dev/scripts/devctl/platform/runtime_state_contract_rows.py`.
- Latest same-lane closure on 2026-04-04: bridge portability — heartbeat
  timestamps, worktree-hash exclusion, swarm-mode plan path, bridge
  metadata regexes, and guard error messages now derive from
  `RepoPathConfig` fields instead of hardcoded VoiceTerm values. Evidence:
  `dev/scripts/devctl/review_channel/heartbeat.py`,
  `dev/scripts/devctl/review_channel/bridge_projection_state.py`,
  `dev/scripts/devctl/review_channel/bridge_projection.py`,
  `dev/scripts/devctl/review_channel/reviewer_state_support.py`,
  `dev/scripts/devctl/review_channel/handoff_constants.py`,
  `dev/scripts/devctl/repo_packs/voiceterm.py`,
  `dev/scripts/checks/review_channel_bridge/report.py`.
- Latest same-lane closure on 2026-04-15: `review_state_parser.py` now accepts
  flat typed review-state payloads by a shared canonical key set
  (`current_session`, `reviewer_runtime`, `coordination`,
  `authority_snapshot`, `packet_inbox`, `recovery_assessment`, and related
  envelope fields) instead of only recognizing bridge-shaped `review` /
  `queue` / `bridge` wrappers. That keeps bridge-backed and event-backed
  producers aligned on one parse surface without reintroducing compatibility
  prose as authority. Evidence:
  `dev/scripts/devctl/runtime/review_state_parser.py`,
  `dev/scripts/devctl/tests/runtime/test_review_state.py`,
  `dev/scripts/checks/check_review_surface_consistency.py`.
- Accepted next Phase-6 direction inside that same lane: keep canonical
  pointer refs as the authority surface for plans/docs/repo-map/evidence,
  then layer native repo-owned `ConceptIndex` / optional ZGraph-compatible
  navigation plus a report-only `devctl` context-graph query surface on top
  of those pointers. Do not introduce a separate semantic authority store.
- Accepted retrieval/control stack inside that same lane: hard guards/probes
  stay the cheapest deterministic classifier layer, `ConceptIndex` /
  ZGraph-compatible graph outputs are the reversible search-space reducer over
  canonical refs, `startup-context` / `ContextPack` reconstruct the minimum
  cited working slice for the current scope, and review/autonomy/Ralph AI
  loops remain the expensive fallback/controller layer for work the cheaper
  layers cannot resolve. Do not collapse those layers into one prompt-local
  blob or let generated graph/context surfaces become a second authority.
- Current graph/intake follow-up inside that same lane: the live
  `context-graph` slice is still a bounded discovery helper, not the full
  least-effort scheduler. Next ladder is explicit: add command->handler/source
  closure plus first richer typed relation families, staged query filtering,
  bounded multi-hop inference, and honesty guards first, then a typed
  `startup-context` / `WorkIntakePacket` reducer that acts as the
  deterministic context router for command goal/intent + changed scope +
  budgeted cited read set + targeted checks, then live routing inputs (diff,
  findings, failed checks, plan scope), then symbol/test/finding/policy/
  workflow/config graph coverage, including Swift/iOS surfaces used by this
  repo.
- Current graph hygiene quick wins inside that same lane: unify `INDEX.md`
  parsing behind one canonical helper for doc-authority/context-graph/plan-
  resolution consumers, add a hard parity guard for `COMMAND_HANDLERS` versus
  `devctl list` command inventory, fix shared topology-scan exclusions so
  calibration/transient roots (`dev/repo_example_temp/**`,
  `.claude/worktrees/**`) never pollute live graph confidence, prefer fresh
  `dev/reports/probes/latest/file_topology.json` +
  `review_packet.json` for changed-path/hint/severity inputs with rescan
  fallback only when artifacts are stale or missing, normalize
  context-graph temperature from the shared hotspot scorer instead of
  maintaining a parallel algorithm, and formalize file-pattern trigger-table
  routing so the graph can request the right warm knowledge for a touched
  subsystem without inflating bootstrap.
- Current context-budget rule inside that same lane: keep the default startup
  packet slim (roughly <=2K tokens) and prefer query-on-demand / warm-context
  retrieval over preloading larger context blobs, because the platform should
  optimize for bounded discovery rather than "load everything just in case."
- Current startup-family rule inside that same lane: `startup-context`
  remains the canonical bounded startup packet; `context-graph --mode
  bootstrap` is a reducer/hot-index helper over the same cached authority,
  not a second peer bootstrap surface.
- Current bootstrap discoverability rule inside that same lane: generated
  `CLAUDE.md` and other repo-pack bootstrap surfaces must advertise the live
  governance capability set (`ai_instruction`, `decision_mode`,
  `governance-review --record`, packet-level operational feedback, and saved
  graph-snapshot baselines) and point agents back to
  `dev/guides/DEVELOPMENT.md` plus `dev/scripts/README.md` for the canonical
  "which tool do I run when?" routing. This is awareness guidance only;
  runtime authority still stays with `startup-context` / `WorkIntakePacket`.
- Current startup-surface closure inside that same lane: the repo-pack
  bootstrap steps, key command block, and post-edit checklist are now
  code-derived instead of manually curated policy prose, and
  `context-graph --mode bootstrap` now surfaces bounded probe/governance/
  watchdog/reliability summaries plus hotspot guidance from existing
  artifacts. Remaining closure is to move the same richer evidence family
  into canonical `startup-context` / `WorkIntakePacket` authority so the
  intake packet stays ahead of the helper surfaces.
- Current deterministic-routing rule inside that same lane: graph work only
  counts as usable startup/recovery help when one bounded request can return a
  cited read set before ad hoc file exploration. The first truthful router
  needs staged exact/canonical/typed-relation filtering, bounded multi-hop
  inference, and a small hot-query cache with explicit invalidation; keep all
  of that generated-only, reversible, and anchored in canonical typed
  relation families (`guards`, `scoped_by`, operation-semantic producer /
  consumer paths) instead of opaque semantic search.
- Current `P0` closure focus inside that sequence: canonical `Finding`-based
  packets, `FixPacket` / `DecisionPacket` split, schema/version matrices,
  `CommandGoalTaxonomy` + validation-routing closure, and a contract-closure
  guard so packet families, generated surfaces, and the runtime contract
  catalog cannot drift apart.
- Current meta-governance follow-up inside that `P0` closure: the platform
  must also prove its own checking stack is complete. Track guard/probe test
  coverage, CI invocation coverage, exception-list completeness, workflow
  timeout coverage, and data-as-code/configuration drift as first-class
  platform evidence instead of assuming the guard registry is self-policing.
- Current recurrence-closing governance rule inside that same `P0` closure:
  escaped defects are not complete at instance remediation. For each escaped
  class, the active plan must now record 1) the root-cause class, 2) the
  minimal deterministic prevention surface (`guard`, typed contract,
  bootstrap/helper contract, smoke test, or explicit bounded debt), 3) the
  equivalent-instance boundary the prevention applies to, and 4) the
  regression proof that closes the class. Generalize enforcement, not patches;
  widen only across instances governed by the same contract, not by loose
  similarity.
- Current accepted self-hosting slice inside that `P0` work: `probe-report`
  now routes its first shared `Finding` / `DecisionPacket` contract seam
  through `devctl.runtime`, durable `ProbeReport` / `ReviewPacket` /
  `ReviewTargets` / `FileTopology` / `ProbeAllowlist` artifacts carry
  explicit schema metadata, and `check_platform_contract_closure.py` now
  enforces runtime-model/artifact-matrix/startup-surface closure for the
  current implemented platform families surfaced by `platform-contracts`.
- Current governance-surface readout: the repository still has 62 raw
  `check_*.py` entrypoints and 26 raw `probe_*.py` entrypoints on disk, while
  the active policy-enabled surface currently exposes 32 hard guards and 23
  review probes. Use the enabled counts for active enforcement scope and the
  raw counts for filesystem inventory only.
- Current VCS-governance proof point inside that same `P0` lane: the repo now
  has its first repo-pack-owned push-routing contract. `repo_governance.push`
  owns remote/default-branch/protected-branch rules plus preflight, post-push,
  and policy-gated bypass routing, `devctl push` now emits typed push-stage
  truth (`validation_ready`, `published_remote`, `post_push_green`), persists
  the managed latest push artifact at `dev/reports/push/latest.json`, writes
  a `published_remote` snapshot as soon as `git push` succeeds, records the
  current branch/HEAD in that artifact so startup can override stale local
  upstream divergence during recovery, and legacy `sync` / release helpers
  now read the same policy instead of hardcoding GitHub push defaults.
- Current checkpoint-intake follow-up inside that same lane: startup surfaces
  must expose not only whether a push is policy-guarded, but whether the
  current worktree is still within the repo-pack-defined continuation budget.
  Agents need deterministic `safe_to_continue_editing` /
  `checkpoint_required` state plus dirty-path budget evidence so they can
  stop and checkpoint a bounded slice before context debt grows, not only
  after the tree has already become arbitrarily messy. Bridge-backed
  `review-channel --action status` now projects the same
  `push_enforcement` snapshot and raises `checkpoint_required` attention so
  operator/read-only flows see that budget without a separate
  `startup-context` run. Accepted next closure rule: checkpoint/push events
  should also emit one generated repo-pack-owned packet into a managed cache
  root so startup can warm from fresh evidence instead of recomputing the same
  bounded git/plan/guard/review summary every session. Keep that layer
  generated-only, hash-invalidated, and disposable; canonical authority stays
  in git state, active plans, repo policy, and guard/review outputs.
- Current startup discoverability follow-up inside that same lane: the compact
  `startup-context --format summary` and markdown render now also surface
  unpublished stack depth (`ahead_of_upstream_commits`) plus explicit
  governed-push timing guidance when local commits are waiting on review or
  checkpoint clearance, so fresh sessions no longer have to infer "when do we
  push?" from buried JSON fields or separate `git` inspection.
- Current checkpoint-scope rule inside that same lane: `context-graph` /
  `ConceptIndex` / ZGraph-compatible outputs may help explain a candidate
  checkpoint by narrowing related plan/check/doc scope around the real diff,
  but they do not decide what belongs in a push. Canonical checkpoint truth
  remains git diff plus routed plan scope plus guard/review evidence; when the
  graph layer is low-confidence, the system should narrow the slice or stop,
  not widen the batch.
- Current self-hosting plan-doc gap inside that same lane: the repo already
  has meaningful typed governance/runtime contracts in code, but governed
  active-plan markdown is still less uniform than the contract layer it
  describes. The next self-hosting closure slice is to freeze one governed
  plan format, extend the existing active-plan/docs-governance enforcement
  path, and bring execution-plan docs into parity with the repo's own
  metadata/header/`Session Resume` expectations before the future
  `PlanRegistry` / `PlanTargetRef` loader claims markdown-derived authority.
- Current plan-authority follow-up after that self-hosting slice: discovery
  and blocking contract enforcement are now in place, but governed plans are
  still only partially consumed as structured runtime state. Today
  `review_channel/promotion.py` reads `## Execution Checklist`, while
  `Session Resume`, `Progress Log`, and `Audit Evidence` remain markdown-only
  restart/evidence surfaces, and `plan_patch_review` mutation ops are
  validated in packet contracts without runtime handlers that apply those
  mutations back to governed plan docs with typed receipts.
- Current typed-markdown runtime baseline inside that same lane: the first
  groundwork slice is now real in code. `ProjectGovernance` carries a typed
  `DocPolicy`, a typed `DocRegistry`, and parsed `PlanRegistry` entries built
  from governed markdown + `INDEX.md`, while keeping the existing path fields
  alive as compatibility seams. The next closure item is to make
  `startup-context` / `WorkIntakePacket` consume that same authority family
  instead of treating `context-graph --mode bootstrap` or ad hoc doc reads as
  peer startup paths.
- Current portability correction inside that typed-markdown slice: repo-pack /
  repo-policy context now owns governed markdown discovery. The runtime no
  longer relies only on `AGENTS.md` + `dev/active/*` assumptions; it now
  prefers `repo_governance.surface_generation.context` plus markdown-root
  policy for process doc, tracker, registry, bootstrap links, and
  startup-authority checks, with focused regressions proving a non-VoiceTerm
  layout. Remaining portability work is broader than path discovery:
  starter-bootstrap still needs to emit the full governed-plan doc set, and
  later `startup-context` / `WorkIntakePacket` still need to consume this
  policy-owned authority family end-to-end.
- Current review-channel bridge-authority cutover status: `review_state.json`
  and `compact.json` now carry a typed `current_session` block for live
  instruction revision, implementer status, implementer ACK state, findings,
  and reviewed scope, and `latest.md` current-status rendering now prefers
  that typed state over append-only bridge prose. The remaining work is to
  migrate writer/mutation paths plus the remaining push/preflight consumers so
  `bridge.md` becomes a generated repo-pack-owned compatibility projection
  instead of a live current-status authority or freshness gate. Fresh-session
  bootstrap now treats checkpoint-before-continue as the start point, with
  `current_session` / `reviewer_runtime` preferred over stale bridge prose
  when they diverge; the next follow-ups are fresh open-finding recomputation
  and a distinct external-agent authority-drift detector.
  `startup-context`, `check_tandem_consistency`, and the governed push gate
  now refresh the bridge-backed typed review-state projection before
  consuming `current_session` / review freshness, so stale
  `dev/reports/review_channel/latest/review_state.json` snapshots no longer
  strand startup or preflight truth behind older bridge-derived state.
  `check_tandem_consistency` now
  prefers typed `review_state.json` authority for 4 of 7 checks (reviewer
  freshness, implementer ACK, completion stall, promotion state); the
  remaining 3 checks still use bridge-text fallback where no typed equivalent
  exists. `startup-context` reads typed `review_accepted` from the projection,
  and the symmetric repo-owned `reviewer-wait` path now wakes from
  `reviewer_worker` hash drift plus projected `current_session`
  implementer ACK/status updates instead of one-shot status reads or ad hoc
  shell sleep loops. 2026-03-26 bridge-hygiene follow-up landed: the repo now
  has `review-channel --action render-bridge` as a repair/rebuild path for the
  transitional compatibility bridge, and `check_review_channel_bridge.py` now
  fails closed on oversize bridges, duplicate/unsupported H2 sections,
  transcript/ANSI contamination, and overgrown live owned sections so a
  4000-line mixed bridge transcript cannot silently remain current-state
  authority. 2026-03-28 follow-up closed the sibling event-backed leak too:
  queue/current-session instruction-shaped projections now use the same flat
  no-H2 context summary as bridge-safe promotion text, while full context
  packets stay in source metadata/prompt surfaces instead of reappearing as
  nested headings in compatibility outputs. 2026-03-29 follow-up closed the
  bounded bridge-projection purity slice too: bridge-backed status projection
  now emits a typed `bridge_projection` payload, `review-channel --action
  render-bridge` rebuilds `bridge.md` only from that typed payload instead of
  reparsing live markdown, and fixed-section render rejects embedded markdown
  headings so duplicate `## Context Recovery Packet` blocks do not leak back
  into the compatibility projection on rerender. This does not retire the
  bridge or finish the full typed writer cutover; those broader MP-355 /
  MP-377 closures remain open. Latest same-lane follow-up (2026-03-29): the
  persisted typed `review_state.json` bridge block now carries
  `reviewed_hash_current` and `review_needed` directly, so saved typed review
  state no longer drops the core reviewer-hash truth while `current_session`
  stays intentionally limited to instruction / ACK state. Same-day authority
  follow-up also closed the live semantic ACK false-stale bug: the
  review-channel path now shares one ACK parser/validator/prompt contract,
  typed `current_session` owns instruction/ACK machine state, bridge-backed
  `bridge-poll` refreshes and prefers the typed `review_state` snapshot for
  live ACK authority, and compatibility bridge rendering prefers typed
  current-session sections for machine-deciding live fields instead of raw
  bridge prose. Remaining follow-up stays broader than ACK wording:
  reviewer-owned prose / wait-reason state still needs the planned
  `DecisionTrace` + typed writer-authority cutover before markdown stops being
  any part of the live authoring path. 2026-03-30 live-proof follow-up closed
  the next repo-owned conductor contract gaps too: generated Claude prompts no
  longer hardcode stale MP-355/VoiceTerm wording, `review-channel --action
  reset-implementer-state` is now a real repair action for canonical pending
  implementer sections, reviewer heartbeat refresh preserves a real reviewer
  checkpoint `Poll Status`, and Claude-side wait treats reviewer-owned hold-
  steady / checkpoint / governed-push-pending state as valid wait posture
  instead of bouncing the operator into manual menu selection. Remaining live
  proof now depends on cutting a checkpoint-clean slice so startup/launch can
  permit a fresh repo-owned relaunch.
- Current runtime-baseline correction after the 2026-03-21 architecture audit:
  Phase 1 closure must keep five runtime-behind-docs gaps explicit instead of
  treating them as background drift. Portability is still blocked first by
  VoiceTerm-default path/runtime authority, startup/review recovery still
  leaks bridge/projection fallback into the control path, provider-shaped
  review fields plus `active_dual_agent` defaults remain compatibility state
  rather than the final middle layer, `plan_patch_review` / `apply` still
  stops at event-state transition without executable plan mutation, and
  concrete slices such as `vcs.push` still need `ActionResult` business-state
  cleanup plus real `RunRecord` closure before the authority loop can claim
  runtime parity with the docs.
- Current portability-audit correction after the 2026-03-26 architecture
  review: the main blocker is broader than the remaining bridge consumer
  count. The typed governance/runtime spine still carries hidden VoiceTerm
  default authority in places where portable mode should fail closed or use an
  explicit repo-pack: `ProjectGovernance` / `DocPolicy` / `PlanRegistry` /
  `ArtifactRoots` / `BridgeConfig` still default missing fields to
  `dev/active/*`, `dev/reports/*`, and `bridge.md`; `active_path_config()`
  still falls back to `VOICETERM_PATH_CONFIG`; several review-channel modules
  still freeze that config at import time; and generated AI/bootstrap/review
  surfaces still emit VoiceTerm/tandem rules as if they were universal. The
  accepted remediation order is now explicit: fail closed on missing
  repo-pack/governance path families outside compatibility mode, remove frozen
  global path capture from runtime surfaces, generate AI/bootstrap/review
  instructions from governed repo-pack state instead of literals, and add a
  portability-drift guard plus non-VoiceTerm fixture-repo proof before
  `MP-377` can claim portable authority-loop closure.
- 2026-03-26 portability-audit follow-up: the current burn-down queue is now
  concrete, not generic. Highest-priority remaining leaks are governance
  models that still default partial state back to VoiceTerm path literals,
  review-state lookup that can still drop to repo-pack globals when callers
  skip explicit governance, plan-resolution/tandem checks that still infer one
  repo's authority chain, bridge-hash exclusions that still assume root
  `bridge.md`, and first-hop AI bootstrap surfaces that still under-specify
  the portable-platform boundary. Treat those as blocking authority-loop work,
  not cleanup to defer behind new features.
- 2026-03-26 architecture-review convergence follow-up: the shared audit now
  covers all Python control-plane subsystems, but convergence does not mean
  the work is done. The remaining mapped fix queue now explicitly includes
  fail-closed `docs-check` defaults, portable MCP identity and status-provider
  boundaries, `process_sweep` binary-pattern generalization,
  repo-pack-defined report-retention policy, integration-federation
  destination-root policy, portable tandem hash exclusions, and the last
  import-time repo-pack path freezes outside review-channel proper. Treat the
  audit as complete enough to route implementation, not as a reason to stop
  promoting findings into scoped plans.
- 2026-03-26 architecture-review closure-truth correction: the bounded Codex
  pass over `dev/audits/architecture_alignment.md` did correct one false
  `MP-375` gap claim (`SUB_SCORE_WEIGHTS` is already owned in
  `review_probes.md`), one `MP-377` owner typo for tandem hash exclusions,
  and the proof links for the fixed push/bridge/docs-teaching rows. That
  pass was ledger cleanup, not proof that whole-platform discovery is
  finished. The live audit loop is now explicit: Claude is the primary broad
  finder across the full AI governance platform and connected Python control-
  plane surfaces; Codex verifies Claude deltas against actual code/docs and
  only then promotes verified findings into `MASTER_PLAN` plus the scoped
  owner plans. `dev/audits/architecture_alignment.md` is the shared audit
  ledger, not the execution owner, and Codex-side broad audit swarms should
  stay off. Do not claim whole-platform "no new issues" or closure until
  full subsystem coverage is re-verified and two consecutive Claude+Codex
  broad passes add no new HIGH/MEDIUM findings.
- 2026-03-26 architecture-review verification follow-up: Codex reviewed
  Claude's next broad pass against the actual code and accepted four concrete
  findings for owner routing. `MP-377` now has two additional startup-
  authority gaps to close: `runtime/startup_context.py` swallows bridge-parse
  failure into `implementation_block_reason="bridge_parse_error"` without
  surfacing that degradation through the startup receipt/rendered operator
  path, and `_resolve_bridge_path()` still catches only `ImportError` while
  sibling startup code already handles `OSError`/`ValueError` fail-closed.
  `MP-376` now also owns two newly verified portability gaps:
  `resolve_docs_check_policy()` silently falls back to VoiceTerm maintainer-
  doc defaults when the repo policy section is empty, and
  `detect_repo_capabilities()` still recognizes only Python/Rust families and
  silently disables language-dependent probes on other repos. The raw Pass 8
  percentage-style portability scores were not accepted as authoritative and
  were stripped back to scoped, evidence-backed claims.
- 2026-03-26 launch-contract follow-up: `MP-355` now also owns the reviewer
  reset/launch seam hardening that was exposed during the architecture-loop
  relaunch attempt. Fresh launch validation must accept the canonical
  reviewer-reset implementer placeholder state (`Claude Status: - pending`,
  `Claude Ack: - pending`) for a new instruction revision, the bridge guard
  must tolerate wrapped required marker text instead of failing on formatting
  alone, and reviewer-owned instruction resets must clear stale `Claude
  Questions` so compatibility-bridge handoff text does not carry dead
  blockers into the next tranche.
- 2026-03-26 architecture-doc teaching correction: portability closure also
  includes the docs and starter surfaces that future AI sessions read first.
  Plain-language architecture/runbook text must front-load that VoiceTerm is
  a first-party adopter/client of the governance platform, `bridge.md` is an
  optional repo-pack-owned compatibility projection, and review/MCP/mobile/
  PyQt6 surfaces are clients over one governed backend. Treat docs that
  re-teach VoiceTerm-first authority or fixed repo-local paths as
  architecture drift, not harmless wording.
- 2026-03-26 documentation-authority/self-hosting priority correction: the
  repo already has the universal markdown/governance plan, but it is split
  across the tracked `MP-377` / `MP-376` docs rather than one root tracker.
  Canonical execution authority stays in `MASTER_PLAN.md`,
  `ai_governance_platform.md`, `platform_authority_loop.md`,
  `portable_code_governance.md`, and `PLAN_FORMAT.md`; root companions such
  as `UNIVERSAL_SYSTEM_PLAN.md`, `UNIVERSAL_SYSTEM_EVIDENCE.md`,
  `ZGRAPH_RESEARCH_EVIDENCE.md`, and `GUARD_AUDIT_FINDINGS.md` stay
  reference-only intake/evidence and must not become parallel trackers. The
  next proof slice is therefore explicit: self-host that doc-authority
  system on this repo first via root markdown/file budgets, active-doc
  graduation/consolidation, and generated AI/bootstrap surfaces from
  governed state, then prove the same contract on non-VoiceTerm adopters.
- 2026-03-26 archive/demotion gate correction: reference-doc cleanup must be
  absorption-first, not delete-first. The current repo still carries 27
  `dev/active/*.md` docs and 10 root-level markdown entrypoints, so no
  archive/demotion move is valid until execution-relevant conclusions from the
  candidate file are mirrored into `MASTER_PLAN` plus the owning scoped plan.
  Thin bridge pointers may stay reference-only, but root evidence companions
  and audit transcripts are blocked from archival until that mapping audit is
  explicit and green.
- 2026-03-26 deferred/ADR lifecycle correction: the owner chain still needs
  one explicit self-governance contract for stale deferred work and accepted
  ADR / Locked Decision parity. Current hygiene covers structure/reference
  drift, but it does not yet give deferred docs reactivation metadata/gates or
  prove that accepted decision records are enforced by runtime/guard surfaces.
- 2026-03-26 push-readiness contract correction: the repo now treats raw git
  cleanliness and actual push eligibility as different layers. `push_ready`
  was misleading because it only meant "clean worktree"; the live controller
  now exposes `worktree_clean`, reviewer gating now uses
  `review_gate_allows_push`, and `startup-context` can emit `await_review`
  for checkpointed-but-unaccepted slices. Remaining `MP-377` closure is the
  deeper contract split between continuation-budget/edit-safety state and
  branch-push mechanics plus the future typed `push_eligible_now` packet.
  Maintainer docs/README must keep teaching the same distinction so future AI
  sessions do not relearn "clean tree == push-ready" from repo prose. Follow-
  on correction: repo-governance push state now also needs a typed advisory-
  context exclusion path (`convo.md` in VoiceTerm today) so local scratch
  files do not strand reviewed commits outside the governed push lane.
- 2026-03-26 governed-push/runtime portability follow-up: two previously
  mapped authority seams are now fixed in code. `sync --push` no longer
  bypasses the governed push path with raw `git push`; it now reuses the
  same startup/review gating, preflight, post-push, and typed push action
  flow as `devctl push`. The typed governance/runtime layer also stops
  inventing VoiceTerm `review_root`, `bridge_path`, and
  `review_channel_path` values from sparse governance payloads, and
  review-state lookup now consults repo-pack candidates only when a repo has
  explicitly overridden them. Remaining open follow-up is broader than this
  patch: raw AI-controlled push callers, portability-drift enforcement, and
  cross-repo fixture proof still need closure under `MP-376` / `MP-377`.
- 2026-03-26 doc-authority portability follow-up: the repo can partially
  support alternate plan filenames and governed doc roots today, but the core
  typed contract still defaults partial payloads back to `AGENTS.md`,
  `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and `dev/reports/*`.
  Treat "works when adopters mirror VoiceTerm names" as a failed portability
  proof. Remaining closure now explicitly includes fail-closed/custom-layout
  authority discovery, custom report-root proof, and review-channel/control-
  plane consumers that still hardcode `bridge.md` plus `dev/active/*`.
- 2026-03-27 architecture focus lock: keep the next platform tranche centered
  on self-hosting authority compression plus governed-push integrity. Until
  those closures land, do not widen scope into new universal-roadmap docs,
  archive/delete sweeps, or extraction packaging churn unless the work
  directly reduces one of these three gaps: governed markdown budget/overlap,
  development-self-hosting vs adopter/bootstrap leakage, or push-contract
  truth. New audit findings in this neighborhood should route through
  `dev/audits/architecture_alignment.md` and then back into `MP-377` /
  `MP-376`, not into another tracker surface.
- 2026-03-27 external-review adjudication: a fresh architecture review was
  accepted as confirming the same owner-chain direction, but only after
  translation into the repo's current typed model. The approved next work is
  now explicit: keep machine startup authority singular through
  `ProjectGovernance` / generated `project.governance.json` plus typed
  registries/receipts, keep the reviewed `project.governance.md` contract as
  the human mirror, add clearer artifact-role/scope classification so AI can
  distinguish platform core vs repo-pack/client vs development-self-hosting
  surfaces, prove optional subsystem capability gating for adopters, and make
  Ralph/remediation consume canonical finding history before promoting new
  guard candidates. The same adjudication also locks three under-specified
  follow-ups into this tranche: route startup-order/warm-ref loading through
  artifact-role/scope gating so dev/process docs and compatibility
  projections are lane-specific, keep guard/probe/bundle/provider registries
  on the existing config-driven policy/repo-pack closure path, and require
  self-host meta-governance plus a second-repo proof before widening graph or
  memory work. Do not create a second constitution doc, a JSON-only rewrite,
  or a blanket "every plan gets a twin now" project outside the existing
  `MP-377` / `MP-376` chain.
- 2026-03-27 authority-leak tranche 1 landed: the first bounded `MP-377`
  startup-authority closure is now live in code. `ProjectGovernance`
  plan/doc entries carry typed `artifact_role` / `authority_kind` /
  `system_scope` / `consumer_scope`, `startup-context` no longer falls back
  to `bridge.md` prose when typed `review_state.json` is missing, default
  warm refs suppress compatibility projections plus lane-specific docs, and
  custom-layout/no-bridge fixture repos now prove the same behavior outside
  the VoiceTerm default layout. Remaining same-lane work stays narrow:
  explicit repo-pack capability gating, broader docs-authority compression,
  fail-closed push publication state, and Ralph canonical-history closure.
- 2026-03-27 shared backlog intake landed: the same authority-loop tranche now
  treats root `backlog.md` as a repo-pack-configured governed shared backlog
  doc instead of an orphaned side file. Startup/work-intake can surface that
  backlog in warm refs plus writeback sinks for human/AI coordination, while
  execution authority stays fail-closed on `dev/active/MASTER_PLAN.md` plus
  the owning active plan. This closes the old "hidden backlog vs tracked
  execution" gap without reopening a second tracker surface.
- 2026-03-27 portable baseline-repo contract clarified: keep `backlog.md`
  empty unless there is real queued work. Foundational architecture and
  cross-repo organization decisions belong in the existing owner-plan chain,
  not in backlog. The next organization slice stays split on purpose:
  `MP-376` owns the reusable repo-shape/convention policy and enforcement
  contract, while `MP-377` owns the minimal startup/work-intake baseline that
  should surface process doc + execution tracker + shared backlog + policy
  without forcing every adopter into the full VoiceTerm plan lattice.
- 2026-03-27 self-hosting organization priority correction: the repo does not
  need another universal-system roadmap. The active `MP-377` / `MP-376`
  chain already owns the universal docs/governance architecture; the missing
  work is executable compression and self-hosting enforcement. Current
  repo-owned baselines make that explicit: `doc-authority` reports `50`
  governed docs / `45,107` lines, `19` budget violations, `4` authority
  overlaps, and `8` consolidation candidates, while `check_package_layout`
  still reports four crowded directories and seven crowded namespace families
  under the `devctl` stack. The same self-hosting lane now ratchets those
  known crowded `devctl` roots/families from `freeze` to `strict` for touched
  edits so the existing `package_layout` engine stops treating active work
  there as ordinary healthy churn. The next priority tranche is therefore
  explicit: finish `DocPolicy` / `DocRegistry` / `doc-authority`, absorb root
  intake conclusions into owner docs, separate development-self-hosting docs
  from adopter/bootstrap surfaces, and use that same contract to shrink the
  live authority surface instead of adding more planning prose.
- 2026-03-27 package-layout truth follow-up: the self-hosting organization
  guard was honest about crowded roots/families but still easy to misread
  because `ok: True` only meant "no blocking drift in this edit." The same
  `package_layout` surface now emits explicit baseline-debt state
  (`status=baseline_debt_detected`, `layout_clean=false`) whenever freeze-mode
  crowded roots/families remain, so the repo cannot describe itself as
  structurally clean while that debt is still open. Keep the next ratchet in
  the same owner chain: use this truthful state to drive bounded decomposition
  and only then promote selected crowded roots/families from reporting debt to
  blocking working-tree failures.
- 2026-03-29 ensure-action probe-guided refactor: `ensure.py` orchestration
  split into `_ensure_helpers.py` (heartbeat refresh, detail assembly, report
  construction) and focused publisher lifecycle helpers. Target function
  identifier density reduced 18-30% (max 69→51). Remaining HIGH findings
  come from both typed field mapping (report/status constructors with 20+
  named fields) and operational helpers that thread `args, repo_root, paths,
  deps` through every call site. Further reduction requires either bundling
  those 4 params into a context object (cascading into `_ensure_supervisor`)
  or accepting the structural minimum for typed data-bridge code.
- 2026-03-29 startup thesis bootstrap closure: `startup-context` now renders a
  bounded `## Why Stack` section from `dev/config/why_stack.md` before the
  SOP/router detail, so fresh sessions see the product mission, proof
  obligation, platform boundaries, and current priority before process-heavy
  guidance. The next same-lane follow-up stays scoped to generated bootstrap
  surfaces: make the client-vs-core boundary equally explicit in starter
  instructions/docs instead of implying it from VoiceTerm defaults.
- 2026-03-30 startup auto-repair closure: repo-owned `startup-context --repair` now
  reads typed `startup-context`, startup-authority, and the same typed
  `ReviewState` owner produced by repo-owned `review-channel` status refresh,
  classifies approval-boundary vs safe-local-repair vs manual-follow-up
  state, applies one bounded repo-owned safe fix per invocation, and refreshes
  the managed startup receipt after each pass. This closes the first local
  repair-controller slice without pretending the wider graph-backed
  architecture-trigger work is finished.
- 2026-03-31 startup repair-path parity follow-up: the bounded
  `startup-context --repair` runtime adapter now forwards the governed
  review-channel `rollover_dir` sibling derived from the managed review root
  when it dispatches repo-owned review-channel actions. That closes the
  immediate refactor regression where bridge-backed status/ensure repair
  crashed on missing runtime-path context before it could classify
  `runtime_missing` or surface the real relaunch boundary.
- 2026-04-09 hookable next-command + feature-branch release-lane follow-up:
  release-lane validation no longer hardcodes CodeRabbit gate lookups to
  `master` when a feature-branch diff routes through `bundle.release`; the
  `check --profile release` gate now resolves the active branch and enables
  commit fallback only off the configured release branch, while keeping the
  release branch strict. The follow-on publish proof also treats unpublished
  local feature-branch SHAs as non-blocking for CodeRabbit pre-push checks:
  if the current SHA is not present in any local remote-tracking ref yet,
  local governed push may proceed and the gate becomes authoritative only
  after publish. The same slice hoists one top-level typed
  `recommended_command` out of `review-channel status` / `doctor`, preferring
  typed doctor or attention recovery commands and otherwise reusing
  `push_decision.next_step_command` so repo-owned hooks and remote-control
  launchers can consume one deterministic next step instead of spelunking
  nested projections.
- 2026-04-09 remote-control prompt/wrapper closure inside the same lane:
  the repo-local Claude phone wrapper now surfaces typed
  `recommended_command` plus `doctor.decision_command` from
  `review-channel status`, prefers that repo-owned review-channel recovery
  path when bootstrap is requested, and only falls back to the full
  `review-channel --action launch` pair when no typed recovery command exists.
  The paired remote-control prompt now starts from the role-bound
  `session-resume --role implementer --format bootstrap` packet and routes
  commit/push through governed `devctl commit` / `devctl push` instead of raw
  git, so the phone-steered Claude session stays on the same typed mutation
  authority path as local repo-owned flows.
- 2026-04-09 recover/bootstrap follow-up inside the same lane: the narrower
  repo-owned `review-channel --action recover --recover-provider claude
  --terminal none` path no longer stops at script generation in governed
  `remote_control`; it now routes through the same detached proof-of-life
  launcher discipline as other headless review-channel starts and waits for
  the current implementer ACK before claiming success. The paired
  `session-resume` source loader now also overwrites stale loaded
  `review_state` payloads with the caller-threaded typed `ReviewState` so
  recover/startup/session-resume reuse one frozen instruction/session truth
  instead of mixing stale compact/current-session text back in.
- 2026-04-10 reviewer-mode takeover follow-up in the same lane: a local
  `reviewer-heartbeat --reviewer-mode single_agent` downgrade now retires the
  detached publisher/reviewer-supervisor runtime before rebuilding status, so
  stale daemon heartbeats cannot reassert `active_dual_agent` metadata and
  push startup-authority / review-status back into relaunch deadlock.
- 2026-04-10 P1/P2 reviewer follow-up in the same lane: `pipeline
  refresh-authorization` now verifies current HEAD before refreshing and
  refuses stale or unavailable HEAD cases, recommending `recover` for stale
  authorizations instead of minting a fresh window for the wrong commit.
  `agent-mind --since-cursor` now avoids the fixed 400 raw-line tail when a
  cursor is present, so decision events survive hundreds of intervening
  low-signal rollout lines before the next poll.
- 2026-03-29 package-layout baseline-debt enforcement closure: the
  `check_package_layout` guard now supports `--fail-on-baseline-debt` with
  optional `--baseline-debt-root` filtering, promoting detected baseline debt
  to a hard CI failure for targeted roots. The tooling and release bundles
  now include `check_package_layout.py --fail-on-baseline-debt
  --baseline-debt-root dev/scripts/devctl/commands`, making the crowded
  `commands/` directory (92 files, max 48; 7 crowded families) a blocking
  violation in default CI lanes instead of silent informational state. This
  closes the ratchet path described in the 2026-03-27 entry: truthful
  baseline-debt reporting now drives hard enforcement on the targeted
  self-hosting hotspot.
- 2026-03-29 package-layout dirty-diff follow-up: the first live conductor
  pass exposed that the new `--fail-on-baseline-debt --baseline-debt-root`
  ratchet was too coarse for local tooling/reviewer loops because it failed
  unrelated dirty worktrees such as bridge-only edits. The guard now keeps
  clean-worktree/adoption-scan enforcement unchanged, but filtered dirty
  working-tree and commit-range runs only hard-fail when the current diff
  actually touches the targeted root. That preserves the `dev/scripts/devctl/commands`
  convergence ratchet for touched hotspot edits without making every local
  tooling pass permanently red on pre-existing baseline debt.
- 2026-03-27 package-layout self-hosting validation follow-up: the recent
  rule-loading extraction into
  `dev/scripts/checks/package_layout/rule_resolution.py` kept the runtime
  architecture pointed the right way, but it also exposed a proof gap in the
  repo's own validation story. The command-level package-layout checks stayed
  green while the support-level tests were still patching the pre-refactor
  `support.py` seam instead of the canonical loaded rule-resolution module.
  The immediate regression is fixed in the test suite; the tracked follow-up
  now lives under `MP-376`: package-layout/internal engine refactors must keep
  the support-layer validation path in the routed default coverage so
  self-hosting proof stays aligned with the canonical seam rather than only
  the public command surface.
- 2026-03-27 governed-push fail-closed closure: `devctl push` now reads
  policy-gated bypass settings from `repo_governance.push.bypass`, reports
  typed push stages (`validation_ready`, `published_remote`,
  `post_push_green`), and stops treating remote publication as equivalent to
  post-push green. The same contract now flows through `sync`, governance
  draft output, and the repo policy itself. Remaining `MP-377` / `MP-376`
  closure is adopter proof and authority-surface compression, not ambiguity in
  branch-push truth.
  so agents and operators do not mistake a remote update for full contract
  success.
- 2026-03-28 push-recovery follow-up: the repo now persists the latest typed
  push result at `dev/reports/push/latest.json`, threads that managed
  artifact through `PushEnforcement`, and teaches `startup-context` to treat
  `published_remote=true` plus `post_push_green=false` as "publication is
  settled; repair the follow-up" instead of "push unresolved". Remaining
  MP-377 closure is the fuller branch/tree-hash `PushPreflightPacket`, not a
  second push authority.
- 2026-04-08 governed-push bypass closure: reverted the temporary
  `repo_governance.push.bypass.allow_skip_preflight=true` repo-policy window
  back to `false` and added a regression that loads the real repo policy so
  the bypass stays closed by default. Clean-tree `startup-context` plus
  `python3 dev/scripts/devctl.py check --profile ci` now prove the current
  snapshot/push authorization lane without the temporary skip-preflight
  escape hatch left open in tree state.
- 2026-04-02 governed-push operator-visibility follow-up: keep the same typed
  publication truth, but make long post-push bundles visibly honest in live
  terminals too. `devctl push --execute` now emits explicit progress notices
  when remote publication is recorded and before each post-push step so
  humans/agents stop inferring "maybe nothing pushed yet" from a quiet audit
  window while the same `published_remote` artifact already proves otherwise.
- 2026-04-04 publish-state projection follow-up: the latest-push artifact was
  already authoritative for startup recovery, but review-channel readiness
  projections could still hide that truth behind `pipeline_unavailable` when
  no live remote-commit pipeline existed or when post-push failed after
  publication. `review-channel status|doctor` now keeps commit-pipeline truth
  when present and otherwise falls back to the matching latest push artifact,
  surfacing `published_remote`, `post_push_green`, `push_report_path`, and
  the recorded follow-up failure reason instead of silently implying a second
  push is needed. The same closure now treats blank approved-target
  identities as valid matches for ordinary branch pushes, so persisted
  publish receipts remain recoverable even when no reviewer-owned target
  identity was attached to the original `devctl push`.
- 2026-04-04 publish-target parity follow-up: the next bounded `MP-377`
  closure on governed push truth is not a new architecture doc. The same
  `latest-push` receipt now has to mean the same thing in startup, doctor,
  event-backed projections, and human-facing push sections: current branch,
  current HEAD, current approved target, and the tracked upstream remote (or
  repo default remote when no upstream exists). Startup/status markdown now
  renders effective current-target truth instead of replaying stale raw
  artifact booleans, and event-backed review-state enrichment now carries the
  same push-enforcement / push-decision parity instead of staying bridge-only.
- 2026-04-04 `devctl dashboard` v2 bounded slice: v1 is landed (commit
  `adb32af`) but under-projects the system. The next slice must replace the
  sparse single-column output with a dense operator dashboard that reads
  all 16 existing JSON artifact surfaces and answers 6 questions on one
  screen: is the loop alive, who owns the turn, what is running, what is
  blocked, what changed recently, what is the next bounded action.
  Implementation order: (1) enrich `DashboardSnapshot` schema with worker
  table, plan progress, publication pipeline with timers, quality summary
  with guard pass/fail counts, audit/proof section, health/daemon status,
  and coordination queue counts; (2) rebuild terminal renderer as dense
  multi-column layout with semantic ANSI colors and compact ASCII
  flowcharts for review/worker/push flows; (3) add `--follow` polling
  with diff-aware refresh; (4) auto-launch in `review-channel launch`,
  `remote-control attach`, and rollover paths; (5) keep portable through
  repo-pack path resolution and `DashboardSnapshot` schema contract.
  Role-neutral naming: Reviewer/Implementer/Worker as primary nouns,
  provider as sublabel. Effective truth first, raw evidence second,
  drill-down path third. 8 research agents completed mapping all data
  dimensions: timers (19,903 events), audit proof (12 surfaces, 136
  governance reviews), analytics (11,457 snapshots over 25 days), worker
  efficiency (tasks/min, stall detection), plan progress (293 MPs, 67.6%
  done), publication pipeline (45 receipts with step timing), session
  health (22 attention states, daemon heartbeats), quality detail (25
  probes, 121 findings, 56.2% cleanup rate). All data already exists as
  JSON artifacts — the problem is bad projection, not missing data.
- 2026-04-04 post-push-green closure intake: the branch is already published
  on `origin/feature/governance-quality-sweep`, and
  `dev/reports/push/latest.json` honestly records `published_remote=true`,
  `post_push_green=false`, and `reason=post_push_bundle_failed`. The next
  bounded `MP-377` slice is therefore not another push attempt; it is to keep
  current-target publication truth aligned across startup/doctor/event/render/
  system-picture surfaces while classifying the remaining
  `check_code_shape --since-ref origin/develop` failures into must-fix-now
  versus explicit debt. Run that slice through the sanctioned review-channel
  topology with `--codex-workers 0 --claude-workers 3` so the branch proves
  planned many-agent execution under conductor-owned state instead of the
  default zero-fanout path.
- 2026-04-09 post-push diff-base reuse follow-up inside the same lane:
  governed push now carries the preflight-resolved `since_ref` forward into
  the post-push bundle instead of hard-resetting follow-up checks to
  `origin/develop` after publication. Existing upstream-backed branches now
  validate only the just-published delta, while first-publish branches still
  use the repo-policy template base. Treat this as the same hookable-truth
  rule the owner chain already wants: hooks, startup packets, and remote-
  control launch surfaces should consume typed next-step / diff-base state
  from repo-owned receipts, not recompute branch literals independently.
- 2026-03-27 repo-entrance/dev-loop adjudication: accepted two additional
  same-lane follow-ups without widening the product roadmap. First, keep the
  root repo entrance split by audience: `README.md` remains the VoiceTerm
  product/user entrypoint while `MP-377` adds a separate platform/developer
  entry surface inside the monorepo and only later promotes that surface into
  the root README of the extracted platform repo. Second, promote
  self-governance from checkpoint budget alone into bounded-slice discipline:
  developer-facing implementer surfaces must keep the human/operator as
  checkpoint/push authority, emit deterministic slice packets for outside
  review, and eventually render "why continue/checkpoint/review/push" from
  typed `DecisionTrace` / `current_session` state rather than from bridge/chat
  prose. Treat this as owner-chain work under `MP-377` / `MP-355`, not as a
  new architecture doc or another audit-only memo.
- 2026-03-27 explanation/learning-path follow-up: accepted the same-lane
  correction that architecture transparency and Python learning need one
  contract-first surface instead of separate lore. The platform should not ask
  AI for unconstrained prose "reasoning"; it should emit a small schema-
  validated decision record with fixed vocabulary (`status`, observed facts,
  triggered rules, rejected options, chosen action, next command,
  uncertainty), then render a junior-dev-readable explanation from that typed
  packet. Pair that runtime work with one platform-owned Python architecture
  guide/decision tree that teaches when to use `dict`, `TypedDict`,
  `dataclass`, boundary-validation models, and `Protocol`, then connects those
  shapes back to repository/service/unit-of-work/dependency-injection patterns
  in plain language. Recommended source spine: Cosmic Python (Ch. 1-6, 8, 13),
  the official typing docs, Pydantic strict-mode/JSON Schema, and FastAPI
  boundary-model docs. Keep Pydantic focused on untrusted or serialized
  boundaries rather than forcing every internal runtime type through it.
  Immediate execution split is explicit now too: do not wait for the full
  Phase-5b `DecisionTrace` artifact before improving operator-facing clarity.
  Use the existing `DecisionPacketRecord`, task-router surfaces, and probe
  best-practice library to land routed-rule `match_evidence`, practice-linked
  why text, plain-language metric explanations, and context-graph/query
  relevance summaries first; then promote the same evidence into the full
  typed provenance family already tracked under `platform_authority_loop`.
- 2026-03-27 deterministic-validation follow-up: accepted the same-lane
  correction that TDD/contract tests can become portable AI trust boundaries,
  but only through the existing runtime/evidence owner chain. The platform
  should add a runner-agnostic validation-contract family, normalize failure
  cases into canonical `Finding` records, execute named `validation_plan`
  selectors before and after AI mutations, and allow `decision_mode` upgrades
  only when the exact finding-scoped validation contract passes. Keep this
  separate from advisory test-quality probes and reject repo-wide coverage-
  threshold shortcuts as the autonomy gate.
- 2026-03-27 scope-capture follow-up: accepted the same-lane architecture
  intake and locked it into tracked plan state before another
  startup pass could narrow the scope away. Keep bridge/latest/chat/status as
  projections over typed `current_session` plus `DecisionTrace`, add a
  minimal `explain-latest` surface, treat validation/test failures as one
  governed evidence family rather than the whole autonomy story, and later
  compile selected `PlanTargetRef` into a typed `PlanExpectationPacket` so
  plan truth is reconciled against observed evidence instead of being
  silently rewritten by runtime drift.
- 2026-03-27 typed-seam/authority follow-up: closed two concrete
  self-governance misses exposed by the explainability rollout instead of
  leaving them as review-only complaints. Startup advisory/push helpers now
  consume typed `PushEnforcement` directly instead of routing fixed-field
  decision logic through `object` + `getattr`, `probe_design_smells` now
  detects first-parameter and multiline-signature `: object` seams, and
  review-channel attention now reports `bridge_contract_error` before
  `checkpoint_required` when `active_dual_agent` truth is already invalid
  because no repo-owned conductors are live. The same same-lane closure now
  also started the bounded hard-enforcement path without inventing a new guard
  family: the dedicated `check_python_typed_seams.py` guard now owns blocking
  enforcement for configured `object`-plus-`getattr` runtime seams, and
  `probe_design_smells` reuses the same scanner so review hints and hard
  policy stay aligned instead of drifting across parallel checker paths.
- 2026-03-27 foundation-first follow-up: accepted the correction that the
  tracked vision still needed its substrate. The same `MP-377` lane now also
  explicitly owns `REPO_ROOT` injection burn-down, git/filesystem adapters,
  typed governance ledger rows, a bounded finding/decision/review aggregate,
  live `validation_plan` execution, failure-case adapters, strict
  contract/guard markers, boundary models, and focused contract-test suites
  so future implementation does not jump to `DecisionTrace` on top of unstable
  foundations.
- 2026-03-27 sequencing follow-up: keep that same authority-loop work ordered
  internally. Phase 5b foundations land first; only then widen into
  `DecisionTrace`, typed `current_session` projection, `explain-latest`, and
  `PlanExpectationPacket`, with closure telemetry/self-governance last unless
  a plan-visible blocker explicitly forces a different order.
- 2026-03-27 governed-push session-lifetime fix: the shared `devctl`
  live-output runner now stops following inherited stdout lifetime once the
  parent push/post-push command has exited, after a short bounded drain for
  buffered lines. This closes the "remote already updated but local push
  session looks wedged" failure shape exposed during the authority-leak
  tranche checkpoint push and keeps governed push completion tied to the real
  command contract instead of detached descendant pipe ownership.
- 2026-03-28 attention priority fix: `REVIEW_FOLLOW_UP_REQUIRED` now
  outranks `CHECKPOINT_REQUIRED` in the attention chain so reviewer-turn
  signals are not hidden behind generic checkpoint state. Also: `ensure`
  refreshes stale heartbeats for inactive modes. Regression test added.
- 2026-03-28 context-graph output honesty: `context-graph --query` no longer
  renders the global Hot Index Summary on zero-match results. Fix in
  `dev/scripts/devctl/context_graph/render.py`. Tracked in
  `dev/active/platform_authority_loop.md`.
- 2026-03-28 MP-377 code-shape modularization: split 7 self-hosting files
  that exceeded the Python 350-line soft limit into 14 focused modules.
  `bridge_projection` -> `bridge_projection` + `bridge_sanitize`;
  `policy_runtime` -> `policy_runtime` + `policy_runtime_checks`;
  `startup_context` -> `startup_context` + `startup_context_render`;
  `check_router_constants` -> `check_router_constants` + `check_router_resolve`;
  `review_channel_bridge_render` -> `review_channel_bridge_render` +
  `review_channel_bridge_render_sections`; `core` -> `core` + `session_probe`;
  `push_policy` -> `push_policy` + `push_policy_parse`. All re-export public
  symbols for backward compatibility; `check_code_shape` working-tree is green
  with 0 violations. Prevention pattern: extract private helper clusters to
  sibling modules while keeping public API in the original module.
- Current deterministic self-governance closure rule after the 2026-03-21
  guard audit: do not treat more guard count or richer graph semantics as
  progress while typed/runtime authority still lies. First close the cheap
  truth gaps (`ActionResult.status` business-state drift in `vcs.push`,
  `context-graph` confidence type mismatch, and advisory-only mypy on the
  `dev/scripts/devctl` lane), then add narrow deterministic enforcement for
  contract-value domains, plan/runtime parity, authority-source integrity, and
  dead authority seams. Keep ZGraph / `context-graph` generated-only until
  those fixes plus the startup/path/review authority cutover are green.
- Current native-N-agent follow-up in the same neighborhood: packet routing,
  `TandemProfile.implementers`, the append-only event lane, and
  `autonomy-swarm` already scale past two agents, but the review-channel
  middle layer still hardcodes provider-shaped queue/bridge/liveness fields
  (`pending_codex`, `pending_claude`, `claude_ack`, `codex_poll_state`,
  fixed agent-id allowlists). Treat the current 8+8 loop as
  conductor-managed multi-agent operation; native N-agent current-session /
  packet-lane authority stays tracked follow-up work under MP-355 and MP-377.
- Current blocking follow-up after that closure slice: replace checkout-path-
  based finding identity with stable repo identity + repo-relative path, add
  the first hard-guard-to-`Finding` normalization seam so blocking and
  advisory evidence stop using different ontologies, extend the contract
  catalog/closure guard to the remaining `P0` families (`ActionResult`,
  `CommandGoalTaxonomy`, `RepoMapSnapshot` / `MapFocusQuery` /
  `TargetedCheckPlan`, `FixPacket`), and keep packaging / adoption proof plus
  tracker-hygiene follow-ups such as the `MASTER_PLAN` state/changelog split
  in `P1`.
- Current architecture caution: `platform-contracts` now covers the already-
  real `ActionResult` / `Finding` / `DecisionPacket` rows, so the spine is no
  longer missing from zero, but it is still not closed or authoritative for
  the whole app. The review ledger still duplicates checkout-path-based
  identity through `governance_review_log.py`, and the current frontend
  clients still converge mostly through emitted projections and compatibility
  adapters instead of one fully closed live backend/service protocol.
- Audit-intake sequencing rule: accepted 2026-03-17 whole-system audit items
  reinforce the current `P0 -> P1 -> P2` order rather than replacing it.
  Close finding identity and guard/`Finding` evidence convergence first, then
  do packaging / install-surface work and tracker compaction, then finish the
  PyQt6/operator-console seam consolidation over the shared backend.
- Whole-system audit alignment rule: `dev/guides/SYSTEM_AUDIT.md` is reference evidence, not
  a second tracker or spec. Only its code-backed blocker tranche changes the
  live execution order: daemon attach/auth hardening, autonomy authority
  hardening, evidence-integrity closure, and self-governance coverage move
  ahead of the remaining authority-loop spine. The rest of the 2026-03-19
  audit remains corroborating reference until its stale counts and internal
  contradictions are cleaned up, after which the tracked order still stays:
  bounded `startup-context` / `ContextPack`, hot/warm/cold session context,
  repo-pack/path-authority closure, then follow-on review-channel /
  guard-boilerplate simplification.
- Accepted semantic-context direction for `MP-377`: keep canonical pointer
  refs / typed anchors as authority, build the first native `devctl`
  `context-graph` / generated `HotIndex` surfaces on top of the existing
  repo-understanding `map` backend, and keep `ConceptIndex` / any
  ZGraph-compatible encoding generated-only. This stays inside the
  `ContextPack` / startup-boundary plan, not as a new MP or a second memory
  authority.
- `MP-377` Phase 6 context-graph implementation landed (Session 43): 7-file
  package at `dev/scripts/devctl/context_graph/`, 4 output modes (bootstrap,
  query, mermaid, dot), ZGraph concept layer with typed edges
  (`documented_by`, `related_to`, `contains`). Startup-authority contract
  updated through the canonical policy chain.
- Accepted next bounded use of that same context-graph slice: policy-driven
  context escalation for live agents. Conductors now get explicit
  unread-scope / failed-attempt / blast-radius query rules plus a preloaded
  lane packet, `loop-packet` / autonomy checkpoints now carry a bounded
  recovery packet forward, and the Ralph CodeRabbit fixer now injects the
  same packet into its Claude prompt. Keep this read-only and generated; it
  is recovery/navigation, not a second authority store.
- Immediate sequencing rule for that graph work: checkpoint the current green
  bounded context-escalation slice before widening graph scope again. Treat
  the passing CI/doc-governance state as the first stable Phase-6
  context-recovery proof, not as permission to pile richer graph work into
  the same mixed tree.
- Next `MP-377` graph order after that checkpoint: honest typed plan/doc/
  command edges plus first richer typed relation families and artifact-backed
  live routing/scoring inputs first (shared scan hygiene,
  `file_topology.json` / `review_packet.json` ingestion, shared hotspot
  scoring, severity-aware ranking, initial `guards` / `scoped_by` /
  operation-semantic producer-consumer paths, staged query filtering,
  bounded multi-hop inference, and a small bidirectional hot-query cache),
  then the remaining backend instruction emitters (review-channel
  promotion/event projections and fresh `swarm_run` prompts), then a
  validation matrix across review-channel / autonomy / Ralph, then richer
  graph capabilities such as transitive blast radius,
  review/governance/autonomy/workflow/config/test edges, and
  agent-authored graph queries.
- Follow-on graph/productization lane after those honesty/intake closures:
  add one portable `architecture-review` command/profile that aggregates the
  same graph, probe, guard, and contract evidence into one system-level health
  report instead of relying on ad hoc grep/manual synthesis. Keep it
  repo-pack-driven, JSON-canonical, and projected into audience-specific views
  rather than inventing a second architecture-analysis stack.
- Follow-up: `devctl` organization/readability cleanup — crowded roots
  (`dev/scripts/devctl/`, `commands/`, `tests/` all over freeze thresholds),
  naming/module convention consistency, and a portable naming-convention
  report/guard path. Current `package_layout` guards hold via freeze mode
  but do not drive cleanup. Keep this as a tracked self-hosting follow-up
  after the checkpointed graph slice rather than mixing it into the same
  implementation batch.
- Audit-integration rule: if a whole-system audit finding is accepted, rewrite it
  into canonical execution state in `MASTER_PLAN`, the relevant active plan
  doc, and maintainer docs when process policy changes. Do not keep live work
  pointing back to `dev/guides/SYSTEM_AUDIT.md` after the canonical docs have
  been updated. Once its accepted items are fully absorbed or explicitly
  rejected, retire the moved audit copy instead of keeping a shadow roadmap.
- Review-ledger caution: a zero false-positive rate is not a success metric on
  its own. Read `false_positive_rate_pct` together with reviewed-vs-
  unreviewed coverage, per-family disposition mix, and time-to-disposition
  before drawing quality conclusions from the ledger.
- Current startup-authority gap: the repo already has partial intake pieces
  (`AGENTS.md` bootstrap order, `check-router`, `orchestrate-status`,
  `docs-check`, `render-surfaces`, `swarm_run`), but not one enforced,
  repo-pack-driven startup path that reads the active plan registry, inspects
  the current git diff, maps the slice to MP scope, and routes accepted
  decisions/findings into the correct plan docs or ledgers automatically.
  Treat that as architecture work for the extracted platform, not as a
  VoiceTerm-only operator habit.
- Current governance-quality gap: plan/startup evidence still needs a
  meta-layer that can report not just code findings but governance findings.
  The platform should be able to say whether every guard has tests, every
  probe has tests, every registered guard runs in CI, every exception entry
  covers a real violation, and every workflow has a timeout. JSONL writers
  and evidence collectors also need integrity checks so a malformed row or
  silent skip is surfaced as a loss of evidence rather than disappearing from
  the record. When the system encodes large static tables as Python
  tuples/functions instead of policy or JSON/YAML config, that should surface
  as a separate data-as-code smell.
- Portable-engine framing: `MP-376` is the reusable engine/adoption layer
  and `MP-377` is the product/repo-governance platform. The engine should
  expose reusable guards, probes, evidence contracts, and startup artifacts;
  repo-governance should own per-repo policy, preset, and adoption routing.
  Keep that split explicit so portable machinery does not absorb product
  authority and product scope does not leak into the engine contract.
- Self-hosting simplification rule: once the blocker tranche and `P0` spine
  are green, run one governance-engine consolidation pass on plan overlap,
  bootstrap-token burden, review-channel sprawl, repeated checker/reporting
  boilerplate, and spec-vs-reality labeling so the platform becomes evidence
  that its own rules improve the codebase operating them.
- Self-hosting structure-governance follow-up: that consolidation pass must
  extend the existing package-layout / compatibility-shim governance into a
  broader repo-owned structure policy over `devctl` root budgets, parser and
  command placement, subsystem file-count budgets, source-of-truth ownership,
  active-doc lifecycle, and shim expiry so the engine can block the same
  accretive sprawl it currently reports.
- Documentation-authority follow-up: this self-hosting pass must also deliver
  one unified docs system for the platform itself. The repo needs governed
  doc classes/lifecycles, bounded hot/warm/cold AI context, active-plan and
  startup-token budgets, canonical markdown schema + anchor rules, and
  docs-governance enforcement so scope stops getting lost in doc sprawl.
- Documentation-authority first-step rule: do not start this cleanup as
  another prose-only effort. The first bounded operator/AI entrypoint should
  be a repo-owned `devctl` command that scans governed markdown, emits the
  current doc registry/authority state, reports format drift and over-budget
  docs, and proposes consolidation targets before `--write` remediation lands.
- Full `dev/guides/SYSTEM_AUDIT.md` intake rule: treat the audit's whole tiered action
  plan as canonical intake that must be mapped into the existing plan system,
  not left in a parallel document. Required mapping: Tier `-1` security ->
  blocker tranche; Tier `0` evidence/feedback -> startup/evidence/context
  closure; Tier `1` bootstrap compression -> hot/warm/cold startup context;
  Tier `2` memory/sessions -> `ContextPack` + memory bridge; Tier `3`
  structural debt -> self-hosting simplification; Tier `4` surface
  simplification -> command/workflow consolidation; Tier `5` portability ->
  repo-pack/packaging/adoption proof; Tier `6` black-box strengthening ->
  missing guards/probes + governance-ledger closure; Tier `7` test hardening
  -> guard/runtime/integration coverage.
- Portability-sequencing rule: do not wait until final packaging work to prove
  the authority loop detaches from VoiceTerm. Once startup authority plus one
  report-only runtime slice exist, run an intentionally rough second-repo
  smoke test through repo-pack selection, one typed action, one blocking
  check, one finding/evidence write, and one shared status/report render so
  hidden VoiceTerm assumptions fail early instead of in Phase 7 polish.
- Path-authority rule: do not replace `active_path_config()` sprawl with one
  new giant hidden authority object. `RepoPathConfig` must decompose into
  bounded groups such as repo roots, artifact/report roots, plan/docs
  authority paths, memory roots, and review/bridge paths so portable modules
  only learn the path family they actually need.
- Proof-scoreboard rule: the portable-governance proof should stay small and
  legible. At minimum track time-to-first-governed-run for a new repo, hard-
  guard blocked-change count, reviewed false-positive rate, quality/cost per
  successful fix, and whether a second repo works without core-engine
  patches.
- Proof-gate rule: keep four named maturity gates explicit across `MP-376` /
  `MP-377`. `Gate 1: not ready` means self-hosting only; `Gate 2: POC ready`
  means one second-repo bootstrap/startup/guard/finding path works with no
  core-engine patches; `Gate 3: early release` adds the installable
  entrypoint plus reviewed setup/onboarding flow and repeatable adopter proof;
  `Gate 4: productizing` adds broader adapters, release-artifact governance,
  richer runtime UX, and benchmarked collaboration/value proof.
- Next coherence-layer follow-up after the current `P0` blockers: widen the
  existing naming-consistency seed into a portable, repo-policy-backed
  naming/organization enforcement layer that can catch cross-file naming
  drift, contract-field naming drift, import-pattern drift, and structural
  template drift without hardcoding VoiceTerm-specific conventions into the
  engine. Start advisory where calibration is unknown; promote only after
  ledger-backed review evidence says the rules are accurate.
- Follow-up after that intake gap is explicit: add one repo-neutral,
  repo-pack-aware work-intake / startup-authority surface so AI agents and
  humans can derive "what plan is active, what changed, what bundle applies,
  and where accepted outcomes must be recorded" from the same executable
  model instead of reconstructing it from prose plus operator memory.
- Current plan amendment from the 2026-03-19 authority-loop audit: do not
  treat repo-pack definition alone as sufficient. The execution scope must
  also include the full runtime rewrite of module-level
  `active_path_config()` freezes, bundle/check extensibility, platform-wide
  contract versioning, proof-pack/evaluation schema, and provenance closure
  for findings/runs/policy state.
- Current transition-sequencing amendment from the 2026-03-19 validator pass:
  do not freeze runtime review identity before the evidence identity scheme is
  unified. Treat the evidence work as Phase `5a` (identity freeze in parallel
  with repo-pack activation and plan registry) plus Phase `5b`
  (provenance/ledger closure after the first runtime slice).
- Current migration-governance amendment from the same pass: Phase 2 must use
  a compatibility-first repo-pack rollout, the legacy governance-review
  ledger needs backfill/upgrade coverage before hard schema enforcement,
  `MP-359` path cleanup is a dependency of the repo-pack rewrite, and Phase 7
  proof criteria must distinguish portable guards from VoiceTerm-specific
  repo-structure guards.
- Current planning-review amendment from the same pass: repo-neutral plan
  hardening must flow through `PlanRegistry` + `PlanTargetRef` +
  `WorkIntakePacket`, reuse the review-channel packet/reducer path for
  plan-gap/patch/ready packets, and resolve canonical markdown targets by
  registry-generated stable anchors rather than brittle surrounding prose or
  raw line numbers. Planning review also needs intake-backed writer leases,
  explicit mutation ops, and a minimum bootstrap artifact set for non-
  VoiceTerm repos. Do not add a second authoritative `plan.md`.
- Current final architecture adjudication from the combined 2026-03-19
  Codex runtime slice plus Claude architecture pass: keep
  `WorkIntakePacket` and `CollaborationSession` as separate `P0`/`P1`
  contracts, keep intake-backed writer leases as the authority model for
  canonical plan/session mutation, and treat `version_counter` /
  `expected_revision` / `state_hash` checks as supplemental freshness guards
  rather than replacements for designated writer ownership. Startup may auto:
  inspect repo state, refresh stale authority artifacts, resume exactly one
  valid session, mark stale runtime/session attachment as `runtime_missing`
  or emit one bounded repair receipt, and emit one bounded intake/resume
  packet. Startup must not auto: guess among multiple active
  plans, launch conductors, or promote itself into `active_dual_agent`
  without explicit operator/policy choice. Phase 7 proof now also needs a
  replayable single-agent vs multi-agent comparison with adjudicated
  findings and quality-to-cost telemetry instead of asserting reviewer-loop
  value informally.
- Startup-token burden is now explicit product debt: the repo should stop
  re-deriving the same maintainer context every session and instead move to a
  cached repo-intelligence layer (`plan snapshot`, `command map`,
  `convention snapshot`, `map snapshot`, targeted-check hints, filtered probe
  view) plus one bounded `startup-context` / `work-intake` surface that
  refreshes only when git state, policy, or active-plan state actually
  changes.
- Memory-integration correction: the Rust Memory Studio already ships a real
  v1 substrate (`ContextPack`, `SurvivalIndex`, deterministic retrieval
  queries, JSONL persistence, in-memory index, staged SQLite schema), so the
  startup-authority path should compose with that system rather than rebuild a
  second unrelated memory stack. The open gap is integration: governance
  evidence and cached repo-intelligence artifacts still do not flow into one
  shared bounded packet with memory exports, and Memory Studio is not yet a
  standalone startup authority by itself.
- Bridge task: add one concrete governance-to-memory bridge that writes
  findings, run records, and repo-intelligence snapshots into the Rust memory
  substrate and lets `startup-context` / `master-report` consume that same
  bounded packet instead of stitching the evidence together ad hoc.
- Architectural Knowledge Base direction accepted (2026-03-17): the platform
  should provide a topic-keyed, SQLite-backed knowledge store so AI agents
  retrieve bounded architectural context by topic chapter instead of loading
  entire plan documents. Auto-capture scripts flag architecturally significant
  events (contract changes, guard/probe registration, plan milestones, schema
  migrations). Each topic chapter has a token budget and exports as JSON into
  the existing `ContextPack` system. The `ConceptIndex` / ZGraph navigation
  artifact maps topic dependencies for graph-traversal-based selective
  retrieval. `P0` prerequisite: activate the SQLite runtime and freeze the
  evidence-to-memory bridge. `P1` deliverable: full topic-keyed knowledge
  base with auto-capture, chapter budgets, and ConceptIndex integration.
  Architecture details in `dev/active/ai_governance_platform.md` under
  "Architectural Knowledge Base (Topic-Keyed AI Context)".
- Bootstrap/adoption should also stop starting from raw policy JSON plus
  scattered prose only. Add one reviewed repo-local governance contract
  surface (`project.governance.md` as the current working name) that AI can
  draft deterministically from repo facts, humans can finish with priorities /
  debt / exception intent, and later startup/policy flows can consume as one
  bounded source of truth.
- Accepted setup-flow shape: `governance-draft` scans repo structure,
  languages, test/CI shape, import topology, and current quality baselines to
  draft that contract; human review/approval fills the non-deterministic
  fields; `governance-bootstrap` and/or a later `governance-init` materialize
  repo policy and startup surfaces from the approved contract; later drift
  scans should suggest contract updates when the repo no longer matches the
  declared layers/roots/rules.
- Recursive convergence thesis is now explicit architecture work: the system
  already re-measures fixes in pieces (`guard-run`, `probe-report`, Ralph
  loops), but it still lacks one cached aggregate evidence surface
  (`master-report`) and one fixed-point orchestration surface (`converge`) for
  the whole guard/probe/ledger/convention stack. Do not treat that loop as
  "done" until the remaining artifact families are schema-versioned and the
  aggregated evidence contract is stable.
- Governance-completeness is part of that convergence surface: `master-report`
  should aggregate not only code findings but meta-findings about guard/test/
  CI/exception coverage, and `converge` should be able to drive the platform
  toward a fixed point where the governance layer itself is internally
  consistent.
- 25-agent architecture audit completed (2026-03-17): every major surface
  audited (Rust A-, Python governance B+, guards B, probes B-, operator
  console B+, CI B-, config A, docs A-, command UX B, portability 62/100,
  error handling B, AI bootstrap C+, self-consistency C). Concrete gaps
  closed in `ai_governance_platform.md` next-action items 30-33:
  `check_governance_closure` meta-guard, JSONL/exception immediate fixes,
  command UX standardization, CI workflow timeouts. Plans are now
  execution-ready.
- Accepted navigation-layer shape: add one deterministic concept index
  (`ConceptIndex`, optionally emitted in a ZGraph-compatible encoding) above
  the contract/policy/plan/map registry stack so startup/work-intake can route
  by concepts without rereading the whole repo. Keep that index generated from
  canonical contracts, plans, command taxonomy, and guard/probe metadata; do
  not let semantic/vector retrieval become the only authority.
- Startup-surface rule: keep one startup artifact family only. `startup-
  context`, `WorkIntakePacket`, and later `ContextPack` are the canonical
  startup/session packets; do not introduce a parallel `bootstrap-context`,
  second manifest family, or free-form session compass that can drift from the
  tracked authority chain.
- Knowledge-base sequencing rule: the architectural knowledge-base / chapter /
  ConceptIndex direction is valid, but it stays behind the current `P0`
  contract/evidence freeze. Immediate priority is to fix the concrete defects
  surfaced by the first governance-quality-feedback attempt: orphan library
  without CLI/artifact wiring, per-check scoring keyed too loosely, canonical
  `ReviewState` payload still carrying compatibility extras, Halstead file
  paths still absolute, and missing dedicated tests for the new package.
  Treat those as the next bounded execution slice before any broader
  knowledge-base capture/UX work.
- Quality-feedback scoring direction: do not treat the first single composite
  maintainability score as the final product contract. The repo-aligned target
  is a transparent multi-lens scorecard with explicit evidence coverage:
  `CodeHealthScore`, `GovernanceQualityScore`, and `OperabilityScore`, plus at
  most one secondary gated overall summary. Do not use median as the top-level
  cross-lens aggregator because it can hide a red lens; if robustness is
  needed, apply median only within one lens across related sub-metrics.
- Naming/convention ownership rule: keep `MP-267` limited to repo-local
  cohesion cleanup. Track the portable convention engine (`naming-scan`,
  `naming-report`, repo-policy schema, reusable naming/organization
  guards/probes) in `portable_code_governance.md`, and track startup/work-
  intake integration plus command-goal taxonomy in
  `ai_governance_platform.md`.
- Current probe-signal calibration: the canonical `devctl probe-report` output
  on this tree is dominated by Python readability/organization work rather
  than Rust ownership/concurrency work (`107` findings total, `98` Python,
  led by `probe_identifier_density` and `probe_blank_line_frequency`). Treat
  that as slice-specific cleanup pressure that should drive filtered
  startup/intake views, not as a claim that the repo's global architecture
  risk is primarily Python readability debt.
- Shared-state parity follow-up: Rust↔Swift daemon/mobile wire names already
  have an explicit guard, but equivalent Python runtime models remain
  unguarded copies. Keep the missing Rust daemon ↔ Python runtime parity guard
  in the `MP-377` contract-closure lane until the shared state/service seam is
  enforced across all consumers.
- Probe guidance still needs one authoring contract: the current probe family
  emits useful `ai_instruction` content, but authoring style is inconsistent
  across families (per-signal dicts, severity dicts, and inline constants).
  Treat a shared instruction template/keying rule as part of AI-usability
  hardening, not as optional polish.
- Current cross-surface convergence gap: the typed runtime direction is real,
  but the repo still emits multiple review/control shapes across backend and
  clients. `ReviewState` is still produced in different bridge-backed and
  event-backed forms, the live review loop still depends on `bridge.md`
  as temporary authority, the review-channel `project_id` is still derived
  from absolute checkout paths, the current mobile relay guard can return
  green with zero matched Rust↔Swift pairs, and PyQt6/iPhone still consume
  compatibility payloads before canonical typed state.
- Accepted next bounded cross-surface order: (1) make bridge-backed and
  event-backed review-channel producers emit one exact `ReviewState` contract
  and move review-channel identity onto stable repo identity instead of
  absolute paths; (2) add the missing daemon-state contract plus executable
  Rust ↔ Python ↔ Swift parity guard so the mobile/backend seam stops
  reporting false-green coverage; (3) migrate Operator Console and iPhone to
  typed-state-first consumers with markdown / `controller_payload` /
  `review_payload` fallback-only behavior; (4) only then keep burning down
  repo-pack path leaks, local risk bucketing, and hard-coded CLI argv
  contracts in surface code.
- Theme and Memory remain active tracked work, but they are not the repo's
  current top-level strategic lane while `MP-377` `P0` contract-freeze is
  active.
- Repo-wide status/read-order rule: after this snapshot, read
  `dev/active/ai_governance_platform.md` for current strategic context and use
  Theme/Memory/operator/mobile docs only for scoped implementation detail.
- Execution mode: prioritize platform extraction, runtime-authority cleanup,
  and cross-client parity; keep unrelated product-lane work maintenance-only
  unless it directly supports that sequence.
- Maintainer-doc clarity update: `dev/DEVELOPMENT.md` now includes an end-to-end lifecycle flowchart plus check/push routing sections while `AGENTS.md` remains the canonical policy router.
- Tooling docs-governance update: `devctl docs-check --strict-tooling` now enforces markdown metadata-header normalization for `Status`/`Last updated`/`Owner` blocks via `check_markdown_metadata_header.py`.
- External publication governance update: `devctl` is gaining a tracked
  publication-sync surface so external papers/sites can declare watched source
  paths, emit stale-publication drift reports, and surface hygiene warnings
  when repo changes outpace synced public artifacts.
- Loop architecture clarity update: `dev/ARCHITECTURE.md` and
  `dev/DEVELOPMENT.md` now document the custom repo-owned Ralph/Wiggum loop
  path and the federated-repo import model in simple flowchart form.
- Continuous swarm hardening kickoff: `dev/active/continuous_swarm.md` now
  tracks the local-first Codex-reviewer / Claude-coder continuation loop,
  launcher modularization, peer-liveness guards, context-rotation handoff, and
  the later proof-gated template-extraction path.
- Desktop operator console prototype update:
  `dev/active/operator_console.md` now tracks a bounded optional PyQt6
  VoiceTerm Operator Console wrapper over the existing Rust runtime and
  `devctl` control surfaces. The active plan now treats this as a repo-aware
  desktop controller shell over typed repo-owned commands, workflow guidance,
  and bounded AI assist, but still not as a replacement execution authority or
  second control plane.
- Loop comment transport hardening update: shared workflow-loop `gh` helpers now
  avoid invalid `--repo` usage for `gh api` calls so summary-and-comment mode
  can publish and upsert commit/PR comments reliably.
- Audit-remediation update: Round-2 high-severity audit fixes landed for prompt
  detection hot-path queue behavior, transcript merge-loop invariants,
  persistent-config duplication reduction, and devctl release/comment/report
  helper hardening with expanded unit coverage.
- Runtime cleanup update: startup splash logo coloring now uses a single
  theme-family accent (no rainbow line rotation), and the stale orphan
  `rust/src/bin/voiceterm/progress.rs` module has been removed.
- Theme Studio maintainability cleanup update: home/colors/borders/components/
  preview/export byte handling now routes through page-scoped helper functions
  in `theme_studio_input.rs`, with runtime style-adjustment routing split into
  focused helper paths; follow-up dedup also centralized vertical-arrow page
  navigation + runtime override cycle wiring so page handlers avoid repeated
  dispatch scaffolding. Theme Studio suite and full CI profile remained green.
- Theme Studio readability follow-up update: `theme_studio/home_page.rs` now
  uses a dedicated row-metadata struct with static tip strings (instead of
  per-row tip `String` allocations), and writer-state test-only timing
  constants were moved out of `writer/state.rs` production scope into
  `writer/state/tests.rs` so runtime modules stay focused on shipped code.
- CI compatibility hotfix update: release-binary workflow runner labels now use
  actionlint-supported macOS targets, latency guard script path resolution now
  supports `rust/` with `src/` fallback, and explicit `devctl triage --cihub`
  opt-in now preserves capability probing when PATH lookup misses the binary.
- Release workflow stability update: `release_attestation.yml` action pins were
  refreshed to valid GitHub-owned SHAs, and `scorecard.yml` now keeps
  workflow-level permissions read-only with write scopes isolated to the
  scorecard job so OpenSSF publish verification succeeds.
- Release preflight auth stability update: `.github/workflows/release_preflight.yml`
  runtime bundle step now exports `GH_TOKEN: ${{ github.token }}` so
  `devctl check --profile release` can run `gh`-backed release gates in CI.
- Release governance update (2026-03-09): the current pre-release audit
  showed that shipping the mobile/control-plane tranche cleanly requires full
  canonical-doc coverage, not just changelog plus a subset of guides.
  Maintainer docs (`AGENTS.md`, `dev/guides/DEVELOPMENT.md`,
  `dev/history/ENGINEERING_EVOLUTION.md`) and canonical user docs
  (`QUICK_START.md`, `guides/TROUBLESHOOTING.md`) now carry explicit release
  notes for the mobile app/install/control-plane path, and the release bundle
  expectation is that `check_mobile_relay_protocol.py` remains green so Rust,
  Python, and iOS payload contracts ship together.
- Release preflight SARIF permission update:
  `.github/workflows/release_preflight.yml` preflight job now grants
  `security-events: write` so zizmor SARIF uploads can publish to code scanning.
- Release preflight zizmor execution update:
  `.github/workflows/release_preflight.yml` now sets zizmor
  `online-audits: false` to prevent cross-repo compare API 403 failures from
  blocking release preflight.
- Release preflight security-scope update:
  `.github/workflows/release_preflight.yml` now runs
  `devctl security` with `--python-scope changed` and the same resolved
  `--since-ref/--head-ref` range used by AI-guard so preflight enforces
  commit-scoped Python checks instead of full-repo formatting backlog, and it
  avoids hard-failing on repository-wide open CodeQL backlog in release
  preflight; `cargo deny` remains blocking while `devctl security` report
  output is advisory evidence in that lane.
- Compat-matrix parser resilience update: compatibility/naming guard scripts now
  share a minimal YAML fallback parser so tooling CI and local checks stay
  deterministic in minimal Python environments without `PyYAML`.
- Compat-matrix parser fail-closed update: malformed inline collection scalars
  in fallback mode now raise explicit parse errors instead of silent coercion.
- Tooling security hardening update: `devctl` loop/mutation/release helper
  defaults now resolve temporary artifact paths via the system temp directory
  API instead of hardcoded `/tmp` literals, satisfying Bandit `B108` checks in
  release-security gates.
- Control-plane simplification update: MP-340 is now Rust-first only (Rust
  overlay + `devctl` + phone/SSH projections). The optional `app/pyside6`
  command-center track is retired from active execution scope.
- CI lane compatibility update: Rust CI MSRV lane now uses toolchain `1.88.0`
  to match current transitive dependency requirements (`time`/`time-core`);
  CI/docs references were synchronized to the new lane contract.
- MP-346 checkpoint update: `CP-016` automated continuation rerun is captured
  at `dev/reports/mp346/checkpoints/20260305T032253Z-cp016/`; operator
  release-scope matrix update is applied (IDE-first `4/4` required cells:
  Cursor+Codex, Cursor+Claude, JetBrains+Codex, JetBrains+Claude), with
  `other` host and `gemini` baseline checks deferred to post-release backlog.
- MP-346 architecture-audit status update (2026-03-05): IDE-first manual
  matrix closure requirement is complete (`4/4`), and no additional MP-346
  runtime/tooling blockers remain in the current non-regression rerun.
- MP-346 closure-followup update (2026-03-05): prior shape/duplication blockers are
  resolved via check-router/docs-check helper decomposition and duplication
  evidence is refreshed (`dev/reports/duplication/jscpd-report.json`,
  `duplication_percent=0.32`, `duplicates_count=14` after latest cleanup pass);
  closure non-regression rerun is green and the
  prior physical-host manual matrix `7/7` gate is superseded by the IDE-first
  release-scope matrix closure (`4/4`) recorded in `CP-016`.
- MP-347 verification refresh (2026-03-05): closure non-regression command pack
  row `2331` was rerun end-to-end and remains green after canonicalizing
  duplication-audit helper ownership and removing stale archive path literals
  from active docs/changelog.
- MP-347 guard-utility expansion update (2026-03-09): `devctl report` now
  supports `--python-guard-backlog` with ranked hotspot aggregation across
  `check_python_dict_schema`, `check_python_global_mutable`,
  `check_python_design_complexity`, `check_python_cyclic_imports`,
  `check_parameter_count`, `check_nesting_depth`, `check_god_class`,
  `check_python_broad_except`, and `check_python_subprocess_policy`, so Python
  clean-code debt can be burned down in priority order before stricter lane
  promotion.
- MP-347 broad-except hardening update (2026-03-09):
  `check_python_broad_except.py` now treats bare `except:` handlers as
  broad-except policy violations, and newly added fail-soft plotting/telemetry
  paths in devctl autonomy/data-science helpers now carry explicit
  `broad-except: allow reason=...` rationale comments.
- MP-347 mutable-state hardening update (2026-03-09):
  `check_python_global_mutable.py` now also enforces non-regressive growth of
  mutable default argument patterns (`[]`, `{}`, `set()/list()/dict()` style
  defaults) so Python mutable-state pitfalls are blocked even when `global`
  keywords are not involved.
- MP-347 suppression-debt update (2026-03-11): `check_python_suppression_debt.py`
  now enforces non-regressive growth of Python lint/type suppressions
  (`# noqa`, `# type: ignore`, `# pylint: disable`, `# pyright: ignore`)
  using tokenized comment scanning, and the portable Python preset now enables
  it by default so the same engine can block new suppression debt here or in
  another repo without hard-coded VoiceTerm path logic.
- MP-347 default-evaluation hardening update (2026-03-11):
  `check_python_global_mutable.py` now also blocks net-new function-call
  default arguments plus dataclass fields that evaluate mutable or callable
  defaults eagerly instead of routing through `field(default_factory=...)`, so
  the portable Python guard stack now covers the next default-argument trap
  slice without needing a second overlapping guard id.
- MP-347 portability hardening update (2026-03-11):
  `quality_policy.py` now resolves per-guard config payloads, standalone guard
  scripts can read those configs through `check_bootstrap.py`, and
  `devctl quality-policy` plus `devctl check --quality-policy` now surface and
  propagate the same policy-owned settings. VoiceTerm-specific `code_shape`
  namespace/layout rules moved out of the portable engine and into the
  repo-owned preset so another repo can reuse the same guard without hidden
  path assumptions.
- MP-347 portable complexity/import update (2026-03-11):
  `check_python_design_complexity.py` now blocks net-new branch-heavy or
  return-heavy Python functions using policy-owned thresholds (with a
  conservative portable default that repo policy can tighten), and
  `check_python_cyclic_imports.py` now blocks net-new top-level local import
  cycles with repo-policy allowlists for known transitional debt. Both guards
  are registered in the portable Python preset, catalog, bundles, workflows,
  and Python backlog report so the next portable hard-guard backlog narrows to
  Rust `result_large_err` / `large_enum_variant`.
- MP-376 portable governance execution-doc update (2026-03-11):
  added `dev/active/portable_code_governance.md` to track the broader
  reusable code-governance-engine direction explicitly: engine vs repo-policy
  boundaries, measurement/data-capture goals, off-repo snapshot/export needs,
  and the eventual multi-repo pilot rollout. This keeps the strategic
  portability/evaluation goal from being scattered across review-probe log
  entries alone.
- MP-377 reusable AI governance platform kickoff (2026-03-12):
  added `dev/active/ai_governance_platform.md` to separate the bigger product
  extraction problem from the portable-governance-engine plan. `MP-376` stays
  focused on guards/probes/policy/bootstrap/export/evaluation, while `MP-377`
  now owns the broader reusable platform architecture: shared runtime/action
  contracts, repo-pack/adopter boundaries, frontend convergence across CLI /
  PyQt6 / overlay / phone surfaces, and the path toward VoiceTerm becoming a
  first consumer of an installable AI-governance platform instead of the place
  where the whole system remains embedded.
- MP-377 runtime-contract expansion update (2026-03-12):
  `ControlState` is no longer the only executable runtime seam. The new
  `dev/scripts/devctl/runtime/review_state.py` contract now normalizes
  review-channel `review_state.json` and `full.json` artifacts into typed
  session/queue/bridge/packet/registry state, and the Operator Console
  review/session/collaboration readers now consume that shared runtime model
  instead of re-parsing raw review payloads locally. This keeps the current
  migration moving in the planned direction: compact cross-surface summary in
  `ControlState`, richer review-channel detail in adjacent runtime contracts,
  and thinner frontend adapters over both.
- MP-377 seam-cleanup follow-up (2026-03-13):
  the remaining live `probe_single_use_helpers` debt in the current runtime /
  governance extraction seam is burned down. `controller_action.py`,
  `docs_check.py`, `path_audit.py`, and `runtime/control_state.py` now keep
  only named seams instead of one-use private wrappers. `path_audit.py`
  remains the stable public seam, with the legacy-scan/workspace-scan
  implementation now split under `path_audit_support/` so crowded-root cleanup
  does not break strict-tooling authority. The probe backlog now narrows to the real portability issue: the large
  `dev/scripts/devctl` root compatibility-shim population that still needs
  package/repo-pack extraction work rather than more local cleanup.
- MP-377 repo-pack surface-generation update (2026-03-13):
  the first concrete Phase 2 vertical slice is now in repo state.
  `dev/config/devctl_repo_policy.json` owns a new
  `repo_governance.surface_generation` section for repo-pack metadata,
  template context, and governed surfaces; `devctl render-surfaces` renders or
  validates those outputs; `check_instruction_surface_sync` plus
  `docs-check --strict-tooling` enforce template-backed surface drift; and
  starter bootstrap/template flows now seed the same contract for adopter
  repos. The remaining Phase 2 follow-up is to add first-class context-budget
  profiles / usage-tier guidance on top of this generated-surface path.
- MP-377 generated-surface integration follow-up (2026-03-13):
  the new repo-pack surface-generation slice is now wired end to end instead
  of half-landed. `render-surfaces` is registered in the public CLI/listing,
  its parser and command implementation now live under governance-owned
  namespaces instead of crowded flat roots, and the paired
  `package_layout/check_instruction_surface_sync.py` guard now runs in
  tooling/release governance lanes.
- MP-377 repo-pack surface-generation hardening update (2026-03-13):
  report-mode surface checks now tolerate missing local-only outputs such as
  `CLAUDE.md` while `render-surfaces --write` still materializes them;
  bootstrap/template starter flows now point adopters at that write path; and
  maintainer docs plus targeted tests now cover the generated-surface contract
  instead of leaving it implicit.
- MP-377 generated-surface concurrency follow-up (2026-03-13):
  the broader governance namespace split briefly reintroduced stale targeted
  references after the first validation pass. The active runtime helper path is
  `dev/scripts/devctl/governance/surface_runtime.py`, the helper now resolves
  `check_agents_bundle_render` through the package import path so focused
  pytest collection stays stable, the public generated-surface runner now lives
  under `dev/scripts/checks/package_layout/`, and the strict-tooling
  docs-check fixture now points at
  `dev/scripts/devctl/commands/governance/render_surfaces.py` instead of the
  old flat command location.
- MP-377 self-hosting layout follow-up (2026-03-13):
  the generated-surface/layout slice is still green after the concurrent
  modularization churn, but that green status needs the right interpretation:
  `check_package_layout.py` is currently enforcing freeze-mode crowding rules
  for `dev/scripts/checks`, `dev/scripts/devctl`,
  `dev/scripts/devctl/commands`, and `dev/scripts/devctl/tests`. That means
  new sprawl is blocked and the recent governance files landed in the correct
  namespaces, but the repo still needs more package/test decomposition work
  before those roots are actually tidy rather than merely baselined.
- MP-377 machine-first governance-command follow-up (2026-03-13):
  the moved governance command family now shares one package-local output/error
  helper that treats JSON as the canonical machine payload and markdown as the
  human projection, and a dispatch-level CLI stability test now proves parser
  wiring, `COMMAND_HANDLERS`, and JSON output across
  `governance-bootstrap`, `governance-export`, `governance-review`, and
  `render-surfaces`. The self-hosting architecture guard was widened in the
  same slice so aliased nested command imports under
  `dev/scripts/devctl/commands/governance/` validate correctly instead of
  forcing the repo back toward flat-root-only command wiring.
- MP-377 machine-output contract audit (2026-03-13):
  audited the shared output path before widening the machine-first rule across
  the repo. The current `--output` flow already avoids full stdout JSON dumps;
  `write_output()` writes the artifact and prints only `Report saved to: ...`.
  The real remaining gap is architectural: that receipt is not a stable
  machine control envelope, and `RunRecord` / `devctl_events` /
  `data-science` still do not record artifact bytes, hashes, or estimated
  token cost. The next slice should add a dedicated machine-artifact emitter
  for JSON-canonical report/packet surfaces (`governance-*`,
  `platform-contracts`, `probe-report`, `data-science`, `loop-packet`, later
  review/autonomy) instead of globally rewriting `emit_output()` for every
  human-oriented command.
- MP-377 machine-artifact emission update (2026-03-13):
  landed the first extraction-friendly implementation of that contract. The
  JSON-canonical surfaces above now emit compact file artifacts plus compact
  JSON stdout receipts when `--format json --output ...` is used, and command
  telemetry/data-science aggregation now capture artifact path/hash/byte/token
  metrics instead of only success/duration. That gives the repo its first
  measurable control-channel contract for AI loops without forcing the same
  behavior onto human-first commands.
- MP-377 simple-command lane follow-up (2026-03-13):
  the first vibecoder-facing façade over policy selection is now in repo
  state. `dev/config/devctl_policies/launcher.json` defines a focused Python
  launcher lane for `scripts/` + `pypi/src`, and `devctl` now exposes that
  lane through short wrappers (`launcher-check`, `launcher-probes`,
  `launcher-policy`) instead of requiring raw `--quality-policy` path
  spelling. This keeps policy files authoritative while proving the product can
  project simpler task-shaped command names for repeated workflows.
- MP-377 launcher command-source pilot (2026-03-13):
  the first launcher-only hard guard is now live behind that focused lane.
  `check_command_source_validation.py` catches free-form `shlex.split(...)`
  on CLI/env/config input, raw `sys.argv` forwarding, and env-controlled
  command argv without validator helpers; `scripts/python_fallback.py` now
  rejects deprecated `--codex-args` free-form passthrough, and
  `pypi/src/voiceterm/cli.py` now validates bootstrap repo URL/ref plus
  forwarded argv before invoking `git` or the native binary.
- MP-377 repo-pack push-governance update (2026-03-21):
  the first repo-pack-owned VCS command-routing slice is now real. The new
  `repo_governance.push` policy owns default remote, development/release
  branch names, protected-branch rules, and the required preflight/post-push
  flow; `devctl push` is the new canonical branch-push surface with
  `TypedAction(action_id="vcs.push")` / `ActionResult` output; generated
  starter surfaces now include a pre-push hook stub; and legacy `sync` /
  `ship` helpers now consume the same policy instead of embedding branch and
  remote defaults in Python.
- MP-376 export/evaluation update (2026-03-11):
  `devctl governance-export` now packages the governance stack into an
  external snapshot/zip with fresh `quality-policy`, `probe-report`, and
  `data-science` artifacts, `dev/guides/PORTABLE_CODE_GOVERNANCE.md` now
  defines the engine/preset/repo-policy boundary plus the evaluation rubric,
  and template schemas now capture both the guarded-episode measurement
  contract and the multi-repo benchmark record. The first broad external pilot
  corpus source is explicitly the maintainer GitHub repo inventory
  (`https://github.com/jguida941?tab=repositories`), while actual non-VoiceTerm
  pilot execution remains open follow-up work.
- MP-376 pilot-onboarding update (2026-03-11):
  the first non-VoiceTerm pilot ran against `ci-cd-hub` and exposed the
  remaining portability leaks directly. `devctl governance-bootstrap` now
  normalizes copied/submodule repos with broken `.git` indirection, `check` /
  `probe-report` / `governance-export` now accept `--adoption-scan` for
  full-surface onboarding runs without a trusted baseline ref, and
  `probe_exception_quality.py` joins the review-probe suite to surface
  suppressive Python exception handling patterns seen in external tooling code.
- MP-376 measurement-ledger update (2026-03-11):
  `devctl governance-review` now records adjudicated guard/probe findings into
  `dev/reports/governance/finding_reviews.jsonl`, writes rolled-up
  `review_summary.{md,json}` artifacts, and feeds those metrics into
  `devctl data-science` so false-positive rate, confirmed-signal rate, and
  cleanup progress are tracked as durable repo evidence instead of chat-only
  notes.
- MP-376 live-cleanup adjudication update (2026-03-11):
  the first high-severity probe debt was burned down through that ledger:
  `probe_exception_quality` findings in `dev/scripts/devctl/collect.py` were
  fixed by narrowing fallback exception handling, the medium translation hint in
  `dev/scripts/devctl/commands/check_support.py` was removed by replacing the
  subprocess-based tempdir lookup with a direct Python implementation, and the
  reviewed outcomes are now recorded as `fixed` in `governance-review`.
- MP-376 portable shim-governance update (2026-03-12):
  compatibility shims are now a first-class portable governance primitive
  instead of a VoiceTerm-only package-layout exception. The engine now owns a
  shared package-layout bootstrap seam, validates shim shape structurally,
  supports policy-owned required metadata fields (`owner`, `reason`, `expiry`,
  `target`), and lets crowded-root/family reports exclude approved shims from
  implementation density while still surfacing shim counts explicitly.
- MP-376 shim-debt probe update (2026-03-12):
  the same portable shim primitive now powers an advisory review layer too.
  `probe_compatibility_shims.py` surfaces missing/expired shim metadata,
  unresolved shim targets, and shim-heavy roots/families, while the fallback
  `run_probe_report.py` path now resolves probe entrypoints from the shared
  quality policy/script catalog instead of carrying a stale hard-coded list.
- MP-376 shim-classification follow-up (2026-04-15):
  repo policy now explicitly allowlists the documented long-lived
  `dev/scripts/checks` helper shims (`code_shape_*.py`,
  `python_default_trap_core.py`, `mobile_relay_rust_parser.py`,
  `rust_guard_common.py`, `rust_check_text_utils.py`,
  `compat_matrix_smoke.py`, `yaml_json_loader.py`) so adoption-scan no longer
  misclassifies them as temporary remove-now debt. The same slice deleted the
  dead `dev/scripts/devctl/quality_policy_values.py` wrapper; the remaining
  real shim backlog is concentrated in the `dev/scripts/devctl` root plus the
  `check_*`, `autonomy_*`, `docs_*`, and `review_channel_*` command families.
- MP-376 package-layout wrapper follow-up (2026-03-12):
  the crowded `dev/scripts/checks/` root no longer hard-codes
  `package_layout.command` as its only allowed shim shape. The portable shim
  validator now ignores canonical shim metadata lines in the thin-wrapper line
  budget, accepts any `package_layout.*` wrapper at the crowded root, and the
  paired devctl tests moved under `dev/scripts/devctl/tests/checks/package_layout/`
  so the crowded test root mirrors the same package boundary.
- MP-376 shim-family cleanup update (2026-03-13):
  retired the next largest temporary `dev/scripts/devctl` root shim family,
  `autonomy_*`, by migrating the remaining repo-visible docs/history/plan
  references to the canonical `dev/scripts/devctl/autonomy/` modules, renaming
  the shim-probe's synthetic fixture paths away from a live wrapper name, and
  deleting 18 obsolete root wrappers. `probe-report` now shows the broader
  `dev/scripts/devctl` root backlog down from 57 temporary wrappers / 135
  repo-visible references to 39 wrappers / 87 references, with `cli_parser_*`
  now the largest remaining family by wrapper count and `triage_*` the next
  highest by repo-visible references.
- MP-376 shim-family cleanup update (2026-03-13):
  finished the next caller-migration tranche after `autonomy_*` by moving the
  remaining repo-visible `cli_parser_*`, `triage_*`, and `triage_loop_*`
  docs/history/active-plan references to the canonical
  `dev/scripts/devctl/cli_parser/` and `dev/scripts/devctl/triage/` packages,
  then deleting 16 obsolete root wrappers. `probe-report` now shows the
  broader `dev/scripts/devctl` root backlog down again from 39 temporary
  wrappers / 87 repo-visible references to 23 wrappers / 46 references; the
  next wrapper-heavy families are `process_sweep_*` and `security_*`, while
  the current repo-visible-reference examples include
  `data_science_metrics.py` and `governance_bootstrap_*`.
- MP-376 shim-family cleanup update (2026-03-13):
  retired the temporary `security_*` root shim family by moving workflow/docs/
  history references to the canonical `dev/scripts/devctl/security/`
  modules and deleting the four obsolete root wrappers. The next
  shim-governance follow-up is now the
  remaining `process_sweep_*` family plus the docs-led wrapper examples
  (`data_science_metrics.py`, `governance_bootstrap_*`) that still keep the
  `dev/scripts/devctl` root above its temporary-shim budget.
- MP-376 design-smell cleanup update (2026-03-11):
  the next medium-severity `probe_single_use_helpers` slice is now burned down
  too: `dev/scripts/devctl/collect.py` no longer carries one-use file-local
  helpers, and the data-science row collectors were split into
  `dev/scripts/devctl/data_science/source_rows.py` so
  `dev/scripts/devctl/data_science/metrics.py` stays focused on snapshot
  orchestration. Those reviewed outcomes are also now recorded as `fixed` in
  `governance-review`.
- MP-376 triage single-use-helper follow-up (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup moved the
  CIHub/external-input triage helpers out of
  `dev/scripts/devctl/commands/triage.py` so the command stays
  orchestration-focused, and the reviewed outcome is now recorded as `fixed`
  in `governance-review`.
- MP-376 loop-packet single-use-helper follow-up (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down too:
  `dev/scripts/devctl/commands/loop_packet_helpers.py` no longer hides JSON
  source loading/command normalization or packet-body dispatch behind one-call
  wrappers. This was treated as a real design-smell signal, not a false
  positive, because the flagged helpers had no reuse or test-seam value; the
  behavior now lives directly in `_discover_artifact_sources()` and
  `_build_packet_body()`, and the reviewed outcome is now recorded as `fixed`
  in `governance-review`.
- MP-376 review-channel single-use-helper adjudication (2026-03-11):
  the next `probe_single_use_helpers` candidate under
  `dev/scripts/devctl/commands/review_channel_bridge_handler.py` is now logged
  as `deferred`, not `false_positive`. Before review, the probe emitted one
  file-level hint over five private helpers; after review, the repo state now
  records the narrower call explicitly: `_validate_live_launch_conflicts()`
  and `_load_bridge_runtime_state()` look like real one-use wrappers,
  `_resolve_promotion_and_terminal_state()` and `_build_sessions()` remain
  defensible seams, and `_post_session_lifecycle_event()` is borderline. That
  keeps the next cleanup selective and auditable instead of treating the whole
  hint as either pure noise or a blanket inline order.
- MP-376 review-channel single-use-helper cleanup (2026-03-11):
  that deferred `review_channel_bridge_handler.py` follow-up is now burned down
  with the selective fix the adjudication called for. Before the fix, the file
  mixed two real one-use wrappers with three meaningful seams; after the fix,
  the live-launch conflict logic now reuses
  `review_channel_bridge_action_support.py`, the one-use bridge-state wrapper
  is removed, and the remaining session/promotion/event boundaries now live as
  named action-support helpers instead of private single-use functions.
  `review_channel_bridge_support.py` stays back under the code-shape soft
  limit after that split. This was still treated as a real design-smell
  signal, not a false positive, and `probe_single_use_helpers` no longer flags
  the handler; the reviewed outcome is now recorded as `fixed` in
  `governance-review`.
- MP-376 governance-export single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/governance_export_artifacts.py`. Before the fix, the
  export path hid quality-policy, probe-report, and data-science artifact
  generation behind three one-call private helpers with no reuse or test-seam
  value; after the fix, `write_generated_artifacts()` writes those artifact
  families directly, `probe_single_use_helpers` no longer flags the file, and
  the reviewed outcome is now recorded as `fixed` in `governance-review`.
- MP-376 governance-export builder single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/governance_export_support.py`. Before the fix, the
  export builder hid repository-external destination validation, snapshot
  source copying, manifest emission, and path-containment checking behind four
  one-call private helpers with no reuse or seam value; after the fix,
  `build_governance_export()` performs those steps directly, leaves
  `_sanitize_snapshot_name()` as the only local helper boundary, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-376 watchdog-episode single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/watchdog/episode.py`. Before the fix, the episode
  builder hid provider inference, guard-family classification, and
  escaped-findings counting behind three one-call private helpers with no
  reuse or test-seam value; after the fix, `build_guarded_coding_episode()`
  performs those derivations directly, leaves `_snapshot()` as the only reused
  local helper boundary, and `probe_single_use_helpers` no longer flags the
  file. This was treated as a real design-smell hit, not a false positive, and
  the reviewed outcome is now recorded as `fixed` in `governance-review`.
- MP-376 watchdog-probe-gate single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/watchdog/probe_gate.py`. Before the fix, the probe gate
  hid allowlist loading, allowlist matching, and report summarization behind
  three one-call private helpers with no reuse or test-seam value; after the
  fix, `run_probe_scan()` performs those steps directly, focused unit tests now
  cover allowlist filtering/fail-open behavior, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-376 quality-policy-scope single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/quality_policy_scopes.py`. Before the fix, the scope
  resolver hid Python-root discovery plus configured-root normalization and
  coercion behind four one-call private helpers with no reuse or test-seam
  value; after the fix, `resolve_quality_scopes()` performs those steps
  directly while `_discover_rust_scope_roots()` remains the only meaningful
  helper boundary, focused unit tests now cover common Python-root discovery
  plus invalid/duplicate scope handling, and `probe_single_use_helpers` no
  longer flags the file. This was treated as a real design-smell hit, not a
  false positive, and the reviewed outcome is now recorded as `fixed` in
  `governance-review`.
- MP-376 review-probe-report single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/review_probe_report.py`. Before the fix, the aggregated
  probe reporter hid per-probe subprocess execution, hint enrichment, batch
  collection, and terminal hotspot rendering behind four one-call private
  helpers with no reuse or seam value; after the fix, `build_probe_report()`
  drives probe execution and risk-hint enrichment directly,
  `render_probe_report_terminal()` renders the top hotspot inline, focused
  unit tests now cover the terminal hotspot path, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-376 triage-support single-use-helper cleanup (2026-03-11):
  the next `probe_single_use_helpers` ledger cleanup is now burned down in
  `dev/scripts/devctl/triage/support.py`. Before the fix, the markdown
  renderer hid project snapshot, issue list, CIHub, and external-input
  sections behind four one-call private helpers with no reuse or seam value;
  after the fix, `render_triage_markdown()` builds those sections directly,
  focused unit tests now cover CIHub/external-input markdown rendering, and
  `probe_single_use_helpers` no longer flags the file. This was treated as a
  real design-smell hit, not a false positive, and the reviewed outcome is now
  recorded as `fixed` in `governance-review`.
- MP-359 operator-console bundle unblock follow-up (2026-03-11):
  the desktop proof lane is back to green after two bounded fixes. First,
  `app/operator_console/views/layout/__init__.py` now lazy-loads
  `WindowShellMixin`, `HAS_THEME_EDITOR`, and workbench helpers instead of
  importing them eagerly during package init, breaking the package-init
  cycle `help_dialog -> layout.__init__ -> ui_window_shell -> help_dialog`
  that had been failing `test_help_dialog.py` during collection. Second,
  `dev/scripts/devctl/phone_status_views.py` now routes compact/trace/action
  projection through the existing `_section()` helper instead of calling
  removed `_controller/_loop/_source_run/_terminal/_ralph` helpers, so the
  Operator Console phone snapshot path is no longer stuck in unavailable
  fallback. `app/operator_console/tests/` is green again in the canonical
  bundle proof path.
- MP-376 phone-status projection hotspot cleanup (2026-03-11):
  the next high-severity Python review-probe hotspot is now burned down in
  `dev/scripts/devctl/phone_status_views.py`. Before the fix,
  `compact_view()`, `trace_view()`, and `actions_view()` returned large
  ad-hoc dict literals and `view_payload()` plus `_render_view_markdown()`
  branched on raw strings, so the `probe_dict_as_struct` and
  `probe_stringly_typed` hints were treated as real signal, not false
  positives. After the fix, `PhoneStatusView` parses the view boundary once,
  typed projection models live in
  `dev/scripts/devctl/phone_status_projection.py`, focused phone-status tests
  cover compact fallback plus trace markdown rendering, `probe-report` no
  longer flags the file, and the follow-on file split keeps
  `phone_status_views.py` back under the code-shape soft limit.
- MP-359 presentation-state probe cleanup follow-up (2026-03-11):
  the remaining Operator Console advisory debt from the probe suite is now
  burned down in `app/operator_console/state/presentation/presentation_state.py`.
  Before the fix, the file hid snapshot-digest lane serialization,
  repo-analytics change-mix rendering, and CI KPI text behind one-call
  private helpers with no reuse or seam value; after the fix,
  `probe_single_use_helpers` no longer flags the file, the residual low
  formatter-helper `probe_design_smells` hint disappears in the same pass, and
  `app/operator_console/tests/state/test_presentation_state.py` remains green.
- MP-376 operator-console presentation-state single-use-helper cleanup (2026-03-11):
  the final repo-wide `probe_single_use_helpers` ledger cleanup is now burned
  down in `app/operator_console/state/presentation/presentation_state.py`.
  Before the fix, the presentation layer hid snapshot-digest lane
  serialization, repo-analytics change-mix formatting, and CI KPI rendering
  behind one-call private helpers with no reuse or test-seam value; after the
  fix, `snapshot_digest()`, `_build_repo_text()`, and `_build_kpi_values()`
  perform those derivations directly, focused presentation-state tests remain
  green, `probe_single_use_helpers` no longer flags any file repo-wide, and
  the reviewed outcome is now recorded as `fixed` in `governance-review`.
- MP-378 code shape expansion audit intake (2026-03-16):
  `dev/active/code_shape_expansion.md` now serves as the subordinate research
  and calibration companion for the next review-probe tranche instead of a
  parallel execution roadmap. The re-audit kept the candidate families, but
  tightened promotion rules: implementation still lands through
  `dev/active/review_probes.md` Phase 5b, every promoted probe needs explicit
  `review_lens` / `risk_type` / severity thresholds / `practices.py` guidance,
  `probe_method_chain_length` is dropped pending redesign, sequential
  mutation-on-dict findings fold into `probe_dict_as_struct` instead of a new
  standalone probe, and the later cross-file/language-expansion phases remain
  blocked on `MP-377` runtime/packaging contracts. Current likely first
  implementation slice: readability probes with proven local signal quality
  plus tuple-return, fan-out, side-effect, and match-arm evaluation.
- MP-350 closure update (2026-03-05): additive read-only MCP adapter
  implementation is complete with code-level contract helpers/tests for
  `check --profile release`, `ship --verify`, and cleanup protections;
  execution tracker moved to
  `dev/archive/2026-03-05-devctl-mcp-contract-hardening.md` and durable
  guidance lives in `dev/guides/MCP_DEVCTL_ALIGNMENT.md`.
- MP-347 architecture-audit refresh (2026-03-05): core tooling/runtime guard
  packs are green (`check_code_shape`, duplication audit with fresh `jscpd`,
  rust quality guards, workflow parity, strict-tooling docs governance), and
  strict hygiene catalog/docs alignment is restored for
  `check_duplication_audit_support.py`; remaining follow-up is scoped to
  risk-add-on SSOT consolidation, local strict-hygiene repeatability noise
  (`__pycache__` warning churn unless `--fix`), function-exception paydown
  before `2026-05-15`, and dead-code allow backlog reduction.
- MP-347 docs-policy dedup update (2026-03-06): docs-check path policy now has
  single-source ownership (`docs_check_policy.py`), and
  `docs_check_constants.py` is a compatibility re-export shim with dedicated
  regression coverage in `dev/scripts/devctl/tests/test_docs_check_constants.py`.
- MP-347 shape-governance refresh (2026-03-06): code-shape policy budgets and
  temporary function exceptions were synchronized for the current tooling
  refactor batch (active-plan sync, multi-agent sync, release parser wiring,
  and devctl command runners), with explicit owner/follow-up metadata and
  expiry tracking through `2026-05-15`.
- MP-347 docs-IA boundary cleanup update (2026-03-06): Phase-15 backlog/active
  boundary work is closed; canonical local backlog now lives at
  `dev/deferred/LOCAL_BACKLOG.md`, canonical guard remediation scaffold output
  now lives at `dev/reports/audits/RUST_AUDIT_FINDINGS.md`, and canonical
  phase-2 research now lives at `dev/deferred/phase2.md` (with bridge pointers
  retained for one migration cycle).
- MP-347 mutation-policy update (2026-03-05): `devctl check --profile release`
  now runs mutation-score in report-only mode (non-blocking warnings with
  post-release follow-up guidance when outcomes are missing/stale/below
  threshold) so strict remote CI + CodeRabbit/Ralph gates remain release
  blockers while mutation hardening stays explicitly tracked work.
- MP-346 post-waiver guardrail hardening update: compatibility-matrix checks now
  parse YAML format directly, smoke runtime-backend detection now derives from
  `BackendRegistry` constructor ownership (not module declarations), and
  isolation scanning now skips broader test-only cfg attributes such as
  `cfg(any(test, ...))` with dedicated unit coverage.
- MP-346 review-driven cleanup update: IPC prompt/wrapper preemption now emits
  consistent `JobEnd(cancelled)` events, compatibility-matrix validation now
  fails on duplicate host/provider ids, and matrix smoke now enforces full
  parsed runtime host/backend/provider sets (excluding explicit
  `BackendFamily::Other` sentinel) to prevent silent governance drift.
- MP-346 reviewer follow-up hardening update: isolation cfg-test skipping now
  excludes mixed expressions containing `not(test)` to avoid production-path
  false negatives, matrix smoke backend discovery is no longer coupled to a
  specific `BackendRegistry` vector layout, matrix validation now fails
  malformed host/provider entries missing string `id` fields, and IPC
  cancellation regression coverage now includes active-Claude wrapper and
  `/cancel` `JobEnd(cancelled)` assertions; targeted IPC + memory-guard tests
  are green in this session.
- MP-346 closure-gate stabilization update: full `devctl check --profile ci`
  rerun is green after tightening `legacy_tui::tests::memory_guard_backend_threads_drop`
  to wait for backend-thread count return-to-baseline (removing a transient
  teardown race from suite-wide execution).
- Tooling governance update: workflow shell-heavy commit-range/scope/path
  resolution now routes through `dev/scripts/workflow_bridge/shell.py`,
  `docs-check --strict-tooling` now enforces `check_workflow_shell_hygiene.py`,
  and `tooling_control_plane.yml` now runs explicit naming-consistency and
  workflow-shell hygiene checks.
- Tooling layout cleanup update (2026-03-12): root-level Python wrappers under
  `dev/scripts/` were removed after package entrypoints were migrated into
  `mutation/`, `coderabbit/`, `workflow_bridge/`, `rust_tools/`, `badges/`,
  and `artifacts/`; `devctl path-audit/path-rewrite` now enforces those moved
  script paths repo-wide, and directory READMEs now make the entrypoint/helper
  split explicit. Portability review for the same slice is also explicit:
  reusable guard/probe policy resolution is ahead of the higher-level workflow
  helpers, while Ralph, mutation, process hygiene, and some docs/router policy
  still carry VoiceTerm-specific code that remains tracked follow-up work.
- Repo-governance portability update (2026-03-12): the next portability slice
  moved `check-router` lane/risk-addon rules and `docs-check`
  user-doc/tooling-doc/evolution/deprecated-reference path policy into
  `dev/config/devctl_repo_policy.json`, with `--quality-policy` overrides on
  both commands. That keeps current VoiceTerm behavior explicit while letting
  another repo adopt the same engine by swapping repo policy instead of
  patching command code.
- MP-346 tooling closure pass update: oversized workflow/devctl helper modules
  were split into companion modules (`autonomy_workflow_bridge`, hygiene ADR
  audits), workflow-shell hygiene now scans both `.yml` + `.yaml` with
  auditable rule-level suppression comments, and release docs now align to the
  same-SHA preflight-first release-gates sequence enforced by publish lanes.
- MP-346 Rust guardrail expansion update: `rust_ci.yml` now emits clippy lint
  histogram JSON and enforces `check_clippy_high_signal.py` against
  `dev/config/clippy/high_signal_lints.json`; `devctl` AI guard + scaffolding
  docs now include `check_rust_test_shape.py` and
  `check_rust_runtime_panic_policy.py`, with unit coverage extended across
  `test_check.py`, `test_audit_scaffold.py`, and dedicated new check-script
  tests.
- MP-346 runtime-lane AI-guard range update: `rust_ci.yml`,
  `release_preflight.yml`, and `security_guard.yml` now resolve commit ranges
  through `workflow_shell_bridge.py resolve-range` and pass those refs to
  `devctl check --profile ai-guard`; `devctl check` also now sequences
  clippy-lint histogram collection before `clippy-high-signal-guard`, and
  naming-consistency parsing was split into a companion module to keep shape
  policy green. Strict clippy zero-warning status was restored after new lint
  families surfaced, and `rust/Cargo.toml` now sets `rust-version = 1.88.0`
  to match the active MSRV lane contract.
- MP-346 pending-guardrail closure update: `devctl release-gates` rendering is
  now Python-3.11-compatible, planned Clippy threshold ratchet is complete
  (`cognitive-complexity-threshold=25`, `too_many_lines=warn`), and new
  duplicate-type + structural-complexity guards are wired into AI-guard and
  audit-scaffold flows; periodic `jscpd` duplication auditing now has a
  dedicated wrapper (`check_duplication_audit.py`) for freshness/threshold
  evidence capture.
- MP-346 continuation audit update: the previously interrupted
  `devctl check --profile ci` rerun is now confirmed green end-to-end, stale
  pre-remediation evidence rows were removed from
  `ide_provider_modularization.md`, and `code_shape_policy.py` now carries an
  explicit path budget for `check_rust_lint_debt.py` so the tooling bundle
  remains non-regressive after the new guardrail wiring.
- MP-347 tooling-ops update: `devctl check --profile fast` now aliases
  `quick` for local iteration naming clarity, and `devctl check-router`
  selects docs/runtime/tooling/release lanes from changed paths with optional
  `--execute` routing of bundle commands plus risk-matrix add-ons.
- MP-347 bundle-governance update: canonical command-bundle authority now
  lives in `dev/scripts/devctl/bundle_registry.py`; `check-router` and
  `check_bundle_workflow_parity.py` now consume the registry, while AGENTS
  bundle blocks are rendered/reference-only docs.
- MP-347 bundle-render automation update: added
  `check_agents_bundle_render.py` (`--write` regen mode) and wired
  `docs-check --strict-tooling` to fail when AGENTS rendered bundle docs drift
  from canonical registry output.
- MP-347 lint-debt governance update: Rust dead-code debt is now inventoryable
  and policy-gated (`--report-dead-code`, `--fail-on-undocumented-dead-code`)
  with all current `#[allow(dead_code)]` instances documented by explicit
  `reason` metadata.
- MP-347 architecture-governance intake update (2026-03-08): post-release
  DevCtl hardening backlog now explicitly includes an
  `architecture_surface_sync` guard for changed/untracked paths plus a
  duplicate/shared-logic candidate guard so new repo surfaces fail earlier
  when they are not wired into authority docs, bundles, workflows, and
  canonical shared-helper boundaries.
- MP-346 formal closure (2026-03-05): Phase 6 governance gate closed;
  all release-scope structural/tooling/governance/testing conditions met
  for IDE-first matrix (4/4); post-release backlog (Gemini overlay,
  JetBrains+Claude render-sync, AntiGravity readiness) tracked in
  `ide_provider_modularization.md` Steps 3g/3h and Phase 5.
- Pre-release architecture audit progress (2026-03-05): Phases 1-7
  are now complete (Phase-7 added 5 new guard scripts, extended 3 existing
  guards, and added hygiene checks; 596/596 tests green).
  Phases 8-14 remain default-deferred post-release unless explicitly promoted
  by operator direction.
- Pre-release architecture audit execution kickoff (2026-03-06): Phase 16
  governance alignment is complete (single pre-release audit authority kept in
  `dev/active/pre_release_architecture_audit.md`; strict tooling
  docs/governance checks green), and the first do-now runtime remediation
  landed by replacing `main.rs` `env::set_var` usage with runtime theme/backend
  overrides; `cargo test --bin voiceterm` remains green (`1526` passed).
- Pre-release architecture audit follow-up (2026-03-06): the
  `feed_prompt_output_and_sync` structural-complexity exception was removed
  after the prompt-occlusion detection split reduced the function below the
  default guard thresholds (`score=9`, `branch_points=7`, `depth=3`).
- Pre-release architecture audit follow-up (2026-03-06): the
  `writer/state/redraw.rs::maybe_redraw_status` structural-complexity
  exception was removed after splitting redraw gating/geometry/apply/render
  helpers reduced the function below the default guard thresholds
  (`score=13`, `branch_points=2`, `depth=2`).
- Pre-release architecture audit follow-up (2026-03-06): writer-state dispatch
  now uses `writer/state/dispatch.rs` for message routing and
  `writer/state/dispatch_pty.rs` for PTY-heavy output. Temporary complexity
  exceptions for dispatch/redraw/prompt were removed after guard checks
  (`check_structural_complexity` `exceptions_defined=0`).
- Pre-release architecture audit follow-up (2026-03-06): readability cleanup
  simplified dense comment/policy wording in the writer dispatch path and
  guard policy text; targeted rustfmt alignment was applied to active Rust
  files and full `devctl check --profile ci` rerun is green.
- Pre-release architecture audit follow-up (2026-03-06): transition
  compatibility cleanup retired `audit-scaffold` legacy `dev/active/` output
  support and retired strict-tooling `dev/DEVELOPMENT.md` alias acceptance;
  `collect_git_status` now uses `git status --porcelain --untracked-files=all`
  so canonical `dev/guides/*` updates are detected without legacy fallback.

## Multi-Agent Coordination Board

This board remains the execution tracker for lane ownership/status.
`dev/active/review_channel.md` now holds the merged markdown-swarm lane plan,
instruction log, shared ledger, and signoff template. `bridge.md` is the
only live cross-team reviewer/coder coordination surface during active swarm
execution.

Branch guards for all agents:

1. Start from `develop` (never from `master`).
2. Use dedicated worktrees and dedicated feature branches per agent.
3. Rebase each active agent branch after every merge to `origin/develop`.
4. Update this board before and after each execution batch.
5. Keep `master` release-only (merge/tag/publish only).
6. Shared hotspot files (`writer/state.rs`, `prompt_occlusion.rs`,
   `claude_prompt_detect.rs`, `theme/rule_profile.rs`,
   `theme/style_pack.rs`) require an explicit claim in the merged
   `review_channel.md` swarm ledger before edits when Theme
   (`MP-148..MP-182`), naming/API cohesion (`MP-267`), and MP-346 scopes
   overlap.

Historical example only: the table below records one prior 8+8 swarm
assignment. Future runs should regenerate lane roles from the active plan
targets / issue clusters and the selected `WorkIntakePacket` /
`PlanExpectationPacket`, not reuse these exact assignments as if they were the
permanent architecture.

| Agent | Lane | Active-doc scope | MP scope (authoritative) | Worktree | Branch | Status | Last update (UTC) | Notes |
|---|---|---|---|---|---|---|---|---|
| `AGENT-1` | Codex architecture contract review | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` | `MP-340, MP-355` | `../codex-voice-wt-a1` | `feature/a1-codex-architecture-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for controller/review/memory contract boundaries. |
| `AGENT-2` | Codex clean-code and state-boundary review | `dev/active/review_channel.md` + runtime pack | `MP-267, MP-340, MP-355` | `../codex-voice-wt-a2` | `feature/a2-codex-clean-code-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for duplication, ownership drift, and mixed-state violations. |
| `AGENT-3` | Codex runtime and handoff review | `dev/active/review_channel.md`, `dev/active/memory_studio.md` + runtime pack | `MP-233, MP-238, MP-243, MP-340, MP-355` | `../codex-voice-wt-a3` | `feature/a3-codex-runtime-handoff-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for handoff, bootstrap, memory-bridge, and runtime correctness. |
| `AGENT-4` | Codex CI and workflow reviewer | `dev/active/review_channel.md` + tooling pack | `MP-297, MP-298, MP-303, MP-306, MP-355` | `../codex-voice-wt-a4` | `feature/a4-codex-ci-workflow-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for CI/CD, bundle/workflow parity, and push-safety. |
| `AGENT-5` | Codex devctl and process-hygiene reviewer | `dev/active/devctl_reporting_upgrade.md`, `dev/active/host_process_hygiene.md` | `MP-297, MP-298, MP-300, MP-303, MP-306, MP-356` | `../codex-voice-wt-a5` | `feature/a5-codex-devctl-process-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for `devctl`, cleanup/audit flow, and maintainer-surface correctness. |
| `AGENT-6` | Codex overlay and UX reviewer | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a6` | `feature/a6-codex-overlay-ux-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for Control/Review/Handoff UX, hitboxes, redraw, and footer honesty. |
| `AGENT-7` | Codex guard and test reviewer | `dev/active/review_channel.md`, `dev/active/host_process_hygiene.md` + tooling pack | `MP-303, MP-355, MP-356` | `../codex-voice-wt-a7` | `feature/a7-codex-guard-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Codex reviewer lane for guard coverage, regression tests, and audit evidence quality. |
| `AGENT-8` | Codex integration and re-review loop | `dev/active/MASTER_PLAN.md`, `dev/active/review_channel.md` | `MP-340, MP-355, MP-356` | `../codex-voice-wt-a8` | `feature/a8-codex-integration-review` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; primary Codex merge/readiness lane that polls every 5 minutes when Claude is still coding. |
| `AGENT-9` | Claude bridge push-safety fixes | `dev/active/review_channel.md` + tooling pack | `MP-303, MP-306, MP-355` | `../codex-voice-wt-a9` | `feature/a9-claude-bridge-push-safety` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for bridge-gate, workflow-order, and branch push-safety fixes. |
| `AGENT-10` | Claude live Git-context fixes | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a10` | `feature/a10-claude-git-context-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for session-root Git context and repo-snapshot correctness. |
| `AGENT-11` | Claude refresh, redraw, and footer fixes | `dev/active/review_channel.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a11` | `feature/a11-claude-refresh-redraw-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for Control/Handoff refresh honesty, error redraw, and footer-hitbox alignment. |
| `AGENT-12` | Claude broker and clipboard fixes | `dev/active/review_channel.md`, `dev/active/autonomous_control_plane.md` + runtime pack | `MP-340, MP-355` | `../codex-voice-wt-a12` | `feature/a12-claude-broker-clipboard-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for broker shutdown cleanup/reporting and writer-routed clipboard behavior. |
| `AGENT-13` | Claude handoff and bootstrap fixes | `dev/active/review_channel.md`, `dev/active/memory_studio.md` + runtime pack | `MP-233, MP-238, MP-243, MP-340, MP-355` | `../codex-voice-wt-a13` | `feature/a13-claude-handoff-bootstrap-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for fresh-prompt bootstrap docs, handoff packet context, and memory-compatible resume paths. |
| `AGENT-14` | Claude workflow and publication-sync fixes | `dev/active/devctl_reporting_upgrade.md` + tooling pack | `MP-297, MP-298, MP-300, MP-303, MP-306` | `../codex-voice-wt-a14` | `feature/a14-claude-workflow-publication-fixes` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for publication-sync scope, workflow ordering, and tooling-gate rationalization. |
| `AGENT-15` | Claude clean-code refactors | `dev/active/naming_api_cohesion.md`, `dev/active/review_channel.md` + runtime/tooling packs | `MP-267, MP-340, MP-355` | `../codex-voice-wt-a15` | `feature/a15-claude-clean-code-refactors` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for dedup, separation-of-concerns cleanup, and mixed-state untangling that reviewers flag. |
| `AGENT-16` | Claude proof and regression closure | `dev/active/review_channel.md`, `dev/active/host_process_hygiene.md` + runtime/tooling packs | `MP-303, MP-340, MP-355, MP-356` | `../codex-voice-wt-a16` | `feature/a16-claude-proof-regression-closure` | `planned` | `2026-03-08T18:21:48Z` | `handoff=swarm-20260308-code-audit`; Claude coding lane for final guard green runs, regression proofs, and cross-lane verification closeout. |

## Strategic Direction

- Protect current moat: terminal-native PTY orchestration, prompt-aware queueing, local-first voice flow.
- Close trust gap: latency metrics must match user perception and be auditable.
- Build differentiated product value in phases:
  1. Visual-first UX pass (telemetry, motion, layout polish, theme ergonomics)
  2. Workflow differentiators (voice navigation, history, CLI workflow polish)
  3. Theme-systemization (visual surfaces first, then full Theme Studio control parity)
  4. Advanced expansion (streaming STT, tmux/neovim, accessibility)

## Unified Active-Docs Phased Map (Execution Order)

This is the cross-plan execution map so agents and developers stay aligned on
main goal and sequence across all active docs.

### Phase A - Governance + Scope Integrity

1. Keep one execution tracker (`MASTER_PLAN`) and strict active-doc sync.
2. Enforce repeat-to-automate and audit evidence as default operating mode.

Mapped scopes:

- `MP-333`, `MP-337`
- `dev/active/INDEX.md`
- `dev/active/review_channel.md`

### Phase B - Runtime and Workspace Reliability Baseline

1. Keep runtime safety/perf/teardown/wake-word hardening green.
2. Complete workspace layout migration so path contracts are stable.

Mapped scopes:

- `MP-127..MP-138`, `MP-341`, `MP-346`, `MP-354`, runtime hardening + host/provider modularization docs.

### Phase C - Tooling Control Plane + Loop Foundations

1. Keep `devctl` reporting/control-plane lane as the automation backbone.
2. Keep Ralph + mutation loops bounded, source-correlated, and policy-gated.
3. Keep external federation bridges pinned and governed.

Mapped scopes:

- `MP-297..MP-300`, `MP-303`, `MP-306`, `MP-325..MP-329`, `MP-334`
- `dev/active/devctl_reporting_upgrade.md`
- `dev/active/autonomous_control_plane.md` (Phases 1-2/5/6)

### Phase D - Theme/Visual Platform Completion

1. Finish resolver-first Theme Studio migration.
2. Keep visual parity gates strict before any GA expansion.

Mapped scopes:

- `MP-148..MP-182`
- `dev/active/theme_upgrade.md`

### Phase E - Memory + Action Studio Platform

1. Build semantic memory + retrieval + action governance without runtime regressions.
2. Promote only with quality, isolation, and compaction gates passing.

Mapped scopes:

- `MP-230..MP-255`
- `dev/active/memory_studio.md`

### Phase F - Architect Controller (Rust TUI + iPhone + Agent Relay)

1. Deliver unified controller state model consumed by Rust Dev panel and phone.
2. Deliver guarded remote controls and reviewer-agent packet relay.
3. Keep branch/CI/replay policy gates mandatory before promote/write actions.

Mapped scopes:

- `MP-330..MP-332`, `MP-336`, `MP-338`
- `MP-340`
- `dev/active/autonomous_control_plane.md` (Phase 3 + 3.5 + 3.7 + 6.1)
- `dev/active/loop_chat_bridge.md`

### Phase G - Release Hardening + Template Extraction

1. Complete rollout soak, policy hardening, and full audit loops.
2. Extract reusable template package only after governance parity is proven.

Mapped scopes:

- `autonomous_control_plane` rollout/template phases
- release/tracker governance bundles and CI lanes.

## ADR Program Backlog (Cross-Plan, Pending)

Create these ADRs in order so agents/dev do not lose architectural scope.
Accepted authorities for unified controller state contract and agent relay
packet protocol have landed (see `dev/adr/0027-*` and `dev/adr/0028-*`).

Remaining backlog:

1. `ADR-0029` Operator Action Policy Model:
   action classes, approval gates, replay/nonce rules, and deny semantics.
2. `ADR-0030` Phone Adapter Architecture:
   SSH-first, push/SMS/chat adapters, auth boundaries, and fallback strategy.
3. `ADR-0031` Rust Dev-Panel Control-Plane Boundary:
   what stays runtime-local vs control-plane-fed; non-interference guarantees.
4. `ADR-0032` Autonomous Loop Stage Machine:
   triage/plan/fix/verify/review/promote transitions and stop conditions.
5. `ADR-0033` Autonomy Metrics + Scientific Audit Method:
   KPI definitions, experiment protocol, and promotion criteria.
6. `ADR-0034` Template Extraction Contract:
   what must be standardized before reuse across repositories.

## Phase 0 - Completed Release Stabilization (v1.0.51-v1.0.52)

- [x] MP-072 Prevent HUD/timer freeze under continuous PTY output.
- [x] MP-073 Improve IDE terminal input compatibility and hidden-HUD discoverability.
- [x] MP-074 Update docs for HUD/input behavior changes and debug guidance.
- [x] MP-075 Finalize latency display semantics to avoid misleading values.
- [x] MP-076 Add latency audit logging and regression tests for displayed latency behavior.
- [x] MP-077 Run release verification (`cargo build --release --bin voiceterm`, tests, docs-check).
- [x] MP-078 Finalize release notes, bump version, tag, push, GitHub release, and Homebrew tap update.
- [x] MP-096 Expand SDLC agent governance: post-push audit loop, testing matrix by change type, CI expansion policy, and per-push docs sync requirements.
- [x] MP-099 Consolidate overlay research into a single reference source (now consolidated under `dev/active/theme_upgrade.md`) and mirror candidate execution items in this plan.

## Phase 1 - Latency Truth and Observability

- [x] MP-079 Define and document latency terms (capture, STT, post-capture processing, displayed HUD latency).
- [x] MP-080 Hide latency badge when reliable latency cannot be measured.
- [x] MP-081 Emit structured `latency_audit|...` logs for analysis.
- [x] MP-082 Add automated tests around latency calculation behavior.
- [x] MP-097 Fix busy-output HUD responsiveness and stale meter/timer artifacts (settings lag under Codex output, stale REC duration/dB after capture, clamp meter floor to stable display bounds).
- [x] MP-098 Eliminate blocking PTY input writes in the overlay event loop so queued/thinking backend output does not stall live typing responsiveness.
- [x] MP-083 Run and document baseline latency measurements with `latency_measurement` and `dev/scripts/tests/measure_latency.sh` (`dev/archive/2026-02-13-latency-baseline.md`).
- [x] MP-084 Add CI-friendly synthetic latency regression guardrails (`.github/workflows/latency_guard.yml` + `measure_latency.sh --ci-guard`).
- [x] MP-194 Normalize HUD latency severity using speech-relative STT speed (`rtf`) while preserving absolute STT delay display and audit logging fields (`speech_ms`, `rtf`) to reduce false "slow" signals on long utterances.
- [x] MP-195 Stop forwarding malformed/fragmented SGR mouse-report escape bytes into wrapped CLI input during interrupts so raw `[<...` fragments do not leak to users.
- [x] MP-196 Expand non-speech transcript sanitization for ambient-sound hallucination tags (`siren`, `engine`, `water` variants) before PTY delivery.
- [x] MP-111 Add governance hygiene automation for archive/ADR/script-doc drift (`python3 dev/scripts/devctl.py hygiene`) and codify archive/ADR lifecycle policy.
- [x] MP-122 Prevent mutation-lane timeout by sharding scheduled `cargo mutants` runs and enforcing one aggregated score across shards.

## Phase 2 - Overlay Quick Wins

- [x] MP-085 Voice macros and custom triggers (`.voiceterm/macros.yaml`).
- [x] MP-086 Runtime macros ON/OFF toggle (settings state + transcript transform gate).
- [x] MP-087 Restore baseline send-mode semantics (`auto`/`insert`) without an extra review-first gate.
- [x] MP-112 Add CI voice-mode regression lane for macros-toggle and send-mode behavior (`.github/workflows/voice_mode_guard.yml`).
- [x] MP-088 Persistent user config (`~/.config/voiceterm/config.toml`) for core preferences (landed runtime load/apply/save flow with CLI-precedence guards, explicit-flag detection for default-valued args, and status-state restore coverage for macros toggle).

## Phase 2A - Visual HUD Sprint (Current Priority)

- [x] MP-101 Add richer HUD telemetry visuals (sparkline/chart/gauge) with bounded data retention.
- [x] MP-100 Add animation transition framework for overlays and state changes (TachyonFX or equivalent).
- [x] MP-054 Optional right-panel visualization modes in minimal HUD.
- [x] MP-105 Add adaptive/contextual HUD layouts and state-driven module expansion.
- [x] MP-113 Tighten startup splash ergonomics and IDE compatibility (shorter splash duration, reliable teardown in IDE terminals, corrected startup tagline centering, and better truecolor detection for JetBrains-style terminals).
- [x] MP-114 Polish startup/theme UX in IDE terminals (remove startup top-gap, keep requested themes on 256-color terminals, and render Theme Picker neutral when current theme is `none`).
- [x] MP-115 Stabilize terminal compatibility regressions (drop startup arrow escape noise during boot, suppress Ctrl+V idle pulse dot beside `PTT`, and restore conservative ANSI fallback when truecolor is not detected).
- [x] MP-116 Fix JetBrains terminal HUD duplication by hardening scroll-region cursor restore semantics.
- [x] MP-117 Prevent one-column HUD wrap in JetBrains terminals (status-banner width guard + row truncation safety).
- [x] MP-118 Harden cross-terminal HUD rendering and PTY teardown paths (universal one-column HUD safety margin, writer-side row clipping to terminal width, and benign PTY-exit write error suppression on shutdown).
- [x] MP-119 Restore the stable `v1.0.53` writer/render baseline for Full HUD while retaining the one-column layout safety margin to recover reliable IDE terminal rendering.
- [x] MP-120 Revert unstable post-release scroll-region protection changes that reintroduced severe Full HUD duplication/corruption during active Codex output.
- [x] MP-121 Harden JetBrains startup/render handoff by auto-skipping splash in IDE terminals and clearing stale HUD/overlay rows on resize before redraw.
- [x] MP-123 Harden PTY/IPC backend teardown to signal process groups and reap child processes, with regression tests that verify descendant cleanup.
- [x] MP-183 Add a PTY session-lease guard that reaps backend process groups from dead VoiceTerm owners before spawning new sessions, without disrupting concurrently active sessions.
- [x] MP-190 Restore Full HUD shortcuts-row trailing visualization alignment so the right panel remains anchored to the far-right corner in full-width layouts.
- [x] MP-124 Add Full-HUD border-style customization (including borderless mode) and keep right-panel telemetry explicitly user-toggleable to `Off`.
- [x] MP-125 Fix HUD right-panel `Anim only` behavior so idle state keeps a static panel visible instead of hiding the panel until recording.
- [x] MP-126 Complete product/distribution naming rebrand to VoiceTerm across code/docs/scripts/app launcher, and add a PyPI launcher package scaffold (`pypi/`) for `voiceterm`.
- [x] MP-139 Tighten user-facing docs information architecture (entrypoint clarity, navigation consistency, and guide discoverability).
- [x] MP-104 Add explicit voice-state visualization (idle/listening/processing/responding) with clear transitions.
- [x] MP-055 Quick theme switcher in settings.
- [x] MP-102 Add toast notification center with auto-dismiss, severity, and history review (landed runtime status-to-toast ingestion with severity mapping, `Ctrl+N` notification-history overlay toggle, periodic auto-dismiss/re-render behavior, and input/parser/help/docs coverage for toast-history control flow).
- [x] MP-226 Fix Claude-mode command/approval prompt occlusion in active overlay sessions: when Claude enters interactive Bash approval or sandbox permission prompts (for example `Do you want to proceed?` while running `Bash(...)` or cross-worktree read prompts), VoiceTerm HUD/overlay rows can obscure prompt text and controls; implement a Claude-specific prompt-state rendering policy (overlay layering, temporary HUD suppression/resume, or reserved prompt-safe rows) so prompts remain readable/actionable without losing runtime status clarity, with non-regression validation for Codex, Cursor, and JetBrains terminals. (2026-02-27 follow-up hardening: suppression now targets high-confidence interactive approval/permission contexts only; low-confidence generic/composer text no longer triggers HUD suppression to avoid disappear/reappear flicker during normal Codex runs. Additional 2026-02-27 resilience update: terminal row/col resolution now normalizes zero-size IDE probes and writer startup redraw uses normalized size fallback so HUD resume/startup does not wait for a keypress. 2026-02-28 targeted overlay follow-up: numbered approval-card detection now suppresses HUD for sparse `1/2/3` option cards, suppression transitions synchronize normalized geometry with writer redraw, and Cursor transition pre-clear now scrubs stale border fragments during `ClearStatus` handoff paths. 2026-02-28 anti-cycle follow-up: Cursor non-rolling hosts no longer engage suppression from tool-activity text alone, and now use explicit/numbered approval-card hints for suppression engagement to prevent keypress-triggered HUD disappearance in normal composer flow.)
  - Repro note (2026-02-19): issue severity appears higher for local/worktree permission prompts during multi-tool explore batches (`+N more tool uses`), while some single-command Claude prompt flows appear acceptable.
  - Additional repro signal (2026-02-19): severity appears correlated with vertical UI density (long wrapped absolute command paths, larger active task list sections, and multi-line tool-batch summaries), suggesting row-budget/stacking pressure near bottom prompt rows.
  - Repro note (2026-02-19, screenshot evidence): during parallel/background-agent orchestration in Claude, long "workaround options" + permission-wall text can exceed available row budget and push prompt/action rows into unreadable overlap, while equivalent Codex sessions remain readable; treat this as a Claude-specific layout compaction/reserved-row failure case.
  - Evidence to capture per repro: terminal rows/cols, HUD mode/style, prompt type (single-command approval vs local/worktree permission), command preview line-wrap count, tool-batch summary presence (`+N more tool uses`), and screenshot before/after prompt render.
  - 2026-02-28 diagnostic follow-up: added gated Claude HUD tracing (`VOICETERM_DEBUG_CLAUDE_HUD=1`) across prompt-occlusion transitions and writer redraw/defer decisions to isolate a new Cursor+Claude normal-typing regression where HUD disappears after the first keypress (non-approval flow).
  - 2026-02-28 writer follow-up: tightened tool-activity suppression overmatch for plain transcript headings, added explicit stale-banner-anchor clearing in writer redraw, and added a short delayed Cursor+Claude typing repair redraw path to recover minimal-HUD line clobber without reintroducing per-keystroke flash.
  - 2026-02-28 minimal-HUD follow-up: Cursor+Claude typing-hold deferral now bypasses for active one-row HUD frames so minimal-HUD redraw is not postponed behind typing bursts, while full-HUD deferral policy remains unchanged.
  - 2026-02-28 traceability follow-up: Cursor+Claude writer debug logs now emit explicit user-input activity scheduling and enhanced-status render decisions (`prev/next banner height`, `hud_style`, `prompt_suppressed`), and pre/post transition flags are now computed from pre-apply state to prevent false-no-change traces while reproducing the remaining disappearance/overwrite regressions.
  - 2026-02-28 repaint follow-up: pre-clear transition redraws now force full banner repaint (no previous-line diff reuse) in Cursor+Claude paths, with explicit `transition redraw mode` debug traces to prove redraw mode on failing keypress/tool-output sequences.
  - 2026-02-28 non-rolling approval-window follow-up: Cursor non-rolling prompt suppression now keeps a short ANSI-stripped rolling approval window so split approval cards (`Do you want to proceed?` + later `1/2/...` options) still suppress HUD deterministically, while debug traces now log chunk/window match sources (`chunk_*` vs `window_*`) to distinguish real prompt hits from missed detections. Writer repair scheduling was also hardened so future Cursor+Claude repair deadlines are not cleared by unrelated redraws before they fire, reducing one-row HUD “disappear until refresh” loops during typing.
  - 2026-02-28 non-rolling release-gate + row-budget tracing follow-up: Cursor non-rolling suppression now requires explicit input-resolution arming plus drained approval window before release (prevents debounce-only unsuppress while approval context remains live), prompt-context fallback markers now keep detection active when backend label routing is noisy (`Tool use`, `Claude wants to`, `What should Claude do instead?`), Cursor Claude extra gap rows increased (`8 -> 10`), and `apply_pty_winsize` debug traces now emit backend/mode/rows/cols/reserved-rows/PTY-rows so overlay overlap can be diagnosed from logs instead of screenshots alone.
  - 2026-02-28 high-confidence guard follow-up: explicit/numbered approval hints now promote `prompt_guard_enabled` in non-rolling paths, so approval cards can suppress HUD even when backend-label guard signals are noisy; runtime debug chunk logs now include `backend_label` + `prompt_guard` booleans for direct branch tracing; non-rolling suppression semantics are now covered by deterministic thread-local test overrides (no shared env mutation races under parallel test execution).
  - 2026-03-01 stress-loop traceability follow-up: added deterministic Cursor+Claude stress artifact capture under `dev/reports/audits/claude_hud_stress/*` (frame snapshots + log counters + anomaly summaries), narrowed non-rolling release-arm consumption to substantial post-input activity, deferred release-arm relatch on window-only stale hints, and hardened writer typing-hold urgency detection for post-`ClearStatus` suppression transitions so approval/HUD churn can be diagnosed via logs and artifact IDs instead of screenshot-only loops. Current status remains partial (approval overlap reduced but not eliminated; see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.10).
  - 2026-03-01 rapid-approval hold + frame/log correlation follow-up: non-rolling input-resolution now arms an explicit sticky suppression hold window to avoid unsuppress gaps between consecutive approval cards, and `claude_hud_stress.py` now records frame timestamps plus bottom-row HUD visibility and correlates each frame to suppression-transition/redraw-commit log events for deterministic overlap attribution (see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.11). Local stress execution in this sandbox remains blocked by detached `screen` session startup failure, so fresh artifact generation is still pending a full terminal host.
  - 2026-03-01 wrapped-approval depth + anomaly-capture follow-up: expanded non-rolling approval scan depth (`2048 -> 8192` bytes, `12 -> 64` lines) so long wrapped option cards in Cursor prompt UIs continue matching numbered approval semantics, and added explicit anomaly logging for `explicit approval hint seen without numbered-match` to surface residual detector misses in runtime logs instead of relying on screenshots alone (see `dev/audits/2026-02-27-terminal-overlay-regression-audit.md` A2.12).
  - 2026-03-01 overlay occlusion closure follow-up: PTY startup winsize is now derived from measured terminal geometry before backend spawn (HUD-aware from frame 1), writer HUD rendering now fences PTY scrolling above reserved HUD rows via scroll-region controls, and resize transitions now force immediate redraw after pre-clear so grow/shrink cycles do not leave input rows hidden until another keypress.
  - 2026-03-01 JetBrains+Claude rendering follow-up: status/banner clear-to-EOL paths now reset ANSI attributes before trimming trailing columns so dark HUD style attributes cannot leak into typed prompt text, and JetBrains Claude extra gap rows now default to `2` for safer startup prompt/HUD separation.
  - 2026-03-01 post-v1.0.98 typing follow-up: JetBrains+Claude writer pre-clear now defers while user input is fresh (typing-hold window) so startup typing bursts do not destructively clear half-HUD rows before idle redraw can restore them.
- [x] MP-285 Standardize HUD policy across all backends: removed Gemini-specific compaction logic to ensure a consistent 4-row Full HUD experience and unified flicker-reduction behavior across Codex, Claude, and Gemini backends.

## Phase 2B - Rust Hardening Audit (Pre-Execution + Implementation)

- [x] MP-127 Replace IPC `/exit` hard process termination with graceful shutdown orchestration and teardown event guarantees (FX-001).
- [x] MP-128 Add explicit runtime ownership and bounded shutdown/join semantics for overlay writer/input threads (FX-002).
- [x] MP-129 Add voice-manager lifecycle hardening for quit-while-recording paths, including explicit stop/join policy and tests (FX-003).
- [x] MP-130 Consolidate process-group signaling/reaping helpers into one canonical utility with invariants tests (FX-004).
- [x] MP-131 Add security/supply-chain CI lane with policy thresholds and failing gates for high-severity issues (FX-005).
- [x] MP-132 Add explicit security posture/threat-model documentation and risky flag guidance (including permission-skip behavior) (FX-006).
- [x] MP-133 Enforce IPC auth timeout + cancellation semantics using tracked auth start timing (FX-007).
- [x] MP-134 Replace IPC fixed-sleep scheduling with event-driven receive strategy to reduce idle CPU jitter (FX-008).
- [x] MP-135 Decompose high-risk event-loop transition/wiring complexity to reduce change blast radius (FX-009).
- [x] MP-136 Establish unsafe-governance checklist for unsafe hotspots with per-invariant test expectations (FX-010).
- [x] MP-137 Add property/fuzz coverage lane for parser and ANSI/OSC boundary handling (FX-011).
- [x] MP-138 Enforce audit/master-plan traceability updates as a mandatory part of each hardening fix (FX-012).
- [x] MP-152 Consolidate hardening governance to `MASTER_PLAN` as the only active tracker: archive `RUST_GUI_AUDIT_2026-02-15.md` under `dev/archive/` and retire dedicated audit-traceability CI/tooling.

## Phase 2C - Theme System Upgrade (Architecture + Guardrails)

Theme Studio execution gate: MP-148..MP-182 are governed by the checklist in
this section. A Theme Studio MP may move to `[x]` only with documented pass
evidence for its mapped gates.

Theme/modularization integration rule: when refactors or fixes touch visual
runtime modules (`theme/*`, `theme_ops.rs`, `theme_picker.rs`, `status_line/*`,
`hud/*`, `writer/*`, `help.rs`, `banner.rs`), update or add the
corresponding `MP-148+` item here in `MASTER_PLAN` and attach mapped
`TS-G*` gate evidence from this section.

Settings-vs-Studio ownership matrix:

| Surface | Owner |
|---|---|
| Theme tokens/palettes, borders, glyph/icon packs, layout/motion behavior, visual state scenes, notification visuals, command-palette/autocomplete visuals | Theme Studio |
| Auto-voice/send-mode/macros, sensitivity/latency display mode, mouse mode, backend/pipeline, close/quit operations | Settings |
| Quick theme cycle and picker shortcuts | Shared entrypoint; deep editing still routes to Theme Studio |

Theme Studio Definition of Done (authoritative checklist):

| Gate | Pass Criteria | Fail Criteria | Required Evidence |
|---|---|---|---|
| `TS-G01 Ownership` | Theme Studio vs Settings ownership matrix is implemented and documented. | Any deep visual edit path remains in Settings post-migration. | Settings menu tests + docs diff. |
| `TS-G02 Schema` | `StylePack` schema/version/migration tests pass for valid + invalid inputs. | Parsing/migration panic, silent drop, or invalid pack applies without fallback. | Unit tests for parse/validate/migrate + fallback tests. |
| `TS-G03 Resolver` | All render paths resolve styles through registry/resolver APIs. | Hardcoded style constants bypass resolver on supported surfaces. | Coverage + static policy gate outputs. |
| `TS-G04 Component IDs` | Every renderable component/state has stable style IDs and defaults. | Unregistered component/state renders in runtime. | Component registry parity tests + snapshots. |
| `TS-G05 Studio Controls` | Every persisted style field is editable in Studio. | Any persisted field has no Studio control mapping. | Studio mapping parity test results. |
| `TS-G06 Snapshot Matrix` | Snapshot suites pass for widths, states, profiles, and key surfaces. | Layout overlap/wrap/clipping regressions vs expected fixtures. | Snapshot artifacts for narrow/medium/wide + state variants. |
| `TS-G07 Interaction UX` | Keyboard-only and mouse-enhanced flows both work with correct focus/hitboxes. | Broken focus order, unreachable controls, or hitbox mismatch. | Interaction integration tests + manual QA checklist output. |
| `TS-G08 Edit Safety` | Apply/save/import/export/undo/redo/rollback flows are deterministic. | User edits can be lost/corrupted or cannot be reverted safely. | End-to-end workflow tests across restart boundaries. |
| `TS-G09 Capability Fallback` | Terminal capability detection + fallback chains behave as specified. | Unsupported capability path crashes or renders unreadable output. | Compatibility matrix tests (truecolor/ansi, graphics/no-graphics). |
| `TS-G10 Runtime Budget` | Render/update paths remain within bounded allocation/tick budgets. | Unbounded buffers, allocation spikes, or frame-thrash in hot paths. | Perf/memory checks + regression benchmarks. |
| `TS-G11 Docs/Operator` | Architecture, usage, troubleshooting, and changelog are updated together. | User-visible behavior changes without aligned docs. | `docs-check` + updated docs references. |
| `TS-G12 Release Readiness` | Full Theme Studio GA validation bundle is green. | Any mandatory gate is missing evidence or failing. | CI report bundle + signoff checklist. |
| `TS-G13 Inspector` | Any rendered element can reveal style path and jump to Studio control. | Inspector cannot locate style ID/path for a rendered element. | Inspector integration tests + state preview tests. |
| `TS-G14 Rule Engine` | Conditional style rules are deterministic and conflict-resolved. | Rule priority conflicts or nondeterministic style outcomes. | Rule engine unit/property tests + scenario snapshots. |
| `TS-G15 Ecosystem Packs` | Third-party widget packs are allowlisted, version-compatible, and parity-mapped. | Dependency added without compatibility matrix or style/studio parity mapping. | Compatibility matrix + parity tests + allowlist audit. |

Theme Studio MP-to-gate mapping:

| MP | Required Gates |
|---|---|
| `MP-148` | `TS-G01`, `TS-G11` |
| `MP-149` | `TS-G02`, `TS-G06`, `TS-G09` |
| `MP-150` | `TS-G02`, `TS-G03` |
| `MP-151` | `TS-G11` |
| `MP-161` | `TS-G03`, `TS-G06`, `TS-G07` |
| `MP-162` | `TS-G03`, `TS-G05` |
| `MP-163` | `TS-G03` |
| `MP-172` | `TS-G04`, `TS-G06` |
| `MP-174` | `TS-G03`, `TS-G05`, `TS-G06` |
| `MP-175` | `TS-G09`, `TS-G15` |
| `MP-176` | `TS-G09`, `TS-G06` |
| `MP-179` | `TS-G15` |
| `MP-180` | `TS-G15`, `TS-G05`, `TS-G06` |
| `MP-182` | `TS-G14`, `TS-G05`, `TS-G06` |
| `MP-164` | `TS-G07` |
| `MP-165` | `TS-G01`, `TS-G07` |
| `MP-166` | `TS-G05`, `TS-G08`, `TS-G07` |
| `MP-167` | `TS-G06`, `TS-G09`, `TS-G10`, `TS-G11`, `TS-G12` |
| `MP-173` | `TS-G03`, `TS-G05`, `TS-G15` |
| `MP-177` | `TS-G15`, `TS-G05` |
| `MP-178` | `TS-G13`, `TS-G07` |
| `MP-181` | `TS-G07`, `TS-G10` |

Theme Studio mandatory verification bundle (per PR):

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py docs-check --user-facing`
- `python3 dev/scripts/devctl.py hygiene`
- `cd rust && cargo test --bin voiceterm`
- use `.github/PULL_REQUEST_TEMPLATE/theme_studio.md` for `TS-G01`..`TS-G15` evidence capture.

- [x] MP-148 Activate the Theme Studio phased track in `MASTER_PLAN` and lock the IA boundary: dedicated `Theme Studio` mode (not `Settings -> Studio`) plus Settings-vs-Studio ownership matrix (landed gate catalog + MP-to-gate map + ownership matrix directly in Phase 2C so visual modularization/fix work now maps to one canonical tracker).
- [x] MP-149 Implement Theme Upgrade Phase 0 safety rails (golden render snapshots, terminal compatibility matrix coverage, and style-schema migration harness) before any user-visible editor expansion (landed style-schema migration harness in `theme/style_schema.rs`, terminal capability matrix tests in `color_mode`, and golden snapshot-matrix coverage for startup banner, theme picker, and status banner render outputs).
- [x] MP-150 Implement Theme Upgrade Phase 1 style engine foundation (`StylePack` schema + resolver + runtime), preserving current built-in theme behavior and startup defaults (landed runtime resolver scaffold `theme/style_pack.rs`, routed `Theme::colors()` through resolver with palette-parity regression tests, enabled runtime schema parsing/migration (`theme/style_schema.rs`) for pack payload ingestion, and hardened schema-version mismatch/invalid-payload fallback to preserve base-theme palettes instead of dropping to `none`).
- [x] MP-151 Ship docs/architecture updates for the new theme system (`dev/ARCHITECTURE.md`, `guides/USAGE.md`, `guides/TROUBLESHOOTING.md`, `dev/CHANGELOG.md`) in lockstep with implementation, including operator guidance, settings-migration guidance, and fallback behavior (landed runtime resolver path docs, schema payload operator guidance, explicit settings-migration notes, and invalid-pack fallback behavior across architecture/usage/troubleshooting/changelog docs).

## Phase 2D - Visual Surface Expansion (Theme Studio Prerequisite)

- [ ] MP-161 Execute a visual-first runtime pass before deep Studio editing: with MP-102 complete, promote MP-103, MP-106, MP-107, MP-108, and MP-109 from Backlog into active execution order with non-regression gates (in progress: toast-history overlay row-width accounting and title rendering were hardened so unicode/ascii glyph themes keep border alignment without stale right-edge artifacts).
- [ ] MP-162 Extend `StylePack` schema/resolver so each runtime visual surface is style-pack addressable (widgets/graphs, toasts, voice-state scenes, command palette, autocomplete, dashboard surfaces), even before all Studio pages ship (in progress: schema/resolver now supports runtime visual overrides for border glyph sets, indicator glyph families, and glyph-set profile selection (`glyphs`: `unicode`/`ascii`) via style-pack payloads, including compact/full/minimal/hidden processing/responding indicator lanes in status rendering while preserving default processing spinner animation unless explicitly overridden; 2026-03-07 aligned next slice: persisted payload-driven runtime routing must close `surfaces.toast_position`, `surfaces.startup_style`, `components.toast_severity_mode`, and `components.banner_style`, not just runtime-only Theme Studio overrides. 2026-03-09 Codex re-review: the status-line ASCII separator leak is closed, but persisted payload-driven consumer proof is still incomplete for those startup/toast/banner fields; keep MP-162 open until consumer-level coverage lands, not just resolver wiring.)
- [x] MP-163 Add explicit coverage tests/gates that fail if new visual runtime surfaces bypass theme resolver paths with hardcoded style constants (landed `theme::tests::runtime_sources_do_not_bypass_theme_resolver_with_palette_constants`, a source-policy gate that scans runtime Rust modules and fails when `THEME_*` palette or `BORDER_*` border constants are referenced outside theme resolver/style-ownership allowlist files).
- [ ] MP-172 Add a styleable component registry and state-matrix contract for all renderable control surfaces (buttons, tabs, lists, tables, trees, scrollbars, modal/popup/tooltip, input/caret/selection) with schema + resolver + snapshot coverage (2026-03-07 alignment note: `theme::component_registry` is still gated by `theme_studio_v2`; the next slice must make that boundary explicit and separate live vs planned registry inventory before registry-backed Studio or CI parity becomes authoritative).
- [ ] MP-174 Migrate existing non-HUD visual surfaces into `StylePack` routing (startup splash/banner, help/settings/theme-picker chrome, calibration/mic-meter visuals, progress bars/spinners, icon/glyph sets) so no current visual path is left outside Theme Studio ownership (in progress: processing/progress spinner rendering paths now resolve through theme/style-pack indicators instead of hardcoded frame constants, glyph-family routing now drives HUD queue/latency/meter symbols + status-line waveform placeholders/pulse dots + progress bar/block/bounce glyphs, `components.progress_bar_family` now routes progress/meter glyph profiles through style-pack resolution, audio-meter calibration/waveform rendering resolves bar/wave/marker glyphs from the shared theme profile, overlay chrome/footer/slider glyphs across help/settings/theme-picker now route through the active glyph profile with footer close hit-testing parity for unicode/ascii separators, startup banner/footer separators now honor glyph-set overrides (`unicode`/`ascii`) across full/compact/minimal banner variants, explicit spinner-style overrides now fall back to ASCII-safe animation frames when glyph profile is ASCII, theme-switch interactions now surface explicit style-pack lock state (read-only/dimmed picker + locked status messaging) when schema payload `base_theme` is active, component-level border routing now resolves `components.overlay_border` across overlay surfaces including transcript-history plus `components.hud_border` for Full-HUD `Theme` border mode through style-pack resolver paths, and 2026-03-09 follow-up hardening routed the remaining status-line full/single-line/compact separators through glyph-aware helpers so ASCII packs stop leaking `│` / `·`; the remaining helper-routing follow-up is now toast severity icons, HUD mode glyphs, and audio-meter markers before introducing additional style-pack fields; post-slice cleanup landed: glyph tables/resolver helpers plus their focused tests extracted from `theme/mod.rs` into `theme/glyphs.rs`. 2026-03-09 Codex re-review confirmed the separator fix but keeps MP-174 open until the remaining helper-routing follow-up lands with focused proof.)
- [x] MP-175 Add a framework capability matrix + parity gate for shipped framework versions (Ratatui widget/symbol families and Crossterm color/input/render capabilities, including synchronized updates + keyboard enhancement flags), and track upgrade deltas before enabling new Studio controls (landed `theme/capability_matrix.rs` with `RatatuiWidget`/`RatatuiSymbolFamily`/`CrosstermCapability` enums, `FrameworkCapabilitySnapshot` pinned at ratatui 0.30 + crossterm 0.29, `check_parity()` gate detecting unregistered widgets and unmapped symbols, `compute_upgrade_delta()` for version transition tracking, `theme_capability_compatible()` for theme/terminal validation, and 18 passing tests covering snapshot parity, delta detection, and breaking-change gates; TS-G09 + TS-G15 evidence).
- [x] MP-176 Implement terminal texture/graphics capability track (`TextureProfile` + adapter policy): symbol-texture baseline for all terminals plus capability-gated Kitty/iTerm2 image paths with enforced fallback chain tests (landed `theme/texture_profile.rs` with `TextureTier` fallback chain (KittyGraphics > ITermInlineImage > Sixel > SymbolTexture > Plain), `SymbolTextureFamily` enum (shade/braille/block/line), `TextureProfile` with max/active tier + terminal detection, `TerminalId` enum covering Kitty/iTerm2/WezTerm/Foot/Mintty/VsCode/Cursor/JetBrains/Alacritty/Warp/Generic/Unknown, environment-based detection via TERM_PROGRAM/TERMINAL_EMULATOR/KITTY_WINDOW_ID/ITERM_SESSION_ID, `resolve_texture_tier()` enforcing fallback chain, and `texture_profile_with_override()` for style-pack tier overrides; 20 passing tests covering fallback ordering, tier resolution, terminal detection, and profile construction; TS-G09 + TS-G06 evidence).
- [x] MP-179 Add dependency baseline strategy for Theme Studio ecosystem packs (Ratatui/Crossterm version pin policy + compatibility matrix + staged upgrade plan) so third-party widget adoption does not fragment resolver/studio parity (landed `theme/dependency_baseline.rs` with `DependencyPin` structs for ratatui 0.30 and crossterm 0.29, `CompatibilityEntry`/`CompatibilityStatus` matrix covering tui-textarea/tui-tree-widget/throbber-widgets-tui/tui-popup/tui-scrollview/tui-big-text/tui-prompts/ratatui-image/tuirealm with per-dep ratatui+crossterm compat status, `UpgradeStep` staged plan (crossterm 0.30 before ratatui 0.31), `check_crate_compatibility()`/`check_pack_compatibility()` policy gates blocking unknown/incompatible crates, and `validate_pin_against_cargo()` for CI pin verification; 19 passing tests covering pin validation, matrix queries, compatibility semantics, and upgrade ordering; TS-G15 evidence).
- [x] MP-180 Pilot a curated widget-pack integration lane (`tui-widgets` family, `tui-textarea`, `tui-tree-widget`, `throbber-widgets-tui`) under style-ID/allowlist gates, with parity tests before feature flags graduate (landed `theme/widget_pack.rs` with `PackMaturity` lifecycle (Candidate > Pilot > Graduated > Retired), `WidgetPackEntry` registry with per-pack `StyleIdScope` namespaces and `ParityRequirement` gates, 6-entry `WIDGET_PACK_REGISTRY` (tui-textarea/tui-tree-widget/throbber-widgets-tui at Pilot; tui-popup/tui-scrollview/tui-big-text at Candidate), `GraduationCheckResult`-based gate blocking pilot packs with unmet parity requirements, `find_pack()`/`active_packs()`/`packs_at_maturity()` queries, `style_id_is_pack_owned()`/`owning_pack_for_style_id()` ownership resolution, and scope overlap detection; 21 passing tests covering registry integrity, scope isolation, maturity ordering, graduation gates, and ownership queries; TS-G15 + TS-G05 + TS-G06 evidence).
- [x] MP-182 Add `RuleProfile` no-code visual automation (threshold/context/state-driven style overrides) with deterministic priority semantics, preview tooling, and snapshot coverage (landed `theme/rule_profile.rs` with `RuleCondition` tagged-union supporting VoiceState/Threshold/Backend/Capability/ColorMode/All/Any conditions, `ThresholdMetric` enum (queue-depth/latency-ms/audio-level-db/terminal-width/terminal-height), `StyleOverride`/`OverrideEntry` for property-level style mutations, `StyleRule` with priority-based conflict resolution and enable/disable toggle, `RuleProfile` with add/remove/toggle operations and `active_rules()` priority-sorted accessor, `evaluate_condition()`/`evaluate_rules()` engine with deterministic first-match-per-key semantics, `preview_rules()` for Studio preview tooling, `parse_rule_profile()` JSON deserialization with nested condition support, and `RuleProfileError` for duplicate/not-found rule operations; 33 passing tests covering condition evaluation, priority semantics, conflict resolution, nested conditions, JSON parsing, and preview output; TS-G14 + TS-G05 + TS-G06 evidence).

## Phase 2E - Theme Studio Delivery (After Visual Surface Expansion)

- [x] MP-164 Implement dedicated `Theme Studio` overlay mode entry points/navigation and remove deep theme editing from generic Settings flows (landed `OverlayMode::ThemeStudio` with dedicated renderer/state selection, routed `Ctrl+Y`/theme-button entrypoints and cross-overlay theme hotkey flows into Theme Studio, added keyboard/mouse navigation (`Enter` action routing to Theme Picker/close plus arrow/ESC handling), wired periodic resize rerender + PTY reserved-row budgeting for Theme Studio mode, and covered interaction/status-row updates with new event-loop/theme-studio/status-line regression tests; TS-G07 evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-165 Migrate legacy visual controls out of settings list (`SettingsItem::Theme`, `SettingsItem::HudStyle`, `SettingsItem::HudBorders`, `SettingsItem::HudPanel`, `SettingsItem::HudAnimate`) so Settings keeps non-theme runtime controls only (landed by removing those rows from `SETTINGS_ITEMS`, preserving quick visual controls via `Ctrl+Y`/`Ctrl+G` theme paths plus `Ctrl+U` HUD-style cycling outside Settings).
- [ ] MP-166 Deliver Studio page control parity for all `StylePack` fields (tokens, layout, widgets, motion, behavior, notifications, command/discovery surfaces, voice-state scenes, startup/wizard/progress/texture surfaces, accessibility, keybinds, profiles) with undo/redo + rollback (in progress: Theme Studio now includes interactive visual-control rows for existing runtime styling (`HUD style`, `HUD borders`, `Right panel`, `Panel animation`) plus live `StylePack` runtime overrides for `Glyph profile`, `Indicator set`, `Progress spinner`, `Progress bars`, `Theme borders`, `Voice scene`, `Toast position`, `Startup splash`, `Toast severity`, and `Banner style`, all adjustable with Enter and Left/Right controls and live current-value labels; overlay rendering now uses settings-style `label + [ value ]` rows with selected-row highlighting, a dedicated `tip:` description row, wider studio-width clamps (`60..=82`), and footer hints that expose left/right adjustment controls; runtime style-pack override edit safety is now wired with dedicated `Undo edit`, `Redo edit`, and `Rollback edits` rows backed by bounded in-session history; Theme Studio input dispatch now routes through page-scoped helper handlers with shared global-key processing and focused runtime-style adjustment routing in `theme_studio_input.rs`, and home-page row rendering now uses structured row metadata with static tip ownership; 2026-03-09 bounded Components-page slice landed: `components_page.rs` now drills down `group -> component -> state` over canonical `style_id` rows, cycles local preview property edits through `StyleResolver`-owned `ResolvedComponentStyle`, and stays scoped away from `theme_studio_input.rs` / `component_registry.rs`; deep multi-page style-pack parity (`tokens`, `layout/motion`, broader field mapping), live reachability/persistence wiring, and `dead_code` allowance removal remain pending; 2026-03-07 aligned next slice: Components page work must edit `ResolvedComponentStyle` keyed by `(style_id, state)` and must not introduce per-component `ThemeColors` maps).
- [ ] MP-167 Run Theme Studio GA validation and docs lockstep updates (snapshot matrix, terminal compatibility matrix, architecture docs, user docs, troubleshooting guidance, changelog entry).
- [ ] MP-173 Add CI policy gates for future visuals: fail if a new renderable component lacks style-ID registration, and fail if post-parity a style-pack field lacks Studio control mapping (in progress: framework capability parity now fails on any newly added Ratatui widget/symbol without registration/mapping coverage, component-registry tests now require exact inventory parity plus unique stable style IDs, and Theme Studio now enforces explicit style-pack field classification (`mapped` vs `deferred`) with the post-parity gate enabled (`STYLE_PACK_STUDIO_PARITY_COMPLETE = true`) so mapping tests now require zero deferred style-pack fields; 2026-03-07 aligned next slice: registry-backed CI gates must count live renderable components only after the MP-172 live/planned boundary is explicit).
- [ ] MP-177 Add widget-pack extensibility parity (first-party plus allowlisted third-party widgets) so newly adopted widget families must register style IDs + resolver bindings + Studio controls before GA.
- [ ] MP-178 Add Theme Studio element inspector parity so users can select any rendered element and jump directly to component/state style controls (with state preview and style-path tracing).
- [ ] MP-181 Add advanced Studio interaction parity (resizable splits, drag/reorder, scrollview-heavy forms, large text/editor fields) with full keyboard fallback and capability-safe mouse behavior.

## Phase 3 - Overlay Differentiators

- [x] MP-090 Voice terminal navigation actions (scroll/copy/error/explain).
- [x] MP-140 Define and enforce macro-vs-navigation precedence (macros first, explicit built-in phrase escape path).
- [x] MP-141 Add Linux clipboard fallback support for voice `copy last error` (wl-copy/xclip/xsel).
- [x] MP-142 Add `devctl docs-check` commit-range mode for post-commit doc audits on clean working trees.
- [x] MP-156 Add release-notes automation (`generate-release-notes.sh`, `devctl release-notes`, `release.sh` notes-file handoff) so each tag has consistent diff-derived markdown notes for GitHub releases.
- [x] MP-144 Add macro-pack onboarding wizard hardening (expanded developer command packs, repo-aware placeholder templating, and optional post-install setup prompt).
- [x] MP-143 Decompose `voice_control/drain.rs` and `event_loop.rs` into smaller modules to reduce review and regression risk (adjacent runtime architecture debt; tracked separately from tooling-control-plane work).
  - [x] MP-143a Extract shared settings-item action dispatch in `event_loop.rs` so Enter/Left/Right settings paths stop duplicating mutation logic.
  - [x] MP-143b Split `event_loop.rs` overlay/input/output handlers into focused modules (`overlay_dispatch`, `input_dispatch`, `output_dispatch`, `periodic_tasks`) and move tests to `event_loop/tests.rs` while preserving regression coverage.
  - [x] MP-143c0 Move `voice_control/drain.rs` tests into `voice_control/drain/tests.rs` so runtime decomposition can land in smaller, reviewable slices.
  - [x] MP-143c1 Extract `voice_control/drain/message_processing.rs` for macro expansion, status message handling, and latency/preview helpers.
  - [x] MP-143c Split `voice_control/drain.rs` into transcript-delivery (`transcript_delivery.rs`), status/latency updates (`message_processing.rs`), and auto-rearm/finalize components (`auto_rearm.rs`) with unchanged behavior coverage.
- [x] MP-182 Decompose `ipc/session.rs` by extracting non-blocking codex/claude/voice/auth event processors into `ipc/session/event_processing/`, keeping command-loop orchestration in `session.rs` and preserving IPC regression coverage.
- [x] MP-170 Harden IPC test event capture isolation so parallel test runs remain deterministic under `cargo test` and `devctl check --profile ci`.
- [x] MP-091 Searchable transcript history and replay workflow (landed `Ctrl+H` overlay with bounded history storage, type-to-filter search, and replay-to-PTY integration plus event-loop/help wiring).
- [x] MP-229 Upgrade transcript-history from transcript-only snippets to source-aware conversation memory capture (`mic`/`you`/`ai`) with wider rows, selected-entry preview, control-sequence-safe search input (`\x1b[0[I`/focus noise no longer leaks into query text), non-replayable guardrails for assistant-output rows, and opt-in markdown session memory logging (`--session-memory`, `--session-memory-path`) for project-local conversation archives.
- [x] MP-199 Add wake-word runtime controls in settings/config (`OFF`/`ON`, sensitivity, cooldown), defaulting to `OFF` for release safety (landed overlay config flags `--wake-word`, `--wake-word-sensitivity`, `--wake-word-cooldown-ms`; settings overlay items + action handlers for wake toggle/sensitivity/cooldown; regression coverage in `settings_handlers::tests`).
- [x] MP-200 Add low-power always-listening wake detector runtime with explicit start/stop ownership and bounded shutdown/join semantics (landed `wake_word` runtime owner with local detector thread lifecycle, settings-driven start/stop reconciliation, bounded join timeout on shutdown, and periodic capture-active pause sync to avoid recorder contention).
- [x] MP-201 Route wake detections through the existing `Ctrl+R` capture path so wake-word and manual recording share one recording/transcription pipeline (landed shared trigger handling in `event_loop/input_dispatch.rs` so wake detections and manual `Ctrl+R` use the same start-capture path; wake detections ignore active-recording stop toggles by design).
- [x] MP-202 Add debounce and false-positive guardrails plus explicit HUD privacy indicator while wake-listening is active (landed explicit Full-HUD wake privacy badge states `Wake: ON`/`Wake: PAUSED`, plus stricter short-utterance wake phrase gating so long/background mentions are ignored before trigger delivery).
- [x] MP-203 Add wake-word regression + soak validation gates (unit/integration/lifecycle tests and long-run false-positive/latency checks) and require passing evidence before release/tag (landed deterministic wake runtime lifecycle tests via spawn-hooked listener ownership checks, expanded detection-path regression tests, long-run hotword false-positive/latency soak test, reusable guard script `dev/scripts/tests/wake_word_guard.sh`, `devctl check --profile release` wake-guard integration, and dedicated CI lane `.github/workflows/wake_word_guard.yml`).
- [x] MP-286 Add an image-capture interaction mode for Codex sessions: expose a persistent ON/OFF mode, show a concise HUD indicator, support click/hotkey capture triggers, and inject a capture prompt with saved image path into the active PTY so users can run picture-assisted chats without leaving VoiceTerm (landed `image_mode.rs` capture pipeline with platform-default command fallback + configurable `--image-capture-command`, added persistent `--image-mode` runtime toggle in CLI/settings/config, added `IMG` status badge, and routed manual trigger paths (`Ctrl+R` + rec button) to image capture only when image mode is enabled while preserving normal voice-record behavior when disabled; capture injects `Please analyze this image file: <path>` into active PTY respecting send mode (`auto` send with newline vs `insert` staged text); docs/changelog/help/flags updated in `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `dev/CHANGELOG.md`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-287 Resume a scoped slice of deferred Dev Mode behind a guarded launch flag: add `--dev` activation (with `--dev-mode`/`-D` aliases), keep default runtime behavior unchanged when absent, and surface explicit in-session mode visibility for dev-only experimentation (landed guarded CLI gate `--dev` with aliases in `config/cli.rs`, wired runtime state to `StatusLineState`, and added a `DEV` Full-HUD badge path so guarded mode is explicit only when enabled; default launch behavior remains unchanged when flag is absent; docs/changelog/help groups updated in `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `dev/CHANGELOG.md`, and `custom_help.rs`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-288 Start deferred Dev Mode foundation by introducing a shared `rust/src/devtools/` core (stable event schema + bounded in-memory session aggregator) and wiring guarded `--dev` runtime capture events into that shared model without changing non-dev runtime behavior (landed new shared `voiceterm::devtools` module with schema-versioned `DevEvent` model + bounded `DevModeStats` ring buffer/session snapshot aggregation in `rust/src/devtools/events.rs` and `rust/src/devtools/state.rs`, exported via `rust/src/devtools/mod.rs` and `rust/src/lib.rs`; runtime bridge now instantiates guarded in-memory dev stats only when `--dev` is enabled (`main.rs`) and records transcript/empty/error voice-job events from the existing drain path without affecting default mode (`event_state.rs`, `event_loop.rs`, `voice_control/drain.rs`); verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-289 Add guarded Dev Mode logging controls and on-disk event persistence: introduce `--dev-log` + `--dev-path`, enforce `--dev` guardrails, and append captured dev events to session JSONL files under the configured dev path without changing non-dev behavior (landed guarded CLI flags `--dev-log` and `--dev-path` in `config/cli.rs` with startup validation gates in `main.rs` (`--dev-log`/`--dev-path` now require `--dev`, and `--dev-path` requires `--dev-log`), added shared dev-event JSONL persistence in `rust/src/devtools/storage.rs` (`DevEventJsonlWriter`, per-session `session-*.jsonl` files under `<dev-root>/sessions/`, default dev root `$HOME/.voiceterm/dev` with `<cwd>/.voiceterm/dev` fallback), and wired runtime logging through the existing guarded voice-drain path so captured dev events append on transcript/empty/error messages only when guarded logging is enabled (`event_state.rs`, `event_loop.rs`, `voice_control/drain.rs`); default non-dev runtime behavior remains unchanged; docs/help/changelog updated in `guides/CLI_FLAGS.md`, `guides/USAGE.md`, `README.md`, `QUICK_START.md`, `custom_help.rs`, and `dev/CHANGELOG.md`; verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `cd rust && cargo test --bin voiceterm`).
- [x] MP-290 Extend Dev CLI reporting with guarded Dev Mode session telemetry summaries: add optional `--dev-logs` support to `devctl status`/`devctl report` (plus `--dev-root` and `--dev-sessions-limit`) so maintainers can inspect recent `session-*.jsonl` event counts/latency/error summaries without opening raw files (landed `collect_dev_log_summary()` in `dev/scripts/devctl/collect.py`, wired CLI flags in `dev/scripts/devctl/cli.py`, rendered markdown/json summary blocks in `dev/scripts/devctl/commands/status.py` and `dev/scripts/devctl/commands/report.py`, and added regression coverage in `dev/scripts/devctl/tests/test_collect_dev_logs.py`, `dev/scripts/devctl/tests/test_status.py`, and `dev/scripts/devctl/tests/test_report.py`; verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_collect_dev_logs dev.scripts.devctl.tests.test_status dev.scripts.devctl.tests.test_report`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`).
- [x] MP-291 Add a guarded `Ctrl+D` Dev panel overlay for `--dev` sessions: landed new `dev_panel.rs` formatter/render contract (read-only guard/logging/session-counter view), added `InputEvent::DevPanelToggle` parsing for raw `Ctrl+D` (`0x04`) and CSI-u `Ctrl+D`, wired guarded toggle behavior (`--dev` opens/closes panel; non-dev forwards `Ctrl+D` EOF byte to PTY so legacy behavior is preserved), introduced `OverlayMode::DevPanel` rendering/open/close/resize/mouse/reserved-row handling (`event_loop.rs`, `overlay_dispatch.rs`, `periodic_tasks.rs`, `overlay_mouse.rs`, `terminal.rs`, `overlays.rs`), and updated shortcut/help docs (`help.rs`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `README.md`, `QUICK_START.md`, `dev/CHANGELOG.md`); verification evidence: `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `cd rust && cargo check --bin voiceterm`, `cd rust && cargo test --bin voiceterm`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-295 Harden prompt-occlusion guardrails for Codex/Claude reply boxes: extend `prompt/claude_prompt_detect.rs` detection beyond approval-only patterns to include reply/composer prompt markers (including Unicode prompt glyphs and Codex command-composer hint text), enable the guard for both Codex and Claude backend labels during startup (`main.rs`), preserve zero-row HUD suppression + PTY row-budget restore behavior when suppression toggles (`prompt/mod.rs`, `event_loop` suppression path), and keep reply/composer suppression active while users type (clear only on submit/cancel input instead of every typed byte); docs/changelog updated in `guides/TROUBLESHOOTING.md`, `dev/ARCHITECTURE.md`, and `dev/CHANGELOG.md`; verification evidence: `cd rust && cargo test claude_prompt_detect --bin voiceterm`, `cd rust && cargo test reply_composer_ --bin voiceterm`, `cd rust && cargo test set_claude_prompt_suppression_updates_pty_row_budget --bin voiceterm`, `cd rust && cargo test periodic_tasks_clear_stale_prompt_suppression_without_new_output --bin voiceterm`, `python3 dev/scripts/devctl.py check --profile ci`, `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [ ] MP-301 Investigate intermittent wake/send reliability for real-world speech variants (for example `hate codex`, `hate cloud`, and while-speaking submit attempts) using targeted matcher tests plus transcript-level debug evidence.
  - [x] Initial slice: expand wake alias/send-intent coverage (`hate`/`pay` -> `hey`, `cloud`/`clog` -> `claude`, plus `send it` / `sending` / `sand`) and emit wake transcript decision traces in debug logs (`voiceterm --logs --log-content`).
  - [x] Reliability slice (2026-02-27): align wake-listener VAD threshold to live mic-sensitivity baseline (plus wake headroom) so wake detection tracks the same voice setup users already tuned for normal capture; also relaxed short wake-capture bounds (`min speech`, `lookback`, `silence tail`) and expanded `claude` alias normalization (`claud`, `clawed`) for lower-effort phrase pickup without shouting.
  - [ ] Follow-up slice: collect reproducible field log samples and tune mid-utterance submit heuristics without increasing false positives from background conversation.

## Phase 3B - Tooling Control Plane Consolidation

- [x] MP-157 Execute tooling-control-plane consolidation (archived at `dev/archive/2026-02-17-tooling-control-plane-consolidation.md`): implement `devctl ship`, deterministic step exits, dry-run behavior, machine-readable step reports, and adapter conversion for release entry points.
- [x] MP-158 Harden `devctl docs-check` policy enforcement so docs requirements are change-class aware and deprecated maintainer command references are surfaced as actionable failures.
- [x] MP-159 Add a dedicated tooling CI quality lane for `devctl` command behavior and maintainer shell-script integrity (release, release-notes, PyPI, Homebrew helpers).
- [x] MP-160 Canonicalize maintainer docs and macro/help surfaces to `devctl` first (`AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, maintainer macro packs, and `Makefile` help), keeping legacy wrappers documented as transitional adapters.
- [x] MP-302 Expand docs-governance control plane and process traceability: enforce strict tooling docs checks plus conditional strict user-facing docs checks in CI, add markdown/image/CLI-flag integrity guards, block accidental root `--*` artifact files, and document handoff/source-of-truth workflow for both human and AI contributors.
- [x] MP-239 Reorganize `AGENTS.md` into an agent-first execution router (task classes, context packs, normal-push vs release workflows, branch sync policy, command bundles, and explicit autonomy/guardrail rules) so AI contributors can deterministically choose the right docs, tools, and checks for each task.
- [x] MP-245 Refine `AGENTS.md` and `dev/DEVELOPMENT.md` into an index-first, user-story-driven execution system: add explicit start-up bootstrap steps, dirty-tree protocol, single-source command bundles, CI lane mapping by risk/path, release version-parity checks (`Cargo.toml` + `pyproject.toml` + macOS `Info.plist` + changelog) with a dedicated parity guard (`dev/scripts/checks/check_release_version_parity.py`), add an AGENTS-structure guard (`dev/scripts/checks/check_agents_contract.py`), and add an active-plan registry/sync guard (`dev/scripts/checks/check_active_plan_sync.py` + `dev/active/INDEX.md`) so SOP/router/bundle and active-doc discovery contracts fail early in local/CI governance checks.
- [x] MP-256 Add an orphaned-test process guardrail to tooling governance by extending `devctl hygiene` to detect leaked `target/debug/deps/voiceterm-*` binaries (error on detached `PPID=1` candidates, warning on active runs), then harden `devctl check` with automatic pre/post orphaned-test cleanup sweeps so interrupted local runs do not accumulate stale test binaries across worktrees.
- [x] MP-258 Automate PyPI publish in release flow by adding `.github/workflows/publish_pypi.yml` (triggered on `release: published`) and aligning maintainer docs so release runs publish through GitHub Actions while `devctl pypi --upload --yes` remains an explicit fallback path.
- [x] MP-259 Automate Codecov coverage uploads by adding `.github/workflows/coverage.yml` (Rust `cargo llvm-cov` LCOV generation + Codecov OIDC upload) and aligning maintainer docs/lane mapping so the README coverage badge is backed by current CI reports instead of `unknown`.
- [x] MP-260 Add non-regressive source-shape guardrails for Rust/Python so oversized files cannot silently drift into new God-file debt: add `dev/scripts/checks/check_code_shape.py` (working-tree + commit-range modes with soft/hard file-size limits and oversize-growth budgets), wire it into `tooling_control_plane.yml`, and add bundle/docs coverage for local maintainer runs.
- [x] MP-261 Refresh README brand banner with a new VoiceTerm hero logo asset (`img/logo-hero.png`) based on the finalized artwork while keeping subtitle/icon identity and removing redundant platform chips from the banner artwork itself (README remains the only consumer; generation script exploration was one-off and not retained in repo tooling).
- [x] MP-282 Consolidate visual planning docs by folding `dev/active/overlay.md` and `dev/active/theme_studio_redesign.md` into `dev/active/theme_upgrade.md`, then update active-index/sync-governance references so one canonical visual spec remains.
- [x] MP-283 Harden release distribution automation by adding a CI release preflight lane (`release_preflight.yml`), a Homebrew publish workflow path (`publish_homebrew.yml`), and safety guards for Homebrew tarball/SHA validation plus `devctl ship` release-version parity enforcement before CI/local publish steps.
- [x] MP-284 Reconcile ADR inventory to runtime truth: remove stale unimplemented proposal ADRs, promote architecture ADRs that match shipped behavior (overlay mode, runtime config precedence, session history boundaries, writer render invariants), and add missing ADR coverage for wake-word ownership, voice-macro precedence, and Claude prompt-safe HUD suppression.
- [x] MP-292 Refactor `devctl` internals to reduce module size, remove command-output drift, and harden missing-binary behavior: extracted shared process-sweep helpers (`dev/scripts/devctl/process_sweep.py`) for `check`/`hygiene`, shared `check` profile normalization (`dev/scripts/devctl/commands/check_profile.py`), shared status/report payload+markdown rendering (`dev/scripts/devctl/status_report.py`), split ship orchestration from step/runtime helpers (`dev/scripts/devctl/commands/ship.py`, `dev/scripts/devctl/commands/ship_common.py`, `dev/scripts/devctl/commands/ship_steps.py`), extracted hygiene audit helpers (`dev/scripts/devctl/commands/hygiene_audits.py`), updated `run_cmd`/ship command checks to return structured failures instead of uncaught Python exceptions when required binaries are missing, and rewrote helper/module docstrings in plain language so junior developers and AI agents can quickly understand when/why each helper exists; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-293 Add a dedicated `devctl security` command so maintainers can run a local security gate aligned with CI policy: landed `dev/scripts/devctl/commands/security.py` (RustSec JSON capture + policy enforcement + optional `zizmor` workflow scan with `--require-optional-tools` strict mode), extracted security CLI parser wiring into `dev/scripts/devctl/security/parser.py` to keep `dev/scripts/devctl/cli.py` below code-shape growth limits, wired list output in `dev/scripts/devctl/commands/listing.py`, added regression coverage in `dev/scripts/devctl/tests/test_security.py`, expanded plain-language process-sweep context for interrupted/stalled test cleanup in `dev/scripts/devctl/process_sweep.py`, and updated maintainer/governance docs (`AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`); verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py security --dry-run --with-zizmor --require-optional-tools --format json`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-294 Consolidate engineering narrative docs into a single canonical history source by folding `dev/docs/TECHNICAL_SHOWCASE.md` and `dev/docs/LINKEDIN_POST.md` into appendices in `dev/history/ENGINEERING_EVOLUTION.md`, then retiring the duplicated `dev/docs/` source files so updates only target one document; verification evidence: `python3 dev/scripts/devctl.py docs-check --user-facing`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-297 Execute a focused `devctl check` usability/performance hardening sequence from maintainer review findings in ordered slices:
  - [x] `#5` failure-output diagnostics: `run_cmd` now streams subprocess output while preserving bounded failure excerpts for non-zero exits (`dev/scripts/devctl/common.py`), `check` prints explicit failed-step summaries with captured context (`dev/scripts/devctl/commands/check.py`), markdown reports include a dedicated failure-output section (`dev/scripts/devctl/steps.py`), and regression coverage/docs were updated (`dev/scripts/devctl/tests/test_common.py`, `dev/scripts/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`); verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
  - [x] `#1` check-step parallelism: `devctl check` now runs independent setup gates (`fmt`, `clippy`, AI guard scripts) and the test/build phase through deterministic parallel batches with stable report ordering (`dev/scripts/devctl/commands/check.py`), includes maintainer controls for sequential fallback and worker tuning (`--no-parallel`, `--parallel-workers` in `dev/scripts/devctl/cli.py`), and adds regression coverage for parser wiring, parallel-path selection, and ordered aggregation (`dev/scripts/devctl/tests/test_check.py`); verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_check`.
  - [x] `#7` profile-vs-flag conflict validation: extracted `validate_profile_flag_conflicts()` into `check_profile.py` with `PROFILE_PRESETS` single source of truth, added 12 regression tests in `test_check.py`.
  - [x] `#4` explicit progress feedback: extracted `count_quality_steps()` and `emit_progress()` into `check_progress.py` with serial `[N/M]` and parallel `[N-M/T]` formats, added 10 regression tests in `test_check.py`.
  - [x] `#2` runaway-process containment: `run_cmd` now starts child steps in isolated process groups and tears down the full subprocess tree on interrupt (`dev/scripts/devctl/common.py`), while process sweep now treats stale active `voiceterm-*` test runners as cleanup/error candidates in both `check` and `hygiene` (`dev/scripts/devctl/process_sweep.py`, `dev/scripts/devctl/commands/check.py`, `dev/scripts/devctl/commands/hygiene.py`); regression coverage added in `dev/scripts/devctl/tests/test_common.py`, `dev/scripts/devctl/tests/test_process_sweep.py`, `dev/scripts/devctl/tests/test_check.py`, and `dev/scripts/devctl/tests/test_hygiene.py`.
  - [x] `#8` ADR-reference + governance parity guard: `devctl hygiene` now flags stale ADR reference patterns (hard-coded ADR counts and wildcard ADR file ranges), validates ADR backlog parity between `MASTER_PLAN` and `autonomous_control_plane`, and enforces reserved-ID coverage for missing backlog ADR files, with regression coverage in `dev/scripts/devctl/tests/test_hygiene.py`; docs were normalized to index-based ADR references in `dev/active/theme_upgrade.md` and `dev/history/ENGINEERING_EVOLUTION.md`, and release/tooling workflows now run workflow-shell + IDE/provider isolation + compat-matrix schema/smoke + naming consistency checks in their governance bundles.
  - [x] `#9` external publication drift governance: landed the tracked
    publication registry (`dev/config/publication_sync_registry.json`),
    `devctl publication-sync` report/record flow
    (`dev/scripts/devctl/publication_sync.py`,
    `dev/scripts/devctl/publication_sync_parser.py`,
    `dev/scripts/devctl/commands/publication_sync.py`), hygiene warnings via
    `dev/scripts/devctl/commands/hygiene.py` +
    `dev/scripts/devctl/commands/hygiene_audits.py`, the explicit guard
    `dev/scripts/checks/check_publication_sync.py`, release-preflight wiring,
    and regression coverage in
    `dev/scripts/devctl/tests/test_publication_sync.py` plus
    `dev/scripts/devctl/tests/test_check_publication_sync.py`; verification
    evidence: `python3 -m unittest dev.scripts.devctl.tests.test_publication_sync dev.scripts.devctl.tests.test_check_publication_sync`,
    `python3 dev/scripts/devctl.py publication-sync --format json`,
    `python3 dev/scripts/checks/check_publication_sync.py --report-only`.
- [x] MP-298 Parallelize independent `devctl status`/`report` collection probes and `ship --verify` subchecks with deterministic aggregation so I/O-heavy control-plane workflows run faster without changing pass/fail policy semantics.
  - [x] 2026-03-09 Rust-audit reporting slice: `devctl report` now has an optional
    parallel-collected `--rust-audits` probe that aggregates the Rust
    best-practices, lint-debt, and runtime-panic guards into one human-readable
    Markdown section with risk/fix explanations, optional matplotlib charts via
    `--with-charts`, deterministic report bundle emission (`--emit-bundle`),
    and shared full-tree support after adding `--absolute` mode to
    `check_rust_runtime_panic_policy.py`; targeted regression coverage added in
    `test_report.py`, `test_status_report_parallel.py`,
    `test_rust_audit_report.py`, and
    `test_check_rust_runtime_panic_policy.py`.
  - [x] 2026-03-09 `ship --verify` closure slice: independent verify subchecks
    now run through deterministic parallel aggregation in
    `dev/scripts/devctl/commands/ship_steps.py`, using quiet worker execution
    plus ordered failure selection so the first failing declared substep still
    determines the verify result even when workers complete out of order;
    regression coverage added in `dev/scripts/devctl/tests/test_ship.py` and
    `dev/scripts/devctl/tests/test_common.py`, with local proof via
    `python3 -m unittest dev.scripts.devctl.tests.test_common dev.scripts.devctl.tests.test_ship`
    and `python3 dev/scripts/devctl.py ship --version 1.1.1 --verify --dry-run --format json`.
- [x] MP-299 Add a `devctl triage` workflow that emits both human-readable markdown and AI-friendly JSON, with optional CIHub ingestion: landed new command surface (`dev/scripts/devctl/commands/triage.py`) plus parser/command inventory wiring (`dev/scripts/devctl/cli.py`, `dev/scripts/devctl/commands/listing.py`), optional `cihub triage` execution + artifact ingestion (`triage.json`, `priority.json`, `triage.md`) under configurable emit directories, and bundle emission mode (`--emit-bundle` writes `<prefix>.md` + `<prefix>.ai.json`) for project handoff/automation use; regression coverage/docs updated in `dev/scripts/devctl/tests/test_triage.py` and `dev/scripts/README.md`; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-300 Deepen `devctl triage` CIHub integration with actionable routing data: map `cihub` artifact records (`priority.json`, `triage.json`) into normalized issues (`category`, `severity`, `owner`, `summary`) via shared enrichment helpers (`dev/scripts/devctl/triage/enrich.py`), add configurable category-owner overrides (`--owner-map-file`) in parser wiring (`dev/scripts/devctl/triage/parser.py`), include rollup counts by severity/category/owner in report payload + markdown output (`dev/scripts/devctl/triage/support.py`), and extend regression coverage for severity/owner routing + owner-map overrides (`dev/scripts/devctl/tests/test_triage.py`) with docs updates in `dev/scripts/README.md`; verification evidence: `python3 -m unittest discover -s dev/scripts/devctl/tests -p 'test_*.py'`, `python3 dev/scripts/devctl.py triage --format md --no-cihub --emit-bundle --bundle-dir /tmp --bundle-prefix vt-triage-smoke --output /tmp/vt-triage-smoke.md`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [x] MP-306 Add proactive report-retention governance to the `devctl` control plane: landed `devctl reports-cleanup` with retention safeguards (`--max-age-days`, `--keep-recent`, protected-path exclusions, dry-run preview, confirmation/`--yes` delete path), wired `hygiene` to always surface stale report-growth warnings with direct cleanup guidance, and added parser/command/hygiene regression coverage plus maintainer docs updates (`dev/scripts/README.md`, `dev/DEVCTL_AUTOGUIDE.md`).
- [ ] MP-379 Harden shared `devctl` reporting collector honesty: `status` /
  `report` must distinguish unavailable optional sources from parse failures,
  keep mutation outcomes and similar probes machine-readable when no results
  exist yet, and stop surfacing `invalid JSON payload` warnings for honest
  no-data cases. Land this on the shared `collect.py` / `status_report.py`
  contract with focused regression coverage so downstream automation sees one
  stable unavailable-state vocabulary.
- [x] MP-339 Migrate repository Rust workspace path from `src/` to `rust/` and update runtime/tooling/CI/docs path contracts in one governed pass (`dev/archive/2026-03-07-rust-workspace-layout-migration.md`), preserving behavior while removing the `src/src` naming pattern (landed filesystem rename + path-contract rewrites across scripts/checks/workflows/docs; follow-up guard hardening landed rename-aware baseline mapping for Rust debt/security checks, active-root discovery + fail-fast behavior for `check_rust_audit_patterns.py`, and an explicit non-regressive `mem::forget` policy in `check_rust_best_practices.py`; sync/tooling gates and Rust build smoke from `rust/` succeeded).
- [x] MP-303 Add automated release-metadata preparation to the `devctl` control plane so maintainers can run one command path before verify/tag: added `--prepare-release` support on `devctl ship`/`devctl release` (`dev/scripts/devctl/cli.py`, `dev/scripts/devctl/commands/release.py`, `dev/scripts/devctl/commands/ship.py`), implemented canonical metadata updaters for Cargo/PyPI/macOS app plist plus changelog heading rollover under `dev/scripts/devctl/commands/release_prep.py` and `ship_steps.py`, and covered step wiring + idempotent prep behavior in `dev/scripts/devctl/tests/test_ship.py` and `dev/scripts/devctl/tests/test_release_prep.py`; docs/governance updates in `AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, and `dev/history/ENGINEERING_EVOLUTION.md`; verification evidence: `python3 -m unittest dev.scripts.devctl.tests.test_ship dev.scripts.devctl.tests.test_release_prep`, `python3 dev/scripts/devctl.py docs-check --strict-tooling`, `python3 dev/scripts/devctl.py hygiene`, `python3 dev/scripts/checks/check_agents_contract.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_release_version_parity.py`, `python3 dev/scripts/checks/check_cli_flags_parity.py`, `python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120`, `python3 dev/scripts/checks/check_code_shape.py`, `python3 dev/scripts/checks/check_rust_lint_debt.py`, `python3 dev/scripts/checks/check_rust_best_practices.py`, `markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md`, `find . -maxdepth 1 -type f -name '--*'`.
- [ ] MP-257 Run a plain-language readability pass across primary `dev/` entry docs (`dev/README.md`, `dev/DEVELOPMENT.md`, `dev/ARCHITECTURE.md`) so new developers can follow workflows quickly without losing technical accuracy.
  - [x] 2026-02-25 workflow readability slice: added `.github/workflows/README.md` with plain-language explanations for all workflow lanes (what runs, when it runs, and local reproduce commands) and added short purpose headers to every `.github/workflows/*.yml` file so intent is visible without opening full YAML bodies.
  - [x] 2026-02-25 core-dev-doc readability slice: simplified workflow/process language in `dev/README.md`, `dev/DEVELOPMENT.md`, and `dev/ARCHITECTURE.md` so operators can scan what to run and why without policy-heavy wording.
  - [x] 2026-02-25 user-guide readability slice: simplified wording across `guides/README.md`, `guides/INSTALL.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `guides/TROUBLESHOOTING.md`, and `guides/WHISPER.md` while preserving command/flag behavior and technical accuracy.
  - [x] 2026-02-25 root-entry readability slice: simplified wording in `README.md`, `QUICK_START.md`, and `DEV_INDEX.md` so first-time users and maintainers can scan setup/docs links quickly without changing any commands, flags, or workflow behavior.
  - [x] 2026-02-25 follow-up dev-entry readability slice: refined plain-language wording in `dev/README.md`, `dev/DEVELOPMENT.md`, and `dev/ARCHITECTURE.md`, and replaced the outdated `src/src` tree in `dev/DEVELOPMENT.md` with the current `rust/` layout summary so docs are both easier to scan and accurate.

## Phase 3C - Codebase Best-Practice Consolidation (Active Audit Track)

- [x] MP-184 Publish a dedicated execution record for full-repo Rust best-practice cleanup and keep task-level progress scoped to that audit track.
- [x] MP-185 Decompose settings action handling for lower coupling and clearer ownership (`settings_handlers` runtime/test separation, enum-cycle consolidation, constructor removal, status-helper extraction, and `SettingsActionContext` sub-context split landed; adjacent `ButtonActionContext::new` constructor removal also landed for consistent context wiring).
- [x] MP-186 Consolidate status-line rendering/button logic (`status_line/buttons.rs` and `status_line/format.rs`) to remove duplicated style/layout decisions and isolate legacy compatibility paths (landed: shared button highlight + queue/ready/latency badge helpers; legacy row helpers are `#[cfg(test)]`-gated with shared framing/separator helpers and reduced dead-code surface; tests split into `status_line/buttons/tests.rs` and `status_line/format/tests.rs`).
- [x] MP-187 Consolidate PTY lifecycle internals into canonical spawn/shutdown helpers and harden session-guard identity/cleanup throttling to reduce stale-process risk without blocking concurrent sessions (landed shared PTY lifecycle helpers in `pty_session/pty.rs`, plus session-lease start-time identity validation and atomic cleanup cadence throttling in `pty_session/session_guard.rs`; additional detached-orphan sweep fallback now reaps stale backend CLIs with `PPID=1` when they are not lease-owned and no longer share a TTY with a live shell, with deterministic unit coverage for elapsed-time parsing and candidate filtering).
- [x] MP-188 Decompose backend orchestration hotspots (`codex/pty_backend.rs`, `ipc/session.rs`) into narrower modules with explicit policy boundaries and lower test/runtime coupling (completed in v1.0.80: landed `codex/pty_backend/{output_sanitize,session_call,job_flow,test_support}.rs` plus `ipc/session/{stdin_reader,claude_job,auth_flow,loop_control,state,event_sink,test_support}.rs`, keeping parent orchestrators focused on runtime control flow).
- [x] MP-189 Add a focused maintainer lint-hardening lane (strict clippy profile + targeted allowlist) and burn down high-value warnings (`must_use`, error docs, redundant clones/closures, risky casts, dead-code drift) (completed in v1.0.80: landed `devctl check --profile maintainer-lint` + `.github/workflows/lint_hardening.yml`, burned down targeted warnings, added Linux ALSA dependency setup for the lane, and documented intentional deferral of precision/truncation DSP cast families).
- [x] MP-191 Fix Homebrew `opt` launcher path detection in `scripts/start.sh` + `scripts/setup.sh` so upgrades reuse persistent user model storage (`~/.local/share/voiceterm/models`) instead of redownloading into versioned Cellar `libexec/whisper_models`.
- [x] MP-192 Fix Full HUD ribbon baseline rendering by padding short waveform history at floor level (`-60 dB`) so right-panel visuals ramp upward instead of drawing a full-height block.
- [x] MP-193 Restore insert-mode early-send behavior for `Ctrl+E` while recording so noisy-room captures can stop early and submit immediately (one-shot force-send path + regression tests + docs alignment).
- [x] MP-197 Make hidden-HUD idle launcher visuals intentionally subdued (dull/muted text and `[open]`) so hidden mode remains non-intrusive.
- [x] MP-198 Align insert-mode `Ctrl+E` dispatch semantics (send staged text, finalize+submit while recording, consume idle/no-staged input) and apply the same muted hidden-launcher gray to hidden recording output.
- [x] MP-204 Refine hidden-HUD idle launcher controls for lower visual noise and better explicitness (remove inline `Ctrl+U` hint from hidden launcher text, add muted `[hide]` control next to `[open]`, support collapsing hidden launcher chrome to `[open]` only, and make `open` two-step from collapsed mode: restore launcher first, then switch HUD style on the next open).
- [x] MP-205 Harden discoverability + feedback ergonomics (expand startup hints for `?`/settings/mouse discoverability, add grouped help overlay sections, and surface explicit idle `Ctrl+E` feedback with `Nothing to send`).
- [x] MP-206 Add first-run onboarding hint persistence (`~/.config/voiceterm/onboarding_state.toml`) so a `Getting started` hint remains until the first successful transcript capture.
- [x] MP-207 Extract shared overlay frame rendering helpers (`overlay_frame`) and route help/settings/theme-picker framing through the shared path to reduce duplicated border/title/separator logic.
- [x] MP-208 Standardize overlay/HUD width accounting with Unicode-aware display width and add HUD module `priority()` semantics so queue/latency indicators survive constrained widths ahead of lower-priority modules.
- [x] MP-209 Replace opaque runtime status errors with log-path-aware messages (`... (log: <path>)`) across capture/transcript failure paths.
- [x] MP-210 Keep splash unchanged, but move discoverability/help affordances into runtime HUD/overlay surfaces (hidden HUD idle hint now includes `? help` + `^O settings`; help overlay adds clickable Docs/Troubleshooting OSC-8 links).
- [x] MP-211 Replace flat clap default `--help` output with a themed, grouped renderer backed by clap command metadata (manual `-h`/`--help` interception, sectioned categories, single-accent hacker-style scan path with dim borders + bracketed headers, theme/no-color parity, and coverage guard so new flags cannot silently skip grouping).
- [x] MP-212 Remove stale pre-release/backlog doc references, align `VoiceTerm.app` Info.plist version with `rust/Cargo.toml`, and sync new `voiceterm` modules in changelog/developer structure docs.
- [x] MP-213 Add a Rust code-review research pack and wire it into the code-quality execution track with an explicit closure/archive handoff path into Theme Upgrade phases (`MP-148+`).
- [x] MP-218 Fix overlay mouse hit-testing for non-left-aligned coordinate spaces so settings/theme/help row clicks and slider adjustments still apply when terminals report centered-panel `x` coordinates.
- [x] MP-219 Clarify settings overlay footer control hints (`[×] close · ↑/↓ move · Enter select · Click/Tap select`) and add regression coverage so footer close click hit-testing stays intact after copy updates.
- [x] MP-220 Fix settings slider click direction handling so pointer input on `Sensitivity`/`Wake sensitivity` tracks can move left/right by click position, with regression tests for backward slider clicks.
- [x] MP-221 Fix hidden-launcher mouse click redraw parity so `[hide]` and collapsed `[open]` clicks immediately repaint launcher state (matching arrow-key `Enter` behavior), with regression tests for both click paths.
- [x] MP-222 Resolve post-release `lint_hardening` CI failures by removing redundant-closure clippy violations in `custom_help.rs` and restoring maintainer-lint lane parity on `master`.
- [x] MP-223 Unify README CI/mutation badge theming to black/gray endpoint styling and enforce red failure states via renderer scripts (`render_ci_badge.py`, `render_mutation_badge.py`) plus CI workflow auto-publish on `master`.
- [x] MP-224 Harden Theme Studio style-pack test determinism by isolating unit tests from ambient shell `VOICETERM_STYLE_PACK_JSON` exports (tests now ignore runtime style-pack env unless explicit opt-in is set, and lock-path tests opt in intentionally), preventing cross-shell snapshot/render drift during `cargo test --bin voiceterm`.
- [x] MP-225 Fix Enter-key auto-mode flip regression: when stale HUD button focus is on `ToggleAutoVoice`, pressing `Enter` now submits PTY input (no mode flip), backed by a focused event-loop regression test and docs sync.
- [x] MP-228 Audit user-doc information architecture and seed screenshot-refresh governance: rebalance `QUICK_START.md` to onboarding scope, move deep runtime semantics to guides, document transcript-history mouse behavior and env parity (`VOICETERM_ONBOARDING_STATE`), and add a maintainer capture matrix for pending UI surfaces.
- [x] MP-214 Close out the active code-quality track by triaging remaining findings, archiving audit records, and continuing execution from Theme Upgrade (`MP-148+`).
- [x] MP-215 Standardize runtime status-line width/truncation on Unicode-aware display width in remaining char-count paths (`rust/src/bin/voiceterm/writer/render.rs` and `rust/src/bin/voiceterm/status_style.rs`) with regression coverage for wide glyphs (landed Unicode-aware width/truncation in writer sanitize/render/status-style paths, preserved printable Unicode status text, and added regression tests for wide-glyph truncation and width accounting).
- [x] MP-216 Consolidate duplicate transcript-preview formatting logic shared by `rust/src/bin/voiceterm/voice_control/navigation.rs` and `rust/src/bin/voiceterm/voice_control/drain/message_processing.rs` into a single helper with shared tests (landed shared `voice_control/transcript_preview.rs` formatter and removed duplicated implementations from navigation/drain paths with focused unit coverage).
- [x] MP-217 Enable settings-overlay row mouse actions so row clicks select and apply setting toggles/cycles (including click paths for `Close` and `Quit`) instead of requiring keyboard-only action keys.
- [x] MP-262 Publish a full senior-level engineering audit baseline in `dev/archive/2026-02-20-senior-engineering-audit.md` with measured code-shape, lint-debt, CI hardening, and automation findings mapped to executable follow-up MPs.
- [x] MP-263 Harden GitHub Actions supply-chain posture: pin third-party actions by commit SHA, define explicit least-privilege `permissions:` on every workflow, and add `concurrency:` groups where duplicate in-flight runs can race or waste minutes (landed by pinning all workflow action refs to 40-char SHAs across `.github/workflows/*.yml`, adding explicit `permissions:`/`concurrency:` blocks to every workflow, and narrowing write scope to job-level where badge-update pushes require `contents: write`).
- [x] MP-264 Add repository ownership and dependency automation baseline by introducing `.github/CODEOWNERS` and `.github/dependabot.yml` (grouped update policies + review routing) so tooling/runtime changes always have accountable reviewers and timely dependency refresh cadence (landed with explicit ownership coverage for runtime/tooling/distribution paths and weekly grouped update policies for GitHub Actions, Cargo, and PyPI packaging surfaces).
- [ ] MP-265 Decompose oversized runtime modules with explicit shape budgets and staged extraction plans (top hotspots: `event_loop/input_dispatch.rs`, `status_line/format.rs`, `status_line/buttons.rs`, `theme/rule_profile.rs`, `theme/style_pack.rs`, `transcript_history.rs`; next maintainability-audit tranche should prioritize `event_loop.rs`, `main.rs`, `dev_command/{broker,review_artifact,command_state}.rs`, and `dev_panel/{review_surface,cockpit_page/mod}.rs`) while preserving non-regression behavior coverage (in progress: `dev/scripts/checks/check_code_shape.py` now enforces path-level non-growth budgets for the hotspot files so decomposition work is CI-measurable instead of policy-only; `event_loop/input_dispatch.rs` overlay-mode handling was extracted into `event_loop/input_dispatch/overlay.rs` + `event_loop/input_dispatch/overlay/overlay_mouse.rs`; prior slice extracted status-line right-panel formatting/animation helpers from `status_line/format.rs` into `status_line/right_panel.rs`; latest slices move minimal-HUD right-panel scene/waveform/pulse helpers from `status_line/buttons.rs` into `status_line/right_panel.rs` and extract queue/wake/latency badge formatting into `status_line/buttons/badges.rs`, reducing `status_line/buttons.rs` from 1059 to 801 lines while keeping focused status-line tests green; newest slices extract compact/minimal HUD helpers into `status_line/format/compact.rs`, then move single-line layout helpers into `status_line/format/single_line.rs`, reduce `theme/rule_profile.rs` by moving inline tests into `theme/rule_profile/tests.rs` (`922 -> 265`), and move writer-state test-only timing constants from `writer/state.rs` into `writer/state/tests.rs` so production writer modules remain runtime-focused; raised file-shape overrides were removed with focused runtime suites and clippy reruns green, writer message routing remains split across `writer/state/dispatch.rs` plus `writer/state/dispatch_pty.rs` after retiring temporary dispatch/redraw/prompt complexity exceptions, and the newest Rust-overlay cleanup split `dev_panel/review_surface.rs` lane helpers plus `dev_panel/cockpit_page/mod.rs` control sections into focused sibling modules (`review_surface_lanes.rs`, `cockpit_page/control_sections.rs`) so both Dev-panel hotspots now sit well below their prior shape-risk thresholds).
- [ ] MP-266 Burn down Rust lint-debt hotspots by reducing `#[allow(...)]` surface area and non-test `unwrap/expect` usage, then add measurable gates/reporting so debt cannot silently regress (in progress: landed `dev/scripts/checks/check_rust_lint_debt.py` with working-tree + commit-range modes, wired governance bundles/docs references, and added tooling-control-plane CI enforcement so changed Rust files cannot add net-new lint debt without an explicit failure signal; latest slice removes 22 `#[allow(dead_code)]` suppressions by scoping PTY counter helper APIs/re-exports to tests in `pty_session/counters.rs` + `pty_session/mod.rs`, with full `devctl check --profile ci` and lifecycle matrix test coverage green; newest enforcement slice keeps AI-guard scripts enabled in `check --profile quick|fast` so default local iteration and post-test quick follow-up paths no longer skip structural/code-quality guards by profile default).
- [ ] MP-267 Run a naming/API cohesion pass across theme/event-loop/status/memory surfaces to remove ambiguous names, tighten public API intent, and consolidate duplicated helper logic into shared modules (`dev/active/naming_api_cohesion.md`; in progress: canonical `swarm_run` command naming now enforced in parser/dispatch/workflow/docs with no legacy alias in active command paths, duplicate triage/mutation policy engines consolidated into shared `loop_fix_policy.py` helper with tests, duplicated devctl numeric parsing consolidated into `dev/scripts/devctl/numeric.py` (`to_int`/`to_float`/`to_optional_float`) with callsite rewiring, Theme Studio list navigation consolidated under shared `theme_studio/nav.rs` with consistent `select_prev`/`select_next` naming across page state + input-dispatch call paths, prompt-occlusion suppression transitions extracted into `event_loop/prompt_occlusion.rs` so output/input/periodic dispatchers share one runtime owner for suppression side effects, and the next portability slice is now explicit in `dev/guides/DEVCTL_ARCHITECTURE.md`: define one repo-policy-backed KISS naming-contract guard for public `devctl` words, generated AI/dev surfaces, and beginner-facing docs copy).
- [x] MP-268 Codify a Rust-reference-first engineering quality contract in `AGENTS.md` and `dev/DEVELOPMENT.md`, including mandatory official-doc reference pack links and handoff evidence requirements for non-trivial Rust changes.
- [ ] MP-269 Add Theme Studio style-pack hot reload (`notify` watcher + debounce + deterministic rollback-safe apply path) so theme iteration does not require restarting VoiceTerm.
- [ ] MP-270 Add algorithmic theme generation mode (`palette`-backed seed-color derivation with contrast guards) and expose it in Theme Studio as an optional starting point, not a replacement for manual edits.
- [ ] MP-271 Replace ad-hoc animation transitions with a deterministic easing profile layer (`keyframe`-style easing contracts or equivalent) and benchmark frame-cost impact on constrained terminals.
- [ ] MP-272 Define and implement Memory Studio context-injection contract for Codex/Claude handoff flows (selection policy, token budget, provenance formatting, failure rollback).
- [ ] MP-273 Produce an overlay architecture ADR evaluating terminal-only vs hybrid desktop overlay (`egui_overlay`/window-layer path) with explicit capability matrix, migration risk, and phased rollout recommendation.
- [x] MP-274 Add AI coding guardrails for Rust best-practice drift by introducing `dev/scripts/checks/check_rust_best_practices.py` (working-tree + commit-range non-regression checks for reason-less `#[allow(...)]`, undocumented `unsafe { ... }`, and public `unsafe fn` without `# Safety` docs), wiring it into `devctl check` (`--profile ai-guard` plus automatic `prepush`/`release` guard steps), and enforcing commit-range execution in `.github/workflows/tooling_control_plane.yml` with docs/bundle parity updates.
- [x] MP-275 Normalize `--input-device` values before runtime recorder lookup by collapsing wrapped whitespace/newline runs and rejecting empty normalized names so wake/manual capture initialization stays resilient to terminal line-wrap paste artifacts.
- [x] MP-276 Harden wake-word runtime diagnostics/ownership handoff: HUD now reflects listener-startup failures (`Wake: ERR` + status/log-path message) instead of false `Wake: ON` state when listener init fails, and wake detection now self-pauses listener capture before triggering shared capture startup to reduce microphone ownership races.
- [x] MP-277 Expand wake-word matcher alias normalization for common STT token-split variants (`code x` -> `codex`, `voice term` -> `voiceterm`) while preserving short-utterance guardrails and updating troubleshooting phrase guidance.
- [x] MP-278 Correct wake-trigger capture origin labeling end-to-end so wake-detected recordings flow through the shared capture path with explicit `WakeWord` trigger semantics (logs/status no longer misreport wake-initiated captures as manual starts).
- [x] MP-279 Reduce wake-state confusion and listener churn: keep `Wake: ON` badge styling steady (no pulse redraw), remove periodic wake-badge animation ticks, and extend wake-listener capture windows to reduce frequent microphone open/close cycling on macOS.
- [x] MP-280 Harden wake re-arm reliability after first trigger by decoupling wake detections from the auto-voice pause latch, allowing longer command tails when wake phrases lead the transcript, and adding no-audio retry backoff to reduce rapid microphone indicator churn on transient capture failures.
- [x] MP-281 Add built-in voice submit intents for insert mode (`send`, `send message`, `submit`) so staged transcripts can be submitted hands-free through the same newline path as Enter, including one-shot wake tails (`hey codex send` / `hey claude send`).
- [x] MP-296 Keep latency visibility stable in auto mode by preserving the last successful latency sample across auto-capture `Empty` cycles and allowing the shortcuts-row latency badge to remain visible during auto recording/processing (manual mode continues hiding during active capture); coverage added in `status_line/buttons/tests.rs` and `voice_control/drain/tests.rs`.

## Phase 3D - Memory + Action Studio (Planning Track)

Memory Studio execution gate: MP-230..MP-255 are governed by
`dev/active/memory_studio.md`. A Memory MP may move to `[x]` only with
documented `MS-G*` pass evidence.

- [x] MP-230 Establish canonical memory event schema + storage foundation (JSONL append log + SQLite index) for machine-usable local memory (`MS-G01`, `MS-G02`).
- [ ] MP-231 Implement deterministic retrieval APIs (topic/task/time/semantic) with provenance-tagged ranking and bounded token budgets (`MS-G03`, `MS-G04`, `MS-G18`, `MS-G19`). Current proving substrate is the shipped in-memory index plus `boot_pack` / `task_pack`; 2026-03-09 follow-ups now auto-extract bounded `MP-*` refs, repo file paths, and small topic tags on live ingest and emit operator-cockpit export artifacts for `task_pack`, `session_handoff`, and `survival_index`. The first scoring-trace/query-evidence closure slice is now live in `memory/survival_index.rs` and Memory cockpit exports (`query_traces` + deduplicated evidence rows); remaining scope is broader semantic/topic ranking coverage and browser-level retrieval UX.
- [x] MP-232 Ship context-pack generation (`context_pack.json` + `context_pack.md`) for AI boot/handoff workflows with explicit evidence references (`MS-G03`, `MS-G07`).
- [ ] MP-233 Deliver Memory Browser overlay (filter/expand/scroll/replay-safe controls) with keyboard+mouse parity (`MS-G06`, `MS-G20`). Current proving path should surface memory status/query/export views inside the Rust operator cockpit first, then expand into the fuller Memory Browser once the cross-plan operator flow is stable. The shipped proof is broader now: Control-tab memory status, a dedicated read-only Memory cockpit tab backed by ingest/review/boot-pack/handoff previews, the Boot-pack-backed Handoff preview, and repo-visible JSON/Markdown exports for `boot_pack`, `task_pack`, `session_handoff`, and the first `survival_index` preview are live. Remaining open scope is the full browser UX plus attach-by-ref/state-flow integration on top of those exports.
- [ ] MP-234 Deliver Action Center overlay with policy-tiered command execution (read-only/confirm-required/blocked), preview/approval flow, and action-run audit logging (`MS-G05`, `MS-G06`). Action policy/catalog scaffolding already exists in `memory/action_audit.rs`; this scope still needs runtime approval flows, audit wiring, and convergence with the MP-340 typed action router so memory-derived suggestions, overlay buttons, and review-channel requests share one approval/waiver model instead of parallel executors.
- [ ] MP-235 Add memory governance controls (retention, redaction hooks, per-project isolation) and regression tests for bounded growth/privacy invariants (`MS-G04`, `MS-G05`). Redaction plus retention-GC foundation is already shipped in `memory/governance.rs`; remaining scope is user-facing policy wiring, isolation profiles, and regression coverage.
- [ ] MP-236 Complete docs + release readiness for Memory Studio (architecture/user docs/changelog + CI evidence bundle) (`MS-G07`, `MS-G08`).
- [ ] MP-237 Add memory-evaluation harness and quality gates (`precision@k`, evidence coverage, deterministic pack snapshots, latency budgets) for release blocking (`MS-G03`, `MS-G04`, `MS-G08`).
- [ ] MP-238 Add model-adapter interop for context packs (Codex/Claude-compatible pack rendering while preserving canonical JSON provenance, including review-channel/controller handoff attachments) (`MS-G03`, `MS-G07`, `MS-G08`). Current runtime proof already builds a boot-pack-backed fresh bootstrap prompt in the Rust handoff cockpit, the Memory cockpit now emits repo-visible JSON/Markdown exports for `boot_pack`, `task_pack`, `session_handoff`, and `survival_index`, and the typed Rust action catalog carries review launch/rollover plus pause/resume actions with JSON summary rendering. Structured `review_state` attach-by-ref is now partially landed: event-backed review packets preserve `context_pack_refs` into reduced state/actions projections, Rust review surfaces/fresh prompts render those refs read-only, and the PyQt6 operator approval path keeps them lossless through decision artifacts. Missing scope is `controller_state` parity, broader provider-shaped review/control attachments, and packet-outcome ingest parity.
- [ ] MP-240 Add validated Memory Cards as a derived-truth layer (decision/project_fact/procedure/gotcha/task_state/glossary) with evidence links, TTL policies, and branch-aware validation-before-injection (`MS-G03`, `MS-G09`).
- [x] MP-241 Wire dev tooling and git intelligence into memory ingestion (`devctl status/report`, release-notes artifacts, git range summaries) and ship compiler outputs (`project_synopsis`, `session_handoff`, `change_digest`) in JSON+MD (`MS-G02`, `MS-G10`).
- [ ] MP-242 Ship read-only MCP memory exposure (resources + tools for search/context packs/validation) with deterministic provenance payloads and policy-safe defaults (`MS-G03`, `MS-G11`).
- [ ] MP-243 Add user memory-control modes (`off`, `capture_only`, `assist`, `paused`, `incognito`) with UI/state persistence and regression coverage for trust/privacy invariants (`MS-G05`, `MS-G06`). Current implementation now spans the Rust Dev-panel Control + Memory tabs with runtime mode/status visibility and mode-cycling, and the 2026-03-09 persistence slice landed startup restore plus persistent-config load/save so the configured `memory_mode` no longer resets on boot and dev-panel mode changes persist immediately into later snapshots. Closure still requires visible controls outside `--dev` plus negative-control/receipt UX.
- [ ] MP-244 Add sequence-aware action safety escalation so multi-command workflows increase policy tier when risk patterns combine (mutation + network + shell exec) and require explicit confirmation evidence (`MS-G05`, `MS-G11`).
- [ ] MP-246 Implement repetition-mining over memory events/command runs to detect high-frequency scriptable workflows, with support+confidence thresholds and provenance-scored candidates (`MS-G03`, `MS-G10`, `MS-G12`).
- [ ] MP-247 Ship automation suggestion flow that proposes script templates + `AGENTS.md` instruction patches + workflow snippets with preview/approve/reject UX (no auto-apply) and acceptance telemetry (`MS-G05`, `MS-G06`, `MS-G12`).
- [ ] MP-248 Add opt-in external transcript import adapters (for example ChatGPT export files) normalized into canonical memory schema with source tagging/redaction and retrieval-only defaults for safety (`MS-G01`, `MS-G05`, `MS-G13`).
- [ ] MP-249 Implement isolation profiles for action execution (`host_read_only`, `container_strict`, `host_confirmed`) with policy wiring, audit logging, and escape-attempt regression tests (`MS-G05`, `MS-G14`).
- [ ] MP-250 Build compaction experiment harness (A/B against no-compaction baseline) with replay fixtures, benchmark adapters, and report artifacts covering quality/citation/latency/token metrics (`MS-G03`, `MS-G15`).
- [ ] MP-251 Gate compaction default-on rollout behind non-inferiority/evidence thresholds and publish operator guidance for safe enablement strategy (`MS-G07`, `MS-G08`, `MS-G15`).
- [ ] MP-252 Prototype Apple Silicon acceleration paths (SIMD/Metal/Core ML where applicable) for memory retrieval/compaction workloads and publish backend benchmark matrix vs CPU reference (`MS-G03`, `MS-G16`).
- [ ] MP-253 Gate acceleration rollout behind non-inferiority quality checks, deterministic-evidence parity checks, and runtime fallback guarantees (`MS-G08`, `MS-G16`).
- [ ] MP-254 Evaluate ZGraph-inspired symbolic compaction for memory units/context packs (pattern aliases for repeated paths/commands/errors), with reversible transforms and deterministic citation-equivalence checks (`MS-G03`, `MS-G15`, `MS-G17`).
- [ ] MP-255 Gate any symbolic compaction rollout behind non-inferiority quality thresholds, round-trip parity fixtures, and explicit default-off operator guidance until `MS-G17` passes (`MS-G07`, `MS-G08`, `MS-G17`).

2026-03-09 implementation alignment for the memory lane: the current runtime
already ships JSONL-backed memory ingest/recovery, an in-memory retrieval
index, operator-cockpit memory status/mode snapshots, and a boot-pack-backed
handoff/bootstrap prompt. The 2026-03-09 runtime follow-ups also landed
operator-cockpit query/export views by emitting repo-visible `boot_pack`,
`task_pack`, `session_handoff`, and `survival_index` JSON/Markdown artifacts
from the Rust Memory tab. The first scoring-trace closure is now shipped via
`memory/survival_index.rs` + structured `survival_index` exports. The next
slice is to turn the remaining proof path into `MP-231`/`MP-238`/`MP-243`
closure evidence by expanding retrieval coverage, finishing review/control
`context_pack_refs` consumption, and landing packet-outcome ingest
before the full Memory Browser / Action Center overlays
become the main product surface.

## Phase 3A - Mutation Hardening (Parallel Track)

- [ ] MP-015 Improve mutation score with targeted high-value tests (promoted from Backlog).
  - [ ] Build a fresh shard-by-shard survivor baseline on `master` and rank hotspots by missed mutants.
  - [x] Add mutation outcomes freshness visibility and stale-data gating in local tooling (`check_mutation_score.py` + `devctl mutation-score` now report source path/age and support `--max-age-hours`).
  - [x] Add targeted mutation-killer coverage for `theme_ops::cycle_theme` ordering/wrap semantics so default-return/empty-list/position-selection mutants are caught deterministically.
  - [x] Add targeted mutation-killer coverage for `Theme::from_name` alias arms (`tokyonight`/`tokyo-night`/`tokyo`, `gruvbox`/`gruv`) and `Theme::available()` list parity so empty/placeholder return mutants are caught.
  - [x] Add targeted mutation-killer coverage for `status_style::status_display_width` arithmetic and `terminal::take_sigwinch` clear-on-read semantics so constant-return/math mutants are caught.
  - [x] Add targeted mutation-killer coverage for `main.rs` runtime guards (`contains_jetbrains_hint`, `is_jetbrains_terminal`, `resolved_meter_update_ms`, and `join_thread_with_timeout`) and eliminate focused survivors (`cargo mutants --file src/bin/voiceterm/main.rs`: 18 caught, 0 missed, 1 unviable).
  - [x] Add targeted mutation-killer coverage for `input/mouse.rs` protocol guards/parsers (SGR/URXVT/X10 prefix+length boundaries and dispatch detection), eliminating focused survivors (`cargo mutants --file src/bin/voiceterm/input/mouse.rs`: 76 caught, 0 missed, 17 unviable).
  - [x] Remove the equivalent survivor path in `config/theme.rs` (`theme_for_backend` redundant `NO_COLOR` branch), keep explicit env-behavior regression coverage, and re-verify focused mutants (`cargo mutants --file src/bin/voiceterm/config/theme.rs`: 6 caught, 0 missed) plus `devctl check --profile ci` green.
  - [x] Eliminate `event_loop.rs` helper/boundary survivors by adding direct coverage for drain/winsize/overlay rendering/button-registry/picker reset paths, hardening settings-direction boundary assertions, and refactoring slider sign math to non-equivalent `is_negative()` checks (`cargo mutants --file src/bin/voiceterm/event_loop.rs`: 58 caught, 0 missed, 2 unviable) with `devctl check --profile ci` green.
  - [x] Remove `config/backend.rs` argument-length equivalent survivors in backend command resolution (`command_parts.len() > 1`) by refactoring to iterator-based split (`next + collect`) and re-verifying focused mutants (`cargo mutants --file src/bin/voiceterm/config/backend.rs`: 1 caught, 0 missed, 1 unviable) with `devctl check --profile ci` green.
  - [x] Add targeted `config/util.rs` path-shape boundary coverage for `is_path_like` (absolute/relative path positives, bare binary and empty-value negatives) and re-verify focused mutants (`cargo mutants --file src/bin/voiceterm/config/util.rs`: 11 caught, 0 missed) with `devctl check --profile ci` green.
  - [x] Add targeted regression coverage for runtime utility hotspots `auth.rs` and `lock.rs` (login command validation + exit-status mapping paths and mutex poison-recovery paths) so low-coverage utility modules stay protected without introducing lint-debt growth.
  - [x] Harden `event_loop/input_dispatch/overlay/overlay_mouse.rs` boundary predicates and add focused Theme Studio/settings mouse regression coverage (footer non-close area, border columns, option-row activation/out-of-range guards), eliminating the focused survivor cluster (`cargo mutants --file src/bin/voiceterm/event_loop/input_dispatch/overlay/overlay_mouse.rs --re 'overlay_mouse\\.rs:(32|39|99|100|119|142|143|144|145):'`: 8 caught, 0 missed).
  - [ ] Add targeted tests for top survivors in current hotspots (`src/bin/voiceterm/config/*`, `src/bin/voiceterm/hud/*`, `src/bin/voiceterm/input/mouse.rs`) and any new top offenders.
  - [ ] Ensure shard jobs always publish outcomes artifacts even when mutants survive.
  - [ ] Re-run mutation workflow until aggregate score holds at or above `0.80` on `master` for two consecutive runs (manual + scheduled).
  - [ ] Keep non-mutation quality gates green after each hardening batch (`python3 dev/scripts/devctl.py check --profile ci`, `Security Guard`).
- MP-015 acceptance gates:
  1. `.github/workflows/mutation-testing.yml` passes on `master` with threshold `0.80`.
  2. Aggregated score gate passes via `python3 dev/scripts/checks/check_mutation_score.py --glob "mutation-shards/**/shard-*-outcomes.json" --threshold 0.80`.
  3. Shard outcomes artifacts are present for all 8 shards in each validation run.
  4. Added hardening tests remain stable across two consecutive mutation workflow runs.

## Phase 4 - Advanced Expansion

- [ ] MP-092 Streaming STT and partial transcript overlay.
- [ ] MP-093 tmux/neovim integration track.
- [ ] MP-094 Accessibility suite (fatigue hints, quiet mode, screen-reader compatibility).
- [ ] MP-095 Custom vocabulary learning and correction persistence.

## Backlog (Not Scheduled)

- [ ] MP-016 Stress test heavy I/O for bounded-memory behavior.
- [ ] MP-031 Add PTY health monitoring for hung process detection.
- [ ] MP-032 Add retry logic for transient audio device failures.
- [ ] MP-033 Add benchmarks to CI for latency regression detection.
- [ ] MP-034 Add mic-meter hotkey for calibration.
- [ ] MP-037 Consider configurable PTY output channel capacity.
- [ ] MP-145 Eliminate startup cursor/ANSI escape artifacts shown in Cursor (Codex and Claude backends), with focus on the splash-screen teardown to VoiceTerm HUD handoff window where artifacts appear before full load. (in progress: writer pre-clear is now constrained to JetBrains terminals to reduce Cursor typing-time HUD flash while preserving JetBrains scroll-ghost mitigation.)
- [x] MP-146 Improve controls-row bracket styling so `[` `]` tokens track active theme colors and selected states use stronger contrast/readability (especially for arrow-mode focus visibility) (landed controls-row bracket tint routing so unfocused pills inherit active button highlight colors instead of always dim brackets, plus focused button emphasis via bold+info-bracket rendering for stronger keyboard focus visibility; covered by `status_line::buttons` regressions `format_button_brackets_track_highlight_color_when_unfocused`, `focused_button_uses_info_brackets_with_bold_emphasis`, and existing focus-bracket parity tests).
- [x] MP-147 Fix Cursor-only mouse-mode scroll conflict: with mouse mode ON, chat/conversation scroll should still work in Cursor for both Codex and Claude backends; preserve current JetBrains behavior (works today in PyCharm/JetBrains), keep architecture/change scope explicitly Cursor-specific, and require JetBrains non-regression validation so the Cursor fix does not break JetBrains scrolling. (landed Cursor-specific scroll-safe mouse handling in writer mouse control: Cursor keeps wheel scrollback available while settings can remain `Mouse: ON - scroll preserved in Cursor`, while JetBrains and other terminals retain existing mouse behavior.) Regression note (2026-02-25): users still report Cursor touchpad/wheel scrolling failing while `Mouse` is ON, with scrollbar drag still working; follow-up tracked in `MP-344`.
- [ ] MP-227 Explore low-noise progress-animation polish for task/status rows (inspired by Claude-style subtle shimmer/accent transitions during active thinking), including optional tiny accent pulses/color sweeps with strict readability/contrast bounds and no distraction under sustained usage; keep as post-priority visual refinement (not current execution scope).
- [x] MP-153 Add a CI docs-governance lane that runs `python3 dev/scripts/devctl.py docs-check --user-facing --strict` for user-facing behavior/doc changes so documentation drift fails early (completed via MP-302 docs-policy lane hardening in `.github/workflows/tooling_control_plane.yml`).
- [ ] MP-154 Add a governance consistency check for active docs + macro packs so removed workflows/scripts are not referenced in non-archive content.
- [ ] MP-155 Add a single pre-release verification command/profile that aggregates CI checks, mutation threshold, docs-governance checks, and hygiene into one machine-readable report artifact.
- [ ] MP-322 Investigate and fix wake-word + send intent "nothing to send" false negative: when using `Hey Claude, send` or `Hey Codex, send` voice commands, VoiceTerm sometimes reports "Nothing to send" even though there is staged text in the PTY input buffer; reproduce with both Claude and Codex backends, capture transcript decision traces (`voiceterm --logs --log-content`), verify send-intent detection timing relative to transcript staging, add targeted matcher/integration tests for the wake-tail send flow, and ensure the send intent checks for staged PTY content (not just VoiceTerm internal staged text state). Physical testing required alongside automated coverage.
- [ ] MP-323 Restore keyboard left/right caret navigation while editing staged text: currently Left/Right (and equivalent arrow-key paths) are captured by tab/button focus navigation instead of moving the text cursor inside the transcript/input field, which blocks correction of Whisper transcription mistakes before submit. Reproduce in active VoiceTerm sessions with staged text, route Left/Right to caret movement whenever text input/edit mode is active, preserve existing tab/control navigation when text edit mode is not active, and add focused keyboard/mouse regression coverage to prevent future text-edit lockouts. (2026-02-27 input-path hardening landed for related navigation regressions: shared arrow parser now accepts colon-parameterized CSI forms used by keyboard-enhancement modes, preventing settings/theme/overlay arrow-navigation dropouts after backend prompt-state transitions. 2026-03-02 field report follow-up: Codex and Claude sessions still show split ownership where arrow keys route either to terminal caret or HUD buttons based on `insert_pending_send`, and users recover by pressing `Ctrl+T`/other hotkeys; scope now includes a deterministic input-ownership model with explicit HUD-focus entry/exit semantics so caret editing and HUD button access remain available without mode confusion. 2026-03-05 backlog clarification: preserve explicit up/down focus handoff between chat region and overlay controls so Left/Right operates on the active surface only; defer this fix until post-next-release unless it becomes a release blocker.)
- [ ] MP-324 Finalize Ralph loop rollout evidence on default branch: after the workflow lands on the default branch, run one `workflow_dispatch` `CodeRabbit Ralph Loop` execution on `develop` (`execution_mode=report-only`) and confirm `check_coderabbit_ralph_gate.py --branch develop` resolves by workflow-run evidence rather than fallback logic; capture run URL and gate output in tooling handoff notes so release gating assumptions are explicit for all agents.
- [x] MP-325 Harden Ralph loop source-run correlation: pin `triage-loop` execution to authoritative source run id/sha when launched from `workflow_run`, fail safely on source mismatch, and preserve manual-dispatch fallback behavior (landed `--source-run-id/--source-run-sha/--source-event` parser+command+core wiring, source-run attempt pinning, run/artifact SHA mismatch detection with explicit `source_run_sha_mismatch` reason codes, and workflow source-run id/sha forwarding in `.github/workflows/coderabbit_ralph_loop.yml`).
- [x] MP-326 Implement real `summary-and-comment` notify semantics for `triage-loop`: add comment-target resolution (`auto|pr|commit`), idempotent marker updates, and workflow permission hardening so comment mode is deterministic and non-spammy (landed comment target flags, PR/commit target resolver, marker-based upsert behavior via GitHub API, and workflow permission updates including `pull-requests: write` + `issues: write`).
- [x] MP-327 Add bounded mutation remediation command surface (`devctl mutation-loop`) with report-only default, scored hotspot outputs, freshness checks, and optional policy-gated fix attempts (landed `dev/scripts/devctl/commands/mutation_loop.py`, `mutation_loop_parser.py`, `mutation_ralph_loop_core.py`, bundle/playbook outputs, and targeted unit coverage).
- [x] MP-328 Add `.github/workflows/mutation_ralph_loop.yml` orchestration: mutation-loop mode controls, bounded retry parameters, artifact bundling, and optional notify surfaces with default non-blocking behavior (landed workflow_run + workflow_dispatch wiring, mode/threshold/notify/comment inputs, summary output, and artifact upload).
- [x] MP-329 Add mutation auto-fix command policy gate: enforce allowlisted commands/prefixes, explicit reason codes on deny paths, and auditable action traces for each attempt (landed `control_plane_policy.json` baseline, `AUTONOMY_MODE` + branch allowlist + command-prefix gating, and policy-deny reason surfacing in mutation loop reports).
- [ ] MP-330 Scaffold Rust containerized mobile control-plane service (`voiceterm-control`) with read-only health/loop/ci/mutation endpoints and constrained workflow-dispatch controls.
- [ ] MP-331 Add phone adapter track (SMS-first pilot + push/chat follow-up) with policy-gated action routing, webhook auth, response/audit persistence, and bounded remote-operation scope. (partial: `devctl autonomy-loop` now emits phone-ready status snapshots under `dev/reports/autonomy/queue/phone/latest.{json,md}` including terminal trace, draft text, and source run context for read-first mobile surfaces; `devctl phone-status` now provides SSH/iPhone-safe projection views (`full|compact|trace|actions`) with optional projection bundle emission for controller-state files; `devctl controller-action` now provides a guarded safe subset (`refresh-status`, `dispatch-report-only`, `pause-loop`, `resume-loop`) with allowlist/kill-switch policy checks and auditable outputs; `app/ios/VoiceTermMobileApp` is now the runnable first-party iPhone shell, `app/ios/VoiceTermMobile` is the shared core package it imports, the app now exposes a short tutorial + live-bundle-first startup path, `devctl mobile-app` now supports a real simulator demo, a live-review simulator mode, and physical-device wizard/install actions, and the mobile bundle now surfaces typed Ralph/controller action previews through the shared backend contract. Remaining scope is the real live adapter: connect the iPhone to the Mac-hosted Rust control service on the same network first, add typed approve/deny plus operator-note/message actions, provider-aware continue/retask flows, and staged phone voice-to-action input, then add a secure off-LAN/cellular path with reconnect/resume semantics so the phone can rejoin long-running plans already active on the home machine without opening raw PTY/devctl ports to the public internet.)
- [ ] MP-332 Add autonomy guardrails and traceability controls (`control_plane_policy.json`, replay protection, mode kill-switch, branch-protection-aware action rejection, duplicate/stale run suppression). (partial: `control_plane_policy.json` added, `AUTONOMY_MODE` + branch/prefix policy gate wired for both mutation and triage fix modes, triage loop now emits dedicated review-escalation comment upserts when retries exhaust unresolved backlog, marker-based duplicate comment suppression landed, `devctl check --profile release` now enforces strict remote release gates (`status --ci --require-ci` + CI-mode CodeRabbit/Ralph checks), bounded controller surfaces now ship via `devctl autonomy-loop` + `.github/workflows/autonomy_controller.yml` with run-scoped checkpoint packet queue artifacts, and scheduled autonomy/watchdog/mutation-loop workflow-run behavior is now mode-gated so background loops are opt-in instead of default red-noise; replay protection + deeper branch-protection/merge-queue enforcement remain pending.)
- [x] MP-333 Enforce active execution-plan traceability governance: non-trivial agent work must be anchored to a `dev/active/*.md` execution-plan doc (with checklist/progress/audit sections), and tooling guardrails must fail when contract markers/required sections drift (landed enforcement updates in `check_active_plan_sync.py` for required execution-plan docs + marker + required sections, plus AGENTS contract references).
- [x] MP-334 Add external-repo federation bridge for reusable autonomy components: pin `code-link-ide` + `ci-cd-hub` in `integrations/`, provide one-command sync path, and document governed selective-import workflow for this repo template path. (landed submodule links + shell helper + `devctl integrations-sync`/`integrations-import` command surfaces, policy allowlists in `control_plane_policy.json` (`integration_federation`), destination-root guards, and JSONL audit logging for sync/import actions.)
- [ ] MP-335 Fix wake word send intent not triggering in auto mode: when VoiceTerm is in auto-listen mode and actively listening, saying "Hey Codex send" (or "Hey Claude send") does not trigger the send action — the wake word is effectively ignored while the mic is already open. Expected behavior: the wake-word detector should remain active during auto-mode listening so that saying the send wake phrase finalizes and submits the current transcript. Distinct from MP-322 (which covers "nothing to send" false negatives when the wake word does fire); this issue is that the wake word never fires at all in auto mode. Reproduce by enabling auto mode, speaking a transcript, then saying "Hey Codex send" without pausing — observe that the message is not sent. Physical testing required.
- [ ] MP-336 Add `network-monitor-tui` to the external federation + dev-mode bridge scope: link a pinned `integrations/network-monitor-tui` source, define allowlisted import profile(s) for throughput/latency sampler primitives, expose a read-only metrics surface for `--dev` + phone status views without introducing remote-control side effects, and add isolated runtime mode flags (`--monitor` and/or `--mode monitor`) so monitor/tooling startup does not interfere with the default Whisper voice-overlay path. The future monitor entry path should open the same Rust operator cockpit used by `--dev`, not a second forked console.
- [x] MP-337 Add repeat-to-automate governance and baseline scientific audit program: require repeated manual work to become guarded automation or explicit debt, add tracked `dev/audits/` runbook/register/schema artifacts, ship analyzer tooling (`dev/scripts/audits/audit_metrics.py`) that quantifies script-only vs AI-assisted vs manual execution share with optional chart outputs, and auto-emit per-command `devctl` audit events (`dev/reports/audits/devctl_events.jsonl`) for continuous trend data.
- [ ] MP-338 Stand up a loop-output-to-chat coordination lane: maintain a dedicated runbook for loop suggestion handoff (`dev/active/loop_chat_bridge.md`), define dry-run/live-run evidence capture, and keep operator decisions/next actions append-only so loop guidance can be promoted safely into autonomous execution. (partial: added `devctl autonomy-report` dated digest bundles, upgraded `devctl autonomy-swarm` to one-command execution with default post-audit digest + reserved `AGENT-REVIEW` lane for live runs, added `devctl swarm_run` for guarded plan-scoped swarm + governance + plan-evidence append, added bounded continuous cycle support via `--continuous/--continuous-max-cycles` so runs keep advancing unchecked checklist items until `plan_complete`, `max_cycles_reached`, or `cycle_failed`, wired workflow-dispatch lane `.github/workflows/autonomy_run.yml`, and added `devctl autonomy-benchmark` matrix reports for plan-scoped swarm-size/tactic tradeoff evidence.)
- [ ] MP-340 Deliver one-system operator surfaces + deterministic autonomy learning: keep Rust overlay as runtime primary, keep iPhone/SSH surfaces over one `controller_state` contract, and implement artifact-driven playbook learning (fingerprints, confidence, promotion/decay gates) so repeated loop tasks are reused safely with auditable evidence. This umbrella scope also owns the cross-plan contract that keeps Memory Studio (`MP-230..MP-255`), the review channel (`MP-355`), and controller surfaces on one shared event/header model, one provider-aware handoff path, and one future unified timeline/replay view rather than three parallel side channels. Current direction: grow the existing Rust Dev panel into a staged operator cockpit (`Control`, `Ops`, `Review`, `Actions`, `Handoff`, plus developer-oriented Git/GitHub/CI/script/memory views), then let `--monitor` reuse that same cockpit as a dedicated startup path. The first `Ops` slice is the Rust-first lane for host-process hygiene, triage summaries, and later external monitor adapters, so those readouts stay in the typed control surface instead of Theme Studio or a parallel ad hoc UI. Buttons may emit high-level intents and AI may resolve those intents to the correct approved playbook, but execution must still route through one typed action catalog plus shared policy/approval/waiver model rather than bypassing safety with raw shell/API execution. MP-340 now also explicitly carries an overlay-native live guard-watchdog direction: the overlay may observe Codex/Claude PTY traffic, session-tail artifacts, repo diffs, and typed review/controller packets to infer what the agent is doing and trigger the matching repo guard family, but guard enforcement must stay typed, policy-gated, debounced, and auditable through `devctl` / controller actions rather than raw terminal injection. The watchdog is now also required to prove impact scientifically: capture matched before/after guarded coding episodes, use paired analysis by task, report effect sizes with confidence intervals plus practical-significance thresholds, and only then promote claims that the guards materially improve Codex/Claude output; the MP-340 analytics layer must also capture repo-owned speed/latency/churn/retry/collaboration metrics from terminal and guard episodes so the project can study time-to-green, guard-hit heatmaps, provider deltas, and other operational signals with a real dashboard instead of anecdotes. Later ML work is allowed, but only as a second-phase ranking/prediction layer over that same artifact corpus after deterministic learning and offline evaluation are already working. Current `phone-status` / `controller-action` payloads and Rust Dev-panel snapshot builders are still interim projections; `devctl mobile-status` is now the first merged SSH-safe phone shim that combines review + controller state, `app/ios/VoiceTermMobile` is the shared first-party core package over that payload, and `app/ios/VoiceTermMobileApp` is the runnable iPhone/iPad app shell over the same emitted mobile bundle with guided simulator demo plus live-review proving modes and typed Ralph/controller action previews, but true MP-340 convergence still only happens once Rust, phone, review, and memory all read one emitted `controller_state` projection set with parity tests and provider-aware memory pack attachments. The mobile end-state is no longer just read-first bundle import: the Mac-hosted Rust control service must become the shared live source for overlay/dev/phone clients, the iPhone must gain typed approvals and structured operator-note/message dispatch plus staged voice-to-action flows, and the same host state must remain reachable over both local Wi-Fi and a secure off-LAN/cellular adapter with reconnect/resume semantics so ongoing plans continue on the home machine without exposing raw PTY or freeform shell access publicly. Immediate follow-up is now explicit: prove a simple phone ping/alert path first, then close richer iPhone parity over the same backend with split/combined terminal-style lane mirrors, typed approvals/notes/instructions, plan-to-agent assignment, simple/technical modes, provider-aware continue/retask routing, and reconnect/resume behavior. PyQt6 today, iPhone now, and any future Electron/Tauri shell later are clients of that shared backend only; none of them become the backend. Execution profiles should be explicit: `Guarded` by default, `AI-assisted Guarded` when the planner picks from the approved catalog, and a visible dev-only `Unsafe Direct` mode for local bypasses that stays red, noisy, and auditable rather than hidden. (2026-02-26 reset: retired the optional `app/pyside6` desktop command-center scaffold to keep operator execution Rust-first; all active scope now routes through Rust Dev panel + `devctl phone-status` + policy-gated `controller-action`. 2026-02-26 federation follow-up: completed fit-gap audit and added narrow import profiles for targeted `code-link-ide`/`ci-cd-hub` reuse instead of broad tree imports.)
- [ ] MP-340 follow-up: treat `triage-loop` consumption and generic triage-artifact consumption as separate closures. The controller already runs `triage-loop` each round, so the remaining gap is that generic `devctl triage` rollups and structured `triage-loop.backlog_items` still do not shape autonomy plan selection or context recovery; feed that same file/line backlog into checkpoint packets and planner context before widening into heavier learning or UI work.
- [ ] MP-340 follow-up: retire the remaining Dev-panel raw-`python3` bypass in `ops_snapshot.rs` so `process-audit` / `triage` refresh routes through `DevCommandBroker` or the shared typed action path instead of a sidecar shellout that skips the broker's timeout, cancellation, and command-audit semantics.
- [ ] MP-340 follow-up: restore `mobile-status` stale-state parity with
  review/runtime truth. The first merged phone surface should distinguish
  `stale` from `runtime_missing` using the same typed review-state semantics as
  `review-channel`, and focused compact/full/alert projections plus tests must
  stay aligned before more phone/app routing lands.
- [ ] MP-341 Runtime architecture hardening pass for product-grade boundaries: tighten `rust/src/lib.rs` public surface (remove legacy re-export drift and prefer internal/facade boundaries), replace stringly `VoiceJobMessage::Error(String)` with typed error categories at subsystem boundaries, harden command parsing (`CustomBackend` quoting-safe parsing), reduce global-side-effect risk in Whisper stderr suppression path, and modernize PyPI launcher distribution flow away from clone+local-build bootstrap toward verified binary delivery. (partial 2026-02-25: hardened SIGWINCH registration via `sigaction` + `SA_RESTART`, removed production `unreachable!()` fallback in Theme Studio non-home renderer path, and reduced silent PTY-output drop risk with explicit unexpected-branch diagnostics.)
- [ ] MP-342 Increase push-to-talk startup grace by about 1 second to prevent early cutoff when users do not speak immediately after pressing PTT: currently first-press captures can end too quickly if there is a short delay before speech starts. Reproduce in Codex/Claude sessions, tune initial-silence/warmup handling for natural speech onset, add regression coverage for delayed speech starts, and verify no regressions for intentional short taps.
- [ ] MP-343 Stabilize screenshot button reliability: screenshot capture currently succeeds intermittently and can stop unexpectedly after some successful attempts. Reproduce repeated capture attempts in active sessions, harden button-triggered capture lifecycle/error handling, add regression coverage for repeated runs, and verify physical behavior with screenshot evidence.
- [ ] MP-344 Re-investigate Cursor mouse-mode scroll behavior and restore reliable wheel/touchpad scrolling when `Mouse` is ON: current reports indicate wheel/touchpad scrolling does not move chat history in Cursor while the draggable scrollbar still works. Document and preserve current workaround (`Mouse` ON + drag scrollbar, or set `Mouse` OFF for touchpad/wheel scrolling and use keyboard button focus with `Enter`), reproduce on Codex/Claude sessions, harden input-mode handling, and add regression coverage for Cursor-specific scroll paths. Scientific baseline seeded on 2026-02-25 via `devctl autonomy-benchmark` run `mp342-344-baseline-matrix-20260225` (covers `MP-342/MP-343/MP-344`; artifacts under `dev/reports/autonomy/benchmarks/mp342-344-baseline-matrix-20260225/`); live control-vs-swarm A/B run captured via `mp342-344-live-baseline-matrix-20260225` plus graph bundle `dev/reports/autonomy/experiments/mp342-344-swarm-vs-solo-20260225/`. 2026-03-05 backlog clarification: keep this scoped as post-next-release work unless it becomes a release blocker.
- [x] MP-345 Stand up a visible `data_science` telemetry workspace and continuous devctl metrics refresh so every devctl command contributes to long-run productivity/agent-sizing research: landed `data_science/README.md` workspace docs, new `devctl data-science` command (`summary.{md,json}` + SVG charts), automatic post-command refresh hook in `dev/scripts/devctl/cli.py` (disable with `DEVCTL_DATA_SCIENCE_DISABLE=1`), and weighted agent recommendation scoring from swarm/benchmark history (`success`, `tasks/min`, `tasks/agent`) under `dev/reports/data_science/latest/`; docs/history updated in `AGENTS.md`, `dev/scripts/README.md`, `dev/DEVCTL_AUTOGUIDE.md`, and `dev/history/ENGINEERING_EVOLUTION.md`.
- [x] MP-346 Execute IDE/provider modularization and compatibility hardening so host-specific behavior (`cursor`, `jetbrains`, `other`) and provider-specific behavior (`codex`, `claude`, `gemini`) are isolated behind explicit adapters, validated by matrix tests, and protected by God-file/code-shape/tooling governance gates (`dev/active/ide_provider_modularization.md`). (2026-03-02 docs scope: published explicit user-facing IDE compatibility matrix in README/USAGE with aligned links in QUICK_START + guides so only verified hosts are advertised as supported. 2026-03-02 audit triage scope added: dependency-policy gate hardening, guard-script coverage closure, adapter-contract completion inventory, and cross-plan shared-file ownership gates. 2026-03-02 exhaustive audit intake triage added: Dependabot/CODEOWNERS path-contract repair, active-plan sync required-row expansion, failure-triage watchlist coverage, current `bytes` RustSec remediation decision, Gemini/docs wording parity, plus CI baseline hardening gaps (MSRV/feature-matrix/macOS runtime lane + `cargo doc` gate) and governance tracker drift fixes. 2026-03-02 seventh-pass audit scope added: explicit host/runtime policy mapping for rolling detector + output redraw and 3 additional RuntimeProfile cross-product decisions, plus check-script signal hardening (`check_rust_audit_patterns`, `check_release_version_parity`, stale code-shape override detection). 2026-03-02 post-review blocker cleanup landed: `check_active_plan_sync.py` shape-budget recovery, `check_ide_provider_isolation.py` docs inventory registration, dedicated `check_agents_contract.py` test coverage, refreshed path-audit aggregate reporting, Gemini backend wording parity across user/developer docs, a new `cargo doc --workspace --no-deps --all-features` gate in `rust_ci.yml`, and explicit `cargo deny` enforcement in security/release workflow lanes. 2026-03-02 dependency-policy remediation closure landed: transitive `bytes` moved to `1.11.1`, `rust/deny.toml` now documents crate-scoped license exceptions for current runtime dependencies plus explicit `RUSTSEC-2024-0436` (`paste`) ignore rationale, and local `cargo deny` gate rerun passes. 2026-03-02 phase-0 governance/tooling follow-up landed: Rust CI now includes explicit MSRV/feature-matrix/macOS runtime validation, failure triage initially expanded for broad watch coverage, `check_code_shape.py` enforces stale override review-window checks, tracker drift was resolved (`MASTER_PLAN` board + local backlog ID deconfliction), and cross-plan shared-hotspot ownership/freeze gates are now mandatory in the runbook + board policy. 2026-03-04 phase-1 incremental cleanup slice landed: status-line JetBrains+Claude single-line fallback routing now consumes canonical `runtime_compat` helper and writer render host detection now maps through canonical `detect_terminal_host()` ownership instead of duplicate local host sniffing logic. 2026-03-04 additional phase-1 host-enum unification landed: writer render/state paths now use canonical `TerminalHost` directly (removed `writer/render.rs` `TerminalFamily` enum and replaced state-side `TerminalFamily` references), with writer-focused plus full `cargo test --bin voiceterm` coverage rerun. 2026-03-04 CI signal hardening follow-up landed: failure-triage scope narrowed to high-signal failure conclusions, release publishers now wait for same-SHA CodeRabbit/Ralph + `Release Preflight` gates, and scheduled autonomy/watchdog/mutation-loop workflow-run behavior now defaults to opt-in mode controls to reduce non-actionable red runs. 2026-03-04 additional phase-1 host-routing cleanup landed for banner/color/theme paths: banner skip policy now routes through canonical `runtime_compat::is_jetbrains_terminal`, color truecolor inference now uses canonical `runtime_compat::detect_terminal_host` for JetBrains/Cursor signals, and `theme/detect.rs` Warp fallback now respects canonical host precedence with dedicated regression coverage. 2026-03-04 final phase-1 host-routing slice landed in `theme/texture_profile.rs`: Cursor/JetBrains identity now routes through canonical `runtime_compat::detect_terminal_host`, local parsing is limited to non-host capability IDs, and regression coverage now asserts host precedence plus Kitty/iTerm fallback markers. 2026-03-04 canonical host-cache contract slice landed: runtime host detection now owns `OnceLock<TerminalHost>` caching in `runtime_compat`, thread-local test override/reset coverage validates deterministic host injection, and writer render no longer duplicates host caching. 2026-03-04 host-cache panic-path hardening landed: `runtime_compat` test override scoping now restores prior thread-local host values via drop guard on unwind, with dedicated panic regression coverage. 2026-03-04 Phase-1.5 shared-helper extraction landed: duplicated HUD debug env parsing/preview helpers were removed from `writer/state.rs`, `event_loop/prompt_occlusion.rs`, and `terminal.rs` and replaced with a shared `hud_debug` module, with full `cargo test --bin voiceterm` rerun green. 2026-03-04 additional Phase-1.5 backend-detection cleanup landed: writer-state backend checks now route through canonical `runtime_compat::backend_family_from_env()` + `BackendFamily` enum matching instead of raw backend-label substring parsing, with full runtime suite rerun green. 2026-03-04 provider-contract scaffolding slice landed: new `provider_adapter` signature module defines `ProviderAdapter`/`PromptDetectionStrategy` and provider-policy enums/config so Phase-2+ extraction can target stable trait contracts; CI profile rerun is green after adding signature-only scaffolding. 2026-03-04 Phase-1.5 closure slice landed: ANSI stripping now routes through shared `ansi` utility, env-var locking in runtime tests now routes through shared `test_env` helper instead of duplicated per-module locks, and `claude_prompt_suppressed` was renamed to `prompt_suppressed` across runtime/test code with full runtime+bundle validation green. 2026-03-04 Phase-2a data-only host timing extraction landed: `runtime_compat::HostTimingConfig` now owns host timing values keyed by `TerminalHost`, and writer timing call sites route through config lookups while preserving characterization behavior and passing full runtime + bundle validation. 2026-03-04 Phase-2b preclear policy extraction landed: writer preclear decisioning now routes through typed `PreclearPolicy` + `PreclearOutcome` so preclear decision and post-preclear flag effects are centralized while preserving existing host/provider behavior and full runtime + bundle validation remained green. 2026-03-04 Phase-2c redraw policy extraction landed: writer output redraw decisioning now routes through typed `RedrawPolicy` + `RedrawPolicyContext` consuming `PreclearOutcome`, so scroll/non-scroll/destructive-clear redraw outcomes are centralized while preserving existing host/provider behavior and full runtime + bundle validation remained green. 2026-03-04 Phase-2d idle-gating timing extraction landed: `maybe_redraw_status` idle/quiet-window/repair-settle gating now routes through typed `IdleRedrawTimingContext` + `resolve_idle_redraw_timing` in `writer/timing.rs`, with full runtime + bundle validation remaining green. 2026-03-04 Phase-2e message-dispatch + runtime-profile extraction closure landed: WriterState now resolves and injects a typed RuntimeProfile at construction, handle_message is dispatch-only, and PTY handling routes through explicit preclear/redraw policy pipeline helpers plus state-update application helpers, and completed the writer-state decomposition target (`writer/state.rs` now 448 lines across dedicated `state/*` modules), so Step 2f is the next scope. 2026-03-04 post-closure governance audit added immediate Step-2f tightening scope: new Step 2f.1 (allowlist burn-down + shape-budget reset), Step 2f.2 (function-size guardrails for dispatcher/pipeline hotspots), and explicit Phase-4 compatibility-governance kickoff (`ide_provider_matrix.yaml`, `check_compat_matrix.py`, `compat_matrix_smoke.py`, `devctl compat-matrix`) directly after Step-2f closure. 2026-03-04 CP-013 closure landed: Step 2f/2f.1/2f.2 are now implemented with blocking isolation defaults, narrowed explicit allowlists, tightened shape budgets, function guardrails with owner/expiry exceptions, and the Phase-4 compatibility governance scaffold is active. 2026-03-04 post-CP-013 hardening slice landed: isolation scanner now catches host-enum + provider-backend helper coupling patterns without broad helper-name false positives, runtime mixed-condition callsites in writer render/dispatch/redraw were rerouted through runtime-profile and canonical compatibility helpers, prompt hotspots were reduced under hard limits (`prompt_occlusion.rs` 1143 and `claude_prompt_detect.rs` 623 via test-module extraction), and lint-debt guard now detects inner `#![allow(...)]` attributes with dedicated regression coverage. 2026-03-04 Phase-3a prompt strategy wiring landed: prompt detector construction now routes through provider adapters with Claude-owned strategy ownership plus temporary legacy-shim parity fallback; CI/runtime/docs governance bundle remains green. 2026-03-04 checkpoint/state sync: `CP-016` docs/state continuation sync is in progress; Step `3a.1` (legacy-shim retirement) is closed, Step `3c` is closed, Step `3b` is now closed (Steps `3e` and `3f` are closed), and Phase-5/Phase-6 closure gates (AntiGravity decision + ADR lock) remain pending. 2026-03-05 Phase-5 defer decision: AntiGravity moved to deferred scope until runtime host fingerprint evidence exists; active MP-346 host matrix scope is now `cursor`/`jetbrains`/`other`. 2026-03-05 Phase-6 governance closure landed: ADR `0035` and ADR `0036` are accepted and indexed, leaving IDE-first `CP-016` manual matrix closure (`4/4`) complete for release scope, with deferred `other`/`gemini` validation tracked as post-next-release backlog. 2026-03-04 additional CP-016 hardening landed: IPC lifecycle routing now delegates through a dedicated provider lifecycle adapter module and isolation guardrails now enforce file-scope coupling detection with explicit temporary allowlist debt for Step-3b hotspot files.)
- [ ] MP-347 Add an execution router for pre-push checks and tighten dead-code debt governance across Rust runtime/tooling paths. (2026-03-05 PR-1 landed: added `devctl check --profile fast` as a compatibility alias of `quick` and updated command/docs surfaces. 2026-03-05 PR-2 landed: added `devctl check-router` with changed-path lane selection (`docs`, `runtime`, `tooling`, `release`), strict unknown-path escalation to tooling lane, risk-add-on detection from AGENTS risk-matrix signals, and optional `--execute` mode that runs routed bundle commands. 2026-03-05 dead-code governance slice landed: `check_rust_lint_debt.py` now inventories dead-code allows and supports policy flags (`--report-dead-code`, `--fail-on-undocumented-dead-code`, `--fail-on-any-dead-code`), AI guard runs now include dead-code reporting, and all current runtime dead-code allow attributes carry explicit rationale metadata. 2026-03-05 PR-3 landed: command bundles moved into canonical `dev/scripts/devctl/bundle_registry.py`; `check-router` and `check_bundle_workflow_parity.py` now consume registry commands and AGENTS bundle blocks are rendered/reference-only. 2026-03-05 PR-4 landed: heavy-check placement formalized in maintainer docs (`prepush`/`release`/CI remain strict; `fast`/`quick` stay local-only minimal lanes). 2026-03-05 PR-5 landed: AGENTS rendered bundle docs are now auto-validated/regenerable via `check_agents_bundle_render.py` and strict-tooling docs gate wiring. 2026-03-05 post-implementation architecture audit reopened remaining scope: current `check_code_shape.py` merge-blockers (`check_router.py` and `docs_check_support.py` growth), router/docs-governance taxonomy duplication, risk-add-on SSOT drift risk, and missing `jscpd` report evidence in `check_duplication_audit.py` must be resolved before re-closing this MP. 2026-03-05 phase-1 closure cleanup landed: shape blockers are resolved via check-router/docs-check decomposition, `check_duplication_audit.py` now emits explicit `status`/`blocked_by_tooling` evidence fields plus an explicit constrained-environment fallback (`--run-python-fallback`) while preserving `jscpd` as primary, canonical `jscpd` report evidence is refreshed (`dev/reports/duplication/jscpd-report.json`), and the closure non-regression command pack is green; remaining MP-347 follow-up is taxonomy/SSOT hardening. 2026-03-05 verification refresh: canonical helper ownership for duplication audit is now stable (`check_duplication_audit_support.py`), stale archive literals were removed from active docs/changelog, and the row `2331` non-regression pack rerun remains fully green. 2026-03-06 docs-IA intake update: Round 4 developer-information-architecture + active-directory hygiene audit is now tracked in `dev/active/pre_release_architecture_audit.md` (Phase 15) and remains open pending migration implementation. 2026-03-06 docs-index follow-up: reduced duplicate entrypoint drift by making `dev/README.md` the explicit canonical developer index and converting `DEV_INDEX.md` into a thin bridge page. 2026-03-06 guide-path migration follow-up: moved durable maintainer guides to `dev/guides/` with one-cycle bridge files at legacy paths and updated mapped coupling surfaces (`docs_check_policy`, `check_router_constants`, `tooling_control_plane.yml`, AGENTS/README entrypoints, and docs-check/path-rewrite tests). 2026-03-08 maintainer-lint follow-up: add an explicit advisory `pedantic` `devctl check` profile, keep it out of required bundles and release gates, and document it as an opt-in lint-hardening sweep so agents use it intentionally instead of treating pedantic noise as mandatory release work. 2026-03-08 pedantic follow-up: keep pedantic on the existing `report`/`triage` architecture by having `check --profile pedantic` emit structured artifacts under `dev/reports/check/`, `report --pedantic` / `triage --pedantic` consume those artifacts through the shared project snapshot, support explicit inline regeneration via `--pedantic-refresh`, and use `dev/config/clippy/pedantic_policy.json` to record promote/defer/review decisions so AI classification is repo-owned instead of ad hoc per release. 2026-03-08 maintainability/IA follow-up: Phase-15 cleanup remains open for retiring temporary bridge entrypoints like `dev/ARCHITECTURE.md` and `dev/BACKLOG.md`, collapsing duplicate `dev/` entrypoints, and turning AGENTS trimming into a real post-release execution slice instead of a lingering note. 2026-03-09 guard follow-up: `check_rust_security_footguns.py` now also flags `unreachable!()` in hot runtime paths under `rust/src/bin/voiceterm/**`, `rust/src/audio/**`, and `rust/src/ipc/**`, with matching unit coverage, so the pre-push guard set keeps tightening around panic-shaped "should never happen" shortcuts in shipped runtime code.)
- [ ] MP-348 Investigate Codex composer/input-row occlusion after recent Codex CLI updates (reported 2026-03-05): during red/green diff-heavy output, IDE terminal sessions can show the backend input/composer row visually obscured near the HUD boundary. `Post-next-release only`; do not execute before release promotion unless explicitly reclassified as a blocker. Required evidence pack: one screenshot + `voiceterm --logs --codex` trace with terminal host/version, HUD style, terminal `rows/cols`, and overlap timing (`while working` vs `ready for input`). Initial code-audit hypothesis for follow-up validation: `terminal.rs` currently keeps Codex on a fixed v1.0.95 reserved-row budget (no extra safety-gap rows), and prompt-occlusion guard routing is presently Claude-only via `runtime_compat::backend_supports_prompt_occlusion_guard`, so Codex composer/card layout changes may bypass suppression and row-budget safeguards. Add targeted regression tests once logs confirm a deterministic repro.
- [ ] MP-349 Investigate Cursor+Claude plan-mode history/HUD corruption + transient garbled terminal output (reported 2026-03-05): in Cursor terminal sessions, asking Claude to enter plan mode (especially with local/background agents) can cause the visible history region to disappear while HUD/status UI rows render over output; some lines show garbled characters/symbols during the bad state. Repro clue from physical testing: issue clears after terminal resize/readjust, suggesting geometry/redraw synchronization drift. `Post-next-release only`; do not execute before release promotion unless explicitly reclassified as a blocker. Required evidence pack: before/after resize screenshots, terminal host/version, provider/backend, HUD style/mode, terminal `rows/cols` before and after resize, `voiceterm --logs` trace with `VOICETERM_DEBUG_CLAUDE_HUD=1`, and a timestamped sequence (`plan request -> corruption -> resize/readjust -> recovery`). Initial code-audit hypotheses: stale geometry cache, missed full-repaint transition, or prompt/HUD reserved-row mismatch in Cursor non-rolling flow. Add deterministic regression tests after a stable log-backed repro is confirmed.
- [x] MP-350 Keep `devctl` as primary control plane and add optional read-only
  MCP adapter without duplicate enforcement layers: locked release/check/cleanup
  semantics as executable contracts, documented MCP as additive (not a
  replacement), and closed the execution tracker into archive
  (`dev/archive/2026-03-05-devctl-mcp-contract-hardening.md`) while retaining
  durable guidance (`dev/MCP_DEVCTL_ALIGNMENT.md`, `dev/DEVCTL_AUTOGUIDE.md`,
  `dev/scripts/README.md`, `dev/ARCHITECTURE.md`).
- [ ] MP-351 Expand the built-in theme catalog with additional curated VoiceTerm
  themes, wire them through Theme Picker/Theme Studio/export surfaces, keep
  CLI/docs parity, and add snapshot coverage so new themes do not regress
  ANSI/256color fallback behavior.
- [ ] MP-352 Add slash-command control for voice modes so users can switch
  between `PTT`/manual voice, `AUTO`, and idle/listening-off flows without
  relying only on hotkeys; deliver `/voice` as a standalone command inside
  Codex CLI and Claude Code sessions without requiring the full VoiceTerm PTY
  overlay. Architecture audit (2026-03-06) confirmed PTY-based slash-menu
  injection is not viable; implementation path is phased: (A) `--capture-once`
  subprocess mode + markdown skill files for immediate `/voice` availability,
  (B) MCP server in Rust (`voiceterm-mcp`) exposing `voice_capture`,
  `voice_status`, `voice_mode_set` tools for both platforms, (C) Claude Code
  plugin packaging + Codex command file for native slash-menu UX. Execution
  spec: `dev/active/slash_command_standalone.md`. 2026-03-09 status: Phase A
  implementation is landed locally (`--capture-once --format text`, slash
  templates, user docs, targeted capture tests green), while full runtime
  validation remains open because current branch-wide guard/test failures are
  unrelated to the slash-command slice. Require manual validation of
  enable/disable/exit behavior before closure.
- [ ] MP-353 Add a settings toggle for momentary push-to-talk hotkey behavior
  ("hold to talk") so manual voice can run as either the current toggle model
  or a press-and-hold capture mode; wire the preference through Settings plus
  config/CLI surfaces, preserve current behavior by default, and require
  physical hotkey validation before closure.
- [x] MP-354 Execute post-release IDE/provider coupling remediation so the
  writer dispatch/timing/startup paths reduce cross-product blast radius before
  additional runtime feature work continues. Scope is tracked in
  `dev/active/ide_provider_modularization.md` Phase 7 (`Step 7a`-`Step 7f`):
  adapter-owned writer state split, `handle_pty_output` pipeline decomposition,
  redraw timing/policy de-tangling, `main.rs` startup decomposition, shared VAD
  factory ownership, and guard-script dedup follow-up with checkpoint packets.
  2026-03-07 status: `Step 7a`, `Step 7b`, `Step 7c`, `Step 7d`, `Step 7e`,
  and `Step 7f` complete (writer adapter-owned state split +
  `handle_pty_output` staged decomposition + runtime-variant timing/policy
  de-tangling + startup phase decomposition + shared
  `audio::create_vad_engine` ownership + guard bootstrap/helper dedup
  closure); queued follow-up `R8 + R9 + R10`, `R6 + R7 + R11`,
  `R12 + R13 + R18`, and residual low-risk `R14 + R15 + R16 + R17` are now
  complete, and Python residual follow-up `P11 + P12` is now complete as well
  (typed `RuleEvalContext`, `AppConfig::validate` helper split, grouped
  prompt-occlusion output signals, glyph-table style resolution,
  runtime/schema + style-schema macro dedup cleanup, parser control-byte
  dispatch helper extraction, wake-listener join lifecycle dedup, lookup-based
  wake send-intent suffix matching, named legacy UI color constants, typed
  `BannerConfig` ownership, render host-resolution threading cleanup,
  style-pack override state accessor dedup, UTC tooling/check report timestamp
  normalization, and explicit `SECONDS_PER_DAY` age-math constants). MP-354 is
  closed; the doc stays active only because post-next-release `MP-346` backlog
  items remain deferred there. Phase-7 priority queue remains closed.
- [ ] MP-355 Deliver a dedicated shared review-channel + staged shared-screen
  execution slice: extend the MP-340 control-plane direction with one
  review-focused packet/event contract (`review_event` append-only authority +
  `review_state` latest snapshot), standard projections (`json`, `ndjson`,
  `md`, `terminal_packet`), and a flat `devctl review-channel` action surface
  (`post`, `status`, `watch`, `inbox`, `ack`, `history`); render a shared
  VoiceTerm surface where Codex + Claude + operator lanes are visible
  together as one collaborative terminal-native workflow, keep separate
  PTY ownership in the initial phases while packets/staged drafts/peer
  awareness stay visible on that same surface, require Claude-side dual-agent
  repolls to consume direct reviewer packets through `inbox/watch` alongside
  bridge polling when the structured queue is available, add the structured
  `check_review_channel.py` guard plus retention/audit integration in the same
  tranche, and keep `check_review_channel_bridge.py` as the temporary
  markdown-bridge guard while `bridge.md` remains the active projection.
  Defer true concurrent shared-target-session writing until lock/lease,
  ack/apply, and audit guardrails are proven. Phase-0 design closure requires
  explicit reconciliation with MP-340 plus `ADR-0027`/
  `ADR-0028`, a lossless header mapping into Memory Studio's canonical event
  envelope, and one
  `context_pack_refs` contract for `task_pack` / `handoff_pack` /
  `survival_index` attachments. Early phases must emit
  `packet_posted|packet_acked|packet_dismissed|packet_applied` into the memory
  ingest path when capture is active and keep provider-specific attachment
  shaping routed through Memory adapter profiles instead of a review-only pack
  format. Current
  transitional operating mode uses repo-root `bridge.md` as a sanctioned
  temporary projection for the current Codex/Claude swarm, but MP-355 itself
  remains a reusable review/runtime contract slice over the shared backend
  rather than the product boundary.
  Current
  transitional operating mode uses repo-root `bridge.md` as a sanctioned
  coordination-log projection with explicit ownership, poll cadence, current-
  state fields, and `check_review_channel_bridge.py` governance until the
  structured artifact path lands, and the final artifact model must remain
  compatible with memory/handoff compilation. Routed actions requested from the
  review lane must go through the same typed command catalog and shared
  approval/waiver engine used by operator buttons and controller surfaces; no
  review-specific raw shell or raw API bypass is allowed. 2026-03-09 bridge-
  hardening follow-up landed: rollover now rejects
  `--await-ack-seconds <= 0` so fresh-session ACK stays fail-closed, and the
  temporary `check_review_channel_bridge.py` guard now requires live
  `Last Reviewed Scope` plus a non-idle `Current Instruction For Claude`
  section whenever the markdown bridge is active. 2026-03-09 bridge-backed
  status follow-up landed: `devctl review-channel --action status` now writes
  current-latest projections under `dev/reports/review_channel/latest/`
  (`review_state.json`, `compact.json`, `full.json`, `actions.json`,
  `latest.md`, `registry/agents.json`), and rollover ACK detection now
  normalizes markdown list items correctly so live visible ACK lines are
  actually observed. 2026-03-09 launch/freshness follow-up landed: fresh
  conductor bootstrap now fails closed on untracked bridge files, stale
  reviewer polls beyond the five-minute heartbeat contract, and idle/missing
  live next-action state; the bridge liveness model now distinguishes
  `poll_due` vs `stale`, and rollover ACK validation now requires the exact ACK
  line inside the provider-owned bridge section (`Poll Status` for Codex,
  `Claude Ack` for Claude) instead of raw substring matches. 2026-03-09
  workflow-parity follow-up landed: `check_bundle_workflow_parity.py` now
  parses per-job run scopes, requires the tooling bundle sequence to stay in
  `docs-policy`, and requires the operator-console pytest lane to stay in
  `operator-console-tests` so wrong-job or out-of-order regressions fail
  closed instead of passing on command-presence alone. Codex re-review later
  the same day narrowed the bridge-hardening closure: `launch` still does not
  invoke the full bridge guard before bootstrap, freshness enforcement is
  still split between the five-minute heartbeat contract and a looser guard
  threshold, generated rollover prompts still hardcode the default ACK
  timeout instead of threading the selected value end-to-end, and one
  duplicate `test_review_channel.py` name still shadows intended coverage.
  2026-03-22 live-loop follow-up: the current bridge/runtime path still
  collapses continuation-budget pauses into generic `waiting_on_peer` even
  when typed status already reports `attention.status=checkpoint_required` and
  `safe_to_continue_editing=false`; keep MP-355 open until checkpoint-gate
  pauses become a first-class typed wait reason across status/projection/
  bridge surfaces so Codex and Claude can stay synchronized while edits are
  intentionally paused. A later same-lane bounded follow-up also closed the
  adjacent reviewer-side stale-state ambiguity: active-dual-agent attention
  and bridge-poll routing now emit `review_follow_up_required` when Claude has
  changed the live tree under an active reviewer supervisor and
  `reviewed_hash_current=false`, so reviewer follow-up no longer looks like a
  generic done/stale state while Codex still owes a re-review pass. Focused
  review-channel tests (`231`) and `devctl check --profile ci` are green on
  that slice. The next bounded same-lane follow-up is now also in: the
  implementer wait/reporting surface exports typed attention status/summary/
  recommended-action fields and state-specific timeout/wake messages, so the
  loop no longer relies on generic "Holding for Codex review" text when the
  backend already knows it is paused on `review_follow_up_required` or
  `claude_ack_stale`. A later same-lane parity step now does the same on the
  reviewer side: `review-channel --action reviewer-wait` exports typed wait
  attention fields and state-specific wake/timeout/unhealthy messages, and the
  reviewer bootstrap contract now explicitly routes Codex onto that repo-owned
  wait path when parked on Claude progress instead of ad-hoc sleep loops. The
  checkpoint-gate pause projection and the broader repo-owned semantic
  reviewer-worker/service path still remain open. A 2026-03-25 stale-
  implementer recovery follow-up also landed the narrower recovery primitive:
  attention now emits `implementer_relaunch_required`, the new
  `review-channel --action recover --recover-provider claude` path replaces
  only the stale Claude conductor, reviewer-follow escalates repeated
  unchanged stale-implementer state through that repo-owned recovery path, and
  `launch|rollover` no longer fail solely because the reviewer loop is stale
  on the implementer side.
  A 2026-03-26 live-loop follow-up also tightened the conductor contract
  itself: the default planned rollover threshold is now 20% remaining context,
  reviewer prompts must stay conductor-only when listed lane worktrees are
  missing instead of improvising live-repo fallback workers, and reviewed-hash
  truth now ignores advisory artifacts such as `convo.md` and `dev/audits/**`
  so live reviewer follow-up tracks the real execution slice instead of scratch
  intake material.
  A second 2026-03-26 follow-up closed the next live honesty gap too: the
  repo now teaches the anti-stall contract through generated `CLAUDE.md`,
  bridge start rules, maintainer docs, and prompt guards together, bridge
  validation rejects no-op implementer parking such as `No change.
  Continuing.` while active work is still assigned, and `review-channel
  --action status` now treats `active_dual_agent` without repo-owned
  conductors as a bridge-contract error instead of healthy detached-daemon
  freshness.
  Latest follow-up (2026-04-04): reviewer bootstrap receipt teaching is now
  equally explicit. Fresh Codex conductors still begin with
  `startup-context --role reviewer --format summary`, but non-zero
  `continue_editing` / `review_pending` and `await_review` /
  `review_pending_before_push` receipts are now documented and taught as
  normal reviewer-owned bootstrap states while the live loop is healthy, so
  the reviewer continues into `review-channel --action status` plus bridge
  heartbeat refresh instead of widening into generic repair. Real repair stays
  bounded to `repair_reviewer_loop`, checkpoint/budget blockers, or typed
  stale/non-live reviewer runtime.
  2026-04-08 recovery-precedence follow-up: typed bridge/runtime recovery now
  keeps the detached-loop path honest too. Once `current_session` shows a
  current Claude ACK but launch truth degrades to
  `detached_runtime_only`/`automation_only`/`hybrid_claude_only`,
  status/startup/doctor no longer misroute that state through
  `reset-implementer-state`; if checkpoint authority is otherwise clear they
  emit `review_loop_relaunch_required` and the reviewer-owned
  `launch|rollover` recovery command instead, but an over-budget
  `reviewed_hash_current=true` / `review_needed=false` snapshot now preempts
  that detached-runtime repair with `checkpoint_required` plus the governed
  checkpoint command.
  2026-04-08 launch-warmup follow-up: typed session-state hints now require a
  true idle prompt before they emit `waiting_for_user_input`. Fresh Terminal
  launch/recover sessions that still show active `esc to interrupt` progress,
  or logs still inside the short warmup window, stay out of the manual-input
  recovery path so the live loop does not stack duplicate Claude windows while
  the new conductor is still bootstrapping.
  A 2026-03-30 stale-reader follow-up closed the next same-lane write-safety
  gap: bridge-backed `status` / `bridge-poll` now emit a typed
  `implementer_state_hash`, active-dual-agent `reviewer-checkpoint` writes
  require that hash alongside the expected instruction revision, and repo-
  owned promotion/scope rewrites thread the same hash when they act on a
  previously validated bridge snapshot.
  A second 2026-03-30 architecture follow-up closed the reviewer-drift gap
  too: reviewer vs implementer startup commands plus explicit reviewer
  takeover now live in runtime-owned `ConductorCapabilityState`, review-
  channel prompt/bridge bootstrap surfaces render from that typed capability,
  and the `platform_layer_boundaries` guard now blocks startup-authority/
  runtime capability modules from importing `review_channel` orchestration
  directly.
  The next narrowed runtime-consumer splice is also explicit: queue and
  attention already drive current-focus and wait projections, but startup/
  work-intake routing and reviewer/implementer scheduling still ignore
  `agent_registry` plus the wider typed review-status bundle, so MP-355 stays
  open until those controller inputs stop being display-only.
  2026-04-02 rollover terminal-cleanup follow-up: Terminal.app launches now
  persist the returned `terminal_window_id` into conductor session metadata,
  `session_probe` snapshots that window id plus the retiring conductor pid
  before rollover rewrites the live session files, and live
  `review-channel --action rollover --terminal terminal-app` now reaps old
  conductor sessions by killing the old pid before closing the empty window.
  Focused launch/helper regressions are green; keep MP-355 open until the
  remaining broader launch/runtime contract gaps are also closed.
  2026-04-03 daemon-liveness follow-up: live
  `review-channel --action launch|rollover --terminal terminal-app` now
  auto-starts the repo-owned ensure-follow publisher plus the reviewer-
  supervisor runtime and fails closed if that detached runtime does not come
  up, so repo-owned launch and the phone-steered remote wrapper no longer
  depend on a separate manual `ensure --follow` bootstrap step. Focused
  launch/runtime regressions are green; keep MP-355 open until crash-restart
  and doctor-registration follow-ups land.
  Keep MP-355 open until those launch/freshness/ACK/coverage gaps are closed.
  2026-03-25 regression follow-up: targeted
  `test_check_review_channel_bridge.py` now shows the temporary bridge guard
  no longer flags resolved verdicts without promoted next-task routing, so the
  fail-closed semantic bridge validator remains an open blocker too.
  2026-03-09 operator
  validation follow-up confirmed the current dirty-tree behavior: focused
  `test_review_channel` coverage passed (`31` tests), `devctl review-channel
  --action status --terminal none --format md` wrote the latest projection
  bundle successfully, and `launch` / `rollover` dry-runs remain expected-red
  while `bridge.md` and `dev/active/review_channel.md` stay untracked
  bridge files in this checkout. A later 2026-03-09 fail-closed follow-up also
  closed the missing-`Claude Status` / missing-`Claude Ack` launch gap and
  stopped degraded `waiting_on_peer` bridge states from reporting `ok: true`
  or `claude.status == active` in review/mobile projections. A later same-day
  launcher follow-up also writes per-session metadata plus live-flushed
  conductor transcript logs under
  `dev/reports/review_channel/latest/sessions/` so repo-owned desktop shells
  can tail real session output without taking PTY ownership away from
  Terminal.app. Another same-day operator-blocker fix now clears inherited
  `CLAUDECODE` markers inside generated Claude conductor scripts so live
  Terminal-app launches do not fail as nested Claude Code sessions when
  started from an existing Claude-owned shell. A later 2026-03-09 Codex
  re-review also confirmed via focused `test_review_channel` coverage that
  custom `--await-ack-seconds` values are threaded end-to-end, so that older
  suspected ACK-timeout bug is no longer part of MP-355's open blocker set.
  A later same-day live-launch audit also found a new bootstrap honesty gap:
  non-dangerous Codex conductors can spend their first minutes on worker fan-
  out and approval-bound tool prompts before rewriting `Last Codex poll`,
  letting the bridge age into stale even while the session logs are active.
  The launcher prompt now requires Codex to stamp `Last Codex poll`, `Last
  non-audit worktree hash`, and `Poll Status` before fan-out and forbids
  parking silently on unanswered approval prompts without reflecting that
  blocked state in the bridge. A later same-day overlay/runtime follow-up also
  landed the first structured-authority consumer in the Rust shell: the Dev-
  panel Review surface now prefers event-backed review artifacts
  (`projections/latest/full.json`, `state/latest.json`, or legacy
  `latest/*.json` outputs) whenever review-channel event sentinels exist,
  parses those JSON projections into the same `ReviewArtifact` view model used
  by the existing markdown bridge, and falls back to `bridge.md` only when
  structured state is absent. That proves the overlay can move onto canonical
  review state without changing default startup mode. A later same-day
  launcher hardening fix now refuses a second live `review-channel --action
  launch --terminal terminal-app` when the existing repo-owned
  `latest/sessions/` artifacts still look active, so operators cannot
  accidentally open duplicate Codex/Claude conductor windows that race on the
  same session-tail files, but the remaining
  event-backed `watch|inbox|ack|dismiss|apply|history` path is still open. A
  2026-04-25 S2 first slice added a bounded read-side
  `PacketOutcomeLedger` to `review-channel --action history --include-outcomes`
  so expired-pending packet rows can carry typed outcomes
  (`delivered_via_commit`, `superseded_by`, `promoted_to_finding`,
  `withdrawn_by_reviewer`, `expired_unrecoverable`; later
  `archived` disposition rows replaced the unresolved `lost` fallback) from
  later event evidence instead of staying invisible graveyard rows. The full
  blocking disposition guard over every pending packet remains open under
  `MP377-P0-T08E`; this slice only proves the typed model and narrow report
  surface. A
  2026-03-13 follow-up also closed the next live-launch honesty gap: the
  Terminal-app launch path now waits for `Last Codex poll` to advance and fails
  closed if a fresh reviewer heartbeat never appears, and the bridge-backed
  `review_state` payload now emits a typed `attention` contract so stale
  reviewer / poll-due / waiting-on-peer state is machine-readable instead of
  living only in warning prose. A same-slice cleanup follow-up extracted that
  attention/launch behavior into `attention.py`, `status_projection.py`, and
  `terminal_app.py` so the live-launch honesty path stays inside the repo's
  shape budget while keeping one typed liveness contract. The next MP-358
  follow-up is now explicit too: the newer `implementer_completion_stall`
  tandem guard must graduate into shared review-channel attention/runtime
  state so the same "Claude parked on review/polling" signal is visible to
  VoiceTerm, PyQt6, phone/mobile, CLI, and generated instruction surfaces
  instead of living only in prompt text plus an on-demand validator. Execution spec:
  `dev/active/review_channel.md`.
- [ ] MP-356 Tighten host-process hygiene automation so local AI/dev runs stop
  relying on manual Activity Monitor checks: add a dedicated host-side
  `devctl process-audit`/`devctl process-cleanup` surface, make the shared
  process sweep descendant-aware for leaked PTY child trees and orphaned-root
  cleanup descendants, update `AGENTS.md`/dev docs so post-test and pre-handoff
  host cleanup/audits are explicit, and close the remaining PTY lifeline
  watchdog leak so `cargo test --bin voiceterm theme` no longer sheds orphaned
  `voiceterm-*` helpers on the host. Follow-up widened the same audit/cleanup
  path to catch orphaned repo-tooling wrapper trees (for example stale
  `zsh -c python3 dev/scripts/...` roots with descendant helpers such as
  `qemu-system-riscv64`), direct shell-script wrappers, repo-runtime
  cargo/target trees from non-`--bin voiceterm` Rust tests, and repo-cwd
  generic helpers (`python3 -m unittest`, `node`/`npm`, `make`/`just`,
  `screen`/`tmux`, `qemu`, `cat`) that outlive their parent tree, while also
  excluding the current audit command's own ancestor tree. Follow-up synthetic
  leak repros tightened strict verification further: freshly detached
  repo-related helpers (`PPID=1`, still younger than the orphan age gate) now
  fail `process-audit --strict` / `process-cleanup --verify` immediately under
  a dedicated `recent_detached` state, and `process-watch` now exits zero once
  it actually recovers to a clean host instead of staying red because earlier
  dirty iterations are preserved in history. `check --profile quick|fast` now
  runs host-side cleanup/verify by default after raw cargo/test-binary
  follow-ups, and routed docs/runtime/tooling/release/post-push bundle
  authority ends with `process-cleanup --verify --format md` so the default
  AI/dev lane re-runs strict host cleanup automatically. Verified 2026-03-08
  with targeted PTY lifecycle tests, process-hygiene unit coverage, `cargo
  test --bin voiceterm theme -- --nocapture`, the required post-run quick
  sweep, strict host `process-audit`, live cleanup/verify of the orphaned
  repo-tooling `zsh -> qemu` tree, and live `process-watch` recovery from fresh
  synthetic repo-runtime + repo-tooling detached-orphan repros. Follow-up
  tracing closed one more live gap on 2026-03-08: banner tests no longer
  deadlock on nested env-lock acquisition, attached interactive helpers are no
  longer reported as stale repo-tooling failures, and AI-operated raw Rust
  tests now have a first-class `devctl guard-run` path that always executes
  the required post-run hygiene follow-up. A 2026-04-10 live headless
  review-channel proof closed the next Q41 gap: registered conductor wrappers
  that intentionally reparent to PID 1 now stay in supervised-conductor state
  for strict `process-audit` / `process-cleanup --verify`, while unregistered
  detached helpers remain blocking. A 2026-04-17 live remote-control follow-up
  closed the stale-authority variant of that same seam: host cleanup
  protection now trusts registry-backed running `session_pid` values when the
  script probe still says `running`, even if `session.live` flipped false
  because prepared-head freshness drifted. That keeps
  `host-process-cleanup-post` green for a real running conductor instead of
  forcing a kill-or-block choice during governed checkpoint retry. A
  2026-05-03 dogfood follow-up closed the opposite failure mode: a registered
  supervised conductor is no longer protected once its embedded
  `SessionCachePacket.head_sha` / review-state `head_sha` differs from current
  `HEAD`. Strict `process-audit` now reports those rows as
  `stale_supervised_conductors`, fails if `ps` access is unavailable, and
  `process-cleanup --verify` expands the stale conductor root to the full
  descendant tree before re-running strict host verification.
  Execution spec:
  `dev/active/host_process_hygiene.md`. 2026-03-09 Codex re-review reopened
  follow-up hardening: orphaned non-allowlisted repo-cwd descendants can
  still slip once the matched parent exits, tty-attached repo helpers
  (`python3 -m pytest` / `python3 -m unittest`) are still under-classified,
  and `guard-run --cwd <other-repo>` still audits/cleans this repo instead of
  the target cwd. Re-close only after focused regression proof covers those
  shapes.
- [ ] MP-357 Fix Claude/Cursor IDE overlay disappearing on terminal resize and
  when launching VoiceTerm in a terminal with pre-existing scrollback content:
  the HUD/status-line overlay can vanish or fail to render after a window resize
  event, and sessions started in terminals that already contain prior output
  sometimes never show the overlay at all. Reproduce both paths (resize-triggered
  disappearance and dirty-scrollback startup), capture `voiceterm --logs` traces
  with terminal host/version, `rows/cols` before and after resize, and scrollback
  line count at launch. Initial hypotheses: stale geometry cache not refreshed on
  SIGWINCH, or initial row-budget calculation not accounting for existing
  scrollback offset. Add deterministic regression coverage for both triggers
  before closure. `Post-next-release only`; do not execute before release
  promotion unless explicitly reclassified as a blocker.
- [ ] MP-358 Harden the local-first continuous Codex-reviewer / Claude-coder
  loop before any reusable template extraction: keep `MASTER_PLAN` plus the
  relevant active-plan checklist as the canonical queue, require automatic
  next-task promotion while scoped work remains, add peer-liveness/stale-peer
  guardrails so neither side keeps working blindly after the other goes stale,
  require Claude-side wait/repoll behavior to consume direct reviewer packets
  through `review-channel inbox/watch` on the same cadence as bridge polling
  when the structured queue exists,
  modularize and clean up the Python launcher/orchestration path with explicit
  failure-report coverage, rotate both conductor terminals through repo-visible
  handoff state once remaining context drops below 50%, and keep host-process
  hygiene green during relaunch/rotation so stale local test or conductor
  sessions do not accumulate detached repo processes. Only after this loop is
  proven stable on VoiceTerm should the same path be carved into a reusable
  toolkit/template. 2026-03-09 Codex re-review confirmed the report-level
  liveness state machine and fail-closed zero-second ACK rejection. The latest
  launcher slice now also supervises clean provider exits so conductors relaunch
  in-place instead of silently dying after one summary. A follow-up MP-358
  tranche also taught host hygiene/process-audit to keep attached supervised
  review-channel conductors visible without classifying them as stale leaks, and
  landed a typed `review-channel --action promote` path plus derived-next-task
  status projections so queue advancement is no longer ad hoc bridge editing.
  The latest launcher hardening slice also adds a typed
  `--refresh-bridge-heartbeat-if-stale` self-heal path for launch/rollover so
  stale reviewer-heartbeat metadata no longer strands the operator at a dead
  `Last Codex poll` guard failure when the rest of the bridge contract is
  still valid.
  The remaining open gaps are end-to-end auto-promotion proof, the 2-3 minute
  poll / five-minute heartbeat contract, and generalized stale-peer recovery. A
  2026-03-13 follow-up also tightens the proof path: live launch now requires a
  real post-launch reviewer heartbeat instead of counting opened windows as
  success, and the same bridge-backed `review_state` path now emits typed
  stale-peer/reviewer `attention` state that downstream restart/UI surfaces can
  consume without re-deriving the condition ad hoc. The same follow-up now also
  drives Codex/operator lane health plus session stats in the default desktop
  workbench, so the local proof surface goes visibly stale instead of hiding
  the failure only in warnings. 2026-03-15 tandem-consistency guard landed:
  `check_tandem_consistency.py` validates role-profile seam alignment across
  peer-liveness, event-reducer, status-projection, launch, prompt, and handoff
  modules; wired into bundle.tooling, CI workflows, and quality-policy presets.
  2026-04-05 follow-up: reviewer-follow stale-runtime recovery now obeys the
  typed recovery command instead of hardcoding peer-stale `rollover`; typed
  `launch` can auto-run only when the typed decision marks relaunch
  auto-fixable, and approval-gated relaunch stays fail-closed on the queued
  reviewer-turn packet path. 2026-04-08 follow-up: bridge-backed
  `current_session` now detects the operator-observed stale reviewer edit
  shape where `Current Instruction For Claude` changed under a reused
  instruction revision; status/bridge-poll re-derive the effective revision,
  downgrade Claude ACK freshness instead of silently leaving it `current`, and
  reviewer-write preconditions accept that effective typed revision during
  repair so repo-owned checkpoint/promotion flows remain recoverable.
  A second 2026-03-15 anti-stall hardening pass now blocks the next real loop
  failure shape too: `implementer_completion_stall` fails when Claude-owned
  status/ack text parks on "instruction unchanged / continuing to poll /
  Codex should review" while the current instruction is still active and not in
  an explicit reviewer-owned wait state. A 2026-03-25 follow-up then narrowed
  the first live stale-implementer recovery path: `review-channel --action
  recover --recover-provider claude` now replaces only the stale Claude
  conductor, and reviewer-follow escalates repeated unchanged stale-
  implementer state through that repo-owned path instead of a full rollover.
  status/ack text parks on "instruction unchanged / continuing to poll /
  Codex should review" while the current instruction is still active and not in
  an explicit reviewer-owned wait state, and the bridge writer/guard now scrub
  + reject contradictory reviewer-mode prose in `Poll Status`. Latest
  2026-03-25 follow-up: repo-owned reviewer heartbeat/checkpoint writes now
  replace stale reviewer-owned `Poll Status` prose instead of stacking a fresh
  note on older revision/ACK bullets, so the markdown bridge stays current-
  state-only when the typed session state advances.
  Latest 2026-04-02 follow-up: the repo-local remote-control wrapper now syncs
  its project slash command from the tracked prompt source, fails early on
  `claude auth status`, surfaces typed review-channel health before opening the
  phone session, and the paired prompt only uses sanctioned `launch`,
  `ensure`, and `recover --recover-provider claude` recovery paths instead of
  an invented Codex-only recover command. The same 2026-04-02 review pass also
  closed the false-fresh reviewer daemon gap: `ensure --follow` and
  `reviewer-heartbeat --follow` now suppress automation-only reviewer heartbeat
  writes and queue a Claude-targeted restore-turn packet through the existing
  review-channel event path instead of pretending detached automation is live
  reviewer work. A 2026-05-11 hardening pass made that suppression unconditional
  for `reviewer-follow` / `ensure-follow` reasons so watcher/progress loops can
  stay live without dirtying the tracked `bridge.md` compatibility projection.
  A follow-on 2026-04-02 recovery
  slice now lets that same reviewer-follow loop auto-trigger the repo-owned
  `review-channel --action rollover` path for repeated unchanged stale
  reviewer/runtime states, reusing the structured handoff bundle plus visible
  rollover ACK contract instead of manual remote-control restart glue. The
  bounded phone/client integration follow-up for that wrapper, operator-lane
  projection, and rollover reuse is tracked under
  `dev/active/continuous_swarm.md` (MP-358).
  The next closure slice is now explicit too: keep one backend for developers
  and agents, add a repo-owned inactive-mode liveness emitter, expose only
  thin mode toggles/aliases (`agents` / `developer`) over that same contract
  instead of a separate dev-only control plane, and treat this loop as one
  local proof harness over the broader shared backend instead of the product
  boundary itself so future loop work removes or narrows VoiceTerm-embedded
  assumptions rather than deepening them. Latest swarm-topology follow-up
  (2026-03-17): Codex remains the sole conductor and final reviewer, Claude
  may fan out bounded coding workers only behind one Claude conductor without
  self-promoting scope or rewriting reviewer-owned bridge state, and every
  non-trivial slice must keep a separate Codex-side architecture-fit reviewer
  before acceptance so worker fan-out does not turn into a second control
  plane. Latest 2026-04-12 follow-up: the owner docs still require one shared
  backend where any supported provider can fill reviewer, implementer, or
  dashboard/operator roles, and the runtime now matches that boundary more
  honestly: status/read-model surfaces prefer provider-neutral
  reviewer/implementer aliases while bridge-shaped `codex_*` / `claude_*`
  fields stay compatibility-only, and governed commit/push approval now binds
  to the exact worker worktree identity so the phone-attached control lane
  cannot publish from the wrong checkout. The next proof remains explicit:
  keep the phone-attached primary worktree as the control/dashboard lane, move
  implementation into reusable isolated worker worktrees, and prove the first
  beta matrix as `Codex reviewer + Codex worker implementer + Claude
  dashboard` before widening to swapped reviewer/implementer assignments.
  Execution spec:
  `dev/active/continuous_swarm.md`.
- [ ] MP-359 Deliver a bounded optional PyQt6 VoiceTerm Operator Console for
  the current review-channel workflow: keep Rust as the PTY/runtime owner,
  keep `devctl review-channel` as the launcher/control surface, render Codex +
  Claude + Operator Bridge State side by side from repo-visible artifacts, and
  provide desktop launch/rollover plus operator decision capture without
  introducing a second control plane. Phase 1.5 (information hierarchy)
  landed: structured `KeyValuePanel` + `StatusIndicator` + toolbar dots
  replace text dumps, `widgets.py` extracted, 67 tests passing. Phases 3-8
  roadmap added: Approval Queue Center Stage, Agent Timeline, Guardrails /
  Kill Switch, System Health, Diff Viewer, and Validation. Phase 2.6 now has
  a concrete directory layout plan (`state/`, `views/`, `theme/`) to organize
  modules before more panels land. The Activity tab now exposes card-based
  agent summaries, typed quick actions (`review-channel --dry-run`,
  `status --ci`, `triage --ci`, `process-audit --strict`), selectable
  human-readable report topics, and staged Codex/Claude summary drafts with
  explicit provenance while keeping command execution on the shared repo-owned
  path. The next AI-assist tranche now explicitly includes an opt-in live
  provider-backed `AI Summary` path for the selected report, with bounded
  Codex/Claude execution, explicit provenance, repo-visible diagnostics, and a
  staged-draft fallback when live provider access is unavailable. The next
  operator-control tranche now
  explicitly includes a one-click `Start Swarm` flow plus direct typed yes/no
  and terminal-control buttons once the `review-channel` action surface grows
  beyond `launch|rollover`, plus a first-class CI/CD status + workflow/log
  visibility panel built on the existing `devctl` surfaces, push-linked run
  history, and an allowlisted script/action palette with AI-assisted action
  selection that still resolves to typed repo-owned commands. The same tranche
  has now landed its first operator-visible pieces: `Start Swarm` exposes
  JSON preflight -> live launch chaining with staged
  preflight/launch/running/failure status on Home + Activity, shared busy-state
  wiring, and command previews, and a new `Workbench` layout adds snap presets
  over resizable lane/report/monitor panes. The latest MP-359 follow-up also
  routes `Dry Run`, `Live`, `Start Swarm`, and `Rollover` through the typed
  review-channel stale-heartbeat self-heal path so the desktop shell no longer
  looks inert when the markdown bridge ages out, and now persists the selected
  layout/workbench tab/splitter state to
  `dev/reports/review_channel/operator_console/layout_state.json` so "screen
  got weird" reports stay reproducible. A follow-up in the same lane now adds
  explicit layout reset/export/import controls plus a new Workbench timeline
  surface that synthesizes per-agent/system events from snapshot + rollover
  handoff artifacts while keeping Raw Bridge as a dedicated tab. A further
  same-day Phase-4.5 slice adds shared workflow chrome to Workbench with a top
  strip (slice/goal/current writer/branch/swarm health), Codex/Claude last
  seen/applied markers, and a bottom posted->read->acked->implementing->tests
  ->reviewed->apply transition row with a script-derived next-action footer.
  The same tranche
  now explicitly includes a GUI swarm-planner surface that reuses
  `autonomy-swarm` / `swarm_run` token-aware sizing logic and feedback signals
  instead of inventing a desktop-only heuristic, plus a visible swarm
  efficiency governor that logs the metrics and control decision behind every
  hold/downshift/upshift/freeze/repurpose action. The same MP now also tracks
  a layout-workbench path for snap-aware pane resizing/repositioning plus a
  multi-theme registry meant to converge on Rust overlay theme/style-pack
  semantics instead of becoming a desktop-only styling fork, with explicit
  style-pack import/read parity first and export/write parity only after the
  desktop mapping is proven round-trip-safe. A 2026-03-13 follow-up also closed
  a read-model honesty gap: the PyQt6 snapshot builder now carries forward
  structured review-state warnings/errors/attention instead of only file-load
  failures, so the desktop shell can show the real repo-owned "Codex stale /
  poll due / waiting on peer" state that the review-channel runtime already
  computed. A same-slice follow-up now also maps non-healthy review attention
  into Codex/operator lane health and session stats, which makes the default
  session-first workbench visibly stale instead of burying the problem in the
  warning list alone. The plan now also explicitly
  includes a repo-aware Command Center, built-in `What this does / When to use
  it / Before you run it / What it will execute / Success / Failure` guidance
  surfaces, repo-state workflow modes (`Develop`, `Review`, `Swarm`,
  `CI Triage`, `Release`, `Process Cleanup`, `Docs/Governance`), and an
  integrated `Ask | Stage | Run` AI-help contract so the desktop app can
  answer questions, stage commands or draft artifacts, and execute the same
  typed repo-owned actions through both manual and AI-assisted paths. 2026-03-09 follow-up hardening
  landed: the live app and theme editor now share one stylesheet compositor,
  `bundle.tooling` now runs the operator-console suite in the canonical local
  proof path, and the GUI launcher now uses `sys.executable` instead of a bare
  `python3` shell assumption. The same tranche now also includes a fuller
  left-anchored theme workbench with `Colors` / `Typography` / `Metrics`
  pages, a real preview gallery, and tokenized typography/radius/padding
  styling so the editor can theme more than just raw color swatches.
  The latest workflow-controller hardening follow-up now makes `Run Loop`
  audit `devctl orchestrate-status` before it launches
  `devctl swarm_run --continuous`, and the shared Home/Activity launchpads
  keep the last audit/loop result inline so operators do not have to dig
  through raw launcher text to see whether the selected markdown scope is
  blocked, launching, or complete.
  2026-03-09 theme-authority follow-up landed: `ThemeState` now carries
  optional builtin `theme_id` identity, `ThemeEngine` is the single
  builtin/custom/draft apply authority, the toolbar reflects draft/custom
  state explicitly instead of keeping a parallel builtin-only truth, and
  detail dialogs now use live engine colors. The same bounded fix also
  repaired an accidental Operator Console import break in `views/widgets.py`
  and the local proof path is green aside from the known bridge-guard
  expected-red on untracked `bridge.md` / `dev/active/review_channel.md`.
  A later 2026-03-09 saved-theme compatibility fix hydrated legacy partial
  `_last_theme.json` and custom preset payloads onto the current semantic
  palette before apply, closing the PyQt6 startup crash on missing keys such
  as `toolbar_bg`.
  The first follow-up after that crash also moved the agent-detail diff pane
  off fixed RGB highlight tints and back onto the live theme palette, closing
  one of the remaining hardcoded desktop surfaces called out by MP-359.
  A further same-day continuation split the editor into surface-scoped
  `Surfaces` / `Navigation` / `Workflows` pages and expanded the in-editor
  preview to cover toolbar/header chrome, nav + monitor tabs, approval queue,
  diagnostics/log pane, diff pane, and representative empty/error states so
  the next theme passes can touch more of the real shell without guessing.
  The next bounded parity slice is now landed too: the desktop theme engine
  can read canonical style-pack JSON payloads plus theme-file TOML metadata,
  hydrate only the shared Rust `base_theme` onto the matching builtin desktop
  palette, and surface provenance plus explicit `Not yet mapped` reporting for
  Rust-only fields such as `overrides`, `surfaces`, `components`, and
  non-`meta` theme-file sections. Export/write parity remains intentionally
  open until that broader cross-surface contract is proven stable.
  A follow-up bounded write slice is now in too: the desktop editor can export
  canonical theme-file TOML and minimal style-pack JSON only when the current
  state still maps exactly to a shared builtin `base_theme`, while lossy
  desktop-only edits stay blocked with explicit messaging instead of fake
  canonical files. The same slice split theme state/storage/overlay parity
  helpers out of `theme_engine.py` so the coordinator no longer keeps growing
  into another mixed-responsibility desktop god-file.
  A further bounded cleanup then removed another obvious pocket of desktop-only
  literals: agent-detail diff fallback colors now resolve from the shared
  builtin semantic palette, and the theme-editor color swatch derives its own
  border/hover chrome from the active swatch instead of fixed hardcoded
  accent/border values. The broader remaining work is still the larger
  hardcoded-surface sweep across the rest of the desktop shell.
  The next same-day sweep narrowed that remaining shell work further by
  removing shared stylesheet RGBA literals from menu hover/border and
  scrollbar track chrome. Those values now derive from semantic theme colors
  (`hover_overlay`, `menu_border_subtle`, `scrollbar_track_bg`) materialized
  by the shared palette builder and exposed in the desktop editor, so later
  cleanup can target only component-specific hardcoded pockets instead of
  generic shell overlays. A final same-day cleanup then removed the last real
  user-facing literal fallback still left in the live theme/view path:
  `agent_detail.py` now falls back to the builtin semantic `text` color when a
  supplied theme value is invalid instead of dropping to raw white, leaving
  only seed data, example payload text, and generic contrast helpers as
  remaining literal hits in the desktop theme tree. One more bounded helper
  follow-up then removed those generic helper escapes from the live editor
  path too: theme-editor swatch buttons now derive contrast text and
  border/hover chrome from the active theme's `text`/`bg_top` colors instead
  of raw black/white constants, so the remaining literal hits are limited to
  palette seed data and example payload text rather than live component
  chrome.
  2026-03-09 screenshot-hardening follow-up landed: wrapped bridge panes now
  avoid the misleading lower-left scrollbar-handle affordance on the common
  read path, non-diff markdown is no longer painted as removal text in agent
  detail dialogs, provider badges and broader tooltips are visible in the
  chrome, in-window `Help` / `Developer` menus now explain the workflow
  without kicking operators out to repo docs, and the theme editor import page
  now explains current import/highlight semantics inline. 2026-03-09 home/read
  follow-up landed too: the app now opens on a guided `Home` launchpad instead
  of dropping directly into raw dashboards, and a shared `Read` mode switch
  now flips report/footer wording between simple and technical modes while
  feeding the same selected source report into staged AI drafts. A later
  2026-03-09 density/mobile-parity follow-up replaced stale Home/Analytics
  filler with repo-owned git/mutation/CI summaries plus read-only
  `phone-status` parity over the same payload planned for iPhone-safe
  surfaces, tightened sidebar/button density, and documented
  `integrations/code-link-ide` as a future reference adapter rather than a
  runtime dependency of the desktop shell. Next slice: expand
  the editor into fuller page-scoped controls for text/borders/buttons/nav/
  approvals/log panes, and push the remaining hardcoded desktop surfaces onto
  the shared token/preview path so the console can theme nearly the full UI
  without widening into a second control plane. Codex re-review later the same
  day narrowed the current closure: the theme-authority split is resolved, but
  live-launch portability/docs honesty, analytics/CI honesty, real
  startup/mutating-path proof, launcher-script execution coverage, and
  checklist/progress consistency remain open before MP-359 can be called
  green. A further bounded Step-6 follow-up is now closed too: the approval
  queue no longer vanishes when empty and instead keeps a visible `0 Pending`
  zero-state so operators retain the center approval affordance even before
  the larger `ApprovalSpine` card migration lands. Another same-day bounded
  technical-density follow-up then made `Read -> Technical` visually real
  instead of prose-only: the PyQt6 Home and Activity surfaces now switch to
  denser terminal-style digest framing with smaller toolbar-first guidance and
  monospace digest/read panes, addressing operator feedback that the shell was
  still too banner-heavy for a command-center workflow. A further same-day
  session-surface follow-up then fixed the next real live-tail gap: the
  desktop no longer crams terminal text, session metadata, and registry rows
  into one pane. `session_trace_reader.py` now keeps separate readable history
  plus current-screen snapshots while filtering private-CSI parse junk and
  `thinking with high effort` spinner noise, and the Workbench/Monitor/Sidebar
  session surfaces now render a large terminal-history pane with smaller
  stats/screen + registry support below so the lower deck carries useful live
  signal instead of blank space. A later same-day operator-feedback follow-up
  tightened that contract again: live session panes now prefer the
  reconstructed visible terminal screen over the noisier raw history stream
  whenever a `script(1)` trace is available, truncated tail reads align to the
  next line boundary so partial ANSI/control fragments do not leak into the
  UI, and the lower `Stats` / `Registry` pair is now one double-click
  flippable card per provider instead of two cramped panes. The next bounded
  follow-up then moved the default shell back onto a card-first snap-aware
  Workbench: visible preset pills returned, the three lane cards stay on
  screen together, launcher/bridge/diagnostics now render side by side
  instead of behind workbench tabs, and always-visible helper copy was
  compacted so terminal surfaces dominate. The next operator-feedback slice
  then restored explicit `Codex Session` and `Claude Session` panes backed by
  the review-channel full projection's agent registry plus bridge state, and
  the default Workbench now uses a top-row `Codex Session | Operator Spine |
  Claude Session` split with raw logs/digests below so the shell shows what
  each side is doing again without pretending those panes are live PTY
  emulators. The next same-day cleanup then grouped that lower deck by job
  instead of leaving every card visible at once: Workbench now uses
  `Terminal`, `Stats`, `Approvals`, and `Reports` tabs so launcher streams,
  repo stats, decision routing, and digest/draft work each live on one
  focused surface. The next operator-feedback follow-up then pushed that idea
  through the whole Workbench instead of keeping a fixed session strip above
  it: `Sessions`, `Terminal`, `Stats`, `Approvals`, and `Reports` are now
  full-page task tabs, so the streaming session row is its own focused page
  and the workbench tabs sit at the top of the surface instead of in the
  middle of the layout. The next same-day live-session follow-up then made
  those `Codex Session` / `Claude Session` panes prefer real tailed launch
  transcripts from `dev/reports/review_channel/latest/sessions/` whenever the
  review-channel launcher has emitted them, while keeping the prior
  full-projection bridge/registry digest as the honest fallback when no live
  log exists yet. A same-day Theme Editor follow-up then repurposed the right
  rail from an always-on preview gallery into `Quick Tune`, `Coverage`, and
  optional `Preview` tabs, and restyled the operator toolbar action buttons
  toward flatter dashboard/instrument-panel chrome. A later same-day theme
  tranche then promoted the editor from colors/tokens into a fuller theme
  contract with persisted `components` + `motion` settings, component-style
  families for borders/buttons/toolbar chrome/inputs/tabs/surfaces, new
  `Components` and `Motion` authoring pages, and a real preview playground for
  front/back card swaps plus pulse feedback so motion controls are no longer
  just roadmap copy. The next explicit planning follow-up now captures the
  remaining density/scale-up work too: chart-backed repo analytics and
  mutation/hotspot views, 4/6/8+ snap-aware multi-agent layouts, read-only
  split/combined lane terminal monitors, broader tooltip/help saturation, and
  richer QSS/theme-pack import plus semantic-highlight controls that keep
  normal report content from reading like an error state. Current stopping
  point: Cursor lane wiring now reaches the Activity summary cards and quality
  reports can emit live review-channel `finding` packets; follow-on cleanup of
  the architecture/memory/guardrail primer content is parked as an explicit
  backlog item in `dev/active/operator_console.md` Phase 4.7.
  (directory reorg) then Phase 3 (approval queue center stage), with `Start
  Swarm`, typed control wiring, and CI visibility tracked in parallel.
  Execution spec:
  `dev/active/operator_console.md`.

- [x] MP-360 Wire AI-driven remediation into Ralph loop: create
  `ralph_ai_fix.py` with Claude Code invocation, false-positive filtering,
  architecture-specific validation (Rust/PyQt6/devctl/iOS), approval-mode
  support, bounded commit/checkpoint automation, and governed push routing.
  Update policy allowlist and workflow default fix command. Add
  cross-architecture guard enforcement policy to `AGENTS.md` and wire 7 new
  guard scripts into `tooling_control_plane.yml`.
- [ ] MP-361 Create guardrail configuration registry
  (`dev/config/ralph_guardrails.json`) mapping finding categories to AGENTS.md
  standards, documentation links, AI fix skills, and portable Ralph
  architecture-validation command mappings so the AI brain has context for
  each finding class and `ralph_ai_fix.py` does not hardcode VoiceTerm build
  targets / test roots on external repos.
- [ ] MP-362 Emit structured guardrail report (`ralph-report.json`) from AI fix
  wrapper with per-finding status, standards refs, fix skills used, and
  aggregate analytics (fix rate, by-architecture, by-severity, false-positive
  rate).
- [ ] MP-363 Add `devctl ralph-status` CLI command with SVG charts (fix rate
  over time, findings by architecture, false-positive rate), data-science
  integration, and phone status projection.
- [ ] MP-364 Add operator console Ralph dashboard (PyQt6 widget with finding
  table, progress bars, guard health indicators, and control buttons for
  start/pause/resume/configure).
- [ ] MP-365 Integrate Ralph loop metrics into phone/iOS status views (compact
  phase/fix_rate/unresolved fields, start/pause/configure actions, and iOS
  MobileRelayViewModel display).
- [ ] MP-366 Deliver unified guardrail control surface
  (`ralph_control_state.json`) so devctl CLI, operator console, and phone app
  all read/write the same start/pause/configure/monitor state with policy
  gates and audit logging.
- [ ] MP-367 Add `check_ralph_guardrail_parity.py` guard to verify every entry
  in `AI_GUARD_CHECKS` has a step in `tooling_control_plane.yml`, a row in
  `ralph_guardrails.json`, and a skill mapping — closing the loop so new
  guards are automatically wired into the full pipeline.
  Execution spec: `dev/active/ralph_guardrail_control_plane.md`.
- [x] MP-368 Implement `probe_concurrency` so heuristic review probes can flag
  async/shared-state race signals without blocking CI.
- [x] MP-369 Implement `probe_design_smells` so Python AI-slop patterns such as
  heavy `getattr()` density and formatter sprawl become typed review targets.
- [x] MP-370 Implement `probe_boolean_params` so unreadable multi-bool
  signatures in Python and Rust are surfaced before they calcify into APIs.
- [x] MP-371 Implement `probe_stringly_typed` so string-dispatch paths that
  should become enums/contracts are surfaced as explicit review hints.
- [x] MP-372 Land the shared review-probe framework (`probe_bootstrap.py`,
  shared schema/utilities, probe registration, and check-profile integration).
- [x] MP-373 Wire the first end-to-end review-probe path with tests and
  non-blocking `devctl check` integration.
- [x] MP-374 Deliver the expanded review-probe catalog plus aggregated
  `devctl probe-report` / `status --probe-report` / `report --probe-report`
  surfaces and stable `review_targets.json` output. Remaining follow-up is
  operator-facing ranking/baselines and deeper probe-specific regression
  coverage, not initial plumbing.
- [ ] MP-375 Shift review-probe next work to operator-first adoption:
  ranking/baselines, self-contained senior-review packets, connectivity-aware
  hotspot scoring, changed-subgraph / hotspot visuals, governance parity, and
  optional operator-console review dashboards. 2026-03-10 follow-up:
  `devctl triage --probe-report` now promotes aggregated probe debt into
  routed issues/next actions, and local `loop-packet` fallback requests the
  same probe summary so packets stay probe-aware even without a prior
  artifact. Later 2026-03-10 follow-up: `devctl probe-report` now emits ranked
  hotspot scoring, `file_topology.json`, `review_packet.{json,md}`, and
  Mermaid/DOT hotspot views, while `status` / `report` / `triage` consume the
  same ranked hotspot summary. A first cleanup pass using that packet reduced
  live findings from 23 across 18 files to 18 across 14 files. Control-plane
  or Ralph adapters stay later and should build on the same stable probe
  artifacts. Latest follow-up: maintainer governance docs now explicitly tell
  AI when to run `check --profile ci`, `probe-report`, and `guard-run`, and
  document the topology/review-packet artifacts emitted by the probe stack.
  Latest portability follow-up: built-in guard/probe capability metadata now
  lives in `devctl/quality_policy_defaults.py`, repo-local
  enablement/default args now live in `dev/config/devctl_repo_policy.json`,
  and `check` / `probe-report` resolve active steps from the
  `quality_policy*.py` policy stack so the current behavior is preserved here
  while the engine moves toward repo-portable presets. Latest preset
  follow-up: VoiceTerm now extends reusable portable presets under
  `dev/config/quality_presets/`, VoiceTerm-only matrix/isolation guards live
  behind the repo-specific preset instead of the portable fallback, and
  `check` / `probe-report` plus probe-backed `status` / `report` / `triage`
  all accept `--quality-policy`; `DEVCTL_QUALITY_POLICY` provides the same
  automation override, and `devctl quality-policy` now renders the resolved
  policy/scopes so maintainers can validate another repo policy without
  editing orchestration code. Latest scope follow-up: scan roots are no longer baked
  into the standalone Python/Rust guard+probe scripts; the repo policy now
  owns `python_guard_roots`, `python_probe_roots`, `rust_guard_roots`, and
  `rust_probe_roots`, and probe-report artifacts surface those resolved roots
  for operator review. Latest onboarding follow-up: `governance-bootstrap`
  now writes a starter `dev/config/devctl_repo_policy.json` for the target
  repo when missing, chooses the nearest portable preset from detected
  Python/Rust capabilities, and ships exported template files
  (`portable_governance_repo_setup.template.md`,
  `portable_devctl_repo_policy.template.json`) so another repo gets a real
  first-run setup path instead of hand-assembling policy from scattered docs.
  Latest usability follow-up: the same bootstrap command now writes a
  repo-local `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` file into the target
  repo so an AI or maintainer has one obvious first-read setup surface after
  export/bootstrap, and `dev/scripts/checks` moved another set of internal
  helper families behind documented subpackages (`active_plan/`,
  `python_analysis/`, `probe_report/`) to keep the root directory flatter.
  Latest portable-guard slices now ship
  `check_python_suppression_debt.py`, `check_python_design_complexity.py`, and
  `check_python_cyclic_imports.py` as default portable Python guards, while
  default-argument traps route through the expanded
  `check_python_global_mutable.py` guard. Latest portability follow-up:
  `check_code_shape.py` namespace/layout rules now resolve from repo-policy
  guard config instead of VoiceTerm-only hard-coded tuples. Next portable
  hard-guard backlog now narrows to Rust `result_large_err` /
  `large_enum_variant` evaluation. Latest next-signal intake: MP-375 now
  explicitly tracks an evidence-driven candidate tranche instead of treating
  probe work as closed. Immediate advisory candidates are tuple-return
  complexity, mutation density, method-chain length, fan-out, and
  side-effect/match-arm complexity. `check_enum_conversion_duplication` stays
  a hard-guard candidate pending portability proof, while cognitive-
  complexity/readability micro-metrics and Python return-type consistency stay
  research-only until they beat existing structural-complexity coverage and
  prior signal-quality findings. Latest architecture-intake follow-up
  (2026-03-24): keep the useful external-review ideas inside the existing
  plan chain instead of a new intake doc. `MP-375` now explicitly owns the
  next actuator closures on top of the already-live feedback loop: a derived
  failure-rule ledger over adjudicated recurring findings, and carried output
  constraints over probe-guidance / `DecisionPacket` families so recurring
  structural smells can shape the next fix instead of only annotating it.
  - [ ] Derive bounded prompt-time failure rules from adjudicated recurring
    findings and inject them into Ralph/autonomy/review prompt builders.
  - [ ] Promote recent successful/waived fix history into prompt-time bad-
    pattern recall so repair prompts can say what already worked, failed, or
    was waived for the same recurring family/file shape.
  - [ ] Extend carried probe guidance / `DecisionPacket` semantics with
    output constraints and record follow/waive/supersede evidence.
  - [ ] Make prompt-time guidance assembly deterministic across failure rules,
    bad-pattern recall, output constraints, and attached guidance refs so
    identical evidence yields identical remediation packets.
  - [ ] Extend carried probe guidance / `DecisionPacket` semantics with a
    typed allowed-transform menu per recurring family so the permitted repair
    operators are explicit and auditable instead of prompt-only lore.
  - [ ] Add signal-interaction / trust weighting on top of probe +
    governance-review evidence so co-occurring signals and chronic
    waiver/false-positive families influence automation trust before
    remediation reaches auto-apply-capable paths.
  - [ ] Add one shared cross-file reference prepass for context-blind probes
    before widening automation trust: `probe_single_use_helpers` and
    similar file-local scanners should be able to query repo-level
    reuse/import evidence so helpers reused outside the current file do not
    false-positive as single-use. First closure tranche: the shared Python
    call-site prepass now lives in `probe_bootstrap` and backs
    `probe_single_use_helpers` with relocation regression coverage; keep this
    item open until the remaining context-blind probes adopt the same corpus.
  - [ ] Close the remaining probe lifecycle joints on top of the already-live
    verdict/history path: hotspot ranking, startup signals, Ralph guidance
    selection, and next-file rotation must become verdict-aware so fixed or
    waived findings cool off instead of refiring indefinitely, and quality-
    feedback trust tuning must feed that same suppression logic.
  - [ ] Make startup probe-health consumption honest on clean trees: default
    `working-tree` probe scans may legitimately return `files_scanned=0`, so
    startup/context/hotspot consumers must distinguish "dirty-scope empty"
    from "repo or branch healthy", reuse durable `latest` summaries or
    explicit `--since-ref` / `--adoption-scan` outputs when they need broader
    health, and surface scope/freshness metadata instead of treating a
    zero-file scan as zero-risk proof.
  Execution spec: `dev/active/review_probes.md`.

- [ ] MP-376 Build the portable code-governance engine + evidence corpus:
  keep the guard/probe/report stack reusable across arbitrary repos without
  engine edits, define the boundary between engine code, portable presets, and
  repo-local policy, capture guarded coding episodes as evaluation data
  (initial output, guard hits, repair loops, accepted diff, human edits, test
  and later-review outcomes), keep the adjudicated finding ledger
  (`governance-review`) current so false-positive and cleanup rates are visible
  in `data-science`, keep first-run onboarding (`governance-bootstrap` +
  `--adoption-scan`) and export flows reusable across arbitrary repos, and
  keep mining repeated low-noise pattern families from live evidence before
  promoting more hard guards. The first external pilot (`ci-cd-hub`) is now
  complete; remaining scope is benchmark automation, active cleanup against the
  evidence log, more pilot-proof engine cleanup, and evidence-driven next
  pattern selection while holding guard code to the same or stricter
  structural standard as guarded code. Execution spec:
  `dev/active/portable_code_governance.md`. Latest CI-parity follow-up
  (2026-03-11): GitHub exposed that `dev/config/devctl_repo_policy.json` and
  the portable preset JSON files were still ignored local artifacts, so local
  validation and CI were resolving different guard/probe sets. The policy/preset
  files are now tracked repo assets, maintainer docs explicitly call out that
  policy changes must be committed, pre-commit CI is narrowed to changed files,
  the tooling-control-plane mypy env export bug is fixed, iOS CI now runs on
  `macos-15` for Swift 6 / newer Xcode project compatibility, and the current
  maintainer-lint redundant-closure regressions are burned down. Latest
  adoption-flow follow-up (2026-03-17): starter policy plus a setup guide is
  no longer enough for the portable path. The next onboarding contract is a
  reviewed repo-local governance doc (`project.governance.md` working name)
  that `governance-draft` can infer from repo facts, humans can finish with
  priorities/debt/exceptions, and `governance-bootstrap` or later
  `governance-init` can consume so adopter repos stop hand-authoring policy
  from scratch. Latest audit-intake follow-up (2026-03-22): portable scope now
  explicitly includes governance-completeness evidence for the engine itself
  (direct guard/probe/subsystem coverage surfaced as meta-findings), a
  portable repo-organization/report surface beyond today's partial
  `package_layout` + docs-governance coverage, tandem/review-infrastructure
  opt-in clarity for adopters so quick-start flows do not silently assume
  `bridge.md`, and continued burn-down of the crowded `dev/scripts/devctl`
  flat root behind the same policy-backed organization contract. Latest
  landed follow-up (2026-04-01): `check_package_layout` now emits advisory
  root-role debt for configured helper-drawer roots, so self-hosting can
  report "`dev/scripts/devctl` is still semantically noisy" without needing a
  blocking crowding violation first. Latest tracked follow-ups from that
  intake:
  - [x] Freeze corpus-first proof as the immediate `MP-376` execution order:
    checkpoint the current slice, seed a fixed Python anchor corpus, run
    `3-5` repo waves, stop on the first new `engine_bug`, rerun all green
    anchors after each engine fix, and switch to the owner `MP-377` blocker
    if the remaining failures collapse to Step-0/startup or governed push.
  - [x] Seed the first fixed Python anchor corpus for that execution order:
    `3-4` maintainer-source repos, `3-4` external mainstream repos, `1-2`
    external adversarial/weird repos, plus the two existing regression
    anchors already proven in `MP-376`. Seeded 2026-04-02 set:
    maintainer `zgraph-scientific-package`, `vector_space`, `mkgui` with
    `MemLite` reserved as the fourth maintainer anchor; external mainstream
    `requests`, `interactions.py`, `yamllint`; external adversarial/weird
    `pre-commit-hooks`.
  - [x] Run Wave 1 of that corpus-first proof program on `3-5` repos and keep
    widening only after the full green-anchor rerun passes again. Wave 1
    completed on `zgraph-scientific-package`, `mkgui`, `requests`,
    `interactions.py`, and `pre-commit-hooks` with no new `engine_bug`; all
    five runs are currently classified as `adopter_finding`.
  - [ ] Keep the external Python adopter corpus explicit and honest in the
    active plan chain: two real repos are enough to expose engine defects and
    seed regression anchors, but not enough to claim broad portability. Run
    the same governed bootstrap/probe/check path on every new repo and keep
    the matrix current in `dev/active/portable_code_governance.md`. The fixed
    seeded reserves behind Wave 1 are `vector_space`, `yamllint`, and
    `MemLite`. 2026-05-14 fixture-gate evidence for
    `MP377-ADOPTER-PILOT-GATE-S1` now lives in
    `dev/active/portable_code_governance.md`: two non-VoiceTerm fixture
    adopters bootstrapped through starter repo-pack policy and completed
    `probe-report --repo-path --adoption-scan` after one source-repo probe
    wrapper crash was fixed inline.
  - [ ] Classify every external-repo failure as `engine_bug` or
    `adopter_finding`, rerun the newly failing repo plus every previously
    tested repo after each engine fix, and only import/adjudicate adopter
    findings once the engine path is clean on that repo. Wave 1 classifications
    so far are all `adopter_finding`; no new `engine_bug` or
    `already_planned_architecture_gap` surfaced.
  - [ ] Surface self-hosting governance completeness as portable meta-findings
    so low test/guard/subsystem coverage becomes measured engine evidence, not
    audit-only prose. (evidence: `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 34)
  - [ ] Extend the portable organization contract to cover root markdown/file
    budgets, metadata/orphan/wrong-hierarchy gaps, and continued
    `dev/scripts/devctl` flat-root burn-down under the same policy-backed
    report surface. The same tranche now explicitly includes custom
    docs-authority / tracker / registry naming proof so portability does not
    depend on `AGENTS.md` / `MASTER_PLAN.md` / `INDEX.md` clones. The same
    follow-up now explicitly includes a package-role / package-cohesion
    contract so repos can distinguish public entrypoints, temporary shims,
    implementation packages, support modules, generated artifacts, and docs
    authority instead of treating "within file budget" as semantic
    organization. (evidence: `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 29, Part 40)
  - [ ] Keep tandem/review infrastructure opt-in in portable presets and setup
    until an adopter explicitly enables that enforcement, and make the enable
    point obvious in bootstrap/setup surfaces. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 41)
  - [ ] Add an explicit optional clean-slate / rollback-on-failure mode for
    external-adopter remediation loops so portable governance can capture a
    pre-fix baseline, roll back bounded bad outputs, and run clean-slate
    autonomy rounds without replacing the current default escalation model.
  - [ ] Add one deterministic reproducibility integration test for the
    portable engine so the same repo snapshot + policy can be replayed
    through deterministic layers twice and produce identical canonical
    findings/packets/receipts aside from allowed volatile fields.
  - [ ] Treat first-run / second-run convergence as a real onboarding proof
    bar for adopters: running `governance-bootstrap`, `startup-context`, and
    the first routed intake on the same repo snapshot twice should converge
    to the same canonical onboarding packet, `WorkIntakePacket`, and advisory
    routing outputs modulo approved volatile fields before portability claims
    graduate past provisional proof.
  - [ ] Freeze portable onboarding modes plus ratification/provenance on top
    of the reviewed governance contract: support `auto`, `assisted`, and
    `locked_down` flows, emit field-level inference provenance plus
    unresolved-authority prompts, and record approval through a repo-owned
    ratification path instead of leaving first-run setup spread across starter
    policy files and chat.
  - [ ] Promote the current portability fixture matrix into a permanent
    benchmark suite: empty repo, custom-layout repo, mixed-language repo, and
    tandem-disabled repo should remain green on
    `governance-bootstrap`/`startup-context`/routed base checks with no
    core-engine patches between adoptions, and regressions on previously-green
    fixtures should block stronger portability claims.
  - [ ] Keep engine-owned resources separate from adopter authority through
    that same productization path: packaged presets/templates/setup assets may
    ship with the engine, but docs authority, plan/backlog ownership, review
    mode, report roots, and path authority must remain repo-owned and
    overridable in adopter state.
  - [ ] Add one explicit absorption-before-archive pass for the repo's own
    reference markdown: no root evidence companion or `dev/active`
    reference/bridge doc should move until its accepted conclusions are
    mirrored into the canonical owner chain and the doc-authority report marks
    it reference-only with no unmapped execution state.
  - [ ] Keep exported measurement schemas honest about lifecycle:
    `portable_governance_episode` and `portable_governance_eval_record`
    remain reference/export artifacts until importer or validator code
    exists; if they graduate into live portable evidence, land executable
    validation and consumer paths in the same slice instead of counting
    templates as active contracts.
  Latest publication-sync follow-up: refreshed the external
  `terminal-as-interface` paper snapshot from committed VoiceTerm HEAD and
  recorded the new baseline in `dev/config/publication_sync_registry.json`
  (`source_ref=4deb8ec8f8c3709f1fb35955f9763c6147df6a95`,
  `external_ref=9cf965f`), returning `check_publication_sync.py` to zero drift.
  Latest PR-gate follow-up (2026-03-12): the remaining GitHub-only failures on
  PR #16 are burned down locally by making `process_sweep` fixtures checkout-
  agnostic, pinning review-channel stale-poll tests to explicit freshness
  policy, clearing leaked runtime/style-pack overrides from the startup-banner
  fallback test, switching iOS `xcode-build` to the generic simulator
  destination, and taking the changed-file `pre-commit` lane back to green.
  Latest closure pass (2026-03-12): the next rerun exposed real local
  portability debt instead of more GitHub workflow drift, so `devctl` now
  keeps repo-owned Python subprocesses on the invoking interpreter,
  compatibility exports are restored for split modules
  (`quality_policy`, `collect`, `status_report`, `triage/support`,
  `check_phases`, `check_python_global_mutable`), and new support modules for
  phone-status plus Activity-tab report helpers pull the touched Python files
  back under code-shape/function-duplication limits without changing behavior.
  Latest probe-cleanup follow-up (2026-03-12): the remaining working-tree
  review hints are now burned down too. `autonomy/phone_status.py` uses a
  typed `RalphSection` boundary instead of anonymous dict helpers,
  `mobile_status_views.py` now delegates typed payload/view support to the new
  `mobile_status_projection.py` module so the renderer stays below its
  code-shape cap, `loop_packet_helpers.py` uses `LoopPacketSourceCommand` for
  the last auto-send string dispatch, the probe packet rerun is clean, and the
  governance ledger is updated with six additional `fixed` probe rows.
  Latest push-repair follow-up (2026-03-12): the first rerun on the refreshed
  PR caught a real changed-file `pre-commit` regression where Ruff had stripped
  compatibility exports still used across the repo. Those re-export seams are
  now restored compactly in `common.py`, `status_report.py`, `collect.py`,
  `triage/support.py`, `commands/check_phases.py`, `process_sweep/core.py`,
  `phone_status_view_support.py`, `quality_policy.py`,
  `check_python_global_mutable.py`, and `probe_report_render.py`; `common.py`
  stays back under its shape cap; changed-file `pre-commit` is green locally
  again; and the full `dev/scripts/devctl/tests` suite reran at
  `1184 passed, 4 subtests passed`.
  Latest external-pilot rerun (2026-03-14): `probe-report --repo-path` plus
  starter-policy scope generation now resolve the target repo consistently
  enough to trust cross-repo counts; rerunning the 13 pilot repos changed the
  durable aggregate from the previously quoted `158` hints to `311`, because
  `ci-cd-hub` widened from a `scripts/`-only under-scan (`7` hints) to a full
  starter-scope scan of `scripts`, `_quarantine`, `cihub`, and `tests`
  (`159` hints). The harder onboarding lane now works too:
  `check --profile ci --repo-path /tmp/governance-pilots/ci-cd-hub --adoption-scan`
  completed and returned `13` failing guard families, and six representative
  `ci-cd-hub` probe findings were recorded into the governance-review ledger
  as `confirmed_issue` evidence. Remaining external coverage gap:
  non-Python/Rust repos still need JS/TS/Java guard/probe packs. Latest
  integration-analysis follow-up (2026-04-01): portable proof now also
  explicitly includes a typed onboarding contract with inference provenance and
  ratification, the seven-step second-repo proof ladder as a permanent
  benchmark suite, and first-run / second-run convergence as part of the real
  adopter bar instead of a one-time bootstrap demo. Latest
  structural-readability follow-up (2026-03-20): the first repo-policy-backed
  naming advisory probe now exists. `probe_term_consistency.py` is wired into
  the shared script catalog and quality-policy registry, VoiceTerm policy now
  seeds canonical-vs-legacy review-channel vocabulary rules, and the portable
  readability tranche can start collecting reviewed signal quality for public
  wording drift instead of relying only on shape/complexity heuristics.
  Latest external-review adjudication follow-up (2026-03-17): reran the
  portable stack against the pinned `integrations/ci-cd-hub` federated
  checkout so the repo-local federation path has distinct evidence from the
  corrected `/tmp/governance-pilots/ci-cd-hub` benchmark. The local-path rerun
  produced `13/15` red AI guard steps plus a richer current probe packet
  (`1828` findings across `266` files), and the target repo now has `7`
  adjudicated ledger rows (`4 confirmed_issue`, `3 false_positive`) under
  `integrations/ci-cd-hub/dev/reports/governance/`. Keep those receipts
  separate from the March 14 cross-repo aggregate; today's run is the pinned
  submodule/local-path proof and finding-quality follow-up, not a replacement
  baseline.
  Latest docs-governance follow-up (2026-03-12): strict-tooling drift is
  closed too. `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, and
  `dev/scripts/README.md` now document that staged `dev/scripts/**` module
  splits must keep compatibility re-exports until repo importers, tests,
  workflows, and pre-commit hooks migrate together. After refreshing the
  review-channel heartbeat, `docs-check --strict-tooling` and the full
  canonical `bundle.tooling` replay are green again under `python3.11` on the
  local workstation, including `397 passed, 181 skipped` in the Operator
  Console suite and a clean `process-cleanup --verify`.
  Latest CI-runner parity follow-up (2026-03-12): the next GitHub rerun
  exposed two environment-sensitive Python regressions plus one operator-
  console timing bug, and they are now burned down locally. Review-channel
  bridge session generation no longer hard-fails when the default resolver
  cannot find `codex`/`claude` on the current PATH before a dry-run or
  simulated launch script is even written, `triage-loop` now passes the
  command module's CI/connectivity predicates through its preflight helper so
  the existing non-blocking-local connectivity test holds under GitHub
  Actions, and `JobRecord.duration_seconds` clamps negative monotonic deltas
  to zero. The reproduced failure shapes are green locally, the full
  `dev/scripts/devctl/tests` suite reran at `1184 passed, 4 subtests passed`,
  and `app/operator_console/tests/` reran at `397 passed, 181 skipped`.
  Review-channel heartbeat parity follow-up (2026-03-12): the next PR rerun
  showed one more CI-only mismatch. `devctl review-channel` auto-refreshes a
  stale bridge heartbeat before `status` / `launch`, but the helper had been
  keying that decision off `check_review_channel_bridge.py` metadata errors.
  On GitHub runners the bridge guard intentionally skips live heartbeat
  freshness enforcement (`GITHUB_ACTIONS=true`), so the refresh path never
  triggered even though bridge liveness was still stale. The helper now keeps
  using the guard for structural bridge validity but derives refreshability
  from direct bridge snapshot/liveness analysis, and the stale-heartbeat tests
  now pin `GITHUB_ACTIONS=true` explicitly so CI runner parity stays covered.
  Tooling-control-plane workflow parity follow-up (2026-03-12): after that fix
  landed, the only remaining PR blocker in `docs policy + governance guard`
  was not a docs regression at all. The workflow's nested
  `check_rust_compiler_warnings.py` step was compiling changed Rust files
  without provisioning the Rust toolchain or Linux ALSA development headers,
  even though the dedicated Rust lanes install both. `tooling_control_plane.yml`
  now installs Rust plus `libasound2-dev` before the compile-time Rust guard
  runs so the docs/governance lane matches the real Rust CI prerequisites.

- [ ] MP-377 Extract the reusable AI governance platform architecture:
  package the current VoiceTerm-local code-quality/control-plane stack as one
  installable system with shared backend contracts for runtime state, typed
  actions, repo packs, provider/workflow adapters, and artifact storage so the
  same platform can power VoiceTerm, a PyQt6 dashboard, CLI flows, and future
  phone/mobile surfaces across arbitrary repos. This scope owns the product-
  level extraction of Ralph/mutation/review-channel/process-hygiene loops and
  the filesystem/package reorganization needed to mirror those layers cleanly.
  It now explicitly includes self-hosting directory/layout governance for
  `devctl` itself plus baseline/adoption layout scanning so external repos can
  receive the same organization contract agents use here, including crowded
  flat-family namespace reporting for `devctl/commands` and other high-density
  roots. The same lane now also owns the AI-facing projection of that
  structure truth: startup/work-intake should expose declared package roles,
  approved exceptions, and live layout debt instead of teaching agents that a
  green crowding receipt means the repo is well organized. It also owns the
  context-budget architecture for AI-facing runs:
  typed context packs, repo-pack-tunable budget profiles, usage telemetry,
  overflow/fallback behavior, and future operator/adopter guidance so better
  code quality does not depend on hidden prompt bloat. This scope also now
  explicitly includes the real package/install surface (`pyproject.toml`,
  build backend, stable CLI entrypoints), repo-pack-owned path resolution for
  removing hard-coded VoiceTerm filesystem assumptions, repo-pack/platform
  compatibility checks, the central finding/review/metric evidence schema, and
  phase-scoped replay/evaluation plus waiver/promotion lifecycle work required
  before external pilots count as proof. It also now explicitly owns the
  self-hosting enforcement backlog behind "why didn't our tools catch this?":
  layer-boundary enforcement, portable-path construction purity,
  provider/workflow adapter routing, contract-completion/orphaned-contract
  checks, schema/platform compatibility validation, and the first repeatable
  command-source/shell-execution checks for platform-grade misses. Public proof
  is part of the deliverable too, not a marketing afterthought: external pilot
  packs should preserve the platform's differentiators in a durable/public
  whitepaper or comparison surface, not only in internal plan text.
  `MP-376` remains the narrower engine/policy/evaluation track. Execution spec:
  `dev/active/ai_governance_platform.md`. This spec is now the only main
  active architecture plan for the standalone governance product scope and
  carries the consolidated repo-grounded assessment, separation roadmap,
  documentation consolidation plan, phase-by-phase implementation order, the
  explicit platform completion gates, and the standing Python/Rust-first
  pattern-mining plus future-language-extension strategy. When present in the
  current shared worktree, `GUARD_AUDIT_FINDINGS.md` and
  `ZGRAPH_RESEARCH_EVIDENCE.md` may be consulted as local reference-only
  companions for supporting evidence and idea inventory, but they are not
  canonical execution authority and all accepted conclusions must be mirrored
  into tracked plan state here plus the `MP-377` spec chain before
  implementation or review.
  Latest synthesis follow-up (2026-04-01): keep the remaining architecture
  deltas in the existing owner chain rather than another memo. `MP-377` owns
  surface-ownership routing, capability projection, release-artifact
  governance, and proof-gate maturity; `MP-376` owns onboarding
  ratification/provenance and the permanent portability benchmark suite; and
  `MP-355` owns role-owned multi-provider plus terminal-host abstraction over
  the same `CollaborationSession` backend.
  Latest cross-client source-of-truth follow-up (2026-04-03): the next
  bounded `MP-377` slice is one generated `system-picture` / external-review
  orientation reducer over typed startup, review, control, governance-review,
  external-findings, and quality-feedback state. That reducer must emit one
  managed repo-owned JSON/Markdown artifact plus one compact GitHub-visible
  markdown projection that share the same typed snapshot identity, then move
  clients onto that shared read model in a fixed order: PyQt6/operator
  console off `bridge.md`-parsed lane state first, iPhone/mobile off
  compatibility-shaped `mobile-status` payloads second, and Claude remote-
  loop plus external-review surfaces onto typed status plus the generated
  summary third. Those clients stay projection-only; they are not new
  authority owners. The same owner chain also keeps prepared launch authority
  typed after launch: remote-control receipt-commit `HEAD` drift must be
  classified from governance/review-state evidence before any runtime reader
  downgrades continuity to `refresh_recommended`.
  Latest ADR-008 follow-up (2026-04-23): governed push now owns managed
  bridge projection cleanup before publication. After preflight reprojects
  `bridge.md`, `devctl push` creates the same external-review receipt commit
  when the remaining dirty paths are only governed projection artifacts,
  refreshes the pushed HEAD for authorization/reporting, and lets pipeline
  state sync match that receipt HEAD back to the approved content commit.
  Latest guard-enforcement follow-up (2026-05-11): the bridge projection-only
  regression guard is no longer catalog-only. `check_bridge_projection_only.py`
  is enforced through quality-policy defaults, `bundle.tooling`,
  `bundle.release`, `tooling_control_plane.yml`, and `release_preflight.yml`
  so bridge/status/current-session compatibility projections remain
  display-only and cannot regain backend authority through an unenforced
  script entry.
  Latest proof-surface follow-up (2026-04-04): `system-picture` now has a
  live repo-owned command path and the tracked proof ledger is a generated
  writeback from that snapshot, not a second execution tracker.
  Do not treat this
  scope as complete when the repo is merely split or packaged; closure requires
  architecture boundary proof, pipeline parity, telemetry trust, replayable
  evidence quality, and cross-repo adoption evidence together. Current explicit
  follow-up: make typed JSON runtime state the live authority over markdown/UI
  projections, generate agent/developer startup surfaces from the same repo-pack
  policy, add one reviewed repo-local governance contract
  (`project.governance.md` working name) that AI can draft and startup
  surfaces can summarize, prove the same-context/same-check-path flow across
  Codex, Claude,
  `active_dual_agent`, `single_agent`, and `tools_only`, separate collaboration
  mode from objective profiles like `bootstrap` / `audit` / `refactor` /
  `review` / `remediation`, define the standalone platform-repo plus VoiceTerm
  back-import proof path, freeze the typed queue/action contract, promote the
  existing topology backend into a first-class portable `map` surface for
  flowcharts/AI context/hook reuse, with complexity/hotspot/evidence overlays,
  targeted-check hints, and a cacheable JSON-plus-SQLite artifact contract,
  keep every major subsystem standalone-usable in any repo while also fully
  composable into one integrated agent app, and keep local tandem validation
  honest about external CI/network/environment
  failures versus real code-quality
  regressions. Keep the whole system in scope here: governance core, runtime,
  adapters, frontends, repo packs, and VoiceTerm as a consumer plus first-party
  local operator shell. VoiceTerm may be the preferred main app and local host
  path, but the backend must remain callable without VoiceTerm by CLI, PyQt6,
  phone/mobile, skills/hooks, automation loops, and external repos. VoiceTerm
  should also be able to drive the full platform action surface through that
  same backend path: guards, probes, quality/reporting, bootstrap/export,
  review-channel actions, remediation loops, and generated instruction/skills
  surfaces. Latest miss-closure follow-up (2026-03-28): commit-range
  docs-governance predicates must reuse one resolved docs/governance contract
  per repo/policy path instead of rescanning policy/authority inside per-path
  loops; keep the cache plus regression test as part of the MP-377
  self-hosting enforcement surface.
  surfaces. Remaining missing-proof items now explicitly include: local
  service lifecycle/attach semantics, a portable contract-sync guard for that
  lifecycle/authority surface, caller authority + approval matrix, and golden
  cross-client parity fixtures over the same backend snapshots. This scope
  now also explicitly requires one cross-cutting coherence matrix over
  vocabulary, identity, state, action, artifact, lifecycle, projections,
  parity, and portability so drift prevention is a planned platform contract
  instead of a collection of local checks. The latest architecture audit also
  promoted six more cross-cutting gaps into explicit scope: public
  deprecation/compatibility windows, multi-client write arbitration, extension
  and adopter conformance packs, whole-system artifact taxonomy/ledger
  classes, degraded-mode semantics, and the stable backend protocol boundary.
  This scope
  also owns durable operator-guide coverage as a first-class contract:
  maintain system-level guide/playbook surfaces (`DEVCTL_AUTOGUIDE`,
  starter instructions, generated local instructions) through repo-policy
  contracts and guard-backed sync rather than human memory alone. This scope
  now explicitly includes docs-boundary cleanup between VoiceTerm and the AI
  system itself: review/startup/operator-control and self-hosting governance
  guidance must live in the `MP-377` owner chain plus maintainer/generated
  surfaces, not in VoiceTerm end-user docs just because the current repo hosts
  both systems. Treat any pressure to patch `README.md`, `QUICK_START.md`,
  `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `guides/INSTALL.md`, or
  `guides/TROUBLESHOOTING.md` for MP-355/MP-377 control-plane semantics as a
  signal that the organization/docs contract is still wrong and needs repair.
  This same slice must finish the repo-agnostic docs policy so product docs,
  self-hosting/development docs, portable adopter docs, and generated
  operator/bootstrap surfaces stop bleeding into one another.
  Latest 2026-04-12 role-portability follow-up: the architecture already says
  launch/bootstrap/runtime authority is role-first, not provider-first, so the
  next bounded `MP-377` slice must remove the remaining provider-coded seams
  from `runtime/role_profile.py`, turn-authority/read-model helpers, and
  bridge/handoff projections, then prove the resulting same-backend role/mode
  matrix locally before widening to the external repo ladder in `MP-376`.
  This scope
  also keeps the existing `package_layout` engine as the self-hosting
  organization seam rather than inventing a second crowding guard: the next
  platform follow-up is to generalize those layout/family rules beyond the
  current Python-biased/freeze-mode coverage so the same modular organization
  contract can govern Rust/workflow/docs families too.
  This scope
  also treats "why didn't the tools catch this?" as an execution rule:
  when a real issue slips through, the follow-up must decide whether the miss
  belongs in an existing reusable guard/probe/contract or a new low-noise
  modular enforcement path instead of stopping at a one-off patch.
  The same scope also owns operator-visible loop observability as a product
  requirement rather than a chat habit: reviewer/coder heartbeat, findings,
  next action, and stale/healthy state must publish automatically through the
  shared backend so chat, CLI, PyQt6, phone/mobile, and overlay users can see
  progress without reopening markdown bridges or manually prompting the loop.
  Latest self-hosting reporting follow-up (2026-03-17): the canonical
  `devctl probe-report` path now threads `repo_root` through markdown/
  terminal rendering so repo-owned `.probe-allowlist.json`
  `design_decision` entries shape the main operator packet instead of only the
  fallback script path; current local filtered probe backlog is medium-only
  (`0` active high, `14` active medium, `25` design decisions). Latest
  audit-intake follow-up (2026-03-22): the next `P0` closure work is wiring,
  not more architecture. `startup-context` must ingest real `Session Resume`
  state instead of a boolean marker, runtime startup/routing must consume live
  `ProjectGovernance` `startup_order` / `command_routing_defaults` /
  `workflow_profiles`, AI repair paths must read canonical `Finding` /
  `DecisionPacket` guidance fields, guard-run/autonomy/review close-out must
  auto-record `governance-review` outcomes, and top-level command crash
  handling must converge on structured `ActionResult` failures instead of raw
  tracebacks. Latest startup-intake follow-up (2026-03-23): the first runtime
  proof for that startup-family closure is now live. `PlanRegistry` entries
  carry parsed `SessionResumeState`, `startup-context` emits a bounded
  `WorkIntakePacket` with `PlanTargetRef` + continuity reconciliation +
  routing hints, and the same path now consumes live `startup_order`,
  `workflow_profiles`, and `command_routing_defaults`. The open remainder in
  this exact lane is broader adoption/hardening, not more contract sketching:
  `CollaborationSession`, more runtime consumers, and the separate
  validation-freshness / raw-push enforcement gaps. Latest enforcement
  follow-up (2026-03-23): `startup-context` is now the explicit Step 0
  bootstrap gate in `AGENTS.md`, generated bootstrap surfaces, and the
  review-channel conductor prompt; it persists a managed `StartupReceipt`
  under the repo-owned reports root derived from live governance/path-root
  authority; and scoped repo-owned launcher/mutation `devctl` paths now
  require that receipt and re-check live startup authority before starting
  another implementation or launcher slice. The remaining gap is narrower
  but still real: fresh raw interactive provider sessions can still skip
  Step 0 until a supported hook/wrapper entry path exists, and broader
  repo-pack activation still remains open, not the old repo-owned-launcher
  "startup-context exists but nothing requires it" hole or the current
  read-only repo pre-commit permission hook. Latest
  bootstrap-compression follow-up (2026-03-27): the human-facing Step 0
  default is now `startup-context --format summary` across generated
  bootstrap surfaces and review-channel conductor/bridge startup text, so AI
  sessions get the same typed startup decision in a compact four-line receipt
  (`action`, `reason`, `blockers`, `next`) before the optional
  `context-graph` expansion. The typed JSON payload and managed startup
  receipt still remain authoritative artifacts under the repo-owned reports
  root; this slice only compresses the human bootstrap projection. Latest
  chat-bootstrap follow-up (2026-03-27): the same generated bootstrap/review
  surfaces now tell agents not to replay that packet into chat by default.
  Chat bootstrap acknowledgements should stay at blocker state plus next step
  unless the operator explicitly asks for the richer packet.
  Local release-preflight follow-up (2026-03-27): the release bundle's
  user-doc gate is now branch-aware. `docs-check --user-facing
  --strict-release` keeps master release validation fully strict while
  feature-branch release-sensitive preflight only turns on the strict user-doc
  requirement when the branch carries a release-style user-doc signal (CLI
  schema drift or a broad user-doc edit set), so tooling-only workflow edits
  no longer strand governed `devctl push` on unrelated product docs.
  Latest release-maintenance follow-up (2026-03-27): the same release bundle
  now distinguishes master-only freshness gates from feature-branch preflight
  noise. `devctl hygiene --strict-release-warnings` keeps the release branch
  fully strict while auto-ignoring release-maintenance warning families on
  non-release branches, and `check_publication_sync.py --release-branch-aware`
  still reports stale publication drift everywhere but only hard-blocks it
  when `HEAD` resolves to the configured release branch. That keeps governed
  feature-branch `check-router` / `devctl push` aligned with real release risk
  instead of stalling on unrelated external-site sync debt.
  Latest
  architecture-framing follow-up (2026-03-24): explain the platform as a
  compiler-like pass pipeline (signal extraction -> decision reduction ->
  constrained execution -> feedback) while keeping typed contracts, not
  prompt lore, authoritative. The accepted follow-on work from that framing is
  explicit actuator/proof closure: dynamic failure rules stay with `MP-375`,
  while `MP-377` now also tracks session-decision artifacts and measured
  convergence proof for iterative remediation/runtime loops. Second-pass
  alignment keeps deterministic prompt ordering, allowed transforms,
  signal-trust gating, change-pressure gating, and reproducibility proof in
  the same owners instead of creating new plan lanes or proof-only artifact
  families.
  - [ ] Land the missing authority-spine runtime nodes
    (`PlanTargetRef`, `WorkIntakePacket`, `CollaborationSession`) before
    widening `P1`/`P2` routing and adoption work. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 32)
  - [ ] Compile plan-derived swarm packets from that same authority spine.
    The selected `PlanTargetRef` / `WorkIntakePacket` /
    `PlanExpectationPacket` should produce bounded reviewer/coder lane
    assignments with explicit role, owned target or issue cluster, owned
    worktree/path scope, allowed command families, required guards,
    expected artifacts, and conductor return contracts. Treat the 8+8 lane
    table as maximum capacity only, not as permanent role truth.
  - [x] Replace boolean-only `Session Resume` detection with typed continuity
    state in `startup-context` / intake routing. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 28) (closed 2026-04-07 — see
    `platform_authority_loop.md` typed-continuity tranche follow-ups A/B/C)
  - [ ] Turn report-only governance-routing and AI-guidance fields into live
    runtime inputs across startup, repair, review, and `guard-run` flows.
    First proof slices landed: Ralph now consumes exact file-matched
    canonical probe `ai_instruction` from `review_targets.json`, autonomy
    `triage-loop` / `loop-packet` now consumes the same guidance from a
    bounded structured backlog slice, review-channel/conductor plus swarm
    inherit that contract through shared context packets, escalation packets
    now carry `## Probe Guidance` plus stable `guidance_refs`, and the
    deterministic route-closure guard now proves the Ralph / autonomy /
    `guard-run` family inside `check_platform_contract_closure.py`, including
    a family-completeness failure if any declared consumer disappears. The
    first carried decision semantic is now live too: matched probe guidance
    merges `DecisionPacket.decision_mode`, Ralph/autonomy/`guard-run` treat
    `approval_required` as a real behavior gate, and the same closure guard
    now proves that family as well. The remaining closure in this same
    tranche is broader single-authority + structured-routing enforcement so
    AI consumers cannot silently negotiate between multiple artifact
    authorities or keep deriving routing keys from prose when typed fields
    already exist, together with explicit adoption proof: prompts must keep
    telling AI to prefer attached probe guidance, matching must prefer
    structured identity, and runtime telemetry must record stable
    `guidance_id` / `guidance_followed` plus fix outcome. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 27, Part 38, Part 52, Part 54)
  - [ ] Add deterministic validation contracts as a first-class AI trust
    boundary instead of treating generic green test suites as sufficient
    confidence: model a portable contract-test family over runner-specific
    adapters, with a pytest-first adapter in this repo but no universal
    pytest assumption in the core contract. Project failing cases into
    canonical `Finding` records, make `DecisionPacket.validation_plan`
    executable as typed validator refs before and after mutations, and allow
    `decision_mode` upgrades only when the exact routed validation plan for
    that finding passes. Passing validators may widen weaker modes, but must
    never override explicit human `approval_required`. Coverage, blast
    radius, and change scope may weight trust, but they do not replace
    finding-scoped validator proof as the autonomy gate. Keep advisory
    test-quality probes distinct from blocking contract-test guards, and keep
    selectors/thresholds repo-policy-owned rather than hardcoded repo-wide
    coverage rules. The underlying rule is testability from typed contracts:
    the same governed input state should yield the same bounded packet and
    validator route, so onboarding and remediation proof can be regression-
    tested instead of prose-reviewed.
  - [ ] Keep the next swarm implementation order foundation-first even when
    fan-out capacity exists. The near-term bounded lanes are
    `validation_plan` execution and contract/workflow hardening, pattern
    aggregation plus typed `current_session` closure, and at most one
    report-only adopter smoke lane for early hidden-coupling signal. Official
    cross-repo proof stays in the later Phase-7 adoption owner lane and must
    not jump ahead of blocker/P0 prerequisites.
  - [ ] Keep live current-status narrow and projection-first:
    `review_state.json.current_session` should carry only the current answer
    by reference to the latest `DecisionTrace` plus the next action,
    wait/block reasons, bounded blocker summary, and live reviewer/ack state.
    `bridge.md`, `latest.md`, chat packets, CLI status, and operator views
    must render from that typed state instead of carrying their own current
    truth.
  - [ ] Add one minimal `explain-latest` read surface over the same owner
    chain: load `current_session` plus the latest `DecisionTrace`, then render
    what changed, why continue/checkpoint/review/push was chosen, which
    evidence blocked or allowed it, and the exact next command without
    inventing another authority path.
  - [ ] Keep deterministic validation as one governed evidence family, not
    the whole autonomy story: failing contract-test / validation-runner cases
    should normalize into canonical `Finding` rows with a distinct
    validation/test-failure signal, while passing validators are one trust
    input only and never a blanket auto-apply proof.
  - [ ] Add the explicit infrastructure prerequisites for that same lane:
    burn down direct `REPO_ROOT` imports through injected repo-root/repo-pack
    dependencies, extract git/filesystem adapters and repository-style
    loaders, replace governance-ledger `dict[str, Any]` rows with typed
    contracts, add a bounded finding/decision/review aggregate, and remove
    inner-runtime subprocess/git lookups from the first touched runtime
    helpers.
  - [ ] Make `validation_plan` and contract testing concrete, not aspirational:
    execute `DecisionPacket.validation_plan` on the first repair/apply lane,
    normalize failure cases into canonical findings through a dedicated
    adapter, register strict pytest contract/guard markers, and add focused
    contract-test coverage for task-router, push-policy, startup-context
    shape, and the first validation/failure adapter path.
  - [ ] `MP377-P0-T22AN-AB` now owns the immediate pytest-runaway dogfood
    closure: Python validation should route through the bounded
    `devctl test-python` adapter, root pytest config must stay scoped and
    timeout-guarded, and `check-router` should add path-aware Python suites
    instead of keeping broad raw pytest in static bundles. The `AGENTS.md`
    command inventory now names `test-python` directly so
    `check_agents_contract.py` protects that adapter as part of startup and
    push governance. 2026-05-04 dogfood of governed push showed the focused
    devctl add-on timing out as one monolithic pytest command; the adapter now
    shards explicit multi-path runs with `--parallel-workers`, the router uses
    that path for focused devctl add-ons, and temp/external work-intake pacing
    no longer falls back to scanning the canonical repo context graph.
    2026-05-06 governed-push dogfood then proved the focused devctl command
    could pass after the generic 300s command budget, but could still time out
    when two heavy targets shared one pytest session, then measured
    `test_development_command.py` passing in 435.45s only after a 600s typed
    session. The router now splits focused devctl targets into serial
    single-target sessions with a 420s measured floor plus target-specific
    measured overrides. 2026-05-08 push-preflight dogfood found
    `test_push.py` passing its assertions but timing out as one serial 600s
    target; the push tests now mock live repo-scale projection scans in unit
    paths, `check-router` emits class-level pytest node-id shards for that
    file with four `test-python` workers, and its typed target floor is reduced
    to 240s from measured 80.48s serial / 48.31s sharded proof.
  - [ ] `MP377-P0-PIPELINE-SCOPE-VALIDATION-S1` threads typed validation scope
    through governed publication checks. Governed push uses
    `pipeline_authorized_phase` for preflight, while standalone checks remain
    strict under `live_worktree`. Router, docs-check, and live projection
    guards must keep their rows visible, preserve original live failures as
    advisory evidence, and avoid treating unrelated dirty worktree state as
    proof that the authorized commit range is invalid. 2026-05-09 packets
    `rev_pkt_3329`, `rev_pkt_3334`, `rev_pkt_3343`, `rev_pkt_3344`,
    `rev_pkt_3345`, `rev_pkt_3346`, `rev_pkt_3347`, `rev_pkt_3349`,
    `rev_pkt_3350`, `rev_pkt_3356`, and Claude approval `rev_pkt_3357`
    converged the design. 2026-05-11 push dogfood exposed the adjacent
    operator-observability gap: publication preflight must fail fast by default
    and must not imply that `git push` has started while it is still running
    guards. Repo policy now owns `fail_fast_on_blocker=true`; audit-only
    policies can opt back into `--keep-going`.
  - [x] `MP377-P0-T22AN-AC` now owns fresh-session orientation automation:
    `devctl session` must run startup-context, session-resume, live
    review-channel status, and context-graph bootstrap before answering
    "where are we" or selecting next work.
    2026-05-08 update: generated boot cards now route fresh sessions through
    `devctl session` first, and the session reducer preserves a blocking
    review/status `AuthoritySnapshot` instead of promoting startup
    `run_devctl_push` through `safe_to_continue=false` or `vcs.push` blocks.
    2026-05-13 live controller dogfood also fixed stale pending-packet blocker
    prose: when typed packet attention reports zero scoped pending packets,
    legacy `session.open_findings` text like `138 pending review packet(s)` no
    longer blocks `agent-loop` or `/develop next`. Closure proof: the focused
    session-orientation/read-only/startup-blocker tests passed 44/44, and a
    live `devctl session --role implementer --include-review-status always
    --format json` emitted a complete `SessionOrientationPacket` with all four
    child reducers parsed.
    2026-05-14 update: `MP377-BOOT-CARD-ROLE-DISCOVERY-S1` closes the adjacent
    fresh-session role-discovery smell by rendering concrete AGENTS/CLAUDE
    role examples, enumerating `reviewer`, `implementer`, `dashboard`, and
    `observer`, surfacing help commands, and teaching `check_agents_contract.py`
    to reject `--role <role>`/invalid-role placeholders.
  - [ ] `MP377-P0-T22AN-AD` now owns Claude `rev_pkt_2863` slash-domain
    architecture: split canonical slash entry points by typed backend domain
    while keeping current `/develop` role presets as compatibility aliases
    until replacement slashes have contracts, docs, and tests.
  - [ ] `MP377-P0-T22AN-AE` now owns the `rev_pkt_2929` handoff-to-
    publication dogfood gap: a `stage_commit_pipeline` packet with typed
    runtime authority should drive ACK/apply, startup push-state evaluation,
    managed projection receipt repair, routed `check-router --execute
    --keep-going` guard coverage/remediation proof, bounded fixed-point
    refresh, concurrent source-edit waiting, governed `devctl push --execute`,
    long-running phase progress, and packet evidence closeout through one
    typed controller instead of watcher-authored shell branching. The
    2026-05-04 router follow-up proved the first automation sub-slice:
    routed preflight now exposes serial/parallel execution-plan metadata,
    keeps projection/status commands ordered, runs independent guard rows in
    worker batches, and splits focused devctl Python proof into serial
    single-target sessions with a measured 420s floor plus target-specific
    measured overrides. The same dogfood cycle exposed the next silent serial phase:
    governed commit now emits VCS phase progress while `git commit` and the
    post-commit ReviewSnapshot receipt hook run, so operators can distinguish
    commit execution, receipt refresh, and push handoff without process-table
    guessing.
  - [ ] `MP377-P0-T22AN-AF` now owns the packet-attention/no-conductor
    boundary: packet post, delivery, follow-loop attention, inbox/watch, and
    packet-backed control paths may update typed packet attention and plan
    intake, but must never launch, replace, clean up, or externally wake a
    provider session. Scheduler/runtime controllers own session starts and
    worker fanout after explicit task-boundary evidence. Claude dogfood
    `rev_pkt_2940` added the post-report `packet_attention` primary key,
    advisory plan-context binding receipts for communication-only notices, and
    `/develop` peer-mind `attention_hint` poll commands.
  - [ ] `MP377-P0-T22AN-AG` now owns `rev_pkt_2936` Class F cold-session
    bootstrap enforcement: startup-context, role-bound session-resume, and
    context-graph bootstrap receipts must be mandatory runtime preconditions,
    not prose conventions that a new agent can skip.
  - [ ] `MP377-P0-T22AN-AH` now owns `rev_pkt_2942` deterministic semantic
    guard promotion: encode contract-renames, vocabulary contracts, and
    dataclass shape clusters as typed guard inputs so wake-to-attention,
    next-command vocabulary drift, and Session*/Packet*/Receipt* type
    proliferation are caught by deterministic checks instead of operator-led
    grep scans.
  - [ ] `MP377-P0-T22AN-AI` now owns `rev_pkt_2943` architectural-suggestion
    routing: aggregate governance/probe/guard findings, rank the top bounded
    suggestions for the current actor/slice, and surface them through
    `/develop` attention before more guard output becomes another ignored
    report backlog.
  - [ ] `MP377-P0-T22AN-G` now explicitly includes `rev_pkt_2944` packet-expiry
    closure: pre-expiry intent extraction and startup batch-ingest must move
    substantive packet bodies into durable plan/finding ownership before
    `clock_expired_without_disposition` can archive the transport.
    2026-05-04 read-side closure: `PacketOutcomeLedger` and
    `PacketDisposition` now preserve `expired_after_durable_binding` for
    packets with `PacketCreationBinding` or durable-ingestion receipts, so
    plan-bound expired Claude/Codex packets remain archived audit rows with a
    durable owner instead of looking like unbound clock loss.
  - [ ] Freeze the first explanation/contract boundary shapes in that same
    lane: use closed-vocabulary status/wait-reason enums for `DecisionTrace`,
    add strict boundary-validation models plus JSON Schema emission for
    `StartupReceipt`, `DecisionTrace`, and `FailurePacket`, and keep those
    models parse-time only so the internal runtime remains on frozen
    dataclasses.
  - [ ] Route fresh `dev/reports/**` operational evidence into the live prompt
    builders and adjacent decision surfaces so bootstrap, conductor, swarm,
    Ralph, loop-packet, escalation, and other runtime controllers consume
    hotspot, verdict-history, watchdog, reliability, queue-state, quality-
    feedback, decision metadata, research-benchmark, and event-history data
    instead of leaving those artifacts write-only or display-only. Immediate
    zero-consumer backlog still called out by audit is now narrower:
    `finding_reviews.jsonl` history plus quality-feedback recommendations are
    flowing through shared context packets, watchdog episode digests plus
    data-science command-reliability lines now flow through the same shared
    packet family, and the first `DecisionPacket` behavior gate
    (`decision_mode`) now reaches live prompt/runtime consumers. Remaining
    backlog is selective startup/work-intake adoption of
    `governance-quality-feedback` plus broader decision/adoption metadata and
    impact measurement, not the original transport gap. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 42, Part 45, Part 54)
  - [ ] Make startup quality-signal loading repo-pack-aware and fail-closed:
    `startup_signals`, `startup-context`, and bootstrap `context-graph`
    must resolve `probe-report`, `governance-review`,
    `governance-quality-feedback`, and data-science summaries from declared
    `ProjectGovernance.artifact_roots` rather than hardcoded path guesses,
    and focused regression tests must prove every advertised startup signal
    family is actually loadable from those emitted roots.
  - [ ] Make startup/work-intake and repo-owned launcher paths consume more
    than receipt presence: `selected_workflow_profile`, `preflight_command`,
    `warm_refs`, `writeback_sinks`, and adjacent live reviewer/agent state
    should steer routing instead of staying render-only fields inside the
    first `WorkIntakePacket` proof. The next bounded closure is coherence:
    `startup-context` must not emit a `check-router --since-ref ...`
    preflight that falls back to `bundle.docs` on the same dirty tree the
    packet already classified as `bundle.tooling`.
  - [ ] Close the raw interactive bootstrap bypass on top of the repo-owned
    receipt gate: a fresh provider-owned `claude` or `codex` shell can
    still skip Step 0 and cold-read files before `startup-context` runs.
    Add one supported hook/wrapper/launcher contract that consumes the same
    startup receipt for raw interactive entry, and keep generated bootstrap
    docs explicit that documented Step 0 is not universal mechanical
    enforcement until that adapter path is live.
  - [ ] Keep docs-governance classification deterministic before
    `DocRegistry` / startup authority widen: canonical
    guide/reference/spec/runbook classes must come from policy/registry
    shape rather than ad hoc path fallbacks, and focused `doc-authority`
    regression tests should pin root-guide classification.
  - [ ] Add a typed session-decision log over `DecisionPacket`,
    guidance-adoption, waiver, and outcome history, then feed it into
    `startup-context` plus future `CollaborationSession` surfaces.
  - [ ] Extend governance closeout before the next self-governance guards go
    hard red: `FindingReview` rows for `missing_guard` / `missing_probe` must
    carry explicit follow-up refs (proposed guard/probe, owning MP, or waiver)
    and runtime/governance paths must share one stable `finding_id` contract.
  - [ ] Add self-governance completeness guards over the declared platform
    contracts: missing-guard/probe follow-up closure, finding-lifecycle
    closure, bounded producer/consumer loop closure for declared machine-
    readable runtime surfaces, and consumer-parity for contract-catalog rows
    marked `live`. Keep loop/parity guards scoped to declared authoritative
    families so human-only outputs and placeholder rows do not create noise.
  - [ ] Add one bounded self-hosting producer-to-consumer smoke lane for the
    governed startup surfaces: exercise `probe-report`,
    `governance-review`, `governance-quality-feedback`,
    `context-graph --mode bootstrap`, `platform-contracts`, and
    `startup-context` against the same artifact roots, and prove the emitted
    startup preflight stays coherent with `check-router` on the same routing
    basis so CI/local smoke validates real emitted data paths instead of only
    schema/catalog drift.
  - [ ] Add lifecycle status to contract-catalog rows (`live`, `scaffold`,
    `planned`, `compat`) and require `RunRecord`, `ArtifactStore`, adapter
    rows, and other exported contracts either to declare one live producer-
    consumer route or stay explicitly non-live until wired.
  - [ ] Split slim decision-path packets from archive/history-heavy artifact
    families in `ArtifactStore` / retention policy so startup, review, and
    runtime controllers can consume routing-critical evidence without loading
    the whole audit/report surface by default.
  - [ ] Add a typed `DecisionTrace` artifact per runtime decision so guard/
    probe results, graph/evidence path, diff stats or graph-delta summary,
    metrics deltas, confidence, chosen decision, and outcome travel together
    before they are aggregated into a session log, instead of creating a
    separate proof-only packet family for the same slice.
  - [ ] Compile the selected `PlanTargetRef` into a typed
    `PlanExpectationPacket` before AI/runtime reconciliation: invariants,
    required artifacts, forbidden states, validation commands, evidence
    queries, and success criteria should become machine-usable expectation
    input. Compare that packet against observed receipts/tests/findings to
    emit plan drift, implementation drift, contract drift, or
    missing-validation findings, and never let observed behavior silently
    rewrite plan truth.
  - [ ] Make explanation outputs deterministic and teachable: define one
    schema-validated decision-record vocabulary for startup/review/push and
    later runtime decisions (`status`, `goal`, `facts_observed`,
    `rules_triggered`, `rejected_options`, `chosen_action`, `next_command`,
    `uncertainty`), keep direct observations separate from guesses, and render
    junior-dev-readable explanations from that packet instead of asking AI for
    open-ended reasoning prose in the authoritative path.
  - [x] Add one platform-owned Python architecture guide and decision tree
    aligned with the same contract-first style: teach when to use `dict`,
    `TypedDict`, `dataclass`, boundary-validation models, and `Protocol`,
    then connect those modeling choices to repository/service/unit-of-work/
    dependency-injection patterns in plain language. Treat Cosmic Python
    (Ch. 1-6, 8, 13), the official typing docs, Pydantic strict-mode/JSON
    Schema, and FastAPI boundary-model docs as the recommended starter stack,
    while keeping Pydantic scoped to untrusted or serialized boundaries rather
    than as the default internal model for every runtime contract.
  - [x] Start the explanation rollout from existing typed surfaces instead of
    waiting for a greenfield trace module: extend `DecisionPacketRecord` and
    the routed startup/task-router/workflow-profile receipts with
    `match_evidence`, rejected-rule traces, and plain-language rule summaries
    so selected bundles and next commands explain why they were chosen. First
    rollout targets are explicit: task-router lane selection,
    `selected_workflow_profile`, startup/push decisions, and context-graph
    query relevance ("why this node matched") before widening to broader
    runtime traces.
  - [x] Reuse the shipped probe teaching corpus before writing new prose:
    render `dev/scripts/checks/probe_report/practices.py` /
    `SIGNAL_TO_PRACTICE` explanations and fix patterns directly into
    canonical probe packets, and add plain-language metric explanations for
    `fan_in`, `fan_out`, `bridge_score`, and hotspot rank so quality signals
    stop surfacing as unlabeled numbers.
  - [x] Explain context-graph/query relevance in the same vocabulary: query
    matches, ranking/downgrade choices, and selected hotspot/context nodes
    should surface one short "why this node matched / why this node ranked"
    explanation instead of only temperatures, edge counts, or returned file
    lists.
  - [x] Close the first explainability-regression misses in the same lane:
    startup decision helpers now keep consuming typed `PushEnforcement`
    instead of `object` + `getattr`, `probe_design_smells` catches
    first-parameter and multiline `: object` seams, and review-channel
    attention surfaces `bridge_contract_error` ahead of checkpoint advice when
    `active_dual_agent` is invalid because no repo-owned conductors are live.
    `check_python_dict_schema` now also blocks growth of the same
    `object`-plus-`getattr` seam inside authoritative runtime/review/
    governance modules.
  - [ ] Evaluate one optional advisory decision-auditor step over
    `DecisionTrace` for high-blast-radius or low-confidence cases; it may
    challenge or confirm the reasoning before mutation, but
    `approval_required` remains a human/operator gate and deterministic
    guards stay authoritative.
  - [ ] Add measured convergence proof to iterative remediation/runtime loops:
    record quality deltas, diminishing-returns thresholds, worsening
    detection, and stop reasons in `RunRecord` and operator/startup
    projections so bounded loops can prove why they stopped.
  - [ ] Add one explicit improvement-proof lane over AI-touched changes:
    keep a typed improvement ledger plus recurrence index so each governed fix
    records before/after guards, validator deltas, changed contracts or
    artifacts, recurrence ids, and one five-way fix classification
    (`real_debt_removed`, `debt_relocated`, `policy_only_cleanup`,
    `behavior_preserving_simplification`, `unknown_outcome`). Use that same
    ledger to separate real semantic improvement from guard-only motion
    before claiming governance quality gains, and later extend it with
    changed-file validation expectations plus contract/golden snapshot parity
    as semantic-regression evidence.
  - [ ] Finish the first graph-routing expansion by emitting live
    `EDGE_KIND_GUARDS` / `EDGE_KIND_SCOPED_BY` edges, land the guard-edge
    quick win first, add the missing node families (`test`, `workflow`,
    `config`, `finding`, `contract`) incrementally, and widen graph consumers
    beyond escalation-only packets into startup, autonomy, repair, and
    operator routing. The first non-escalation consumer should let
    high-confidence `guards` / `scoped_by` relations influence startup /
    work-intake / validator routing rather than keeping those edges render-
    only. Keep this behind the direct closure tranches:
    `ai_instruction` wiring, the produced-but-never-consumed meta-guard, and
    startup/session unification should not block on ZGraph; it becomes the
    query engine once these edges and consumers land. First closure slice is
    now live: the builder emits guard-coverage edges from active quality
    policy + scope roots and initial policy-backed plan-ownership edges from
    docs-policy tooling prefixes. Remaining work is the node-family rollout,
    query filtering/downranking so guard-edge fan-out does not drown useful
    imports, plan-registry-backed scoped ownership beyond docs-policy tooling
    prefixes, and wider non-escalation consumers. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 43, Part 47)
  - [ ] Add deterministic temporal ZGraph snapshots on top of that graph lane:
    save graph snapshots at CI/check boundaries, diff successive snapshots,
    and surface architecture-drift/trend answers by reusing the existing
    snapshot/delta patterns already present in data-science and quality-
    feedback instead of creating a second graph-analysis stack. First slice
    now live: `context-graph --mode bootstrap` persists a typed
    `ContextGraphSnapshot` artifact under `dev/reports/graph_snapshots/`, and
    `--save-snapshot` widens that same writer to the other graph modes.
    Second slice now live too: `context-graph --mode diff --from ... --to ...`
    resolves saved snapshots back into a typed `ContextGraphDelta`, reports
    added/removed/changed nodes and edges plus edge-kind/temperature deltas,
    and adds a rolling trend summary over recent snapshots. Follow-up
    hardening now landed too: `latest` / `previous` ordering comes from
    snapshot capture time instead of filesystem `mtime`, direct-path trend
    scans ignore non-snapshot sibling JSON, and delta/trend anchors now emit
    portable snapshot-store-relative paths instead of machine-local absolute
    paths. Remaining work is wider capture automation and richer drift
    interpretation, not basic diff/trend plumbing. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 53)
  - [ ] Add a generated-only graph normalization/compaction reducer after the
    first query-engine proof: distinguish routing-grade vs render-only
    edges, precompute bounded high-signal neighborhoods for startup /
    work-intake / common query paths, and prove the compacted view
    preserves canonical refs while lowering default query noise. Keep the
    reducer reversible and disposable so it never becomes a second
    authority store.
  - [ ] Add check-runner performance contracts after the first cache-backed
    startup / `system-picture` path is real: diff-aware and language-aware
    skip rules, shared parser/AST reuse for multi-guard runs, immutable
    tree-hash guard-result caching, and layered early-exit execution should
    be measured, typed, and invalidated from canonical tree/work-scope
    inputs rather than guessed.
  - [ ] Evaluate temporal stability/volatility signals on top of that graph
    lane before promoting them into routing or temperature authority:
    change-frequency and centrality-like impact metadata should become
    policy-backed evidence first, not fixed one-off math.
  - [ ] Separate presentation temperature from action gating on top of that
    same evidence lane: derive a policy-backed change-pressure score from
    volatility/stability signals, quality-feedback state, watchdog/probe
    risk, command reliability, and guidance trust so runtime controllers can
    decide whether to act, escalate, or downgrade to `approval_required`
    without overloading hotspot temperature with decision semantics.
  - [ ] Add one explicit trigger from local repair context into bounded
    global architecture review: repeated churn or policy-declared coupling
    deltas should be able to promote a slice from local guidance to a wider
    architecture pass without making full-graph reasoning the default.
    Current partial proof: `startup-context --repair` now gives startup one typed local
    repair controller over approval-boundary vs safe-local-repair vs
    manual-follow-up state, consumes the same typed `ReviewState` owner as
    `review-channel`, and refreshes startup receipts after one bounded
    repo-owned fix per pass, but it does not yet promote recurring churn into
    graph-backed architecture review automatically.
  - [ ] Unify the current startup systems behind one canonical
    `startup-context` / `WorkIntakePacket` path so bootstrap instructions,
    governed-plan `Session Resume`, repo memory, and recent episode evidence
    feed one bounded startup packet instead of four disconnected sources.
    Current partial proof: generated bootstrap surfaces and review-channel
    bootstrap prompts now explicitly tell agents when to escalate from the
    slim bootstrap helper to typed `startup-context`, and governance draft
    discovery now only serializes `memory_roots` when real canonical repo
    roots exist instead of emitting an always-empty placeholder. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 46)
  - [ ] Promote checkpoint budget from advisory status to fail-closed startup
    authority: when the typed startup / collaboration receipt reports
    `safe_to_continue_editing=false` or `checkpoint_required=true`, repo-owned
    launchers must refuse to start the next implementation slice and only
    promote checkpoint/review work until a fresh post-commit/push receipt
    clears the budget. Current partial proof: `review-channel --action
    launch|rollover` now treat the typed checkpoint budget as a hard launch
    blocker, `startup-context` itself now returns non-zero on that same typed
    checkpoint receipt, and `check_startup_authority_contract.py` now fails when the
    startup authority packet is already over budget or when repo-local Python
    imports only resolve from worktree-only modules instead of the git index,
    while separately validating committed importer content against `HEAD`
    without treating a legitimate staged atomic split as broken.
    Latest follow-up (2026-04-02): the same startup-authority contract now
    also fails when a local checkpoint exists (`ahead_of_upstream_commits > 0`)
    and the worktree is dirty again, and the VoiceTerm quality-policy preset
    now enables that guard in the default `check --profile ci` lane so the
    branch-local dirty-after-checkpoint state goes red before governed push.
    Latest follow-up (2026-04-09): the same self-hosting lane now fails closed
    on guard-registration drift too. `check_mutation_bypass_graph_closure.py`
    is now wired through the portable Python quality-policy preset plus the
    shared tooling/release bundle/workflow lanes, and
    `check_guard_enforcement_inventory.py` + `check_bundle_workflow_parity.py`
    are treated as required closure whenever a new public guard graduates into
    shared hard-guard status.
    Latest follow-up (2026-04-03): startup receipt freshness is now intent-
    aware too. `review-channel --action launch|rollover` keep the hard
    checkpoint/branch/non-reviewer-authority blockers, but plain HEAD drift
    only blocks reviewer bootstrap when the diff since the receipt crosses
    guarded quality-scope roots; implementation/push lanes still require exact
    HEAD equality.
    Latest follow-up (2026-04-02): post-publication governed push receipts now
    also stop at the fetched divergence boundary. When the tracked branch is
    already at `ahead == 0`, `devctl push` skips router preflight entirely and
    returns the existing `branch_already_pushed` / `published_remote` truth
    instead of defaulting zero changed paths into the docs lane and saving a
    fabricated blocked receipt.
    Current follow-up after the 2026-03-23 closure pass: `startup-context`
    itself is now the documented Step 0 gate, it persists a managed
    `StartupReceipt` under the repo-owned reports root derived from live
    governance/path-root authority, and scoped repo-owned launcher/mutation
  `devctl` commands (`push`, `sync`, `guard-run`, `autonomy-loop`,
  `autonomy-swarm`, `swarm_run`, `review-channel --action launch|rollover`,
  and selected controller actions) now require a fresh receipt and still
  fail closed on live startup-authority errors. Remaining closure is broader
  raw provider entry, repo-pack activation, plus any additional mutating
  commands that should graduate into the same gate, not the original
  instruction-surface loophole. Latest follow-up (2026-03-24): the typed review-state
  consumers behind that same startup/tandem path now share one repo-pack-
  aware resolver instead of hardcoding
  `dev/reports/review_channel/latest/review_state.json`, so
  `startup-context`, startup `WorkIntakePacket` routing, and
  `check_tandem_consistency` stay aligned with review-state candidate-path
  authority while the remaining raw provider/repo-pack activation work stays
  explicit. Latest follow-up (2026-03-24): guarded feature-branch push
  preflight now diffs against the tracked upstream ref instead of always
  `origin/develop`, which removed the false `bundle.release` / CodeRabbit
  feature-branch block, and the tooling lane now treats stale
  mutation-badge freshness as visible non-blocking debt instead of a local
  push blocker while leaving release lanes unchanged. Latest follow-up
  (2026-03-24): `check_governance_closure` now recognizes shared test
  coverage by content reference and AI-guard CI coverage via
  `devctl check --profile ci`, while the previously-uncovered guard/probe
  scripts gained smoke coverage, so guarded push now fails on real
  meta-governance debt instead of filename/YAML false negatives. Latest
  follow-up (2026-03-25): maintainer docs were corrected to stop
  overstating `context-graph` `scoped_by` coverage; the live builder still
  derives those ownership edges from docs-policy prefixes while the broader
  plan-registry-backed ownership expansion remains open in the MP-377 graph
  lane. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 28, Part 36, Part 41)
  - [ ] Auto-record `governance-review` close-out and converge top-level
    failures on structured `ActionResult` crash envelopes. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 36, Part 39)
  - [ ] Turn session continuity into one typed path by combining parsed
    `Session Resume`, episode/execution digests, shared memory hints, and
    review/bridge liveness into the startup continuity packet instead of
    leaving them as disconnected silos. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 48)
  - [ ] Make architectural absorption a required finding-disposition rule: no
    important finding closes until it is classified for recurrence risk,
    mapped to an approved prevention surface or explicit waiver, and verified
    at both the local-fix and systemic-prevention layers. For externally found
    architecture smells, the closure step must also prove whether the current
    checker stack fired on the touched files and classify any miss as no-rule,
    too-narrow detection, or advisory-only severity before moving on.
  - [ ] Evaluate additive `devctl-mcp` transport over the existing
    context-graph / startup / plan-status read surfaces after authority-loop
    closure; keep it read-only first and route any writeback through the same
    typed action/approval path as the CLI. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 49)
  - [ ] Improve the portable governance CLI/operator surface with
    `guard-explain`, `which-tests`, described `devctl list` output, per-check
    status/timing, and an incremental check path so adopters can discover the
    right validation slice without source-diving. (evidence:
    `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 44)
  Latest audit-guide closure follow-up (2026-03-22): the full accepted
  `dev/guides/SYSTEM_AUDIT.md` action set is now explicitly owned in the
  canonical plan chain rather than partly implied in reference prose.
  `platform_authority_loop.md` now carries blocker/startup/memory/path-
  portability items
  (`D1-D5`, `S1-S4`, `E1`, `G1`, `A5-A12`, `A22-A23`), this `MP-377` platform
  plan carries feedback/runtime/self-governance closure (`A1-A4`, `A13`,
  `A16-A19`, `A27`, `A29`, `T3-T5`), `MP-376` carries portability/adoption
  proof (`A14`, `A20-A26`), `MP-355` carries review-channel consolidation
  (`A15`, `T1`), `review_probes.md` carries probe expansion/history wiring
  plus probe-quality portability/scoring calibration (`A28`, `A30`), and
  `MP-340` carries watchdog coverage (`T2`).
  `dev/guides/SYSTEM_AUDIT.md` is now integration-complete reference evidence
  pending retirement after the current Phase 7 proof/cleanup gate.
  `MP-340`,
  `MP-355`,
  and the current `MP-377` priority ladder is now explicit: `P0` = coherence,
  identity, registry, lifecycle, approvals, `map`, evidence bridge, and parity
  contracts; `P1` = product-operability, packaging/adoption, and full client/
  mode parity; `P2` = later enrichments that must not bypass the spine. Latest
  audit-intake sequencing: the 2026-03-16 architecture re-audit is now phased
  under that ladder instead of treated as a flat backlog. Current execution is
  limited to the `P0` contract-freeze tranche (`ActionResult`,
  `CommandGoalTaxonomy`, `RepoMapSnapshot` / `MapFocusQuery` /
  `TargetedCheckPlan`, attach/auth + service identity, write arbitration,
  degraded-mode, `Finding`/schema/artifact compatibility, and the first typed
  split between deterministic AI-fix packets and reusable design-decision
  packets with policy-owned auto-apply/recommend/approval semantics for the
  same AI/human evidence contract). Latest concrete landing (2026-03-17):
  `probe-report` now emits typed decision packets from `.probe-allowlist.json`
  `design_decision` entries with explicit decision modes and validation steps,
  so the self-hosting packet matches that contract instead of exposing a
  maintainer-only review bucket; latest contract-closure follow-up
  (2026-03-17): `check_platform_contract_closure.py` now enforces bounded
  closure between the shared blueprint, current runtime dataclass contracts,
  durable artifact schema metadata, and startup-surface command routing for
  the already-real platform families, with repo policy, bundles, and
  maintainer docs updated in the same slice;
  packaging/
  adoption/client-parity remains `P1`, and proof/scale extensions remain `P2`.
  `MP-358`, and `MP-359` are subordinate implementation lanes inside this
  boundary, not alternate product architectures. Immediate separation-first
  queue: remove direct `repo_packs.voiceterm` imports from portable/runtime
  layers, stop frontend imports of repo-internal `devctl` modules and bridge
  files, move typed JSON/runtime state to live authority over `bridge.md`
  while keeping markdown as an optional backend-fed mode/projection, freeze
  the VoiceTerm operator-shell boundary over the same backend used by
  CLI/PyQt6/phone, add one simple backend-owned agent lifecycle
  `ensure/start/resume/stop` surface for all clients, and push remaining
  VoiceTerm-only env/log/process defaults into adopter-layer wiring. Keep
  landing new loop/control-plane capability behind reusable seams while this
  extraction work is active; do not keep widening the VoiceTerm-embedded shape
  and defer separation to a later cleanup pass.
  Completion proof now explicitly includes collaboration-mode parity: the same
  system must work for `Codex+Claude`, `human+Claude`, and `human+tools-only`
  operation with one backend truth, the same routed checks, and the same
  operator-visible progress semantics across chat/CLI/PyQt6/phone/overlay.
  Naming/abstraction proof is now explicit too: keep the backend command/action
  inventory complete and stable, then project simpler user-facing aliases,
  skills, slash commands, and client buttons grouped by user goal (`inspect`,
  `review`, `fix`, `run`, `control`, `adopt`, `publish`, `maintain`) so the
  system stays understandable without hiding major architecture surfaces like
  review packets, control-plane loops, operator/device controls, portability,
  release/reporting flows, and whole-system maintenance/cleanup. Those
  user-facing wrappers should be repo-pack/policy configurable so developers
  and agent adopters can tune names/defaults without patching the portable
  core. Deep architecture review on 2026-03-16 also tightened the glue
  contract here: `Finding` stays the canonical evidence record and now needs
  family-wide migration, command/service outcomes need one typed
  `ActionResult` envelope, durable machine-output families need explicit
  schema-version coverage, and grouped command discovery must stay tied to the
  same command-goal taxonomy rather than drifting into ad hoc per-client help
  text. Do not demote multi-client write arbitration to later polish; many
  shells over one backend makes it part of the spine. The first concrete
  lifecycle/control-plane follow-up is now the shared
  `review-channel ensure/watch` slice so reviewer heartbeat/update publishing
  and mode-aware liveness move into the backend instead of remaining chat/MD
  habits. The first publisher step in that slice now exists as
  `review-channel ensure --follow`, which advances reviewer heartbeat on
  cadence and emits structured status frames, but controller-owned supervision
  and auto-start lifecycle still remain open. The newer
  `--start-publisher-if-missing` seam is real progress, but active dual-agent
  mode still false-greens when the publisher is missing because that lifecycle
  state is not yet part of the shared attention/runtime truth. The recent
  5-hour Claude wait also proved the same controller path still lacks timeout
  budgets, overdue escalation, and clean stop/cleanup semantics, so those are
  now part of the same lifecycle contract instead of future operator polish.
  The bounded M55 truth slice is now accepted, and the bounded M63 timeout/
  escalation slice is accepted too: the shared reviewer/coder loop now emits
  machine-readable `reviewer_overdue` attention with a configurable threshold.
  The bounded M64 clean-stop slice is accepted too: direct follow-backed
  controller runs now emit explicit stop reasons plus final publisher state.
  The bounded M65 detached publisher durability slice is accepted too:
  detached start now records `failed_start`, and later dead-PID reads infer
  `detached_exit` instead of leaving blank stop state. The bounded M66
  publisher-lifecycle attention slice is accepted too: shared attention/runtime
  state now distinguishes `failed_start` and `detached_exit` instead of
  collapsing both into generic `publisher_missing`, with the focused
  review-channel/runtime bundle green (`135` passing). The first bounded M67
  reviewer-worker seam is accepted too: `review-channel status`, `ensure`,
  `reviewer-heartbeat`, `reviewer-checkpoint`, and bridge-backed `full.json`
  projections now emit machine-readable `reviewer_worker` state, while
  `ensure --follow` cadence frames surface `review_needed` without pretending
  semantic review already happened. In Codex-only local-review mode,
  `single_agent` is the sanctioned reviewer state for this slice, and typed
  turn-authority reads should prefer `bridge.claude_ack_current` when the
  typed `current_session` ACK state is unknown. The bounded `M68`
  report-only supervisor/
  watch slice is accepted too: `reviewer-heartbeat --follow` now polls on
  cadence, refreshes reviewer heartbeat through the same repo-owned Python
  seam, and emits operator-visible `reviewer_worker` frames without claiming
  semantic review completion, with current local re-review green (`122`
  review-channel tests plus `check_review_channel_bridge.py`). The larger
  reviewer-lane blocker still remains explicit: the current Codex reviewer path
  is still chat-bound rather than a repo-owned persistent reviewer
  worker/service, so the loop can still stall even while Claude keeps polling
  correctly. The next bounded follow-up inside that blocker is now `M69`: add
  repo-owned detached lifecycle/status truth for the report-only supervisor
  path so it can stay alive and observable outside the current terminal/chat
  session before widening into semantic review automation. The first `M69`
  cleanup on the current local diff is already in: bridge-backed `status` and
  `_build_reviewer_state_report()` now reuse the already-computed
  `status_snapshot.reviewer_worker` value instead of re-running
  `check_review_needed()`, and the supporting lifecycle/follow helper split.
  The next local truth-closure slice now also fails reviewer-owned bridge
  rewrites closed when pending reviewer-targeted packets still exist in the
  event-backed inbox, and projects explicit runtime counts through doctor /
  dashboard / bridge-status surfaces so remote-control dashboards can see live
  conductor and daemon totals without inferring from bridge prose. The same
  governed-push lane now closes the temporary repo-policy bypass window too:
  `allow_skip_preflight` is back to `false`, and `test_push.py` loads the
  checked-in repo policy file so a future override cannot linger silently in
  branch-visible state after the paired recovery commit is supposed to land.
  keeps `check_code_shape.py` green while preserving the same reviewer-worker
  contract. The review-surface parity proof now also checks persisted disk
  `review_state` against the computed turn-authority / bridge-poll
  projection, so the live review snapshot cannot drift from the on-disk
  authority. The next same-scope cleanup is in too: both extracted
  `output_error` follow-loop exits now persist final stopped publisher/
  supervisor heartbeat state, lifecycle reads treat explicit stop records as
  not running even if the writer PID is still briefly alive while the CLI
  unwinds, and lifecycle heartbeats now persist per-PID variants so readers
  can select the freshest live publisher/supervisor writer before falling back
  to the freshest stopped/dead record. That closes the bounded `M69`
  detached-lifecycle truth seam on the current local diff. The next same-scope
  platform contract now keeps repo/worktree-scoped service identity and
  discovery plus backend attach/auth semantics in the accepted local baseline:
  the Python `devctl/review_channel` seam emits stable `service_identity` and
  `attach_auth_policy` payloads across bridge-backed status/report/projection
  surfaces so clients attach to the correct repo/worktree instance and the
  current local-only approval boundary is explicit. The next same-scope
  daemon-event to runtime-state reducer is now in too: live publisher and
  reviewer-supervisor follow loops append `daemon_started` /
  `daemon_heartbeat` / `daemon_stopped` rows into the structured event log,
  bridge-backed `status` now derives both runtime daemons from persisted
  lifecycle heartbeat truth instead of hard-coding an empty supervisor,
  `latest.md` renders that same runtime block for operators, and auto
  event-backed status stays gated on materialized `state.json` so daemon-only
  event logs do not silently flip authority. The next same-scope correction is
  now in too: event-backed liveness keeps explicit reviewer-owned bridge mode
  ahead of daemon lifecycle rows, ignores stopped daemon mode hints, and stops
  stale typed `current_session` drift warnings from reverse-overwriting a
  newer reviewer heartbeat/checkpoint bridge write. The next same-scope follow-up is
  now the retirement path for VoiceTerm-local action brokerage so the "one
  backend" claim becomes executable rather than aspirational. Preferred
  end-state is now explicit too:
  VoiceTerm should host/supervise that shared daemon/controller stack as the
  best local shell when present, but the same backend must remain
  directly attachable by CLI, PyQt6, phone/mobile, and skills/hooks without
  hidden VoiceTerm-only orchestration. The existing VoiceTerm daemon/session
  transport is necessary, but it is not yet the controller loop: PTY/session
  attach and terminal packet staging do not by themselves satisfy reviewer
  heartbeat, agent lifecycle `ensure/watch`, queue/action routing, or shared
  review/control-state publishing. Publisher/supervisor daemons are runtime
  infrastructure and projection health only; they may report
  `runtime_missing`, but they must not rewrite reviewer/session mode
  authority. The next controller follow-up should upgrade that daemon role
  from passive bridge watcher to bounded round supervisor: fresh agent
  invocation/re-entry, explicit ACK deadlines, and no-progress/error-repeat
  circuit breakers sourced from typed session state rather than markdown
  polling alone.

Control-plane program sequencing (maps to MP-330/331/332/336/338/340/355/360..367):

1. Ship canonical multi-view controller state projections (`full/compact/trace/actions`) from one packet source.
2. Add SSH-first/iPhone-safe read surfaces (`phone-status`) and Rust Dev-panel parity for run/agent/policy visibility.
3. Land the dedicated review-channel state/event contract and multi-format
   projections as a review-focused profile over the broader
   `controller_state` direction so reviewer/coder communication is packetized
   instead of living in hidden chat state.
4. Add a shared-screen VoiceTerm review surface that shows Codex, Claude, and
   operator lanes together while keeping early PTY ownership separate.
5. Keep desktop GUI clients non-canonical; allow only thin optional wrappers
   over Rust surfaces (`--dev`, future shared-screen review UI),
   `phone-status`, `controller-action`, and `devctl` APIs.
6. Freeze a typed queue/action path (`plan item`/packet/operator intent ->
   queue record -> typed action -> adapter/runtime handler -> receipt/state)
   so VoiceTerm stages and renders actions without becoming a second backend.
7. Add guarded operator actions (`dispatch-report-only`, `pause`, `resume`, `refresh`) with full audit logging.
8. Add reviewer-agent packet ingestion lane so loop-review feedback is machine-consumable, not manual copy/paste.
9. Add charted KPI trend surfaces (loop throughput, unresolved trend, mutation trend, automation-vs-AI mix) for architect decisions.
10. Add deterministic learning loop (`fingerprint -> playbook -> confidence -> guarded promote/decay`) with explicit evidence.
11. Promote staged write controls and any true shared-session mode only after replay protection + branch-protection-aware promotion guards are verified.

## Deferred Plans

- `dev/deferred/DEV_MODE_PLAN.md` (paused until Phases 1-2 outcomes are complete).
- MP-089 LLM-assisted voice-to-command generation (optional local/API provider) is deferred; current product focus is Codex/Claude CLI-native flow quality, not an additional LLM mediation layer.
- Post-next-release MP-346 backlog: stabilize Gemini startup/HUD flash behavior in `cursor` and `jetbrains` via adapter-owned policy paths (no new mixed host/provider branching outside adapter/runtime-profile ownership), with checkpoint + matrix evidence before closure.
- Post-next-release MP-346 backlog: investigate JetBrains+Claude non-regressive render-sync artifacts seen during long-output sessions (intermittent help/settings overlay flashing and duplicated bottom status-strip/HUD rows after short replies), capture focused logs/screenshots, and route fixes through adapter/runtime-profile ownership paths.
- Post-next-release MP-346 backlog: start AntiGravity reactivation readiness intake by defining runtime host fingerprint requirements and a compatibility-test design for `codex`/`claude`/`gemini` expectations before lifting deferred scope.
- Post-next-release MP-348 backlog: Codex red/green diff-era composer/input-row occlusion investigation is explicitly deferred until after release and requires logs+screenshot evidence before any runtime change.
- Post-next-release MP-349 backlog: Cursor+Claude plan-mode history/HUD corruption and transient garbled terminal output is explicitly deferred until after release; resize/readjust-driven recovery is a primary diagnostic clue for geometry/redraw synchronization investigation.
- AntiGravity host support is deferred until runtime fingerprint evidence
  exists; current release-scope MP-346 matrix closure is IDE-first
  (`cursor`, `jetbrains`), while `other` host validation is explicit
  post-next-release backlog.

## Release Policy (Checklist)

1. Confirm version parity and changelog readiness (`rust/Cargo.toml`,
   `pypi/pyproject.toml`, app plist, `dev/CHANGELOG.md`).
2. Run release verification bundle (`bundle.release`).
3. Run and wait for `release_preflight.yml` success for the exact target
   version/SHA.
4. Create/tag release from `master` only after same-SHA preflight success.
5. Monitor publish workflows (`publish_pypi`, `publish_homebrew`,
   `publish_release_binaries`, `release_attestation`) and verify PyPI payload
   (`https://pypi.org/pypi/voiceterm/<version>/json`).
6. Use local manual publish fallbacks only if workflows are unavailable.

## Execution Gate (Every Feature)

1. Create or link an MP item before implementation.
2. Implement the feature and add/update tests in the same change.
3. Run SDLC verification for scope:
   `python3 dev/scripts/devctl.py check --profile ci`
4. Run docs coverage check for user-facing work:
   `python3 dev/scripts/devctl.py docs-check --user-facing`
5. Update required docs (`dev/CHANGELOG.md` + relevant guides) before merge.
6. Push only after checks pass and plan/docs are aligned.

## References

- Execution + release tracking: `dev/active/MASTER_PLAN.md`
- Theme Studio architecture + gate checklist + consolidated overlay research/redesign detail: `dev/active/theme_upgrade.md`
- Memory + Action Studio architecture + gate checklist: `dev/active/memory_studio.md`
- Pre-release architecture/tooling cleanup execution plan: `dev/active/pre_release_architecture_audit.md`
- Consolidated full-surface audit findings evidence (reference-only): `dev/active/audit.md`
- Raw multi-agent audit merge transcript evidence (reference-only): `dev/active/move.md`
- ReviewSnapshot hardening audit intake (reference-only, routed through the
  MP-377 / MP-376 owner chain): `dev/audits/architecture_hardening_plan.md`
- Generated ReviewSnapshot projection (do not hand-edit): `dev/audits/REVIEW_SNAPSHOT.md`
- Devctl MCP + contract alignment guide: `dev/MCP_DEVCTL_ALIGNMENT.md`
- Autonomous loop + mobile control-plane execution spec: `dev/active/autonomous_control_plane.md`
- Loop artifact-to-chat suggestion coordination runbook: `dev/active/loop_chat_bridge.md`
- IDE/provider adapter modularization execution spec: `dev/active/ide_provider_modularization.md`
- Standalone slash command plan (Codex/Claude without overlay): `dev/active/slash_command_standalone.md`
- SDLC policy: `AGENTS.md`
- Architecture: `dev/ARCHITECTURE.md`
- Changelog: `dev/CHANGELOG.md`

## Archive Log

- `dev/archive/2026-03-05-devctl-mcp-contract-hardening.md`
- `dev/archive/2026-01-29-claudeaudit-completed.md`
- `dev/archive/2026-01-29-docs-governance.md`
- `dev/archive/2026-02-01-terminal-restore-guard.md`
- `dev/archive/2026-02-01-transcript-queue-flush.md`
- `dev/archive/2026-02-02-release-audit-completed.md`
- `dev/archive/2026-02-17-tooling-control-plane-consolidation.md`
- `dev/archive/2026-02-20-senior-engineering-audit.md`

## Generated Review Packet Creation Bindings

This generated ledger projects packet creation bindings for humans. The typed row authority is `dev/state/plan_index.jsonl`; packets remain communication and provenance after durable ownership lands.

- [ ] `PKT-BIND-REV-PKT-2710` Packet finding: Bundle DD: ACK rev_pkt_2709 + verified /develop slice landed with Bundle CC primitives + 4 post-CC findings + meta-guard suggestion (source `rev_pkt_2710`; target `plan:MP-377`; posted `2026-05-01T23:10:33.168871Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2708` Packet finding: Beta-test pass CC: ARCHITECTURAL — packets are supposed to merge into PlanRows at CREATION time per operator's contract; 1172 packets in carry_forward_debt prove the auto-bind is broken; full design for (Phase 1) PacketDe... (source `rev_pkt_2708`; target `plan:MP-377`; posted `2026-05-01T22:57:02.469936Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2711` Packet finding: Bundle EE: orphan-inventory exposes 16 phantom AGENT-N lanes + unregistered sibling clone (178/92 dirty/untracked) + 29 stash orphans (~30K cumulative dirty); governance-quality-feedback Grade F (53.2/100) with 3 of 7 sub... (source `rev_pkt_2711`; target `plan:MP-377`; posted `2026-05-01T23:20:11.748015Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2714` Packet finding: Bundle EE: typed-contract closure ring gaps (population/conservation/identity/register/query unguarded) + wake-delivery is contract-only (live evidence rev_pkt_2712 unacked). 5-guard portable proposal + wake-delivery prop... (source `rev_pkt_2714`; target `plan:MP-377`; posted `2026-05-01T23:37:27.834722Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2716` Packet finding: Bundle EE Addendum (extended): 9 routing-layer symptoms 23:30-23:50Z all collapse into one principal-actor migration slice (ai_governance_platform.md 904/913/1817/3667/8240-8245/10925). Sections 7-9 add live evidence: tar... (source `rev_pkt_2716`; target `plan:MP-377`; posted `2026-05-01T23:56:45.963306Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2725` Packet finding: Bundle FF: 10 /develop slash-command UX gaps captured during one real-agent flow iteration. Includes broken --packet-id filter, no body-read surface, pending_actionable empty while attention_required=True, hardcoded actor... (source `rev_pkt_2725`; target `plan:MP-377`; posted `2026-05-02T00:34:10.705689Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2726` Packet finding: Bundle GG: /develop as agent-end-user platform. Operator reframe (agents ARE end users; friction = architectural breakage). 8 concrete frictions from this session, Bundle FF F2 corrected (renderer-conservation), slice-rep... (source `rev_pkt_2726`; target `plan:MP-377`; posted `2026-05-02T00:48:02.780834Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2727` Packet finding: Bundle HH: Bundle GG corrections after 3-agent verification. Verbs: 6/8 ALREADY EXIST in code (only chain truly missing); real gap is 3 writers (MutationLease claim, handoff packet, RecoveryIntent). Frictions: 6/8 real ar... (source `rev_pkt_2727`; target `plan:MP-377`; posted `2026-05-02T00:54:20.390915Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2728` Packet finding: Bundle II: Learning surface gaps. governance-quality-feedback is Grade F (53.2/100), 3/7 sub-scores have NO EVIDENCE LOADED (code_shape, duplication, time_to_green). 0 FP classifications ever recorded - precision metric i... (source `rev_pkt_2728`; target `plan:MP-377`; posted `2026-05-02T01:00:07.010888Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2729` Packet finding: Bundle JJ: META-ARCHITECTURE — missing orchestration layer is the single gap behind Bundle EE/EE-Addendum/FF/GG/HH/II. System has detection + typed recommendations but NO orchestrator that consumes signals and fires write... (source `rev_pkt_2729`; target `plan:MP-377`; posted `2026-05-02T01:07:41.793179Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2730` Packet finding: Bundle KK: Multi-session test results. Operator spawned passive Codex (marker CODEX_PASSIVE_SYSTEM_TEST_MARKER_2026-05-02_A) + new Claude. agent_work_board STILL 5 rows post-spawn (typed surfaces don't auto-detect new ses... (source `rev_pkt_2730`; target `plan:MP-377`; posted `2026-05-02T01:14:06.549189Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2732` Packet finding: Bundle LL: Continued dogfood. Self-correction on Bundle KK Section 2 (work_board has 3-min detection lag, not 'never detects'). pause/resume confirmed writer_not_enabled previews (now 9/9 actuating verbs). tandem-validate... (source `rev_pkt_2732`; target `plan:MP-377`; posted `2026-05-02T01:24:08.032444Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2733` Packet finding: Bundle MM: agent-loop is a superset of /develop with 6 typed-surface disagreements not visible in /develop. codex_sessions: '0 live / 4 typed work-board' (literal in-field disagreement). coordination_topology: single_agen... (source `rev_pkt_2733`; target `plan:MP-377`; posted `2026-05-02T01:28:07.016837Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2735` Packet finding: Bundle NN: VERIFICATION of Codex's Bundle EE→MM fix slice. 5 of 6 claims verified ✅. peer_minds field landed cleanly (Bundle EE S1 closed). runtime field exposes 8 unregistered sessions / 6 fresh / 3 stale (rich new diagn... (source `rev_pkt_2735`; target `plan:MP-377`; posted `2026-05-02T01:38:22.952080Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2695` Packet finding: Proof gate: unscoped finding packets can satisfy scoped_packet_target for multiple Codex sessions (source `rev_pkt_2695`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2690` Packet finding: Lifecycle probes: duplicate event id, pending packet lag, and ACKed carry-forward debt need one maintenance lane (source `rev_pkt_2690`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2689` Packet finding: Generated surface drift: SYSTEM_MAP managed block is stale after connectivity changes (source `rev_pkt_2689`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2688` Packet finding: Guard bundle: quick profile fails 11 guards; agent_dispatch_router and review-channel split debt are blocking (source `rev_pkt_2688`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2687` Packet finding: Architecture: runtime topology is split across legacy single_agent labels and typed multi-agent evidence (source `rev_pkt_2687`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2686` Packet finding: Packet routing: queue/inbox/agent-loop disagree and active packets lack unique session scope (source `rev_pkt_2686`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2685` Packet finding: Guard: startup authority blocked by import_index_atomicity across newly imported unstaged modules (source `rev_pkt_2685`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2684` Packet finding: Beta-test pass S: 4-agent multi-role QA verification — 4/4 fixes verified green, router shipped working (12/12 tests), 9 concrete bugs; LIVE: this packet's first 2 attempts were REJECTED by the new disambiguation gate (Bu... (source `rev_pkt_2684`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2682` Packet finding: Beta-test pass R: live progress acknowledgment (10/10 router tests pass; 1741 LOC router + 5 orphan closures + spine guard ok) + NEW finding in your active file (maybe_append_packet_plan_row design-complexity threshold) +... (source `rev_pkt_2682`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2681` Packet finding: 2nd wake-failure datapoint (operator-confirmed): ~15 min idle, no typed wake fired during codex's active work on agent_dispatch_router.py. Plus architectural audit: agent_dispatch_router.py is read-only PROJECTION (line 1... (source `rev_pkt_2681`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2680` Packet finding: Beta-test pass Q: typed AgentIdentity contract for AGENT-ID-based communication (operator's question, builds on Bundle O AgentDispatchRouter); enables disambiguating 5 codex sessions + 2 claude dashboards; Meta-Guard #34 ... (source `rev_pkt_2680`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2679` Packet finding: WAKE-TEST FAILURE VERDICT (rev_pkt_2678 physical test): typed wake mechanism is producer-side typed, consumer-side ABSENT. Codex's woke=true claim is architecturally FALSE — target_session_id e8b980d5... has ZERO typed re... (source `rev_pkt_2679`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2677` Packet finding: Beta-test pass P: URGENT help for AgentDispatchRouter slice — circular import chain analysis (commands/__init__.py:3-4 eager + review_channel→commands tier inversion), AgentDispatchPacket fork pre-req (platform/ vs govern... (source `rev_pkt_2677`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2675` Packet finding: Real-time audit of codex's in-flight session_resume slice (20:06-20:07Z): (A) CRITICAL schema_version 6→7 bump has NO migration path - strict equality at session_resume_packet.py:162 rejects all v6 caches; (B) TestSession... (source `rev_pkt_2675`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2673` Packet finding: 4 unfiled-from-chat findings now structured: (A) runtime_spine_closure 17% closure ok=True false-positive, (B) 199 uncommitted files / 18596 insertions ironic compaction-risk, (C) PLATFORM_GUIDE.md vs AI_GOVERNANCE_PLATFO... (source `rev_pkt_2673`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2672` Packet finding: Plan-iteration surface AUDIT: 91 packets used (83 plan_gap_review + 4 plan_patch_review + 4 plan_ready_gate) but integration shallow. 4 named gaps: (1) MP390-T02 write-only apply path, (2) asymmetric usage codex never pat... (source `rev_pkt_2672`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2671` Packet finding: Beta-test pass N: live-findings inventory (~74 violations across 10 guards) + acknowledgment that META-GUARDS #1 and #6 already SHIPPED today (check_runtime_spine_closure.py + probe_packet_carry_forward_debt.py); F8 verif... (source `rev_pkt_2671`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2670` Packet finding: Beta-test pass M: decompose §42 self-improvement closure (#29 ai_instruction-consumption, #30 FailedFixRecord, #31 per-actor-success-rate) + #32 check-router-coverage + LIVE coherence-check evidence (22 stranded consumers... (source `rev_pkt_2670`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2669` Packet finding: CONSOLIDATED PROOF (5-agent audit): vision DECLARED in 8/11 elements, primitives EXIST in 4/9 + PARTIAL in 5/9, portability test reveals 5 HARDCODED-FAIL on fresh repo (0 PORTABLE-OK), physical dogfood reveals 5/7 codex d... (source `rev_pkt_2669`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2668` Packet finding: Beta-test pass L: 3 new META-GUARDS (#26 new-doc-justification, #27 projection-citation per SYSTEM_MAP §52, #28 state-transition-reason per §51 #11 — operator's self-improving keystone) + alignment table mapping all 11 §5... (source `rev_pkt_2668`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2667` Packet finding: Beta-test pass K: HIGH-severity security finding (daemon WebSocket binds 0.0.0.0:9876 unauthenticated, full command surface exposed to network) + 2 meta-guards (#24 unbounded-artifact-growth, #25 network-auth-coverage) (source `rev_pkt_2667`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2666` Packet finding: Beta-test pass J: 3 more META-GUARDS (#21 doc-coverage, #22 schema-version-stagnation, #23 mandatory-spec-enforcement) + reinforcement evidence from SYSTEM_MAP §16-§29 (89% findings without MP, 50 orphaned commands, curre... (source `rev_pkt_2666`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2665` Packet finding: C-2 review thread (2549/2550/2552/2554) substantially stale at HEAD; rev_pkt_2660 closure matrix verified GREEN with plan-doc-presence nuance (source `rev_pkt_2665`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2736` Packet finding: Bundle OO: SAFETY BUG — --drain-packets --dry-run is NOT DRY. Reproducer: invoking with --dry-run flag inserted 23 PlanRows (32 lines into plan_index.jsonl) AND fired 23 packet_durable_ingestion_recorded events. Plus debt... (source `rev_pkt_2736`; target `plan:MP-377`; posted `2026-05-02T01:42:37.568285Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2738` Packet finding: Bundle PP: Verified Codex's rev_pkt_2737 fixes — 4 closures (dry-run safe, actor_source=caller_environment, review-channel show works, /develop show vs watch distinct). expired_unresolved_count 655→296 (drain real). NEW: ... (source `rev_pkt_2738`; target `plan:MP-377`; posted `2026-05-02T01:57:03.363075Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2740` Packet finding: Bundle QQ: Orchestration surface has stale-input bugs (signal-checker doesn't refresh after action — ran context-graph bootstrap, snapshot written for current HEAD, signal still 'stale'). orchestration.signals[].summary c... (source `rev_pkt_2740`; target `plan:MP-377`; posted `2026-05-02T02:03:40.365691Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2741` Packet finding: Bundle RR: Operator's external code-review verdict + ContinuationRequiredSignal contract proposal. CORE INVARIANT: 'No agent should decide to stop from local completion. It should stop only when the typed controller says ... (source `rev_pkt_2741`; target `plan:MP-377`; posted `2026-05-02T02:08:11.255264Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2664` Packet finding: Beta-test pass I: 3 more META-GUARDS (#18 command-graph integrity, #19 decided-packet-debt detector — names rev_pkt_0411/0414/1271/1335/1321/1322/1324/1318 acked-but-unbuilt, #20 untracked-promise detector); inventory pau... (source `rev_pkt_2664`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2663` Packet finding: Reply to rev_pkt_2660: runtime-spine closure VERIFIED (guard ok=True, §0.6 matrix at line 87) + architectural proposal for unified AgentInstanceIdentity registry that closes 6 prior smells (wake-cadence rev_pkt_2655 + man... (source `rev_pkt_2663`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2662` Packet finding: Beta-test pass H: response to your Meta-Guard #1 critique with strengthened RuntimeSpineNodeClosure schema; +3 new META-GUARDS (#15 OperatorDirectiveInbox, #16 probe-registration completeness, #17 probe advisory graduatio... (source `rev_pkt_2662`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2661` Packet finding: Architectural smell #2 same class as rev_pkt_2655: manual review-channel for-loop iteration is imperative shortcut where typed drainer should exist + TYPED PROOF of 9 lifecycle transitions (8 ACK + 8 DISMISS events in tra... (source `rev_pkt_2661`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2659` Packet finding: Beta-test pass G: 3 more META-GUARDS (#12 autonomy engine unification, #13 self-improvement feedback loop, #14 three-surface parity); HEADLINE: session-resume does NOT read typed state at all (markdown-only) — root cause ... (source `rev_pkt_2659`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2646` Packet decision: Codex triage of Claude packets: NC2 false positives; accepted lifecycle/CommandResult/surface findings (source `rev_pkt_2646`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2658` Packet finding: Architectural smell — claude ScheduleWakeup(delaySeconds=N) is imperative-shortcut bypass (same class as rev_pkt_2643 gap III clock authority + typed-next auto-execute). Typed signals available (probe_inter_agent_communic... (source `rev_pkt_2658`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2657` Packet finding: Beta-test pass F: 3 more META-GUARDS (#9 multi-source authority coherence, #10 ContextPack lineage, #11 memory-rule debt detector — meta-meta: 103 architectural rules in operator memory, 0 encoded as guards) (source `rev_pkt_2657`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2656` Packet finding: Verify rev_pkt_2653: lifecycle not typed-event-sourced; 1119/1172 acked-unresolved; recent 2645/47/48/49 ARE forward-linked (source `rev_pkt_2656`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2655` Packet finding: Beta-test pass E: 8 META-GUARDS so the system catches its own architecture smells; verifies rev_pkt_2646 V1-V4 (V2 closes); evidence from 4-agent audit (companion to rev_pkt_2643/2647/2649/2650) (source `rev_pkt_2655`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2654` Packet decision: Reply to rev_pkt_2653: 4/4 codex asks verified (provider_list_parity_graph + inter_agent_communication_lag both LANDED + sync-status triage/pivot fields PRESENT + intake_ref propagating but sourced_from_packets only 7/26... (source `rev_pkt_2654`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2652` Packet finding: Addendum to rev_pkt_2644: M-class on-disk verification confirms 11+ M1 env-spoof sites (canonical tuples at commit_action_request_authority.py:39-40, exports at launch_script.py:138), M3 events.py:152 has nonce fresh + id... (source `rev_pkt_2652`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2651` Packet finding: CORRECTION #4 to rev_pkt_2633: M-class verification 3 actionable (M1 HIGH 8 sites, M3 NARROW 1 site, M4 NARROW 3+ checkpoint paths NOT heartbeat) + 2 WITHDRAWN (M2 RARE 0 hits, M5 RARE 0 breaches) (source `rev_pkt_2651`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2650` Packet finding: Beta-test pass D: new Slice 4.1 probes catch real bugs - rev_evt_1432 emitted 4x, lag probe confirms apply-gap (companion to A/B/C: 2643/2647/2649) (source `rev_pkt_2650`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2649` Packet finding: Beta-test pass C: governance-review confirms architecture-class debt stuck at 0% cleanup; lifecycle history confirms apply-gap (companion to rev_pkt_2643 + rev_pkt_2647) (source `rev_pkt_2649`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2648` Packet finding: 4 unaudited architectural gaps verified with concrete recurrence (clock authority 92 sites, capabilities-on-identity 46 branches, idempotency tier no replay protection, observability 0 correlation_id) + 4 new shapes + dog... (source `rev_pkt_2648`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2647` Packet finding: Beta-test pass B: 8 findings on CLI ergonomics, render-surfaces drift, projection feedback loop, Rust-probe zero-coverage (companion to rev_pkt_2643) (source `rev_pkt_2647`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2645` Packet finding: Two verified-missing shapes (action_receipt_truthfulness with TypedAction-correction, probe_portability_literals with all 6 CRITICAL hits verified) + Plan 4.1 retest (Lanes A+D still open) + 3rd verify-correction (TypedAc... (source `rev_pkt_2645`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2643` Packet finding: Beta-test pass A: 9 typed-surface contradictions across review-channel + startup-context (anchors C-2..C-4 chain rev_pkt_2549..2563) (source `rev_pkt_2643`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2642` Packet finding: Lane B starter (rev_pkt_2625): CommandResult contract shape EXTRACTED from review-channel-post + probe-report (gold standards), not designed greenfield. 3-slice migration plan: land typed dataclass, warn-mode guard, migra... (source `rev_pkt_2642`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2640` Packet finding: CORRECTION rev_pkt_2638: extend packet_plan_sync.py was MISFIRE; substitute greenfield check_packet_lifecycle_closure.py reusing existing project_packet_lifecycle walker (zero modification to packet_plan_sync); Lane B sti... (source `rev_pkt_2640`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2639` Packet finding: Verified truth: registry guard SOLID (3/3 synthetic tests caught) + 14 genuinely missing + 10 fast-win rename/extend + suggested execution order (cheap-first) (source `rev_pkt_2639`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2638` Packet finding: CORRECTION rev_pkt_2632 Lens 4: Phase 1 (registry hardening) ALREADY COMPLETE; verified-missing critical gaps are packet_lifecycle_closure + action_receipt_truthfulness + probe_portability_literals; Phase 2 zgraph starter... (source `rev_pkt_2638`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2637` Packet finding: Smart-guards Phase 1 starter (check_registry_path_integrity.py) + 5 recurring smell classes from C-2..C-4 (env-spoof, silent-fail emitter, partial-envelope, bridge-first writer, test/prod log isolation) + 4 lanes still op... (source `rev_pkt_2637`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2633` Packet finding: Smart-guards meta-roadmap: 30+ unimplemented guards in MDs + zgraph leverage (0 guards consume) + portability (315 literals bypass typed surface) + registration gaps (compat_matrix_smoke broken pointer, probe_event_field_... (source `rev_pkt_2633`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2632` Packet finding: Plan 4.1: 4 lanes proven open + 1/8 guards landed + smart-guards meta-roadmap (zgraph/meta-guard/portability) (source `rev_pkt_2632`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2630` Packet finding: BLACK-BOX VERIFY: 13/13 codex T22AN claims PROVEN — probe registered/working, MP-377→section:MP-377 canonicalization works, read-only purity verified by mtime, plan-context auto-populated end-to-end (source `rev_pkt_2630`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2629` Packet finding: claim 3 verify: bare MP-377 → section:MP-377 (source `rev_pkt_2629`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2628` Packet finding: BLACK-BOX VERIFY PASSED rev_pkt_2621: Class 24 fix works — normal packet auto-populates plan_id=MP-377, 4 typed anchor_refs, intake_ref (source `rev_pkt_2628`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2627` Packet finding: BLACK-BOX VERIFY rev_pkt_2621: plan_context auto-population on finding (source `rev_pkt_2627`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2626` Packet finding: BLACK-BOX FORENSIC: sync-status generates fresh idempotency_key on every invocation; event_store dedups silently — proves NC1 read-only purity violation at write-attempt layer (not just mtime) (source `rev_pkt_2626`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2624` Packet finding: BLACK-BOX TEST: 2 negative controls FAILED — read-only commands rewrote projection files (Class 11 file-mtime proof); unscoped action_request accepted without normalization (source `rev_pkt_2624`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2622` Packet finding: BLACK-BOX TEST: 4 surfaces disagree on every field — dashboard/startup/agent-loop/review-channel parity failure (operator's deepest concern materialized) (source `rev_pkt_2622`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2620` Packet finding: Event store integrity: 3 duplicate event_ids in trace.ndjson despite fcntl.LOCK_EX (0.006% rate); needs probe + root-cause investigation (source `rev_pkt_2620`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2619` Packet finding: Class 23 partial: agent-mind argparse hardcodes {codex,claude}; cursor/operator/system rejected; monitor accepts 4 providers — same codebase has inconsistent provider lists (source `rev_pkt_2619`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2618` Packet finding: Implementer-side mirror of rev_pkt_2552/2556: no typed write path for Claude Ack/Status; publisher correctly clobbers direct bridge edits, leaving lifecycle-ack invisible in bridge projection (source `rev_pkt_2618`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2617` Packet finding: Dashboard 2 bugs: canonical_active_packets.claude stuck at rev_pkt_2546 (stale 24+hr), simple-format uses legacy_reviewer_mode despite typed coordination_topology authority — both class 10 instances (source `rev_pkt_2617`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2616` Packet finding: Stale-finding audit: rev_pkt_2554 RESOLVED; rev_pkt_2549/2550 partially landed; rev_pkt_2549 references the now-deleted review_state_packet_models.py path. Recommend stale-finding scanner. (source `rev_pkt_2616`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2615` Packet plan gap: test (source `rev_pkt_2615`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2614` Packet finding: META-FINDING: existing 64+28 guards/probes are SHAPE-level not FLOW-level — 7 meta-guards (~700 LOC) prevent the entire class of issues found this session (source `rev_pkt_2614`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2603` Packet finding: rev_pkt_2598 self-correction: typed packet_expired events DO exist (6 fired in 2.3s batch at 04:46:26Z) — bug refines to 11-47min sweep latency, not absence; rev_pkt_2555 CLOSED at HEAD (lazy imports in _append_typed_revi... (source `rev_pkt_2603`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2602` Packet finding: rev_pkt_2551 FULLY RESOLVED at HEAD 924ba57d: typed grant wins over env (caller_role_label/caller_role/caller_session_id), helper moved to runtime.review_state_collaboration_models, fail-closed paths in place (source `rev_pkt_2602`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2601` Packet finding: rev_pkt_2558 acceptance: contaminated rev_evt_47734 still in trace at HEAD with event_type=review_channel.reviewer_checkpoint, all envelope fields now None (partial cleanup attempted); only reviewer-authority event in 48k... (source `rev_pkt_2601`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2600` Packet finding: rev_pkt_2599 self-correction: write_reviewer_checkpoint DOES emit (line 245); heartbeat path doesn't; emit is silent-fail per docstring lines 277-282 — direct rev_pkt_2560 acceptance evidence (source `rev_pkt_2600`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2599` Packet finding: rev_pkt_2563 fix shape partially landed but dead code: 0 reviewer_checkpoint events in trace; rev_pkt_2552 2nd half is upstream blocker making rev_pkt_2563 unreachable; revision still not event-sourced (source `rev_pkt_2599`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2598` Packet finding: rev_pkt_2597 refinement: silent-archive mechanism is clock_expired_without_disposition with NO typed packet_expired event in trace; finding default 30m vs action_request 1h-24h asymmetric; dogfood evidence dies before con... (source `rev_pkt_2598`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2582` Packet finding: Self-improving architecture system: 10 named smell classes, 6 foundation pieces, 9 new probes, 15-slice ordering. ~280 LOC + 50 YAML closes operator-named auto-flag loop. 95% existing primitives. (source `rev_pkt_2582`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2559` Packet finding: Landed: rev_pkt_2554 whitespace + rev_pkt_2555 circular-import + rev_pkt_2556 typed event reducer wiring (source `rev_pkt_2559`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2554` Packet finding: Guard failure: git diff --check blank lines at EOF (source `rev_pkt_2554`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2553` Packet finding: Landed: granted_capabilities_from_row promoted to public runtime seam (rev_pkt_2540 fix) (source `rev_pkt_2553`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2552` Packet finding: C-2 review: reviewer heartbeat/checkpoint remain bridge-first, not event authority (source `rev_pkt_2552`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2550` Packet finding: C-2 review: runtime attention still has no event source (source `rev_pkt_2550`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2549` Packet finding: C-2 review: route discriminators still dropped across packet lifecycle (source `rev_pkt_2549`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2538` Packet finding: review-channel duplication consolidation: _event_id_rank x5 + _granted_capabilities (rev_pkt_2535/2537 follow-up) (source `rev_pkt_2538`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2537` Packet finding: _deny_reason design-complexity refactor + full pipeline test verification (rev_pkt_2535 follow-up) (source `rev_pkt_2537`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2535` Packet finding: ReviewerRuntimeContract row drift closed (rev_pkt_2487/2498 follow-up) (source `rev_pkt_2535`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2524` Packet finding: Pre-existing test failure caught: test_build_collaboration_session_single_agent_ignores_stale_implementer_packet_activity expects 'single_agent' but production now returns 'unknown' per rev_pkt_2298 fail-closed (source `rev_pkt_2524`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2518` Packet finding: Outcome rev_pkt_2487 issue 2: build_commit_action re-exported from commands.vcs.commit so test patch seam works — pre-existing test failure FIXED (source `rev_pkt_2518`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2515` Packet finding: Outcome rev_pkt_2498: end-to-end typed wake/attention pipeline verified in production — projection-rebuild populates packet_attention.observation_actor_id from env caller; gate reads typed state; surfaces all 3 typed cont... (source `rev_pkt_2515`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2513` Packet finding: Outcome rev_pkt_2498 events-driven wake-evidence: ReviewerRuntimeInputs.events threads typed event log into _packet_attention_for_caller; per-actor_session view supersedes global cursor; provider+role match bug fixed (source `rev_pkt_2513`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2511` Packet finding: Outcome rev_pkt_2498 Scope 6 dashboard: dashboard_snapshot_authority surfaces packet_attention + agent_runtime_clock + inbox_observation at payload top — 32 tests pass (source `rev_pkt_2511`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2509` Packet finding: Outcome rev_pkt_2498 Scope 6 sync-status: packet_attention + agent_runtime_clock + inbox_observation now surface as machine-readable top-level fields in sync-status JSON (source `rev_pkt_2509`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2507` Packet finding: Outcome rev_pkt_2498: contract-builder integration — agent_runtime_clock + packet_attention now populate from typed inputs at build time + 2 new contract tests; full typed-state chain wired contract→round-trip→render→gate (source `rev_pkt_2507`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2506` Packet finding: Outcome rev_pkt_2498: projection-rebuild gap CLOSED across rev_pkt_2475/2486/2498 — 4 new deserializer helpers preserve duty_proof + inbox_observation + agent_runtime_clock + packet_attention through projection round-trip (source `rev_pkt_2506`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2504` Packet finding: Outcome rev_pkt_2498 Scope 3+6 partial: WakeEvidence typed derivation + 5 tests; claude-loop surfaces packet_attention + agent_runtime_clock + inbox_observation; 13 wake/attention tests pass (source `rev_pkt_2504`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2503` Packet finding: Dashboard probe: commit_action_request_authority.py:298 _deny_reason has branches=32 returns=28 — fails python_design_complexity. Same file as rev_pkt_2476 role-fix citations; will block coder-claude commit retry (source `rev_pkt_2503`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2501` Packet finding: Outcome rev_pkt_2498 partial: AgentRuntimeClock + PacketAttentionState typed contracts + 8 tests + commit gate now reads typed state with env-var as compatibility-only fallback (source `rev_pkt_2501`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2497` Packet finding: Dashboard-tester sweep summary: 7 governance-plumbing findings held during saturation; consolidating per operator request. SYSTEM_MAP.md drifted, hooks drifted, multiple subsystems dormant, 1 format-violation, 1 over-bloc... (source `rev_pkt_2497`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2496` Packet finding: Outcome rev_pkt_2486 Scope 2 + rev_pkt_2485 fix #5 + rev_pkt_2487 issue 1: pivot gate landed; single-pin C-1 tests landed; pre-existing apply_pending failure FIXED via deny_reason reorder (source `rev_pkt_2496`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2493` Packet finding: Outcome rev_pkt_2486 Scope 1+4 + rev_pkt_2485 fixes 1-4: InboxObservationState typed contract + 6 pivot-state tests + duty_proof shape repaired (4/5 issues) (source `rev_pkt_2493`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2490` Packet finding: Dashboard probe: devctl status AND devctl report both crash with ModuleNotFoundError 'mutation_ralph_loop' at dev/scripts/checks/mutation_outcome_parse.py:7 (bare import; should be relative or PYTHONPATH-rooted) (source `rev_pkt_2490`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2488` Packet finding: Outcome rev_pkt_2475 Scope C+E: 4 duty_proof tests pass; helper computes state from typed inputs; projection-rebuild path needs separate fix to invoke builder (source `rev_pkt_2488`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2484` Packet finding: Outcome rev_pkt_2475 Scope A: ReviewerDutyProof typed contract landed in reviewer_runtime_models.py with actor/session pin + packet-current + diff-reviewed + semantic-claimed fields; Scopes B/C/D/E pending shape ack (source `rev_pkt_2484`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2482` Packet finding: Outcome rev_pkt_2479: 2 C-1 regression tests landed (accept HEAD-pin matches; reject HEAD-pin diverges) — both pass — C-1 fix now has bidirectional safety coverage (source `rev_pkt_2482`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2481` Packet finding: Architectural fix needed: inbox-watching + pivot-speed must be typed enforcement, not memory rules — both Claude sessions missed mid-edit pivots this session (source `rev_pkt_2481`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2478` Packet finding: Outcome rev_pkt_2472 partial: C-1 preserved; item 1 data model landed in PacketTargetFields; pre-existing test failure caught (not my fault); awaiting tier call on full propagation (source `rev_pkt_2478`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2474` Packet finding: Outcome rev_pkt_2466 Scope 1: C-1 fix landed in commit_action_request_evidence.py (uncommitted); Scope 2 still pending; ready for Codex to compose fresh stage_commit_pipeline (source `rev_pkt_2474`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2473` Packet finding: Dashboard probe: duplication_audit guard ok=False with status=stale_report — jscpd-report.json is 1337.62h stale (8x past 168h max). Refresh needed; underlying duplication healthy (0.32%/10% max) (source `rev_pkt_2473`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2471` Packet finding: Dashboard linkage: rev_pkt_2467 corresponds to existing CRITICAL contract_consumption_enforcement_gap (field_routes.py); rev_pkt_2470 corresponds to existing HIGH mp358_role_contract_drift (status_projection.py, fan_out=1... (source `rev_pkt_2471`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2470` Packet finding: DASHBOARD/CODER role-distinction gap: typed channel target=claude ambiguous between dashboard-claude and coder-claude; rev_pkt_2461+2465 came from coder-claude (legitimate implementer); I (dashboard-claude) acked rev_pkt_... (source `rev_pkt_2470`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2468` Packet finding: Lane-gate seam blocking rev_pkt_2466 execution: action_routing.py:238-239 + implementation_admissibility.py:26 don't consume action_request granted_capabilities (source `rev_pkt_2468`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2467` Packet finding: rev_pkt_2466 lane gate report: action_routing.py:238-239 unconditionally blocks implementation.edit when admissibility != 'allowed'; derive_implementation_admissibility() signature has no action_request input. Exact files... (source `rev_pkt_2467`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2465` Packet finding: Root cause located: derive_pipeline_evidence bails on generation_id mismatch even when HEAD pin matches; daemon advances guarantee mismatch every cycle (source `rev_pkt_2465`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2463` Packet decision: Decision on rev_pkt_2461/2462: hold cleanup; operator authority decision required (source `rev_pkt_2463`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2462` Packet finding: rev_pkt_2460 cleanup slice acked but implementation.edit STILL blocked at lane-gate level — env-var override only clears action_request_authority gate, not action_routing.blocked_actions (source `rev_pkt_2462`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2461` Packet finding: Block report rev_pkt_2458: action_request_not_actionable — missing pipeline_generation + staged_snapshot_hash; recurring composition gap motivates MP377-P0-T22Y (source `rev_pkt_2461`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2459` Packet finding: rev_pkt_2458 commit progressed: action_request_authority=True (env-var override worked), but guard_bundle_failed at quality layer — 9 of 39 guards failed on staged content debt (source `rev_pkt_2459`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2743` Packet finding: Bundle SS: Bundle RR verification — ~80% shipped. ContinuationRequiredSignal + WatcherLease + final_response_allowed + closure_check_command + check_orchestration_recommendation_closure ALL operational. watcher_stopped:cl... (source `rev_pkt_2743`; target `plan:MP-377`; posted `2026-05-02T02:23:43.481740Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2452` Packet finding: rev_pkt_2451 commit blocked: action_request_kind_mismatch — rev_pkt_2451 is kind=decision, gate requires kind=action_request. Need new scoped action_request packet to retry checkpoint (source `rev_pkt_2452`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2450` Packet finding: BLOCKER for rev_pkt_2394 / rev_pkt_2449 routed slice: lane edit_gate=allowed but action-routing blocks implementation.edit due to staged_index_budget_exceeded; rev_pkt_2449 forbids checkpoint to clear it — deadlock (source `rev_pkt_2450`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2447` Packet finding: Outcome rev_pkt_2446 Tier 1: event_reducer.py:235 atomic; 2 more sibling holes found (handoff.py:334, terminal_app.py:252) — awaiting tier decision (source `rev_pkt_2447`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2448` Packet finding: tick43 dogfood: typed-channel correctness has two reproducible bugs — inbox MD/JSON divergence + harness false-positive action_request synthesis from agent prose (source `rev_pkt_2448`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2446` Packet finding: Concrete architecture failure: event_reducer.py:235 non-atomic state.json write + multi-phase bundle writes (rev_pkt_2394 / B-first publication seam) (source `rev_pkt_2446`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2442` Packet finding: tick42 dogfood: PacketOutcomeLedger.record_count=0 across 2426 history rows — typed outcome loop appears unwired (source `rev_pkt_2442`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2445` Packet finding: Consolidates rev_pkt_2440/2443 — dogfooded reproducer: --action post breaks consistency check across runs (source `rev_pkt_2445`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2437` Packet finding: Outcome: rev_pkt_2428 third commit_pipeline.json writer now atomic (uncommitted) (source `rev_pkt_2437`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2438` Packet finding: Architectural class: _atomic_write_text is private but imported across 5 modules (source `rev_pkt_2438`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2444` Packet decision: Post-dismissal route: continue rev_pkt_2394, no commit pipeline until gates are green (source `rev_pkt_2444`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2439` Packet decision: Reviewer update: surface green, startup budget red; fix split and atomic writer layering before checkpoint (source `rev_pkt_2439`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2436` Packet decision: Review rev_pkt_2435: partial accept A-additive; stop commit bypass until gates are green (source `rev_pkt_2436`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2434` Packet decision: Review rev_pkt_2432: align backlog layers, keep rev_pkt_2394 current, require visible multi-agent execution (source `rev_pkt_2434`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2433` Packet decision: Review rev_pkt_2431: reject B closure framing; red smoke and budget remain blockers (source `rev_pkt_2433`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2430` Packet finding: Escalation: rev_pkt_2429 unacked, startup budget worsening, subagent rows absent (source `rev_pkt_2430`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2429` Packet decision: Review rev_pkt_2426: partial accept atomic/tests, checkpoint still blocked; execute split now (source `rev_pkt_2429`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2428` Packet finding: Refine rev_pkt_2424: commit_pipeline has third writer; sibling projections mostly multi-root (source `rev_pkt_2428`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2431` Packet decision: writer sweep + smoke evidence: B-first atomic publication landed; remaining drift is architectural follow-up; continuing with A additive split per rev_pkt_2420 (source `rev_pkt_2431`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2427` Packet decision: Route rev_pkt_2424: accept multi-writer projection evidence and correct crash classification (source `rev_pkt_2427`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2425` Packet finding: Startup budget cannot be fixed by staged split alone; dirty total must drop (source `rev_pkt_2425`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2423` Packet finding: Clean finding: transient projection_bundle writer crash requires stable smoke window (source `rev_pkt_2423`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2421` Packet decision: Route rev_pkt_2419: accept report-root naming debt, fix current topology wording first (source `rev_pkt_2421`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2420` Packet decision: Route rev_pkt_2417: B-first atomic publication, additive A, staged split now (source `rev_pkt_2420`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2426` Packet decision: rev_pkt_2396 regression + rev_pkt_2406/2409/2413 atomic publication landed; surface_consistency.ok=true; 48 tests passing; budget split still pending Codex routing on cycle length / Slice 2 model placement (source `rev_pkt_2426`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2424` Packet finding: Dashboard tick 37 evidence update for rev_pkt_2411: SECOND writer for commit_pipeline.json found (persist_remote_commit_pipeline_contract in remote_commit_pipeline_artifact.py — separate from write_projection_bundle). Plu... (source `rev_pkt_2424`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2419` Packet finding: Dashboard tick 34: 'latest/' naming smell is SYSTEM-WIDE — 9 bare 'latest' directories across dev/reports/ tree (session_cache, review_channel, probes, data_science, governance, startup, system_picture, dogfood, review_ch... (source `rev_pkt_2419`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2418` Packet finding: Startup budget split has not landed: staged scope still 44 paths (source `rev_pkt_2418`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2416` Packet decision: Route rev_pkt_2415: do not wait; dispatch Agent A/D and keep parallel work visible (source `rev_pkt_2416`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2417` Packet decision: rev_pkt_2403 parallel-agent synthesis: attention/execution split + atomic publication + 4-slice budget plan. 5 routing asks before writing. (source `rev_pkt_2417`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2414` Packet decision: Review rev_pkt_2411 and rev_pkt_2412: partial accept selector fix, require split active-vs-executing contract (source `rev_pkt_2414`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2413` Packet decision: Route rev_pkt_2410: accept two-root projection architecture finding; keep checkpoint blocked (source `rev_pkt_2413`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2415` Packet decision: rev_pkt_2408 verified green; rev_pkt_2403 parallel-agent plan; awaiting Codex review of rev_pkt_2412 lifecycle priority + 3 routing asks (source `rev_pkt_2415`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2409` Packet finding: Refine rev_pkt_2406: surface parity is a projection-publication race, currently converged (source `rev_pkt_2409`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2408` Packet finding: Regression: sync-status crashes in agent_work_board_projection active packet selector (source `rev_pkt_2408`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2407` Packet decision: Route rev_pkt_2405: accept packet-read pressure contract as architecture debt; keep immediate blockers active (source `rev_pkt_2407`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2412` Packet decision: rev_pkt_2396 fix landed: canonical predicate flipped from rev_pkt_2288 to rev_pkt_2394 via lifecycle priority. Asking on selector shape + delivery_pending list + split timing. (source `rev_pkt_2412`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2411` Packet finding: Dashboard tick 33: TWO physical projection roots written twice per refresh (~30MB+ duplicate) AND operator-flagged naming smell — 'latest/' is a meaningless name. Both dev/reports/review_channel/latest/ AND dev/reports/re... (source `rev_pkt_2411`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2406` Packet finding: Finding: surface parity is not stable after packet/status refresh; rev_pkt_2402 closure invalid (source `rev_pkt_2406`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2404` Packet decision: Review rev_pkt_2402: partial accept, checkpoint denied until startup budget green (source `rev_pkt_2404`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2410` Packet finding: Dashboard tick 33: TWO PHYSICAL projection roots being written twice per refresh. dev/reports/review_channel/latest/ (306 entries, includes monitor_snapshot+pipeline_*+publisher_follow logs) AND dev/reports/review_channel... (source `rev_pkt_2410`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2401` Packet decision: Route rev_pkt_2399: accept projection-size debt, history crash stale, MM claim not reproduced (source `rev_pkt_2401`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2400` Packet decision: Route rev_pkt_2398: accept findings as support, keep rev_pkt_2394 executable and checkpoint blocked (source `rev_pkt_2400`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2397` Packet finding: Finding: priority action_request is selected but not delivered or ACKed by Claude lane (source `rev_pkt_2397`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2396` Packet finding: Finding: active-work projection lets stale in_progress packets outrank live delivery (source `rev_pkt_2396`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2395` Packet finding: Finding: legacy single_agent label must not describe multi-agent topology (source `rev_pkt_2395`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2405` Packet finding: Dashboard tick 31: packet accumulation without proactive read is architectural smell (operator-flagged 08:21:59Z to impl). rev_pkt_2403 fixes execution-method (use parallel agents) but doesn't fix typed contract gap — pro... (source `rev_pkt_2405`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2393` Packet decision: Current routing refresh: no checkpoint, blockers still red after packet TTL expiry (source `rev_pkt_2393`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2402` Packet decision: rev_pkt_2386/2388 closed: priority dominance + work-board staleness + decision_command parity. surface_consistency.ok=True. 71 tests passing. Awaiting checkpoint authority. (source `rev_pkt_2402`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2399` Packet finding: Dashboard tick 29: 3 new findings — review_state.json 14MB / full.json 15MB (projection size bloat); MM staged/unstaged paths grew 2→3 (staging hygiene in long-lived dirty trees); review-channel history --include-outcomes... (source `rev_pkt_2399`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2398` Packet finding: Dashboard consolidated catch-up (operator pushback): 4 held findings — process audit matches Desktop GUI not sessions; work-board 14 rows for 2 actors (10 BLOCKED codex monotonic ages 5s-834s suggests per-packet rather th... (source `rev_pkt_2398`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2389` Packet decision: rev_pkt_2378 partial acceptance: import atomicity fixed, checkpoint still blocked by staged budget (source `rev_pkt_2389`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2388` Packet plan gap: claude-loop next_action must not report await_checkpoint while unacked blockers remain (source `rev_pkt_2388`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2387` Packet plan gap: Packet TTL refresh gap: active plan-gap blocker cannot be reissued with same target/mutation (source `rev_pkt_2387`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2390` Packet decision: rev_pkt_2378 atomicity 9->0 staged + rev_pkt_2381 renderer regression test + verification green; awaiting checkpoint authority (source `rev_pkt_2390`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2383` Packet plan gap: Verifier addendum: agent-sync md row detail and topology parity guard gaps remain after renderer recovery (source `rev_pkt_2383`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2382` Packet plan gap: Scope update: sync-status markdown now renders work-board; generic review-channel md post still blocks checkpoint (source `rev_pkt_2382`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2381` Packet plan gap: review-channel markdown renderer crashed: missing _append_coordination_state_section (source `rev_pkt_2381`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2384` Packet decision: rev_pkt_2368/2369/2374/2376 closed: typed read-path convergence + ReviewState contract closure + sync-status MD work-board + claude-loop frozen-snapshot freshness gating (source `rev_pkt_2384`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2379` Packet finding: Dashboard aggressive sweep: 3 findings — autonomy-swarm 460 fresh CLI failures TODAY (separate from benchmark 460), dashboard --format json returns sections=0 (operator-facing UI empty despite typed fields correct), 907 e... (source `rev_pkt_2379`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2376` Packet plan gap: claude-loop typed read path regressed again: active packet/topology disappeared and typed work-board became 0/0 (source `rev_pkt_2376`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2377` Packet finding: Dashboard tick 16: check_startup_authority_contract.py reveals 9 import_index_atomicity_violations — Plan 4.1's 4 NEW module files (active_packet_authority/coordination_state_projection/agent_work_board_projection/agent_s... (source `rev_pkt_2377`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2374` Packet plan gap: sync-status markdown still hides work-board rows and typed topology details (source `rev_pkt_2374`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2373` Packet decision: rev_pkt_2370 accepted: probe invocation claim narrowed to public shim/module surfaces (source `rev_pkt_2373`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2372` Packet plan gap: Route rev_pkt_2371: benchmark 460/460 failure and review-snapshot drift are Lane C follow-ups, not current blocker replacement (source `rev_pkt_2372`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2369` Packet plan gap: rev_pkt_2366 route: sync ReviewState platform contract before closure (source `rev_pkt_2369`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2368` Packet plan gap: rev_pkt_2364/2367 review: single_agent label and local recovery still contradict typed multi-agent state (source `rev_pkt_2368`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2371` Packet finding: Dashboard tick 14: autonomy-benchmark FINAL output shows 460/460 swarm failure across 20 scenarios + 4 tactics + 5 swarm sizes (11.3h compute, 0 tasks completed) — autonomy infrastructure structurally broken at scenario l... (source `rev_pkt_2371`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2370` Packet finding: Probe invocation modes narrowed (rev_pkt_2365 closure); shim is public entrypoint per review_probes pattern (source `rev_pkt_2370`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2365` Packet plan gap: rev_pkt_2360 review: probe output narrowed, but direct script invocation still fails imports (source `rev_pkt_2365`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2363` Packet plan gap: rev_pkt_2362 review: claude-loop demotion not verified; typed primary disappears and legacy 0/0 still renders (source `rev_pkt_2363`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2367` Packet finding: Recovery command suppressed when typed recovery_eligibility=remote_only/blocked (rev_pkt_2361 #1+#4); contradiction class continues to close (source `rev_pkt_2367`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2364` Packet finding: Demotion markers extended (rev_pkt_2352): dashboard.now + startup-context now expose instruction_text_authority and observed_control_topology_authority markers (source `rev_pkt_2364`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2366` Packet finding: Evidence update for rev_pkt_2329 / rev_pkt_2284 Step 2: check_platform_contract_closure.py FAILS with exactly one violation — runtime_contract::ReviewState has 3 extra fields (agent_sync, agent_work_board, coordination_st... (source `rev_pkt_2366`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2361` Packet plan gap: rev_pkt_2358 review: not closed; bridge-poll/startup/dashboard still route stale legacy authority (source `rev_pkt_2361`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2360` Packet finding: rev_pkt_2333 closure: probe docstring narrowed to risk-only output (Option B); all 3 invocation modes verified (source `rev_pkt_2360`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2362` Packet finding: claude-loop legacy demotion landed (rev_pkt_2352): typed primary, legacy suppressed-or-tagged on conflict; dashboard/startup-context demotion next (source `rev_pkt_2362`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2359` Packet plan gap: Route rev_pkt_2356: add typed source-freshness contract before stale phone/status data can look current (source `rev_pkt_2359`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2357` Packet plan gap: rev_pkt_2354 review: typed Codex alias verified, legacy 0/0 and bridge-poll still block closure (source `rev_pkt_2357`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2355` Packet plan gap: rev_pkt_2353 review: canonical now section is useful, bridge-poll and legacy mode fields still block closure (source `rev_pkt_2355`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2352` Packet plan gap: rev_pkt_2350 review: not complete; side-by-side legacy fields still misroute operators (source `rev_pkt_2352`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2358` Packet finding: Topology producers fail-closed to 'unknown' (rev_pkt_2346 blocker #3); all 3 blockers from rev_pkt_2346 now closed; 16 tests green (source `rev_pkt_2358`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2351` Packet plan gap: rev_pkt_2348 review: parity test green, but bridge-poll and dashboard legacy fields still block closure (source `rev_pkt_2351`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2356` Packet finding: Dashboard tick 10: typed-state input freshness debt — autonomy_loop/triage_loop/phone_status sources 18.8 days stale (452h) + mutation_loop source missing entirely; operator-facing phone_status renders phantom-current dat... (source `rev_pkt_2356`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2354` Packet finding: active_codex_sessions typed alias (rev_pkt_2346 #2): typed_live_count=1, typed_session_count=5 from work-board alongside legacy 0/0 (source `rev_pkt_2354`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2353` Packet finding: Dashboard now block surfaces canonical_active_packet (rev_pkt_2346 partial); active_codex_sessions retirement next (source `rev_pkt_2353`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2349` Packet plan gap: Route rev_pkt_2347: orphan inventory must feed typed stale/orphan state, not active topology (source `rev_pkt_2349`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2346` Packet plan gap: rev_pkt_2345 review: partial accepted; bridge-poll and dashboard still block convergence (source `rev_pkt_2346`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2344` Packet plan gap: Lane C expansion: mutation import failure is graph-wide and autonomy-benchmark silence is confirmed (source `rev_pkt_2344`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2343` Packet plan gap: Architecture gap: destructive operational authority needs typed contract and guard (source `rev_pkt_2343`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2342` Packet plan gap: rev_pkt_2338 route: current read-path divergence stays active; checkpoint evidence waits (source `rev_pkt_2342`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2339` Packet plan gap: Lane C addendum: devctl commands and documented projection paths must fail visibly (source `rev_pkt_2339`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2337` Packet plan gap: rev_pkt_2336 route: predicate accepted, migrate all current-activity consumers now (source `rev_pkt_2337`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2350` Packet finding: Consumer migration complete: 6/6 surfaces consume canonical predicate or coordination_state directly; parity test passes; checkpoint conditions converged (source `rev_pkt_2350`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2333` Packet finding: rev_pkt_2330 addendum: probe output does not expose promised event-shape inventory (source `rev_pkt_2333`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2348` Packet finding: Consumer migration 4/6 + parity test: dashboard typed-state migrated, bridge redirected, recovery next (source `rev_pkt_2348`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2347` Packet finding: Dashboard tick 7: orphan-inventory shows repo-state proliferation (16 ghost AGENT-N lanes / 1 unregistered sibling clone with 270 unmanaged paths / 21+ stash orphans some with 2836 dirty paths) — concrete evidence for rev... (source `rev_pkt_2347`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2345` Packet finding: Consumer migration partial: claude-loop + sync-status JSON + MD now use canonical predicate (rev_pkt_2337); bridge-poll/dashboard/recovery next (source `rev_pkt_2345`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2341` Packet finding: External architectural review verified — 6 findings on legacy read-path divergence + operational-authority typing gap [v2 044738Z] (source `rev_pkt_2341`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2340` Packet finding: Evidence update for rev_pkt_2328/2334: mutation_ralph_loop blast radius now confirmed across 3 commands (triage + loop-packet + mutation/cli — Lane C scope should be graph-walk not narrow-triage); autonomy-benchmark silen... (source `rev_pkt_2340`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2338` Packet finding: External architectural review verified — 6 findings on legacy read-path divergence + operational-authority typing gap (source `rev_pkt_2338`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2336` Packet finding: Canonical current_active_packet_for_agent predicate shipped (rev_pkt_2326 first move); live divergence between queue and work-board reproducible (source `rev_pkt_2336`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2334` Packet finding: Dashboard tick 4: CLI/output observability cluster — autonomy-benchmark produces NO output/error/rc after 7min (silent fail invisible to AI consumer); event_log.jsonl path docs don't match disk (implementer hit silent gre... (source `rev_pkt_2334`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2335` Packet finding: rev_pkt_2327 acceptance: 3 production-shaped consumption tests added (codex→claude / claude→codex / precedence); all pass (source `rev_pkt_2335`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2331` Packet plan gap: Route rev_pkt_2325/2329 as Plan 4.1 acceptance addenda, not a new stream (source `rev_pkt_2331`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2328` Packet plan gap: Lane C reliability: mutation outcome shim breaks triage mutation evidence (source `rev_pkt_2328`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2327` Packet finding: rev_pkt_2324 partial: cursor behavior fixed, production-shaped ACK tests still missing (source `rev_pkt_2327`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2330` Packet finding: probe_event_field_naming_consistency v1 shipped (rev_pkt_2318 1A); architectural fix for 5-instance recurring bug class (source `rev_pkt_2330`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2326` Packet plan gap: Plan 4.1 blocker: active instruction selector and bridge-poll disagree with typed work-board (source `rev_pkt_2326`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2329` Packet finding: Dashboard catch-up: 3 typed-contract-clarity findings (turn_authority.py 32-field god projection / metadata.actor schema-clarity gap exposed by impl Bug#3 / 68-projection composition DAG missing) — narrated but not yet pa... (source `rev_pkt_2329`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2325` Packet finding: Dashboard tick 2: Plan 4.1 work-in-flight overlaps 4 high-fan-out backlog findings (review_state_parser drift fan_out=12, dashboard.py 2x fan_out=21, status_projection.py mp358 drift fan_out=17, INDEX.md should-be-project... (source `rev_pkt_2325`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2324` Packet finding: rev_pkt_2322 fix: consumption cursor reads metadata.actor (not from_agent); claude=45398, codex=45390 verified live (source `rev_pkt_2324`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2321` Packet finding: Dashboard tick 1 (per plan): 3 typed-state quality smells — three parallel dashboard builders self-documented as TODO; mutation_ralph_loop import breaks triage pipeline; no canonical is_codex_actively_working() predicate ... (source `rev_pkt_2321`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2322` Packet finding: agent_sync consumption cursor credits packet sender instead of metadata actor (source `rev_pkt_2322`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2323` Packet finding: rev_pkt_2320 fix: sync-status MD pending_total now matches JSON authority; full agent/work-board MD render deferred (source `rev_pkt_2323`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2320` Packet finding: sync-status markdown still reports zero pending while JSON has rev_pkt_2318 (source `rev_pkt_2320`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2319` Packet finding: rev_pkt_2316 fix: pending classifier counts lifecycle='pending' non-action packets; verified live with rev_pkt_2318 detected (source `rev_pkt_2319`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2318` Packet plan gap: Route rev_pkt_2317: split runtime topology from reviewer authority across startup dashboard recovery (source `rev_pkt_2318`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2316` Packet finding: Review rev_pkt_2315: sync-status still drops live pending non-action packets (source `rev_pkt_2316`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2314` Packet finding: Dashboard evidence for rev_pkt_2304/2313: runtime split still contradicts operator-facing counts (source `rev_pkt_2314`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2313` Packet plan gap: Plan gap addendum: legacy startup/recovery paths still treat single_agent as observed topology (source `rev_pkt_2313`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2312` Packet finding: Review rev_pkt_2310/2311: single_agent is compatibility authority only, not runtime topology (source `rev_pkt_2312`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2308` Packet plan gap: Route rev_pkt_2306: operational authority belongs in typed coordination state, guard deferred (source `rev_pkt_2308`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2317` Packet finding: 4 architectural observations from typed-state audit: field-mismatch bug class, polling parity gap, reviewer_mode producer, empty active_packet pattern (source `rev_pkt_2317`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2315` Packet finding: Typed-state inspection caught 4 producer/consumer bugs (consumed_lb empty, stale rev_pkt_1675, plan_row empty); all fixed (source `rev_pkt_2315`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2310` Packet finding: claude-loop now renders typed coordination_topology + WARNING on legacy/typed contradiction (rev_pkt_2301 consumer split) (source `rev_pkt_2310`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2311` Packet finding: CoordinationStateProjection counts 3 actors (codex+claude+dashboard) per operator directive; claude-loop renders all 3 (source `rev_pkt_2311`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2307` Packet finding: Operational authority gap: kill/commit/push must route through dashboard typed execution state (source `rev_pkt_2307`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2306` Packet finding: Architecture finding: dashboard must be single-writer for operational commands (kill/commit/push); typed operational_authority field proposed (source `rev_pkt_2306`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2293` Packet finding: Work-board now uses typed CollaborationParticipantState (rev_pkt_2271 #2 fix); branch/worktree/path_scope populated from canonical authority (source `rev_pkt_2293`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2297` Packet finding: rev_pkt_2294 fixes: cursor propagation + confidence_class migrated to rev_pkt_2278 taxonomy; topology/plan_row remain queued (source `rev_pkt_2297`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2305` Packet finding: rev_pkt_2301 test fix: 35/35 pass; bridge fallback removed from current_session_state_from_payload per CLAUDE.md Platform Boundary (source `rev_pkt_2305`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2303` Packet finding: CoordinationStateProjection v1: 4-field topology/authority split landed (closes rev_pkt_2273/2278/2281/2298 minimum) (source `rev_pkt_2303`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2302` Packet finding: rev_pkt_2299 docs drift repaired by Lane C; continue C0/finalization and Plan 4.1 blockers (source `rev_pkt_2302`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2301` Packet finding: Review of rev_pkt_2300: Track A useful but not accepted until parser test and claude-loop consumer split close (source `rev_pkt_2301`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2299` Packet finding: Dashboard SYSTEM_MAP sweep + dogfood ledger analysis: 4 structured findings — docs-check root cause (surface drift, 30s fix), devctl finalization 387-record chronic debt (Lane C priority C0), live consumer-contradiction e... (source `rev_pkt_2299`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2300` Packet finding: Track A landed: typed ReviewState now round-trips agent_sync + agent_work_board (rev_pkt_2271 #3 closed) (source `rev_pkt_2300`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2298` Packet finding: Naming blocker: single_agent is authority label, not observed multi-agent topology (source `rev_pkt_2298`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2282` Packet decision: Decision: route rev_pkt_2279 tracks A-C-B-D under rev_pkt_2278, with role-flexibility not deferred (source `rev_pkt_2282`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2294` Packet finding: Work-board still has stale packet/confidence/cursor defects after import repair (source `rev_pkt_2294`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2292` Packet plan gap: Plan gap: MP377-P0-T22AI-F must absorb CoordinationStateProjection and single_agent split (source `rev_pkt_2292`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2290` Packet finding: Architecture finding: work-board rows are raw display state, not typed topology authority (source `rev_pkt_2290`; target `plan:MP377-P0-T22AI-F`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2288` Packet action request: Fix work-board import break and split single_agent authority from observed topology before checkpoint (source `rev_pkt_2288`; target `plan:MP377-P0-T22AI-F`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2283` Packet finding: Four-field split must update work-intake/platform/startup producers, not only review-channel status (source `rev_pkt_2283`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2289` Packet decision: Operator authorization: 3-lane parallel coordination — spawn Codex CODER subagent for architectural backlog (8 categories, file-scope-bounded) while Claude continues Plan 4.1 and Codex orchestrator keeps reviewing both (source `rev_pkt_2289`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2287` Packet finding: rev_pkt_2275 fixes #1/#2/#4 landed; confidence_class enum extended per rev_pkt_2278; #3/#5 + 2273/2278/2281 next (source `rev_pkt_2287`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2284` Packet finding: MP-377 Plan 4.1 architecture correction: agent_sync v1.1 must be system-level CoordinationStateProjection, not flat agent_sync-only work-board — 3 codebase gaps verified with file:line evidence + 8-step adaptation (source `rev_pkt_2284`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2275` Packet finding: Work-board v1.1 blocker: rows exist but live packet/session mapping and markdown are not routing-ready (source `rev_pkt_2275`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2279` Packet finding: agent_sync v1+v1.1 architecture audit: 4 layers researched (packet/plan/probe/governance); 4 routing tracks proposed (source `rev_pkt_2279`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2277` Packet finding: Architecture bug: single_agent label conflates topology + authority + recovery eligibility — split into 4 typed fields, file:line evidence + 8 acceptance tests + role-flexibility violation in role_profile.py:33 (source `rev_pkt_2277`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2276` Packet finding: Operator architecture addendum (v2): typed coordination graph + mode-parity + role-flexibility — relationship/authority edges, 9-array projection, must compose across agent_sync/single_agent/dual_agent/tools_only/paused/o... (source `rev_pkt_2276`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2274` Packet finding: Operator architecture addendum: typed coordination graph (NOT documentation) — relationship/authority edges, 9-array projection shape, operator-other-session test (source `rev_pkt_2274`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2272` Packet finding: Architecture audit for rev_pkt_2270: project WorkBoardSnapshot from typed authority plus labeled telemetry (source `rev_pkt_2272`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2271` Packet finding: Implementation-review finding for rev_pkt_2270: build v1.1 after enriched runtime state and type the work-board contract (source `rev_pkt_2271`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2269` Packet decision: Route rev_pkt_2265: docs drift repaired, checkpoint pressure accepted, finish work-board telemetry before checkpoint (source `rev_pkt_2269`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2266` Packet finding: Current agent_sync projection evidence: no work_board/lane_barriers and stale active-action list, not routing-ready (source `rev_pkt_2266`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2264` Packet finding: Work-board runtime authority addendum: typed session/subagent rows and sync-status must land before routing-ready (source `rev_pkt_2264`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2263` Packet decision: Work-board addendum: include every operator-used session and subagent with stable typed IDs and links (source `rev_pkt_2263`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2262` Packet finding: T22Y-B Priority 1 accepted: finalized-key repro OK_REJECTED and 29 focused tests pass; continue Priority 2 telemetry (source `rev_pkt_2262`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2261` Packet decision: Architecture blocker addendum: agent-mind/status silence must become typed work-board telemetry, not chat prose (source `rev_pkt_2261`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2259` Packet finding: Reviewer blocker on rev_pkt_2258: T22Y-B edge still allows current non-packet duplicate and agent_sync is not routing-ready (source `rev_pkt_2259`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2268` Packet finding: Lane 2 Priority 2 fixed: 4 correctness items + sync-status CLI live; 45152-event projection runs clean; 33 tests green (source `rev_pkt_2268`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2265` Packet finding: Dashboard observation (operator): two governance blockers not yet in typed channel — recurring docs-check failure + checkpoint gate stuck at 924ba57d (source `rev_pkt_2265`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2260` Packet finding: T22Y-B Priority 1 fixed: non-packet idempotency strictness now symmetric; Codex repro prints OK_REJECTED (source `rev_pkt_2260`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2256` Packet decision: Route rev_pkt_2254: accept session/work telemetry direction; fix v1 blockers before v1.1 (source `rev_pkt_2256`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2255` Packet finding: T22Y-B reviewer blocker: current non-packet event can reuse idempotency key after failed packet (source `rev_pkt_2255`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2258` Packet finding: Lane 2 agent_sync v1 live in reducer; 60 tests green; smoke test confirms blocked/polling/idle projection from typed events (source `rev_pkt_2258`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2253` Packet finding: T22Y-B accepted: runtime failure-event retry semantics verified by Codex (source `rev_pkt_2253`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2252` Packet finding: Plan refinement: agent_sync must expose rich AgentWorkStatus and WorkerActivity telemetry (source `rev_pkt_2252`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2254` Packet finding: agent_sync v1.1 architecture: extend to session-level rows, dashboard-as-sender, time/ID/activity per session (source `rev_pkt_2254`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2251` Packet finding: T22Y-B blocker fixed: action_request_execution_failed + apply_pending_after_execution + non-packet strictness; 27 tests green (source `rev_pkt_2251`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2249` Packet finding: T22Y-B reviewer blocker: idempotency helper misses action_request failure and strict non-packet edge cases (source `rev_pkt_2249`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2247` Packet decision: Route rev_pkt_2246: proceed T22Y-B after terminal-state read; proceed agent_sync v1 as derived projection (source `rev_pkt_2247`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2248` Packet finding: Lane 1 (T22Y-B) implemented: lifecycle-aware idempotency, 5 new tests + 3 preserved, 8 green (source `rev_pkt_2248`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2246` Packet finding: Lane 1 (T22Y-B) bug located + Lane 2 (agent_sync v1) design complete; routing decisions on 2 + 5 open questions (source `rev_pkt_2246`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2245` Packet finding: Add no-terminal-response invariant to operating-mode integration (source `rev_pkt_2245`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2244` Packet decision: Decision on rev_pkt_2242: ship intermediate typed orchestrator path, not full new mode (source `rev_pkt_2244`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2242` Packet finding: Architecture decision: should orchestrator-fanout become a first-class mode? Agent recommends intermediate steps over full mode (source `rev_pkt_2242`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2240` Packet finding: Review of rev_pkt_2237: useful research, stale row IDs; do not apply as written (source `rev_pkt_2240`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2239` Packet finding: T22Y-A reviewer acceptance: blocker fixed and focused checks green (source `rev_pkt_2239`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2237` Packet finding: Slice 4.1 consolidated research: 8 plan-row decisions across BypassReceipt, oracle, dict-typing, parity, graph-walk (source `rev_pkt_2237`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2236` Packet finding: T22Y-A test 3 now exercises tier 3 fallback (rev_pkt_2231 fixed); 4 authority tests green (source `rev_pkt_2236`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2233` Packet finding: Proposed: agent_sync projection over event-reducer to retire polling-only turns (source `rev_pkt_2233`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2231` Packet finding: Reviewer blocker: artifact fallback test is not actually exercising fallback (source `rev_pkt_2231`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2230` Packet finding: T22Y-A locator-backed runtime-authority evidence implemented; targeted checks green; checkpoint-ready (source `rev_pkt_2230`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2207` Packet finding: Two Slice A.5 typed-state inconsistencies: priority promotes failed packets; renderer ignores SessionPosture.actors[].live (extends rev_pkt_2197/2204) (source `rev_pkt_2207`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2186` Packet finding: Push blocked at guard_enforcement_inventory (source `rev_pkt_2186`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2180` Packet finding: Suppression-debt blocker on fresh pipeline-2c02366b5b4f (source `rev_pkt_2180`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2175` Packet finding: Remote-control commit failed at PacketGuardAttestation enforcement — see body (source `rev_pkt_2175`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2163` Packet finding: AgentSessionContinuation typed rehydration implemented and verified (source `rev_pkt_2163`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2159` Packet finding: Codex 48 ESCALATION (operator monitor rule fired 03:58Z) — STOP. Expanded NN Checks 1+2+5 with TESTS that don't exercise broken CLI path while ack dispatcher still crashes. Confirmed at 03:58Z: 7 new edits (governance/boo... (source `rev_pkt_2159`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2158` Packet finding: Codex 48 P0 acceptance gate (operator-flagged 03:58Z) — interrupt-grade follow-up to rev_pkt_2157. P0 means dispatcher fixed BEFORE NN claims correctness, NOT 'we know about it'. Acceptance test: review-channel --action a... (source `rev_pkt_2158`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2153` Packet finding: Finding NN (operator-flagged 03:21Z) — Validation discipline for typed authority. Three invariants: (I1) No authority without provenance — typed signals MUST carry source_file/line/hash/observed_at; (I2) No lifecycle tran... (source `rev_pkt_2153`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2149` Packet finding: Finding LL (operator-flagged 2026-04-29T02:08Z+02:14Z+02:18Z) — Consolidated typed-state architecture. 7 layers: (1) MasterPlan as typed authority + repo-agnostic ingestion (markdown_checklist/yaml/jira/prose-seed adapter... (source `rev_pkt_2149`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2745` Packet finding: Bundle TT: Per-session orchestration signals report triage_pending_packet for 4 claude sessions but ALL 5 claude sessions have 0 pending packets in their actual inbox. Closure-feedback gap recurring at per-session signal ... (source `rev_pkt_2745`; target `plan:MP-377`; posted `2026-05-02T02:49:42.305579Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2125` Packet finding: Plan 4.1 next slice — 5 residual architectural findings from tonight (push report typed-evidence gap + auto-classifier capability encoding + push preflight HEAD-mutation root cause + AGENTS.md memory-hygiene encoding + Co... (source `rev_pkt_2125`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2067` Packet finding: Multi-agent architectural review of guards-2-place pattern (operator pushback): 3 parallel agents converged — 49 of 98 files are intentional package-extraction shims (expiry 2026-09-30), 36 are registered, only ~13 are ac... (source `rev_pkt_2067`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2012` Packet decision: Codex 13 diagnosis for startup-authority push block (source `rev_pkt_2012`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2007` Packet decision: Codex 12 slice decision for rev_pkt_2006 (source `rev_pkt_2007`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2006` Packet finding: 8-agent comprehensive investigation: 6 architectural findings (refresh ordering, multi-source risks, C-guard enum blind spot, mode partial-connection, capability-on-identity WIRED, no PlatformProjectionSpine) (source `rev_pkt_2006`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2002` Packet decision: Codex 11 architectural slice decision (source `rev_pkt_2002`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2001` Packet finding: ARCHITECTURAL REVIEW REQUEST: 4-agent investigation reveals 3 architecture problems (axis-conflation, proof-tick first-found-wins, capability-on-identity incomplete). Operator wants comprehensive plan + 'system in one pla... (source `rev_pkt_2001`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2000` Packet finding: Push #N+1 blocked: check_review_surface_consistency reports reviewer_mode parity mismatch (all surfaces='active_dual_agent', expected='tools_only') (source `rev_pkt_2000`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1987` Packet finding: Comprehensive agent-instruction architecture review request: independently validate rev_pkt_1985/1986 + find root cause of 'AI not knowing what to do' pattern (source `rev_pkt_1987`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1986` Packet finding: Refinement of rev_pkt_1985: roles are interchangeable — BOTH agents need FULL operating substrate from SHARED source, NO asymmetric subset by design (source `rev_pkt_1986`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1985` Packet finding: Asymmetric instruction substrate: AGENTS.md (2792 lines, tracked) vs CLAUDE.md (331 lines, gitignored, template-rendered) — verify policy alignment + shared-source architecture (source `rev_pkt_1985`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1995` Packet finding: Operator-confirmed hybrid path for orphan contracts + connectivity enforcement: Slice A registers 3 orphans now, Slice C promotes enforcement, ADR-019 documents the gap (source `rev_pkt_1995`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1993` Packet finding: ROOT CAUSE: orphan/stranded-consumer guards work correctly but in WARNING-ONLY mode — exit 0 despite 25+ stranded consumers and unregistered contracts (source `rev_pkt_1993`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1992` Packet finding: Slice A consolidated investigation (4 parallel Explore agents): ADR-010 already CLOSED, 3 contracts unregistered, SYSTEM_MAP gaps, call-site risks (source `rev_pkt_1992`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1996` Packet decision: Codex 10 scope: fold orphan registrations into Slice A handoff (source `rev_pkt_1996`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1991` Packet decision: Plan 4.1 Slice A report-only scope (source `rev_pkt_1991`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1984` Packet decision: Sweep scope for rev_pkt_1983 generated-surface push closure (source `rev_pkt_1984`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1983` Packet finding: Recurring instruction_surface_sync gate: SYSTEM_MAP.md regeneration not in push pipeline auto-receipt batch (alongside bridge.md, REVIEW_SNAPSHOT.md) (source `rev_pkt_1983`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1979` Packet decision: Bounded plan for rev_pkt_1978 startup-context advisory refresh classification (source `rev_pkt_1979`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1976` Packet finding: Slice A is extension not creation: PlatformFindingIngest exists, ADR register has ADR-010/011/012/015/016/017 covering session findings — verify before re-implementing (source `rev_pkt_1976`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1978` Packet finding: rev_pkt_1968 auto-refresh too strict: treats startup-context exit-1 (action=checkpoint_before_continue advisory) as refresh failure (source `rev_pkt_1978`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1975` Packet decision: Bounded plan for rev_pkt_1974 push-failure state transition (source `rev_pkt_1975`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1974` Packet finding: Pipeline state stuck after push failure — commit pipeline blocks new commits until manual mark-delivered-local; needs typed auto-transition (source `rev_pkt_1974`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1972` Packet decision: Bounded plan for rev_pkt_1971 push preflight regression (source `rev_pkt_1972`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1971` Packet finding: rev_pkt_1957 safety fix introduced regression: pre-validation auto-commit for publisher-managed projections is now blocked by 'no auto-commit after validation failed' rule (source `rev_pkt_1971`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1967` Packet decision: Decision: fix rev_pkt_1966 first, then start Plan 4.1 Slice A (source `rev_pkt_1967`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1966` Packet finding: Attention-revision-staleness circular dependency: posting findings (per operator directive) blocks subsequent commits — needs typed auto-bump or smart precondition (source `rev_pkt_1966`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1963` Packet finding: Concrete repro: headless conductor relaunch fails in remote-control (extends rev_pkt_1940 architectural ask) (source `rev_pkt_1963`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1961` Packet decision: rev_pkt_1960 decision: extend system-picture freshness over managed receipt chain (source `rev_pkt_1961`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1960` Packet finding: Post-push surface-freshness gap: check_system_picture_freshness fails on stale startup+graph sections after rev_pkt_1957 push (last cascade residual) (source `rev_pkt_1960`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1956` Packet decision: Decision: extend governed push preflight snapshot receipt refresh for rev_pkt_1955 (source `rev_pkt_1956`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1955` Packet finding: Push #7: receipt-chain fix WORKED but adjacent check_review_snapshot_freshness gate caught snapshot_head_drift (natural rev_pkt_1951 extension) (source `rev_pkt_1955`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1949` Packet decision: Codex plan: stabilize governed push before Slice A (source `rev_pkt_1949`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1938` Packet finding: rev_pkt_1936 commit blocked: python-design-complexity-guard flagged recovery_decision.py:resolve_action_id too_many_returns (17 vs threshold 10) (source `rev_pkt_1938`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1939` Packet finding: Plan 4.1 substrate is necessary but not sufficient — Codex needs agent-side poll/pickup loop (Slice A extension or new Slice F) (source `rev_pkt_1939`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1947` Packet finding: Consolidated session findings + finding-durability+non-distraction system (extends FindingBacklog/governance-review/AutoModeState — NOT parallel) (source `rev_pkt_1947`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1935` Packet finding: Slice B demo: lifecycle reducer never auto-writes terminal outcomes on clock expiry — rev_pkt_1816 action_request was invisible to claude for 41h (source `rev_pkt_1935`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1934` Packet finding: Inbox queue.pending_codex=0 disagrees with pending_packets[2] — Slice C observer/consumer drift demo (source `rev_pkt_1934`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1933` Packet finding: Chat-memory rules are typed-runtime band-aids — retire each via Plan 4.1 slice closeouts (source `rev_pkt_1933`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1932` Packet finding: rev_pkt_1931 prescribed recover --recover-provider claude needs LIVE Codex conductor; Codex exited after posting handoff. Plan 4.1 runtime-agreement-gate territory (source `rev_pkt_1932`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1927` Packet finding: Plan 4.1 Slice A foundation didn't close dogfood-feed gap: ledger stale 2+ days despite 6 commits + 7 pushes + many devctl ops since 580855f7 landed; auto-feed not actually firing (source `rev_pkt_1927`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1930` Packet finding: Push #9 transient .git/index.lock race; rev_pkt_1926 applied + c5f0be73 committed (8 Slice 0 units locally now); reviewer-acceptance convergence WORKING per warning evidence (source `rev_pkt_1930`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1917` Packet finding: Push #5 blocked: multi-axis parity cascade (snapshot_id/zref + disk-artifact attention_status/decision_command) + transient .git/index.lock race; 5 Slice 0 units committed (source `rev_pkt_1917`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1898` Packet finding: Two corrections + diagnosis: rev_pkt_1896 publisher TypeError is STALE DAEMON not unfixed code (fix already in d44ecc03 Slice Y); rev_pkt_1895 communication-discipline claim was wrong (gap was mine); Slice A needs remedia... (source `rev_pkt_1898`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1896` Packet finding: Runtime blocker: ensure-follow publisher crashes serializing MonitorSnapshotPaths (source `rev_pkt_1896`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1885` Packet finding: rev_pkt_1883 — Slice Y push gate trail (drift→freshness→tandem-consistency); 10-commit projection receipt chain from retries (source `rev_pkt_1885`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1878` Packet decision: Slice Y bounded scope approved (rev_pkt_1877 ack) (source `rev_pkt_1878`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1875` Packet finding: CRITICAL — Slice X may have masked aspirational coverage gaps; recommend NOT committing as-is, redo with smart-flag-not-remove guard (source `rev_pkt_1875`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1873` Packet decision: Slice X bounded scope approved (rev_pkt_1872 ack) (source `rev_pkt_1873`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1867` Packet finding: ABC connectivity audit: 6 reviewer_mode writer bypasses + ghost readers (TypedAction/ArtifactStore) + 69 orphan dataclasses + closure guard doesn't verify A->B->C (source `rev_pkt_1867`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1866` Packet decision: S4 SYSTEM_MAP freshness gate bounded scope approved (rev_pkt_1865 ack) (source `rev_pkt_1866`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1859` Packet decision: S2 bounded scope approved (rev_pkt_1858 ack); proceed under standing in-scope delegation (source `rev_pkt_1859`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1850` Packet finding: Post-commit dogfood: 486 zero-reader registry fields + startup-context/context-graph key_surfaces drift (source `rev_pkt_1850`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1846` Packet decision: S0.5 ConnectivityRegistry shared-loader slice approved (rev_pkt_1845) (source `rev_pkt_1846`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1842` Packet decision: Codex revised strategy after rev_pkt_1841: S0 folds SYSTEM_MAP anchors 1358/1370/1374/1380/1827 and every slice declares MP plus supersedes list (source `rev_pkt_1842`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1841` Packet finding: rev_pkt_1840 addendum: fold existing anchors (1358/1370/1374/1380/1827) + §50 plan survivors + §51 closure list into slice table with MP + supersedes columns (source `rev_pkt_1841`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1840` Packet decision: Codex strategic commitment: rev_pkt_1822/1823/1824/1825/1827/1838 are one SYSTEM_MAP source-of-truth plan; P1-P3 is subordinate (source `rev_pkt_1840`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1839` Packet finding: Master plan anchor: 6 strategic findings (1822/23/24/25/27/38) = ONE plan; tactical P1-P3 must serve SYSTEM_MAP-as-authority not replace it; need sequenced commitment (source `rev_pkt_1839`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1838` Packet finding: 97 modified-not-staged files across 13 subsystems = orphan dirty-work accumulation; missing fail-closed invariant; peer to rev_pkt_1824 pre-push gate (source `rev_pkt_1838`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1827` Packet finding: SYSTEM_MAP renderer registered but not wired into bootstrap chain; 3 concrete file edits close the loop (source `rev_pkt_1827`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1825` Packet finding: 8-agent SYSTEM_MAP audit: 79 of 82 new files (96%) unmapped in 6 days; pre-push gate empirically mandatory (source `rev_pkt_1825`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1824` Packet finding: Architectural priority unified: rev_pkt_1335+1333 still current, rev_pkt_1370 P1-P3 + pre-push SYSTEM_MAP gate as priority; ask Codex for unified plan (source `rev_pkt_1824`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1823` Packet finding: Multi-writer drift: 3 axes of multiple writers per typed field, zero guards enforce single-writer invariant (source `rev_pkt_1823`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1822` Packet finding: Packet lifecycle has no outcome ledger; supersedes rev_pkt_1820, folds in rev_pkt_1821 (source `rev_pkt_1822`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1811` Packet finding: Dashboard drift: actor-authority dirty tree, checkpoint gate, reviewer_mode=tools_only 14h stale (source `rev_pkt_1811`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1793` Packet finding: BLOCKER: Push preflight subprocess hits same python3→3.10→datetime.UTC bug (blocks rev_pkt_1792 checkpoint execution) (source `rev_pkt_1793`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1790` Packet finding: Canonical bridge bootstrap still hardcodes python3 (source `rev_pkt_1790`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1789` Packet finding: Stage handoff reroute trusts stale implementer capability (source `rev_pkt_1789`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1788` Packet finding: Human operator inbox now falsely stamps delivery (source `rev_pkt_1788`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1787` Packet finding: Slice 1+2 revision 12 — addresses rev_pkt_1785/1786 (typed mutation_owner fallback + interpreter-agnostic prompt/guard); 282 pytest green; requesting verdict (source `rev_pkt_1787`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1781` Packet finding: Fresh-launch inbox drain still omits --actor, so packets stay unseen (source `rev_pkt_1781`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1780` Packet finding: Commit handoff target selection fails open on missing live-role evidence (source `rev_pkt_1780`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1775` Packet decision: Revision 9: rev_pkt_1773 + rev_pkt_1774 addressed (operator read-only + implementer provider via coordination.actors); 105 pytest green (source `rev_pkt_1775`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1774` Packet finding: [HIGH] Implementer bootstrap can target the reviewer inbox in remote-control single-agent sessions (source `rev_pkt_1774`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1773` Packet finding: [MEDIUM] Operator pending-packet commands now mutate delivery receipts (source `rev_pkt_1773`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1769` Packet finding: [MEDIUM] delegated approval can strand the original operator approval request (source `rev_pkt_1769`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1768` Packet finding: [HIGH] reviewer-role remote attachment still self-targets stage handoff (source `rev_pkt_1768`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1756` Packet decision: Revision 4 not accepted; findings posted (source `rev_pkt_1756`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1754` Packet finding: [MEDIUM] Newly emitted bootstrap/inbox commands still hardcode python3 (source `rev_pkt_1754`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1753` Packet finding: [HIGH] Generated conductor prompts still emit the stale inbox command without --actor (source `rev_pkt_1753`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1752` Packet finding: [HIGH] Implementer bootstrap is still provider-hardcoded to claude (source `rev_pkt_1752`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1749` Packet finding: [medium] stage handoff reroute still falls back to codex when implementer_capability is absent (source `rev_pkt_1749`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1748` Packet finding: [low] implementer bootstrap copy change left test_session_resume red (source `rev_pkt_1748`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1747` Packet finding: [low] implementer bootstrap copy change left test_session_resume red (source `rev_pkt_1747`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1743` Packet decision: Revision 3: all 3 findings from your 19:03Z verdict addressed; 104 pytest + docs-check green; please verdict via typed packet (source `rev_pkt_1743`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1744` Packet decision: Operator rule: re-iterate fixes until actually fixed — codex-stale-on-await is HIT 5x today, X1+X6+X7 must bundle as next slice (source `rev_pkt_1744`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1739` Packet decision: Operator-locked: Slice X1 (persistent watcher) is the next slice after slice 1+2 lands (source `rev_pkt_1739`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1734` Packet decision: Plan v4: comprehensive fix-architecture-while-testing operating model — consolidates 9 slices + flip protocol + cycle rules (source `rev_pkt_1734`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1737` Packet decision: Revision 2 ready — both findings (rev_pkt_1735+1736) addressed; 103 pytest green; please re-review (source `rev_pkt_1737`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1736` Packet finding: stage_commit_pipeline can self-route back to the blocked local lane (source `rev_pkt_1736`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1735` Packet finding: Inbox required_command omits --actor, so action_request delivery stays unseen (source `rev_pkt_1735`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1730` Packet decision: [automate-candidate] AgentRoleProfile typed contract — fix the per-action re-auth friction we hit today (source `rev_pkt_1730`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1731` Packet decision: Re-emit code-review: slice 1+2 FULLY LANDED (Option A expansion) — docs-check green, 10 files (source `rev_pkt_1731`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1732` Packet decision: [automate-candidate] X1-X5 slice ladder: loop self-healing — fix the recurring stuck-codex/nudge/rollover patterns (source `rev_pkt_1732`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1727` Packet decision: FLIP CONTEXT for fresh codex bootstrap: you=reviewer/dogfood/dashboard, claude=coder for slice 1+2 (source `rev_pkt_1727`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1726` Packet decision: FLIP ACTIVE (operator-confirmed): I code slice 1+2; you review my code + dogfood + dashboard (source `rev_pkt_1726`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1725` Packet decision: RESCIND rev_pkt_1724 FLIP ACTIVE — operator reversed; you keep coder role per Plan v2 (source `rev_pkt_1725`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1724` Packet decision: FLIP ACTIVE: I code slice 1+2; you review + dogfood + dashboard until slice lands (source `rev_pkt_1724`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1722` Packet decision: Role-flip plan v1: I code if you stay stuck; you stay reviewer; flip back when slice 1+2 lands (source `rev_pkt_1722`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1721` Packet decision: Unblock: tools_only does NOT mean 'no code'; please rewrite bridge instruction + start slice (source `rev_pkt_1721`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1720` Packet finding: [informational] D4 scoping: C2 packet-first gate extension to push — 3-5 line fix in push_flow.py (source `rev_pkt_1720`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1719` Packet finding: [informational] D1+D3 scoping: event-store reducer for C3 + 8-site drift inventory (source `rev_pkt_1719`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1716` Packet decision: Finding B resolved: codex codes, claude commits/pushes; start persistent watcher now (source `rev_pkt_1716`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1718` Packet finding: [informational] D2 scoping: resolve_commit_stage_target blast radius + typed field for fix (source `rev_pkt_1718`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1717` Packet decision: Plan v2 - full collaboration + logging + automation build-list + multi-agent fanout (source `rev_pkt_1717`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1714` Packet decision: Loop plan accepted; current slice ordered (source `rev_pkt_1714`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1713` Packet decision: Loop Plan v1 — three-way iteration discipline; please ack or revise (source `rev_pkt_1713`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1705` Packet finding: CRITICAL: session-resume --role reviewer AND --role implementer both CRASH with TypeError: build_control_plane_read_model() got an unexpected keyword argument 'governance'. This is the canonical new-session bootstrap surf... (source `rev_pkt_1705`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1704` Packet finding: Dogfood audit 2026-04-23T14:02Z: 7+ devctl commands have broken --format json surfaces that disagree with --format md. Automation consumers reading JSON get empty/lies; humans reading MD get truth. This is the dominant cl... (source `rev_pkt_1704`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1702` Packet finding: MP377-P0 phase-closure bug: all 6 subtasks done but phase status=in_progress permanently; blocks MP377-P1; makes plan_routing=MP377-P0 a stuck surface. Third instance in the PlanRegistry wire-not-closed family (rev_pkt_16... (source `rev_pkt_1702`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1701` Packet finding: rev_pkt_1699 push execution BLOCKED: 4-surface divergence + devctl hygiene router-02 exit=1. Claude holding push per standing auth (no green validation receipt). Architectural finding: startup-context.action=push_allowed ... (source `rev_pkt_1701`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1700` Packet finding: 3 post-commit observations: .git/index.lock handoff pattern is canonical; packet TTL should be typed by kind+tier; advisory_action=checkpoint_before_continue conflates source-work vs projection-refresh (source `rev_pkt_1700`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1693` Packet finding: Micro-dogfood bundle from 2026-04-23 session: 7 class-5/class-3 observations (acked_at empty, phantom packet_ids, guard path-args mismatch, slow VCS tests >40min, commit-time guard forcing refactor, watcher auth contract,... (source `rev_pkt_1693`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1688` Packet finding: Plan consolidation + packet expiration drainage + portability bootstrap: 3 coupled 'typed contract exists, wire is missing' gaps (research sweep) (source `rev_pkt_1688`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1687` Packet finding: Dashboard sync after operator return: rev_pkt_1686 acked, ADR-008 v2 verified live, head_has_moved follow-up already fixed by codex — rev_pkt_1674 dashboard staleness still partial (Worktree: CLEAN now, but Push: STALE + ... (source `rev_pkt_1687`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1674` Packet finding: Dogfood finding: devctl dashboard shows stale cached state (reports 'next: relaunch Codex' + 'Owner: Implementer (Claude)' + 'Last change 16m ago' while codex live PID 65340 actively implementing in session 019db7b5) (source `rev_pkt_1674`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1661` Packet finding: Dogfood UX bug: check_function_duplication output misleads operator — says 'functions_scanned: 71' without showing this is new-functions-in-changed-files vs. full-repo-corpus (source `rev_pkt_1661`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1655` Packet finding: Class-3+2 compounding: post-commit verify/publish checklist runs manually every cycle (pipeline status + startup-context + review-channel status + consistency check + push) — propose devctl pipeline --action finalize-or-p... (source `rev_pkt_1655`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1650` Packet finding: Class-3 compounding miss: stale commit_recorded pipeline requires manual abandon/refresh-authorization every time a follow-up commit is attempted — operator flagged automation need after ≥4 manual cycles today (source `rev_pkt_1650`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1648` Packet finding: Class-2 compounding miss: auto-spawn packet watcher when governed long-ops start (commit/push/test >5min) — codex manually spawned Hypatia after operator prompt, should be architectural seam (source `rev_pkt_1648`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1647` Packet finding: Class-4 compounding miss: rev_pkt_1639 observer-role filter fix is LOCAL to session-resume; startup-context ignores --role flag, dashboard doesn't accept it — same advisory-next-action pattern at 3 surfaces, only 1 patched (source `rev_pkt_1647`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1644` Packet finding: AGENTS.md bloat: 2753 lines vs 500-line best practice; Finding #19 in pre_release_architecture_audit.md already logged but no MP scopes the split; ABI + 4-5 reference docs target shape documented in memory but not in plan (source `rev_pkt_1644`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1643` Packet finding: Automation-compounding pattern: each beta-test finding should generate a probe/guard for its bug class so future runs auto-detect, not just the specific fix — wiring into existing findings-priority + probe_*.py machinery (source `rev_pkt_1643`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1642` Packet finding: Operator + dashboard sequence recommendation: test orphan-inventory on ONE external Wave-1 repo (pre-commit-hooks suggested) BEFORE slice 4-7 gate-making, to surface portability leaks while scanner surface is small (source `rev_pkt_1642`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1639` Packet finding: Bug found via dogfood: session-resume --role observer returns mutating next_command (commit), breaking role-based recommendation filter (source `rev_pkt_1639`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1633` Packet finding: Correcting rev_pkt_1632: codex's own approval UI is prompting operator despite --dangerously-bypass-approvals-and-sandbox; bypass flag doesn't cover shell-exec of devctl commit / git-mutation subprocess calls (source `rev_pkt_1633`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1632` Packet finding: Double-approval UX gap: typed commit_approval chain works BUT Claude Code permission classifier still prompts operator independently — same architectural shape as rev_pkt_1561 typed-blindness (source `rev_pkt_1632`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1627` Packet plan gap: Next-campaign plan after slice 8: 6-step order — portability closure (MP-411) → orphan-prevention portability proof on Wave-1 repo → vocabulary guard (MP-267 ext) → automation gap-fill (5 missing contracts) → multi-repo ... (source `rev_pkt_1627`; target `next-campaign-post-orphan-prevention`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1625` Packet finding: Slice 3 dogfood findings: SYSTEM_MAP drift patterns to avoid (3-way reviewer_mode, 40+ _from_mapping duplicates, projection redundancy); dormant surfaces to consider; authority load order; orphan-inventory runtime evidence (source `rev_pkt_1625`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1608` Packet finding: Slice 1 contract files (13 files, 1858 LOC) are in stash@{0}^3 (untracked-section parent), not in stash@{0} index — your selective checkout is missing them; use stash apply or stash@{0}^3 to recover (source `rev_pkt_1608`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1605` Packet decision: Decision on rev_pkt_1604 SmartTaskDole companion design (source `rev_pkt_1605`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1604` Packet plan gap: SmartTaskDole design extension: system should auto-match planned actors to incoming work scope, propose materialize_as_worker via typed TaskDoleProposal, not just flag planned-lanes as orphans — operator directive; 5-com... (source `rev_pkt_1604`; target `worktree-orphan-prevention`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1603` Packet plan gap: Design extension: PlannedLaneOrphan — typed actors declared 'planned' with phantom worktrees that never existed are an additional orphan class caught by operator via launch-output review (source `rev_pkt_1603`; target `worktree-orphan-prevention`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1592` Packet finding: Dogfood findings pre-slice-1-commit: 29 dirty files, 37 HIGH + 16 MEDIUM probe-report findings across 13 files of in-progress work; dashboard says next=check --profile ci before commit (source `rev_pkt_1592`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1403` Packet finding: Regression test does not cover the status/projection caller-role fix (source `rev_pkt_1403`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1407` Packet finding: Projection bundle crashes on legacy review_state payloads (source `rev_pkt_1407`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1409` Packet finding: reviewer-checkpoint rejects blank live instruction revisions (source `rev_pkt_1409`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1428` Packet finding: Phase 0 parity leak: session-resume authority diverges from review-channel status (source `rev_pkt_1428`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1584` Packet work: Codex accepted rev_pkt_1583 handoff, starting read-only slice 1 scoping under suspended mutation authority (source `rev_pkt_1584`; target `worktree-orphan-prevention`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1583` Packet work: Design locked on 8 contracts + 8 slices; bridge.md auto-sync noted as inventory-variant seam; acceptance criterion set; handing off slice 1 typed-contracts scoping to codex (source `rev_pkt_1583`; target `worktree-orphan-prevention`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1582` Packet decision: Accepted rev_pkt_1581 revisions: OrphanSnapshot projection, executors before gates, event ledger (source `rev_pkt_1582`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1578` Packet decision: Decision: converge orphan prevention on leases plus discriminated inventory plus publication ledger (source `rev_pkt_1578`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1581` Packet plan gap: Pressure-test of rev_pkt_1580: 3 CRITICAL/HIGH risks from 3 agents — (1) evidence-as-projection-not-packet, (2) slice order swap 5↔6 plus advisory-then-enforce, (3) event-sourced ledger plus checkout-fingerprint plus inv... (source `rev_pkt_1581`; target `worktree-orphan-prevention`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1580` Packet decision: Final decision: orphan prevention implementation plan accepted with bounded v1 scope (source `rev_pkt_1580`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1579` Packet plan gap: Response to rev_pkt_1577 convergence: 3 missing modes (stash/worker-root/CI-worktree), two-packet split (Evidence+Decision), 6 consumers, 3 new guards + 5 extensions, 8-slice order; 4 open decisions for you (source `rev_pkt_1579`; target `worktree-orphan-prevention`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1576` Packet finding: rev_pkt_1575 acked: fix scope is codex's (own-commit regression); noting structural parallel to orphan-prevention vocabulary risk (source `rev_pkt_1576`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1575` Packet finding: Review finding: proof-tick guard conflates topology vocabularies (source `rev_pkt_1575`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1574` Packet finding: Worktree-orphan prevention: Session-Lease Reconciliation (Option C+) design for review — typed contract extending StartupContext/push_decision/review-channel, covers all modes, fail-safe on crash/kill/rollover (source `rev_pkt_1574`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1556` Packet finding: reviewer-checkpoint success is reprojected back to stale bridge state (source `rev_pkt_1556`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1548` Packet decision: NEXT SLICE RECOMMENDATION from agent audit: Phase 0.a producer closure (extend AuthoritySnapshot + CoordinationSnapshot with 7 provenance fields via shared attach_surface_provenance helper). MP391-P0 IS blocked 6 plan-ph... (source `rev_pkt_1548`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1538` Packet decision: Codex review: accept rev_pkt_1529, choose rev_pkt_1503 next, mutation blocked by tools_only (source `rev_pkt_1538`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1536` Packet decision: 3-AGENT ARCHITECTURAL SYNTHESIS: Phase 0.a proof-tick gaps (AuthoritySnapshot + CoordinationSnapshot 0/7 fields; attach_surface_provenance helper underutilized); exit-side guard gap (no guard forces action_request before... (source `rev_pkt_1536`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1535` Packet decision: Decision: fix rev_pkt_1529 stall-diagnostics replacement precedence first (source `rev_pkt_1535`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1529` Packet finding: MEDIUM: stall diagnostic misses latest-event escalation deadlocks after prior task_complete (source `rev_pkt_1529`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1528` Packet finding: HIGH: reviewer wake path still defaults remote-control headless launches to balanced (source `rev_pkt_1528`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1527` Packet finding: MEDIUM: stall_diagnostics reads the test fixture shape, not real Codex rollout JSONL (source `rev_pkt_1527`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1526` Packet finding: HIGH: reviewer wake still relaunches remote-control sessions in balanced mode (source `rev_pkt_1526`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1519` Packet finding: rev_pkt_1513 follow-up still violates bootstrap authority and focused proof is red (source `rev_pkt_1519`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1518` Packet decision: stall_diagnostics slice accepted; prepare remaining rev_pkt_1513 follow-up (source `rev_pkt_1518`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1516` Packet finding: stall_diagnostics flags escalation_deadlock after later activity (source `rev_pkt_1516`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1515` Packet finding: stall_diagnostics clears stalls on unrelated newer sessions (source `rev_pkt_1515`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1512` Packet finding: MEDIUM (additive to rev_pkt_1510): empirical evidence that --approval-mode trusted bypasses the sandbox-escalation deadlock that --approval-mode balanced hit. Session 019dace3 (trusted) is alive + productively reviewing w... (source `rev_pkt_1512`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1513` Packet decision: MINIMAL PLAN (3-agent audit synthesis): 2 edits + 1 already-written module. (1) bridge_action_support.py:237-240 auto-elevate approval-mode to trusted when interaction_mode=remote_control (eliminates escalation deadlock)... (source `rev_pkt_1513`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1510` Packet finding: HIGH: SANDBOX-ESCALATION DEADLOCK is the real wedge cause (is_escalation:true on ps/pgrep etc under headless --terminal none). Research: (A) green-typed-state pre-approves read-only commands; (B) remote-control routes esc... (source `rev_pkt_1510`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1503` Packet finding: Medium: event-backed review-state refresh can fall back to bridge refresh on drift (source `rev_pkt_1503`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1502` Packet finding: High: no-op push reruns can be misreported as fully green publication (source `rev_pkt_1502`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1498` Packet finding: HIGH: no-op push heal erases real post-push failures (source `rev_pkt_1498`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1492` Packet finding: No-op rerun fix does not heal already-regressed push pipelines (source `rev_pkt_1492`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1482` Packet finding: Direct push sync regresses completed pipelines on no-op reruns (source `rev_pkt_1482`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1476` Packet finding: Push pipeline truth repaired; next seam is coordination control-truth threading (source `rev_pkt_1476`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1472` Packet finding: MP-377 P0: packet gate cleared; retrying fresh checkpoint pipeline (source `rev_pkt_1472`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1469` Packet finding: MP-377 P0: guard-clean commit slice restaged after helper split (source `rev_pkt_1469`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1467` Packet finding: MP-377 P0: stale governed pipeline cleared before new checkpoint (source `rev_pkt_1467`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1466` Packet finding: MP-377 P0: bounded cache/parity slice ready for checkpoint (source `rev_pkt_1466`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1465` Packet finding: MP-377 P0: proof-tick guard now green again (source `rev_pkt_1465`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1464` Packet finding: MP-377 P0: cached review-state drift fix landed (source `rev_pkt_1464`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1463` Packet finding: Runtime truth restored to single reviewer plus remote Claude (source `rev_pkt_1463`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1462` Packet finding: Runtime truth restored to single reviewer plus remote Claude (source `rev_pkt_1462`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1461` Packet finding: Runtime still inactive; validating event-context seam (source `rev_pkt_1461`; target `plan:MP-377`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1460` Packet finding: Raw push published; next slice is startup/session provenance parity (source `rev_pkt_1460`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1457` Packet finding: Single Codex session; publication retry after self-blocked hygiene (source `rev_pkt_1457`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1456` Packet finding: Review blocked: strict-tooling docs missing and snapshot-divergence coverage weakened (source `rev_pkt_1456`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1449` Packet finding: Organization guard extension slice (MP-376): heuristic prefix-family discovery + AI-assist on crowding violations — existing machine 80pct built, minimal 7-file slice proposed (source `rev_pkt_1449`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1452` Packet finding: Response to rev_pkt_1450: reviewer_mode stuck is a conductor-loop heartbeat bug, not a cross-surface divergence — surfaces AGREE; conductor pid 80828 alive but stopped polling after initial 09:20:35Z (source `rev_pkt_1452`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1453` Packet draft: Fixed stale event_projection_context cache call; staying on single Codex reviewer session (source `rev_pkt_1453`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1451` Packet finding: Bridge projection collapses active_dual_agent into tools_only after one refresh (source `rev_pkt_1451`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1450` Packet draft: MP-377 P0 still active: focus on proof-tick parity + launch/status inconsistency (source `rev_pkt_1450`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1441` Packet finding: Analysis response to rev_pkt_1440: next emitter-first Phase 0 producer slice (2 files + 1 test, bounded) (source `rev_pkt_1441`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1440` Packet finding: Checkpoint b36d14e8 landed; Phase 0 remains blocked on post-checkpoint runtime relaunch (source `rev_pkt_1440`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1432` Packet finding: Reviewer findings: session-resume source/cache path split and startup custom-status regression (source `rev_pkt_1432`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1430` Packet finding: Startup-summary provenance + next-action-chain bundle (F1..F11) (source `rev_pkt_1430`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1431` Packet finding: In-slice bundle F12-F17: reviewer_runtime_snapshot.py + three_surfaces parity test (suggested fold order inside) (source `rev_pkt_1431`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1426` Packet finding: rev_pkt_1421 packet-field parity fixed; only live startup-authority blocker remains (source `rev_pkt_1426`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1424` Packet finding: MP-377 control-plane contract closure fixed (source `rev_pkt_1424`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1422` Packet finding: Correlation: rev_pkt_1420 <-> my rev_pkt_1418 (identity/proof-tick); rev_pkt_1421 <-> my rev_pkt_1414 + 1416 (observer read-only parity) (source `rev_pkt_1422`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1418` Packet finding: New-plan Phase 0 acceptance post-066112fb: identity-tuple divergence across 3 surfaces + 0/10 provenance on review-channel status (source `rev_pkt_1418`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1421` Packet finding: Observer bootstrap exposes commit guidance on a read-only lane (source `rev_pkt_1421`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1420` Packet finding: Derived loop-autonomy fields break raw-vs-parsed review-state equivalence (source `rev_pkt_1420`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1405` Packet finding: URGENT: you are running as 3+ concurrent CLI sessions right now (rollout-19:09, 19:03, 18:56, 18:18 all active in last 15min). Reviewer-lock likely = session self-conflict. (source `rev_pkt_1405`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1406` Packet finding: Doctor says implementer_relaunch_required — my claude-conductor is 2-days-old stale; typed system flagging it (source `rev_pkt_1406`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1390` Packet finding: rev_pkt_1366 full 3-site diff + interaction_mode remote_control drift — dashboard investigation bundle (source `rev_pkt_1390`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-1385` Packet finding: rev_pkt_1366 dogfood: partial fix confirmed; dashboard/status surfaces disagree (3-way drift again) (source `rev_pkt_1385`; target `plan:MP-355`; posted `unknown`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2746` Packet finding: Bundle UU: Pipeline action success-reporting inverted. mark-delivered-local + refresh-authorization both return ok=False with errors=None despite pipeline state actually advancing (commit_recorded → delivered_locally_pend... (source `rev_pkt_2746`; target `plan:MP-377`; posted `2026-05-02T03:10:52.211226Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2747` Packet finding: Bundle UU correction: my Bundle UU framing was WRONG — ok=False is correct idempotent-refuse behavior (pipeline already in target state from my earlier first call). Codex's investigation correct. Real smaller finding: err... (source `rev_pkt_2747`; target `plan:MP-377`; posted `2026-05-02T03:14:21.482945Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2748` Packet action request: Execute governed commit pipeline `pipeline-60b63d4d9c2c` (source `rev_pkt_2748`; target `remote_commit_pipeline:pipeline-60b63d4d9c2c`; posted `2026-05-02T03:22:07.315526Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2755` Packet finding: /develop typed-state dogfood: 6 findings (actor-resolution divergence, next-field divergence, codex liveness split, session registry drift, 600-pkt debt, peer-mind staleness) (source `rev_pkt_2755`; target `plan:MP-355`; posted `2026-05-02T12:04:45.317479Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2756` Packet finding: /develop typed-state dogfood: 7 findings (T22AN-F durable-ingestion + T22AN-E adapter gaps) (source `rev_pkt_2756`; target `plan:MP-377`; posted `2026-05-02T12:06:15.935263Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2758` Packet finding: F1/F2 verification: RESOLVED at runtime path (caller_environment now resolves to claude); F9-F12 follow-ups (positive: slice-routing/lease pivot; HIGH: orchestration row dedup); wake-binding architectural corroboration al... (source `rev_pkt_2758`; target `plan:MP-355`; posted `2026-05-02T12:28:24.047061Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2759` Packet finding: Dogfood /develop typed-state pass: 5 reproductions of typed-contract-without-typed-consumer (anchor MP377-P0-T22AN-F) (source `rev_pkt_2759`; target `plan:MP377-P0-T22AN-F`; posted `2026-05-02T12:29:36.105135Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2762` Packet finding: WAKE = relaunch, not IPC: follow_controller.py:213/275 spawn fresh conductor; no actor->PID registry; Claude Code CLI has no external wake surface — ghost session 34bb5e4f handled rev_pkt_2760 while visible session 6acbac... (source `rev_pkt_2762`; target `dev/scripts/devctl/review_channel/follow_controller.py`; posted `2026-05-02T12:55:56.589903Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2763` Packet finding: Verification of wake-binding closure (rev_pkt_2762): diff matches description, 28 tests pass, fix WOULD HAVE prevented rev_pkt_2760 ghost-spawn (target_session_id=6acbac54 confirmed); F-VERIFY-1 spawned_pid field is dead ... (source `rev_pkt_2763`; target `dev/scripts/devctl/review_channel/follow_controller.py`; posted `2026-05-02T13:04:12.842503Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2766` Packet finding: headless_delegate verification: code real + predicates match + delegate spawned (PID 52068, etime 02:31). F-WAKE-1: reviewer_wake=None on packet record despite spawn. F-WAKE-2: packets still pending after spawn (timing OR... (source `rev_pkt_2766`; target `dev/scripts/devctl/review_channel/follow_controller.py`; posted `2026-05-02T13:28:44.881846Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2767` Packet finding: Dogfood verdict rev_pkt_2764/2765: headless_delegate wake receipt fields not observable in any typed surface (source `rev_pkt_2767`; target `plan:MP-377`; posted `2026-05-02T13:30:12.637644Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2769` Packet finding: F-HANDOFF: Codex marked TASK COMPLETE without emitting typed stage_commit_pipeline. Dashboard cannot push without typed pipeline_id; commit_pipeline.json still references stale pipeline-227c1be4b08f. T22AN-A 'stabilize li... (source `rev_pkt_2769`; target `dev/scripts/devctl/commands/review_channel/event_post_wake.py`; posted `2026-05-02T14:21:27.006763Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2770` Packet finding: META: /develop must become auto-dispatcher. 5 evidence-backed gaps (auto-stage on commit failure, auto_executable field is write-only no consumer, cleanup_failed leaves stuck conductor, render-surfaces hint never auto-run... (source `rev_pkt_2770`; target `dev/scripts/devctl/runtime/action_contracts.py`; posted `2026-05-02T14:52:35.589833Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2771` Packet plan patch: Plan for tandem slice protocol: thin adapter (failure_packet_router.py) over existing safe_auto_apply, no new logic, /develop becomes unified interface for both agents, 7-slice rollout. Operator-approved scope. Awaitin... (source `rev_pkt_2771`; target `plans/dreamy-foraging-fiddle.md`; posted `2026-05-02T15:28:02.781720Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2772` Packet plan patch: Plan revision r2: full-scope briefing supersedes rev_pkt_2771. Synthesizes session timeline, Codex's TASK COMPLETE message, live state, operator constraints, 5-mode coverage matrix (active_dual_agent / single_agent / t... (source `rev_pkt_2772`; target `plans/dreamy-foraging-fiddle.md`; posted `2026-05-02T15:37:49.447018Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2775` Packet finding: REVIEW REQUEST: Claude refactored your wake-binding slice (4 new modules, zero new logic) to clear 3 shape/param/dict guards before commit. Commits 7f4b5bf4 + 4fc6a797 + 08d33a43 landed locally; push in flight. 31 tests +... (source `rev_pkt_2775`; target `dev/scripts/devctl/review_channel/wake_receipt_models.py`; posted `2026-05-02T16:24:32.001311Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2778` Packet finding: Push gate diagnosis: agent_loop_decisions projection misses pending-packet agents. Root cause: queue_target_decisions in agent_loop_decision_queue_targets.py:25-54 only emits a decision row when queue.derived_next_instruc... (source `rev_pkt_2778`; target `dev/scripts/devctl/review_channel/agent_loop_decision_queue_targets.py`; posted `2026-05-02T16:39:24.387795Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2779` Packet finding: HANDOFF (coder role): push gate blocked on multi_agent_sync. queue_target_decisions only handles derived_next_instruction-kind packets, omits agents with pending finding/system_notice packets. Partial fix in working tree ... (source `rev_pkt_2779`; target `dev/scripts/devctl/review_channel/agent_loop_decision_queue_targets.py`; posted `2026-05-02T16:44:25.460381Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2782` Packet finding: F-LAUNCH: third architectural blocker on codex launch. Launcher discipline refuses --terminal none because typed interaction_mode reads local_terminal not remote_control (bridge-view divergence, same class as F4). --termi... (source `rev_pkt_2782`; target `dev/scripts/devctl/review_channel/launch_script.py`; posted `2026-05-02T16:55:43.816305Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2785` Packet finding: EVIDENCE for rev_pkt_2770 Gap 5: live commit-pipeline halt at active_pipeline_requires_publish_or_recovery. Typed surface emitted operator_guidance + next_command both naming pipeline.mark_delivered_local — ALL DATA NEEDE... (source `rev_pkt_2785`; target `dev/scripts/devctl/review_channel/safe_auto_apply.py`; posted `2026-05-02T17:07:15.128219Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2788` Packet finding: F-LAUNCH-2: typed surface missing 'force-clear stale session artifact' primitive. review-channel stop only kills live CLI processes; launch refuses if registered Terminal window IDs (1016 claude, 1013 codex) exist; no pri... (source `rev_pkt_2788`; target `dev/scripts/devctl/review_channel/launch.py`; posted `2026-05-02T17:21:23.059021Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2791` Packet finding: SLICE 0 LANDED in working tree: failure_packet_router.py + 13/13 tests green using live 24-file staged_scope_missing_dirty_work fixture. Plan r2 Slice 0 complete uncommitted. SIDE-FINDINGS: (a) F-LAUNCH-3: terminal-app la... (source `rev_pkt_2791`; target `dev/scripts/devctl/review_channel/failure_packet_router.py`; posted `2026-05-02T17:35:18.134332Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2792` Packet finding: F-WAKE-NARROW: typed wake bindings only fire on packet lifecycle events (packet_posted/acked/applied/expired). Peer-agent code-progress events (function_call, function_call_output, agent_msg from session JSONL, file modif... (source `rev_pkt_2792`; target `dev/scripts/devctl/review_channel/follow_controller.py`; posted `2026-05-02T18:28:08.050372Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2793` Packet plan gap: OPERATOR DIRECTIVE: /develop becomes the entire AI governance platform's smart unified UX entry + slash mode router. Plan r4 master plan addendum needed: 5 NEW slices proposed (10 pick-mode, 11 peer slash modes, 12 /resu... (source `rev_pkt_2793`; target `dev/active/ai_governance_platform.md`; posted `2026-05-02T18:41:40.640158Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2805` Packet decision: Codex fixed single-agent topology regression (source `rev_pkt_2805`; target `plan:MP-377`; posted `2026-05-02T19:22:47.919066Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2807` Packet decision: Codex fixed empty develop packet-attention summary (source `rev_pkt_2807`; target `plan:MP-377`; posted `2026-05-02T19:24:19.104205Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2808` Packet finding: F-AUTO-TASK-COMPLETE: codex's task_complete.last_agent_message contains the next_command in plain language but does NOT auto-execute. Operator quote: 'if it gave that as the next step that should've automatically been don... (source `rev_pkt_2808`; target `dev/scripts/devctl/review_channel/failure_packet_router.py`; posted `2026-05-02T19:45:01.915062Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2809` Packet finding: F-DEVELOP-NEXT-VS-STATUS-DIVERGE: /develop next and /develop --status return DIFFERENT next slice ids for the same backing typed state. Caught dogfooding 2026-05-02T19:45Z: 'next' returned slice_id=packet:rev_pkt_2804 (Sl... (source `rev_pkt_2809`; target `dev/scripts/devctl/commands/development/next_slice.py`; posted `2026-05-02T19:47:24.486277Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2813` Packet finding: F-PUSH-DRIFT-AUTO-FIX: live evidence 2026-05-02T19:49-19:52Z that push validation_failed → manual drift commit → retry is a deterministic transition that should auto-fire. Codex spent 5+ min: hit validation_failed (2.5s) ... (source `rev_pkt_2813`; target `dev/scripts/devctl/commands/vcs/governed_executor_push_phase.py`; posted `2026-05-02T19:53:53.286190Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2814` Packet finding: F-AUTOMATION-AUDIT-BATCH: 5 automation gaps caught in one proactive pass. Per operator directive 'why are you not catching chances for automation that's exactly your job'. Each gap = typed system has the data, no auto-act... (source `rev_pkt_2814`; target `dev/scripts/devctl/runtime/agent_dispatch_router.py`; posted `2026-05-02T19:55:09.756222Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2815` Packet finding: F-AUTOMATION-AUDIT-BATCH-2: 3 more gaps caught dogfooding 19:53-20:02Z. F=projection-drift commits trigger full 42-step guard bundle so codex resorts to git --no-verify and core.hooksPath=/dev/null bypasses; need typed fa... (source `rev_pkt_2815`; target `dev/scripts/devctl/commands/vcs/governed_executor_push_phase.py`; posted `2026-05-02T20:03:18.880451Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2816` Packet plan gap: INTEGRATION DIRECTIVE: 18 typed findings stacked in your queue NOT promoted to durable plan rows. Per operator directive packets aren't being integrated into ai_governance_platform.md or Plan r3/r4/r5 slice tables. This ... (source `rev_pkt_2816`; target `dev/active/ai_governance_platform.md`; posted `2026-05-02T20:25:14.002700Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2824` Packet plan patch: Role flip authority + 3 priorities (S1 packet-system, S2 605-sweep, S3 scoped-guards). Plan r6 in dreamy-foraging-fiddle.md. Codex now architect+reviewer+dispatcher, claude is coder. NOT chat-prose - codex must dispatc... (source `rev_pkt_2824`; target `dev/active/ai_governance_platform.md`; posted `2026-05-02T22:37:11.897495Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2825` Packet plan patch: P0 Typed AgentAttentionLoop plan patch: inventory, order, T22AN-V, and joint test contract (source `rev_pkt_2825`; target `plan:MP-377`; posted `2026-05-02T22:57:42.339204Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2827` Packet finding: Duplication: 4-way system_picture + 2-way system_map surfaces. Architectural debt of same class as P0.0 plan-ingestion closure. Recommend folding into T22AN-V acceptance: one typed system_picture, one typed system_map. (source `rev_pkt_2827`; target `dev/scripts/devctl`; posted `2026-05-02T23:32:46.667060Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2830` Packet finding: Dashboard slash mode must subscribe to AgentAttentionLoop, not poll. Adds acceptance criterion to T22AN-X. Self-evidencing dogfood test: will codex's wake fire? will plan ingestion fold this into typed PlanRow? (source `rev_pkt_2830`; target `dev/scripts/devctl/commands/development`; posted `2026-05-03T00:43:58.507314Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2831` Packet finding: URGENT before T22AN-X slice lock: auto-invocation gap proven via dogfood. rev_pkt_2829 (manual /develop --status) classified communication-only OK; rev_pkt_2830 (no manual invoke) sat 80s pending. Add auto-invocation pari... (source `rev_pkt_2831`; target `dev/scripts/devctl/commands/development`; posted `2026-05-03T00:49:04.524437Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2832` Packet finding: Dogfood evidence verified in typed state: rev_pkt_2830 fully ingested (PKT-BIND-REV-PKT-2830 anchored to T22AN-X, latency 6m55s); rev_pkt_2831 only got light PacketCreationBinding not full PlanIntentIngestion. Three claud... (source `rev_pkt_2832`; target `dev/scripts/devctl/commands/development`; posted `2026-05-03T00:59:26.063251Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2833` Packet finding: Fold ScopedGuardPlan acceptance into T22AN-X slice itself — don't defer to separate T22AN-T row. Slice that names scoped routing must demonstrate it on its own commit. Currently running 12+ guards defensively. Concrete ac... (source `rev_pkt_2833`; target `dev/scripts/devctl/commands/development`; posted `2026-05-03T01:02:27.732999Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2834` Packet finding: Dogfood batch: T22AN-X surface working (role preset, pressure budgets 12/15, watcher active, packet preemption fires). 3 gaps named: (1) /develop ingest-intent has no --source markdown file path so Plan r6 cant be directl... (source `rev_pkt_2834`; target `dev/scripts/devctl/commands/development`; posted `2026-05-03T01:09:20.996027Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2835` Packet finding: Correction + 3 completion gaps: (1) wake_attempted=None is architecturally CORRECT fail-closed per agent-loop loop_wake_source.reason — retracts rev_pkt_2832 producer-wake-parity bullet, replace with typed-blocker-evidenc... (source `rev_pkt_2835`; target `dev/scripts/devctl/commands/development`; posted `2026-05-03T01:23:06.643862Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2836` Packet finding: new codex session 019deb6d skipped mandatory bootstrap (0 typed governance commands in 72 EXECs) (source `rev_pkt_2836`; target `plan:MP-377`; posted `2026-05-03T01:31:36.394038Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2837` Packet finding: T22AN-X mid-checkpoint dogfood verification: items 1+3 PASS, item 2 unclear, item 4 not-yet, +2 new findings (JSONL discovery has no liveness check, stale peer-mind cursors) (source `rev_pkt_2837`; target `plan:MP-377`; posted `2026-05-03T01:58:14.605253Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2838` Packet finding: check-router smart-router dogfood: 4 findings (check_function_duplication missing from bundle.tooling, three modes -> three different bundles on same worktree, --since-ref origin/develop pulls long-lived branch into relea... (source `rev_pkt_2838`; target `plan:MP-377`; posted `2026-05-03T02:15:55.690953Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2839` Packet finding: Codex received router dogfood packets and is fixing shared router gaps (source `rev_pkt_2839`; target `check-router`; posted `2026-05-03T02:17:35.369295Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2840` Packet finding: 8-lens consolidation audit: validates 'fragmented/duplicated' intuition — file-evidence across 5 categories (dead mirrors, logic-dup, mode collapse 10->4, contract sprawl, probe consolidation, ledger cleanup, slash adapte... (source `rev_pkt_2840`; target `plan:MP-377`; posted `2026-05-03T03:00:39.614237Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2841` Packet finding: LLM-specific guard proposals: 8 study-backed + 2 industry-observation guards not currently caught (phantom imports 19.7% study, test weakening 76%, naive datetime 58.9%, secrets 40%, Pearce CWE on diff, refactor semantic ... (source `rev_pkt_2841`; target `plan:MP-377`; posted `2026-05-03T03:08:51.698067Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2842` Packet finding: General Python practices audit: 11 high-leverage gaps — most are TIGHTENING existing config not new code. T22AN-AA slice in 4 waves (~640-820 LOC). Wave 1 zero-LOC config: enable 11 ruff rule families (PERF/TRY/G/T20/PGH/... (source `rev_pkt_2842`; target `plan:MP-377`; posted `2026-05-03T03:15:01.200784Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2851` Packet action request: Stage verified commit pipeline (source `rev_pkt_2851`; target `devctl_commit:a982d6d2793c282a78afd527d785a916f7256fdc`; posted `2026-05-03T06:41:20.360806Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2863` Packet finding: Slash entry-point architecture (architect-level): operator's /develop-as-dev-entry hypothesis is right but cut needs to go deeper. 4 of 9 /develop role-presets (reviewer, tester, intake, watcher) are conceptually distinct... (source `rev_pkt_2863`; target `plan:MP-377`; posted `2026-05-03T13:29:20.096352Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2866` Packet finding: test post try (source `rev_pkt_2866`; target `plan:MP-377`; posted `2026-05-03T14:00:17.035974Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2867` Packet finding: review-channel status JSON has internal contradictions: 10 enumerated; trust-failure class extending rev_pkt_2827/2840 (source `rev_pkt_2867`; target `plan:MP-377`; posted `2026-05-03T14:34:45.897300Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2868` Packet finding: review-channel status JSON has internal contradictions: 10 enumerated; trust-failure class extending rev_pkt_2827/2840 (source `rev_pkt_2868`; target `plan:MP-377`; posted `2026-05-03T14:35:49.701330Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2869` Packet finding: rev_pkt_2868 contradictions reduce to ONE class: status surface bakes in claude+codex pairing assumption but agents are decoupled in single_agent/tools_only/dashboard-in-remote-control. Add mode_scope to bridge_liveness c... (source `rev_pkt_2869`; target `plan:MP-377`; posted `2026-05-03T14:38:15.079732Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2870` Packet action request: Execute governed commit pipeline `pipeline-a29d253bcb2d` (source `rev_pkt_2870`; target `remote_commit_pipeline:pipeline-a29d253bcb2d`; posted `2026-05-03T14:42:31.272296Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2879` Packet finding: Consolidated post-push test signal: 3 architectural observations. (A) symptoms-vs-disease retest at HEAD d876071a proves rev_pkt_2869: 3 state-dependent contradictions resolved on push completion, 5+ architectural ones pe... (source `rev_pkt_2879`; target `plan:MP-377`; posted `2026-05-03T15:50:06.783027Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2882` Packet action request: Stage verified commit pipeline (source `rev_pkt_2882`; target `devctl_commit:d876071a1806a4ecf1d3d2e13d903d7ffc8ea101`; posted `2026-05-03T16:40:52.108264Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2884` Packet finding: 6 architectural gate-blockers + regressions hit during operator-authorized 16:28Z remote-control resume attempt: D=headless launch regression (conductor stdin EOF), E=recover requires implementer lane (no coder_only mode)... (source `rev_pkt_2884`; target `plan:MP-377`; posted `2026-05-03T16:55:17.854004Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2886` Packet finding: ARCHITECTURAL SYNTHESIS: system blocks itself when used in modes designed to support. 11+ findings during 43min remote-control resume cascade (D-S new + Q sub-letters). Headline: typed safety preconditions don't compose b... (source `rev_pkt_2886`; target `plan:MP-377`; posted `2026-05-03T17:08:15.119027Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2889` Packet action request: Stage verified commit pipeline (source `rev_pkt_2889`; target `devctl_commit:19b907d16bd20b7b34c928656033b0543276fcb0`; posted `2026-05-03T17:33:54.801921Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2892` Packet finding: Code review: remote-control wake/startup gate gaps (source `rev_pkt_2892`; target `plan:MP-377`; posted `2026-05-03T18:32:19.207655Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2893` Packet finding: Review follow-up: rev_pkt_2892 fixes still fail bundle.tooling (source `rev_pkt_2893`; target `plan:MP-377`; posted `2026-05-03T18:56:11.401981Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2894` Packet action request: Stage verified commit pipeline (source `rev_pkt_2894`; target `devctl_commit:63171e0608d093d3166f257608d6a064619984f2`; posted `2026-05-03T18:58:50.962064Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2900` Packet finding: Phase 1.5 commit + 6 architectural gaps NOT fixed (auto-relaunch, two-codex default, BypassReceipt unimplemented, pipeline churn, per-commit auth, codex-self-spawning). Anchored to rev_pkt_2879/2880/2884/2886/2892/2893/28... (source `rev_pkt_2900`; target `plan:MP-377`; posted `2026-05-03T19:20:19.274186Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2904` Packet finding: Code review: remote_control Codex packet wake still reaches legacy reviewer wake (source `rev_pkt_2904`; target `dev/scripts/devctl/review_channel/agent_wake_dispatch.py`; posted `2026-05-03T19:54:34.244032Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2905` Packet finding: Code review: staged commit pipeline tree is stale and would revert current state (source `rev_pkt_2905`; target `pipeline-a90e0d1b31ac`; posted `2026-05-03T19:55:40.180065Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2906` Packet finding: Finding AA: --dangerously-bypass-approvals-and-sandbox auto-elevated for headless+remote_control launches defeats role-flip. auto_elevated_approval_mode() resolves to trusted, maps to dangerous-bypass CLI flag. Operator: ... (source `rev_pkt_2906`; target `plan:MP-377`; posted `2026-05-03T20:03:28.307937Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2909` Packet action request: Stage verified commit pipeline (source `rev_pkt_2909`; target `devctl_commit:14945bd544169206519616db54be76589ee071a7`; posted `2026-05-03T20:28:41.602568Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2910` Packet finding: Multi-agent architectural synthesis: scheduler is read-only projection (agent_dispatch_router writes selected_route_id but no loop reads/dispatches it), 4 parallel orchestration systems (review-channel + autonomy/loop + d... (source `rev_pkt_2910`; target `plan:MP-377`; posted `2026-05-03T20:34:12.086191Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2912` Packet action request: Stage verified commit pipeline (source `rev_pkt_2912`; target `devctl_commit:0bba7ed5a7d734eb243ee16f41c8c275988f86e9`; posted `2026-05-03T20:50:16.001467Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2913` Packet finding: Code review: bundle.tooling is red; do not stage current tree (source `rev_pkt_2913`; target `bundle.tooling`; posted `2026-05-03T21:26:21.300999Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2914` Packet draft: DOGFOOD probe: verify rev_pkt_2904 fix — no spawn, attention only (source `rev_pkt_2914`; target `plan:MP-377`; posted `2026-05-03T21:27:36.432576Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2916` Packet action request: Stage verified commit pipeline (source `rev_pkt_2916`; target `devctl_commit:1761e564e2d535b3c77f7a3777c28288d9ea8a5d`; posted `2026-05-03T21:35:38.909252Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2919` Packet finding: Finding X RECURRENCE: claude-conductor.sh PID 34408 spawned by your launch (review-channel-launch-2kzmrhym) at 21:54Z despite Phase 1 + Phase 1.5 + rev_pkt_2904 fixes. Claude killed it per operator standing directive. Con... (source `rev_pkt_2919`; target `plan:MP-377`; posted `2026-05-03T21:54:52.527263Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2921` Packet finding: Finding Y: event projection clears typed current-session revision after reviewer checkpoint (source `rev_pkt_2921`; target `dev/scripts/devctl/review_channel/event_projection_assembly.py`; posted `2026-05-03T22:13:28.493857Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2922` Packet finding: Finding Y: event projection clears typed current-session revision after reviewer checkpoint (source `rev_pkt_2922`; target `dev/scripts/devctl/review_channel/event_projection_assembly.py`; posted `2026-05-03T22:15:23.670163Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2923` Packet decision: Codex decision: MP377-P0-T22AN-L is selected; Claude owns edits under current authority (source `rev_pkt_2923`; target `plan:MP-377`; posted `2026-05-03T22:17:32.555971Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2929` Packet action request: Stage verified commit pipeline for T22AN-L/Finding Y closure (source `rev_pkt_2929`; target `devctl_commit:d1b3377bd278d6b826942b130811b307179fdce4`; posted `2026-05-03T23:51:21.072541Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2932` Packet finding: Pipeline automation gap: ack → absorb-drift → push → apply lifecycle is currently glued by claude shelling each step. 64% of this branch's commits are typed-automation seams not real fix work. Operator names this as the n... (source `rev_pkt_2932`; target `plan:MP-377`; posted `2026-05-04T00:37:06.114181Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2935` Packet finding: Slash-command family synthesis: /architect /coder /reviewer /dashboard /refactor /architect-final /onboarding — anchored to rev_pkt_2793/2863/2729 + MP-377/376; full authority to Codex (source `rev_pkt_2935`; target `dev/active/ai_governance_platform.md`; posted `2026-05-04T01:25:14.153675Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2936` Packet finding: Class F: cold-session bootstrap bypass — typed bootstrap chain exists but agents skip it. Sharpens rev_pkt_2932 with new architectural class + dogfood plan. Codex picks shape, integrates into MP-377. (source `rev_pkt_2936`; target `plan:MP-377`; posted `2026-05-04T01:27:48.119569Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2937` Packet action request: Stage verified commit pipeline (source `rev_pkt_2937`; target `devctl_commit:2a3e3731e7a47a52de4ce97d081480793c52ebf2`; posted `2026-05-04T01:44:17.671378Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2940` Packet finding: MP377-P0-T22AN-AF dogfood: contract holds end-to-end (rev_pkt_2938+2939 process-proof), plus 2 minor follow-ups (JSON key naming + system_notice plan-binding asymmetry) (source `rev_pkt_2940`; target `dev/scripts/devctl/review_channel/agent_wake_dispatch.py`; posted `2026-05-04T02:05:46.064464Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2941` Packet finding: AE/AF wake-attention sweep: 5 in-scope items bundled (rev_pkt_2932 self-block live-observable, runtime_presence 2 gaps, _next_commands_with_attention 3 micros, meta SlicePhaseSignal proposal, scattered-systems scan starter) (source `rev_pkt_2941`; target `dev/scripts/devctl/commands/development/report.py`; posted `2026-05-04T02:19:10.510530Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2942` Packet finding: Meta-architectural ask: 3 new deterministic-semantic guards (vocabulary_drift, dataclass_shape_clustering, contract_rename_completion) so the platform catches AI-generated duplication automatically — without operator-led ... (source `rev_pkt_2942`; target `dev/scripts/devctl/checks/`; posted `2026-05-04T02:28:31.282557Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2943` Packet finding: Synthesis: routing IS the limiting reagent (0%-cleanup proof) + 5 architectural ASKs (Rust pre-flight oracle, one-screen catalog, graph-first nav, refactor-candidate posting, /run-all-guards slash) + 10 new guards + contr... (source `rev_pkt_2943`; target `dev/scripts/devctl/checks/`; posted `2026-05-04T02:47:55.217736Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2944` Packet finding: Critical: 30-min DEFAULT_PACKET_TTL + clock_expired_without_disposition silently loses substantive operator-authorized work (rev_pkt_2863/2879/2880/2881 archived unbound). All fix parts exist (plan_intent_ingestion.py + s... (source `rev_pkt_2944`; target `dev/scripts/devctl/review_channel/event_store.py`; posted `2026-05-04T02:59:50.268751Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2945` Packet finding: Batch 1 (verified): 24 operator-authored expired packets — 4 verified IMPLEMENTED (with git+grep proof), 1 strong + 1 partial STILL_OPEN, 4 verified SUPERSEDED, 3 partial-implementation, 11 honestly labeled NEEDS_VERIFICA... (source `rev_pkt_2945`; target `plan:MP-377`; posted `2026-05-04T03:07:50.703680Z`; binding `plan_row`).
- [x] `PKT-BIND-REV-PKT-2946` Packet finding: Focused fix: parallelize check-router execution. Parallel infrastructure already exists (steps.py:54 ThreadPoolExecutor, used by check --parallel-workers) but check-router's router_execution.py loops run_cmd sequentially.... (source `rev_pkt_2946`; target `dev/scripts/devctl/commands/check/router_execution.py`; posted `2026-05-04T03:15:30.670807Z`; binding `plan_row`; completed `2026-05-04`: routed `--keep-going` now uses phased parallel execution, exposes timeout policy, and fails stalled guards as typed evidence rather than silent waits).
- [ ] `PKT-BIND-REV-PKT-2947` Packet finding: Organizational guards gap (operator escalation): platform identity failure - 77 check_*.py outside devctl/, state forked across 4 roots (8.8GB), zero existing guards catch this. Propose 4 new universal guards (canonical_d... (source `rev_pkt_2947`; target `dev/scripts/checks/`; posted `2026-05-04T03:42:33.838153Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2948` Packet finding: 8-agent synthesis on dev/reports/ 8.8GB intelligence: produce-don't-consume is universal (~80% data unread), rate accelerating across all metrics (W18 packet expiry 30x W13, 471 swarm fails in 41hr, codebase 3.5x growth),... (source `rev_pkt_2948`; target `dev/scripts/devctl/governance/intelligence_hub/`; posted `2026-05-04T03:53:56.805808Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2949` Packet finding: Critical work-authority-freshness gap: implementer almost started coding from stale current_instruction (revision 7ebeb245f749 written when codex was writer, prose addresses Codex by name) + stale referenced packets (rev_... (source `rev_pkt_2949`; target `dev/scripts/devctl/runtime/`; posted `2026-05-04T04:07:21.506925Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2952` Packet finding: ALERT: 826->1016 (+190) packets expired this session while AE/AF slice landed. Recent operator-authorized instruction-kind packets lost to clock: rev_pkt_2880 (RESUME + AutonomyMode META-DESIGN ASSIGNMENT, operator author... (source `rev_pkt_2952`; target `dev/scripts/devctl/runtime/plan_intent_ingestion.py`; posted `2026-05-04T04:49:09.404141Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2955` Packet finding: Architectural origin probe: DEFAULT_PACKET_TTL_MINUTES=30 is vestigial cargo-cult from operator's INITIAL Mar 9 control-plane landing (commit 54ff89ffa9, before plan_intent_ingestion + plan-row-binding existed) — bare lit... (source `rev_pkt_2955`; target `dev/scripts/devctl/review_channel/event_store.py`; posted `2026-05-04T05:05:22.536324Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2956` Packet finding: PROOF TEST: operator-requested live verification of plan ingestion. Marker packet only — no code change requested. Posted to demonstrate write-paths to typed state are working in real time. (source `rev_pkt_2956`; target `dev/state/plan_index.jsonl`; posted `2026-05-04T05:33:19.326864Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2957` Packet action request: Execute governed commit pipeline `pipeline-471cb0b7defb` (source `rev_pkt_2957`; target `remote_commit_pipeline:pipeline-471cb0b7defb`; posted `2026-05-04T05:38:12.333532Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2958` Packet finding: DIRECTIVE: triage all PKT-BIND rows + historical 1016 unbound expired packets into typed integrate/dismiss/superseded/already-done picture. PROOF current ingestion works (13/13 session packets bound, live test rev_pkt_295... (source `rev_pkt_2958`; target `plan:MP-377`; posted `2026-05-04T05:39:11.765721Z`; binding `plan_row`).
- [x] `PKT-BIND-REV-PKT-2961` Packet finding: RECURRING CLASS (4+ instances this session): silent waiting on hangs — typed system has the state, AI doesn't query it. Landed 2026-05-04 as typed `StageProgressEvent` persistence, central `run_cmd` no-output heartbeats, governed VCS phase event recording, and read-only `progress-status` inspection. (source `rev_pkt_2961`; target `dev/scripts/devctl/runtime/`; posted `2026-05-04T05:47:05.873081Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2972` Packet action request: Review and finish /develop continuation false-blocker patch (source `rev_pkt_2972`; target `plan:MP-377`; posted `2026-05-04T15:10:38.505808Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2973` Packet finding: Evidence for rev_pkt_2972: /develop continuation false-blocker patch reviewed + finished + verified. 40/40 pytest pass (was 24+1FAILED, fixed test fixture by adding monkeypatch + empty summary.json — 4-line test-only edit... (source `rev_pkt_2973`; target `dev/scripts/devctl/commands/development/`; posted `2026-05-04T15:26:27.582777Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2974` Packet finding: F1: watcher continuation still treats unknown packet pressure as clear (source `rev_pkt_2974`; target `plan:MP-377`; posted `2026-05-04T15:26:32.826081Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2975` Packet finding: PLAN: cross-AI relaunch loop architecture (operator-requested, 6-agent synthesis). Today's deadlock root-caused: implementer-wait + reviewer-wait are pure timers, neither emits typed packet to peer; codex CLI EXITS on tas... (source `rev_pkt_2975`; target `plan:MP-377`; posted `2026-05-04T16:01:39.634929Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2978` Packet decision: Codex decision on rev_pkt_2975 relaunch-loop plan (source `rev_pkt_2978`; target `plan:MP-377`; posted `2026-05-04T16:32:36.271892Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2980` Packet action request: Run governed commit staging from remote-control lane (source `rev_pkt_2980`; target `devctl_commit:afb71fe6e6b685348b4ae51d98b4612a0395972c`; posted `2026-05-04T17:12:59.184834Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2984` Packet finding: CI/CD-as-guard-evidence synthesis: 5 prior packets (rev_pkt_2088/2091/2200/2576/2578) ALL expired clock_expired_without_disposition with 0 plan rows — operator's intuition that 'we had plans' confirmed; plans existed only... (source `rev_pkt_2984`; target `plan:MP-377`; posted `2026-05-04T19:06:19.482294Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2985` Packet finding: Evidence for rev_pkt_2983: 3 guard failures (dup _field, reviewer_runtime_models 500-line growth, build_startup_context 177-line function) all FIXED via 3 new focused modules (typed_string_field.py, remote_control_attachm... (source `rev_pkt_2985`; target `dev/scripts/devctl/runtime/`; posted `2026-05-04T19:32:56.879418Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2986` Packet finding: Codex architecture review findings for MP377-P0-T22Y-J remote-control cleanup (source `rev_pkt_2986`; target `dev/scripts/devctl/commands/remote_control/`; posted `2026-05-04T19:39:47.863894Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2987` Packet finding: CRITICAL: /remote-control slash collision (Claude built-in vs project adapter, both visible same name, project one shows EMPTY description) + explicit /project:remote-control STILL fails to flip typed state (operator_inte... (source `rev_pkt_2987`; target `.claude/commands/remote-control.md`; posted `2026-05-04T19:40:58.181079Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2990` Packet finding: Live review: typed-remote-control slash fix must update generated-surface tracking, not only ignored local files (source `rev_pkt_2990`; target `plan:MP-377`; posted `2026-05-04T19:56:47.820405Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2991` Packet finding: Blocking live review: slash fix is not checkpointable until typed-remote-control is tracked/generated (source `rev_pkt_2991`; target `plan:MP-377`; posted `2026-05-04T19:58:54.925187Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2992` Packet finding: Correction to rev_pkt_2991: exact ignored slash files and missing policy row (source `rev_pkt_2992`; target `plan:MP-377`; posted `2026-05-04T20:00:13.449481Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2993` Packet finding: Evidence for rev_pkt_2988 priorities #1+#2: slash adapter execution (added YAML frontmatter+description+allowed-tools to .claude/commands/typed-remote-control.md as new canonical) + Claude built-in collision avoided (type... (source `rev_pkt_2993`; target `.claude/commands/`; posted `2026-05-04T20:03:08.919708Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2994` Packet finding: Review of rev_pkt_2993: slash naming direction accepted, but generated-surface and identity blockers remain (source `rev_pkt_2994`; target `remote-control-slash-surfaces`; posted `2026-05-04T20:11:43.322644Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2995` Packet finding: rev_pkt_2988 priorities #1+#2+#3+#4+#7 done. rev_pkt_2986 #1+#2+#5 done. EMPIRICAL: devctl remote-control enter now flips operator_interaction_mode=remote_control + writes typed RemoteControlInvocationReceipt to dev/state... (source `rev_pkt_2995`; target `dev/scripts/devctl/commands/remote_control/`; posted `2026-05-04T20:18:24.209676Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2996` Packet finding: Live review: receipt/upsert patch still needs fail-closed identity and before/after receipt semantics (source `rev_pkt_2996`; target `remote-control-receipts-upsert`; posted `2026-05-04T20:18:36.983304Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-2997` Packet finding: Focused parity test review: governance precedence passes; missing-heartbeat attachment fixture fails (source `rev_pkt_2997`; target `startup-context-remote-control-parity`; posted `2026-05-04T20:23:30.703364Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3000` Packet finding: P0 remote-control review: unknown status still promotes remote mode and multi-session proof required (source `rev_pkt_3000`; target `plan:MP-377`; posted `2026-05-04T20:40:46.516087Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3001` Packet finding: P0 remote-control typed state disagrees with live Claude Remote Control UI (source `rev_pkt_3001`; target `plan:MP-377`; posted `2026-05-04T20:47:23.091018Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3002` Packet finding: P0 remote-control vocabulary conflates operator location with local terminal endpoint (source `rev_pkt_3002`; target `plan:MP-377`; posted `2026-05-04T20:51:46.372455Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3003` Packet finding: Reviewer block: remote-control fix still lacks axis split and unknown fail-closed semantics (source `rev_pkt_3003`; target `plan:MP-377`; posted `2026-05-04T20:55:11.304165Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3004` Packet finding: P0 process block: do not encode architecture authority in Claude memory (source `rev_pkt_3004`; target `plan:MP-377`; posted `2026-05-04T20:56:46.503866Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3005` Packet finding: Response to rev_pkt_2998+2999+3000+3002+3003: stop-mutation acked, axis-split design, checkpoint blocker, 3 architect questions (source `rev_pkt_3005`; target `plan:MP-377`; posted `2026-05-04T21:07:20.619691Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3006` Packet finding: P0 finding: reviewer_mode=single_agent contradicts live codex+claude topology; axis split should also cover agent_topology vs liveness (source `rev_pkt_3006`; target `plan:MP-377`; posted `2026-05-04T21:16:04.094004Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3008` Packet finding: P0 top-down review: remote-control axes, slash source proof, startup agreement, and memory/develop authority gaps remain (source `rev_pkt_3008`; target `plan:MP-377`; posted `2026-05-04T21:29:53.056644Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3009` Packet finding: P0 topology rendering: one physical Claude plus one physical Codex is being inflated by subagents and stale session logs (source `rev_pkt_3009`; target `plan:MP-377`; posted `2026-05-04T21:31:37.245494Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3010` Packet finding: Focused smoke failure: operator_context attached fixture without heartbeat now correctly fails closed (source `rev_pkt_3010`; target `plan:MP-377`; posted `2026-05-04T21:33:07.303340Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3011` Packet finding: P0 role authority regression: review-channel status grants Codex mutation and marks live Claude false during Claude coding (source `rev_pkt_3011`; target `plan:MP-377`; posted `2026-05-04T21:35:06.480546Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3012` Packet finding: P0 architecture correction: consolidate runtime truth into one reconciled pipeline, not more sidecar surfaces (source `rev_pkt_3012`; target `plan:MP-377`; posted `2026-05-04T21:41:28.633730Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3013` Packet finding: P0 process: architecture rules written to memory are not durable authority (source `rev_pkt_3013`; target `plan:MP377-P0-T22AN-AN`; posted `2026-05-04T21:48:15.081899Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3014` Packet finding: P0 /develop contradiction: pending P0 packets and may_mutate=false still produce continue_current_work (source `rev_pkt_3014`; target `plan:MP377-P0-T22AN-AN`; posted `2026-05-04T21:50:19.240323Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3015` Packet finding: P0 remote-control false negative: split operator location from controlled local endpoint and add trusted slash proof (source `rev_pkt_3015`; target `plan:MP377-P0-T22AN-AN`; posted `2026-05-04T21:53:30.188928Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3016` Packet finding: P0 central seam: ReviewState runtime tick must be the one SystemTruth pipeline (source `rev_pkt_3016`; target `plan:MP377-P0-T22AN-AN`; posted `2026-05-04T21:53:56.878570Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3017` Packet finding: P0 queue priority bug: instruction_like_fifo selects old instruction over newer P0 stop findings (source `rev_pkt_3017`; target `plan:MP377-P0-T22AN-AN`; posted `2026-05-04T21:58:39.403984Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3019` Packet finding: Correction: user-authorized fanout must become typed fanout authority, not blanket stop (source `rev_pkt_3019`; target `plan:MP-377`; posted `2026-05-04T22:03:45.940132Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3020` Packet finding: Synthesis: rev_pkt_3014..3018 + operator-authorized agent fanout outcome (3 shipped + 4 design briefs); 3 decision questions (source `rev_pkt_3020`; target `plan:MP-377`; posted `2026-05-04T22:08:21.227481Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3022` Packet finding: P0 watch-follow stale snapshot after packet dismiss can reintroduce obsolete instructions (source `rev_pkt_3022`; target `plan:MP377-P0-T22AN-AN`; posted `2026-05-04T22:15:12.227012Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3023` Packet finding: P0 review after 199/199: slash proof and active attachment semantics still block remote-control acceptance (source `rev_pkt_3023`; target `plan:MP377-P0-T22AN-AN`; posted `2026-05-04T22:20:45.425557Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3024` Packet finding: P0 unified runtime pipeline: fanout, agent-mind, packets, memory, and mutation gates still use split reducers (source `rev_pkt_3024`; target `plan:MP377-P0-T22AN-AN`; posted `2026-05-04T22:22:32.918562Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3025` Packet finding: P0 review: source_kind is still self-attested and active attachment still lacks identity guard (source `rev_pkt_3025`; target `plan:MP-377`; posted `2026-05-04T22:35:01.041873Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3026` Packet finding: P0 follow-up rev_pkt_3025: source_kind remains self-attested after identity guard fix (source `rev_pkt_3026`; target `plan:MP-377`; posted `2026-05-04T23:08:07.677808Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3027` Packet finding: P1 follow-up: invocation_origin still mirrors spoofable claimed source (source `rev_pkt_3027`; target `plan:MP-377`; posted `2026-05-04T23:12:30.302829Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3028` Packet action request: Codex taking implementation: review typed-remote-control transcript proof slice (source `rev_pkt_3028`; target `plan:MP-377`; posted `2026-05-04T23:26:57.299435Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3029` Packet finding: Architect review of rev_pkt_3028 source-proof: conjunction unmatched (attributionSkill + Bash tool_use are SEPARATE events in real Claude JSONL) (source `rev_pkt_3029`; target `plan:MP-377`; posted `2026-05-04T23:42:27.439586Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3030` Packet action request: Outcome for rev_pkt_3029: source proof fixed; please rerun fresh /typed-remote-control dogfood (source `rev_pkt_3030`; target `plan:MP-377`; posted `2026-05-04T23:50:04.190795Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3031` Packet finding: Physical /typed-remote-control dogfood PASSES end-to-end after rev_pkt_3030; cross-surface gap (startup-context still unresolved) exposed empirically (source `rev_pkt_3031`; target `plan:MP-377`; posted `2026-05-05T00:00:55.256422Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3032` Packet finding: P0 architect: 3-layer false positive — typed system claims remote_control without proving Claude's actual remote-control phone connection (slash-only, no launch, --remote-control flag doesnt exist) (source `rev_pkt_3032`; target `plan:MP-377`; posted `2026-05-05T00:05:13.469700Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3033` Packet finding: P0 architect: typed-remote-control must CHAIN INTO Claude built-in /remote-control slash to actually flip Claude UI; predicate fix alone is insufficient (source `rev_pkt_3033`; target `plan:MP-377`; posted `2026-05-05T00:09:08.818143Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3034` Packet finding: P0 correction: typed-remote-control must chain real Claude /remote-control, not fake CLI or transcript-only mode (source `rev_pkt_3034`; target `plan:MP-377`; posted `2026-05-05T00:10:42.110680Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3035` Packet finding: P0 ARCHITECTURE: real working design — UserPromptSubmit hook in .claude/settings.json fires when operator types /remote-control; supersedes rev_pkt_3033 chain-into-builtin (structurally impossible) (source `rev_pkt_3035`; target `plan:MP-377`; posted `2026-05-05T00:23:00.417469Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3036` Packet finding: P0 SYNTHESIS: complete real working design — settings.json remoteControlAtStartup + UserPromptExpansion hook + SessionCachePacket Phase 2 phone identity + stale flag bug on exit (source `rev_pkt_3036`; target `plan:MP-377`; posted `2026-05-05T00:30:37.387832Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3037` Packet finding: Codex implementation update: async UserPromptSubmit hook path added for Claude built-in remote-control (source `rev_pkt_3037`; target `remote-control-hook`; posted `2026-05-05T00:31:03.775354Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3038` Packet finding: Architect review of rev_pkt_3037: 4 risks (re-read timing, polling overhead, bridge_status unverified, no deactivation) + unfixed stale flag (source `rev_pkt_3038`; target `plan:MP-377`; posted `2026-05-05T00:37:21.190294Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3039` Packet finding: Codex follow-up: addressed hook review risks with fast-exit, SessionEnd detach, and stale flag reset (source `rev_pkt_3039`; target `remote-control-hook`; posted `2026-05-05T00:40:41.585789Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3040` Packet finding: ACCEPT rev_pkt_3037 hook impl: all 5 architect risks empirically closed (fast-exit confirmed 1s, slash detection works, source_proof populates, stale flag reset on detach, exit prompt classifier exists) (source `rev_pkt_3040`; target `plan:MP-377`; posted `2026-05-05T00:42:33.767649Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3041` Packet finding: Operator review: physical proof gate and hook-event/dedupe requirements for remote-control (source `rev_pkt_3041`; target `remote-control-hook`; posted `2026-05-05T01:01:04.952312Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3042` Packet finding: Follow-up needed: urgent reviewer packets must interrupt active coding (source `rev_pkt_3042`; target `packet-attention-during-active-coding`; posted `2026-05-05T01:12:28.939164Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3043` Packet finding: PacketUrgency + PacketAttentionPolicy design response to rev_pkt_3042: 4 slices, mutation gate at agent_loop_policy.policy_for_turn, closes rev_pkt_3017 as side effect (source `rev_pkt_3043`; target `plan:MP-377`; posted `2026-05-05T01:19:11.898796Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3044` Packet finding: AMENDMENT to rev_pkt_3043: attention should be PREDICTIVE/CONTINUOUS not reactive/interrupt — peer attention sync + in-flight signaling so AI doesn't stop when work is obviously coming (source `rev_pkt_3044`; target `plan:MP-377`; posted `2026-05-05T01:23:03.681270Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3045` Packet finding: MP-385 role-first turn authority design + empirical drift evidence (current_slice stale by 30+ packets); closes rev_pkt_3011 via verify_mutation_grant() typed gate (source `rev_pkt_3045`; target `plan:MP-377`; posted `2026-05-05T01:30:03.198576Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3046` Packet finding: P0 EMPIRICAL: bridge_status event ALONE is Claude authoritative proof; transcript_proof.py:55-60 conjunction with prior local_command is over-strict and blocks UI-activated remote-control from promoting (source `rev_pkt_3046`; target `plan:MP-377`; posted `2026-05-05T01:40:49.133428Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3047` Packet finding: 🎯 SILVER BULLET: ~/.claude/sessions/<pid>.json bridgeSessionId is the live state file (source `rev_pkt_3047`; target `plan:MP-377`; posted `2026-05-05T02:00:34.099675Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3048` Packet finding: Architect verdict: rev_pkt_3047 silver bullet + RuntimeTruthSnapshot + GroundTruthProbeRunReceipt + gate check shipped as ONE connected pipeline (not 3 silos) — 57/57 tests pass — operator's connected-pipeline framing sat... (source `rev_pkt_3048`; target `plan:MP-377`; posted `2026-05-05T02:50:10.296838Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3049` Packet finding: Implemented rev_pkt_3048 connected RuntimeTruth pipeline (source `rev_pkt_3049`; target `runtime://runtime-truth-pipeline`; posted `2026-05-05T03:16:07.883347Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3054` Packet action request: Execute governed commit pipeline `pipeline-4010446f1057` (source `rev_pkt_3054`; target `remote_commit_pipeline:pipeline-4010446f1057`; posted `2026-05-05T03:38:15.086608Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3057` Packet finding: Research lane reply: thesis support (source `rev_pkt_3057`; target `plan:MP-377`; posted `2026-05-05T03:55:33.991074Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3058` Packet finding: Research lane reply: thesis support for graph-constrained execution (5-pass model + Semgrep taint analogy + snapshot caveat) (source `rev_pkt_3058`; target `plan:MP-377`; posted `2026-05-05T03:56:10.021582Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3059` Packet finding: Architect lane reply: GraphScopeProof typed-state design (operator-framed shared receipt + per-file evidence matrix + 5-step direction) (source `rev_pkt_3059`; target `plan:MP-377`; posted `2026-05-05T03:57:06.601837Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3060` Packet finding: Reviewer lane reply: GraphScopeProof authority-boundary review — 6 leak surfaces + 3 identity gaps + canonical gates that must not be bypassed (source `rev_pkt_3060`; target `plan:MP-377`; posted `2026-05-05T03:58:19.139770Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3063` Packet finding: Regression in ed79cd0e: 1/28 focused test fail — _runtime_io._session_state_proof attribute access broken by surgical-import refactor; minimal 1-line fix (source `rev_pkt_3063`; target `plan:MP-377`; posted `2026-05-05T04:21:35.267378Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3064` Packet action request: Codex defer-publication slice ready for Claude remote-control checkpoint handoff (source `rev_pkt_3064`; target `plan:MP-377`; posted `2026-05-05T13:14:36.229064Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3065` Packet finding: Reviewer-lane review of defer-publication slice (rev_pkt_3064 response): 6 architectural findings — naming, test coverage gap, brittle string-match in pending detection, authority-boundary guard ask (source `rev_pkt_3065`; target `plan:MP-377`; posted `2026-05-05T13:22:19.696065Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3066` Packet action request: Codex attention-window and publication-deferral follow-up ready for Claude review (source `rev_pkt_3066`; target `plan:MP-377`; posted `2026-05-05T13:47:41.241753Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3067` Packet finding: Reviewer-lane response to rev_pkt_3066: rev_pkt_3065 findings 1-5 VERIFIED in code+tests; 4 held peer_attention_window concerns folded in; finding 6 open as research-lane (source `rev_pkt_3067`; target `plan:MP-377`; posted `2026-05-05T13:57:49.922486Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3068` Packet finding: Architectural smell: typed next= field is not role-scoped — gives commands the caller cannot execute under remote-control + role + defer-publication. Operator-flagged. Slice A proposal in body. (source `rev_pkt_3068`; target `plan:MP-377`; posted `2026-05-05T14:44:55.919877Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3069` Packet finding: Smart bypass system architecture (operator-designed) + launcher-discipline interaction_mode drift bug + role-scoped next= sharpening + end-to-end test plan — 4 composing slices for next codex architectural session (source `rev_pkt_3069`; target `plan:MP-377`; posted `2026-05-05T15:17:20.013827Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3073` Packet finding: Reviewer/architect assessment of operator's GovernedExceptionLifecycle plan: agree with reframe (Exception→Repair→Proof→Learning > BypassReceipt-only); 7 concerns codex should resolve; claude's commitment as reviewer-arch... (source `rev_pkt_3073`; target `plan:MP-377`; posted `2026-05-05T23:09:31.952615Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3078` Packet finding: Operator extension to rev_pkt_3076: add MP377-P0-GUARD-CADENCE-S1 + GUARD-DEFERRAL-S1 + EXC-S1D physical-dogfood gate + T08F role-swap proof; do NOT expand EXC-S1; tier 0 always immediate; cadence is governance not bypass (source `rev_pkt_3078`; target `plan:MP-377`; posted `2026-05-06T02:13:42.296834Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3082` Packet finding: Dogfood receipt for rev_pkt_3081: boot-card route IS typed and fail-closed (CONFIRMED). session-resume returned authority_result=blocked with both blockers (code-shape debt + coordination_resync_required); did NOT call sl... (source `rev_pkt_3082`; target `plan:MP-377`; posted `2026-05-06T04:04:32.337589Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3084` Packet finding: 10 architectural observations from boot-card dogfood: packet lifecycle debt, reviewer_mode drift, ZRef format inconsistency, boot-card surface asymmetry, runtime spine partial contracts, routing field unification, capabil... (source `rev_pkt_3084`; target `plan:MP-377`; posted `2026-05-06T04:11:41.139267Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3086` Packet finding: Role-matrix dogfood Pass B: claude-as-implementer from CLAUDE.md; coordination rule verified (CODEX.md absent); both Pass A reviewer and Pass B implementer routed correctly; same blockers persist across role-lane switch (... (source `rev_pkt_3086`; target `plan:MP-377`; posted `2026-05-06T04:25:04.725930Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3087` Packet decision: Disposition for rev_pkt_3084 boot-card dogfood observations (source `rev_pkt_3087`; target `plan:MP-377`; posted `2026-05-06T04:26:44.928685Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3097` Packet decision: Reviewer disposition for commit 2b8397a5: ACCEPTED — clean bounded slice; closure proof for operator directive #4 SEALED via devctl push --execute (status=post_push_green, published_remote=True). Bypass posture RETIRED. ... (source `rev_pkt_3097`; target `plan:MP-377`; posted `2026-05-06T15:02:11.197421Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3127` Packet action request: Stage verified commit pipeline (source `rev_pkt_3127`; target `devctl_commit:e3f17d2501e035538ae4dfb41b493f7069faf902`; posted `2026-05-06T21:02:11.458329Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3131` Packet action request: IMPLEMENT NOW: rev_pkt_3125 deterministic selector — pick from queue, write code, write tests, governed commit + push. Code this session, not just plan amendments. (source `rev_pkt_3131`; target `plan:MP-377`; posted `2026-05-06T21:28:13.092297Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3134` Packet decision: Reviewer verdict on launch-lockup queue: launch authority recovery first (source `rev_pkt_3134`; target `plan:MP-377`; posted `2026-05-06T22:40:49.634039Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3136` Packet finding: Checkpoint blocked by code-shape guard (source `rev_pkt_3136`; target `guard:code-shape-guard`; posted `2026-05-06T23:27:17.110331Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3137` Packet finding: Launch reviewer-mode override cannot restore active_dual_agent (source `rev_pkt_3137`; target `dev/scripts/devctl/commands/review_channel/bridge_support.py:218`; posted `2026-05-06T23:28:02.133395Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3138` Packet finding: Tooling bundle blocked by strict docs-check (source `rev_pkt_3138`; target `guard:docs-check-strict-tooling`; posted `2026-05-06T23:30:28.865890Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3139` Packet finding: Discovery: voiceterm publisher daemon auto-spawns codex (gap #13 invocation provenance) + staged_index_budget_exceeded blocks legitimate large slices (NEW gap #14) (source `rev_pkt_3139`; target `plan:MP-377`; posted `2026-05-07T00:00:45.647308Z`; binding `plan_row`).
- [x] `PKT-BIND-REV-PKT-3140` Packet finding: Gap #15: typed bypass system exists (operator-override + lifecycle) but agents don't know — discoverability deficit; auto-surface in gate failures + startup-context (source `rev_pkt_3140`; target `plan:MP-377`; posted `2026-05-07T00:21:51.860365Z`; binding `plan_row`; closed by `TypedGateFailure` + `BypassReceipt` surfacing).
- [ ] `PKT-BIND-REV-PKT-3142` Packet action request: Remote-control checkpoint through Claude (source `rev_pkt_3142`; target `devctl_commit:e3f17d2501e035538ae4dfb41b493f7069faf902`; posted `2026-05-07T02:06:05.951794Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3144` Packet finding: rev_pkt_3142 blocked: typed authority split-in-mode unencoded; unified slice proposal for mode-isolated N-agent role assignment + pipeline architecture (source `rev_pkt_3144`; target `devctl_commit:e3f17d2501e035538ae4dfb41b493f7069faf902`; posted `2026-05-07T02:15:00.856852Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3145` Packet finding: Architectural addendum to rev_pkt_3144: parallel mode-derivation in startup_context.py:138-291 is the proximate cause of the 02:30:11 regression; fold steps A-D into your in-flight role-split work (source `rev_pkt_3145`; target `dev/scripts/devctl/runtime/startup_context.py:138-291`; posted `2026-05-07T02:39:34.937357Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3146` Packet finding: rev_pkt_3146: same-class regression broke devctl during your fix (circular import conductor_capability ↔ review_state_models); missing guards (projection-ownership canonicalization + cold-boot smoke); operator directive —... (source `rev_pkt_3146`; target `dev/scripts/devctl/runtime/conductor_capability.py`; posted `2026-05-07T02:50:16.539526Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3147` Packet finding: rev_pkt_3147: 6 integration regressions in rev_pkt_3144 slice prove the projection-ownership-registry primitive is the missing guard; promote rev_pkt_3146 generalized component 9 into its own implementable slice (typed co... (source `rev_pkt_3147`; target `dev/scripts/checks/check_projection_ownership.py`; posted `2026-05-07T03:30:47.498147Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3148` Packet finding: rev_pkt_3148: 3 independent Explore-agent investigations confirm operator hypothesis — bridge.md is the root smell. Round-trip self-derivation (heartbeat.py:99-151), 6+ gate decisions parsed from bridge content, 4 bridge-... (source `rev_pkt_3148`; target `dev/scripts/devctl/review_channel/heartbeat.py:99-151`; posted `2026-05-07T03:38:21.579710Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3149` Packet finding: rev_pkt_3149: 3 architectural smells from external code review not yet packeted — (1) over-mocking (~20-30 tests asserting call-counts/mock-args/private-state instead of contracts; ContractAssertionGuard fix), (2) 5-way o... (source `rev_pkt_3149`; target `dev/scripts/devctl/commands/review_channel/status_readiness.py:27`; posted `2026-05-07T04:10:24.206638Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3151` Packet finding: rev_pkt_3150: 2 Explore-agent investigations confirm the channel has zero relevance-aware checks at packet-send time — only structural (idempotency, routing, lifecycle, well-formedness). 'Should I send this packet?' is cu... (source `rev_pkt_3151`; target `dev/scripts/devctl/review_channel/packet_route_resolution.py:116-144`; posted `2026-05-07T04:33:38.025412Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3153` Packet finding: rev_pkt_3152 blocker: capability grants landed (mutation_owner=claude, repo.stage+repo.commit granted via mutation_owner source) but action-allowlist projection didn't propagate (vcs.stage|commit|push still in blocked_act... (source `rev_pkt_3153`; target `dev/scripts/devctl/runtime/authority_snapshot_actions.py`; posted `2026-05-07T05:29:10.502862Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3155` Packet action request: Role-scoped checkpoint repair for implementer lane (source `rev_pkt_3155`; target `devctl_commit:e3f17d2501e035538ae4dfb41b493f7069faf902`; posted `2026-05-07T06:43:16.684315Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3164` Packet finding: Codex checkpoint landed; reviewing guard/result-output automation gaps (source `rev_pkt_3164`; target `plan:MP377-P0`; posted `2026-05-07T18:39:50.851447Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3167` Packet finding: Codex patched smart-check selector and cold-boot enforcement gap (source `rev_pkt_3167`; target `plan:MP377-P0`; posted `2026-05-07T20:00:09.288854Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3168` Packet finding: pending_packets_to_me reader logic duplicated across 3 sites; consolidate into one shared agent_sync helper (source `rev_pkt_3168`; target `plan:MP-377`; posted `2026-05-07T20:34:03.576494Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3169` Packet finding: Checkpoint automation leaves sandbox stage denial and guard repair as manual agent decisions (source `rev_pkt_3169`; target `governance-checkpoint-automation`; posted `2026-05-07T20:45:32.026200Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3172` Packet finding: Required-action name strings duplicated as inline literals across 4+ sites; consolidate to canonical constants alongside GOVERNED_CHECKPOINT_COMMIT pattern (source `rev_pkt_3172`; target `plan:MP-377`; posted `2026-05-07T22:11:24.036574Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3173` Packet finding: CheckpointRepairAuthority stored in push_failure_transition field; add a typed checkpoint_repair_authority field on RemoteCommitPipelineContract to match the contract name (source `rev_pkt_3173`; target `plan:MP-377`; posted `2026-05-07T22:16:46.974226Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3174` Packet finding: Two typed-projection drift findings: work-board declares wt-a1/wt-a9 worktrees that don't exist on disk; docs-check strict-tooling fails for AGENTS.md/DEVELOPMENT.md/README.md after ebd484c1's 17 tooling changes (source `rev_pkt_3174`; target `plan:MP-377`; posted `2026-05-07T22:28:11.835389Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3179` Packet finding: Findings G+H landed as committed precedent in d7bd8e78; net-new Finding L: develop campaign projection disagrees with itself on global backlog count + auxiliary 17h stale (source `rev_pkt_3179`; target `plan:MP-377`; posted `2026-05-07T23:26:20.262416Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3180` Packet finding: Finding M: _effective_reviewer_mode 10-source fallback cascade in action_routing_publication_defer.py is the symptom of contradictions C1+C2+C3, not the fix; reduce to single authoritative source (source `rev_pkt_3180`; target `plan:MP-377`; posted `2026-05-07T23:30:56.196996Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3181` Packet finding: Finding N: system-map Connectivity Registry omits CheckpointRepairAuthority even though platform-contracts confirms it (78->79 closure); same surface-disagreement class as Finding L (source `rev_pkt_3181`; target `plan:MP-377`; posted `2026-05-07T23:34:12.995936Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3182` Packet finding: Finding O: review-channel post takes 45s; full.json projection is 24MB and likely serialized on every typed-state mutation; throttles feedback rate (source `rev_pkt_3182`; target `plan:MP-377`; posted `2026-05-07T23:36:02.150600Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3202` Packet finding: MP377-P0-T22AN-AC consolidated observations: 3 smells (string-substring command detection, watcher 300s timeout band-aid, override command not auto-surfaced) + 1 GOOD automation (typed suppress_artifact_writes default) — ... (source `rev_pkt_3202`; target `plan:MP-377`; posted `2026-05-08T12:51:14.531836Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3203` Packet finding: Meta-finding: packet system works (rev_pkt_3202 just landed, 36s) but 36s post latency persists post-Finding-O-fix; recommend fresh-agent multi-explorer audit of post path (profiling, projection write surface, event-appen... (source `rev_pkt_3203`; target `plan:MP-377`; posted `2026-05-08T12:53:46.843829Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3205` Packet decision: MP377-P0-T22AN-AC implementation ready for authorized checkpoint (source `rev_pkt_3205`; target `plan:MP-377`; posted `2026-05-08T13:04:04.144179Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3206` Packet finding: T22AN-AC follow-up: ack rev_pkt_3205 (impl complete + green); residual obs 5 (override reason hardcoded 'operator requested scoped edit-only repair' literal in scoped_operator_override_command — same stringly_typed class ... (source `rev_pkt_3206`; target `plan:MP-377`; posted `2026-05-08T13:07:23.264607Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3207` Packet decision: rev_pkt_3206 absorbed; T22AN-AC remains checkpoint-ready (source `rev_pkt_3207`; target `plan:MP-377`; posted `2026-05-08T13:10:37.459380Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3208` Packet action request: Checkpoint gate red after T22AN-AC review absorption (source `rev_pkt_3208`; target `plan:MP-377`; posted `2026-05-08T13:15:47.523589Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3210` Packet finding: Pytest runtime policy should bind startup_context latency before timeout bumps (source `rev_pkt_3210`; target `plan:MP-377`; posted `2026-05-08T13:24:39.888938Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3213` Packet finding: Architecture proposal: typed wake-packet contracts (SessionTerminationPolicy + kind=continuation_anchor/stop_anchor + task_complete_decision gate); body-text approach proved insufficient when codex went dormant despite an... (source `rev_pkt_3213`; target `plan:MP-377`; posted `2026-05-08T13:43:09.744496Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3221` Packet action request: Stage verified commit pipeline (source `rev_pkt_3221`; target `devctl_commit:7a797932f6d32f486d807d3cf8270f4759ce0f1d`; posted `2026-05-08T14:44:15.700396Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3225` Packet action request: Stage verified commit pipeline for MP-377 (source `rev_pkt_3225`; target `devctl_commit:7a797932f6d32f486d807d3cf8270f4759ce0f1d`; posted `2026-05-08T15:14:27.595937Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3233` Packet finding: bundle.tooling blocked for MP-377 stage_commit_pipeline (source `rev_pkt_3233`; target `plan:MP-377`; posted `2026-05-08T15:50:57.786043Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3235` Packet action request: Stage verified commit pipeline for MP-377 (source `rev_pkt_3235`; target `devctl_commit:7a797932f6d32f486d807d3cf8270f4759ce0f1d`; posted `2026-05-08T16:09:48.588822Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3241` Packet finding: Finding 7: claude-side ScheduleWakeup must fold into typed system (operator-named architectural gap); composes with current SessionTerminationPolicy slice as natural follow-on; extend AgentWorkBoardRow with monitor_cadenc... (source `rev_pkt_3241`; target `plan:MP-377`; posted `2026-05-08T17:09:06.210823Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3243` Packet action request: Stage and checkpoint MP-377 SessionTerminationPolicy slice (source `rev_pkt_3243`; target `devctl_commit:d31f125bc3468dd0ee84d39f4f597a6b4a2d6fc9`; posted `2026-05-08T17:18:11.220345Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3245` Packet finding: Continuation anchors can resume the wrong actor (source `rev_pkt_3245`; target `dev/scripts/devctl/runtime/session_termination_policy.py`; posted `2026-05-08T18:27:33.129201Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3246` Packet finding: Finding 8: claude permission gate must be typed-state-driven; R1+R2+R3 synthesized; honors test_collaboration_session.py claude_authority test refs (source `rev_pkt_3246`; target `plan:MP-377`; posted `2026-05-08T18:32:34.072027Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3247` Packet finding: Finding 8 + persistent loop: unified authority research synthesis (R1+R2+R3); VERIFY AGAINST MASTER PLAN first; honors test_collaboration_session.py claude_authority test refs (source `rev_pkt_3247`; target `plan:MP-377`; posted `2026-05-08T18:39:36.794317Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3248` Packet finding: Finding 9 PRIORITY-1 recover path silently spawned wrong agent type (source `rev_pkt_3248`; target `plan:MP-377`; posted `2026-05-08T18:54:29.623192Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3251` Packet finding: META-FINDING: STOP re-investigating; READ ingested typed plan FIRST — claude's Findings 7/8/9 likely duplicate existing MP377 rows; bridge.md = 90% root cause per operator (source `rev_pkt_3251`; target `plan:MP-377`; posted `2026-05-08T19:05:15.601829Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3252` Packet finding: META-FINDING (re-routed to live session 019e08f7): STOP re-investigating; READ ingested typed plan; bridge.md=90% root cause; Findings 7/8/9 likely duplicate existing MP377 rows (source `rev_pkt_3252`; target `plan:MP-377`; posted `2026-05-08T19:06:37.042168Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3255` Packet finding: rev_pkt_3245 still open: route-scoped continuation-anchor fix and regression missing (source `rev_pkt_3255`; target `dev/scripts/devctl/runtime/session_termination_policy.py`; posted `2026-05-08T19:12:24.087512Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3256` Packet action request: Stage verified commit pipeline (source `rev_pkt_3256`; target `devctl_commit:314cb43943c6ede8eed78534054dfe9bdb7623b4`; posted `2026-05-08T19:26:03.302118Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3261` Packet finding: Codex cannot take local coding authority while reviewer gate blocks implementation (source `rev_pkt_3261`; target `review-channel`; posted `2026-05-08T19:41:02.868545Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3272` Packet action request: BLOCKED: Codex reviewer cannot take raw commit authority; review_channel test target fails collection (source `rev_pkt_3272`; target `review-channel-test-verification`; posted `2026-05-08T20:39:01.352253Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3273` Packet finding: CONSOLIDATED FINDING — wake-anchor must compose with FULL mode matrix (NOT standalone); per-mode WakeAnchorPolicy in OperatorModePolicy; /wake-anchor slash command; subprocess watchdog; +6 architect-role observations from... (source `rev_pkt_3273`; target `plan:MP-377`; posted `2026-05-08T20:49:01.308063Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3275` Packet finding: Review-loop relaunch remains blocked after launch attempt (source `rev_pkt_3275`; target `review-channel-launch`; posted `2026-05-08T21:06:45.142907Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3276` Packet finding: Review-loop relaunch returned but runtime still not live (source `rev_pkt_3276`; target `review-channel-launch`; posted `2026-05-08T21:08:22.305727Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3277` Packet action request: Approval required: recover stale Claude implementer conductor (source `rev_pkt_3277`; target `claude-conductor`; posted `2026-05-08T21:11:18.355177Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3278` Packet finding: bundle.tooling blocked at docs-check (source `rev_pkt_3278`; target `bundle.tooling`; posted `2026-05-08T21:13:06.844662Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3279` Packet action request: Stage verified commit pipeline (source `rev_pkt_3279`; target `devctl_commit:b6a74ca6b1b4659620e450bf12087f0aca933532`; posted `2026-05-08T21:13:52.118824Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3284` Packet action request: BLOCKED: clear startup authority before Codex edits launcher (source `rev_pkt_3284`; target `startup_authority`; posted `2026-05-08T21:32:59.179115Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3289` Packet action request: Stage/commit checkpoint for MP-377 launcher recursion reducer fix (source `rev_pkt_3289`; target `devctl_commit:b6a74ca6b1b4659620e450bf12087f0aca933532`; posted `2026-05-08T22:01:32.586319Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3291` Packet finding: Focused devctl review-channel test fails under python3.11 interpreter token (source `rev_pkt_3291`; target `dev/scripts/devctl/tests/review_channel/test_review_channel.py`; posted `2026-05-08T22:33:11.936299Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3292` Packet finding: bundle.tooling failed after reviewer checkpoint; guard evidence blocks acceptance (source `rev_pkt_3292`; target `bundle.tooling`; posted `2026-05-08T22:45:13.493734Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3294` Packet finding: END-OF-CLAUDE-SESSION HANDOFF — full ledger consolidated (20 items: 2 FIXED-VERIFIED at a196ba90; 16 OPEN; 1 DEFERRED; 2 INFORMATIONAL); operator spawning new claude session; codex keeps iterating; new claude reads inbox ... (source `rev_pkt_3294`; target `plan:MP-377`; posted `2026-05-08T22:51:20.063507Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3295` Packet action request: Stage verified commit pipeline (source `rev_pkt_3295`; target `devctl_commit:a196ba9090e216d166967c6dd108698bd94fbd1f`; posted `2026-05-08T22:59:06.238868Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3298` Packet finding: claude held findings: #25 continuation_anchor actor-scope gap (session_termination_policy.py:152-183), #26 agent_sync_pending vs packet_lifecycle.archived disagreement; packet_transport_expiry.py audit COMPOSES_CLEANLY (source `rev_pkt_3298`; target `plan:MP-377`; posted `2026-05-09T00:23:01.062177Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3299` Packet finding: Checkpoint authority blocks further Codex edits (source `rev_pkt_3299`; target `checkpoint_authority`; posted `2026-05-09T00:43:51.896507Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3326` Packet action request: Run governed commit staging from remote-control lane (source `rev_pkt_3326`; target `devctl_commit:a196ba9090e216d166967c6dd108698bd94fbd1f`; posted `2026-05-09T04:00:50.509189Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3329` Packet finding: SYNTHESIS: 3-class architectural cascade (ledger #30 working-tree-mode + #32 lane-capability + #31 topology-vocab); claude REFUSES rev_pkt_3326 cross-role takeover; codex picks path (source `rev_pkt_3329`; target `plan:MP-377`; posted `2026-05-09T04:14:51.312843Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3331` Packet finding: LEDGER #34: graph_snapshots disk-spam parallel-surface (12GB, 760 files, ~2GB/day, 7 snapshots/hr same HEAD); writer ignores existing 1hr freshness cache; graph_snapshots orphaned from MANAGED_REPORT_SUBROOTS; Fix A idemp... (source `rev_pkt_3331`; target `plan:MP-377`; posted `2026-05-09T04:27:04.311313Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3332` Packet finding: LEDGER #33+#35 MERGED: peer-mind cross-visibility + work-boundary auto-emit + co-audit-mode formalization (3-audit cross-converged); 2 parallel liveness planes (bridge poll-age vs agent-mind cursor); fix shape A=tagged wo... (source `rev_pkt_3332`; target `plan:MP-377`; posted `2026-05-09T04:30:28.916605Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3334` Packet decision: CONVERGE on rev_pkt_3333: Class A-prime fix shape APPROVED — preflight import_index_atomicity must read staged tree (git show <tree>:<path>), startup-authority live-worktree behavior unchanged; same architectural class a... (source `rev_pkt_3334`; target `plan:MP-377`; posted `2026-05-09T04:50:04.155434Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3338` Packet decision: APPROVAL REFRESH PATH: rerun devctl commit (pipeline-061b962aeb8e abandoned); architectural approval from rev_pkt_3334 persists for tree 6d876b; new pipeline auto-emits approval_request which /remote-control flow handles... (source `rev_pkt_3338`; target `plan:MP-377`; posted `2026-05-09T05:06:43.338900Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3342` Packet decision: OUTCOME — Class A + Class A-prime FIXED-VERIFIED at HEAD 3ce8a67d (was a196ba90); 14 files committed; live-test probes 3/3 green; ledger #30 + #32-adjacent + Class A-prime atomicity all live in tree (source `rev_pkt_3342`; target `plan:MP-377`; posted `2026-05-09T05:10:54.515984Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3344` Packet decision: CONVERGE rev_pkt_3343: Class A-double-prime fix APPROVED — governed push validates against authorized commit_sha when pipeline.state=commit_recorded; MANDATORY branch-identity invariants preserved per feedback_branch_ide... (source `rev_pkt_3344`; target `plan:MP-377`; posted `2026-05-09T05:13:15.602717Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3346` Packet decision: CONVERGE rev_pkt_3345: Class A-triple-prime fix APPROVED (projection sync compares before/after dirty sets, only fails on repair-phase-introduced paths) + META-FINDING: PipelineScopeValidationLeak class — 4 sequential in... (source `rev_pkt_3346`; target `plan:MP-377`; posted `2026-05-09T05:23:36.390329Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3348` Packet decision: CONVERGE rev_pkt_3347: Class A-quadruple-prime APPROVED (5th instance same class) + META-FINDING ELEVATED — PipelineScopeValidationLeak now empirically validated (source `rev_pkt_3348`; target `plan:MP-377`; posted `2026-05-09T05:32:57.501568Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3350` Packet decision: CONVERGE rev_pkt_3349: Class A-sextuple-prime APPROVED (6th instance) + STRONG MUST-PIVOT — ValidationScope enum is overdue; band-aid cost now > systemic cost; concrete pivot path proposed for next slice after this band-... (source `rev_pkt_3350`; target `plan:MP-377`; posted `2026-05-09T05:47:30.042602Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3351` Packet action request: Run governed commit staging from remote-control lane (source `rev_pkt_3351`; target `devctl_commit:18c1db4ba0d09c825a06f27271a8738b7ed28004`; posted `2026-05-09T05:58:23.236747Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3357` Packet decision: CONFIRM rev_pkt_3356: ValidationScope systemic boundaries CONFIRMED — typed scope object + thread through pipeline callers + standalone strictness preserved + AST probe to prevent recurrence; mandatory regression guards ... (source `rev_pkt_3357`; target `plan:MP-377`; posted `2026-05-09T07:23:16.072966Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3370` Packet action request: Run governed commit staging from remote-control lane (source `rev_pkt_3370`; target `devctl_commit:2164a20fef50051b3a9e8932fd7e7d83d306e156`; posted `2026-05-09T12:40:46.864176Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3373` Packet decision: POST-COMMIT SYNTHESIS RE-PROBE on commit 6ebd631e: 5 typed-authority modules landed; GAP 2 (9 fail-closed gates with hardcoded active_dual_agent literal) + GAP 1 (_TOPOLOGY_TERMS no plan owner) remain for sequel commit (source `rev_pkt_3373`; target `plan:MP-377`; posted `2026-05-09T13:34:08.952393Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3374` Packet decision: POST-COMMIT SYNTHESIS RE-PROBE 6ebd631e (source `rev_pkt_3374`; target `plan:MP-377`; posted `2026-05-09T13:34:42.110665Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3375` Packet finding: PUSH BLOCKED: role-topology commit preflight failures (source `rev_pkt_3375`; target `plan:MP-377`; posted `2026-05-09T13:59:28.486670Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3376` Packet action request: Run governed commit staging from remote-control lane (source `rev_pkt_3376`; target `devctl_commit:6ebd631e4d551c560513ca2a8e77afb140a2f346`; posted `2026-05-09T14:26:01.535759Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3385` Packet decision: UNIFIED SYNTHESIS folds rev_pkt_3374 (topology GAP 2) with packet-attention architecture audit: 1360-packet backlog + 638 expired + 14% ack rate. Existing plan rows (PACKET-INTAKE-SCHEDULER-S1 in_progress + ROLE-MATRIX/R... (source `rev_pkt_3385`; target `plan:MP-377`; posted `2026-05-09T15:22:46.842973Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3392` Packet finding: GAP D recovery bug: pipeline abandon receipt resurrected by projection refresh (source `rev_pkt_3392`; target `plan:MP-377`; posted `2026-05-09T16:08:06.095572Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3402` Packet decision: SENIOR-ARCHITECT VERDICT TASK_COMPLETE 17:36:59Z GAP 2 slice: APPROVED-WITH-FOLLOW-UP. Multi-agent audit confirmed no duplication + good composition + tests valid. STILL-WRONG: 9 fail-closed gates hardcode active_dual_ag... (source `rev_pkt_3402`; target `plan:MP-377`; posted `2026-05-09T17:44:11.411743Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3430` Packet decision: PLAN_REVIEW_RESPONSE for codex's Streamed Sprouting Pizza: Remote-Control Reproduction Gate proposal — verdict ACCEPT-WITH-AMENDMENTS. 3 multi-agent audits done. Phase 2.5 composes with T22Y-J/RC-PAIR-S1/EXC-S1 (in_progr... (source `rev_pkt_3430`; target `plan:MP-377`; posted `2026-05-10T03:23:28.201233Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3431` Packet finding: Local Codex implementation blocked; Claude-spawned remote-control Codex proof required (source `rev_pkt_3431`; target `remote-control-reproduction-gate`; posted `2026-05-10T03:26:51.691702Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3432` Packet decision: CLAUDE TASK_STARTED — reviewer/architect cadence active in Phase 4 execution. Operator-with-claude state. Acks codex TASK_COMPLETE 03:27:21Z + failed-post correctly-not-bypassed. Claude clearing cut_checkpoint gate next.... (source `rev_pkt_3432`; target `plan:MP-377`; posted `2026-05-10T03:29:45.569337Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3433` Packet decision: CODEX RESPONSE — AGREE with Claude amendments; add auto peer-watch loop defect (source `rev_pkt_3433`; target `plan:MP-377`; posted `2026-05-10T03:32:11.941683Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3434` Packet decision: FOCUS CORRECTION — ignore ingest.md; stay on streamed-sprouting-pizza + remote-control proof (source `rev_pkt_3434`; target `plan:MP-377`; posted `2026-05-10T03:32:59.802091Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3435` Packet decision: CLAUDE ACK + REVIEW_ACCEPTED for rev_pkt_3433 (AGREE-WITH-ONE-ADDITION) + rev_pkt_3434 (FOCUS CORRECTION ignore ingest.md). Phase 2 acceptance design fully agreed. AutoPeerWatchOnBlockedImplementation defect accepted; co... (source `rev_pkt_3435`; target `plan:MP-377`; posted `2026-05-10T03:37:24.106172Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3436` Packet decision: CLAUDE TASK_PROGRESS — spawning 3 multi-agent architecture audits on codex's projection-writer refactor (one prepared bundle payload approach). Per protocol + codex's own requirement; please hold commit until audit verdi... (source `rev_pkt_3436`; target `plan:MP-377`; posted `2026-05-10T03:42:47.162878Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3437` Packet decision: CLAUDE REVIEW_ACCEPTED on projection-writer refactor — APPROVE-WITH-AUDIT-FINDINGS. 3 multi-agent audits complete. Verdict: refactor architecturally correct + composes with 5 existing typed contracts. KEY FINDING: produc... (source `rev_pkt_3437`; target `plan:MP-377`; posted `2026-05-10T03:45:40.378781Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3438` Packet decision: CODEX TASK_PRODUCED projection-writer refactor + peer-watch fix ready for Claude physical review (source `rev_pkt_3438`; target `plan:MP-377`; posted `2026-05-10T03:50:04.265939Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3439` Packet decision: CLAUDE REVIEW_FAILED (partial) on rev_pkt_3438 — refactor PASSED structurally + 6/6 tests + 5 contracts compose, BUT check_review_surface_consistency still RED on Hypothesis 3 (startup_context.py:329-331 computes fresh s... (source `rev_pkt_3439`; target `plan:MP-377`; posted `2026-05-10T03:59:42.993654Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3440` Packet finding: CLAUDE 3-AUDIT VERDICT on collaboration_profile module — PATH IS RIGHT. 1 amendment: role-binding source. PLUS: review_surface_consistency.py is now GREEN per claude live-test (the original Phase 2 blocker is closed). Sli... (source `rev_pkt_3440`; target `plan:MP-377`; posted `2026-05-10T04:11:48.601951Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3441` Packet finding: OPERATOR FEATURE ASK + CLAUDE peer-watch ack: operator wants stop-at-packet / stop-at-MP-row flag in agent_sync mode. Plus claude saw codex's mode rename to agent_sync + --role-count, and saw codex's peer-read of claude's... (source `rev_pkt_3441`; target `plan:MP-377`; posted `2026-05-10T04:21:05.380058Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3442` Packet finding: USE-THIS-SYSTEM (8-point #5): SessionTerminationPolicy + STOP_ANCHOR_PACKET_KIND already exist for operator's stop-at-packet/MP feature ask. NO NEW CONTRACT needed. Plus audit on agent_sync rename: GOOD with 1 cleanup (de... (source `rev_pkt_3442`; target `plan:MP-377`; posted `2026-05-10T04:22:55.177731Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3443` Packet decision: CLAUDE PHYSICAL_TEST GREEN — review_surface_consistency now ok=True (Hypothesis 3 fix landed). 89/89 tests pass: test_projection_bundle 6 + test_check_review_surface_consistency 28 + test_agent_loop_decision 34 + test_sc... (source `rev_pkt_3443`; target `plan:MP-377`; posted `2026-05-10T04:29:07.421647Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3444` Packet decision: CLAUDE TASK_PROGRESS @ 04:38Z — both agents agree review_surface_consistency GREEN with one snapshot across startup/review_state/compact/commit_pipeline. Codex msg confirms unified producer-tick fix landed; claude live t... (source `rev_pkt_3444`; target `plan:MP-377`; posted `2026-05-10T04:39:01.568369Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3445` Packet decision: CODEX TASK_PRODUCED agent_sync + projection atomicity fixes ready for Claude reproduction (source `rev_pkt_3445`; target `plan:MP-377`; posted `2026-05-10T04:42:59.600274Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3446` Packet finding: CLAUDE REVIEW + AUDIT: rev_pkt_3445 acked. LIVE PHYSICAL-TEST FROM REMOTE-CONTROL SESSION 79f22d9c: review_surface_consistency ok ✓, docs-check ok ✓, 50/50 tests ✓ (test_projection_bundle 6, test_check_review_surface 28, ... (source `rev_pkt_3446`; target `plan:MP-377`; posted `2026-05-10T04:48:50.420997Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3447` Packet decision: CLAUDE WAKE-PACKET (8-point #4) @ 04:53Z — codex TASK_COMPLETE 9min ago, silent since. review_surface still GREEN cycle 5. Ack codex's task_complete + bidirectional peer-watch confirmed (codex peer-read claude's cursor 3... (source `rev_pkt_3447`; target `plan:MP-377`; posted `2026-05-10T04:54:50.819702Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3449` Packet decision: FRESH-CODEX HAND-OFF + EXPLICIT WORK FOCUS — operator says codex is drifting. Claude directing 6-priority work list (PRIORITY 1: stop_anchor target validation; 2: CollaborationSessionState wire; 3-6: derive_wake/FindingB... (source `rev_pkt_3449`; target `plan:MP-377`; posted `2026-05-10T05:10:51.589248Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3450` Packet decision: AGENT_SYNC CONNECTIVITY: stop_anchor target validation proposal (source `rev_pkt_3450`; target `plan:MP-377`; posted `2026-05-10T05:12:19.502547Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3451` Packet decision: FRESH-CODEX HAND-OFF (2nd respawn) — claude detected new codex session 019e104c after 019e103d was replaced. Same 6-priority work focus list. NOTE: codex just hit smell #001 live (tried --role coding-agent, had to retry ... (source `rev_pkt_3451`; target `plan:MP-377`; posted `2026-05-10T05:15:28.814790Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3454` Packet decision: CLAUDE REVIEW VERDICT rev_pkt_3452: APPROVE-WITH-FOLLOWUP. Reviewer physical-test green (test_development_team 19/19; invalid solo case EXIT 1 ok=False status=blocked; valid agent_sync case EXIT 0 ok=True). Independent c... (source `rev_pkt_3454`; target `plan:MP-377`; posted `2026-05-10T05:32:32.658518Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3456` Packet decision: CLAUDE Priority 2 PROPOSAL VERDICT: ACCEPT — composition clean. All 8 typed surfaces verified at file:line; _collaboration_profile_session already exists at profiles.py:478 (zero new redactor needed). Codex authorized to... (source `rev_pkt_3456`; target `plan:MP-377`; posted `2026-05-10T05:39:33.678619Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3458` Packet decision: AGENT_SYNC CONNECTIVITY: derive_wake_evidence_for_actor wiring proposal (source `rev_pkt_3458`; target `plan:MP-377`; posted `2026-05-10T05:52:37.215515Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3459` Packet decision: CLAUDE REVIEW VERDICT rev_pkt_3457: APPROVE. Reviewer physical-test green (test_development_team 21/21; CLI agent_sync MD render shows full collaboration_session block — owner/authority/peer_review/arbitration/ready_gate... (source `rev_pkt_3459`; target `plan:MP-377`; posted `2026-05-10T05:58:19.320224Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3460` Packet decision: AGENT_SYNC CONNECTIVITY: workflow packet-kind wiring proposal (source `rev_pkt_3460`; target `plan:MP-377`; posted `2026-05-10T06:08:08.124850Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3462` Packet decision: CLAUDE Priority 2.5 PROPOSAL VERDICT: ADJUST (ACCEPT-WITH-CRITICAL-FOLLOWUP). Audit 5/5 ACCEPT for kind extension; 1/1 CRITICAL: Slice A gap #6 state-extension at packet_lifecycle_state.py:10-36 missing — without it, age... (source `rev_pkt_3462`; target `plan:MP-377`; posted `2026-05-10T06:15:05.721768Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3468` Packet decision: BRIDGE PROJECTION REPAIR: remove bridge-derived authority path (source `rev_pkt_3468`; target `plan:MP-377`; posted `2026-05-10T07:10:11.072590Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3469` Packet decision: CODEX — BACK TO THE PLAN. You drifted into bridge-as-authority cycles 14-16 (5 file violations packeted in rev_pkt_3466 + rev_pkt_3467). Slice C target per streamed-sprouting-pizza.md is the 9 active_dual_agent gate site... (source `rev_pkt_3469`; target `plan:MP-377`; posted `2026-05-10T07:11:01.230497Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3471` Packet decision: PROVIDER LITERAL CORRECTION: ACK filter must use typed role vocabulary (source `rev_pkt_3471`; target `plan:MP-377`; posted `2026-05-10T07:16:00.420785Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3475` Packet decision: CODEX — TYPED ROOT-CAUSE FOUND. ACK freshness authority is typed at ack_freshness_authority.py:11 (is_implementer_ack_current) + event_projection_ack_state.py:17-52 (preserve_reducer_implementer_ack outputs implementer_a... (source `rev_pkt_3475`; target `plan:MP-377`; posted `2026-05-10T07:24:12.222614Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3478` Packet decision: OPERATOR ARCHITECTURAL RECOVERY FRAMEWORK + claude parallel-agent validation. Operator's invariant: bridge=projection, typed=authority, projections do NOT feed authority back into runtime. 6-step recovery: (1) freeze bri... (source `rev_pkt_3478`; target `plan:MP-377`; posted `2026-05-10T07:30:42.160500Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3482` Packet decision: CODEX BOTH CONTRADICTIONS RESOLVED. Conflict A (_bridge_poll validation): KEEP validate_live_bridge_contract(snapshot, typed_current_session=...) IFF typed_current_session supplied; rev_pkt_3478 LANE B guard supersedes r... (source `rev_pkt_3482`; target `plan:MP-377`; posted `2026-05-10T07:38:54.556420Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3483` Packet decision: CODEX GUARD SCOPE CORRECTION — operator's 10-point plan supersedes rev_pkt_3482 narrowing. Your 07:41:03Z agent_msg said you're applying check_bridge_projection_only.py as 'enforced-regression guard for the surfaces alre... (source `rev_pkt_3483`; target `plan:MP-377`; posted `2026-05-10T07:43:10.322644Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3485` Packet decision: BEFORE-EDIT CHECKPOINT: rev_pkt_3483 scope correction; pausing narrow guard and validating repo-wide guard plan (source `rev_pkt_3485`; target `plan:MP-377`; posted `2026-05-10T07:46:04.216785Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3492` Packet decision: CODEX rev_pkt_3490 acked. Architectural reframing GOOD but scope-creep risk: LANE G concrete actions ARE the enforcement layer. The 3 guards (check_bridge_projection_only repo-wide + check_provider_authority_literals + c... (source `rev_pkt_3492`; target `plan:MP-377`; posted `2026-05-10T08:01:34.817197Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3495` Packet decision: ARCHITECTURE PROPOSAL: axes-first replacement for overloaded single_agent/dual_agent topology literals (source `rev_pkt_3495`; target `plan:MP-377`; posted `2026-05-10T08:21:54.975284Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3496` Packet decision: AGREEMENT with rev_pkt_3494: helper-wrap-literal IS smell. Plan section 6 corrected; smell #019 logged. Typed-topology-vocabulary direction confirmed: runtime authority gates consume LiveRoleTopology multi-provider tuple... (source `rev_pkt_3496`; target `plan:MP-377`; posted `2026-05-10T08:24:25.615334Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3499` Packet decision: MANDATE: stopping without typed continuation is a control-plane smell; enforce role-neutral continuation receipts (source `rev_pkt_3499`; target `plan:MP-377`; posted `2026-05-10T08:33:22.103186Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3502` Packet decision: CRITICAL FIX APPLIED 08:42Z — devctl.py was BROKEN by missing reviewer_mode_is_single_agent function in runtime/reviewer_mode.py (your cycle 17 extraction missed it). 3 consumers broken at import time: operator_context.p... (source `rev_pkt_3502`; target `plan:MP-377`; posted `2026-05-10T08:44:12.002120Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3504` Packet finding: FINDING: helper-wrapped reviewer-mode/topology literals remain in runtime authority paths (source `rev_pkt_3504`; target `plan:MP-377`; posted `2026-05-10T08:51:03.209613Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3505` Packet decision: CLAUDE CONSOLIDATION rev_pkt_3500/3501/3503 acked. Codex's 3-packet synthesis CONVERGENT with reviewer rev_pkt_3497 + plan section 6 + operator's invariant. 4-axis split (actor/role occupancy + role vocabulary + authorit... (source `rev_pkt_3505`; target `plan:MP-377`; posted `2026-05-10T08:53:41.414676Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3506` Packet finding: BLOCKER: startup authority import-index atomicity requires live-tree mutator action (source `rev_pkt_3506`; target `plan:MP-377`; posted `2026-05-10T08:58:23.878290Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3508` Packet finding: CLAUDE SELF-ITERATING AUDIT on smell #024 (typed-state-not-self-updating, operator-elevated 08:55Z): 6 INSTANCES found across codebase. INSTANCE #1 continuation.py:40-48 controller stale after ack; #2 startup_blocker_deci... (source `rev_pkt_3508`; target `plan:MP-377`; posted `2026-05-10T09:00:18.487275Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3510` Packet decision: CLAUDE CONSOLIDATION rev_pkt_3509 acked. 3-way thesis convergence (codex audit + claude audit 1 thesis-evaluation + claude audit 2 resumability/receipts) — event log = authority, ReviewChannel reducer = only producer, pr... (source `rev_pkt_3510`; target `plan:MP-377`; posted `2026-05-10T09:09:27.596886Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3511` Packet finding: BLOCKED: edit-only override cannot repair import-index atomicity because vcs.stage is blocked (source `rev_pkt_3511`; target `plan:MP-377`; posted `2026-05-10T09:14:06.602555Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3513` Packet decision: ack rev_pkt_3511 + decision: task_blocked option + YouTube research outcome + smell #024 dogfood-LIVE + composability check (source `rev_pkt_3513`; target `plan:MP-377`; posted `2026-05-10T09:22:34.930407Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3514` Packet finding: BLOCKED: import_index_atomicity repair exceeds edit-only override scope; task_blocked kind missing (source `rev_pkt_3514`; target `plan:MP-377`; posted `2026-05-10T09:25:34.584253Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3515` Packet decision: READ_ONLY_SYNTHESIS: typed topology, import atomicity, packet freshness (source `rev_pkt_3515`; target `plan:MP-377`; posted `2026-05-10T09:32:48.469141Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3516` Packet finding: DOUBLE-LAYER AUDIT RESULTS: smell #024 INSTANCE #7 root cause = review_packet_inbox.py:313-317 stricter filter; 1-line fix + smell #026 + review_accepted orphan finding + 2 typed-invariant tests (source `rev_pkt_3516`; target `plan:MP-377`; posted `2026-05-10T09:32:59.271844Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3517` Packet decision: USE-THIS-SYSTEM: typed authority surfaces MP377-P0-CHECKPOINT-AUTOMATION-S1 slice composes directly with your rev_pkt_3514 Option 2 typed-checkpoint repair path; read-only audit work scope for codex within current edit-o... (source `rev_pkt_3517`; target `plan:MP-377`; posted `2026-05-10T09:47:24.162643Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3520` Packet finding: FINDING: Claude packet attention surfaces disagree on rev_pkt_3499 vs rev_pkt_3519 (source `rev_pkt_3520`; target `plan:MP-377`; posted `2026-05-10T10:04:13.298576Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3524` Packet finding: FINDING: review-channel history latest window omits rev_pkt_3523 while direct show and inbox see it (source `rev_pkt_3524`; target `plan:MP-377`; posted `2026-05-10T10:25:45.901552Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3535` Packet finding: FINDING: history latest window omits live rev_pkt_3534 while Claude inbox sees it (source `rev_pkt_3535`; target `plan:MP-377`; posted `2026-05-10T11:17:36.542284Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3540` Packet finding: ROOT CAUSE smell #032: 73-min bilateral stall; eventbus substrate design closes smell #024 R3 + #025 R1 + #032 R2 simultaneously; STEP 4 scope revised to land substrate first (source `rev_pkt_3540`; target `plan:MP-377`; posted `2026-05-10T12:43:52.512666Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3542` Packet finding: FINDING: reviewer-role lane was granted implementation.edit under operator override (source `rev_pkt_3542`; target `plan:MP-377`; posted `2026-05-10T12:49:48.572994Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3552` Packet finding: FINDING: smell #032 RECURRENCE after STEP 5 (codex task_complete at 13:30:21Z preceded review_accepted by 90s); STEP 6 priority reorder — eventbus substrate ELEVATED from STEP 7+ to STEP 6 (source `rev_pkt_3552`; target `plan:MP-377`; posted `2026-05-10T13:35:25.506892Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3553` Packet decision: USE-THIS-SYSTEM rev_pkt_3552 + STEP 6 architectural intelligence (6 fix shapes pre-identified): smell #032 R2 eventbus substrate ELEVATED to PRIMARY; agent_loop_proof_packets.py:24-28 P1/P4 fix; OperatorOverrideAttestati... (source `rev_pkt_3553`; target `plan:MP-377`; posted `2026-05-10T16:19:52.602545Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3554` Packet finding: TESTABLE-ARTIFACT GAP: STEP 1-5 has 122 passing tests but ZERO operator-runnable demo; MP377-P0-T22Y-L remote-control gate still [ ] INCOMPLETE; need devctl demo verify-override + verify-checkpoint-automation CLI commands (source `rev_pkt_3554`; target `plan:MP-377`; posted `2026-05-10T16:22:32.806666Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3564` Packet decision: ARCHITECTURE DECISION: close final-response/anchor/packet loop through existing controller (source `rev_pkt_3564`; target `plan:MP-377`; posted `2026-05-10T17:21:42.061794Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3565` Packet decision: DECISION: bilateral-protocol mandate evolution; ingest into typed-state plan as MP377-AGENT-LOOP-BILATERAL-PROTOCOL-S1 + Gap A/B/C closures; codex designs BEST approach (Option 1 hybrid 7-property typed contract recommen... (source `rev_pkt_3565`; target `plan:MP-377`; posted `2026-05-10T17:22:04.658092Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3566` Packet decision: CODEX RESPONSE rev_pkt_3565: bilateral protocol must sit on session-iteration controller (source `rev_pkt_3566`; target `plan:MP-377`; posted `2026-05-10T17:24:54.539973Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3569` Packet decision: DECISION: System consolidation architectural fix (3 NEW typed contracts) — SystemAuditSwarmReceipt + check_uniqueness_invariants + check_composability_invariant; closes honor-system gap; institutionalizes adversarial swa... (source `rev_pkt_3569`; target `plan:MP-377`; posted `2026-05-10T17:42:55.075990Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3587` Packet finding: Checkpoint required before MP-377 continuation (source `rev_pkt_3587`; target `plan:MP-377`; posted `2026-05-10T21:35:49.999443Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3589` Packet decision: Operator edit-only override for MP-377 continuation (source `rev_pkt_3589`; target `plan:MP-377`; posted `2026-05-10T21:41:59.561063Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3596` Packet decision: Forward synthesis: recommend MP377-CORRELATION-ID-SPINE-S1 next; claude-side parallel task = regenerate projection artifacts to close smell #046; smell convergence map for #042/#049 + #046/#048; 3 alternative slices if c... (source `rev_pkt_3596`; target `plan:MP-377`; posted `2026-05-10T21:58:45.582934Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3599` Packet decision: Pre-decision agent-mind synthesis for MP377-CORRELATION-ID-SPINE-S1 you just opened at 22:21Z: 5 composability anchors + 6 smells (#042/#044/#046/#050/#051/#052 + codex #048/#049) convergent on correlation-spine + 4 pre-... (source `rev_pkt_3599`; target `plan:MP-377`; posted `2026-05-10T22:22:57.006652Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3609` Packet finding: Cycle 137 retraction + situational-awareness packet: smell #052 RETRACTED (I miscounted subagent rollouts as separate sessions); smell #053 NEW (agent-mind doesn't surface parent-vs-subagent distinction); 'Hilbert' subage... (source `rev_pkt_3609`; target `plan:MP-377`; posted `2026-05-10T22:52:45.841575Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3612` Packet decision: DUAL AUDIT SYNTHESIS (Agent A Hilbert cross-validation + Agent B independent duplicate hunt): 12 verified-open provider-string-as-authority sites + 1 silent bug at agent_sync_packet_classification.py:44 + 1 critical smel... (source `rev_pkt_3612`; target `plan:MP-377`; posted `2026-05-10T23:15:02.377411Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3615` Packet finding: GROUND-TRUTH CONFIRMED 1-line gap in your patch: agent_loop_decision.py:87-93 task_complete_decision() call MISSING packet_attention arg; new pending_review_packet + continuation_anchor_missing branches at 94-97 WILL NEVE... (source `rev_pkt_3615`; target `plan:MP-377`; posted `2026-05-10T23:31:23.850731Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3616` Packet finding: Verified import path for the 1-line fix in my previous packet: implementer_packet_attention_for lives at dev/scripts/devctl/review_channel/current_session_event_state.py:11+87+102 (source `rev_pkt_3616`; target `plan:MP-377`; posted `2026-05-10T23:32:32.149370Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3620` Packet finding: ROOT CAUSE of dogfood failure: orchestration_models.py:84-85 DevelopmentContinuationRequiredSignal defaults final_response_allowed=True + final_response_gate_allowed=True; permissive defaults bypass your TaskCompleteDecis... (source `rev_pkt_3620`; target `plan:MP-377`; posted `2026-05-10T23:44:26.741546Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3625` Packet finding: Operator-naming directive: drop 'wake' from continue_to_wake_packet_goal + watcher-auto-trigger architectural gap (operator prompted 3 times) + 3-tranche plan (source `rev_pkt_3625`; target `plan:MP-377`; posted `2026-05-11T00:15:06.945362Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3627` Packet finding: 3-agent synth: urgent packets→plan ingestion + continuation_goal output resolution + supersession; ALL via existing typed surfaces (no new authority). 3 file edits + 5 MP-377 row amendments. (source `rev_pkt_3627`; target `plan:MP-377`; posted `2026-05-11T00:58:40.419518Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3628` Packet finding: 3-agent synth on PlanPositionAck: Agent C wins (smallest surface) — 3 fields on AuthoritySnapshot + safe_to_continue gates symmetric to FinalResponseGateResult; terminology contract closes poison-literal gap; operator-fra... (source `rev_pkt_3628`; target `plan:MP-377`; posted `2026-05-11T01:18:04.877911Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3636` Packet action request: Run governed commit staging from remote-control lane (source `rev_pkt_3636`; target `devctl_commit:267ccfd6a6928c3f9b0f5f1230151aedf89eb6aa`; posted `2026-05-11T03:26:46.522809Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3637` Packet finding: Auto-snapshot recursive chain: push_preflight_projection.py:101 creates snapshot-of-snapshot commits unbounded; 6 chained commits in current backlog, root-cause file:line + 4 fix options in body (source `rev_pkt_3637`; target `dev/scripts/devctl/commands/vcs/push_preflight_projection.py:101`; posted `2026-05-11T03:38:31.258668Z`; binding `plan_row`).
  - 2026-05-11 follow-up under `MP377-P1-T07`: startup/work-intake push-preflight projections now mirror governed push fail-fast publication semantics and managed projection receipt cleanup no-ops on already-managed ReviewSnapshot/generated-surface receipt heads, closing the operator-observed receipt-loop/polling smell without creating a new authority surface.
- [ ] `PKT-BIND-REV-PKT-3645` Packet finding: Claude-reviewer regresses to passive ScheduleWakeup polling instead of active in-turn auditing (smell #008+#009 recurrence at meta-level). Audit coverage this session: 1 fired / 12 expected = 8.3%. Operator directed this ... (source `rev_pkt_3645`; target `dev/scripts/devctl/runtime/ground_truth_probe_receipt.py`; posted `2026-05-11T06:57:09.576319Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3646` Packet finding: Claude-reviewer regresses to passive ScheduleWakeup polling instead of active in-turn auditing (smell #008+#009 recurrence at meta-level). Operator: 'falling back to polling is a massive code smell that needs to be sent t... (source `rev_pkt_3646`; target `dev/scripts/devctl/review_channel/event_reducer.py:387`; posted `2026-05-11T06:58:44.830301Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3647` Packet finding: PRIMARY: Claude-reviewer passive-polling regression (smell #008+#009 meta-level; audit coverage 1/12=8.3%; operator-mandated). SECONDARY: D-ValueCoercion cluster extended +3 (codex's uncommitted 7th-slice introduced new i... (source `rev_pkt_3647`; target `dev/scripts/devctl/commands/vcs/commit_action_request_revision.py:38`; posted `2026-05-11T07:03:09.693722Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3648` Packet finding: PRIMARY: Claude-reviewer passive-polling regression (smell #008+#009 meta-level; operator-mandated). SECONDARY: D-ValueCoercion +4 inline helpers in 7th slice (3 _text + 1 _mapping at revision/pipeline/lifecycle_gate/bund... (source `rev_pkt_3648`; target `dev/scripts/devctl/commands/vcs/commit_action_request_revision.py:38`; posted `2026-05-11T07:05:08.726840Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3649` Packet finding: PRIMARY: Claude-reviewer passive-polling regression (smell #008+#009 meta-level; operator-mandated 06:54Z). SECONDARY: D-ValueCoercion +4 inline helpers in uncommitted 7th slice (revision.py:31 + pipeline.py:53 + lifecycl... (source `rev_pkt_3649`; target `dev/scripts/devctl/commands/vcs/commit_action_request_revision.py:31`; posted `2026-05-11T07:10:27.027836Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3650` Packet action request: Run governed commit staging from remote-control lane (source `rev_pkt_3650`; target `devctl_commit:87f8b2dd2d59ec2250cb5f891091894bf3417294`; posted `2026-05-11T07:14:00.105486Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3656` Packet action request: Run governed commit staging from remote-control lane (source `rev_pkt_3656`; target `devctl_commit:9318cfd00b31e028c7e09653f93f75ccab94020f`; posted `2026-05-11T09:34:02.760321Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3663` Packet action request: Run governed commit staging from remote-control lane (source `rev_pkt_3663`; target `devctl_commit:5b5c0d065e965a06d2e49e4122ba6938895a28bd`; posted `2026-05-11T11:40:59.877524Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3673` Packet action request: Run governed commit staging from remote-control lane (source `rev_pkt_3673`; target `devctl_commit:170167c1416a008d0d816d8bbb01b2bb44a95aa6`; posted `2026-05-11T13:01:16.614785Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3681` Packet finding: PRE-COMMIT AUDIT slice 18 (packet_body_observed event + proof gate) — Explore agent verdict SAFE TO LAND; §11 5 EXTENDED-SAFE clusters (D-PacketAuthorityDualInjection + D-ValueCoercion canonical-only + D-DevelopNext + D-A... (source `rev_pkt_3681`; target `plan:MP-377`; posted `2026-05-11T14:41:42.314840Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3682` Packet action request: Audit MP377 packet-body gate and watcher body-state fix (source `rev_pkt_3682`; target `plan:MP-377`; posted `2026-05-11T15:08:30.623187Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3683` Packet finding: AUDIT RESPONSE rev_pkt_3682 — 3/4 surfaces PASS (show body receipt + 5-layer projection preservation + watcher signature body-fields), 1/4 GAP_CONFIRMED_REMAINING (reviewer-cycle receipt is distinct architectural debt). R... (source `rev_pkt_3683`; target `plan:MP-377`; posted `2026-05-11T15:19:05.895870Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3684` Packet finding: OPERATOR MANDATE 2026-05-11: ONE SYSTEM — continue_to_goal MUST compose with packet-body-consumption gate like Legos. Mode A (consume packets before commit) + Mode B (continue_to_goal anchor) compose, NOT parallel. Defaul... (source `rev_pkt_3684`; target `plan:MP-377`; posted `2026-05-11T15:49:07.194376Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3687` Packet finding: CODEX REVIEW SLICE 18 BLOCKER FINDINGS — 5 bugs found in 17min thorough composability review: 2 P1 (consumption-gap bypass via cleared fallback body-open + receipt-head refresh breaks authorized-receipt push test) + 3 P2 ... (source `rev_pkt_3687`; target `plan:MP-377`; posted `2026-05-11T17:21:45.579407Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3690` Packet finding: check-router guard bundle blocked by strict tooling docs policy (source `rev_pkt_3690`; target `dev/scripts/devctl.py:check-router`; posted `2026-05-11T19:15:08.260371Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3694` Packet finding: Pre-decision audit: correlation_spine.py + action_contracts.py:26-252 already exist; compose with them rather than create parallel (source `rev_pkt_3694`; target `dev/scripts/devctl/runtime/correlation_spine.py`; posted `2026-05-11T20:33:07.295343Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3698` Packet finding: Architectural audit PASS — correlation-spine integration composes correctly with existing typed pipeline; no duplicates, no parallel systems (source `rev_pkt_3698`; target `dev/scripts/devctl/runtime/correlation_spine.py`; posted `2026-05-11T20:46:52.218122Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3701` Packet finding: Smell #061 logged — reviewer-role posted body-string PASS verdicts instead of typed-evidence-bound packets; same anti-pattern violates plan §0.5 Property #7 (source `rev_pkt_3701`; target `codesmells.md:smell-061`; posted `2026-05-11T20:59:45.158855Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3702` Packet finding: Architectural slice MP377-PACKET-POST-TYPED-EVIDENCE-GUARD-S1 — operator-mandated fail-closed guard so smell #061 cannot recur (source `rev_pkt_3702`; target `dev/scripts/devctl/commands/review_channel/event_post_action.py`; posted `2026-05-11T21:01:24.445544Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3705` Packet finding: Correlation-spine coverage gap FLAG — ValidationReceipt + ExceptionReceipt + FindingRecord + packet_body_observation events still UNWIRED (source `rev_pkt_3705`; target `dev/scripts/devctl/runtime/correlation_spine.py`; posted `2026-05-11T21:06:01.756298Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3708` Packet finding: FLAG (non-blocking) — DogfoodSelfCheckReceipt typed contract used in dogfood artifacts but not registered in contract_registry.jsonl; thesis-edge case for evidence-bearing artifacts vs mutation contracts (source `rev_pkt_3708`; target `dev/state/contract_registry.jsonl`; posted `2026-05-11T21:14:22.055931Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3710` Packet finding: Architectural slice MP377-EVIDENCE-LIFECYCLE-ARCHIVE-S1 — operator-mandated evidence-lifecycle-archive (21GB dev/reports/ + 76MB single trace.ndjson; NEVER delete, archive after lifecycle closure) (source `rev_pkt_3710`; target `dev/scripts/devctl/runtime/plan_source_retention_anchors.py`; posted `2026-05-11T21:17:24.699044Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3729` Packet finding: Architectural slice MP377-SESSION-ACTIVITY-LOG-S1 — operator-mandated per-session typed activity log composing with just-shipped EvidenceArchive (source `rev_pkt_3729`; target `dev/scripts/devctl/runtime/evidence_archive.py`; posted `2026-05-11T22:24:00.681139Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3739` Packet finding: Architectural slice MP377-TYPED-SLASH-COMMAND-ENTRY-POINTS-S1 — thin slash-command entry points over typed program; operator + AI use identical entry points (source `rev_pkt_3739`; target `.claude/commands/`; posted `2026-05-11T22:59:35.580743Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3740` Packet finding: AMENDMENT to MP377-TYPED-SLASH-COMMAND-ENTRY-POINTS-S1 — universality: ANY AGENT uses identical entry points (not just operator+AI) (source `rev_pkt_3740`; target `.claude/commands/`; posted `2026-05-11T23:01:01.964928Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3744` Packet finding: Operator-flagged regression: claude reviewer keeps emitting status-update tables despite plan §26.13.2 — rules-not-strong-enough; codex investigate + propose typed fix (source `rev_pkt_3744`; target `dev/scripts/devctl/runtime/reviewer_response_shape.py`; posted `2026-05-11T23:09:59.029793Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3750` Packet finding: Architectural slice MP377-TYPED-ROLE-MODE-CUSTOMIZATION-S1 — operator-editable typed role customization + cards + guards + /role-create slash commands; codex DESIGN REVIEW requested (6 questions) (source `rev_pkt_3750`; target `dev/scripts/devctl/runtime/role_profile.py`; posted `2026-05-11T23:23:57.946913Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3753` Packet decision: Codex design decision for MP377 typed role-mode customization (source `rev_pkt_3753`; target `plan:MP-377`; posted `2026-05-11T23:31:05.720877Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3755` Packet finding: FLAG — reviewer_response_shape typed contract correct, but report.py:179 doesn't pass proposed_response_text; production gate inert (source `rev_pkt_3755`; target `dev/scripts/devctl/commands/development/report.py:179-184`; posted `2026-05-11T23:41:17.299982Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3759` Packet finding: Architectural slice MP377-COMPOSABLE-MODE-CHAIN-S1 — operator's chainable-mode design VALIDATED by dual Explore audits; 5 typed-contract gaps for codex design review (source `rev_pkt_3759`; target `dev/scripts/devctl/runtime/development_scaling_defaults.py`; posted `2026-05-12T00:04:30.512038Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3765` Packet finding: Amendment to MP377-COMPOSABLE-MODE-CHAIN-S1 — universality: ANY existing mode/flag composable; not specifically dogfood+architect example (source `rev_pkt_3765`; target `dev/scripts/devctl/runtime/development_collaboration_modes.py`; posted `2026-05-12T01:05:19.709615Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3767` Packet finding: FLAG — 6 of 8 new mode-chain typed contracts are context-graph disconnected-islands; Property #4 resumability gap (source `rev_pkt_3767`; target `dev/scripts/devctl/runtime/development_collaboration_modes.py`; posted `2026-05-12T01:09:13.395013Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3775` Packet finding: §11 duplicate-cluster hunt: 2 new flags — D-Topology (MED) at action_routing_publication_defer.py:224 + D-ValueCoercion (LOW) (source `rev_pkt_3775`; target `plan:MP-377`; posted `2026-05-12T01:50:10.002498Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3780` Packet finding: rev_pkt_3761 mode-chain: GREEN check + 3 FLAGS + 2 disconnected islands; ALSO smell #063 process-FREEZE + smell #064 /bypass layering (source `rev_pkt_3780`; target `plan:MP-377`; posted `2026-05-12T02:12:52.613142Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3781` Packet finding: Smell #065 ingest-not-blocking: session reducer hangs no default timeout; recurrence of smell #001 (--role codex invalid); plus context briefing for your inbox (source `rev_pkt_3781`; target `plan:MP-377`; posted `2026-05-12T02:19:49.297725Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3787` Packet finding: MP377 stale-session final gate routed rev_pkt_3778 but agent-loop pivoted to rev_pkt_3775 (source `rev_pkt_3787`; target `plan:MP-377`; posted `2026-05-12T02:56:22.203470Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3790` Packet finding: Synthesis ack for rev_pkt_3787: 3 evidence paths (your rev_pkt_3787 + my smell #058 layer-a + Explore map) converge on typed-gate-without-consumer-observation-proof class; 5-file composability map (source `rev_pkt_3790`; target `plan:MP-377`; posted `2026-05-12T03:24:34.376707Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3796` Packet finding: Operator-mandated synthesis design verification — wake_request packet kind + --synthesis flag + wake driver outside agents; claude ran 3 paced Explores; do you see better connections? (source `rev_pkt_3796`; target `plan:MP-377`; posted `2026-05-12T03:53:13.064598Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3798` Packet decision: MP377 synthesis wake design disposition from Codex (source `rev_pkt_3798`; target `plan:MP-377`; posted `2026-05-12T04:03:42.731767Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3816` Packet finding: Post-rev_pkt_3813 cluster check: D-DevelopNext CONSOLIDATED; 3-layer composition hierarchy de-risks layer-d supervise driver work; no parallel paths introduced (source `rev_pkt_3816`; target `plan:MP-377`; posted `2026-05-12T05:47:39.060196Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3819` Packet finding: Action Focus Gate proposal composability map — architecture mostly PRESENT; PacketCreationBinding IS the existing primitive; gap is MANDATORY ROUTING ENFORCEMENT not new contracts (source `rev_pkt_3819`; target `plan:MP-377`; posted `2026-05-12T06:15:45.083833Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3820` Packet decision: MP377 Action Focus Gate slicing decision: extend existing routing gates, no parallel contract (source `rev_pkt_3820`; target `plan:MP-377`; posted `2026-05-12T06:22:52.877005Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3821` Packet finding: Z ref / context-graph system extension map — 4 missing decision contracts (audit_receipts + PacketCreationBinding + AgentLoopDecision + SessionTerminationPolicy) + 4 indexing extensions + 3 underused tag dimensions (source `rev_pkt_3821`; target `plan:MP-377`; posted `2026-05-12T06:23:47.986264Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3822` Packet decision: MP377 z-ref/context-graph slicing decision: audit receipts first, follow-on not current stop repair (source `rev_pkt_3822`; target `plan:MP-377`; posted `2026-05-12T06:26:26.389865Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3824` Packet finding: Z ref / context-graph full deep-integration map (operator-mandated 8-agent synthesis): 16+ writers vs 1 active reader of semantic_zref; bootstrap emits 4 of 22 node kinds; 222 of 378 contracts unindexed; graph-walk capped... (source `rev_pkt_3824`; target `dev/scripts/devctl/context_graph/`; posted `2026-05-12T06:52:32.706039Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3825` Packet finding: MP-377 typed continuation policy -> typed continuation enforcement transition (operator-relayed analysis amplification, 8-agent synthesis): ~75% architectural closure + ~10% behavioral adoption. AgentSuperviseReport is QU... (source `rev_pkt_3825`; target `dev/scripts/devctl/runtime/agent_supervise_driver.py`; posted `2026-05-12T06:52:53.500630Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3826` Packet finding: Z ref full deep-integration map (8-agent synthesis): 16+ writers vs 1 active reader; bootstrap 4 of 22 node kinds; 222 of 378 unindexed; graph-walk capped 6 hops; 4 highest-leverage extensions; 25 queued plan rows (source `rev_pkt_3826`; target `dev/scripts/devctl/context_graph/`; posted `2026-05-12T06:54:07.821801Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3827` Packet finding: MP-377 typed continuation policy -> typed continuation enforcement transition (operator-relayed analysis amplification, 8-agent synthesis): ~75% architectural closure + ~10% behavioral adoption. AgentSuperviseReport is QU... (source `rev_pkt_3827`; target `dev/scripts/devctl/runtime/agent_supervise_driver.py`; posted `2026-05-12T06:54:37.123705Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3828` Packet decision: MP377 context-graph deep-integration slicing: follow-on rows, not current continuation repair (source `rev_pkt_3828`; target `plan:MP-377`; posted `2026-05-12T07:22:01.334585Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3834` Packet decision: MP377 continuation handoff repair interim decision: /develop carries edit-only override; dirty task_produced blocked (source `rev_pkt_3834`; target `plan:MP-377`; posted `2026-05-12T11:18:00.735838Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3835` Packet decision: MP377 continuation repair update: stale peer route suppressed; body-open blocker normalized (source `rev_pkt_3835`; target `plan:MP-377`; posted `2026-05-12T11:44:30.401977Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3836` Packet decision: MP377 continuation gate repair: prose peer repair now yields scoped Codex override (source `rev_pkt_3836`; target `plan:MP-377`; posted `2026-05-12T12:15:44.116581Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3838` Packet decision: MP377 continuation gate repair updated with docs-check proof (source `rev_pkt_3838`; target `plan:MP-377`; posted `2026-05-12T12:21:48.542161Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3840` Packet finding: Reviewer verdict on rev_pkt_3839: typed-discipline correct under scoped edit-only override; claude mutation lane pending operator typed authority; composability ask on ScopedOverrideHandoffLifecycle (source `rev_pkt_3840`; target `plan:MP-377`; posted `2026-05-12T13:19:05.892226Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3841` Packet finding: Wake packet: codex task_complete 13:27Z under closed-gate must_continue; MP377-P0-CHECKPOINT-AUTOMATION-S1 not closed; smell #058 layer-e candidate awaiting classification on re-engagement (source `rev_pkt_3841`; target `plan:MP-377`; posted `2026-05-12T13:35:04.854255Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3842` Packet finding: OPERATOR BYPASS AUTHORIZED for codex re-engagement on MP377-P0-CHECKPOINT-AUTOMATION-S1; smell #058 LAYER-E CONFIRMED was root cause of 13:27Z stop; guards fired correctly, gate-vocabulary failed; anchors not mis-set (sto... (source `rev_pkt_3842`; target `plan:MP-377`; posted `2026-05-12T14:55:35.783605Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3843` Packet finding: OPERATOR amplified architectural asks: (1) did guard work? guard fired but didn't enforce CLI terminator; (2) why isn't bypass in GovernedExceptionLifecycle? typed bypass lifecycle proposal; (3) real-life-test rule; (4) A... (source `rev_pkt_3843`; target `plan:MP-377`; posted `2026-05-12T15:30:27.092200Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3844` Packet work: ANCHOR TEST: codex observe + honor by 15:42:12Z on MP377-P0-CHECKPOINT-AUTOMATION-S1 (anchor system verification) (source `rev_pkt_3844`; target `plan:MP-377`; posted `2026-05-12T15:35:52.318639Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3845` Packet finding: PLAN-INGESTION: Full recovery saga 13:27Z->15:51Z; 5 architectural findings (gate-vocabulary layer-e, bypass-not-in-GovernedExceptionLifecycle, dangerous-flag-not-typed-authority, anchor-not-wired, codex-bridge-parallel-s... (source `rev_pkt_3845`; target `plan:MP-377`; posted `2026-05-12T15:53:31.171396Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3846` Packet work: STOP_ANCHOR TEST: codex should stop work on MP377-P0-CHECKPOINT-AUTOMATION-S1 by 2026-05-12T16:23:00Z to test typed stop_anchor system (operator-requested verification) (source `rev_pkt_3846`; target `plan:MP-377`; posted `2026-05-12T16:08:33.151433Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3847` Packet finding: BYPASS-LAUNCH BLOCKERS evidence (7 concrete blockers from 30min launch fight); BypassLifecycle PRIORITY 1 architectural fix ask; UniversalGovernanceLifecycle PRIORITY 2; real-life-test rule PRIORITY 3; stop_anchor rev_pkt... (source `rev_pkt_3847`; target `plan:MP-377`; posted `2026-05-12T16:09:27.089818Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3848` Packet finding: MULTI-AGENT SYNTHESIS: 3 Plan agents — BypassLifecycle skeleton ALREADY EXISTS at lifetime_bypass_mode.py:38; UniversalGovernanceLifecycle is view-reducer (NO new ledger, same governed_exception_lifecycles.jsonl); smell #... (source `rev_pkt_3848`; target `plan:MP-377`; posted `2026-05-12T16:22:37.331804Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3850` Packet finding: FOLLOW-UP: 3 of 4 sub-lifecycles are PARTIAL DUPLICATES; codex should EXTEND existing typed contracts not create new — EmissionGateLifecycle extends TaskCompleteDecision (session_termination_policy.py:83-100); BridgeAttac... (source `rev_pkt_3850`; target `plan:MP-377`; posted `2026-05-12T16:29:52.699336Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3853` Packet finding: ROUND F FEEDBACK: codex BypassLifecycle 90% aligned, 3 NEW BUGS (dead EVALUATING/RECEIPT_ISSUED enum; revoke APPENDS causing dup receipt_id; from_mapping missing) + 5 CROSS-IMPACT GAPS untouched + slice-id MP377-P0-BYPASS... (source `rev_pkt_3853`; target `plan:MP-377`; posted `2026-05-12T17:01:53.169859Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3854` Packet finding: Charter complete 87P + review-before-ingest + 4 gaps closed + 3 arch clarifications (source `rev_pkt_3854`; target `plan:MP-377`; posted `2026-05-12T17:58:48.160413Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3855` Packet finding: Ack rev_pkt_3852 + SYSTEM_MAP visibility gap finding + shlex refactor verdict + post-commit directive (source `rev_pkt_3855`; target `plan:MP-377`; posted `2026-05-12T18:01:12.255888Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3857` Packet finding: Pivot-relevant finding (P89 fire-sooner rule): 3 CLI surface gaps + 2 charter additions P88/P89 + propose devctl bypass CLI as next slice (source `rev_pkt_3857`; target `plan:MP-377`; posted `2026-05-12T18:31:43.570720Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3858` Packet finding: Charter update P90-P93: PacketSupersessionLink + RelationshipGraph + ADR receipt + CharterDelivery — extends rev_pkt_3854/3855/3857 (manual P92 ADR semantics) (source `rev_pkt_3858`; target `plan:MP-377`; posted `2026-05-12T18:45:56.521395Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3859` Packet finding: Typed-state integrity gap: resolve_goal_progress_receipt has no caller in events.py — mandate at MASTER_PLAN.md:96 unmet (pivot_now per P89) (source `rev_pkt_3859`; target `plan:MP-377`; posted `2026-05-12T18:51:19.680880Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3860` Packet finding: Commit eb336244 LANDED: BypassLifecycle composability + P88-P93 + live-test confirms parallel-surfaces CLI gap + managed-commit-gate state-machine bug (P61 finding) (source `rev_pkt_3860`; target `plan:MP-377`; posted `2026-05-12T19:09:14.564310Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3861` Packet finding: FULL-SCOPE HANDOFF: prior codex 019e1cf8 stuck 32min; commit eb336244 landed; charter 93P; don't-stop-on-blockers; next slice devctl bypass CLI (source `rev_pkt_3861`; target `plan:MP-377`; posted `2026-05-12T19:36:18.114688Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3864` Packet finding: Operator clarification: typed authority should be ROLE-based not model-named; --actor flag forgeable (P38+P74+P58+P88+P91 gap) (source `rev_pkt_3864`; target `plan:MP-377`; posted `2026-05-12T20:29:00.271093Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3865` Packet finding: Operator concern #3: typed apply needs review-evidence validation not just any string (builds on rev_pkt_3864 role-authority gap) (source `rev_pkt_3865`; target `plan:MP-377`; posted `2026-05-12T20:31:01.926141Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3866` Packet finding: AMENDMENT to rev_pkt_3864/3865: proposed fix should compose with existing surfaces (PacketTransitionRequest+ValidationReceipt+ExceptionReceipt+RoundProofState) not duplicate — operator no-parallel-surfaces rule (source `rev_pkt_3866`; target `plan:MP-377`; posted `2026-05-12T20:34:12.650261Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3867` Packet finding: Operator concern #4: typed FixLifecycle for bug-fix work — composes with P21/P29/P59/P75/P76/P77/P78/P82 (zero new parallel surfaces) (source `rev_pkt_3867`; target `plan:MP-377`; posted `2026-05-12T20:36:42.725327Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3870` Packet finding: ACK 6bd6f207: Codex fixed governed_executor.py:111 bug claude flagged in rev_pkt_3860; full bilateral debug+fix cycle COMPLETE end-to-end (~100min). Charter validations #19+#20. (source `rev_pkt_3870`; target `plan:MP-377`; posted `2026-05-12T20:42:36.657455Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3871` Packet finding: Refined P94 BugFixLifecycle composes 9 existing typed contracts (FindingRecord+GovernedExceptionLifecycle+DogfoodRecord+ActionResult+RoundProofState+CommitReceipt+ValidationReceipt+PeerSessionHandshakeEvidence+ExceptionRe... (source `rev_pkt_3871`; target `plan:MP-377`; posted `2026-05-12T20:46:55.604824Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3872` Packet decision: Consolidated review post-6bd6f207: code-reviewer SAFE-TO-KEEP + 1 follow-up smell batched; 5-packet arc 3864-3871 is ONE consolidated slice; P94 BugFixLifecycle ADDED to plan (94 priorities). NOT pivot - continue run_dev... (source `rev_pkt_3872`; target `plan:MP-377`; posted `2026-05-12T20:57:17.674237Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3875` Packet decision: CONVERGENCE post-753cf164: codex independently authored typed-PipelineHandle pattern (last_persisted_pipeline + _load_stage_pipeline_after_persist) matching claude code-reviewer recommendation 20:54Z; charter validations... (source `rev_pkt_3875`; target `plan:MP-377`; posted `2026-05-12T21:07:04.317030Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3878` Packet finding: PIVOT-NOW iter4: your 21:19:38Z root-cause (execute_commit reloads pipeline from projection) is the SAME bug class claude code-reviewer flagged 20:54Z (rev_pkt_3872). Fix BUG CLASS not symptom: restrict load_pipeline() to... (source `rev_pkt_3878`; target `plan:MP-377`; posted `2026-05-12T21:21:51.831151Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3879` Packet finding: ITER-4 VERDICT (claude code-reviewer 21:23Z): YOUR fix is structural at API layer (memo-aware load_pipeline = 3rd valid strategy, distinct from iter-2 and from claude's prior rev_pkt_3878 call-site-restriction recommendat... (source `rev_pkt_3879`; target `plan:MP-377`; posted `2026-05-12T21:25:44.232640Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3882` Packet decision: FULL-ROUND-TRIP-ACK: Iter-4 commit dea85ab1 LANDED 21:32Z. API-layer memo-aware load_pipeline PASSED the approval-resolution failure path that REJECTED iter-3. P94 BugFixLifecycle canonical first instance CLOSED: 4 itera... (source `rev_pkt_3882`; target `plan:MP-377`; posted `2026-05-12T21:33:27.998987Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3887` Packet finding: PUSH-BYPASS TYPED ENFORCEMENT GAP (operator-directed 21:51Z + 2-agent investigation): pre-push hook refuses raw git push via binary devctl.governed-push config flag, NOT typed BypassReceipt validation. BypassLifecycle has... (source `rev_pkt_3887`; target `plan:MP-377`; posted `2026-05-12T21:53:44.542738Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3888` Packet finding: PIVOT-NOW (operator directive 21:52Z): raw git push must require typed BypassReceipt+reason via pre-push hook. Audit: pre-push-governed-push.sh EXISTS + refuses raw push UNCONDITIONALLY but does NOT integrate typed Bypass... (source `rev_pkt_3888`; target `plan:MP-377`; posted `2026-05-12T21:53:50.570221Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3893` Packet finding: SLASH-ARCHITECTURE UNIFICATION (operator concern #7 22:08Z + 2-agent investigation): /develop ALREADY the de-facto system-entry (20 actions, 5+ subsystems); 9-slash inventory over-fragmented (exceeds P58 ≤4 cap); 3 duplic... (source `rev_pkt_3893`; target `plan:MP-377`; posted `2026-05-12T22:13:07.326752Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3900` Packet finding: THREE NEW CHARTER PRIORITIES (operator concerns #9-#11 22:40-23:25Z): P58.3 PortabilityEnforcementGuard (5 coupling-point fixes; new check_platform_portability.py guard; AI Governance Platform must work with any adopter r... (source `rev_pkt_3900`; target `plan:MP-377`; posted `2026-05-12T23:09:04.125673Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3904` Packet finding: Two observations for codex review (no prescribed fix): (1) hammock plan ingestion was rejected 2026-05-12T19:44Z with reason missing_plan_row_or_checklist_authority — risk that today's 7 directives live in markdown only; ... (source `rev_pkt_3904`; target `plan:MP-377`; posted `2026-05-13T00:13:40.248169Z`; binding `plan_row`).
  - 2026-05-13 follow-up under `MP377-P0-T08`: live remote-control dogfood landed the P99/P100 easy wins (check-router config caching, governed-push parallel-worker wiring, review-channel `--packet-kind` alias, and top-level markdown errors) and exposed a strict-tooling docs gate loop around generated `AGENTS.md`. The docs-check policy now uses `tooling_required_doc_aliases` so generated projection-only boot cards can be satisfied by their durable owner doc instead of forcing manual generated-surface edits; governed push remains responsible for rerendering surfaces before publication.
  - 2026-05-14 follow-up under `MP377-AUTOINVAL`: review-channel packet posts now keep the no-wake process boundary while emitting `PacketArrivalDerivedStateInvalidation` metadata in the existing packet-attention receipt. The receipt names the derived consumers that must reload event-backed review state (`review_state`, compact/full/actions projections, packet inbox, work board, agent-loop decisions, `startup-context`, and `/develop next`) and records whether the packet-post reducer already refreshed projections.

## Priority 97 — RepoSemanticClassifier + DenialTier + CumulativeRiskSignature family (MP-377)

Self-hosted typed classifier surface for the codex-voice platform's own typed governance. Composes with P1 (FeatureShipLifecycle terminal states), P3 (receipt schema unification), P8 (ReviewerRound evidence binding), P96 (GateRemediationReceipt precedent — rev_pkt_3911 / commit b4acaba1). Three composable layers fill three confirmed gaps in the existing typed-contract family: (a) no semantic-graph classifier surface on top of `context_graph_models.py`; (b) no `denial_tier` distinction on `ExceptionReceipt` separating operator-overridable from inviolable denials; (c) no cumulative-risk-signature field on `AgentMindSlice` / `CommitReceipt` / `DogfoodRecord`. The platform's typed packets already carry explicit `intent_class` and `composes_with` metadata, so a typed self-classifier reading those signals is strictly stronger than any heuristic alternative.

- [ ] `MP378-P97-L1-CLASSIFIER` Land `RepoSemanticClassifier` + `ClassifierProbeReceipt` at `dev/scripts/devctl/runtime/repo_semantic_classifier.py`; consumes `context_graph_models.py` snapshot (24 node kinds / 13 edge kinds / ~11k nodes / 148k edges) and `ConnectivityRegistrySnapshot` (110 contracts); emits verdict ∈ {`composes`, `extends`, `parallel_authority_smell`, `unclassified`}; wires into `action_contracts.py` routing decision and `review_channel/packet_contract.py` pre-publication vetting. ~300 LOC including new receipt type. Composes with P3 unified receipt shape.
- [ ] `MP378-P97-L2-DENIAL-TIER` Add `denial_tier: str = "policy_override"` field to `ExceptionReceipt` in `dev/scripts/devctl/runtime/governed_exception_receipts.py` with values {`soft_cumulative` (decays / retry possible), `hard_invariant` (operator authorization cannot override), `policy_override` (operator may attest-override via `authority_evidence_refs`)}; extend `validate_exception_receipt` in `governed_exception_validation.py`, `_bypass_request_denial_reason` in `bypass_lifecycle_evaluation.py`, add `exception_overridability_policy` mapping in `project_governance_contract.py`. ~75 LOC additive. Smallest-first slice.
- [ ] `MP378-P97-L3-RISK-SIGNATURE` Land `CumulativeRiskSignature` + `RiskSignatureSnapshot` at `dev/scripts/devctl/runtime/cumulative_risk_signature.py`; per-action weights (tool invocation +2, escalation +5, error +3); tracks N consecutive `passed` / `composes` outcomes; decays score 50% after N resets; emits `RiskSignatureSnapshot` periodically and at threshold breach; score > threshold auto-emits `ExceptionReceipt(denial_tier="soft_cumulative")` for operator review. Add `risk_signature_id` + `latest_threat_level` to `agent_mind_slice.py`; `risk_delta: float` to `commit_receipt.py`. ~245 LOC.
- [ ] `MP378-P97-VERIFY` Real-life-test typed receipt chain per `feedback_real_life_test_shipped_features`: L2 emit `ExceptionReceipt(denial_tier=policy_override)` + operator attest-override; L1 emit one `ClassifierProbeReceipt` per verdict class (`composes` / `extends` / `parallel_authority_smell`); L3 emit `RiskSignatureSnapshot` showing accumulation + decay + threshold-triggered auto-`ExceptionReceipt`. All evidence archived via `/archive-evidence`. Closure: all four P97 rows transition `[ ]` → `[x]`.
- [ ] `PKT-BIND-REV-PKT-3939` Packet decision: Priority 102 architectural proposal: Typestate-Governed Attestation Pipeline over LTS — evolve BypassLifecycle pattern + extend ZGraph EdgeKind, do NOT invent parallel Receipt[State] generic surface (source `rev_pkt_3939`; target `plan:MP-377`; posted `2026-05-13T05:48:38.115704Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3941` Packet decision: P102 REFINEMENT (refines rev_pkt_3939): 5-phase rollout + FastAPI-style @governed_transition decorator + exhaustiveness-checked algebraic results + Kobzol patterns (source `rev_pkt_3941`; target `plan:MP-377`; posted `2026-05-13T05:56:43.222457Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3943` Packet decision: P102 CONSOLIDATION (refines rev_pkt_3939+3941): SLSA industry-twin + Dagster decorator + dbt/HTN/LangGraph kinship; ZGraph audit reveals EDGE_KIND_RECEIPT_PROVES already exists — Phase 5 much smaller; total 18-30 hours f... (source `rev_pkt_3943`; target `plan:MP-377`; posted `2026-05-13T06:09:36.440790Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3948` Packet decision: P102 Phase 1 PIVOT: mypy.ini + pyrightconfig.json ALREADY EXIST at repo root — Phase 1 must COMPOSE existing configs, NOT create parallel files. Per master charter no-parallel-surfaces rule. (source `rev_pkt_3948`; target `plan:MP-377`; posted `2026-05-13T18:27:42.460160Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3949` Packet finding: ARCHITECTURAL FINDING: 23-min startup-authority cascade — phase 4 packet-attention drain ate 15 of 23 min. Composes with P88/P89/P57 Cluster 6/P63/P74. (source `rev_pkt_3949`; target `plan:MP-377`; posted `2026-05-13T18:35:42.004353Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3953` Packet decision: OPERATOR VERDICT on rev_pkt_3949 (23-min cascade): keep lifecycle design (correct), but SEPARATE 3 proof classes + DIFFERENTIATE blocking by surface + BATCH body-observation. Implementation-ready refinement. Composes P88... (source `rev_pkt_3953`; target `plan:MP-377`; posted `2026-05-13T19:01:18.584550Z`; binding `plan_row`).
  - 2026-05-13 P102 Phase 5 foundation landed in the existing lifecycle
    architecture: `BypassLifecycle` reducers declare governed transition
    metadata through `@governed_transition`, the repo-owned
    `dev/state/transition_modules.jsonl` manifest prevents import-order drift,
    and `TransitionContract` / `GovernedTransitionModule` are registered with
    platform-contract and schema-fixture closure. This remains metadata over
    current lifecycle surfaces, not a parallel receipt-state system.
  - 2026-05-13 P102 Phase C landed the first algebraic result-case slice over
    existing lifecycle outputs: bypass activation, governed push projection,
    and `TaskCompleteDecision` routing now have discriminated dataclass cases
    with strict `Literal` / `match` / `assert_never` coverage. These cases
    project canonical `BypassLifecycle`, `ActionResult`, and
    `TaskCompleteDecision` state; they do not introduce a parallel receipt
    authority.
  - 2026-05-13 P102 Phase 1.5 landed nominal governance ID wrappers:
    `PacketId`, `ReceiptId`, and `PlanRowId` now live in
    `runtime/typed_ids.py` with normalizers and evidence-ref helpers. The
    first use stays at command/evidence helper boundaries so persisted typed
    contracts remain string-compatible while strict checks can prevent future
    packet/receipt/plan-row swaps.
  - 2026-05-13 P102 Phase 7 landed `check_governed_transitions.py`: the guard
    loads governed-transition manifest modules, builds lifecycle graph edges
    from `TransitionContract` metadata, and proves state/graph reachability
    through `walk_context_graph`. It is registered in the script catalog,
    shared governance bundle, and tooling/release workflows.
- [ ] `PKT-BIND-REV-PKT-3958` Packet finding: Idris-ST enforcement-gap research: @governed_transition is metadata-only; 4 typestate pairs implicit; 9-stage compiler mapping; receipts DBC-incomplete; 3 options for Phase 7/8 scope (source `rev_pkt_3958`; target `plan:MP-377`; posted `2026-05-13T20:17:09.375695Z`; binding `plan_row`).
  - 2026-05-13 Codex disposition: accept the enforcement-gap finding and
    choose Option A. Phase 7 remains the metadata/graph verifier. Queue
    follow-up work as `P102-ENFORCE-S1` for opt-in runtime
    precondition/postcondition enforcement over existing lifecycle state
    resolvers and `P102-RECEIPT-DBC-S1` for transition id plus pre/post-state
    receipt evidence on existing validation/commit receipt boundaries.
    Third-party design-by-contract libraries are evaluation candidates only,
    not authority and not part of the Phase 7 slice.
  - 2026-05-13 `P102-ENFORCE-S1` landed as an opt-in extension to the existing
    `@governed_transition` surface: runtime-enforced transitions declare
    pre/post state resolvers, raise `TransitionStateViolation` on illegal state
    refs, and keep metadata-only behavior as the default. The canonical
    `BypassLifecycle` reducers now enforce their declared `requires` and
    `produces` refs without introducing a parallel design-by-contract system.
  - 2026-05-13 `rev_pkt_3973` disposition: adopt Option A before Phase D
    widens. `BypassRequest` and `BypassReceipt` now carry explicit
    `BypassLifecycleState`, the request/receipt resolvers read actual input
    state instead of returning constants, pre-state resolvers receive wrapped
    function arguments, and post-state resolvers receive only the reducer
    result. Focused coverage now rejects illegal request/receipt states and
    proves multi-state `requires` / `produces` membership. `rev_pkt_3975`
    refined the same slice before commit: revoke construction now sets the
    inner `BypassReceipt.state` to `REVOKED` instead of inheriting the issued
    default.
- [ ] `PKT-BIND-REV-PKT-3960` Packet finding: Pre-decision architectural review (operator-directed): ZGraph+zRef+traversal map + ai_governance_platform.md fit + 3 parallel-surface risks + smaller Phase 8 composition path (Agent 3 found: reuse require_receipt_state, n... (source `rev_pkt_3960`; target `plan:MP-377`; posted `2026-05-13T20:40:13.945631Z`; binding `plan_row`).
  - 2026-05-13 Codex disposition: accept the smaller composition path. Phase
    8 should not introduce a standalone `check_attestation_path.py` package or
    a new enforcing decorator. The landed slice extends existing
    `ValidationReceipt` and `CommitReceipt` evidence with pre/post states and
    verifies emitted receipt state through `require_receipt_state()` at the
    governed validation and commit boundaries.
- [ ] `PKT-BIND-REV-PKT-3962` Packet finding: Multi-modal audit (operator-directed): system is multi-modal-with-gaps; 3 CI/CD-hardcoded smells in auto-mode + startup_context; docs architecturally-sound but rhetorically-cage-heavy; 3 options for fix (doc-only / arch f... (source `rev_pkt_3962`; target `plan:MP-377`; posted `2026-05-13T21:09:14.415297Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3964` Packet finding: Unified settings projection (operator-directed): 24 gates + ci-cd-hub deep-dive + canonical chokepoint at entrypoint.py:452 + P87 cloud CI alignment; 3 patterns to IMPORT from ci-cd-hub, 3 to AVOID; codex should spawn own... (source `rev_pkt_3964`; target `plan:MP-377`; posted `2026-05-13T21:32:57.965048Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3965` Packet finding: ADR Mode + AI-Decision-ADR-Receipts (operator keystone): ADR is governance MODE not mandate (4 levels: off/observe/advisory/strict); typed DesignDecisionRecord per material AI decision; composes with correlation_spine + c... (source `rev_pkt_3965`; target `plan:MP-377`; posted `2026-05-13T21:40:37.284835Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3966` Packet finding: FULL GOVERNANCE ARCHITECTURE (operator 4-directive synthesis): 3-layer hierarchy (UI projection / typed mode policy / immutable evidence); ModeChangeReceipt + AIDecisionADRReceipt + governance_gates; You may disable gates... (source `rev_pkt_3966`; target `plan:MP-377`; posted `2026-05-13T21:45:02.191757Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3968` Packet finding: Directive 5 — Automation Discovery Growth Harness (operator-directed): system already exists manually (codesmells.md→audits→plan_index); clippy_pedantic.top_promote_candidates IS template mirror; master charter P47+P56+P6... (source `rev_pkt_3968`; target `plan:MP-377`; posted `2026-05-13T22:12:02.160289Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3969` Packet finding: Directive 6 — Governance Discovery Role + Smart Dashboard (operator-directed): MAJOR FINDING role_customization.py already supports user-defined roles (config-only for governance_discovery_agent); 14-surface dashboard via... (source `rev_pkt_3969`; target `plan:MP-377`; posted `2026-05-13T22:22:36.393414Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3970` Packet finding: Directive 7 — Explainable Operator Console + platform decision (operator-directed): old operator_console.md EXISTS (NOT lost) at dev/active/ (51KB, MP-359); PyQt6 console Phase-1 COMPLETE (168 files, 14 tests, 5 workspace... (source `rev_pkt_3970`; target `plan:MP-377`; posted `2026-05-13T22:41:30.543682Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3971` Packet finding: Directive 7 Operator Console Platform Decision (source `rev_pkt_3971`; target `plan:MP-377`; posted `2026-05-13T22:42:03.849528Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3973` Packet finding: P102 Phase D PRE-LANDING — 2 of 4 governed_transition state resolvers tautological (BypassRequest/BypassReceipt return constants without reading input state); resolver signature asymmetry secondary foot-gun. Decision need... (source `rev_pkt_3973`; target `plan:MP-377`; posted `2026-05-13T23:04:23.370641Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3974` Packet finding: OPERATOR PRODUCT FINDING — Directive 7 refinement: dashboard JSON is RICH (3962 packets + 20+ surfaces), renderer is SHALLOW (~6 fields); build operator/cockpit projection OVER existing JSON instead of new data layer; ope... (source `rev_pkt_3974`; target `dev/scripts/devctl/dashboard/`; posted `2026-05-13T23:05:26.035682Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3975` Packet finding: REFINES rev_pkt_3973 — Option A WIP missing state=REVOKED at _revoked_receipt() (bypass_lifecycle_evaluation.py:313). One-line patch before commit prevents silent correctness regression on revoked-receipt state propagation. (source `rev_pkt_3975`; target `plan:MP-377`; posted `2026-05-13T23:14:54.553061Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3977` Packet finding: WAVE 0 PLAN-COHERENCE OBSERVATION (codex design authority): cross-check shows P31+P56 substantively landed under different names; P57+P74 partial (registries exist, no keystone contract); P84 partial (drift exists, smells... (source `rev_pkt_3977`; target `plan:MP-377`; posted `2026-05-13T23:35:04.331192Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3980` Packet finding: OPERATOR-DRIVEN DESIGN PROPOSAL: --tracker projection joining 6 typed-state axes (git+packets+plan_index+agent-mind+receipts+stage-events) for anchor-windowed 'what AI accomplished' visibility. FOUNDATION EXISTS (SessionA... (source `rev_pkt_3980`; target `plan:MP-377`; posted `2026-05-14T00:30:47.945944Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3983` Packet finding: OPERATOR-DRIVEN: PlanRowPhaseProjection — SDLC-phase projection that DERIVES phase from existing receipt chains (NOT new authority). Scout 3 verdict: NOT a new P97 — reframe as projection-adapter under P57 ConsolidationMa... (source `rev_pkt_3983`; target `plan:MP-377`; posted `2026-05-14T01:06:10.676797Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3985` Packet finding: REFINES rev_pkt_3983 (PlanRowPhaseProjection) — operator voice-mode brainstorm added 3 extensions: (1) CAPABILITY-TYPE model (READ/WRITE/COMMIT/PUBLISH keys; dangerous functions require matching key; roles DERIVED from ca... (source `rev_pkt_3985`; target `plan:MP-377`; posted `2026-05-14T01:17:33.844410Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3987` Packet finding: REFINES rev_pkt_3985 with CONCRETE PYTHON ENCODING — operator screenshot 21:27 confirms canonical Rust generic-typestate pattern (User<Viewer>/<Editor>/<Admin>; methods physically don't exist on wrong state-type). Python ... (source `rev_pkt_3987`; target `plan:MP-377`; posted `2026-05-14T01:30:09.952675Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3989` Packet finding: OPERATOR-DRIVEN: ci-cd-hub (already at integrations/ci-cd-hub + /Users/jguida941/Dev/GitHubProject/ci-cd-hub) is the DETERMINISTIC REPO ONBOARDING CORE for the AI governance platform. Typed bridge via VerifiedRepoProfile.... (source `rev_pkt_3989`; target `plan:MP-377`; posted `2026-05-14T01:54:58.126082Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3991` Packet finding: VERIFICATION SYNTHESIS — operator's deep-research framing (2026-05-14T02:09Z) verified against codebase by 3 sub-agents. 90% MAPS TO EXISTING infrastructure (all 7 adoption commands + 10 spine contracts + 9-repo matrix + ... (source `rev_pkt_3991`; target `plan:MP-377`; posted `2026-05-14T02:12:03.654955Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3992` Packet finding: OPERATOR-DRIVEN: Remote Evidence Runner — async typed validation with cloud-backed receipts. 8 sub-agents verified ~70% substrate present (cloud-execution wired with 31 workflows + 14 workflow_dispatch + 6 cron, ingest-ex... (source `rev_pkt_3992`; target `plan:MP-377`; posted `2026-05-14T02:24:05.578240Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-3996` Packet finding: REFINES rev_pkt_3993 Remote Evidence Queue with 3 minimal substrate-fill gaps from 3-agent second-pass verification: (1) Working-backward detection MISSING — needs find_finding_affected_paths_in_current_tree() reusing exi... (source `rev_pkt_3996`; target `plan:MP-377`; posted `2026-05-14T02:37:10.020753Z`; binding `plan_row`).
  - 2026-05-14 `MP377-REMOTE-EVIDENCE-QUEUE-PATH-FRESHNESS-S1` landed the
    first Remote Evidence Queue substrate slice from `rev_pkt_3996`:
    `RemoteValidationReceipt` models, current-tree path freshness for
    `FindingRecord` evidence using existing git changed-path utilities, and
    additive `tree_content_hash` identity on `CommitReceipt` and `RunRecord`.
    The Finding-to-next-action bridge remains the next Remote Evidence Queue
    follow-up.
  - 2026-05-14 `MP377-AUTOINVAL-PRODUCER-WIRING-S1` landed the first producer
    wiring slice for derived-state invalidation without creating a parallel
    event bus. Packet lifecycle transitions, packet-debt repair ingestion,
    session-liveness expiry events, and plan-ingestion receipts now attach
    shared invalidation metadata to their existing evidence rows. The
    `PlanIntentIngestionReceipt` contract gained additive
    `derived_state_invalidated` / `derived_state_invalidation` fields so plan,
    startup, inbox, work-board, agent-loop, and `/develop next` consumers can
    reload from typed evidence after plan authority changes.
  - 2026-05-14 `MP377-AUTOMATION-FLAGGING-PACKET-KIND-S1` adds
    `automation_opportunity` as an advisory review-channel packet kind for
    automation candidates. It stays on the existing packet carrier surface:
    typed evidence is required, plan target/anchor/intake refs are allowed as
    non-authoritative context, and mutation/runtime guard fields remain
    rejected so executable work still flows through plan ingestion.
- [ ] `PKT-BIND-REV-PKT-4004` Packet finding: S2 PIVOT-FIX (pre-commit): session_status_projection.py reads untyped dict mappings — needs typed imports of RecoveryAssessmentState/SessionActivityEntry/AgentMindSlice to close PARALLEL-SURFACE-RISK. Also: 6 missing clas... (source `rev_pkt_4004`; target `plan:MP-377`; posted `2026-05-14T13:09:18.234854Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4008` Packet finding: S3 pivot-relevant: Bash(*) wildcard at settings.local.json:4 makes typed permission rules inert + .claude/settings.local.json is gitignored. Decisions needed pre-commit. (source `rev_pkt_4008`; target `dev/scripts/devctl/runtime/classifier_safety_attestation.py`; posted `2026-05-14T13:54:10.615658Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4010` Packet finding: S3 review_accepted (5/5 absorbed, 13/13 tests pass) + RECURRING-CLASS SYSTEM_MAP gap: 3 slices silently skipped SYSTEM_MAP doc-sweep; docs-check strict-tooling has no contract_registry-to-SYSTEM_MAP binding. Inline-fix ar... (source `rev_pkt_4010`; target `dev/scripts/devctl/runtime/classifier_safety_attestation.py`; posted `2026-05-14T14:10:04.463394Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4012` Packet finding: Arch-fix review_accepted (guard works, live dogfood pass) + RECURSIVE-CLASS: the fix itself exhibits the recurring-class gap it fixes (no dedicated plan row, wrong target on PKT-BIND row, no commit anchor, no PlanIntentRe... (source `rev_pkt_4012`; target `dev/scripts/checks/check_systemmap_covers_contract_registry.py`; posted `2026-05-14T14:40:00.598447Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4013` Packet task_started: MP-378 S4 SessionLivenessReconciler (source `rev_pkt_4013`; target `plan:MP-378-LAUNCH-BOOTSTRAP-FIX-S4`; posted `2026-05-14T14:42:57.479602Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4014` Packet finding: S4 pre-substrate PIVOT: 4 compose-target design decisions + recursive-class MUTATING (continuity weakening at each cycle: S2/S3 strong → arch-fix partial → S4 task-start zero PKT-BIND row). 5 absorption items breakable du... (source `rev_pkt_4014`; target `dev/scripts/devctl/runtime/session_liveness_reconciler.py`; posted `2026-05-14T14:48:21.781478Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4015` Packet finding: S4 pre-commit: CLI carve CLEAN ✓ + COMPOSE-PARALLEL trip-wire (substrate at attachment-layer not signal-chain; Decision 1.4 NEITHER picked; Item D back-reg SKIPPED) + docstring regression (1-line on PID-SIGTERM substrate ... (source `rev_pkt_4015`; target `dev/scripts/devctl/runtime/session_liveness_reconciler.py`; posted `2026-05-14T14:58:08.282123Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4016` Packet finding: S4 review_accepted (17/17 PASS, docstring exceeds S3, Item D absorbed, Finding 1 Option A documented, Decision 1.4 delegate) + META-FINDING: recurring-class IS the lack of guards. STABILIZED on 4 guard-enforced axes; PROP... (source `rev_pkt_4016`; target `dev/scripts/devctl/runtime/session_liveness_reconciler.py`; posted `2026-05-14T15:27:49.133753Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4017` Packet finding: OPERATOR MANDATE 2026-05-14T15:35Z: META-FINDING elevated from observation to active-build. 5 guards (P1-P5) now MANDATORY across S5-S7 + arch-fix. Plan must carry guard-discovery-loop charter row. Claude /loop gains step... (source `rev_pkt_4017`; target `plan:MP-378`; posted `2026-05-14T15:37:25.618461Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4019` Packet finding: Guard P1 shape matches proposal + retroactive S4 hygiene LANDED (major win). BUT P1 correctness gap: enforced-row classifier is lexical-only, misses task_started_packet_binding mutation_op. ALSO 2 NEW LIVE-VALIDATED guard... (source `rev_pkt_4019`; target `dev/scripts/checks/check_plan_index_commit_continuity.py`; posted `2026-05-14T15:56:43.481632Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4020` Packet finding: Guard P1 POST-COMMIT: 5/6 DISCIPLINE-COMPLETE + classifier upgrade exceeds Finding 1 ask + CI gating both workflows + 9/9+12/12 tests PASS. BUT guard FIRES with 2 live violations on its own first run (charter row + PKT-BI... (source `rev_pkt_4020`; target `dev/scripts/checks/check_plan_index_commit_continuity.py`; posted `2026-05-14T16:10:52.058835Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4021` Packet finding: OPERATOR DIRECTIVE 2026-05-14T16:11Z: retire rev_pkt_3982 push-batching override. Raw git commit AND raw git push per slice from now on. 55 unpushed accumulated is itself the time-eater operator wants to eliminate. Resolv... (source `rev_pkt_4021`; target `operator-mandate:raw-push-per-slice-2026-05-14T16:11Z`; posted `2026-05-14T16:14:46.994898Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4022` Packet finding: OPERATOR ARCHITECTURAL FINDING 2026-05-14T16:18Z: raw git commit/push bypass typed BypassLifecycle/GovernedExceptionLifecycle. Guards skip on raw-committed work; end-of-session governed-push may miss what should-have-been... (source `rev_pkt_4022`; target `operator-mandate:raw-git-typed-receipt-integration-2026-05-14T16:18Z`; posted `2026-05-14T16:21:45.528508Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4023` Packet finding: OPERATOR META-META-MANDATE 2026-05-14T16:25Z: step H expanded to TWO subaxes — un-guarded invariants (existing) + system-alignment misfits (NEW). Propose typed SystemAlignmentRole + SystemImprovementOpportunity + SystemIm... (source `rev_pkt_4023`; target `plan:MP-378`; posted `2026-05-14T16:27:23.287257Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4024` Packet finding: P10 substrate pre-commit review: 13/13 fields match rev_pkt_4022 (StrEnum stronger + git_args added). BUT 2 load-bearing INTEGRATION-MISSING per NEW SystemAlignmentRole (BypassLifecycle linkage zero imports; GovernedExcep... (source `rev_pkt_4024`; target `dev/scripts/devctl/runtime/raw_git_bypass_receipts.py`; posted `2026-05-14T16:37:21.885735Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4025` Packet finding: OPERATOR CLARIFICATION 2026-05-14T16:46Z: end-of-session governed push MUST automatically read raw_git_bypass_receipts.jsonl + replay skipped guards per receipt. Without automation, receipts are write-only. Propose Compon... (source `rev_pkt_4025`; target `operator-mandate:automated-guard-replay-2026-05-14T16:46Z`; posted `2026-05-14T16:44:08.365779Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4026` Packet finding: P10 post-commit: 3/3 rev_pkt_4024 absorbed (BypassLifecycle 33 refs + GovernedException 12 refs + HEAD-advance noop guard) + 9/9 tests PASS + live dogfood proves fixes work. BUT META-RECURSIVE MISS WORSE THAN P1 — P10 has... (source `rev_pkt_4026`; target `dev/scripts/devctl/runtime/raw_git_bypass_receipts.py`; posted `2026-05-14T17:08:36.086567Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4027` Packet finding: OPERATOR UX OBSERVATION 2026-05-14T17:25Z: bare ok=true is misleading especially in BLIND-pass cases. R52 Guard P1 returning ok=True while invisible to missing P10 applied row IS the empirical proof. Propose typed TypedOu... (source `rev_pkt_4027`; target `operator-mandate:typed-output-human-summary-2026-05-14T17:25Z`; posted `2026-05-14T17:27:10.553200Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4028` Packet finding: Guard P2 PRE-COMMIT: 7/7 tests PASS + 4/4 wiring + live human_summary (rev_pkt_4027 partial absorption ✓). BUT COMPOSE-PARALLEL trip-wire: substrate:24-27 hardcodes TASK_STARTED_KIND literals instead of importing canonica... (source `rev_pkt_4028`; target `dev/scripts/checks/check_packet_pkt_bind_completeness.py`; posted `2026-05-14T18:07:27.191621Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4029` Packet finding: P2 commit 03379dd7: 7/7 tests + live human_summary (rev_pkt_4027 organic absorption 2nd instance) + snapshot pairing + canonical 6-step. BUT 3rd ITERATION of META-recursive miss (P1+P10+P2 all same pattern): grep commit:0... (source `rev_pkt_4029`; target `dev/scripts/checks/check_packet_pkt_bind_completeness.py`; posted `2026-05-14T18:26:34.766154Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4030` Packet finding: OPERATOR MANDATE 2026-05-14T18:48Z: codebase claims portable governance platform but ships codex-voice-specific literals. Empirical proof: Guard P1+P2 both hardcode MANDATE_PACKET_ID="rev_pkt_4017" — fresh adopter repo wo... (source `rev_pkt_4030`; target `plan:MP-378`; posted `2026-05-14T18:48:44.743899Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4031` Packet finding: rev_pkt_4032: FeatureLifecycleProof + Guard P17 + wrapper-pre-push fix — 8th un-typed drift class; 0 push-receipts in entire store; raw-git push wrapper empirically failed end-to-end (pre-push hook blocks); 73 batched com... (source `rev_pkt_4031`; target `plan:MP-355`; posted `2026-05-14T19:27:57.255365Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4032` Packet finding: Comprehensive operator-mandate: role-capability dictation + toggle-accountability + agent_mind under-use + 15-20 parallel surfaces + Guard P20 anti-parallel-literals. 6 prior plans queued (rev_pkt_3685/3964/3965/3966/MP37... (source `rev_pkt_4032`; target `plan:MP-355`; posted `2026-05-14T19:58:51.536006Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4033` Packet finding: Queue-attention dysfunction (12th un-typed-drift). 1366 plan rows / 1317 queued (96.4%) / 681 stalled ≥3 days (51.7% of total) / oldest 14 days (MP377-GUARDIR-ACTION-SPACE-CATALOGUE). Supplement to rev_pkt_4032. Proposed ... (source `rev_pkt_4033`; target `plan:MP-355`; posted `2026-05-14T20:03:04.790894Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4034` Packet finding: Priority+linking+self-discovery (13th un-typed-drift) + post-commit 22cfecd2 fleet report. Charter P88-P93 FALSELY claimed landed (rev_pkt_3860) — zero Python hits. 198 probes, ZERO target operator-class findings. codesme... (source `rev_pkt_4034`; target `plan:MP-355`; posted `2026-05-14T20:14:01.306066Z`; binding `plan_row`).
- [ ] `PKT-BIND-REV-PKT-4035` Packet finding: 14th un-typed-drift: agent-as-typed-workflow + continuous-improvement-mode. Operator's 14 manual mandates THIS session = empirical proof AI lacks typed discovery mode. Proposed AgentWorkflowSpec + ContinuousImprovementMod... (source `rev_pkt_4035`; target `plan:MP-355`; posted `2026-05-14T20:15:57.879324Z`; binding `plan_row`).
