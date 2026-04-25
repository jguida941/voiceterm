# Remote Control Runtime Closure Plan

**Status**: active  |  **Last updated**: 2026-04-18 | **Owner:** Tooling/control plane/review runtime/dashboard
Execution plan contract: required
This spec is mirrored in `dev/active/MASTER_PLAN.md` under `MP-380..MP-387`.
It closes the remote-control/operator-surface gaps found in the 2026-04-04
architecture review of commits `5bed0fa..4094c39` and the 2026-04-05
pushed-branch review through `b819efa`.

## Scope

Close the remaining phone/remote-control architecture gaps without creating a
second bridge-only authority path. The target is one typed remote-control
runtime that drives reviewer lifecycle, action requests, dashboard projections,
auto-poll behavior, and slim reviewer bootstrap/session-resume truth across
CLI, bridge compatibility text, and later phone/operator-console clients.

Out of scope for this tranche: a second VCS executor, a second packet/action
transport, or any new frontend that parses raw bridge markdown once a typed
contract exists.

## Execution Checklist

- [ ] MP-384 / MP-387 coordination-read-model convergence: carry
      `CoordinationSnapshot` through `ControlPlaneReadModel`, make
      `startup-context` summary/machine-summary and reviewer bootstrap read the
      same bounded coordination/current-slice/resync truth, and prove one
      governed remote-control launch where the operator sees the same topology,
      fanout, ownership, and resync answer across dashboard, bootstrap, and
      phone-facing views.
- [ ] MP-384 / MP-387 role-first participant/turn-authority closure: replace
      provider-biased defaults and projections (`runtime/role_profile.py`,
      turn-authority helpers, bridge/handoff poll fields, same-provider
      rollover assumptions) with typed role + actor assignment so Codex,
      Claude, or another supported provider can fill reviewer, implementer, or
      dashboard/operator roles over the same backend. Prove the first live
      matrix as `Codex reviewer + Codex worker implementer + Claude phone
      dashboard`, then widen to swapped reviewer/implementer assignments
      without changing the backend authority path.
- [ ] MP-383 / MP-385 remote participant communication slice: project one
      typed actor/work-claim view for reviewer, coder, and delegated agents,
      then route repo-owned packet/action-request communication from
      remote-control/dashboard/phone surfaces to those participants without
      reviving bridge-only prose as authority.
- [x] Architecture-review the 8 commits ahead of the tracked upstream and map
      the gaps onto existing owner contracts.
- [x] MP-380 Add one typed operator-interaction mode (`local_terminal` vs
      `remote_control`) and project it through `ProjectGovernance`,
      `StartupContext`, `ReviewState`, and reviewer-runtime surfaces.
      (Partial: fail-closed slice landed; ReviewState projection deferred.)
- [ ] MP-381 Add one typed `CheckResult` / `ViolationRecord` contract family
      plus one shared renderer/JSON projection for checks, probes,
      governance-review, startup summaries, and dashboard consumers.
- [x] MP-382 Finish headless session lifecycle closure so launch, recovery,
      and rollover honor typed operator mode, survive non-zero conductor exit,
      and do not recommend `Terminal.app` in remote-control mode.
      (Partial: terminal-mode/visibility plus proof-of-life slices landed;
      session cleanup, orphan refusal, startup preflight cleanup, and full
      rollover/recovery closure remain.)
- [x] MP-383 Converge bridge `## Action Requests` onto the existing
      `PacketPostRequest(kind="action_request")` event path and keep bridge
      action rows as projection-only compatibility text.
- [ ] MP-384 Make `devctl dashboard` the single operator surface over typed
      review/runtime/check state instead of bridge regex and `format_steps_text`
      parsing.
- [ ] MP-384 narrow read-side convergence must include helper/fallback seams,
      not only top-level commands: `mobile_status`, `control_state`,
      startup-repair/status fallbacks, `repo_packs/review_helpers.py`, and
      repo-pack thin-client readers must stop rebuilding control truth when
      `ControlPlaneReadModel` / typed `ReviewState` already exist.
- [ ] MP-385 Add repo-owned remote-control auto-poll/update cadence for
      reviewer, implementer, and operator-facing surfaces using the same typed
      runtime state and packet queue.
- [ ] MP-386 Add one typed discoverability/system-map slice with
      `SystemCatalog`, derived `AgentDispatchPacket`, and a thin `view`
      adapter so agents/operators can ask what exists, what to run, and how to
      render it without reviving prose-only discovery.
- [ ] MP-386 converge the duplicate `SystemCatalog` / `AgentDispatchPacket`
      families through an adapter plus public-surface parity for
      `discover`, `view`, and `context-graph` before deleting either schema
      family.
- [ ] Add graph-backed duplicate-authority probes over `context-graph`,
      `SystemCatalog`, and `AgentDispatchPacket`: detect stale bridge/fallback
      readers, missing guard-dispatch coverage, dead topology, and
      plan/prompt drift first as measured probes, then only promote proven
      low-noise cases into blocking guards.
- [ ] Keep the read-side graph tranche dependency-ordered. This lane consumes
      the graph/query substrate; it does not invent a second backend. Do not
      widen into read-side schema diff, `SystemCatalog` union-diff, or other
      heavier graph claims until the smaller codeshape/query substrate and the
      declared consumer schemas exist in the upstream owner docs.
- [ ] Add graph-backed guard-coverage closure over the same policy surface:
      label each active `check_*.py` / hard-guard node with its routed quality
      lane from repo policy, then fail when a declared hard guard has no live
      incoming lane binding. Missing enforcement coverage should become a
      query result instead of a manual audit.
- [ ] Keep those graph-backed read-side proofs bounded: current-tick parity or
      mutation-adjacent guards may fail closed only when they use the current
      snapshot plus a matching graph-schema version. Historical trend queries,
      corpus comparisons, and retrospective topology scans stay advisory until
      precision is proven.
- [ ] Add one read-side schema-diff proof over
      `dev/scripts/devctl/commands/dashboard.py`,
      `dev/scripts/devctl/commands/mobile_status.py`,
      `dev/scripts/devctl/runtime/control_state.py`,
      `dev/scripts/devctl/commands/governance/session_resume_support.py`, and
      `dev/scripts/devctl/runtime/startup_context.py`: each consumer must
      derive the same bounded control fields from `ControlPlaneReadModel` /
      typed `ReviewState`, or emit a typed mismatch instead of silently
      restacking fallbacks.
- [ ] Converge `dev/scripts/devctl/governance/system_catalog.py` and
      `dev/scripts/devctl/platform/system_catalog.py` through one union-diff
      adapter that records `{origin, compatibility_mode, data_loss}` per
      field and uses that diff to choose the canonical public schema before
      broader `discover` / `view` rollout.
- [ ] Add a raw-bridge-reader anti-regression guard for this lane: new
      read-side consumers must not parse `bridge.md` or dashboard bridge
      sections directly when typed `review_state` / `ControlPlaneReadModel`
      already exist. Track the remaining sanctioned compatibility parsers
      explicitly and block fresh ones from landing outside that path.
- [ ] Replace heuristic stale-topology cleanup with graph-backed packet/session
      evidence where possible: track session, decision-packet, approval, and
      review-candidate edges across recent generations so queue expiry and
      dead-topology cleanup can distinguish abandoned state from merely
      delayed operators.
- [ ] Build two graph-backed runtime proofs on top of the same contracts:
      cluster recurring findings from `dev/scripts/devctl/runtime/finding_contracts.py`
      plus `dev/scripts/devctl/governance/guard_findings.py` so repeated
      patterns escalate deterministically, and emit one cross-surface parity
      artifact proving startup, session-resume, dashboard, mobile, and bridge
      compatibility surfaces agree on `{snapshot_id, generation_id, head_sha,
      worktree_hash}` for the same proof tick.
- [ ] Once those read-side schemas stabilize, derive parity tests from the
      contract graph instead of hand-maintaining one-off assertions. Invariants
      such as `ControlPlaneReadModel` / `StartupContext` push-readiness and
      reviewer-bootstrap field parity should generate focused regression tests
      from the same schema graph.
- [ ] MP-387 Make `session-resume` / `SessionCachePacket` the first-hop
      reviewer bootstrap with `last_reviewed_sha`, `head_at_push_time`, one
      frozen `ReviewCandidateRecord` for dirty-tree or commit-range review
      targets, current-head freshness, and typed operator-mode truth derived
      from repo-owned artifacts instead of stale bridge prose.

### 2026-04-05 Architecture Absorption Tranche

- [x] MP-380 Fail closed on unresolved operator interaction mode. Remote-
      control sessions must not silently downgrade to `local_terminal` in
      `ProjectGovernance`, `StartupContext`, or `ControlPlaneReadModel`.
- [ ] MP-381 Extend platform contract closure to `ControlPlaneReadModel`,
      `AutoModeState`, and `SessionCachePacket`, including field-route families
      for dashboard, phone/mobile, startup-context, auto-mode, and session-
      resume projections.
- [x] MP-382 Require reviewer proof-of-life for
      `review-channel --action launch|rollover --terminal none`; detached
      publisher/supervisor heartbeats without live conductor sessions are a
      launch failure plus cleanup/recover state, not a healthy launch.
- [ ] MP-382 Follow-through: add `devctl session-cleanup`, prelaunch orphan
      detection, and launch refusal/force-clean semantics so session lifecycle
      safety matches the now-typed terminal visibility contract.
- [ ] MP-384 Invalidate stale review verdict/findings when
      `review_needed=true` or `reviewed_hash_current=false`; operator-facing
      surfaces must project stale-review truth instead of replaying old verdict
      text as current authority.
- [ ] MP-384 and MP-385 Split `pending_packets_total` from
      `pending_action_requests` so dashboard/doctor/auto-mode/operator surfaces
      stop treating every queued packet as an actionable request.
- [ ] MP-384 and MP-385 clarify `safe_to_fanout=false` as a mutating-fanout
      and worktree-expansion block, not a blanket analysis block, and project
      that distinction through dashboard, bootstrap, prompt, and operator
      surfaces so read-only advisory review remains allowed.
- [ ] MP-386 and MP-387 Make guard/contract discoverability and reviewer
      bootstrap align: `SystemCatalog` / `AgentDispatchPacket` should expose
      the exact guard bundle and typed context a fresh Claude or Codex session
      must consume before acting.
- [ ] MP-386 and MP-387 migrate AI/bootstrap teaching surfaces off bridge-first
      lore: generated `CLAUDE.md`, `bootstrap_surfaces.py`,
      `remote_bridge_prompt.md`, and review-channel prompt sections must render
      typed workflow guidance from canonical runtime state.
- [ ] MP-381 and MP-384 Make validation cadence deterministic and inspectable:
      expose a tree-bound `ValidationPlan` / `ValidationReceipt` selected by
      repo routing, project selected bundle/add-ons/escalation reasons plus
      checkpoint/push sufficiency, and treat missing quality evidence as
      `unknown` / `stale` instead of green.
- [ ] MP-387 proof closure: add one fresh-AI bootstrap proof and one read-only
      blocked-fanout remote-review proof in addition to the live
      remote-control/dashboard parity run.

## Cross-Cutting Closure Rules

1. AUD-10 explainability
   - Every new remote-control status/report surface must project typed reason
     chains (`diagnosis`, `policy`, `target`, `fix`, `source`) from canonical
     runtime/check contracts instead of reducing failures to prose-only
     summaries.
2. AUD-11 agent-agnostic capability rule
   - Lifecycle hooks, notification channels, permission relay, scheduled
     tasks, and delegated-agent coordination may land only as repo-owned
     runtime/adapter contracts or typed follow-on packets. Do not add
     Claude-only or bridge-only authority paths.
3. AUD-13 session cleanup
   - `MP-380` and `MP-382` own stale-session/orphan cleanup, startup preflight
     cleanup, and dashboard/doctor visibility over conductor, daemon, and
     Terminal ownership. Follow-on slices may consume those typed outputs but
     must not fork lifecycle authority.
4. AUD-14 session rollover
   - `MP-382` and `MP-385` must extend `HandoffBundle`, `launch_records`, and
     reviewer-runtime rollover truth to same-provider handoff (`Claude ->
     Claude`, `Codex -> Codex`) plus clean old-session retirement and
     operator-visible transition history.

## Python Contract-Shape Alignment (2026-04-05 Kobzol audit absorption)

These rules absorb the six-pattern Python audit into the active remote-control
plan. They govern touched files in the current `MP-380` / `MP-382` slice first,
then carry forward into `MP-381`, `MP-383`, `MP-384`, and `MP-387`. They do
not authorize a repo-wide cleanup pass outside the bounded execution slice.

1. Type hints on edited surfaces
   - Every new or edited function in this tranche must land with explicit
     parameter and return annotations so the fail-closed operator-mode and
     proof-of-life path is statically checkable at the boundaries we touch.
2. Dataclasses at runtime boundaries
   - When typed owners already exist (`ProjectGovernance`, `StartupContext`,
     `ReviewerGateState`, `ControlPlaneReadModel`, `SessionCachePacket`,
     launch/recovery snapshots), keep those models alive through function
     signatures and reducers instead of collapsing to `dict[str, Any]`,
     ad hoc tuples, or projection-first helpers.
3. Closed variants as types
   - Finite mode/kind/status sets in this lane (`operator_interaction_mode`,
     launch posture, proof-of-life/runtime state, action kind, compact
     format selectors) should use `Literal`, `StrEnum`, or a closed union
     before another raw string-dispatch branch is added.
4. Minimal newtypes where swap risk is real
   - When a touched helper takes multiple same-shaped identifiers or labels in
     one call, introduce a narrow `NewType` wrapper only if it removes a real
     transposition hazard in the operator/runtime contract. Do not add
     decorative wrappers with no immediate boundary value.
5. Owner-side construction functions
   - Prefer `@classmethod` / named construction helpers on the owning
     dataclass when the same runtime record can be built from distinct control
     paths (for example launch, recovery, or resume) instead of scattering
     parallel `build_*` / `*_from_payload` logic across unrelated helpers.
6. Typestate over boolean bundles
   - `MP-382` specifically must collapse proof-of-life, waiting-for-input,
     stale, detached-only, and explicitly-stopped launch truth into one typed
     lifecycle state instead of re-deriving health from loose boolean bundles
     in multiple surfaces.

## Data Contracts

1. Operator-mode authority
   - Declared owner: extend `ProjectGovernance.BridgeConfig` with one typed
     operator-interaction mode (`local_terminal` or `remote_control`).
   - Live projection: mirror the same value into `ReviewState` collaboration /
     reviewer-runtime surfaces and `StartupContext.reviewer_gate`.
   - All launch, recovery, dashboard, and auto-poll decisions must read that
     value instead of hardcoding `terminal-app` vs headless behavior.
