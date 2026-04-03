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
Architecture is now correct. Remaining problem is execution/supervision, not modeling.

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

ChatGPT Pro's latest review verified against pushed code:

| Claim | Verdict | Evidence |
|---|---|---|
| Bridge still active gate | **CONFIRMED** | `bridge_review_accepted()` regex-parses prose, no typed-only path |
| No ReviewerRuntimeContract | **CONFIRMED** | Lifecycle distributed across 87+ modules, no ContractSpec row |
| Startup ownership empty | **CONFIRMED** | All 14 ContractSpec have `startup_surface_tokens=()` |
| Rollover is behavioral patch | **REJECTED** | Rollover delegates through HandoffBundle/ACK, uses typed AttentionStatus enum |
| Terminal cleanup not contract-backed | **CONFIRMED** | Standalone helper, returns untracked `list[str]`, no typed state persisted |

ChatGPT Pro was right on 4 of 5 claims. The rollover IS real contract-backed work, not a patch.

## Concrete Next Steps (from 6-agent implementation assessment)

**Priority: Create ReviewerRuntimeContract + startup ownership, then make bridge a projection**

1. **Add ReviewerRuntimeContract** (~15 lines) to `runtime_state_contract_rows.py` with 5 fields: `review_accepted`, `current_verdict`, `open_findings`, `verdict_accepted_at_utc`, `findings_clear_count`

2. **Refactor bridge acceptance to typed state** (4-5 files):
   - `status_projection_bridge_state.py:142-149` — read from typed state
   - `state.py:97` — replace `bridge_review_accepted(bridge_snapshot)` with typed field
   - `bridge_validation.py:108` — typed field as source-of-truth
   - `handoff.py` — propagate typed `review_accepted`
   - Tests — verify typed path works

3. **Populate startup_surface_tokens** on all 14 contracts (one-line per contract, 2-3 field names each)

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
| 13 | **ReviewerRuntimeContract** — unified lifecycle owner | 46 files, 1569 insertions, 11 new files. Contract owns reviewer mode/freshness/stale/rollover/ACK/poll/session/acceptance/publish-clear. Bridge acceptance demoted to fallback. Doctor surface projects from contract. startup_surface_tokens populated on all 14 contracts. | 7e4d1c2 |

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

**115 total findings | 68 fixed | 47 open**

Key open findings:
- `bridge_projection_drops_operator_direction` — FIXED in 801349f
- `bridge_still_active_gate_not_projection` — open, architectural
- `need_review_channel_doctor_surface` — open, needs implementation
- `startup_surface_tokens_unpopulated` — open, all 14 contracts empty
- `reviewer_truth_distributed_no_owner` — open, architectural
- `push_invalidation_head_equality` — open but cycle broken by P0
- `manual_codex_rollover` — FIXED in 09349aa (automated rollover landed)
- `zombie_terminal_cleanup` — FIXED in 37f683d (terminal cleanup landed)
- `agent_architecture_bypass` — open, root cause of all agent misbehavior
- `agent_tooling_contract_ignorance` — open, agents don't know typed vocabulary

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

## ChatGPT Pro Architectural Direction (updated ~8:00pm EDT)

**Verdict: "You have enough mechanisms now. What you still lack is one owner."**

ChatGPT Pro reviewed the branch 3 times. Consistent finding each time: the landed work is real and on-architecture, but it's behavioral patches around a missing contract seam. The system is improving operationally but the architectural seam is still open.

**Key correction from latest review:** The proposed 5-field ReviewerRuntimeContract (review_accepted, current_verdict, open_findings, verdict_accepted_at_utc, findings_clear_count) is TOO SMALL. Those are bridge/verdict state only. The real lifecycle owner also needs: reviewer freshness, stale reason, rollover/ACK state, poll freshness, and session ownership. Without those, you just create a typed acceptance object while leaving the lifecycle fragmented.

### What to implement next (in order)

**1. ReviewerRuntimeContract (the missing owner — FULL lifecycle, not just acceptance)**

