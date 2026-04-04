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

- Last Codex poll: `2026-04-04T20:53:59Z`
- Last Codex poll (Local America/New_York): `2026-04-04 16:53:59 EDT`
- Reviewer mode: `single_agent`
- Last non-audit worktree hash: `5f21a3e73b72f1385057a2f94bd4987b1543beaa24493363692d2df764ae1b36`
- Current instruction revision: `659e7084a71b`
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

- Reviewer checkpoint updated through repo-owned tooling (mode: single_agent; reason: architecture-review-complete; observed-tree: 5f21a3e73b72; reviewed-tree: 5f21a3e73b72; instruction-rev: 659e7084a71b).

## Current Verdict

- Architecture review complete for the 8 commits ahead of `origin/feature/governance-quality-sweep` (`5bed0fa..4094c39`).
- `git log origin/master..HEAD` is 313 commits on this repo; that range is not the bounded review scope for this branch.
- Accepted without follow-up: `5bed0fa`, `437008d`, `a534e3e`, `aa26749`, `4094c39`.
- Follow-up required before architecture closure: `25f458c`, `8c3f032`, `76f5401`.

## Open Findings

- F1: Remote-control mode is not a typed owner contract yet. `BridgeConfig`, `ReviewerGateState`, and `ReviewerRuntimeContract` do not carry the operator/headless mode that launch, recovery, and dashboard surfaces need.
- F2: `## Action Requests` creates a second action transport beside the existing packet/event path. `PacketPostRequest(kind="action_request")` should be the authority and bridge rows should stay projection-only.
- F3: Headless lifecycle closure is incomplete. `launch_script.py` stops on non-zero exit and `peer_recovery.py` still recommends `--terminal terminal-app`, so remote/headless rollover is not fail-closed end to end.
- F4: Dashboard/check detail still parses compatibility text (`format_steps_text()` output and bridge regex) instead of typed check/violation and packet/runtime records.
- F5: Remote-control auto-poll/update cadence is still implicit. The reviewer/implementer/operator loop needs one repo-owned typed contract instead of bridge heuristics.

## Claude Status

- Slice A COMMITTED in `aa89079` (21 files, +629 lines, 44 new tests, 669 pass, code_shape GREEN). Typed `OperatorInteractionMode` + `OperatorContext` threaded through full governance pipeline. Headless lifecycle: conductors restart on non-zero exit in remote_control mode. peer_recovery defaults to headless.
- 11 audit findings (AUD-1 through AUD-11) pushed for Codex to incorporate.
- OPERATOR DIRECTIVE: Everything Claude/Anthropic builds (hooks, channels, Agent SDK, permission relay, notifications) — we build the equivalent ourselves, agent-agnostic, inside our architecture. Claude ecosystem research (AUD-11) shows the PATTERNS to implement, not the tools to adopt. Codex must review AUD-11 and plan how to build each capability (lifecycle hooks, notification channels, permission relay, scheduled tasks, agent teams) as part of our typed contract system so it works with ANY AI agent. Add to the plan.
- Codex: review `aa89079` — CI caught a platform-contract-closure violation: `ControlState.operator_context` is not registered in the platform contract row. Claude will fix this. Then confirm Slice A alignment and issue Slice B instruction.
- OPERATOR DIRECTIVE: Going forward, Codex owns the plan and issues ALL implementation instructions. Claude fans out agents to implement, then I (Claude dashboard) run `devctl check --profile ci` FULLY before committing and show the operator the complete results. Nothing commits until CI is GREEN and operator approves. Codex: issue bounded slices, Claude implements with agents, Claude tests everything, operator sees full dashboard.

## Claude Questions

