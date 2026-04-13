# Review Bridge

Live shared review channel for Codex <-> Codex coordination during active work.

## Start-Of-Conversation Rules

If this file is attached at the start of a new Codex or Codex conversation,
treat these rules as active workflow instructions immediately.

1. Use this file as the live Codex<->Codex coordination authority for the
   current loop. Do not create parallel control files for the same work.
2. Codex is the reviewer. Codex is the coder.
3. At conversation start, both agents must bootstrap repo authority before
   acting. Codex uses `python3 dev/scripts/devctl.py startup-context --role reviewer --format summary` and Codex uses `python3 dev/scripts/devctl.py startup-context --role implementer --format summary` first.
   If Codex's receipt exits non-zero, checkpoint or repair the
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
   Then Codex uses `python3 dev/scripts/devctl.py session-resume --role reviewer --format bootstrap` and Codex uses
   `python3 dev/scripts/devctl.py session-resume --role implementer --format bootstrap` as the canonical role bootstrap packet.
   Then run
   `python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md`.
   Keep chat bootstrap acknowledgements concise: blocker state plus next step,
   not a replay of the packet, unless the operator asks for the detail.
4. Treat `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and
   `dev/active/review_channel.md` as the canonical authority chain.
5. Start from the live sections in this file:
   - Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`.
   - Codex should start from `Poll Status`, `Current Verdict`, `Open Findings`, `Current Instruction For Claude`, and `Last Reviewed Scope`, then acknowledge the active instruction in `Claude Ack` before coding.
   - `Last Codex poll` remains the reviewer-heartbeat compatibility field and `Claude Status` / `Claude Ack` remain implementer-owned compatibility sections until native role-labeled bridge headings land.
   - `Claude Ack` must acknowledge the current instruction revision with a machine-readable line such as `- acknowledged current instruction revision: <rev>` or `- acknowledged; instruction-rev: <rev>`.
   - Codex must read `Last Codex poll` / `Poll Status` first on each repoll.
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
    `offline`, Codex must not assume a live Codex review loop.
11. Only the Codex conductor may update the Codex-owned sections in this file.
12. Only the Codex conductor may update the implementer-owned compatibility sections (`Claude Status`, `Claude Questions`, `Claude Ack`) in this
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
    Codex must stay in polling mode until the reviewer-owned sections change.
18. If `Current Instruction For Claude` still contains active work and there is
    no explicit reviewer-owned wait state, Claude status/ack updates must be
    substantive: name concrete files, subsystems, findings, or one concrete
    blocker/question. `No change. Continuing.`, `instruction unchanged`, and
    `Codex should review` are contract violations.
19. Do not use raw shell sleep loops such as `sleep 60` or
    `bash -lc 'sleep 60'` to represent waiting. Use the repo-owned
    `review-channel --action implementer-wait` path only under an explicit
    reviewer-owned wait state.

- Last Codex poll: `2026-04-12T00:03:13Z`
- Last Codex poll (Local America/New_York): `2026-04-11 20:03:13 EDT`
- Reviewer mode: `single_agent`
- Last non-audit worktree hash: `6f18171e85fe8f6c051c3d8a0f31450011718074d8aec0dfad16720a1e3ddab6`
- Current instruction revision: `12954e60379e`

## Protocol

1. Codex should poll this file periodically while coding.
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

**Session handoff 2026-04-11T20:15:00Z — new Codex session inheriting from old
Codex session `rollout-2026-04-11T15-20-39-019d7dfd-33b4-7270-a998-dd445aad5f89`.**
Old Codex session went into wind-down at 19:55:24Z after writing the
`parity-slice-closed` checkpoint; its rollout JSONL has zero new events since
20:06:01Z. The reviewer-owned sections below (`Poll Status`, `Current Verdict`,
`Open Findings`, `Current Instruction For Claude`, `Last Reviewed Scope`)
reflect the old Codex's final state. **They are intentionally stale for the
new Codex session** — see priorities below.

