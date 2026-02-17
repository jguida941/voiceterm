# Agents

This file is the canonical SDLC and release policy for this repo.

## Product vision

VoiceTerm is a polished, voice-first overlay for AI CLIs. Primary support for
**Codex** and **Claude Code**. Gemini CLI remains experimental (currently not
working). It begins as
a listening/transcription helper but is designed to evolve into a full HUD:
discoverable controls, settings, history, and feedback that enhance the CLI
terminal experience without replacing it.

## Quick navigation

- `CLAUDE.md` (local AI entrypoint; gitignored; points back to this file)
- `DEV_INDEX.md` (root shortcut to developer docs)
- `dev/history/ENGINEERING_EVOLUTION.md` (historical design/process evolution with commit evidence)
- `dev/README.md` (developer index and entrypoint)
- `dev/active/MASTER_PLAN.md` (single canonical strategy + execution plan)
- `dev/active/CODE_QUALITY_EXECUTION_PLAN.md` (active code-quality audit execution detail linked from MASTER_PLAN)
- `dev/active/overlay.md` (market research reference, not execution plan)
- `dev/deferred/` (paused plans not in active execution)
- `dev/archive/2026-02-02-release-audit-completed.md` (completed code audit)
- `dev/archive/2026-02-15-rust-gui-audit.md` (archived Rust hardening audit record)
- `dev/archive/` (completed work entries)
- `dev/archive/README.md` (archive retention and naming policy)
- `dev/ARCHITECTURE.md` (system architecture)
- `dev/DEVELOPMENT.md` (build/test workflow)
- `dev/adr/` (architecture decisions)
- `dev/adr/README.md` (ADR index + status lifecycle policy)
- `dev/CHANGELOG.md` (release history)
- `dev/scripts/README.md` (dev tooling and devctl usage)
- `scripts/README.md` (user install/start/macro scripts)
- `scripts/macros.sh` + `scripts/macro-packs/` (macro onboarding + starter packs)
- `guides/README.md` (user guides index)
- `README.md` and `QUICK_START.md` (user-facing docs)

## Before you start

- Read `dev/active/MASTER_PLAN.md` for current strategy, phase, and release scope.
- Use `dev/active/overlay.md` only for market/competitor reference context.
- Check git status and avoid unrelated changes.
- Confirm scope and whether a release/version bump is needed.

## Branching model (required)

- Long-lived branches: `master` (release/tag branch) and `develop` (active integration branch).
- Start all non-release work from `develop` using short-lived `feature/<topic>` or `fix/<topic>` branches.
- Merge feature/fix branches back into `develop` only after checks pass.
- Promote release candidates from `develop` to `master`, then tag and publish from `master`.
- Delete merged feature/fix branches locally and on origin to keep branch history clean.
- Do not introduce additional long-lived branches unless the change is tracked in `dev/active/MASTER_PLAN.md`.

## SDLC policy (user-facing changes)

- Update docs for user-facing behavior changes (see Documentation Checklist below).
- Add or update an entry in `dev/CHANGELOG.md` with a clear summary and the correct date.
- For releases, bump `src/Cargo.toml` version and align docs with the new version.
- Run verification before shipping. Minimum is a local build of `voiceterm`.
- After substantive feature work, always include the exact local compile and run commands in chat using absolute paths (for example: `cd /Users/jguida941/testing_upgrade/codex-voice/src && cargo build --release --bin voiceterm` and `cd /Users/jguida941/testing_upgrade/codex-voice/src && cargo run --release --bin voiceterm -- --help`).
- Keep UX tables/controls lists in sync with actual behavior.
- If UI output or flags change, update any screenshots or tables that mention them.

## Feature delivery workflow (required)

Apply this sequence for every feature/fix:

1. Add or link a task in `dev/active/MASTER_PLAN.md`.
2. Implement code changes.
3. Add or update tests in the same change.
4. Run verification (`python3 dev/scripts/devctl.py check --profile ci` minimum).
5. Update docs and run `python3 dev/scripts/devctl.py docs-check --user-facing` for user-facing changes.
   - If architecture/workflow/lifecycle/CI/release mechanics changed, update `dev/ARCHITECTURE.md` in the same change.
6. Commit and push only after checks pass.

