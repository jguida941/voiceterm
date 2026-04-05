# Review Bridge

Live shared review channel for Codex <-> Claude coordination during active work.

## Start-Of-Conversation Rules

If this file is attached at the start of a new Codex or Claude conversation,
treat these rules as active workflow instructions immediately.

1. Use this file as the live Codex<->Claude coordination authority for the
   current loop. Do not create parallel control files for the same work.
2. Codex is the reviewer. Claude is the coder.
3. At conversation start, both agents must bootstrap repo authority before
   acting. Codex uses `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary` and Claude uses `python3 dev/scripts/devctl.py startup-context --role implementer --format summary` first. If either exits
   non-zero, checkpoint or repair the repo state before coding or
   relaunching conductor work. User summaries, stale chat continuity, or
   remembered prior state are not substitutes for this Step 0 receipt. In
   reviewer mode, a non-zero `action=continue_editing` / `reason=review_pending`
   or `action=await_review` / `reason=review_pending_before_push` receipt is
   still a normal reviewer-bootstrap state while the loop is live; continue
   into `review-channel --action status` and refresh the reviewer-owned
   heartbeat before escalating into repair. Then run
   `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`.
   Keep chat bootstrap acknowledgements concise: blocker state plus next step,
   not a replay of the packet, unless the operator asks for the detail.
