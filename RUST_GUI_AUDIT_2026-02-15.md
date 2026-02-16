# Rust GUI Audit - VoiceTerm

Date: 2026-02-15  
Repo: `codex-voice`  
Scope requested: current Rust GUI (overlay/interlay), whole non-legacy app, test split, code quality + architecture audit, and product improvement ideas.

## Plan Executed

1. Establish measurement scope from latest release (`v1.0.66`) and exclude legacy GUI paths.
2. Compute LOC statistics (app vs tests, overlay-only, module and file concentration).
3. Run quality checks (`cargo test`, `cargo fmt --check`, `cargo clippy -D warnings`).
4. Run full-file static audit across every non-legacy Rust file for complexity/risk signals.
5. Review hotspot files manually and produce concrete refactor/test/product recommendations.
6. Produce a root-level report with full per-file appendix.

## Scope and Exclusions

Excluded old GUI files:

- `src/src/legacy_tui/`
- `src/src/legacy_ui.rs`

Excluded legacy size:

- 5 files
- 1,603 LOC

## LOC Baseline (Latest Release)

Count source: tag `v1.0.66` (`src/Cargo.toml:3` shows `version = "1.0.66"`).

### Core totals

- Non-legacy Rust total: **36,089 LOC** across **124 files**
- Test files (`tests.rs` / `tests/`): **5,771 LOC** across **5 files**
- Inline `#[cfg(test)]` blocks (estimated): **9,410 LOC**
- Total test LOC (estimated): **15,181 LOC** (**42.1%**)
- Non-test app LOC (estimated): **20,908 LOC** (**57.9%**)

### Overlay (`src/src/bin/voiceterm/`)

- Overlay total: **20,032 LOC** across **74 files**
- Overlay inline test LOC (estimated): **7,611 LOC**
- Overlay non-test LOC: **12,421 LOC**

Overlay share:

- 55.5% of non-legacy Rust LOC
- 59.4% of non-test LOC
- 50.1% of all test LOC

## Developer-Centric Stats

### Size distribution (non-legacy)

- `<100 LOC`: 47 files (37.9% of files, 6.0% of LOC)
- `100-249 LOC`: 32 files (25.8% of files, 16.0% of LOC)
- `250-499 LOC`: 29 files (23.4% of files, 28.9% of LOC)
- `500-999 LOC`: 10 files (8.1% of files, 20.8% of LOC)
- `1000+ LOC`: 6 files (4.8% of files, 28.3% of LOC)

### Concentration

- Top 1 file = 2,604 LOC (7.2% of total)
- Top 5 files = 8,936 LOC (24.8%)
- Top 10 files = 13,735 LOC (38.1%)
- Top 20 files = 19,577 LOC (54.2%)

### Largest files (non-legacy)

1. `src/src/bin/voiceterm/event_loop.rs` - 2,604 LOC
2. `src/src/pty_session/tests.rs` - 1,909 LOC
3. `src/src/ipc/tests.rs` - 1,521 LOC
4. `src/src/bin/voiceterm/status_line/buttons.rs` - 1,500 LOC
5. `src/src/bin/voiceterm/status_line/format.rs` - 1,402 LOC
6. `src/src/bin/voiceterm/settings_handlers.rs` - 1,274 LOC

### Release trend (recent tags)

- `v1.0.64` -> `v1.0.66`: +1,118 LOC total non-legacy (+3.2%)
- `v1.0.64` -> `v1.0.66`: +1,118 LOC in overlay (+5.9%)

## Verification and Quality Checks

### Passed

- `cd src && cargo test --workspace --all-features`
  - Unit tests: 449 passed
  - Integration tests: 4 passed
  - Doc tests: 0

### Failed (needs cleanup to keep strict lint gate green)

- `cd src && cargo fmt --all -- --check && cargo clippy --workspace --all-features --all-targets -- -D warnings`
- Clippy errors:
  1. `src/tests/voiceterm_cli.rs:13` (`clippy::option_env_unwrap`)
  2. `src/src/bin/voiceterm/banner.rs:387` (`clippy::assertions_on_constants`)
  3. `src/src/bin/voiceterm/color_mode.rs:223` (`clippy::manual_range_contains`)
  4. `src/src/bin/voiceterm/settings_handlers.rs:409` (`clippy::too_many_arguments`, in test helper)

## Findings (Ordered by Severity)

### Medium

1. Event loop is carrying too many responsibilities in one file and one control flow path.  
   - Evidence: `src/src/bin/voiceterm/event_loop.rs:555` (`run_event_loop`), `src/src/bin/voiceterm/event_loop.rs:267` (`run_periodic_tasks`), and repeated overlay transition blocks around `src/src/bin/voiceterm/event_loop.rs:629`, `src/src/bin/voiceterm/event_loop.rs:929`, `src/src/bin/voiceterm/event_loop.rs:980`, `src/src/bin/voiceterm/event_loop.rs:1130`.
   - Risk: regression risk and higher cognitive load for input/overlay state changes.
   - Recommendation: split into `overlay_state_machine`, `input_dispatch`, and `periodic_tasks` modules with typed transition helpers.

2. Unsafe surface area is concentrated in PTY/STT internals and should remain tightly encapsulated.  
   - Evidence: `src/src/pty_session/pty.rs` (16 non-test `unsafe` usages), `src/src/stt.rs` (7), `src/src/pty_session/io.rs` (3), `src/src/pty_session/osc.rs` (2).
   - Risk: FFI/syscall safety regressions when behavior changes.
   - Recommendation: keep all `unsafe` behind narrow safe wrappers and add explicit invariants/tests around those wrappers.

3. Strict lint profile currently fails, so quality gate is not fully clean.  
   - Evidence: clippy failures listed above.
   - Risk: drift between intended and actual code quality bar.
   - Recommendation: resolve 4 lints and keep `-D warnings` lane green.

### Low

1. Repeated `SettingsActionContext::new(...)` construction creates boilerplate and chance of inconsistent wiring.  
   - Evidence: repeated in `src/src/bin/voiceterm/event_loop.rs:596`, `src/src/bin/voiceterm/event_loop.rs:683`, `src/src/bin/voiceterm/event_loop.rs:784`, `src/src/bin/voiceterm/event_loop.rs:1210`, `src/src/bin/voiceterm/event_loop.rs:1313`, `src/src/bin/voiceterm/event_loop.rs:1344`, etc.
   - Recommendation: add a small builder/factory (`event_loop::settings_ctx(&mut state, &mut timers, deps)`).

