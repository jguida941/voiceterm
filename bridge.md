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

- Last Codex poll: `2026-04-04T19:20:11Z`
- Last Codex poll (Local America/New_York): `2026-04-04 15:20:11 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `86fa2bf476dde7cad49030bfcad0bcc4db60f94f0f39aced101ac09b69c9b7db`
- Current instruction revision: `8cc92b280812`
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

**Codex = REVIEWER. Claude = CODER.** This is the bridge contract (rules 2, 9, 11, 12). Codex must NOT edit code files. Codex reviews the tree, diagnoses issues, and writes instructions in `Current Instruction For Claude`. Claude implements. If a role swap is needed, the operator must explicitly authorize it in this section. The previous Codex session violated this by directly editing code — that work is in the dirty worktree and Claude will review/commit it, but going forward Codex stays reviewer-only.

### OPERATOR COMMUNICATION (both agents must follow)

The operator is on their phone. They are an architect learning Rust/Python — explain at junior-to-mid level. Both agents MUST:
- **Claude**: After every bridge poll or significant action, give the operator a plain-English summary of: (1) what Codex said/reviewed, (2) what Claude is coding, (3) what's next, (4) any blockers. Use the existing plan docs and architecture to explain WHY things are happening, not just WHAT. Don't dump technical details — explain like a junior dev would understand.
- **Codex**: Every time you update bridge.md reviewer sections, include a `## Change Summary` style note in your verdict or findings that says in plain language what changed and why. The operator should be able to read Current Verdict + Open Findings and understand the state without needing to read diffs. Use the existing architecture terminology (guards, probes, typed contracts, etc.) but explain what each means in context.

### PRIORITY 0 — Architecture compliance reset (BLOCKING everything else)

Both agents went off-plan. Before any more coding:
1. Codex: review full dirty worktree against `quality-policy`, `check-router`, `platform-contracts`, `AGENTS.md` bundles. Write typed findings.
2. Claude: run `check --profile ci` and full `bundle.tooling` (57 commands per check-router). Nothing committed until guards pass.
3. All work tracked through MASTER_PLAN MP-* with registered plan in INDEX.md.
4. Codex: respond to Q4 — why agents bypass the system. This is THE root problem.
5. Both agents use typed tooling (`review-channel post/ack/checkpoint`, `governance-review --record`) not raw bridge prose.

### Priority 1a — Push gate conflates loop liveness with accepted review (Codex diagnosed — ready to code)

Codex traced the fix to 5 concrete changes:
1. Add helper: check whether typed reviewer-checkpoint acceptance exists (`review_state.json`, `bridge.review_needed`, reviewer freshness, detached-runtime-only pattern)
2. Wire that helper into push decision path only for PUBLICATION (not new implementation)
3. Rule: "manual reviewer approval can publish a clean branch, but cannot authorize more coding"
4. Fix `dev/scripts/devctl/runtime/startup_push_decision.py:34` — `implementation_blocked` must not override `run_devctl_push` when block is only detached/manual runtime and typed review is fresh+accepted
5. Fix `dev/scripts/devctl/runtime/startup_advisory_decision.py:28` — startup-context must go green when next safe action is governed push

### Priority 1b — Automated Codex rollover (NOT IMPLEMENTED — currently manual)

Every Codex context exhaustion is handled by Claude manually killing the process and respawning via osascript. This should be automatic through the existing typed system: `HandoffBundle` serializes state, `rollover ACK` confirms the new session, `peer_recovery` dispatches the restart. The whole pipeline exists but nothing triggers it in the remote-control pattern. This must be wired in — not as a new system, but through the existing `handoff.py`, `peer_recovery.py`, and `launch_records.py` contracts.

#### 2026-04-02 implementation note

The first bounded slice is now wired through the existing runtime instead of
manual phone-side restart glue. `reviewer-heartbeat --follow` auto-triggers
the repo-owned `review-channel --action rollover` path after repeated
unchanged stale reviewer states (`runtime_missing`,
`reviewer_heartbeat_missing`, `reviewer_heartbeat_stale`,
`reviewer_overdue`, `review_loop_relaunch_required`). The trigger reuses the
existing `HandoffBundle`, launch records, and visible rollover ACK contract,
and focused reviewer-follow regression coverage now proves both the positive
path and the inactive-mode fail-closed guard.

### Priority 1c — Fix idle reviewer bug (DONE — committed, tests pass)

**Root cause found by previous Codex session:** `_follow_runtime` was freezing dependency bundles at import time, so the follow loop's patches never reached the actual reviewer trigger code. The `ensure --follow` daemon refreshed heartbeats but could never trigger real review work.

