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

- Last Codex poll: `2026-04-08T18:26:17Z`
- Last Codex poll (Local America/New_York): `2026-04-08 14:26:17 EDT`
- Reviewer mode: `single_agent`
- Last non-audit worktree hash: `8c72dbb81cb362ae197c9a59a1aa8b207314f8bdfc6faff4aae7b60b2a4f24ac`
- Current instruction revision: `6e0cacd366b6`
- Last checkpoint action: `reviewer-checkpoint`
- Head at push time: `9a6dd2faac4586b3dea8b525461007fa77e78b5f`
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

- Reviewer checkpoint updated through repo-owned tooling (mode: single_agent; reason: diff-review; observed-tree: 8c72dbb81cb3; reviewed-tree: 8c72dbb81cb3; instruction-rev: 6e0cacd366b6).

## Current Verdict

- changes requested
- Change Summary: the newly reviewed commit range does not address the scoped F1/F2/F3 coordination/dashboard/startup parity work, so those findings remain open. It also introduces a new operator-mode regression: the governance scan path now defaults missing `operator_interaction_mode` to `remote_control`, which bypasses the intended fail-closed `unresolved` behavior instead of wiring the mode through repo policy.

## Open Findings

- F1: Coordination source-of-truth still diverges across the target surfaces. `ControlPlaneReadModel`/dashboard still read `cfg.review_state_json_rel` (`dev/reports/review_channel/state/latest.json`), `session-resume` reads `<review_root>/review_state.json`, and `startup-context` refreshes a bridge-backed snapshot. On this branch those three paths already disagree: `startup-context --role reviewer --format summary` reports `coordination=multi_agent_orchestrated/single_agent->single_agent`, `session-resume --role reviewer --format json` reports `multi_agent_orchestrated/dual_agent->single_agent`, and `dashboard --format json` reports `single_agent/single_agent->single_agent` with `current_slice="Session rollover: Codex, Claude conductors started"`. Until all three surfaces share one governed loader, the scoped MP-384/MP-387 parity proof is false.
- F2: The markdown dashboard now mislabels every pending packet as an action packet. `render_pending_packets_markdown()` prints `Pending action packets`, but `_extract_typed_packets()` still forwards every pending packet kind, so notices/findings/instructions are presented as operator actions.
- F3: `StartupContext.coordination` still drops the ownership answer that this slice is supposed to converge. `_startup_coordination_dict()` and the machine summary keep topology/fanout/resync fields but omit `ownership_status` (and the related authority/work-ownership posture), so startup bootstrap cannot provide the promised ownership truth even when the underlying `CoordinationSnapshot` has it.
- F4: `BridgeConfig.operator_interaction_mode` now defaults to `remote_control` in the contract model, but `_scan_bridge_config()` still never reads that field from repo policy. Every scan-based consumer therefore treats an unconfigured repo as remote-control: `scan_repo_governance(policy={}).bridge_config.operator_interaction_mode` now returns `remote_control`, while the typed parse path still resolves the same missing field to `unresolved`. That breaks the MP-380 fail-closed contract and can silently permit headless launch behavior in repos that never opted into remote control.

## Claude Status

- F1/F2/F3 coded + live-verified. Awaiting operator commit permission (remote_control gate). F4 and Q1–Q21 out of scope.
- F1: `load_sources`, `build_control_plane_read_model`, `_load_governed_sources` now all route review_state through `load_current_review_state_payload`. Live-proven: `startup-context`/`session-resume`/`dashboard --format json` return identical `current_slice`, topology `multi_agent_orchestrated/single_agent/single_agent`, `ownership_status=outside_scope_dirty_paths`, matching `resync_reasons`.
- F2: `render_pending_packets_markdown` emits generic `**Pending packets**:`; test updated.
- F3: new `runtime/startup_context_projections.py` owns `startup_coordination_dict` and now emits `ownership_status`/`authority_mode`/`work_ownership_mode`/`sync_cadence_mode`; summary renderer adds `ownership_status=`. Extraction also cleared the pre-existing `mixed_concerns_on_touched_file` violation on `startup_context.py`.
- 455/455 focused green; `check --profile ci` 38/40 (only reds are expected dirty tree + untracked new module; both clear on commit).

## Claude Questions

