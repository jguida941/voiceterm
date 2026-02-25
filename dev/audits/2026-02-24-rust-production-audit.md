# VoiceTerm Rust Production-Grade Code Audit

**Generated:** 2026-02-24
**Trigger:** Manual full-codebase Rust audit -- NASA-level production readiness review
**Scope:** All 256 Rust source files (~80k+ LOC) across `rust/src/` library and `rust/src/bin/voiceterm/` binary
**Method:** READ-ONLY line-by-line review against AGENTS.md Engineering Quality Contract, Rust API Guidelines, and OWASP top 10

---

## Scope

Full-surface audit of the entire Rust codebase covering:

1. **Event Loop** -- `event_loop.rs`, `event_state.rs`, `input_dispatch/`, `output_dispatch.rs`, `overlay_dispatch.rs`, `periodic_tasks.rs`, `dev_panel_commands.rs`, tests (12 files, ~8,600 LOC)
2. **Theme System** -- `theme/`, `theme_ops.rs`, `theme_picker.rs`, `theme_studio/` (31 files, ~7,500 LOC)
3. **Audio/Voice/STT Pipeline** -- `audio/`, `voice.rs`, `stt.rs`, `vad_earshot.rs`, `voice_control/`, `wake_word.rs`, `audio_meter/`, `transcript/`, `transcript_history/` (35 files, ~8,000 LOC)
4. **IPC/Backend/Config** -- `ipc/`, `backend/`, `config/`, `codex/`, `auth.rs` (38 files, ~6,500 LOC)
5. **UI/HUD/Writer/Status** -- `main.rs`, `banner.rs`, `buttons.rs`, `hud/`, `status_line/`, `writer/`, `overlays.rs`, `icons.rs`, `dev_panel.rs`, `dev_command/`, `help.rs`, terminal utils (45 files, ~9,000 LOC)
6. **Memory/Settings/Input/Prompt/Infrastructure** -- `memory/`, `settings/`, `input/`, `prompt/`, `pty_session/`, `devtools/`, `legacy_tui/`, utility modules (60 files, ~7,000 LOC)

Focus areas:
- **Naming**: behavior-oriented, consistent, no unclear abbreviations
- **Comments**: explain "why" not "what", no stale comments
- **Duplication**: extract shared helpers, consolidate parallel logic
- **Risk**: unwrap/panic paths reachable from user input, unsafe blocks, resource leaks
- **Rust best practices**: error types, trait implementations, idiomatic patterns
- **Production readiness**: graceful degradation, logging, resource cleanup
- **Feature opportunities**: improvements that would harden production use

## Required Sources

- `AGENTS.md`
- `dev/DEVELOPMENT.md`
- `dev/active/MASTER_PLAN.md`
- `rust/Cargo.toml`
- `rust/src/**`

## Standards References

- Rust Book: <https://doc.rust-lang.org/book/>
- Rust API Guidelines: <https://rust-lang.github.io/api-guidelines/>
- Rustonomicon: <https://doc.rust-lang.org/nomicon/>
- Clippy lint index: <https://rust-lang.github.io/rust-clippy/master/>
- POSIX signal safety: <https://pubs.opengroup.org/onlinepubs/9699919799/>
- OWASP Top 10: <https://owasp.org/www-project-top-ten/>

## Guard Summary

| Area | Files Reviewed | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| Event Loop | 12 | 4 | 14 | 15 | 33 |
| Theme System | 31 | 6 | 17 | 14 | 37 |
| Audio/Voice/STT | 35 | 7 | 14 | 13 | 34 |
| IPC/Backend/Config | 38 | 5 | 13 | 20 | 38 |
| UI/HUD/Writer/Status | 45 | 6 | 16 | 15 | 37 |
| **TOTAL** | **161** | **28** | **74** | **77** | **179** |

---

## Findings

---

# PART 1: EVENT LOOP (EV)

## HIGH

### EV-H-1. `std::env::set_var` / `remove_var` in tests -- UB since Rust 1.83

`rust/src/bin/voiceterm/event_loop/tests.rs:1123,1149`

`std::env::set_var("VOICETERM_DEV_PACKET_AUTOSEND", "1")` and `remove_var` are called in test code. Since Rust 1.83 these are `unsafe` because mutating the environment while other threads read it is undefined behavior per POSIX. Tests run with `#[test]` which uses threads.

**Fix:** Inject the auto-send flag as a parameter to the function under test, or use a `thread_local!` override. If env mutation is necessary, use the `temp-env` crate with proper serialization.

---

### EV-H-2. `dev_packet_auto_send_runtime_enabled()` reads env on every call

`rust/src/bin/voiceterm/event_loop/dev_panel_commands.rs:5-11`

Calls `std::env::var` from a potentially hot path. `getenv` is not guaranteed thread-safe on all platforms. Environment configuration should be read once at startup and stored in config state.

**Fix:** Read `VOICETERM_DEV_PACKET_AUTOSEND` once during startup and store in `OverlayConfig` or `EventLoopDeps`.

---

### EV-H-3. Silent data loss in writer channel send

`rust/src/bin/voiceterm/event_loop/output_dispatch.rs:74-83`

```rust
Err(TrySendError::Full(_)) => {}   // silently drops data
```

The `Full` arm for non-`PtyOutput` variants silently discards the message. While theoretically unreachable, silent data loss in a terminal overlay could cause output corruption. Same pattern at `event_loop.rs:534-540`.

**Fix:** Replace with `unreachable!("unexpected non-PtyOutput variant")` or log a debug warning.

---

### EV-H-4. `unreachable!()` in production rendering path

`rust/src/bin/voiceterm/event_loop/overlay_dispatch.rs:124`

```rust
StudioPage::Home => unreachable!(),
```

Inside `render_theme_studio_overlay_for_state`, a nested match has `StudioPage::Home => unreachable!()`. If a refactoring alters the page variable, the process panics, leaving the terminal in a corrupted state.

**Fix:** Replace with a safe fallback that logs a warning and renders an empty page.

---

## MEDIUM

### EV-M-1. Magic byte constants scattered through input dispatch

`rust/src/bin/voiceterm/event_loop/input_dispatch.rs` (lines 55, 160, 227, 453), `overlay.rs` (lines 129, 221, 285, 386, 435), `theme_studio_input.rs` (lines 89, 104, 112, 326)

Raw hex byte literals: `0x04` (Ctrl-D), `0x05` (Ctrl-E), `0x0d` (CR), `0x1b` (Escape), `0x09` (Tab), `0x7f` (Backspace) used without named constants.

**Fix:** Define named constants at module level:
```rust
const CTRL_D_EOF: u8 = 0x04;
const CTRL_E_ENQ: u8 = 0x05;
const CARRIAGE_RETURN: u8 = 0x0d;
const ESCAPE: u8 = 0x1b;
const TAB: u8 = 0x09;
const BACKSPACE: u8 = 0x7f;
```

---

### EV-M-2. `send_enhanced_status_with_buttons` duplicated 15+ times

`periodic_tasks.rs`, `input_dispatch.rs`, `output_dispatch.rs` -- same 6-argument call repeated at least 15 times.

**Fix:** Extract helper:
```rust
fn emit_status_update(state: &EventLoopState, deps: &EventLoopDeps) {
    send_enhanced_status_with_buttons(
        &deps.writer_tx, &deps.button_registry, &state.status_state,
        state.overlay_mode, state.terminal_cols, state.theme,
    );
}
```

---

### EV-M-3. `set_status` call pattern duplicated ~20 times

`dev_panel_commands.rs`, `input_dispatch.rs`, `periodic_tasks.rs` -- same first 4 arguments repeated ~20 times.

**Fix:** Create a `StatusWriter` struct bundling `writer_tx`, `status_clear_deadline`, `current_status`, `status_state` with a single `set(msg, duration)` method.

---

### EV-M-4. `run_periodic_tasks` is ~350 lines handling 19 concerns

`rust/src/bin/voiceterm/event_loop/periodic_tasks.rs:8-359`

Handles resize, theme hot-reload, theme picker timeout, recording duration, meter levels, spinner animation, heartbeat, prompt tracker, voice drain, wake word HUD, transcript flush, latency expiry, toast capture, auto-voice trigger, and more in one function.

