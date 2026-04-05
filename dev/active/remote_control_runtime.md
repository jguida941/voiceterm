# Remote Control Runtime Closure Plan

**Status**: active  |  **Last updated**: 2026-04-05 | **Owner:** Tooling/control plane/review runtime/dashboard
Execution plan contract: required
This spec is mirrored in `dev/active/MASTER_PLAN.md` under `MP-380..MP-386`.
It closes the remote-control/operator-surface gaps found in the 2026-04-04
architecture review of commits `5bed0fa..4094c39`.

## Scope

Close the remaining phone/remote-control architecture gaps without creating a
second bridge-only authority path. The target is one typed remote-control
runtime that drives reviewer lifecycle, action requests, dashboard projections,
and auto-poll behavior across CLI, bridge compatibility text, and later
phone/operator-console clients.

Out of scope for this tranche: a second VCS executor, a second packet/action
transport, or any new frontend that parses raw bridge markdown once a typed
contract exists.

## Execution Checklist

- [x] Architecture-review the 8 commits ahead of the tracked upstream and map
      the gaps onto existing owner contracts.
- [ ] MP-380 Add one typed operator-interaction mode (`local_terminal` vs
      `remote_control`) and project it through `ProjectGovernance`,
      `StartupContext`, `ReviewState`, and reviewer-runtime surfaces.
- [ ] MP-381 Add one typed `CheckResult` / `ViolationRecord` contract family
      plus one shared renderer/JSON projection for checks, probes,
      governance-review, startup summaries, and dashboard consumers.
- [ ] MP-382 Finish headless session lifecycle closure so launch, recovery,
      and rollover honor typed operator mode, survive non-zero conductor exit,
      and do not recommend `Terminal.app` in remote-control mode.
- [ ] MP-383 Converge bridge `## Action Requests` onto the existing
      `PacketPostRequest(kind="action_request")` event path and keep bridge
      action rows as projection-only compatibility text.
- [ ] MP-384 Make `devctl dashboard` the single operator surface over typed
      review/runtime/check state instead of bridge regex and `format_steps_text`
      parsing.
- [ ] MP-385 Add repo-owned remote-control auto-poll/update cadence for
      reviewer, implementer, and operator-facing surfaces using the same typed
      runtime state and packet queue.
- [ ] MP-386 Add one typed discoverability/system-map slice with
      `SystemCatalog`, derived `AgentDispatchPacket`, and a thin `view`
      adapter so agents/operators can ask what exists, what to run, and how to
      render it without reviving prose-only discovery.

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

### Priority 3: Hard parity guard — `check_control_plane_parity.py`
- **What**: One fixture proves dashboard, auto-mode, session-resume, phone, and mobile agree on the same ControlPlaneReadModel inputs
- **Scope**: New guard or extension of `check_platform_contract_closure.py`
- **Why third**: Without parity proof, surfaces can silently disagree and the operator sees different state depending on which surface they check
- **Touches**: MP-381 (typed contracts), AUD-24, Findings 5, 11, 18

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

See `bridge.md` § Claude Findings and § Codex Findings for the full catalog.
Summary: 3 P0, 8 P1 (including Codex HIGH), 5 P2, 4 new guards needed.

## Progress Log

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

- Current status: architecture review is complete, Slice A (`MP-380/382`) is
  committed and validated by targeted contract checks, and the remaining
  execution queue is `MP-383..MP-386`.
- Next action: keep Slice A limited to review/validation, then fan out
  `MP-383`, `MP-381`, `MP-384`, `MP-385`, and `MP-386` in bounded parallel
  with disjoint write sets and one final CI/docs/plan-sync pass before
  commit/push approval.
- Context rule: read `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/active/ai_governance_platform.md`,
  `dev/active/platform_authority_loop.md`,
  `dev/active/remote_commit_pipeline.md`, and this plan before editing
  review-channel runtime, dashboard, or remote-control surfaces.
- Scope note: the bounded review scope for this session is the 8 commits ahead
  of `@{upstream}`. `git log origin/master..HEAD` currently returns 313 commits
  on this repo and is not the narrow review range for this branch.

## Audit Evidence

- `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary`
- `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`
- `python3 dev/scripts/devctl.py platform-contracts --format md`
- `git log --oneline origin/master..HEAD`
- `git log --oneline @{upstream}..HEAD`
- Key contract/code review inputs:
  `dev/scripts/devctl/runtime/project_governance_contract.py`,
  `dev/scripts/devctl/runtime/project_governance_parse.py`,
  `dev/scripts/devctl/runtime/startup_context.py`,
  `dev/scripts/devctl/runtime/reviewer_runtime_models.py`,
  `dev/scripts/devctl/runtime/operator_context.py`,
  `dev/scripts/devctl/review_channel/packet_contract.py`,
  `dev/scripts/devctl/review_channel/action_request.py`,
  `dev/scripts/devctl/review_channel/bridge_projection_state.py`,
  `dev/scripts/devctl/review_channel/launch_script.py`,
  `dev/scripts/devctl/review_channel/peer_recovery.py`,
  `dev/scripts/devctl/commands/dashboard.py`,
  `dev/scripts/devctl/commands/dashboard_data.py`,
  `dev/scripts/devctl/steps.py`,
  `dev/scripts/devctl/governance/task_router_contract.py`,
  `dev/scripts/devctl/commands/check/router_support.py`,
  `dev/scripts/devctl/script_catalog.py`,
  `dev/scripts/devctl/platform/surface_definitions.py`.
