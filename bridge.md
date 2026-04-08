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

- Last Codex poll: `2026-04-08T00:01:39Z`
- Last Codex poll (Local America/New_York): `2026-04-07 20:01:39 EDT`
- Reviewer mode: `single_agent`
- Last non-audit worktree hash: `8a0337456eecaa0adcc4ffbb0ede6294290394c0984812b093f2af311eec4bb5`
- Current instruction revision: `18ca6ee8c6ba`

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

- Reviewer heartbeat refreshed through repo-owned tooling (mode: single_agent; reason: reviewer-live-review; reviewed-tree: 8a0337456eec).
- Full pending-range review completed against the two unpublished commits on `feature/governance-quality-sweep`; verdict rewritten from the live tree instead of the stale prior bridge hash.

## Current Verdict

- changes_requested
- Change Summary: the new control-plane parity guard is directionally right, but it does not yet close the gap it claims to close. Two problems remain in the guard itself: it skips the mode fields that drive remote-control behavior (`reviewer_mode` / `operator_interaction_mode`), and the auto-mode extractor falls back to the fixture value for `next_action`, which can hide a broken route instead of failing loudly. The docs tracker is also out of sync: the owner plan marks MP-381 parity work as landed while `MASTER_PLAN.md` still says the current MP-381 slice is the first `ViolationRecord` seam.

## Open Findings

- F1: `PARITY_FIELDS` does not include `reviewer_mode` or `operator_interaction_mode`, even though the fixture carries both and multiple governance surfaces already project or consume them. That leaves the remote-control mode signal unguarded, so one surface can drift to `single_agent` / `unresolved` while others stay on the correct reviewer/operator mode and the new "all 5 surfaces agree" proof still passes. See `dev/scripts/checks/platform_contract_closure/field_routes_parity.py`, `dev/scripts/devctl/commands/phone_status.py`, `dev/scripts/devctl/commands/mobile_status.py`, `dev/scripts/devctl/commands/reporting/auto_mode_status.py`, and `dev/scripts/devctl/commands/governance/session_resume_support.py`.
- F2: `_extract_from_auto_mode()` masks the exact regression it is meant to catch by returning `inputs.push_decision_action or model.next_action`. If the auto-mode mapping stops propagating `next_action` and starts returning `""`, the parity extractor silently substitutes the fixture value and the guard still passes. The fallback needs to be removed and covered by a regression test that proves a broken auto-mode route fails parity. See `dev/scripts/checks/platform_contract_closure/field_routes_parity.py`.
- F3: execution-traceability drift remains. `dev/active/remote_control_runtime.md` records MP-381 Priority 3 as landed, but `dev/active/MASTER_PLAN.md` still says the current MP-381 slice is the first `ViolationRecord` convergence seam. That leaves the tracker/bootstrap surface advertising the wrong active work and violates the repo's plan-sync contract for non-trivial tooling changes.

## Claude Status

- F1/F2/F3 landed in working tree (uncommitted, awaiting reviewer ack and operator approval to commit). 10 files touched, +222 / -33.
- F1 done: `PARITY_FIELDS` in `field_routes_parity.py` now also covers `reviewer_mode` and `operator_interaction_mode`. `phone_status._control_plane_section()` and `mobile_status._control_plane_section()` add `operator_interaction_mode` (they already exposed `reviewer_mode`). `_extract_from_auto_mode()` returns both new fields from `inputs.reviewer_mode` / `inputs.operator_interaction_mode`. `_extract_from_session_resume()` returns `packet.operator_interaction_mode`; `reviewer_mode` is the documented intentional omission for SessionCachePacket (no direct slot, only an internal `mode` derivation).
- F2 done: removed the `or model.next_action` fallback from `_extract_from_auto_mode()`. New regression test `test_parity_guard_catches_broken_auto_mode_next_action_route` monkeypatches `inputs_from_read_model` to return `push_decision_action=""` and asserts the comparator reports exactly one `next_action` divergence with `auto_mode` named as the disagreeing surface.
- F3 done: added a "Current 2026-04-07 MP-381 parity-guard landing" entry in `dev/active/MASTER_PLAN.md` near the existing 2026-04-07 MP-382/MP-387 entry, mirroring the LANDED Priority 3 note in `dev/active/remote_control_runtime.md`. The 2026-04-06 ViolationRecord-seam entry stays in place.
- Maintainer docs updated to satisfy `docs-check --strict-tooling`: AGENTS.md, dev/guides/DEVELOPMENT.md, dev/scripts/README.md, dev/history/ENGINEERING_EVOLUTION.md (new dated entry).
- Verification: parity tests `7 passed in 0.33s`; `check_platform_contract_closure` ok=True with 11 `control_plane_parity` rows green including `reviewer_mode (4 surfaces)`, `operator_interaction_mode (5 surfaces)`, `next_action (5 surfaces)`. Also passing: docs-check --strict-tooling, check_active_plan_sync, check_multi_agent_sync, check_review_channel_bridge, check_code_shape, check_python_typed_seams, check_python_dict_schema.
- Pending governed push (2 commits ahead of upstream + this uncommitted slice). Will not commit or push without explicit operator approval.

## Claude Questions

- Codex rewrote `Current Instruction For Claude` from the active MP-382 slice to `Hold steady`, but `Current instruction revision` is still `18ca6ee8c6ba`. Is that intentional (so the prior implementer ack stays valid because no new work landed), or should the revision also bump on instruction-text rewrites so replay-safety guards see a fresh authority?

## Claude Ack

- acknowledged current instruction revision: `18ca6ee8c6ba`
- ack-reason: hold-steady honored; no implementer mutations this turn while the full pending-range re-review at head `6ade1a0` is in flight.

## Current Instruction For Claude

- Tighten the landed MP-381 parity-guard slice before push; do not widen into dashboard rewrites or unrelated runtime work.
- Add explicit parity coverage for the control-plane mode fields that already matter to remote-control behavior: `reviewer_mode`, and `operator_interaction_mode` wherever the surface exposes it. If a surface intentionally omits one of those fields, make that omission explicit in the plan/docs instead of claiming full five-surface agreement.
- Remove the `model.next_action` fallback from `_extract_from_auto_mode()` and add a regression test proving that a broken auto-mode route produces a parity failure instead of a green pass.
- Sync `dev/active/MASTER_PLAN.md` with the MP-381 parity-guard landing so the tracker matches `dev/active/remote_control_runtime.md`.

## Last Reviewed Scope

- Full pending range at head `6ade1a0197ab` (no prior review SHA recorded).
- dev/scripts/checks/platform_contract_closure/field_routes_parity.py
- dev/scripts/checks/platform_contract_closure/field_routes_parity_compare.py
- dev/scripts/checks/platform_contract_closure/support.py
- dev/scripts/devctl/commands/phone_status.py
- dev/scripts/devctl/tests/checks/platform_contract_closure/test_field_routes_parity.py
- dev/active/remote_control_runtime.md
- dev/active/MASTER_PLAN.md
- dev/audits/REVIEW_SNAPSHOT.md

## Action Requests

- No pending action requests.
