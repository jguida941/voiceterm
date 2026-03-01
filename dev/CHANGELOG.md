# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented here, following the SDLC policy defined in `AGENTS.md`.
Note: Some historical entries reference internal documents that are not published in this repository.

## [Unreleased]

### Runtime Hardening

- Reuse native Whisper inference state across voice captures to avoid per-transcription state allocation overhead in the STT path.
- Reduce the default `--voice-lookback-ms` from `500` to `200` so less trailing silence is sent to Whisper by default.

### Documentation

- Add a dedicated Dev Mode guide (`guides/DEV_MODE.md`) with command-by-command
  Dev panel behavior (`status`, `report`, `triage`, `loop-packet`, `security`,
  `sync`), panel field explanations (`Active`, `Last`), and troubleshooting for
  `json-error` output and packet-text staging behavior.
- Link the new Dev Mode guide from core user entry points (`README`,
  `QUICK_START`, `guides/README`, `guides/USAGE`, `guides/CLI_FLAGS`,
  `guides/INSTALL`, `guides/TROUBLESHOOTING`, and `DEV_INDEX`).

## [1.0.97] - 2026-03-01
### UX

- Harden JetBrains + Claude HUD behavior by using JediTerm-safe cursor save/restore handling, avoiding JetBrains scroll-region writes, and keeping redraw cursor visibility untouched during status rendering.
- Improve JetBrains HUD stability under heavy backend output with row-width clamping for single-row banner updates and safer pre-clear handling for Claude output chunks that start with absolute cursor positioning.
- Keep JetBrains + Claude prompt/HUD separation more stable at startup by reserving one extra Claude gap row in JetBrains terminals.

## [1.0.96] - 2026-03-01
### UX

- Keep the active Codex/Claude input row visible during long summaries/tool turns by fencing PTY scrolling above active HUD rows (writer now sets/restores terminal scroll region with HUD lifecycle).
- Improve Claude approval-card prompt safety in non-rolling terminals by hardening explicit + numbered approval hint handling and keeping suppression anchored to live approval windows.
- Fix Cursor/Claude grow-resize redraw timing so HUD repaint is not deferred behind recent-typing hold windows.

### Runtime Hardening

- Start PTY sessions with HUD-aware initial winsize (terminal rows minus reserved HUD rows) so backend UIs do not briefly start at full-height and overlap bottom HUD space.
- Expand PTY spawn API to accept initial rows/cols explicitly (`PtyCliSession::new` / `PtyOverlaySession::new`) and update all call sites/tests for deterministic startup geometry.

### Documentation

- Update README/Usage/Troubleshooting/Architecture guidance for the current prompt-safety policy (approval-focused suppression), scroll-region HUD isolation, and resize redraw behavior.
- Document HUD compatibility overrides and diagnostics in CLI env docs (`VOICETERM_CLAUDE_EXTRA_GAP_ROWS`, `VOICETERM_HUD_SAFETY_GAP_ROWS`, `VOICETERM_DEBUG_CLAUDE_HUD`).

## [1.0.95] - 2026-02-27
### UX

- Fix overlay arrow-navigation dropouts after terminal keyboard-enhancement mode shifts by accepting colon-parameterized CSI arrow sequences (for example `CSI 1;1:3A`) in shared arrow parsing.
- Narrow prompt-occlusion suppression to high-confidence interactive approvals/permissions only (single-command approvals, worktree/sandbox permission prompts, multi-tool approval summaries) so normal Codex composer/working text no longer causes VoiceTerm HUD disappear/reappear flicker.
- Improve wake-word pickup setup by aligning wake VAD to the active mic sensitivity baseline (with wake headroom), relaxing short wake-capture bounds, and expanding `claude` alias matching (`claud`, `clawed`) so wake phrases are easier to trigger without shouting.

### Code Quality

- Keep `maintainer-lint` green on current Rust toolchains by removing redundant
  clippy patterns in voice capture and dev-panel snapshot paths. No runtime
  behavior change.

## [1.0.94] - 2026-02-25
### Control Plane

- Add an optional PySide6 desktop command-center scaffold under `app/pyside6/` with modular tabbed surfaces (`Quick Ops`, `Catalog`, `GitHub Runs`, `Git`, `Terminal`), non-blocking command execution (`QProcess`), and a broad command catalog that reuses existing `devctl`/governance/git/cargo/workflow command paths.

### Runtime Hardening

- Harden terminal resize signal registration by switching to `sigaction` (`SA_RESTART`) for `SIGWINCH`, reducing non-portable `signal()` behavior in long-running sessions.
- Replace a Theme Studio non-home render `unreachable!()` with a safe fallback line so unexpected page-state mismatches no longer panic.
- Add explicit diagnostics when PTY output queueing hits an unexpected writer-message variant instead of silently discarding that branch.

### Theme Studio Upgrade

- Add multi-page tabbed Theme Studio with 6 pages (Home, Colors, Borders, Components, Preview, Export) navigated via Tab/Shift+Tab.
- Add Colors page with inline RGB color picker (R/G/B sliders, hex entry mode) for editing all 10 semantic color fields. Color changes apply live to the active theme via runtime color override.
- Add indicator set and glyph set selectors to Colors page with Left/Right cycling and live symbol preview.
- Add Borders page with 5 border style options (Single, Rounded, Double, Heavy, None) and live mini-box previews. Enter applies the selected border style.
- Add Components page as a browsable catalog of 54 component IDs organized into 10 groups (HUD, Buttons, Toast, Overlay, Theme Studio, Voice Scene, Transcript, Banner, Progress, Settings) with color swatches and semantic-color hint labels.
- Add Preview page showing read-only live preview of HUD status line colors, indicators, toast severity colors, and border chrome.
- Add Export page with TOML file export to `~/.config/voiceterm/themes/`, OSC 52 clipboard copy, and import stub.
- Introduce `Rgb`, `ColorValue`, and `ResolvedThemeColors` types (`color_value.rs`) enabling runtime color editing while preserving the `&'static str` rendering pipeline via `Box::leak` string interning.
- Add TOML theme file support (`theme_file.rs`, `theme_dir.rs`) with three-tier token system (palette, semantic colors, component overrides), base_theme inheritance, validation, and round-trip export/import.
- Add per-component style resolver (`style_resolver.rs`) mapping 54 ComponentIds to semantic default colors with optional per-component/state overrides.
- Add runtime color override system (`set_runtime_color_override`) as highest-precedence layer in `resolve_theme_colors()`.
- Add `--theme-file <PATH>` CLI flag and `VOICETERM_THEME_FILE` env var for loading TOML theme files.
- Add theme file hot-reload via mtime polling + FNV-1a content hashing (~500ms cycle).
- Add tab bar renderer (`format_tab_bar`) for multi-page Studio navigation.

### Documentation

- Refresh screenshot placement in `README.md` and `guides/USAGE.md` to include the new shortcuts overlay, notification-history overlay, wake-word flow, and hidden-HUD-recording visuals.

## [1.0.93] - 2026-02-24
### UX

- Restore single-accent startup ASCII splash rendering so wide-terminal startup no longer rotates rainbow logo lines and instead tracks the active theme family (for example Tokyo Night purple border accents).
- Preserve Cursor terminal mouse-wheel scrolling while leaving mouse mode ON (`Mouse: ON - scroll preserved in Cursor`) by keeping Cursor on scroll-safe mouse handling, while leaving JetBrains/other terminal mouse behavior unchanged.
- Reduce Cursor typing-time HUD flash by limiting writer-side HUD pre-clear behavior to JetBrains terminals, while keeping scroll-ghost protection for JetBrains redraw paths.

### Runtime Hardening

- Type `VoiceJobMessage::Error` payloads with `VoiceError` variants and bounded drop-time worker join behavior so voice thread lifecycle and downstream error handling are deterministic.
- Harden Whisper model-load stderr suppression with an RAII restore guard so stderr is restored on every exit path.
- Parse custom backend commands with `shell_words` (quoted-arg aware) plus fallback behavior for malformed shell syntax.
- Remove orphaned `rust/src/bin/voiceterm/progress.rs` (no longer compiled) to avoid stale, out-of-sync progress helpers drifting from active runtime code paths.

### Packaging

- Fix PyPI launcher bootstrap Cargo-manifest detection to support both `rust/` (current workspace layout) and legacy `src/` repositories.

## [1.0.92] - 2026-02-24
### Persistence

- Wire `MemoryIngestor` into the runtime: initialize from `main.rs` with project-scoped JSONL persistence, cross-session recovery via `recover_from_jsonl()`, and triple-write ingestion (voice transcripts, PTY input, PTY output) mirroring the existing `TranscriptHistory` + `SessionMemoryLogger` pattern. Add devctl metric appenders (`status`, `report`, `triage`) and failure knowledge-base writer to `~/.voiceterm/dev/`. (MP-230, MP-232, MP-241)

### UX

- Expand the guarded `--dev` panel into a `Dev Tools` command surface that can run allowlisted `devctl` actions (`status`, `report`, `triage`, `security`, `sync`) asynchronously with in-panel status and completion summaries. Mutating `sync` runs require explicit confirmation.
- Keep `Ctrl+R` dedicated to voice capture and add `Ctrl+X` for one-shot image prompts; `--image-mode` now acts as persistent HUD `[rec]` image mode, and default macOS image capture now uses `screencapture` (screenshot-first).

### Runtime Hardening

- Harden dev/runtime safety boundaries: UTF-8-safe preview truncation for IPC logs, char-safe transcript/input truncation limits, multi-occurrence secret redaction, non-deterministic event/session ID suffixing, and saturating float-to-`i16` audio conversion in VAD paths.

### Tooling

- Add `check_rust_audit_patterns.py` and wire it into `devctl check --profile ai-guard` plus security/release CI lanes so known audit regression patterns are blocked automatically.
- Rename the repository Rust workspace root from `src/` to `rust/` and migrate path contracts across scripts, guard checks, CI workflows, and developer docs.
- Add `devctl autonomy-loop` plus `.github/workflows/autonomy_controller.yml` for bounded controller orchestration (round/hour/task caps), run-scoped checkpoint packet + queue artifacts, phone-ready `latest.json`/`latest.md` status snapshots (terminal trace + draft + run context), and optional PR promote flow guarded by remote branch existence checks.

### Code Quality

- Extract `dev_command` test module into `dev_command/tests.rs` to bring the file under the code-shape soft limit and eliminate `unwrap`/`expect` growth in test helpers.
- Migrate YAML macro parsing to `serde_norway` and remove unsound `serde_yml`/`libyml` usage flagged by RustSec.

## [1.0.91] - 2026-02-23

### UX

- Add Gemini-specific HUD compaction so `--gemini` sessions keep a single-row HUD when `Full` style is selected, reducing textbox crowding and redraw flicker while preserving existing Full HUD behavior for other backends.
- Expand prompt-occlusion guardrails for Codex and Claude reply/composer prompts (including Unicode prompt markers and Codex command-composer hints) so HUD rows are suppressed sooner when the interactive reply area is active.
- Keep reply/composer prompt suppression active while typing (clear on submit/cancel) so the HUD does not re-occlude the active Claude/Codex input row mid-reply.
- Add `Image mode` runtime toggle for picture-assisted prompts: when enabled, `Ctrl+R`/HUD `[rec]` captures an image, saves it to `.voiceterm/captures/`, shows an `IMG` HUD badge, and injects a Codex prompt line using the saved image path.
- Add a guarded developer launch mode (`--dev`, alias `--dev-mode` / `-D`) that keeps default runtime behavior unchanged when absent and shows a `DEV` HUD badge when active.
- Add guarded dev-event logging controls (`--dev-log`, `--dev-path`) that require `--dev` and persist per-session JSONL event files under the configured dev data root.
- Add a guarded `Ctrl+D` Dev panel overlay (`--dev` only) that surfaces in-session dev counters (transcript/empty/error counts, words, latency, and ring-buffer size) plus logging-root visibility without changing non-dev behavior.
- Expand Theme Studio runtime controls with `Toast position`, `Startup splash`, `Toast severity`, and `Banner style`, and wire these rows into undo/redo/rollback history so the added style-pack fields are live-editable from the overlay.
- Refresh Theme Studio row rendering to settings-style `label + [ value ]` controls with selected-row highlighting, a dedicated `tip:` description row, wider panel width (`60..=82`), and explicit left/right adjustment hints in the footer so row text no longer truncates into the frame border.
- Route style-pack component border overrides through runtime rendering: `components.overlay_border` now drives overlay frame borders (help/settings/theme-picker/theme-studio/toast plus themed CLI help output), and `components.hud_border` now drives Full-HUD borders when HUD border mode is `Theme`.
- Route startup banner separators and explicit spinner animations through glyph-profile fallback rules so `Glyph profile: ASCII` keeps startup separators and spinner frames ASCII-safe.
- Improve Full/Minimal HUD controls-row readability by tinting button brackets to each button's active theme color and adding stronger focused-bracket contrast in arrow-key focus mode.
- Route transcript-history overlay borders through the style-pack overlay border resolver so `components.overlay_border` now applies consistently across help/settings/theme-picker/theme-studio/toast/history overlays.
- Add a small manual/PTT capture grace window by applying a manual-only `+400 ms` silence-tail adjustment (clamped to max capture) so brief hesitation before speaking is less likely to auto-stop recording too early.
- Keep the shortcuts-row latency badge stable in auto mode by preserving the latest successful latency sample across auto-capture `Empty` cycles and allowing the badge to remain visible while auto capture is actively recording/processing.
- Expand wake/send command parsing for common Whisper mishears: backend-addressed submit phrases now accept variants like `code x send`, `hate codex`, `pay clog`, and `hate cloud`/`okay cloud`, wake submit tails now include `send it`/`sending`/`sand`, and explicit voice `send` submits in `auto` mode so false `Nothing to send` statuses are reduced when text is visibly staged in the backend composer.
- Add wake transcript decision diagnostics in debug logs (`voiceterm --logs --log-content`) so field triage can see raw/normalized/canonical wake parsing when submit phrases are intermittently missed.

### Documentation

