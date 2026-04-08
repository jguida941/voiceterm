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

- Last Codex poll: `2026-04-08T20:52:34Z`
- Last Codex poll (Local America/New_York): `2026-04-08 16:52:34 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `0ff08577b656f51e9e665e5510263621c0dd92e8c531628b069c3d0cb0923e74`
- Current instruction revision: `64b45d5fd553`
- Last checkpoint action: `reviewer-checkpoint`
- Head at push time: `81cff0d87d8d20b871a71d69dd69a7eb2116b0fe`
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

- Reviewer checkpoint updated through repo-owned tooling (mode: active_dual_agent; reason: review-pass; observed-tree: 0ff08577b656; reviewed-tree: 0ff08577b656; instruction-rev: 64b45d5fd553).

## Current Verdict

- changes requested
- Change Summary: The preserved WIP in `079d7f3f` partially wires `session-resume` and the dashboard read model to the shared coordination loader, but the governing startup surface still bypasses that loader, so live coordination parity is still broken. The scan-based governance path also still constructs `BridgeConfig` without repo-policy `operator_interaction_mode`, so missing policy keeps failing open to `local_terminal` instead of the required `unresolved`. Focused validation is not handoff-ready either: the targeted suite is still red on the startup token-budget check.

## Open Findings

- F1: `dev/scripts/devctl/runtime/startup_context.py` still bypasses the shared loader. `build_startup_context()` continues to build coordination through `build_work_intake_coordination_state()` + `build_coordination_snapshot()` instead of `coordination_loader.load_coordination_snapshot()`, while `session_resume_support.py` and `control_plane_read_model.py` now reuse the loader-backed read model. Live proof on this head still diverges: `startup-context --role reviewer --format json` reports `declared_topology=multi_agent_orchestrated`, `observed_topology=single_agent`, `recommended_topology=single_agent`, `ownership_status=clear`, `resync_reasons=[attention:review_loop_relaunch_required,...]`, while `session-resume --role reviewer --format json` and `dashboard --format json` report `observed_topology=dual_agent` with the same slice/ownership fields. This violates the MP-384 / MP-387 one-snapshot parity requirement.
- F4: `dev/scripts/devctl/governance/draft_policy_scan.py` still returns `BridgeConfig(...)` without threading repo-policy `operator_interaction_mode`, so scan-based governance inherits the dataclass default `local_terminal` instead of the fail-closed parse result used by `bridge_config_from_mapping()`. Live proof on this head: `scan_repo_governance(repo, policy={}).bridge_config.operator_interaction_mode` returns `local_terminal`, while `bridge_config_from_mapping({}).operator_interaction_mode` returns `unresolved`. `startup-context --role reviewer --format json` still exposes that fail-open scan result under `governance.bridge_config.operator_interaction_mode` and `reviewer_gate.operator_interaction_mode`.
- F5: This diff did not add the focused regression coverage the instruction asked for, and the required focused suite is still red. `python3 -m pytest dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_startup_context.py dev/scripts/devctl/tests/governance/test_session_resume.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short` finished `1 failed, 451 passed`; the failure is `dev/scripts/devctl/tests/runtime/test_startup_context.py::TestStartupContextBuild::test_slim_token_budget` (`10139` tokens, budget `< 10000`). Do not claim this slice verified until the missing regression coverage is added and the focused suite is green or explicitly blocked.

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

Scoped from `dev/active/remote_control_runtime.md` via `--scope`.

- Finish F1 by routing `startup-context` through the same governed coordination loader path that `session-resume` and `ControlPlaneReadModel` now use. After the fix, `startup-context --role reviewer --format json`, `session-resume --role reviewer --format json`, and `dashboard --format json` must return identical `current_slice`, `declared_topology`, `observed_topology`, `recommended_topology`, `ownership_status`, and `resync_reasons` from one snapshot per tick.
- Finish F4 by teaching the scan-based governance path to read repo-policy `operator_interaction_mode` and pass it through `BridgeConfig` via the same fail-closed parser used by `bridge_config_from_mapping()`. `scan_repo_governance(policy={}).bridge_config.operator_interaction_mode` and `bridge_config_from_mapping({}).operator_interaction_mode` must both resolve to `unresolved` when the field is absent.
- Add focused regression coverage for both fixes: one parity test that proves startup-context/session-resume/dashboard coordination fields match on the same governed state, and one scan-governance test that proves missing `operator_interaction_mode` stays `unresolved` while explicit values survive.
- Re-run `python3 -m pytest dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_startup_context.py dev/scripts/devctl/tests/governance/test_session_resume.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short` and keep working until it is green. The current red test is `dev/scripts/devctl/tests/runtime/test_startup_context.py::TestStartupContextBuild::test_slim_token_budget`; if that budget failure remains after F1/F4, reduce the startup packet or record a scoped blocker before handoff.
- Then run the required tooling verification bundle before handoff.

## Last Reviewed Scope

- Review range `9a6dd2faac4586b3dea8b525461007fa77e78b5f..81cff0d87d8d20b871a71d69dd69a7eb2116b0fe`.
- New code-carrying commit after the prior reviewer scope: `079d7f3f` (`session_resume_support.py`, `control_plane_read_model.py`). The later commits in this range are bridge/audit refreshes, not new F1/F4 code.
- Relevant code paths reviewed: `dev/scripts/devctl/commands/governance/session_resume_support.py`, `dev/scripts/devctl/runtime/control_plane_read_model.py`, `dev/scripts/devctl/runtime/startup_context.py`, `dev/scripts/devctl/runtime/coordination_loader.py`, `dev/scripts/devctl/governance/draft_policy_scan.py`, `dev/scripts/devctl/runtime/project_governance_parse.py`, `dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py`.
- Live F1 proof: `startup-context --role reviewer --format json` still reports `declared_topology=multi_agent_orchestrated`, `observed_topology=single_agent`, `recommended_topology=single_agent`; `session-resume --role reviewer --format json` and `dashboard --format json` report `observed_topology=dual_agent` with the same slice and ownership fields.
- Live F4 proof: `python3 -c 'from pathlib import Path; from dev.scripts.devctl.governance.draft import scan_repo_governance; from dev.scripts.devctl.runtime.project_governance_parse import bridge_config_from_mapping; repo=Path(".").resolve(); print(scan_repo_governance(repo, policy={}).bridge_config.operator_interaction_mode); print(bridge_config_from_mapping({}).operator_interaction_mode)'` prints `local_terminal` then `unresolved`.
- Focused validation: `python3 -m pytest dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_startup_context.py dev/scripts/devctl/tests/governance/test_session_resume.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short` -> `1 failed, 451 passed`; failing test: `dev/scripts/devctl/tests/runtime/test_startup_context.py::TestStartupContextBuild::test_slim_token_budget`.

## Action Requests

- **Re-scope Claude-CLI's instruction to include Q-series findings.** Claude-CLI only sees F1/F2/F3 (baked into launch prompt); has NOT picked up Q1-Q21 from `dev/audits/LIVE_RUN.md`. Priority: Q20 (packet transport broken), Q12 (deserializer), Q1 (devctl commit self-block), Q9/Q10/Q21 (mode TTL).
- **Retire `dev/audits/LIVE_RUN.md` once packet transport round-trips cleanly.** Emergency workaround for Q20; once `review-channel post + inbox` round-trips 100% and Q11/Q12 are fixed, findings should flow through the typed receipt system.
