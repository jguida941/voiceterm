# Project-Wide Senior Code Audit (2026-02-23)

Full codebase review of the `codex-voice` project against Rust idioms, official
Rust API Guidelines, OWASP security practices, and software engineering best
practices. Covers architecture, threading, memory safety, voice/audio pipeline,
UI/overlay rendering, naming, modularity, and agent-generated code.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [P0 — Critical Findings](#p0--critical-findings)
3. [P1 — High-Priority Findings](#p1--high-priority-findings)
4. [P2 — Medium-Priority Findings](#p2--medium-priority-findings)
5. [P3 — Low-Priority Findings](#p3--low-priority-findings)
6. [Agent Code Audit (AREA-T1, AREA-M1)](#agent-code-audit)
7. [Positive Findings](#positive-findings)
8. [Action Items Summary](#action-items-summary)
9. [References](#references)

---

## Executive Summary

The voiceterm codebase demonstrates **solid architectural design** with effective
use of Rust's safety guarantees. The multi-threaded model (event loop, writer,
input, voice worker, wake-word listener) uses crossbeam channels with bounded
capacity and proper backpressure. Signal handling is async-signal-safe and global
state is minimal.

However, the audit identified **3 critical (P0)**, **10 high (P1)**, **18 medium
(P2)**, and **14 low (P3)** findings across 45 issues. The most urgent are a
panic-risk unchecked index in `memory/store/sqlite.rs`, rendering logic misplaced
in the event loop, and ~3K lines of dead theme infrastructure.

Agent-generated code from Wave 1 has one regression (AREA-T1: discard) and one
promising draft (AREA-M1: keep with 8 fixes).

---

## P0 — Critical Findings

### P0-1: Unchecked Index in Memory Store — Panic Risk

**File:** `memory/store/sqlite.rs` lines 83, 104

**Issue:** `self.events[idx]` uses direct index access from a HashMap of stored
indices. If the topic/task index becomes stale (event removed, vector
reallocated), this panics at runtime.

```rust
// Line 83 — by_topic()
let event = &self.events[idx];  // UNCHECKED — panics if idx >= len

// Line 104 — by_task()
let event = &self.events[idx];  // Same pattern
```

**Fix:**
```rust
let Some(event) = self.events.get(idx) else { continue; };
```

---

### P0-2: Rendering Logic in Event Dispatch — Separation of Concerns Violation

**File:** `event_loop.rs` lines 351–425

**Issue:** Six `render_*_overlay_for_state()` functions are defined inside the
event loop module instead of in the overlay/rendering modules they logically
belong to. This entangles event handling with presentation, making overlays
impossible to test independently.

Affected functions:
- `render_help_overlay_for_state()`
- `render_settings_overlay_for_state()`
- `render_theme_picker_overlay_for_state()`
- `render_theme_studio_overlay_for_state()`
- `render_transcript_history_overlay_for_state()`
- `render_toast_history_overlay_for_state()`

**Fix:** Move to a dedicated `overlay_dispatch.rs` or into each overlay's own
module. Keep event loop focused on dispatch logic only.

---

### P0-3: Excessive Dead Code with `#[allow(dead_code)]`

**Files:** `main.rs:28,48`, `overlays.rs:29-33`, `settings/items.rs:20-28`,
`theme/` (5 modules totaling ~3,100 lines)

**Issue:** 40+ instances of `#[allow(dead_code)]` across the codebase. The theme
subsystem has 5 fully-implemented but entirely unused modules:

| Module | Lines | Status |
|--------|-------|--------|
| `capability_matrix.rs` | 582 | Dead |
| `dependency_baseline.rs` | 490 | Dead |
| `texture_profile.rs` | 485 | Dead |
| `widget_pack.rs` | 536 | Dead |
| `rule_profile.rs` | 1,050 | Dead |

Additionally: `memory` module marked dead in `main.rs`, `ToastHistory` overlay
mode dead in `overlays.rs`, several settings items dead in `items.rs`.

**Fix:** Either integrate these modules or remove them. Use `#[cfg(feature = "...")]`
feature gates if they are planned for future phases. Dead code creates confusion
and isn't tested against regressions.

---

## P1 — High-Priority Findings

### P1-1: Unbounded Buffer Allocation in Audio Capture — DoS Risk

**File:** `audio/recorder.rs` lines 115–117

**Issue:** Expected sample count is calculated from device-reported sample rate
and channel count without defensive bounds. A malicious/misconfigured USB audio
device could demand gigabytes of memory.

```rust
let expected_samples =
    (duration.as_secs_f64() * device_sample_rate as f64 * channels as f64).ceil() as usize;
let buffer = Arc::new(Mutex::new(Vec::<f32>::with_capacity(expected_samples)));
```

**Fix:** Add a hard cap:
```rust
const MAX_EXPECTED_SAMPLES: usize = 48_000 * 16 * 60; // ~60s at 48kHz, 16ch
let expected_samples = computed_samples.min(MAX_EXPECTED_SAMPLES);
```

---

### P1-2: Unsafe FFI Without RAII Recovery Guarantee

**File:** `stt.rs` lines 68–122

**Issue:** `libc::dup2()` redirects stderr during Whisper model load. If the
model load panics or the restore `dup2` fails, stderr is permanently lost for
the process. No RAII guard ensures restoration.

**Fix:** Use a `StderrGuard` struct with `Drop` impl:
```rust
struct StderrGuard { orig_fd: i32 }
impl Drop for StderrGuard {
    fn drop(&mut self) {
        if self.orig_fd >= 0 {
            unsafe { libc::dup2(self.orig_fd, 2); libc::close(self.orig_fd); }
        }
    }
}
```

---

### P1-3: Race Condition in Wake-Word Listener Thread Cleanup

**File:** `wake_word.rs` lines 229–295

**Issue:** `reap_finished_listener()` checks `is_finished()` then joins with
timeout. If join times out, the old listener is detached but continues running.
The next `start_listener()` spawns a new detector, creating two threads
competing for the microphone.

**Fix:** Signal stop before joining. If join times out, do not start a new
listener until the old one actually terminates. Track listener identity.

---

### P1-4: Lock Poisoning Silent Failure in Audio Callback

**File:** `audio/recorder.rs` lines 129–171

**Issue:** Audio buffer callback uses `if let Ok(mut buf) = buffer_clone.lock()`
— silently drops audio frames if the lock is poisoned. No logging, no counter,
no user indication of missing audio.

**Fix:** Log poisoning events and increment a dropped-frame counter:
```rust
Err(_) => {
    log_debug("audio buffer lock poisoned — dropping frame");
    dropped.fetch_add(1, Ordering::Relaxed);
}
```

---

### P1-5: Frame Buffer Infinite Loop on Empty Frames

**File:** `audio/capture.rs` lines 128–140

**Issue:** `push_frame()` enforces max buffer size by popping old frames. If an
empty frame (0 samples) is pushed, `total_samples` never decreases, causing the
eviction loop to spin infinitely.

```rust
while self.total_samples > self.max_samples {
    if let Some(record) = self.frames.pop_front() {
        self.total_samples = self.total_samples.saturating_sub(record.samples.len());
        // If record.samples is empty, total_samples unchanged → infinite loop
    }
}
```

**Fix:** Reject empty frames at the top: `if samples.is_empty() { return; }`

---

### P1-6: Legacy Button Row Duplication

**File:** `status_line/buttons.rs` lines 549–738

**Issue:** ~190 lines of legacy button rendering duplicated alongside the
current implementation. Both paths produce status-line buttons but use different
logic, creating maintenance burden and divergence risk.

**Fix:** Remove the legacy path or extract a shared renderer.

---

### P1-7: Hardcoded ANSI Escape Bypassing Theme System

**File:** `status_line/buttons.rs` line 36

**Issue:** A raw ANSI escape code is hardcoded for the hidden launcher color,
bypassing the `ThemeColors` system entirely. Other buttons use theme colors
correctly.

**Fix:** Route through `ThemeColors` like all other button colors.

---

### P1-8: Overlay Rendering Code Duplication

**Files:** `help.rs` (405 lines), `settings/render.rs` (537 lines),
`theme_picker.rs` (254 lines), `theme_studio.rs` (563 lines),
`transcript_history.rs` (829 lines), `toast.rs` (672 lines)

**Issue:** All 6 overlay implementations duplicate the same structural pattern:
import `overlay_frame` helpers, build lines vec, add frame_top/title/separator,
format content rows, add footer, join with `"\n"`. No shared template or builder.

**Fix:** Create an `OverlayBuilder` in `overlay_frame.rs`:
```rust
pub struct OverlayBuilder { lines: Vec<String>, colors: ThemeColors, /* ... */ }
impl OverlayBuilder {
    fn frame_top(&mut self) -> &mut Self { /* ... */ }
    fn title(&mut self, text: &str) -> &mut Self { /* ... */ }
    fn separator(&mut self) -> &mut Self { /* ... */ }
    fn footer(&mut self, text: &str) -> &mut Self { /* ... */ }
    fn build(self) -> String { /* ... */ }
}
```

---

### P1-9: Status Line God-Files

**Files:** `status_line/format.rs` (936 lines), `status_line/buttons.rs` (801 lines)

**Issue:** Both files mix multiple concerns:
- `format.rs`: status banner layout + full/minimal/hidden HUD rendering +
  shortcut bar + right panel formatting + border/theme application
- `buttons.rs`: position calculation + rendering + badge formatting (latency,
  queue, wake, ready) + multiple HUD style handling

**Fix:** Decompose into sub-modules: `format/full_hud.rs`, `format/minimal_hud.rs`,
`format/shortcuts.rs`, `buttons/layout.rs`, `buttons/badges.rs`, `buttons/render.rs`.

---

### P1-10: Scattered Cycle Logic Duplication

**Files:** `memory/types.rs`, `theme_ops.rs`, `event_loop/input_dispatch/overlay.rs`
lines 695–745

**Issue:** Cycle-next/cycle-prev index logic reimplemented in 8+ places:
```rust
fn cycle_override_index(current_idx: usize, len: usize, direction: i32) -> usize {
    if len == 0 { return 0; }
    if direction < 0 { if current_idx == 0 { len - 1 } else { current_idx - 1 } }
    else { (current_idx + 1) % len }
}
```

**Fix:** Extract to a shared `utils/cycle.rs` or implement a `Cyclic` trait.

---

## P2 — Medium-Priority Findings

### P2-1: Style Pack Mutex Poisoning — Silent Recovery

**File:** `theme/style_pack.rs` lines 199–231

**Issue:** `runtime_style_pack_overrides()` recovers from poisoned mutex via
`into_inner()` without logging. If a thread panicked while modifying overrides,
subsequent reads silently accept potentially corrupted state.

**Fix:** Log all poisoning events. Consider `parking_lot::Mutex` (no poisoning).

---

### P2-2: Voice Manager Thread Lifecycle Edge Case

**File:** `voice_control/manager.rs` lines 232–256

**Issue:** Drop impl uses 200ms timeout for worker join. If worker is stuck in a
system call (audio I/O), it's silently detached without resource cleanup. The
`log_debug()` call in Drop may fail during process teardown.

**Fix:** Increase timeout to 500ms minimum. Signal stop before join attempt.

---

### P2-3: Configuration Injection via Shell Word Fallback

**File:** `config/util.rs` lines 10–14

**Issue:** `split_backend_command()` falls back to simple whitespace split when
`shell_words::split()` fails on malformed input. Input like `"cmd 'arg1 arg2"`
would bypass quoting semantics.

**Fix:** Log the parse failure. Consider rejecting malformed input entirely
rather than silently degrading.

---

### P2-4: Mutex Poisoning Silent Recovery in Voice Module

**File:** `voice.rs` lines 213, 239, 409

**Issue:** Three `.unwrap_or_else(|e| e.into_inner())` calls recover from
poisoned test hook storage without logging. Masks potential test corruption.

**Fix:** Add `log_debug("test hook storage lock poisoned; recovering")` on each.

---

### P2-5: Audio Stream Not Paused on Error Path

**File:** `audio/recorder.rs` lines 337–396

**Issue:** In `record_with_vad_impl()`, if an error occurs after `stream.play()`,
several early-exit paths don't pause the stream. Microphone stays open, blocking
other applications.

**Fix:** Use RAII `StreamGuard` that calls `stream.pause()` in its `Drop` impl.

---

### P2-6: Thread Handle Join Errors Silently Discarded

**File:** `voice_control/manager.rs` lines 175–177

**Issue:** `let _ = handle.join()` discards thread panic information. If the
voice worker panicked after sending its result, the panic trace is lost.

**Fix:** `if let Err(err) = handle.join() { log_debug(&format!("worker panicked: {err:?}")); }`

---

### P2-7: Duplicated Border Rendering

**File:** `overlay_frame.rs` lines 31–58

**Issue:** `frame_top()` and `frame_bottom()` contain near-identical logic
differing only in which corner characters are used. Not DRY.

**Fix:** Extract a shared `frame_line(left_corner, right_corner, horizontal, width)` helper.

---

### P2-8: Duplicated Border Generation in Format Module

**File:** `status_line/format.rs` lines 266–267, 533

**Issue:** Horizontal border strings generated with same repeat-pad-truncate
logic in two separate locations.

**Fix:** Extract to a shared border generation helper.

---

### P2-9: Hardcoded RGB Gradient in Banner

**File:** `banner.rs` lines 29–41

**Issue:** RGB gradient values are hardcoded constants, not routed through the
theme system. Banner colors won't change with theme selection.

**Fix:** Add banner gradient slots to `ThemeColors` or derive from accent colors.

---

### P2-10: Duplicate Mode Indicator Rendering

**Files:** `status_line/buttons.rs`, `status_line/format.rs`

**Issue:** Mode indicator (voice state badge) is rendered in both modules with
slightly different logic, creating divergence risk.

**Fix:** Single source of truth — render in one place, call from the other.

---

### P2-11: Duplicate Slider Rendering

**File:** `settings/render.rs` lines 256–293

**Issue:** Slider widget rendering logic for settings values reimplements
character-level bar building that could be shared with the audio meter renderer.

**Fix:** Extract a generic `render_bar(value, max, width, filled_char, empty_char)` utility.

---

### P2-12: Padding Calculation Duplication

**Files:** Multiple overlay and status line modules

**Issue:** `" ".repeat(padding)` and `display_width` + truncation patterns
appear in 6+ modules with identical logic.

**Fix:** Centralize in `overlay_frame.rs` as `padded_line(content, width)`.

---

### P2-13: Large Parameter Lists (>5 params)

**Files:** `event_loop/input_dispatch/overlay.rs`, `theme_picker.rs` line 121,
multiple `settings_handlers` functions

**Issue:** Several functions take 6–9 parameters, with `format_option_line_with_preview()`
already suppressed via `#[allow(clippy::too_many_arguments)]`.

**Fix:** Group related params into context structs.

---

### P2-14: Missing Type Aliases / Newtypes for Indices

**File:** `event_state.rs`

**Issue:** `EventLoopState` uses bare `usize` for multiple semantically distinct
indices (`theme_studio_selected`, `theme_picker_selected`, etc.). Easy to mix up.

**Fix:** Use `type SelectedIndex = usize;` or a `SelectedIndex(usize)` newtype.

---

### P2-15: Settings Module Boundary Confusion

**File:** `settings/items.rs`

**Issue:** Layout/dimension helpers (`settings_overlay_footer()`,
`settings_overlay_width_for_terminal()`, `settings_overlay_height()`) are in
`items.rs` instead of `render.rs` where they're consumed.

**Fix:** Move to `render.rs` or a dedicated `layout.rs`.

---

### P2-16: Inconsistent Rendering Function Naming

**Files:** All overlay modules

**Issue:** Overlay modules use `format_*()` (returns String) while `overlays.rs`
wraps them with `show_*()` (sends to writer). The naming convention isn't
documented and `format_` vs `show_` confusion is common.

**Fix:** Document the convention: `format_*()` = pure String builder,
`show_*()` = format + send to writer. Add a comment in `overlays.rs`.

---

### P2-17: Mixed Concerns in Transcript/Toast Modules

**Files:** `transcript_history.rs` (829 lines), `toast.rs` (672 lines)

**Issue:** Both files combine data storage, rendering, navigation state, and
search logic in a single file. These should be split into `storage + overlay`
sub-modules like `settings/` already does.

---

### P2-18: Silent Message Loss on Status Send Timeout

**File:** `writer/mod.rs` line 107

**Issue:** `try_send_status_message()` silently drops messages when the 2ms
timeout expires. Under heavy load, status updates vanish without logging.

**Fix:** Log dropped messages at debug level.

---

## P3 — Low-Priority Findings

### P3-1: PTY Input Buffer Offset Not Documented

**File:** `event_loop.rs` line 630

**Issue:** `pending_pty_input_offset += written` is non-saturating. Safe because
write result can't exceed buffer length, but the invariant isn't documented.

**Fix:** Add comment: `// Invariant: written <= remaining bytes in front buffer`

---

### P3-2: Hardcoded OSC8 Escape in Help Overlay

**File:** `help.rs` line 227

**Issue:** Raw OSC8 hyperlink escape sequence hardcoded instead of routing
through a terminal capability check.

---

### P3-3: Test Data Construction Duplication

**Files:** Multiple test modules

**Issue:** Test helper construction (creating mock themes, events, states)
duplicated across test modules. Not worth a shared test harness yet but worth
noting as the test suite grows.

---

### P3-4: Module Proliferation in Theme Directory

**File:** `theme/mod.rs` (13 sub-modules)

**Issue:** 5 of 13 theme sub-modules are entirely dead code (see P0-3). The
remaining 8 are properly structured.

---

### P3-5: Orphaned/Incomplete Features

**Files:** `memory/action_audit.rs`, `memory/context_pack.rs`

**Issue:** Fully implemented modules with no UI integration. Tests pass but
nothing calls them from the event loop.

**Fix:** Track as planned work items or remove.

---

### P3-6: Fragile Dependency Graph — No Enforcement

**Issue:** Event loop → overlays → renderers → theme chain is clean today but
undocumented. Adding features could introduce cycles without tooling to catch it.

**Fix:** Document the dependency DAG. Consider a `cargo-depgraph` check.

---

### P3-7: Scattered Layout Constants

**Files:** `event_loop.rs:75-85`, `status_line/format.rs:35-68`,
`overlay_frame.rs`, each overlay module

**Issue:** Timing, dimension, and padding constants spread across 10+ files.
Not centralized.

**Fix:** Create `layout_constants.rs` grouping event timing, status line
dimensions, overlay dimensions.

---

### P3-8: CSI Buffer Overflow — Mitigated

**File:** `input/parser.rs` lines 140–214

**Issue:** 32-byte max CSI buffer. Excess sequences are properly dropped. No
actual risk, but high-frequency long sequences could cause performance churn.

---

### P3-9: Resample Ratio Validation — Edge Case

**File:** `audio/resample.rs` lines 96–104

**Issue:** Out-of-range device rates are rejected with generic error. The
fallback `basic_resample` also validates, so no actual gap. Properly handled.

---

### P3-10: Wake-Word Sensitivity Clamping Not Logged

**File:** `wake_word.rs` lines 78–85

**Issue:** `WakeSettings::clamped()` silently adjusts out-of-range values. Users
won't know their sensitivity was modified.

**Fix:** Log when clamping adjusts a value.

---

### P3-11: Shell Injection in Config — Mitigated

**File:** `config/backend.rs` lines 30–79

**Issue:** Backend command passed to PTY, not shell. PTY execution model
mitigates command injection. Properly handled.

---

### P3-12: HashMap vs BTreeMap for Deterministic Iteration

**File:** `theme/component_registry.rs`

**Issue:** Component registry uses `HashMap`. For snapshot tests requiring
deterministic iteration order, `BTreeMap` would be more appropriate. Pre-existing
issue.

---

### P3-13: Missing `#[must_use]` on Public Query Methods

**Files:** `memory/store/sqlite.rs`, `memory/retrieval.rs`

**Issue:** Codebase uses `#[must_use]` on methods where ignoring the return value
is likely a bug (e.g., `style_id()`). Memory query methods lack this annotation.

---

### P3-14: Missing `Display` Impls for New Enums

**Files:** `memory/types.rs` (`EventType`), planned `BrowserFilterMode`

**Issue:** New enums should implement `Display` for logging/debugging. Existing
`EventType` has `as_str()` but not `Display`.

---

## Agent Code Audit

### AREA-T1: component_registry.rs — REGRESSION, DO NOT MERGE

**Severity:** Critical — Discard all changes

The agent **replaced** the existing well-structured component registry with a
simpler version that lost critical features:

| Feature | Original | Agent Version |
|---------|----------|---------------|
| Component count | 54 IDs | 42 IDs (lost 12 surfaces) |
| Registry key | `(ComponentId, ComponentState)` composite | `ComponentId` only — breaks per-state style resolution |
| `style_id()` | `const fn` exhaustive match | Removed entirely |
| `resolver_routed` flag | Present for legacy compat | Removed |
| Constructor name | `build_default()` | `new()` — misleading for expensive setup |
| Snapshot tests | TS-G04 gate evidence | Removed |

Missing surfaces: VoiceIdle, VoiceListening, VoiceProcessing, VoiceResponding,
MeterPeak, MeterThreshold, PaletteFrame, PaletteMatch, AutocompleteRow,
DashboardPanel, StartupTagline, IconPack.

**Action:** `git -C codex-voice-wt-t1 checkout -- .`

---

### AREA-M1: memory/browser.rs — PROMISING, NEEDS 8 FIXES

**Severity:** Medium (fixable)

The Memory Browser overlay (`browser.rs`, 591 lines) follows codebase patterns
well. All wiring changes were reverted (compile failure), only `browser.rs`
survived as untracked.

**What works:** Correct API usage, overlay rendering pattern, glyph resolution,
17 tests, state management following `SettingsMenuState` pattern.

**Issues to fix:**

| # | Priority | Fix |
|---|----------|-----|
| 1 | P1 | `"\r\n"` → `"\n"` line join (line 359) |
| 2 | P1 | Replace magic `100` with `BROWSER_QUERY_LIMIT` const |
| 3 | P1 | Safe timestamp slicing: `.get(..19).unwrap_or(&event.ts)` |
| 4 | P2 | Extract `framed_overlay_row()` into `overlay_frame.rs` |
| 5 | P2 | Rename `search_color` → `search_style` |
| 6 | P2 | Add `pub(crate) mod browser;` to `memory/mod.rs` |
| 7 | P2 | Rename `memory_browser_overlay_width` → `..._for_terminal` |
| 8 | P3 | Add `Display` impl for `BrowserFilterMode` |

---

## Positive Findings

The codebase gets many things right:

- **Thread ownership model**: Clean — event loop owns PTY, voice, wake-word.
  Writer thread spawned separately with bounded channel (512). Input thread
  with bounded channel (256). No shared mutable state except channels.
- **Crossbeam channels with backpressure**: PTY input gated at 256KB max buffer.
  Wake-word channel bounded at 8 messages.
- **Signal handling**: Single `AtomicBool` with `SeqCst` ordering. Async-signal-safe.
- **Only 2 global mutable statics**: `SIGWINCH_RECEIVED` (AtomicBool) and
  `RUNTIME_STYLE_PACK_OVERRIDES` (OnceLock<Mutex>). Both properly protected.
- **Saturating arithmetic**: Used correctly throughout event loop accounting.
- **Graceful shutdown**: Thread joins with timeouts. Channel disconnection
  triggers clean exit.
- **`const fn style_id()`**: Exhaustive match forces compile-time coverage for
  every `ComponentId` variant. Excellent Rust pattern.
- **Test isolation**: Fresh instances per test. No shared test state leakage.
- **Escape sequence parsing**: Bounded 32-byte CSI buffer with proper overflow
  handling.

---

## Action Items Summary

| # | Sev | Area | Action |
|---|-----|------|--------|
| 1 | P0 | Memory | Fix unchecked index in `sqlite.rs` — use `.get()` |
| 2 | P0 | Architecture | Move render functions out of `event_loop.rs` |
| 3 | P0 | Hygiene | Remove or feature-gate ~3.1K lines dead theme code |
| 4 | P1 | Audio | Cap buffer allocation in `recorder.rs` |
| 5 | P1 | FFI | Add RAII stderr guard in `stt.rs` |
| 6 | P1 | Threading | Fix wake-word listener dual-thread race |
| 7 | P1 | Audio | Log lock poisoning in audio callback |
| 8 | P1 | Audio | Reject empty frames in `capture.rs` |
| 9 | P1 | UI | Remove legacy button row duplication |
| 10 | P1 | UI | Route hardcoded ANSI through theme system |
| 11 | P1 | UI | Extract `OverlayBuilder` to DRY overlay code |
| 12 | P1 | UI | Decompose status_line god-files |
| 13 | P1 | Logic | Centralize cycle index logic |
| 14 | P2 | Threading | Log mutex poisoning in style_pack.rs |
| 15 | P2 | Threading | Increase voice manager join timeout |
| 16 | P2 | Config | Log shell_words parse failures |
| 17 | P2 | Voice | Log test hook poisoning recovery |
| 18 | P2 | Audio | RAII stream guard for error paths |
| 19 | P2 | Voice | Log thread join panics instead of discarding |
| 20 | P2 | UI | DRY border rendering in overlay_frame |
| 21 | P2 | UI | DRY border generation in format.rs |
| 22 | P2 | UI | Route banner gradient through theme |
| 23 | P2 | UI | Consolidate mode indicator rendering |
| 24 | P2 | UI | Extract shared slider/bar renderer |
| 25 | P2 | UI | Centralize padding helpers |
| 26 | P2 | API | Reduce parameter lists with context structs |
| 27 | P2 | Types | Add type aliases for index fields |
| 28 | P2 | Modules | Move settings layout helpers to render.rs |
| 29 | P2 | Naming | Document format_ vs show_ convention |
| 30 | P2 | Modules | Split transcript_history/toast into sub-modules |
| 31 | P2 | Writer | Log dropped status messages |
| 32 | P0 | Agent | Discard AREA-T1 changes entirely |
| 33 | P1 | Agent | Fix AREA-M1 browser.rs (8 issues above) |

---

## References

- Rust API Guidelines — naming: https://rust-lang.github.io/api-guidelines/naming.html
- Rust API Guidelines — interop: https://rust-lang.github.io/api-guidelines/interoperability.html
- Rust Book — error handling: https://doc.rust-lang.org/book/ch09-00-error-handling.html
- Rust Book — fearless concurrency: https://doc.rust-lang.org/book/ch16-00-concurrency.html
- POSIX signal safety: IEEE Std 1003.1-2017 §2.4.3
- Codebase files reviewed: `main.rs`, `event_loop.rs`, `event_state.rs`,
  `terminal.rs`, `writer/mod.rs`, `writer/state.rs`, `voice_control/manager.rs`,
  `voice.rs`, `stt.rs`, `audio/recorder.rs`, `audio/capture.rs`,
  `audio/resample.rs`, `wake_word.rs`, `input/parser.rs`, `input/mouse.rs`,
  `config/util.rs`, `config/backend.rs`, `help.rs`, `theme_studio.rs`,
  `theme_picker.rs`, `transcript_history.rs`, `toast.rs`, `overlays.rs`,
  `overlay_frame.rs`, `settings/items.rs`, `settings/state.rs`,
  `settings/render.rs`, `status_line/format.rs`, `status_line/buttons.rs`,
  `banner.rs`, `theme/mod.rs`, `theme/style_pack.rs`,
  `theme/component_registry.rs`, `memory/mod.rs`, `memory/types.rs`,
  `memory/store/sqlite.rs`, `memory/retrieval.rs`, `memory/action_audit.rs`,
  `memory/context_pack.rs`, `memory/browser.rs` (agent-generated)