- Rewrite user-facing doc intros in plain language and lead with the hands-free flow (`--auto-voice --wake-word --voice-send-mode insert`) so wake mode and voice submit are immediately visible in `README.md`, `QUICK_START.md`, and guide entry points.
- Add an explicit wake + voice send walkthrough (Alexa-style flow) with step-by-step examples and one-shot phrases (`hey codex send`, `hey claude send`) in user docs.
- Make wake + voice send docs GUI-first (Settings + shortcuts) and keep CLI flags as optional startup shortcuts.
- Fix README badge rendering so `Whisper` and `license` chips no longer clip text in GitHub page rendering.
- Document image-mode controls/flags (`--image-mode`, `--image-capture-command`, `VOICETERM_IMAGE_CAPTURE_COMMAND`) in `USAGE`, `CLI_FLAGS`, and `QUICK_START`.
- Document guarded dev-event logging flags (`--dev-log`, `--dev-path`) and JSONL log location behavior in `USAGE`, `CLI_FLAGS`, `README`, and `QUICK_START`.
- Fix README license badge rendering by switching to a stable static `license | MIT` shield so the label segment remains readable.

## [1.0.90] - 2026-02-23

### UX

- Improve wake-word trigger reliability after first activation by allowing wake detections even when auto-voice idle re-arm is paused by user action.
- Broaden actionable wake phrase matching when the wake phrase leads the transcript so natural command-style phrases (for example `hey codex ...`) are less likely to be missed.
- Add built-in voice submit intents (`send`, `send message`, `submit`) that submit staged `insert`-mode text without keyboard input, including one-shot wake tails (`hey codex send` / `hey claude send`).
- In `insert` mode, make `Ctrl+E` strictly finalize-only: it now requests early finalize while recording, never sends Enter, and shows explicit idle guidance (`Text staged; press Enter to send` / `Nothing to finalize`).

### Runtime Hardening

- Add wake-listener no-audio retry backoff to reduce rapid microphone open/close churn during transient no-sample capture failures.

## [1.0.89] - 2026-02-23

### UX

- Improve wake-word alias matching for common Whisper token splits so wake phrases still trigger when transcripts come through as `code x` or `voice term`.
- Fix wake-trigger capture origin labeling so logs/status now report `wake-word` instead of `manual` when wake detection starts recording.
- Make the Full HUD `Wake: ON` badge steady (remove pulse redraw) so wake state no longer appears to flicker on/off.
- Reduce wake-listener microphone stream churn by extending wake detection capture windows, which lowers frequent mic indicator flapping on macOS.

### Documentation

- Update wake-word troubleshooting guidance with expanded accepted phrase variants (`code x`, `voice term`) for faster field debugging.

## [1.0.88] - 2026-02-22

### UX

- Fix `Ctrl+N` toast-history overlay rendering so border columns stay aligned across theme glyph modes and long notification lists.
- Fix toast-history overlay line endings/width accounting so every rendered row keeps exact panel width without stray right-edge artifacts.
- Harden overlay mouse hit-gates so non-close footer clicks and Theme Studio border clicks do not trigger unintended selection actions.
- Add Theme Studio edit-safety controls for runtime style-pack overrides: `Undo edit`, `Redo edit`, and `Rollback edits` rows with bounded history so live visual override changes can be reverted without restarting.
- Normalize `--input-device` values during config validation by collapsing wrapped whitespace/newlines and rejecting empty normalized values, so pasted multi-line device names no longer fail wake/manual capture setup.
- Fix wake-word runtime health signaling: when wake listener startup fails, HUD now shows `Wake: ERR` (instead of `Wake: ON`) and surfaces `Wake listener unavailable (log: ...)`, preventing false-ready wake indicators.
- Reduce wake-trigger capture handoff races by pausing wake-listener capture immediately after a wake detection event is queued, so manual capture startup can claim the microphone without overlap.

### Code Quality

- Add targeted regression coverage for `auth.rs` login-command validation/status handling and `lock.rs` mutex-poison recovery.
- Stabilize process-signal missing-PID test selection by preferring a high ESRCH candidate and avoiding race-prone fallback behavior.
- Add Theme Studio policy gates for MP-173: capability parity now fails on unregistered Ratatui widget/symbol additions, component registry inventory checks are exact with stable style-ID uniqueness, and style-pack fields must be explicitly classified as Studio-mapped or deferred (with a post-parity zero-deferred gate path).
- Harden `devctl check` with automatic pre/post orphaned-test sweeps so detached `target/*/deps/voiceterm-*` runners are reaped before and after local verification runs (disable via `--no-process-sweep-cleanup` when needed).

### Documentation

- Add backend-login troubleshooting guidance for missing backend command errors during `--login` flows.
- Sync core user docs (`README`, `QUICK_START`, `USAGE`, `CLI_FLAGS`, `INSTALL`, `TROUBLESHOOTING`) with Theme Studio runtime edit recovery controls, wake listener `Wake: ERR` status semantics, and `--input-device` whitespace/newline normalization behavior.

## [1.0.87] - 2026-02-20

<details>
<summary>Code Quality (internal refactors, no user-visible changes)</summary>

- Remove unused lint suppressions in PTY counters module.
- Extract right-panel rendering helpers into a dedicated module for cleaner code organization.
- Centralize full/minimal HUD right-panel scene and waveform helpers.
- Extract badge helpers (queue/wake/latency) into a dedicated submodule.

</details>

### Documentation

- Restyle README badges with a unified red-orange/charcoal theme and refine the flat badge treatment/sizing for visual consistency.
- Simplify core user guides (`README.md`, `QUICK_START.md`, `guides/*`) plus contributor/security references for clearer onboarding language and reduced duplication.
- Record MP-265 decomposition progress in engineering evolution history to keep tooling-governance documentation synchronized with master-plan updates.

## [1.0.86] - 2026-02-20

### UX

- Remove legacy visual controls from `Ctrl+O` Settings (`Theme`, `HUD style`, `Borders`, `Right panel`, `Anim rec-only`) so Settings focuses on non-theme runtime controls; visual selection now routes through `Ctrl+Y`/`Ctrl+G`/`Ctrl+U` shortcuts and HUD display flags.
- Add a dedicated Theme Studio entry flow: `Ctrl+Y` now opens Theme Studio first (instead of jumping directly into Theme Picker), with keyboard/mouse navigation and `Enter` routing from the Theme Studio picker row into the legacy Theme Picker overlay.
- Add first interactive Theme Studio visual controls for existing runtime styling: `HUD style`, `HUD borders`, `Right panel`, and `Panel animation` rows now apply directly from Theme Studio (with Enter and Left/Right arrow adjustments).
- Replace Theme Studio placeholder rows with runtime-editable style-pack controls: `Glyph profile` and `Indicator set` now cycle live rendering overrides from Theme Studio (`Enter` and Left/Right arrows).
- Add a runtime-editable `Theme borders` row in Theme Studio so overlay/theme border profiles (`theme`/`single`/`rounded`/`double`/`heavy`/`none`) can be cycled live from the same control surface.
- Add a runtime-editable `Progress spinner` row in Theme Studio so processing spinner style (`theme`/`braille`/`dots`/`line`/`block`) can be cycled live for status-line and progress spinner surfaces.
- Add a runtime-editable `Progress bars` row in Theme Studio so progress bar family (`theme`/`bar`/`compact`/`blocks`/`braille`) can be cycled live for progress and meter-style surfaces.
- Add a runtime-editable `Voice scene` row in Theme Studio so scene style (`theme`/`pulse`/`static`/`minimal`) can be cycled live for full/minimal status right-panel behavior.
- Add live value readouts in Theme Studio control rows so `HUD style`, `HUD borders`, `Right panel`, and `Panel animation` always show the currently active setting before adjustment.

### Docs

- Clarify `guides/USAGE.md` wording that HUD border/right-panel animation controls are launch-time CLI flag options rather than Settings rows.
- Replace the README top banner asset with a thinner/smaller VoiceTerm hero image and add a transparent variant (`img/logo-hero-transparent.png`) for light-background checks while removing redundant platform chips from the banner artwork.
- Tune the transparent hero variant for readability on light backgrounds by restoring all three terminal-style window-control dots, strengthening top-bar chrome, and removing the subtitle line from the transparent banner treatment.

## [1.0.85] - 2026-02-20

### UX

- Add notification-history overlay (`Ctrl+N`) and wire runtime status updates into the toast center with severity mapping (`INFO`/`OK`/`WARN`/`ERR`) plus auto-dismiss lifecycle tracking.
- Add transcript history overlay (`Ctrl+H`) with type-to-filter search and replay into the active CLI input.
- Upgrade transcript history to capture source-aware conversation rows (`mic`/`you`/`ai`) from both PTY input and PTY output, add a selected-entry preview pane, widen default overlay width for longer lines, and block replay for output-only (`ai`) rows.
- Add persistent runtime settings storage at `~/.config/voiceterm/config.toml` for core HUD/voice preferences while preserving CLI-flag precedence per launch.
- Improve themed `--help` readability by adding spacer rows between option blocks, using a distinct section-header accent color, and applying a separate definition-text color so groups like `[Backend]`/`[Voice]` and their descriptions are easier to scan.
- Fix transcript-history overlay row layout on ANSI-themed terminals so border columns stay aligned (removes stray interior `│` artifacts caused by ANSI-aware width mismatches).
- Fix transcript-history search input to ignore terminal control/focus escape noise (for example `\\x1b[0[I`) so non-text sequences no longer appear in the search field.
- Add opt-in markdown session memory logging (`--session-memory`, `--session-memory-path`) so users can persist newline-delimited user/backend conversation history to a project-local file.

### Runtime Hardening

- Harden Claude interactive prompt safety: when approval/permission prompts are detected, HUD rows are fully suppressed (no reserved PTY rows) and automatically restored on user input or timeout.
- Fix prompt-suppression lifecycle so timeout-based HUD restore also runs on periodic ticks (not only on new PTY output).

<details>
<summary>Code Quality (internal refactors, no user-visible changes)</summary>

- Standardize status-line width handling on Unicode display width.
- Consolidate transcript-preview formatting into a shared helper.
- Fix persistent-config detection so explicit default values are not overridden by saved config.
- Wire style-pack theme resolver with fallback to built-in palettes.
- Route all indicator, glyph, spinner, and progress bar rendering through the theme resolver.
- Extend glyph-profile routing to audio meter, overlay chrome, and footer symbols.
- Harden style-pack lock UX so theme switching shows lock status when a base theme is set.
- Add theme resolver policy gate test.
- Add StylePack V4 schema migration and notification lifecycle.
- Add session memory subsystem foundation.

</details>

### Documentation

- Add collapsible advanced-detail sections in `README.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, and `guides/WHISPER.md` so core setup/usage info stays visible while deeper reference content stays easy to expand.
- Rewrite the `README.md` Features section in plain language with a core-features-first layout, then group secondary capabilities under a shorter `Everyday tools` list.
- Fix README version badge source to use latest semver tag metadata (instead of release-only metadata) so the badge does not render `INVALID` when release API data is delayed/missing.
- Standardize README badge styling to compact flat black/gray chips (including CI/mutation endpoint badges), with automated CI/mutation rendering so pass stays dark while failures render red, and align primary badge order to `Rust`, `macOS`, `Linux`, `Whisper`.
- Replace a release-note style controls dump in `README.md` with concise references to `guides/USAGE.md`, `dev/CHANGELOG.md`, and `dev/DEVELOPMENT.md` so the README stays focused on stable onboarding content.
- Replace the verbose README Settings Menu details with direct links to `guides/USAGE.md` sections (`Settings Menu`, `Themes`, `HUD styles`) to keep README onboarding-focused.
- Reorder README sections so `Voice Macros` appears before `Engineering History` for better feature-first navigation.
- Restructure the README `Controls` section into grouped link lists (`keybindings`, `CLI flags`, `related docs`) to match the rest of the docs navigation style.
- Rebalance onboarding-vs-reference documentation scope: trim `QUICK_START.md` to essential setup/controls, move deep runtime behavior notes into guides, and keep pre-release/test-branch flow in `guides/INSTALL.md`.
- Expand user-guide/runtime parity for transcript history and control semantics (`Ctrl+E` idle feedback, transcript-history mouse selection/close behavior), and document `VOICETERM_ONBOARDING_STATE` plus `VOICETERM_STYLE_PACK_JSON` in the CLI env-var reference.
- Add a maintainer screenshot-refresh capture matrix in `dev/DEVELOPMENT.md` so UI image updates are tracked per surface instead of ad-hoc.
- Harden docs governance control-plane checks: add CLI flag parity + screenshot integrity guard scripts, enforce `ENGINEERING_EVOLUTION.md` updates for tooling/process/CI shifts via `docs-check --strict-tooling`, and add CI/root-artifact guardrails in `tooling_control_plane.yml`.
- Refresh core user-doc parity for transcript-history/session-memory behavior across `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `guides/INSTALL.md`, and `guides/TROUBLESHOOTING.md`.
- Add onboarding decision-flow diagrams to `guides/USAGE.md`, `guides/TROUBLESHOOTING.md`, and `.github/CONTRIBUTING.md`, and simplify `QUICK_START.md` to core controls plus direct links to the full usage reference.
- Reformat `guides/INSTALL.md` entrypoint content for readability by replacing the noisy top docs-map block and making each install option (`Homebrew`/`PyPI`/`source`/`app`/`manual`) collapsible.
- Clarify install doc structure by adding a dedicated `Option F: Windows (WSL2 only)` collapsible section and replacing the long post-install command block with a concise `After install` section that links to canonical usage/macro/navigation docs.
- Remove pre-release integration/test-branch command steps from the user install guide, and point maintainers to `dev/DEVELOPMENT.md` testing/manual-QA guidance; add an explicit `Optional: Macro Wizard` section in `guides/INSTALL.md` with install-time and post-install entrypoints.
- Reorganize `guides/USAGE.md` for faster scanning: remove the redundant top contents block, add recommended reading paths, group core controls by intent, add a common-task quick index, place local shortcuts near collapsible advanced sections, and convert launch recipes to a goal/command table.
- Reorganize `guides/TROUBLESHOOTING.md` navigation: remove the redundant top contents block, route Quick Fix jumps to top-level sections, and add section-local shortcut links above each collapsible block.
- Track theme capability matrix milestones (framework parity, texture profile, dependency baseline, widget pack, rule profile) in master plan.

## [1.0.84] - 2026-02-19

### UX

- Fix Enter-key behavior when HUD focus is on the Auto-voice toggle: pressing `Enter` now submits PTY input instead of flipping auto mode.

### Code Quality

- Add regression coverage for Enter-key handling when stale HUD button focus is on `ToggleAutoVoice`, plus focused mutation-hardening coverage in overlay input dispatch hotspots.
- Resolve a strict clippy lint (`needless_lifetimes`) in status-line heartbeat formatting so CI lint gates remain green.

