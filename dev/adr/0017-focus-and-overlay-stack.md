# ADR 0017: Single Active Overlay Mode and Input Routing

Status: Accepted
Date: 2026-02-23

## Context

VoiceTerm renders overlays inside a live PTY session. Early UI planning considered
stacked modals with a dedicated focus stack, but the runtime now prioritizes
deterministic PTY row budgeting and low-state transitions under continuous backend
output.

## Decision

Use one active overlay state (`OverlayMode`) instead of a nested overlay stack:

- Exactly one overlay is active at a time (`None`, `Help`, `Settings`,
  `ThemePicker`, `ThemeStudio`, `TranscriptHistory`, `ToastHistory`, ...).
- Opening an overlay replaces the current mode; closing sets mode back to `None`.
- Input routing is mode-first: overlay handlers run only for the active mode.
- Every overlay transition re-syncs PTY winsize/reserved rows so shell output,
  HUD rows, and overlay rows stay aligned.

## Consequences

**Positive:**

- Deterministic overlay transitions and input routing.
- Lower risk of stale focus/stack corruption during heavy PTY output.
- Simpler winsize and redraw coordination.

**Negative:**

- No nested modal layering in the current architecture.
- Each overlay keeps local selection/filter state instead of a shared focus stack.

## Alternatives Considered

- **Overlay stack + focus stack**: rejected for now due added state complexity and
  higher regression risk in terminal-row budgeting paths.
- **Ad hoc per-overlay input routing**: rejected because it increases event-loop
  drift and makes behavior harder to reason about.

## Links

- `src/src/bin/voiceterm/event_state.rs`
- `src/src/bin/voiceterm/overlays.rs`
- `src/src/bin/voiceterm/event_loop/overlay_dispatch.rs`
- `src/src/bin/voiceterm/terminal.rs`