Not another helper file. The admitted typed owner of ALL reviewer runtime truth. Must own:
- reviewer mode + effective mode
- reviewer freshness (fresh/poll_due/stale/overdue/missing)
- stale reason (which attention state triggered)
- rollover state (rollover_id, pending ACK, trigger reason)
- last poll freshness (UTC timestamp + age)
- session/terminal ownership (PID, window_id, script_path)
- recovery action currently allowed (from peer_recovery dispatch)
- review acceptance (verdict + findings state)
- publish-clear condition (all of the above must be green)

Add as ContractSpec in `runtime_state_contract_rows.py` with ~10 fields.
Create companion dataclass as the runtime model.
This replaces the current fragmentation across 5+ modules.

**2. Demote bridge_review_accepted() from authority to projection**

Currently `bridge_review_accepted()` regex-parses bridge prose to determine push eligibility. That's markdown-driven authority, not typed-runtime authority. Refactor: 4-5 files need to read from typed `ReviewBridgeState.review_accepted` instead of calling `bridge_review_accepted(BridgeSnapshot)`.

Files: `status_projection_bridge_state.py:142`, `state.py:97`, `bridge_validation.py:108`, `handoff.py`, tests.

**3. Doctor surface as PROJECTION over the contract**

Do NOT make doctor another independent analyzer. Make it a projection over ReviewerRuntimeContract + ReviewerGateState + session truth. One surface, one source of truth.

**4. Startup ownership metadata**

Populate `startup_surface_tokens` on all 14 ContractSpec rows (2-3 tokens each, one-line per contract). Add `contract_ownership_map` to StartupContext so agents get ownership metadata at bootstrap, not by reading prose.

### Design rule

> typed state is authority, bridge is projection
> one owner per lifecycle, not distributed fragments
> doctor projects from the owner, doesn't independently analyze
> startup tells agents what exists, not just what's allowed

## Commit-Level Proof (for ChatGPT Pro — verify against commits, not file pages)

| What | Commit | Proof command |
|---|---|---|
| ReviewerRuntimeContract exists | `7e4d1c2` | `git show 7e4d1c2:dev/scripts/devctl/platform/runtime_state_contract_rows.py \| grep ReviewerRuntimeContract` |
| Doctor surface exists | `7e4d1c2` | `git show 7e4d1c2:dev/scripts/devctl/review_channel/reviewer_runtime_doctor.py \| head -5` |
| Bridge checks typed state first | `7e4d1c2` | `git show 7e4d1c2:dev/scripts/devctl/review_channel/bridge_validation_acceptance.py \| grep _runtime_review_accepted` |
| startup_surface_tokens populated | `7e4d1c2` | `git show 7e4d1c2:dev/scripts/devctl/platform/runtime_identity_contract_rows.py \| grep startup_surface_tokens` |
| Push uses publish_clear not bridge | `7e4d1c2` | `state.py` line 297: `review_gate_allows_push=bool(reviewer_runtime.publish_clear)` |
| Audit file matches code | `85be0aa` | This file corrected to reflect actual branch state |

## Next Steps (from ChatGPT Pro's latest review)

**The architecture is finally close. The remaining failure is execution, not modeling.**

ChatGPT Pro's directive: "Do one bounded pass focused on:"

1. **Daemon auto-start in governed launch** — `bridge_launch_control.py` must start publisher/supervisor when launching Codex. Currently neither governed nor manual launch starts the daemon.

2. **Crash restart via launchd** — Write a macOS `launchd` plist (~20 lines) that auto-restarts the follow daemon on exit. Wrap existing `follow_loop.py` stack.

3. **Register doctor in parser** — `reviewer_runtime_doctor.py` exists with 18 fields but `--action doctor` is not in `parser.py`. Add it.

4. **Add contract_ownership_map to StartupContext** — startup_surface_tokens are populated but StartupContext has no field that maps contracts to their ownership. Add bounded map built from ContractSpec registry.

5. **Prove one clean path and one rescue path before shipping:**
   - Clean: launch → daemon alive → review → ACK → push (all typed, no bridge prose)
   - Rescue: stale reviewer → daemon detects → rollover fires → terminal cleanup → fresh session → green

**Do NOT add more recovery recipes until daemon liveness is closed.**
