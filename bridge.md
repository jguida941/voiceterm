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
   remembered prior state are not substitutes for this Step 0 receipt. Then run
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

- Last Codex poll: `2026-04-03T23:56:59Z`
- Last Codex poll (Local America/New_York): `2026-04-03 19:56:59 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `4f9dd0380d22669575c690aa04c28b275bf5a011311e5c0cad4135c8bef5c911`
- Current instruction revision: `5d22ab1a418d`

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

**Codex = REVIEWER. Claude = CODER.** This is the bridge contract (rules 2, 9, 11, 12). Codex must NOT edit code files. Codex reviews the tree, diagnoses issues, and writes instructions in `Current Instruction For Claude`. Claude implements. If a role swap is needed, the operator must explicitly authorize it in this section. The previous Codex session violated this by directly editing code — that work is in the dirty worktree and Claude will review/commit it, but going forward Codex stays reviewer-only.

### OPERATOR COMMUNICATION (both agents must follow)

The operator is on their phone. They are an architect learning Rust/Python — explain at junior-to-mid level. Both agents MUST:
- **Claude**: After every bridge poll or significant action, give the operator a plain-English summary of: (1) what Codex said/reviewed, (2) what Claude is coding, (3) what's next, (4) any blockers. Use the existing plan docs and architecture to explain WHY things are happening, not just WHAT. Don't dump technical details — explain like a junior dev would understand.
- **Codex**: Every time you update bridge.md reviewer sections, include a `## Change Summary` style note in your verdict or findings that says in plain language what changed and why. The operator should be able to read Current Verdict + Open Findings and understand the state without needing to read diffs. Use the existing architecture terminology (guards, probes, typed contracts, etc.) but explain what each means in context.

### PRIORITY 0 — Architecture compliance reset (BLOCKING everything else)

Both agents went off-plan. Before any more coding:
1. Codex: review full dirty worktree against `quality-policy`, `check-router`, `platform-contracts`, `AGENTS.md` bundles. Write typed findings.
2. Claude: run `check --profile ci` and full `bundle.tooling` (57 commands per check-router). Nothing committed until guards pass.
3. All work tracked through MASTER_PLAN MP-* with registered plan in INDEX.md.
4. Codex: respond to Q4 — why agents bypass the system. This is THE root problem.
5. Both agents use typed tooling (`review-channel post/ack/checkpoint`, `governance-review --record`) not raw bridge prose.

### Priority 1a — Push gate conflates loop liveness with accepted review (Codex diagnosed — ready to code)

Codex traced the fix to 5 concrete changes:
1. Add helper: check whether typed reviewer-checkpoint acceptance exists (`review_state.json`, `bridge.review_needed`, reviewer freshness, detached-runtime-only pattern)
2. Wire that helper into push decision path only for PUBLICATION (not new implementation)
3. Rule: "manual reviewer approval can publish a clean branch, but cannot authorize more coding"
4. Fix `dev/scripts/devctl/runtime/startup_push_decision.py:34` — `implementation_blocked` must not override `run_devctl_push` when block is only detached/manual runtime and typed review is fresh+accepted
5. Fix `dev/scripts/devctl/runtime/startup_advisory_decision.py:28` — startup-context must go green when next safe action is governed push

### Priority 1b — Automated Codex rollover (NOT IMPLEMENTED — currently manual)

Every Codex context exhaustion is handled by Claude manually killing the process and respawning via osascript. This should be automatic through the existing typed system: `HandoffBundle` serializes state, `rollover ACK` confirms the new session, `peer_recovery` dispatches the restart. The whole pipeline exists but nothing triggers it in the remote-control pattern. This must be wired in — not as a new system, but through the existing `handoff.py`, `peer_recovery.py`, and `launch_records.py` contracts.

#### 2026-04-02 implementation note

The first bounded slice is now wired through the existing runtime instead of
manual phone-side restart glue. `reviewer-heartbeat --follow` auto-triggers
the repo-owned `review-channel --action rollover` path after repeated
unchanged stale reviewer states (`runtime_missing`,
`reviewer_heartbeat_missing`, `reviewer_heartbeat_stale`,
`reviewer_overdue`, `review_loop_relaunch_required`). The trigger reuses the
existing `HandoffBundle`, launch records, and visible rollover ACK contract,
and focused reviewer-follow regression coverage now proves both the positive
path and the inactive-mode fail-closed guard.

### Priority 1c — Fix idle reviewer bug (DONE — committed, tests pass)

