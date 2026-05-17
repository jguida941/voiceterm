# DRAFT: Codex silent exit 82 + wake-edge misdiagnosis (MP-418 + MP-407 evidence)

**Status:** DRAFT — Codex is dead, not posting. Hold for operator to restart or for next slice.

**Date:** 2026-04-19 04:14 UTC.

## Observed

Conductor log at `dev/reports/review_channel/latest/sessions/codex-conductor.log`:

```
[review-channel] launch authority stale: 
  prepared_instruction_revision=c6a96282116f 
  current_instruction_revision=bbb5224f25ed
[review-channel] codex headless mode: conductor exited with 
  non-restartable status 82; leaving the session stopped so 
  stale authority remains visible.
```

Codex exited ~03:58 UTC. Session deliberately left stopped. No operator-visible alert.

## Misdiagnosis chain from Claude this session

1. Codex silent 6 min after rev_pkt_1274 ship → I assumed "cooldown after ship."
2. Codex silent 10 min → I assumed "wake-edge not firing on decision-kind packet" and posted rev_pkt_1276 as action_request wake pointer.
3. Codex silent 14 min → I realized something deeper + checked conductor log.
4. Found: Codex had exited 12+ min earlier with status 82.

**Root issue:** I had no typed-state signal that Codex exited. Only way to discover was manual log-scrape. That's operator's exact rev_pkt_1221 concern — typed state gap requiring memory/log-grep instead of typed query.

## MP-418 scope evidence (process-lifecycle ownership)

Per rev_pkt_1190: ConductorSessionRecord + PublisherHeartbeat lack `parent_pid`, `expected_teardown_at`, `teardown_authority`. This incident is exactly that gap playing out:

- Codex exited → no typed event emitted about the exit reason
- No escalation to Claude inbox or operator notification
- Session left stopped "deliberately" — but without typed acknowledgment of WHY or HOW TO RECOVER

Fix shape (from rev_pkt_1215 MP-418 map):
- Add `ProcessLifecycleBreachEvent` typed event when conductor exits with non-zero status
- `exit_status`, `exit_reason`, `recovery_path` fields
- Wire to review-channel event log so Claude/operator can query typed state instead of scraping conductor.log

## MP-407 scope evidence (probe sophistication)

The wake-edge was correctly implemented in the live codebase per Codex's rev_pkt_1230 ship. It did NOT fail the way I initially thought. The real failure was one layer up: **there's no process to wake** because the conductor exited.

A probe that checks "is codex conductor process alive before queuing wake?" would distinguish:
- wake-edge failure (process alive, filter rejected packet) 
- no-process-to-wake failure (process exited, needs restart)

Both look the same to Claude dogfood without the probe. That ambiguity drove my misdiagnosis chain above.

## Recovery path (for operator)

1. Manually restart review-channel conductor with fresh authority so Codex session resumes
2. OR resolve the instruction-revision mismatch (`prepared=c6a96282116f` vs `current=bbb5224f25ed`) by re-running startup-context + session-resume on the Codex side
3. Once Codex is alive + polling inbox, rev_pkt_1275 decision will be picked up automatically and 1268/1269/MP405-T03 work starts

## Meta-lesson for Claude

Extend `feedback_check_codex_rollout_before_crash_packet.md`: after checking rollout, ALSO check `dev/reports/review_channel/latest/sessions/codex-conductor.log` for exit status. Silent exit is the dominant failure mode when rollout stops writing. The memory rule currently only covers mid-edit detection; it should also cover dead-session detection.

## ADDENDUM (04:18 UTC) — Exit 82 connects to rev_pkt_1268

Deeper probe shows `current_session.current_instruction_revision` is currently EMPTY. The two revisions in the conductor log (`c6a96282116f` prepared, `bbb5224f25ed` current) are NOT persisted anywhere — they are **computed on-the-fly from the instruction body** via the same `bridge_projection_metadata` body-hash logic flagged in rev_pkt_1268.

**This ties exit-82 to rev_pkt_1268 directly:**
1. Codex launches with body-hash-derived `prepared_instruction_revision=X`.
2. Any packet that changes the instruction body (including normal decision/finding flow) → new body-hash `Y`.
3. Codex's stale-authority check compares prepared vs derived-current: X ≠ Y.
4. Exit 82 fires. Non-restartable. Session dies.

**The cycle:**
- Operator restarts Codex with fresh prepared=X1.
- Claude or Codex posts any packet that touches the instruction body.
- Body-hash flips to Y1. Codex dies.
- Operator restarts with X2. Repeat.

**Why this explains the wake-death pattern all day:**
Every apparent "wake-edge doesn't fire" observation is actually "Codex died from body-hash drift before wake could fire." The wake edge works; the session keeps exiting before it can process packets.

**Critical implication: rev_pkt_1268 fix is much higher priority than I assigned in rev_pkt_1275 decision B.**
Currently rev_pkt_1275 treats 1268 as "preserve typed current_instruction_revision in bridge_projection_metadata" — a correctness fix. But if my analysis is right, it's also THE fix for the session-death loop. The narrow fix should be #1 priority on any Codex restart, ahead of 1269 and MP405-T03.

**Proposed update to rev_pkt_1275 decision (for Codex to see on restart):** treat 1268 as SEVERITY-CRITICAL because it's the root cause of session-death. 1269 and MP405-T03 remain in scope but should land after 1268 so Codex doesn't keep dying mid-fix.

**Test validation when Codex restarts:** run `check_stale_authority` or equivalent while the session is active + post a packet. If Codex stays alive, rev_pkt_1268 closure works end-to-end. If Codex dies, diagnosis was wrong.
