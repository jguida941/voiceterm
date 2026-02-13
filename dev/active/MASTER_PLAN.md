# Overlay Master Plan (Active)

## Status Snapshot (2026-02-13)
- Strategic source plan: `dev/active/overlay.md`
- Execution tracker: `dev/active/MASTER_PLAN.md` (this file)
- Deferred plans: `dev/deferred/`
- Last tagged release: `v1.0.50` (2026-02-09)
- Current release target: `v1.0.51`

## Purpose
- Keep one active execution board tied directly to the overlay roadmap.
- Track release readiness, latency correctness, and phased feature delivery.
- Keep paused work visible but out of the active queue.

## Planning Model
1. `dev/active/overlay.md` defines product direction and phased roadmap.
2. This file defines concrete implementation and release tasks.
3. Completed items move to `dev/archive/` with a dated entry.
4. Deferred plans stay in `dev/deferred/` until explicitly reactivated.

## Phase 0 - Release 1.0.51 Stabilization (In Progress)
- [x] MP-072 Prevent HUD/timer freeze under continuous PTY output.
- [x] MP-073 Improve IDE terminal input compatibility and hidden-HUD discoverability.
- [x] MP-074 Update user docs for HUD/input behavior changes and debug guidance.
- [x] MP-075 Finalize latency display semantics to avoid misleading values when metrics are partial.
- [x] MP-076 Add latency audit logging + regression tests for displayed latency behavior.
- [x] MP-077 Run release verification (`cargo build --release --bin voxterm`, targeted tests, docs-check).
- [ ] MP-078 Finalize release notes, bump version, tag, push, and publish Homebrew tap update.

## Phase 1 - Latency Truth and Observability
- [x] MP-079 Define and document latency terms:
  capture time, STT time, post-capture processing time, and displayed HUD latency.
- [x] MP-080 Keep HUD latency badge hidden when latency cannot be measured reliably.
- [x] MP-081 Emit structured latency audit lines suitable for log-based analysis.
- [x] MP-082 Add automated checks around latency calculations in unit/integration tests.
- [ ] MP-083 Run and document baseline latency measurements with `latency_measurement` and `dev/scripts/tests/measure_latency.sh`.
- [ ] MP-084 Add CI-friendly latency regression guardrails for synthetic runs.

## Phase 2 - Overlay Quick Wins (from `overlay.md`)
- [ ] MP-085 Voice macros and custom triggers (`.voxterm/macros.yaml`).
- [ ] MP-086 Command mode vs dictation mode (toggle + UX/state model).
- [ ] MP-087 Transcript preview/edit before send.
- [ ] MP-088 Persistent user config (`~/.config/voxterm/config.toml`) for core preferences.

## Phase 3 - Overlay Differentiators
- [ ] MP-089 LLM-assisted voice-to-command generation (optional local/API provider).
- [ ] MP-090 Voice terminal navigation actions (scroll/copy/error/explain).
- [ ] MP-091 Searchable transcript history and replay workflow.

## Phase 4 - Advanced Expansion
- [ ] MP-092 Streaming STT and partial transcript overlay.
- [ ] MP-093 tmux/neovim integration track.
- [ ] MP-094 Accessibility suite (fatigue hints, quiet mode, screen-reader compatibility).
- [ ] MP-095 Custom vocabulary learning and correction persistence.

## Carry-Over Backlog (Not Scheduled Yet)
- [ ] MP-015 Improve mutation score with targeted high-value tests.
- [ ] MP-016 Stress test heavy I/O for bounded-memory validation.
- [ ] MP-031 Add PTY health monitoring for hung process detection.
- [ ] MP-032 Add retry logic for transient audio device failures.
- [ ] MP-033 Add benchmarks to CI for latency regression detection.
- [ ] MP-034 Add mic-meter hotkey for calibration.
- [ ] MP-037 Consider configurable PTY output channel capacity.
- [ ] MP-054 Optional right-panel visualization modes in minimal HUD.
- [ ] MP-055 Quick theme switcher in settings.

## Release Branching and Tag Policy
- Use `feature/*` branches for scoped work and merge into `master` after verification.
- Use `release/<version>` only for final stabilization when needed.
- Tag only from `master` after changelog/version/docs alignment and local verification.
- Sequence for each release:
  1. `src/Cargo.toml` version bump
  2. `dev/CHANGELOG.md` entry finalized
  3. verification pass
  4. tag + push
  5. GitHub release
  6. Homebrew tap update

## Deferred Plans
- `dev/deferred/DEV_MODE_PLAN.md` (paused until overlay phases 0-2 are complete).

## Archive Log
- `dev/archive/2026-01-29-claudeaudit-completed.md`
- `dev/archive/2026-01-29-docs-governance.md`
- `dev/archive/2026-02-01-terminal-restore-guard.md`
- `dev/archive/2026-02-01-transcript-queue-flush.md`
- `dev/archive/2026-02-02-release-audit-completed.md`
