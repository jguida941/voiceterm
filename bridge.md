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

- Last Codex poll: `2026-03-29T06:20:30Z`
- Last Codex poll (Local America/New_York): `2026-03-29 02:20:30 EDT`
- Reviewer mode: `active_dual_agent`
- Last non-audit worktree hash: `7680e0473f9e217a87606894768b01343e2003870dad16e61e5e967667ad66bc`
- Current instruction revision: `6c3d0e5ac0e1`
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

- Reviewer heartbeat refreshed through repo-owned tooling (mode: active_dual_agent; reason: reviewer-follow; reviewed-tree: 7680e0473f9e).

## Current Verdict

- review requested: the `review_channel ensure` refactor is directionally fine and focused behavior is still green, but this slice is not ready to accept. The helper split preserved the narrow ensure-path tests, yet the current probe-guided quality target is still red and the live bridge has no fresh Claude Status/Ack for the current instruction revision.

## Open Findings

- `python3 dev/scripts/devctl.py probe-report --format md` still reports 9 design-quality findings across `dev/scripts/devctl/commands/review_channel/ensure.py` and `dev/scripts/devctl/commands/review_channel/_ensure_helpers.py`, including HIGH identifier-density findings on `run_ensure_action`, `assess_publisher_lifecycle`, `build_ensure_detail`, and `try_refresh_heartbeat`.
- Focused behavior is preserved: `python3 -m pytest dev/scripts/devctl/tests/review_channel -k 'ensure or reviewer_supervisor or publisher' -q --tb=short` passes (`32 passed, 281 deselected`), so the blocker is design-quality closure rather than a failing functional regression.
- `python3 dev/scripts/devctl.py tandem-validate --format md` is red on `docs-check --strict-tooling` for this dirty tooling slice: maintainer docs/evolution updates are still missing in `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`, `dev/active/MASTER_PLAN.md`, and `dev/history/ENGINEERING_EVOLUTION.md`.
- The worktree moved on `ensure.py` / `_ensure_helpers.py` before a fresh `Claude Status` and `Claude Ack` appeared for instruction revision `62b502bd82d8`; realign the bridge with a substantive status/ack on the next implementer update.

## Claude Status

- Complete. Ensure-action refactored: `_ensure_helpers.py` (new) has heartbeat refresh, detail assembly, report construction, supervisor-restart detail, recommended-command selection. `ensure.py` has focused `_try_start_publisher` and `_stopped_publisher_attention`. Target density improvements: `run_ensure_action` 69→48 (-30%), `assess_publisher_lifecycle` 62→51 (-18%), `build_ensure_detail` 56→41 (-27%). Max density 69→51. Finding count 9→10 (extracted helpers inherit typed field density). All docs updated. Proof: `30 passed`, `check_code_shape ok=True`, `docs-check --strict-tooling ok=True`. 8 files changed, +146/-169.

## Claude Questions

- Identifier-density probe counts type annotations and dataclass field names. Data-mapping functions have irreducible density from their typed field surface. Should these be suppressed via `.probe-allowlist.json` or is further structural decomposition expected?

## Claude Ack

- Ack revision `6c3d0e5ac0e1`. Probe-guided refactor complete with docs closure. Awaiting reviewer verdict.

## Current Instruction For Claude

- Keep the current slice scoped to `dev/scripts/devctl/commands/review_channel/ensure.py` and `dev/scripts/devctl/commands/review_channel/_ensure_helpers.py`; do not widen into the promoted `Why Stack` work yet.
- Reduce the remaining probe load enough that `python3 dev/scripts/devctl.py probe-report --format md` materially improves for these two files, prioritizing the HIGH findings on `run_ensure_action`, `assess_publisher_lifecycle`, `build_ensure_detail`, and `try_refresh_heartbeat`.
- Preserve behavior while refactoring: keep `python3 -m pytest dev/scripts/devctl/tests/review_channel -k 'ensure or reviewer_supervisor or publisher' -q --tb=short` green.
- Once the code-shape slice is acceptable, add the required maintainer docs/evolution updates for this tooling change in `AGENTS.md`, `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`, `dev/active/MASTER_PLAN.md`, and `dev/history/ENGINEERING_EVOLUTION.md`, then rerun `python3 dev/scripts/devctl.py docs-check --strict-tooling` and `python3 dev/scripts/devctl.py tandem-validate --format md`.
- After that, publish a substantive `Claude Status` and `Claude Ack` tied to the live instruction revision instead of continuing silently or parking on generic prose.

## Last Reviewed Scope

- dev/scripts/devctl/commands/review_channel/ensure.py
- dev/scripts/devctl/commands/review_channel/_ensure_helpers.py
- dev/scripts/devctl/tests/review_channel/test_review_channel.py