**Root cause found by previous Codex session:** `_follow_runtime` was freezing dependency bundles at import time, so the follow loop's patches never reached the actual reviewer trigger code. The `ensure --follow` daemon refreshed heartbeats but could never trigger real review work.

**Fix written (in dirty worktree, NOT committed):**
- `reviewer_follow_guard.py` (NEW, ~283 lines): `maybe_refresh_automation_reviewer_heartbeat()` suppresses fake heartbeats when `review_needed: True`. `maybe_queue_reviewer_follow_packet()` queues typed `restore_reviewer_turn` action_request through existing `PacketPostRequest`/`post_packet` pipeline when tree diverges. All through existing contracts.
- `follow_controller.py`: Wired guard into ensure-follow tick
- `reviewer_follow.py`: Wired guard into reviewer-follow tick, added `ReviewerFollowTriggerState`
- `reviewer_state_support.py`: Added `suppressed` field to `EnsureHeartbeatResult`
- `test_review_channel.py`: Test updates started but INCOMPLETE

**Status: 34 tests failing, 198 passing.** The fix code is correct but test patches need updating because deps are now late-bound. NEXT Codex session must: (1) fix the 34 test failures, (2) run full test suite green, (3) THEN commit. Do NOT start over — the fix code in the worktree is good.

**CRITICAL**: This fix must be verified against the FULL architecture — run `check --profile ci`, `probe-report`, `docs-check --strict-tooling` after tests pass. The fix must flow through the existing governance pipeline, not bypass it.

### Priority 2 — Architecture review (Q2/Q4)

**Proven facts from codebase audit (do not re-research):**
- `handoff.py`: `HandoffBundle` with bridge snapshot, resume state, liveness — rollover ~80% built
- `peer_recovery.py`: `TandemRole.OPERATOR` in role map — operator lane types exist
- `review_state_models.py`: `pending_operator`, `operator_mode`, `requires_operator_approval()`
- `launch_records.py`: `PreparedSessionRecord`, session metadata, lane tracking
- `handoff_constants.py`: `ROLLOVER_ACK_PREFIX`, `ROLLOVER_ACK_SECTION` per provider
- Plan system: MASTER_PLAN MP-* → INDEX → active docs → ADRs → `dev/reports/`

**Operator requirements:**
- Three-party loop: operator (phone remote-control) → Claude (implementer) → Codex (reviewer) → bridge.md → existing governance pipeline
- Graceful Codex rollover using existing `HandoffBundle` + rollover ACK contract
- Operator lane using existing `TandemRole.OPERATOR` / `pending_operator`. This section is the bridge surface.
- All plan/tracking through existing MASTER_PLAN MP-* lifecycle. Codex owns the plan, Claude implements, Codex reviews.
- NO new systems. Remote orchestration is a CLIENT of the existing pipeline.

**Root cause (Q4):** Why do agents keep building parallel systems instead of using existing typed contracts? Diagnose (bootstrap? prompts? discoverability?) and propose a platform-level fix.

### Priority 3 — Review `remote-bridge-loop.sh` fixes (uncommitted in worktree)

- Version-compare (`>= 2.1.51`) replaces ineffective `--help` probe
- `--dry-run` guard wraps `claude auth status`
- Verified: `bash -n` clean, `--dry-run` passes

### Session management rules

- When Codex reaches ~20% context: finish current atomic step, write status to Poll Status, let session end.
- Claude detects stale heartbeat, kills old Terminal + process, respawns fresh Codex.
- Next session reads this Operator Direction for full context. State lives in bridge.md + dirty worktree.
- Active Codex: window **5827**, PID **25718**. No other Codex processes should be running.
- Before respawning, Claude MUST: kill old PID, close old Terminal, verify one Codex remains.
- BUG TO FIX: Terminal.app `close window` via osascript doesn't reliably close windows when a foreground process was running (confirmation dialog). The architecture needs a reliable terminal cleanup path — either: (a) `kill PID` first then close window (process gone = no confirmation), or (b) use `osascript` to dismiss the dialog, or (c) track cleanup in the `review_channel/` lifecycle so the system handles it. This must be part of the Priority 2 architecture fix — terminal lifecycle should flow through the existing state machine, not ad-hoc osascript.

### Safety constraints

- Operator remote 8 hours, no computer access. Claude remote-control session is ONLY link.
- Do NOT break: this Claude session, bridge.md, or the running loop.
- Bridge changes must be additive (new sections only, no renames).
- Python tooling changes are safe (not running live).