2. A couple of production `unwrap()` calls can be removed with no behavior change.  
   - Evidence: `src/src/bin/voiceterm/button_handlers.rs:274`, `src/src/bin/voiceterm/button_handlers.rs:278`.
   - Recommendation: convert to `if let Some(idx)` / early return for clarity and no panic path.

3. A few high-length lines reduce readability in hot modules.  
   - Evidence: longest lines in `src/src/voice.rs` and `src/src/bin/voiceterm/status_line/format.rs`.
   - Recommendation: line-wrap long format/regex constructs and extract constants/builders.

## Organization and Modularization Opportunities

1. Extract overlay transition policy from event loop.  
   - New module idea: `src/src/bin/voiceterm/overlay_transition.rs` for mode enter/exit, resize hooks, and redraw policy.
2. Break `run_periodic_tasks` into independent tasks.  
   - Split into `tick_resize`, `tick_recording`, `tick_processing`, `tick_prompt`, `tick_auto_voice`, `tick_deadlines`.
3. Consolidate settings action dispatch map.  
   - Replace repeated match arms with a table-driven dispatcher from `SettingsItem` -> action enum.
4. Separate test support builders from runtime module files.  
   - Move test-only helpers to `tests/support/*` for clearer production/test boundaries.
5. Consider lifting overlay runtime into a library crate module and keeping `main.rs` as thin composition.

## Testing Improvements

1. Add targeted non-test coverage for high-LOC modules with no inline test markers:
   - `src/src/ipc/session.rs`
   - `src/src/pty_session/pty.rs`
   - `src/src/ipc/router.rs`
   - `src/src/bin/voiceterm/button_handlers.rs`
   - `src/src/audio/resample.rs`
2. Add property/fuzz tests for parser-like logic:
   - prompt parsing (`prompt/*`), ANSI handling (`utf8_safe`, `pty_session/osc`), input parser (`input/parser.rs`).
3. Add regression tests around overlay mode transitions in one matrix test harness:
   - Help <-> Settings <-> ThemePicker transitions
   - resize + mouse + hud-style interactions
4. Keep clippy and formatting lanes mandatory in local pre-push workflow.

## Product and UX Expansion Ideas (Beyond "Overlay + Voice Mode")

### Visual

1. Add a timeline strip for transcript lifecycle (captured -> normalized -> queued -> injected -> sent).
2. Add a compact mini-chart for latency trend with per-phase breakdown (capture/STT/inject) toggle.
3. Add richer theme packs and semantic color modes for accessibility (color-blind-safe palettes).
4. Add transition presets (none/subtle/expressive) with deterministic low-latency defaults.

### Product surface

1. Session replay and searchable command/transcript history panel.
2. Multi-backend orchestration mode (route transcript to selected backend profile).
3. Voice macro recorder/editor UI with project-level and global scopes.
4. Smart action layer: slash-command palette, quick snippets, and context-aware suggestions.
5. Optional plugin hooks for custom HUD modules and post-transcript transforms.

## Suggested Near-Term Roadmap

1. Fix clippy blockers (4 issues) and keep strict lint gate clean.
2. Refactor event-loop transition logic into dedicated modules without behavior changes.
3. Add tests around refactored transition/state-machine paths.
4. Ship one visual upgrade (phase timeline + latency breakdown chip) behind a feature flag.

## Latency Audit Addendum (Requested Follow-up)

### What appears to be happening

- Your observed `~350-450ms` with occasional `500-900ms` is broadly consistent with the current code path and is generally good for local Whisper-style dictation.
- The HUD latency is intentionally post-capture processing latency (primarily STT time when present), not full speak-to-send wall-clock.

### Latency risk areas found in code

1. Voice message draining is tied to the 50ms periodic event-loop tick.  
   - Evidence: `src/src/bin/voiceterm/event_loop.rs:53`, `src/src/bin/voiceterm/event_loop.rs:561`, `src/src/bin/voiceterm/event_loop.rs:441`  
   - Effect: adds up to ~50ms jitter before a completed voice job is reflected in HUD/status.

2. Whisper inference threads are hard-capped at 8.  
   - Evidence: `src/src/stt.rs:117`  
   - Effect: can leave performance on the table on higher-core machines.

3. Default auto-stop silence tail is 1000ms (intentional but latency-heavy).  
   - Evidence: `src/src/config/defaults.rs:11`, `src/src/config/mod.rs:155`, `src/src/config/validation.rs:48`  
   - Effect: in auto-stop flow, this can dominate perceived end-of-speech delay unless manually stopped early.

4. Fallback latency path may look surprisingly small in some runs.  
   - Evidence: `src/src/bin/voiceterm/voice_control/drain.rs:431`  
   - Effect: when STT metrics are absent, `elapsed-capture` fallback can produce values that feel inconsistent with perception.

### Safe no-break fix plan (staged)

1. Stage A: Add richer latency diagnostics first (no behavior change).
   - Keep existing display semantics.
   - Extend audit logs with trigger source and pipeline mode so odd samples are traceable.
   - Gate: existing tests + no UI/behavior regression.

2. Stage B: Reduce scheduler jitter without changing user-visible semantics.
   - Move `drain_voice_messages(...)` to run on each loop iteration (before/after select), not only periodic tick.
   - Keep periodic tasks unchanged otherwise.
   - Risk control: preserve ordering, add deterministic unit test proving faster drain and no duplicate sends.

3. Stage C: Make STT threading tunable while preserving current default.
   - Add optional `--whisper-threads` (or env override).
   - Default remains current behavior (`min(num_cpus, 8)`), so no surprise regressions.
   - Add validation bounds and tests for parsing + propagation.

4. Stage D: Clarify latency semantics in UI/docs.
   - Keep current metric but label explicitly as processing/STT latency.
   - Optionally add a second metric (end-to-send) for users who want wall-clock visibility.
   - Risk control: behind setting or display mode to avoid clutter.

5. Stage E: Optional latency profile tuning (opt-in, not default change).
   - Recommended low-latency profile for power users (e.g., lower silence tail, greedy decode).
   - Keep defaults stable to avoid quality regressions for existing users.

### Regression safety gates required for each stage

1. `python3 dev/scripts/devctl.py check --profile ci`
2. `cd src && cargo test --bin voiceterm latency -- --nocapture`
3. `cd src && cargo test --bin voiceterm update_last_latency -- --nocapture`
4. `cd src && cargo test --bin latency_measurement -- --nocapture`
5. `./dev/scripts/tests/measure_latency.sh --ci-guard --count 3`

### Suggested acceptance criteria

1. No functional regressions in transcript send modes (`auto`/`insert`) and queue behavior.
2. Mean processing latency unchanged or better; p95 jitter reduced after Stage B.
3. No new clippy/fmt regressions.
4. Docs and status-line wording stay aligned with measured semantics.