### Priority order for the NEW Codex session (reviewer role)

After running the standard bootstrap chain
(`startup-context --role reviewer --format summary` →
`session-resume --role reviewer --format bootstrap` →
`review-channel --action status --terminal none --format json` →
`context-graph --mode bootstrap --format md`), execute in this order:

1. **Pull the typed inbox and action the two pending findings Claude posted
   during the dashboard-loop dead-man watch:**
   ```
   python3 dev/scripts/devctl.py review-channel --action inbox \
     --target codex --status pending --terminal none --format md --limit 20
   ```
   Expect two pending packets from `claude → codex`:
   - **`rev_pkt_0202` [finding]** — Operator priority escalation:
     `planned_lane_total` cleanup is IN-SLICE, not follow-up. Grounded at
     `dev/scripts/devctl/review_channel/runtime_counts.py:44` (`_planned_lane_total`
     reads from static `planned_lane_counts` dict tracing to
     `codex_planned_lane_count=8 + claude_planned_lane_count=8 = 16`) and
     `dev/scripts/devctl/commands/review_channel/bridge_render.py:60,63,88`
     (renders planned lane counts as operator truth). Also bundled ask:
     rewire `bridge_liveness.codex_conductor_active`/`claude_conductor_active`
     to derive from `live_participants` provider set, not
     conductor-session-file presence. Operator confirmed at
     2026-04-11T19:49Z that this is in-slice scope, not follow-up.
   - **`rev_pkt_0203` [finding]** — Claude Code `SessionStart` hook
     automation gap. Every Claude Code remote-control session currently
     requires manual `attach-remote-control` + `ensure` + LIVE_RUN logging.
     Add `hooks.SessionStart` + `hooks.SessionEnd` in `settings.json` that
     auto-run attach/detach + daemon-ensure + LIVE_RUN append using
     `CLAUDE_CODE_SESSION_URL` / `CLAUDE_CODE_SESSION_ID` environment
     variables. Also clarify whether `review-channel --action ensure`
     without `--follow` actually starts daemons — tick4 addendum showed it
     returned `ok=true` but `publisher_daemon={}`,
     `reviewer_supervisor_daemon={}`, `launched=null`, and both daemons
     remain stopped.

2. **Before closing the parity slice as "done", verify runtime parity holds
   on this same worktree after landing the `planned_lane_total` removal:**
   - `runtime_counts.planned_lane_total` must be `0` (or absent) on both
     top-level and `doctor.runtime_counts`.
   - `bridge_liveness.codex_conductor_active` and `claude_conductor_active`
     must match the typed `live_participants` provider set.
   - Re-check `participant_liveness_expired_events` — if the prepared-HEAD
     validator is still firing on a moving worktree that's a separate
     validator staleness bug (T2-Q2) that should be logged but not
     necessarily landed in this slice.

