# VoiceTerm Rust Codebase Audit

**Date:** 2026-02-23
**Scope:** Full codebase (206 Rust files, 68,617 lines)
**Reviewer:** Senior Rust code review (automated multi-agent audit)
**Methodology:** Every `.rs` file, `Cargo.toml`, project structure, and documentation reviewed against official Rust API Guidelines, Clippy recommendations, and idiomatic Rust patterns.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Critical Issues](#2-critical-issues)
3. [High-Severity Issues](#3-high-severity-issues)
4. [Medium-Severity Issues](#4-medium-severity-issues)
5. [Low-Severity Issues](#5-low-severity-issues)
6. [Code Duplication Map](#6-code-duplication-map)
7. [Modularity & Organization Recommendations](#7-modularity--organization-recommendations)
8. [Project Configuration & Tooling](#8-project-configuration--tooling)
9. [Positive Observations](#9-positive-observations)
10. [Prioritized Action Plan](#10-prioritized-action-plan)

---

## 1. Executive Summary

| Severity | Count | Key Themes |
|----------|-------|------------|
| **CRITICAL** | 8 | UTF-8 panics, deprecated dependency, dead theme code, security gaps |
| **HIGH** | 18 | Code duplication (12 instances), god objects, monolithic functions |
| **MEDIUM** | 30 | Non-idiomatic patterns, missing docs, `#[allow(dead_code)]` abuse |
| **LOW** | 25 | Minor style, optimization opportunities, naming inconsistencies |

**Overall Assessment:** The codebase demonstrates strong engineering fundamentals: exceptional `unsafe` documentation, RAII discipline, bounded resource management, thorough test coverage, and graceful degradation. However, it suffers from significant code duplication (~12 distinct instances), speculative dead code in the theme system (~2,600 lines), several runtime panic risks from UTF-8 byte slicing, and architectural strain from being a single 68K-line crate that should be a workspace.

---

## 2. Critical Issues

### CRIT-1: UTF-8 byte slicing can panic on non-ASCII input

**Files:**
- `src/src/ipc/session/claude_job.rs:143-146`
- `src/src/ipc/session/event_processing/claude.rs:20-23`

```rust
log_debug_content(&format!(
    "Starting Claude job with prompt: {}...",
    &prompt[..prompt.len().min(30)]  // panics on multi-byte UTF-8
));
```

If the prompt contains multi-byte UTF-8 characters (e.g., emoji, CJK), `&prompt[..30]` will panic with "byte index is not a char boundary."

**Fix:**
```rust
let preview: String = prompt.chars().take(30).collect();
log_debug_content(&format!("Starting Claude job with prompt: {preview}..."));
```

---

### CRIT-2: UTF-8 truncation panic in legacy TUI state

**File:** `src/src/legacy_tui/state.rs:635-639`

```rust
let truncated = if input.len() > INPUT_MAX_CHARS {
    input.truncate(INPUT_MAX_CHARS);  // byte index, not char count!
    true
```

`String::truncate` takes a byte index but `INPUT_MAX_CHARS` is conceptually a character limit. Multi-byte input will panic.

**Fix:**
```rust
if let Some((idx, _)) = input.char_indices().nth(INPUT_MAX_CHARS) {
    input.truncate(idx);
}
```

---

### CRIT-3: `serde_yaml` dependency is officially deprecated

**File:** `src/Cargo.toml:24`, Lock: `version = "0.9.34+deprecated"`

The `serde_yaml` crate was deprecated by its maintainer. No security patches or bug fixes will be released.

**Fix:** Migrate to `serde_yml` (community fork) or switch macros config to TOML (already used for persistent config).

---

### CRIT-4: Five theme files are entirely dead code (~2,600 lines)

**Files (all `#[allow(dead_code)]` at file scope):**
- `src/src/bin/voiceterm/theme/capability_matrix.rs`
- `src/src/bin/voiceterm/theme/dependency_baseline.rs`
- `src/src/bin/voiceterm/theme/texture_profile.rs`
- `src/src/bin/voiceterm/theme/widget_pack.rs`
- `src/src/bin/voiceterm/theme/rule_profile.rs` (1,051 lines alone)
- `src/src/bin/voiceterm/theme/component_registry.rs`

These are speculative infrastructure with zero runtime usage. They increase compile time and maintenance burden.

**Fix:** Move behind `#[cfg(feature = "theme-studio-v2")]` or delete. Reduce theme module from 14 files to 8.

---

### CRIT-5: Secret redaction only replaces the first occurrence

**File:** `src/src/bin/voiceterm/memory/governance.rs:29-58`

```rust
if let Some(pos) = redacted.find(prefix) {
    // only replaces first match
}
```

If text contains multiple secrets (e.g., `"key1=sk-abc key2=sk-xyz"`), only the first is redacted. This is a privacy gap in a data persistence layer.

**Fix:** Use `while let Some(pos) = redacted.find(prefix)` loop or `replace` with a regex.

---

### CRIT-6: Non-unique event ID generation in memory system

**File:** `src/src/bin/voiceterm/memory/types.rs:369-386`

```rust
let rand_suffix: u32 = (ts as u32).wrapping_mul(2654435761);
```

The "random" suffix is derived deterministically from the timestamp. Two calls within the same millisecond produce identical IDs, causing data loss.

**Fix:** Use an `AtomicU64` counter or inject actual randomness via `getrandom`.

---

### CRIT-7: f32-to-i16 overflow in earshot VAD conversion

**File:** `src/src/vad_earshot.rs:43`

```rust
self.scratch.push((clamped * 32_768.0) as i16);
```

When `clamped == 1.0`, the product is 32,768 which exceeds `i16::MAX` (32,767). Rust saturates since 1.45, but the intent is ambiguous.

**Fix:** Use `32_767.0` as the multiplier for the `f32 -> i16` direction.

---

### CRIT-8: No `[lints]` section -- clippy policy not codified

**File:** `src/Cargo.toml`

Lint policy is only enforced via CLI flags in the Makefile. Developers and IDEs running `cargo build` see no clippy warnings. No `clippy.toml` or `rustfmt.toml` exists.

**Fix:** Add `[lints.clippy]` section to Cargo.toml and create a `rustfmt.toml`.

---

## 3. High-Severity Issues

### HIGH-1: Duplicated `is_jetbrains_terminal()` across 3 files (behavioral divergence)

**Files:**
- `src/src/bin/voiceterm/main.rs:120-159`
- `src/src/bin/voiceterm/banner.rs:202-238`
- `src/src/bin/voiceterm/writer/render.rs:22-68`

The `banner.rs` version checks fewer env var patterns than `main.rs`, causing inconsistent detection. Only `render.rs` caches with `OnceLock`.

**Fix:** Extract a single canonical function with `OnceLock` caching into a shared utility module.

---

### HIGH-2: Backend implementations are nearly identical boilerplate (~300 lines)

**Files:** `src/src/backend/{codex,claude,gemini,aider,opencode}.rs`

All five files share identical structure. Only string literals differ (name, binary, prompt_pattern).

**Fix:** Use a declarative macro or a single struct parameterized by a config enum.

---

### HIGH-3: Duplicated `rms_db` function

**Files:**
- `src/src/mic_meter.rs:18-37`
- `src/src/audio/meter.rs:42-49`

Identical RMS-to-dB logic maintained independently. Risk of divergent fixes.

**Fix:** Reuse `crate::audio::meter::rms_db` from `mic_meter.rs`.

---

### HIGH-4: Stream-building logic duplicated between `record_for` and `record_with_vad_impl`

**File:** `src/src/audio/recorder.rs:97-184` and `262-335`

Both functions independently build CPAL input streams with the same three-way `match format` on `SampleFormat::{F32, I16, U16}`.

**Fix:** Extract stream-building into a shared helper.

---

### HIGH-5: `EventLoopState` is a god object (30+ `pub(crate)` fields)

**File:** `src/src/bin/voiceterm/event_state.rs:30-71`

No logical grouping. Fields for PTY I/O, theme studio, overlay state, and voice control are all mixed.

**Fix:** Group into sub-structs: `PtyInputState`, `ThemeStudioState`, `OverlayState`, etc.

---

### HIGH-6: `periodic_tasks::run_periodic_tasks` is ~300 lines handling 17 distinct concerns

**File:** `src/src/bin/voiceterm/event_loop/periodic_tasks.rs:8-310`

Handles SIGWINCH, meter updates, spinner ticks, heartbeat, prompt idle, voice drain, wake word, toast, auto-voice, and more -- all in one function.

**Fix:** Extract each logical block into a named helper function.

---

### HIGH-7: `main()` is 410+ lines

**File:** `src/src/bin/voiceterm/main.rs:227-638`

Handles CLI parsing, config, dev setup, PTY creation, channel creation, thread spawning, voice setup, status init, wake word, onboarding, event loop, and shutdown.

**Fix:** Extract into named setup functions: `setup_voice_runtime()`, `setup_pty_session()`, etc.

---

### HIGH-8: 10 identical copy-paste functions in `theme_studio_cycles.rs`

**File:** `src/src/bin/voiceterm/event_loop/input_dispatch/overlay/theme_studio_cycles.rs:1-184`

All 10 `cycle_runtime_*_override` functions follow the exact same pattern.

**Fix:** Single generic function:
```rust
fn cycle_enum_option<T: Copy + PartialEq>(
    current: Option<T>, variants: &[Option<T>], direction: i32
) -> Option<T>
```

---

### HIGH-9: `send_enhanced_status_with_buttons` called 20+ times with 6 identical args

**Files:** `event_loop/periodic_tasks.rs`, `event_loop/input_dispatch.rs`, `event_loop.rs`

**Fix:** Create a `send_hud_update(state, deps)` helper.

---

### HIGH-10: Duplicated token canonicalization between `navigation.rs` and `wake_word.rs`

**Files:**
- `src/src/bin/voiceterm/voice_control/navigation.rs:48-86`
- `src/src/bin/voiceterm/wake_word.rs:627-654`

Nearly identical STT canonicalization (merging "code"+"x" -> "codex", alias tables).

**Fix:** Extract shared `stt_token_canonicalization` module.

---

### HIGH-11: Duplicated `StubSession` test helper in 3 files

**Files:**
- `voice_control/navigation.rs:380-396`
- `voice_control/drain/tests.rs:12-28`
- `transcript/delivery.rs:168-184`

**Fix:** Single `#[cfg(test)]` test utility module.

---

### HIGH-12: `ButtonActionContext` has 24 fields (god context pattern)

**File:** `src/src/bin/voiceterm/button_handlers.rs:27-51`

Passes essentially the entire application state by reference.

**Fix:** Decompose into sub-contexts by domain.

---

### HIGH-13: Duplicated status line indicator functions

**Files:**
- `src/src/bin/voiceterm/status_line/format.rs`
- `src/src/bin/voiceterm/status_line/buttons.rs`

`with_color`, `base_mode_indicator`, `recording_mode_indicator`, `processing_mode_indicator` are independently implemented.

**Fix:** Extract to `status_line/indicators.rs`.

---

### HIGH-14: Duplicated `display_width` / `truncate_display`

**Files:**
- `src/src/bin/voiceterm/overlay_frame.rs:7-28`
- `src/src/bin/voiceterm/status_line/text.rs`

**Fix:** Unify into a single utility module.

---

### HIGH-15: Missing doc comments on core types

**File:** `src/src/bin/voiceterm/event_state.rs`

`EventLoopState`, `EventLoopTimers`, `EventLoopDeps` -- the most important types in the application -- have zero doc comments. Fields like `suppress_startup_escape_input`, `force_send_on_next_transcript`, `meter_floor_started_at` are opaque.

---

### HIGH-16: `VoiceDrainContext` has 22 fields, `TranscriptDeliveryContext` has 30+

**File:** `src/src/bin/voiceterm/voice_control/drain.rs:33-71`

**Fix:** Group into sub-structs: `StatusContext`, `TimingContext`, `TranscriptQueueContext`.

---

### HIGH-17: Silent job cancellation inconsistency in IPC router

**File:** `src/src/ipc/router.rs:95-102`

When a new prompt arrives while a job is active, the existing job is cancelled without emitting a `JobEnd` event. Compare to `cancel_active_jobs` (lines 266-294) which properly emits `JobEnd`. Clients lose track of job lifecycle state.

---

### HIGH-18: `env::set_var` / `env::remove_var` in tests without `unsafe` blocks

**Files:** Multiple (main.rs, banner.rs, config/theme.rs, input/spawn.rs, onboarding.rs, legacy_tui/tests.rs, doctor.rs)

Marked `unsafe` since Rust 1.66. Required to be in `unsafe` blocks for Rust 2024 edition.

**Fix:** Wrap in `unsafe` blocks with `// SAFETY:` documentation, or refactor detection functions to accept env values as parameters.

---

## 4. Medium-Severity Issues

### MEDIUM-1: `auth.rs` uses `String` errors instead of typed error handling
- **File:** `src/src/auth.rs:4` -- `pub type AuthResult = Result<(), String>`
- All other modules use `anyhow::Result`. This is the only module with raw `String` errors.

### MEDIUM-2: `AiBackend::command()` clones `Vec<String>` on every call
- **File:** All backend files, trait method
- **Fix:** Return `&[String]` instead.

### MEDIUM-3: `window_by_columns` treats zero-width chars as width 1
- **File:** `src/src/utf8_safe.rs:120`
- Combining diacritics and ZWJ characters incorrectly consume a display column.

### MEDIUM-4: `sanitize_output_line` silently replaces backticks with quotes
- **File:** `src/src/legacy_ui.rs:293`
- Alters markdown code spans in AI output without documented rationale.

### MEDIUM-5: `NON_SPEECH_PATTERN` regex is ~700 chars with duplicated word lists
- **File:** `src/src/voice.rs:308`
- **Fix:** Generate pattern from a word list helper.

### MEDIUM-6: `design_low_pass` uses `== 0.0` float comparison
- **File:** `src/src/audio/resample.rs:296`
- Safe in practice but needs a comment explaining why.

### MEDIUM-7: `Provider::from_str` shadows `std::str::FromStr` trait
- **File:** `src/src/ipc/protocol.rs:204-218`
- Prevents idiomatic `"codex".parse::<Provider>()`.

### MEDIUM-8: Doc comments placed after attributes (non-idiomatic)
- **File:** `src/src/ipc/protocol.rs:74-77, 93-95, 121-124, 180-182`
- Doc comments must immediately precede the item, not follow `#[serde(...)]`.

### MEDIUM-9: `BoundedEventQueue::drop_non_terminal` triple linear scan
- **File:** `src/src/codex/backend.rs:310-334`
- O(n) per push under backpressure with capacity 1024.

### MEDIUM-10: Log rotation truncates entire file (loses all history)
- **File:** `src/src/legacy_tui/logging.rs:63-76`
- **Fix:** Tail-preserving rotation (rename to `.old`).

### MEDIUM-11: `run_python_transcription` reads entire stdout into memory
- **File:** `src/src/legacy_tui/state.rs:114-141`
- No size bounds; a verbose Python bug could cause OOM.

### MEDIUM-12: `write_stub_script` test helper duplicated in 2 files
- `src/src/ipc/tests.rs:77-93` and `src/src/codex/tests.rs:408-424`

### MEDIUM-13: String-based provider passing throughout IPC module
- Provider names passed as `String`, parsed repeatedly with `Provider::from_str`.
- **Fix:** Use `Provider` enum directly via serde deserialization.

### MEDIUM-14: Inconsistent mutex recovery patterns
- Codex module: `lock_or_recover`. Legacy TUI: `unwrap_or_else(PoisonError::into_inner)`. IPC: `unwrap_or_else(|e| e.into_inner())`.
- **Fix:** Standardize on `lock_or_recover` everywhere.

### MEDIUM-15: `#[allow(dead_code)]` in production code without documented rationale
- `voice_control/manager.rs:65`, `audio_meter/format.rs:74,160`, `memory/store/sqlite.rs:58`, `memory/ingest.rs:177`, `prompt/claude_prompt_detect.rs:252,284,290,350`, `event_state.rs:67-70`, `writer/mod.rs:22-25`
- Per AGENTS.md: requires documented rationale and follow-up MP item.

### MEDIUM-16: `StatusLineState` has 30+ public fields with no validation
- **File:** `src/src/bin/voiceterm/status_line/state.rs:141-208`
- Invalid state combinations possible (e.g., `recording_duration = Some` when not recording).

### MEDIUM-17: `ThemeStudioView` duplicates all `RuntimeStylePackOverrides` fields
- **File:** `src/src/bin/voiceterm/theme_studio.rs:66-87`
- Adding a new override field requires changes in 3 places.
- **Fix:** Embed `RuntimeStylePackOverrides` directly.

### MEDIUM-18: `StatusType::from_message` infers severity from message text
- **File:** `src/src/bin/voiceterm/status_style.rs:28-62`
- String matching on "failed" is fragile. Status messages should carry typed severity.

### MEDIUM-19: 11 nearly identical `normalize_xxx` functions in `style_schema.rs`
- **Fix:** Implement `FromStr` on each enum or use a macro.

### MEDIUM-20: Parallel enum hierarchies between `runtime_overrides.rs` and `style_schema.rs`
- 10 override enums mirror normalization functions. Must be updated in lockstep.

### MEDIUM-21: `push_theme_studio_history_entry` uses `Vec::remove(0)` (O(n))
- **File:** `src/src/bin/voiceterm/event_loop/input_dispatch/overlay.rs:627-635`
- **Fix:** Use `VecDeque`.

### MEDIUM-22: `count_lines` reads entire file just to count entries
- **File:** `src/src/devtools/storage.rs:86-91`
- **Fix:** Track count via metadata or start at 0 since appending.

### MEDIUM-23: Duplicated date arithmetic in `types.rs` and `governance.rs`
- Two separate implementations of `days_to_ymd`, `is_leap` using different integer widths.

### MEDIUM-24: NaN passes validation silently in memory schema
- **File:** `src/src/bin/voiceterm/memory/schema.rs:27-38`
- `importance < 0.0 || importance > 1.0` is false for NaN.
- **Fix:** Use `!(0.0..=1.0).contains(&event.importance)`.

### MEDIUM-25: `truncate_text` in `context_pack.rs` mixes byte and char counting
- **File:** `src/src/bin/voiceterm/memory/context_pack.rs:198-206`
- Fast path checks `text.len()` (bytes) against a char limit.

### MEDIUM-26: `devtools/storage.rs` uses `HOME` but not `XDG_DATA_HOME`
- Minor cross-platform concern on Linux.

### MEDIUM-27: Hardcoded ANSI escape codes in `buttons.rs` bypass theme system
- **File:** `src/src/bin/voiceterm/status_line/buttons.rs:39-40`

### MEDIUM-28: Duplicated `format_duration` in `progress.rs` and `session_stats.rs`
- Nearly identical duration formatting logic.

### MEDIUM-29: Duplicated `take_stream_line` in `transcript_history.rs` and `session_memory.rs`

### MEDIUM-30: `sanitized_input_text()` returns an exact clone with no sanitization
- **File:** `src/src/legacy_tui/state.rs:727-729`
- Misleading function name.

---

## 5. Low-Severity Issues

### LOW-1: `#[allow(dead_code)]` on `enable_mouse_capture` without explanation
- `src/src/terminal_restore.rs:56`

### LOW-2: `legacy_tui::*` glob re-export in `lib.rs`
- `src/src/lib.rs:26` -- makes symbol tracing difficult.

### LOW-3: Missing `#[must_use]` on `with_args()` backend factory methods

### LOW-4: Non-Unix `process_signal.rs` stub silently succeeds without logging

### LOW-5: Test names use redundant `test_` prefix in backend tests

### LOW-6: `Provider` missing `Display` trait implementation
- Forces `.as_str().to_string()` pattern (~15 occurrences).

### LOW-7: Session ID uses truncated timestamp (collision risk in same millisecond)
- `src/src/ipc/session/state.rs:18-24`

### LOW-8: `emit_capabilities` allocates fresh Vec on every call
- `src/src/ipc/session/state.rs:84-109`

### LOW-9: Thread-keyed event storage in test support grows unbounded
- `src/src/ipc/session/test_support.rs:7-9`

### LOW-10: `splash_duration_ms()` silently caps without warning
- `src/src/bin/voiceterm/banner.rs:55-61`

### LOW-11: `format_debug_bytes` creates 64 small string allocations
- `src/src/bin/voiceterm/input/spawn.rs:18-31`

### LOW-12: Onboarding manual TOML parser is fragile
- `src/src/bin/voiceterm/onboarding.rs:33-46`
- Splitting on `=` won't handle comments or multi-line values.

### LOW-13: `join_thread_with_timeout` busy-waits with 10ms sleeps
- `src/src/bin/voiceterm/main.rs:206-225`
- Acceptable for shutdown path but could use `recv_timeout`.

### LOW-14: `looks_like_error_line` substring matching has false positives
- `src/src/bin/voiceterm/prompt/tracker.rs:192-198`
- "error handling is important" matches as an error line.

### LOW-15: `pipeline.rs` is a single boolean AND function (over-abstraction)
- `src/src/bin/voiceterm/voice_control/pipeline.rs`

### LOW-16: `format_transcript_preview` minimum floor (4) is undocumented
- `src/src/bin/voiceterm/voice_control/transcript_preview.rs:22`

### LOW-17: `help_overlay_width()` returns hardcoded constant (dead code)
- `src/src/bin/voiceterm/help.rs:288-291`

### LOW-18: `status_messages.rs` is a single one-line function file
- Could be inlined.

### LOW-19: `detect.rs` has only a single function (`is_warp_terminal`)
- Could be inlined into theme/mod.rs.

### LOW-20: `StatusBanner::height` is always `lines.len()` -- derived value stored as field

### LOW-21: `ToastCenter::push` and `push_with_duration` share duplicated eviction logic

### LOW-22: Test-only `test_crash` and `test_utf8_bug` compiled as release binaries
- Should be `[[example]]` targets or gated behind a feature.

### LOW-23: `edition = "2021"` -- consider upgrading to 2024
- Brings stricter `unsafe` handling and other improvements.

### LOW-24: `num_cpus` crate superseded by `std::thread::available_parallelism()`
- Can be eliminated entirely.

### LOW-25: Naming inconsistency: `resolved_cols` vs `read_terminal_size`
- Unclear which uses cached values vs live reads.

---

## 6. Code Duplication Map

| # | What | Where | Lines Wasted |
|---|------|-------|-------------|
| 1 | `is_jetbrains_terminal()` | main.rs, banner.rs, writer/render.rs | ~120 |
| 2 | Backend boilerplate (5 files) | backend/*.rs | ~300 |
| 3 | `rms_db` function | mic_meter.rs, audio/meter.rs | ~30 |
| 4 | CPAL stream building | audio/recorder.rs (2 locations) | ~150 |
| 5 | Token canonicalization | voice_control/navigation.rs, wake_word.rs | ~80 |
| 6 | `StubSession` test helper | 3 test files | ~50 |
| 7 | `write_stub_script` test helper | ipc/tests.rs, codex/tests.rs | ~30 |
| 8 | Status line indicators | format.rs, buttons.rs | ~60 |
| 9 | `display_width` / `truncate_display` | overlay_frame.rs, status_line/text.rs | ~40 |
| 10 | `format_duration` | progress.rs, session_stats.rs | ~25 |
| 11 | `take_stream_line` | transcript_history.rs, session_memory.rs | ~30 |
| 12 | `strip_ansi_sgr` test helper | toast.rs, transcript_history.rs tests | ~30 |
| 13 | `theme_studio_cycles` (10 functions) | theme_studio_cycles.rs | ~150 |
| 14 | Date arithmetic (`days_to_ymd`, `is_leap`) | memory/types.rs, memory/governance.rs | ~80 |
| 15 | `section_line` formatting | dev_panel.rs, help.rs | ~30 |
| **Total** | | | **~1,205 lines** |

---

## 7. Modularity & Organization Recommendations

### 7.1 Workspace Decomposition (HIGH priority)

At 68K lines in a single crate, compile times and testability suffer. Recommended workspace structure:

```
src/
├── Cargo.toml              # [workspace] with members
├── crates/
│   ├── voiceterm-core/     # config, backend presets, doctor, telemetry, terminal_restore
│   ├── voiceterm-audio/    # audio capture, VAD, resample, mic_meter
│   ├── voiceterm-stt/      # Whisper transcription, voice orchestration
│   ├── voiceterm-pty/      # PTY session, session guard, process signals
│   ├── voiceterm-ipc/      # IPC protocol, router, session
│   └── voiceterm/          # Binary: event loop, UI, theme, overlays
└── Cargo.lock
```

Benefits:
- Independent `cargo test -p voiceterm-audio`
- Faster incremental compilation
- Clean dependency boundaries
- Each crate has a focused public API

### 7.2 Resolve `src/src/` Nesting

The unconventional `src/src/` path forces `cd src &&` on every build command. Either:
- Move `Cargo.toml` to the repository root (idiomatic), or
- Document the rationale and add `[workspace]` even for single-member

### 7.3 Theme Module Reduction (14 -> 8 files)

**Keep:** mod.rs, colors.rs, palettes.rs, borders.rs, style_pack.rs, style_schema.rs, runtime_overrides.rs, detect.rs

**Remove/gate:** capability_matrix.rs, dependency_baseline.rs, texture_profile.rs, widget_pack.rs, rule_profile.rs, component_registry.rs

### 7.4 Extract Shared Utilities

Create these shared modules to eliminate duplication:

```
terminal_detect.rs      # is_jetbrains_terminal, is_cursor, is_warp (with OnceLock caching)
ui_utils.rs             # display_width, truncate_display, format_duration, section_line
stt_canonicalize.rs     # Shared token canonicalization for wake_word + navigation
test_helpers.rs         # StubSession, write_stub_script, recv_output_contains, strip_ansi
```

### 7.5 Break Down God Objects

| Object | Fields | Fix |
|--------|--------|-----|
| `EventLoopState` | 30+ | Sub-structs: PtyInputState, ThemeStudioState, OverlayState |
| `ButtonActionContext` | 24 | Sub-contexts by domain |
| `VoiceDrainContext` | 22 | Sub-structs: StatusContext, TimingContext |
| `TranscriptDeliveryContext` | 30+ | Sub-structs by domain |
| `StatusLineState` | 30+ | Builder pattern or typed state machine |

---

## 8. Project Configuration & Tooling

### 8.1 Cargo.toml Missing Metadata

```toml
# Add to [package]:
description = "Voice-first overlay for AI CLIs"
license = "MIT"
repository = "https://github.com/..."
rust-version = "1.70"
keywords = ["voice", "terminal", "whisper", "cli"]
categories = ["command-line-utilities"]
```

### 8.2 Add Release Profile

```toml
[profile.release]
lto = "thin"
codegen-units = 1
strip = true
```

Critical for audio/STT performance paths.

### 8.3 Add Lint Configuration

```toml
[lints.clippy]
all = "warn"
pedantic = { level = "warn", priority = -1 }
module_name_repetitions = "allow"
must_use_candidate = "allow"
```

### 8.4 Dependency Updates Needed

| Dependency | Current | Issue |
|------------|---------|-------|
| `serde_yaml` | 0.9.34 | **Deprecated** -- migrate to `serde_yml` |
| `ratatui` | 0.26.3 | Stale -- latest is 0.29+ |
| `crossterm` | 0.27.0 | Stale -- latest is 0.28+ |
| `num_cpus` | 1.17 | Superseded by `std::thread::available_parallelism()` |

### 8.5 Missing Configuration Files

- `rustfmt.toml` -- should exist even with defaults
- `clippy.toml` -- cognitive complexity threshold, line limits
- `.cargo/config.toml` -- platform-specific build instructions

---

## 9. Positive Observations

These are things the codebase does **exceptionally well** that should be preserved:

1. **Exceptional `unsafe` documentation.** Nearly every `unsafe` block has a `// SAFETY:` comment. Exemplary for a codebase with FFI (Whisper, CPAL, PTY).

2. **RAII discipline.** Terminal restoration, PTY cleanup, session guards, and test hooks all use Drop/guard patterns. No resource leaks on panic paths.

3. **Bounded resource management.** `MAX_PENDING_TRANSCRIPTS = 5`, `WAKE_EVENT_CHANNEL_CAPACITY = 8`, prompt log rotation at 5MB. Consistently prevents unbounded growth.

4. **Poison recovery.** The `lock_or_recover` pattern prevents panicked threads from deadlocking the application.

5. **Graceful degradation.** Voice pipeline falls back: native Rust -> Python. Resampler falls back: rubato -> basic FIR. Clear error messages at each level.

6. **Thorough test coverage.** Nearly every module has `#[cfg(test)] mod tests` with edge-case coverage. The wake_word soak test (5000 rounds, p95 latency budget) is production-grade guardrail testing.

7. **CI pipeline breadth.** 16 workflow files: mutation testing, parser fuzzing, latency guardrails, security audits. Far above average.

8. **Feature-gated optional dependencies.** `rubato` and `earshot` are properly behind feature flags with fallbacks.

9. **Configuration validation.** Shell metacharacter filtering, path canonicalization with repo-root confinement, ISO-639-1 language code validation.

10. **Session guard orphan cleanup.** Filesystem lease files with process liveness checks and start-time correlation.

11. **HudModule trait design.** Clean composable `id()`, `render()`, `min_width()`, `priority()`, `tick_interval()` abstraction.

12. **Exceptional governance documentation.** `AGENTS.md` with 12-step SOP, task router, risk matrix, CI lane mapping. Best-in-class.

---

## 10. Prioritized Action Plan

### Phase 1: Fix Runtime Risks (1-2 days)

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 1 | Fix UTF-8 byte slicing in 3 locations (CRIT-1, CRIT-2) | Low | Prevents runtime panics |
| 2 | Fix secret redaction to replace all occurrences (CRIT-5) | Low | Security fix |
| 3 | Fix event ID generation uniqueness (CRIT-6) | Low | Data integrity |
| 4 | Fix f32-to-i16 overflow in VAD (CRIT-7) | Low | Correctness |
| 5 | Fix `format_bar_standard` subtraction underflow (CRIT in theme audit) | Low | Prevents panic |
| 6 | Fix NaN validation in memory schema (MEDIUM-24) | Low | Correctness |

### Phase 2: Dependency & Config Hygiene (1 day)

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 7 | Migrate `serde_yaml` -> `serde_yml` (CRIT-3) | Low | Eliminates deprecated dep |
| 8 | Add `[lints.clippy]` to Cargo.toml (CRIT-8) | Low | Codifies lint policy |
| 9 | Add package metadata to Cargo.toml (HIGH-1 in config) | Low | License compliance |
| 10 | Add `[profile.release]` with LTO (HIGH-3 in config) | Low | Performance |
| 11 | Remove `num_cpus`, use stdlib (LOW-24) | Low | Removes dependency |
| 12 | Create `rustfmt.toml` and `clippy.toml` | Low | Tooling consistency |

### Phase 3: Eliminate Code Duplication (2-3 days)

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 13 | Extract shared `terminal_detect` module | Medium | Fixes HIGH-1 |
| 14 | Macro/generalize backend boilerplate | Medium | Fixes HIGH-2, ~300 lines |
| 15 | Extract shared `stt_canonicalize` module | Medium | Fixes HIGH-10 |
| 16 | Consolidate `rms_db`, stream building | Low | Fixes HIGH-3, HIGH-4 |
| 17 | Extract shared test helpers module | Medium | Fixes HIGH-11, MEDIUM-12 |
| 18 | Deduplicate status line indicators | Medium | Fixes HIGH-13 |
| 19 | Extract `ui_utils` (display_width, format_duration, etc.) | Medium | Fixes HIGH-14, MEDIUM-28, MEDIUM-29 |
| 20 | Generic `cycle_enum_option` for theme studio | Low | Fixes HIGH-8 |

### Phase 4: Reduce Complexity & Improve Modularity (3-5 days)

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 21 | Remove/gate 6 dead theme files (~2,600 lines) | Low | Fixes CRIT-4 |
| 22 | Break down `EventLoopState` into sub-structs | Medium | Fixes HIGH-5 |
| 23 | Extract `periodic_tasks` into named helpers | Medium | Fixes HIGH-6 |
| 24 | Decompose `main()` into setup functions | Medium | Fixes HIGH-7 |
| 25 | Add doc comments to core types | Medium | Fixes HIGH-15 |
| 26 | Audit and resolve all `#[allow(dead_code)]` | Medium | Fixes MEDIUM-15 |
| 27 | Wrap `env::set_var` in `unsafe` blocks | Low | Fixes HIGH-18 |

### Phase 5: Architectural Improvements (1-2 weeks)

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 28 | Upgrade ratatui 0.29 + crossterm 0.28 | High | Bug fixes, perf |
| 29 | Resolve `src/src/` nesting | High | Dev experience |
| 30 | Workspace decomposition (5-6 crates) | High | Compile times, modularity |

---

## 11. Continuation Pass Addendum (Post-Limit Deep Dive)

This addendum captures **new opportunities** from a second full sweep.  
These items are additive and are **not yet folded into** the original severity counts.

### 11.1 Method (Second Sweep)

- Ran:
  - `cd src && cargo clippy --workspace --all-targets --all-features -- -W clippy::all`
  - `cd src && cargo clippy --workspace --all-targets --all-features -- -W clippy::pedantic`
- Ran repository-wide pattern scans for:
  - queue operations (`remove(0)`, `drain(..)`), narrowing casts, `#[allow(...)]`, and large-function hotspots
- Manually reviewed hot runtime paths in:
  - `audio/dispatch.rs`, `audio/recorder.rs`, `config/validation.rs`, `devtools/storage.rs`, `status_line/animation.rs`, `backend/mod.rs`

### 11.2 Additional Findings

### ADD-1 (HIGH): `FrameDispatcher` uses front-drain in hot audio path (O(n) shifts + alloc churn)

**File:** `src/src/audio/dispatch.rs:72-77`

```rust
while self.pending.len() >= self.frame_samples {
    let frame: Vec<f32> = self.pending.drain(..self.frame_samples).collect();
    if let Err(err) = self.sender.try_send(frame) { ... }
}
```

`Vec::drain(..N)` from the front repeatedly shifts remaining elements. In live capture this runs continuously and adds avoidable CPU/memory pressure.

**Fix:** Use `VecDeque<f32>` for `pending` (`pop_front` semantics) or maintain a start offset and compact occasionally.

---

### ADD-2 (HIGH): `AppConfig::validate` is a monolithic mixed-responsibility function

**File:** `src/src/config/validation.rs:34-254`

`validate()` currently does all of the following in one body:
- range/policy validation
- filesystem canonicalization
- binary sanitization
- model auto-discovery
- language normalization

This raises cognitive load and weakens test granularity.

**Fix:** Split into staged helpers (`validate_numeric_bounds`, `validate_binary_paths`, `resolve_whisper_model`, `validate_language`, `validate_ffmpeg_device`) with a pure-validation pass separated from path-mutation side effects.

---

### ADD-3 (MEDIUM): `record_with_vad_impl` remains oversized after prior cleanup

**File:** `src/src/audio/recorder.rs:262-401`

The function still combines:
- stream construction for multiple sample formats
- callback dispatch wiring
- capture/VAD loop
- stop-reason handling
- metrics finalization

**Fix:** Decompose into three focused units:
1. stream builder,
2. capture loop,
3. final metrics/result assembly.

---

### ADD-4 (MEDIUM): Dev-event JSONL writer flushes on every append

**File:** `src/src/devtools/storage.rs:40-45`

```rust
writeln!(self.file, "{json}")?;
self.file.flush()?;
```

Per-event flush is durable but expensive for bursty event streams.

**Fix:** Add buffered policy (`flush_every_n`, timer-based flush, explicit flush on shutdown). Keep strict flush only for crash-critical modes.

---

### ADD-5 (MEDIUM): Integration test binary lookup uses runtime panic path

**File:** `src/tests/voiceterm_cli.rs:13`

```rust
option_env!("CARGO_BIN_EXE_voiceterm").expect("voiceterm test binary not built")
```

This pattern can panic at runtime in test environments where compile-time assumptions drift.

**Fix:** Use `env!("CARGO_BIN_EXE_voiceterm")` for compile-time enforcement, matching Clippy `option_env_unwrap` guidance.

---

### ADD-6 (MEDIUM): Boolean-field explosion still encodes many invalid state combinations

**Representative files:**
- `src/src/config/mod.rs:24` (`AppConfig`)
- `src/src/bin/voiceterm/config/cli.rs:119` (`OverlayConfig`)
- `src/src/bin/voiceterm/persistent_config.rs:362` (`CliExplicitFlags`)
- `src/src/bin/voiceterm/status_line/state.rs:141` (`StatusLineState`)

Multiple bool-heavy structs are still present after first-pass findings. This pattern increases illegal-state surface and branching complexity.

**Fix:** Convert grouped booleans into domain enums/newtypes (for example, `LoggingMode`, `WakePolicy`, `HudVisibilityPolicy`) or typed bitflags when combinations are truly valid.

---

### ADD-7 (MEDIUM): Widespread narrowing casts in runtime paths rely on silent truncation semantics

**Representative files:**
- `src/src/devtools/events.rs:133-138`
- `src/src/devtools/state.rs:105-107`
- `src/src/bin/voiceterm/audio_meter/format.rs:35-36`
- `src/src/bin/voiceterm/status_line/animation.rs:23-25`

Many casts are clamped beforehand, but conversion intent is not consistently explicit. This makes correctness audits harder on cross-platform widths.

**Fix:** Standardize with explicit conversion helpers (`try_from` + clamp/fallback + comment) and document intentional truncation where needed.

---

### ADD-8 (MEDIUM): Status-line animation uses wall-clock (`SystemTime`) instead of monotonic clock

**File:** `src/src/bin/voiceterm/status_line/animation.rs:21-54`

Animation frame selection currently keys off UNIX-epoch wall clock. Clock adjustments (NTP, manual changes, VM time jumps) can cause jittery frame jumps.

**Fix:** Base animation on `Instant` deltas from startup/session anchors for monotonic behavior.

---

### ADD-9 (LOW): Backend lookup allocates lowercase strings per query

**File:** `src/src/backend/mod.rs:86-90`

```rust
let name_lower = name.to_lowercase();
... b.name().to_lowercase() == name_lower
```

This is small but avoidable allocation in lookup path.

**Fix:** Use ASCII-insensitive comparison without allocation (`eq_ignore_ascii_case`) or pre-normalize registry keys.

---

### ADD-10 (LOW): Public devtools API docs still miss explicit failure contracts

**File:** `src/src/devtools/storage.rs:22-57`

Public `io::Result` methods (`open`, `open_session`, `append`, `flush`) currently lack explicit rustdoc `# Errors` sections.

**Fix:** Add `# Errors` docs per method (path creation/open failures, serialization failures, write/flush errors) to align with API-guideline failure documentation expectations.

---

### ADD-11 (LOW): Rolling prompt context uses `Vec::remove(0)` instead of queue structure

**File:** `src/src/bin/voiceterm/prompt/claude_prompt_detect.rs:159-171`

This is bounded (max 8 lines), so impact is low, but the data structure intent is queue-like.

**Fix:** Switch `recent_lines` to `VecDeque<String>` for direct push/pop queue semantics and clearer intent.

### 11.3 Source-Backed Pattern Notes (Rust References)

The second sweep aligned recommendations with current Rust guidance:

- Prefer monotonic timing (`Instant`) for elapsed-time behavior; `SystemTime` is non-monotonic.
- `std::env::{set_var, remove_var}` become explicitly unsafe in Rust 2024; call sites should be audited for single-thread safety.
- `option_env!(..).unwrap()` is flagged by Clippy; `env!` gives compile-time failure semantics when required.
- Numeric `as` casts that may truncate are accepted by Rust but are intentionally flagged by Clippy for explicitness.
- Public `Result` APIs should document `# Errors`.

See links in the next section.

## 12. Rust References Consulted (Google + Official Docs)

- Rust `Instant` docs: <https://doc.rust-lang.org/std/time/struct.Instant.html>
- Rust `SystemTime` docs: <https://doc.rust-lang.org/nightly/std/time/struct.SystemTime.html>
- Rust 2024 newly unsafe functions (`set_var`, `remove_var`): <https://doc.rust-lang.org/nightly/edition-guide/rust-2024/newly-unsafe-functions.html>
- `std::env::set_var` safety docs: <https://doc.rust-lang.org/std/env/fn.set_var.html>
- `std::env::remove_var` safety docs: <https://doc.rust-lang.org/std/env/fn.remove_var.html>
- `env!` macro (compile-time requirement): <https://doc.rust-lang.org/std/macro.env.html>
- `option_env!` macro: <https://doc.rust-lang.org/stable/core/macro.option_env.html>
- Clippy `option_env_unwrap`: <https://rust-lang.github.io/rust-clippy/rust-1.86.0/index.html#option_env_unwrap>
- Clippy `cast_possible_truncation`: <https://rust-lang.github.io/rust-clippy/master/index.html#cast_possible_truncation>
- Clippy docs index: <https://rust-lang.github.io/rust-clippy/>
- Rust API Guidelines (documentation / failure docs): <https://rust-lang.github.io/api-guidelines/documentation.html>
- `VecDeque` queue semantics: <https://doc.rust-lang.org/std/collections/struct.VecDeque.html>

---

*End of audit. Base report: 8 critical, 18 high, 30 medium, 25 low findings across 206 files. Addendum above contains additional post-limit opportunities pending triage into the main severity counts.*
