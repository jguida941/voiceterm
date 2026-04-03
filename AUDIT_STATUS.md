# Remote Orchestration Audit Status

**Branch:** `feature/governance-quality-sweep`
**Last updated:** 2026-04-02 ~10:30pm EDT
**Purpose:** Temporary file for ChatGPT Pro review. Delete when done.

**NOTE FOR CHATGPT PRO:** If file page views look stale, verify against commits directly:
- Commit `85be0aa` = this audit fix (branch tip)
- Commit `7e4d1c2` = ReviewerRuntimeContract (46 files, 1569 lines)
- Use `github.com/jguida941/voiceterm/commit/7e4d1c2` to see the diff directly

## Summary

30 commits pushed. 235+ tests passing (pending revalidation on latest).
Started with 0 fixes, ended with 13 landed and pushed.
ReviewerRuntimeContract (the unified lifecycle owner) is committed and pushed (7e4d1c2).
Architecture is mostly correct. Remaining problems are execution/supervision AND partial authority closure (bridge prose fallback, missing ownership map, HEAD equality).

## CRITICAL FINDING: Why Codex Keeps Going Idle (8-agent investigation)

This is the #1 operational problem. Over 6 hours today, Codex went idle 20+ times. The system detected it every time (`runtime_missing`, `reviewer_overdue`) but could never self-heal. Here's why:

**Root cause: No persistent supervisor in the remote-control pattern.**

The Codex CLI (`codex --full-auto`) has NO built-in polling loop. It processes its prompt, does work, then sits at the prompt. It has no heartbeat, no bridge polling, no self-monitoring. When it finishes its work, it just stops.

The system has a daemon (`ensure --follow`) designed to compensate, but:
- The daemon is ONLY started by `ensure` or `reviewer-heartbeat` actions, never by `launch`
- Neither the governed launch path nor the manual remote-control path auto-starts it
- If it crashes, nothing respawns it — it's a detached process with no parent
- It's a heartbeat publisher, NOT a lifecycle supervisor — it detects `runtime_missing` but doesn't fix it

**The automated rollover code we committed (09349aa) is wired into the daemon tick.** So if the daemon isn't running, the rollover never fires. The fix exists in the code but nobody is running the code.

**8-agent findings:**

| Finding | Evidence |
|---|---|
| Codex CLI has no polling mechanism | `launch_sessions_if_requested()` opens Terminal but never starts publisher |
| Daemons only start via explicit `ensure` action | Never auto-started by `launch` or manual Codex spawn |
| Neither launch path starts daemons | `bridge_handler.py` and `prompt.py` both missing daemon spawn |
| `ensure --follow` can't self-heal | Detects `runtime_missing` but only reports, doesn't fix |
| Rollover code requires running daemon | `maybe_auto_trigger_rollover_on_stale_codex()` is inside daemon tick at `reviewer_follow.py:186` |
| Claude Code could be the daemon | Via MCP server (recommended) or SessionStart hook |
| Industry pattern: needs `launchd` plist | Wrap existing `follow_loop.py` in launchd for auto-restart (~20 lines) |
| Recurrence: 116 error-state polls in 6 hours | `runtime_missing` 5x, `reviewer_overdue` 15x, manual intervention every time |

**Proposed fixes (in order of effort):**
1. **Immediate**: Add daemon auto-start to `bridge_launch_control.py` so governed launch starts publisher/supervisor
2. **Short-term**: Add `launchd` plist (~20 lines) to auto-restart the follow daemon on crash
3. **Medium-term**: Claude Code SessionStart hook that runs `ensure --follow` at session start
4. **Long-term**: MCP server exposing `governance_state()` / `guard_results()` as tools any agent can call

## Latest Verification Round (6 agents, ~7pm EDT)

Pre-7e4d1c2 verification (HISTORICAL — these findings were from BEFORE the ReviewerRuntimeContract landed):

