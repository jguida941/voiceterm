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

- Last Codex poll: `2026-03-28T01:40:22Z`
- Last Codex poll (Local America/New_York): `2026-03-27 21:40:22 EDT`
- Reviewer mode: `single_agent`
- Last non-audit worktree hash: `4211c01637d51c0b4020f96871efd55f98524002e080dc717138d13e71916f62`
- Current instruction revision: `9b86eb1499cd`
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

- Reviewer checkpoint updated through repo-owned tooling (mode: single_agent; reason: review-pass; tree: 4211c01637d5; instruction-rev: 9b86eb1499cd).

## Current Verdict

- reviewer accepted

## Open Findings

- none

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

- turn escaped-finding closure into a typed meta-governance contract for MP-377. Use the release-maintenance/import-shim tranche as the seed case and land finding-class to prevention-surface routing, regression proof, and repo-visible closure writeback without widening into unrelated cleanup.

## Last Reviewed Scope

- AGENTS.md
- dev/active/MASTER_PLAN.md
- dev/active/ai_governance_platform.md
- dev/scripts/checks/bundle_registry_dry/command.py
- dev/scripts/checks/bundle_registry_dry/analysis.py
- dev/scripts/checks/bundle_registry_dry/loader.py
- dev/scripts/checks/bundle_registry_dry/rendering.py
- dev/scripts/devctl/tests/checks/test_check_bundle_registry_dry.py

