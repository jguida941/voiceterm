# Agents

This file is the canonical SDLC, release, and AI execution policy for this repo.
If any process docs conflict, follow `AGENTS.md` first.

## Purpose

VoiceTerm is a polished, voice-first overlay for AI CLIs.
Primary support: **Codex** and **Claude Code**.
Gemini CLI remains experimental.

Goal of this file: give agents one repeatable process so every task follows the
same execution path with minimal ambiguity.

## Source-of-truth map

| Question | Canonical source |
|---|---|
| What are we executing now? | `dev/active/MASTER_PLAN.md` |
| What active docs exist and what role does each play? | `dev/active/INDEX.md` |
| Where is consolidated Theme Studio + overlay visual planning context? | `dev/active/theme_upgrade.md` |
| How do we run parallel multi-agent worktrees this cycle? | `dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md` |
| What user behavior is current? | `guides/USAGE.md`, `guides/CLI_FLAGS.md` |
| What flags are actually supported? | `src/src/bin/voiceterm/config/cli.rs`, `src/src/config/mod.rs` |
| How do we build/test/release? | `dev/DEVELOPMENT.md`, `dev/scripts/README.md` |
| Where is the developer lifecycle quick guide? | `dev/DEVELOPMENT.md` (`End-to-end lifecycle flow`, `What checks protect us`, `When to push where`) |
| Where are clean-code and Rust-reference rules defined? | `AGENTS.md` (`Engineering quality contract`), `dev/DEVELOPMENT.md` (`Engineering quality review protocol`) |
| What process is mandatory? | `AGENTS.md` |
| What architecture/lifecycle is current? | `dev/ARCHITECTURE.md` |
| Where is process history tracked? | `dev/history/ENGINEERING_EVOLUTION.md` |

## Instruction scope and precedence

When multiple instruction sources exist, apply this precedence:

1. Session-level system/developer/user instructions.
2. The nearest `AGENTS.md` to the files being edited.
3. Ancestor `AGENTS.md` files (including repo root).
4. Linked owner docs from the source-of-truth map.

If subtrees require different workflows, add nested `AGENTS.md` files and keep
them scoped to that subtree.

## Mandatory 12-step SOP (always)

Run this sequence for every task. Do not skip steps.

1. Run session bootstrap checks and load `dev/active/INDEX.md` (`bundle.bootstrap`).
2. Decide scope (`develop` work or `master` release work).
3. Classify task using the task router table.
4. Load only the required context pack listed for your task class.
5. Link or confirm MP scope in `dev/active/MASTER_PLAN.md` before edits.
6. Implement changes and tests.
7. Run the bundle required by your task class.
8. Run matrix tests required by touched risk classes.
9. Update docs/screenshots/ADRs required by governance.
10. Self-review security, memory, errors, concurrency, performance, and style.
11. Push through branch policy and run post-push audit (`bundle.post-push`).
12. Capture handoff summary using `dev/DEVELOPMENT.md` template.

## AI operating contract (required)

1. Be autonomous by default: implement, test, docs, and validation end-to-end.
2. Ask only when required: ambiguous UX/product intent, destructive actions,
   credentials/publishing/tagging, or conflicting policy signals.
3. Stay guarded: do not invent behavior, do not skip required checks.
4. Keep changes scoped: ignore unrelated diffs unless user asks.

## Engineering quality contract (required)

For non-trivial Rust runtime/tooling changes, contributors must:

1. Validate design/implementation against official references before coding:
   - Rust Book: `https://doc.rust-lang.org/book/`
   - Rust Reference: `https://doc.rust-lang.org/reference/`
   - Rust API Guidelines: `https://rust-lang.github.io/api-guidelines/`
   - Rustonomicon (unsafe/FFI): `https://doc.rust-lang.org/nomicon/`
   - Standard library docs: `https://doc.rust-lang.org/std/`
   - Clippy lint index: `https://rust-lang.github.io/rust-clippy/master/`
2. Keep naming and ownership explicit: names should describe behavior, modules
   should keep one responsibility, and public APIs should expose stable
   intent-based contracts.
3. Treat technical debt as explicit debt: `#[allow(...)]`, non-test
   `unwrap/expect`, and oversized files/functions require documented rationale
   and a follow-up MP item when not resolved immediately.
4. Prefer consolidation over duplication: extract shared helpers instead of
   repeating logic across overlays/themes/settings/status surfaces.
5. Record references consulted in handoff for non-trivial Rust changes.

## Branch policy (required)

- `develop`: integration branch for normal feature/fix/docs work.
- `master`: release/tag branch and rare hotfix branch.