**Fix:** Extract each logical block into named sub-functions. The main function should read as a high-level orchestrator.

---

### EV-M-5. `handle_overlay_input_event` has 30+ match arms

`rust/src/bin/voiceterm/event_loop/input_dispatch/overlay.rs:35-466`

A single massive match combining overlay mode and input event. Hard to verify completeness.

**Fix:** Consider a table-driven or trait-based dispatch, or at minimum group by overlay mode with sub-functions.

---

### EV-M-6. `VoiceDrainContext` requires manually spreading 22 fields

`rust/src/bin/voiceterm/event_loop.rs:268-311`

Building context requires manual field-by-field extraction from `state`, `timers`, and `deps`. Error-prone when adding fields. Same pattern with `ButtonActionContext` (14 fields) and `SettingsActionContext` (11 fields).

**Fix:** Have context accept `&mut EventLoopState`, `&mut EventLoopTimers`, `&mut EventLoopDeps` directly, or provide a `from_parts(state, timers, deps, now)` constructor.

---

### EV-M-7. `EventLoopState` has 37 fields -- God Object

`rust/src/bin/voiceterm/event_state.rs:41-87`

Holds configuration, UI state, audio state, theme studio state, transcript history, PTY buffers, memory ingestion, prompt detection, and toast notifications.

**Fix:** Group into sub-structs: `ThemeStudioState`, `ThemePickerState`, `PtyBufferState`, `VoiceState`.

---

### EV-M-8. 10 identical `cycle_runtime_*_override` functions

`rust/src/bin/voiceterm/event_loop/input_dispatch/overlay/theme_studio_cycles.rs:1-199`

All 10 functions follow the exact same pattern: define array, find position, cycle index, return value. 185 lines of nearly identical code.

**Fix:** Create a generic helper:
```rust
fn cycle_option_values<T: PartialEq + Copy>(
    current: Option<T>, values: &[Option<T>], direction: i32,
) -> Option<T>
```

---

### EV-M-9. `Vec::remove(0)` for theme undo history (O(n))

`rust/src/bin/voiceterm/event_loop/input_dispatch/overlay/theme_studio_input.rs:552-560`

`history.remove(0)` shifts all elements. While `THEME_STUDIO_HISTORY_LIMIT` is 64, this is the wrong data structure.

**Fix:** Change to `VecDeque` and use `push_back`/`pop_front`.

---

### EV-M-10. Theme hot-reload silently swallows TOML parse errors

`rust/src/bin/voiceterm/event_loop/periodic_tasks.rs:69-102`

When TOML parsing or theme resolution fails, the error is silently swallowed. User gets no feedback that their edit was rejected.

**Fix:** Log the error and display a transient status message like "Theme file has errors."

---

### EV-M-11. Toast history overlay geometry hardcoded inline

`rust/src/bin/voiceterm/event_loop/input_dispatch/overlay/overlay_mouse.rs:81-93`

Width (`cols.min(60)`) and footer format are hardcoded rather than using shared functions from the toast module. Magic numbers 60 and 4 not sourced from named constants.

**Fix:** Extract `toast_history_overlay_width()`, `toast_history_overlay_inner_width()`, `toast_history_overlay_footer()`.

---

### EV-M-12. Test file is 5,035 lines with no module organization

`rust/src/bin/voiceterm/event_loop/tests.rs`

100+ test functions covering PTY I/O, voice, wake word, overlays, mouse, theme studio, dev panel, settings, latency, and toast -- all in one flat file.

**Fix:** Split into sub-modules: `tests/pty_io.rs`, `tests/voice_capture.rs`, `tests/overlay_navigation.rs`, etc.

---

### EV-M-13. Dead code: `should_send_staged_text_hotkey` never called

`rust/src/bin/voiceterm/event_loop/input_dispatch.rs:431-433`

Defined but never invoked. Appears replaced by `should_consume_insert_send_hotkey` and `should_finalize_insert_capture_hotkey`.

**Fix:** Remove the function.

---

### EV-M-14. Two functions with identical implementations

`rust/src/bin/voiceterm/event_loop/input_dispatch.rs:431-437`

`should_send_staged_text_hotkey` and `should_preserve_terminal_caret_navigation` have identical bodies.

**Fix:** Have one call the other, or inline the unused one.

---

## LOW

### EV-L-1. `use super::*` glob imports in 7 submodules

All event loop submodules use `use super::*`. Defeats dead-import analysis, can cause name collisions.

**Fix:** Replace with explicit imports, at minimum for new files.

---

### EV-L-2. Type aliases add no type safety

`rust/src/bin/voiceterm/event_state.rs:36-39`

`ThemeStudioSelectionIndex`, `ThemePickerSelectionIndex`, `SpinnerFrameIndex`, `InputBufferOffset` all resolve to `usize` with no newtype safety.

**Fix:** Either convert to newtype structs or remove aliases and document via field names.

---

### EV-L-3. `THEME_FILE_POLL_INTERVAL_MS` defined inside function body

`rust/src/bin/voiceterm/event_loop/periodic_tasks.rs:60`

Inconsistent with other timing constants at module level.

**Fix:** Move to top of file alongside `LATENCY_BADGE_MAX_AGE_SECS`, `TOAST_TICK_INTERVAL_MS`.

---

### EV-L-4. `let status = ...; let _ = status;` confusing discard pattern

`rust/src/bin/voiceterm/event_loop/input_dispatch/overlay/theme_studio_input.rs:75-76`

Captures and immediately discards export result. Misleading.

**Fix:** Call `execute()` without binding, or handle the status.

---

### EV-L-5. Comment references undefined "reply composers"

`rust/src/bin/voiceterm/event_loop/input_dispatch.rs:115-116`

"Reply composers should stay suppressed while the user is still typing" -- term not defined anywhere.

**Fix:** Replace with: "When Claude Code shows an interactive prompt (e.g., 'Do you want to apply? [Y/n]'), we suppress the HUD to avoid occluding the prompt."

---

### EV-L-6. `resolved_cols` called repeatedly without caching

`rust/src/bin/voiceterm/event_loop/overlay_dispatch.rs` -- called at lines 6, 11, 25, 43, 79, 154, 165, 170.

**Fix:** Compute once per cycle and pass as parameter.

---

### EV-L-7. Non-Home theme studio render branch exceeds 70 lines

`rust/src/bin/voiceterm/event_loop/overlay_dispatch.rs:76-147`

**Fix:** Extract `render_studio_page_content()` and `render_studio_overlay_frame()` helpers.

---

### EV-L-8. Key API functions lack doc comments

All 12 event loop files. `run_event_loop`, `handle_input_event`, `handle_output_chunk`, `run_periodic_tasks`, etc. have no `///` doc comments.

**Fix:** Add doc comments to key API surfaces.

---

### EV-L-9. `handle_theme_studio_bytes` has 4-level nested match

`rust/src/bin/voiceterm/event_loop/input_dispatch/overlay/theme_studio_input.rs:82-301`

~220 lines with deeply nested control flow.

**Fix:** Extract `handle_colors_page_input()`, `handle_colors_picker_input()`, etc.

---

### EV-L-10. 16-arm repetitive match in `apply_theme_studio_adjustment`

`rust/src/bin/voiceterm/event_loop/input_dispatch/overlay/theme_studio_input.rs:359-503`

**Fix:** Create a mapping from `ThemeStudioItem` to override field and use generic dispatch.

---

### EV-L-11. Test harness spawns real PTY session with `cat`

`rust/src/bin/voiceterm/event_loop/tests.rs:324`

Every test spawns a real process via PTY. Slow, can fail in CI containers.

**Fix:** Consider a `NullPtySession` mock for tests that don't exercise real PTY I/O.

---

### EV-L-12. Dead check: `direction != 0` is always true

`rust/src/bin/voiceterm/event_loop/input_dispatch/overlay.rs:300`

After matching `ArrowKey::Left | ArrowKey::Right`, direction is always -1 or 1, never 0.

**Fix:** Remove the dead check.

---

