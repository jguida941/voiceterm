# VoiceTerm Continuous Audit Log

**Started:** 2026-02-24T20:23:00Z
**Method:** Multi-agent parallel swarm with rotating focus areas
**Pattern:** 4 workers per wave + 1 reviewer, continuous until clean
**Repo:** jguida941/voiceterm (branch: develop)
**CI Status:** `devctl check --profile ci` PASS, `--profile quick` PASS

---

## Wave 1: Deep Pattern Search

**Focus:** (1) panic/unsafe paths, (2) silent error discard, (3) resource leaks, (4) concurrency bugs
**Duration:** ~5 minutes wall-clock (4 agents parallel)
**Files scanned:** 256 .rs files

### Wave 1 Summary Table

| Agent | Focus | HIGH | MEDIUM | LOW | NONE | Total |
|---|---|---|---|---|---|---|
| Agent-1 | Panic/unsafe paths | 0 | 4 | 5 | - | 9 |
| Agent-2 | Silent error discard | 27 | 44 | 20 | - | 91 |
| Agent-3 | Resource leaks | 0 | 1 | 6 | - | 7 |
| Agent-4 | Concurrency bugs | 0 | 3 | 8 | 7 | 18 |
| **TOTAL** | | **27** | **52** | **39** | **7** | **125** |

---

### Agent-1: Panic/Unsafe Path Audit

**Result:** Codebase is clean. Zero `todo!()` macros. Zero CRITICAL panic paths.

**MEDIUM (4):**
- `voice.rs:461`, `voice_benchmark.rs:153`, `wake_word.rs:532`, `latency_measurement.rs:571` -- `unreachable!()` for earshot VAD without feature flag. Reachable from config if validation bypassed.

**LOW (5):**
- `transcript/delivery.rs:84` -- defensive `unreachable!` after `front()` check (logically sound)
- `pty_session/counters.rs:207,214` -- loop guard panics (`cfg(test|mutants)` only)
- `ipc/session/loop_control.rs:21` -- IPC loop guard (`cfg(test|mutants)` only)
- `utf8_safe.rs:145` -- debug-only assertion (release gracefully degrades)

**Unsafe:** All 20+ production `unsafe` blocks are in PTY/signal code with SAFETY comments. All audited clean.

---

### Agent-2: Silent Error Discard Audit

**Result:** 91 instances of silently discarded errors across 6 patterns.

**Top 5 HIGH findings:**
1. **F15** `codex/pty_backend/job_flow.rs:27,40,57,128,235` -- `let _ = sender.emit(...)` drops `Canceled`, `FatalError`, `Finished` events on queue overflow. Only `Started` event (line 68) checks the return value.
2. **F01** `voice.rs:196` -- Voice capture result silently lost on channel disconnect
3. **F05-F06** `pty_session/pty.rs:662,670` -- SIGTERM/SIGKILL delivery errors silently swallowed
4. **F07-F11** `ipc/session/claude_job.rs:17-39` -- Entire process termination chain is fire-and-forget
5. **F16** `session_memory.rs:64,92,104,107,109` -- All memory writes silently ignore I/O errors

**String-typed errors (8 locations):**
- `auth.rs` -- `AuthResult = Result<(), String>`
- `claude_job.rs` -- all start functions return `Result<_, String>`
- `dev_command/mod.rs` -- broker methods return `Result<_, String>`
- `voice_macros.rs` -- parser returns `Result<_, String>`
- `rule_profile/eval.rs` -- parser returns `Result<_, String>`

**Full catalog:** 27 HIGH (I/O, IPC, process signals), 44 MEDIUM (UI channels, locks, terminal), 20 LOW (cleanup, env vars)

---

### Agent-3: Resource Leak Audit

**Result:** Codebase demonstrates strong resource management. PTY has 3-layer cleanup defense. Audio uses RAII guards.

**MEDIUM (1):**
- `ipc/router.rs:382` -- Auth flow thread JoinHandle discarded with no cancellation for the login subprocess. If IPC session exits during auth, orphaned thread + child process persist.

**LOW (6):**
- `ipc/session/claude_job.rs:82` -- Reader thread JoinHandles dropped (terminate on child exit)
- `theme/color_value.rs:207` -- `Box::leak` (intentional, ~400 bytes/theme switch)
- `voice.rs:380-385` -- Mutex held during Whisper inference (mitigated by single-job arch)
- `voice.rs:360-365` -- Mutex held during audio capture (mitigated by single-job arch)
- `dev_command/mod.rs:503` -- Temp files leak on abnormal termination only
- `dev_command/mod.rs:489-490` -- Stdout temp file orphaned if stderr File::create fails

---

### Agent-4: Concurrency Bug Audit

**Result:** No data races or deadlocks found. No `static mut`. No lock ordering violations.

**MEDIUM (3):**
- `voice.rs:56-73` -- `VoiceJob::Drop` blocks calling thread up to 200ms with spin-wait
- `wake_word.rs:352-356` -- `WakeWordRuntime::Drop` blocks up to 1000ms
- `ipc/session/claude_job.rs:12-39` -- `terminate_piped_child` final `child.wait()` after SIGKILL has no timeout (potential indefinite block)

