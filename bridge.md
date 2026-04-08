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

- Last Codex poll: `2026-04-08T21:34:59Z`
- Last Codex poll (Local America/New_York): `2026-04-08 17:34:59 EDT`
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
- Change Summary: F1 and F4 are now closed on the live code path. `startup-context`, `session-resume`, and `dashboard` report the same coordination snapshot on this tree, and the scan-based governance path now fails closed to `operator_interaction_mode=unresolved` on empty policy. The slice is still not handoff-ready because F5 remains open: the required focused suite is red on the startup packet token-budget gate, and a docs-only follow-up commit landed during review without changing the code paths under test.

## Open Findings

- F5: The exact required focused suite is still red on the startup packet budget gate. `python3 -m pytest dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_startup_context.py dev/scripts/devctl/tests/governance/test_session_resume.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short` now finishes `1 failed, 456 passed`; the failing test is `dev/scripts/devctl/tests/runtime/test_startup_context.py::TestStartupContextBuild::test_slim_token_budget`, which reports `10521` tokens against the `<10000` budget. Local size breakdown shows `build_startup_context().to_dict()` is dominated by the `governance` payload (~5661 tokens), with `work_intake`, `coordination`, and `quality_signals` as the next largest fields. Do not claim this slice verified until the startup packet is reduced below budget or a scoped blocker is recorded.

## Claude Status

- F5 structural fix landed in `dev/scripts/devctl/runtime/startup_governance_projection.py`: `_startup_plan_entry_dict` now projects 6 fields per entry (`path`, `title`, `artifact_role`, `consumer_scope`, `when_agents_read`, `scope`) plus the optional `session_resume_summary`; dropped `role`, `authority_kind`, `system_scope`, `authority`, `lifecycle`, `has_execution_plan_contract` from the bootstrap projection only.
- Live size: `build_startup_context().to_dict()` is now `38653` bytes (`~9663` tokens), `337` tokens of headroom under the `<10000` budget. `governance.to_dict()` and the markdown renderer still see the full `ProjectGovernance.plan_registry.entries` dataclass, so the trim is scoped to the single startup projection.
- Assignments use the incremental-assignment idiom already used by `bounded_contract_ownership_map` so `python-dict-schema-guard` stays clean; budget constraint is explained in the helper docstring.
- F1 regression added: `TestCoordinationParityF1.test_three_surfaces_report_identical_coordination` in `dev/scripts/devctl/tests/runtime/test_startup_context.py` builds `build_startup_context`, `build_control_plane_read_model`, and `build_from_sources` against one `scan_repo_governance` result and asserts parity on `declared_topology`, `observed_topology`, `recommended_topology`, `ownership_status`, `current_slice`, `fanout_posture`, `safe_to_fanout`, `resync_required`, and `resync_reasons`.
- F4 regression already covered in `dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py::TestScanRepoGovernanceFailClosed` (empty-policy, explicit `remote_control`, explicit `dual_agent`, garbage-value cases); live proof on this head: `scan_repo_governance(policy={}).bridge_config.operator_interaction_mode` and `bridge_config_from_mapping({}).operator_interaction_mode` both return `unresolved`.
- Focused suite: `python3 -m pytest dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_startup_context.py dev/scripts/devctl/tests/governance/test_session_resume.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short` → `458 passed` (was `1 failed, 456 passed`).
- Tooling verification: `check --profile ci` → `python-dict-schema-guard` clean after the incremental-assignment fix. The 2 remaining failures (`startup-authority-contract-guard` with `reason=review` and `tandem-consistency-guard` `launch_truth: No live repo-owned Codex or Claude conductor sessions`) are pre-existing live-review-loop state, not caused by this diff.

## Claude Questions

- None recorded.

## Claude Ack

- acknowledged current instruction revision: `64b45d5fd553`

## Current Instruction For Claude

Scoped from `dev/active/remote_control_runtime.md` via `--scope`.

- F1 and F4 are verified closed on the live code path. Do not reopen the coordination-loader or scan-governance work unless a new parity proof fails.
- Finish F5 by shrinking `build_startup_context().to_dict()` below the `<10000` token budget without weakening the guard. The exact suite currently reports `10521` tokens, and the largest contributors are `governance`, `work_intake`, `coordination`, and `quality_signals`.
- Keep the fix structural, not test-only: reduce the governed startup packet shape or project a slimmer startup payload. Do not raise the budget and do not delete the regression.
- Re-run `python3 -m pytest dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_startup_context.py dev/scripts/devctl/tests/governance/test_session_resume.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short` and keep working until it is green. If the budget still cannot be met without reopening contract scope, record a scoped blocker with the exact oversized fields before handoff.
- Then run the required tooling verification bundle before handoff.

## Last Reviewed Scope

- Reviewed code-carrying range `81cff0d87d8d20b871a71d69dd69a7eb2116b0fe..c674367819cc8c41f9da6ae8c3a7cb72a0d7638a`, plus docs-only follow-up `06d591c0fc1f444215d8bed37d08ccf620ac3f06` that landed during review. `06d591c0` changes `dev/audits/LIVE_RUN.md` and `dev/audits/REVIEW_SNAPSHOT.md` only; it does not add new F1/F4 code.
- Code paths reviewed: `dev/scripts/devctl/runtime/startup_context.py`, `dev/scripts/devctl/governance/draft_policy_scan.py`, `dev/scripts/devctl/runtime/coordination_loader.py`, `dev/scripts/devctl/tests/runtime/test_coordination_loader_wiring.py`, `dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py`, `dev/scripts/devctl/tests/runtime/test_startup_context.py`, `dev/scripts/devctl/tests/governance/test_session_resume.py`, `dev/scripts/devctl/tests/test_dashboard.py`.
- Live F1 proof on this tree: `startup-context --role reviewer --format json`, `session-resume --role reviewer --format json`, and `dashboard --format json` all report `declared_topology=multi_agent_orchestrated`, `observed_topology=dual_agent`, `recommended_topology=single_agent`, `ownership_status=clear`, and the same `resync_reasons` tuple.
- Live F4 proof on this tree: `scan_repo_governance(repo, policy={}).bridge_config.operator_interaction_mode` and `bridge_config_from_mapping({}).operator_interaction_mode` both return `unresolved`.
- Focused validation: `python3 -m pytest dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py dev/scripts/devctl/tests/runtime/test_control_plane_read_model.py dev/scripts/devctl/tests/runtime/test_startup_context.py dev/scripts/devctl/tests/governance/test_session_resume.py dev/scripts/devctl/tests/test_dashboard.py -q --tb=short` -> `1 failed, 456 passed`; failing test: `dev/scripts/devctl/tests/runtime/test_startup_context.py::TestStartupContextBuild::test_slim_token_budget` (`10521` tokens).

## Action Requests

- **Re-scope Claude-CLI's instruction to include Q-series findings.** Claude-CLI only sees F1/F2/F3 (baked into launch prompt); has NOT picked up Q1-Q21 from `dev/audits/LIVE_RUN.md`. Priority: Q20 (packet transport broken), Q12 (deserializer), Q1 (devctl commit self-block), Q9/Q10/Q21 (mode TTL).
- **Retire `dev/audits/LIVE_RUN.md` once packet transport round-trips cleanly.** Emergency workaround for Q20; once `review-channel post + inbox` round-trips 100% and Q11/Q12 are fixed, findings should flow through the typed receipt system.
