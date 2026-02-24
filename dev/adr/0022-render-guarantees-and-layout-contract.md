# ADR 0022: Writer Render Invariants for HUD and Overlay Safety

Status: Accepted
Date: 2026-02-23

## Context

VoiceTerm draws HUD/overlay content in the same terminal as live backend PTY
output. Without strict render invariants, HUD and shell output can corrupt each
other, especially on resize and high-output workloads.

## Decision

Enforce terminal-safety invariants through the serialized writer path:

- Route HUD/overlay writes through the writer thread (`WriterMessage`) so PTY and
  UI output do not interleave unpredictably.
- Wrap draw operations with cursor save/restore sequences.
- Render by explicit row positioning in reserved rows and clear trailing stale
  characters on each written line.
- Recompute reserved rows and clear old-geometry HUD/overlay rows on resize
  before redraw.
- Truncate status text by display width (Unicode-aware) to keep line bounds.
- Coalesce redraw timing so settings/status updates stay responsive under
  continuous PTY output.

## Consequences

**Positive:**

- Stable HUD/overlay rendering across terminal environments.
- Fewer resize ghost-frame and stale-row regressions.
- Clear, testable invariants around width and draw scope.

**Negative:**

- More bookkeeping in writer state and resize handling.
- Render behavior depends on strict message-path discipline.

## Alternatives Considered

- **Direct ad hoc writes from event loop/input paths**: rejected due output
  interleaving and race-prone redraw behavior.
- **Free-form overlay writes with newline-based flow**: rejected because it
  cannot preserve shell-region integrity in shared PTY rendering.

## Links

- `rust/src/bin/voiceterm/writer/mod.rs`
- `rust/src/bin/voiceterm/writer/state.rs`
- `rust/src/bin/voiceterm/writer/render.rs`
- `rust/src/bin/voiceterm/terminal.rs`
