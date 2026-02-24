# ADR 0025: Voice Macro Precedence and Built-In Navigation Resolution

Status: Accepted
Date: 2026-02-23

## Context

VoiceTerm supports project macros (`.voiceterm/macros.yaml`) and built-in voice
navigation actions (scroll, send, copy/show/explain last error). Without a clear
precedence policy, overlapping phrases can produce unpredictable behavior.

## Decision

Use a deterministic transcript transform order:

- Load project macro rules from `.voiceterm/macros.yaml`; macro expansion is
  controlled by a runtime `Macros` toggle (default OFF).
- Apply macro expansion before built-in navigation parsing.
- If a macro matched, skip built-in navigation resolution for that transcript.
- Keep explicit built-in escape phrases (`voice scroll up`, `voice scroll down`)
  available for users who keep overlapping macro triggers.
- Allow macro rules to override send mode (`auto` or `insert`) per rule.

## Consequences

**Positive:**

- Predictable transcript handling with clear macro-vs-built-in behavior.
- Project-specific workflows stay flexible without breaking core voice actions.
- Users retain explicit phrasing to force built-in actions when needed.

**Negative:**

- Macro trigger mistakes can shadow built-in intents until corrected.
- Requires documentation/testing to keep precedence behavior discoverable.

## Alternatives Considered

- **Built-ins always first**: rejected because it would block valid
  project-specific macro commands.
- **No precedence policy (first parser wins by code path)**: rejected because it
  creates hidden behavior drift over time.

## Links

- `rust/src/bin/voiceterm/voice_macros.rs`
- `rust/src/bin/voiceterm/voice_control/drain/transcript_delivery.rs`
- `rust/src/bin/voiceterm/voice_control/navigation.rs`
- `dev/active/MASTER_PLAN.md` (`MP-085`, `MP-086`, `MP-090`, `MP-140`, `MP-281`)
