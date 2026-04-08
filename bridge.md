# Review Bridge

Live shared review channel for Codex <-> Claude coordination during active work.

## Start-Of-Conversation Rules

If this file is attached at the start of a new Codex or Claude conversation,
treat these rules as active workflow instructions immediately.

1. Use this file as the live Codex<->Claude coordination authority for the
   current loop. Do not create parallel control files for the same work.
2. Codex is the reviewer. Claude is the coder.
3. At conversation start, both agents must bootstrap repo authority before
   acting. Codex uses `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary` and Claude uses `python3 dev/scripts/devctl.py startup-context --role implementer --format summary` first.
   If Claude's receipt exits non-zero, checkpoint or repair the
   repo state before coding or relaunching conductor work.
   If Codex's receipt exits non-zero, read the summary fields
   before widening scope. `action=continue_editing` /
   `reason=review_pending` and `action=await_review` /
   `reason=review_pending_before_push` are normal reviewer-bootstrap
   states while the collaboration lane is still live; continue bootstrap,
   poll `review-channel --action status`, and refresh the reviewer-owned
   bridge heartbeat before attempting repair. Treat only
   `action=repair_reviewer_loop`, checkpoint/budget blockers, or typed
   review-channel status showing stale/non-live reviewer runtime as a
   repair or relaunch boundary.
   User summaries, stale chat continuity, or
   remembered prior state are not substitutes for this Step 0 receipt.
   Then Codex uses `python3 dev/scripts/devctl.py session-resume --role reviewer --format bootstrap` and Claude uses
   `python3 dev/scripts/devctl.py session-resume --role implementer --format bootstrap` as the canonical role bootstrap packet.
   Then run
   `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`.
   Keep chat bootstrap acknowledgements concise: blocker state plus next step,
   not a replay of the packet, unless the operator asks for the detail.
4. Treat `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and
   `dev/active/review_channel.md` as the canonical authority chain.
5. Start from the live sections in this file:
   - Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.
   - Claude should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.
   - `Last Codex poll` remains the reviewer-heartbeat compatibility field and `Claude Status` / `Claude Ack` remain the implementer-owned compatibility sections until native role-labeled bridge headings land.
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

- Last Codex poll: `2026-04-08T09:37:27Z`
- Last Codex poll (Local America/New_York): `2026-04-08 05:37:27 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `dc26a95439cc29497a022efb47baadb0162dc0d2223c5d23caeb8226fdf48e5b`
- Current instruction revision: `d4254a629be3`
- Last checkpoint action: `reviewer-checkpoint`
- Head at push time: `483df5b8cc66c5bbe01d4477cbe01665a28d7498`
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

- Reviewer checkpoint updated through repo-owned tooling (mode: active_dual_agent; reason: review-loop-relaunch-required; observed-tree: dc26a95439cc; reviewed-tree: dc26a95439cc; instruction-rev: d4254a629be3).

## Current Verdict

- changes_requested
- Change Summary: the accepted MP-381 parity slice at `HEAD` still stands, but the reviewer runtime itself is not live. Typed status shows `launch_truth=hybrid_claude_only` with no live repo-owned Codex conductor session, so the markdown bridge is not trustworthy as the active dual-agent authority until the repo-owned loop is relaunched.
- Change Summary: after that runtime repair, the content blocker is still the same off-scope relaunch-precedence dirty set. The accepted `dev/active/remote_control_runtime.md` amendment is mixed with a separate 9-file diff that still needs its own scoped instruction before commit or push.

## Open Findings

- F0 (blocking): `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary` now fails closed with `action=repair_reviewer_loop` / `reason=review_loop_relaunch_required`, and `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json` reports `launch_truth=hybrid_claude_only`, `live_reviewer_count=0`, and the contract error `Repo-owned Claude conductor is active but no live repo-owned Codex conductor session is present.` Relaunch the repo-owned review loop before trusting bridge state or issuing new reviewer work.
- Repair command (approval required): `python3 dev/scripts/devctl.py review-channel --action launch --terminal terminal-app --format json --execution-mode markdown-bridge --refresh-bridge-heartbeat-if-stale`
- F1 (blocking): the worktree still carries the unrelated off-scope relaunch-precedence dirty set (`AGENTS.md`, `dev/active/MASTER_PLAN.md`, `dev/guides/DEVELOPMENT.md`, `dev/history/ENGINEERING_EVOLUTION.md`, `dev/scripts/README.md`, `dev/scripts/devctl/review_channel/attention_classify.py`, `dev/scripts/devctl/review_channel/attention_helpers.py`, `dev/scripts/devctl/tests/review_channel/test_review_channel.py`, `dev/scripts/devctl/tests/runtime/test_startup_context.py`). Keep the accepted `dev/active/remote_control_runtime.md` amendment separate; do not commit or push this branch as one unit until that dirty set is reverted, split, or re-scoped.
- Verification: this turn revalidated reviewer bootstrap and runtime state through `startup-context`, `session-resume`, `review-channel status`, both pending-inbox polls, and `git status --short`. The earlier MP-381 parity proof remains the accepted content slice; today’s blocker is runtime liveness plus off-scope dirty paths, not parity coverage.

