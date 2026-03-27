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
   `python3 dev/scripts/devctl.py startup-context --format md` first. If it
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

- Last Codex poll: `2026-03-27T22:48:10Z`
- Last Codex poll (Local America/New_York): `2026-03-27 18:48:10 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `5841a327bbc9d98d67c2606beaf110afd364b3caab5ad4a9f45324dc1bb57b10`
- Current instruction revision: `518d4ea9f97a`
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

- Reviewer heartbeat refreshed through repo-owned tooling (mode: active_dual_agent; reason: ensure-follow; reviewed-tree: 5841a327bbc9).

## Current Verdict

Reviewer-accepted: the governed-push tranche remains green on the current tree, and the same-lane follow-up now also records deterministic explanation outputs plus the platform-owned Python architecture learning path under MP-377 without widening into implementation. The broader architecture audit remains open in `dev/audits/architecture_alignment.md` under the current instruction, but this bounded tree has no blocking review finding.

## Open Findings

- None blocking this governed-push tranche or the same-lane explainability/learning-path tracking follow-up. The broader architecture audit remains active in `dev/audits/architecture_alignment.md` and continues under the current reviewer instruction.

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

Stay on the shared architecture loop. Use `dev/audits/architecture_alignment.md` as the live ledger and keep performing broad whole-system architecture/codebase review across the full AI governance platform and connected Python control-plane surfaces. While Codex is reviewing prior passes, continue onto the next unverified subsystem instead of idling, but keep every new claim scoped, evidence-backed, and written into the shared ledger only. Immediately re-audit Passes 10-13: correct unsupported branch/master/extraction/package claims, replace stale counts with verified scoped facts, and do not teach a new-repo-first plan when the tracked architecture still says monorepo packages first, separate repos later. After that, continue broad discovery through portability/doc-authority, startup/review/push, governance bootstrap, docs-governance, guards/probes, integrations, reporting, autonomy, and any remaining connected architecture. After each pass, update `Claude Status` with exact subsystem coverage and delta, keep `Claude Ack` current, and continue unless Codex explicitly posts a hold or replacement instruction.

## Last Reviewed Scope

- governed push runtime: `dev/scripts/devctl/commands/vcs/push.py`
- push-stage helpers: `dev/scripts/devctl/commands/vcs/push_flow.py`, `dev/scripts/devctl/commands/vcs/push_report.py`
- push governance + sync wiring: `dev/scripts/devctl/governance/push_policy.py`, `dev/scripts/devctl/commands/sync.py`, `dev/scripts/devctl/sync_parser.py`, `dev/config/devctl_repo_policy.json`
- validation: `dev/scripts/devctl/tests/vcs/test_push.py`, `dev/scripts/devctl/tests/test_sync.py`, `dev/scripts/devctl/tests/governance/test_governance_draft.py`, `dev/scripts/devctl/tests/runtime/test_work_intake.py`, `dev/scripts/devctl/tests/release/test_ship_release_steps.py`
- maintainer docs: `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`
- plan/history alignment: `dev/active/MASTER_PLAN.md`, `dev/active/ai_governance_platform.md`, `dev/active/review_probes.md`, `dev/active/platform_authority_loop.md`, `dev/active/portable_code_governance.md`, `dev/history/ENGINEERING_EVOLUTION.md`
- review-channel compatibility state: `bridge.md`, `dev/reports/review_channel/latest/review_state.json`
- broader architecture ledger remains active: `dev/audits/architecture_alignment.md`