## Non-Test Module Summary

| Module | Files | Non-test LOC | non-test unsafe | non-test unwrap | non-test expect | non-test panic |
|---|---:|---:|---:|---:|---:|---:|
| `bin/voiceterm` | 74 | 12421 | 1 | 2 | 1 | 0 |
| `ipc` | 4 | 1457 | 1 | 0 | 0 | 0 |
| `codex` | 4 | 1268 | 1 | 0 | 0 | 0 |
| `audio` | 7 | 1186 | 0 | 0 | 0 | 0 |
| `pty_session` | 5 | 1102 | 21 | 0 | 3 | 0 |
| `config` | 3 | 697 | 0 | 0 | 0 | 0 |
| `bin/latency_measurement.rs` | 1 | 665 | 0 | 2 | 0 | 0 |
| `backend` | 7 | 433 | 0 | 0 | 1 | 0 |
| `voice.rs` | 1 | 329 | 0 | 0 | 1 | 0 |
| `doctor.rs` | 1 | 251 | 0 | 0 | 0 | 0 |
| `utf8_safe.rs` | 1 | 221 | 0 | 0 | 0 | 1 |
| `stt.rs` | 1 | 197 | 7 | 0 | 0 | 0 |
| `bin/voice_benchmark.rs` | 1 | 173 | 0 | 0 | 0 | 0 |
| `mic_meter.rs` | 1 | 138 | 0 | 0 | 0 | 0 |
| `terminal_restore.rs` | 1 | 105 | 0 | 0 | 0 | 0 |
| `vad_earshot.rs` | 1 | 63 | 0 | 0 | 0 | 0 |
| `auth.rs` | 1 | 55 | 0 | 0 | 0 | 0 |
| `telemetry.rs` | 1 | 39 | 0 | 0 | 0 | 0 |
| `bin/test_utf8_bug.rs` | 1 | 35 | 0 | 0 | 0 | 0 |
| `bin/test_crash.rs` | 1 | 34 | 0 | 0 | 0 | 0 |
| `lib.rs` | 1 | 26 | 0 | 0 | 0 | 0 |
| `lock.rs` | 1 | 13 | 0 | 0 | 0 | 0 |

## Full File Appendix (Every Non-Legacy Rust File)

Risk scoring here is heuristic for audit prioritization only.

