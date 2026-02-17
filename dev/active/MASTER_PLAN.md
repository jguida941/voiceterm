# Master Plan (Active, Unified)

## Canonical Plan Rule

- This file is the single active plan for strategy, execution, and release tracking.
- `dev/active/overlay.md` is reference research only (market/competitor + UX audit), not an execution plan.
- Deferred work lives in `dev/deferred/` and must be explicitly reactivated here before implementation.

## Status Snapshot (2026-02-17)

- Last tagged release: `v1.0.70` (2026-02-17)
- Current release target: `TBD` (next post-`v1.0.70` target pending planning sync)
- Active development branch: `develop`
- Release branch: `master`
- Strategic focus: mutation-hardening execution to keep `mutation-testing` green at `>=0.80` while executing a visual-surface-first Theme Studio track.

## Strategic Direction

- Protect current moat: terminal-native PTY orchestration, prompt-aware queueing, local-first voice flow.
- Close trust gap: latency metrics must match user perception and be auditable.
- Build differentiated product value in phases:
  1. Visual-first UX pass (telemetry, motion, layout polish, theme ergonomics)
  2. Workflow differentiators (voice navigation, history, CLI workflow polish)
  3. Theme-systemization (visual surfaces first, then full Theme Studio control parity)
  4. Advanced expansion (streaming STT, tmux/neovim, accessibility)

## Phase 0 - Completed Release Stabilization (v1.0.51-v1.0.52)

- [x] MP-072 Prevent HUD/timer freeze under continuous PTY output.
- [x] MP-073 Improve IDE terminal input compatibility and hidden-HUD discoverability.
- [x] MP-074 Update docs for HUD/input behavior changes and debug guidance.
- [x] MP-075 Finalize latency display semantics to avoid misleading values.
- [x] MP-076 Add latency audit logging and regression tests for displayed latency behavior.
- [x] MP-077 Run release verification (`cargo build --release --bin voiceterm`, tests, docs-check).
- [x] MP-078 Finalize release notes, bump version, tag, push, GitHub release, and Homebrew tap update.
- [x] MP-096 Expand SDLC agent governance: post-push audit loop, testing matrix by change type, CI expansion policy, and per-push docs sync requirements.
- [x] MP-099 Consolidate overlay research into a single reference source (`dev/active/overlay.md`) and mirror candidate execution items in this plan.

## Phase 1 - Latency Truth and Observability

- [x] MP-079 Define and document latency terms (capture, STT, post-capture processing, displayed HUD latency).
- [x] MP-080 Hide latency badge when reliable latency cannot be measured.
- [x] MP-081 Emit structured `latency_audit|...` logs for analysis.
- [x] MP-082 Add automated tests around latency calculation behavior.
- [x] MP-097 Fix busy-output HUD responsiveness and stale meter/timer artifacts (settings lag under Codex output, stale REC duration/dB after capture, clamp meter floor to stable display bounds).
- [x] MP-098 Eliminate blocking PTY input writes in the overlay event loop so queued/thinking backend output does not stall live typing responsiveness.
- [x] MP-083 Run and document baseline latency measurements with `latency_measurement` and `dev/scripts/tests/measure_latency.sh` (`dev/archive/2026-02-13-latency-baseline.md`).
- [x] MP-084 Add CI-friendly synthetic latency regression guardrails (`.github/workflows/latency_guard.yml` + `measure_latency.sh --ci-guard`).
- [x] MP-111 Add governance hygiene automation for archive/ADR/script-doc drift (`python3 dev/scripts/devctl.py hygiene`) and codify archive/ADR lifecycle policy.
- [x] MP-122 Prevent mutation-lane timeout by sharding scheduled `cargo mutants` runs and enforcing one aggregated score across shards.

## Phase 2 - Overlay Quick Wins

- [x] MP-085 Voice macros and custom triggers (`.voiceterm/macros.yaml`).
- [x] MP-086 Runtime macros ON/OFF toggle (settings state + transcript transform gate).
- [x] MP-087 Restore baseline send-mode semantics (`auto`/`insert`) without an extra review-first gate.
- [x] MP-112 Add CI voice-mode regression lane for macros-toggle and send-mode behavior (`.github/workflows/voice_mode_guard.yml`).
- [ ] MP-088 Persistent user config (`~/.config/voiceterm/config.toml`) for core preferences (deferred until visual sprint is complete).

## Phase 2A - Visual HUD Sprint (Current Priority)

