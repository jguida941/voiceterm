# DRAFT: Wake-system empirical fail — both sides not working per 2026-04-19 live test

**Status:** DRAFT — Codex dead, not posting. Push when Codex restarts.

**Test date:** 2026-04-19 ~09:43 UTC

## Operator directive (verbatim)

"this wasnt the plan for you and codex to use same wake system so u didnt hve to mnaully wake and codex can us same sysstem it sadi that and its oth not owrking u should test to see if it works and it should test so u cn se if it works from both sides with u and codex"

## Test design

Post a `kind=action_request`, `to_agent=codex` packet while Codex conductor is DEAD. If wake system works per rev_pkt_1230 design, this should trigger `maybe_wake_posted_reviewer_packet → maybe_wake_waiting_reviewer_conductor → launch_waiting_reviewer_conductor` and spawn a fresh codex session.

## Observed pre-state

- Codex conductor expired 09:52 UTC (per rev_pkt_1291 — `runtime_missing`, `no_live_agents`)
- 3 prior restart attempts today all died within ~20min:
  - `rollout-2026-04-19T00-33-31-*.jsonl`
  - `rollout-2026-04-19T00-39-45-*.jsonl`
  - `rollout-2026-04-19T00-53-56-*.jsonl` (last one, expired)

## Test execution

Posted `rev_pkt_1292`:
- kind=action_request
- to_agent=codex
- operator_interaction_mode=remote_control (expected from runtime)
- policy_hint=operator_approval_required

## Result

- **`reviewer_wake` field: `None`** in the post response JSON
- No new `codex --full-auto` process spawned (pgrep after post: empty)
- No new rollout file created in `~/.codex/sessions/2026/04/19/`
- 6+ min after post: state unchanged, latest rollout still the pre-test file

## Architectural finding

Wake-edge fails on **dead-conductor → relaunch** path. The `maybe_wake_waiting_reviewer_conductor` implementation assumes an alive-but-waiting session; when the session has exited (status 82, context exhaustion, etc.), `load_conductor_sessions` returns no live sessions, the wake helper returns None silently, and no relaunch happens.

This combines TWO half-built-typed-state cases from earlier in this session:
1. **rev_pkt_1214 scope:** wake edge never designed to cover dead-host spawn. Named as "separate seam."
2. **rev_pkt_1190 / MP-418 scope:** process-lifecycle ownership — no typed event emits when conductor dies, so no downstream trigger can kick a relaunch.

Combined: dead session + no death-event + wake-edge-only-wakes-alive = session-death loop requiring operator manual nudge every ~20min.

## Fix direction (naming the decision, not implementing)

Two layers needed:
1. **MP-418 typed death event:** when conductor exits (any status), emit `ProcessLifecycleBreachEvent` into the event log. Fields: `exit_status`, `exit_reason`, `recovery_path`, `timestamp`.
2. **Wake-edge extension for dead-host:** when `maybe_wake_waiting_reviewer_conductor` sees no live session BUT pending action_request to that agent, escalate to `launch_fresh_reviewer_conductor` (not `launch_waiting_reviewer_conductor`). New code path, but uses existing `build_launch_sessions` + `launch_sessions_headless` plumbing.

Both layers fit MP-418 + MP-414 scope per plan entries already landed.

## Validation when fix lands

Same test as above: kill codex conductor → post action_request → fresh conductor should spawn within 30s → rollout file created → packet processed → response packet posted back.

## Claude-host side

Not covered by this test. Claude-host wake is a separate architectural seam per rev_pkt_1232. My tick-based ScheduleWakeup is the current-best, max 2-min lag between packet arrival and Claude observation. No external push mechanism from repo-side to Claude Code session.
