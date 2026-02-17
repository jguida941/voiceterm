# Rust Code Review Research Pack

Date: 2026-02-17  
Status: Active companion for code-quality and architecture review work  
Linked plan: `dev/active/CODE_QUALITY_EXECUTION_PLAN.md`

This file is the source pack for Rust review work in this repo:

1. inspect implementation paths in this codebase
2. cross-check assumptions with primary Rust/crate documentation
3. write findings back into active execution trackers

## 0) Workspace Rust Surface Map

Use this map to anchor review scopes before opening docs:

| Review area | Primary code paths | Why this area is high-leverage |
|---|---|---|
| Overlay runtime and event loop | `src/src/bin/voiceterm/` (`main.rs`, `event_loop/`, `status_line/`, `hud/`, `settings_handlers.rs`) | Highest change frequency and user-visible behavior |
| PTY/session lifecycle | `src/src/pty_session/` | Process ownership, terminal safety, stale-session cleanup risk |
| IPC/session orchestration | `src/src/ipc/` and `src/src/ipc/session/` | Backend integration, auth flow, event routing correctness |
| Backend adapters | `src/src/backend/` and `src/src/codex/` | Provider-specific behavior and command execution policy |
| Audio/voice/STT path | `src/src/audio/`, `src/src/voice.rs`, `src/src/stt.rs`, `src/src/vad_earshot.rs` | Latency, capture lifecycle, CPU/memory sensitivity |
| Config and CLI contract | `src/src/config/` and `src/src/bin/voiceterm/config/cli.rs` | User contract stability, defaults, and diagnostics |

## 1) Core Official Rust Docs

- Rust Learn portal: <https://www.rust-lang.org/learn>
- The Rust Book: <https://doc.rust-lang.org/book/>
- Rust Reference: <https://doc.rust-lang.org/reference/>
- Standard Library docs: <https://doc.rust-lang.org/std/>
- Rust By Example: <https://doc.rust-lang.org/rust-by-example/>
- Edition Guide: <https://doc.rust-lang.org/edition-guide/>
- The Rustonomicon (unsafe Rust): <https://doc.rust-lang.org/nomicon/>
- The Unstable Book: <https://doc.rust-lang.org/unstable-book/>

## 2) Compiler / Tooling / Diagnostics (Official)

- Cargo Book: <https://doc.rust-lang.org/cargo/>
- rustc Book: <https://doc.rust-lang.org/rustc/index.html>
- rustdoc Book: <https://doc.rust-lang.org/rustdoc/index.html>
- Rust Compiler Error Index: <https://doc.rust-lang.org/error_codes/error-index.html>
- Clippy docs: <https://doc.rust-lang.org/clippy/>
- Clippy lint catalog: <https://doc.rust-lang.org/clippy/lints.html>
- rustfmt docs: <https://rust-lang.github.io/rustfmt/>
- rustfmt project: <https://github.com/rust-lang/rustfmt>
- rustc-dev-guide: <https://rustc-dev-guide.rust-lang.org/>
- Rust Forge (project governance/workflows): <https://forge.rust-lang.org/>

## 3) Safety / API / Architecture Guidance

- Rust API Guidelines: <https://rust-lang.github.io/api-guidelines/>
- Async Book: <https://rust-lang.github.io/async-book/>
- Unsafe Code Guidelines reference: <https://rust-lang.github.io/unsafe-code-guidelines/>
- std-dev safety comment policy (`SAFETY:`): <https://std-dev-guide.rust-lang.org/policy/safety-comments.html>

## 4) Dependency Docs (Mapped to This Workspace)

From `src/Cargo.toml` and current runtime architecture:

- clap: <https://docs.rs/clap/latest/clap/>
- crossterm: <https://docs.rs/crossterm/latest/crossterm/>
- ratatui: <https://docs.rs/ratatui/latest/ratatui/>
- Ratatui site: <https://ratatui.rs/>
- crossbeam-channel: <https://docs.rs/crossbeam-channel/latest/crossbeam_channel/>
- serde: <https://docs.rs/serde/latest/serde/>
- serde_json: <https://docs.rs/serde_json/latest/serde_json/>
- serde_yaml: <https://docs.rs/serde_yaml/latest/serde_yaml/>
- regex: <https://docs.rs/regex/latest/regex/>
- tracing: <https://docs.rs/tracing/latest/tracing/>
- tracing-subscriber: <https://docs.rs/tracing-subscriber/latest/tracing_subscriber/>
- cpal: <https://docs.rs/cpal/latest/cpal/>
- whisper-rs: <https://docs.rs/whisper-rs/latest/whisper_rs/>
- vte: <https://docs.rs/vte/latest/vte/>
- unicode-width: <https://docs.rs/unicode-width/latest/unicode_width/>
- anyhow: <https://docs.rs/anyhow/latest/anyhow/>
- strip-ansi-escapes: <https://docs.rs/strip-ansi-escapes/latest/strip_ansi_escapes/>
- rubato: <https://docs.rs/rubato/latest/rubato/>
- earshot: <https://docs.rs/earshot/latest/earshot/>
- proptest: <https://docs.rs/proptest/latest/proptest/>