- [x] MP-101 Add richer HUD telemetry visuals (sparkline/chart/gauge) with bounded data retention.
- [x] MP-100 Add animation transition framework for overlays and state changes (TachyonFX or equivalent).
- [x] MP-054 Optional right-panel visualization modes in minimal HUD.
- [x] MP-105 Add adaptive/contextual HUD layouts and state-driven module expansion.
- [x] MP-113 Tighten startup splash ergonomics and IDE compatibility (shorter splash duration, reliable teardown in IDE terminals, corrected startup tagline centering, and better truecolor detection for JetBrains-style terminals).
- [x] MP-114 Polish startup/theme UX in IDE terminals (remove startup top-gap, keep requested themes on 256-color terminals, and render Theme Picker neutral when current theme is `none`).
- [x] MP-115 Stabilize terminal compatibility regressions (drop startup arrow escape noise during boot, suppress Ctrl+V idle pulse dot beside `PTT`, and restore conservative ANSI fallback when truecolor is not detected).
- [x] MP-116 Fix JetBrains terminal HUD duplication by hardening scroll-region cursor restore semantics.
- [x] MP-117 Prevent one-column HUD wrap in JetBrains terminals (status-banner width guard + row truncation safety).
- [x] MP-118 Harden cross-terminal HUD rendering and PTY teardown paths (universal one-column HUD safety margin, writer-side row clipping to terminal width, and benign PTY-exit write error suppression on shutdown).
- [x] MP-119 Restore the stable `v1.0.53` writer/render baseline for Full HUD while retaining the one-column layout safety margin to recover reliable IDE terminal rendering.
- [x] MP-120 Revert unstable post-release scroll-region protection changes that reintroduced severe Full HUD duplication/corruption during active Codex output.
- [x] MP-121 Harden JetBrains startup/render handoff by auto-skipping splash in IDE terminals and clearing stale HUD/overlay rows on resize before redraw.
- [x] MP-123 Harden PTY/IPC backend teardown to signal process groups and reap child processes, with regression tests that verify descendant cleanup.
- [x] MP-124 Add Full-HUD border-style customization (including borderless mode) and keep right-panel telemetry explicitly user-toggleable to `Off`.
- [x] MP-125 Fix HUD right-panel `Anim only` behavior so idle state keeps a static panel visible instead of hiding the panel until recording.
- [x] MP-126 Complete product/distribution naming rebrand to VoiceTerm across code/docs/scripts/app launcher, and add a PyPI launcher package scaffold (`pypi/`) for `voiceterm`.
- [x] MP-139 Tighten user-facing docs information architecture (entrypoint clarity, navigation consistency, and guide discoverability).
- [x] MP-104 Add explicit voice-state visualization (idle/listening/processing/responding) with clear transitions.
- [x] MP-055 Quick theme switcher in settings.
- [ ] MP-102 Add toast notification center with auto-dismiss, severity, and history review.

## Phase 2B - Rust Hardening Audit (Pre-Execution + Implementation)

- [x] MP-127 Replace IPC `/exit` hard process termination with graceful shutdown orchestration and teardown event guarantees (FX-001).
- [x] MP-128 Add explicit runtime ownership and bounded shutdown/join semantics for overlay writer/input threads (FX-002).
- [x] MP-129 Add voice-manager lifecycle hardening for quit-while-recording paths, including explicit stop/join policy and tests (FX-003).
- [x] MP-130 Consolidate process-group signaling/reaping helpers into one canonical utility with invariants tests (FX-004).
- [x] MP-131 Add security/supply-chain CI lane with policy thresholds and failing gates for high-severity issues (FX-005).
- [x] MP-132 Add explicit security posture/threat-model documentation and risky flag guidance (including permission-skip behavior) (FX-006).
- [x] MP-133 Enforce IPC auth timeout + cancellation semantics using tracked auth start timing (FX-007).
- [x] MP-134 Replace IPC fixed-sleep scheduling with event-driven receive strategy to reduce idle CPU jitter (FX-008).
- [x] MP-135 Decompose high-risk event-loop transition/wiring complexity to reduce change blast radius (FX-009).
- [x] MP-136 Establish unsafe-governance checklist for unsafe hotspots with per-invariant test expectations (FX-010).
- [x] MP-137 Add property/fuzz coverage lane for parser and ANSI/OSC boundary handling (FX-011).
- [x] MP-138 Enforce audit/master-plan traceability updates as a mandatory part of each hardening fix (FX-012).
- [x] MP-152 Consolidate hardening governance to `MASTER_PLAN` as the only active tracker: archive `RUST_GUI_AUDIT_2026-02-15.md` under `dev/archive/` and retire dedicated audit-traceability CI/tooling.

## Phase 2C - Theme System Upgrade (Architecture + Guardrails)