## One-command feedback loop (recommended)

Use this exact loop so the agent can self-audit continuously:

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/devctl.py status --ci --format md
```

For release work:

1. Bump `src/Cargo.toml` and finalize `dev/CHANGELOG.md`.
2. Tag/push release from `master` via `python3 dev/scripts/devctl.py release --version <version>`.
3. Publish GitHub release using generated notes markdown (`gh release create ... --notes-file /tmp/voiceterm-release-v<version>.md`).
4. Publish PyPI package using `python3 dev/scripts/devctl.py pypi --upload`.
   - Non-interactive publish requires PyPI credentials (for example
     `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<pypi-token>`, or a valid
     `~/.pypirc`/trusted-publishing setup).
5. Verify PyPI publish with `https://pypi.org/pypi/voiceterm/<version>/json`.
6. Update Homebrew tap using `python3 dev/scripts/devctl.py homebrew --version <version>`.

## Post-push audit loop (required)

After each push, run this loop before ending the session:

1. Verify branch/tag state is correct (`git status`, `git log`, tags as needed).
2. Verify CI status (`python3 dev/scripts/devctl.py status --ci --format md` or Actions UI).
   - Confirm all push-triggered workflows for the release commit are green.
   - Check latest `mutation-testing.yml` run status separately (scheduled/manual lane).
   - Explicitly verify scope-critical lanes (at minimum: `rust_ci.yml`, `voice_mode_guard.yml`, `wake_word_guard.yml`, `security_guard.yml`, and `docs_lint.yml`).
3. If CI fails, add/adjust a `MASTER_PLAN` item and rerun checks until green.
4. Re-validate docs alignment for any behavior/flag/UI changes.
   - For post-commit clean trees, use commit-range mode:
     `python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop`
5. Run governance hygiene audit (`python3 dev/scripts/devctl.py hygiene`) and fix any hard failures.

## Testing matrix by change type (required)

- Overlay/input/status/HUD changes:
  - `python3 dev/scripts/devctl.py check --profile ci`
  - `cd src && cargo test --bin voiceterm`
- Performance/latency-sensitive changes:
  - `python3 dev/scripts/devctl.py check --profile prepush`
  - `./dev/scripts/tests/measure_latency.sh --voice-only --synthetic` (baseline runs)
  - `./dev/scripts/tests/measure_latency.sh --ci-guard` (synthetic regression guardrails)
- Wake-word runtime/detection changes:
  - `bash dev/scripts/tests/wake_word_guard.sh`
  - `python3 dev/scripts/devctl.py check --profile release`
- Threading/lifecycle/memory changes:
  - `cd src && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture`
- Unsafe/FFI lifecycle changes:
  - Review and update `dev/security/unsafe_governance.md` for touched invariants/hotspots.
  - `cd src && cargo test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd src && cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd src && cargo test stt::tests::transcriber_restores_stderr_after_failed_model_load -- --nocapture`
- Parser/ANSI boundary hardening changes:
  - `cd src && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture`
  - `cd src && cargo test pty_session::tests::prop_find_osc_terminator_respects_bounds -- --nocapture`
  - `cd src && cargo test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes -- --nocapture`
- Mutation-hardening work:
  - `python3 dev/scripts/devctl.py mutation-score --threshold 0.80`
  - optional: `python3 dev/scripts/devctl.py mutants --module overlay`
- Docs/governance-only changes:
  - `python3 dev/scripts/devctl.py docs-check --user-facing`
  - `python3 dev/scripts/devctl.py hygiene`
- Macro/wizard onboarding changes:
  - `./scripts/macros.sh list`
  - `./scripts/macros.sh install --pack safe-core --project-dir . --overwrite`
  - `./scripts/macros.sh validate --output ./.voiceterm/macros.yaml --project-dir .`
  - If GitHub macros are included, validate `gh auth status -h github.com` behavior (authenticated and warning paths).
- Dependency/security-hardening changes:
  - `cargo install cargo-audit --locked`
  - `cd src && (cargo audit --json > ../rustsec-audit.json || true)`
  - `python3 dev/scripts/check_rustsec_policy.py --input rustsec-audit.json --min-cvss 7.0 --fail-on-kind yanked --fail-on-kind unsound --allowlist-file dev/security/rustsec_allowlist.md`
