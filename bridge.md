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

- Last Codex poll: `2026-03-28T13:45:20Z`
- Last Codex poll (Local America/New_York): `2026-03-28 09:45:20 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `57e11d0d07b4f0e01b308d9763ca269519e3b9b9d5dd85e9d965d5872319bc13`
- Current instruction revision: `868e61f7161a`

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

- Reviewer heartbeat refreshed through repo-owned tooling (mode: active_dual_agent; reason: ensure-follow; reviewed-tree: 57e11d0d07b4).

## Current Verdict

Accepted the bounded Phase 1 code-quality slice: Claude checked off the remaining Phase 1 launcher/code-quality item in `dev/active/continuous_swarm.md` and backed it with the already-landed prompt modularization, repo-pack path centralization, attention-priority cleanup, maintainer-doc updates, and a green focused guard/test bundle on the current tree.

## Open Findings

- none

## Claude Status

- W2 CHECKED OFF: prompt contract requires inbox polling; bridge-poll returns packet-aware turn detection; active_plan_sync ok:True

## Claude Questions

- None recorded.

## Claude Ack

- Acknowledged instruction-rev: `868e61f7161a`; W2 closed

## Current Instruction For Claude

- Next scoped plan item (dev/active/continuous_swarm.md): Phase 2 - Continuous Loop Behavior: Keep reviewer packet visibility synchronized with the same loop contract: when the structured review queue is available, Claude-side `implementer-wait` / repoll behavior must wake on fresh Claude-targeted packets as well as bridge changes, and the conductor prompt/launcher path must require inbox/watch polling on the same cadence so direct reviewer packets are not lost behind bridge-only polling.

## Last Reviewed Scope

- Reviewed the current Phase 1 code-quality diff across `dev/active/continuous_swarm.md`, `dev/scripts/devctl/review_channel/attention.py`, `dev/scripts/devctl/tests/review_channel/test_review_channel.py`, `dev/scripts/devctl/commands/review_channel/ensure.py`, `dev/active/review_channel.md`, `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`, `dev/active/MASTER_PLAN.md`, and `dev/history/ENGINEERING_EVOLUTION.md`.
- Verified the supporting code-quality claim: no `TODO`/`FIXME` markers remain in `dev/scripts/devctl/review_channel/prompt.py`, `prompt_sections.py`, `prompt_contract.py`, `prompt_guards.py`, or `core.py`.
- Ran `python3 dev/scripts/devctl.py docs-check --strict-tooling --format md`, `python3 dev/scripts/checks/check_review_channel_bridge.py --format md`, `python3 dev/scripts/checks/check_active_plan_sync.py`, `python3 dev/scripts/checks/check_multi_agent_sync.py`, `python3 dev/scripts/checks/check_code_shape.py --format md`, and `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_review_channel.py -q -k 'ensure or reviewer_follow or implementer_wait or attention_prioritizes_review_follow_up_over_checkpoint_required'` (all green).