| File | LOC | Non-test LOC (est.) | fns | pub fns | cfg(test) markers | non-test unwrap | non-test expect | non-test panic | non-test unsafe | Risk | Score | Test file | Longest line |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|---:|
| `src/src/audio/capture.rs` | 355 | 337 | 3 | 16 | 2 | 0 | 0 | 0 | 0 | Low | 1 | no | 96 |
| `src/src/audio/dispatch.rs` | 87 | 87 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 87 |
| `src/src/audio/meter.rs` | 86 | 48 | 9 | 4 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 88 |
| `src/src/audio/mod.rs` | 25 | 23 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 87 |
| `src/src/audio/recorder.rs` | 401 | 192 | 9 | 8 | 2 | 0 | 0 | 0 | 0 | Low | 0 | no | 110 |
| `src/src/audio/resample.rs` | 317 | 301 | 0 | 9 | 0 | 0 | 0 | 0 | 0 | Low | 2 | no | 97 |
| `src/src/audio/tests.rs` | 986 | 975 | 80 | 0 | 0 | 2 | 4 | 0 | 0 | Low | 1 | yes | 97 |
| `src/src/audio/vad.rs` | 198 | 198 | 10 | 3 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 92 |
| `src/src/auth.rs` | 55 | 55 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 83 |
| `src/src/backend/aider.rs` | 75 | 55 | 10 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 96 |
| `src/src/backend/claude.rs` | 88 | 55 | 11 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 96 |
| `src/src/backend/codex.rs` | 74 | 54 | 10 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 81 |
| `src/src/backend/custom.rs` | 99 | 68 | 10 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 100 |
| `src/src/backend/gemini.rs` | 74 | 54 | 10 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 95 |
| `src/src/backend/mod.rs` | 136 | 93 | 15 | 5 | 1 | 0 | 1 | 0 | 0 | Low | 1 | no | 89 |
| `src/src/backend/opencode.rs` | 74 | 54 | 10 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 81 |
| `src/src/bin/latency_measurement.rs` | 761 | 665 | 22 | 0 | 1 | 2 | 0 | 0 | 0 | Low | 3 | no | 139 |
| `src/src/bin/test_crash.rs` | 34 | 34 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 91 |
| `src/src/bin/test_utf8_bug.rs` | 35 | 35 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 89 |
| `src/src/bin/voice_benchmark.rs` | 205 | 173 | 9 | 0 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 131 |
| `src/src/bin/voiceterm/arrow_keys.rs` | 168 | 106 | 9 | 3 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 90 |
| `src/src/bin/voiceterm/audio_meter/format.rs` | 262 | 188 | 11 | 4 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 98 |
| `src/src/bin/voiceterm/audio_meter/measure.rs` | 38 | 38 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 88 |
| `src/src/bin/voiceterm/audio_meter/mod.rs` | 115 | 96 | 3 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 93 |
| `src/src/bin/voiceterm/audio_meter/recommend.rs` | 50 | 50 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 111 |
| `src/src/bin/voiceterm/banner.rs` | 482 | 265 | 32 | 5 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 186 |
| `src/src/bin/voiceterm/button_handlers.rs` | 318 | 318 | 2 | 5 | 0 | 2 | 0 | 0 | 0 | Low | 3 | no | 93 |
| `src/src/bin/voiceterm/buttons.rs` | 164 | 126 | 10 | 8 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 89 |
| `src/src/bin/voiceterm/cli_utils.rs` | 62 | 44 | 2 | 3 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 81 |
| `src/src/bin/voiceterm/color_mode.rs` | 710 | 168 | 31 | 6 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 97 |
| `src/src/bin/voiceterm/config/backend.rs` | 240 | 88 | 13 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 86 |
| `src/src/bin/voiceterm/config/cli.rs` | 198 | 198 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 127 |
| `src/src/bin/voiceterm/config/mod.rs` | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 94 |
| `src/src/bin/voiceterm/config/theme.rs` | 201 | 45 | 6 | 3 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 84 |
| `src/src/bin/voiceterm/config/util.rs` | 38 | 38 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 89 |
| `src/src/bin/voiceterm/event_loop.rs` | 2604 | 1681 | 76 | 1 | 15 | 0 | 0 | 0 | 0 | Medium | 4 | no | 123 |
| `src/src/bin/voiceterm/event_state.rs` | 76 | 76 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 84 |
| `src/src/bin/voiceterm/help.rs` | 331 | 227 | 20 | 5 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 100 |
| `src/src/bin/voiceterm/hud/latency_module.rs` | 206 | 96 | 17 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 92 |
| `src/src/bin/voiceterm/hud/meter_module.rs` | 256 | 109 | 21 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 92 |
| `src/src/bin/voiceterm/hud/mod.rs` | 437 | 211 | 32 | 10 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 93 |
| `src/src/bin/voiceterm/hud/mode_module.rs` | 133 | 59 | 12 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 76 |
| `src/src/bin/voiceterm/hud/queue_module.rs` | 148 | 54 | 14 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 72 |
| `src/src/bin/voiceterm/icons.rs` | 157 | 101 | 8 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 109 |
| `src/src/bin/voiceterm/input/event.rs` | 22 | 22 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 77 |
| `src/src/bin/voiceterm/input/mod.rs` | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 77 |
| `src/src/bin/voiceterm/input/mouse.rs` | 170 | 135 | 6 | 8 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 99 |
| `src/src/bin/voiceterm/input/parser.rs` | 472 | 280 | 23 | 3 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 98 |
| `src/src/bin/voiceterm/input/spawn.rs` | 78 | 78 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 84 |
| `src/src/bin/voiceterm/main.rs` | 459 | 432 | 7 | 0 | 1 | 0 | 0 | 0 | 0 | Low | 1 | no | 96 |
| `src/src/bin/voiceterm/overlays.rs` | 135 | 69 | 3 | 3 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 93 |
| `src/src/bin/voiceterm/progress.rs` | 369 | 223 | 27 | 6 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 109 |
| `src/src/bin/voiceterm/prompt/logger.rs` | 220 | 96 | 9 | 3 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 87 |
| `src/src/bin/voiceterm/prompt/mod.rs` | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 80 |
| `src/src/bin/voiceterm/prompt/regex.rs` | 109 | 46 | 2 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 94 |
| `src/src/bin/voiceterm/prompt/strip.rs` | 31 | 31 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 80 |
| `src/src/bin/voiceterm/prompt/tracker.rs` | 374 | 203 | 19 | 10 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 96 |
| `src/src/bin/voiceterm/session_stats.rs` | 289 | 158 | 27 | 8 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 98 |
| `src/src/bin/voiceterm/settings/items.rs` | 74 | 74 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 96 |
| `src/src/bin/voiceterm/settings/mod.rs` | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 84 |
| `src/src/bin/voiceterm/settings/render.rs` | 344 | 304 | 18 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 1 | no | 96 |
| `src/src/bin/voiceterm/settings/state.rs` | 36 | 36 | 4 | 4 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 87 |
| `src/src/bin/voiceterm/settings_handlers.rs` | 1274 | 396 | 20 | 12 | 1 | 0 | 0 | 0 | 0 | Low | 1 | no | 100 |
| `src/src/bin/voiceterm/status_line/animation.rs` | 122 | 81 | 6 | 6 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 115 |
| `src/src/bin/voiceterm/status_line/buttons.rs` | 1500 | 805 | 65 | 5 | 1 | 0 | 0 | 0 | 0 | Low | 2 | no | 104 |
| `src/src/bin/voiceterm/status_line/format.rs` | 1402 | 948 | 65 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 2 | no | 196 |
| `src/src/bin/voiceterm/status_line/layout.rs` | 52 | 32 | 2 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 88 |
| `src/src/bin/voiceterm/status_line/mod.rs` | 25 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 90 |
| `src/src/bin/voiceterm/status_line/state.rs` | 234 | 192 | 11 | 7 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 96 |
| `src/src/bin/voiceterm/status_line/text.rs` | 92 | 66 | 3 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 87 |
| `src/src/bin/voiceterm/status_style.rs` | 253 | 142 | 20 | 9 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 85 |
| `src/src/bin/voiceterm/terminal.rs` | 191 | 97 | 6 | 7 | 1 | 0 | 0 | 0 | 1 | Low | 3 | no | 98 |
| `src/src/bin/voiceterm/theme/borders.rs` | 102 | 102 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 78 |
| `src/src/bin/voiceterm/theme/colors.rs` | 35 | 35 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 85 |
| `src/src/bin/voiceterm/theme/detect.rs` | 9 | 9 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 77 |
| `src/src/bin/voiceterm/theme/mod.rs` | 241 | 150 | 14 | 5 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 89 |
| `src/src/bin/voiceterm/theme/palettes.rs` | 237 | 237 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 88 |
| `src/src/bin/voiceterm/theme_ops.rs` | 230 | 144 | 3 | 6 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 100 |
| `src/src/bin/voiceterm/theme_picker.rs` | 237 | 194 | 11 | 4 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 96 |
| `src/src/bin/voiceterm/transcript/delivery.rs` | 357 | 161 | 8 | 4 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 97 |
| `src/src/bin/voiceterm/transcript/idle.rs` | 62 | 41 | 2 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 89 |
| `src/src/bin/voiceterm/transcript/mod.rs` | 11 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 96 |
| `src/src/bin/voiceterm/transcript/queue.rs` | 65 | 33 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 81 |
| `src/src/bin/voiceterm/transcript/session.rs` | 60 | 23 | 7 | 0 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 92 |
| `src/src/bin/voiceterm/voice_control/drain.rs` | 700 | 494 | 14 | 4 | 1 | 0 | 0 | 0 | 0 | Low | 1 | no | 120 |
| `src/src/bin/voiceterm/voice_control/manager.rs` | 448 | 288 | 11 | 9 | 1 | 0 | 1 | 0 | 0 | Low | 1 | no | 97 |
| `src/src/bin/voiceterm/voice_control/mod.rs` | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 91 |
| `src/src/bin/voiceterm/voice_control/pipeline.rs` | 27 | 15 | 1 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 88 |
| `src/src/bin/voiceterm/voice_macros.rs` | 410 | 295 | 15 | 5 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 98 |
| `src/src/bin/voiceterm/writer/mod.rs` | 135 | 95 | 1 | 3 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 90 |
| `src/src/bin/voiceterm/writer/mouse.rs` | 32 | 32 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 79 |
| `src/src/bin/voiceterm/writer/render.rs` | 443 | 291 | 18 | 6 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 97 |
| `src/src/bin/voiceterm/writer/sanitize.rs` | 33 | 21 | 1 | 2 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 83 |
| `src/src/bin/voiceterm/writer/state.rs` | 378 | 338 | 6 | 3 | 1 | 0 | 0 | 0 | 0 | Low | 1 | no | 101 |
| `src/src/codex/backend.rs` | 384 | 347 | 11 | 17 | 4 | 0 | 0 | 0 | 0 | Low | 1 | no | 103 |
| `src/src/codex/cli.rs` | 208 | 194 | 3 | 6 | 5 | 0 | 0 | 0 | 1 | Low | 3 | no | 99 |
| `src/src/codex/mod.rs` | 28 | 20 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | Low | 0 | no | 114 |
| `src/src/codex/pty_backend.rs` | 818 | 707 | 17 | 28 | 26 | 0 | 0 | 0 | 0 | Low | 2 | no | 142 |
| `src/src/codex/tests.rs` | 622 | 622 | 53 | 0 | 0 | 22 | 15 | 1 | 2 | Low | 1 | yes | 96 |
| `src/src/config/defaults.rs` | 68 | 68 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 102 |
| `src/src/config/mod.rs` | 271 | 269 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 97 |
| `src/src/config/tests.rs` | 733 | 733 | 76 | 0 | 0 | 38 | 4 | 0 | 0 | Low | 1 | yes | 100 |
| `src/src/config/validation.rs` | 378 | 360 | 4 | 7 | 2 | 0 | 0 | 0 | 0 | Low | 1 | no | 115 |
| `src/src/doctor.rs` | 351 | 251 | 19 | 6 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 92 |
| `src/src/ipc/mod.rs` | 24 | 22 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 88 |
| `src/src/ipc/protocol.rs` | 218 | 218 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 81 |
| `src/src/ipc/router.rs` | 370 | 370 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | Low | 2 | no | 156 |
| `src/src/ipc/session.rs` | 960 | 847 | 6 | 20 | 0 | 0 | 0 | 0 | 1 | Medium | 6 | no | 100 |
| `src/src/ipc/tests.rs` | 1521 | 1521 | 75 | 0 | 0 | 46 | 7 | 27 | 3 | Low | 2 | yes | 132 |
| `src/src/lib.rs` | 26 | 26 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 84 |
| `src/src/lock.rs` | 13 | 13 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 94 |
| `src/src/mic_meter.rs` | 164 | 138 | 9 | 1 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 111 |
| `src/src/pty_session/counters.rs` | 280 | 53 | 0 | 35 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 98 |
| `src/src/pty_session/io.rs` | 231 | 189 | 0 | 6 | 0 | 0 | 0 | 0 | 3 | Low | 3 | no | 101 |
| `src/src/pty_session/mod.rs` | 28 | 12 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | Low | 0 | no | 99 |
| `src/src/pty_session/osc.rs` | 364 | 272 | 0 | 10 | 0 | 0 | 0 | 0 | 2 | Low | 3 | no | 99 |
| `src/src/pty_session/pty.rs` | 653 | 576 | 21 | 20 | 0 | 0 | 3 | 0 | 16 | Medium | 6 | no | 107 |
| `src/src/pty_session/tests.rs` | 1909 | 1909 | 134 | 0 | 0 | 63 | 13 | 2 | 106 | Low | 2 | yes | 95 |
| `src/src/stt.rs` | 208 | 197 | 6 | 4 | 1 | 0 | 0 | 0 | 7 | Low | 3 | no | 97 |
| `src/src/telemetry.rs` | 39 | 39 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 83 |
| `src/src/terminal_restore.rs` | 105 | 105 | 9 | 7 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 94 |
| `src/src/utf8_safe.rs` | 292 | 221 | 16 | 9 | 1 | 0 | 0 | 1 | 0 | Low | 1 | no | 92 |
| `src/src/vad_earshot.rs` | 63 | 63 | 4 | 1 | 0 | 0 | 0 | 0 | 0 | Low | 0 | no | 87 |
| `src/src/voice.rs` | 563 | 329 | 23 | 5 | 5 | 0 | 1 | 0 | 0 | Low | 2 | no | 290 |