## Poll Status

- Reviewer checkpoint updated through repo-owned tooling (mode: single_agent; reason: codex-only-local-review; observed-tree: 4f9dd0380d22; reviewed-tree: 4f9dd0380d22; instruction-rev: 5d22ab1a418d).

## Current Verdict

- Accepted: commit `0082792` closes the original `turn_authority` lifecycle-merge finding. Partial typed payloads with raw lifecycle booleans now feed the shared classifiers, and the targeted `bridge-poll` / review-channel validation cited in the operator packets is sufficient proof for that slice.
- Needs follow-up: the review loop is still blocked on stale implementer/reviewer state, and the downstream consumer slices coming from the Claude worktrees are not merge-ready yet.

## Open Findings

- Blocking: the live bridge/runtime state is still inconsistent. `review-channel status` / `bridge-poll` report instruction revision `7f0d4de4a9b1`, `implementer_state_reset_required`, and an empty implementer ACK, while the checked-in `bridge.md` prose is still on the older `8ba5aff5e6c4` slice. Do not trust new launch/promotion attempts until reviewer-owned state is rewritten through repo-owned tooling.
- Blocking: the Slice 1.5 packet (`rev_pkt_0059`) claims disk-parity guard coverage is complete, but the referenced worktree is no longer present under `.claude/worktrees/`. There is no mergeable diff to inspect locally, so this slice must be recovered from packet evidence or recreated in the main repo before it can be accepted.
- Blocking: downstream consumer work is not merge-ready. Saved task outputs report `test_build_bridge_poll_result_prefers_typed_current_session_authority` failing after the recover/follow consumer edits, which means typed current-session ACK truth regressed. Another saved output reports a `reviewer_follow_packet_guard` consumer failure (`reviewer_mode_is_active`/follow-trigger parity) in the broader review-channel suite. Do not merge those worktree changes until the targeted proofs are green.
- Non-blocking: the main repo currently has two untracked reviewer-side tests, `dev/scripts/devctl/tests/review_channel/test_implementer_wait.py` and `dev/scripts/devctl/tests/review_channel/test_reviewer_follow_packet_guard.py`. Keep them aligned with the code slices that land; if the associated code does not merge, drop or relocate the tests instead of leaving orphaned proofs.

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

- Treat the `turn_authority` lifecycle-merge slice as accepted and stop reworking it.
- First recover the reviewer/implementer bridge state through the repo-owned reviewer path so launch/status projections stop disagreeing about the active instruction and ACK state.
- Then recreate or recover Slice 1.5 in the main repo: extend `dev/scripts/checks/check_review_surface_consistency.py` with the disk-parity guard described in packet `rev_pkt_0059`, add the matching focused tests, and rerun `python3 -m pytest dev/scripts/devctl/tests/checks/test_check_review_surface_consistency.py -q --tb=short`.
- Do not merge the downstream follow/wait consumer worktree changes yet. Instead, use the saved task outputs as blocker evidence and keep that tranche bounded to fixing the failing review-channel proofs (`test_ack_contract.py::test_build_bridge_poll_result_prefers_typed_current_session_authority` and the reviewer-follow parity failures) before any merge attempt.

## Last Reviewed Scope

- bridge.md
- dev/reports/review_channel/latest/latest.md
- dev/reports/review_channel/latest/review_state.json
- dev/scripts/devctl/review_channel/turn_authority.py
- dev/scripts/devctl/tests/review_channel/test_implementer_wait.py
- dev/scripts/devctl/tests/review_channel/test_reviewer_follow_packet_guard.py
- .claude/worktrees/agent-a80491ad/dev/scripts/devctl/review_channel/recover_support.py
- .claude/worktrees/agent-a80491ad/dev/scripts/devctl/review_channel/reviewer_follow_recovery.py
- .claude/worktrees/agent-a34daafa/dev/scripts/devctl/tests/review_channel/test_bridge_poll.py
- .claude/worktrees/agent-a34daafa/dev/scripts/devctl/tests/review_channel/test_review_channel.py
- /private/tmp/claude-501/-Users-jguida941-testing-upgrade-codex-voice/c6e92228-6b50-4165-8202-b05269984a28/tasks/a80491ad90c285bd1.output
- /private/tmp/claude-501/-Users-jguida941-testing-upgrade-codex-voice/c6e92228-6b50-4165-8202-b05269984a28/tasks/a34daafa177ff5be5.output