Non-release work flow:

1. `git fetch origin`
2. `git checkout develop`
3. `git pull --ff-only origin develop`
4. `git checkout -b feature/<topic>` or `git checkout -b fix/<topic>`
5. Commit and push short-lived branch.
6. Merge short-lived branch into `develop` only after required checks pass.

Release promotion flow:

1. Ensure `develop` checks are green.
2. Merge `develop` into `master`.
3. Tag from `master`.

If a hotfix lands on `master`, back-merge `master` to `develop` promptly.

## Dirty-tree protocol (required)

When `git status --short` is not clean:

1. Do not discard unrelated edits.
2. Edit only files needed for the current task.
3. Use commit-range checks carefully (`--since-ref`) only when the range is
   valid for current branch/repo state.
4. Note unrelated pre-existing changes in handoff when they affect confidence.

## Active-plan onboarding (adding files under `dev/active/`)

When adding any new markdown file under `dev/active/`, this sequence is required:

1. Add an entry in `dev/active/INDEX.md` with:
   - path
   - role (`tracker` | `spec` | `runbook` | `reference`)
   - execution authority
   - MP scope
   - when agents should read it
2. If the file carries execution state, reflect that scope in
   `dev/active/MASTER_PLAN.md` (the only tracker authority).
3. Update discovery links in `AGENTS.md`, `DEV_INDEX.md`, and `dev/README.md`
   if navigation/ownership changed.
4. Run `python3 dev/scripts/check_active_plan_sync.py`.
5. Run `python3 dev/scripts/devctl.py docs-check --strict-tooling`.
6. Run `python3 dev/scripts/devctl.py hygiene`.
7. Commit file + index + governance docs in one change.

## Task router (pick one class)

| User story | Task class | Required bundle |
|---|---|---|
| Changed runtime behavior under `src/**` | Runtime feature/fix | `bundle.runtime` |
| Changed HUD/layout/controls/flags/UI text | HUD/overlay/controls/flags | `bundle.runtime` |
| Touched perf/latency/wake/threading/unsafe/parser boundaries | Risk-sensitive runtime | `bundle.runtime` |
| Changed only user-facing docs | Docs-only | `bundle.docs` |
| Changed tooling/process/CI/governance surfaces | Tooling/process/CI | `bundle.tooling` |
| Preparing/publishing release | Release/tag/distribution | `bundle.release` |

## Context packs (load only what class needs)

### Runtime pack

- `src/src/bin/voiceterm/main.rs`
- `src/src/bin/voiceterm/event_loop.rs`
- `src/src/bin/voiceterm/event_state.rs`
- `src/src/bin/voiceterm/status_line/`
- `src/src/bin/voiceterm/hud/`
- `dev/ARCHITECTURE.md`
- `guides/USAGE.md`
- `guides/CLI_FLAGS.md`

### Voice pack

- `src/src/bin/voiceterm/voice_control/`
- `src/src/audio/`
- `src/src/stt.rs`
- `src/src/bin/voiceterm/wake_word.rs`

### PTY/lifecycle pack

- `src/src/pty_session/`
- `src/src/ipc/`
- `src/src/terminal_restore.rs`

### Tooling/process pack

- `AGENTS.md`
- `dev/active/INDEX.md`
- `dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md`
- `dev/DEVELOPMENT.md`
- `dev/scripts/README.md`
- `dev/history/ENGINEERING_EVOLUTION.md`
- `.github/workflows/`
- `dev/scripts/devctl/commands/`

### Release pack

- `src/Cargo.toml`
- `pypi/pyproject.toml`
- `app/macos/VoiceTerm.app/Contents/Info.plist`
- `dev/CHANGELOG.md`
- `dev/scripts/README.md`

## Command bundles (source of truth)

### `bundle.bootstrap`

