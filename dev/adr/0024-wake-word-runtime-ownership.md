# ADR 0024: Wake-Word Runtime Ownership and Privacy Guardrails

Status: Accepted
Date: 2026-02-23

## Context

Wake-word support introduces always-listening behavior inside the same runtime
that already manages manual recording, PTY IO, and HUD updates. Without explicit
ownership and safety rules, wake mode can cause thread leaks, capture conflicts,
false-positive triggers, and privacy confusion.

## Decision

Adopt a guarded wake-word runtime model:

- Keep wake-word disabled by default; users must explicitly enable it.
- Centralize listener lifecycle ownership in `WakeWordRuntime` (start/stop/restart
  based on settings changes) with bounded join semantics on shutdown.
- Pause wake listening while capture is already active to avoid microphone
  contention, then resume when safe.
- Route wake detections through the same capture/transcription path used by
  manual recording so behavior stays consistent.
- Clamp sensitivity/cooldown and apply short-utterance/phrase guardrails to
  reduce false positives.
- Surface explicit wake HUD state (`Wake: ON`, `Wake: PAUSED`, error states) so
  users can verify listener behavior.

## Consequences

**Positive:**

- Consistent capture behavior between manual and wake-triggered flows.
- Lower lifecycle risk from leaked listener threads or orphaned capture loops.
- Clearer privacy posture through explicit opt-in and visible wake status.

**Negative:**

- Additional runtime complexity in listener reconciliation and retry paths.
- Wake detection quality still depends on environment noise and STT variability.

## Alternatives Considered

- **Dedicated independent wake pipeline**: rejected because it duplicates capture
  orchestration and increases drift from manual record paths.
- **Wake always-on by default**: rejected due privacy and accidental-trigger risk.

## Links

- `src/src/bin/voiceterm/wake_word.rs`
- `src/src/bin/voiceterm/event_loop/input_dispatch.rs`
- `src/src/bin/voiceterm/settings_handlers.rs`
- `dev/active/MASTER_PLAN.md` (`MP-199`..`MP-203`, `MP-276`..`MP-280`)