### EV-L-13. `#[cfg(not(test))]` creates divergent test/production paths

`rust/src/bin/voiceterm/event_loop/input_dispatch/overlay/theme_studio_input.rs:30-34,186-190`

Production code for `set_runtime_color_override` is compiled out in tests.

**Fix:** Use a thread-local mock hook instead of `cfg(not(test))`.

---

### EV-L-14. Missing `ToastHistoryToggle` in replay filter

`rust/src/bin/voiceterm/event_loop/input_dispatch/overlay.rs:468-473`

`TranscriptHistoryToggle` is filtered (not replayed after overlay close), but `ToastHistoryToggle` is not. Asymmetric.

**Fix:** Add to filter list for symmetry, or document intent.

---

### EV-L-15. `step` on `direction == 0` undocumented

`rust/src/bin/voiceterm/event_loop.rs:421`

When `direction == 0` (Enter), `step` becomes 1. Some items cycle on Enter, some do not. Inconsistency not documented.

**Fix:** Add a comment explaining the design choice.

---

# PART 2: THEME SYSTEM (TH)

## HIGH

### TH-H-1. `Box::leak` memory accumulation with no reclaim path

`rust/src/bin/voiceterm/theme/color_value.rs:194-208`

```rust
fn intern_string(s: &str) -> &'static str {
    Box::leak(s.to_string().into_boxed_str())
}
```

Called from `to_legacy_theme_colors()` for ~16 fields per invocation. Theme Studio applies colors on every picker confirmation. Over a long session, leaked memory grows without bound.

**Fix:** Use a `HashMap<String, &'static str>` dedupe cache, or switch `ThemeColors` from `&'static str` to owned `String`.

---

### TH-H-2. Poisoned mutex silently recovers with potentially stale data

`rust/src/bin/voiceterm/theme/style_pack.rs:164-170` (4 locations)

```rust
Err(poisoned) => {
    log_debug("runtime style-pack overrides lock poisoned; recovering read");
    *poisoned.into_inner()
}
```

A poisoned mutex means prior panic during mutation -- data may be in a partially-updated, inconsistent state. Silently continuing could produce garbled theme rendering.

**Fix:** Reset to default `RuntimeStylePackOverrides` when recovering from poison.

---

### TH-H-3. `do_copy_clipboard` writes raw escape sequences to stdout

`rust/src/bin/voiceterm/theme_studio/export_page.rs:135-148`

Writes OSC 52 directly to stdout from a state-management method. Bypasses the terminal rendering pipeline. `let _ =` discards write errors.

**Fix:** Return the OSC 52 string from the method and let the event loop handle the write.

---

### TH-H-4. Tautological test assertion: `files.is_empty() || !files.is_empty()`

`rust/src/bin/voiceterm/theme/theme_dir.rs:79-84`

Always `true` regardless of input. This test provides zero coverage.

**Fix:** Replace with meaningful assertion (e.g., all returned paths end in `.toml`).

---

### TH-H-5. `ThemeFileError` does not implement `std::error::Error`

`rust/src/bin/voiceterm/theme/theme_file.rs:26-55`

Implements `Display` but not `Error`. Prevents use with `?` in `Box<dyn Error>` contexts. `Io` variant stores stringified error, losing the original `std::io::Error`.

Compare: `StyleSchemaError` and `RuleProfileError` both correctly implement `Error`.

**Fix:** Add `impl std::error::Error for ThemeFileError {}`. Store `std::io::Error` instead of `String` for `Io` variant.

---

### TH-H-6. `theme_capability_compatible` always returns `true`

`rust/src/bin/voiceterm/theme/capability_matrix.rs:303-310`

`CrosstermCapability::all()` is a hardcoded const that always includes `TrueColor`. Function unconditionally returns `true` for every theme. Dead logic giving false sense of runtime checking.

**Fix:** Query actual terminal color support, or document as a placeholder.

---

## MEDIUM

### TH-M-1. 11 near-identical `normalize_*` functions

`rust/src/bin/voiceterm/theme/style_schema.rs:355-427`

All follow identical pattern: check for `Theme` variant, return `None`.

**Fix:** Generic `normalize<T: HasThemeVariant>(value: Option<T>) -> Option<T>`.

---

### TH-M-2. 10 identical if-let convert blocks in `apply_runtime_style_pack_overrides`

`rust/src/bin/voiceterm/theme/style_pack.rs:246-322`

**Fix:** Implement `From<RuntimeXOverride> for SchemaXOverride` for each pair.

---

### TH-M-3. `runtime_overrides.rs` duplicates schema enum types 1:1

`rust/src/bin/voiceterm/theme/runtime_overrides.rs` (96 lines)

10 runtime enums are near-duplicates of schema enums without `Theme` variant.

**Fix:** Use a shared macro to generate both sets.

---

### TH-M-4. `resolve_theme_file` is 87 lines of repetitive resolution

`rust/src/bin/voiceterm/theme/theme_file.rs:255-342`

10 identical color-field resolution blocks.

**Fix:** Extract into a helper that takes `&[(Option<String>, &mut ColorValue)]`.

---

### TH-M-5. `export_theme_file` is 108 lines

`rust/src/bin/voiceterm/theme/theme_file.rs:349-457`

Repetitive `push_str` and `format!` calls.

**Fix:** Factor each TOML section into its own helper.

---

### TH-M-6. `parse_style_schema` is 107 lines with V2/V3/V4 duplication

`rust/src/bin/voiceterm/theme/style_schema.rs:429-536`

**Fix:** Extract shared profile/override normalization into a helper.

---

### TH-M-7. `build_default()` in component_registry is ~260 lines

`rust/src/bin/voiceterm/theme/component_registry.rs:283-541`

**Fix:** Use a macro or data-driven approach (const array of tuples + loop).

---

### TH-M-8. `theme_studio_row` is 127 lines (19-arm match)

`rust/src/bin/voiceterm/theme_studio/home_page.rs:237-364`

**Fix:** Store static portions (label, tip) in a const array or associated method.

---

### TH-M-9. Misleading enum variant names `ColorsGlyphs` and `LayoutMotion`

`rust/src/bin/voiceterm/theme_studio/home_page.rs:27-28`

`ColorsGlyphs` controls glyph *profile* (not colors). `LayoutMotion` controls indicator *set* (not layout or motion). Display labels correctly show "Glyph profile" and "Indicator set".

**Fix:** Rename to `GlyphProfile` and `IndicatorSet`.

---

### TH-M-10. `all_component_ids()` uses Debug-format sorting

`rust/src/bin/voiceterm/theme/component_registry.rs:561-566`

`ids.sort_unstable_by_key(|id| format!("{id:?}"))` creates allocations per element and produces fragile ordering.

**Fix:** Derive `Ord` on `ComponentId` based on stable discriminant.

---

### TH-M-11. `from_style_id` duplicates entire `style_id` mapping in reverse (54+54 arms)

`rust/src/bin/voiceterm/theme/component_registry.rs:118-239`

**Fix:** Generate both mappings from a single const lookup array.

---

### TH-M-12. `RuleEvalContext::capabilities` is `Vec<String>` with linear search

`rust/src/bin/voiceterm/theme/rule_profile.rs:244`

O(n) scan per capability condition per rule.

**Fix:** Use `HashSet<String>`.

---

### TH-M-13. `parse_rule_profile` returns `Result<_, String>` (stringly-typed error)

`rust/src/bin/voiceterm/theme/rule_profile/eval.rs:137-139`

Discards structured `serde_json::Error`.

**Fix:** Return `Result<_, serde_json::Error>` or a dedicated error enum.

---

### TH-M-14. Colors/Borders pages hardcode Unicode markers, ignoring `glyph_set`

`rust/src/bin/voiceterm/theme_studio/colors_page.rs:235`

Rest of codebase checks `glyph_set` for Unicode vs ASCII. These pages hardcode Unicode.

**Fix:** Accept `GlyphSet` and use `overlay_row_marker()`.

---

### TH-M-15. Blanket `#![allow(dead_code)]` on multiple theme modules

`component_registry.rs:9`, `export_page.rs:8`, `components_page.rs`

Hides orphaned code from detection.