| Claim | Pre-7e4d1c2 verdict | Post-7e4d1c2 status |
|---|---|---|
| Bridge still active gate | was CONFIRMED | NOW PARTIALLY FIXED — typed first, prose fallback |
| No ReviewerRuntimeContract | was CONFIRMED | NOW FIXED — 7e4d1c2 added 10-field ContractSpec |
| Startup ownership empty | was CONFIRMED | NOW FIXED — all 15 contracts have 3 tokens each |
| Rollover is behavioral patch | was REJECTED | STILL correct — rollover is real contract-backed |
| Terminal cleanup not contract-backed | was CONFIRMED | STILL accurate — helper function, not typed state |

## Concrete Next Steps (from 6-agent implementation assessment)

**Priority: Create ReviewerRuntimeContract + startup ownership, then make bridge a projection**

1. **Add ReviewerRuntimeContract** (~15 lines) to `runtime_state_contract_rows.py` with 5 fields: `review_accepted`, `current_verdict`, `open_findings`, `verdict_accepted_at_utc`, `findings_clear_count`

2. **Refactor bridge acceptance to typed state** (4-5 files):
   - `status_projection_bridge_state.py:142-149` — read from typed state
   - `state.py:97` — replace `bridge_review_accepted(bridge_snapshot)` with typed field
   - `bridge_validation.py:108` — typed field as source-of-truth
   - `handoff.py` — propagate typed `review_accepted`
   - Tests — verify typed path works

3. **Populate startup_surface_tokens** on all 15 contracts (one-line per contract, 2-3 field names each)

## What Was Fixed and Pushed Today

| # | Fix | File(s) | Commit |
|---|---|---|---|
| 1 | Idle reviewer masked by fake heartbeats | `reviewer_follow_guard.py`, `reviewer_follow_heartbeat_guard.py` | dde6c2d |
| 2 | Dedupe one-shot bug (restore packet fires only once) | `reviewer_follow_packet_guard.py` | 91fd388 |
| 3 | Dry-run contract violation (auth + caffeinate in preview) | `remote-bridge-loop.sh` | dde6c2d |
| 4 | Push gate: `startup_advisory_decision.py:38` | `startup_advisory_decision.py` | e3ce4fd |
| 5 | Push gate: `startup_push_decision.py:223` | `startup_push_decision.py` | e3ce4fd |
| 6 | Push gate: `runtime_checks.py:67` | `startup_authority_contract/runtime_checks.py` | e7c4898 |
| 7 | Acceptance regex (push approved not recognized) | `bridge_validation_acceptance.py` | 26c76ec |
| 8 | Bridge guard rejects Operator Direction | `bridge_sanitize.py` | 80cc2e8 |
| 9 | Docs governance drift (dangling remote_orchestration.md refs) | `AGENTS.md`, `INDEX.md`, `MASTER_PLAN.md` | e068d7a |
| 10 | Automated reviewer rollover | `reviewer_follow_recovery.py` (+192 lines) | 09349aa |
| 11 | Terminal lifecycle cleanup | `terminal_app.py` (+143 lines), `launch_records.py`, `session_probe.py` | 37f683d |
| 12 | Bridge projection silently dropped Operator Direction | `bridge_projection_state.py`, `bridge_sanitize.py`, `handoff_constants.py` | 801349f |
| 13 | **ReviewerRuntimeContract** — unified lifecycle owner | 46 files, 1569 insertions, 11 new files. Contract owns reviewer mode/freshness/stale/rollover/ACK/poll/session/acceptance/publish-clear. Bridge acceptance demoted to fallback. Doctor surface projects from contract. startup_surface_tokens populated on all 15 contracts. | 7e4d1c2 |

## What's Still Open (verified by 4 agents against actual code ~10pm EDT)

### DONE (verified in code, no longer open)