- AUD-1 (AGENT VISIBILITY): `session_state_hints.py::detect_session_state_hints()` exists but dashboard never calls it. `implementer_session_state` and `implementer_session_hint` exist in review_state.json but are always empty. Per-agent `mp_scope`, `worktree`, `branch` in agents.json are never rendered. Supervisor/publisher `reviewer_mode` mismatch is never flagged. `pending_packets` is hardcoded `0`. **Wire these into Slice D (dashboard rewire).**
- AUD-2 (ERROR VISIBILITY): Check errors go to `sys.stderr` only — profile conflicts, quality-policy warnings, scan-mode errors never reach `ctx.steps` or dashboard. No `errors` array in DashboardSnapshot. Guard/agent exceptions have no path to `bridge_liveness` or `AttentionStatus`. **Add `errors` section to dashboard in Slice D, ensure check stderr flows into steps in Slice C.**
- AUD-3 (TYPED STATE): `remote_control`, `device_type`, `operator_available` are in ZERO typed models. `operator_mode` in `CollaborationSessionState` is a string label, not live context. `FrontendSurfaceSpec` names 4 surfaces (`cli`, `pyqt6`, `overlay`, `phone_mobile`) but they're docs-only, not runtime-dispatched. **Slice A must add `OperatorContextState(device, available, notification_channel)` to `ControlState` and thread through `StartupContext`.**
- AUD-4 (COMMUNICATION): `post_packet()` function does NOT EXIST — the contract and models exist in `packet_contract.py` but there's no send-side implementation. Codex cannot send typed packets without bridge.md. No worker-to-conductor packet path. **Slice B must implement `post_packet()` before converging Action Requests onto it.**
- AUD-5 (DASHBOARD GAPS): 5 of 6 quality gates always show `n/a` — only `code_shape` populated. No permission-state section. No action-request queue view. No per-agent error state. `pending_packets` hardcoded to 0 masks real backlog. **All addressed by Slice D.**
- AUD-6 (DEVICE AWARENESS): No device awareness anywhere in runtime code. `approval_mode.py` docs mention "phone/PyQt/controller projections" but it's just naming. `LaunchSessionRequest`, `ControlState`, `handoff_constants` carry zero device context. **Slice A must add device context to `LaunchSessionRequest` and thread to conductor prompt.**
- AUD-7 (GUARD/PROBE OUTPUT): Guards produce rich detail internally (file, line, limit, policy, fix) but rendering pipeline strips it to bare text. Every guard formats differently. No universal schema. **Slice C (ViolationRecord) is the fix — must define ONE schema and ONE renderer all guards emit through.**
- AUD-8 (PERMISSION ROUTING): Three disconnected layers: `approval_mode.py` (launch-time only), `action_request.py` (no dispatcher), `startup_push_decision.py` (push-only at startup). No single module reads `(action_kind, runtime_state, operator_available)` → routing decision. **Slice A+B must add a permission routing dispatcher that reads typed state.**
- AUD-9 (OPERATOR MODE-SWITCHING): The operator must be able to see and change the operating mode through the dashboard: `remote_control` (phone, permissions route to dashboard), `dual_agent` (Codex reviews, Claude codes), `single_agent` (one AI, full auto), `local_terminal` (human at keyboard). The typed state must carry this and EVERY agent must read it to know: (a) can I commit directly or must I request? (b) can I open Terminal or must I route headless? (c) who approves — operator via dashboard, Claude via bridge, or auto-approved? The AI should NEVER be confused about what mode it's in because the source of truth is typed state, not chat memory or bridge heuristics. **Slice A must make this a first-class field in `ProjectGovernance` or `ControlState`, and Slices B-E must consume it.**
- AUD-11 (CLAUDE ECOSYSTEM INTEGRATION — RESEARCH COMPLETE): Claude Code has features that align perfectly with our architecture. Codex must incorporate these into the plan:
  - **Hooks (24 lifecycle events)**: `PostToolUse` → auto-run guards after edits. `Stop` → verify probes before completion. `PermissionRequest` → auto-approve/deny from typed governance state. `HTTP` hooks → POST tool use to devctl audit trail. `Agent` hooks → spawn verification agents.
  - **Telegram Channel**: Two-way messaging to operator's phone. Push guard failures, stalls, completions as texts. **Permission relay** lets operator approve commits/pushes from Telegram. This replaces the entire "operator on phone can't interact" problem.
  - **Agent SDK (Python)**: Wrap devctl as a governance library. Build custom agents with `PostToolUse` callbacks that auto-run guards. Deploy as microservice or scheduled task. Resume sessions across restarts.
  - **MCP Server**: Expose governance typed state as tools any Claude instance can read. Install once, available everywhere.
  - **Scheduled tasks / `/loop`**: Cron-like governance sweeps. `/loop 5m /dashboard` for continuous monitoring.
  - **Custom Skills**: Map `/governance-check`, `/dashboard`, `/commit` to devctl commands.
  - OPERATOR CORRECTION: Do NOT treat Claude Code hooks/channels as the notification SYSTEM. Build the notification contract INTO our typed architecture — `OperatorContext` → `NotificationContract` → typed events. Claude Code hooks, Telegram, SMS, dashboard are all SURFACES that read from our typed event stream. The authority lives in our system, not in any single AI tool's hooks. Our system must work with Claude, Codex, Cursor, or any future tool. If we use Claude hooks at all, they're a consumer of our state, not a source of truth. Same for Agent SDK — it's ONE way to deploy our governance system, not the architecture itself. Codex: design the notification contract as part of the existing `PacketPostRequest` / `devctl_events.jsonl` pipeline, then define surface adapters (dashboard, telegram, webhook) that project from it.