**Fix:** Remove blanket allow; add targeted `#[allow(dead_code)]` on specific items.

---

### TH-M-16. `validate_theme_file` does not check component palette references

`rust/src/bin/voiceterm/theme/theme_file.rs:495-522`

Only checks top-level color fields, missing palette references in `file.components`.

**Fix:** Extend validation to component style entries.

---

### TH-M-17. Custom `base64_encode` instead of using the `base64` crate

`rust/src/bin/voiceterm/theme_studio/export_page.rs:158-180`

Hand-rolled base64 encoder. Maintenance burden and potential subtle bugs.

**Fix:** Use `base64::engine::general_purpose::STANDARD.encode()`, or add comprehensive tests for custom impl.

---

## LOW

### TH-L-1. ANSI theme uses Unicode indicators despite targeting basic terminals

`rust/src/bin/voiceterm/theme/palettes.rs`

**Fix:** Use ASCII indicators for ANSI theme.

---

### TH-L-2. Magic numbers in Theme Studio rendering (60, 82, 20 unnamed)

`rust/src/bin/voiceterm/theme_studio/home_page.rs:105,168`

**Fix:** Extract into named constants.

---

### TH-L-3. Missing `#[non_exhaustive]` on growth-likely enums

`ColorField`, `StudioPage`, `ComponentId`, `ComponentState` -- likely to gain variants.

---

### TH-L-4. `as f64` casts in rule evaluation

`rust/src/bin/voiceterm/theme/rule_profile/eval.rs:17,20-21`

`u32 as f64` is lossless for realistic values but `as` casts are a code-smell.

**Fix:** Use `f64::from()` where possible, or comment on lossless guarantee.

---

### TH-L-5. Comments describe "what" not "why" throughout

`color_value.rs:106`, `theme_file.rs:263`, `style_pack.rs:34`

**Fix:** Focus comments on design decisions, constraints, and non-obvious trade-offs.

---

### TH-L-6. `indicator_set_preview` hardcodes Codex-specific default glyphs

`rust/src/bin/voiceterm/theme_studio/colors_page.rs:313-320`

Preview shows Codex defaults regardless of active theme.

**Fix:** Accept current theme's indicators as parameter.

---

### TH-L-7. `border_set_name` has silent fallback to "single"

`rust/src/bin/voiceterm/theme/theme_file.rs:473-487`

Unrecognized border sets silently default to "single".

**Fix:** Log a debug message for the fallback case.

---

### TH-L-8. `toml_theme_file_colors` is 63 lines mixing 3 concerns

`rust/src/bin/voiceterm/theme/style_pack.rs:521-584`

**Fix:** Extract named-theme resolution into a separate function.

---

### TH-L-9. `style_pack_field_studio_mapping_deferred` always returns false

`rust/src/bin/voiceterm/theme_studio/home_page.rs:496-511`

Dead configuration code since `STYLE_PACK_STUDIO_PARITY_COMPLETE = true`.

**Fix:** Remove or document retention purpose.

---

### TH-L-10. Inconsistent error types across theme subsystem

Four different error patterns: `ThemeFileError` (no `Error` trait), `StyleSchemaError` (correct), `RuleProfileError` (correct), `parse_rule_profile` (returns `String`).

**Fix:** Standardize on `Display` + `Error` for all error enums.

---

### TH-L-11. `execute` method mixes I/O with state mutation

`rust/src/bin/voiceterm/theme_studio/export_page.rs:89-107`

**Fix:** Return an `ExportResult` enum; let the caller perform I/O.

---

### TH-L-12. `detect.rs` only detects Warp terminal (9 lines)

`rust/src/bin/voiceterm/theme/detect.rs`

Very limited. No coverage for Windows Terminal, tmux, screen, SSH.

**Fix:** Add doc-comment explaining minimal scope.

---

### TH-L-13. `format_tab_bar` manually computes padding

`rust/src/bin/voiceterm/theme_studio/mod.rs:99-137`

Duplicates centering logic from `overlay_frame`.

**Fix:** Reuse existing padding utilities.

---

### TH-L-14. Color picker defaults to gray for non-RGB colors

`rust/src/bin/voiceterm/theme_studio/colors_page.rs:132-139`

ANSI16 value is silently discarded when opening picker.

**Fix:** Show warning or attempt best-effort ANSI-to-RGB conversion.

---

# PART 3: AUDIO/VOICE/STT PIPELINE (AV)

## HIGH

### AV-H-1. Duplicated `create_vad_engine` function

`rust/src/voice.rs:451-465` and `rust/src/bin/voiceterm/wake_word.rs:520-536`

Two nearly identical functions with identical `unreachable!()` calls. A new VAD variant requires updating both.

**Fix:** Extract into the library crate as a shared function.

---

### AV-H-2. `unreachable!()` on user-configurable VAD engine input

`rust/src/voice.rs:461` and `rust/src/bin/voiceterm/wake_word.rs:532`

`VadEngineKind::Earshot` can be selected via user config. Without the `vad_earshot` feature, `unreachable!()` panics the process on user-controlled input.

**Fix:** Return `anyhow::bail!()` or fall back to `SimpleThresholdVad` with a warning log.

---

### AV-H-3. RMS dB calculation implemented three times

`rust/src/audio/meter.rs:42-49`, `rust/src/audio/vad.rs:180-191`, `rust/src/bin/voiceterm/audio_meter/measure.rs:10-17`

Identical `energy.sqrt().max(1e-6)` and `20.0 * rms.log10()` math.

**Fix:** Make `audio::rms_db` `pub` and use it everywhere.

---

### AV-H-4. Duplicated `canonicalize_hotword_tokens` and `normalize_navigation_tokens`

`rust/src/bin/voiceterm/wake_word.rs:682-709` and `rust/src/bin/voiceterm/voice_control/navigation.rs:48-86`

Nearly identical token canonicalization: merging "code"+"x" into "codex", mapping "codec"/"kodak"/"cloud" etc. Textually identical match arms.

**Fix:** Extract shared `canonicalize_stt_tokens()` utility.

---

### AV-H-5. Duplicated audio sample format conversion (F32/I16/U16 match blocks)

`rust/src/audio/recorder.rs:171-216` and `rust/src/audio/recorder.rs:342-406`

Both `record_for` and `record_with_vad_impl` contain identical 3-arm format conversion blocks.

**Fix:** Define named converter functions and reduce with a macro or generic helper.

---

### AV-H-6. `drain_voice_messages` is 152 lines, destructures 25+ fields

`rust/src/bin/voiceterm/voice_control/drain.rs:75-227`

First 27 lines manually rebind all fields from `VoiceDrainContext`. Fragile when adding fields.

**Fix:** Pass `ctx` directly to sub-functions. Group fields into smaller sub-structs.

---

### AV-H-7. `VoiceJob::Drop` spin-wait can block UI thread up to 200ms

`rust/src/voice.rs:57-73`

Polls `handle.is_finished()` in a tight loop with 5ms sleeps. If dropped on the event-loop thread, this stalls event processing. Same in `VoiceManager::Drop` (500ms timeout).

**Fix:** Spawn join-wait on a background thread, or document that VoiceJob must not be dropped on the main thread.

---

## MEDIUM

### AV-M-1. Magic number `-60.0` dB repeated in 5+ files

`audio/meter.rs:6`, `audio/recorder.rs:470`, `voice.rs:264`, `audio_meter/format.rs:180,186`, `audio_meter/mod.rs:48`

**Fix:** Use `audio::meter::DEFAULT_METER_DB` consistently (make it `pub`).

---

### AV-M-2. `resample_to_target_rate` silently returns input on `device_rate == 0`

`rust/src/audio/resample.rs:45-47`

A rate of 0 Hz is nonsensical; silently passing through hides upstream bugs.

**Fix:** Log a warning or return empty.

---

### AV-M-3. `NON_SPEECH_PATTERN` regex includes typo "water spashing"

`rust/src/voice.rs:416`

Missing 'l' -- "spashing" vs "splashing". Both misspelled and correctly-spelled versions present.

**Fix:** Remove "water spashing" or document as known Whisper hallucination.

---

