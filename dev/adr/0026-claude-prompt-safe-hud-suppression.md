# ADR 0026: Claude Prompt-Safe HUD Suppression

Status: Accepted
Date: 2026-02-23

## Context

Claude CLI interactive approval/permission prompts can be visually occluded by
HUD/overlay rows in dense terminal layouts. This makes approval prompts
unreadable and blocks action flow unless the HUD is suppressed at the right time.

## Decision

Adopt backend-specific prompt-safe suppression for Claude sessions:

- Detect interactive Claude prompt patterns from PTY output.
- When prompt state is detected, set prompt suppression active and reserve zero
  HUD rows so prompt content has full terminal row budget.
- Recompute PTY winsize immediately on suppression transitions.
- Clear suppression on user input response or timeout and restore normal HUD rows.
- Keep this behavior scoped to Claude backend handling; other backends do not use
  this detector path.

## Consequences

**Positive:**

- Prevents prompt/action-row occlusion during Claude approvals.
- Keeps prompt interactions readable without manual HUD toggles.
- Preserves normal HUD behavior outside prompt windows.

**Negative:**

- Detection relies on pattern heuristics that may require maintenance.
- Temporary HUD disappearance can look abrupt during prompt transitions.

## Alternatives Considered

- **Always reserve fewer HUD rows**: rejected because it permanently reduces HUD
  fidelity even when no prompt is active.
- **Backend-agnostic blanket suppression on generic prompt-like text**: rejected
  to avoid false positives in non-Claude flows.

## Links

- `src/src/bin/voiceterm/prompt/claude_prompt_detect.rs`
- `src/src/bin/voiceterm/event_loop/output_dispatch.rs`
- `src/src/bin/voiceterm/event_loop/input_dispatch.rs`
- `src/src/bin/voiceterm/terminal.rs`
- `dev/active/MASTER_PLAN.md` (`MP-226`)
