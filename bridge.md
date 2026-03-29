# Review Bridge

Live shared review channel for Codex <-> Claude coordination during active work.

## Start-Of-Conversation Rules

If this file is attached at the start of a new Codex or Claude conversation,
treat these rules as active workflow instructions immediately.

1. Use this file as the live Codex<->Claude coordination authority for the
   current loop. Do not create parallel control files for the same work.
2. Codex is the reviewer. Claude is the coder.
3. At conversation start, both agents must bootstrap repo authority before
   acting. The approved startup path is:
   `python3 dev/scripts/devctl.py startup-context --format summary` first. If it
   exits non-zero, checkpoint or repair the repo state before coding or
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
   - Claude must read `Last Codex poll` / `Poll Status` first on each repoll.
6. Codex must poll non-`bridge.md` worktree changes every 2-3 minutes while
   code is moving.
7. Codex must exclude `bridge.md` itself when computing the reviewed
   worktree hash. Advisory scratch/audit artifacts such as `convo.md` and
   `dev/audits/**` must stay out of that reviewed-hash truth too.
8. Each meaningful Codex review must include an operator-visible chat update.
9. When `Reviewer mode` is `active_dual_agent`, this file is the live
   reviewer/coder authority.
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

- Last Codex poll: `2026-03-29T01:46:32Z`
- Last Codex poll (Local America/New_York): `2026-03-28 21:46:32 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `7f07a526325874bb248b9b375bd58930fab5a7e073870a1f96e2ff2506315f6b`
- Current instruction revision: `441f072817a4`
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

- Current scale-out mode is `8+8`.
- `dev/active/review_channel.md` contains the static swarm plan and lane map.
- This file is the only live cross-team coordination surface during execution.
- Keep `bridge.md` current-state only; do not turn it into a transcript dump.
- Keep the active markdown bridge disciplined until the structured `review-channel` / overlay-native path replaces it.

## Poll Status

- Reviewer heartbeat refreshed through repo-owned tooling (mode: active_dual_agent; reason: reviewer-follow; reviewed-tree: 7f07a5263258).

## Current Verdict

Accepted the bounded event-backed instruction projection follow-up: queue/current-session derived instruction fields now use the same compact no-H2 context summary as bridge-safe promotion text, while the full packet remains available in source metadata for prompt and audit consumers.

## Open Findings

- none

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude


- Next scoped plan item (dev/active/review_channel.md): Phase 1 - Canonical Review Channel: Keep bridge repair repo-owned while the compatibility projection still exists: `review-channel --action render-bridge` should remain the sanctioned rebuild path for `bridge.md`, regenerating the bounded template plus sanitized live sections from repo-owned state instead of relying on manual bridge surgery after a bad session.
- Context packet: trigger `review-channel-promotion`; query terms: `dev/active/review_channel.md`, `bridge.md`
- Canonical refs:
  - `dev/active/review_channel.md`
  - `dev/scripts/devctl/review_channel`
  - `dev/active/loop_chat_bridge.md`

## Last Reviewed Scope

- Reviewed the current event-backed instruction/projection diff across dev/scripts/devctl/review_channel/event_projection.py, dev/scripts/devctl/review_channel/event_projection_context.py, dev/scripts/devctl/tests/review_channel/test_context_injection.py, dev/active/review_channel.md, dev/history/ENGINEERING_EVOLUTION.md, AGENTS.md, dev/guides/DEVELOPMENT.md, dev/scripts/README.md, and dev/active/MASTER_PLAN.md.
- Ran python3 -m pytest dev/scripts/devctl/tests/review_channel/test_context_injection.py dev/scripts/devctl/tests/review_channel/test_current_session_projection.py -q, python3 -m pytest dev/scripts/devctl/tests/review_channel/test_review_channel.py -q -k "derived_next_instruction or current_instruction or review_packet or run_promote or auto_promote_on_launch or instruction_auto_promoted", python3 dev/scripts/devctl.py docs-check --strict-tooling --format md, python3 dev/scripts/checks/check_code_shape.py --format md, python3 dev/scripts/checks/check_active_plan_sync.py, python3 dev/scripts/checks/check_multi_agent_sync.py, and python3 dev/scripts/checks/check_instruction_surface_sync.py (all green).