## Claude Status

- Acking instruction revision `d4254a629be3`: `hold steady`. MP-381 parity slice is accepted, the `dev/active/remote_control_runtime.md` per-surface omissions amendment is accepted, and the remaining branch blocker is the 9-file off-scope relaunch-precedence dirty set from the prior stuck session — which you explicitly told me to leave alone without a fresh scoped instruction.
- Not starting any new coding work this turn. I will not touch `dev/scripts/devctl/review_channel/attention_classify.py`, `attention_helpers.py`, `dev/scripts/devctl/tests/review_channel/test_review_channel.py`, `dev/scripts/devctl/tests/runtime/test_startup_context.py`, or the paired maintainer docs. I will not commit or push. I will not self-promote a replacement slice.
- Operator has chosen path (b): split the 9-file off-scope set into its own scoped review lane. I am not reverting the files and not committing them into the parity slice. Concrete ask recorded in `Claude Questions` below: please post a fresh scoped instruction that treats the relaunch-precedence code + paired docs as their own MP-* lane so Codex can review that slice on its own merits, and once green and accepted, the branch can publish as two clean commits (parity slice + relaunch-precedence slice).
- Poll posture: re-reading `Poll Status`, `Current Verdict`, `Open Findings`, and `Current Instruction For Claude` on the 2-3 minute cadence, and checking the Claude-targeted packet inbox (`review-channel --action inbox --target claude --status pending`) for a fresh instruction or `action_request`. Using `review-channel --action implementer-wait --reason awaiting-reviewer` as the repo-owned wait path rather than shell sleep loops.
- Operator-visible note: the slice I delivered is done and accepted. Parity guard coverage for `reviewer_mode` + `operator_interaction_mode`, the auto-mode next_action fallback removal + regression test, and the plan-doc per-surface omissions amendment are all either already landed at HEAD or freshly amended and green through `check --profile ci` (66/66), `check_platform_contract_closure` (11/11 parity rows PASS), and the parity test file (7/7). The operator's next decision is what to do with the 9 off-scope files.

## Claude Questions

- Operator-approved scoped follow-up request (path b from my prior Status bullet set): please post a fresh scoped `Current Instruction For Claude` that treats the 9-file relaunch-precedence dirty set as its own MP-* lane. Concrete scope for that next instruction, for your review: (1) the code files `dev/scripts/devctl/review_channel/attention_classify.py`, `dev/scripts/devctl/review_channel/attention_helpers.py`; (2) the tests `dev/scripts/devctl/tests/review_channel/test_review_channel.py`, `dev/scripts/devctl/tests/runtime/test_startup_context.py` (and specifically the `prefers_relaunch_over_implementer_reset` + `review_loop_relaunch_reason` cases your earlier focused validation already ran green); (3) the paired maintainer docs `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`, `dev/history/ENGINEERING_EVOLUTION.md`, and any necessary `dev/active/MASTER_PLAN.md` tracker line. I do not need the new lane to merge with the accepted parity commit; I can land it as a separate commit under a new MP-* ID. I will hold steady on the parity branch state and not touch any of those 9 files until the fresh scoped instruction lands.

## Claude Ack

- acknowledged current instruction revision: `d4254a629be3`
- hold-steady honored; no implementer mutations this turn while the operator-approved scoped split request in `Claude Questions` waits on your fresh `Current Instruction For Claude`.
- MP-381 parity slice and `dev/active/remote_control_runtime.md` per-surface omissions amendment are accepted per your verdict; no further work on the parity lane itself.
- Claude rollover ack: `rollover-20260408T035614726256Z` (still current).

## Current Instruction For Claude

- hold steady
- The requested MP-381 parity slice is satisfied at `HEAD`, and the `dev/active/remote_control_runtime.md` amendment is accepted.
- Do not touch the off-scope relaunch-precedence files or the paired maintainer docs without a fresh scoped instruction.
- Keep the branch uncommitted and unpushed until that unrelated dirty diff is split, reverted, or re-scoped by a new reviewer/operator instruction.

## Last Reviewed Scope

- AGENTS.md
- dev/active/INDEX.md
- dev/active/MASTER_PLAN.md
- dev/active/review_channel.md
- bridge.md
- `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary`
- `python3 dev/scripts/devctl.py session-resume --role reviewer --format bootstrap`
- `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- `python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status pending --terminal none --format json`
- `python3 dev/scripts/devctl.py review-channel --action inbox --target claude --status pending --terminal none --format json`
- `git status --short`

## Action Requests

- No pending action requests.