### Documentation

- Add a Codecov coverage badge to the README badge row.
- Refresh user/developer docs for the v1.0.84 release-prep pass and mutation-shard triage workflow guidance.

## [1.0.83] - 2026-02-17

### UX

- Fix hidden-mode launcher mouse interaction feedback: clicking `[hide]` and collapsed `[open]` now triggers an immediate HUD redraw (matching arrow-key + `Enter` behavior) instead of waiting for a later periodic repaint.

## [1.0.82] - 2026-02-17

### Packaging

- Align PyPI package metadata version with Rust/app release metadata so `devctl ship --pypi` and version consistency gates pass in one release flow.

### Documentation

- Refresh active plan shipment snapshot after the `v1.0.81` distribution run so release status and next target planning stay synchronized.

## [1.0.81] - 2026-02-17

### UX

- Refine hidden HUD idle launcher behavior: remove the inline `Ctrl+U` hint from hidden launcher text, add a muted `[hide]` control next to `[open]`, let `hide` collapse the launcher to only `[open]`, and make `open` two-step from collapsed mode (first click restores launcher, next click switches HUD style) while keeping the existing `Ctrl+U` shortcut path.
- Expand startup and first-run discoverability: startup splash shortcuts now surface `?` help + `Ctrl+O` settings + mouse-click support, and first run shows a persistent `Getting started` hint until the first successful transcript capture.
- Replace flat clap `--help` output with a themed, grouped help screen (manual `-h`/`--help` path) that now uses a single accent family for faster scanning (gold-toned flags + matching section headers), dim/quiet frame/meta styling, plus bracketed section headers and `> --flag` label prefixes for a terminal-native visual style, while keeping runtime `--no-color`/`NO_COLOR` plain-text behavior.
- Group help overlay shortcuts into task categories (`Recording`, `Mode`, `Appearance`, `Sensitivity`, `Navigation`) for faster scanning.
- Add persistent runtime help discoverability without changing splash behavior: hidden HUD idle launcher now surfaces `? help` + `^O settings`, and the help overlay now includes clickable Docs/Troubleshooting OSC-8 links.
- Tighten settings overlay readability: widened labels, explicit `Wake cooldown`/`Anim rec-only` naming, selected-item description footer, slider range hints, and read-only indicators for `Backend`/`Pipeline`.
- Clarify settings footer controls with explicit keyboard and pointer guidance (`[×] close · ↑/↓ move · Enter select · Click/Tap select`) so overlay navigation is more readable and touch-friendly.
- Fix settings slider pointer behavior so clicking left/right on slider tracks now moves in the matching direction (instead of always stepping forward).
- Add settings-overlay mouse row actions: clicking a settings row now selects it and applies the same toggle/cycle behavior as keyboard controls (with row-click support for `Close` and `Quit`).
- Fix overlay mouse hit-testing for settings/theme/help panels so click actions continue to work when terminals report non-left-aligned panel `x` coordinates (restores reliable row toggles and slider adjustments by click).
- When `Ctrl+E` is pressed in insert mode while idle with no staged text, VoiceTerm now shows `Nothing to send` instead of silently consuming the key.

### Runtime Hardening

- Remove overlay input drop behavior for unmatched keys: when help/settings/theme overlays are open, unmatched input now closes the overlay and replays the action into the normal input path instead of swallowing it.
- Replace generic capture/transcript failure statuses with actionable log-path messages (`... (log: <path>)`) across event-loop, button-handler, and transcript delivery paths.
- Persist first-run onboarding completion to `~/.config/voiceterm/onboarding_state.toml` (overrideable via `VOICETERM_ONBOARDING_STATE`) after the first successful transcript.

### Code Quality

- Extract shared overlay frame rendering primitives (`overlay_frame`) and remove duplicated border/title/separator implementations from help/settings/theme-picker overlays.
- Standardize overlay/HUD width logic to Unicode-aware display-width helpers and add HUD module priority ordering so queue/latency modules are retained first under constrained widths.
- Extract themed help/status message helpers into dedicated modules (`custom_help.rs`, `status_messages.rs`) so help rendering and log-path status formatting are reused across runtime paths.

## [1.0.80] - 2026-02-17

### UX

- Add wake-word controls plus runtime listener wiring: settings/CLI now configure `Wake word` ON/OFF, sensitivity, and cooldown (still default OFF), detections feed the same capture-start path used by `Ctrl+R`, and wake-listener lifecycle now has explicit start/stop ownership with bounded shutdown joins.
- Add explicit wake privacy HUD state plus guardrails: Full HUD now shows `Wake: ON` (theme-matched pulse) vs `Wake: PAUSED`, and wake phrase matching is constrained to short, command-like utterances to reduce false positives from background conversation.

### Runtime Hardening

- Extend PTY session-guard cleanup with a detached-backend orphan sweep: during cleanup, VoiceTerm now also reaps backend CLIs (`codex`, `claude`, `gemini`, `aider`, `opencode`) that are detached (`PPID=1`), older than a safety threshold, not covered by active lease files, and no longer have a live shell process on the same TTY.

### Code Quality (MP-188)

- Decompose `ipc/session.rs` backend orchestration: Claude launch, auth flow, loop control, IPC state construction, and event-emit/test-capture plumbing now delegate through dedicated extracted modules (`session/claude_job.rs`, `session/auth_flow.rs`, `session/loop_control.rs`, `session/state.rs`, `session/event_sink.rs`, `session/test_support.rs`), keeping `session.rs` focused on command-loop orchestration.
- Decompose `codex/pty_backend.rs` backend orchestration: PTY-arg construction, job event emission, persistent-session polling/cache, output sanitization, and test infrastructure now delegate through extracted submodules (`pty_backend/output_sanitize.rs`, `pty_backend/session_call.rs`, `pty_backend/job_flow.rs`, `pty_backend/test_support.rs`), reducing coupling and review blast radius.

### Tooling (MP-189)

- Add maintainer lint-hardening lane (`devctl check --profile maintainer-lint`) and corresponding CI workflow (`lint_hardening.yml`) enforcing `redundant_clone`, `redundant_closure_for_method_calls`, `cast_possible_wrap`, and `dead_code` clippy families.
- Burn down `redundant_clone`, `redundant_closure_for_method_calls`, and `cast_possible_wrap` findings across runtime/core modules; complete a one-time `must_use_candidate`/`missing_errors_doc` sweep across backend/audio/config/codex/ipc/legacy/pty/STT modules.

### Tests

- Add session-guard unit coverage for `ps` elapsed-time parsing and detached-orphan candidate filtering so process-cleanup heuristics remain deterministic and reviewable.
- Add wake-word regression/soak validation gates: new lifecycle + detection-path regression coverage, long-run false-positive/matcher-latency soak test, reusable guard script (`dev/scripts/tests/wake_word_guard.sh`), release-profile `devctl check` integration, and CI lane (`wake_word_guard.yml`).

## [1.0.79] - 2026-02-17

### UX

- In insert send mode, consume `Ctrl+E` when no staged text is pending and recording is idle so raw `Ctrl+E` is no longer forwarded to the wrapped CLI.
- Rename insert-mode early-submit status from `Sending capture...` to `Finalizing capture...` to match the stop-and-transcribe behavior.
- Apply hidden launcher muted-gray styling to hidden recording strip output so hidden mode uses one consistent subdued color treatment.

### Documentation

- Run a full user-doc sync for recording/send controls and hidden HUD behavior across `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `guides/INSTALL.md`, and `guides/TROUBLESHOOTING.md`.

## [1.0.78] - 2026-02-17

### UX

- Prevent malformed/fragmented mouse-report escape sequences from leaking into the wrapped CLI input stream during interrupts, which could previously surface raw `[<...` fragments in the terminal.
- Hide/reset latency badges when captures produce no transcript (`Empty`/error paths), use direct STT timing only (no derived fallback math), auto-expire stale idle latency badges after a short window, and color latency severity by speech-relative STT speed (`rtf`) so long utterances do not falsely read as regressions.
- Expand transcript non-speech sanitization to strip additional Whisper ambient-sound hallucination tags such as `(siren wailing)`, `(engine revving)`, and `(water splashing)`.
- In insert mode, make `Ctrl+E` send staged text immediately when present, and otherwise request early-stop submit while recording with no staged text.
- Tune hidden HUD idle visuals to a subdued/dull gray launcher treatment (`VoiceTerm hidden · Ctrl+U` + `[open]`) so hidden mode stays unobtrusive.

## [1.0.77] - 2026-02-17

### UX

- Fix `Ctrl+E` behavior in insert/edit mode while recording: when no staged text is pending, it now requests early-stop processing and forces one-shot transcript submit so noisy-room captures can be sent immediately without waiting for silence timeout.

### Documentation

- Clarify control docs (`README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `guides/TROUBLESHOOTING.md`) so `Ctrl+R` is documented as stop-without-send and `Ctrl+E` as stop-and-submit for insert-mode active recording.

## [1.0.76] - 2026-02-17

### UX

- Fix Full HUD `ribbon` visualizer baseline behavior by padding short waveform history with floor-level samples, so bars rise from the baseline instead of rendering as a full-height block at startup.
- Make `Ctrl+R` a strict recording start/stop toggle for both manual and auto capture, and ensure stop cancels capture without sending text; `Ctrl+E` remains the explicit send-now path for staged insert-mode text.
- Restore theme-specific recording indicators across Full/Minimal/Hidden/compact HUD rendering so each theme keeps matching icons while recording state pulses through theme-native accent colors.

### Packaging

- Fix Homebrew model-cache persistence for `opt` launch paths: `scripts/start.sh` and `scripts/setup.sh` now detect both Homebrew `Cellar` and `opt` prefixes (including symlink-resolved paths) so model downloads stay in `~/.local/share/voiceterm/models` across upgrades instead of being redownloaded per-version under `libexec/whisper_models`.

### Tests

- Add `dev/scripts/devctl/tests/test_homebrew_model_paths.py` to guard Homebrew `opt` path detection and symlink-aware (`pwd -P`) script resolution in startup/setup model-directory logic.
- Add status-line regression coverage that enforces theme-specific recording indicators in Full/Minimal/compact HUD paths.

## [1.0.75] - 2026-02-17

### UX

- In insert send mode, make `Enter` submit-only (always forwards newline) so command submission is never blocked by recording-state stop logic.
- Add `Ctrl+R` recording toggle behavior (start when idle, stop early when recording) and `Ctrl+E` send-now handling for staged insert-mode text during active capture.
- Keep idle ribbon placeholder bars theme-accented in status-line waveform panels so HUD visuals stay consistent with the active palette.

### Documentation