- **ReviewerRuntimeContract** — EXISTS in `runtime_state_contract_rows.py` (commit 7e4d1c2). Owns reviewer mode, freshness, stale reason, rollover, ACK, poll, session, acceptance, publish_clear.
- **startup_surface_tokens** — POPULATED on all 15 ContractSpec rows (3 tokens each).
- **Bridge acceptance demotion** — PARTIALLY DONE. `bridge_review_accepted()` checks typed `reviewer_runtime` first. Push decision uses `reviewer_runtime.publish_clear` directly.
- **Push invalidation cycle** — FIXED. `review_gate_allows_push` bypasses `implementation_blocked`.

### STILL OPEN (verified by agents)

**1. No persistent supervisor (CRITICAL — root cause of idle-Codex)**
- The Codex CLI has no polling loop — processes prompt and stops
- Follow daemon never auto-started by launch or manual spawn
- Rollover code only runs inside daemon tick — if daemon is dead, rollover never fires
- Today: 116 error-state polls, 20+ manual interventions over 6 hours
- **FIX:** daemon auto-start in launch path + launchd plist for crash restart

**2. Doctor surface exists but NOT registered in parser**
- `reviewer_runtime_doctor.py` is a full 18-field health projection (status, freshness, recovery, recommended command)
- BUT `--action doctor` is NOT in the parser's action choices
- The doctor is only accessible as a nested field within `--action status`
- **FIX:** register `doctor` action in parser.py, add dispatch in `__init__.py`

**3. StartupContext missing contract_ownership_map**
- startup_surface_tokens ARE populated (done)
- BUT StartupContext has no `contract_ownership_map` field
- No runtime path maps contracts back to their startup surface presence
- **FIX:** add bounded ownership map to StartupContext built from ContractSpec registry

**4. Bridge prose is still a live fallback**
- `bridge_review_accepted()` checks typed state FIRST (good)
- BUT falls back to regex prose-parsing when typed state is absent
- Push path (`status_push_decision.py`) does bypass bridge via `publish_clear` (good)
- **FIX:** remove prose fallback once typed state is always available, or make it log a warning

## Verified Findings (8-agent verification x3 rounds)

All fixes use existing typed contracts — no ad hoc bypasses:
- `PacketPostRequest` pipeline for restore packets
- `ReviewerGateState` for push gate decisions
- `PushDecisionInputs` for push decision threading
- `HandoffBundle` + rollover ACK for reviewer recovery
- `BRIDGE_ALLOWED_H2` / `BRIDGE_SECTION_ORDER` for bridge contracts
- `PreparedSessionRecord` for terminal tracking

ChatGPT Pro's diagnosis (updated after verifying latest push):
- "The owner exists now. The system still does not force everyone to use it."
- "You no longer mainly have a modeling problem. You have an execution/supervision problem plus a repo-truth consistency problem."
- "Good recovery logic + insufficient liveness guarantees, instead of good recovery logic + guaranteed supervisor execution."

## Governance Findings (from `governance-review --format md`)

**115+ total findings | ~70 fixed | ~45 open** (counts approximate — governance-review tracks exact state)

Key findings corrected for current branch state:
- `bridge_projection_drops_operator_direction` — FIXED in 801349f
- `bridge_still_active_gate_not_projection` — PARTIALLY FIXED in 7e4d1c2 (typed first, prose fallback remains)
- `need_review_channel_doctor_surface` — PARTIALLY FIXED in 7e4d1c2 (surface exists, not registered in parser)
- `startup_surface_tokens_unpopulated` — FIXED in 7e4d1c2 (all 15 contracts populated with 3 tokens each)
- `reviewer_truth_distributed_no_owner` — FIXED in 7e4d1c2 (ReviewerRuntimeContract is the admitted owner)
- `push_invalidation_head_equality` — open (HEAD equality check still in push_state.py, needs acceptance identity redesign)
- `manual_codex_rollover` — FIXED in 09349aa (automated rollover landed)
- `zombie_terminal_cleanup` — FIXED in 37f683d (terminal cleanup landed)
- `agent_architecture_bypass` — open (no startup ownership map yet)
- `agent_tooling_contract_ignorance` — open (agents still lack typed vocabulary)