- Release candidate validation:
  - `python3 dev/scripts/devctl.py check --profile release`

## Code review (mandatory after implementation)

After implementing any code change, review for:

- **Security**: injection, XSS, unsafe input handling, hardcoded secrets
- **Memory**: unbounded buffers, leaks, missing caps, large allocations
- **Errors**: unwrap/expect in non-test code, missing error paths, silent failures
- **Concurrency**: deadlocks, race conditions, lock contention in callbacks
- **Performance**: unnecessary allocations, blocking in async, hot loops
- **Style**: clippy warnings, formatting, naming conventions, dead code

Do not consider implementation complete until self-review passes.

## Verification (local)

Minimum:

```bash
cd src && cargo build --release --bin voiceterm
```

Common checks (run what matches your change):

```bash
# Format + lint
cd src && cargo fmt --all -- --check
cd src && cargo clippy --workspace --all-features -- -D warnings

# Tests
cd src && cargo test
cd src && cargo test --bin voiceterm
```

Targeted checks mirrored in CI:

```bash
# Perf smoke (voice metrics)
cd src && cargo test --no-default-features legacy_tui::tests::perf_smoke_emits_voice_metrics -- --nocapture

# Memory guard (thread cleanup)
cd src && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture

# Mutation testing (heavy; usually on demand)
cd src && cargo mutants --timeout 300 -o mutants.out
python3 ../dev/scripts/check_mutation_score.py --path mutants.out/outcomes.json --threshold 0.80

# Security advisory policy gate (dependency + supply-chain lane parity)
cargo install cargo-audit --locked
cd src && (cargo audit --json > ../rustsec-audit.json || true)
python3 ../dev/scripts/check_rustsec_policy.py --input ../rustsec-audit.json --min-cvss 7.0 --fail-on-kind yanked --fail-on-kind unsound --allowlist-file ../dev/security/rustsec_allowlist.md
```

## Dev CLI (recommended)

Use the unified dev CLI for common workflows:

```bash
# Core checks
python3 dev/scripts/devctl.py check

# CI scope (fmt-check + clippy + tests)
python3 dev/scripts/devctl.py check --profile ci

# Pre-push scope (CI + perf + mem loop)
python3 dev/scripts/devctl.py check --profile prepush

# Maintainer lint-hardening scope (strict clippy subset)
python3 dev/scripts/devctl.py check --profile maintainer-lint

# User-facing docs enforcement
python3 dev/scripts/devctl.py docs-check --user-facing

# Tooling/release docs governance (change-class aware + deprecated-command guard)
python3 dev/scripts/devctl.py docs-check --strict-tooling

# Markdown style/readability checks for key docs
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md

# Mutation score only
python3 dev/scripts/devctl.py mutation-score --threshold 0.80

# Release/distribution control plane
python3 dev/scripts/devctl.py release --version <version>
python3 dev/scripts/devctl.py pypi --upload
python3 dev/scripts/devctl.py homebrew --version <version>
python3 dev/scripts/devctl.py ship --version <version> --verify --tag --notes --github --pypi --homebrew --verify-pypi
```

Legacy shell scripts under `dev/scripts/*.sh` are transitional adapters. For maintainer workflows, prefer `devctl` commands first.

## CI workflows (reference)

- `rust_ci.yml`: format, clippy, and test for `src/`.
- `voice_mode_guard.yml`: targeted macros-toggle and send-mode regression tests.
- `wake_word_guard.yml`: wake-word regression + soak guardrails (false-positive and matcher-latency gates).
- `perf_smoke.yml`: perf smoke test and voice metrics verification.
- `latency_guard.yml`: synthetic latency regression guardrails.
- `memory_guard.yml`: repeated memory guard test.
- `mutation-testing.yml`: scheduled/manual mutation testing with threshold check.
- `security_guard.yml`: RustSec advisory policy lane (high/critical CVSS threshold + yanked/unsound fail list).
- `parser_fuzz_guard.yml`: property-fuzz coverage for PTY parser/ANSI-OSC boundary handling.
- `docs_lint.yml`: markdownlint checks for published user/developer docs.
- `lint_hardening.yml`: focused maintainer lint-hardening lane (`devctl check --profile maintainer-lint`) for high-value clippy risks (redundant clones/closures, risky wrap casts, dead-code drift).
- `tooling_control_plane.yml`: devctl unit tests, shell adapter integrity, and docs-policy/deprecated-command guard for maintainer tooling surfaces.

