# ADR 0021: Session Transcript History and Opt-In Memory Logging

Status: Accepted
Date: 2026-02-23

## Context

VoiceTerm needs usable in-session recall (`Ctrl+H` history overlay) without
forcing disk persistence of potentially sensitive transcript content.

## Decision

Use a split model: bounded in-memory history by default, optional disk logging.

- Keep transcript history in memory for the active session so `Ctrl+H` search and
  review work without extra setup.
- Track source-tagged rows (`mic`, `you`, `ai`) and allow replay only for
  replay-safe sources (`mic`, `you`).
- Keep persistence opt-in via `--session-memory` (default off), with optional
  `--session-memory-path` override.
- Sanitize/control-filter transcript input so control-sequence noise does not
  pollute history search or replay paths.

## Consequences

**Positive:**

- History UX works out of the box with no mandatory disk retention.
- Privacy posture is safer for default usage (persistent logging is explicit).
- Replay safety is clearer because assistant-output rows are non-replayable.

**Negative:**

- History is session-scoped unless users opt in to memory logging.
- Full retention policy controls are still separate follow-up work.

## Alternatives Considered

- **Always-on persisted transcript database**: rejected due privacy and surprise risk.
- **No built-in history**: rejected because it weakens transcript debugging and reuse.

## Links

- `rust/src/bin/voiceterm/transcript_history.rs`
- `rust/src/bin/voiceterm/session_memory.rs`
- `rust/src/config/mod.rs`
- `dev/active/MASTER_PLAN.md` (`MP-091`, `MP-229`, `MP-235`)
