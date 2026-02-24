# ADR 0019: Persistent Runtime Config with CLI-First Precedence

Status: Accepted
Date: 2026-02-23

## Context

VoiceTerm needs persistent runtime preferences (theme, HUD style, wake-word
settings, macros toggle, latency display, etc.) while preserving command-line
flags as the explicit source of truth for each launch.

## Decision

Persist runtime preferences in `~/.config/voiceterm/config.toml` with CLI-first
precedence:

- Store supported runtime keys as optional fields in `config.toml`.
- Load config leniently: unknown keys are ignored for forward compatibility.
- Detect explicit CLI flags and keep them authoritative over persisted values.
- Save runtime preference changes back to disk on settings updates (best-effort;
  write failures do not crash runtime).
- Keep explicit schema-migration machinery for subsystems that require it
  (`theme/style_schema.rs`, memory schema work), not for the current
  `config.toml` key set.

## Consequences

**Positive:**

- Stable cross-session defaults without overriding explicit launch intent.
- Forward-compatible config parsing when new keys are added.
- Simple runtime model for users and maintainers.

**Negative:**

- `config.toml` is not schema-versioned today.
- Persistence writes are best-effort, not transactional/atomic.

## Alternatives Considered

- **Pure CLI-only config**: rejected because repeated flag entry is high-friction.
- **Always versioned runtime config with migration framework**: deferred for now;
  current key set is handled with tolerant parsing and explicit-CLI precedence.

## Links

- `rust/src/bin/voiceterm/persistent_config.rs`
- `rust/src/config/mod.rs`
- `dev/active/MASTER_PLAN.md` (`MP-088`)
