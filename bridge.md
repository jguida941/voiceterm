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

- Last Codex poll: `2026-04-10T05:37:36Z`
- Last Codex poll (Local America/New_York): `2026-04-10 01:37:36 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `7ac7a814b0e333ed9ff42d91c957eb0eab9fca25d922aa9024b62311aec069d4`
- Current instruction revision: `f27dccca4082`
- Last checkpoint action: `reviewer-checkpoint`
- Head at push time: `c06cf533ef27efb145f53f0d13e5069eba18cfaf`
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



## Poll Status

- Reviewer checkpoint updated through repo-owned tooling (mode: active_dual_agent; reason: review-finding-f3-startup-gate-bypass; observed-tree: 7ac7a814b0e3; reviewed-tree: 7ac7a814b0e3; instruction-rev: f27dccca4082).

## Current Verdict

Follow-up required before acceptance: F1 and F2 are resolved in the current tree, but F3 remains blocking for the startup-gate repair slice.

## Open Findings

F3 blocking: `command_requires_startup_gate()` still returns `False` for `review-channel launch` and `rollover` when `_is_repair_launch()` sees `receipt.advisory_action == "repair_reviewer_loop"`. Because `enforce_startup_gate()` exits before loading the startup report, a repair receipt can bypass receipt freshness, checkpoint budget, and live authority checks instead of being allowed only after those checks. The new test also encodes the bypass expectation instead of proving stale or checkpoint-required repair receipts still block.

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

- Fix F3 before asking for re-review. Keep the dataclass crash fix and docs-check closure intact, but move or constrain the `repair_reviewer_loop` allowance so `review-channel launch` or `rollover` cannot bypass receipt freshness, checkpoint, budget, or live authority checks. Add regression coverage proving stale or checkpoint-required repair receipts still block. Rerun `python3 -m unittest dev.scripts.devctl.tests.runtime.test_startup_gate` and `python3 dev/scripts/devctl.py docs-check --strict-tooling`, then report results.

## Last Reviewed Scope

- 5687e3be..c06cf533 plus dirty `dev/history/ENGINEERING_EVOLUTION.md`; F1/F2 resolved, F3 blocking

## Action Requests

- No pending action requests.