```bash
git status --short
git branch --show-current
git remote -v
git log --oneline --decorate -n 10
sed -n '1,220p' dev/active/INDEX.md
python3 dev/scripts/devctl.py list
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.runtime`

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/check_active_plan_sync.py
python3 dev/scripts/check_cli_flags_parity.py
python3 dev/scripts/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/check_code_shape.py
python3 dev/scripts/check_rust_lint_debt.py
python3 dev/scripts/check_rust_best_practices.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.docs`

```bash
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/check_active_plan_sync.py
python3 dev/scripts/check_cli_flags_parity.py
python3 dev/scripts/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/check_code_shape.py
python3 dev/scripts/check_rust_lint_debt.py
python3 dev/scripts/check_rust_best_practices.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.tooling`

```bash
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/check_agents_contract.py
python3 dev/scripts/check_active_plan_sync.py
python3 dev/scripts/check_release_version_parity.py
python3 dev/scripts/check_cli_flags_parity.py
python3 dev/scripts/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/check_code_shape.py
python3 dev/scripts/check_rust_lint_debt.py
python3 dev/scripts/check_rust_best_practices.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.release`

```bash
python3 dev/scripts/devctl.py check --profile release
python3 dev/scripts/devctl.py docs-check --user-facing --strict
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/check_agents_contract.py
python3 dev/scripts/check_active_plan_sync.py
python3 dev/scripts/check_release_version_parity.py
python3 dev/scripts/check_cli_flags_parity.py
python3 dev/scripts/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/check_code_shape.py
python3 dev/scripts/check_rust_lint_debt.py
python3 dev/scripts/check_rust_best_practices.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.post-push`

```bash
git status
git log --oneline --decorate -n 10
python3 dev/scripts/devctl.py status --ci --require-ci --format md
python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/check_active_plan_sync.py
python3 dev/scripts/check_cli_flags_parity.py
python3 dev/scripts/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/check_code_shape.py --since-ref origin/develop
python3 dev/scripts/check_rust_lint_debt.py --since-ref origin/develop
python3 dev/scripts/check_rust_best_practices.py --since-ref origin/develop
find . -maxdepth 1 -type f -name '--*'
```

## Runtime risk matrix (required add-ons)

- Overlay/input/status/HUD changes:
  - `python3 dev/scripts/devctl.py check --profile ci`
  - `cd src && cargo test --bin voiceterm`
- Performance/latency-sensitive changes:
  - `python3 dev/scripts/devctl.py check --profile prepush`
  - `./dev/scripts/tests/measure_latency.sh --voice-only --synthetic`
  - `./dev/scripts/tests/measure_latency.sh --ci-guard`
- Wake-word runtime/detection changes:
  - `bash dev/scripts/tests/wake_word_guard.sh`
  - `python3 dev/scripts/devctl.py check --profile release`
- Threading/lifecycle/memory changes:
  - `cd src && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture`
- Unsafe/FFI lifecycle changes:
  - Update `dev/security/unsafe_governance.md`
  - `cd src && cargo test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd src && cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd src && cargo test stt::tests::transcriber_restores_stderr_after_failed_model_load -- --nocapture`
- Parser/ANSI boundary hardening changes:
  - `cd src && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture`
  - `cd src && cargo test pty_session::tests::prop_find_osc_terminator_respects_bounds -- --nocapture`
  - `cd src && cargo test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes -- --nocapture`
- Mutation-hardening work:
  - `python3 dev/scripts/devctl.py mutation-score --threshold 0.80 --max-age-hours 72`
  - optional: `python3 dev/scripts/devctl.py mutants --module overlay`
- Macro/wizard onboarding changes:
  - `./scripts/macros.sh list`
  - `./scripts/macros.sh install --pack safe-core --project-dir . --overwrite`
  - `./scripts/macros.sh validate --output ./.voiceterm/macros.yaml --project-dir .`
  - Validate `gh auth status -h github.com` behavior when GH macros are included
- Dependency/security-hardening changes:
  - `cargo install cargo-audit --locked`
  - `cd src && (cargo audit --json > ../rustsec-audit.json || true)`
  - `python3 dev/scripts/check_rustsec_policy.py --input rustsec-audit.json --min-cvss 7.0 --fail-on-kind yanked --fail-on-kind unsound --allowlist-file dev/security/rustsec_allowlist.md`

## Release SOP (master only)

Use this exact sequence:

1. Confirm `git checkout master` and clean working tree.
2. Verify version parity:
   - `python3 dev/scripts/check_release_version_parity.py`
   - `src/Cargo.toml` has `version = X.Y.Z`
   - `pypi/pyproject.toml` has `[project].version = X.Y.Z`
   - `app/macos/VoiceTerm.app/Contents/Info.plist` has
     `CFBundleShortVersionString = X.Y.Z` and `CFBundleVersion = X.Y.Z`
   - `dev/CHANGELOG.md` has release heading for `X.Y.Z`
3. Verify release prerequisites:
   - `gh auth status -h github.com`
   - GitHub Actions secret `PYPI_API_TOKEN` exists for `.github/workflows/publish_pypi.yml`
   - GitHub Actions secret `HOMEBREW_TAP_TOKEN` exists for `.github/workflows/publish_homebrew.yml`
   - Optional local fallback: Homebrew tap path is resolvable (`HOMEBREW_VOICETERM_PATH` or `brew --repo`)
4. Run `bundle.release`.
5. Run release tagging and notes:

   ```bash
   python3 dev/scripts/devctl.py release --version <version>
   gh release create v<version> --title "v<version>" --notes-file /tmp/voiceterm-release-v<version>.md
   # PyPI publish runs automatically via .github/workflows/publish_pypi.yml.
   gh run list --workflow publish_pypi.yml --limit 1
   # Homebrew publish runs automatically via .github/workflows/publish_homebrew.yml.
   gh run list --workflow publish_homebrew.yml --limit 1
   # gh run watch <run-id>
   curl -fsSL https://pypi.org/pypi/voiceterm/<version>/json
   # Local fallback (if workflow is unavailable):
   python3 dev/scripts/devctl.py homebrew --version <version>
   ```

6. Run `bundle.post-push`.

Unified control plane alternatives:

```bash
# Workflow-first release path (recommended)
python3 dev/scripts/devctl.py ship --version <version> --verify --tag --notes --github --yes
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1

