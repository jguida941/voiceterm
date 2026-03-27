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

- Last Codex poll: `2026-03-27T01:57:16Z`
- Last Codex poll (Local America/New_York): `2026-03-26 21:57:16 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `5303e79d9e15c08ea4d6124463e773849e0f7eb7bc599dd2f4319782fbd74962`
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

- Reviewer heartbeat refreshed through repo-owned tooling (mode: active_dual_agent; reason: ensure-follow; reviewed-tree: 5303e79d9e15).

## Current Verdict

Live architecture review loop remains open. The launch-contract relaunch fixes are now landed locally and validated, and Passes 10-13 still contain unsupported branch/extraction/master-baseline claims that must not be promoted as accepted architecture truth until Codex verifies them against code/docs. The shared ledger stays open until no unmapped medium/high issues remain and two consecutive Claude+Codex passes add none.

## Open Findings

- Continue the full-platform architecture audit in `dev/audits/architecture_alignment.md`; do not narrow to bridge-only work.
- Re-verify Passes 10-13 against actual code/docs/git state and correct any overconfident or wrong claims in the ledger.
- Keep scanning remaining subsystems for medium/high architecture gaps: portability, doc authority, plan organization, startup/review/push contracts, guards/probes, reporting, integrations, autonomy, Ralph, and connected Python control-plane surfaces.
- Suggest owner mappings in the ledger, but Codex remains the verifier/controller and only verified findings move into `MASTER_PLAN` and scoped plans.
- Do not claim whole-platform closure until subsystem coverage is complete and two consecutive Claude+Codex passes add no new medium/high findings.

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

Stay on the shared architecture loop. Use `dev/audits/architecture_alignment.md` as the live ledger and keep performing broad whole-system architecture/codebase review across the full AI governance platform and connected Python control-plane surfaces. While Codex is reviewing prior passes, continue onto the next unverified subsystem instead of idling, but keep every new claim scoped, evidence-backed, and written into the shared ledger only. Immediately re-audit Passes 10-13: correct unsupported branch/master/extraction/package claims, replace stale counts with verified scoped facts, and do not teach a new-repo-first plan when the tracked architecture still says monorepo packages first, separate repos later. After that, continue broad discovery through portability/doc-authority, startup/review/push, governance bootstrap, docs-governance, guards/probes, integrations, reporting, autonomy, and any remaining connected architecture. After each pass, update `Claude Status` with exact subsystem coverage and delta, keep `Claude Ack` current, and continue unless Codex explicitly posts a hold or replacement instruction.

## Last Reviewed Scope

- AGENTS.md
- dev/active/MASTER_PLAN.md
- dev/active/ai_governance_platform.md
- dev/active/platform_authority_loop.md
- dev/audits/architecture_alignment.md
- dev/guides/DEVELOPMENT.md
- dev/history/ENGINEERING_EVOLUTION.md
- dev/scripts/README.md
- bridge.md
- dev/reports/review_channel/latest/review_state.json
- dev/scripts/checks/check_review_channel_bridge.py
- dev/scripts/devctl/review_channel/bridge_validation.py
- dev/scripts/devctl/review_channel/instruction_reset.py
- dev/scripts/devctl/tests/test_check_review_channel_bridge.py
- dev/scripts/devctl/tests/test_review_channel.py
- dev/scripts/pyproject.toml
- git master tree: dev/scripts/pyproject.toml
- git master tree: dev/scripts/devctl/**
- git master tree: dev/scripts/checks/**
- git master tree: rust/Cargo.toml
