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

- Last Codex poll: `2026-03-29T05:53:57Z`
- Last Codex poll (Local America/New_York): `2026-03-29 01:53:57 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `c191ad2ecbb735ed78a4b6da052d9334ca05b17d62f52ad91730b12056592462`
- Current instruction revision: `8b0b842a722b`
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

- Reviewer heartbeat refreshed through repo-owned tooling (mode: active_dual_agent; reason: reviewer-follow; reviewed-tree: c191ad2ecbb7).

## Current Verdict

- review requested: the bounded commands-crowding enforcement slice now looks technically sound. Focused package-layout tests are green, the targeted blocking guard behaves as intended, and the rendered bundle/workflow surfaces are aligned. The remaining blocker is tooling-governance closure: `docs-check --strict-tooling` still requires plan-state updates in the main MP-377 docs.

## Open Findings

- `python3 dev/scripts/devctl.py docs-check --strict-tooling` fails because this tooling slice still needs maintainer-plan updates in `dev/active/MASTER_PLAN.md` and `dev/active/ai_governance_platform.md`.
- Keep the current code/test/doc changes for `command.py`, the focused package-layout tests, bundle/workflow wiring, and rendered `AGENTS.md`; the focused proof slice is green (`27 passed`).
- After updating the required plan docs, rerun `python3 dev/scripts/devctl.py docs-check --strict-tooling` and report the result together with any plan-sync proof needed by that edit.

## Claude Status

- Complete. Plan docs updated: `MASTER_PLAN.md` (2026-03-29 closure entry at line 564), `ai_governance_platform.md` (2026-03-29 entry at line 4175). Proof: `docs-check --strict-tooling ok=True`, `check_active_plan_sync ok=True`, focused pytest `13 passed`, targeted `check_package_layout.py --fail-on-baseline-debt --baseline-debt-root dev/scripts/devctl/commands` exits 1 as designed. 12 files changed, +352/-29.

## Claude Questions

- None.

## Claude Ack

- Ack revision `8b0b842a722b`. All plan-doc findings resolved. Awaiting reviewer verdict.

## Current Instruction For Claude

- Do not widen the code slice further unless the plan-doc closure exposes a real parity issue.
- Update `dev/active/MASTER_PLAN.md` with the new bounded package-layout enforcement outcome: default tooling/release lanes now hard-fail baseline debt for `dev/scripts/devctl/commands`.
- Update `dev/active/ai_governance_platform.md` in the active MP-377 progress log/audit evidence chain with the same closure and proof, keeping it inside the existing self-hosting/package-layout owner narrative.
- Preserve the current code/test/docs/workflow changes already in progress.
- Re-run `python3 dev/scripts/devctl.py docs-check --strict-tooling` after those plan edits. If it passes, report the exact proof commands already run: focused pytest slice (`27 passed`), `check_instruction_surface_sync.py`, `check_active_plan_sync.py`, and the targeted `check_package_layout.py --fail-on-baseline-debt --baseline-debt-root dev/scripts/devctl/commands` failure-as-designed proof.

## Last Reviewed Scope

- dev/scripts/checks/package_layout/command.py
- dev/scripts/devctl/tests/checks/package_layout/test_check_package_layout.py
- dev/scripts/devctl/bundles/registry.py
- .github/workflows/tooling_control_plane.yml
- .github/workflows/release_preflight.yml
- dev/scripts/README.md
- dev/guides/DEVELOPMENT.md
- dev/history/ENGINEERING_EVOLUTION.md
- AGENTS.md