2. Remote-control mutation/approval transport
   - Authoritative transport: the existing review-channel packet/event path,
     specifically `PacketPostRequest(kind="action_request")` with typed target
     metadata and reduced packet state.
   - `bridge.md` `## Action Requests` remains compatibility projection only. It
     may summarize pending action packets, but it must not become a second
     execution queue or parser-owned authority surface.
   - Packet transport receipts are not implementer ACKs. `ack`, `apply`, and
     `dismiss` update packet lifecycle only; the implementer ACK contract still
     requires `Claude Ack` / typed `current_session` evidence for the current
     instruction revision.
3. Check and violation evidence
   - Add one typed `CheckResult` owner for per-check execution state plus one
     typed `ViolationRecord` row for normalized file/line/policy/fix detail.
   - `ViolationRecord` is the only structured violation row rendered by
     dashboard, CI summaries, startup summaries, and compact AI-facing status
     output. `Finding` remains the escalated governance-review record derived
     from a violation when richer review/probe evidence is required.
4. Frontend rule
   - `devctl dashboard`, bridge projections, phone/mobile surfaces, and the
     Operator Console consume typed `ReviewState`, reduced packet state, and
     typed check-result artifacts.
   - Raw bridge regex and `format_steps_text()` scraping are transitional debt
     to remove during `MP-384`, not long-term frontend/runtime contracts.
5. Discoverability / dispatch / presentation
   - `SystemCatalog` is a static generated capability registry built from
     existing command, guard, probe, surface, and repo-policy registries. It
     owns "what exists", not live runtime truth.
   - `AgentDispatchPacket` is a derived routing packet composed from
     `classify_lane()`, live quality policy, and
     `StartupContext` / `ProjectGovernance.enabled_checks`. It recommends
     "what to run" for a bounded change set and never becomes a second policy
     store.
   - The future `devctl view` adapter is a frontend-only renderer dispatch
     over typed artifacts (`ReviewState`, `ControlState`, `SystemCatalog`,
     typed check results). It owns "how to show it", not execution or state
     mutation.
   - `context-graph` keeps relationship topology ownership; any catalog,
     dispatch, or view slice must feed or consume it without duplicating edge
     authority.

## Architectural Diagnosis (2026-04-05, triple-validated: Claude 3-agent + Codex GPT-5.4 + operator review)

**Core finding**: The read side (ControlPlaneReadModel, AutoModeState, SessionCachePacket) is increasingly correct. The write side (enforcement, closure, parity) is still incomplete. The system can describe the right behavior while still allowing the wrong behavior.

**In the operator's terms**: "You now have a decent IR. What you still need is a linker, a lease manager, and proof-carrying CI."

### Evidence chain
- `afd6866` introduced ControlPlaneReadModel to replace 5 independent state computations ✓
- `79be213` fixed typed review_accepted, split conductor liveness ✓
- `976f816` moved auto-mode onto the shared read model ✓
- `e6bdb7b` wired all 5 surfaces to ControlPlaneReadModel ✓
- `0c0746b` added head-tracking/drift wiring for reviewer startup ✓
- BUT: bridge.md still shows rejected review of `7103707..031782e` while HEAD is at `8bb3c66`
- BUT: `ControlPlaneReadModel`, `AutoModeState`, `SessionCachePacket` not in platform-contract-closure catalog
- BUT: raw `git commit` completely bypasses 64 guards
- BUT: operator_interaction_mode silently defaults to `local_terminal` in a phone-steered session
- BUT: headless launch declares success on `Popen()` without reviewer proof-of-life
- 198 tests pass, contract-closure passes, CI looks green — while live runtime reports `reviewer_heartbeat_stale`, `launch_truth=detached_runtime_only`, `last_reviewed=none`, `mode=local_terminal`

### Root cause
Not "no CI" and not "the model is dumb." The repo lacks a hard closure mechanism that makes disconnected logic structurally impossible. The plan already names the fix: one contract-field registry, one closure guard, one parity guard, one end-to-end connectivity check, and one governed commit path. Until those exist, the model can still "do the wrong thing" because the system still permits unguided write paths and partial propagation.

## Execution Priorities (2026-04-05, operator-approved order)

These supersede the original MP-380..MP-386 order for implementation sequencing.
The MP scopes remain valid but are now cross-cut by enforcement-first priority.

### 2026-04-12 Phase-0 visibility override

Before widening into more autonomy or dashboard polish, keep this bounded
remote/runtime order explicit:

1. Collapse dashboard, monitor, mobile-status, and phone-status onto one
   reducer-backed blocker/next-action vocabulary.
2. Make `FindingBacklog` the single open-findings reader for runtime,
   dashboard, startup, monitor, bridge, and ranked backlog tooling.
3. Freeze one shared packet lifecycle plus bidirectional event wake path for
   all lanes, not separate timer pollers and inbox heuristics.
4. Surface live tool-call / mutation progress through typed `agent-mind` /
   current-session state so the dashboard stops guessing from historical
   messages.
5. Only after those visibility surfaces converge, rerun the role-first remote
   commit/push proof and widen loop-v2 / `devctl develop` consumers.

### Priority 1: Close enforcement — `devctl commit` + repo hook (AUD-27)
- **What**: Raw `git commit` without a green guard bundle must be structurally impossible
- **Scope**: Git pre-commit hook + `devctl commit` wrapper + CI guard verifying governed pipeline
- **Why first**: Every other fix can be committed ungated without this. Nothing else matters if commits bypass guards.
- **Touches**: MP-380 (governance enforcement), AUD-27

### Priority 2: Session-resume as mandatory reviewer bootstrap
- **What**: Reviewer launch/relaunch begins with `session-resume --role reviewer`; if `head_sha != last_reviewed_sha`, review that exact range — no blind polling
- **Scope**: Wire conductor prompt to start from session-resume, heartbeat must capture HEAD on every write
- **Why second**: Fixes the stale-review loop (AUD-22) and makes reviewer sessions deterministic
- **Touches**: MP-382 (session lifecycle), AUD-22, Finding 2

### Priority 3: Hard parity guard — `check_control_plane_parity.py` [LANDED 2026-04-07]
- **What**: One fixture proves dashboard, auto-mode, session-resume, phone, and mobile agree on every parity field each surface actually exposes from the same ControlPlaneReadModel inputs. Surfaces that intentionally omit a field are skipped by the comparator rather than treated as parity violations (see **Per-surface omissions** below).
- **Scope**: New guard or extension of `check_platform_contract_closure.py`
- **Why third**: Without parity proof, surfaces can silently disagree and the operator sees different state depending on which surface they check
- **Touches**: MP-381 (typed contracts), AUD-24, Findings 5, 11, 18
- **Closure (2026-04-07)**: Implemented as the new
  `dev/scripts/checks/platform_contract_closure/field_routes_parity.py` module
  wired into `check_platform_contract_closure`. One deterministic fixture
  flows through dashboard `_assemble`, `inputs_from_read_model`,
  `build_from_sources`, and the pure phone/mobile `_control_plane_section`
  helpers; the comparator fails the closure aggregator on any cross-surface
  disagreement on the parity fields. Phone surface refactored to expose a
  pure `_control_plane_section(model)` matching `mobile_status` so the
  fixture path stays I/O-free. Follow-up: Finding F11 also needs a
  loud-failure mode at the dashboard layer when the read model is missing.
- **Closure tightening (2026-04-08)**: `PARITY_FIELDS` now explicitly covers
  `reviewer_mode` and `operator_interaction_mode` on every surface that
  carries them, and the auto-mode extractor no longer falls back to
  `model.next_action` when `inputs_from_read_model` returns an empty
  `push_decision_action`. A new regression test
  `test_parity_guard_catches_broken_auto_mode_next_action_route` proves a
  broken auto-mode route now surfaces as a `next_action` parity divergence
  naming `auto_mode` as the disagreeing surface instead of silently going
  green.
- **Per-surface omissions** (intentional, comparator skips absent fields
  rather than flagging parity violations):
  - `SessionCachePacket` (session-resume) has no direct `reviewer_mode`
    slot and only derives mode internally from an upstream `reviewer_mode`
    input, so the parity guard does not check `reviewer_mode` against
    session-resume; the remaining four surfaces still cross-check it.
    `SessionCachePacket` also does not carry `push_eligible`,
    `implementation_blocked`, `review_accepted`, or
    `pending_action_requests`, because those are not part of the
    session-resume bootstrap contract.
  - `AutoModeInputs` scopes itself to the auto-mode decision surface and
    therefore omits `resolved_phase`, `push_eligible`, `top_blocker`, and
    `next_command`; the four remaining surfaces still cross-check those.
  - The phone `_control_plane_section` intentionally omits
    `implementation_blocked`; mobile, dashboard, and auto-mode continue to
    cross-check it, and `test_phone_pure_function_matches_disk_function`
    pins the omission so it cannot silently widen.

### Priority 4: Field-registry / closure pass (AUD-25)
- **What**: New typed fields registered once, auto-checked for consumer coverage, test scaffolding, renderer binding, SystemCatalog presence
- **Scope**: Register `ControlPlaneReadModel`, `AutoModeState`, `SessionCachePacket` in platform contract catalog; extend field-route families
- **Why fourth**: The architecture has the IR but not the linker — this IS the linker
- **Touches**: MP-386, AUD-25, Codex-1, Finding 18

### Priority 5: Demote bridge.md to projection-only in practice
- **What**: Move durable workflow instructions to plan/runbook authority; keep bridge narrowly stateful; add freshness/generation checks
- **Scope**: Invalidate reviewer acceptance when `reviewed_hash_current=false`; stale bridge data cannot silently drive behavior
- **Why fifth**: Bridge-as-authority is the source of every stale-review and stale-verdict bug
- **Touches**: MP-383, Codex-5, Findings 1, 4, 7, 8

### Priority 6: Governance CI as primary lane
- **What**: One workflow running governance/runtime test suite, parity guard, contract-closure, and end-to-end connectivity proofs
- **Scope**: New or updated workflow that tests packets, checks, probes, session-resume, auto-mode, remote-control mode
- **Why sixth**: Current CI reflects older product shape (Rust VoiceTerm) more than governance platform
- **Touches**: MP-384, AUD-23, AUD-26

### Priority 7: Split resolver concerns
- **What**: `control_plane_resolve.py` split into artifact loaders, source-precedence policy, pure reducers, surface renderers
- **Scope**: Refactor only — no new behavior, just clearer boundaries for future guard generation and parity testing
- **Why last**: Architecture improvement that makes Priorities 3-4 easier to maintain long-term
- **Touches**: MP-381, Finding 5

## 26 Consolidated Findings (Claude 20 + Codex 6, 2026-04-05)

### P0 CRITICAL

| ID | Finding | File(s) | Fix |
|---|---|---|---|
| F1 | Bridge parsed as authority via regex (3 independent regex parses fail silently) | reviewer_state.py:270-322 | Read typed state from review_state.json first |
| F2 | `head_at_push_time` never updated on heartbeat — ROOT CAUSE of stale reviews | reviewer_state.py:57-96 | Every bridge write must capture current HEAD |
| F3 | No pre-commit hook installed (AUD-27) — 65+ ungated commits | .git/hooks/ | Install hook + `devctl commit` + CI audit |

### P1 HIGH (Claude)

| ID | Finding | File(s) | Fix |
|---|---|---|---|
| F4 | Session-resume missing auto-mode phase | session_resume_support.py | Add resolved_phase, next_transition to SessionCachePacket |
| F5 | Session-resume contradicts ControlPlaneReadModel (reads receipt directly) | session_resume_support.py:130-156 | Pure projection of read model, delete receipt-reading |
| F6 | No projection schema version validation | projection_bundle.py:45-150 | Assert schema_version at entry |
| F7 | No bridge/JSON projection parity guard | reviewer_state.py, reviewer_state_support.py | Post-write parity check |
| F8 | `push_eligible` ignores `last_guard_ok` | control_plane_read_model.py:154 | Gate on both push_action AND last_guard_ok |
| F9 | Session cache ignores receipt mtime | session_resume_support.py | Add receipt_mtime to cache key |
| F10 | `push_decision_action` no enum validation | auto_mode.py | Assert valid values at entry |
| F11 | Dashboard falls back to independent computation | dashboard.py:419-476 | Fail loudly or show "read model unavailable" |

### P1 HIGH (Codex)

| ID | Finding | File(s) | Fix |
|---|---|---|---|
| C1 | Contract-closure doesn't cover control-plane contracts | runtime_state_contract_rows.py, field_routes.py | Register ControlPlaneReadModel/AutoModeState/SessionCachePacket |
| C2 | Headless launch optimistic — no reviewer proof-of-life in terminal=none | bridge_launch_control.py:117 | Require proof-of-life, cleanup on failure |
| C3 | Remote-control mode fail-open to local_terminal | project_governance_contract.py:200 | Emit unknown and block if unresolved |
| C4 | Local commits structurally ungated | .pre-commit-config.yaml | devctl commit or Git hook with guard bundle |

### P2 MEDIUM

| ID | Finding | Fix |
|---|---|---|
| C5 | Stale review verdict replayed as current truth | Invalidate acceptance when reviewed_hash_current=false |
| C6 | pending_action_requests counts all packets | Split into pending_packets_total and pending_action_requests |
| F12 | build_conductor_prompt has 19 params, bare dicts | Extract to dataclasses |
| F13 | Broad-except swallows errors in preamble build | Add structured logging |
| F14 | Projection refresh silently fails | Add logging/result enum |
| F15 | AutoModeInputs.push_decision_reason orphan field | Remove or wire |
| F16 | ControlPlaneReadModel.ahead_of_upstream orphan field | Remove or wire |

### Missing Guards (new)

| ID | Guard | Check |
|---|---|---|
| F17 | check_bridge_head_freshness.py | head_at_push_time age < heartbeat interval |
| F18 | Extend check_platform_contract_closure.py | Every ControlPlaneReadModel field consumed by ≥1 surface |
| F19 | Auto-mode transition invariants | PUSHING/COMMITTING require last_guard_ok==True |
| F20 | check_heartbeat_consistency.py | Fresh poll + stale HEAD = error |

### 8-Agent Implementation Fan-Out (pending Codex approval)

| Agent | Scope | Priority | Touches |
|---|---|---|---|
| 1 | `devctl commit` wrapper + pre-commit hook | P1 / AUD-27 | F3, C4 |
| 2 | Session-resume mandatory reviewer bootstrap | P2 / AUD-22 | F2, F4 |
| 3 | `check_control_plane_parity.py` guard (landed 2026-04-07) | P3 / AUD-24 | F18, F11 |
| 4 | Register contracts in platform catalog | P4 / Codex-1 | C1, F18 |
| 5 | Invalidate stale reviewer acceptance | P5 / Codex-5 | C5, F7 |
| 6 | push_eligible + auto-mode transition invariants | Quick wins | F8, F10, F19 |
| 7 | Split pending_action_requests + cache fix | Codex-6 | C6, F9 |
| 8 | Headless launch proof-of-life + operator mode | Codex-2/3 | C2, C3 |

