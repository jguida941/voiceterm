# Development

## Contents

- [Project structure](#project-structure)
- [Building](#building)
- [Testing](#testing)
- [Contribution workflow](#contribution-workflow)
- [Code style](#code-style)
- [Testing philosophy](#testing-philosophy)

## Project structure

```
voxterm/
├── .github/
│   ├── CONTRIBUTING.md   # Contribution guidelines
│   ├── SECURITY.md       # Security policy
│   └── workflows/        # CI workflows
├── VoxTerm.app/      # macOS double-click launcher
├── agents.md             # SDLC policy and release checklist
├── QUICK_START.md        # Fast setup and commands
├── docs/
│   ├── CHANGELOG.md        # Release history
│   ├── CLI_FLAGS.md        # Full CLI and env reference
│   ├── INSTALL.md          # Install options and PATH notes
│   ├── TROUBLESHOOTING.md  # Common issues and fixes
│   ├── USAGE.md            # Controls and overlay behavior
│   ├── active/             # Active plans and work in progress
│   │   ├── MASTER_PLAN.md        # Active work and verification
│   │   ├── BACKLOG.md            # Deprecated pointer (see master plan)
│   │   ├── UI_ENHANCEMENT_PLAN.md # UI roadmap + research notes
│   ├── archive/            # Completed work entries (incl. release reviews & retired plans)
│   └── dev/                # Reference and architecture docs
│       ├── ARCHITECTURE.md       # Architecture diagrams and data flow
│       ├── DEVELOPMENT.md        # Build/test workflow
│       ├── SDLC.md               # Deprecated pointer to agents.md
│       └── adr/                  # Architecture decision records
├── img/                 # Screenshots
├── rust_tui/            # Rust overlay + voice pipeline
│   └── src/
│       ├── bin/codex_overlay/main.rs # Overlay entry point
│       ├── app/         # TUI state + logging
│       ├── audio/       # CPAL recording, VAD, resample
│       ├── backend/     # AI CLI backend presets (overlay selection)
│       ├── codex/       # Provider backend + PTY worker
│       ├── config/      # CLI flags + validation
│       ├── ipc/         # JSON IPC mode
│       ├── pty_session/ # PTY wrapper
│       ├── voice.rs     # Voice capture orchestration
│       ├── mic_meter.rs # Ambient/speech level sampler
│       ├── stt.rs       # Whisper transcription
│       └── ui.rs        # Full TUI rendering
├── scripts/             # Setup and test scripts
├── models/              # Whisper GGML models
├── start.sh             # Linux/macOS launcher
└── install.sh           # One-time installer
```

## Building

```bash
# Rust overlay
cd rust_tui && cargo build --release --bin voxterm

# Rust backend (optional dev binary)
cd rust_tui && cargo build --release
```

## Testing

```bash
# Rust tests
cd rust_tui && cargo test

# Overlay tests
cd rust_tui && cargo test --bin voxterm

# Perf smoke (voice metrics)
cd rust_tui && cargo test --no-default-features app::tests::perf_smoke_emits_voice_metrics -- --nocapture

# Memory guard (thread cleanup)
cd rust_tui && cargo test --no-default-features app::tests::memory_guard_backend_threads_drop -- --nocapture

# Mutation tests (CI enforces 80% minimum score)
cd rust_tui && cargo mutants --timeout 300 -o mutants.out
python3 ../scripts/check_mutation_score.py --path mutants.out/outcomes.json --threshold 0.80
```

## Contribution workflow

- Open or comment on an issue for non-trivial changes so scope and UX expectations are aligned.
- Keep UX tables/controls lists and docs in sync with behavior.
- Update `docs/CHANGELOG.md` for user-facing changes and note verification steps in PRs.

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
| Rust TUI CI | `.github/workflows/rust_tui.yml` | Build, test, clippy, fmt |
| Mutation Testing | `.github/workflows/mutation-testing.yml` | 80% minimum mutation score |

**Before pushing, run locally:**

```bash
cd rust_tui

# Format code
cargo fmt

# Lint (must pass with no warnings)
cargo clippy --workspace --all-features -- -D warnings

# Run tests
cargo test

# Check mutation score (optional, CI enforces this)
cargo mutants --timeout 300 -o mutants.out
python3 ../scripts/dev/check_mutation_score.py --path mutants.out/outcomes.json --threshold 0.80
```

**Check CI status:** [GitHub Actions](https://github.com/jguida941/voxterm/actions)

## Releasing

### Version bump

1. Update version in `rust_tui/Cargo.toml`
2. Update `docs/CHANGELOG.md` with release notes
3. Commit: `git commit -m "Release vX.Y.Z"`

### Create GitHub release

```bash
# Use the release script (recommended)
./scripts/dev/release.sh X.Y.Z

# Create release on GitHub
gh release create vX.Y.Z --title "vX.Y.Z" --notes "See CHANGELOG.md"
```

### Update Homebrew tap

```bash
# Use the update script (recommended)
./scripts/dev/update-homebrew.sh X.Y.Z
```

This automatically fetches the SHA256 and updates the formula.

Users can then upgrade:
```bash
brew update && brew upgrade voxterm
```

See `scripts/README.md` for full script documentation.

## Local development tips

**AI review notes** (e.g., `claude_review.md`) are local-only, gitignored, and kept in the repo root for session notes.

**Test with different backends:**
```bash
voxterm              # Codex (default)
voxterm --claude     # Claude Code
voxterm --gemini     # Gemini CLI (limited support)
```

**Debug logging:**
```bash
voxterm --logs                    # Enable debug log
tail -f $TMPDIR/voxterm_tui.log   # Watch log output
```