### AV-M-4. `execute_voice_navigation_action` is 204 lines

`rust/src/bin/voiceterm/voice_control/navigation.rs:169-373`

**Fix:** Extract each action handler into its own function.

---

### AV-M-5. `StubSession` test helper copy-pasted 3 times

`voice_control/drain/tests.rs:14-29`, `voice_control/navigation.rs:380-396`, `transcript/delivery.rs:168-184`

**Fix:** Define once in shared test utilities.

---

### AV-M-6. `recv_output_contains` test helper duplicated

`transcript/delivery.rs:186-198` and `transcript/session.rs:30-42`

**Fix:** Move to shared test helper.

---

### AV-M-7. NaN propagation via `LiveMeter` `f32::to_bits`/`from_bits`

`rust/src/audio/meter.rs:24-32`

NaN stored via `to_bits` will silently propagate through all arithmetic.

**Fix:** Add NaN guard: `let db = if db.is_nan() { DEFAULT_METER_DB } else { db };`

---

### AV-M-8. `record_with_vad_impl` is 176 lines

`rust/src/audio/recorder.rs:318-494`

Core recording function. Bug here = high impact.

**Fix:** Extract `build_vad_input_stream()`, `run_vad_capture_loop()`, `assemble_capture_metrics()`.

---

### AV-M-9. `handle_transcript_message` is 82 lines with high fan-out

`rust/src/bin/voiceterm/voice_control/drain/transcript_delivery.rs:35-117`

**Fix:** Decompose into smaller named steps.

---

### AV-M-10. `capture_voice_native` doesn't guard `capture_active` on panic

`rust/src/voice.rs:347-409`

If recorder lock panics, `capture_active` remains `true` forever.

**Fix:** Use `scopeguard` to ensure `capture_active.store(false, ...)` runs on panic.

---

### AV-M-11. `EarshotVad::process_frame` silently swallows predict errors

`rust/src/vad_earshot.rs:58-62`

Returns `Uncertain` on error. If earshot consistently fails, recording never stops.

**Fix:** Log first error. Return `Silence` after repeated failures.

---

### AV-M-12. Wake listener thread doesn't report panic to caller

`rust/src/bin/voiceterm/wake_word.rs:358-412`

Thread terminates silently on panic. User gets no indication wake-word listening stopped.

**Fix:** Wrap in `catch_unwind` and send a notification event.

---

### AV-M-13. Whisper thread count hardcoded to max 4

`rust/src/stt.rs:99-103`

On 16+ core machines, leaves performance on the table.

**Fix:** Make configurable via `--whisper-threads` or named constant with rationale comment.

---

### AV-M-14. `AudioLevel::default()` returns 0.0 dB (full-scale, not silence)

`rust/src/bin/voiceterm/audio_meter/mod.rs:20-26`

Every other part of codebase uses `-60.0` as silence floor. Default of `0.0` is confusing.

**Fix:** Implement `Default` explicitly with floor dB values.

---

## LOW

### AV-L-1. TODO without issue tracker reference

`rust/src/audio/tests.rs:199`

---

### AV-L-2. `#[allow(dead_code)]` on `active_source()` method

`rust/src/bin/voiceterm/voice_control/manager.rs:72-75`

---

### AV-L-3. `HistoryEntry::captured_at` stored but never read

`rust/src/bin/voiceterm/transcript_history.rs:53-54`

---

### AV-L-4. Inconsistent naming: `silence_streak_ms` vs `silence_tail_ms` vs `silence_duration_ms`

`audio/capture.rs:217,300,24`, `audio/vad.rs:22`

**Fix:** Standardize naming with a brief naming note in `VadConfig`.

---

### AV-L-5. `format_transcript_preview` silently clamps `max_len` to 4

`rust/src/bin/voiceterm/voice_control/transcript_preview.rs:22`

**Fix:** Document minimum in doc comment.

---

### AV-L-6. `serde_norway` used instead of `serde_yaml` without explanation

`rust/src/bin/voiceterm/voice_macros.rs:247`

**Fix:** Add comment explaining the choice.

---

### AV-L-7. `VoiceMacros::len()` exists without `is_empty()` (Clippy warning)

`rust/src/bin/voiceterm/voice_macros.rs:80`

**Fix:** Add `is_empty()`.

---

### AV-L-8. 17 constants in `wake_word.rs` without grouping comments

`rust/src/bin/voiceterm/wake_word.rs:21-66`

**Fix:** Group with section comments (capture timing, detection thresholds, thread lifecycle).

---

### AV-L-9. Test cleanup uses `let _ = fs::remove_dir_all()` instead of `tempfile::tempdir()`

`voice_control/drain/tests.rs:99,116`, `voice_macros.rs:408`

---

### AV-L-10. `wrap_display_lines` pads with empty strings undocumented

`rust/src/bin/voiceterm/transcript_history/render.rs:71-99`

**Fix:** Add doc comment noting padding behavior.

---

### AV-L-11. STT non-Unix stub may not compile (`AppConfig` not imported)

`rust/src/stt.rs:181`

---

### AV-L-12. Missing `strip_assistant_address_prefix` doc comment

`rust/src/bin/voiceterm/voice_control/navigation.rs:88-103`

**Fix:** Document that stripping only affects navigation matching, not transcript delivery.

---

### AV-L-13. Test `#[allow(dead_code)]` on `StubSession` fields

Multiple test files. Could use `#[cfg(test)]` instead.

---

# PART 4: IPC/BACKEND/CONFIG (IF)

## HIGH

### IF-H-1. Auth timeout leaks thread and subprocess

`rust/src/ipc/session/event_processing/auth.rs:11-23`, `rust/src/ipc/router.rs:382-392`

When auth times out, the background thread with its `run_login_command` child process continues running indefinitely. The subprocess holds `/dev/tty`. Thread + process persist until process exit.

**Fix:** Store a kill mechanism (child PID or cancellation token) in `AuthJob`. On timeout, signal the subprocess, then join the thread.

---

### IF-H-2. IPC stdin reader allows unbounded memory via malformed input

`rust/src/ipc/session/stdin_reader.rs:16-39`

No maximum line length enforced. A malicious client can send a multi-gigabyte JSON line causing OOM. The unbounded `mpsc::channel()` provides no backpressure.

**Fix:** Use `BufReader::read_line` with max-length check (e.g., 1 MiB). Use `mpsc::sync_channel` with bounded capacity.

---

### IF-H-3. `--dangerously-skip-permissions` passed without additional confirmation

`rust/src/ipc/session/claude_job.rs:42-48`

Controlled solely by `claude_skip_permissions` config boolean. Any IPC client can trigger arbitrary Claude code execution without permission prompts. No additional confirmation, rate limiting, or audit logging.

**Fix:** Log a warning when active. Consider per-session or per-prompt confirmation.

---

### IF-H-4. Prompt injection via slash commands in IPC `send_prompt`

`rust/src/ipc/router.rs:76-135`

`{"cmd":"send_prompt","prompt":"/exit"}` triggers `handle_exit`, shutting down the session. `parse_input` treats IPC prompts as REPL commands.

**Fix:** Do not route `IpcCommand::SendPrompt` through `parse_input`. Slash command parsing should only apply to human REPL input, not structured JSON IPC.

---

### IF-H-5. `cancel_active_jobs` blocks event loop for 150ms

`rust/src/ipc/router.rs:94-102`

`ClaudeJob::Drop` calls `terminate_piped_child` which has a 150ms sleep loop on the main IPC event loop thread.

**Fix:** Move termination to a background thread or use non-blocking reaping.

---

## MEDIUM

### IF-M-1. Duplicated `write_stub_script` test helper

`rust/src/ipc/tests.rs:77-93` and `rust/src/codex/tests.rs:408-424`

**Fix:** Extract into shared test utility.

---

### IF-M-2. `process_claude_events` is 128 lines with 4-level nesting

`rust/src/ipc/session/event_processing/claude.rs:10-128`

**Fix:** Extract piped and PTY paths into separate functions.

---

### IF-M-3. Magic drain timeout numbers

`rust/src/ipc/session/event_processing/claude.rs:53-54`

