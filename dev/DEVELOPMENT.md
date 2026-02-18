# Development

## Contents

- [Project structure](#project-structure)
- [Building](#building)
- [Testing](#testing)
- [Manual QA checklist](#manual-qa-checklist)
- [Contribution workflow](#contribution-workflow)
- [Pre-refactor docs readiness checklist](#pre-refactor-docs-readiness-checklist)
- [Code style](#code-style)
- [Testing philosophy](#testing-philosophy)

## Project structure

```text
voiceterm/
├── .github/
│   ├── CONTRIBUTING.md   # Contribution guidelines
│   ├── SECURITY.md       # Security policy
│   └── workflows/        # CI workflows
├── app/
│   ├── macos/VoiceTerm.app # macOS double-click launcher
│   └── windows/          # Windows launcher (planned placeholder)
├── AGENTS.md             # SDLC policy and release checklist
├── QUICK_START.md        # Fast setup and commands
├── guides/
│   ├── CLI_FLAGS.md        # Full CLI and env reference
│   ├── INSTALL.md          # Install options and PATH notes
│   ├── TROUBLESHOOTING.md  # Common issues and fixes
│   ├── USAGE.md            # Controls and overlay behavior
│   └── WHISPER.md          # Whisper model guidance
├── dev/
│   ├── ARCHITECTURE.md     # Architecture diagrams and data flow
│   ├── CHANGELOG.md        # Release history
│   ├── DEVELOPMENT.md      # Build/test workflow
│   ├── active/             # Active plans and work in progress
│   ├── archive/            # Completed work entries
│   ├── adr/                # Architecture decision records
│   └── scripts/            # Developer scripts
│       ├── release.sh         # Legacy adapter -> devctl release
│       ├── generate-release-notes.sh # Markdown notes from git diff history
│       ├── publish-pypi.sh    # Legacy adapter -> devctl pypi
│       ├── update-homebrew.sh # Legacy adapter -> devctl homebrew
│       ├── check_mutation_score.py # Mutation score helper
│       └── tests/             # Test scripts
├── img/                 # Screenshots
├── Makefile             # Developer tasks
├── src/                 # Rust overlay + voice pipeline
│   └── src/
│       ├── bin/voiceterm/main.rs # Overlay entry point
│       ├── bin/voiceterm/banner.rs # Startup splash + banner config
│       ├── bin/voiceterm/custom_help.rs # Themed CLI help renderer
│       ├── bin/voiceterm/help.rs # Shortcut overlay rendering
│       ├── bin/voiceterm/onboarding.rs # First-run onboarding state persistence
│       ├── bin/voiceterm/overlay_frame.rs # Shared overlay frame layout helpers
│       ├── bin/voiceterm/status_messages.rs # Reusable status message builders
│       ├── bin/voiceterm/terminal.rs # Terminal sizing + signal handling
│       ├── bin/voiceterm/event_loop/ # Event-loop dispatch modules + tests
│       ├── bin/voiceterm/audio_meter/ # Mic meter UI (`--mic-meter`)
│       ├── bin/voiceterm/hud/ # HUD modules and right panel visuals
│       ├── bin/voiceterm/status_line/ # Status line layout + formatting
│       ├── bin/voiceterm/settings/ # Settings overlay
│       ├── bin/voiceterm/transcript/ # Transcript queue + delivery
│       ├── bin/voiceterm/voice_control/ # Voice capture lifecycle + drain orchestration
│       ├── bin/voiceterm/voice_control/drain/ # Voice drain helpers + tests
│       ├── bin/voiceterm/input/ # Input parsing + events
│       ├── bin/voiceterm/writer/ # Output writer + overlays
│       ├── bin/voiceterm/theme/ # Theme definitions
│       ├── legacy_tui/   # Codex TUI state + logging (legacy)
│       ├── audio/       # CPAL recording, VAD, resample
│       ├── backend/     # AI CLI backend presets (overlay)
│       ├── codex/       # Codex-specific backend + PTY worker (TUI/IPC)
│       ├── config/      # CLI flags + validation
│       ├── ipc/         # JSON IPC mode + protocol/router/session loop
│       ├── ipc/session/ # IPC non-blocking event processing helpers
│       ├── pty_session/ # PTY wrapper
│       ├── voice.rs     # Voice capture orchestration
│       ├── mic_meter.rs # Ambient/speech level sampler
│       ├── stt.rs       # Whisper transcription
│       ├── auth.rs      # Backend auth helpers
│       ├── doctor.rs    # Diagnostics report
│       ├── telemetry.rs # Structured trace logging
│       ├── terminal_restore.rs # Panic-safe terminal restore
│       └── legacy_ui.rs  # Codex TUI rendering (legacy)
├── scripts/
│   ├── README.md        # Script documentation
│   ├── install.sh       # One-time installer
│   ├── start.sh         # Linux/macOS launcher
│   ├── setup.sh         # Model download and setup
│   └── python_fallback.py # Python fallback pipeline
├── whisper_models/      # Whisper GGML models
└── bin/                 # Install wrapper (created by install.sh)
```

Note: `src/` is the Rust workspace root and the crate lives under `src/src/`. This layout is intentional (workspace + crate separation).
`dev/active/MASTER_PLAN.md` is the canonical execution tracker.

## Building

```bash
# Rust overlay
cd src && cargo build --release --bin voiceterm

# Rust backend (optional dev binary)
cd src && cargo build --release
```

## Testing

```bash
# Rust tests
cd src && cargo test

# Overlay tests
cd src && cargo test --bin voiceterm

# Perf smoke (voice metrics)
cd src && cargo test --no-default-features legacy_tui::tests::perf_smoke_emits_voice_metrics -- --nocapture

# Wake-word regression + soak guardrails
bash dev/scripts/tests/wake_word_guard.sh

# Memory guard (thread cleanup)
cd src && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture

# Security advisory policy (high/critical + yanked/unsound gate)
cargo install cargo-audit --locked
cd src && (cargo audit --json > ../rustsec-audit.json || true)
python3 ../dev/scripts/check_rustsec_policy.py --input ../rustsec-audit.json --min-cvss 7.0 --fail-on-kind yanked --fail-on-kind unsound --allowlist-file ../dev/security/rustsec_allowlist.md

# Unsafe/FFI governance (for PTY/stt unsafe changes)
# 1) update invariants checklist doc:
#    dev/security/unsafe_governance.md
cd src && cargo test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group -- --nocapture
cd src && cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture
cd src && cargo test stt::tests::transcriber_restores_stderr_after_failed_model_load -- --nocapture

# Parser/ANSI boundary property-fuzz coverage
cd src && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture
cd src && cargo test pty_session::tests::prop_find_osc_terminator_respects_bounds -- --nocapture
cd src && cargo test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes -- --nocapture

# Mutation tests (single run; CI enforces 80% minimum score)
cd src && cargo mutants --timeout 300 -o mutants.out --json
python3 ../dev/scripts/check_mutation_score.py --glob "mutants.out/**/outcomes.json" --threshold 0.80

# Mutation tests (sharded, mirrors CI approach)
cd src && cargo mutants --baseline skip --timeout 180 --shard 1/8 -o mutants.out --json
python3 ../dev/scripts/check_mutation_score.py --glob "mutants.out/**/outcomes.json" --threshold 0.80

# Mutation tests (offline/sandboxed; use a writable cache)
rsync -a ~/.cargo/ /tmp/cargo-home/
cd src && CARGO_HOME=/tmp/cargo-home CARGO_TARGET_DIR=/tmp/cargo-target CARGO_NET_OFFLINE=true cargo mutants --timeout 300 -o mutants.out --json
python3 ../dev/scripts/check_mutation_score.py --glob "mutants.out/**/outcomes.json" --threshold 0.80

# Mutation helper script (module filter + offline env)
python3 ../dev/scripts/mutants.py --module overlay --offline --cargo-home /tmp/cargo-home --cargo-target-dir /tmp/cargo-target

# Summarize top paths with survived mutants
python3 ../dev/scripts/mutants.py --results-only --top 10

# Plot hotspots (top 25% by default)
python3 ../dev/scripts/mutants.py --results-only --plot --plot-scope dir --plot-top-pct 25
```

`--results-only` auto-detects the most recent `outcomes.json` under `src/mutants.out/`.
Mutation runs can be long; plan to run them overnight and use Ctrl+C to stop if needed.

## Dev CLI (devctl)

Unified CLI for common dev workflows:

```bash
# Core checks (fmt, clippy, tests, build)
python3 dev/scripts/devctl.py check

# Match CI scope (fmt-check + clippy + tests)
python3 dev/scripts/devctl.py check --profile ci

# Pre-push scope (CI + perf + mem loop)
python3 dev/scripts/devctl.py check --profile prepush

# Maintainer lint-hardening lane (strict clippy policy subset)
python3 dev/scripts/devctl.py check --profile maintainer-lint

# Release verification lane (includes wake-word guard + mutation-score gate)
python3 dev/scripts/devctl.py check --profile release

# Quick scope (fmt-check + clippy only)
python3 dev/scripts/devctl.py check --profile quick

# Mutants wrapper (offline cache)
python3 dev/scripts/devctl.py mutants --module overlay --offline \
  --cargo-home /tmp/cargo-home --cargo-target-dir /tmp/cargo-target

# Mutants wrapper (run one shard)
python3 dev/scripts/devctl.py mutants --module overlay --shard 1/8

# Check mutation score only
python3 dev/scripts/devctl.py mutation-score --threshold 0.80

# Docs check (user-facing changes must update docs + changelog)
python3 dev/scripts/devctl.py docs-check --user-facing

# Tooling/release docs policy (change-class aware + deprecated-command guard)
python3 dev/scripts/devctl.py docs-check --strict-tooling

# Post-commit docs check over a commit range (works on clean trees)
python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop

# Governance hygiene audit (archive + ADR + scripts docs)
python3 dev/scripts/devctl.py hygiene

# Release/distribution control plane
python3 dev/scripts/devctl.py release --version X.Y.Z
python3 dev/scripts/devctl.py pypi --upload
python3 dev/scripts/devctl.py homebrew --version X.Y.Z
python3 dev/scripts/devctl.py ship --version X.Y.Z --verify --tag --notes --github --pypi --homebrew --verify-pypi

# Generate a report (JSON/MD)
python3 dev/scripts/devctl.py report --format json --output /tmp/devctl-report.json

# Include recent GitHub Actions runs (requires gh auth)
python3 dev/scripts/devctl.py status --ci --format md

# Pipe report output to a CLI that accepts stdin (requires login)
python3 dev/scripts/devctl.py report --format md --pipe-command codex
python3 dev/scripts/devctl.py report --format md --pipe-command claude
# If your CLI needs a stdin flag, pass it via --pipe-args.
```

Implementation layout:

- `dev/scripts/devctl.py`: thin entrypoint wrapper
- `dev/scripts/devctl/cli.py`: argument parsing and dispatch
- `dev/scripts/devctl/commands/`: per-command implementations
- `dev/scripts/devctl/common.py`: shared helpers (run_cmd, env, output)
- `dev/scripts/devctl/collect.py`: git/CI/mutation summaries for reports

Legacy shell scripts in `dev/scripts/*.sh` are compatibility adapters and should not be the canonical maintainer workflow.

## Manual QA checklist

- [ ] Auto-voice status visibility: Full HUD keeps mode label (`AUTO`/`PTT`) while active-state text (`Recording`/`Processing`) and meter remain visible.
- [ ] Queue flush works in both insert and auto send modes.
- [ ] Prompt logging is off by default unless explicitly enabled.
- [ ] Two terminals can run independently without shared state leaks.

## Contribution workflow

- Open or comment on an issue for non-trivial changes so scope and UX expectations are aligned.
- Keep UX tables/controls lists and docs in sync with behavior.
- Update `dev/CHANGELOG.md` for user-facing changes and note verification steps in PRs.

## Pre-refactor docs readiness checklist

Use this checklist before larger UI/behavior refactors to avoid documentation drift:

- [ ] `README.md` updated (features list, screenshots, quick overview).
- [ ] `QUICK_START.md` updated (install steps and common commands).
- [ ] `guides/USAGE.md` updated (controls, status messages, theme list).
- [ ] `guides/CLI_FLAGS.md` updated (flags and defaults).
- [ ] `guides/INSTALL.md` updated (dependencies, setup steps, PATH notes).
- [ ] `guides/TROUBLESHOOTING.md` updated (new known issues/fixes).
- [ ] `img/` screenshots refreshed if UI output/controls changed.

## Code style

- Rust: run `cargo fmt` and `cargo clippy --workspace --all-features -- -D warnings`.
- Keep changes small and reviewable; avoid unrelated refactors.
- Prefer explicit error handling in user-facing flows (status line + logs) so failures are observable.

## Testing philosophy

- Favor fast unit tests for parsing, queueing, and prompt detection logic.
- Add regression tests when fixing a reported bug.
- Run at least `cargo test` locally for most changes; add targeted bin tests for overlay-only work.

## CI/CD Workflow

GitHub Actions run on every push and PR:

| Workflow | File | What it checks |
|----------|------|----------------|
| Rust TUI CI | `.github/workflows/rust_ci.yml` | Build, test, clippy, fmt |
| Voice Mode Guard | `.github/workflows/voice_mode_guard.yml` | Focused macros toggle + send-mode label regressions |
| Wake Word Guard | `.github/workflows/wake_word_guard.yml` | Wake-word regression + soak guardrails |
| Perf Smoke | `.github/workflows/perf_smoke.yml` | Perf smoke test + metrics verification |
| Latency Guard | `.github/workflows/latency_guard.yml` | Synthetic latency regression guardrails |
| Memory Guard | `.github/workflows/memory_guard.yml` | 20x memory guard loop |
| Mutation Testing | `.github/workflows/mutation-testing.yml` | sharded scheduled mutation run + aggregated 80% score gate |
| Security Guard | `.github/workflows/security_guard.yml` | RustSec advisory policy gate (high/critical threshold + yanked/unsound fail list) |
| Parser Fuzz Guard | `.github/workflows/parser_fuzz_guard.yml` | property-fuzz parser/ANSI-OSC boundary coverage |
| Docs Lint | `.github/workflows/docs_lint.yml` | markdown style/readability checks for key published docs |
| Lint Hardening | `.github/workflows/lint_hardening.yml` | maintainer lint-hardening profile (`devctl check --profile maintainer-lint`) with strict clippy subset for redundant clones/closures, risky wrap casts, and dead-code drift |
| Tooling Control Plane | `.github/workflows/tooling_control_plane.yml` | devctl unit tests, shell adapter integrity, and docs/deprecated-command policy guard |

**Before pushing, run locally (recommended):**

```bash
# Core CI (matches rust_ci.yml)
make ci

# Full push/PR suite (adds perf smoke + memory guard loop)
make prepush

# Governance/doc architecture hygiene
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/devctl.py docs-check --strict-tooling

# Security advisory policy gate (matches security_guard.yml)
cargo install cargo-audit --locked
cd src && (cargo audit --json > ../rustsec-audit.json || true)
python3 ../dev/scripts/check_rustsec_policy.py --input ../rustsec-audit.json --min-cvss 7.0 --fail-on-kind yanked --fail-on-kind unsound --allowlist-file ../dev/security/rustsec_allowlist.md

# Parser property-fuzz lane (matches parser_fuzz_guard.yml)
cd src && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture
cd src && cargo test pty_session::tests::prop_find_osc_terminator_respects_bounds -- --nocapture
cd src && cargo test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes -- --nocapture

# Markdown style/readability checks for key docs
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
```

**Manual equivalents (if you prefer direct cargo commands):**

```bash
cd src

# Format code
cargo fmt

# Lint (must pass with no warnings)
cargo clippy --workspace --all-features -- -D warnings

# Run tests
cargo test --workspace --all-features

# Check mutation score (optional, CI enforces this)
cargo mutants --timeout 300 -o mutants.out --json
python3 ../dev/scripts/check_mutation_score.py --glob "mutants.out/**/outcomes.json" --threshold 0.80
```

**Check CI status:** [GitHub Actions](https://github.com/jguida941/voiceterm/actions)

## Releasing

### Version bump

1. Update version in `src/Cargo.toml`
2. Update `dev/CHANGELOG.md` with release notes
3. Commit: `git commit -m "Release vX.Y.Z"`

### Create GitHub release

```bash
# Canonical control plane
python3 dev/scripts/devctl.py release --version X.Y.Z

# Create release on GitHub
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file /tmp/voiceterm-release-vX.Y.Z.md
```

`devctl release` auto-generates `/tmp/voiceterm-release-vX.Y.Z.md` from the git
compare range (previous tag to current tag). You can also generate it manually:

```bash
python3 dev/scripts/devctl.py release-notes --version X.Y.Z
```

### Update Homebrew tap

```bash
# Canonical control plane
python3 dev/scripts/devctl.py homebrew --version X.Y.Z
```

### Publish PyPI package

```bash
# Build + upload package to PyPI
python3 dev/scripts/devctl.py pypi --upload

# Verify the published version appears (replace X.Y.Z)
curl -fsSL https://pypi.org/pypi/voiceterm/X.Y.Z/json | rg '"version"'
```

Use `python3 dev/scripts/devctl.py homebrew --version X.Y.Z` in the previous step to fetch
the SHA256 and update the Homebrew formula.

Legacy wrappers (`dev/scripts/release.sh`, `dev/scripts/publish-pypi.sh`,
`dev/scripts/update-homebrew.sh`) remain for compatibility and route into
`devctl`.

Users can then upgrade:

```bash
brew update && brew upgrade voiceterm
```

See `scripts/README.md` for full script documentation.

## Local development tips

**Test with different backends:**

```bash
voiceterm              # Codex (default)
voiceterm --claude     # Claude Code
voiceterm --gemini     # Gemini CLI (experimental; not fully validated)
```

**Debug logging:**

```bash
voiceterm --logs                    # Enable debug log
tail -f $TMPDIR/voiceterm_tui.log   # Watch log output
tail -f $TMPDIR/voiceterm_trace.jsonl  # Watch structured trace output (JSON)
```