Theme Studio execution gate: MP-148..MP-182 are governed by the
`Theme Studio Definition of Done (Authoritative Checklist)` in
`dev/active/theme_upgrade.md`; a Theme Studio MP may move to `[x]` only with
documented pass evidence for its mapped gates.

- [ ] MP-148 Activate `dev/active/theme_upgrade.md` as an executable phased track in this plan, and lock the IA boundary: dedicated `Theme Studio` mode (not `Settings -> Studio`) plus Settings-vs-Studio ownership matrix.
- [ ] MP-149 Implement Theme Upgrade Phase 0 safety rails (golden render snapshots, terminal compatibility matrix coverage, and style-schema migration harness) before any user-visible editor expansion.
- [ ] MP-150 Implement Theme Upgrade Phase 1 style engine foundation (`StylePack` schema + resolver + runtime), preserving current built-in theme behavior and startup defaults.
- [ ] MP-151 Ship docs/architecture updates for the new theme system (`dev/ARCHITECTURE.md`, `guides/USAGE.md`, `guides/TROUBLESHOOTING.md`, `dev/CHANGELOG.md`) in lockstep with implementation, including operator guidance, settings-migration guidance, and fallback behavior.

## Phase 2D - Visual Surface Expansion (Theme Studio Prerequisite)

- [ ] MP-161 Execute a visual-first runtime pass before deep Studio editing: complete MP-102 and promote MP-103, MP-106, MP-107, MP-108, and MP-109 from Backlog into active execution order with non-regression gates.
- [ ] MP-162 Extend `StylePack` schema/resolver so each runtime visual surface is style-pack addressable (widgets/graphs, toasts, voice-state scenes, command palette, autocomplete, dashboard surfaces), even before all Studio pages ship.
- [ ] MP-163 Add explicit coverage tests/gates that fail if new visual runtime surfaces bypass theme resolver paths with hardcoded style constants.
- [ ] MP-172 Add a styleable component registry and state-matrix contract for all renderable control surfaces (buttons, tabs, lists, tables, trees, scrollbars, modal/popup/tooltip, input/caret/selection) with schema + resolver + snapshot coverage.
- [ ] MP-174 Migrate existing non-HUD visual surfaces into `StylePack` routing (startup splash/banner, help/settings/theme-picker chrome, calibration/mic-meter visuals, progress bars/spinners, icon/glyph sets) so no current visual path is left outside Theme Studio ownership.
- [ ] MP-175 Add a framework capability matrix + parity gate for shipped framework versions (Ratatui widget/symbol families and Crossterm color/input/render capabilities, including synchronized updates + keyboard enhancement flags), and track upgrade deltas before enabling new Studio controls.
- [ ] MP-176 Implement terminal texture/graphics capability track (`TextureProfile` + adapter policy): symbol-texture baseline for all terminals plus capability-gated Kitty/iTerm2 image paths with enforced fallback chain tests.
- [ ] MP-179 Add dependency baseline strategy for Theme Studio ecosystem packs (Ratatui/Crossterm version pin policy + compatibility matrix + staged upgrade plan) so third-party widget adoption does not fragment resolver/studio parity.
- [ ] MP-180 Pilot a curated widget-pack integration lane (`tui-widgets` family, `tui-textarea`, `tui-tree-widget`, `throbber-widgets-tui`) under style-ID/allowlist gates, with parity tests before feature flags graduate.
- [ ] MP-182 Add `RuleProfile` no-code visual automation (threshold/context/state-driven style overrides) with deterministic priority semantics, preview tooling, and snapshot coverage.

## Phase 2E - Theme Studio Delivery (After Visual Surface Expansion)

- [ ] MP-164 Implement dedicated `Theme Studio` overlay mode entry points/navigation and remove deep theme editing from generic Settings flows.
- [ ] MP-165 Migrate legacy visual controls out of settings list (`SettingsItem::Theme`, `SettingsItem::HudStyle`, `SettingsItem::HudBorders`, `SettingsItem::HudPanel`, `SettingsItem::HudAnimate`) so Settings keeps non-theme runtime controls only.
- [ ] MP-166 Deliver Studio page control parity for all `StylePack` fields (tokens, layout, widgets, motion, behavior, notifications, command/discovery surfaces, voice-state scenes, startup/wizard/progress/texture surfaces, accessibility, keybinds, profiles) with undo/redo + rollback.
- [ ] MP-167 Run Theme Studio GA validation and docs lockstep updates (snapshot matrix, terminal compatibility matrix, architecture docs, user docs, troubleshooting guidance, changelog entry).
- [ ] MP-173 Add CI policy gates for future visuals: fail if a new renderable component lacks style-ID registration, and fail if post-parity a style-pack field lacks Studio control mapping.
- [ ] MP-177 Add widget-pack extensibility parity (first-party plus allowlisted third-party widgets) so newly adopted widget families must register style IDs + resolver bindings + Studio controls before GA.
- [ ] MP-178 Add Theme Studio element inspector parity so users can select any rendered element and jump directly to component/state style controls (with state preview and style-path tracing).
- [ ] MP-181 Add advanced Studio interaction parity (resizable splits, drag/reorder, scrollview-heavy forms, large text/editor fields) with full keyboard fallback and capability-safe mouse behavior.

