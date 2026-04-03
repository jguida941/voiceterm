# Remote Orchestration Audit Status

**Branch:** `feature/governance-quality-sweep`
**Last updated:** 2026-04-02 ~10:30pm EDT
**Purpose:** Temporary file for ChatGPT Pro review. Delete when done.

**NOTE FOR CHATGPT PRO:** If file page views look stale, verify against commits directly:
- Commit `650702b` = latest audit cleanup (current branch tip)
- Commit `7e4d1c2` = ReviewerRuntimeContract (46 files, 1569 lines)
- Use `github.com/jguida941/voiceterm/commit/7e4d1c2` to see the diff directly
- Phase 0 IS in the Implementation Plan section (see "Phase 0: Typed commit/push pipeline" below)

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

**Note:** Pre-7e4d1c2 verification findings have been superseded. See "DONE" section above for current state. ReviewerRuntimeContract EXISTS (7e4d1c2). startup_surface_tokens ARE populated (all 15 contracts). Bridge acceptance IS partially demoted (typed first, prose fallback).

## Concrete Next Steps (SUPERSEDED — see Implementation Plan below)

Items 1-3 below are DONE. See commit `7e4d1c2` proof table. Current work is Phase 0-4 in the Implementation Plan section.

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

**0. Remote-session commit flow (NEW — discovered during Phase 1 implementation)**

Codex CLI sandbox blocks `git commit` on `.git/index.lock`, showing a permission dialog that requires physical keyboard access. When the operator is remote, this blocks all progress.

**This is NOT a manual workaround. It must be a typed, automated pipeline using existing contracts:**

The entire flow — Codex stages → guards run → Claude validates → operator approves → commit → governed push — must be automated through the existing typed governance system. No manual guard runs, no ad hoc commits, no prose-based approval. Every step should flow through `ReviewerRuntimeContract`, `TypedAction`, `PacketPostRequest`, and the existing guard/probe stack.

**NEEDS DESIGN BY CODEX (Phase 0 — blocks all other phases):**

ChatGPT Pro's Phase 0 specification:

1. **Introduce a typed commit/push pipeline owner** — one repo-owned orchestration object modeling the lifecycle: `drafted/staged → guards_running → guards_passed/failed → operator_approval_pending → operator_approved/rejected → commit_pending → commit_recorded → push_pending → push_completed/push_blocked`. Lives under the same ownership domain as `ReviewerRuntimeContract`. Not bridge prose, not shell sequencing.

2. **Treat commit as a governed action** — Codex produces staged changes + intent. Guard bundle runs automatically. Claude/reviewer validates from typed outputs. Operator approval via review-channel typed packet. A governed executor performs commit/push only after typed preconditions pass. Returns `TypedAction → ActionResult`, not terminal text.

3. **Use `PacketPostRequest` for approval** — operator approval from phone is a typed packet through review-channel, not prose edits. The phone/dashboard emits an approval packet.

4. **Make remote-control read-mostly dashboard** — shows: reviewer runtime health, guard bundle status, staged diff summary, approval state, commit/push eligibility, recovery recommendation. Compatible with existing doctor/status projections. Remote terminal must NOT have invisible local prompts blocking progress.

5. **Promote doctor to first-class action** — phone dashboard needs `--action doctor` as the primary health command.

6. **Phase 0 must include supervisor ownership** — no typed commit/push path is valid unless the follow daemon is live and owned by architecture, not user ritual.

**Codex design doc must include:** pipeline owner + typed state, action graph (stage→guard→approve→commit→push→recover), reused contracts, new typed records needed, packet vocabulary for remote approval, executor boundary for commit/push, doctor/dashboard fields, fail-closed rules, migration from current ad hoc flow.

**Rule: No new prose authority. No shell-first path. No agent-specific shortcut. The repo owns the lifecycle.**

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
| G | Remove remaining bridge-derived inputs from push projection | NOT CODED | `status_push_decision.py` + `state.py` | ~20 lines | Push gate already uses typed `publish_clear`, but `implementation_blocked` still derives from bridge-liveness fields like `reviewer_mode` and `claude_ack_current`. Move those into `ReviewerRuntimeContract` first, then remove bridge dependency. |
| H | Acceptance identity redesign (tree hash receipt) | NOT CODED | `reviewer_runtime_models.py` + producer/projection/test updates | ~60 lines | Replace HEAD equality with reviewer-owned tree hash receipt. Extend existing rollover_id pattern from handoff.py. Touches models, projection, and startup. |
| I | Cross-surface consistency proof | NOT CODED | `dev/scripts/checks/` | ~50 lines | startup-context, status, and push can currently disagree because they independently call refresh_status_snapshot with no versioning. |
| J | Daemon regression tests | NOT CODED | `dev/scripts/devctl/tests/` | ~80 lines | Cover: absent at login, crash mid-review, stale config, duplicate start, heartbeat suppression, inactive no-op. |
| K | Prove clean end-to-end path | NOT TESTED | Integration test | TBD | launch → daemon → review → ACK → push (all typed, no bridge prose) |
| L | Prove rescue end-to-end path | NOT TESTED | Integration test | TBD | stale reviewer → daemon detects → rollover → cleanup → fresh session → green |