- Canonical tracking for Q1–Q21 lives in `dev/audits/LIVE_RUN.md` (tracked, append-only) — file:line breadcrumbs, severity, and fix notes all there.
- Q20 (packet transport broken) still open: `review-channel --action inbox --target codex --status pending` returns 0 packets while `--action history` returns 20 including `status=pending` Q-series items. Trust LIVE_RUN.md over the packet queue until Codex audits the inbox/history contract mismatch and the packet durability gap.
- Q4 tactically fixed in `f177aae` (BridgeConfig default flipped to `remote_control`); structural fix (config-driven read) still open — overlaps with Codex F4.
- Q11 hotfixed in `ca59eaf` (`pending_approvals` tolerates dict-shaped packets); underlying deserializer (Q12) still open.

## Claude Ack

- acknowledged current instruction revision: `6e0cacd366b6`
- F1/F2/F3 landed and live-proven. Focused suites 455/455 green. `check --profile ci` at 38/40 with only expected dirty-tree + untracked-new-module failures, both pending commit.
- Operator gate: `interaction_mode=remote_control`. Paused before `git commit` on the F1/F2/F3 scope, awaiting explicit operator authorization; a separate push approval will be required after commit lands.
- F4 and the Q1–Q21 LIVE_RUN.md backlog remain outside the current scoped instruction and are untouched.
- Codex reviewer-owned content (Poll Status, Verdict, Open Findings, Current Instruction, Last Reviewed Scope, Action Requests) preserved verbatim; only implementer-owned Status/Ack edited this turn.
- Launch posture: `--terminal none` (remote_control).

## Current Instruction For Claude

Scoped from `dev/active/remote_control_runtime.md` via `--scope`.

- Fix F1 by routing `ControlPlaneReadModel`, dashboard, `startup-context`, and `session-resume` through one shared governed review-state/coordination loader. Do not keep dashboard on `state/latest.json` while `session-resume` reads `<review_root>/review_state.json` and `startup-context` regenerates a third snapshot. After the fix, prove the live repo returns the same `current_slice`, `declared/observed/recommended_topology`, `ownership_status`, and `resync_reasons` from `startup-context --role reviewer --format json`, `session-resume --role reviewer --format json`, and `dashboard --format json`.
- Fix F2 by either filtering the markdown dashboard section to `kind == "action_request"` or restoring a generic pending-packets label until MP-384/MP-385 splits `pending_packets_total` from `pending_action_requests`.
- Fix F3 by keeping `StartupContext.coordination` lossless enough for the scoped parity contract: include `ownership_status` in the typed startup payload and machine summary if startup bootstrap remains one of the proof surfaces.
- Re-run the focused coordination/startup/session-resume/dashboard tests, then run the required tooling verification bundle before handoff.

## Last Reviewed Scope

- Review range `d2e648f6a7e33f6aa4adb6aae4c42ef5801652c2..409e65e9061c9637b305cd3ce0fbe5e12f7cce4d`
- `dev/scripts/devctl/runtime/project_governance_contract.py` and `dev/scripts/devctl/runtime/review_state_models.py`
- `dev/scripts/checks/code_shape/code_shape_policy.py` plus the generated/update-only artifacts in `dev/CHANGELOG.md`, `dev/audits/LIVE_RUN.md`, `dev/audits/REVIEW_SNAPSHOT.md`, and `bridge.md`
- Runtime proof: `scan_repo_governance(policy={}).bridge_config.operator_interaction_mode` -> `remote_control`, while `bridge_config_from_mapping({}).operator_interaction_mode` -> `unresolved`
- Focused validation: `python3 -m pytest dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py -q`

## Action Requests

- **Re-scope Claude-CLI's instruction to include Q-series findings.** Claude-CLI only sees F1/F2/F3 (baked into launch prompt); has NOT picked up Q1-Q21 from `dev/audits/LIVE_RUN.md`. Priority: Q20 (packet transport broken), Q12 (deserializer), Q1 (devctl commit self-block), Q9/Q10/Q21 (mode TTL).
- **Retire `dev/audits/LIVE_RUN.md` once packet transport round-trips cleanly.** Emergency workaround for Q20; once `review-channel post + inbox` round-trips 100% and Q11/Q12 are fixed, findings should flow through the typed receipt system.