## Progress Log

- 2026-04-18: Closed the first role-implicit commit-approval gap in the live
  `/remote-control` dogfood loop without reopening blanket promptless
  approval. Governed commit preflight now resolves a typed
  `CommitApprovalAuthority` from `interaction_mode` plus active
  `remote_control_attachment` evidence, so `remote_control` only
  auto-satisfies approval when runtime proves an active operator-role
  delegate for the current lane. Plain `remote_control` still fails closed at
  `operator_approval_pending`, and `devctl commit --approve-pending` remains
  the explicit resume path otherwise. Focused proof is green on the
  delegate-backed auto-approval, no-delegate pending, explicit resume, synced
  approval persistence, pending-phase reporting, and interaction-mode
  resolution regressions.
- 2026-04-15: Locked the remote-control dogfood expansion to one typed
  baseline instead of ad hoc widening. The owner-doc chain now says the first
  live proof is `Codex conductor/reviewer + Claude remote-control implementer
  + permanent Claude packet watcher`, not a free-form worker swarm, and the
  dogfood ledger can now record the campaign/scenario/topology/lane linkage
  that ties those remote runs back to canonical findings and `LIVE_RUN`
  mirror updates. The compatibility-finding ingress is explicit too:
  `governance-import-findings --input-format md` now imports `LIVE_RUN.md`
  through repo-scoped `repo_name:Q-ID` identity, so remote-control misses can
  move into the canonical backlog without hand-copying markdown prose.
- 2026-04-13: Closed the guard-driven modularization and compatibility-seam
  cleanup that the live remote-control dogfood loop surfaced in the typed
  review-channel/runtime lane. The pending-packet, reviewer-follow,
  session-resume, startup-context, bridge-projection, collaboration-session,
  review-state parser/model, and status projection/state surfaces now route
  through smaller companion modules without tripping dict-schema, code-shape,
  duplication, or parameter-count guards. The same pass restored the old
  monkeypatch/import compatibility seams that the refactors briefly broke
  (`review_channel.state`, `commands.review_channel.status`,
  `session_resume_support`, `collaboration_session`, `reviewer_follow`,
  current-session support), and the full affected Python test surface is green
  again. The remaining non-code blocker is external to this slice: the
  startup-authority checkpoint gate still requires the governed commit that
  the writable lane must execute on Codex's behalf.
- 2026-04-13: Closed the first load-bearing typed attention/revocation slice
  from the live Codex/Claude dogfood loop. `ReviewState` now carries one
  canonical `packet_inbox` reducer over packet lifecycle/attention state, and
  the event-backed projection, bridge-backed status projection,
  `startup-context`, `session-resume`, and reviewer-follow all read that same
  typed record instead of recomputing wake/focus independently. Governed stage
  and commit now fail closed with `attention_revision_stale` when the live
  typed inbox carries actionable attention newer than the startup receipt the
  write lane last acknowledged, so stale attention now revokes repo-write
  authority instead of depending on polling folklore or chat-local reminders.
  The same slice also closed the live startup command regressions Claude found
  while dogfooding: `startup-context --format summary` no longer crashes on a
  missing `asdict` import, and the JSON payload now promotes
  `checkpoint_required` / `safe_to_continue_editing` to top-level booleans so
  the explicit block is not buried only inside nested action-routing output.
- 2026-04-13: Closed the next current-instruction detour in the typed review
  path. The queue reducer remains the only place that is allowed to select a
  packet-derived next instruction; `event_current_instruction()` and
  `current_focus_line()` now read the typed queue/current-session authority
  instead of independently falling back to bridge text or raw packet summaries.
  Focused queue/current-session/dashboard regressions are green. The remaining
  live seam is now narrower and explicit: bridge-backed `review-channel
  status` still warns that compatibility markdown drifted from typed
  `current_session`, so the next slice is to collapse that bridge status view
  onto the same typed selector path instead of letting compatibility state lag.
- 2026-04-13: Closed the next startup-slice teaching gap in the live
  remote-control lane. The coordination snapshot reducer no longer lets bare
  scope tokens like `MP-355` outrank a real live typed instruction or
  continuity action, so `startup-context --format summary` now surfaces the
  active typed work item instead of a dead plan token when the session already
  knows what the current slice is.
- 2026-04-13: Closed the live same-agent runtime-count contradiction that
  Claude surfaced during the remote-control dogfood loop. In `single_agent`
  mode the typed collaboration session can already assign both
  `review_agent=codex` and `coding_agent=codex`, but the operator-facing
  runtime counters were still reading only participant rows and therefore
  reported `live_implementer_total=0` whenever Codex was actively coding
  while Claude stayed attached as the dashboard/operator lane. The shared
  runtime-count reducers for `review-channel status` and startup topology now
  consume live typed `role_assignments` first and fall back to participant
  rows only when typed role evidence is absent, so the live lane now projects
  the expected `participants_total=2`, `live_reviewer_total=1`,
  `live_implementer_total=1`, and `active_conductor_count=1`. The remaining
  follow-up is narrower: `startup-context` still carries the stale old
  `current_slice` prose from the pre-fix finding, so current-session/current-
  slice projection still needs its own refresh/convergence pass.
- 2026-04-12: Closed the next stale-compatibility bridge seam in the live
  remote/dashboard lane. `review-channel --action status` already rebuilt the
  typed `review_state` bundle, but the operator-visible `bridge.md`
  compatibility file could still lag behind that truth and leave the real
  state stranded in `dev/reports/review_channel/latest/latest.md`. The status
  path now reuses the existing typed bridge renderer when it detects typed
  `current_session` drift, so a stale `bridge.md` is rewritten from the same
  typed projection during status refresh instead of requiring a separate
  repair command just to make the compatibility bridge match the repo-owned
  state.
- 2026-04-12: Closed one bounded packet-wake gap in the running follow loops.
  `ensure --follow` / reviewer-follow already had a repo-owned cadence runner,
  but their progress token only watched bridge text plus worktree hash, so a
  fresh Claude->Codex pending packet still did not count as live progress
  unless someone separately started `review-channel --action watch --follow`.
  The shared follow-loop progress token now includes the live reviewer packet
  queue, so an arriving reviewer-targeted packet becomes a repo-owned wake
  signal for running follow sessions instead of operator folklore.
- 2026-04-12: Absorbed the latest dashboard architecture review into the
  runtime owner doc. The repo already has most of the required pieces, but
  four status surfaces still describe one blocker differently, findings still
  split across packet/markdown/runtime paths, dashboard wake still depends
  partly on timers, and observer lanes still need separate `agent-mind` reads
  to see live tool calls. The bounded order here is now explicit in plan
  state: surface consolidation, `FindingBacklog`, packet lifecycle/event
  wake, then live tool-call projection.
- 2026-04-12: Rejected the linked-worktree/shadow-gitdir detour after the
  remote-control dogfood session. The active startup receipt on the primary
  lane already projects `worktree_strategy=shared_primary_worktree` with
  `safe_to_fanout=False`, which means the default remote-control
  reviewer/implementer/dashboard stack shares the governed primary checkout
  until an explicit delegated worker is launched. Worker worktrees remain
  optional fanout only, with their own typed `worktree_identity`; treating
  them as the default remote-control topology was an off-spec workaround that
  created stale topology stories and commit-pipeline hacks instead of closing
  the real role/authority/read-model gaps.
- 2026-04-12: Planned the next Q55/Q84 findings-consumer closure from live
  dogfood evidence in the worker lane. `findings-priority` still ranks
  markdown from `LIVE_RUN.md`, `event_open_findings()` currently projects only
  `pending review packet(s)`, dashboard still renders `Open findings: 0`, and
  `monitor` can emit `should_emit_finding=True` without a durable sink. The
  bounded runtime design is now explicit: add one canonical
  `FindingBacklog` snapshot/loader over typed finding rows, make
  `review-channel --action post --kind finding` append backlog rows with
  stable `finding_id` / human `Q-ID` / packet lineage, route
  dashboard/startup/monitor/bridge/findings-priority through that reader, and
  leave `LIVE_RUN.md` as compatibility import/projection only while
  `governance-review` stays the shared disposition sink.
- 2026-04-12: Closed the next bounded stale-projection seam in the remote
  dashboard lane. When governance still points at the legacy
  `.../review_channel/latest` compatibility root, `review_state_locator` now
  prefers the sibling event-backed `projections/latest/review_state.json`
  bundle and preserves that path even for live-refresh callers. That keeps
  dashboard/startup/session-resume on the same event-backed current-slice and
  coordination text instead of silently rehydrating stale bridge-era
  compatibility payloads. The remaining read-side closure is still the larger
  one called out by Q55/Q83: a single canonical `ControlPlaneReadModel` and a
  single typed finding surface shared by packets, dashboard, and ranked
  LIVE_RUN intake.
- 2026-04-12: Closed the next role-first read-model / governed-push identity
  follow-up from the worker-lane beta loop. `review-channel status`,
  dashboard/mobile projections, and shared review-state/runtime readers now
  prefer provider-neutral reviewer/implementer aliases
  (`reviewer_poll_state`, `last_reviewer_poll_*`, `implementer_ack*`) while
  preserving `codex_*` / `claude_*` bridge fields as compatibility-only
  outputs. The same pass made commit/push approval explicitly worktree-bound:
  the staged pipeline, persisted push authorization, and latest-push status
  now carry `worktree_identity`, and publish readiness fails closed when the
  current checkout is not the checkout that staged the approved pipeline. When
  requested worker fanout is zero that checkout is the shared primary lane;
  when an explicit delegated worker exists it is the delegated worker lane.
- 2026-04-12: Closed the next worker-lane portability slice from the same
  role-first beta loop. The launcher no longer treats `LaneAssignment.worktree`
  as read-only plan prose: each launched provider session now resolves one
  workspace root, records it in session metadata, runs the generated
  conductor script from that worktree, and threads the same workspace/lane
  identity into prompt text, collaboration participants, coordination actor
  rows, startup-context rendering, and dashboard/mobile coordination views.
  The same slice also tightened the stale single-agent diagnosis path: when
  typed liveness projects `overall_state=single_agent_active`, recovery
  classification now reports the real blocker (for example
  `checkpoint_required`) instead of forcing a misleading `inactive`/resume
  decision.
- 2026-04-12: Started the role-first remote-control beta-matrix closure in the
  worker lane. The live owner docs already require role-first authority, but
  the current beta state still exposes provider-shaped seams: `single_agent`
  plus a live local reviewer still projects `overall_state=inactive`, stale
  `last_codex_poll_*` fields still leak provider identity into liveness, and
  bridge/handoff/turn-authority helpers still assume `codex reviewer` /
  `claude implementer`. The next closure order is now explicit: converge
  `ControlPlaneReadModel` and typed participant registry first, replace
  provider-coded role defaults and handoff fields second, keep the default
  remote-control lane on the shared primary checkout while requested worker
  fanout is zero and reserve isolated worktrees for explicit delegated-worker
  fanout third, then rerun the live remote-control beta matrix before
  widening to external-repo proof.
- 2026-04-11: Closed the first remote-participant visibility seam for the
  live dashboard/remote-control lane. Active `attach-remote-control`
  artifacts now feed the typed collaboration roster/role assignments instead
  of stopping at `ReviewerRuntimeContract`, so a live external Claude session
  can project as a live implementer in `review_state`, runtime counts,
  registry/actor views, and coordination surfaces even when the old
  prepared-conductor metadata is stale. This is still provider-scoped
  attachment truth, not the final multi-worker/session registry for
  same-provider fanout.
- 2026-04-11: Closed the bounded liveness-emission cleanup that the typed
  authority review had flagged. `attach_conductor_session_state()` is now
  projection-only again, while `review_channel.state.refresh_status_snapshot()`
  invokes the explicit participant-liveness producer and projects any emitted
  expiry rows back into `bridge_liveness`. This keeps event emission owned by
  the refresh boundary instead of a helper-side effect, preserves reducer
  idempotency, and gives the remote-control read path one named producer seam
  for future typed heartbeat cutover work.
- 2026-04-11: Closed the next read/write parity seam for the remote-control
  dashboard lane. The repo-owned reviewer checkpoint/status path no longer
  crashes on the remote-role roster helper typo, and top-level
  `review-channel --action status` now derives runtime counts from the same
  typed collaboration participant state as `doctor`/`startup-context`, so the
  attached Claude remote-control session projects consistently as
  `live_implementer_total=1` / `active_conductor_count=1` across the bridge,
  status JSON, and startup authority surfaces. Static planned-lane capacity
  counts remain a separate follow-up; this closure only makes live runtime
  truth converge on typed participant evidence.
- 2026-04-11: Tightened the remote dashboard observer contract after the live
  beta-test premature-kill miss. The repo-owned `agent-mind` rollout surface
  now summarizes `apply_patch` target files so remote-control/dashboard
  observers can see edit progress through typed state instead of raw JSONL
  grep heuristics, and the tracked remote Claude prompt now requires
  cursor-based `agent-mind` polling plus target-file diff/mtime verification
  before declaring a no-edit stall or killing/relaunching Codex. The same
  prompt also promotes "typed finding first, prose second" so `review-channel`
  packets remain the authority path while `bridge.md` / `LIVE_RUN.md` stay
  compatibility projections.
- 2026-04-11: Closed the next local-reviewer visibility seam for the same
  remote dashboard lane. In `single_agent` mode the collaboration session now
  treats recent typed `review-channel` activity from `codex`
  (`packet_posted/acked/applied/dismissed`) as repo-owned local reviewer
  presence until that evidence becomes truly overdue, so `status`, `doctor`,
  and startup-facing runtime counts can surface the active local Codex
  reviewer even when there is no `codex-conductor.json` artifact. This keeps
  the visibility fix inside typed repo artifacts instead of widening into
  home-directory rollout watchers or process-table heuristics.
- 2026-04-11: Closed the next dashboard parity seam in the same remote-control
  beta loop. `dashboard --view health` and the shared `ControlPlaneReadModel`
  no longer trust stale publisher/supervisor heartbeats first; they prefer the
  typed reviewer-runtime/bridge liveness fields and only fall back to raw
  artifacts when typed authority is absent. The same reducer now also treats
  fresh single-agent local reviewer packet activity as positive repo-owned
  reviewer evidence before trusting stale `codex-conductor.json` metadata, so
  the dashboard, status, and doctor surfaces converge on one daemon/conductor
  story during remote dashboard re-tests.
