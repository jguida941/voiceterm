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