## 5) Highly Recommended Community References

Use these after checking official docs first:

- Comprehensive Rust (Google): <https://google.github.io/comprehensive-rust/>
- Rustlings: <https://github.com/rust-lang/rustlings>
- Command Line Apps in Rust: <https://rust-cli.github.io/book/>
- Rust Design Patterns: <https://rust-unofficial.github.io/patterns/>
- Rust Performance Book: <https://nnethercote.github.io/perf-book/introduction.html>
- Tokio tutorial (async runtime patterns): <https://tokio.rs/tokio/tutorial>
- Rust Users Forum: <https://users.rust-lang.org/>

## 6) Review Loop (Code <-> Docs)

Use this sequence for each subsystem:

1. Choose scope and risk class (PTY, IPC, overlay/HUD, audio/STT, config/parser).
2. Read target code and list concrete questions (safety, ownership, perf, API contract).
3. Check relevant official Rust docs and crate docs from sections 1-4.
4. Validate assumptions against tests and runtime call paths.
5. Record findings with severity and file/line references.
6. Convert accepted findings into actionable items in
   `dev/active/CODE_QUALITY_EXECUTION_PLAN.md` and/or `dev/active/MASTER_PLAN.md`.
7. Land fixes with tests and run required verification gates.

## 7) Finding Template

Use this format for consistency:

```md
### Finding: <short title>
- Severity: high | medium | low
- Area: safety | memory | error-handling | concurrency | perf | style
- File: <path:line>
- Problem: <what is wrong and why it matters>
- Evidence: <code path + test behavior + doc link>
- Recommended fix: <specific change>
- Verification: <tests/checks to prove fix>
```

## 8) Plan Integration Rules

- For structural/runtime refactors: add `CQ-*` tasks to
  `dev/active/CODE_QUALITY_EXECUTION_PLAN.md`.
- For broader product/UX/roadmap work: add `MP-*` tasks to
  `dev/active/MASTER_PLAN.md`.
- Keep this file as the active research source while code-quality closure is in
  progress.

## 9) Initial Audit Intake (2026-02-17)

### Finding: Runtime status renderer still uses char-count width

- Severity: medium
- Area: style | error-handling
- File: `src/src/bin/voiceterm/writer/render.rs:160`
- Problem: status truncation/display-width decisions currently use
  `sanitized.chars().count()`, which can mis-measure wide glyphs and CJK output.
- Evidence: Runtime path in `write_status_line` uses char count while adjacent
  renderer paths have moved to Unicode-aware width helpers.
- Recommended fix: switch truncation + width policy to shared Unicode-aware
  display-width helpers and add coverage for wide glyph strings.
- Tracking: `MP-215`

### Finding: Status-style helper has stale char-count width behavior

- Severity: low
- Area: style
- File: `src/src/bin/voiceterm/status_style.rs:138`
- Problem: `status_display_width` still computes width with
  `text.chars().count()`, which can reintroduce drift if reused.
- Evidence: helper is not part of the normalized display-width utility path.
- Recommended fix: either migrate to Unicode-aware width or remove this helper
  if it remains unused.
- Tracking: `MP-215`

### Finding: Duplicate transcript preview formatter in two runtime modules

- Severity: low
- Area: style | maintainability
- File: `src/src/bin/voiceterm/voice_control/navigation.rs:291`
- Problem: `format_transcript_preview` logic is duplicated in navigation and
  drain processing, increasing drift risk on future behavior tweaks.
- Evidence: same collapse/truncate implementation also appears in
  `src/src/bin/voiceterm/voice_control/drain/message_processing.rs:238`.
- Recommended fix: extract one shared helper with a focused test table.
- Tracking: `MP-216`

## 10) Closure and Handoff (Code Quality -> Theme Upgrade)

When all remaining code-quality follow-on findings are either fixed or deferred
with explicit rationale:

1. mark closure in `dev/active/CODE_QUALITY_EXECUTION_PLAN.md`
2. move the completed execution record to `dev/archive/` per archive policy
3. continue visual/theming execution through `dev/active/MASTER_PLAN.md`
   Phase 2C/2D/2E (`MP-148` onward)