- 2026-04-11: Closed the next remote-dashboard beta miss after Claude caught a
  long-running Codex turn falling out of single-agent liveness. The shared
  local-reviewer activity authority now treats recent local rollout JSONL
  writes as live evidence when packet activity goes quiet, so `status`,
  `doctor`, collaboration/runtime counts, and dashboard health stay aligned
  during extended edit/test passes instead of timing out on packet recency
  alone.
- 2026-04-11: Closed the queue-plus-hope seam Claude found in the same
  remote-dashboard beta loop. Event-backed `action_request` packets now keep a
  repo-owned typed delivery receipt: post seeds
  `delivery_emitted_at_utc`, targeted `review-channel --action inbox|watch`
  polls stamp `delivery_observed_at_utc` / `delivery_observed_by` only when
  `--actor` matches the target agent, and `ack|apply` stamp
  `execution_started_at_utc` / `execution_started_by`.
  Those fields now flow back into typed packet rows and dashboard pending
  packet JSON, so remote modes can prove they actually saw or started a
  request before the operator treats a pending queue row as ignored.
- 2026-04-11: Closed the next selective-consumption seam in the same
  remote-dashboard beta loop. Event-backed queue derivation now prefers live
  `action_request` packets over later findings/instructions when it projects
  `derived_next_instruction`, and the source payload now records
  `selection_policy`, `control_state`, and `wake_required` /
  `delivery_required` hints. Queue derivation also reruns after receipt
  hydration, so the same repo-owned inbox poll can move a packet from
  `delivery_pending` to `execution_pending` immediately instead of leaving the
  queue metadata one tick behind the packet rows.
- 2026-04-10: Closed Q57 under the same `MP-384` / `MP-385` remote-control
  monitoring slice. The repo now has one canonical `devctl monitor`
  single-pass surface over typed startup/control-plane authority, plus the
  detached `review-channel --action ensure --follow` publisher writes the
  same `monitor_snapshot.{json,md}` bundle into the governed review-status
  root on each cadence. Remote phone mode no longer needs manual dashboard +
  startup-context stitching just to answer current state, next command,
  source authority classes, or whether observer self-audit should fire.
- 2026-04-10: Started the Q40/Q42 remote-control safety slice from the live
  audit. Startup-context should now distinguish observe-only recovery from
  relaunch/terminate authority before any destructive runtime action, and
  dashboard/observer lanes should route implementation defects through
  findings or packets when a live implementer owns the lane. Q51's quick
  follow-up is scoped to a narrow mobile terminal renderer for
  `remote_control` dashboard mode; stale blocker provenance remains a
  separate read-model freshness follow-up unless the same typed path already
  exposes it.
- 2026-04-10: Closed the local-review takeover drift that kept reanimating a
  dead dual-agent loop. A deliberate
  `review-channel --action reviewer-heartbeat --reviewer-mode single_agent`
  now retires detached publisher/reviewer-supervisor daemons before the
  reviewer status snapshot is rebuilt, so stale lifecycle heartbeats cannot
  silently rewrite the bridge back to `active_dual_agent` after Codex has
  reclaimed local single-agent authority.
- 2026-04-09: Closed one bounded repo-owned recover-path launch gap that was
  still making the phone-steered loop look healthier than it was. The live
  `review-channel --action recover --recover-provider claude --terminal none`
  path prepared a fresh Claude script and metadata but never actually spawned
  the implementer because `_maybe_launch_recover_sessions()` only launched for
  `terminal-app`. Headless recover now routes through the same detached
  proof-of-life launcher discipline as other headless review-channel starts,
  preserves launch warnings in the recover report, and waits for the same ACK
  refresh contract instead of silently reporting a no-op recover as success.
- 2026-04-09: Closed one bounded external-session identity slice for the
  phone-steered Claude path without creating a second authority channel.
  `review-channel --action attach-remote-control` now writes one canonical
  `remote_control_attachment` sidecar under the review status root, refreshes
  typed `review_state.json` when the governed bridge/runtime paths are
  available, and projects the same typed record through
  `ReviewerRuntimeContract`, `ControlPlaneReadModel`, `SessionCachePacket`,
  and `StartupContext`. The repo-local `remote-bridge-loop.sh` wrapper now
  marks external Claude remote-control sessions as typed runtime state
  (`unknown` on launch when the URL is not known yet, `attached` when the
  caller supplies `--session-url` / `--session-id`, `detached` on exit), and
  the managed pre-push hook now prints typed next-step guidance from
  `startup-context --format summary` instead of only a static fallback.
- 2026-04-09: Absorbed the repo-specific graph-backed read-side tranche into
  this owner doc. The next concrete proofs are now explicit: schema diff
  across startup/session/dashboard/mobile, raw-bridge-reader regression
  closure, `SystemCatalog` union-diff, recurring-finding clustering, dead
  topology evidence, and one cross-surface snapshot-parity artifact for the
  live proof tick.
- 2026-04-09: Closed one bounded phone/remote-control bootstrap drift in the
  repo-local Claude wrapper/prompt path without inventing a second authority
  layer. `dev/scripts/remote-bridge-loop.sh` now surfaces the typed top-level
  `recommended_command` plus `doctor.decision_command` from
  `review-channel --action status` and prefers that repo-owned review-channel
  recovery command when `--bootstrap-review-channel` is requested, falling
  back to the full `launch` pair only when no typed recovery path exists. The
  paired `dev/scripts/remote_bridge_prompt.md` / `.claude/commands/
  bridge-loop.md` prompt now bootstraps through `session-resume --role
  implementer --format bootstrap`, prefers typed next-command / recovery
  fields over hand-built launch prose, and routes commit/push through
  governed `devctl commit` / `devctl push` instead of raw git. This keeps the
  external Claude remote-control session on the same typed runtime and
  governed mutation path as repo-owned local flows.
- 2026-04-09: Closed the promptless remote-control commit gap in the governed
  mutation lane. A live `reviewer_runtime.remote_control_attachment` now
  promotes fallback interaction-mode derivation to `remote_control` across
  `ControlPlaneReadModel`, `StartupContext`, and `session-resume`, and the
  governed `devctl commit` path now self-applies its typed approval packet in
  `remote_control` mode instead of parking on `operator_approval_pending`.
  This is the structural fix for phone-steered Claude sessions hanging on
  commit-class approval prompts while still staying inside the typed mutation
  pipeline.
- 2026-04-09: Closed one bounded MP-384/MP-387 command-boundary freeze
  follow-up for the reopened F1 parity rerun. `session-resume` cache misses
  now force one live `load_current_review_state(... prefer_cached_projection=
  False)` read instead of reusing a cached projection, and dashboard now
  resolves governance plus current review state once per snapshot before
  threading that same typed payload through both `load_sources()` and
  `ControlPlaneReadModel`. The focused dashboard/session-resume/startup/read-
  model parity bundle is green on consecutive runs. The remaining read-side
  follow-up is now explicit and smaller: keep mobile/helper/repo-pack
  fallbacks on the same frozen review-state tick and then rerun the live
  remote-control proof instead of reopening another reducer-only slice.
- 2026-04-09: Closed one bounded helper/read-model authority seam in the
  MP-384 read-side convergence lane. `mobile-status` now loads the caller's
  selected review bundle first and then builds `ControlPlaneReadModel` against
  that same `--review-status-dir` instead of silently falling back to the
  default repo-pack bundle. The shared loader path now accepts that override in
  `runtime/control_plane_sources.py`,
  `runtime/control_plane_read_model.py`, and
  `runtime/review_state_locator.py`, while the thin-client repo-pack helpers
  only reuse cached `full.json` / `review_state.json` when those files are at
  least as fresh as the current `bridge.md` plus `review_channel.md`.
  `repo_packs/voiceterm.py` now routes through the same shared
  `load_mobile_review_state()` path instead of bypassing it. Focused
  `mobile-status`, read-model, review-state-locator, surface-wiring, and
  repo-pack regressions are green. The remaining read-side closure still
  includes broader startup/session-resume/dashboard parity plus the producer
  cutover tracked in the owner chain below.
- 2026-04-09: Closed one bounded MP-384/MP-387 session-resume/read-model freeze
  follow-up without widening into a full dashboard rewrite. The shared
  `ControlPlaneReadModel` now honors a caller-threaded typed `ReviewState`
  payload for reviewer/attention resolution instead of only for coordination,
  `session-resume` cache misses resolve `load_current_review_state()` once and
  pass that same typed object through `_load_governed_sources()` /
  `build_from_sources()`, and `system-picture` now builds startup/runtime
  sections from one pre-resolved governance + review-state pair instead of
  refreshing live state a second time. Focused `session-resume`,
  `ControlPlaneReadModel`, `system-picture`, and the targeted F1
  coordination-parity regression are green. The next read-side consumer
  follow-up remains explicit too: keep `startup_context`, dashboard/mobile
  mixed-authority cleanup, and helper/repo-pack fallbacks on the same frozen
  review-state tick before claiming the remote-control bootstrap path is fully
  converged.
- 2026-04-08: Absorbed the typed-authority convergence phases 2 through 4 into
  this owner doc instead of carrying them as free-standing prose. The live
  scope is now explicit: queue/topology hygiene, read-side authority
  convergence including helper and repo-pack fallbacks, `safe_to_fanout`
  semantics, schema-first `SystemCatalog` migration, AI bootstrap/prompt
  teaching, and the layered proof set (live remote-control parity, read-only
  blocked-fanout review, and fresh-AI bootstrap). Mutation/publish closure
  stays in `remote_commit_pipeline.md`; producer/identity authority stays in
  `platform_authority_loop.md`.
- 2026-04-09 smarter-guard layering review:
  this lane is not blocked by package layout; it is blocked by mixed and
  duplicate readers. Resume from that diagnosis: blocking closure here is
  read-model-first consumers, legacy fallback removal, truthful
  `safe_to_fanout` semantics, schema-first `SystemCatalog` migration,
  AI-teaching parity, and graph-backed duplicate-authority probes that expose
  stale bridge paths or missing dispatch coverage before another live proof
  widens the lane.
- 2026-04-08: Closed one bounded MP-384/MP-385 packet/dashboard convergence
  slice on top of the governed commit path repair. The live queue contract now
  distinguishes actionable pending packets from stale history in one shared
  helper, and dashboard/review-state/action-request/current-session surfaces
  all read that same live queue instead of independently filtering
  `status=pending`. Dashboard also no longer mixes plan markdown and typed
  bridge/session truth for its primary operator sections: typed instruction,
  reviewer mode, and current slice now win when present, while compatibility
  markdown remains fallback-only when typed review-state is absent. Focused
  packet/runtime/dashboard tests and the broader remote-control parity bundle
  passed in this session. The remaining live blocker is still bridge cadence /
  stale poll freshness in the real repo state, not stale packet history or a
  dashboard-specific split authority bug.
- 2026-04-08: Accepted the remote-control/operator follow-up for the new
  coordination packet. The remaining failure is architectural projection
  drift: `session-resume` and markdown bootstrap already show coordination,
  but `ControlPlaneReadModel` still has no coordination field, the Step-0
  `startup-context --format summary` surface stays silent, and dashboard still
  mixes typed coordination truth with local topology heuristics. The next
  bounded MP-384/MP-387 slice is therefore explicit: read coordination from
  the shared control-plane model, make summary/machine-summary load-bearing on
  current-slice/topology/resync truth, demote dashboard heuristics to
  telemetry, and check whether launch retargeting into this slice can become a
  repo-owned automation path instead of a manual operator rewrite.
- 2026-04-08: Closed one bounded MP-381/MP-384/MP-387 review-runtime
  observability slice. Bridge-backed `status` no longer pins reviewer-owned
  `current_session` to stale persisted state when the live bridge checkpoint
  changed, event-backed `current_session` now preserves Claude session-state
  hints, expiry-aware pending/stale packet counting now flows through the
  bridge-backed status/rewrite guard path, and dashboard/control-plane
  conductor liveness now reuses the shared repo-owned `session_probe`
  authority instead of metadata-only `session_pid` reads. Session-resume
  bootstrap now converges on the same reviewer instruction/finding truth after
  status refresh, and the dashboard packet surface is relabeled as generic
  pending packets instead of action-only packets. Focused regressions cover the
  bridge-authority cutover, session hints, stale packet filtering/counting, and
  shared session-probe liveness fallback. Live launch proof remains the next
  step once the tooling bundle is green.
- 2026-04-07: Landed MP-381 Priority 3 (Hard parity guard) — `check_control_plane_parity` now part of `check_platform_contract_closure`. One deterministic `ControlPlaneReadModel` fixture is rendered through all 5 governance surfaces (dashboard, auto-mode, session-resume, phone, mobile) and the guard fails CI if any surface disagrees on resolved_phase, top_blocker, next_action, next_command, push_eligible, review_accepted, last_guard_ok, or pending_action_requests. Also refactored `phone_status._build_control_plane_section` to match `mobile_status._control_plane_section`'s pure-function shape — both now take a `ControlPlaneReadModel` directly, enabling fixture-driven testing without disk I/O. This closes the "silent surface disagreement" gap flagged by Finding F11 (Dashboard falls back to independent computation) for the parity axis; follow-up work is required to also harden Finding F11 at the dashboard layer itself. Follow-ups A/B (Priorities 2 and 4) and other MP-381 subpriorities remain open.
- 2026-04-07: Closed the `MP-383` action-request projection/binding repair
  after the single-agent recovery turn exposed the root cause: packet state,
  bridge compatibility text, and session-resume/bootstrap cache could drift
  because the bridge renderer trusted an incomplete compatibility projection
  and generic `action_request` packets could encode commit/check/push-class
  work as prose-only bodies. The repair keeps `## Action Requests` as a
  projection-only view over event packets, reconstructs missing fixed bridge
  sections from typed review-state fallbacks, compacts packet bodies before
  rendering, and only projects executable runtime action requests that carry
  target binding. New `commit` / `push` action-request posts must now carry a
  runtime target plus remote-commit pipeline generation, staged snapshot hash,
  and guard summary; `run_check` / `kill_process` requests require a runtime
  target ref and revision. This prevents another packet -> bridge -> runtime
  split-brain where the packet inbox sees a request but the live bridge cannot
  render it safely or tells an implementer to execute an unbound action.
- 2026-04-07: Integrated the operator concern about commit/push latency as a
  plan-owned architecture finding instead of a request to weaken safeguards.
  Accepted conclusion: the system should keep strict proof, but stop leaving
  fast/checkpoint/push/release tier selection to actor judgment. The code
  seam is real: the remote VCS stage intent carries `guard_profile` but no
  validation plan id/tree-bound receipt, stage execution scopes paths and
  records a staged tree hash but does not verify a validation receipt, and
  the control-plane quality reducer still treats a missing push report as
  guard-green. This remains queued under `MP-381` / `MP-384` plus the
  `dev/active/remote_commit_pipeline.md` commit-gate lane; Claude should not
  widen the current push/checkpoint work into a discretionary "run fewer
  checks" change.