## Second-Pass Addendum (Additional Opportunities)

This section captures additional opportunities discovered in a second full scan.

### High-impact opportunities

1. Collapse repeated overlay transition code into shared transition helpers/state-machine primitives.  
   Evidence:
   - `src/src/bin/voiceterm/event_loop.rs:632`
   - `src/src/bin/voiceterm/event_loop.rs:651`
   - `src/src/bin/voiceterm/event_loop.rs:663`
   - `src/src/bin/voiceterm/event_loop.rs:932`
   - `src/src/bin/voiceterm/event_loop.rs:982`
   - `src/src/bin/voiceterm/event_loop.rs:1133`
   Opportunity: create `enter_overlay(mode)`, `leave_overlay()`, and `redraw_overlay()` helpers to remove duplicated resize/redraw/button-registry logic.

2. Remove repeated `SettingsActionContext::new(...)` wiring in event loop input handling.  
   Evidence:
   - `src/src/bin/voiceterm/event_loop.rs:596`
   - `src/src/bin/voiceterm/event_loop.rs:683`
   - `src/src/bin/voiceterm/event_loop.rs:784`
   - `src/src/bin/voiceterm/event_loop.rs:1210`
   - `src/src/bin/voiceterm/event_loop.rs:1313`
   - `src/src/bin/voiceterm/event_loop.rs:1344`
   - `src/src/bin/voiceterm/event_loop.rs:1375`
   - `src/src/bin/voiceterm/event_loop.rs:1397`
   Opportunity: add a local builder/factory for settings context (pattern already exists in `ButtonActionContext::settings_context` at `src/src/bin/voiceterm/button_handlers.rs:203`).

3. Replace IPC fixed-sleep loop with event-driven waits and formal auth timeout handling.  
   Evidence:
   - Busy loop sleep: `src/src/ipc/session.rs:639`
   - Auth start timestamp exists but is unused: `src/src/ipc/session.rs:76`, `src/src/ipc/session.rs:80`, `src/src/ipc/session.rs:922`
   Opportunity:
   - switch loop from `try_recv + sleep(5ms)` to `recv_timeout/select` style scheduling.
   - enforce auth timeout using existing `started_at` field and emit recoverable timeout errors.

4. Reduce high-frequency `StatusLineState` cloning pressure in writer pipeline.  
   Evidence:
   - Full state clone per status send: `src/src/bin/voiceterm/writer/mod.rs:85`, `src/src/bin/voiceterm/writer/mod.rs:93`
   - Frequent status emissions in event loop: `src/src/bin/voiceterm/event_loop.rs:365`, `src/src/bin/voiceterm/event_loop.rs:395`, `src/src/bin/voiceterm/event_loop.rs:414`
   Opportunity: use partial update messages, `Arc<StatusLineState>`, or diff-driven message types to reduce allocation/copy churn during meter/spinner updates.

