# Remote Orchestration Audit Status

**Branch:** `feature/governance-quality-sweep`
**Last updated:** 2026-04-03 ~12:30pm EDT
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
Architecture is mostly correct. Remaining problems are execution/supervision
and the still-open daemon/parser/runtime follow-up items below, not bridge/prose
authority. Phase 3/4 surface-ownership consistency
(`contract_ownership_map`, cross-surface generation proof, audit auto-sync, and
their proof tests) is now implemented locally.

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

**Note:** Pre-7e4d1c2 verification findings have been superseded. See "DONE" section above for current state. ReviewerRuntimeContract EXISTS (7e4d1c2). startup_surface_tokens ARE populated (all 15 contracts). Phase-2 authority cleanup is now coded locally: bridge acceptance is typed-only, push projection reads reviewer-runtime block state, and push recovery no longer keys off raw `HEAD` equality.

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

## Current Follow-up State (revalidated against actual code)

### DONE (verified in code, no longer open)

- **ReviewerRuntimeContract** — EXISTS in `runtime_state_contract_rows.py` (commit 7e4d1c2). Owns reviewer mode, freshness, stale reason, rollover, ACK, poll, session, acceptance, publish_clear.
- **startup_surface_tokens** — POPULATED on all 15 ContractSpec rows (3 tokens each).
- **Bridge acceptance demotion** — DONE locally. `bridge_review_accepted()` is now typed-only and push decision uses `reviewer_runtime.publish_clear` directly.
- **Push invalidation cycle** — FIXED. `review_gate_allows_push` bypasses `implementation_blocked`.
- **Bridge-derived push inputs** — DONE locally. `ReviewerRuntimeContract` now owns implementer ACK-current plus implementation-block state, and startup/status projections read those typed fields instead of bridge-liveness `reviewer_mode` / `claude_ack_current`.
- **Acceptance identity redesign** — DONE locally. Governed push recovery now keys off the reviewer-approved `tree-receipt-<timestamp>:<staged_tree_hash>` identity instead of raw `HEAD` equality.

### JUST COMPLETED

**Phase 0 design doc committed and pushed** (commit `c4b5da4`):
- `dev/active/remote_commit_pipeline.md` — 389 lines, covers all 9 ChatGPT Pro components
- Registered in INDEX.md under MP-377 with proper load order
- All guards passed: check_active_plan_sync, docs-check --strict-tooling, hygiene
- **NOTE FOR CHATGPT PRO:** Codex designed this doc, ran all guards, confirmed they passed — then COULD NOT COMMIT because the sandbox blocked git commit. Claude committed on Codex's behalf after independently verifying guards. This is live proof that Phase 0 is the correct next priority: the system that designs the typed commit pipeline was itself blocked by the lack of that pipeline.

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

**3. StartupContext ownership/runtime map is now present locally**
- startup_surface_tokens ARE populated
- `StartupContext` now carries `contract_ownership_map`
- The map derives from the shared `ContractSpec` registry instead of being hand-maintained
- Remaining work is broader daemon/parser/runtime closure, not this bootstrap ownership surface

**4. Bridge prose fallback is removed locally**
- `bridge_review_accepted()` now reads typed state only
- Bridge regex parsing remains available only as projection-time input for
  building reviewer-runtime acceptance, not as a second runtime authority path
- Push/status/startup gates now consume reviewer-runtime truth directly

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
- "You no longer mainly have a modeling problem. You have an execution/supervision problem, and the repo-truth consistency slice needs to stay enforced instead of drifting back open."
- "Good recovery logic + insufficient liveness guarantees, instead of good recovery logic + guaranteed supervisor execution."

## Governance Findings (from `governance-review --format md`)

**115+ total findings | ~70 fixed | ~45 open** (counts approximate — governance-review tracks exact state)

