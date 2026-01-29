# SDLC Policy

This repo follows the SDLC expectations below for user-facing changes and releases.

## User-facing changes

- Update docs for user-facing behavior changes (at minimum `README.md` and `QUICK_START.md`).
- Add or update a `docs/CHANGELOG.md` entry with a clear summary and the correct date.
- Run verification before shipping. Minimum is a local build of `codex-voice`, plus any relevant tests.
- Keep UX tables/controls lists in sync with actual behavior.
- If UI output or flags change, update any screenshots or tables that mention them.

## Verification (local)

Minimum:

```bash
cd rust_tui && cargo build --release --bin codex-voice
```

Common checks (run what matches your change):

```bash
# Format + lint
cd rust_tui && cargo fmt --all -- --check
cd rust_tui && cargo clippy --workspace --all-features -- -D warnings

# Tests
cd rust_tui && cargo test
cd rust_tui && cargo test --bin codex-voice
```

Targeted checks mirrored in CI:

```bash
# Perf smoke (voice metrics)
cd rust_tui && cargo test --no-default-features app::tests::perf_smoke_emits_voice_metrics -- --nocapture

# Memory guard (thread cleanup)
cd rust_tui && cargo test --no-default-features app::tests::memory_guard_backend_threads_drop -- --nocapture

# Mutation testing (heavy; usually on demand)
cd rust_tui && cargo mutants --timeout 300 -o mutants.out
python3 ../scripts/check_mutation_score.py --path mutants.out/outcomes.json --threshold 0.80
```

## CI workflows (reference)

- `rust_tui.yml`: format, clippy, and test for `rust_tui/`.
- `perf_smoke.yml`: perf smoke test and voice metrics verification.
- `memory_guard.yml`: repeated memory guard test.
- `mutation-testing.yml`: scheduled mutation testing with threshold check.

## Releases

- Bump `rust_tui/Cargo.toml` version and align docs with the new version.
- Update the Homebrew tap formula (version + checksum) and push it.
- Verify a fresh install after updating the tap (`brew install` or `brew reinstall`).

## Homebrew tap

- https://github.com/jguida941/homebrew-codex-voice