# Manual fallback (run PyPI/Homebrew locally)
python3 dev/scripts/devctl.py ship --version <version> --pypi --verify-pypi --homebrew --yes
```

## CI lane mapping (what must be green)

| Change signal | Lanes to verify |
|---|---|
| `src/**` runtime changes | `rust_ci.yml` |
| Send mode/macros/transcript delivery | `voice_mode_guard.yml` |
| Wake-word runtime/detection | `wake_word_guard.yml` |
| Perf-sensitive paths | `perf_smoke.yml`, `latency_guard.yml` |
| Long-running worker/thread lifecycle | `memory_guard.yml` |
| Parser/ANSI/OSC boundary logic | `parser_fuzz_guard.yml` |
| Dependency/security policy changes | `security_guard.yml` |
| Coverage reporting / Codecov badge freshness | `coverage.yml` |
| Rust/Python source-file shape drift (God-file growth) | `tooling_control_plane.yml` |
| User docs/markdown changes | `docs_lint.yml` |
| Release preflight verification bundle | `release_preflight.yml` |
| GitHub release publication / PyPI distribution | `publish_pypi.yml` |
| GitHub release publication / Homebrew distribution | `publish_homebrew.yml` |
| Tooling/process/docs governance surfaces (`dev/scripts/**`, `scripts/macro-packs/**`, `.github/workflows/**`, `AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, `Makefile`) | `tooling_control_plane.yml` |
| Mutation-hardening work | `mutation-testing.yml` (scheduled) plus local mutation-score evidence |

## Documentation governance

Always evaluate:

- `dev/CHANGELOG.md` (required for user-facing behavior changes)
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- `README.md`
- `QUICK_START.md`
- `guides/USAGE.md`
- `guides/CLI_FLAGS.md`
- `guides/INSTALL.md`
- `guides/TROUBLESHOOTING.md`
- `dev/ARCHITECTURE.md`
- `dev/DEVELOPMENT.md`
- `dev/scripts/README.md`
- `dev/history/ENGINEERING_EVOLUTION.md` (required for tooling/process/CI shifts)

Plain-language rule for docs updates:

- For user/developer docs (`README.md`, `QUICK_START.md`, `guides/*`, `dev/*`), prefer plain language over policy-heavy wording.
- Use short, direct sentences and concrete commands.
- Keep technical accuracy, but avoid unnecessary jargon.

Update flow:

1. Link/adjust MP item in `dev/active/MASTER_PLAN.md`.
2. Update `dev/CHANGELOG.md` for user-facing behavior.
3. Update user docs for behavior/flag/UI changes.
4. Update developer docs for architecture/workflow/tooling changes.
5. Update screenshots/tables when UI output changes.
6. Add/update ADR when architecture decisions change.

Enforcement commands:

```bash
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --user-facing --strict
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/check_agents_contract.py
python3 dev/scripts/check_active_plan_sync.py
python3 dev/scripts/check_cli_flags_parity.py
python3 dev/scripts/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/check_code_shape.py
python3 dev/scripts/check_rust_lint_debt.py
python3 dev/scripts/check_rust_best_practices.py
```

## Tooling inventory

Canonical tool: `python3 dev/scripts/devctl.py ...`

Core commands:

- `check` (`ci`, `prepush`, `release`, `maintainer-lint`, `quick`, `ai-guard`)
  - Includes automatic orphaned-test cleanup sweep before/after checks (`target/*/deps/voiceterm-*`, detached `PPID=1`).
  - Use `--no-process-sweep-cleanup` only when a run must preserve in-flight test processes.
- `docs-check`
- `hygiene` (archive/ADR/scripts governance plus orphaned `target/debug/deps/voiceterm-*` test-process sweep)
- `mutation-score` (reports outcomes source freshness; optional stale-data gate via `--max-age-hours`)
- `mutants`
- `release`
- `release-notes`
- `ship`
- `pypi`
- `homebrew`
- `status` (supports optional guarded Dev Mode log summaries via `--dev-logs`)
- `report` (supports optional guarded Dev Mode log summaries via `--dev-logs`)
- `list`

Supporting scripts:

- `dev/scripts/check_agents_contract.py`
- `dev/scripts/check_active_plan_sync.py`
- `dev/scripts/check_cli_flags_parity.py`
- `dev/scripts/check_release_version_parity.py`
- `dev/scripts/check_screenshot_integrity.py`
- `dev/scripts/check_code_shape.py`
- `dev/scripts/check_rust_lint_debt.py`
- `dev/scripts/check_rust_best_practices.py`
- `dev/scripts/check_mutation_score.py`
- `dev/scripts/check_rustsec_policy.py`
- `dev/scripts/tests/measure_latency.sh`
- `dev/scripts/tests/wake_word_guard.sh`
- `scripts/macros.sh`

`check_code_shape.py` enforces both language-level limits and path-level
hotspot budgets for Phase 3C decomposition targets.
`check_rust_lint_debt.py` enforces non-regressive growth for `#[allow(...)]`
and non-test `unwrap/expect` call-sites in changed Rust files.
`check_rust_best_practices.py` blocks non-regressive growth of reason-less
`#[allow(...)]`, undocumented `unsafe { ... }` blocks, and public `unsafe fn`
surfaces without `# Safety` docs in changed Rust files.