```rust
let drain_ms = if job.pending_exit.is_some() { 5 } else { 25 };
```

**Fix:** Define named constants.

---

### IF-M-4. Provider string literals hardcoded instead of using `Provider::as_str()`

`event_processing/codex.rs:34,43,57,85`, `event_processing/claude.rs:151`, `router.rs:199,202,221,224`

**Fix:** Use `Provider::Codex.as_str()` / `Provider::Claude.as_str()`.

---

### IF-M-5. `validate()` function is 225 lines

`rust/src/config/validation.rs:34-259`

**Fix:** Extract thematic validators: `validate_voice_pipeline()`, `validate_binaries()`, `validate_language()`.

---

### IF-M-6. `BackendRegistry::register` allows silent duplicate names

`rust/src/backend/mod.rs:112-114`

**Fix:** Check for name conflicts before inserting.

---

### IF-M-7. `send_event` silently swallows stdout write failures

`rust/src/ipc/session/event_sink.rs:7-27`

Broken stdout pipe means client disconnected, but execution continues.

**Fix:** Track consecutive failures. Set a shutdown flag on persistent `BrokenPipe`.

---

### IF-M-8. `session_id` uses millisecond timestamp -- not unique under rapid restarts

`rust/src/ipc/session/state.rs:18-24`

**Fix:** Use `uuid::Uuid::new_v4()` or add PID and random component.

---

### IF-M-9. `VOICETERM_PROVIDER` env var silently falls back to Codex

`rust/src/ipc/session/state.rs:33-36`

Unrecognized value produces no warning.

**Fix:** Log a warning for unrecognized provider values.

---

### IF-M-10. `call_codex_via_session` re-sanitizes full output buffer on every poll

`rust/src/codex/pty_backend/session_call.rs:150-152`

Cache is dirtied on every chunk. With 2 MiB max, sanitization runs on megabytes every 50ms.

**Fix:** Incremental sanitization -- only sanitize new chunks and append.

---

### IF-M-11. IPC `Provider` enum only has 2 variants; backend registry has 5+

`rust/src/ipc/protocol.rs:197-202` vs `rust/src/backend/mod.rs:72-82`

Gemini, Aider, and OpenCode backends invisible to IPC clients.

**Fix:** Dynamically derive IPC provider list from registry, or document the limitation.

---

### IF-M-12. `BoundedEventQueue::push` can drop terminal events under backpressure

`rust/src/codex/backend.rs:296-303`

Callers discard `BackendQueueError` with `let _ =`. Critical `Finished`/`FatalError` events could be lost.

**Fix:** Ensure terminal events always succeed (force eviction or expand capacity).

---

### IF-M-13. `normalize_control_bytes` guard could silently truncate output

`rust/src/codex/pty_backend/output_sanitize.rs:97-107`

Guard is `4 * input_length`. Pathological PTY output could exhaust it.

**Fix:** Log when guard is exhausted.

---

## LOW

### IF-L-1. `#[allow(dead_code)]` on `started_at` -- misleading on `AuthJob` (field IS used)

`rust/src/ipc/session.rs:74-75,84-85`

---

### IF-L-2. Typo "possibe" in aider backend doc comment

`rust/src/backend/aider.rs:2`

---

### IF-L-3. Section header says "Stdin Reader Thread" above Claude job helpers

`rust/src/ipc/session.rs:162-168`

---

### IF-L-4. `CustomBackend::command()` has unreachable `Ok(_)` branch

`rust/src/backend/custom.rs:60-61`

---

### IF-L-5. `IpcEvent` does not derive `PartialEq` -- verbose test assertions

`rust/src/ipc/protocol.rs:16`

---

### IF-L-6. `IpcCommand` does not derive `Serialize` -- no round-trip testing

`rust/src/ipc/protocol.rs:150`

---

### IF-L-7. `Provider::Err` type is `&'static str` instead of proper error

`rust/src/ipc/protocol.rs:218-219`

---

### IF-L-8. `sanitize_pty_output` re-exported from `codex/` but is a generic utility

`rust/src/codex/mod.rs:21`

**Fix:** Move to shared `utils::pty` module.

---

### IF-L-9. `OnceLock` in test support cannot be reset between tests

`rust/src/ipc/session/test_support.rs:11`

---

### IF-L-10. `run_ipc_loop` panics with `mutants` feature in non-test builds

`rust/src/ipc/session/loop_control.rs:20-22`

**Fix:** Split `test` and `mutants` cfg; use log+break for mutants.

---

### IF-L-11. `WrapperCmd` comments describe syntax, not purpose

`rust/src/ipc/router.rs:28-37`

---

### IF-L-12. `WrapperCmd::Status` and `WrapperCmd::Capabilities` do identical things

`rust/src/ipc/router.rs:168-173`

---

### IF-L-13. `env::set_var` / `remove_var` in config tests (unsafe 2024 edition)

`rust/src/config/tests.rs:547-554`

---

### IF-L-14. `validate()` calls `canonical_repo_root()` unconditionally

`rust/src/config/validation.rs:37`

Runs even for early-exit modes (`--list-input-devices`, `--doctor`).

---

### IF-L-15. `CodexBackend::prompt_pattern` returns empty string (matches everything)

`rust/src/backend/codex.rs:47-49`

**Fix:** Return `Option<&str>` with `None`.

---

### IF-L-16. `AuthResult` uses `String` error type

`rust/src/auth.rs:4`

**Fix:** Use a dedicated `AuthError` enum.

---

### IF-L-17. Backend modules (aider, gemini, opencode) are structural boilerplate

`rust/src/backend/{aider,gemini,opencode}.rs`

**Fix:** Define a `define_backend!` macro.

---

### IF-L-18. `run_ipc_mode` drops `cmd_tx` immediately in test/mutant builds

`rust/src/ipc/session.rs:228-237`

---

### IF-L-19. `process_voice_events` ignores `cancelled` flag for voice cleanup

`rust/src/ipc/session/event_processing/voice.rs:7-9`

Returns `true` without setting `stop_flag` or emitting `VoiceEnd`.

**Fix:** Set `job.stop_flag = true` and emit `VoiceEnd` event.

---

### IF-L-20. `codex_cli_backend` is `Arc` but only used on one thread

`rust/src/ipc/session.rs:45`

---

# PART 5: UI/HUD/WRITER/STATUS (UI)

## HIGH

### UI-H-1. Triplicated `is_jetbrains_terminal()` with divergent behavior

`rust/src/bin/voiceterm/main.rs:121-160`, `banner.rs:197-233`, `writer/render.rs:22-68`

Three copies with different match sets: `main.rs` and `render.rs` check 5 hints (`jetbrains`, `jediterm`, `pycharm`, `intellij`, `idea`), but `banner.rs` only checks 2 (`jetbrains`, `jediterm`). `render.rs` caches with `OnceLock`; others re-evaluate.

**Fix:** Extract a single canonical `is_jetbrains_terminal()` into a shared utility with `OnceLock` caching.

---

### UI-H-2. Shell injection via `sh -lc` with user-supplied command

`rust/src/bin/voiceterm/image_mode.rs:61-75`

`image_capture_command` config value passed directly to `sh -lc`. Login shell loads user profile which may alter PATH.

**Fix:** Use `-c` instead of `-lc`. Document trust model. Prefer `Command::new(program).args(args)` when shell interpretation is not needed.

---

### UI-H-3. `unreachable!()` in `ButtonAction::to_input_event()` reachable by user input

`rust/src/bin/voiceterm/buttons.rs:49-53`

`CollapseHiddenLauncher` variant triggers panic if routing changes.

**Fix:** Return `Option<InputEvent>` and return `None` for this variant.

---

### UI-H-4. `libc::signal()` is deprecated and non-portable

`rust/src/bin/voiceterm/terminal.rs:30-39`

POSIX documents that `signal()` behavior is "unspecified" after handler fires on some systems.

**Fix:** Replace with `libc::sigaction()` using `SA_RESTART`.

---

### UI-H-5. `SystemTime` used for animation timing instead of monotonic clock

`rust/src/bin/voiceterm/status_line/animation.rs:18-24,35-38,49-52`

