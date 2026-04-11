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

- Last Codex poll: `2026-04-11T08:24:32Z`
- Last Codex poll (Local America/New_York): `2026-04-11 04:24:32 EDT`
- Reviewer mode: `single_agent`
- Last non-audit worktree hash: `323ca380bac93223394f94fce0f485536bc1d6c7b1d828bd44fc12a5051d6607`
- Current instruction revision: `214e376fabc0`
- Last checkpoint action: `reviewer-checkpoint`
- Head at push time: `e1dac6168b6da235267c902e5c19ce690dff8322`
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

Active slice: Q98/Q99 startup-context integration delta + Codex's two P1
regressions on the same startup path. Q37 is closed upstream (`efcb2cd9`);
do not follow that lane. The reviewer-owned sections below
(Current Verdict, Open Findings, Current Instruction For Claude,
Last Reviewed Scope) are authoritative for adjudication state.

### Priority order for the implementer
1. **P1 — `dev/scripts/devctl/runtime/work_intake_pacing.py:158-176`** — fix
   the work-intake pacing regression surfaced by Codex. Treat the reviewer's
   open finding as the canonical spec.
2. **P1 — `dev/scripts/devctl/commands/governance/startup_context.py:48-108`**
   — fix the second startup regression Codex flagged on the same session.
3. **Q98/Q99 integration delta** — land the typed startup projection work
   described in `dev/audits/LIVE_RUN.md` sections Q98 and Q99. Route every
   `top_blocker` / `next_action` decision through
   `dev/scripts/devctl/runtime/startup_blocker_decision.py` (kernel landing
   in parallel via Coder C).

### Constraints
- Do NOT hand-edit reviewer-owned sections. Use typed `review-channel --action
  post` packets for findings/blockers.
- Claude (privileged terminal) owns all `git commit` / governed push.
- Rerun `startup-context --format summary` after each commit; follow
  `push_decision` as the next-remote-action state machine.

## Poll Status

- Reviewer checkpoint updated through repo-owned tooling (mode: single_agent; reason: codex-review-snapshot-gating; observed-tree: 323ca380bac9; reviewed-tree: 323ca380bac9; instruction-rev: 214e376fabc0).

## Current Verdict

- Follow-up required before acceptance.
- The review range `3c294f0d..e1dac616` still has one blocking issue: the new review-snapshot gate does not actually block governed push guidance in the current `single_agent` reviewer lane when the live reviewer verdict is follow-up required.

## Open Findings

- `dev/scripts/devctl/runtime/review_snapshot_state.py:107-137` only downgrades `push_eligible_now` and the governed push `next_step_command` when `effective_reviewer_mode == active_dual_agent` or `implementation_blocked=True`. In the current `single_agent` remote-control lane, a follow-up-required verdict (`review_accepted=False` or `review_gate_allows_push=False`) still falls through and preserves the push command, so the Q92 regression can recur as soon as the branch is ahead again. Add a `single_agent` regression test and gate the snapshot on the live reviewer verdict rather than dual-agent mode alone.

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

- Hold steady. Do not run `python3 dev/scripts/devctl.py push --execute`.
- Fix `dev/scripts/devctl/runtime/review_snapshot_state.py:107-137` so reviewer-verdict gating also downgrades governed push projections in the current `single_agent` remote-control lane when `review_accepted=False` or `review_gate_allows_push=False`.
- Add a regression test in `dev/scripts/devctl/tests/runtime/test_review_snapshot.py` covering the `single_agent` follow-up-required case.
- Rerun `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary`, `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`, `python3 dev/scripts/devctl.py review-snapshot --write --format md`, and the required tooling bundle, then request a fresh Codex review on the updated diff.

## Last Reviewed Scope

- 3c294f0d44379460274ed4b85675d2bd9a0161df..e1dac6168b6da235267c902e5c19ce690dff8322
- bridge.md
- dev/audits/REVIEW_SNAPSHOT.md
- dev/scripts/devctl/commands/governance/startup_context.py
- dev/scripts/devctl/review_channel/write_preconditions.py
- dev/scripts/devctl/runtime/review_snapshot_state.py
- dev/scripts/devctl/runtime/startup_blocker_decision.py
- dev/scripts/devctl/runtime/work_intake_pacing.py
- dev/scripts/devctl/tests/runtime/test_review_snapshot.py

## Action Requests

- No pending action requests.
