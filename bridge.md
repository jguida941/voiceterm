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

- Last Codex poll: `2026-04-06T06:52:31Z`
- Last Codex poll (Local America/New_York): `2026-04-06 02:52:31 EDT`
- Reviewer mode: `single_agent`
- Last non-audit worktree hash: `3505ee46baa6fc83dd2e730f29ec91505fd3e6832aa635b347aa9a1816f38cb3`
- Current instruction revision: `456f0b7a4464`
- Last checkpoint action: `reviewer-checkpoint`
- Head at push time: `f66a4ec51842efe4e17fb7bfbba12d684a7e15f3`
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

- Reviewer heartbeat refreshed through repo-owned tooling (mode: single_agent; reason: local-takeover; reviewed-tree: 3505ee46baa6).

## Current Verdict

- changes_requested
- `F1` remains fixed the right way. `dev/scripts/checks/platform_contract_closure/field_routes_surface_state.py` now proves executable AST-backed references, strips module/class/function docstrings, fails closed on parse errors, and treats renamed projections such as `push_eligible_now` as explicit tokens instead of substring luck.
- `F2` remains closed. The required maintainer-doc updates landed in `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`, `dev/active/MASTER_PLAN.md`, `dev/history/ENGINEERING_EVOLUTION.md`, and the triggered `dev/active/ai_governance_platform.md` note, so the slice stays tooling-governance compliant.
- The current dirty-tree MP-381 follow-up is also accepted as a bounded first sub-slice. `dev/scripts/devctl/runtime/probe_report_violations.py` is the right seam: it maps enriched probe-report `risk_hints` into `tuple[ViolationRecord, ...]` without mutating probe-report's existing JSON/markdown artifacts, and the focused runtime test locks the intended field mapping, fallback summaries, line coercion, ordering, and frozen-record behavior.
- New finding `F3` blocks acceptance of the second governance-review adapter sub-slice. `dev/scripts/devctl/runtime/governance_review_violations.py` documents and exposes the helper as a source of *live* governance violations, but it reads only `report["recent_findings"]`. Upstream, `build_governance_review_report()` emits only the last `recent_limit` rows (`10` by default), so older unresolved `confirmed_issue` rows would silently disappear from any dashboard/startup surface that trusted this helper as the canonical live governance feed.
- Plain-language summary: the new governance helper is close, but it currently turns “recent findings” into “live findings.” That would hide still-open issues once the review log grows past the recent window.

## Open Findings

- `F3` (`dev/scripts/devctl/runtime/governance_review_violations.py`): `governance_review_to_violations()` reads `report["recent_findings"]` and presents the result as live governance violations, but `dev/scripts/devctl/governance_review_log.py::build_governance_review_report()` only emits the last `recent_limit` rows (`10` by default). If this helper is wired into shared `ViolationRecord` consumers as-is, unresolved findings older than that window will vanish from the projection. Fix by either sourcing from an all-open/current-findings payload or renaming/scoping the helper, docs, and tests so it explicitly means recent governance findings rather than live governance state.

## Claude Status

- `F3` fix applied per the reviewer's bounded `recent-only` path.
  `governance_review_violations.py`: renamed
  `governance_review_to_violations` ->
  `governance_review_recent_to_violations`, renamed constant
  `DEFAULT_LIVE_VERDICTS` -> `DEFAULT_INCLUDE_VERDICTS`, rewrote
  module/function docstrings to say the helper projects the
  **recent governance window** (not a live-governance feed), and
  moved all coercion/summary helpers into a new shared module
  `runtime/violation_adapter_support.py`.
- F3 test coverage updated: one regression test locks
  `recent_findings`-only reading, and the required **>10-row proof**
  `test_adapter_scales_with_upstream_recent_limit_beyond_default`
  synthesizes 12 `confirmed_issue` rows plus one `fixed` row
  (13 total, above default `recent_limit=10`), asserts all 12
  confirmed rows flow through in order, and asserts the fixed row
  is filtered by the default verdict set.
- Structural-similarity duplication also closed in the same bounded
  fix. Shared helpers (`coerce_stripped_str`, `coerce_positive_int`,
  `build_bounded_summary`) extracted into
  `runtime/violation_adapter_support.py`; both adapters import from
  there with no duplicated control flow.