Subject to NTP adjustments. Animation frames can repeat or jump.

**Fix:** Use `Instant::now()` with stored start reference.

---

### UI-H-6. Multi-byte character boundary issue in `StreamLineBuffer::push_char`

`rust/src/bin/voiceterm/stream_line_buffer.rs:20-26`

Guard checks `buffer.len()` (bytes) but `push(ch)` for 4-byte emoji can exceed `max_bytes` by 3.

**Fix:** Check `self.buffer.len() + ch.len_utf8() <= self.max_bytes`.

---

## MEDIUM

### UI-M-1. O(n) front-drain on latency history Vec

`rust/src/bin/voiceterm/status_line/state.rs:213-219`

`drain(0..overflow)` shifts all remaining elements.

**Fix:** Use `VecDeque<u32>`.

---

### UI-M-2. Fragile `text.pop()` to remove trailing newline

`rust/src/bin/voiceterm/image_mode.rs:35-38`

Relies on exact last character being `\n`. Brittle if format string changes.

**Fix:** Use conditional formatting directly.

---

### UI-M-3. `#![allow(dead_code)]` blanket on icons module

`rust/src/bin/voiceterm/icons.rs:5`

**Fix:** Remove blanket; add targeted allows with comments.

---

### UI-M-4. Identity function `effective_hud_style()` returns input unchanged

`rust/src/bin/voiceterm/status_line/layout.rs:19-21`

Remnant of removed compaction policy. Stale doc-comment says "backend-specific compaction policies."

**Fix:** Inline away and update doc-comment.

---

### UI-M-5. Hardcoded numeric constants throughout HUD rendering

`hud/latency_module.rs:20-25` (150, 300, 500, 800), `hud/meter_module.rs:18` (6 bars), `help.rs:215` (key_width=10), `dev_panel.rs:168` (label_width=17), `terminal.rs:82` (toast_height=10), `status_line/buttons/badges.rs:53-59` (latency 300, 500)

**Fix:** Extract all into named constants with doc-comments.

---

### UI-M-6. `get_icons()` uses bare `bool` parameter

`rust/src/bin/voiceterm/icons.rs:94-100`

`get_icons(true)` is unclear at call sites.

**Fix:** Accept `enum GlyphMode { Unicode, Ascii }`.

---

### UI-M-7. Onboarding TOML parser drops values containing `=`

`rust/src/bin/voiceterm/onboarding.rs:38-44`

Uses `split('=').nth(1)` -- truncates values with embedded `=`.

**Fix:** Use `splitn(2, '=').nth(1)`.

---

### UI-M-8. `WriterMessage::Status` marked `#[allow(dead_code)]`

`rust/src/bin/voiceterm/writer/mod.rs`

**Fix:** Verify usage. If dead, remove variant entirely.

---

### UI-M-9. `StatusBanner.buttons` has misleading `#[allow(dead_code)]`

`rust/src/bin/voiceterm/status_line/state.rs:106-107`

Field IS populated and consumed. Allow is wrong.

**Fix:** Remove `#[allow(dead_code)]`.

---

### UI-M-10. Overly aggressive ANSI reset in `truncate_display`

`rust/src/bin/voiceterm/status_line/text.rs:59-62`

Triggers for any `\x1b[` sequence including cursor movements, not just colors.

**Fix:** Track whether last escape was a color setter (SGR).

---

### UI-M-11. `main()` exceeds 450 lines

`rust/src/bin/voiceterm/main.rs:228-~690`

**Fix:** Extract `parse_and_validate_config()`, `initialize_runtime()`, `run_event_loop()`.

---

### UI-M-12. `broker_worker()` exceeds 130 lines

`rust/src/bin/voiceterm/dev_command/mod.rs:351-480`

**Fix:** Extract `handle_active_process()`, `poll_process_completion()`, `handle_idle_request()`.

---

### UI-M-13. `format_button_row_with_positions` exceeds 100 lines

`rust/src/bin/voiceterm/status_line/buttons.rs`

**Fix:** Extract badge rendering and position calculation.

---

### UI-M-14. `env::set_var` in main before threads spawn

`rust/src/bin/voiceterm/main.rs:262`

Unsafe in Rust 1.66+. Latent hazard if init order changes.

**Fix:** Pass through config struct rather than environment bridging.

---

### UI-M-15. Duplicated `with_color()` helper in status_line

`rust/src/bin/voiceterm/status_line/format.rs:93-99` and `status_line/buttons.rs`

**Fix:** Move to `status_line/text.rs`.

---

### UI-M-16. `take_line()` trims whitespace without documenting

`rust/src/bin/voiceterm/stream_line_buffer.rs:32-47`

Implicit normalization callers may not expect.

**Fix:** Add doc-comment noting trim behavior.

---

## LOW

### UI-L-1. Animation timing constant comments should be `///` doc-comments

`rust/src/bin/voiceterm/status_line/animation.rs:12-13`

---

### UI-L-2. `resolve_sound_flag` name misleading (just an OR)

`rust/src/bin/voiceterm/cli_utils.rs`

**Fix:** Rename to `is_sound_enabled()`.

---

### UI-L-3. `pty_line_col_estimate` name ambiguous

`rust/src/bin/voiceterm/writer/state.rs:82`

**Fix:** Rename to `pty_current_col`.

---

### UI-L-4. Inconsistent error handling: mouse `write_all` logged but `flush` discarded

`rust/src/bin/voiceterm/writer/mouse.rs:13-31`

**Fix:** Log flush errors too.

---

### UI-L-5. Inconsistent `OnceLock` caching of terminal detection

`writer/render.rs` caches; `main.rs` and `banner.rs` re-evaluate.

**Fix:** Centralize (resolved by UI-H-1).

---

### UI-L-6. Stale doc-comment on `effective_hud_style_for_state`

`rust/src/bin/voiceterm/status_line/layout.rs:23-24`

References "backend-specific compaction policies" that no longer exist.

---

### UI-L-7. TODO comments without issue tracker references

Multiple files.

---

### UI-L-8. Repeated `format!` allocations for cursor sequences in render hot path

`rust/src/bin/voiceterm/writer/render.rs:172,208,236,262,276,297,319`

**Fix:** Use `write!(&mut sequence, ...)` directly.

---

### UI-L-9. Inconsistent `let _ =` vs explicit logging for channel sends

`dev_command/mod.rs`, `writer/state.rs`

**Fix:** Log on error for normal-path sends.

---

### UI-L-10. `as u16` casts without overflow checks in render loop

`rust/src/bin/voiceterm/writer/render.rs:207,235,296`

**Fix:** Use `u16::try_from(idx).unwrap_or(0)`.

---

### UI-L-11. Test env var save/restore boilerplate in `color_mode.rs`

**Fix:** Create `EnvGuard` struct with RAII restore.

---

### UI-L-12. Arrow key parser doesn't handle kitty keyboard protocol

`rust/src/bin/voiceterm/arrow_keys.rs`

**Fix:** Consider adding kitty protocol support or document supported sequences.

---

### UI-L-13. No cleanup of `.voiceterm/captures/` directory

`rust/src/bin/voiceterm/image_mode.rs`

**Fix:** Add configurable retention policy.

---

### UI-L-14. `status_clear_height_for_redraw` should be a method on `DisplayState`

`rust/src/bin/voiceterm/writer/state.rs:67-73`

---

### UI-L-15. `#[allow(dead_code)]` on `SPINNER_ASCII`, `SPINNER_CIRCLE`, `ASCII_ICONS`

`rust/src/bin/voiceterm/icons.rs`

If genuinely unused, remove. If reserved, document.

---

# PART 6: CROSS-CUTTING PATTERNS

## Systemic Issues (apply to multiple subsystems)

### SYS-1. `std::env::set_var` / `remove_var` used unsafely in tests

**Files:** `event_loop/tests.rs`, `config/tests.rs`, `devtools/storage.rs`, `color_mode.rs`

Since Rust 1.83, these are `unsafe`. The test runner is multi-threaded.

**Fix (project-wide):** Migrate all env-mutating tests to either (a) parameter injection, (b) thread-local overrides, or (c) the `temp-env` crate.

---