**LOW (8):**
- `voice.rs:46-367` -- `AtomicBool::Relaxed` on stop/capture flags (benign on x86, delayed on ARM)
- `wake_word.rs:131-392` -- Same Relaxed ordering on wake word flags
- `logging.rs:98-151` -- Relaxed on log enable flags (safe due to startup ordering)
- `session_guard.rs:405-420` -- Relaxed CAS for cleanup throttle (correct usage)
- `recorder.rs:347-398` -- `try_lock` in audio callback (correct for real-time)
- `logging.rs, lock.rs` -- Mutex poison recovery (conscious resilience tradeoff)
- `io.rs, state.rs, claude_job.rs` -- `thread::sleep` polling loops (acceptable)
- test code `env::set_var` without unsafe (test-only concern)

---

## Wave 1 Cross-Cutting Insights

### New findings not in the static audit (2026-02-24-rust-production-audit.md):

1. **91 silent error discards** -- The static audit identified ~15 of these. Agent-2 found 91 total by exhaustive grep+read across all files. The `job_flow.rs` event emission pattern (F15) is the most critical new finding.

2. **Zero CRITICAL panic paths** -- Better than the static audit suggested. All `unreachable!()` calls are either test-only or behind cfg gates. The 4 earshot VAD instances are the only production concern.

3. **Process termination chain is entirely fire-and-forget** -- `terminate_piped_child` in `claude_job.rs` discards errors from kill, SIGTERM, SIGKILL, and wait. Combined with the auth thread leak (Agent-3 MEDIUM), this is a systemic pattern.

4. **Concurrency is clean** -- No data races, no deadlocks, no `static mut`. The 3 blocking-Drop patterns are the only real concern, and they have timeouts (except the final `child.wait()`).

---

## Wave 2: Reviewer + Code Quality Audit

**Focus:** (Reviewer) validate Wave 1 top 5, (5) naming/consistency, (6) dead code, (7) API contract violations
**Duration:** ~4 minutes wall-clock (4 agents parallel)
**Files scanned:** 256 .rs files

### Wave 2 Summary Table

| Agent | Focus | HIGH | MEDIUM | LOW | FALSE POS | Total |
|---|---|---|---|---|---|---|
| Reviewer | Validate Wave 1 top 5 | 0 | 2 | 2 | 1 | 5 |
| Agent-5 | Naming/consistency | 3 | 13 | 18 | 0 | 34 |
| Agent-6 | Dead code | 3 | 7 | 9 | 3 | 22 |
| Agent-7 | API contract violations | 0 | 5 | 17 | 0 | 22 |
| **TOTAL** | | **6** | **27** | **46** | **4** | **83** |

---

### Reviewer: Wave 1 Spot-Check Validation

**Result:** 3 CONFIRMED, 1 REJECTED (false positive), 1 PARTIALLY CONFIRMED. Severity adjustments applied.

| Finding | Verdict | Adjusted Severity | Notes |
|---|---|---|---|
| F15: Inconsistent emit error handling | **CONFIRMED** | MEDIUM (downgraded from CRITICAL) | Real inconsistency; `let _ =` on terminal events is defensible but add `log_debug` |
| Auth thread leak on timeout | **CONFIRMED** | MEDIUM | Thread + child process can outlive logical job; needs kill/abort mechanism |
| `terminate_piped_child` unbounded wait | **CONFIRMED** | LOW | Requires kernel D-state to manifest; add timed wait for defense-in-depth |
| Earshot `unreachable!` reachable | **REJECTED** | N/A (False Positive) | Upstream `config/validation.rs:144-147` prevents this path; `unreachable!` is correct |
| `Box::leak` no dedup cache | **PARTIALLY CONFIRMED** | LOW/INFORMATIONAL | ~200-400 bytes per infrequent user action; negligible |

---

### Agent-5: Naming & Consistency Audit

**Result:** 34 findings across 6 categories. Codebase is generally disciplined.

**HIGH (3) -- DRY violations:**
- `is_jetbrains_terminal()` triplicated: `main.rs:130`, `writer/render.rs:35`, `banner.rs:197`
- `process_exists()` duplicated: `pty.rs:651`, `session_guard.rs:288`
- `is_leap` / `is_leap_i64` duplicated: `memory/types.rs:484`, `memory/governance.rs:183`

**MEDIUM (13) -- Naming convention deviations:**
- **11 `get_` prefix violations** (Rust convention avoids `get_`): `get_recorder`, `get_transcriber`, `get_scroll_offset`, `get_animation_frame`, `get_processing_spinner`, `get_button_positions`, `get_button_defs`, `get_icons`, `get_by_id`
- **2 misleading side-effect functions**: `set_claude_prompt_suppression` (also resizes PTY + sends UI refresh), `set_status` (also broadcasts via channel + deduplicates)

**LOW (18) -- Bool predicate naming:**
- 18 functions return `bool` without `is_`/`has_`/`can_`/`should_` prefix (e.g., `process_exists`, `waitpid_failed`, `guard_elapsed_exceeded`, `emit_started_event`, `stop_listener`, `apply_hex_buffer`)