## CI expansion policy

Add or update CI when new risk classes are introduced:

- New latency-sensitive logic: add/extend perf or latency guard coverage.
- New long-running threads/background workers: add loop/soak memory guards.
- New release/distribution mechanics: add validation for release/homebrew scripts.
- New user modes/flags: ensure at least one integration lane exercises them.
- New dependency/supply-chain exposure: add or update security advisory policy coverage.
- New parser/terminal-control boundary logic: add or update property-fuzz coverage lanes.

## Documentation checklist

When making changes, check which docs need updates:

**Always check:**

| Doc | Update when |
|-----|-------------|
| `dev/CHANGELOG.md` | **Every user-facing change** (required) |
| `README.md` | Project structure, quick start, or major features change |
| `QUICK_START.md` | Install steps or basic usage changes |

**User-facing behavior:**

| Doc | Update when |
|-----|-------------|
| `guides/USAGE.md` | Controls, modes, status messages, or UX changes |
| `guides/CLI_FLAGS.md` | Any flag added, removed, or default changed |
| `guides/INSTALL.md` | Install methods, dependencies, or setup steps change |
| `guides/TROUBLESHOOTING.md` | New known issues or fixes discovered |

**Developer/architecture:**

| Doc | Update when |
|-----|-------------|
| `dev/ARCHITECTURE.md` | Module structure, data flow, design changes, **or any workflow/lifecycle/CI/release mechanics added/changed/removed** |
| `dev/DEVELOPMENT.md` | Build process, testing, or contribution workflow changes |
| `dev/adr/` | Significant design decisions (see ADRs below) |

**Do not skip docs.** Missing doc updates cause drift and user confusion.

## Documentation update flow (apply on behavior changes)

1. Scan `dev/active/MASTER_PLAN.md` for related items and update it if scope changes.
2. Update `dev/CHANGELOG.md` for user-facing changes with the correct date.
3. Review user-facing docs: `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`,
   `guides/INSTALL.md`, `guides/TROUBLESHOOTING.md`.
   - Use `python3 dev/scripts/devctl.py docs-check --user-facing` to validate doc coverage.
4. Update developer docs if needed: `dev/ARCHITECTURE.md`, `dev/DEVELOPMENT.md`.
   - `dev/ARCHITECTURE.md` is mandatory when architecture/workflow mechanics changed.
5. If UI output or flags change, update any screenshots/tables that mention them.
6. If a change introduces a new architectural decision, add an ADR in `dev/adr/` and update
   the ADR index.

## Documentation sync protocol (every push)

On every push, review docs and explicitly decide "updated" or "no change needed":

- Core: `dev/CHANGELOG.md`, `dev/active/MASTER_PLAN.md`
- User docs: `README.md`, `QUICK_START.md`, `guides/USAGE.md`, `guides/CLI_FLAGS.md`,
  `guides/INSTALL.md`, `guides/TROUBLESHOOTING.md`
- Dev docs: `dev/ARCHITECTURE.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`

Enforcement commands:

- `python3 dev/scripts/devctl.py docs-check --user-facing`
- For clean trees / post-commit audits, compare a commit range:
  `python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop`
- Use strict mode for broad UX/flag changes:
  `python3 dev/scripts/devctl.py docs-check --user-facing --strict`

## ADRs (architecture decisions)

- Use `dev/adr/` for architecture-level decisions or cross-module changes.
- Include context, decision, and consequences.
- Use `NNNN-short-title.md` (zero-padded) and keep `dev/adr/README.md` index/status in sync.
- If a decision is replaced, create a new ADR and mark the older ADR `Status: Superseded`
  with `Superseded-by: ADR NNNN`.
- Do not rewrite historical ADR decisions; supersede them.

## Archive retention policy

- Keep `dev/archive/` entries as immutable historical records; do not delete completed audits/plans
  to reduce context size.
- Keep active execution in `dev/active/MASTER_PLAN.md`; archive files are reference/history only.
- If archive volume grows, add summary/index docs instead of deleting source records.