- 2026-04-07: Closed the bounded `MP-382` / `MP-387` launch-authority
  follow-up from the active reviewer verdict. The live bridge-handler path no
  longer reads missing `bridge_liveness.interaction_mode`; it resolves the
  governed operator interaction mode once and passes that value to both
  `build_launch_sessions()` and `launch_sessions_if_requested()`. The
  unowned `--allow-headless-override` CLI/test surface was removed. Prepared
  conductor metadata and generated launch scripts now carry prepared HEAD,
  current instruction revision, and a typed turn/session token; the script
  re-reads `review_state.json` before provider start and treats stale
  authority as a non-restartable headless exit instead of looping forever.
- 2026-04-07: Closed the follow-up reviewer-supervisor restart-policy gap
  exposed during push preparation. The live respawn symptom was the
  repo-owned `reviewer-heartbeat --follow --auto-promote` supervisor, not a
  provider conductor script; `manual_stop` was non-restartable in the launchd
  publisher wrapper but the repo-owned ensure/reviewer-heartbeat auto-start
  path could still recreate the supervisor. The reviewer-supervisor restart
  policy now treats `manual_stop` / `completed` as non-restartable for both
  `ensure` auto-heal and reviewer-heartbeat auto-start, while the launchd
  publisher wrapper also maps the stale launch-authority exit code `82` to a
  successful no-restart service exit.
- 2026-04-06: Integrated the operator-supplied static GitHub branch review
  against the live local reviewer/runtime state. The review is directionally
  correct and aligns with this plan's existing architecture diagnosis: the
  platform is stronger at typed modeling than at enforced lowering/execution.
  Triaged outcome:
  `MP-382` current-slice fit: the stale/inactive recovery guidance gap was
  real in local reviewer runtime, so the bounded fix landed locally in the
  review-channel attention/recover path (missing live Claude conductor now
  escalates to `implementer_relaunch_required`, and repo-owned recover now
  dry-runs successfully from the fresh reviewer checkpoint state).
  Plan-only, do-not-widen items: `ControlPlaneReadModel` fail-open quality /
  daemon truth tightening stays queued under `MP-381` / `MP-384`; one typed
  operator-directive ingress and packet-backed operator actions stay queued
  under `MP-380` / `MP-383` / `MP-385`; broader auto-mode decisiveness and
  dashboard-as-single-surface remain `MP-384` / `MP-385`; discoverability and
  bootstrap closure remain `MP-386` / `MP-387`; governed VCS self-hosting
  repair parity stays queued with the existing executor/pipeline work and must
  not be folded into the live launch-authority slice. Result: keep Claude on
  the existing `MP-382` + `MP-387` launch-authority/runtime closure turn and
  treat the broader branch-review findings as confirmed backlog within this
  plan, not as ad hoc new scope.
- 2026-04-05: Closed the dirty-tree reviewer/implementer handoff seam inside
  `MP-387` without adding a second authority store. Bridge-backed status now
  emits one typed `ReviewCandidateRecord` into `review_state.json` /
  `compact.json`, `session-resume` / reviewer prompt rendering prefer that
  candidate over raw `last_reviewed_sha..head_sha` inference, and the status
  pipeline fails closed when Claude claims a completed slice but the candidate
  is missing, invalid, or stale. The candidate is frozen against
  instruction-revision + implementer-state hash + changed-path/worktree target
  and invalidates on worktree drift without a new implementer completion.
  Focused regressions now cover dirty-tree candidate emission, scope-mismatch
  rejection, drift invalidation, review-state parsing, and reviewer bootstrap
  rendering.
- 2026-04-05: Accepted the post-visibility architecture nuance for `MP-382`.
  Terminal-mode selection is no longer the honest blocker here: typed operator
  mode, typed visibility, and headless proof-of-life now exist. The remaining
  lifecycle gap is stale-session cleanup and refusal: session-end cleanup,
  startup preflight cleanup, orphan Terminal/daemon detection, and operator-
  visible orphan state in dashboard/doctor/status. Keep that work in this
  owner lane instead of reopening visible-vs-headless wording as if it were
  the unsolved problem.
- 2026-04-05: Landed the provider-neutral role-bootstrap follow-up inside the
  live `MP-382` / `MP-387` lane. `LaneAssignment` now carries an explicit
  tandem role inferred from the planned review-channel lane text, conductor
  launch specs/prompts consume that role instead of assuming
  `codex -> reviewer` / `claude -> implementer`, and the typed conductor
  capability/bootstrap path now accepts explicit role overrides so either
  provider can own reviewer or implementer startup while still using the same
  repo-owned `startup-context --role <role>` and
  `session-resume --role <role> --format bootstrap` receipts. The bridge stays
  compatibility-shaped for now (`Last Codex poll`, `Claude Status` /
  `Claude Ack` headings remain), but start rules/prompts now explain those as
  role-owned compatibility fields when provider assignments are swapped.
  Narrow recover/reviewer-follow paths were widened the same way:
  `review-channel --action recover --recover-provider <provider>` now accepts
  the current implementer provider, while the live reviewer-session guard is
  derived from planned role ownership instead of hardcoded Codex/Claude
  assumptions. Focused permutation coverage now exercises
  `Codex reviewer / Claude implementer` and
  `Claude reviewer / Codex implementer` through launch-topology, prompt,
  bridge-projection, recover, and runtime-capability tests.
- 2026-04-05: Landed MP-380 + MP-382 first bounded slice (Claude).
  MP-380: Added `OperatorInteractionMode.UNRESOLVED` to `operator_context.py`
  with `resolve_operator_interaction_mode()`, `is_remote_mode()`,
  `is_resolved()` helpers. Fixed fail-open defaults in 5 files:
  `project_governance_parse.py` (parse layer), `startup_context.py`
  (ReviewerGateState default + `_interaction_mode_from_reviewer_mode`),
  `control_plane_read_model.py` (op_mode chain + `_default_read_model`),
  `session_resume_support.py` (SessionCachePacket + `derive_interaction_mode` +
  `packet_from_mapping`), `_publisher.py` (cadence defaults). Empty/missing
  mode now resolves to `"unresolved"` instead of silently degrading to
  `"local_terminal"`.
  MP-382: Replaced bare boolean return in `_launch_sessions_headless` with
  typed `HeadlessLaunchStatus` StrEnum (`alive`, `dead_on_arrival`,
  `spawn_failed`, `script_missing`) and `HeadlessLaunchResult` frozen
  dataclass. After spawn, PID is polled 3× at 0.3s intervals for proof-of-
  life. Dead-on-arrival processes are surfaced as typed warnings, not silently
  treated as healthy. Applied Kobzol contract-shape rules to touched files:
  StrEnum for finite variants, dataclass for structured results, type hints
  on all edited functions.
  35 focused tests in `test_operator_mode_fail_closed.py` + 714 existing pass.
- 2026-04-05: Absorbed the Kobzol six-pattern Python audit into this plan as a
  slice contract, not as permission for a repo-wide cleanup sweep. For the
  live `MP-380` / `MP-382` tranche, touched remote-control/runtime files must
  add explicit type hints on edited functions, keep existing dataclass owners
  at function boundaries, replace new stringly finite variants with
  `Literal` / `StrEnum` / closed unions where practical, use narrow
  `NewType` wrappers only when they remove a real identifier-swap hazard,
  prefer owner-side construction helpers for multi-path runtime records, and
  model launch/proof-of-life with typed lifecycle state instead of loose
  boolean bundles. Later `MP-381` / `MP-383` / `MP-384` / `MP-387` work
  should keep the same contract-shape rules as it converges action requests,
  check outputs, dashboard projections, and reviewer bootstrap state.
- 2026-04-05: Operator-directed the next live worker slice away from the
  isolated reviewer-follow relaunch symptom and back onto the typed
  remote-control architecture closure. The approved architecture rule stays
  singular: `ProjectGovernance.BridgeConfig.operator_interaction_mode`,
  `ReviewerGateState`, `ControlPlaneReadModel`, and `SessionCachePacket` own
  operator mode and launch posture; `PacketPostRequest(kind="action_request")`
  remains the only operator-approval transport; `CheckResult` /
  `ViolationRecord` remain the shared check-output contract; and `bridge.md`
  stays compatibility projection only. For the live Claude worker, the first
  bounded implementation slice is `MP-380` + `MP-382`: remove fail-open
  `local_terminal` defaults, surface unresolved operator mode as typed
  fail-closed state, and make terminal-none launch/recovery consume that typed
  mode plus reviewer proof-of-life instead of treating manual-input prompts or
  detached daemon heartbeats as healthy runtime. Defer dashboard /
  `ViolationRecord` expansion and packet-queue cleanup until this slice is
  green.
- 2026-04-05: Reviewed Claude follow-up commits `fde0899` and `5eb8bbc`.
  Accepted the technical commit-gate closure in `fde0899`: `devctl commit`
  now uses the explicit `--` passthrough contract via
  `argparse.REMAINDER`, the hook guidance path no longer dies under
  `set -e`, and focused verification passed
  (`python3 -m pytest dev/scripts/devctl/tests/vcs/test_commit_gate.py dev/scripts/devctl/tests/runtime/test_reviewer_observation.py dev/scripts/devctl/tests/governance/test_session_resume.py` -> `104 passed`).
  One process finding remains on the follow-up bridge handoff: Claude did
  not write the required commit-gate closure into this plan before
  self-promoting in `bridge.md`, and the bridge text declared "ready for
  promotion to next slice" / implied work should continue while reviewer
  promotion was still pending. Bound the next slice to lane hygiene only:
  no new parity/CI work until the missing plan-state closure and explicit
  await-review behavior are restored. The separate "still stopping"
  symptom is runtime state, not a new coding slice: `review-channel status`
  still reports `review_loop_relaunch_required` / `launch_truth=detached_runtime_only`,
  so agents must report that blocker instead of routing around it.
- 2026-04-05: Reviewed Claude's mixed dirty tree after `e391e88`. The
  bounded `ReviewerObservation` observed-head follow-up is now closed:
  `status_projection.py` threads `snapshot` into the typed bridge reducer,
  `status_projection_bridge_state.py` / `review_bridge_field_authority.py`
  now carry `head_at_push_time`, and `ReviewBridgeState` persists that field.
  Live projections now agree on the observed head: `compact.json`,
  `review_state.json`, and `session-resume` all surface
  `head_at_push_time` / `observed_head_sha=e391e880e76fbb45e343ede4b7e75c57c1bd8b5a`.
  Focused verification passed:
  `python3 -m pytest dev/scripts/devctl/tests/vcs/test_commit_gate.py dev/scripts/devctl/tests/runtime/test_reviewer_observation.py dev/scripts/devctl/tests/governance/test_session_resume.py`
  (`101 passed`). The same dirty tree widened out of scope into a new
  commit-gate slice before checkpoint. New review findings: the real
  `devctl commit` CLI still rejects option-style passthrough flags because
  `sync_parser.py` models passthrough as a positional list, and the new
  pre-commit hook's friendly failure guidance is dead code under `set -e`.
  Bound the next slice to commit-gate closure plus checkpoint; do not widen
  further until the guarded commit path is honest.
- 2026-04-05: Reviewed follow-up commit `e391e88`. The stale/not-seen parity
  miss is closed: `session-resume` now reads typed
  `reviewer_runtime.reviewer_freshness` first, so stale reviewer state no
  longer degrades to `pending_review` in the session cache. One bounded
  contract miss remains: live `compact.json` / `review_state.json`
  `reviewer_observation.observed_head_sha` is still blank because the reduced
  bridge/state projection still never carries `head_at_push_time`. Keep the
  next slice focused on threading that typed field through the bridge/review-
  state model path and adding one projection/session-resume parity regression.
- 2026-04-05: Fixed ReviewerObservation honesty (Codex review of `a29477d`).
  `poll_due`/`overdue` now fail closed to `not_seen`/`stale=true`.
  Projection uses typed `reviewer_runtime.reviewer_freshness` instead of
  inferring "fresh" from timestamp. `review_state.json` now includes
  `reviewer_observation`. 11 tests (2 new regressions for overdue + accepted).
- 2026-04-05: Reviewed `a29477d` (`ReviewerObservation`). One bounded
  follow-up remains before the contract is honest across live surfaces. The
  core reducer in `runtime/reviewer_observation.py` still treats
  `reviewer_freshness=poll_due|overdue` as non-stale, so
  `SessionCachePacket.reviewer_observation_status` can still report
  `pending_review` for an overdue reviewer. The compatibility projection in
  `review_channel/projection_observation.py` also drops typed freshness and
  forces `"fresh"` whenever `last_codex_poll_utc` exists, so compact/read-model
  consumers disagree about whether Codex has actually seen the current HEAD.
  Validation of the refreshed artifacts also showed the status pipeline still
  strips `head_at_push_time`, leaving `compact.json.reviewer_observation`
  without `observed_head_sha`, and `review_state.json` still does not expose a
  top-level `reviewer_observation` block. Bound the next slice to staleness
  normalization plus honest `review_state.json` / `compact.json` projection
  coverage; the commit/checkpoint decision is already typed elsewhere via
  `push_decision.action=await_checkpoint` and reviewer bootstrap
  `resolved_phase=committing`.
- 2026-04-05: Landed typed `ReviewerObservation` contract (MP-385/MP-387).
  Frozen dataclass with status enum: `not_seen` / `pending_review` /
  `under_review` / `accepted`. Derived from `reviewer_freshness`,
  `review_needed`, `reviewed_hash_current`, `last_reviewed_sha` — no bridge
  parsing. Wired through: `ControlPlaneReadModel.reviewer_observation`,
  `compact.json` via `build_observation_projection()`,
  `SessionCachePacket.reviewer_observation_status`. Contract closure
  updated: both new fields registered, 0 violations. 9 new tests,
  73 session-resume tests pass, 35 read-model tests pass.
- 2026-04-05: Accepted follow-up commit `5861900` for the reviewer-bootstrap
  mixed-state routing bug. Live typed status still does not expose one
  reviewer-observation receipt that answers "has Codex already seen the
  current HEAD, and is that head still pending review or already accepted?"
  Existing contracts expose poll freshness (`last_codex_poll_*`), drift
  (`review_needed`, `reviewed_hash_current`), and acceptance baseline
  (`last_reviewed_sha`, `head_at_push_time`), but not one bounded
  observation block for `observed_head -> observation time -> review state`.
  Bound the next slice to `MP-385` / `MP-387`: add one typed
  reviewer-observation contract projected through review-state/status,
  operator-facing surfaces, and `session-resume` instead of extending bridge
  prose.