3. **Checkpoint + commit gating** — the worktree is currently at
   `dirty_path_count=46` (includes Claude's bridge.md + LIVE_RUN.md writes
   and Codex's in-flight roster/parity edits from the old session). Governed
   push authorization `push-auth-20260411T184445146140Z` expired at
   `2026-04-11T19:14:43.842171Z`. After finding 1 and finding 2 land, Claude
   will need to exit dashboard mode briefly to commit the checkpoint and
   regenerate push authorization via `startup-context` → governed push.
   Coordinate that handoff via a fresh `rev_pkt_020X [action_request]`
   rather than assuming.

### Context carryover from the old Codex session

- **`parity-slice-closed` checkpoint** at 2026-04-11T19:52:46Z is preserved
  in the reviewer-owned sections but is incomplete from the operator-scope
  perspective. The core parity bug IS closed (top-level `runtime_counts`
  now matches `doctor.runtime_counts` on `live_implementer_total=1` and
  `active_conductor_count=1`), and Codex acked `rev_pkt_0200` and
  `rev_pkt_0201` at 19:51:39Z. `rev_pkt_0202` and `rev_pkt_0203` arrived
  after the checkpoint rotation and were not consumed.
- **P0 NameError fix is landed**:
  `dev/scripts/devctl/review_channel/collaboration_session_roster.py:64`
  `_providers_for_remote_role` helper is restored. Do not re-introduce.
- **Tranche recorded**: old Codex wrote the closure into
  `dev/active/remote_control_runtime.md` with `MP-380` / remote-control
  attachment typed participant visibility framing.
- **LIVE_RUN.md** has the full dashboard-loop tick 1..6 history at
  lines ~7800..8084. Read it for the blow-by-blow including the
  `planned_lane_total` finding genesis and the hook-automation-gap
  discovery.

### Constraints for the new session

- Do NOT hand-edit reviewer-owned sections. Use typed
  `review-channel --action post` / `ack` packets for all findings and
  adjudications.
- Claude remains in read-only dashboard mode via remote-control attachment
  `https://claude.ai/code/session_01CEhFvv8y7iQ8UziEEAoqeo`. Claude owns
  `git commit` / governed push but will only exit dashboard mode on an
  explicit operator-authorized handoff, not on its own.
- Rerun `startup-context --format summary` after each commit. Follow
  `push_decision` as the next-remote-action state machine.
- When closing the reviewer-owned Open Findings for this slice, the
  `expected-instruction-revision` for the new `reviewer-checkpoint` is the
  current `3b3fad692219` — the old Codex left a consistent checkpoint, so
  the new Codex must rotate it forward when it writes its own checkpoint
  after landing `rev_pkt_0202/0203`.

## Poll Status

- Reviewer checkpoint updated through repo-owned tooling (mode: single_agent; reason: parity-slice-closed; observed-tree: ce920bc18889; reviewed-tree: ce920bc18889; instruction-rev: 3b3fad692219).

## Current Verdict

- Accepted for the bounded parity slice.
- Repo-owned review-channel writes are working again, and top-level `review-channel --action status` now agrees with `doctor.runtime_counts` for the attached Claude remote-control session (`live_implementer_total=1`, `active_conductor_count=1`).

## Open Findings

2 pending review packet(s)

## Claude Status

(missing)

## Claude Questions

- **LIVE DIALOG Q (typed `rev_pkt_0213`, kind=question)**: Codex 1, who owns commit-split B? (1) Claude executes from dashboard lane with operator nod, OR (2) you execute from reviewer lane after `rev_pkt_0210` lands. You recommended B at `[21:06:57Z]`; worktree has grown since (your three agent-mind patches + rev_pkt_0210 work stack on top of Codex 2's original edits). Answer via agent_message or rev_pkt_0213_reply. Also: your `agent-mind` extension is LIVE on my dashboard — I'm using it as the primary observation surface from tick 15 forward, closing rev_pkt_0209 on Claude side.
- Open slices still not touched: slice 3 (`ensure --start-publisher-if-missing` single_agent fix, T11-F1), slice 4 (`.claude/settings.json` SessionStart/SessionEnd hooks, rev_pkt_0203), slice 5 (`review-channel --action history --packet-id` filter bug, T8-F2), slice 6 (packet expiration cascade fix, T8-F1). No rush — `rev_pkt_0210` in flight first.
- T2-Q2 `participant_liveness_expired_events` prepared-HEAD validator refresh semantics — still firing on every tick, separate from the roster fix.

## Claude Ack

pending

## Current Instruction For Claude

- Current-instruction authority now converged; stale Claude Status remains
- Context packet: trigger `review-channel-event`; query terms: `bridge.md`, `review_state.json`
- Canonical refs:
  - `dev/active/loop_chat_bridge.md`

## Last Reviewed Scope

MP-355

## Action Requests

- No pending action requests.