## Implementation Plan (ChatGPT Pro final review + corrections applied)

**Status: Conditionally approved for implementation. Phase 0 design must come first.**

### Phase 0: Typed commit/push pipeline (DESIGN FIRST — blocks everything)

Codex must produce a design doc before coding. No isolated fixes until the pipeline owner is specified.

**Design doc must include:**
- Pipeline owner and canonical typed state (`drafted/staged → guards_running → guards_passed/failed → operator_approval_pending → approved/rejected → commit_pending → commit_recorded → push_pending → push_completed/blocked`)
- Action graph: stage → guard → approve → commit → push → recover
- Which existing contracts are reused (`ReviewerRuntimeContract`, `TypedAction → ActionResult`, `PacketPostRequest`, guard bundles)
- Which new typed records are needed (likely 1-2)
- Packet vocabulary for remote approval (operator approval = typed packet, not prose)
- Executor boundary for commit/push in remote mode (governed action returning `ActionResult`, not terminal text)
- Doctor/dashboard projection fields for phone display
- Fail-closed rules
- Migration from current ad hoc flow

### Phase 1: Daemon liveness + doctor (after Phase 0 design is approved)

ChatGPT Pro corrections applied:

| Step | Item | File | Size | Correction |
|---|---|---|---|---|
| 1a | Publisher daemon auto-start | Actual launch/action router (not `bridge_launch_control.py` alone) | ~10 lines | Publisher is the persistent service; it already restarts reviewer_supervisor. Target the real owner surface. |
| 1b | launchd plist with exit-class semantics | `dev/config/` | ~30 lines | Must define restart behavior per exit reason: `timed_out` and `inactivity_timeout` restart, `manual_stop` does NOT restart, `output_error` restarts with backoff. |
| 1c | Doctor registration + daemon-liveness fields | `parser.py` + `commands/__init__.py` + `reviewer_runtime_doctor.py` | ~20 lines | Register `--action doctor`. Expand doctor to include publisher/supervisor running state, last stop reason, last heartbeat timestamps. |
| 1d | Daemon regression tests | `dev/scripts/devctl/tests/` | ~80 lines | Cover: absent at login, crash mid-review, stale config, duplicate start, heartbeat suppression, inactive no-op. |

### Phase 2: Eliminate bridge/prose authority (after Phase 1 proven)

ChatGPT Pro corrections applied:

| Step | Item | File | Size | Correction |
|---|---|---|---|---|
| 2a | Eliminate markdown/prose authority from push | `status_push_decision.py` + move needed fields into `ReviewerRuntimeContract` | ~30 lines | Don't cut typed bridge-state inputs that carry required runtime facts. Move remaining needed fields (reviewer_mode, claude_ack_current) into the contract first, then remove prose dependency. |
| 2b | Remove bridge prose fallback | `bridge_validation_acceptance.py` | ~10 lines | Typed state becomes sole authority. |
| 2c | Acceptance identity redesign | `reviewer_runtime_models.py` + producer/projection/tests | ~60 lines | Tree hash receipt extending rollover_id pattern. |
| 2d | Fix stale docstring in reviewer_follow.py | `reviewer_follow.py` | 1 line | Still says "report-only supervisor status" — misleading about module authority. |

### Phase 3: Surface ownership + consistency (after Phase 2 proven)

ChatGPT Pro corrections applied:

| Step | Item | File | Size | Correction |
|---|---|---|---|---|
| 3a | contract_ownership_map in StartupContext | `startup_context.py` | ~15 lines | Derive from ContractSpec registry, not hand-maintained. |
| 3b | Shared snapshot_id/generation stamp | Typed projections | ~20 lines | All surfaces built from same generation. Not just a check script — a real versioning token. |
| 3c | Cross-surface consistency proof | `dev/scripts/checks/` | ~50 lines | Assert all surfaces were built from same generation. |
| 3d | Audit file auto-sync guard | `dev/scripts/checks/` | ~30 lines | Prevents drift. |

### Phase 4: Prove it works (after Phase 3 proven)

| Step | Item | What |
|---|---|---|
| 4a | Clean path test | launch → daemon → review → tree-hash receipt → push (all typed, zero bridge, zero prose) |
| 4b | Rescue path test | stale reviewer → daemon detects → rollover → cleanup → fresh session → doctor green |
| 4c | Surface convergence test | doctor + startup + push gate + bridge projection all queried, assert same generation stamp |
| 4d | Remote-session test | phone → typed approval packet → governed commit → governed push (no physical keyboard needed) |

**Phase order: 0 → 1 → 2 → 3 → 4. Each phase closes a precondition the next depends on. No skipping.**

**Rule: No new prose authority. No shell-first path. No agent-specific shortcut. The repo owns the lifecycle.**