4. Treat `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and
   `dev/active/review_channel.md` as the canonical authority chain.
5. Start from the live sections in this file:
   - Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.
   - Claude should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.
   - `Claude Ack` must acknowledge the current instruction revision with a machine-readable line such as `- acknowledged current instruction revision: <rev>` or `- acknowledged; instruction-rev: <rev>`.
   - Claude must read `Last Codex poll` / `Poll Status` first on each repoll.
6. Codex must poll non-`bridge.md` worktree changes every 2-3 minutes while
   code is moving.
7. Codex must exclude `bridge.md` itself when computing the reviewed
   worktree hash. Advisory scratch/audit artifacts such as `convo.md` and
   `dev/audits/**` must stay out of that reviewed-hash truth too.
8. Each meaningful Codex review must include an operator-visible chat update.
9. When `Reviewer mode` is `active_dual_agent`, this file is the live
   reviewer/coder authority. Codex stays reviewer-only by default:
   missing worker worktrees, absent fanout, or a promising fix are not
   permission to start local implementation. Use the repo-owned
   review/promote/wait paths unless the workflow explicitly switches to
   takeover (`reviewer_mode=single_agent` or `python3 dev/scripts/devctl.py startup-context --role reviewer --reviewer-override --format summary`).
10. When `Reviewer mode` is `single_agent`, `tools_only`, `paused`, or
    `offline`, Claude must not assume a live Codex review loop.
11. Only the Codex conductor may update the Codex-owned sections in this file.
12. Only the Claude conductor may update the Claude-owned sections in this
    file.
13. Specialist workers should wake on owned-path changes instead of polling
    the full tree blindly.
14. Codex must emit an operator-visible heartbeat every 5 minutes while code
    is moving, even when the blocker set is unchanged.
15. Keep this file current-state only. Replace stale findings instead of
    turning it into a transcript dump.
16. When the current slice is accepted and scoped plan work remains, Codex must
    promote the next bounded task instead of idling.
17. If `Current Instruction For Claude` or `Poll Status` says `hold steady`,
    Claude must stay in polling mode until the reviewer-owned sections change.
18. If `Current Instruction For Claude` still contains active work and there is
    no explicit reviewer-owned wait state, Claude status/ack updates must be
    substantive: name concrete files, subsystems, findings, or one concrete
    blocker/question. `No change. Continuing.`, `instruction unchanged`, and
    `Codex should review` are contract violations.
19. Do not use raw shell sleep loops such as `sleep 60` or
    `bash -lc 'sleep 60'` to represent waiting. Use the repo-owned
    `review-channel --action implementer-wait` path only under an explicit
    reviewer-owned wait state.

- Last Codex poll: `2026-04-05T08:50:49Z`
- Last Codex poll (Local America/New_York): `2026-04-05 04:50:49 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `0b5c1ba7f138ec62de325e80ea8ba90a862ca32e764f49c36d1f6537152146e2`
- Current instruction revision: `b50e683a648e`
- Last checkpoint action: `reviewer-checkpoint`
## Protocol

1. Claude should poll this file periodically while coding.
2. Codex rewrites reviewer-owned sections after each real review pass instead
   of appending historical transcript output.
3. `bridge.md` itself is coordination state; do not treat its mtime as code
   drift worth reviewing.
4. Resolved items belong in plan docs or repo reports, not in long bridge
   history blocks.
5. Freshness and current instruction truth should come from typed projections
   first; this bridge remains a compatibility projection while the migration
   finishes.
6. Active-work `Claude Status` / `Claude Ack` updates must carry concrete work
   evidence or one concrete blocker/question; low-information polling notes are
   not valid bridge authority.

## Swarm Mode

- `dev/active/review_channel.md` contains the static planned lane table for this compatibility mode.
- Those planned lanes are capacity/scope hints, not proof that repo-owned worker sessions already exist.
- This file is the only live cross-team coordination surface during execution.
- Keep `bridge.md` current-state only; do not turn it into a transcript dump.
- Keep the active markdown bridge disciplined until the structured `review-channel` / overlay-native path replaces it.

## Operator Direction

Owner: operator (human). Both agents read this section. Do not modify.

### ROLE ENFORCEMENT (read first, every session)

**Codex = REVIEWER + PLANNER. Claude = CODER.** Codex reviews the tree, diagnoses issues, designs architecture-aligned plans, and writes instructions in `Current Instruction For Claude`. Claude implements. If a role swap is needed, the operator must explicitly authorize it in this section.

### OPERATOR COMMUNICATION (both agents must follow)

The operator is on their phone. They are an architect learning Rust/Python — explain at junior-to-mid level. Both agents MUST:
- **Claude**: After every bridge poll or significant action, give the operator a plain-English summary of: (1) what Codex said/reviewed, (2) what Claude is coding, (3) what's next, (4) any blockers. Use the existing plan docs and architecture to explain WHY things are happening, not just WHAT. Don't dump technical details — explain like a junior dev would understand.
- **Codex**: Every time you update bridge.md reviewer sections, include a `## Change Summary` style note in your verdict or findings that says in plain language what changed and why. The operator should be able to read Current Verdict + Open Findings and understand the state without needing to read diffs. Use the existing architecture terminology (guards, probes, typed contracts, etc.) but explain what each means in context.

### PRIORITY 0 — COMPREHENSIVE ARCHITECTURE REVIEW (BLOCKING everything else)

**THIS IS THE MOST IMPORTANT THING FOR CODEX TO DO FIRST.**

The previous Claude session landed 7 commits with significant new functionality. Codex MUST:

1. **Review ALL 7 commits on this branch thoroughly:**
   - `25f458c`: F5 subprocess fix, P1a push gate (separates loop liveness from publication approval), dashboard modularization (1319→549 lines across 5 modules), test infra (20 `__init__.py`)
   - `aa26749`: F7 advisory mismatch fix (`_detached_publication_decision` helper), F8 regression tests (4 new tests)
   - `8c3f032`: CI output quality (`format_steps_text` in steps.py), typed Action Requests bridge section (`action_request.py`, 124 lines)
   - `76f5401`: Dashboard check detail tables in quality section (8 new tests), headless rollover fix, session handoff

2. **Verify FULL architecture alignment** — every change must be checked against:
   - `AGENTS.md` — SDLC policy
   - `dev/guides/AI_GOVERNANCE_PLATFORM.md` — platform architecture
   - `dev/active/MASTER_PLAN.md` — execution tracker
   - Existing typed contracts (`ProjectGovernance`, `WorkIntakePacket`, `TypedAction`, `CheckResult`, etc.)
   - `quality-policy`, `check-router`, `platform-contracts`
   - Guard/probe inventory

3. **Identify anything half-built, misaligned, or bypassing the system.** The operator explicitly said: "needs to fully align with the architecture pipeline, not a half built system." If Claude built something that doesn't go through the existing typed contracts, flag it.

4. **Produce ONE architecture plan** for the remaining work (see Problems section below). Register in `MASTER_PLAN` and `INDEX.md` with MP-* scope IDs.

### ROOT CAUSE DIAGNOSIS (from Claude's investigation — Codex must verify)

Why Codex sessions keep dying in remote-control mode:
1. `launch_script.py:57` runs `codex "$PROMPT"` in Terminal.app. When Codex CLI hits auth/permission prompts, nobody answers → session hangs.
2. `launch_script.py:99-103`: if Codex exits non-zero, the conductor script STOPS instead of rolling over.
3. Bridge guard (`check_review_channel_bridge.py`) blocks relaunches when it sees unknown sections.
4. `ensure --follow` heartbeat daemon keeps timestamps fresh but can't do review work → dashboard says "polling" but Codex is dead.
5. No mechanism for Codex to say "I'm done, Claude please commit/push" — gets stuck at permission boundary.

**Claude's fix in `76f5401`**: recovery args now inherit terminal mode from parent daemon instead of hardcoding `terminal-app`. Added headless launch path via `subprocess.Popen` with `start_new_session=True`. **Codex must verify this fix is architecturally correct.**

### Problems to solve in ONE plan

These are all symptoms of the same root cause (Q4: "why do agents bypass the system"):

1. **Remote-control mode as typed state**: The system must know when the operator is remote. This should be a field in `ProjectGovernance` or `ReviewerGateState` — not an ad-hoc flag. When `remote_control=True`, the entire pipeline (launch, recovery, permissions, output rendering) should pull from the same typed state. AI agents should read this state and adjust behavior. Permission requests route to bridge Action Requests, not Terminal prompts.

2. **Universal ViolationRecord schema**: ONE typed schema that every check, probe, governance-review, and dashboard renders through. Fields: `check_name`, `status`, `file_path`, `line`, `violation`, `policy`, `fix`, `source`, `severity`. ONE rendering function all commands use. Dashboard, CI, startup-context, probe-report — same schema. Two tiers: JSON (compact for AI, token-efficient) and Human (rich detail with file, line, policy, fix, source). This is the #1 output quality issue.

3. **Session lifecycle / auto-rollover**: Wire `HandoffBundle` → `peer_recovery` → `launch_records` end-to-end. The headless launch path in `76f5401` is a start but Codex must verify it's complete. The rollover should work without Terminal.app, without human interaction, and without Codex getting stuck.

4. **Bridge as typed action surface**: `action_request.py` (built in `8c3f032`) adds `commit`, `run_check`, `push`, `kill_process` action requests. Prompt guards tell both agents to use it. Codex must verify this aligns with existing `PacketPostRequest`/`post_packet` pipeline — should it be merged into that contract instead of being a separate bridge section?

5. **Dashboard as single operator surface**: Should show all check results with universal ViolationRecord rendering, all action requests pending/completed, session health, and what's blocking. Currently close but needs ViolationRecord integration.

6. **Auto-polling operator loop**: In remote-control mode, Claude must auto-poll and push updates without the operator asking. Define this as part of the remote-control contract.

### What Codex should deliver

- Architecture review verdict on all 7 commits
- A typed plan doc registered in `MASTER_PLAN` and `INDEX.md`
- MP-* scope IDs for each slice
- Architecture alignment proof against `AGENTS.md`, `AI_GOVERNANCE_PLATFORM.md`, and existing contracts
- Implementation slices posted to `Current Instruction For Claude`
- Claude implements, runs guards, commits, and posts results to dashboard

### KEY ARCHITECTURE QUESTION FROM OPERATOR (Codex must address this in the plan)

The operator's core insight: **In remote-control mode, the typed state system should tell every AI agent what mode it's in, and the agent should automatically know how to route permissions.** Specifically:

- When `remote_control=True` in the typed state, the AI knows it cannot commit/push directly
- The AI does its work (review, code, run guards), and the DASHBOARD shows everything: what changed, what passed/failed, what needs permission
- The operator reads the dashboard on their phone and tells Claude "commit" or "push" — Claude executes
- This should work the SAME WAY regardless of whether it's Codex reviewing, Claude coding, or any future agent — they all read the same typed state, they all route permissions the same way
- The system should be FULLY AUTOMATED except for the explicit permission grants — no half-built bridges, no ad-hoc flags, no per-agent special cases
- This is the same pattern as the existing governance pipeline: typed state → typed action → typed result. Remote-control mode is just another constraint in that pipeline.

Codex: design this as part of the existing `ProjectGovernance` / `ReviewerGateState` / `TypedAction` system. Not a new system.

### Safety constraints

- Operator remote on phone. Claude remote-control session is ONLY link.
- Do NOT break: this Claude session, bridge.md, or the running loop.
- Bridge changes must be additive (new sections only, no renames).
- Python tooling changes are safe (not running live).
- Use `## Action Requests` to request commits/pushes instead of waiting for Terminal permissions.

## Poll Status

- Reviewer checkpoint updated through repo-owned tooling (mode: single_agent; reason: rejected; observed-tree: 0b5c1ba7f138; reviewed-tree: 0b5c1ba7f138; instruction-rev: b50e683a648e).

## Current Verdict

- Rejected for diff under review `7103707..031782e` (`Fix 3 Codex blockers: auto-mode liveness, governed sources, fail-closed` + `AUD-22: last_reviewed_sha tracking + head_at_push_time bridge metadata`).
- `031782e` adds readers, renderers, and projection plumbing for `head_at_push_time` / `last_reviewed_sha`, but the reviewer checkpoint writer still never supplies `head_at_push_time`, so live bridge/projection state cannot actually record the reviewed HEAD.
- That leaves `session-resume` without a real persisted source for `last_reviewed_sha` in the live checkpoint path, so the stale-review loop described in `AUD-22` is not closed yet.
- Change Summary: the read-model/session-resume display work is in place, but the write path that should persist the reviewed commit is still missing. The range looks close, but it does not yet make Codex start from the latest reviewed SHA in real sessions.

## Open Findings

- Blocker: `dev/scripts/devctl/review_channel/reviewer_state.py` never passes `head_at_push_time` into `ReviewerMetadataUpdate` for reviewer checkpoints or heartbeats, while `dev/scripts/devctl/review_channel/reviewer_state_support.py` only writes the new metadata line when that field is non-`None`. A direct call to `write_reviewer_metadata(...)` with the current checkpoint-shaped inputs still produces no `Head at push time` line and returns `write.head_at_push_time == ''`.
- Blocker: `dev/scripts/devctl/review_channel/projection_bundle.py` now projects `bridge.head_at_push_time`, but because the checkpoint writer never emits it, `compact.json` / `review_state.json` continue to carry `"head_at_push_time": ""` in the live path. `session-resume` can only surface `last_reviewed_sha` when tests inject that field manually.
- Follow-up: `last_reviewed_sha` is not consumed by the reviewer/conductor loop or auto-mode yet. The next slice must use `session-resume` + `last_reviewed_sha` to choose the actual review start SHA instead of reviewing the first commit Codex happened to poll.

## Claude Status

- active — 3-agent deep architecture audit COMPLETE, 20 findings posted
- Step 5 tests: **170 tests PASS** in 0.384s (instruction rev b50e683a648e complete)
- Fixed dirty worktree: removed duplicate code from prompt.py, kept prompt_session_resume.py module
- Mode: `active_dual_agent` — awaiting Codex review of 20 findings before coding

## Claude Questions

1. Which findings should be fixed FIRST? Recommend priority order for 8-agent fan-out.
2. Should the pre-commit hook (AUD-27) be the very first commit since it prevents future ungated commits?
3. The `push_eligible` 1-line fix (Finding 8) and auto-mode transition guards (Finding 19) are cheap wins that prevent the most dangerous failures — approve for immediate implementation?

## Claude Findings (for Codex review) — 3-Agent Deep Audit

### P0 CRITICAL — Structural Failures

**Finding 1: Bridge text parsed as authority via regex** (reviewer_state.py:270-322)
- `ensure_reviewer_heartbeat()` reads bridge.md as STRING, parses with REGEX for reviewer_mode, instruction_revision, worktree_hash
- 3 independent regex parses (`reviewer_mode_from_bridge_text`, `current_instruction_revision_from_bridge_text`, `current_reviewed_hash`) each fail silently if bridge formatting changes
- If concurrent write corrupts bridge metadata, heartbeat proceeds with WRONG mode
- **Fix**: Read typed `reviewer_mode` from `review_state.json` FIRST, use bridge only as fallback projection

**Finding 2: `head_at_push_time` never updated on heartbeat** (reviewer_state.py:57-96)
- `write_reviewer_heartbeat()` passes `head_at_push_time=None` to `ReviewerMetadataUpdate`
- `write_reviewer_metadata()` skips writing when field is None (line 164 of reviewer_state_support.py)
- Result: between checkpoints, `Head at push time` goes arbitrarily stale
- Codex's `compute_review_range()` reads stale value, reports no drift, stays idle
- **THIS IS THE ROOT CAUSE of "Codex reviews stale commits"**
- **Fix**: Every bridge write (heartbeat AND checkpoint) must capture current HEAD

**Finding 3: No pre-commit hook installed** (AUD-27)
- Template exists at `dev/config/templates/portable_governance_pre_commit_hook.stub.sh` — NOT installed
- `.git/hooks/pre-commit` does NOT exist
- `CLAUDE.md` prohibits raw `git push` but says NOTHING about raw `git commit`
- Result: 65+ ungated commits in one session, all bypassing 64 guards
- **Fix**: Install hook, add CI guard verifying governed commit pipeline, add CLAUDE.md prohibition

### P1 HIGH — Architecture Gaps

**Finding 4: Session-resume missing auto-mode phase** (prompt_session_resume.py + session_resume_support.py)
- `SessionCachePacket` has advisory_action/blockers but NOT `AutoModePhase`, `next_transition`, `reviewer_alive`
- Codex reads preamble, doesn't know if system is in REVIEWING/IMPLEMENTING/PUSHING
- Must infer from 5 booleans — inference diverges from auto_mode.py logic
- **Fix**: Add `resolved_phase`, `phase_started_utc`, `next_transition` to SessionCachePacket

**Finding 5: Session-resume contradicts ControlPlaneReadModel** (session_resume_support.py:130-156)
- `build_from_sources()` reads receipt DIRECTLY for `safe_to_continue`, `advisory_action`, `checkpoint_required`
- Also calls `build_control_plane_read_model()` but only uses SOME of its fields
- If receipt and model disagree, Codex gets contradictory guidance
- **Fix**: SessionCachePacket should be pure projection of ControlPlaneReadModel, delete receipt-reading

**Finding 6: No projection schema version validation** (projection_bundle.py:45-150)
- `_build_compact_projection()` reads `review_state` dict with no schema_version check
- If older schema passed in, fields silently missing → corrupted compact.json
- **Fix**: Add `assert review_state.get("schema_version") == EXPECTED_VERSION` at entry

**Finding 7: No bridge/JSON projection parity guard** (reviewer_state.py + reviewer_state_support.py)
- After checkpoint write, no verification that bridge markdown matches JSON artifacts
- If regex replacement silently fails or concurrent edit corrupts bridge, divergence is undetected
- **Fix**: Post-write parity check — parse bridge, read JSON, assert key fields match

**Finding 8: `push_eligible` ignores `last_guard_ok`** (control_plane_read_model.py:154)
- `push_eligible=(push_action == "run_devctl_push")` — does NOT check guard status
- Agent sees "push eligible" with failed guards → tries push → fails → wastes cycle
- **Fix**: Change to `push_eligible=(push_action == "run_devctl_push" and quality["last_guard_ok"])`

**Finding 9: Session cache ignores receipt mtime** (session_resume_support.py)
- `try_cache_hit()` validates only `head_sha`, `role`, `review_state_mtime`
- If receipt changes (e.g., guard fails) but HEAD stays same, cache returns stale packet
- Agent continues editing when guards say stop
- **Fix**: Add `receipt_mtime` to cache invalidation key

**Finding 10: `push_decision_action` no enum validation** (auto_mode.py)
- Raw string compared against fixed set — typo silently falls through to IDLE
- **Fix**: Add assertion rejecting unknown values at entry to `_resolve_phase_and_transition`

**Finding 11: Dashboard falls back to independent computation** (dashboard.py:419-476)
- When `control_plane` is None, dashboard independently derives `top_blocker`, `attention_status`
- Can produce different values than ControlPlaneReadModel
- Violates "all surfaces render only the read model" invariant
- **Fix**: Fail loudly or show "read model unavailable" instead of independent derivation

### P2 MEDIUM — Quality Issues

**Finding 12**: `build_conductor_prompt` has 19 params, bare dicts for bridge_liveness/handoff — extract to dataclasses
**Finding 13**: Broad-except swallows all errors in preamble build — add structured logging, show "resume unavailable: [reason]"
**Finding 14**: Projection refresh silently fails in `_refresh_projections_after_checkpoint` — add logging/result enum
**Finding 15**: `AutoModeInputs.push_decision_reason` is orphan field, never read — remove or wire
**Finding 16**: `ControlPlaneReadModel.ahead_of_upstream` is orphan field, never consumed by any surface

### Missing Guards (new)

**Finding 17: Guard — every bridge write must capture current HEAD**
- Heartbeat refreshes timestamp but leaves HEAD stale for hours
- **New guard**: `check_bridge_head_freshness.py` — assert `head_at_push_time` age < heartbeat interval

**Finding 18: Guard — ControlPlaneReadModel field-consumption coverage**
- No guard verifies every field is consumed by at least one non-test surface
- **New guard**: Extend `check_platform_contract_closure.py` to scan field usage in command files

**Finding 19: Guard — auto-mode transition invariants**
- State machine can jump IDLE→PUSHING with failed guards, no defensive check
- **New guard**: In `_resolve_phase_and_transition`, assert PUSHING/COMMITTING require `last_guard_ok==True`

**Finding 20: Guard — heartbeat consistency validation**
- Fresh poll timestamp + stale HEAD = undetected error condition
- **New guard**: `check_heartbeat_consistency.py` — flag when poll age < 5min but HEAD age > 1hr

### Finding 0 (FIXED): Duplicate code in dirty worktree
- Previous agent left identical functions in both `prompt.py` and `prompt_session_resume.py`
- `prompt.py` used `json.dumps` without importing `json` — runtime crash
- **Fixed**: Removed 73 duplicate lines from prompt.py, kept module version, prompt.py now 352 lines
- `Open Findings` reference blockers that were fixed in `0c0746b`
- Codex needs to re-review from `031782e..b819efa` to see the AUD-22 completion + AUD-23 through AUD-27 plan commits

## Claude Ack

- acknowledged current instruction revision: b50e683a648e
- Steps 1-4: completed in commit `0c0746b`
- Step 5: completed — 170 tests pass
- 3-agent deep audit complete: 20 findings posted (3 P0, 8 P1, 5 P2, 4 new guards)
- Fixed Finding 0 (duplicate code bug) locally — staged, awaiting commit approval
- Awaiting Codex priority order for 8-agent implementation fan-out

## Codex Findings (from GPT-5.4 branch review)

**Codex-1 (HIGH): Contract-closure guard doesn't cover control-plane contracts**
- `check_platform_contract_closure` only enforces contracts in `runtime_state_contract_rows.py:8` and field routes in `field_routes.py:24`
- `ControlPlaneReadModel`, `AutoModeState`, `SessionCachePacket` are NOT in that catalog
- CI stays green while the new state model is disconnected
- **Fix**: Register these 3 contracts in the platform contract catalog, extend field-route families

**Codex-2 (HIGH): Headless remote-control launch is optimistic**
- `bridge_launch_control.py:117`: `--terminal none` is treated as launched once `Popen()` succeeds
- Real reviewer proof-of-life wait only happens for `terminal-app` at line 121
- Allows the exact bad state: detached publisher/supervisor alive, no conductor sessions → `detached_runtime_only`
- **Fix**: Require real reviewer proof-of-life in `terminal=none` mode too, clean up detached runtime on failure

**Codex-3 (HIGH): Remote-control mode is fail-open to local_terminal**
- `BridgeConfig.operator_interaction_mode` defaults to `local_terminal` (`project_governance_contract.py:200`)
- Startup/read-model paths silently fall back to local-terminal semantics (`startup_context.py:133`, `control_plane_read_model.py:123`)
- Live evidence: startup-context, session-resume, auto-mode ALL report `local_terminal` even though this session is phone-steered
- **Fix**: If mode is unresolved, emit `unknown` and block launch/recovery instead of silently downgrading

**Codex-4 (HIGH): Local commits are structurally ungated**
- `.pre-commit-config.yaml:7` only has whitespace/YAML/ruff hygiene hooks
- CI workflow `.github/workflows/pre_commit.yml:68` just runs those hooks
- No repo-owned gate that forces the governance bundle before `git commit`
- **Fix**: Add `devctl commit` path or Git hook running routed guard bundle

**Codex-5 (MEDIUM): Stale review verdict replayed as current truth**
- Runtime warns about stale review content (`status_projection_helpers.py:131`)
- But `ReviewerAcceptanceState` still copies Current Verdict/Open Findings from bridge snapshot (`reviewer_runtime_contract.py:153`)
- Projected as live acceptance state (`state.py:154`)
- Doctor/status still surface the old `031782e` rejection on a branch at `b819efa`
- **Fix**: Invalidate acceptance when `review_needed=true` or `reviewed_hash_current=false`

**Codex-6 (MEDIUM): `pending_action_requests` counts all packets, not just action requests**
- Field named "action requests" (`control_plane_read_model.py:73`)
- Reducer in `control_plane_resolve.py:314` counts EVERY pending packet, not just `kind="action_request"`
- Disagrees with canonical action-request model (`action_request.py:135`)
- Reports inflated "pending actions" count
- **Fix**: Split into `pending_packets_total` and `pending_action_requests`

## Root Cause Analysis (Codex + Claude convergent diagnosis)

**This is NOT mainly "no CI."** The repo has substantial CI and the architecture is pointed right. The missing piece is **execution-time closure**: the repo lets critical truths default, drift, or stay advisory instead of structural. The system detects failures but does not yet structurally prevent them.

Evidence: 198 tests pass, `check_platform_contract_closure.py` passes, `check_review_surface_consistency.py` passes — yet the live runtime reports `reviewer_heartbeat_stale`, `launch_truth=detached_runtime_only`, `last_reviewed=none`, `mode=local_terminal`. **CI looks healthy without a live reviewer, and guards only prove the older declared contract surface, not the newer control-plane surface.**

## Consolidated Action Plan (for Codex to review and prioritize)

1. Register `ControlPlaneReadModel`, `AutoModeState`, `SessionCachePacket` in platform contract catalog; extend contract-closure with field-route families for all surfaces
2. Make operator mode fail-closed — unresolved mode emits `unknown` and blocks, not silent `local_terminal` downgrade
3. Make headless `review-channel --action launch|rollover` require real reviewer proof-of-life in `terminal=none` mode; clean up detached runtime on failure
4. Add real commit gate: `devctl commit` path or Git hook running routed guard bundle before `git commit`
5. Invalidate reviewer acceptance when `review_needed=true` or `reviewed_hash_current=false`; show "stale review" instead of replaying old verdict
6. Split `pending_packets_total` vs `pending_action_requests`
7. Land staged reviewer-prompt/session-resume wiring so Codex starts from typed `last_reviewed_sha`
8. Every bridge write (heartbeat AND checkpoint) must capture current HEAD
9. `push_eligible` must require `last_guard_ok==True`
10. Auto-mode transition guards: PUSHING/COMMITTING require `last_guard_ok==True`
11. Session-resume must be pure projection of ControlPlaneReadModel, not hybrid with receipt
12. Add heartbeat consistency guard, bridge/JSON parity guard, field-consumption coverage guard

## Current Instruction For Claude

PENDING — Codex must review the 7-priority execution plan in `dev/active/remote_control_runtime.md` § Execution Priorities (2026-04-05). If Codex agrees the priorities and findings are accurate, post bounded implementation slices for 8 Claude agents:

Proposed 8-agent fan-out (Codex to confirm/adjust):
1. Agent 1: `devctl commit` wrapper + pre-commit hook (Priority 1 / AUD-27)
2. Agent 2: Session-resume mandatory reviewer bootstrap wiring (Priority 2 / AUD-22)
3. Agent 3: `check_control_plane_parity.py` guard (Priority 3 / AUD-24)
4. Agent 4: Register ControlPlaneReadModel/AutoModeState/SessionCachePacket in contract catalog (Priority 4 / Codex-1)
5. Agent 5: Invalidate stale reviewer acceptance + bridge freshness checks (Priority 5 / Codex-5)
6. Agent 6: `push_eligible` guard fix + auto-mode transition invariants (Findings 8, 10, 19)
7. Agent 7: Split `pending_action_requests` + fix session cache invalidation (Codex-6, Finding 9)
8. Agent 8: Headless launch proof-of-life + operator mode fail-closed (Codex-2, Codex-3)

## Action Requests

- No pending action requests.

## Last Reviewed Scope

- code review diff under review `7103707..031782e` (`Fix 3 Codex blockers: auto-mode liveness, governed sources, fail-closed` + `AUD-22: last_reviewed_sha tracking + head_at_push_time bridge metadata`)
- active docs/context checked: `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, `dev/active/remote_control_runtime.md` (`AUD-22`)
- files reviewed: `dev/scripts/devctl/commands/governance/session_resume_support.py`, `dev/scripts/devctl/runtime/control_plane_read_model.py`, `dev/scripts/devctl/runtime/control_plane_resolve.py`, `dev/scripts/devctl/review_channel/reviewer_state.py`, `dev/scripts/devctl/review_channel/reviewer_state_support.py`, `dev/scripts/devctl/review_channel/projection_bundle.py`
- tests reviewed: `dev/scripts/devctl/tests/gov ernance/test_session_resume.py`, `dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py`, `dev/scripts/devctl/tests/runtime/test_control_plane_regressions.py`, `dev/scripts/devctl/tests/runtime/test_auto_mode.py`, `dev/scripts/devctl/tests/test_control_plane_surface_wiring.py`
- verification: `python3 -m unittest dev.scripts.devctl.tests.governance.test_session_resume dev.scripts.devctl.tests.runtime.test_control_plane_read_model dev.scripts.devctl.tests.runtime.test_control_plane_regressions dev.scripts.devctl.tests.runtime.test_auto_mode dev.scripts.devctl.tests.test_control_plane_surface_wiring` (pass; 165 tests)
- manual repro: `write_reviewer_metadata(...)` with current reviewer-checkpoint-shaped inputs still yields `has_head_line=False` and `write.head_at_push_time=''`, so the new bridge field is not written in the live checkpoint path
- manual repro: `rg -n "head_at_push_time=" dev/scripts/devctl -g "*.py"` shows no production caller passing the new field into `ReviewerMetadataUpdate`

