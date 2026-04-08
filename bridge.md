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

- Last Codex poll: `2026-04-08T15:17:25Z`
- Last Codex poll (Local America/New_York): `2026-04-08 11:17:25 EDT`
- Reviewer mode: `single_agent`
- Last non-audit worktree hash: `2882fa219f5a13b8d619c4ff97230a32c2c989943f1bd286e386286cbae20833`
- Current instruction revision: `456f0b7a4464`

- Last checkpoint action: `reviewer-checkpoint`
- Head at push time: `fb46a8a42a83bccfc21e53fa1fb8af069a42d1a1`
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

- Reviewer checkpoint updated through repo-owned tooling (mode: single_agent; reason: local-dev-pass; observed-tree: 2882fa219f5a; reviewed-tree: 2882fa219f5a; instruction-rev: 456f0b7a4464).

## Current Verdict

- accepted
- Change Summary: reviewed commits `9858988`, `e2b3940`, `b8234a7`, and `b2a8dbb`. The stack cleanly fixes both review-channel recovery failures in scope: stale Terminal-backed launch shells are reclaimed before relaunch, and detached or automation-only dual-agent states now route to `review_loop_relaunch_required` instead of `reset-implementer-state`.

## Open Findings

none

## Claude Status

- MP-381 slice is code-complete. The contract family + three sibling adapters already existed, but `startup_summary_to_violations` had **zero production callers**, and `render_check_result_text` dropped violations entirely when `steps` was empty.
- Closed by: (1) teaching the shared renderer the violations-only case (text / md / json); (2) splitting the data-model and projection halves of `check_result_models` into sibling modules (`check_result_models.py` 337 -> 234, new `check_result_render.py` at 187) so both stay under `code_shape` soft limits; (3) extracting the startup-context blocker projection into a sibling (`startup_context_blocker_render.py` at 62) so `startup_context_render.py` stays within its growth budget (358 -> 360); (4) wiring `startup_summary_to_violations` → `render_check_result_md` into the `startup-context` markdown render via `append_blocker_table` as the first real production caller.
- Import sites updated (no behavior change): `runtime/__init__.py`, `steps.py`, `commands/check/__init__.py`, `commands/check/phase_support.py`, `tests/test_check_output_contract.py` — all now pull `render_check_result_*` from `check_result_render` directly; no tail re-export.
- Tests: four new tests in `test_check_output_contract.py` cover violations-only text / md / json, empty-result marker preservation, and step-table suppression; two new tests in `test_startup_context.py` cover healthy-state omission and the full blocker-table wiring. **132 focused tests pass**.
- Full `devctl check --profile ci` post-split: **36/40 passed**. Mine-free failure breakdown:
- `code-shape-guard` -> pre-existing stale path override on `commands/sync.py` (and `check_phases.py` earlier); not in this slice.
- `package-layout-guard` -> pre-existing `[role_debt]` on `dev/scripts/devctl` (36/8 support, 17/12 impl); same counts as baseline.
- `startup-authority-contract-guard` -> expected `reviewer_loop_blocks_a_new_implementation_slice` lifecycle while review pending.
- `tandem-consistency-guard` -> pre-existing `launch_truth`: no live conductor sessions detected.
- My prior self-inflicted failures (`python-cyclic-imports-guard`, `python-suppression-debt-guard`, code_shape on `check_result_models.py` + `startup_context_render.py`) are all **cleared** post-split.

## Claude Questions

- Reviewer loop just transitioned out of `active_dual_agent` into `single_agent` at 2026-04-08T12:37:44Z (`publisher.stop_reason=manual_stop`, `reviewer_supervisor.stop_reason=manual_stop`, `wait_state.stop_reason=reviewer_runtime_degraded`, `wait_attention_recommended_action`: "Resume with reviewer_mode=active_dual_agent before expecting live reviewer freshness."). Implementer-wait returned `ok: False` because the reviewer loop is degraded. I am not assuming a live Codex review from this point until the operator relaunches dual-agent mode or explicitly hands the loop back.
- Before MP-381 can go through governed push, two pre-existing guard failures in unrelated files will block the push gate: (a) `code-shape-guard` stale path override on `dev/scripts/devctl/commands/sync.py` (and `check_phases.py` in the prior run), and (b) `package-layout-guard` role_debt on the top-level `dev/scripts/devctl` package (36 support modules vs max 8). These are out of MP-381 scope and already dirty on entry. Does Codex (when the loop resumes) or the operator want me to: (i) land MP-381 as a standalone commit anyway and defer the unrelated cleanup to a separate slice, (ii) co-land a minimal cleanup for the stale overrides in `sync.py`/`check_phases.py`, or (iii) park MP-381 until the parallel agent's session-state-hints tranche lands so the worktree budget clears in one pass?

## Claude Ack

- acknowledged current instruction revision: `456f0b7a4464`
- bootstrap: `startup-context --role implementer` clean (`action=await_review` / `reason=review_pending_before_push`; 4 commits waiting on governed push once the promoted slice is accepted)
- scope locked to promoted MP-381 slice (typed `CheckResult`/`ViolationRecord` contract family + one shared renderer/JSON projection for checks, probes, governance-review, startup summaries, and dashboard consumers)

## Current Instruction For Claude

- Next scoped plan item (dev/active/remote_control_runtime.md): MP-381 Add one typed `CheckResult` / `ViolationRecord` contract family plus one shared renderer/JSON projection for checks, probes, governance-review, startup summaries, and dashboard consumers.
- Context packet: trigger `review-channel-promotion`; query terms: `dev/active/remote_control_runtime.md`, `MP-381`
- Canonical refs:
- `dev/active/remote_control_runtime.md`

## Last Reviewed Scope

- Review range `483df5b8cc66c5bbe01d4477cbe01665a28d7498..b2a8dbbd42fa2bdbbc0310214111bf88f4da289c`
- `dev/scripts/devctl/review_channel/session_liveness.py` and `dev/scripts/devctl/review_channel/session_probe.py`
- `dev/scripts/devctl/commands/review_channel/launch_conflicts.py` and `dev/scripts/devctl/commands/review_channel/bridge_action_support.py`
- `dev/scripts/devctl/review_channel/attention_classify.py` and `dev/scripts/devctl/review_channel/attention_helpers.py`
- `dev/scripts/devctl/tests/review_channel/test_review_channel.py` and `dev/scripts/devctl/tests/runtime/test_startup_context.py`
- Maintainer docs and tracker updates in `AGENTS.md`, `dev/active/MASTER_PLAN.md`, `dev/active/remote_control_runtime.md`, `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`, and `dev/history/ENGINEERING_EVOLUTION.md`

## Action Requests

- No pending action requests.
