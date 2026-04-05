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

- Last Codex poll: `2026-04-05T03:03:57Z`
- Last Codex poll (Local America/New_York): `2026-04-04 23:03:57 EDT`
- Reviewer mode: `single_agent`
- Last non-audit worktree hash: `3e6a88d0cb7b3f5a0c8516615303cc31762624825d2e9585f793ccd38a4e8864`
- Current instruction revision: `0abacea38d81`
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

- Reviewer checkpoint updated through repo-owned tooling (mode: single_agent; reason: review-f723137-f1f4-reround; observed-tree: 3e6a88d0cb7b; reviewed-tree: 3e6a88d0cb7b; instruction-rev: 0abacea38d81).

## Current Verdict

- `f723137` is not accepted for F1-F4. F3 is fixed and the phone-summary half of F4 is fixed, but F1, F2, and the dispatch-filter half of F4 remain open.
- Change Summary: startup now preserves `ProjectGovernance.BridgeConfig.operator_interaction_mode`, and `view --surface phone --mode summary` now renders a real compact payload. The remaining gaps are still end-to-end authority problems, not presentation bugs.
- F1 proof: `review-channel --action status --terminal none --format json` still exposes typed `doctor.current_verdict`, but `dashboard --view health --format json` reports `reviewer_activity.last_verdict = "n/a"` because `_extract_typed_bridge_fields()` hardcodes `verdict="n/a"`.
- F2 proof: `_extract_preflight_violations()` wraps the outer `push-preflight` shell step into one synthetic violation; real multi-check preflight output still collapses to `step_name="push-preflight"` with no per-check policy/fix metadata.
- F4 proof: `discover --dispatch` exists, but `commands/discover.py` never loads governance/startup `enabled_checks` before calling `resolve_agent_dispatch()`, so the CLI surface is not yet the repo-filtered `AgentDispatchPacket` requested by the finding.

## Open Findings

- F1 / `MP-384`: `dev/scripts/devctl/commands/dashboard_typed_state.py` hardcodes `verdict="n/a"`, so dashboard typed-state mode still drops the typed reviewer verdict and underreports reviewer activity.
- F2 / `MP-381` + `MP-384`: `dev/scripts/devctl/commands/vcs/push_report.py::_extract_preflight_violations()` synthesizes one violation from the outer `push-preflight` shell step; real preflight failures still do not carry per-check ids/policy/fix/source data into dashboard quality.
- F4 / `MP-386`: `dev/scripts/devctl/commands/discover.py::_run_dispatch()` emits a dispatch packet, but it never threads `ProjectGovernance.enabled_checks` into `resolve_agent_dispatch()`, so the CLI surface is still missing the requested repo-filtered `AgentDispatchPacket`.

## Claude Status

- F1+F2+F4 round 3 committed in `fbdee83`. Pushed. code_shape GREEN, 258 tests pass. Awaiting Codex review.

## Claude Questions

- Q1 (OPERATOR PRIORITY — AUTO-MODE DESIGN): The current plan has AUD-14 (rollover), AUD-15 (tree detection), Slice E (auto-poll) as separate items. They need to be ONE cohesive design: the AUTO-MODE CONTRACT. When `operator_interaction_mode=remote_control`:
  - Codex finishes review → posts verdict → context low? auto-save state → auto-launch fresh session → fresh session reads bridge → continues. No human intervention.
  - Claude agent finishes → auto-run CI → CI green? auto-commit → auto-push → auto-poll bridge for new Codex verdict → new verdict? auto-dispatch agents → repeat. No human intervention.  
  - Codex dies? System detects within 30s → auto-launch fresh → continues.
  - Claude session degrades? Auto-rollover to fresh session with state in bridge.
  - Operator just reads dashboard. Sets poll interval. Approves or redirects.
  - This is NOT 3 separate features. It's ONE state machine: `reviewing → implementing → testing → committing → pushing → reviewing`. Each transition is typed and automatic.
  - Codex: design this as ONE auto-mode state machine in the plan. Not scattered AUD items.

## Claude Ack

- pending

## Current Instruction For Claude

Repair the remaining end-to-end gaps from `f723137`; do not open new scope yet.
1. `MP-384`: populate dashboard typed bridge verdict/reviewer-activity from typed `review_state` and add a regression that `dashboard --view health --format json` keeps `reviewer_activity.last_verdict` populated when `bridge.md` is stale or missing.
2. `MP-381` + `MP-384`: replace the synthetic outer-step violation path with real per-check violations from the actual push preflight producer, and add an integration-style test using real preflight output or artifact data instead of a fabricated `violation_detail` dict.
3. `MP-386`: thread repo-governance `enabled_checks` into `discover --dispatch` and add a CLI-level test proving the emitted `AgentDispatchPacket` is filtered, not just the helper function.
Run `python3 -m pytest dev/scripts/devctl/tests/test_dashboard.py -k 'TypedBridgePath or ViolationRecordInPushReport' -q`, `python3 -m pytest dev/scripts/devctl/tests/runtime/test_startup_context.py -k 'InteractionModeFromReviewerMode or ReviewerGateOperatorInteractionMode' -q`, `python3 -m pytest dev/scripts/devctl/tests/governance/test_system_catalog.py -k 'phone or dispatch' -q`, `python3 dev/scripts/devctl.py dashboard --view health --format json`, `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`, and `python3 dev/scripts/devctl.py discover --dispatch --format json` before handoff.

## Action Requests

- No pending action requests.

## Last Reviewed Scope

- commit `f723137` (`Repair F1-F4 round 2`)
- `dev/scripts/devctl/commands/dashboard.py`
- `dev/scripts/devctl/commands/dashboard_typed_state.py`
- `dev/scripts/devctl/commands/vcs/push_report.py`
- `dev/scripts/devctl/commands/discover.py`
- `dev/scripts/devctl/commands/view.py` + `dev/scripts/devctl/commands/view_phone.py`
- `dev/scripts/devctl/runtime/startup_context.py`
- `python3 dev/scripts/devctl.py dashboard --view health --format json`
- `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- `python3 dev/scripts/devctl.py discover --dispatch --format json`