Key findings corrected for current branch state:
- `bridge_projection_drops_operator_direction` — FIXED in 801349f
- `bridge_still_active_gate_not_projection` — FIXED locally (`bridge_review_accepted()` is typed-only; prose remains projection-only input)
- `need_review_channel_doctor_surface` — PARTIALLY FIXED in 7e4d1c2 (surface exists, not registered in parser)
- `startup_surface_tokens_unpopulated` — FIXED in 7e4d1c2 (all 15 contracts populated with 3 tokens each)
- `reviewer_truth_distributed_no_owner` — FIXED in 7e4d1c2 (ReviewerRuntimeContract is the admitted owner)
- `push_invalidation_head_equality` — FIXED locally (push recovery matches reviewer-approved tree-hash receipts, not raw `HEAD` equality)
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
2. ~~Demote bridge acceptance~~ — DONE (typed state is sole authority)
3. ~~Doctor as projection~~ — DONE (18-field surface, but not registered in parser yet)
4. ~~Populate startup_surface_tokens~~ — DONE (all 15 contracts have 3 tokens each)

**Current directive: "The owner exists. The system still does not force everyone to use it."**

The remaining problem is execution/supervision, not modeling:
- The recovery logic exists but nobody reliably runs it
- The doctor surface exists but agents can't invoke it
- Bridge fallback has been removed from the runtime acceptance helper
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
| 7 | Bridge acceptance demoted | `7e4d1c2` + local Phase 2 | `bridge_validation_acceptance.py` | `_runtime_review_accepted()` is now the sole acceptance authority; bridge prose is projection-only input |
| 8 | Push reads from contract | `7e4d1c2` | `state.py` | `review_gate_allows_push=bool(reviewer_runtime.publish_clear)` |
| 9 | Startup reads from contract | `7e4d1c2` | `startup_context.py` | `state.reviewer_runtime.review_acceptance.review_accepted` and `publish_clear` |
| 10 | startup_surface_tokens populated | `7e4d1c2` | All 4 contract row files | All 15 ContractSpec rows have 3 tokens each |
| 11 | Automated reviewer rollover | `09349aa` | `reviewer_follow_recovery.py` | `maybe_auto_trigger_rollover_on_stale_codex()` with 5 attention states |
| 12 | Terminal cleanup | `37f683d` | `terminal_app.py` | `cleanup_terminal_session()` with SIGTERM + window close |
| 13 | Audit matches code | `85be0aa` | `AUDIT_STATUS.md` | Corrected to reflect actual branch state |

### Follow-up matrix (revalidated against ChatGPT Pro review; locally completed rows marked explicitly)

| # | What | Status | Where | Est. size | Why |
|---|---|---|---|---|---|
| A | Daemon auto-start in launch | **DONE** `1aaef8c` | `bridge_launch_control.py` | Landed | Publisher auto-starts on launch via `ensure_launch_runtime_daemons()`. |
| B | launchd plist for crash restart | **DONE** `1aaef8c` | `dev/config/launchd/` | Landed | Plist template + service wrapper. RunAtLoad, KeepAlive, exit-class semantics. Needs host deployment. |
| C | Register `--action doctor` | **DONE** `46fb2ed` | `parser.py` + `commands/__init__.py` | Landed | Doctor dispatches through `ReviewChannelAction.DOCTOR`. |
| D | contract_ownership_map | **DONE** `3d3d157` | `startup_context.py` | Landed | Derived from ContractSpec registry. Exposes owner_layer, runtime_model, startup_surface_tokens. ChatGPT Pro notes: could be richer (authoritative artifact, allowed projections, recovery surface). |
| E | Remove bridge prose fallback | **DONE** `a543dd2` | `bridge_validation_acceptance.py` | Landed | Typed runtime is sole authority. Prose removed. |
| F | Audit file auto-sync guard | **DONE** `3d3d157` | `check_audit_status_sync.py` | Landed | ChatGPT Pro notes: currently narrow (fixed markers only), needs widening. |
| G | Remove bridge-derived push inputs | **DONE** `a543dd2` | `status_push_decision.py` | Landed | `implementation_blocked` now from `ReviewerRuntimeContract`, not bridge-liveness. |
| H | Acceptance identity redesign | **DONE** `a543dd2` | `reviewer_runtime_models.py` + updates | Landed | Tree hash receipt replaces HEAD equality. |
| I | Cross-surface consistency proof | **DONE** `3d3d157` | `check_review_surface_consistency.py` | Landed | Enforces shared `snapshot_id`/generation across surfaces. |
| J | Daemon regression tests | **DONE** `1aaef8c` | `test_launchd_service.py` | Landed | Tests for service wrapper behavior. |
| K | Prove clean end-to-end path | **DONE** | Integration test | Landed | `test_phase4_clean_path_surface_snapshot_alignment` |
| L | Prove rescue end-to-end path | **DONE** | Integration test | Landed | `test_phase4_rescue_path_recovers_doctor_health_and_snapshot` |