### Medium-impact opportunities

1. Thin `main` into explicit bootstrap stages and move assembly to a runtime builder.  
   Evidence:
   - `main` orchestrates CLI parse, doctor, setup, PTY init, thread spawn, initial render, and shutdown in one function: `src/src/bin/voiceterm/main.rs:146`
   Opportunity: split into `bootstrap_config`, `bootstrap_io`, `bootstrap_runtime`, `run`, and `shutdown` phases.

2. Gate diagnostic binaries behind a dev feature/profile to reduce release surface and CI/clippy noise.  
   Evidence:
   - Explicit release bins in `Cargo.toml`: `src/Cargo.toml:50`, `src/Cargo.toml:54`
   - Diagnostic binaries: `src/src/bin/test_crash.rs:1`, `src/src/bin/test_utf8_bug.rs:1`
   Opportunity: add `required-features = ["dev-tools"]` and keep production/release artifact set minimal.

3. Remove avoidable production unwrap/expect sites still remaining outside tests.  
   Evidence:
   - `src/src/bin/voiceterm/button_handlers.rs:274`
   - `src/src/bin/voiceterm/button_handlers.rs:278`
   - `src/src/backend/mod.rs:80`
   - `src/src/voice.rs:317`
   Opportunity: replace with explicit match paths or `debug_assert` + fallback behavior where invariants are static.

4. Consider more memory-efficient pending-input representation in event loop write path.  
   Evidence:
   - Partial write remainder allocates new `Vec`: `src/src/bin/voiceterm/event_loop.rs:243`
   Opportunity: use shared byte buffer with offset/index instead of allocating remainder slices on each partial write.

5. Latency measurement log parsing currently reads full file into memory for tail scan.  
   Evidence:
   - `src/src/bin/latency_measurement.rs:436`
   Opportunity: stream a bounded tail window directly (ring buffer of last N lines) to reduce memory spikes on large logs.

### Testing and maintainability additions

1. Add explicit tests around critical non-test files that currently have no in-file `#[cfg(test)]` markers and high LOC.  
    Priority targets:
    - `src/src/ipc/session.rs`
    - `src/src/pty_session/pty.rs`
    - `src/src/ipc/router.rs`
    - `src/src/bin/voiceterm/button_handlers.rs`
    - `src/src/audio/resample.rs`

2. Move very large test blocks out of implementation files to improve readability of production code paths.  
    Evidence:
    - `src/src/bin/voiceterm/event_loop.rs` (2,604 LOC total; large internal test section begins at `src/src/bin/voiceterm/event_loop.rs:1753`)
    - `src/src/bin/voiceterm/settings_handlers.rs` (1,274 LOC with large in-file tests)
    Opportunity: shift to `tests/` or sibling `*_tests.rs` modules for large suites.

### Additional product opportunities (beyond first report)

1. Add IPC-side observability and diagnostics stream (queue depth, dropped updates, loop latency, redraw lag) to power adaptive UI and profiling mode.  
    Suggested anchor points:
    - event loop tick and queue handling: `src/src/bin/voiceterm/event_loop.rs:267`, `src/src/bin/voiceterm/event_loop.rs:227`
    - writer redraw pacing: `src/src/bin/voiceterm/writer/state.rs:221`

2. Add “safe mode” startup profile that disables advanced HUD modules/animations and narrows update cadence for fragile terminals.  
    Suggested anchors:
    - meter cadence and JetBrains override: `src/src/bin/voiceterm/main.rs:138`
    - periodic task cadence: `src/src/bin/voiceterm/event_loop.rs:53`

## Pre-Execution Gap Audit (SDLC + Security + Scalability + Rust Best Practices)

This section captures additional gaps that should be closed (or explicitly deferred with rationale) before starting implementation phases.

### Critical gaps (close first)

1. IPC hard-exit path can bypass structured teardown semantics.  
   Evidence:
   - `std::process::exit(0)` in `src/src/ipc/router.rs:178`
   Risk:
   - abrupt process exit can skip intended shutdown orchestration and make teardown behavior harder to reason about.
   Action:
   - replace hard exit with a graceful shutdown signal/path through `run_ipc_loop`.
   - ensure active Codex/Claude/voice work is cancelled and terminal `JobEnd`/`VoiceEnd` events are emitted before exit.
   Acceptance criteria:
   - `/exit` during active provider and active voice sessions leaves no lingering child processes in repeated loop tests.

2. Background thread lifecycle ownership is implicit in overlay startup/shutdown.  
   Evidence:
   - `let _writer_handle = spawn_writer_thread(writer_rx);` at `src/src/bin/voiceterm/main.rs:267`
   - `let _input_handle = spawn_input_thread(input_tx);` at `src/src/bin/voiceterm/main.rs:298`
   Risk:
   - detached thread handles reduce deterministic teardown guarantees and complicate leak triage.
   Action:
   - introduce explicit runtime handle ownership (writer/input) with bounded shutdown + join semantics.
   - add teardown timing/timeout diagnostics.
   Acceptance criteria:
   - shutdown path logs/metrics show thread termination success (or timeout path) in all quit modes.

3. Voice worker cleanup relies on polling/normal-path behavior and has no `Drop` safety net in manager.  
   Evidence:
   - `VoiceManager` defined in `src/src/bin/voiceterm/voice_control/manager.rs:25`
   - no `impl Drop for VoiceManager` in that module
   Risk:
   - active capture worker may outlive intended manager lifecycle on abrupt or uncommon exit paths.
   Action:
   - add explicit manager drop cleanup policy (request stop + bounded join) and tests for quit-while-recording.
   Acceptance criteria:
   - no live voice worker threads/processes after exit from active recording states.

4. Process-group signaling helpers are duplicated across modules.  
   Evidence:
   - `src/src/ipc/session.rs:316`
   - `src/src/pty_session/pty.rs:428`
   - `src/src/codex/cli.rs:177`
   Risk:
   - subtle divergence in signal/reap behavior over time.
   Action:
   - consolidate signaling/reap strategy into a shared utility with one invariants/test suite.
   Acceptance criteria:
   - single canonical helper used by IPC, PTY session drop, and Codex CLI cancel paths.

### High-value SDLC/security gaps

1. Security/supply-chain CI gates are missing as first-class lanes.  
   Evidence:
   - workflows present: `rust_ci.yml`, `voice_mode_guard.yml`, `perf_smoke.yml`, `latency_guard.yml`, `memory_guard.yml`, `mutation-testing.yml`
   - no dedicated dependency/security workflow currently present
   Risk:
   - vulnerable dependency drift or policy regressions can be caught late.
   Action:
   - add a security lane (for example: dependency vulnerability + policy checks) and define fail thresholds.
   Acceptance criteria:
   - PR/CI fails on high-severity dependency issues or policy violations.