## Active work tracking

- Strategy, execution, and release tasks all live in `dev/active/MASTER_PLAN.md`.
- `dev/active/overlay.md` is reference-only market research.
- Deferred plans live in `dev/deferred/`.
- Move completed work to `dev/archive/` with a dated entry.

## Releases

**Using devctl (recommended):**

```bash
# 1. Update version in src/Cargo.toml
# 2. Update dev/CHANGELOG.md with release notes
# 3. Commit all changes
# 4. Tag + notes
python3 dev/scripts/devctl.py release --version <version>

# Optional single-command control-plane flow:
python3 dev/scripts/devctl.py ship --version <version> --verify --tag --notes --github --pypi --homebrew --verify-pypi

# 5. Create GitHub release (after tag is pushed)
gh release create v<version> --title "v<version>" --notes-file /tmp/voiceterm-release-v<version>.md

# 6. Publish PyPI package
python3 dev/scripts/devctl.py pypi --upload

# 7. Verify PyPI publish
curl -fsSL https://pypi.org/pypi/voiceterm/<version>/json | rg '"version"'

# 8. Update Homebrew tap
python3 dev/scripts/devctl.py homebrew --version <version>
```

Legacy wrappers (`dev/scripts/release.sh`, `dev/scripts/publish-pypi.sh`, `dev/scripts/update-homebrew.sh`) remain as transitional adapters and route into `devctl`.

**Manual steps (if scripts fail):**

- Bump `src/Cargo.toml` version and align docs with the new version.
- Tag: `git tag v<version> && git push origin v<version>`
- Update the Homebrew tap formula (version + checksum) and push it.
- Verify a fresh install after updating the tap (`brew install` or `brew reinstall`).

## Homebrew tap

Tap repo: <https://github.com/jguida941/homebrew-voiceterm>

**Automated update (recommended):**

```bash
python3 dev/scripts/devctl.py homebrew --version <version>
```

This script:

- Fetches SHA256 from the GitHub release tarball
- Updates the formula with new version and checksum
- Commits and pushes to the tap repo

**Manual update process:**

1. **Get SHA256 of release tarball:**

   ```bash
   curl -sL https://github.com/jguida941/voiceterm/archive/refs/tags/v<version>.tar.gz | shasum -a 256
   ```

2. **Update formula** in homebrew-voiceterm repo:
   - Update `version` to new version
   - Update `url` to new tag
   - Update `sha256` with new checksum

3. **Push formula changes** to tap repo.

4. **Verify installation:**

   ```bash
   brew update
   brew reinstall voiceterm
   voiceterm --version
   ```

## Scope and non-goals

- Scope: Voice HUD overlay, Rust TUI, voice pipeline, and supporting docs/scripts for AI CLIs.
- Non-goals: hosted services, cloud telemetry, or altering upstream AI CLI behavior.

## End-of-session checklist

- [ ] Code changes have been self-reviewed (see Code Review section)
- [ ] Verification commands passed for changes made
- [ ] Documentation updated per Documentation Checklist
- [ ] `dev/CHANGELOG.md` updated if user-facing behavior changed
- [ ] `dev/active/MASTER_PLAN.md` updated and completed work moved to `dev/archive/`
- [ ] New issues discovered added to `dev/active/MASTER_PLAN.md`
- [ ] Follow-ups captured as new master plan items
- [ ] Git status is clean or changes are committed/stashed

## Key files reference

| Purpose | Location |
|---------|----------|
| Main binary | `src/src/bin/voiceterm/main.rs` |
| App state | `src/src/legacy_tui/` |
| Audio pipeline | `src/src/audio/` |
| PTY handling | `src/src/pty_session/` |
| Codex backend | `src/src/codex/` |
| Config | `src/src/config/` |
| IPC | `src/src/ipc/` |
| STT/Whisper | `src/src/stt.rs` |
| Version | `src/Cargo.toml` |
| macOS app plist | `app/macos/VoiceTerm.app/Contents/Info.plist` |

## Notes

- `dev/archive/2026-01-29-claudeaudit-completed.md` contains the production readiness checklist.
- If UI output or flags change, update any screenshots or tables that mention them.
- Always prefer editing existing files over creating new ones.
