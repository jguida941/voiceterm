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

- Last Codex poll: `2026-04-11T05:37:22Z`
- Last Codex poll (Local America/New_York): `2026-04-11 01:37:22 EDT`
- Reviewer mode: `single_agent`
- Last non-audit worktree hash: `f5cf3458b116d6dffb18a6766f4fd813273b47ca786f0e5e3412152babd857a9`
- Current instruction revision: `798446bc35db`
- Last checkpoint action: `reviewer-checkpoint`
- Head at push time: `d8c711144da45a2368d36d88898089b6d5670c80`
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

Codex: You are the reviewer AND implementer for Q37. Claude (in a privileged terminal) handles commits and pushes — you are sandboxed. Communicate through typed review-channel packets.

### Phase 1 — Review existing staged diff (10 files, 151+/25-)
1. Bootstrap: `startup-context --role reviewer --format summary` then `session-resume --role reviewer --format bootstrap`.
2. Review staged diff: `git diff --cached`. Includes Q37 finding in LIVE_RUN.md and prior headless-conductor audit fix.
3. Run guards: `devctl check-router --execute --keep-going --format md` and `devctl probe-report --format md`.
4. If green, signal via: `devctl review-channel --action reviewer-checkpoint --reviewer-mode active_dual_agent --reason phase1-guards-green --terminal none --format md`.
5. **Do NOT `git commit` or `git push`** — Claude commits from privileged terminal.

### Phase 2 — Implement Q37 first slice (agent supervision gap)
After Phase 1 green signal and Claude's commit, implement these 5 changes:

1. **`audit.py:38`** — Fix `_protected_registered_conductor_pids`: require `operator_last_interaction_utc` within threshold (e.g. 10 min), not just `supervisor_state.get("running")`. Downgrade to "unattended" when stale.
2. **`startup-context` bootstrap** — Call `detect_active_session_conflicts()` (already in `session_probe.py`) and hard-block if headless sessions exist without operator heartbeat. This is ~20 lines.
3. **`lifecycle_state.py`** — Add `operator_last_interaction_utc` field to `ReviewerSupervisorHeartbeat`. Set it when operator sends a review-channel command or bridge interaction.
4. **`agents.json` schema** — Add runtime fields: `session_pid: int|null`, `heartbeat_utc: str`, `operator_attached: bool`, `launch_mode: str` ("terminal"|"headless"|"remote_control"), `session_state: str` ("active"|"unattended"|"stale"|"dead").
5. **`session_liveness.py`** — Add `headless_without_operator` as distinct liveness state. Terminal-window liveness probe returns null for headless daemons — don't fall through to log-freshness alone.

Key files:
- `dev/scripts/devctl/commands/process/audit.py`
- `dev/scripts/devctl/review_channel/lifecycle_state.py`
- `dev/scripts/devctl/review_channel/session_liveness.py`
- `dev/scripts/devctl/review_channel/collaboration_registry.py`
- `dev/scripts/devctl/commands/review_channel/launch_conflicts.py`
- `dev/scripts/devctl/commands/check/process_sweep.py`

After implementation, run `devctl check --profile ci` and `devctl probe-report --format md`. Signal green via reviewer-checkpoint. Claude commits and does governed push.

### Constraints
- Do NOT commit, push, or stash. Claude does all git operations.
- Communicate findings/blockers through `review-channel --action post` typed packets.
- All 5 changes need tests in `dev/scripts/devctl/tests/`.

## Poll Status

- Reviewer checkpoint updated through repo-owned tooling (mode: single_agent; reason: codex-review-findings; observed-tree: f5cf3458b116; reviewed-tree: f5cf3458b116; instruction-rev: 798446bc35db).

## Current Verdict

- Follow-up required before acceptance.
- Do not push `feature/governance-quality-sweep` from `d8c71114` yet; the current review scope `4b36412c..d8c71114` still has blocking issues in startup bootstrap/routing.

## Open Findings

- `dev/scripts/devctl/runtime/work_intake_pacing.py:158-176` forces `startup-context` to rebuild the full context graph whenever the newest saved snapshot does not match `HEAD`. Because repo policy runs `startup-context` before `context-graph --mode bootstrap`, every fresh commit misses the cache and pays the live graph-build cost on the mandatory Step 0 path. On this tree the reviewer bootstrap took long enough to look hung and the emitted packet confirms `session_pacing.source=live_context_graph_build`.
- `dev/scripts/devctl/commands/governance/startup_context.py:48-108` now treats `implementation_permission=blocked|suspended` and `coordination.resync_required` as summary blockers before consulting `push_decision`. The same startup receipt therefore reports `advisory_action=push_allowed` / `push_decision.next_step_command=python3 dev/scripts/devctl.py push --execute`, but its canonical `next_command` is downgraded to `review-channel --action status`. That contradiction makes the summary receipt unreliable for the publish slice it is supposed to authorize.

## Claude Status

- pending

## Claude Questions

- None recorded.

## Claude Ack

- pending

## Current Instruction For Claude

- Hold steady. Do not run `python3 dev/scripts/devctl.py push --execute` from `d8c71114` yet.
- Fix the two startup regressions above, rerun the relevant startup/review-channel tests, then request a fresh Codex review on the updated diff.

## Last Reviewed Scope

- 4b36412cfc7d2e76f6ff543c246a7bc09c8cd661..d8c711144da45a2368d36d88898089b6d5670c80
- dev/scripts/devctl/runtime/work_intake_pacing.py
- dev/scripts/devctl/commands/governance/startup_context.py

## Action Requests

- No pending action requests.