## Key Architecture Files

| Purpose | File |
|---|---|
| Push decision | `dev/scripts/devctl/runtime/startup_push_decision.py` |
| Startup advisory | `dev/scripts/devctl/runtime/startup_advisory_decision.py` |
| Startup context | `dev/scripts/devctl/runtime/startup_context.py` |
| Launch truth | `dev/scripts/devctl/review_channel/launch_truth.py` |
| Bridge validation | `dev/scripts/devctl/review_channel/bridge_sanitize.py` |
| Bridge acceptance | `dev/scripts/devctl/review_channel/bridge_validation_acceptance.py` |
| Bridge projection | `dev/scripts/devctl/review_channel/bridge_projection_state.py` |
| Handoff/rollover | `dev/scripts/devctl/review_channel/handoff.py` |
| Peer recovery | `dev/scripts/devctl/review_channel/peer_recovery.py` |
| Status projection | `dev/scripts/devctl/review_channel/state.py` |
| Terminal launch/cleanup | `dev/scripts/devctl/review_channel/terminal_app.py` |
| Reviewer follow | `dev/scripts/devctl/review_channel/reviewer_follow.py` |
| Reviewer recovery | `dev/scripts/devctl/review_channel/reviewer_follow_recovery.py` |
| Startup authority | `dev/scripts/checks/startup_authority_contract/runtime_checks.py` |
| Platform contracts | `dev/scripts/devctl/platform/contracts.py` |
| Contract rows | `dev/scripts/devctl/platform/runtime_*_contract_rows.py` |

## ChatGPT Pro Architectural Direction (updated ~10:30pm EDT)

**Previous directive (items 1-4 below are now DONE):**
1. ~~Create ReviewerRuntimeContract~~ — DONE (commit `7e4d1c2`, 10-field ContractSpec + dataclass)
2. ~~Demote bridge acceptance~~ — DONE (typed state checked first, prose is fallback)
3. ~~Doctor as projection~~ — DONE (18-field surface, but not registered in parser yet)
4. ~~Populate startup_surface_tokens~~ — DONE (all 15 contracts have 3 tokens each)

**Current directive: "The owner exists. The system still does not force everyone to use it."**

The remaining problem is execution/supervision, not modeling:
- The recovery logic exists but nobody reliably runs it
- The doctor surface exists but agents can't invoke it
- The bridge fallback still exists as a second truth path
- The startup tokens exist but no ownership map tells agents which contract owns what
- Audit files can drift from code with no guard to prevent it

### Design rules (from ChatGPT Pro)

> typed state is authority, bridge is projection
> one owner per lifecycle, not distributed fragments
> doctor projects from the owner, doesn't independently analyze
> startup tells agents what exists, not just what's allowed
> audit files cannot claim a state unless a commit proves it
> do NOT add more recovery recipes until daemon liveness is closed

## Commit-Level Proof (for ChatGPT Pro — verify against commits, not file pages)

### Implemented and pushed — with commit + file proof