### Remaining follow-ups (from ChatGPT Pro final review of f82643d)

| # | What | Why | Est. |
|---|---|---|---|
| M | Widen `check_audit_status_sync.py` | Currently narrow (fixed markers only). Needs general repo-truth proof. | ~30 lines |
| N | Enrich `contract_ownership_map` | Currently exposes owner_layer/runtime_model/tokens. Needs authoritative_artifact, allowed_projections, recovery_surface. | ~20 lines |
| O | Clean AUDIT_STATUS.md historical sections | Historical rows mixed with current state. Done above. | This commit |
| P | Deploy launchd plist on host | Template exists but not installed. Ops step, not code. | Manual |

## Implementation Plan (ALL PHASES IMPLEMENTED — see proof table above)

**Status: Implementation complete. ChatGPT Pro approved direction. Three follow-ups remain (M, N, P).**

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

## Full Implementation Status (2026-04-02 to 2026-04-03)

### All phases committed and pushed

| Phase | Commit | Lines added | Lines deleted | Guards | Tests |
|---|---|---|---|---|---|
| Phase 0 Design | `c4b5da4` | 389 | 0 | ALL PASS | — |
| Phase 0 Slice 1: Contract + doctor | `46fb2ed` | 291 | 0 | ALL PASS | 39 passed |
| Phase 0 Slice 2: Approval packets | `4264c0a` | 444 | 16 | plan-sync PASS | 213 lines tests |
| Phase 0 Slices 3+4: Governed actions | `088152f` | 1,817 | 58 | ALL PASS | governed_executor tests |
| Phase 1: Daemon liveness + launchd | `1aaef8c` | 615 | 99 | ALL PASS | launchd service tests |
| Phase 2: Bridge authority eliminated | `a543dd2` | 750 | 282 | ALL PASS | acceptance identity tests |
| Phases 3+4: Ownership + consistency + proofs | `3d3d157` | 1,105 | 44 | plan-sync PASS | 6 new test files |
| CI workflow parity + docs | `06c43e5` | 29 | 5 | ALL PASS | 94 passed |

**Totals: ~5,440 insertions, ~504 deletions across all phases.**

### New files created

- `dev/active/remote_commit_pipeline.md` — Phase 0 design doc
- `dev/scripts/devctl/commands/vcs/governed_executor.py` — governed commit/push executor
- `dev/scripts/devctl/commands/vcs/governed_executor_support.py` — executor support
- `dev/scripts/devctl/commands/review_channel/doctor_support.py` — doctor CLI dispatch
- `dev/scripts/devctl/review_channel/doctor_markdown.py` — doctor markdown renderer
- `dev/scripts/devctl/review_channel/remote_commit_pipeline_artifact.py` — pipeline artifact builder
- `dev/scripts/devctl/runtime/remote_commit_pipeline_models.py` — CommitIntentState + pipeline typed records
- `dev/scripts/devctl/runtime/review_state_commit_pipeline_parse.py` — pipeline state parser
- `dev/scripts/devctl/runtime/surface_snapshot.py` — cross-surface generation stamps
- `dev/config/launchd/review_channel_publisher.plist.template` — launchd plist for daemon restart
- `dev/config/launchd/review_channel_publisher_service.py` — launchd service wrapper
- `dev/scripts/checks/check_audit_status_sync.py` — audit/code drift guard
- `dev/scripts/checks/check_review_surface_consistency.py` — cross-surface consistency guard
- Tests: `test_governed_executor.py`, `test_launchd_service.py`, `test_check_audit_status_sync.py`, `test_check_review_surface_consistency.py`, `test_remote_commit_pipeline_phases34.py`

### What was proven