**Module naming:** `legacy_tui` vs `legacy_ui` confusion (recommendation: rename to `legacy_app`)

---

### Agent-6: Dead Code Audit

**Result:** 3 HIGH, 7 MEDIUM, 3 false suppressions. Codebase has ~300+ lines of genuinely dead code hidden by `#[allow(dead_code)]`.

**HIGH (3):**
1. **`icons.rs`** -- Entire 158-line module is dead. `mod icons;` declared in `main.rs:29` but zero symbols consumed anywhere. Theme module has parallel constants.
2. **`WriterMessage::Status`** variant -- Pattern-matched in `writer/state.rs:167` but **never constructed** anywhere. Superseded by `EnhancedStatus`.
3. **`theme_studio_v2` feature** -- 5 modules (`capability_matrix`, `component_registry`, `dependency_baseline`, `rule_profile`, `texture_profile`, `widget_pack`) behind a never-enabled feature flag with zero consumers.

**MEDIUM (7):**
- `ClaudeJob.started_at` -- Written but never read in production (unlike `AuthJob.started_at` which IS read)
- `PipelineJsonResult.prompt` and `.codex_output` -- Deserialized but never consumed
- `HistoryEntry.captured_at` -- Written, never read ("retained for future time-based UI")
- `MemoryIngestor::events_rejected()` -- Zero callers
- `StatusBanner.buttons` -- Populated but only read in test code
- `clear_runtime_color_override()` -- Defined, zero callers
- `style_resolver.rs` blanket `#![allow(dead_code)]` hides 3 dead-in-production functions

**FALSE suppressions (should remove `#[allow(dead_code)]`):**
- `AuthJob.started_at` -- IS used in `auth.rs:11`
- `MeterModule::with_bar_count()` -- IS used in `status_line/format.rs:730`
- `BORDER_NONE` -- IS used in 4 files

---

### Agent-7: API Contract Violations

**Result:** 5 MEDIUM, 17 LOW. Several Clippy-enforceable violations. All `From` impls infallible. All `Drop`+`Clone` combinations clean. All `PartialOrd`+`Ord` properly paired.

**MEDIUM (5):**
1. `VoiceMacros::len()` without `is_empty()` -- Clippy `len_without_is_empty`
2. `MemoryIndex::is_empty()` gated behind `#[cfg(test)]` while `len()` is unconditional
3. `RuleEvalContext::Default` sets `backend: String::new()` for semantically required field
4. `rms_db()` missing `#[must_use]` on pure computation
5. `VoiceMacros::len()` missing `#[must_use]` on pure accessor

**LOW (17):**
- 11 types derive `Clone` without `PartialEq` (all trivially comparable: `MeterReading`, `IpcEvent`, `IpcCommand`, `DevModeStats`, `CaptureResult`, `RequestMode`, `CodexJobStats`, `ProgressGlyphProfile`, `IconSet`, `InFlightCommand`, `CompactHudProfile`)
- 5 types use `pub` in binary crate (should be `pub(crate)`: HUD modules, `BannerConfig`, `SessionStats`, `IconSet`)
- 1 `BannerConfig::Default` with magic strings `"codex"`, `"coral"`

**Clean categories (no violations):**
- All error types implement both `Display` + `Error` ✓
- No `Drop` + `Clone` combinations ✓
- All `From` impls infallible ✓
- All `PartialOrd` + `Ord` properly paired ✓

---

## Wave 2 Cross-Cutting Insights

### Severity adjustments from Reviewer:
1. **F15 job_flow.rs event emissions** downgraded CRITICAL → MEDIUM. The `let _ =` pattern on terminal events is defensible in Rust; adding `log_debug` is sufficient.
2. **Earshot `unreachable!` REJECTED** as false positive. Config validation at `validation.rs:144-147` prevents the path. The 4 `unreachable!()` in Wave 1 Agent-1 MEDIUM findings are now reduced to 0 real findings.

### Major new findings:
1. **158 lines of entirely dead code** in `icons.rs` hidden by blanket `#![allow(dead_code)]` -- the worst kind of dead code because it has a parallel live implementation in the theme module.
2. **`WriterMessage::Status` is a ghost variant** -- pattern-matched but never constructed. This is a maintenance trap.
3. **3 false `#[allow(dead_code)]` suppressions** -- code that IS used but annotated as dead, suggesting the annotations were added speculatively.
4. **Naming inconsistencies** are concentrated in the legacy layer (`legacy_tui/state.rs`) and the `get_` prefix pattern (11 instances). The voiceterm binary is cleaner.

### Running totals (Wave 1 + Wave 2):
| Severity | Wave 1 | Wave 2 | Cumulative |
|---|---|---|---|
| HIGH | 27 | 6 | 33 |
| MEDIUM | 52 | 27 | 79 |
| LOW | 39 | 46 | 85 |
| FALSE POS | 0 | 4 | 4 |
| **Total** | **125** | **83** | **201** (net: **197**) |

---