| # | What | Commit | File | What to look for |
|---|---|---|---|---|
| 1 | ReviewerRuntimeContract ContractSpec | `7e4d1c2` | `runtime_state_contract_rows.py` | `contract_id="ReviewerRuntimeContract"` with 10 required fields |
| 2 | ReviewerRuntimeContract dataclass | `7e4d1c2` | `reviewer_runtime_models.py` | Dataclass with reviewer_mode, freshness, stale_reason, rollover, session_owner, acceptance, publish_clear |
| 3 | Contract builder | `7e4d1c2` | `reviewer_runtime_contract.py` | `build_reviewer_runtime_contract()` assembles from bridge_liveness + attention + session |
| 4 | Doctor projection | `7e4d1c2` | `reviewer_runtime_doctor.py` | 18-field health surface projecting from the contract |
| 5 | Session owner | `7e4d1c2` | `reviewer_runtime_session_owner.py` | Terminal PID + window_id ownership |
| 6 | Rollover state owner | `7e4d1c2` | `reviewer_runtime_rollover.py` | rollover_id, ack_pending, trigger reason |
| 7 | Bridge acceptance demoted | `7e4d1c2` | `bridge_validation_acceptance.py` | `_runtime_review_accepted()` checks typed state FIRST, prose is fallback |
| 8 | Push reads from contract | `7e4d1c2` | `state.py` | `review_gate_allows_push=bool(reviewer_runtime.publish_clear)` |
| 9 | Startup reads from contract | `7e4d1c2` | `startup_context.py` | `state.reviewer_runtime.review_acceptance.review_accepted` and `publish_clear` |
| 10 | startup_surface_tokens populated | `7e4d1c2` | All 4 contract row files | All 15 ContractSpec rows have 3 tokens each |
| 11 | Automated reviewer rollover | `09349aa` | `reviewer_follow_recovery.py` | `maybe_auto_trigger_rollover_on_stale_codex()` with 5 attention states |
| 12 | Terminal cleanup | `37f683d` | `terminal_app.py` | `cleanup_terminal_session()` with SIGTERM + window close |
| 13 | Audit matches code | `85be0aa` | `AUDIT_STATUS.md` | Corrected to reflect actual branch state |

### NOT yet implemented — what remains (verified by 8 agents against ChatGPT Pro review)

| # | What | Status | Where | Est. size | Why |
|---|---|---|---|---|---|
| A | Daemon auto-start in launch | NOT CODED | `dev/scripts/devctl/commands/review_channel/bridge_launch_control.py` | ~10 lines | Root cause of idle-Codex. Neither governed nor manual launch starts daemon. Must also cover manual remote-control sessions via launchd plist (item B). |
| B | launchd plist for crash restart | NOT CODED | `dev/config/` | ~20 lines | Daemon dies, nothing restarts it. |
| C | Register `--action doctor` in parser | NOT CODED | `dev/scripts/devctl/review_channel/parser.py` + `dev/scripts/devctl/commands/review_channel/__init__.py` | ~5 lines | Doctor exists but CLI can't invoke it. Dispatch in commands-layer `__init__.py`. |
| D | contract_ownership_map in StartupContext | NOT CODED | `startup_context.py` | ~15 lines | Must derive from ContractSpec registry (not hand-maintained). Agents need typed "who owns what" at bootstrap. |
| E | Remove bridge prose fallback | NOT CODED | `bridge_validation_acceptance.py` | ~10 lines | Typed state is primary but prose fallback is still live. |
| F | Audit file auto-sync guard | NOT CODED | `dev/scripts/checks/` | ~30 lines | Prevents audit/code drift that confused agents today. |
| G | Eliminate bridge from push authority path | NOT CODED | `status_push_decision.py` | ~20 lines | Push must gate on typed `publish_clear` only, not bridge-derived fields. |
| H | Acceptance identity redesign (tree hash receipt) | NOT CODED | `reviewer_runtime_models.py` + producer/projection/test updates | ~60 lines | Replace HEAD equality with reviewer-owned tree hash receipt. Extend existing rollover_id pattern from handoff.py. Touches models, projection, and startup. |
| I | Cross-surface consistency proof | NOT CODED | `dev/scripts/checks/` | ~50 lines | startup-context, status, and push can currently disagree because they independently call refresh_status_snapshot with no versioning. |
| J | Daemon regression tests | NOT CODED | `dev/scripts/devctl/tests/` | ~80 lines | Cover: absent at login, crash mid-review, stale config, duplicate start, heartbeat suppression, inactive no-op. |
| K | Prove clean end-to-end path | NOT TESTED | Integration test | TBD | launch → daemon → review → ACK → push (all typed, no bridge prose) |
| L | Prove rescue end-to-end path | NOT TESTED | Integration test | TBD | stale reviewer → daemon detects → rollover → cleanup → fresh session → green |