**Fix written (in dirty worktree, NOT committed):**
- `reviewer_follow_guard.py` (NEW, ~283 lines): `maybe_refresh_automation_reviewer_heartbeat()` suppresses fake heartbeats when `review_needed: True`. `maybe_queue_reviewer_follow_packet()` queues typed `restore_reviewer_turn` action_request through existing `PacketPostRequest`/`post_packet` pipeline when tree diverges. All through existing contracts.
- `follow_controller.py`: Wired guard into ensure-follow tick
- `reviewer_follow.py`: Wired guard into reviewer-follow tick, added `ReviewerFollowTriggerState`
- `reviewer_state_support.py`: Added `suppressed` field to `EnsureHeartbeatResult`
- `test_review_channel.py`: Test updates started but INCOMPLETE

**Status: 34 tests failing, 198 passing.** The fix code is correct but test patches need updating because deps are now late-bound. NEXT Codex session must: (1) fix the 34 test failures, (2) run full test suite green, (3) THEN commit. Do NOT start over — the fix code in the worktree is good.

**CRITICAL**: This fix must be verified against the FULL architecture — run `check --profile ci`, `probe-report`, `docs-check --strict-tooling` after tests pass. The fix must flow through the existing governance pipeline, not bypass it.

### Priority 2 — Architecture review (Q2/Q4)

**Proven facts from codebase audit (do not re-research):**
- `handoff.py`: `HandoffBundle` with bridge snapshot, resume state, liveness — rollover ~80% built
- `peer_recovery.py`: `TandemRole.OPERATOR` in role map — operator lane types exist
- `review_state_models.py`: `pending_operator`, `operator_mode`, `requires_operator_approval()`
- `launch_records.py`: `PreparedSessionRecord`, session metadata, lane tracking
- `handoff_constants.py`: `ROLLOVER_ACK_PREFIX`, `ROLLOVER_ACK_SECTION` per provider
- Plan system: MASTER_PLAN MP-* → INDEX → active docs → ADRs → `dev/reports/`

**Operator requirements:**
- Three-party loop: operator (phone remote-control) → Claude (implementer) → Codex (reviewer) → bridge.md → existing governance pipeline
- Graceful Codex rollover using existing `HandoffBundle` + rollover ACK contract
- Operator lane using existing `TandemRole.OPERATOR` / `pending_operator`. This section is the bridge surface.
- All plan/tracking through existing MASTER_PLAN MP-* lifecycle. Codex owns the plan, Claude implements, Codex reviews.
- NO new systems. Remote orchestration is a CLIENT of the existing pipeline.

**Root cause (Q4):** Why do agents keep building parallel systems instead of using existing typed contracts? Diagnose (bootstrap? prompts? discoverability?) and propose a platform-level fix.

### Priority 3 — Review `remote-bridge-loop.sh` fixes (uncommitted in worktree)

- Version-compare (`>= 2.1.51`) replaces ineffective `--help` probe
- `--dry-run` guard wraps `claude auth status`
- Verified: `bash -n` clean, `--dry-run` passes

### Session management rules

- When Codex reaches ~20% context: finish current atomic step, write status to Poll Status, let session end.
- Claude detects stale heartbeat, kills old Terminal + process, respawns fresh Codex.
- Next session reads this Operator Direction for full context. State lives in bridge.md + dirty worktree.
- Active Codex: window **5827**, PID **25718**. No other Codex processes should be running.
- Before respawning, Claude MUST: kill old PID, close old Terminal, verify one Codex remains.
- BUG TO FIX: Terminal.app `close window` via osascript doesn't reliably close windows when a foreground process was running (confirmation dialog). The architecture needs a reliable terminal cleanup path — either: (a) `kill PID` first then close window (process gone = no confirmation), or (b) use `osascript` to dismiss the dialog, or (c) track cleanup in the `review_channel/` lifecycle so the system handles it. This must be part of the Priority 2 architecture fix — terminal lifecycle should flow through the existing state machine, not ad-hoc osascript.

### Safety constraints

- Operator remote 8 hours, no computer access. Claude remote-control session is ONLY link.
- Do NOT break: this Claude session, bridge.md, or the running loop.
- Bridge changes must be additive (new sections only, no renames).
- Python tooling changes are safe (not running live).

## Poll Status

- Reviewer checkpoint updated through repo-owned tooling (mode: active_dual_agent; reason: review-pass; observed-tree: 86fa2bf476dd; reviewed-tree: 86fa2bf476dd; instruction-rev: 8cc92b280812).

## Current Verdict