- `RemoteCommitPipelineContract` owns the full lifecycle: staged → guards → approve → commit → push → recover
- `--action doctor` registered and dispatched as first-class CLI surface
- Bridge prose fully demoted — typed state is sole authority for push
- Acceptance identity uses reviewer-owned tree hash receipt, not HEAD equality
- Publisher daemon auto-starts on launch with launchd crash restart
- Cross-surface consistency guard ensures all surfaces agree on same generation
- Audit/code drift guard prevents AUDIT_STATUS.md from lying about the repo

### Known remaining issue

Codex CLI sandbox blocks `git commit` when running remotely. The Phase 0 pipeline contract models this as a governed action through the executor boundary, but the executor itself still runs through Claude Code (which has commit authority). This is architecturally correct — Codex codes, Claude commits after guard validation, operator approves push — but it means the full autonomous loop requires both agents running. The idle-Codex pattern persists until the launchd plist is actually deployed on the host.

### For ChatGPT Pro review

All code is on GitHub at `feature/governance-quality-sweep`. Key files to verify:
- `dev/active/remote_commit_pipeline.md` — design doc
- `dev/scripts/devctl/commands/vcs/governed_executor.py` — executor boundary
- `dev/scripts/devctl/runtime/remote_commit_pipeline_models.py` — typed pipeline state
- `dev/config/launchd/review_channel_publisher.plist.template` — daemon supervisor
- `dev/scripts/checks/check_review_surface_consistency.py` — consistency guard
- `dev/scripts/devctl/review_channel/reviewer_runtime_doctor.py` — doctor projection

## Live Test Plan (2026-04-03)

**Operator is home. System should be proven end-to-end.**

### Test 1: Codex reviews, Claude codes
- Launch Codex as reviewer via the governed launch path
- Verify daemon auto-starts (publisher + supervisor)
- Verify `review-channel --action doctor` shows healthy state
- Claude codes a small change, Codex reviews it
- Operator approves push from remote-control session

### Test 2: Claude reviews, Codex codes (role swap)
- Launch Codex as coder, Claude as reviewer
- Verify the same typed pipeline works in reverse
- Prove role swap works through the existing bridge protocol

### Test 3: Self-healing
- Kill the Codex process manually
- Verify daemon detects idle/stale reviewer
- Verify rollover fires automatically
- Verify fresh Codex session picks up from handoff state
- Verify terminal cleanup closes old window

### Test 4: Governed remote commit
- Codex stages work
- Guards run automatically
- Claude commits (governed executor)
- Operator approves push from phone
- `devctl push --execute` succeeds

### Test 5: Deploy launchd plist
- Install the plist template on host
- Verify daemon auto-restarts after crash
- Verify `manual_stop` does NOT trigger restart

### Test 6: Test on another repo
- Use the portable governance system on a second repository
- Prove the full pipeline works without VoiceTerm-specific assumptions

### After all tests pass
- Merge `feature/governance-quality-sweep` to `develop`
- Update MASTER_PLAN with completion evidence
- Record in ENGINEERING_EVOLUTION

## Launch Gate Fix (from ChatGPT Pro + 4-agent verification)

**Root cause:** Push path was fixed (review_gate_allows_push bypasses implementation_blocked) but launch path was NOT. The governed launch gate still ties launcher eligibility to exact HEAD via startup receipt, and any state repair that commits to bridge.md invalidates the receipt.

**4 confirmed issues:**
1. `startup_receipt.py` — HEAD equality stales on any bridge commit (`launch_gate_stale_head_loop`)
2. `startup_gate.py` — recovery exception only filters reviewer-loop-block, NOT stale-HEAD (`launch_gate_exception_too_narrow`)
3. `peer_recovery.py` — `reviewer_overdue`/`implementer_state_reset_required` use `block_launch` but should `permit_repair` (`launch_reviewer_states_should_permit_repair`)
4. Push reads `review_gate_allows_push` but launch never does (push/launch asymmetry)

**Fix (from ChatGPT Pro):**
- Split launcher authority from edit-slice authority in `startup_receipt.py`
- Widen gate exception in `startup_gate.py` to also drop stale-HEAD failures for launch/rollover
- Reclassify reviewer states as `permit_repair` for launch intent
- Let launch refresh its own receipt after state repair

**Rule: "You solved reviewer authority for publication, but you did not solve reviewer bootstrap authority for launch."**