## Implementation Plan (ChatGPT Pro + 8-agent verified, all 5 missing items added)

**The architecture is correct. Remaining failures are execution + authority closure.**

**8-agent verification results (this round):**
- state.py DID land typed path — ChatGPT Pro was reading stale code for that one
- HEAD equality IS still real and unfixed in push_state.py:111-115
- Cross-surface inconsistency IS possible — startup, status, push each independently refresh with no versioning
- reviewer_follow_recovery.py scope expanded (docstring stale) — now covers both implementer AND reviewer
- Phase reorder CONFIRMED correct — authority before liveness
- All 5 missing items ARE genuinely missing
- Acceptance identity: no reviewed_tree_hash exists, but rollover_id pattern in handoff.py is extensible
- Existing `reviewed_worktree_hash` in handoff resume_state is metadata only, not acceptance identity

### Phase 1: Daemon liveness (BLOCKS self-healing)

| Step | Item | File | Size |
|---|---|---|---|
| 1a | Daemon auto-start in launch | `bridge_launch_control.py` | ~10 lines |
| 1b | launchd plist for crash restart | `dev/config/` | ~20 lines |
| 1c | Daemon regression tests (absent, crash, stale, duplicate, suppression, inactive) | `dev/scripts/devctl/tests/` | ~80 lines |

**Why first:** Root cause of idle-Codex. Nothing self-heals without a running daemon.

### Phase 1.5: Doctor promotion (unblocks all verification)

| Step | Item | File | Size |
|---|---|---|---|
| 1.5a | Register `--action doctor` in parser | `dev/scripts/devctl/review_channel/parser.py` + `dev/scripts/devctl/commands/review_channel/__init__.py` | ~5 lines |

**Why here:** Cheap (5 lines), unblocks every later phase. Operators and agents need one canonical health command.

### Phase 2: Eliminate bridge authority (BLOCKS correct decisions)

| Step | Item | File | Size |
|---|---|---|---|
| 2a | Eliminate bridge from push authority path | `status_push_decision.py` | ~20 lines |
| 2b | Remove bridge prose fallback | `bridge_validation_acceptance.py` | ~10 lines |
| 2c | Acceptance identity redesign (tree hash receipt) | `reviewer_runtime_models.py` | ~40 lines |

**Why second:** Daemon-first gives a system that wakes up but may read wrong artifact. Authority-closure ensures daemon trusts typed state. Acceptance identity replaces fragile HEAD equality with reviewer-owned tree hash receipt (extend existing rollover_id pattern from handoff.py).

### Phase 3: Surface ownership + consistency

| Step | Item | File | Size |
|---|---|---|---|
| 3a | contract_ownership_map in StartupContext | `startup_context.py` | ~15 lines |
| 3b | Cross-surface consistency proof | `dev/scripts/checks/` | ~50 lines |
| 3c | Audit file auto-sync guard | `dev/scripts/checks/` | ~30 lines |

**Why third:** Agents need ownership metadata at bootstrap. Consistency proof ensures startup-context, status, and push all agree (currently they independently refresh with no versioning — verified by agents). Audit guard prevents the drift that confused agents today.

### Phase 4: Prove it works

| Step | Item | What |
|---|---|---|
| 4a | Clean path test | launch → daemon → review → tree-hash receipt → push (all typed, zero bridge) |
| 4b | Rescue path test | stale reviewer → daemon detects → rollover → cleanup → fresh session → doctor green |
| 4c | Surface convergence test | doctor + startup + push gate + bridge projection queried on same state, outputs compared |

**Phase order rationale:** Daemon liveness (1) blocks self-healing. Doctor (1.5) unblocks verification. Bridge elimination (2) closes the second truth path before integration tests. Surface consistency (3) depends on bridge being closed. Proofs (4) prove the final design, not an intermediate state.

**Do NOT skip phases. Each phase closes a precondition the next depends on.**