### SYS-2. Inconsistent error types across modules

| Pattern | Examples |
|---|---|
| `Result<_, String>` | `auth.rs`, `parse_rule_profile`, voice macros |
| Custom enum without `Error` trait | `ThemeFileError` |
| Custom enum with `Error` trait | `StyleSchemaError`, `RuleProfileError` |
| `anyhow::Error` | Most binary-level code |

**Fix:** Standardize: library code uses custom enums with `Display` + `Error`. Binary code uses `anyhow`. Never return `Result<_, String>`.

---

### SYS-3. Blanket `#![allow(dead_code)]` on 5+ modules

**Files:** `icons.rs`, `component_registry.rs`, `export_page.rs`, `components_page.rs`, `writer/mod.rs`

**Fix:** Remove blankets; use targeted allows with rationale comments.

---

### SYS-4. `unreachable!()` in 6+ locations reachable from user input or refactoring

**Files:** `overlay_dispatch.rs`, `buttons.rs`, `voice.rs`, `wake_word.rs`

**Fix (project-wide):** Audit every `unreachable!()` call. Replace with safe fallbacks in production paths, reserve for genuinely impossible arms.

---

### SYS-5. Long functions (>50 lines) in 20+ locations

**Top offenders:**
- `main.rs:main()` -- 450+ lines
- `periodic_tasks.rs:run_periodic_tasks` -- 350 lines
- `component_registry.rs:build_default()` -- 260 lines
- `config/validation.rs:validate()` -- 225 lines
- `navigation.rs:execute_voice_navigation_action` -- 204 lines
- `recorder.rs:record_with_vad_impl` -- 176 lines
- `drain.rs:drain_voice_messages` -- 152 lines
- `home_page.rs:theme_studio_row` -- 127 lines

---

### SYS-6. Duplicated logic patterns (>15 instances identified)

| Pattern | Duplication Count | Estimated Lines Saved |
|---|---|---|
| `send_enhanced_status_with_buttons` 6-arg call | 15+ | ~90 |
| `set_status` 4-arg boilerplate | 20+ | ~100 |
| `is_jetbrains_terminal` | 3 (with divergence) | ~80 |
| `create_vad_engine` | 2 | ~30 |
| RMS dB calculation | 3 | ~25 |
| STT token canonicalization | 2 | ~60 |
| Audio format conversion blocks | 2 | ~50 |
| `StubSession` test helper | 3 | ~45 |
| `normalize_*` functions | 11 | ~70 |
| Runtime override enums | 10 | ~80 |
| `cycle_runtime_*_override` | 10 | ~150 |
| `style_id`/`from_style_id` dual mapping | 108 arms | ~100 |
| **Total estimated** | | **~880 lines** |

---

# PART 7: FEATURE OPPORTUNITIES

### FEAT-1. Rolling latency histogram

The `update_last_latency` function computes RTF but only stores latest value. A small rolling window with percentile computation would give users better insight into typical voice-to-text latency. The `latency_history_ms` Vec exists but is not used for percentile display.

### FEAT-2. `VadEngine::is_healthy()` method

Since `EarshotVad` silently swallows errors as `Uncertain`, a health check method would allow the capture loop to detect and report degraded VAD performance.

### FEAT-3. Resampler quality configuration

Rubato resampler parameters (`sinc_len`, `oversampling_factor`) are hardcoded. A "resampler quality" setting (low/medium/high) would let users on resource-constrained devices trade quality for latency.

### FEAT-4. Theme hot-reload error feedback

When a user edits a `.toml` theme file and introduces a syntax error, there is no visible feedback that the edit was rejected. A transient status message or toast would significantly improve the editing experience.

### FEAT-5. Image capture directory cleanup

`.voiceterm/captures/` grows without bound. A configurable retention policy (keep last N or last 24h) with cleanup on startup would prevent disk bloat.

### FEAT-6. Kitty keyboard protocol support

Modern terminals (kitty, ghostty, WezTerm) use the kitty keyboard protocol. Supporting CSI-u sequences would improve arrow navigation in these terminals.

### FEAT-7. `VoiceDrainContext` simplification

Replace the 25-field manual destructure pattern with a builder or `from_parts` constructor. This would reduce fragility when adding new voice features.

---

# PART 8: POSITIVE OBSERVATIONS

The codebase demonstrates strong engineering discipline in many areas:

1. **Thorough test coverage.** Over 5,000 lines of event loop tests, comprehensive edge case coverage (WouldBlock, BrokenPipe, boundary conditions), and dedicated non-interference regression tests.

2. **Clean test hook architecture.** Thread-local function-pointer hooks with RAII guards prevent test pollution and enable deterministic testing without real subprocess dependencies.

3. **Consistent defensive arithmetic.** `saturating_sub`, `saturating_add`, and `checked` operations used throughout for index/coordinate arithmetic, preventing overflow panics.

4. **Well-designed PTY I/O error handling.** Correct distinction between retryable (`WouldBlock`, `Interrupted`) and fatal errors with proper backpressure management.

5. **Strong security validation.** `config/validation.rs` validates binary paths, canonicalizes filesystem paths, jail-checks against repo root, and rejects shell metacharacters from ffmpeg device names.

6. **Clean module decomposition.** Event loop split into focused modules; IPC layered as protocol/router/session/event_processing; theme system layered as palettes/schema/runtime/studio.

7. **Schema versioning with migration.** V1->V2->V3->V4 style schema migration path with backward compatibility.

8. **`#[must_use]` annotations.** Pure functions consistently annotated, preventing accidental discard of computed values.

9. **RAII-based cleanup.** `StreamPauseGuard`, `RuntimeStylePackOverrideGuard`, thread join timeouts, and Drop implementations show careful attention to resource cleanup.

10. **Production-tested STT error handling.** `VoiceError` enum with stable `.code()` labels for telemetry. Whisper hallucination patterns actively cataloged from real-world STT quirks.

---

## Remediation Priority Matrix

| Priority | Category | Findings | Estimated Impact |
|---|---|---|---|
| **P0** | Security | IF-H-2 (OOM), IF-H-3 (skip-perms), IF-H-4 (prompt injection), UI-H-2 (shell injection) | Data loss, unauthorized execution |
| **P1** | Crash risk | AV-H-2 (unreachable on user input), EV-H-4, UI-H-3, SYS-4 | Process panic, corrupted terminal |
| **P1** | Resource leak | IF-H-1 (auth thread leak), AV-H-7 (UI thread block), IF-H-5 (event loop block) | Orphaned processes, UI stalls |
| **P2** | Memory leak | TH-H-1 (Box::leak accumulation) | Unbounded growth in long sessions |
| **P2** | Data integrity | EV-H-3 (silent data loss), TH-H-2 (poisoned mutex), IF-M-12 (dropped events) | Output corruption, state inconsistency |
| **P3** | Code duplication | SYS-6 (15+ patterns, ~880 lines) | Maintenance burden, drift risk |
| **P3** | Long functions | SYS-5 (20+ functions >50 lines) | Review difficulty, bug hiding |
| **P4** | Naming/comments | TH-M-9, EV-L-5, all "why" comment gaps | Cognitive load |
| **P4** | Dead code | EV-M-13, UI-M-4, TH-L-9, SYS-3 | False coverage, confusion |

---

## Verification Checklist

- [ ] All `unreachable!()` calls audited and replaced where reachable
- [ ] All `std::env::set_var` in tests migrated to safe alternatives
- [ ] `is_jetbrains_terminal()` consolidated to single implementation
- [ ] `send_enhanced_status_with_buttons` extracted to helper
- [ ] `set_status` boilerplate consolidated
- [ ] IPC stdin reader bounded
- [ ] Slash command parsing separated from IPC prompt routing
- [ ] `Box::leak` replaced with dedupe cache or owned strings
- [ ] Auth timeout kills subprocess
- [ ] Long functions decomposed (top 10 offenders)
- [ ] `create_vad_engine` + `canonicalize_hotword_tokens` deduplicated
- [ ] `rms_db` consolidated to single implementation
- [ ] `cargo clippy -- -D warnings` passes
- [ ] `cargo test` passes after all changes