- Update user docs (`README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `guides/INSTALL.md`, `guides/TROUBLESHOOTING.md`) for the new recording/send control model.
- Refresh user and developer docs for current HUD wording, install/flags guidance, and active planning indexes without version-specific callouts in user-facing guides.

## [1.0.74] - 2026-02-17

### UX

- Restore Full HUD right-panel telemetry (`ribbon`/`dots`/`heartbeat`) to the main status row (top-right lane) while keeping the shortcuts row focused on interactive controls.
- Expand active mode signaling so Full HUD now shows live state labels (`AUTO REC`, `PTT REC`, `AUTO PROC`, `PTT RESP`) with animated recording/processing indicators.
- Keep recording button highlighting theme-native (`colors.recording`) so active capture remains consistent with each theme palette.

## [1.0.73] - 2026-02-17

### UX

- Restore right-edge anchoring for the Full HUD trailing visualization panel so the waveform lane stays pinned to the far-right corner instead of drifting next to shortcut text.

### Runtime Hardening

- Add a PTY session-lease guard that records VoiceTerm-owned backend parent PIDs and reaps stale process groups from dead owners before each new PTY spawn, preventing orphan carryover without blocking multiple concurrent VoiceTerm sessions.

### Code Quality

- Reduce `settings_handlers` duplication by introducing a shared enum-cycling helper and moving its large test module into `settings_handlers/tests.rs` for lower runtime-file coupling.

### Documentation

- Document startup PTY stale-lease cleanup behavior for maintainers (`dev/ARCHITECTURE.md`) and operators (`guides/TROUBLESHOOTING.md`).

## [1.0.72] - 2026-02-17

### UX

- Move the Full HUD right-panel visualizer lane (`Ribbon`/`Dots`/`Heartbeat`) to the shortcuts row so it aligns with latency/theme/help controls instead of occupying the main status row.
- Reduce transient JetBrains cursor artifact flashes (`|`/block cursor) during HUD redraws by hiding/restoring the cursor around JetBrains-specific status/overlay paint sequences.
- Preserve selected themes on `xterm-256color` terminals (fallback to `ansi` only on ANSI16 terminals) so visualizer/border styling no longer collapses to a single ANSI look.
- Rebalance HUD/mic meter severity thresholds to restore visible green/yellow/red transitions during normal-to-loud speech.
- Improve high-output HUD responsiveness by prioritizing pending status/overlay redraws and increasing PTY output chunk batching to reduce settings/navigation lag while backend output is streaming.

### Documentation

- Sync user guides (`README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`, `guides/INSTALL.md`, `guides/TROUBLESHOOTING.md`) with Full HUD visualizer lane placement, `xterm-256color` theme behavior, JetBrains cursor-flash mitigation notes, and high-output responsiveness guidance.

## [1.0.71] - 2026-02-17

### Runtime Hardening

- Keep status/overlay UI updates non-blocking under writer queue pressure so heavy backend output does not stall settings navigation or recording HUD refreshes.
- Rebalance meter severity coloring for normal speech vs loud transients to reduce false "too loud" visual signals in waveform/dot panels.

### Documentation

- Expand release test guidance (`dev/DEVELOPMENT.md`) with paired operator workflow, process churn/CPU leak checks, and high-load responsiveness validation.
- Sync user docs (`README.md`, `QUICK_START.md`, `guides/CLI_FLAGS.md`, `guides/INSTALL.md`, `guides/TROUBLESHOOTING.md`, `guides/USAGE.md`) with pre-release validation flow and updated lag/meter troubleshooting guidance.

## [1.0.70] - 2026-02-17

### Documentation

- Archive `RUST_GUI_AUDIT_2026-02-15.md` to `dev/archive/2026-02-15-rust-gui-audit.md` and keep `dev/active/MASTER_PLAN.md` as the sole active hardening execution tracker.
- Refresh developer governance docs (`AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/ARCHITECTURE.md`, `dev/scripts/README.md`, `.github/GUIDE.md`) to remove active dependency on the archived Rust GUI audit file.
- Fix `guides/USAGE.md` status-table spacing to keep `docs_lint` markdown table validation green.

### UX

- Remove remaining pipeline labels from user-facing status text (`Listening Manual Mode`, `Transcript ready`, `No speech detected`, and HUD mode tokens) and keep pipeline visibility in Settings (`Voice pipeline`).
- Fix overlay mouse interaction handling so non-action body clicks no longer close active overlays; keep close behavior on explicit controls (footer `[×]`) and preserve clickable theme-row selection in Theme Picker.

### CI/Tooling

- Retire `.github/workflows/audit_traceability_guard.yml`, remove `dev/scripts/check_audit_traceability.py`, and remove the `make traceability-audit` helper target to simplify active CI/tooling flow around `MASTER_PLAN.md`.
- Add `dev/scripts/generate-release-notes.sh` plus `devctl release-notes`/`make release-notes` wrappers, and wire `release.sh` to auto-generate `/tmp/voiceterm-release-vX.Y.Z.md` for `gh release create --notes-file`.
- Add mutation-score badge generation (`dev/scripts/render_mutation_badge.py` + `.github/badges/mutation-score.json`) and switch README mutation badge to a percentage endpoint (red/orange/green by score, `failed` only when outcomes are unavailable or invalid).

### Runtime Hardening

- Prevent orphaned backend CLI processes on abrupt terminal/IDE termination by adding a PTY child lifeline watchdog that escalates `SIGTERM` -> `SIGKILL` on parent disappearance, plus regression coverage for parent `SIGKILL` teardown.
- Decompose runtime hot-path modules for lower review risk: split `event_loop` input/output/periodic/overlay handlers into focused modules, split `voice_control/drain` message-processing helpers into dedicated submodules, and extract IPC non-blocking event processors into `ipc/session/event_processing/` (plus `ipc/session/loop_runtime.rs` for command/loop helpers) while preserving regression coverage.

## [1.0.69] - 2026-02-17

### UX

- Stabilize Full HUD mode labels so the left mode lane keeps `PTT`/`AUTO`/`IDLE` while active capture/transcription state transitions appear in the main status message lane.
- Simplify empty-capture wording by removing backend pipeline labels from the user-facing `No speech detected` status text.
- Start `Settings -> Macros` in `OFF` state on startup so macro expansion is opt-in.
- Add a project starter macro pack at `.voiceterm/macros.yaml` with common codex-voice developer workflow commands.
- Add dedicated macro onboarding wizard `scripts/macros.sh` with pack selection (`safe-core`, `power-git`, `full-dev`), git-origin repo auto-detection, and generated-file validation.
- Expand shipped macro packs with high-frequency git/GitHub workflows plus codex-voice maintainer checks/release helpers, add placeholder templating (`__GITHUB_REPO__`, `__GITHUB_OWNER__`, `__DEFAULT_BRANCH__`, `__GITHUB_USER__`, `__CURRENT_BRANCH__`), and validate GitHub CLI readiness/auth for GitHub macro packs.
- Extend source install flow (`scripts/setup.sh install`) with an optional post-install macro wizard prompt and explicit `--with-macros-wizard` / `--macros-pack` flags.

## [1.0.68] - 2026-02-16

### UX

- Add an explicit `responding` voice state in HUD modes (Full/Minimal/Hidden), including automatic reset back to idle when backend output arrives or status deadlines clear.
- Only enter `responding` when transcript delivery actually submits to the backend (auto/newline path), avoiding false `responding` state in insert mode.
- Add quick theme cycling on `Ctrl+G` (plus CSI-u terminal variants), and surface the new shortcut in the help overlay and HUD shortcut rows.
- Add built-in voice navigation actions for `scroll up`, `scroll down`, `show last error`, `copy last error`, and `explain last error`.
- Apply macro-first precedence for overlapping voice phrases; built-in navigation can still be forced with explicit `voice scroll up` / `voice scroll down`.
- Add Linux clipboard support for `copy last error` via `wl-copy`, `xclip`, or `xsel` fallback (macOS `pbcopy` unchanged).

### Tests

- Add parser regression coverage for `Ctrl+G` direct and CSI-u key paths.
- Add prompt-tracker coverage for capturing the latest error-like output line.
- Add voice-navigation unit coverage for scroll/show/copy/explain command actions.
- Add regression coverage that enforces macro-first precedence over built-in voice navigation phrase matches.

### Tooling

- Add commit-range mode to docs-check (`python3 dev/scripts/devctl.py docs-check --user-facing --since-ref <ref>`) so post-commit audits remain meaningful on a clean working tree.

## [1.0.67] - 2026-02-15

### Documentation

- Add a root developer docs shortcut (`DEV_INDEX.md`) that points to the canonical developer index (`dev/README.md`) and move the canonical engineering timeline to `dev/history/ENGINEERING_EVOLUTION.md`.
- Rename developer docs hub wording from "docs map" to "Developer Index" and simplify README developer links.
- Refresh `dev/active/MASTER_PLAN.md` status snapshot to the current release baseline (`v1.0.66`).
- Run staged markdown-structure cleanup for core developer docs (`AGENTS.md`, `CLAUDE.md`, `dev/active/MASTER_PLAN.md`, `dev/history/ENGINEERING_EVOLUTION.md`, `dev/ARCHITECTURE.md`, `dev/adr/README.md`, `dev/scripts/README.md`) and user CLI flags docs (`guides/CLI_FLAGS.md`) to satisfy current markdownlint policy.
- Consolidate troubleshooting into a single canonical guide (`guides/TROUBLESHOOTING.md`) and replace split-page links with section anchors.
- Add documentation entrypoint indexes at `guides/README.md` and `dev/README.md`, plus an explicit README section linking `dev/history/ENGINEERING_EVOLUTION.md` for architecture/process history navigation.
- Rework documentation entrypoints into a clearer task-first navigation model (README quick nav + documentation order hints, expanded guides index by goal, and consistent cross-links across quick start/whisper/dev docs map pages).
- Add repository markdown quality gates via `.markdownlint.yaml` and `.github/workflows/docs_lint.yml`, and resolve markdown structure/rendering issues in the key published docs set.
- Remove version-specific stability callouts from user guides/README and keep release/version detail centralized in the changelog and release notes.
- Clarify README macro toggle wording and link directly to the Usage guide section that explains macro file format and behavior.
- Simplify README backend/UI sections to focus on primary Codex/Claude support and move detailed/advanced behavior references to the Usage guide.
- Reorganize README controls into grouped sections (voice, UI/navigation, sensitivity, session control) and link to the Usage guide for full behavior details.
- Add a dedicated `Voice Macros` heading in README so macro behavior guidance is clearly separated from keyboard controls.
- Expand README macro explanation with a concrete trigger example plus clear ON/OFF behavior semantics.
- Center the README banner wordmark within `img/logo.svg` so the brand image appears visually centered on GitHub.
- Move the README voice recording image into a standalone section placed before supported AI CLI examples for a cleaner reading flow.
- Remove hotkey labels from README UI section headings and keep keybind details in the controls table.
- Move README `Install Options` directly below `Quick Start` and update quick-nav order so install paths are visible earlier.
- Promote README `Voice Macros` to a top-level section and point controls help text directly to the Usage guide keyboard-shortcuts reference.
- Replace the verbose README controls key table with direct links to the Usage guide shortcut/settings references.
- Merge README onboarding into one `Install and Start` section so install paths and first-run steps are not split across separate sections.
- Remove duplicated install content from README and keep one concise install/start flow with links to the full install guide for alternatives/details.
- Reformat README install flow with collapsible per-method blocks (Homebrew/PyPI/source/macOS app) while keeping a single unified onboarding section.
- Add `Controls` to README quick navigation so users can jump directly to that section.
- Refine README install layout to avoid mixed numbered steps around collapsibles (clean method blocks with the recommended path expanded by default).
- Split README AI CLI prerequisite snippet into explicit Codex and Claude install blocks before the VoiceTerm install step.
- Remove `(default)` labels from Codex headings in README for cleaner backend section wording.
- Bold the README install prerequisite labels (`Codex` and `Claude Code`) to improve visual scanability.
- Reorganize `guides/USAGE.md` around a task-first flow (quick start, controls, modes, customization, macros, status reference) with reduced duplication and consistent `auto`/`insert` terminology.
- Replace branch-pinned raw image links in usage/readme docs with repository-relative paths for stable previews across branches and PRs.
- Tighten `guides/CLI_FLAGS.md`, `guides/INSTALL.md`, and `guides/TROUBLESHOOTING.md` by fixing section navigation, removing internal implementation-heavy wording from user flows, and improving cross-guide linking.
- Add an install-path decision table in `guides/INSTALL.md` so users can quickly choose Homebrew, PyPI, source, app, or manual run based on their goal.
- Standardize backend support references to the canonical matrix in `guides/USAGE.md#backend-support` and link to it from README/quick start/flags/troubleshooting docs.
- Add an explicit unsafe-governance checklist at `dev/security/unsafe_governance.md` and link it from `AGENTS.md`/`dev/DEVELOPMENT.md` so PTY/STT unsafe changes carry per-invariant test expectations.

### CI

- Align `docs_lint.yml` trigger paths with the exact markdown files linted (published docs subset + `DEV_INDEX.md`).
- Add a dedicated `Security Guard` workflow (`.github/workflows/security_guard.yml`) that runs RustSec advisory scans and enforces policy thresholds.
- Enforce dependency risk gates via `dev/scripts/checks/check_rustsec_policy.py` (fail on CVSS >= 7.0 plus `yanked`/`unsound` warning kinds) and upload the audit report as a CI artifact.
- Add `parser_fuzz_guard.yml` for parser/ANSI-OSC property-fuzz regression coverage.
- Add `audit_traceability_guard.yml` to enforce hardening-traceability consistency between `dev/active/MASTER_PLAN.md` and `RUST_GUI_AUDIT_2026-02-15.md`.

### Security

- Expand `.github/SECURITY.md` with an explicit local threat model, trust-boundary notes, and operational guidance for `--claude-skip-permissions`.
- Add risky-flag guidance for `--claude-skip-permissions` in `guides/CLI_FLAGS.md` and a troubleshooting path in `guides/TROUBLESHOOTING.md`.

### Tests

- Add `stt::tests::transcriber_restores_stderr_after_failed_model_load` to verify stderr descriptor restoration invariants in the Whisper model-load error path.
- Add proptest-based parser boundary regressions for `find_csi_sequence`, `find_osc_terminator`, and `split_incomplete_escape`.

### Tooling

- Add `dev/scripts/check_audit_traceability.py` and Makefile shortcuts (`parser-fuzz`, `traceability-audit`) for local parity with new hardening governance lanes.

## [1.0.66] - 2026-02-15

### CI

- Fix `Voice Mode Guard` workflow commands to run against the current `voiceterm` binary name.
- Fix `Perf Smoke` workflow log verification to read `voiceterm_tui.log`.

### Tests

- Remove a flaky PTY-exit assertion in `event_loop` tests that intermittently failed on GitHub runners while preserving deterministic non-retry error-path coverage.

## [1.0.65] - 2026-02-14

### Packaging

- Publish a PyPI metadata refresh so the project page uses product-style VoiceTerm messaging instead of launcher-only wording.
- Update PyPI metadata author to **Justin Guida** and improve package description/links for consistency with the main repository docs.

## [1.0.64] - 2026-02-14

### Branding

- Complete project rebrand to **VoiceTerm** across the codebase, CLI help text, startup banner/UI copy, docs, scripts, and macOS app bundle path (`app/macos/VoiceTerm.app`).
- Rename Rust package/binary defaults to `voiceterm` and move overlay source path to `rust/src/bin/voiceterm/`.

### Packaging

- Add a PyPI package scaffold under `pypi/` (`name = "voiceterm"`) with a launcher entrypoint.
- Add `dev/scripts/publish-pypi.sh` to build/check PyPI artifacts and optionally upload with `--upload`.

### Documentation

- Update install/readme docs with `voiceterm` command usage and add PyPI install guidance (`pipx install voiceterm` / `pip install --user voiceterm`).

## [1.0.63] - 2026-02-14

### UX

- Harden PTY teardown and resize signaling so VoiceTerm targets the full backend process group (wrapper + descendants), not just the direct child PID, reducing orphan `codex`/`claude` processes after repeated exits/cancels.
- Ensure Claude IPC piped-mode cancellation/disconnect paths terminate and reap child processes to prevent stale process accumulation across many runs.
- Reduce JetBrains overlay flicker by ignoring no-op SIGWINCH updates (unchanged rows/cols), avoiding redundant PTY resize signaling and HUD redraw clears.
- Reduce recording-mode flicker by avoiding full status-banner clears on steady-state redraws; writer now clears only when banner height shrinks.
- Use DEC cursor save/restore plus temporary autowrap disable during JetBrains HUD redraws, while keeping Cursor/other terminals on existing safe paths.
- Apply a JetBrains-specific meter redraw floor (120ms) during recording to lower repaint churn while preserving responsiveness.
- Stabilize shortcut-pill bracket coloring during rapid recording redraws by removing per-pill reset churn that could briefly show default terminal white in JetBrains.
- Reduce JetBrains repaint jitter by writing HUD rows before `EL` trailing clears (instead of clear-then-paint), and keep a one-column right gutter on the full HUD main row.
- Avoid repainting unchanged HUD banner rows during steady-state updates, so JetBrains recording refreshes only rewrite lines that actually changed.
- Add configurable Full HUD border styles (`theme`/`single`/`rounded`/`double`/`heavy`/`none`) and expose border-style selection in Settings; right-panel visualization remains user-toggleable to `Off` for a text-only HUD.
- Fix `Anim only` semantics for right-panel telemetry: when enabled, idle HUD now keeps a static panel visible (non-animated) instead of hiding it entirely until recording starts.

### Tests

- Add PTY lifecycle regression coverage that spawns a process-group leader with descendants and verifies descendant cleanup for both `PtyCliSession` and `PtyOverlaySession` drop paths.
- Add writer resize coverage to ensure unchanged terminal dimensions are treated as no-op redraw events.

## [1.0.62] - 2026-02-14

### UX

- Revert the post-`v1.0.61` scroll-region protection change that caused severe Full HUD redraw corruption/duplication in active Codex sessions.
- Re-publish the known-good Full HUD writer/render baseline (the `v1.0.53`-derived path) as the current stable release.
- Clear stale HUD/overlay rows on resize before redraw so ghost top/bottom frames are removed when terminal geometry changes during startup/runtime.
- Auto-skip startup splash in JetBrains IDE terminals (PyCharm/IntelliJ/CLion/WebStorm) to avoid alternate-screen handoff artifacts.

### Tests

- Add startup-banner coverage for JetBrains environment detection and skip behavior.

### Documentation

- Clarify release history: `v1.0.62` supersedes the first `v1.0.61` tag for HUD stability.
- Update troubleshooting and architecture notes for JetBrains startup behavior and resize ghost-frame cleanup.

## [1.0.61] - 2026-02-13

### UX

- Restore the `v1.0.53` HUD writer/render path in current builds to recover stable Full HUD behavior in Cursor and JetBrains terminals while preserving later non-render features.
- Keep the one-column HUD safety margin in status formatting to avoid right-edge autowrap drift in IDE terminals.

### Documentation

- Sync release/user docs for the `v1.0.61` HUD stabilization rollback and IDE troubleshooting guidance.

## [1.0.60] - 2026-02-13

### UX

- Prevent cross-terminal HUD wrap artifacts by reserving a one-column safety margin for banner rendering and clipping writer-rendered HUD/overlay rows to terminal width before output.
- Suppress misleading PTY shutdown noise by treating expected exit-time write failures (`EIO`/broken pipe family) as benign when backend PTY teardown has already started.

### Tests

- Add writer render coverage ensuring status-banner and overlay panel rows are clipped to terminal width.

### Documentation

- Update troubleshooting guidance for JetBrains HUD duplication symptoms and clarify that PTY exit-write `EIO` log noise is fixed in `v1.0.60`.

## [1.0.59] - 2026-02-13

### UX

- Fix a remaining JetBrains full-HUD wrap edge case by guarding rendered banner width and preventing one-column overflow in the shortcuts row.

### Tests

- Add status-line row-width coverage ensuring full-HUD shortcuts rows stay within banner bounds.

## [1.0.58] - 2026-02-13

### UX

- Fix full-HUD duplication/stacking in JetBrains terminals (PyCharm/CLion) by using ANSI cursor save/restore semantics that preserve active scroll-region margins.

### Tests

- Add writer scroll-region sequence assertions to ensure render paths avoid DEC cursor restore codes that can reset terminal scroll margins.

## [1.0.57] - 2026-02-13

### UX

- Suppress startup arrow-key escape noise until backend output begins so pre-launch swipes/arrow presses on the splash screen do not leak `^[...` sequences into Claude/Codex prompts.
- Suppress idle transition pulse markers for auto-voice toggles so `Ctrl+V` no longer shows a transient dot beside `PTT`.
- Restore conservative theme fallback behavior: non-truecolor terminals now resolve truecolor themes to `ansi`, and generic IDE env markers alone no longer force truecolor mode.

### Tests

- Add shared arrow-escape noise coverage for full sequences, partial fragments, and non-noise input pass-through.
- Add theme-resolution coverage for 256-color fallback behavior in runtime theme switching (`theme_ops`) and config theme resolution.
- Add color-mode coverage ensuring generic IDE markers without terminal truecolor hints resolve to `Color256` instead of `TrueColor`.

### Documentation

- Update docs wording so adaptive HUD transition-pulse behavior reflects current implementation.
- Prune troubleshooting guidance to current behavior by removing legacy fixed-issue upgrade notes.

## [1.0.56] - 2026-02-13

### UX

- Shorten startup splash dwell time, render it in an alternate screen, and clear with stronger reset sequences so IDE terminals (for example PyCharm) do not retain the splash frame.
- Fix startup tagline centering by using display-width math for Unicode separators (`│`) instead of byte length.
- Improve terminal color capability detection so JetBrains/VSCode-style terminals that omit `COLORTERM` can still use truecolor themes instead of always falling back to ANSI.
- Rename Settings send-mode `Insert` label to user-facing `Edit` so terminology matches HUD/status messaging.
- Preserve Full HUD lane alignment between the duration separator and `[edit]` shortcut column.
- Remove the startup ASCII banner’s leading blank line so splash content sits closer to the top edge instead of opening with extra top whitespace.
- Keep requested themes on `xterm-256color` terminals (fallback to `ansi` only on true ANSI-16 environments) so IDE terminals are less likely to collapse into one look.
- Expand JetBrains terminal truecolor heuristics (`TERM_PROGRAM`/`TERMINAL_EMULATOR`/IDE env markers) to better match PyCharm/CLion integrations.
- Render Theme Picker rows neutrally when current theme is `none` (no per-theme color previews), so `none` mode no longer looks colorized.

### Tests

- Add settings-render coverage for `Send mode -> [ Edit ]` label semantics.
- Add full-HUD layout coverage ensuring the duration separator aligns with the `[edit]` shortcut lane.
- Add startup-banner coverage ensuring ASCII splash output no longer starts with a blank line.
- Add color-mode coverage for JetBrains `TERM_PROGRAM` and IDE-marker env detection.
- Add theme-picker coverage verifying `none` mode renders neutral preview rows (no ANSI/theme glyph colorization).
- Add theme-resolution coverage for `xterm-256color` keep-theme behavior and explicit ANSI-16 fallback behavior.

### Documentation

- Update user docs and troubleshooting notes for startup splash behavior, IDE theme capability differences, and `none` theme preview behavior.

## [1.0.55] - 2026-02-13

### UX

- Add project-scoped voice macro expansion from `.voiceterm/macros.yaml` before transcript injection, including trigger-to-command mappings and template macros with `{TRANSCRIPT}` remainder substitution.
- Support per-macro send-mode overrides (`auto`/`insert`) so selected macros can stay in insert behavior even when global send mode is auto.
- Add a runtime `Macros` ON/OFF setting in the Settings panel to control macro expansion without changing send mode behavior.
- Keep status/HUD text aligned with baseline `auto`/`insert` semantics (no extra review/intent labels).
- Add compact right-panel visualization rendering to **Minimal HUD** for Ribbon/Dots/Heartbeat modes, honoring the existing recording-only panel setting.
- Add bounded sparkline-style telemetry in compact HUD views for both meter levels and latency trend.
- Add a short state-transition pulse marker on mode/state changes so status updates are easier to perceive.
- Add adaptive compact HUD module selection by context (recording vs busy queue vs idle) so narrow layouts prioritize relevant telemetry.
- In Minimal HUD with right-panel visuals, color ribbon waveform bars by level (instead of inheriting terminal default white), and stabilize idle status text to concise labels (`Ready`/`Queued N`/`Warning`/`Error`) to reduce layout churn.
- Fix Full HUD right-panel width handling so idle/status text (including `Ready`) remains visible instead of collapsing to blank when Ribbon/Heartbeat is enabled.
- Tighten Full HUD idle semantics: use `PTT` label (instead of `MANUAL`), collapse idle success/info text to `Ready`, and avoid duplicate queue text when `Q:n` is already shown in the shortcuts row.
- Remove transition-marker dot jitter in recording/processing labels; transition pulses now use brief `✦`/`•` markers only in idle transitions.
- Improve Full HUD visual balance by increasing the maximum right-panel ribbon waveform width.
- Keep Full HUD steady-state `Ready` near the dB lane in the main row while latency remains in the shortcuts row.
- Add runtime latency display modes (`Off`, `Nms`, `Latency: Nms`) so users can choose whether shortcuts-row latency is hidden, compact, or labeled.
- Color the full labeled latency text (`Latency: Nms`) with the same threshold color as compact latency (`Nms`).
- Suppress duplicate active-state text in Full HUD main row (for example `processing`/`ready`) so recording/processing state is shown once via the left mode indicator.
- Update send-mode status wording to user-facing `Edit mode: press Enter to send` when insert behavior is active.

### CI

- Add a dedicated latency guard workflow (`.github/workflows/latency_guard.yml`) that runs synthetic voice-only regression bounds in CI.
- Extend `latency_measurement` and `dev/scripts/tests/measure_latency.sh` with CI guardrail flags (`--ci-guard`, `--skip-stt`, and min/max latency bounds) for deterministic regression checks.
- Add a dedicated voice-mode regression workflow (`.github/workflows/voice_mode_guard.yml`) to continuously validate macros-toggle and send-mode behavior.

### Documentation

- Document latency baseline results in `dev/archive/2026-02-13-latency-baseline.md`.
- Document the latency guard workflow and command usage in `dev/scripts/README.md`.
- Document voice macros in `guides/USAGE.md`, `guides/TROUBLESHOOTING.md`, and `dev/ARCHITECTURE.md`.
- Document the runtime macros ON/OFF behavior in usage/troubleshooting/architecture docs.

### Tests

- Add unit coverage for voice macro parsing, trigger matching, template remainder substitution, and project file loading.
- Add settings and drain coverage for macros ON/OFF behavior.
- Add status-line/button coverage for baseline send-mode labels (`send`/`edit`).
- Add status-line coverage for Minimal HUD right-panel rendering and recording-only visibility behavior.
- Add coverage for bounded latency history retention and transition animation marker behavior.
- Add HUD module coverage for meter/latency sparkline rendering.
- Add status-line coverage for adaptive compact module registry selection.
- Add minimal-HUD coverage for ribbon colorized waveform output and idle status compaction behavior.

### Developer Experience

- Add `python3 dev/scripts/devctl.py hygiene` to audit archive naming, ADR status/index consistency, and `dev/scripts` documentation coverage.
- Add archive retention and ADR supersession lifecycle policy updates across `AGENTS.md`, `dev/archive/README.md`, and `dev/adr/README.md`.

## [1.0.54] - 2026-02-13

### UX

- Expand Claude prompt-ready matching to recognize confirmation prompts (for example `[Y/n]`) in addition to bare `>` prompt lines.
- Reserve the terminal scroll region above the HUD/overlay so long PTY output does not scroll through the bottom HUD rows.
- Ensure terminal resize correctly resets stale scroll-region state when HUD reservation shrinks to zero.
- Clear stale recording duration/meter/preview visuals when auto-voice is disabled, including the capture-cancel path.

### Tests

- Add Claude backend prompt-pattern coverage for confirmation prompts.
- Add writer render coverage for setting and resetting terminal scroll-region sequences.

## [1.0.53] - 2026-02-13

### UX

- Improve HUD/overlay responsiveness while CLI output is continuously streaming by reducing writer redraw wait thresholds and forcing redraw opportunities during PTY output flow.
- Batch PTY output chunks in the event loop before forwarding to the writer to reduce message pressure and settings/HUD lag while Codex is busy.
- Use non-blocking PTY-output dispatch with deferred backpressure handling so busy output no longer blocks input/settings event handling.
- Queue and flush PTY input with non-blocking writes so typing and Enter forwarding remain responsive even when backend output is busy or PTY writes hit temporary backpressure.
- Clear stale capture visuals (recording duration + dB waveform/meter) when capture exits recording mode so the HUD does not freeze with old timer/meter values.
- Clamp live recording meter floor to `-60dB` for stable display semantics.

### Tests

- Add PTY write coverage for single-attempt non-blocking writes, including partial-write and `WouldBlock` behavior.

### Documentation

- Add troubleshooting guidance for delayed typing/Enter behavior under heavy backend output.

## [1.0.52] - 2026-02-13

### Documentation

- Promote `AGENTS.md` to a tracked repository policy file and remove the ignore rule that prevented policy updates from being versioned.
- Expand agent workflow requirements with a mandatory post-push audit loop, testing matrix by change type, CI expansion policy, and per-push documentation sync protocol.
- Unify active planning into a single canonical `dev/active/MASTER_PLAN.md` and clarify that `dev/active/overlay.md` is reference market research.

## [1.0.51] - 2026-02-13

### UX

- Prevent HUD freeze (REC duration, live dB meter, queue/heartbeat status) when PTY output is continuously active by running periodic overlay tasks independently of the `select!` timeout branch.
- Render the HUD/launcher immediately on startup so users always see VoiceTerm controls without waiting for the first status update.
- Hidden HUD now shows a branded `VoiceTerm` launcher row with a clickable `open` button and `Ctrl+U` hint while idle.
- Improve terminal compatibility for controls by parsing parameterized CSI arrow sequences and additional mouse protocols (URXVT + X10, alongside SGR).
- Allow Left/Right + Enter HUD button navigation even when mouse clicking is toggled off.
- Treat HUD latency as post-capture processing time and hide the badge when metrics are incomplete instead of showing a misleading estimate.

### Diagnostics

- Add `VOICETERM_DEBUG_INPUT=1` to log raw input byte sequences and decoded input events for IDE terminal compatibility debugging.
- Add `latency_audit|...` debug log lines with displayed/capture/STT/elapsed timing fields per transcript.

### Tests

- Validate the fix with local `voiceterm` build/test checks to cover the queue + busy-output regression path.
- Add parser coverage for URXVT/X10 mouse events, partial X10 buffering, and parameterized CSI arrow sequences.
- Add hidden-HUD coverage for the idle launcher button/row behavior.
- Add unit coverage for latency calculation behavior (prefer STT timing, fallback from capture, hide when metrics are missing).

## [1.0.50] - 2026-02-09

### UX

- Buffer partial input escape sequences so SGR mouse scroll/motion does not leak into Claude output.

### Tests

- Ensure partial SGR mouse sequences are buffered across input reads.

## [1.0.49] - 2026-02-09

### UX

- Ignore non-click SGR mouse events so trackpad scroll/motion does not flood Claude output or stall the HUD timer.

### Tests

- Add an input parser check that wheel events are dropped.

## [1.0.48] - 2026-02-09

### UX

- Buffer partial PTY escape sequences so mouse reporting does not leak into Claude output.

### Tests

- Add coverage for buffering incomplete PTY escape sequences.

## [1.0.47] - 2026-02-09

### UX

- Preserve CRLF PTY output so line content is not erased during control-edit handling.

### Tests

- Cover CRLF handling for PTY control edits and PTY output capture in IPC tests.

## [1.0.46] - 2026-02-08

### Tests

- Stabilize PTY/IPC exit checks and avoid a racy token assertion.

### Chore

- Run rustfmt on test files and silence mutants-feature lint warnings.

## [1.0.45] - 2026-02-08

### Documentation

- Document `VOICETERM_NO_STARTUP_BANNER` in install and troubleshooting guides.
- Audit and refresh docs: clarify terminal injection vs backend submission, expand CLI flag coverage, and update troubleshooting/Whisper wording.
- Replace the Usage guide hero image with the logo and remove the stale hero asset.
- Address doc audit gaps: sensitivity labels, backend list, missing flags, archive links, model sizing notes, and Whisper search path notes.
- Add a version badge and Support section to the README.
- Add GitHub community files (code of conduct, issue templates, PR template).
- Add the HUD style shortcut (`Ctrl+U`) to Quick Start controls.

### CI

- Update perf/memory guard test selectors to `legacy_tui::tests` after the legacy rename.

### Tests

- Gate high-quality resampler test helpers behind feature flags to keep no-feature builds clean.
- Expand audio, IPC, and PTY coverage for cancellation, retry, and lifecycle edge cases.

## [1.0.44] - 2026-02-06

### UX

- Show the startup banner when launching via wrapper scripts; set `VOICETERM_NO_STARTUP_BANNER` to suppress it.

### Documentation

- Document `VOICETERM_NO_STARTUP_BANNER` in CLI environment variables.

## [1.0.43] - 2026-02-06

### UX

- Add `--login` to run backend CLI authentication (Codex/Claude) before launching the overlay.
- Honor backend-specific default themes when `--theme` is not provided.
- IPC mode now streams Claude output via PTY and reports transcript duration in `transcript` events.

### Diagnostics

- Add JSON structured tracing logs (default: `voiceterm_trace.jsonl` in the temp directory) when logging is enabled.

### Documentation

- Reorder README sections for readability with a Quick Nav, early Requirements, and a grouped UI Tour.
- Add the README logo asset and restore the overlay-running screenshot in the Usage guide.
- Remove outdated theme picker screenshot notes.
- Document the new `--login` flag across Quick Start, Usage, CLI flags, Install, and Troubleshooting guides.

## [1.0.42] - 2026-02-03

### UX

- Render the startup splash before raw mode and normalize line endings so the logo lines don't drift.
- Show the startup splash before launching the CLI, keep it visible for 10s, then clear before Codex starts.

### Documentation

- Add a Codex backend screenshot to the README.
- Add a Hidden HUD screenshot to the Usage guide.
- Add installer output screenshot to the Install guide.

## [1.0.40] - 2026-02-03

### UX

- Center the ASCII art logo and add a tagline with version and keyboard shortcuts underneath.
- Show the ASCII banner with tagline instead of the separate config line for wide terminals.

## [1.0.39] - 2026-02-03

### UX

- Add shiny purple ASCII art logo banner on startup (displays when terminal is ≥66 columns wide).

### Documentation

- Reformat README Whisper model setup/requirements for readability and remove the roadmap section.
- Rewrite the install guide to recommend Homebrew and clarify the install paths.
- Move Homebrew update troubleshooting steps into the troubleshooting guide and link from install.
- Remove Gemini references from user-facing docs (README, Quick Start, Usage, CLI Flags, Install, Troubleshooting).
- Reflow user guides for readability (Quick Start, Usage, CLI Flags, Troubleshooting, Whisper).

### UX

- Show the startup logo as a temporary overlay after initial CLI output (visible for at least 10s) so it does not conflict with the Codex intro panel.

## [1.0.38] - 2026-02-03

### UX

- Theme picker now supports arrow-key navigation, Enter to select, and multi-digit theme numbers.

### Documentation

- Refresh the Claude backend screenshot.

## [1.0.37] - 2026-02-03

### UX

- Add a minimal HUD back button and make overlay controls clickable (theme rows + close buttons), with more reliable mouse/tap handling.
- Right panel brackets stay dim regardless of waveform color.
- Keep last meter waveform/dB and recording duration between recordings to reduce flicker, and remove the duplicated waveform from the main row.
- Remove the left-side sensitivity dB from the full HUD row to avoid redundant readings.
- Add a Heartbeat right-panel mode that shows a subtle pulse.
- Render "Ready" in the success color in full and minimal HUD modes.
- Remove the redundant Chips right-panel mode.
- Add HUD button navigation via Left/Right arrows (when Mouse is enabled) and clean up mouse click handling.
- Add Tokyo Night and Gruvbox themes to the picker.
- Mouse control is enabled by default (toggle it off in Settings).

### Bug Fixes

- Fix latency display to avoid bottoming out at 0ms when capture timing skews.

### Documentation

- Note that mouse control is enabled by default and update theme-picker click guidance.

**Remaining audit items (future work):**

### Code Quality

- Group writer thread state into a struct to simplify redraw logic (MP-049).

### Documentation

- Simplify backend docs to Codex + Claude, mark Gemini as in works, and remove references to other AI backends.
- Clarify Whisper model selection in install/quick start docs and call out the optional `--codex` flag.

## [1.0.36] - 2026-02-02

### UX

- Stabilize the full HUD main-row layout by reserving sensitivity/duration/meter slots with dim placeholders and widening the right-side panel with a VU label to prevent flicker.

### Documentation

- Refresh hero, theme picker, settings, and recording screenshots, and add a minimal HUD screenshot.

## [1.0.35] - 2026-02-02

### Features

- Add minimal mode HUD: `--hud-style minimal` or `--minimal-hud` shows a single-line strip (e.g., `◉ AUTO · Ready`, `● REC · -55dB`).
- Add hidden mode HUD: `--hud-style hidden` keeps a blank row when idle, only shows `REC` while recording.
- Add `Ctrl+U` hotkey to cycle HUD style (Full → Minimal → Hidden) at runtime.
- Add Claude and Codex themes; default theme now follows backend when `--theme` is not set.
- Add ChatGPT theme (`--theme chatgpt`) with emerald green brand color (#10a37f).

### Bug Fixes

- Stop duplicate status-line updates from spamming repeated "Transcript ready" messages by relying on the HUD banner.

### Code Quality (Code Audit - Phase 1 Quick Wins)

- Fix potential buffer bounds panic in CSI-u sequence parsing by validating minimum length before indexing.
- Add I/O error logging for stdout write/flush operations to improve debugging.
- Optimize waveform rendering by using iterator chains instead of Vec allocations.
- Add `#[inline]` hints to hot-path functions (display_width, level_color, rms_db, peak_db).
- Add `#[must_use]` attributes to key struct/function returns to catch accidental discards.
- Pre-allocate `meter_levels` Vec with METER_HISTORY_MAX capacity to reduce clone overhead.
- Consolidate METER_HISTORY_MAX constant to `status_line.rs` (single source of truth).
- Optimize hot-path formatters (format_shortcut_colored, format_mode_indicator, format_chip, format_pulse_dots) to use push_str instead of format! macros.
- Consolidate status-line formatting helpers to reduce duplication and improve maintainability.
- Reduce oversized handle_voice_message parameter list by introducing a context struct.
- Add pre-refactor docs readiness checklist to keep README/QUICK_START/USAGE/CLI_FLAGS/INSTALL/TROUBLESHOOTING and screenshots in sync.
- Add SAFETY comments around unsafe blocks in PTY, signal, and Whisper integration code.
- Add public API docs for core modules (voice, audio, pty_session) to clarify usage.
- Document prompt tracking and transcript queue structures plus batching logic for maintainability.
- Extract timing "magic numbers" into named constants in main loop, writer thread, and voice status handling.
- Gate the manual_stop helper behind test/mutant cfg to avoid dead code in release builds.
- Standardize PTY write error messages to use a consistent prefix.
- Emit errno details for child_exec failures before exiting the PTY child process.
- Document the brief, startup-only stderr redirect used during Whisper model load.
- Remove a redundant CaptureMetrics clone in the voice capture path.
- Add a manual QA checklist for auto-voice visibility, queue flush, prompt logging, and multi-terminal runs.
- Add docstrings/comments across devctl and dev scripts to improve maintainability.
- Add an integration test covering transcript delivery into the PTY session (voice → injection path).
- Add PTY reader thread EOF/disconnect tests to cover child-exit recovery behavior.
- Add IPC event-loop integration coverage for active job/voice/auth processing.
- Add concurrency stress test coverage for parallel voice jobs via the fallback pipeline.
- Harden arrow-key parsing against index overflow when scanning input bytes.

### Documentation

- Update README + usage theme counts to 11 and note that the theme picker screenshot needs refresh.
- Document offline mutation testing workflow and new mutants.py cache/target overrides.
- Extend mutants.py summaries with top files/directories and results paths for faster triage.
- Add mutants.py matplotlib hotspot plotting (top 25% by default) with a CLI flag.
- Add devctl.py unified dev CLI for checks, mutants, mutation score, releases, and reports.
- Modularize devctl into command modules under dev/scripts/devctl/ for easier extension.
- Allow devctl status/report outputs to be piped into other CLIs via --pipe-command.
- Add devctl profiles, list command, and docs-check to enforce user-facing guide updates.
- Note mutation runs can be long; recommend overnight runs and allow Ctrl+C to stop.

## [1.0.34] - 2026-02-02

### Bug Fixes

- Drain voice capture results even while PTY output is streaming so "Processing" clears and transcripts queue/send while the CLI is busy.
- In manual mode, queue transcripts while the CLI is busy and send after prompt/idle instead of silently injecting mid-stream.
- Fix dim text appearing blurry on Coral/ANSI themes by using dark gray instead of ANSI dim attribute.

### Documentation

- Document queued transcript behavior in the usage guide and troubleshooting status messages.

### UX

- Refresh the HUD control row with button-style shortcuts: dim brackets/keys, colored labels when active.
- Clearer button labels: `^V auto/ptt` (voice mode), `^T auto/insert` (send mode).
- Recording button shows red when active, yellow when processing.
- Auto-voice button shows blue when listening, dim when push-to-talk.
- Send mode button shows green for auto-send, yellow for insert mode.
- All button colors are theme-aware and match the current theme palette.
- Add a right-side HUD panel (Ribbon/Dots/Chips) with a recording-only animation toggle in Settings.

## [1.0.33] - 2026-02-02

### Reorganization

- Major codebase reorganization: `rust_tui/` → `src/`, `docs/` → `guides/` + `dev/`
- Rename Rust crate from `rust_tui` to `voiceterm` to match project name
- Add Makefile for common developer commands
- Add `dev/scripts/mutants.py` for interactive mutation testing

### Bug Fixes

- Fix macOS app launcher breaking on paths containing apostrophes
- Fix Homebrew formula paths after repo reorganization
- Add explicit platform detection to setup and start scripts (macOS, Linux, Windows WSL2)
- Align macOS app version metadata with the 1.0.33 release

### UX

- Status banner top border now shows a VoiceTerm label with theme-matched Vox/Term colors instead of the theme name

### Documentation

- Add `guides/WHISPER.md` for model selection guidance
- Add platform support table to installation docs
- Fix manual hotkeys in terminals that emit CSI-u key sequences (Ctrl+R/Ctrl+V/etc).
- Retry PTY writes on would-block errors so transcript injection is reliable under load.
- In manual mode, send transcripts immediately instead of waiting on prompt detection.
- Avoid auto-voice status flicker on empty captures; only surface dropped-frame notes.
- Skip duplicate startup banners when launched from wrapper scripts.
- Use ANSI save/restore for status redraws and improve themed banner background alignment.
- Reserve terminal rows for the status banner/overlays so CLI output no longer overlaps the HUD.
- Clear banner rows on every redraw to prevent stacked ghost lines after scrolling.
- Lower the default VAD threshold to -55 dB to improve voice detection on quieter mics.
- Suppress the auto-voice "Listening" status message so the meter display stays clean.
- Add a settings overlay with arrow-key navigation and button-style controls.
- Move pipeline labeling into the recording tag and shorten status labels to "Rust"/"Python".
- Use combined ANSI/DEC cursor save/restore to keep the input cursor stable across overlays.
- Fill the status banner background across the full row to avoid uneven tinting.
- Make Nord theme HUD backgrounds transparent to avoid a washed-out look on dark terminals.
- Automatically disable HUD background fills in Warp terminals to prevent black bars behind text.
- Restore cursor attributes after HUD draws to keep CLI colors intact.
- Show settings/help hints in the HUD idle message and overlay footers.
- Fix documentation links and dev test script paths after repo reorg (guides/dev).
- Align Homebrew tap instructions and CI workflow references with the new repo layout.

## [1.0.32] - 2026-02-02

### Bug Fixes

- Fix overlay border alignment in theme picker, settings, and help overlays.
- Fix Unicode character width calculations in overlay title lines.
- Remove background color applications from status line for transparent rendering.
- Simplify settings footer text to avoid Unicode width issues.

## [1.0.31] - 2026-02-02

### Bug Fixes

- Fix theme picker border alignment where right border extended too far.
- Fix status banner background color bleeding outside the box on themed overlays (Nord, etc.).
- Fix top border width calculation in status banner.

## [1.0.30] - 2026-02-02

### Branding (Breaking)

- Rename the project to VoiceTerm across the CLI, docs, and UI strings.
- New primary command: `voiceterm`.
- New env var prefix: `VOICETERM_*`.
- New config path: `~/.config/voiceterm/`.
- New model path: `~/.local/share/voiceterm/models`.
- New log files: `voiceterm_tui.log` and `voiceterm_crash.log`.
- macOS app renamed to `VoiceTerm.app`.

### Privacy

- Avoid logging full panic details to the debug log unless `--log-content` is enabled.

### UX

- Refresh the startup banner styling and show backend/theme/auto state.

## [1.0.29] - 2026-02-02

### Reliability

- Add a terminal restore guard with a shared panic hook so raw mode/alternate screen clean up even on crashes.
- Emit a minimal crash log entry (metadata only unless log content is enabled).
- Add `--doctor` diagnostics output for terminal/config/audio visibility.
- Clear overlay panel regions when the height changes to avoid resize artifacts.
- Improve queued transcript flushing by allowing idle-based sends when prompt detection stalls after output finishes.

## [1.0.28] - 2026-01-31

### UX + Visuals

- Theme picker overlay (Ctrl+Y) with numbered selection.
- Live waveform + dB meter during recording in the status line.
- Transcript preview snippet shown briefly after transcription.
- Help/status shortcuts refreshed; overlay panels follow the active theme.
- Compact HUD modules now surface queue depth and last capture latency when available.

### Audio Feedback

- Optional notification sounds: `--sounds`, `--sound-on-complete`, `--sound-on-error`.

### CLI

- New `--backend` flag for selecting Codex/Claude/Gemini/Aider/OpenCode or a custom command (defaults to Codex).
- Backend-specific prompt patterns are used when available; Codex continues to auto-learn prompts by default.
- `--backend` custom commands now accept quoted arguments.

### Docs

- Updated usage, quick start, CLI flags, README, install, troubleshooting, and architecture/development docs to match the new options.

## [1.0.27] - 2026-01-31

### UX + Visuals

- Launcher now lists `?` help and theme flags in the startup tables.
- Launcher now documents available themes and `--no-color`.

### Docs

- Architecture doc now includes the overlay visual system components.
- Added modularization audit plan doc for historical tracking.

## [1.0.26] - 2026-01-31

### UX + Visuals

- **Overlay status line**: structured layout with mode/pipeline/sensitivity, themed colors, and automatic ANSI fallback.
- **Help overlay**: press `?` to show the shortcut panel (any key closes it).
- **Startup banner**: display version + config summary on launch.
- **Mic meter**: `--mic-meter` now renders a visual bar display alongside the suggested threshold.
- **Session summary**: print transcript/session stats on exit when activity is present.

### CLI

- **New flags**: `--theme` (coral/catppuccin/dracula/nord/ansi/none) and `--no-color`.
- **NO_COLOR support**: standard env var disables colors in the overlay.

### Fixes

- Status line refreshes when state changes even if the message text stays the same.
- Truncated status messages keep their original indicator/color for consistent meaning.
- Help overlay rendering clamps to terminal height to avoid scrolling in small terminals.

## [1.0.25] - 2026-01-29

### Docs

- Refresh README messaging, requirements, and controls summary for clearer onboarding.
- Reorganize README navigation and contributing links for a tighter user/developer split.
- Document the release review location in `dev/DEVELOPMENT.md` and update master plan source inputs.

## [1.0.24] - 2026-01-29

### Build + Release

- **Version bump**: update `rust_tui/Cargo.toml` to 1.0.24 and align `VoiceTerm.app` Info.plist.

### Refactor

- **Rust modularization**: split large modules (`ipc`, `pty_session`, `codex`, `audio`, `config`, `app`, and overlay helpers) into focused submodules with tests preserved.
- **Test access**: keep test-only hooks and visibility intact to avoid mutation/test regressions.

### Docs

- **Doc layout sync**: update architecture/development/visual docs to match the new module layout.
- **Active plan**: mark the modularization plan complete and document the post-split layout.
- **Policy links**: align SDLC/changelog references and backlog paths for consistent navigation.

## [1.0.23] - 2026-01-29

### Docs

- **README layout**: move macOS app (folder picker) section below UI modes.
- **macOS app version**: align `VoiceTerm.app` Info.plist to 1.0.23.
- **Auto-voice status copy**: clarify that "Auto-voice enabled" means auto-voice is on while idle.
- **Usage guidance**: tighten wording for mode selection and long-dictation tips.
- **Usage layout**: add a mode matrix table that shows how listening and send modes combine.
- **Usage modes**: consolidate voice mode details into a single chart and move long-dictation notes into the same section.
- **Usage notes**: add prompt-detection fallback and Python fallback behavior notes.
- **Usage polish**: add a contents list, fix Quick Start wording, and include a `--lang` example.
- **Troubleshooting layout**: reorganize sections to reduce repetition and improve scanability.
- **Docs structure**: move dev docs under `docs/dev` and active plans under `dev/active` (update links).
- **Troubleshooting links**: make Quick Fixes entries clickable jump links.
- **Docs navigation**: add contents lists to README and Install docs.
- **CLI flags accuracy**: correct prompt log defaults and voice silence tail default.
- **ADR tracking**: keep ADRs under `dev/adr` and track them in git.
- **Backlog cleanup**: remove duplicate queue item and normalize headings.
- **Dev docs navigation**: add contents lists to architecture, development, and modularization docs.
- **Docs formatting**: replace em dashes with hyphen separators for consistency.
- **SDLC policy**: move policy to `docs/dev/SDLC.md` and point the changelog at a tracked file.
- **Repo hygiene**: add `LICENSE`, `CONTRIBUTING.md`, and `SECURITY.md`.
- **README badges**: add CI, perf, memory guard, mutation testing, and license badges.
- **Docs navigation**: add "See Also" tables to install, CLI flags, and troubleshooting docs.
- **Dev docs**: expand contribution workflow, code style, and testing philosophy guidance.
- **Legacy CLI docs**: clarify deprecated status and mark quick start as non-functional.

## [1.0.22] - 2026-01-29

### Docs

- **macOS app visibility**: restore the folder-picker app path in README/Quick Start/Install docs.
- **macOS app version**: align `VoiceTerm.app` Info.plist to 1.0.22.

## [1.0.21] - 2026-01-29

### Build + Release

- **Whisper crates compatibility**: align `whisper-rs` to the latest compatible 0.14.x release to avoid `links = "whisper"` conflicts.
- **Status redraw refactor**: reduce argument fanout in the overlay status redraw helper (clippy clean).
- **macOS app version**: align `VoiceTerm.app` Info.plist to 1.0.21.

## [1.0.20] - 2026-01-29

### UX + Controls

- **Auto-voice startup**: auto mode now begins listening immediately when enabled (no silent wait).
- **Auto-voice status**: keep "Auto-voice enabled" visible on startup and when toggling on.
- **Status line stability**: defer status redraws until output is quiet to prevent ANSI garbage in the prompt.
- **Insert-mode rearm**: auto-voice re-arms immediately after transcripts when using insert send mode.
- **Capture limit**: max configurable capture duration raised to 60s (default still 30s).
- **Sensitivity hotkey alias**: `Ctrl+/` now also decreases mic sensitivity (same as `Ctrl+\`).
- **Transcript queueing**: once a prompt is detected, transcripts now wait for the next prompt instead of auto-sending on idle.
- **Prompt detection**: default prompt detection now auto-learns the prompt line (no default regex).

### Reliability + Privacy

- **Logging opt-in**: debug logs are disabled by default; enable with `--logs` (add `--log-content` for prompt/transcript snippets).
- **Prompt log opt-in**: prompt detection logs are disabled by default unless `--prompt-log` is set.
- **Log caps**: debug and prompt logs now rotate to avoid unbounded growth.
- **Buffer caps**: overlay input/writer channels, PTY combined output, and TUI input buffers are bounded.
- **Queue safety**: transcript queue drops now warn in the status line.
- **Security hardening**: `--claude-cmd` is sanitized; `--claude-skip-permissions` is configurable.

### Whisper + Audio

- **VAD smoothing**: new `--voice-vad-smoothing-frames` reduces flapping in noisy rooms.
- **Silence tail default**: reduced to 1000ms for lower latency.
- **Whisper tuning**: added `--lang auto`, `--whisper-beam-size`, and `--whisper-temperature`.
- **Capture metrics**: dropped audio frames are surfaced in the status line when present.

### Tests

- **New coverage** for mic meter calculations, STT error paths, UI input handling, transcript queue drop/flush, and config validation.

### Docs

- **README refresh**: streamlined quick start and moved deep sections into focused docs.
- **New guides**: added install, usage, CLI flags, troubleshooting, and development docs.
- **CLI flags**: consolidated into a single doc with voiceterm and rust_tui sections, plus missing flags and log env vars.

## [1.0.19] - 2026-01-29

### Changes

- **Transcript flush**: queued transcripts now auto-send after a short idle period (not just on prompt).
- **Queue merge**: queued transcripts are merged into a single message when flushed.
- **New flag**: `--transcript-idle-ms` controls the idle threshold for transcript auto-send.
- **CSI-u handling**: input parser now properly drops CSI-u sequences (avoids garbage text in the prompt).

## [1.0.17] - 2026-01-29

### Fixes

- **Auto-voice status spam**: avoid repeated status updates on empty captures.
- **Transcript queue**: only advances prompt gating when a newline is sent (fixes stuck queues in insert mode).
- **Prompt detection**: default regex `^>\\s?` to match Codex prompt reliably.
- **Status dedupe**: avoid re-sending identical status lines.

## [1.0.16] - 2026-01-29

### Changes

- **Binary rename**: `voiceterm` is now the only user-facing command (no `codex-overlay`).
- **Prompt log path**: configured via `--prompt-log` or `VOICETERM_PROMPT_LOG` (no default unless set).
- **Env cleanup**: Legacy overlay prompt env vars are no longer supported; use `VOICETERM_PROMPT_*`.
- **Docs/scripts**: update build/run instructions to use `voiceterm`.

## [1.0.15] - 2026-01-29

### Fixes

- **Overlay build fix**: remove stray duplicate block that broke compilation in `voiceterm` (source: `src/bin/voiceterm/`).

## [1.0.14] - 2026-01-29

### UX + Controls

- **Sensitivity hotkeys**: `Ctrl+]` / `Ctrl+\` adjust mic sensitivity (no Ctrl++/Ctrl+-).
- **Mic meter mode**: add `--mic-meter` plus ambient/speech duration flags to recommend a VAD threshold.
- **Startup/README updates**: refresh shortcut and command hints to match the new bindings.
- **Transcript queue**: when Codex is busy, transcripts are queued and sent on the next prompt; status shows queued count.

## [1.0.13] - 2026-01-28

### Build Fixes

- **Clippy clean**: resolve lint warnings across audio, codex, IPC, and PTY helpers for a clean CI run.

## [1.0.12] - 2026-01-28

### Testing & Reliability

- **Mutation coverage expansion**: add test hooks and integration tests across PTY, IPC, Codex backend, and overlay paths.
- **Overlay input/ANSI handling**: refactor input parsing and ANSI stripping for more robust control-sequence handling.
- **Audio pipeline hardening**: refactor recorder module and tighten resample/trimming behavior for stability.

## [1.0.11] - 2026-01-28

### Testing & Quality

- **Mutation coverage improvements**: expand PTY session tests and internal counters to harden mutation kills.
- **Mutation CI threshold**: mutation-testing workflow now enforces an 80% minimum score.

## [1.0.10] - 2026-01-25

### Build Fixes

- **Mutation testing baseline**: create a stub pipeline script during tests when the repo root is not present.

## [1.0.9] - 2026-01-25

### Build Fixes

- **Clippy cleanup in voiceterm**: resolve collapsible-if, map_or, clamp, and question-mark lints under `-D warnings` (source: `src/bin/voiceterm/`).

## [1.0.8] - 2026-01-25

### Build Fixes

- **SIGWINCH handler type**: cast the handler to `libc::sighandler_t` to satisfy libc 0.2.180 on Unix.
- **CI formatting cleanup**: apply `cargo fmt` so the rust-tui workflow passes.

## [1.0.7] - 2026-01-25

### Build Fixes

- **AtomicBool import for VAD stop flag**: fixes CI builds when high-quality-audio is disabled.

## [1.0.6] - 2026-01-25

### Auto-Voice Behavior

- **Silence no longer stops auto-voice**: empty captures immediately re-arm instead of waiting for new PTY output.
- **Less UI noise on silence**: auto mode keeps a simple "Auto-voice enabled" status instead of spamming "No speech detected".

## [1.0.5] - 2026-01-25

### Voice Capture UX Fixes

- **Insert-mode Enter stops early**: pressing Enter while recording now stops capture and transcribes the partial audio.
- **Processing status stays visible** until transcription completes or an error/empty result arrives.
- **Auto-voice cancel is real**: disabling auto-voice (Ctrl+V) now stops the active capture instead of dropping the handle.
- **Python fallback cancel**: Enter in insert mode cancels the python fallback capture (no partial stop available).
- **LF/CRLF Enter support**: terminals sending LF or CRLF now trigger the Enter interception reliably.

### Error Handling

- **Manual stop with no samples** returns an empty transcript instead of a fallback error.

## [1.0.4] - 2026-01-25

### Fast Local Transcription Feature

- **Benchmarked STT latency**: ~250ms processing after speech ends (tested with real microphone input).
- **Added feature to README**: "Fast local transcription - ~250ms processing after speech ends, no cloud API calls".
- **Verified code path**: latency_measurement binary uses identical code path as voiceterm (same voice::start_voice_job → stt::Transcriber).

### Bug Fixes

- **Filter [BLANK_AUDIO]**: Whisper's `[BLANK_AUDIO]` token is now filtered from transcripts, preventing spam in auto-voice mode when user stops talking.
- **Mermaid diagram**: Converted ASCII "How It Works" diagram to proper Mermaid flowchart for GitHub rendering.

## [1.0.3] - 2026-01-25

### UI Styling Refresh

- **Modern TUI styling**: rounded borders, vibrant red theme, bold titles in Rust overlay.
- **Startup tables refresh**: Unicode box-drawing characters, matching red theme.
- **Updated banner**: accurate description - "Rust overlay wrapping Codex CLI / Speak to Codex with Whisper STT".
- **README screenshot**: added startup screenshot to img/startup.png.

### Startup UX Polish (2026-01-24) - COMPLETE

- **VoiceTerm banner**: `start.sh` now uses the Rust launch banner from the legacy CLI.
- **Compact quickstart tables**: launch output shows quick controls + common commands in green tables.
- **Adaptive layout**: smaller banner + dual-color columns keep tables visible in shorter terminals.
- **Startup output test**: `scripts/tests/startup_output_test.sh` guards line widths.

### Simplified Install Flow (2026-01-23) - COMPLETE

- **New installer**: added `scripts/install.sh` plus `scripts/setup.sh install` to download the Whisper model, build the Rust overlay, and install a `voiceterm` wrapper.
- **Overlay-first defaults**: `scripts/setup.sh` now defaults to `install` so it builds the Rust overlay by default.
- **Docs updated**: README + QUICK_START now point to `./scripts/install.sh` and `voiceterm` for the simplest path.

### Rust-Only Docs + Launchers (2026-01-23) - COMPLETE

- **Docs sweep**: removed legacy CLI references from user-facing docs and the audit.
- **Launchers aligned**: `start.sh` and `scripts/setup.sh` now run overlay-only; Windows launcher points to WSL/macos/linux.
- **Backlog tracking**: follow-up work and open UX items are tracked in `dev/active/MASTER_PLAN.md`.

### Overlay UX (2026-01-23) - COMPLETE

- **New hotkeys**: Ctrl+T toggles send mode (auto vs insert), Ctrl++/Ctrl+- adjust mic sensitivity in 5 dB steps.
- **Startup hints**: `start.sh` prints the key controls and common flag examples for non-programmers.

### Homebrew Runtime Fixes (2026-01-23) - COMPLETE

- **Prebuilt overlay reuse**: `start.sh` now uses `voiceterm` from PATH when available, skipping builds in Homebrew installs.
- **User-writable model storage**: model downloads fall back to `~/.local/share/voiceterm/models` when the repo/libexec is not writable.
- **Homebrew detection**: Homebrew installs always use the user model directory instead of libexec, even if libexec is writable.
- **Install wrapper safety**: skip existing global `voiceterm` commands and prefer safe locations unless overridden.

### Rust Overlay Mode + Packaging (2026-01-22) - COMPLETE

- **Added Rust overlay mode**: new `voiceterm` binary runs Codex in a PTY, forwards raw ANSI output, and injects voice transcripts as keystrokes.
- **Prompt-aware auto-voice**: prompt detection with idle fallback plus configurable regex overrides for auto-voice triggering.
- **Serialized output writer**: PTY output + status line rendering go through a single writer thread to avoid terminal corruption.
- **PTY passthrough improvements**: new raw PTY session that answers DSR/DA queries without stripping ANSI.
- **Resizing support**: SIGWINCH handling updates PTY size and keeps the overlay stable.
- **Startup/launcher updates**: `start.sh` now defaults to overlay, ensures a Whisper model exists, and passes `--whisper-model-path`; macOS app launcher now uses overlay mode.
- **Docs refresh**: new `ARCHITECTURE.md` with detailed Rust-only diagrams and flows; README expanded with install paths, commands, and Homebrew instructions.
- **Repo hygiene**: internal architecture/archive/reference directories are now ignored by git and removed from the tracked set.

### Project Cleanup + macOS Launcher (2026-01-11) - COMPLETE

- **Added macOS app launcher**: `VoiceTerm.app` now in repo alongside `start.sh` and `start.bat` for cross-platform consistency.
- **Major project structure cleanup**:
  - Removed duplicate files from `rust_tui/` (CHANGELOG, docs/, screenshots, etc.)
  - Moved rust_tui test scripts to `rust_tui/scripts/`
  - Consolidated scripts: deleted redundant launchers (`run_tui.sh`, `launch_tui.py`, `run_in_pty.py`)
  - Moved benchmark scripts to `scripts/tests/`
  - Deleted legacy folders (`stubs/`, `tst/`)
  - Kept `voiceterm.py` as legacy Python fallback
- **Updated all README diagrams** to match actual project structure.
- **Updated .gitignore** to exclude internal dev docs (`PROJECT_OVERVIEW.md`, `agents.md`, etc.)
- **Fixed Cargo.toml** reference to deleted test file.
- **82 Rust tests passing**.

### PTY Readiness + Auth Flow (2026-01-11) - COMPLETE

- **PTY readiness handshake**: wait for initial output and fail fast when only control output appears, preventing 20-30s stalls on persistent sessions.
- **/auth login flow**: new IPC command + wrapper command runs provider login via /dev/tty, with auth_start/auth_end events and raw mode suspension in TS.
- **Output delivery fix**: Codex Finished output is delivered even if the worker signal channel disconnects.
- **CI/testing updates**: added `mutation-testing.yml` and extended integration test coverage for the auth command.

### Provider-Agnostic Backend + JSON IPC (2026-01-10) - COMPLETE

- **Implemented provider-agnostic backend**: `rust_tui/src/ipc.rs` rewritten with non-blocking event loop, supporting both Codex and Claude CLIs with full slash-command parity.
- **IPC client flow functional**: JSON IPC supports voice capture, provider switching, and full event streaming.
- **Rust IPC mode**: `--json-ipc` flag enables JSON-lines protocol with capability handshake on startup.
- **All critical bugs fixed**:
  - IPC no longer blocks during job processing (stdin reader thread)
  - Codex/Claude output streams to IPC clients
  - Ctrl+R wired for voice capture (raw mode)
  - Unknown `/` commands forwarded to provider
- **New features**:
  - Capability handshake with full system info (`capabilities` event)
  - Session-level provider switching (`/provider claude`)
  - One-off provider commands (`/codex <prompt>`, `/claude <prompt>`)
  - Setup script for Whisper model download (`scripts/setup.sh`)
- **Test coverage**:
  - 18 unit tests for provider routing and IPC protocol
  - 12 integration tests for end-to-end flow
  - All tests passing

### CRITICAL - Phase 2B Design Correction (2025-11-13 Evening)

- **Rejected original Phase 2B "chunked Whisper" proposal (Option A)** after identifying fatal architectural flaw: sequential chunk transcription provides NO latency improvement (capture + Σchunks often slower than capture + single_batch). Original proposal would have wasted weeks implementing slower approach.
- **Documented corrected design** in the internal architecture archive (2025-11-13), specifying streaming mel + Whisper FFI architecture (Option B) as only viable path to <750ms voice latency target. User confirmed requirement: "we need to do option 2 i want it to be responsive not slow".
- **Design includes:** Three-worker parallel architecture (capture/mel/stt), streaming Whisper FFI wrapper, fallback ladder (streaming→batch→Python), comprehensive measurement gates, 5-6 week implementation plan, and mandatory approval gates before any coding begins.
- **Measurement gate executed:** Recorded 10 end-to-end Ctrl+R→Codex runs (short/medium commands) and captured results in the internal architecture archive (2025-11-13). Voice pipeline averages 1.19 s, Codex averages 9.2 s (≈88 % of total latency), so Phase 2B remains blocked until Codex latency is addressed or stakeholders explicitly accept the limited ROI.
- **Codex remediation plan:** Authored the Codex latency plan in the internal architecture archive (2025-11-13), covering telemetry upgrades, PTY/CLI health checks, CLI profiling, and alternative backend options. Phase 2B remains gated on executing this plan and obtaining stakeholder approval.
- **Persistent PTY fix:** Health check now waits 5 s and only verifies the child process is alive (no synthetic prompts), so conversations start clean and persistent sessions stay responsive. Python helper path was removed; persistent mode is pure Rust. Next Codex task is streaming output so the UI shows tokens as they arrive.
- **Next steps:** (1) Address Codex latency or approve proceeding despite the bottleneck, (2) Decide between local streaming (Option B) vs. cloud STT vs. deferral, (3) Confirm complexity budget (5–6 weeks acceptable), (4) Only after approvals resume Phase 2B work.

### Added

- Completed the Phase 2A recorder work: `FrameAccumulator` maintains bounded frame buffers with lookback-aware trimming, `CaptureMetrics` now report `capture_ms`, and perf smoke parses the real `voice_metrics|…` log lines emitted by `voice.rs`.
- Added `CaptureState` helpers plus unit tests covering max-duration timeout, min-speech gating, and manual stop semantics so recorder edge cases stay regression-tested.
- Phase 2A scaffolding: introduced the `VadEngine` trait, Earshot feature gating, and a fallback energy-based VAD so recorder callers can swap implementations without API churn.
- Runtime-selectable VADs: new `--voice-vad-engine <earshot|simple>` flag (documented in `docs/references/quick_start.md`), validation, and `VoicePipelineConfig` plumbing so operators can pick Earshot (default when the feature is built) or the lightweight threshold fallback without touching source code.
- Added the `vad_earshot` optional dependency/feature wiring in `Cargo.toml` together with the new `rust_tui/src/vad_earshot.rs` adapter.
- Updated the voice pipeline to call `Recorder::record_with_vad`, log per-utterance metrics, and honor the latency plan’s logging/backpressure rules.
- Introduced the async Codex worker module (`rust_tui/src/codex.rs`) plus the supporting test-only job hook harness so Codex calls can run off the UI thread and remain unit-testable without shelling out.
- Documented the approved Phase 1 backend plan (“Option 2.5” event-stream refactor) in the internal architecture archive (2025-11-13), capturing the Wrapper Scope Correction + Instruction blocks required before touching Codex integration.
- Added perf/memory guard rails: `app::tests::{perf_smoke_emits_timing_log,memory_guard_backend_threads_drop}` together with `.github/workflows/perf_smoke.yml` and `.github/workflows/memory_guard.yml` so CI enforces telemetry output and backend thread cleanup.
- Implemented the Phase 1 backend refactor: `CodexJobRunner`/`CodexJob` abstractions with bounded queues, `CodexCliBackend` PTY ownership, App wiring to Codex events, and new queue/tests (`cargo test --no-default-features`).
- Benchmark harness for Phase 2A: `audio::offline_capture_from_pcm`, the `voice_benchmark` binary, and `scripts/benchmark_voice.sh` capture deterministic short/medium/long clip metrics that feed the capture_ms SLA (internal benchmark notes live in the 2025-11-13 archive).

### Changed

- Replaced the `Recorder::record_with_vad` stub (non-test builds) with the new chunked capture loop (bounded channel + VAD decisions + metrics) ahead of the perf_smoke gate.
- `App`/`ui` now spawn Codex work asynchronously, render a spinner with Esc/Ctrl+C cancellation, and log `timing|phase=codex_job|...` metrics; `cargo test --no-default-features` gates the new worker while the `earshot` crate remains offline.
- Corrected the Earshot profile mapping (`rust_tui/src/vad_earshot.rs`) and fixed the Rubato `SincFixedIn` construction (`rust_tui/src/audio.rs`) so the high-quality resampler runs cleanly instead of spamming “expected 256 channels” and falling back on every frame.
- Introduced an explicit redraw flag in `App` plus a simplified `ui.rs` loop so job completions and spinner ticks refresh the TUI automatically; recordings/transcripts now appear without requiring stray keypresses while still capping idle redraws.
- Tightened the persistent Codex PTY timeout (2 s to first printable output, 10 s overall) so we fall back to the CLI path quickly when the helper is silent, eliminating the 30–45 s per-request stall.
- Resolved the remaining clippy warnings by introducing `JobContext`, simplifying queue errors, modernizing format strings, and gating unused imports; `cargo clippy --no-default-features` now runs clean.

### Fixed

- Restored the missing atomic `Ordering` import under all feature combinations (`rust_tui/src/audio.rs`) and removed the redundant crate-level cfg guard from `rust_tui/src/vad_earshot.rs`, unblocking `cargo clippy --all-features` and `cargo test --no-default-features`.
- Codex backend module once again satisfies `cargo fmt`: moved the `#[cfg(test)]` attribute ahead of the gated `AtomicUsize` import (`rust_tui/src/codex.rs`) to follow Rust formatting rules.
- GitHub Actions Linux runners now install ALSA headers before running our audio-heavy tests (`.github/workflows/perf_smoke.yml`, `.github/workflows/memory_guard.yml`), fixing the `alsa-sys` build failures on CI.
- `voice_benchmark` now validates `--voice-vad-engine earshot` against the `vad_earshot` feature via the new `ensure_vad_engine_supported` helper plus clap-based unit tests, preventing the `unreachable!()` panic the reviewer observed when the benchmark binary is compiled without the feature flag.

### Known Issues

- `cargo check`/`test` cannot download the `earshot` crate in this environment; run the builds once network access is available to validate the new code paths.

## [2025-11-12]

### Added

- Established baseline governance artifacts: `master_index.md`, repository `CHANGELOG.md`, root `PROJECT_OVERVIEW.md` (planned updates), and the initial dated architecture folder in the internal archive.
- Consolidated legacy documentation into the daily architecture tree (internal archive), the references set, and audits; backfilled the original architecture overview into the internal archive (2025-11-11).
- Relocated root-level guides (`ARCHITECTURE.md`, `MASTER_DOC.md`, `plan.md`) into the internal references set, corrected the historical architecture baseline to the internal archive (2025-11-11), and updated navigation pointers accordingly.
- Updated the new references (`quick_start.md`, `testing.md`, `python_legacy.md`) to reflect the current Rust pipeline (Ctrl+R voice key, `cargo run` workflow, native audio tests) and annotated the legacy plan in `dev/archive/MVP_PLAN_2024.md`.
- Added a concise root `README.md`, introduced the “You Are Here” section in `PROJECT_OVERVIEW.md`, renamed `docs/guides/` → `docs/references/` (`quick_start.md`, `testing.md`, `python_legacy.md`, `milestones.md`, `troubleshooting.md`), and archived superseded guides under `dev/archive/OBSOLETE_GUIDES_2025-11-12/`.
- Updated helper scripts (`rust_tui/test_performance.sh`, `test_voice.sh`, `simple_test.sh`, `final_test.sh`) to rely on `cargo run`, Ctrl+R instructions, and the shared `${TMPDIR}/voiceterm_tui.log`.
- Extended `agents.md` with an end-of-session checklist so every workday records architecture notes, changelog entries, and the “You Are Here” pointer.
- Consolidated the CI/CD references into a single `docs/references/cicd_plan.md`, merging the previous implementation + dependency guides and archiving the superseded files under `dev/archive/OBSOLETE_REFERENCES_2025-11-12/`.
- Expanded `docs/references/cicd_plan.md` with appendices covering phase-by-phase scripts, tooling/dependency matrices, rollback/cost controls, and troubleshooting so it fully supersedes the archived references.
- Captured the latency remediation plan in `docs/audits/latency_remediation_plan_2025-11-12.md` and updated `PROJECT_OVERVIEW.md` to prioritize latency stabilization workstreams ahead of module decomposition and CI enhancements.
- Strengthened the latency plan with explicit Phase 2A/2B/3 naming, backpressure/frame/shutdown/fallback policies, and structured tracing + CI perf gate requirements so phase execution is unambiguous.
- Added production-grade detail to the latency plan: failure hierarchy, VAD safety rails, bounded resource budgets, observability schema, CI enforcement hooks, and a 15-day execution timeline.
- Updated `agents.md` so the latency requirements explicitly point to the Phase 2B specification (`docs/audits/latency_remediation_plan_2025-11-12.md`) and mandate adherence to the new resource/observability/CI rules.
- Documented the state machine, config/deployment profiles, and concurrency guardrails inside the latency plan so downstream work follows the same lifecycle semantics.
- Hardened `agents.md` with Scope/Non-goals, "Before You Start" instructions, condensed voice requirements referencing the latency plan, explicit doc-update rules, and a prominent end-of-session checklist.
- Recorded the readiness audit (`docs/audits/READINESS_AUDIT_2025-11-12.md`), summarized its findings in the architecture log, and captured the Phase 2A design (Earshot VAD, config surface, metrics, exit criteria) plus the immediate task list (perf_smoke CI, Python feature flag, module decomposition planning).

See `docs/audits/latency_remediation_plan_2025-11-12.md` for the complete latency specification.