## Phase 3 - Overlay Differentiators

- [x] MP-090 Voice terminal navigation actions (scroll/copy/error/explain).
- [x] MP-140 Define and enforce macro-vs-navigation precedence (macros first, explicit built-in phrase escape path).
- [x] MP-141 Add Linux clipboard fallback support for voice `copy last error` (wl-copy/xclip/xsel).
- [x] MP-142 Add `devctl docs-check` commit-range mode for post-commit doc audits on clean working trees.
- [x] MP-156 Add release-notes automation (`generate-release-notes.sh`, `devctl release-notes`, `release.sh` notes-file handoff) so each tag has consistent diff-derived markdown notes for GitHub releases.
- [x] MP-144 Add macro-pack onboarding wizard hardening (expanded developer command packs, repo-aware placeholder templating, and optional post-install setup prompt).
- [x] MP-143 Decompose `voice_control/drain.rs` and `event_loop.rs` into smaller modules to reduce review and regression risk (adjacent runtime architecture debt; tracked separately from tooling-control-plane work).
  - [x] MP-143a Extract shared settings-item action dispatch in `event_loop.rs` so Enter/Left/Right settings paths stop duplicating mutation logic.
  - [x] MP-143b Split `event_loop.rs` overlay/input/output handlers into focused modules (`overlay_dispatch`, `input_dispatch`, `output_dispatch`, `periodic_tasks`) and move tests to `event_loop/tests.rs` while preserving regression coverage.
  - [x] MP-143c0 Move `voice_control/drain.rs` tests into `voice_control/drain/tests.rs` so runtime decomposition can land in smaller, reviewable slices.
  - [x] MP-143c1 Extract `voice_control/drain/message_processing.rs` for macro expansion, status message handling, and latency/preview helpers.
  - [x] MP-143c Split `voice_control/drain.rs` into transcript-delivery (`transcript_delivery.rs`), status/latency updates (`message_processing.rs`), and auto-rearm/finalize components (`auto_rearm.rs`) with unchanged behavior coverage.
- [x] MP-182 Decompose `ipc/session.rs` by extracting non-blocking codex/claude/voice/auth event processors into `ipc/session/event_processing/`, keeping command-loop orchestration in `session.rs` and preserving IPC regression coverage.
- [x] MP-170 Harden IPC test event capture isolation so parallel test runs remain deterministic under `cargo test` and `devctl check --profile ci`.
- [ ] MP-091 Searchable transcript history and replay workflow.

## Phase 3B - Tooling Control Plane Consolidation