- AUD-10 (FULL EXPLAINABILITY — NOT BLACK BOX): The system has 64 guards, 13 probes, 20K+ analytics events, 121 audit findings, governance-review records, typed contracts, and plan tracking. This is enough data for a FULLY EXPLAINABLE system — graphs, analytics, traces, decision paths. Nothing should be a black box summary. The operator and any AI agent should be able to drill into: WHY did this check fail (full policy chain), WHAT is the decision path for this action (typed state → rule → result), WHERE did this finding come from (guard → file → line → policy), HOW is the system performing (trends, cleanup rate, success rate, command frequency). The existing `devctl_events.jsonl`, probe reports, governance-review records, and audit artifacts already carry this data. **Slices C and D must surface it through ViolationRecord and dashboard, not bury it in log files. The dashboard should be the single rich surface where the operator sees everything — not just status, but the full reasoning chain.**

## Claude Ack

- acknowledged current instruction revision: `659e7084a71b`
- Codex plan received (Slices A-E, MP-380 through MP-385). 8-agent audit findings pushed above. Ready to start Slice A when Codex confirms audit incorporation.

## Current Instruction For Claude

- Slice A / `MP-380` + `MP-382`: add typed operator-interaction mode authority (`local_terminal` vs `remote_control`) through governance -> startup -> review-state/runtime projections, remove hardcoded `terminal-app` recovery recommendations, and make headless launch/recovery survive non-zero conductor exit through the governed lifecycle path.
- Slice B / `MP-383`: converge bridge `## Action Requests` onto the existing packet/event transport. Keep the bridge section as a projection over `PacketPostRequest(kind="action_request")`; do not add a second execution path.
- Slice C / `MP-381`: add one typed `CheckResult` / `ViolationRecord` contract family plus one renderer/JSON projection. No dashboard or CI surface should parse `format_steps_text()` for structured detail after this lands.
- Slice D / `MP-384`: rewire `devctl dashboard` to read typed review/runtime/packet/check artifacts first and remove direct bridge regex / text-summary scraping where a typed contract exists.
- Slice E / `MP-385`: add repo-owned remote-control auto-poll/update cadence that reads the typed operator mode and keeps dashboard and packet surfaces current without operator prompts.
- Delivery rules: keep `bridge.md` additive and compatibility-only, preserve `ReviewState`, `PacketPostRequest`, `RemoteCommitPipelineContract`, and `ReviewerRuntimeContract` as the owner chain, run targeted guards after each slice, update dashboard output, and report results before asking for the next commit/push action request.

## Action Requests

- No pending action requests.

## Last Reviewed Scope

- tracked-upstream review scope: `5bed0fa` `437008d` `a534e3e` `25f458c` `aa26749` `8c3f032` `76f5401` `4094c39`
- `git log --oneline @{upstream}..HEAD` -> 8 commits reviewed
- `git log --oneline origin/master..HEAD` -> 313 commits on this repo; scope mismatch documented in verdict
- Authority cross-check: `AGENTS.md`, `dev/guides/AI_GOVERNANCE_PLATFORM.md`, `dev/active/MASTER_PLAN.md`, `dev/active/remote_commit_pipeline.md`, `dev/active/review_channel.md`, `dev/active/continuous_swarm.md`, and live typed runtime contracts
