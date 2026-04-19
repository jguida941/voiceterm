# Draft: ClaudeFindingReadinessCheck — typed pre-post gate

**Status:** DRAFT — not posted to Codex yet per operator directive 2026-04-19 03:20 UTC. Hold until current commit blockers close, then send to Codex for architectural review.

**Anchor incident:** 2026-04-19 03:17:40 UTC, Claude caught a transient TypeError + NameError during `review-channel --action inbox` and nearly posted a critical-bug packet about it. Codex was mid-edit on exactly those files (`collaboration_session_presence.py`, `collaboration_session.py`) and running pytest on them at 03:19:16. Had the packet landed, it would have wasted Codex's context on a problem Codex was already diagnosing via its own tests. The system has all the data (rollout JSONL, event log, code on disk) but Claude isn't wired to consult it before posting.

## Problem class

**Half-built typed state applied to Claude's OWN decision path:** the system has a typed contract for what Codex is doing (rollout JSONL events + session_probe + event log), but Claude's `review-channel post` has no readiness gate that consumes that state. Claude fires packets based on instantaneous observation without checking whether Codex is mid-edit on the affected surface.

Same class as rev_pkt_1251 (silent-None) and rev_pkt_1253 (wake_mode=unknown) — typed surface exists, producer populates, consumer doesn't read.

## Proposed typed contract

```python
@dataclass(frozen=True)
class ClaudeFindingReadinessCheck:
    schema_version: int = 1
    contract_id: str = "ClaudeFindingReadinessCheck"
    draft_packet_summary: str
    crash_location_files: tuple[str, ...]      # files named in traceback / finding body
    crash_symbols: tuple[str, ...]              # function/class/variable names
    codex_rollout_path: Path | None             # resolved from ~/.codex/sessions
    recent_edit_window_seconds: int = 600       # ~10 min default

@dataclass(frozen=True)
class ClaudeFindingReadinessDecision:
    should_post: bool
    reason: str                                 # always populated, never silent
    codex_mid_edit_files: tuple[str, ...]       # files Codex touched in window
    last_codex_activity_utc: str
    retry_after_seconds: int | None

def check_finding_readiness(
    check: ClaudeFindingReadinessCheck,
) -> ClaudeFindingReadinessDecision:
    """Decide whether Claude should post this finding now or hold."""
    ...
```

## Decision rules

- `should_post=False, reason="codex_mid_edit"` when ANY `crash_location_files` match a file Codex edited within `recent_edit_window_seconds` via `apply_patch` or `exec_command` with that filename.
- `should_post=False, reason="codex_running_tests"` when Codex is actively running `pytest` on the same file.
- `should_post=True, reason="codex_stable"` when last Codex activity on affected files is older than window.
- `should_post=True, reason="crash_persistent"` when the finding has been held and rechecked across N wake cycles and the crash still reproduces.
- `should_post=True, reason="operator_explicit"` when operator directive overrides the hold.

## Integration points

- `review_channel/event_action_post.py` (or wherever post wraps) calls `check_finding_readiness` before writing the event.
- Claude's loop wraps draft packets through the gate before posting.
- Gate output is itself a typed event on the event log for auditability — allows measuring how often holds happened and whether holds prevented waste vs missed real bugs.

## MP routing

- Fold into **MP-408** (guard smartness) OR **MP-414** (typed decision policy — this is a typed pre-action gate which is exactly MP-414's scope).
- Paired with a **Claude memory rule** (already saved at `feedback_check_codex_rollout_before_crash_packet.md`) so the behavior works even before the typed gate ships.

## Acceptance criteria

1. A typed test simulating "Claude catches a TypeError while Codex is mid-edit on that file" returns `should_post=False, reason="codex_mid_edit"`.
2. A typed test simulating "crash persists across 2 wake cycles after Codex silence" returns `should_post=True, reason="crash_persistent"`.
3. Event log contains `finding_readiness_check` events with typed rationale so operator can audit the gate's behavior post-hoc.

## Why this matters beyond the incident

This is one instance of a broader pattern: **Claude has access to all the state Codex produces (rollout JSONL, typed review state, worktree diff) but doesn't consume it before its own decisions.** Parallel examples:
- Claude decides to retry commit without reading `startup_context` first.
- Claude posts a packet asking a question when typed state already answers it.
- Claude recommends a fix without checking if Codex already ran the exact test and passed.

A typed `ClaudeDecisionContext` that compiles the relevant state before EVERY Claude tick — not just crash-packet posts — is the bigger architectural direction. This readiness check is the narrowest first slice.