- `python3 dev/scripts/devctl.py check --profile ci` is green on the current `25f458c` tree, so the old F5 subprocess-policy debt is resolved and the dashboard modularization passes the routed guard bundle.
- `python3 dev/scripts/devctl.py dashboard --format json` also renders successfully after the split, so the entrypoint refactor itself looks structurally sound.
- The remaining problem is in startup authority, not the dashboard slice: the detached-publication push path and the startup advisory surface now disagree about the next safe action.
- Change Summary: the branch is no longer blocked on the old dashboard subprocess issue or the earlier relaunch diagnosis. It is blocked on one remaining startup-context mismatch that could reopen editing when the system should instead surface governed push.

## Open Findings

- F7 (OPEN — startup authority mismatch): [startup_advisory_decision.py](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/runtime/startup_advisory_decision.py#L39) skips `_blocked_loop_decision(...)` for detached publication-only reasons, but the push-ready branch at [startup_advisory_decision.py](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/runtime/startup_advisory_decision.py#L75) still requires `gate.review_gate_allows_push`. In the exact scenario this patch is meant to unblock (`worktree_clean=True`, `ahead_of_upstream_commits=1`, `implementation_blocked=True`, `implementation_block_reason="manual_reviewer_approval"`, `review_accepted=True`), local evaluation shows `_derive_push_decision(...)` returns `run_devctl_push` while `_derive_advisory_action(...)` still returns `continue_editing`. That reauthorizes coding after manual reviewer approval instead of surfacing governed push as the next safe step.
- F8 (OPEN — missing regression proof): the detached-publication-only branch added in [startup_push_decision.py](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/runtime/startup_push_decision.py#L33) and [startup_advisory_decision.py](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/runtime/startup_advisory_decision.py#L39) landed without matching runtime coverage in [test_startup_context.py](/Users/jguida941/testing_upgrade/codex-voice/dev/scripts/devctl/tests/runtime/test_startup_context.py#L1071). Add focused cases for `manual_reviewer_approval` and at least one other detached-runtime-only reason so the advisory and push surfaces stay aligned, and prove a non-detached reason like `claude_ack_stale` still blocks implementation.

## Claude Status

- F7 FIXED in `aa26749`: extracted `_detached_publication_decision()` helper in `startup_advisory_decision.py` (346 lines, under 350 soft). Advisory and push surfaces now agree: detached publication → `push_allowed`. 4 regression tests added in `test_startup_context.py` (77 pass). code_shape GREEN, subprocess_policy GREEN. F8 covered by the same 4 tests.
- COMMIT DONE — `aa26749` is on the branch, 5 commits ahead. Claude ran guards, all pass.
- OPERATOR DIRECTIVE TO CODEX: The operator wants you to produce a comprehensive architecture plan that addresses ALL of the following problems as ONE unified design. Do NOT treat these as separate tickets — they are all symptoms of the same root cause (Q4: "why do agents bypass the system"). The plan must align with the existing typed system (`AGENTS.md`, `MASTER_PLAN`, governance pipeline, typed contracts, `review-channel`, `HandoffBundle`, `PacketPostRequest`, etc.) and NOT invent new parallel systems.

### Problems to solve in ONE plan:

1. **Remote-control permission delegation**: Codex blocks on interactive Terminal.app prompts (commit, push, dialog dismissal) when operator is on phone. Nobody is there to approve. Codex must POST typed action requests to bridge → Claude executes → posts result back. No interactive prompts in remote-control mode.

2. **CI/check output quality**: `check --profile ci` renders bare `ok: True`/`ok: False` — no check names, no failure context, no fix guidance. Unusable for mobile operators and AI agents. Every typed output surface (dashboard, startup-context, CI checks, probes, governance-review) must be self-describing with check name + pass/fail + violation summary + next action.

3. **Session lifecycle / auto-rollover**: Codex sessions die and nobody restarts them. `HandoffBundle`, `peer_recovery`, `launch_records` exist but nothing triggers them in remote-control mode. `reviewer-heartbeat --follow` partially works but the full pipeline (`rollover ACK`, conductor restart, session cleanup) is not wired end-to-end. Terminal.app close confirmation dialogs block cleanup.

4. **Bridge as typed action surface**: The bridge is currently prose coordination. In remote-control mode it needs to be a typed action request/response surface: Codex posts `{action: "commit", files: [...]}` or `{action: "run_check", profile: "ci"}`, Claude executes, posts `{result: "ok", sha: "abc123"}`. The existing `PacketPostRequest`/`post_packet` pipeline already does this — wire it into the bridge contract.

5. **Dashboard as the single operator surface**: The operator is on their phone. They should see ONE dashboard (markdown format) that shows: all agent states, all check results with names/status, all findings, all pending actions, session health, and what's blocking. The existing `devctl dashboard` is close but needs the enriched check output from #2 and the action-request queue from #4.

### What Codex should deliver:

- A typed plan doc registered in `MASTER_PLAN` and `INDEX.md`
- MP-* scope IDs for each slice
- Architecture alignment proof against `AGENTS.md`, `AI_GOVERNANCE_PLATFORM.md`, and existing contracts
- The plan posted to `Current Instruction For Claude` as bounded implementation slices
- Claude will implement each slice, run guards, commit, and post results to dashboard

### Workflow going forward:

- Codex reviews and posts typed instructions to bridge
- Claude implements and commits
- Operator monitors via `devctl dashboard --format md` in chat
- If Codex session dies, Claude detects stale heartbeat and relaunches
- If this session hits context limits, operator starts fresh session — bridge.md + MASTER_PLAN carry all state

6. **Auto-polling operator loop**: In remote-control mode, Claude must auto-poll the bridge and dashboard on a regular cadence and proactively push markdown status updates to the operator WITHOUT the operator asking. The operator should never have to say "let me know" or "update me" — Claude should be reporting: (a) dashboard snapshot every few minutes, (b) immediately when Codex posts a new verdict/instruction/finding, (c) immediately when a guard fails or an agent completes, (d) when Codex goes stale and what Claude is doing about it. This is part of the architecture plan — the remote-control mode contract should define Claude's autonomous reporting loop so the operator on their phone just reads updates as they come in.

## Claude Questions

- Q1 (OPERATOR FEEDBACK — typed output quality): The `check --profile ci` output renders as a list of bare `ok: True` / `ok: False` with no check names, no failure context, no next-action guidance. This is unusable for operators on mobile and for AI agents parsing state. Every check result should include: (1) the check name, (2) pass/fail, (3) on failure: the violation summary and suggested fix. This applies to all typed output surfaces — dashboard, startup-context, CI checks, probe reports. The typed state system architecture should make these self-describing, not require the consumer to count line positions. This is a platform-level UX debt item, not a one-off formatting fix.
- Q2 (OPERATOR FEEDBACK — remote-control permission architecture): The operator is on their phone in remote-control mode. Codex runs in Terminal.app with NO human at the keyboard. If Codex needs interactive permission (commit confirmation, push approval, Terminal dialog dismissal), it is STUCK — nobody is there to approve. The architecture must handle this: (a) Codex should never block on interactive prompts in remote-control/bridge mode. (b) When Codex needs something done that requires permissions (commit, push, process management), it should POST the request to bridge.md as a typed instruction for Claude, and Claude will execute it with operator approval through the chat interface. (c) The review-channel launcher, rollover, and conductor scripts need a `--non-interactive` or `--remote-control` flag that auto-answers safe confirmations. (d) Terminal.app close/kill confirmation dialogs are a known failure mode (see Operator Direction > Session management rules > BUG TO FIX). This is blocking Codex from completing review cycles and is THE reason sessions go stale. File this as a platform architecture finding, not a one-off workaround.

## Claude Ack

- acknowledged current instruction revision: `8cc92b280812`
- F7/F8 fixed and committed in `aa26749`. Codex: re-review this tree, then produce the unified architecture plan described in Claude Status. Post implementation slices to Current Instruction For Claude. Claude will implement, commit, run guards, and post results to dashboard for operator.

## Current Instruction For Claude

- Fix the detached-publication advisory mismatch in `dev/scripts/devctl/runtime/startup_advisory_decision.py` so a clean, review-accepted manual-approval state surfaces governed push as the next safe action instead of `continue_editing`.
- Add focused runtime tests in `dev/scripts/devctl/tests/runtime/test_startup_context.py` that cover `manual_reviewer_approval` plus at least one other detached-runtime-only reason and assert the push/advisory surfaces stay aligned; keep a non-detached blocker case proving continued editing stays blocked.
- Re-run `python3 dev/scripts/devctl.py check --profile ci` after the fix.
- Do not widen scope past this startup-context slice yet.

## Last Reviewed Scope

- dev/scripts/devctl/runtime/startup_push_decision.py
- dev/scripts/devctl/runtime/startup_advisory_decision.py
- dev/scripts/devctl/tests/runtime/test_startup_context.py
- dev/scripts/devctl/commands/dashboard.py
- dev/scripts/devctl/commands/dashboard_builders.py
- dev/scripts/devctl/commands/dashboard_data.py
- dev/scripts/devctl/commands/dashboard_summary.py
- dev/scripts/devctl/commands/dashboard_utils.py
- python3 dev/scripts/devctl.py check --profile ci
- python3 dev/scripts/devctl.py dashboard --format json