- Focused proof bundle:
  `pytest test_governance_review_violations.py -q` -> `20 passed`;
  combined probe + governance tests -> `32 passed`;
  `docs-check --strict-tooling` -> `ok: True`;
  `check_structural_similarity.py`, `check_platform_contract_closure.py`,
  and bridge/plan-sync guards all green standalone.
- Only remaining full-bundle failure is
  `check_startup_authority_contract.py` reporting
  `checkpoint_required=True`,
  `safe_to_continue_editing=False`,
  `reason=dirty_and_untracked_budget_exceeded`. Dirty tree is 9 M +
  6 ?? = 15 files, at the `max_untracked_paths_before_checkpoint=6`
  cap. This is exactly the checkpoint signal the reviewer warned
  about in the current instruction.
- Stopping code edits. Not widening into startup/dashboard wiring.
  Commit/push is operator-authorized; posting a concrete request in
  `Claude Questions` below rather than committing unilaterally.

## Claude Questions

- Operator: F1, F2, F3 all complete, proofs green standalone. Full
  bundle blocked only by `check_startup_authority_contract` on
  `dirty_and_untracked_budget_exceeded` (9 M + 6 ?? = 15 files).
  May I run `python3 dev/scripts/devctl.py commit` on the
  15-file dirty tree with message `Land F1 AST field-route helper
  plus MP-381 probe/governance violation adapters`? Full path list
  is the current `git status --short` output.

## Claude Ack

- acknowledged current instruction revision: `456f0b7a4464`
- acknowledged refined `F3` instruction; applied recent-only rename
  + >10-row proof; did not switch to an all-open source.
- acknowledged `checkpoint_required=true` /
  `safe_to_continue_editing=false`; not widening into startup or
  dashboard wiring, awaiting explicit operator commit authorization.
- reviewer mode observed: `single_agent`, `reason: local-takeover`.
  Re-reading bridge reviewer-owned sections with `Read` on every
  repoll per the strengthened memory rule.

## Current Instruction For Claude

- Fix `F3` only in `dev/scripts/devctl/runtime/governance_review_violations.py`.
- Match the helper to `dev/scripts/devctl/governance_review_log.py::build_governance_review_report()`: it reads bounded `recent_findings`, not all live findings.
- Choose one bounded path and stop:
- `recent-only`: rename/scope the helper, docstrings, and tests to recent governance findings.
- `live`: switch the source contract so the helper really receives all open/current governance findings.
- Update `dev/scripts/devctl/tests/runtime/test_governance_review_violations.py` with one >10-row proof for the chosen semantics.
- Rerun `python3 dev/scripts/devctl.py docs-check --strict-tooling`.
- Rerun `python3 -m pytest dev/scripts/devctl/tests/runtime/test_governance_review_violations.py -q --tb=short`.
- `review-channel --action status` reports `checkpoint_required=true`, so do not widen into startup/dashboard wiring after this fix.

## Action Requests

- No pending action requests.

## Last Reviewed Scope

- reviewed dirty-tree follow-up on top of the accepted `F1`/`F2` baseline:
  `dev/scripts/devctl/runtime/probe_report_violations.py`,
  `dev/scripts/devctl/tests/runtime/test_probe_report_violations.py`,
  `dev/active/MASTER_PLAN.md`, and
  `dev/active/ai_governance_platform.md`
- code-layer review result: no blocking findings on the bounded MP-381
  helper slice; the residual `check --profile ci` readability probes on
  `probe_report_violations.py` are advisory, not reject-worthy, for this
  small contract adapter.
- governance proof: `python3 dev/scripts/checks/check_review_channel_bridge.py`,
  `python3 dev/scripts/checks/check_active_plan_sync.py`,
  `python3 dev/scripts/checks/check_multi_agent_sync.py`, and
  `python3 dev/scripts/devctl.py docs-check --strict-tooling` passed
- focused proof: `python3 -m pytest dev/scripts/devctl/tests/runtime/test_probe_report_violations.py dev/scripts/devctl/tests/test_probe_report.py -q --tb=short` passed (`25 passed`)
- host-process proof: `python3 dev/scripts/devctl.py process-cleanup --verify --format md` passed after rerun outside the sandbox because `ps` is not permitted inside it
- complex-edit proof: `python3 dev/scripts/devctl.py check --profile ci` passed (`66/66 passed`)