## CI workflows (reference)

- `rust_ci.yml`
- `voice_mode_guard.yml`
- `wake_word_guard.yml`
- `perf_smoke.yml`
- `latency_guard.yml`
- `memory_guard.yml`
- `mutation-testing.yml`
- `security_guard.yml`
- `parser_fuzz_guard.yml`
- `coverage.yml`
- `docs_lint.yml`
- `lint_hardening.yml`
- `release_preflight.yml`
- `tooling_control_plane.yml`
- `publish_pypi.yml`
- `publish_homebrew.yml`

## CI expansion policy

Add or extend CI when new risk classes are introduced:

- New latency-sensitive logic -> perf/latency guard coverage
- New long-running threads/workers -> memory loop/soak coverage
- New release/distribution mechanics -> release/homebrew/pypi validation
- New user modes/flags -> at least one integration lane exercises them
- New dependency/supply-chain exposure -> security policy coverage
- New parser/control-sequence boundary logic -> property-fuzz coverage
- New/edited workflows must keep action refs SHA-pinned (`uses: org/action@<40-hex>`)
  and declare explicit `permissions:` + `concurrency:` blocks.

## Mandatory self-review checklist

Before calling implementation done, review for:

- Security: injection, unsafe input handling, secret exposure
- Memory: unbounded buffers, leaks, large allocations
- Error handling: unwrap/expect in non-test code, missing failure paths
- Concurrency: deadlocks, races, lock contention
- Performance: unnecessary allocations, blocking in hot paths
- Style/maintenance: clippy warnings, naming, dead code
- API/docs alignment: Rust reference checks captured for non-trivial changes
- CI supply chain: workflow refs pinned, permissions least-privilege, concurrency set

## Handoff paper trail protocol

For substantive sessions, use `dev/DEVELOPMENT.md` -> `Handoff paper trail template`.
Include:

- exact commands run
- docs decisions (`updated` or `no change needed`)
- screenshot decisions
- Rust references consulted (for non-trivial Rust changes)
- follow-up MP IDs

## Archive and ADR policy

- Keep `dev/archive/` immutable (no deletions/rewrites).
- Keep active execution in `dev/active/MASTER_PLAN.md`.
- Use `dev/adr/` for architecture decisions.
- Supersede ADRs with new ADRs; do not rewrite old ADR history.

## End-of-session checklist

- [ ] Mandatory SOP steps were completed.
- [ ] Verification commands passed for scope.
- [ ] Docs updated per governance checklist.
- [ ] `dev/CHANGELOG.md` updated if behavior is user-facing.
- [ ] `dev/active/MASTER_PLAN.md` updated.
- [ ] Follow-up work captured as MP items.
- [ ] Handoff summary captured.
- [ ] Root `--*` artifact check run and clean.
- [ ] Git state is clean or intentionally staged/committed.

## Notes

- `dev/archive/2026-01-29-claudeaudit-completed.md` contains the production readiness checklist.
- Prefer editing existing files over creating new ones.