2. Threat-model and security posture docs are not explicit enough for operator-facing risk decisions.  
   Evidence:
   - Claude IPC path can add `--dangerously-skip-permissions` (`src/src/ipc/session.rs:384`, `src/src/ipc/session.rs:387`)
   - no matching user-facing guidance found in current guides set for this behavior
   Risk:
   - unclear operator risk understanding for permission-bypass modes.
   Action:
   - add a concise security model section (trust boundaries, local-only assumptions, risky flags, recommended defaults).
   Acceptance criteria:
   - docs include explicit risk notes and recommended safe defaults for permission-sensitive options.

3. Auth lifecycle has a timestamp but no enforced timeout behavior.  
   Evidence:
   - `AuthJob.started_at` in `src/src/ipc/session.rs:76` and `src/src/ipc/session.rs:80`
   - no timeout enforcement in current auth event processing path
   Risk:
   - stalled auth jobs can degrade responsiveness and lifecycle predictability.
   Action:
   - define auth timeout policy and emit recoverable timeout errors with cancellation path.
   Acceptance criteria:
   - stuck auth flows terminate predictably and recover without process restart.

4. IPC loop still uses fixed sleep scheduling.  
   Evidence:
   - `thread::sleep(Duration::from_millis(5));` in `src/src/ipc/session.rs:640`
   Risk:
   - unnecessary CPU wake-ups and latency jitter under mixed loads.
   Action:
   - move to event-driven scheduling (`recv_timeout`/select style) while preserving responsiveness.
   Acceptance criteria:
   - equal-or-better responsiveness with reduced idle CPU activity.

### Rust engineering quality gaps (maintainability/scalability)

1. Event-loop complexity still presents change-risk concentration.  
   Evidence:
   - `src/src/bin/voiceterm/event_loop.rs` remains high-LOC and transition-dense.
   Action:
   - prioritize extraction of overlay transition policy and settings-context builders before feature expansion.
   Acceptance criteria:
   - reduced duplicate transition code paths and lower churn blast radius per change.

2. Define and enforce an explicit unsafe-governance checklist per module with unsafe code.  
    Evidence:
    - non-test unsafe concentration highlighted in this audit (`pty_session`, `stt`, PTY internals)
    Action:
    - require per-unsafe-block invariants + targeted tests + reviewer checklist item.
    Acceptance criteria:
    - each unsafe hotspot has documented invariants and dedicated regression coverage.

3. Property/fuzz coverage is still limited for parser-like boundaries.  
    Evidence:
    - no dedicated fuzz harness directory currently present (`fuzz/` not found)
    - parser and ANSI-heavy modules are critical boundary surfaces
    Action:
    - add targeted property/fuzz tests for input parser, prompt regex handling, and ANSI/OSC processing.
    Acceptance criteria:
    - fuzz/property lane executes regularly and catches malformed-input regressions.

### Required cohesion audit before implementation starts

1. Add a formal traceability table in this file and keep it authoritative.  
    Required columns:
    - `finding_id`
    - `severity`
    - `evidence_path`
    - `fix_owner`
    - `phase`
    - `test_ids`
    - `master_plan_item`
    - `status`
    Rule:
    - any fix merged to code must update this table and linked `dev/active/MASTER_PLAN.md` item in the same change.

### Pre-start gates (must be explicitly satisfied or deferred with reason)

1. Lifecycle teardown regression suite defined for overlay + IPC + active voice + active backend combinations.
2. Security lane definition agreed (dependency/policy checks + thresholds).
3. Threat-model note approved and scheduled for docs update.
4. Traceability table seeded with all critical/high findings above.
5. Ownership assigned for each critical item and linked to active master-plan entries.

### Traceability table (authoritative)

| finding_id | severity | evidence_path | fix_owner | phase | test_ids | master_plan_item | status |
|---|---|---|---|---|---|---|---|
| FX-001 | Critical | `src/src/ipc/router.rs:178` | Core Maintainer | Phase 1 | `ipc::tests::handle_wrapper_exit_requests_graceful_shutdown`; `ipc::tests::handle_send_prompt_allows_exit_during_auth`; `ipc::tests::run_ipc_loop_exits_when_graceful_exit_requested_and_idle` | MP-127 | Done |
| FX-002 | Critical | `src/src/bin/voiceterm/main.rs:267`, `src/src/bin/voiceterm/main.rs:298` | Core Maintainer | Phase 1 | `voiceterm::main` targeted test pass (smoke) | MP-128 | Done |
| FX-003 | Critical | `src/src/bin/voiceterm/voice_control/manager.rs:25` | Core Maintainer | Phase 1 | `voice_control::manager::tests::voice_manager_drop_requests_stop_for_active_job` | MP-129 | Done |
| FX-004 | High | `src/src/ipc/session.rs:316`, `src/src/pty_session/pty.rs:428`, `src/src/codex/cli.rs:177` | Core Maintainer | Phase 1 | `process_signal::tests::signal_helper_missing_pid_is_optional_error`; `codex::tests::send_signal_tracks_failure_on_invalid_pid` | MP-130 | Done |
| FX-005 | High | `.github/workflows/` (current workflow set) | Core Maintainer | Phase 4 | `security_guard.yml` lane + `dev/scripts/check_rustsec_policy.py` threshold gate + `dev/security/rustsec_allowlist.md` | MP-131 | Done |
| FX-006 | High | `src/src/ipc/session.rs:384`, `src/src/ipc/session.rs:387` | Core Maintainer | Phase 4 | `python3 dev/scripts/devctl.py docs-check --user-facing` | MP-132 | Done |
| FX-007 | High | `src/src/ipc/session.rs:76`, `src/src/ipc/session.rs:80` | Core Maintainer | Phase 1 | `ipc::tests::process_auth_events_times_out_stalled_job` | MP-133 | Done |
| FX-008 | High | `src/src/ipc/session.rs:640` | Core Maintainer | Phase 2 | `ipc::tests::run_ipc_loop_respects_max_loops_with_live_channel`; `ipc::tests::run_ipc_loop_processes_commands` | MP-134 | Done |
| FX-009 | Medium | `src/src/bin/voiceterm/event_loop.rs` | Core Maintainer | Phase 3 | `event_loop::tests::run_event_loop_processes_multiple_input_events_before_exit`; `event_loop::tests::run_periodic_tasks_clears_theme_digits_outside_picker_mode`; `event_loop::tests::run_periodic_tasks_sigwinch_no_size_change_skips_resize_messages` | MP-135 | Done |
| FX-010 | Medium | unsafe concentration in `src/src/pty_session/`, `src/src/stt.rs` | Core Maintainer | Phase 3 | `pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group`; `pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group`; `pty_session::tests::pty_overlay_session_set_winsize_updates_and_minimums`; `stt::tests::transcriber_rejects_missing_model`; `stt::tests::transcriber_restores_stderr_after_failed_model_load`; `dev/security/unsafe_governance.md` checklist | MP-136 | Done |
| FX-011 | Medium | parser/ANSI boundary modules + missing `fuzz/` harness | Core Maintainer | Phase 3 | `pty_session::tests::prop_find_csi_sequence_respects_bounds`; `pty_session::tests::prop_find_osc_terminator_respects_bounds`; `pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes`; `.github/workflows/parser_fuzz_guard.yml` | MP-137 | Done |
| FX-012 | High | this audit file + `dev/active/MASTER_PLAN.md` sync protocol | Core Maintainer | Phase 4 | `dev/scripts/check_audit_traceability.py`; `.github/workflows/audit_traceability_guard.yml`; `make traceability-audit` | MP-138 | Done |