- 2026-04-05: Reviewed the pushed branch through `b819efa` and converted the
  architecture review into tracked closure work. The live runtime still
  reports `launch_truth=detached_runtime_only`,
  `reviewer_heartbeat_stale`, and `operator_interaction_mode=local_terminal`
  while the control-plane lane already has typed runtime contracts in flight.
  Accepted blockers now tracked here: operator mode still fails open to
  `local_terminal`, headless launch still treats detached daemon heartbeats as
  success, platform contract closure still does not catalog
  `ControlPlaneReadModel` / `AutoModeState` / `SessionCachePacket`, stale
  review verdict text still projects as current truth after head drift, and
  pending packet counts are still mislabeled as actionable requests. The
  structural raw-commit gap stays tracked in `dev/active/remote_commit_pipeline.md`.
- 2026-04-04: Reviewed the 8 commits ahead of
  `origin/feature/governance-quality-sweep`
  (`5bed0fa`, `437008d`, `a534e3e`, `25f458c`, `aa26749`, `8c3f032`,
  `76f5401`, `4094c39`). Accepted the portability/push-truth slices and logged
  four blocking architecture gaps: remote-control state is not typed through
  startup/runtime owners, bridge `Action Requests` creates a second action
  transport, headless lifecycle still stops on non-zero exit and recommends
  `terminal-app`, and dashboard/check-detail surfaces still parse compatibility
  text instead of typed records.
- 2026-04-04: Bound those gaps to `MP-380..MP-386` so the closure path stays
  under the existing `MP-377` owner chain instead of becoming bridge-local
  review lore.