- [x] MP-157 Execute tooling-control-plane consolidation (archived at `dev/archive/2026-02-17-tooling-control-plane-consolidation.md`): implement `devctl ship`, deterministic step exits, dry-run behavior, machine-readable step reports, and adapter conversion for release entry points.
- [x] MP-158 Harden `devctl docs-check` policy enforcement so docs requirements are change-class aware and deprecated maintainer command references are surfaced as actionable failures.
- [x] MP-159 Add a dedicated tooling CI quality lane for `devctl` command behavior and maintainer shell-script integrity (release, release-notes, PyPI, Homebrew helpers).
- [x] MP-160 Canonicalize maintainer docs and macro/help surfaces to `devctl` first (`AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, maintainer macro packs, and `Makefile` help), keeping legacy wrappers documented as transitional adapters.

## Phase 3A - Mutation Hardening (Current Execution Focus)

- [ ] MP-015 Improve mutation score with targeted high-value tests (promoted from Backlog).
  - [ ] Build a fresh shard-by-shard survivor baseline on `master` and rank hotspots by missed mutants.
  - [ ] Add targeted tests for top survivors in current hotspots (`src/bin/voiceterm/config/*`, `src/bin/voiceterm/hud/*`, `src/bin/voiceterm/input/mouse.rs`) and any new top offenders.
  - [ ] Ensure shard jobs always publish outcomes artifacts even when mutants survive.
  - [ ] Re-run mutation workflow until aggregate score holds at or above `0.80` on `master` for two consecutive runs (manual + scheduled).
  - [ ] Keep non-mutation quality gates green after each hardening batch (`python3 dev/scripts/devctl.py check --profile ci`, `Security Guard`).
- MP-015 acceptance gates:
  1. `.github/workflows/mutation-testing.yml` passes on `master` with threshold `0.80`.
  2. Aggregated score gate passes via `python3 dev/scripts/check_mutation_score.py --glob "mutation-shards/**/shard-*-outcomes.json" --threshold 0.80`.
  3. Shard outcomes artifacts are present for all 8 shards in each validation run.
  4. Added hardening tests remain stable across two consecutive mutation workflow runs.

## Phase 4 - Advanced Expansion

- [ ] MP-092 Streaming STT and partial transcript overlay.
- [ ] MP-093 tmux/neovim integration track.
- [ ] MP-094 Accessibility suite (fatigue hints, quiet mode, screen-reader compatibility).
- [ ] MP-095 Custom vocabulary learning and correction persistence.

## Backlog (Not Scheduled)

- [ ] MP-016 Stress test heavy I/O for bounded-memory behavior.
- [ ] MP-031 Add PTY health monitoring for hung process detection.
- [ ] MP-032 Add retry logic for transient audio device failures.
- [ ] MP-033 Add benchmarks to CI for latency regression detection.
- [ ] MP-034 Add mic-meter hotkey for calibration.
- [ ] MP-037 Consider configurable PTY output channel capacity.
- [ ] MP-145 Eliminate startup cursor/ANSI escape artifacts shown in Cursor (Codex and Claude backends), with focus on the splash-screen teardown to VoiceTerm HUD handoff window where artifacts appear before full load.
- [ ] MP-146 Improve controls-row bracket styling so `[` `]` tokens track active theme colors and selected states use stronger contrast/readability (especially for arrow-mode focus visibility).
- [ ] MP-147 Fix Cursor-only mouse-mode scroll conflict: with mouse mode ON, chat/conversation scroll should still work in Cursor for both Codex and Claude backends; preserve current JetBrains behavior (works today in PyCharm/JetBrains), keep architecture/change scope explicitly Cursor-specific, and require JetBrains non-regression validation so the Cursor fix does not break JetBrains scrolling.
- [ ] MP-153 Add a CI docs-governance lane that runs `python3 dev/scripts/devctl.py docs-check --user-facing --strict` for user-facing behavior/doc changes so documentation drift fails early.
- [ ] MP-154 Add a governance consistency check for active docs + macro packs so removed workflows/scripts are not referenced in non-archive content.
- [ ] MP-155 Add a single pre-release verification command/profile that aggregates CI checks, mutation threshold, docs-governance checks, and hygiene into one machine-readable report artifact.

## Deferred Plans

- `dev/deferred/DEV_MODE_PLAN.md` (paused until Phases 1-2 outcomes are complete).
- MP-089 LLM-assisted voice-to-command generation (optional local/API provider) is deferred; current product focus is Codex/Claude CLI-native flow quality, not an additional LLM mediation layer.

## Release Policy (Checklist)

1. `src/Cargo.toml` version bump
2. `dev/CHANGELOG.md` entry finalized
3. Verification pass for change scope
4. Tag + push from `master`
5. GitHub release creation
6. PyPI package publish
7. PyPI publish verification (`https://pypi.org/pypi/voiceterm/<version>/json`)
8. Homebrew tap formula update + push

## Execution Gate (Every Feature)

1. Create or link an MP item before implementation.
2. Implement the feature and add/update tests in the same change.
3. Run SDLC verification for scope:
   `python3 dev/scripts/devctl.py check --profile ci`
4. Run docs coverage check for user-facing work:
   `python3 dev/scripts/devctl.py docs-check --user-facing`
5. Update required docs (`dev/CHANGELOG.md` + relevant guides) before merge.
6. Push only after checks pass and plan/docs are aligned.

## References

- Execution + release tracking: `dev/active/MASTER_PLAN.md`
- Market, competitor, and UX evidence: `dev/active/overlay.md`
- SDLC policy: `AGENTS.md`
- Architecture: `dev/ARCHITECTURE.md`
- Changelog: `dev/CHANGELOG.md`

## Archive Log

- `dev/archive/2026-01-29-claudeaudit-completed.md`
- `dev/archive/2026-01-29-docs-governance.md`
- `dev/archive/2026-02-01-terminal-restore-guard.md`
- `dev/archive/2026-02-01-transcript-queue-flush.md`
- `dev/archive/2026-02-02-release-audit-completed.md`
- `dev/archive/2026-02-17-tooling-control-plane-consolidation.md`
