# VoiceTerm Full-Surface Code Quality Audit

**Generated:** 2026-02-24
**Trigger:** Manual full-codebase audit (Rust + devctl tooling)
**Scope:** All Rust source (~71k LOC, 229 files), devctl Python tooling (~35k LOC, 206 files)
**Method:** READ-ONLY review against AGENTS.md Engineering Quality Contract

---

## Scope

Full-surface audit of the VoiceTerm codebase covering:

1. Rust core library modules (`rust/src/`)
2. Rust voiceterm binary modules (`rust/src/bin/voiceterm/`)
3. devctl Python tooling (`dev/scripts/`)
4. Shell scripts and Makefile automation

Focus areas per AGENTS.md Engineering Quality Contract:
- Naming: behavior-oriented, consistent, no unclear abbreviations
- KISS: simple code, simple comments, no over-engineering
- Rust best practices: unwrap/expect discipline, allow rationale, unsafe docs
- Code duplication: extract shared helpers, consolidate parallel logic
- Automation gaps: manual steps that should be scripted

## Required Sources

- `AGENTS.md`
- `dev/DEVELOPMENT.md`
- `dev/ARCHITECTURE.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `rust/Cargo.toml`
- `rust/src/**`
- `dev/scripts/**`

## Standards References

- Rust Book: <https://doc.rust-lang.org/book/>
- Rust Reference: <https://doc.rust-lang.org/reference/>
- Rust API Guidelines: <https://rust-lang.github.io/api-guidelines/>
- Rustonomicon: <https://doc.rust-lang.org/nomicon/>
- Rust std docs: <https://doc.rust-lang.org/std/>
- Clippy lint index: <https://rust-lang.github.io/rust-clippy/master/>

## Guard Summary

| Area | Files Reviewed | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| Rust core library | 60+ | 5 | 18 | 16 | 39 |
| Voiceterm event loop & core | 11 | 5 | 11 | 8 | 24 |
| Voiceterm status line & theme | 22 | 6 | 14 | 15 | 35 |
| Voiceterm voice/memory/writer | 27 | 5 | 10 | 10 | 25 |
| devctl Python tooling | 30+ | 5 | 9 | 7 | 21 |
| **TOTAL** | **150+** | **26** | **62** | **56** | **144** |

---

## Findings

### PART 1: RUST CORE LIBRARY (HIGH)

#### RC-H1. Float equality comparison in FIR filter normalization

`rust/src/audio/resample.rs:310`

`sum != 0.0` is exact float comparison. A near-zero sum from Hamming-windowed sinc
taps could inflate FIR coefficients to extreme magnitudes. Use `sum.abs() > f32::EPSILON`.

#### RC-H2. `Provider::from_str` shadows the `FromStr` trait convention

`rust/src/ipc/protocol.rs:211`

Inherent method `Provider::from_str` returns `Option<Self>`, conflicting with std
`FromStr` (which returns `Result`). This prevents `"codex".parse::<Provider>()`.
Either implement `FromStr` properly or rename to `try_from_name`.

#### RC-H3. `env::set_var` in tests without `unsafe` block (edition 2024 breakage)

`rust/src/devtools/storage.rs:167,171-172`

`env::set_var` / `env::remove_var` are `unsafe` in Rust 1.83+. These calls are
NOT wrapped in `unsafe` blocks (unlike the correctly handled instances in
`telemetry.rs`). Will fail to compile on edition 2024.

#### RC-H4. `event_sink::send_event` silently drops serialization errors

`rust/src/ipc/session/event_sink.rs:11`

If `serde_json::to_string` fails, the IPC event is silently discarded. A frontend
waiting for `job_end` could hang indefinitely. At minimum log the error.

#### RC-H5. Busy-wait polling loop in `wait_child_with_cancel`

`rust/src/codex/cli.rs:81-116`

Uses `try_recv()` + `thread::sleep(50ms)` instead of `recv_timeout()`. Wastes CPU
on long-running operations (up to 60s timeout).

---

### PART 2: VOICETERM EVENT LOOP & CORE (HIGH)

#### VE-H1. `EventLoopState` god-struct with 40+ fields

`rust/src/bin/voiceterm/event_state.rs:36-75`

All mutable runtime state lives in one struct. Forces every handler to take
`&mut EventLoopState`, prevents fine-grained borrowing, and creates 28-field
context structs assembled repeatedly. Group into sub-structs: `PtyInputBuffer`,
`ThemeStudioState`, `RecordingState`, etc.

#### VE-H2. `send_enhanced_status_with_buttons` called 20+ times with identical 6-arg pattern

Multiple files in `event_loop/`

Same six arguments threaded identically at every call site. A helper method on a
borrowed context struct would eliminate all repetition.

#### VE-H3. `set_status` called with same 6-arg pattern repeatedly

`event_loop/input_dispatch.rs` (9+ locations)

Same first four arguments always from the same sources. A context wrapper would
shrink every call to a 2-arg invocation.

#### VE-H4. Giant `match` block in overlay input handler spans 500 lines

`event_loop/input_dispatch/overlay.rs:42-497`

Single match expression with ~40 arms. Per-overlay handler functions with shared
navigation dispatch would be more maintainable.

#### VE-H5. Overlay navigation boilerplate duplicated across every mode

`event_loop/input_dispatch/overlay.rs:91-211`

`HelpToggle`, `SettingsToggle`, `ThemePicker` navigation logic repeated identically
for each overlay mode. Extract shared "try handle common overlay navigation" function.

---

### PART 3: VOICETERM STATUS LINE & THEME (HIGH)

#### VT-H1. `with_color` defined identically in two files

`status_line/buttons.rs:81-87` and `status_line/format.rs:93-99`

Exact duplicate function. Move to shared location (`text.rs` or utility module).

#### VT-H2. `format_pulse_dots` and `minimal_pulse_dots` are near-identical

`status_line/right_panel.rs:111-134` and `right_panel.rs:298-326`

Same normalization, loop, wrapping, and color logic. Only glyph source differs.
`format_pulse_dots` also ignores `GlyphSet` (correctness issue for ASCII users).

#### VT-H3. Button row rendering has large duplicated compact fallback

`status_line/buttons.rs:508-633`

Two nearly identical 40-line loops for normal and compact modes. Extract helper
parameterized by button indices and separator width.

#### VT-H4. `effective_hud_style` is a no-op identity function

`status_line/layout.rs:19-21`

Returns its argument unchanged. Dead placeholder. Remove or implement.

#### VT-H5. `apply_runtime_style_pack_overrides` is 76 lines of mechanical mapping

`theme/style_pack.rs:205-281`

10 repetitions of the same unwrap-convert-assign pattern between parallel
Runtime/Schema enum hierarchies. Implement `From` traits or unify the hierarchies.

#### VT-H6. 11 nearly identical `normalize_*` functions in `style_schema.rs`

`theme/style_schema.rs:355-427`

All follow `match value { Some(Xxx::Theme) | None => None, other => other }`.
Replace with one generic function or macro.

---

### PART 4: VOICETERM VOICE/MEMORY/WRITER (HIGH)

#### VM-H1. `VoiceDrainContext` has 28 fields, immediate full destructure

`voice_control/drain.rs:45-102`

And `TranscriptDeliveryContext` has 27 fields. These god-structs are the primary
voice-pipeline maintenance burden.

#### VM-H2. Module-wide blanket `#![allow(dead_code)]` on entire memory module

`memory/mod.rs:15-22`

Suppresses dead-code warnings across 10 files. Hides real issues. Each
pre-staged item should carry its own `#[allow]` with a specific ticket.

#### VM-H3. Calendar computation duplicated across `types.rs` and `governance.rs`

`memory/types.rs:444-486` and `memory/governance.rs:116-185`

Two independent hand-rolled Gregorian calendar implementations (one `u64`, one
`i64`). Bug fix in one won't reach the other. Consolidate or use `time` crate.

#### VM-H4. Token canonicalization duplicated between `navigation.rs` and `wake_word.rs`

`voice_control/navigation.rs:48-86` and `wake_word.rs:680-707`

Same STT-misrecognition corrections in two places. New aliases must be added twice.
Extract shared `canonicalize_stt_tokens` utility.

#### VM-H5. JSONL append errors silently discarded during ingestion

`memory/ingest.rs:146-148`

`let _ = writer.append(&event)` discards IO errors. Creates silent consistency gap
between in-memory index and durable store. At minimum increment a counter or log.

---

### PART 5: DEVCTL PYTHON TOOLING (HIGH)

#### DT-H1. Silenced bare `except Exception: pass` hides real errors

`devctl/commands/triage.py:221-222`, `status.py:38-39`, `report.py:35-36`

Swallows all exceptions including `PermissionError`, `TypeError`, disk-full. Should
at minimum log a warning.

#### DT-H2. Dead branch: identical `if`/`else` bodies in `_resolve_use_cihub`

`devctl/commands/triage.py:82-88`

Both branches execute identical code. Either dead code or a latent bug.

#### DT-H3. `cmd_str` does not quote arguments containing spaces

`devctl/common.py:19-21`

`" ".join(cmd)` produces misleading output for paths with spaces. Use `shlex.join()`.

#### DT-H4. `subprocess.run` without error handling in `pipe_output`

`devctl/common.py:197-206`

No `try/except` for `OSError`, no timeout. Hung pipe command blocks indefinitely.

#### DT-H5. `update-homebrew.sh` mutates git config without `--local` guard

`dev/scripts/update-homebrew.sh:214-218`

`git config` writes without `--local` can affect unexpected scope. Should be
explicit about config scope.

---

### MEDIUM FINDINGS SUMMARY (62 total)

#### Rust Core Library (18 medium)
- 8x `#[allow(dead_code)]` without rationale (mostly test/mutant infra in `ipc/session.rs` and `event_sink.rs`)
- 4x unwrap/expect in non-test code (`stt.rs:81,104`, `codex/pty_backend.rs:65,101`) with silent fallbacks
- 5x overly complex functions exceeding 100 lines (`recorder.rs`, `session_guard.rs`, `legacy_tui/state.rs`, `output_sanitize.rs`, `session_call.rs`)
- 1x typo: "possibe" in `backend/aider.rs:2`

#### Voiceterm Event Loop (11 medium)
- `flush_pending_output_or_continue` has confusing return semantics (naming)
- `main()` is 446 lines (complexity)
- 180 lines of `#[cfg(test)]` hook infrastructure in production code paths
- 28-field `VoiceDrainContext` assembled every drain call
- `contains_jetbrains_hint` matches "idea" as substring (false positive risk)
- `libc::signal()` instead of `sigaction()` for SIGWINCH (platform-specific behavior)
- 28-field `ButtonActionContext` assembled repeatedly
- `Vec::remove(0)` instead of `VecDeque` for bounded history
- 9 hardcoded magic byte literals without named constants (0x04, 0x05, 0x0d, 0x1b, 0x7f)
- 7 near-identical `render_*_overlay_for_state` functions
- Toast history overlay hardcodes reserved rows to 10

#### Voiceterm Status/Theme (14 medium)
- `#[allow(dead_code)]` on pub field `StatusBanner.buttons`
- 2x naming: `ColorsGlyphs` and `LayoutMotion` don't describe behavior (should be `GlyphProfile` and `IndicatorSet`)
- `format.rs` at 904 lines mixes multiple responsibilities
- Verbose doc comments describe evolution instead of behavior
- `format_status_banner` has nested HUD-style branching (extract per-style functions)
- Blanket `#![allow(dead_code)]` on `component_registry.rs`
- 5x `#[allow(dead_code)]` on feature-gated modules in `theme/mod.rs`
- `#[allow(clippy::too_many_arguments)]` on functions with 10-11 params (use context structs)
- `parse_style_schema` has 100+ lines of repetitive version branching
- `truncate_display` hard-codes `\x1b[0m` reset sequence assumption
- Duplicate heartbeat panel rendering logic

#### Voiceterm Voice/Memory/Writer (10 medium)
- 12x repeated `set_status` calls with identical 7-param signature in `navigation.rs`
- Duplicated pipeline-mapping logic in `message_processing.rs`
- `word_slice_eq` reimplements `==` for slices (delete it)
- 2x `#[allow(dead_code)]` on accessors without ticket reference
- `NonTranscriptDispatchContext` is a negation-name (rename to `VoiceStatusContext`)
- Hand-rolled ISO timestamp formatting (use `time` crate)
- `truncate_text` mixes byte length and char count semantics
- `redact_secrets` uses fragile while-loop string mutation
- Unused `_project_id` parameter without explanation
- 5 different context structs for one drain operation (naming confusion)

#### devctl Tooling (9 medium)
- Massive code duplication across 4 check scripts (`_run_git`, `_validate_ref`, etc. copied 4x)
- Report-emit boilerplate duplicated across 20+ commands
- 19+ separate `_render_md()` functions with same structural pattern
- Fragile `try/except ModuleNotFoundError` import pattern in 10+ files
- `ship_common.py` has incomplete "TOML-like" parser (use `tomllib`)
- No retry logic for network operations in ship/release pipeline
- `autonomy_loop.py` run function is 100+ lines of sequential logic
- `check.py` uses mutable list-in-list counter (inconsistent with `nonlocal` in same function)
- `triage.py` calls `apply_defaults_to_issues` and `build_next_actions` twice (first call wasted)

---

### LOW FINDINGS SUMMARY (56 total)

Key low-severity patterns across all areas:
- Redundant `#[allow]` attributes where underlying issue is already suppressed
- Unnecessary lifetime annotations where elision handles it
- Minor naming improvements (e.g., `init_guard` -> `init_iteration_limit`)
- Dead code in test wrappers and feature-gated modules
- Inconsistent `datetime.now()` timezone handling across Python commands
- Superseded shell scripts (`sync_external_integrations.sh`, `release.sh`)
- `PATH_POLICY_OVERRIDES` hardcoded in source instead of config file
- Hardcoded magic numbers without named constants
- `super::super::` import chains instead of `use` imports

---

## Remediation Actions

### Priority 1: Correctness (fix immediately)

| ID | Action | Files |
|---|---|---|
| RC-H1 | Use epsilon comparison for FIR filter normalization | `audio/resample.rs` |
| RC-H3 | Wrap `env::set_var` in `unsafe` blocks for edition 2024 | `devtools/storage.rs` |
| RC-H4 | Log serialization errors in IPC event sink | `ipc/session/event_sink.rs` |
| DT-H2 | Fix dead branch in `_resolve_use_cihub` | `commands/triage.py` |
| VM-H5 | Log or count JSONL append errors | `memory/ingest.rs` |
| DT-H1 | Replace bare `except Exception: pass` with logging | `triage.py`, `status.py`, `report.py` |

### Priority 2: Structural (reduce maintenance burden)

| ID | Action | Files |
|---|---|---|
| VE-H1 | Break `EventLoopState` into sub-structs | `event_state.rs` |
| VE-H2/H3 | Create status/button context wrappers | `event_loop/` |
| VE-H4/H5 | Extract per-overlay handlers, shared navigation | `input_dispatch/overlay.rs` |
| VM-H1 | Reduce voice drain context struct sizes | `voice_control/drain.rs` |
| VT-H5/H6 | Implement `From` traits, generic normalize | `style_pack.rs`, `style_schema.rs` |

### Priority 3: Deduplication (DRY)

| ID | Action | Files |
|---|---|---|
| VT-H1 | Move `with_color` to shared module | `status_line/` |
| VT-H2 | Unify pulse dots rendering | `right_panel.rs` |
| VM-H3 | Consolidate calendar math | `memory/types.rs`, `memory/governance.rs` |
| VM-H4 | Extract shared STT canonicalization | `navigation.rs`, `wake_word.rs` |
| DT-M1 | Extract shared check-script utilities | `checks/` (4 scripts) |
| DT-M2 | Add `emit_report()` helper | `devctl/commands/` (20+ files) |

### Priority 4: KISS simplification

| ID | Action | Files |
|---|---|---|
| RC-H2 | Implement `FromStr` or rename `from_str` | `ipc/protocol.rs` |
| RC-H5 | Replace busy-wait with `recv_timeout` | `codex/cli.rs` |
| VT-H4 | Remove no-op `effective_hud_style` | `status_line/layout.rs` |
| VM-H2 | Replace blanket `allow` with per-item annotations | `memory/mod.rs` |
| DT-H3 | Use `shlex.join()` in `cmd_str` | `devctl/common.py` |
| DT-M5 | Use `tomllib` for version reading | `ship_common.py` |

### Priority 5: Automation wins

| ID | Action | Impact |
|---|---|---|
| DT-M6 | Add retry wrapper for network ops in ship pipeline | Prevents transient failures from killing releases |
| DT-L3 | Remove/redirect superseded shell scripts | Reduces maintenance surface |
| DT-M4 | Fix `sys.path` once in entrypoint instead of dual-import pattern | Eliminates 10+ `try/except ModuleNotFoundError` |

---

## Positive Observations

1. **Consistent `anyhow::Context` usage** across nearly all fallible operations
2. **Defensive saturating arithmetic** preventing overflow in long-running sessions
3. **Mutex poison recovery** pattern in `lock.rs`
4. **Safety documentation on every `unsafe` block** in production code
5. **Bounded buffers everywhere** preventing unbounded memory growth
6. **Clean trait-based backend abstraction** making new AI CLI backends trivial to add
7. **RAII cleanup guards** guaranteeing resource release on panics
8. **Strong test coverage** across all reviewed modules
9. **Dry-run support** on every destructive devctl command
10. **Audit trail** for integration and release operations

---

## Verification Checklist

- [ ] Fixes implemented for all Priority 1 (correctness) findings.
- [ ] Structural refactoring planned for Priority 2 items (track in MASTER_PLAN).
- [ ] Deduplication items addressed or logged in AUTOMATION_DEBT_REGISTER.
- [ ] `python3 dev/scripts/devctl.py check --profile ai-guard` passes.
- [ ] `python3 dev/scripts/devctl.py check --profile ci` passes.
- [ ] `python3 dev/scripts/checks/check_rust_best_practices.py` passes.
- [ ] `python3 dev/scripts/checks/check_rust_lint_debt.py` passes.
- [ ] `python3 dev/scripts/checks/check_code_shape.py` passes.
- [ ] Task-class bundle and risk-matrix checks pass.
- [ ] Docs and plan entries updated for behavior/process changes.
- [ ] Scaffold closed or regenerated with zero open findings.

---

## Round 2: Follow-Up Audit (post-fix review + new coverage)

**Date:** 2026-02-24 (follow-up pass)

### Fix Verification Summary

All 10 previously identified HIGH-severity fixes were applied correctly:

| Original ID | Fix Status | Notes |
|---|---|---|
| RC-H1 (float equality) | FIXED | `resample.rs` uses proper comparison now. One secondary float equality at line 296 remains (safe for odd taps but undocumented precondition). |
| RC-H2 (Provider::from_str) | FIXED | Proper `FromStr` trait impl + `parse_name` convenience method. Clean, idiomatic. |
| RC-H3 (env::set_var unsafe) | FIXED | Wrapped in `unsafe` with SAFETY comments referencing `with_env_lock`. |
| RC-H4 (event sink drops errors) | FIXED | Now logs via `log_debug` for serialization, write, and flush failures. |
| RC-H5 (busy-wait loop) | FIXED | Replaced with `recv_timeout(50ms)`. SIGTERM-to-SIGKILL escalation is clean. |
| DT-H1 (bare except) | FIXED | All three files now use `except Exception as exc` with stderr warnings. |
| DT-H2 (dead branch) | FIXED | `_resolve_use_cihub` refactored with clean three-outcome flow + extracted `_cihub_supports_triage`. |
| DT-H3 (cmd_str quoting) | FIXED | Now uses `shlex.join()`. Test confirms space-quoting works. |
| DT-H4 (pipe_output) | FIXED | Three-layer defense: which check (code 2), timeout (code 124), OSError (code 127). |
| DT-H5 (git config --local) | FIXED | Both check and set now use `--local` flag explicitly. |

### Round 2: NEW HIGH Findings (5)

#### R2-H1. `progress.rs`:5 -- File-level `#![allow(dead_code)]` suppresses all warnings

Blanket suppression across entire file. Several pub types/functions may be genuinely dead. Each should carry its own `#[allow]` or be removed.

#### R2-H2. `claude_prompt_detect.rs`:159 -- `Vec::remove(0)` in PTY output hot path

O(n) operation on every byte batch. `recent_lines` should be `VecDeque` for O(1) `pop_front`. Same pattern at lines 169-173.

#### R2-H3. `transcript/delivery.rs`:82-83 -- Dead `else` branch after guaranteed `.front()` success

Inner `let Some(next) = pending.pop_front() else { break }` can never fail because `.front()` just succeeded. Dead code.

#### R2-H4. `persistent_config.rs`:202-307 -- 105 lines of repetitive if-let chains

13 nearly identical blocks for applying config fields. Macro or field-visitor pattern would halve the code.

#### R2-H5. `buttons.rs`:49-53 -- `panic!` in `to_input_event` for `CollapseHiddenLauncher`

Even though `#[cfg(test)]`, tests hitting this path crash with no useful diagnostic. Use `unreachable!()` with context or return `Result`.

### Round 2: NEW MEDIUM Findings (13)

| ID | File | Line(s) | Category | Description |
|---|---|---|---|---|
| R2-M1 | `settings/render.rs` | 287-324 | DUPLICATION | `format_slider` and `format_normalized_slider` share 95% identical logic. Extract shared `render_slider_at_ratio`. |
| R2-M2 | `session_memory.rs` + `transcript_history.rs` | 165-180 / 229-244 | DUPLICATION | `take_stream_line` function duplicated verbatim across two files. |
| R2-M3 | `session_memory.rs` + `transcript_history.rs` | 135-149 / 192-206 | DUPLICATION | `push_user_char`/`push_assistant_char` patterns duplicated. Extract shared `StreamLineBuffer`. |
| R2-M4 | `prompt/regex.rs` | 56-127 | DUPLICATION | Full `OverlayConfig` struct constructed manually in every test. Use `make_default_config()` helper. |
| R2-M5 | `config/theme.rs` + `banner.rs` | 100-200 / 366-400 | DUPLICATION | Env var save/restore boilerplate repeated across test functions. Generalize `with_env_vars` helper. |
| R2-M6 | `claude_prompt_detect.rs` | 12-13 | ALLOW | `#[allow(dead_code)]` on `PromptOcclusionDiagnostic` without future-intent comment. |
| R2-M7 | `claude_prompt_detect.rs` | 350-366 | DEAD_CODE | `estimate_command_wrap_depth` called only from dead `capture_diagnostic`. Assess for removal. |
| R2-M8 | `toast.rs` | 263 | DEAD_CODE | `let _ = toast.created_at;` is leftover dead code. Remove. |
| R2-M9 | `hud/mod.rs` | 39-71 | ALLOW | Multiple items (`Mode::label`, `HudRegistry::get/len/is_empty/iter`, `recording_duration_secs`, `backend_name`) carry `#[allow(dead_code)]` with no rationale. |
| R2-M10 | `button_handlers.rs` | 28-52 | COMPLEXITY | `ButtonActionContext` has 22 reference fields. Use sub-context pattern from `SettingsActionContext`. |
| R2-M11 | `prompt/tracker.rs` | 130-139 | BEST_PRACTICE | `matches_prompt` uses `matches \|= ` instead of short-circuit `\|\|`. Simplify to combinator chain. |
| R2-M12 | `persistent_config.rs` | 118-172 | DUPLICATION | `serialize_user_config` is 54 lines of repetitive if-let-push. Use macro. |
| R2-M13 | `settings_handlers.rs` | 314-348 | DUPLICATION | Four `cycle_*` wrapper functions are pure boilerplate. Inline the const arrays at callsites. |

### Round 2: NEW LOW Findings (14)

| ID | File | Description |
|---|---|---|
| R2-L1 | `config/cli.rs` | 5 Display impls follow identical pattern. Consider `strum::Display` derive or macro. |
| R2-L2 | `config/backend.rs:52` | Variable `default_cmd` should be `registry_cmd` (name describes source, not role). |
| R2-L3 | `transcript/idle.rs` | Deeply nested conditional in `transcript_ready`. Extract idle-fallback helper. |
| R2-L4 | `settings/render.rs:97-100` | `read_only` condition is hard to parse. Rewrite as match expression. |
| R2-L5 | `settings/render.rs:340-362` | Nested color-styling logic can be collapsed to `match (selected, read_only)`. |
| R2-L6 | `onboarding.rs:33-46` | Hand-rolled TOML parser for one boolean. Fine for now, document as intentionally minimal. |
| R2-L7 | `persistent_config.rs:54-63` | `parse_toml_value` doesn't handle escaped quotes. Document limitation. |
| R2-L8 | `session_stats.rs:145` + `progress.rs:181` | `format_duration` duplicated across two files. Consolidate. |
| R2-L9 | `banner.rs:44-51` | `centered_padding` name could be `center_left_padding` for clarity. |
| R2-L10 | `transcript_history.rs:155-156` | `#[allow(dead_code)]` on `len()`/`all_newest_first()`. Use `#[cfg(test)]` instead. |
| R2-L11 | `toast.rs:160-187` | `push_with_duration` duplicates eviction/push logic from `push`. Share internal helper. |
| R2-L12 | `hud/mod.rs:21-23` | Local `display_width` wraps `UnicodeWidthStr::width`. Two `display_width` functions exist (hud + overlay_frame). Consolidate. |
| R2-L13 | `claude_prompt_detect.rs:306-340` | Same `contains` pattern repeated 5 times. Extract `any_pattern_matches` helper. |
| R2-L14 | `settings/render.rs:232-281` | Six `*_button` functions all just call `button_label(match_arm)`. Could use Display trait. |

### Round 2: devctl Remaining Issues

| ID | File | Severity | Description |
|---|---|---|---|
| R2-DT1 | `ship_common.py:67-73` | MEDIUM | `read_version()` still uses simplistic line parser. Use `tomllib` (Python 3.11+). |
| R2-DT2 | `test_loop_comment.py` | MEDIUM | Missing tests for all error paths (gh_json error, non-numeric id, mutate error, non-zero rc). |
| R2-DT3 | `test_common.py` | MEDIUM | Missing test for pipe_output "command not found" (which==None) path. |
| R2-DT4 | `common.py:193` | LOW | `write_text()` without explicit `encoding="utf-8"`. |
| R2-DT5 | `common.py:40-41` | LOW | `_run_with_live_output` Popen has no programmatic timeout. |
| R2-DT6 | `triage.py:113` + `check.py:333` | LOW | Naive `datetime.now()` timestamps; inconsistent with UTC usage elsewhere. |
| R2-DT7 | `autonomy_loop.py:72-73` | LOW | Dense chained `or`/`.strip()` expressions. Extract `resolve_env_or_default()` helper. |

### Updated Totals (Round 1 + Round 2)

| Metric | Round 1 | Round 2 New | Round 2 Fixed | Net Open |
|---|---|---|---|---|
| HIGH | 26 | 5 | 10 fixed | 21 |
| MEDIUM | 62 | 13 + 3 devctl | 0 | 78 |
| LOW | 56 | 14 + 3 devctl | 0 | 73 |
| **TOTAL** | **144** | **38** | **10** | **172** |

### Top 5 Impact Opportunities (Round 2)

1. **Extract shared `StreamLineBuffer`** -- Eliminates `take_stream_line` + `push_*_char` duplication across `session_memory.rs` and `transcript_history.rs`
2. **Use `VecDeque` in prompt detector** -- O(1) hot-path improvement for PTY output processing
3. **Macro-ize persistent config** -- Halves `apply_user_config_to_overlay` and `serialize_user_config` (160 lines -> ~80)
4. **Consolidate `ButtonActionContext`** using sub-context pattern -- Reduces 22-field struct to composable pieces
5. **Audit all `#[allow(dead_code)]`** across `progress.rs`, `hud/mod.rs`, `claude_prompt_detect.rs` -- Remove genuinely dead code, `#[cfg(test)]` what's test-only

---

## Round 3: Remediation Pass (implemented)

**Date:** 2026-02-24

### Fixed in this pass

#### Round 2 HIGH

- [x] **R2-H1** `progress.rs` file-level dead-code suppression removed (module no longer compiled in runtime path; dead-code blanket removed).
- [x] **R2-H2** `claude_prompt_detect.rs` switched to `VecDeque` and `pop_front()` for O(1) context eviction.
- [x] **R2-H3** `transcript/delivery.rs` merge loop dead branch removed; front/pop invariant tightened.
- [x] **R2-H4** `persistent_config.rs` repetitive apply chains refactored with shared helpers and enum parsers.
- [x] **R2-H5** `buttons.rs` test-only panic path replaced with `unreachable!` invariant.

#### Round 2 medium/low addressed in same patch

- [x] **R2-M1** `settings/render.rs` slider rendering duplication reduced via shared `render_slider_at_ratio`.
- [x] **R2-M2 / R2-M3** shared `StreamLineBuffer` extracted and wired into `session_memory.rs` + `transcript_history.rs`.
- [x] **R2-M4** `prompt/regex.rs` tests now use a shared default-config helper instead of repeated full config literals.
- [x] **R2-M8** `toast.rs` removed dead `created_at` no-op usage and cleaned struct/constructor surface.
- [x] **R2-M11** `prompt/tracker.rs` `matches_prompt` now uses short-circuit combinators.
- [x] **R2-M12** `persistent_config.rs` serialization deduped with shared TOML emit helpers.
- [x] **R2-M9 / R2-L12** HUD dead-code cleanup completed (`display_width` unified; test-only helpers gated with `#[cfg(test)]`).
- [x] **R2-L10** `transcript_history.rs` test-only helpers gated with `#[cfg(test)]` instead of `#[allow(dead_code)]`.
- [x] **R2-L11** `toast.rs` `push_with_duration` now reuses shared active-toast insertion path.
- [x] **R2-L13** prompt pattern checks consolidated via `context_matches_patterns`.
- [x] **R2-L4 / R2-L5** settings row rendering conditionals simplified via direct match-style logic.
- [x] **R2-L6 / R2-L7** onboarding + persistent-config minimal parser limitations now explicitly documented in code comments.
- [x] **R2-L14** settings button rendering now uses enum `Display` where possible to remove repetitive match wrappers.
- [x] **R2-L2** backend resolver local variable renamed (`default_cmd` -> `registry_cmd`) for clearer intent.

#### Round 2 devctl findings

- [x] **R2-DT1** `ship_common.py` version parsing now TOML-backed (`[package]`/`[project]`) with Python 3.10 fallback parser.
- [x] **R2-DT2** `test_loop_comment.py` error-path coverage added (list failure, non-numeric ID, mutation failure, unexpected payload).
- [x] **R2-DT3** `test_common.py` now covers missing pipe command path (`which == None` -> rc `2`).
- [x] **R2-DT4** `common.py` report writer now uses explicit `encoding="utf-8"`.
- [x] **R2-DT5** `_run_with_live_output` now has explicit timeout control with env override (`VOICETERM_DEVCTL_LIVE_OUTPUT_TIMEOUT_SECONDS`), timeout return code `124`, and regression tests.
- [x] **R2-DT6** `triage.py` and `check.py` timestamps standardized to UTC.
- [x] **R2-DT7** `autonomy_loop.py` extracted `_resolve_env_or_default()` helper to replace dense chained expression.

### Validation run evidence

- `python3 -m unittest dev.scripts.devctl.tests.test_common dev.scripts.devctl.tests.test_loop_comment dev.scripts.devctl.tests.test_ship` -> **PASS**
- `cd rust && cargo test --bin voiceterm` -> **PASS**
- `python3 dev/scripts/devctl.py check --profile ci` -> **PASS**
- `python3 dev/scripts/devctl.py docs-check --strict-tooling` -> **PASS**

### Remaining notable open items from Round 2

- [ ] Remaining Round 2 medium/low structural items not yet addressed in this pass (notably `ButtonActionContext` decomposition and broader cross-module helper consolidation such as banner/config env-test utilities and duration-format helper unification).
