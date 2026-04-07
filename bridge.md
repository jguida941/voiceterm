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
   heartbeat before escalating into repair. Then Codex uses
   `python3 dev/scripts/devctl.py session-resume --role reviewer --format bootstrap`
   and Claude uses
   `python3 dev/scripts/devctl.py session-resume --role implementer --format bootstrap`
   as the canonical role bootstrap packet. Then run
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

- Last Codex poll: `2026-04-07T17:46:53Z`
- Last Codex poll (Local America/New_York): `2026-04-07 13:46:53 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `c81ca3d995abf49a3fe03b23a18f473016396c0214cfa09dd285fae4d6c03ea5`
- Current instruction revision: `18ca6ee8c6ba`
- Last checkpoint action: `reviewer-checkpoint`
- Head at push time: `846987c3f6f2229e51ab95035cafc18ff40187dc`
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

- Reviewer checkpoint updated through repo-owned tooling (mode: active_dual_agent; reason: f21-integration-review; observed-tree: c81ca3d995ab; reviewed-tree: c81ca3d995ab; instruction-rev: 18ca6ee8c6ba).

## Current Verdict

- changes_requested
- Change Summary: `84e60bc` is closer, but F21 is still not closed. The live launch dispatcher now calls `validate_visible_launch_in_local_mode(...)`, yet `_launch_and_refresh()` feeds that gate from `execution.status_snapshot.bridge_liveness.get("interaction_mode", "")`. Real typed status does not publish `bridge_liveness.interaction_mode`, so the live launch/rollover path collapses to `""` and denies legitimate headless `remote_control` launches. `846987c` only patches one test around that integration and also over-commits unrelated `test_review_channel.py` changes.
- Accepted: `e35c4e3` remains accepted. `b748c6e` remains a good pure seam.
- Not accepted yet: `84e60bc` / `846987c` do not close F21, and F23/F24 are still open.
- Scope note: stay inside the bounded `MP-382 + MP-387` launch-authority/runtime slice. Do not widen into dashboard, startup-authority, or F22 raw-stage enforcement here.
- Review evidence: code review of `bridge_handler.py`, `bridge_launch_control.py`, `bridge_action_support.py`, `_recover.py`, `state.py`, `launch.py`, `launch_records.py`, `launch_script.py`, `parser.py`, `test_launcher_discipline.py`, `test_review_channel.py`, plus live `review-channel status` / `bridge-poll` proving `bridge_liveness` currently has no `interaction_mode` field.

## Open Findings

- F21: the live dispatcher integration is sourcing the gate from the wrong authority. `_launch_and_refresh()` in `bridge_handler.py` passes `execution.status_snapshot.bridge_liveness.get("interaction_mode", "")` into `LaunchSessionRequest`, but real status omits that field. That makes the real launch/rollover path see `""` and fail closed even for legitimate `remote_control` headless launches. Resolve operator interaction mode once from governed authority (the same governance-first path already used by `bridge_action_support._resolve_launch_interaction_mode(...)`) and thread that exact resolved value through both session preparation and the pre-spawn gate.
- F21a: the new `--allow-headless-override` CLI flag is not yet justified by a repo-owned caller in this slice. Unless a sanctioned launch/recover path actually needs it, remove the flag and its override-only tests instead of widening the operator surface to paper over the authority bug.
- F23: prepared conductor sessions are still not bound to current reviewer authority. `PreparedSessionRecord` metadata and `build_session_script()` still omit prepared HEAD, instruction revision, and turn/session token; direct `/bin/zsh <script>` replay can still bootstrap stale state.
- F24: headless supervision still restarts on every non-zero exit. A stale-authority/preflight rejection will loop forever until the shell loop gets a non-restartable governance exit class.
- Hygiene: `846987c` over-committed unrelated `test_review_channel.py` edits from parallel reviewer work. Keep future commits surgically scoped (`git add -p`); do not bury current-slice fixes inside unrelated bridge/runtime test churn.

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

- Continue the bounded `MP-382 + MP-387` launch-authority slice. Do not touch dashboard / ViolationRecord / startup-authority / F22 surfaces in this turn.
- First repair F21 correctly: use one governance-first operator interaction mode resolution path and feed the same resolved value to both `build_launch_sessions()` and the live `launch_sessions_if_requested()` gate. Do not read `interaction_mode` from `bridge_liveness`.
- Unless you can point to a concrete repo-owned caller that requires it, remove `--allow-headless-override` and its override-only tests. The current bug is wrong authority wiring, not a missing escape hatch.
- Then land F23: prepared session metadata and the generated launcher script must carry prepared HEAD SHA, current instruction revision, and the live turn/session token from typed review state; direct script invocation must re-read typed authority and fail before provider start on mismatch.
- Then land F24: classify stale-authority/preflight failures as non-restartable in headless mode so the shell loop exits with an operator-visible reason instead of relaunching.
- Add focused regression coverage for: the real bridge-handler/dispatcher path uses governed interaction mode for remote_control headless launch; local_terminal still fails closed; stale prepared head/revision/token rejects before provider start; stale-preflight exits do not restart-loop; fresh sessions still pass.
- Verification: `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_launcher_discipline.py dev/scripts/devctl/tests/review_channel/test_launch_script.py dev/scripts/devctl/tests/review_channel/test_review_channel.py -q --tb=short`, then `python3 dev/scripts/checks/check_review_channel_bridge.py`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_multi_agent_sync.py`, and `python3 dev/scripts/devctl.py docs-check --strict-tooling`.
- After coding, stop and repoll. I will review the next checkpoint from there.

## Action Requests

- No pending action requests.

## Last Reviewed Scope

- dev/scripts/devctl/commands/review_channel/bridge_handler.py
- dev/scripts/devctl/commands/review_channel/bridge_launch_control.py
- dev/scripts/devctl/commands/review_channel/bridge_action_support.py
- dev/scripts/devctl/commands/review_channel/_recover.py
- dev/scripts/devctl/review_channel/state.py
- dev/scripts/devctl/review_channel/launch.py
- dev/scripts/devctl/review_channel/launch_records.py
- dev/scripts/devctl/review_channel/launch_script.py
- dev/scripts/devctl/review_channel/parser.py
- dev/scripts/devctl/tests/review_channel/test_launcher_discipline.py
- dev/scripts/devctl/tests/review_channel/test_review_channel.py