- 2026-04-04: Claude 8-agent audit (AUD-1..AUD-14) mapped to tracked slices:
  - Slice A (MP-380/382): AUD-3 (no typed remote_control/device/available), AUD-6 (zero device awareness), AUD-8 (3 disconnected permission layers), AUD-9 (operator mode-switching)
  - Slice B (MP-383): AUD-4 (post_packet() doesn't exist), AUD-8 (permission routing dispatcher)
  - Slice C (MP-381): AUD-2 (errors to stderr only), AUD-7 (guards format differently, no universal schema)
  - Slice D (MP-384): AUD-1 (session_state_hints never called), AUD-2 (no errors in dashboard), AUD-5 (5/6 quality gates always n/a, pending_packets hardcoded 0)
  - Slice E (MP-385): dependent on A-D
  - Slice F (MP-386): AUD-12a/b/c discoverability closure
  - AUD-10: full explainability — surface reasoning chains, not summaries
  - AUD-11: build lifecycle hooks, notification channels, permission relay, scheduled tasks as OUR typed contracts (agent-agnostic), not Claude-specific features. External tools are surface adapters, not authority.
  - AUD-12 (DISCOVERABILITY + SYSTEM MAP — 3-AGENT AUDIT COMPLETE):
    - context-graph ALREADY catalogs 69 guards, 25 probes, all commands, plans, guides. 4 modes (bootstrap/query/concept-view/diff). Mermaid + Graphviz output. 360+ saved snapshots. Token-efficient bootstrap (~2250 tokens).
    - SLIM MAP feasible: `startup-context` (82 tok) + `context-graph` top section (400 tok) + `dashboard` now block (150 tok) + `check-router` lane (500 tok) = ~1130 tokens. Gives 80% operational context. `quality-policy` (4663 tok) and `platform-contracts` (7336 tok) stay on-demand.
    - 67 commands, 20+ desktop console views, matplotlib/SVG/mermaid charts, MCP adapter, phone-status — all exist but NONE discoverable to new agents/operators.
    - 5 GAPS in context-graph: (1) named guard/probe roster in bootstrap (shows counts not names), (2) IMPACT TRAVERSAL — changed files → applicable guards (THE missing piece that caused Claude to skip CI), (3) surfaces as first-class graph nodes, (4) per-command argument schemas, (5) guard dependency edges.
  - AUD-12a (AGENT DISPATCH ORACLE): `resolve_agent_dispatch(changed_paths, scan_mode) -> AgentDispatchPacket` in `task_router_contract.py`. Composes existing `classify_lane` + `QualityStepSpec.languages` filter + `StartupContext` advisory. Returns named guards, preflight command, context level. This is THE fix for AI agents skipping guards.
  - AUD-12b (VIEW ADAPTER): `devctl view --surface phone --mode dashboard`. ONE snapshot -> `RENDERERS[(surface, mode)]` dispatch. `dashboard_render.py` already proves the pattern. Add `("phone", "summary")`, `("ai", "slim")`, `("cli", "flowchart")`. `surface_definitions.py` already names 4 surfaces.
  - AUD-12c (SYSTEM CATALOG): `devctl discover` command. Typed `SystemCatalog` (commands + guards + probes + surfaces + report_types). Builds from existing registries (`QualityStepSpec`, `COMMANDS`, `frontend_surfaces`). Formats: slim (~500 tok for AI), full (markdown), interactive (JSON for PyQt6). `--filter guards-for-file:X` returns deterministic guard list. Feeds context-graph as capability nodes.
  - Design rule: `SystemCatalog` owns WHAT EXISTS (static). `context-graph` owns RELATIONSHIPS (dynamic). `AgentDispatchPacket` owns WHAT TO RUN (derived). `view` owns HOW TO SHOW IT (rendering). Same data, different views.
  - AUD-14 (REMOTE SESSION AUTO-ROLLOVER): When a Claude remote-control session degrades (low context window, high token usage, compaction happening), the system should automatically: (1) save all state to bridge.md + plan doc, (2) start a fresh Claude session that picks up where it left off, (3) stop the degraded session. The new session reads bridge + plan doc and continues work. The old session stops cleanly — not left hanging. Same for Codex sessions. This is the existing `HandoffBundle` → `rollover ACK` contract but wired for Claude-to-Claude handoff, not just Codex-to-Codex. The operator should NOT have to manually kill old sessions or start new ones — the system handles it. Dashboard should show: "Session 1 degraded → Session 2 started → Session 1 stopped." Codex: integrate into Slice A (headless lifecycle) and Slice E (auto-poll cadence).
  - AUD-13 (SESSION CLEANUP / TERMINAL LIFECYCLE): Stale Terminal.app windows and daemon processes accumulate across sessions. When a Codex conductor exits, the Terminal window stays open. When a daemon is launched, it persists after the session ends. In remote-control mode, nobody is at the keyboard to close them. The architecture needs: (1) a `devctl session-cleanup` command that kills stale conductor/daemon processes and closes orphaned Terminal windows, (2) automatic cleanup on session end (conductor exit hook), (3) cleanup on session START (before launching new conductors, verify no orphans from previous sessions), (4) dashboard should show active sessions/windows/daemons and flag orphans, (5) `review-channel --action launch` should refuse if orphan sessions exist and offer `--force` to clean first. This is part of the headless lifecycle (Slice A/MP-382) and remote-control mode (Slice A/MP-380). Codex: integrate into the plan.
- 2026-04-04: Promoted discoverability into tracked `MP-386` scope. Contract
  alignment is explicit: `SystemCatalog` is static capability inventory,
  `AgentDispatchPacket` is derived routing, `view` is presentation-only, and
  `context-graph` remains the relationship authority.

## ChatGPT Architecture Review Audit (2026-04-04, 8-agent validation)

External review identified core problem: "too many partially smart surfaces, not enough single-owner resolved state." 8 Claude agents validated against codebase:

### P0 — Must Fix
- **ONE resolved control state**: 4 independent reducers (push_decision, advisory_decision, status_push_decision, dashboard_summary) compute state with different vocabularies. Need ONE enum: `awaiting_checkpoint | awaiting_review | push_ready | push_blocked | guards_failed`. All surfaces render only that.
- **Session lease model**: No lease concept anywhere. Need: ConductorSessionLease (expiry, renewal, invalidation), WorkerLease, LastAckRevision, ExpectedStateHash, StaleTimeoutClass, RecoverabilityClass. Recovery becomes deterministic: stale+no conductor+reviewer owns turn → awaiting_implementer_recovery → actions narrow.

### P1 — Important
- **Read/write separation**: `build_snapshot` reads files AND computes decisions. Need ONE `ControlPlaneReadModel` built once, consumed by all. `TypedAction→ActionResult` stays separate.
- **Bridge is still control authority**: 4 paths read bridge.md as authority (liveness gate, turn authority, action dispatch, push gate). Need typed `ReviewerHeartbeat`, `TurnAuthority`, `PacketPostRequest`-backed actions to retire bridge.
- **Typed reasoning**: `RuleMatchEvidenceRecord` exists but missing `evidence_refs`, `blocked_by`, `next_allowed_actions`, `next_recommended_action`. Can't assemble "Push blocked because X" from typed fields.
- **Cross-surface invariants**: Only 14 tests, partial coverage. Need 3 proof tests: all-surfaces-agree-on-push-ready, publisher-false-blocks-push, no-conductor-blocks-active.

### P1+ — Architecture
- **Parallel worktrees**: `LaneAssignment.worktree` parsed but never consumed by launcher. 3 gaps: add worktree_path to LaunchSessionRequest, wire git worktree in build_session_script, pass per-worktree path to conductor prompt.
- **Portability**: `repo_packs/voiceterm.py` correctly isolated but `active_path_config()` defaults to VoiceTerm. No pip package. No second repo-pack registered.

## Architecture Authority Audit (8-lane, Codex-directed, 2026-04-05)

| Lane | Verdict | Finding |
|---|---|---|
| L1 Raw bridge | 2 GAPS | `_parse_bridge_mode` (governance scan) has no typed alt. Launch reads raw bridge. |
| L2 Reducers | DISAGREE | 3 reducers. Fallback recomputes from raw bridge when `typed_authority_complete` false. |
| L3 Session parity | DIVERGES | `stale_label` "stale" vs "unknown" between bridge/event paths → `implementation_blocked` diverges. |
| L4 Writers | CONFLICT | 4 writers share Poll Status with no concurrency guard. `refresh_bridge_heartbeat` skips `Reviewer mode`. |
| L5 Paths | 3 PATTERNS | `REPO_ROOT` bypasses repo-pack+governance. `active_path_config` ignores governance. Only `review_state_locator` is fully correct. |
| L6 Consumers | 5 INDEPENDENT | Console, dashboard, phone, mobile, control-state all compute state independently. |
| L7 Packets | CLEAN | Action requests properly projection-only (MP-383 accepted). |
| L8 Plan coverage | 0/8 DONE | All MPs open. 5 subsystems (release, mutation, triage, autonomy, doc-authority) have NO owner. |

Highest-value next slice: ONE resolved `ControlPlaneReadModel` builder that replaces the 5 independent state computations (L6) and the 3 disagreeing reducers (L2) with a single source. L7 is the reference pattern. L3's stale_label divergence is the cheapest single fix.

## Outer Ring Audit (Round 7, 8-agent, 2026-04-04)

| Subsystem | Status | Detail |
|---|---|---|
| CI workflows | SILO | 30 workflows run devctl but write no typed artifacts. No dashboard CI feed. |
| Rust runtime | SEPARATE | JSON over sockets, Python never reads. Only static naming-parity guard. |
| INDEX registry | PARTIAL | 10+ consumers but dashboard completely disconnected. |
| ADR system | SILO | Typed internally, plain dict at boundary. Only in hygiene. |
| CHANGELOG | BOOLEAN | Single bool gate, no structured data. |
| Publication-sync | SILO | Standalone, untyped dict, no dashboard. |
| Compat-matrix | SILO | Standalone CLI, plain dict. |
| Guard-run/swarm | SILO | Typed structs internally but standalone output. No dashboard. |
| Process-audit/sweep | SILO | Plain dicts, no dashboard connection. |

Round 7 found 0 new well-integrated subsystems in the outer ring.

## Subsystem Integration Audit (Round 6, 8-agent, 2026-04-04)

| Subsystem | Status | Detail |
|---|---|---|
| Release pipeline | SILO | Zero ControlState/ReviewState awareness. No dashboard visibility. All from git/config. |
| Mutation testing | SILO | No typed artifacts. Dashboard shows badge staleness only, not coverage. |
| Triage | SILO | No governance-review connection. Dashboard has launch button only. |
| Sync | OK | Operational utility, correctly consumes push policy. |
| Render-surfaces | PARTIAL | Reads policy file independently. Consumed by one check guard. |
| Quality-policy vs runtime | BROKEN | startup_context has ZERO imports from quality_policy/defaults.py. They can disagree on enabled checks with no enforcement. |
| Watchdog/data-science | PARTIAL | Dashboard reads avg_time_to_green + event_stats. Benchmark, swarm, external findings all ignored. |

## Operator Visibility Gaps (from live testing 2026-04-04)

- AUD-16 (CODEX OUTPUT — FULL VISIBILITY LIKE CLAUDE): Codex CLI truncates tool output to `… +N lines`. Claude has ctrl+o to expand everything. Operator loses ~80% of Codex output. THREE approaches, all additive:
  - (a) TYPED ARTIFACTS: Codex writes full results to typed artifacts (review_state, check reports, verdict files). Dashboard reads artifacts and renders with expand/collapse. Operator reads dashboard, not terminal.
  - (b) CONDUCTOR LOG RENDERER: `launch_script.py` already pipes Codex through `script` to a log file. Add a real-time TUI/overlay renderer that reads the conductor log and shows summary + expandable detail — same UX as Claude's ctrl+o but through our system. The VoiceTerm overlay TUI surface already exists in `surface_definitions.py`.
  - (c) OPERATOR CONSOLE PANEL: PyQt6 desktop app gets a "Codex Live" panel that reads conductor log in real-time. Full output, searchable, filterable.
  - Design rule: the operator should NEVER have to read raw Codex terminal with truncated output. Whether they use dashboard, TUI overlay, or operator console — they see everything Claude shows, through our rendering system. Push to Codex to design which approach lands first.
- AUD-17 (USER TIMEZONE): All timestamps should render in the operator's timezone, not UTC. `OperatorContext` needs a `timezone` field (e.g. `America/New_York`). Every surface reads it.
- AUD-18 (CONTINUOUS UPDATE LOOP): Claude must update the operator at a user-set interval without stopping. No gaps. The operator should never have to say "what's going on" or "keep updating me." This is part of the auto-mode state machine (Q1 in bridge).
- AUD-20 (SESSION CACHE — 98% BOOTSTRAP WASTE): Current bootstrap loads ~60K tokens (AGENTS.md 42K + CLAUDE.md 4.4K + bridge.md 4.9K + plan doc 6.4K + context-graph 2.2K). Actual decision-relevant payload is ~1K tokens. Design: `devctl session-resume --role <role> --format json` emits a `SessionCachePacket` (~500 tokens) from existing typed artifacts (receipt.json + compact.json + review_state.json + context-graph snapshots). AGENTS.md rules reduce to 5 booleans already in typed state. Role-specific profiles (reviewer vs implementer). Cache-hit on same HEAD (~1ms). Saves 42K+ tokens per session. Codex: implement as MP-387 and make it the FIRST thing any session runs instead of the current bootstrap chain.
- AUD-27 (GIT COMMIT MUST BE GATED BY GUARDS — SYSTEMIC FAILURE): Claude committed ~65 times tonight without running the full guard suite. This happened because `git commit` is ungated — nothing blocks it without guards passing. The governed push (`devctl push --execute`) runs guards, but Claude bypassed it by using raw `git commit`. This should be STRUCTURALLY IMPOSSIBLE. Fix options: (1) git pre-commit hook that runs `devctl check --profile quick` and blocks on failure, (2) `devctl commit` command that wraps `git commit` with mandatory guard checks, (3) Claude Code hook (PostToolUse on Bash) that detects `git commit` and auto-runs guards before allowing it, (4) the auto-mode state machine should gate commit on `last_guard_ok=true`. The root cause: the architecture trusts agents to voluntarily run guards instead of ENFORCING it. No agent — Claude, Codex, human — should be able to commit ungarded code. Codex: implement the pre-commit hook or `devctl commit` wrapper as the FIRST thing in the next session.
- AUD-25 (PERMANENT ANTI-DISCONNECTION — AUTO-PROPAGATION ARCHITECTURE): Root cause of everything being disconnected: adding a typed field doesn't auto-propagate. Fix: (1) ONE registry of every contract field that auto-generates surface bindings, guard coverage, test scaffolding, dashboard rendering. Add `last_reviewed_sha` → registry generates dashboard column, phone field, session-resume field, CI parity test, guard check. (2) `devctl contract-check` guard blocks merge if ANY field missing from ANY surface. (3) Every guard, probe, packet, dashboard section, phone field registered in SystemCatalog so nothing exists outside. (4) `devctl scaffold --field X --contract Y` generates bindings + tests automatically. Codex: design as the permanent solution — make disconnection structurally impossible.
- AUD-26 (CI/CD MUST TEST PROBES, GUARDS, PACKETS, EVERYTHING): The 64 guards, 13 probes, all packet kinds, all dashboard sections, all typed contracts — CI must prove they're ALL connected and accurate. Not just run them — prove the OUTPUT is correct and consumed by downstream surfaces. When a guard adds a finding, prove the finding reaches the dashboard. When a probe fires, prove it reaches governance-review. When a packet posts, prove it reaches the action request projection. Every piece end-to-end, not just individual pass/fail. Codex: design as extension of `check_platform_contract_closure.py` + new `check_end_to_end_connectivity.py`.
- AUD-24 (CI GUARDS FOR TYPED STATE CONTRACTS): When we add a field to ControlPlaneReadModel, a guard should auto-verify it's wired through all 5 surfaces. When we add an auto-mode phase, a guard should prove all reducers agree. The platform-contract-closure guard already does this for dataclass fields vs contract rows — extend it to: (1) cross-surface parity proofs (all surfaces produce same value for same input), (2) typed field coverage (every ControlPlaneReadModel field consumed by at least one surface), (3) reducer agreement (attention, recovery, turn-authority produce same status for same bridge state), (4) session-resume cache freshness (cache fields match source artifact fields). These should be GUARDS (Layer 1, block merge) not probes. Codex: design as an extension of existing `check_platform_contract_closure.py` or a new `check_control_plane_parity.py`.
- AUD-23 (CI/CD MUST TEST THE GOVERNANCE PLATFORM, NOT JUST VOICETERM): The 30 CI workflows were built for the old Rust voiceterm binary. They don't test: ControlPlaneReadModel, session-resume, auto-mode, typed state contracts, ViolationRecord rendering, action request packet flow, operator mode resolution, bridge projection parity, session lifecycle. Lots of CI runs are failing on things unrelated to what we're building. The CI should: (1) run the full governance/runtime test suite (500+ tests we added tonight), (2) run cross-surface parity proofs, (3) test the session cache and auto-mode state machine, (4) prove ControlPlaneReadModel agrees across all 5 surfaces, (5) test remote-control mode end-to-end. Codex: update the CI workflow configs to match the actual codebase, not the old product.
- AUD-22 (CODEX REVIEWS STALE COMMIT — MISSES NEWER HEAD): Codex repeatedly reviews an older commit while newer fixes are already pushed. It polls for HEAD changes but misses commits that land between its poll cycles. This wastes entire review sessions. Root cause: Codex's poll loop (`while HEAD == old; sleep 5`) only catches the FIRST new commit. If Claude pushes multiple commits (e.g. implementation + fix), Codex reviews the first and misses the second. Fix: the session cache / session-resume should carry `last_reviewed_sha` so the next session knows exactly where to start. The bridge should carry `head_at_push_time` so Codex always reviews the LATEST, not whatever it polled first. This must be part of the auto-mode state machine — each review cycle starts from the current HEAD, not from a cached poll.
- AUD-21 (CODEX FAILS TO WRITE BRIDGE VERDICT): Codex completes review, says "accepted" in terminal output, then PARKS at prompt without writing the verdict to bridge.md. This happens EVERY session — Codex reviews, verifies, runs tests, but the final bridge edit either doesn't happen or gets stuck. Root cause unknown — could be: (a) bridge guard blocks the write and Codex silently fails, (b) Codex runs out of "action budget" after reading too many files, (c) the bridge edit tool needs explicit file permissions, (d) Codex's internal state machine doesn't prioritize the write. This is THE #1 blocker to the auto-mode loop. Without bridge writes, Claude never sees the verdict, the loop stalls, and the operator has to manually relay. Codex: AUDIT why this happens by examining your own tool call history and bridge guard output. Fix it.
- AUD-19 (CODEX CONTEXT EFFICIENCY): Codex burns 70%+ of context on file exploration before acting. One planning session read 40+ files, ran 50+ searches, used 148K/258K tokens, and produced ZERO instructions. The system needs: (1) a slim reviewer bootstrap that gives Codex ONLY what it needs (plan doc + changed files, not the entire codebase), (2) context budget guidance in the prompt ("use <30% of context for reading, spend the rest on output"), (3) if Codex uses >50% context without posting to bridge, auto-save and rollover. This is part of the auto-mode state machine and session lease model.

## Infrastructure Seam Audit (Round 5, 8-agent, 2026-04-04)

| Seam | Status | Detail |
|---|---|---|
| Startup receipt | GOOD | Written once by startup_receipt.py, dashboard reads artifact |
| Attention classification | GOOD | Single classify_attention_status(), fanned to all surfaces |
| Review state / compact | GOOD | Atomic write from same dict in write_projection_bundle() |
| Instruction revision | MOSTLY GOOD | All trace to bridge line, minor priority waterfall risk |
| Heartbeat/daemon | BROKEN | Dashboard uses only `stopped_at_utc` to determine running. Review-channel also checks PID liveness + heartbeat freshness. Crashed daemon (dead PID, no stop) shows RUNNING on dashboard, NOT RUNNING on review-channel. |
| Git state | BROKEN | 3 independent subprocess call sites (_git_short, collect_git_status, _collect_git_status_for_repo). No shared utility. |
| Bridge findings | BROKEN | Dashboard parses bridge.md markdown directly. Typed review_state exists upstream but dashboard doesn't read it for findings. |
| Repo-pack config | BROKEN | Only 7 of 100+ call sites use active_path_config(). 35+ files bypass with REPO_ROOT literal. Portability blocker. |

Reference patterns (GOOD — everything should follow these):
1. Approval mode: computed once in approval_mode.py, threaded via ControlState.approvals
2. Startup receipt: computed once, written to artifact, consumers read artifact
3. Attention: single classifier, result fanned to all surfaces
4. Review state: atomic multi-file write from single source dict

## System Seam Audit (Round 4, 8-agent, 2026-04-04)

| Seam | Status | Detail |
|---|---|---|
| Approval mode | GOOD | Computed once (`approval_mode.py`), shared via `ControlState.approvals`. THE PATTERN. |
| Plan tracking | BROKEN | 3 independent parsers: dashboard text-scans MASTER_PLAN, context-graph reads INDEX.md, startup ignores it |
| Worker topology | PARTIAL | Same file but passive reader (dashboard) vs active writer (review-channel). Stale file = stale dashboard. |
| Publication/push | BROKEN | Dashboard reads `push/latest.json`, startup computes from live git. Can disagree. |
| Autonomy loop | SILO | Own artifacts, dashboard/typed state never reads them. Phone-status connected but disconnected from dashboard. |
| Doc-authority | SILO | Budget/overlaps/consolidation invisible outside `devctl doc-authority` command |
| Error handling | AD-HOC | 3 patterns (stderr print, raise, structured step). No shared error log/artifact. |
| Cross-surface tests | ZERO | 66 cross-refs but no test proves two surfaces agree for same inputs |

Approval mode is the REFERENCE PATTERN: one computation, one place, all surfaces read from it.

## Data Pipeline Audit (Round 3, 8-agent, 2026-04-04)

Every data pipeline from source → surface was audited. Core finding: **every surface computes independently, rich data is discarded at every layer, no shared read model.**

| Pipeline | Data Available | Data Surfaced | Lost |
|---|---|---|---|
| Guard → Dashboard | Full per-check results with file/line/policy | Only push-preflight, capped at 10 | Guards run outside push invisible |
| Probe → Dashboard | Per-file, per-probe findings with severity | Aggregate counts only (high: N) | All actionable detail |
| Governance → Dashboard | Per-finding verdicts, recurrence risk, fix notes | 4 summary counters | Everything per-finding |
| Startup vs Dashboard | Both compute push/quality/review state | Independent paths, different sources | Silent disagreement possible |
| Operator Console | Own parallel state models, own dataclasses | Raw JSON socket from daemon | No shared typed state with CLI |
| Phone surface | Static JSON artifact | Pre-built file, no live data | Git, daemons, quality, probes, events, plans |
| Event log (20K events) | Duration, area, argv, retries, cycle_id, timestamps | 5 aggregated totals + 20-event sparkline | ~95% of data buried |
| MCP adapter | 4 read-only tools, typed JSON | Status/report/compat/release | No per-file guard query, no dashboard, no typed state query |

### Root cause (confirms ChatGPT P0 diagnosis)
No `ControlPlaneReadModel` exists. Each surface independently reads raw artifact files and computes its own derived state. The fix is ONE builder that reads all sources once, produces ONE resolved read model, and ALL surfaces render only that.

## Session Resume

- 2026-04-18 role-implicit commit-approval slice:
  resume from the live `/remote-control` dogfood regression, not from either
  blanket extreme. The repo already projects one active
  `remote_control_attachment` for Claude with `role=operator`, and the same
  review state exposes Claude as both `coding_agent` and `operator_agent`
  while startup/control-plane still resolve `interaction_mode=remote_control`.
  The next bounded closure is to replace string-only remote-control approval
  gating with one typed approval-authority decision: auto-satisfy the governed
  commit approval step only when runtime evidence proves an active
  operator-role delegation for the current remote-control lane; otherwise keep
  the explicit typed approval-packet / `devctl commit --approve-pending`
  recovery path fail-closed.
- 2026-04-15 remote-control campaign baseline:
  resume this lane from the bounded live proof, not from abstract fanout.
  The default topology is `Codex conductor/reviewer + Claude remote-control
  implementer + permanent Claude packet watcher`; worker fanout stays zero for
  mutating work until startup receipts stop reporting
  `safe_to_fanout=False` / `resync_required=True`.
- 2026-04-15 finding-ingress contract:
  remote-control misses now have one explicit compatibility path.
  `LIVE_RUN.md` remains projection/mirror evidence only, but
  `governance-import-findings --input-format md` can import those sections
  with repo-scoped `repo_name:Q-ID` identity while dogfood rows carry the
  matching campaign, topology, and finding references needed to correlate the
  live run.
- 2026-04-13 packet-inbox + stale-attention write barrier:
  resume from current-instruction convergence, not from packet attention
  modeling again. `ReviewState.packet_inbox` is now the canonical typed wake /
  focus reducer for startup-context, session-resume, reviewer-follow, and the
  governed stage/commit path. The remaining bounded closure is to collapse
  dashboard/status/current-session onto one current-instruction selector so a
  finding packet can never become the operator-visible instruction in one
  surface while another surface still shows the old bridge instruction.
- 2026-04-13 typed selector closure / bridge-status follow-up:
  resume from the bridge-backed compatibility drift, not from raw packet
  fallbacks again. The typed queue is now the only packet-derived instruction
  selector, but `review-channel status` in markdown-bridge mode still reports
  stale bridge drift for `current_session`. The next bounded step is to make
  that bridge-mode status report consume the same typed current-session/current
  focus path directly or otherwise rewrite the compatibility bridge before it
  renders operator-visible instruction text.
- 2026-04-13 actionable current-slice closure:
  resume from the next operator-language/authority slice, not from startup
  current-slice drift again. Startup now prefers a live typed instruction over
  bare plan-scope placeholders, so the next bounded work is clarifying
  participant/conductor/reviewer/implementer semantics in operator-facing
  surfaces while keeping the same typed authority model.
- 2026-04-13 single-agent dual-role count closure:
  resume from the narrower `current_slice` projection mismatch, not from
  reviewer/implementer count truth again. `review-channel status` and
  startup-facing runtime counts now agree that the live remote-control lane is
  one active Codex conductor filling both reviewer and implementer roles while
  Claude remains the dashboard/operator participant. The next bounded step is
  to make `startup-context` / `current_session` refresh that same live slice
  text instead of keeping the stale "0 implementers" prose after the count
  fix.
- 2026-04-12 bridge-sync + packet-wake closure:
  resume from the next event-wake/read-model tranche, not from another
  compatibility artifact split. `review-channel status` now owns
  `bridge.md` re-projection when typed `current_session` drift is detected,
  and the running follow loops now treat reviewer-targeted pending packets as
  progress. The next bounded proof step is to attach that packet wake to the
  live dashboard/operator lane more explicitly, then rerun the Claude
  dashboard / Codex local-implementer commit proof on the same typed packet
  path.
- 2026-04-12 surface-consolidation + event-stream closure:
  resume from one typed read model and one packet lifecycle, not four status
  surfaces plus timer pollers. The next bounded order is explicit: collapse
  dashboard/monitor/mobile/phone onto one reducer-backed blocker vocabulary,
  make `FindingBacklog` the single open-findings reader, freeze the shared
  packet lifecycle and bidirectional wake path for all lanes, and surface live
  tool-call progress through `agent-mind` / typed current-session state. This
  is Phase 0 visibility closure for the remote/dashboard lane and must land
  before loop-v2 / `devctl develop` autonomy claims widen.
- 2026-04-12 shared-primary topology correction:
  resume from the governed default, not the workaround path. When
  startup/runtime project `worktree_strategy=shared_primary_worktree` and
  requested worker fanout is zero, Codex coding/review activity plus the
  attached dashboard/operator share the primary checkout and use the same
  governed commit/push path. Only explicit delegated workers get isolated
  worktrees and separate `worktree_identity` publication authority. The next
  proof step is to teach this default through bootstrap/dashboard/status so
  agents stop inventing linked-worktree/shadow-gitdir recoveries.
- 2026-04-12 findings-convergence slice:
  resume from one canonical findings reader, not more packet counting and not
  more bridge parsing. The next bounded runtime step is a shared
  `FindingBacklog` loader/snapshot that owns live open findings for
  dashboard/operator views, startup bootstrap, monitor self-audit, bridge
  projection, and ranked backlog tooling. `review-channel --action post
  --kind finding` must become an intake writer into that backlog, existing
  `LIVE_RUN.md` findings must enter through import/projection compatibility,
  and `governance-review` must stay the close-out sink over the same
  `finding_id` / `Q-ID` identity. The current dogfood proof to retire is
  concrete: dashboard says `Open findings: 0`, monitor says
  `should_emit_finding=True` with no consumer, and `findings-priority` still
  scrapes 134 markdown findings.
- 2026-04-12 role-first beta-matrix slice:
  resume with the control-lane/worker-lane split and the first read-side
  identity closure already landed. The default remote-control lane shares the
  primary checkout while worker fanout is zero; isolated worker worktrees are
  reserved for explicit delegated fanout. Typed read models now prefer
  reviewer/implementer aliases over provider-coded bridge names, and
  commit/push approval is bound to the `worktree_identity` that staged it.
  The next proof step is the live rerun of Codex coding on the primary lane
  with Claude attached as dashboard/operator, then delegated-worker and
  swapped reviewer/implementer permutations once that matrix stays green.
- 2026-04-09 external-session attachment closure: resume from the next
  consumer/UI pass, not another write-path invention. The typed
  `remote_control_attachment` record now exists in reviewer runtime,
  startup-context, session-resume, and the control-plane read model. The next
  bounded follow-up is projection parity: surface it where helpful in
  dashboard/operator views and then reuse it for the live remote-control proof
  instead of introducing another remote-session registry.
- 2026-04-09 command-boundary freeze closure: the reopened MP-384/MP-387 F1
  parity rerun is now repaired at the CLI edge too, not only in reducer-only
  tests. Resume from the next bounded follow-up only: keep the remaining
  mobile/helper/repo-pack readers on the same frozen review-state tick, then
  rerun the live remote-control proof. Do not reopen another broad dashboard
  rewrite or a second coordination-model plan.
- 2026-04-08 typed-authority convergence absorption: resume from the combined
  phases 2 through 4 closure order, not from isolated dashboard polish. After
  coordination lands in the shared read model, immediately include helper /
  repo-pack fallback readers, clarify `safe_to_fanout` read-only semantics,
  migrate duplicate SystemCatalog/bootstrap/prompt surfaces through parity-
  backed adapters, and then prove the result in one live remote-control run,
  one blocked-fanout read-only review, and one fresh-AI bootstrap run.
- 2026-04-09 graph-backed read-side intake:
  resume the next slice with the concrete probes, not more theory: schema diff
  across startup/session/dashboard/mobile, raw bridge-reader closure,
  `SystemCatalog` union-diff, recurring-finding clustering, dead-topology
  evidence, and a single snapshot-parity artifact.
- Current status update: the coordination packet now exists on the live
  runtime, but the launch-critical read side is still split. Resume from the
  concrete closure order: add coordination to `ControlPlaneReadModel`, expose
  the same bounded fields in `startup-context --format summary` /
  machine-summary, make `resync_required` and unsafe fanout posture visible to
  blocker/next-command selection, then relaunch the governed remote-control
  Codex-reviewer / Claude-coder loop on this scope and decide whether that
  retarget/relaunch can be automated by repo-owned state.
- Current status: the review/runtime architecture is mapped cleanly enough to
  stop guessing. The remaining gaps are now explicit tracked closure items:
  fail-closed operator mode, terminal-none proof-of-life launch validation,
  session cleanup/orphan refusal/startup preflight cleanup, control-plane
  contract-catalog coverage, stale-review invalidation, queue metric split,
  typed reviewer bootstrap/session-resume truth, and deterministic validation
  plan/receipt routing for checkpoint/commit/push cadence. The `MP-383`
  bridge Action Requests queue is now projection-only and runtime-bound for
  executable actions, and the queue/dashboard packet split is closed for live
  actionable vs stale packet history. The remaining operator-surface problem
  in the live repo is cadence/freshness and discoverability: the system still
  needs one repo-owned reviewer-loop/remote-lane harness and stronger typed
  field consumption discipline so agents stop falling back to prose and stale
  bridge timing.
- Next action: after validation, relaunch the repo-owned dual-agent loop and
  have Codex review this single-agent repair plus the already-landed
  `MP-382` / `MP-387` launch-authority closure. Keep future work bounded to
  the remaining lifecycle/queue/dashboard/session-resume items above; do not
  reopen a bridge-prose-only permission path.
- Context rule: read `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/active/ai_governance_platform.md`,
  `dev/active/platform_authority_loop.md`,
  `dev/active/remote_commit_pipeline.md`, and this plan before editing
  review-channel runtime, dashboard, or remote-control surfaces.
- Scope note: the bounded review scope for this session is the 8 commits ahead
  of `@{upstream}`. `git log origin/master..HEAD` currently returns 313 commits
  on this repo and is not the narrow review range for this branch.

## Audit Evidence

- 2026-04-09 caller-selected review-bundle authority validation:
  `python3 -m pytest dev/scripts/devctl/tests/test_mobile_status.py dev/scripts/devctl/tests/test_control_plane_surface_wiring.py dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_review_state_locator.py dev/scripts/devctl/tests/test_repo_packs.py -q --tb=short`
  passed (`75 passed`).
  `python3 dev/scripts/devctl.py docs-check --strict-tooling`,
  `python3 dev/scripts/checks/check_active_plan_sync.py`,
  `python3 dev/scripts/checks/check_multi_agent_sync.py`, and
  `python3 dev/scripts/checks/check_platform_contract_closure.py`
  all passed after the owner-doc updates for this slice.
- 2026-04-07 action-request projection/binding validation:
  `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_action_request.py dev/scripts/devctl/tests/review_channel/test_plan_packets.py dev/scripts/devctl/tests/review_channel/test_bridge_render.py -q --tb=short`
  passed (`56 passed`), and
  `python3 dev/scripts/devctl.py review-channel --action render-bridge --terminal none --format json`
  passed after previously failing on an overgrown packet-projected
  `## Action Requests` section.
- 2026-04-07 launch-authority/runtime closure validation:
  `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_launcher_discipline.py dev/scripts/devctl/tests/review_channel/test_launch_script.py dev/scripts/devctl/tests/review_channel/test_promotion_guard.py dev/scripts/devctl/tests/review_channel/test_review_channel.py dev/scripts/devctl/tests/runtime/test_auto_mode.py -q --tb=short`
  passed (`383 passed`). `python3 dev/scripts/devctl.py check --profile ci`
  reached `38/40` passing; remaining failures are governance-state blockers
  only (`startup-authority-contract-guard` dirty checkpoint budget and
  `tandem-consistency-guard` missing live repo-owned conductors). Follow-up
  handoff guards passed:
  `python3 dev/scripts/checks/check_review_channel_bridge.py`,
  `python3 dev/scripts/checks/check_active_plan_sync.py`,
  `python3 dev/scripts/checks/check_multi_agent_sync.py`, and
  `python3 dev/scripts/devctl.py docs-check --strict-tooling`.
- 2026-04-07 reviewer-supervisor restart-policy validation:
  `python3 -m py_compile dev/config/launchd/review_channel_publisher_service.py dev/scripts/devctl/commands/review_channel/_publisher.py dev/scripts/devctl/commands/review_channel/_ensure_supervisor.py dev/scripts/devctl/commands/review_channel/_ensure_helpers.py dev/scripts/devctl/commands/review_channel/_supervisor_restart_policy.py`,
  `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_launchd_service.py dev/scripts/devctl/tests/review_channel/test_stop.py -q`,
  and the targeted `ReviewChannelCommandTests` supervisor ensure tests passed.
- Operator-supplied static GitHub branch review of the Apr 5-6 commit cluster,
  cross-checked against the active `MP-380..MP-387` plan and the live local
  reviewer/runtime state.
- `python3 dev/scripts/devctl.py review-channel --action stop --daemon-kind reviewer_supervisor --format json`
- `python3 dev/scripts/devctl.py review-channel --action stop --daemon-kind publisher --format json`
- `python3 dev/scripts/devctl.py review-channel --action reviewer-checkpoint --reviewer-mode active_dual_agent --reason launch-authority-runtime-closure --checkpoint-payload-file /tmp/reviewer-checkpoint-runtime-fix.json --expected-instruction-revision f6a4ce8b1d85 --expected-implementer-state-hash 3173468d76d917c8958a811594411b999c946920130e5bd5ea2ea527b6d49953 --format json`
- `python3 dev/scripts/devctl.py review-channel --action ensure --follow --terminal none --format json --execution-mode markdown-bridge --follow-inactivity-timeout-seconds 0`
- `python3 dev/scripts/devctl.py review-channel --action recover --recover-provider claude --terminal terminal-app --dry-run --format json`
- `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_promotion_guard.py dev/scripts/devctl/tests/review_channel/test_launcher_discipline.py -q --tb=short`
- `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_review_channel.py -q -k "recover_allows_missing_live_claude_conductor or missing_live_claude_conductor or attention_treats_pending_implementer_reset_as_waiting_on_peer or attention_treats_waiting_input_hint_as_implementer_relaunch_required or reviewer_follow_auto_recovers_stalled_implementer or auto_promote_skipped_when_bridge_has_active_instruction" --tb=short`
- `python3 dev/scripts/checks/check_review_channel_bridge.py`
- `python3 dev/scripts/checks/check_active_plan_sync.py`
- `python3 dev/scripts/checks/check_multi_agent_sync.py`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary`
- `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`
- 2026-04-07 validation-cadence architecture intake:
  `python3 dev/scripts/devctl.py startup-context --format summary` failed
  closed with `action=checkpoint_before_continue`,
  `reason=dirty_path_budget_exceeded`; `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`
  confirmed the same checkpoint blockers. Code inspection covered the governed
  VCS stage/commit seams, `control_plane_resolve.resolve_quality()`, and
  `check-router` routed lane output before the accepted plan update.
- 2026-04-08 packet/dashboard convergence validation:
  `python3 -m pytest dev/scripts/devctl/tests/vcs/test_commit_gate.py dev/scripts/devctl/tests/vcs/test_governed_executor.py dev/scripts/devctl/tests/runtime/test_push_authorization.py dev/scripts/devctl/tests/vcs/test_push.py dev/scripts/devctl/tests/review_channel/test_packet_queue_cleanup.py dev/scripts/devctl/tests/runtime/test_review_state.py dev/scripts/devctl/tests/review_channel/test_pending_packet_guards.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short`
  passed (`289 passed`).
  `python3 -m pytest dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_startup_context.py dev/scripts/devctl/tests/governance/test_session_resume.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short`
  passed (`459 passed`).
  `python3 dev/scripts/checks/check_review_channel_bridge.py`
  failed on live repo cadence with stale `Last Codex poll`, and
  `python3 dev/scripts/devctl.py startup-context --format summary`
  still failed closed on dirty checkpoint budget / reviewer-overdue runtime
  blockers even though the targeted parity suites were green.
- `python3 dev/scripts/devctl.py platform-contracts --format md`
- `python3 dev/scripts/checks/check_platform_contract_closure.py --format md`
- `python3 dev/scripts/checks/check_review_surface_consistency.py`
- `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- `python3 dev/scripts/devctl.py review-channel --action doctor --terminal none --format json`
- `python3 dev/scripts/devctl.py session-resume --role reviewer --format summary`
- `python3 dev/scripts/devctl.py auto-mode --format json`
- `python3 -m pytest dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_auto_mode.py dev/scripts/devctl/tests/governance/test_session_resume.py dev/scripts/devctl/tests/review_channel/test_reviewer_checkpoint_inputs.py dev/scripts/devctl/tests/review_channel/test_launch_script.py dev/scripts/devctl/tests/test_control_plane_surface_wiring.py`
- `git log --oneline origin/master..HEAD`
- `git log --oneline @{upstream}..HEAD`
- Key contract/code review inputs:
  `dev/scripts/devctl/runtime/project_governance_contract.py`,
  `dev/scripts/devctl/runtime/project_governance_parse.py`,
  `dev/scripts/devctl/runtime/control_plane_read_model.py`,
  `dev/scripts/devctl/runtime/control_plane_resolve.py`,
  `dev/scripts/devctl/runtime/auto_mode.py`,
  `dev/scripts/devctl/commands/governance/session_resume_support.py`,
  `dev/scripts/devctl/runtime/startup_context.py`,
  `dev/scripts/devctl/runtime/reviewer_runtime_models.py`,
  `dev/scripts/devctl/runtime/operator_context.py`,
  `dev/scripts/devctl/commands/review_channel/bridge_launch_control.py`,
  `dev/scripts/devctl/review_channel/launch_truth.py`,
  `dev/scripts/devctl/review_channel/packet_contract.py`,
  `dev/scripts/devctl/review_channel/action_request.py`,
  `dev/scripts/devctl/review_channel/bridge_projection_state.py`,
  `dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`,
  `dev/scripts/devctl/review_channel/status_projection_helpers.py`,
  `dev/scripts/devctl/review_channel/state.py`,
  `dev/scripts/devctl/review_channel/launch_script.py`,
  `dev/scripts/devctl/review_channel/peer_recovery.py`,
  `dev/scripts/devctl/commands/dashboard.py`,
  `dev/scripts/devctl/commands/dashboard_data.py`,
  `dev/scripts/devctl/steps.py`,
  `dev/scripts/devctl/governance/task_router_contract.py`,
  `dev/scripts/devctl/platform/runtime_state_contract_rows.py`,
  `dev/scripts/checks/platform_contract_closure/field_routes.py`,
  `dev/scripts/checks/platform_contract_closure/support.py`,
  `dev/scripts/devctl/commands/check/router_support.py`,
  `dev/scripts/devctl/script_catalog.py`,
  `dev/scripts/devctl/platform/surface_definitions.py`.