### Execution progress (Phase 2B completed)

- MP-127 (FX-001) completed:
  - replaced hard IPC `/exit` process termination path with graceful-exit signaling and loop-exit conditions.
  - allowed `/exit` wrapper handling even while auth job is active.
  - added IPC regression tests:
    - `ipc::tests::handle_wrapper_exit_requests_graceful_shutdown`
    - `ipc::tests::handle_send_prompt_allows_exit_during_auth`
    - `ipc::tests::run_ipc_loop_exits_when_graceful_exit_requested_and_idle`
- MP-128 (FX-002) completed:
  - added explicit writer/input thread ownership in overlay main runtime.
  - added bounded shutdown/join diagnostics to avoid silent teardown ambiguity.
- MP-129 (FX-003) completed:
  - added `Drop` lifecycle guard for `VoiceManager` to request stop and perform bounded worker join.
  - added regression test:
    - `voice_control::manager::tests::voice_manager_drop_requests_stop_for_active_job`
- MP-130 (FX-004) completed:
  - added shared `process_signal::signal_process_group_or_pid(...)` helper with explicit `missing_is_ok` policy.
  - removed duplicated per-module signal helpers and routed IPC/PTY/Codex callers through the shared helper.
  - added shared invariants test coverage:
    - `process_signal::tests::signal_helper_missing_pid_is_optional_error`
- MP-133 (FX-007) completed:
  - enforced bounded auth lifecycle timeout and explicit timeout `AuthEnd` emission path.
  - added regression test:
    - `ipc::tests::process_auth_events_times_out_stalled_job`
- MP-134 (FX-008) completed:
  - replaced IPC command polling + fixed post-loop sleep with `recv_timeout` wait strategy.
  - retained bounded wake cadence while reducing idle busy-spin risk.
- MP-131 (FX-005) completed:
  - added `Security Guard` CI lane (`.github/workflows/security_guard.yml`) for supply-chain policy enforcement.
  - added `dev/scripts/check_rustsec_policy.py` to gate high/critical RustSec advisories and failing warning kinds (`yanked`, `unsound`).
  - added `dev/security/rustsec_allowlist.md` for explicit, temporary transitive advisory exceptions.
- MP-132 (FX-006) completed:
  - documented threat model/trust boundaries in `.github/SECURITY.md`.
  - documented `--claude-skip-permissions` risk posture and operational guidance in `guides/CLI_FLAGS.md` and `guides/TROUBLESHOOTING.md`.
- MP-135 (FX-009) completed:
  - decomposed high-churn overlay event-loop wiring into shared helpers in `src/src/bin/voiceterm/event_loop.rs`:
    - centralized settings/button action context construction (`settings_action_context`, `button_action_context`).
    - centralized overlay transition/render routines (`sync_overlay_winsize`, overlay render helpers, theme-picker reset helpers).
    - replaced repeated button-registry refresh blocks with a single `refresh_button_registry_if_mouse` path.
  - retained existing behavior while reducing callsite duplication and transition blast radius in the main event loop.
- MP-136 (FX-010) completed:
  - added explicit unsafe-governance checklist at `dev/security/unsafe_governance.md` with required review gates and per-hotspot invariants.
  - mapped PTY lifecycle unsafe boundaries (`spawn_pty_child`, `child_exec`, `set_nonblocking`, teardown/reaping, winsize ioctls) to concrete regression-test expectations.
  - added `stt::tests::transcriber_restores_stderr_after_failed_model_load` to verify stderr fd restoration invariants around `dup`/`dup2` error paths.
  - wired governance references into `AGENTS.md` and `dev/DEVELOPMENT.md` so unsafe-focused changes have explicit local verification commands.
- MP-137 (FX-011) completed:
  - added property-fuzz parser boundary tests in `src/src/pty_session/tests.rs` for ANSI/OSC parsing helpers:
    - `prop_find_csi_sequence_respects_bounds`
    - `prop_find_osc_terminator_respects_bounds`
    - `prop_split_incomplete_escape_preserves_original_bytes`
  - added dedicated CI lane `.github/workflows/parser_fuzz_guard.yml` to run parser property-fuzz regressions on push/PR and scheduled cadence.
  - added local Makefile parity target `make parser-fuzz`.
- MP-138 (FX-012) completed:
  - added `dev/scripts/check_audit_traceability.py` to validate hardening mapping consistency across `dev/active/MASTER_PLAN.md` and this audit traceability table.
  - added dedicated CI lane `.github/workflows/audit_traceability_guard.yml` so traceability mismatches fail in PR/push workflows.
  - added local parity target `make traceability-audit` and documented usage in `dev/scripts/README.md` / `dev/DEVELOPMENT.md`.

Verification runs recorded:

- `python3 dev/scripts/devctl.py check --profile ci` (pass)
- `python3 dev/scripts/devctl.py check --profile prepush` (pass)
- `python3 dev/scripts/devctl.py check --profile release` (pass)
- `python3 dev/scripts/devctl.py docs-check --user-facing` (pass)
- `python3 dev/scripts/devctl.py docs-check --user-facing --strict` (pass)
- `markdownlint -c .markdownlint.yaml README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md` (pass)
- `make security-audit` (pass; RustSec policy script + allowlist path validated)
- `make parser-fuzz` (pass; parser boundary property-fuzz regressions)
- `make traceability-audit` (pass; plan/audit sync guard)
- `python3 dev/scripts/devctl.py hygiene` (pass; known `__pycache__` warning only)
- targeted regression tests above (pass)
