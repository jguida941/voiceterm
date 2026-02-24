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
| Where is active-doc execution authority vs reference-only scope defined? | `dev/active/INDEX.md` (`Role`, `Execution authority`, `When agents read`) |
| Where is consolidated Theme Studio + overlay visual planning context? | `dev/active/theme_upgrade.md` |
| Where is long-range phase-2 research context? | `dev/active/phase2.md` |
| Where is the `devctl` reporting + CIHub integration roadmap? | `dev/active/devctl_reporting_upgrade.md` |
| Where is the autonomous loop + mobile control-plane execution spec? | `dev/active/autonomous_control_plane.md` |
| Where is the loop-output-to-chat coordination runbook? | `dev/active/loop_chat_bridge.md` |
| Where is the Rust workspace path/layout migration execution plan? | `dev/active/rust_workspace_layout_migration.md` |
| Where are external repo federation links/import rules (`code-link-ide`, `ci-cd-hub`)? | `dev/integrations/EXTERNAL_REPOS.md` |
| Where do we track repeated manual friction and automation debt? | `dev/audits/AUTOMATION_DEBT_REGISTER.md` |
| Where is the baseline full-surface audit runbook/checklist? | `dev/audits/2026-02-24-autonomy-baseline-audit.md` |
| Where are audit metrics definitions (AI vs script share, automation coverage, charts)? | `dev/audits/METRICS_SCHEMA.md` |
| How do we run parallel multi-agent worktrees this cycle? | `dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md` |
| Where are `devctl` command semantics and examples? | `dev/scripts/README.md` |
| Where is the devctl automation playbook? | `dev/DEVCTL_AUTOGUIDE.md` |
| Where is the remediation scaffold template used by guard-driven Rust audits? | `dev/config/templates/rust_audit_findings_template.md` |
| What user behavior is current? | `guides/USAGE.md`, `guides/CLI_FLAGS.md` |
| What flags are actually supported? | `rust/src/bin/voiceterm/config/cli.rs`, `rust/src/config/mod.rs` |
| How do we build/test/release? | `dev/DEVELOPMENT.md`, `dev/scripts/README.md` |
| Where is the developer lifecycle quick guide? | `dev/DEVELOPMENT.md` (`End-to-end lifecycle flow`, `What checks protect us`, `When to push where`) |
| Where are clean-code and Rust-reference rules defined? | `AGENTS.md` (`Engineering quality contract`), `dev/DEVELOPMENT.md` (`Engineering quality review protocol`) |
| What process is mandatory? | `AGENTS.md` |
| What architecture/lifecycle is current? | `dev/ARCHITECTURE.md` |
| Where are CI lane implementations and release publishers? | `.github/workflows/` |
| Where is process history tracked? | `dev/history/ENGINEERING_EVOLUTION.md` |

## Instruction scope and precedence

When multiple instruction sources exist, apply this precedence:

1. Session-level system/developer/user instructions.
2. The nearest `AGENTS.md` to the files being edited.
3. Ancestor `AGENTS.md` files (including repo root).
4. Linked owner docs from the source-of-truth map.

If subtrees require different workflows, add nested `AGENTS.md` files and keep
them scoped to that subtree.

## Autonomous execution route (required)

Use this route to run end-to-end without ambiguity:

1. Load `dev/active/INDEX.md`, then `dev/active/MASTER_PLAN.md`.
2. Use `INDEX.md` role/authority fields to decide which active docs are required:
   - `tracker` is execution authority.
   - `spec` is read when matching MP scope is in play.
   - `runbook` is read for active multi-agent cycles.
   - `reference` is context-only; do not treat as execution state.
3. Select task class in the router table and run the matching command bundle.
4. Apply risk-matrix add-ons for touched runtime risk classes.
5. Run docs-governance/self-review/end-of-session checklist before handoff.

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

## Execution-plan traceability (required)

For non-trivial work (runtime/tooling/process/CI/release), execution must be
anchored in an active tracked plan doc under `dev/active/`.

1. Create or update the relevant execution-plan doc before implementation
   (for example `dev/active/autonomous_control_plane.md`).
2. Execution-plan docs must include the marker line:
   `Execution plan contract: required`.
3. Execution-plan docs must include these sections:
   - `## Scope`
   - `## Execution Checklist`
   - `## Progress Log`
   - `## Audit Evidence`
4. The associated MP scope must be present in both `dev/active/INDEX.md` and
   `dev/active/MASTER_PLAN.md`.
4.1 In multi-agent runs, progress/decisions must be written into the active
    plan markdown and/or `MASTER_PLAN` updates; hidden memory-only coordination
    is not acceptable execution state.
5. `python3 dev/scripts/checks/check_active_plan_sync.py` is the enforcement
   gate and must pass before merge.

## Continuous improvement loop (required)

Use a repeat-to-automate loop so the toolchain gets stronger after every run.

1. Record friction points in the active-plan progress log and/or handoff notes
   for every non-trivial execution session.
2. If the same workaround/manual step repeats 2+ times in the same MP scope,
   resolve it before closure by:
   - automating it as a guarded `devctl` command/workflow/check with tests, or
   - logging it as explicit debt in `dev/audits/AUTOMATION_DEBT_REGISTER.md`
     with owner, risk, and exit criteria.
3. "Cannot automate yet" is acceptable only with a documented reason and a
   guard path (checklist/runbook entry that prevents unsafe execution).
4. When automation lands, update command/docs surfaces in the same change
   (`AGENTS.md`, `dev/scripts/README.md`, `dev/DEVCTL_AUTOGUIDE.md` as needed).
5. Baseline full-surface audit execution starts from
   `dev/audits/2026-02-24-autonomy-baseline-audit.md` and should be copied
   forward for each new audit cycle.
6. Audit cycles should emit quantitative metrics from event logs
   (`automation_coverage_pct`, `script_only_pct`, `ai_assisted_pct`,
   `human_manual_pct`, `success_rate_pct`) and chart outputs via
   `python3 dev/scripts/audits/audit_metrics.py`.

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

Routine helper:

- `python3 dev/scripts/devctl.py sync --push` can audit/sync `develop` +
  `master` + current branch with clean-tree and fast-forward guards.

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
2.1 If the file is an execution plan, include marker
    `Execution plan contract: required` and sections `Scope`,
    `Execution Checklist`, `Progress Log`, and `Audit Evidence`.
3. Update discovery links in `AGENTS.md`, `DEV_INDEX.md`, and `dev/README.md`
   if navigation/ownership changed.
4. Run `python3 dev/scripts/checks/check_active_plan_sync.py`.
5. Run `python3 dev/scripts/checks/check_multi_agent_sync.py`.
6. Run `python3 dev/scripts/devctl.py docs-check --strict-tooling`.
7. Run `python3 dev/scripts/devctl.py hygiene`.
8. Commit file + index + governance docs in one change.

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

- `rust/src/bin/voiceterm/main.rs`
- `rust/src/bin/voiceterm/event_loop.rs`
- `rust/src/bin/voiceterm/event_state.rs`
- `rust/src/bin/voiceterm/status_line/`
- `rust/src/bin/voiceterm/hud/`
- `dev/ARCHITECTURE.md`
- `guides/USAGE.md`
- `guides/CLI_FLAGS.md`

### Voice pack

- `rust/src/bin/voiceterm/voice_control/`
- `rust/src/audio/`
- `rust/src/stt.rs`
- `rust/src/bin/voiceterm/wake_word.rs`

### PTY/lifecycle pack

- `rust/src/pty_session/`
- `rust/src/ipc/`
- `rust/src/terminal_restore.rs`

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

- `rust/Cargo.toml`
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
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.docs`

```bash
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.tooling`

```bash
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_release_version_parity.py
python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.release`

```bash
python3 dev/scripts/devctl.py check --profile release
python3 dev/scripts/devctl.py docs-check --user-facing --strict
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_release_version_parity.py
python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

### `bundle.post-push`

```bash
git status
git log --oneline --decorate -n 10
python3 dev/scripts/devctl.py status --ci --require-ci --format md
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 120 --format md
python3 dev/scripts/devctl.py docs-check --user-facing --since-ref origin/develop
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_lint_debt.py --since-ref origin/develop
python3 dev/scripts/checks/check_rust_best_practices.py --since-ref origin/develop
find . -maxdepth 1 -type f -name '--*'
```

## Runtime risk matrix (required add-ons)

- Overlay/input/status/HUD changes:
  - `python3 dev/scripts/devctl.py check --profile ci`
  - `cd rust && cargo test --bin voiceterm`
- Performance/latency-sensitive changes:
  - `python3 dev/scripts/devctl.py check --profile prepush`
  - `./dev/scripts/tests/measure_latency.sh --voice-only --synthetic`
  - `./dev/scripts/tests/measure_latency.sh --ci-guard`
- Wake-word runtime/detection changes:
  - `bash dev/scripts/tests/wake_word_guard.sh`
  - `python3 dev/scripts/devctl.py check --profile release`
- Threading/lifecycle/memory changes:
  - `cd rust && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture`
- Unsafe/FFI lifecycle changes:
  - Update `dev/security/unsafe_governance.md`
  - `cd rust && cargo test pty_session::tests::pty_cli_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd rust && cargo test pty_session::tests::pty_overlay_session_drop_terminates_descendants_in_process_group -- --nocapture`
  - `cd rust && cargo test stt::tests::transcriber_restores_stderr_after_failed_model_load -- --nocapture`
- Parser/ANSI boundary hardening changes:
  - `cd rust && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture`
  - `cd rust && cargo test pty_session::tests::prop_find_osc_terminator_respects_bounds -- --nocapture`
  - `cd rust && cargo test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes -- --nocapture`
- Mutation-hardening work:
  - `python3 dev/scripts/devctl.py mutation-score --threshold 0.80 --max-age-hours 72`
  - optional: `python3 dev/scripts/devctl.py mutants --module overlay`
- Macro/wizard onboarding changes:
  - `./scripts/macros.sh list`
  - `./scripts/macros.sh install --pack safe-core --project-dir . --overwrite`
  - `./scripts/macros.sh validate --output ./.voiceterm/macros.yaml --project-dir .`
  - Validate `gh auth status -h github.com` behavior when GH macros are included
- Dependency/security-hardening changes:
  - `python3 dev/scripts/devctl.py security`
  - optional strict workflow scan: `python3 dev/scripts/devctl.py security --with-zizmor --require-optional-tools`
  - fallback manual path:
    `cargo install cargo-audit --locked`,
    `cd rust && (cargo audit --json > ../rustsec-audit.json || true)`,
    `python3 dev/scripts/checks/check_rustsec_policy.py --input rustsec-audit.json --min-cvss 7.0 --fail-on-kind yanked --fail-on-kind unsound --allowlist-file dev/security/rustsec_allowlist.md`

## Release SOP (master only)

Use this exact sequence:

1. Confirm `git checkout master` and clean working tree.
2. Verify version parity:
   - `python3 dev/scripts/checks/check_release_version_parity.py`
   - `rust/Cargo.toml` has `version = X.Y.Z`
   - `pypi/pyproject.toml` has `[project].version = X.Y.Z`
   - `app/macos/VoiceTerm.app/Contents/Info.plist` has
     `CFBundleShortVersionString = X.Y.Z` and `CFBundleVersion = X.Y.Z`
   - `dev/CHANGELOG.md` has release heading for `X.Y.Z`
   - `dev/active/MASTER_PLAN.md` Status Snapshot has
     `Last tagged release: vX.Y.Z` and `Current release target: post-vX.Y.Z planning`
3. Verify release prerequisites:
   - `gh auth status -h github.com`
   - Latest `CodeRabbit Triage Bridge` run for release commit is `success` (no unresolved medium/high CodeRabbit findings)
   - `python3 dev/scripts/checks/check_coderabbit_gate.py --branch master`
   - Latest `CodeRabbit Ralph Loop` run for release commit is `success`
   - `python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master`
   - GitHub Actions secret `PYPI_API_TOKEN` exists for `.github/workflows/publish_pypi.yml`
   - GitHub Actions secret `HOMEBREW_TAP_TOKEN` exists for `.github/workflows/publish_homebrew.yml`
   - Optional local fallback: Homebrew tap path is resolvable (`HOMEBREW_VOICETERM_PATH` or `brew --repo`)
4. Run `bundle.release`.
5. Run release tagging and notes:

   ```bash
   # Optional one-step metadata prep (Cargo/PyPI/app plist/changelog):
   python3 dev/scripts/devctl.py ship --version <version> --prepare-release
   python3 dev/scripts/devctl.py release --version <version>
   gh release create v<version> --title "v<version>" --notes-file /tmp/voiceterm-release-v<version>.md
   # PyPI publish runs automatically via .github/workflows/publish_pypi.yml.
   gh run list --workflow publish_pypi.yml --limit 1
   # Homebrew publish runs automatically via .github/workflows/publish_homebrew.yml.
   gh run list --workflow publish_homebrew.yml --limit 1
   # Native release binaries publish via .github/workflows/publish_release_binaries.yml.
   gh run list --workflow publish_release_binaries.yml --limit 1
   # Release source provenance attestations run via .github/workflows/release_attestation.yml.
   gh run list --workflow release_attestation.yml --limit 1
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
# Workflow-first release path with auto metadata prep
python3 dev/scripts/devctl.py ship --version <version> --prepare-release --verify --tag --notes --github --yes
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow publish_release_binaries.yml --limit 1
gh run list --workflow release_attestation.yml --limit 1

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
| Dependency manifest/lockfile deltas in PRs | `dependency_review.yml` |
| Workflow syntax + policy drift | `workflow_lint.yml` |
| AI PR review signal ingestion and owner/severity rollups | `coderabbit_triage.yml` |
| Bounded AI remediation loop for CodeRabbit medium/high backlog | `coderabbit_ralph_loop.yml` |
| Bounded autonomous controller loop (checkpoint packets + queue artifacts + optional promote PR) | `autonomy_controller.yml` |
| Guarded plan-scoped autonomy swarm pipeline (scope load + swarm + reviewer + governance + plan evidence append) | `autonomy_run.yml` |
| Bounded mutation remediation loop (report-only default, optional policy-gated fix mode) | `mutation_ralph_loop.yml` |
| Release commit guard for unresolved CodeRabbit medium/high findings | `coderabbit_triage.yml`, `coderabbit_ralph_loop.yml`, `release_preflight.yml`, `publish_pypi.yml`, `publish_homebrew.yml`, `publish_release_binaries.yml`, `release_attestation.yml` |
| Supply-chain posture drift | `scorecard.yml` |
| Coverage reporting / Codecov badge freshness | `coverage.yml` |
| Rust/Python source-file shape drift (God-file growth) | `tooling_control_plane.yml` |
| Multi-agent instruction/ack timers and stale-lane accountability | `tooling_control_plane.yml`, `orchestrator_watchdog.yml` |
| User docs/markdown changes | `docs_lint.yml` |
| Release preflight verification bundle | `release_preflight.yml` |
| GitHub release publication / PyPI distribution | `publish_pypi.yml` |
| GitHub release publication / Homebrew distribution | `publish_homebrew.yml` |
| GitHub release publication / native binaries | `publish_release_binaries.yml` |
| Release source provenance attestation | `release_attestation.yml` |
| Any non-success CI workflow run | `failure_triage.yml` (workflow-run triage bundle + artifact upload; trusted same-repo events only, branch allowlist defaults to `develop,master` and can be overridden with repo variable `FAILURE_TRIAGE_BRANCHES`) |
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
- `dev/audits/README.md`
- `dev/audits/AUTOMATION_DEBT_REGISTER.md`
- `dev/audits/METRICS_SCHEMA.md`
- `dev/integrations/EXTERNAL_REPOS.md`
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
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
```

## Tooling inventory

Canonical tool: `python3 dev/scripts/devctl.py ...`

Core commands:

- `check` (`ci`, `prepush`, `release`, `maintainer-lint`, `quick`, `ai-guard`)
  - Runs setup gates (`fmt`, `clippy`, AI guard scripts) and test/build phases in parallel batches by default.
  - Use `--parallel-workers <n>` to tune worker count, or `--no-parallel` to force sequential execution.
  - Includes automatic orphaned/stale test-process cleanup before/after checks (`target/*/deps/voiceterm-*`, detached `PPID=1`, plus stale active runners aged `>=600s`).
  - Use `--no-process-sweep-cleanup` only when a run must preserve in-flight test processes.
- `docs-check`
  - `--strict-tooling` also runs active-plan + multi-agent sync gates, markdown metadata-header checks, plus stale-path audit so tooling/process changes cannot bypass active-doc/lane governance.
  - Check-script moves must be reflected in `dev/scripts/devctl/script_catalog.py` so strict-tooling path audits stay canonical.
- `hygiene` (archive/ADR/scripts governance plus orphaned/stale `target/debug/deps/voiceterm-*` test-process sweep; optional `--fix` removes detected `dev/scripts/**/__pycache__` directories)
- `path-audit` (stale-reference scan for legacy check-script paths; excludes `dev/archive/`)
- `path-rewrite` (auto-rewrite legacy check-script paths to canonical registry targets; use `--dry-run` first)
- `sync` (branch-sync automation with clean-tree, remote-ref, and `--ff-only` pull guards; optional `--push` for ahead branches)
- `integrations-sync` (policy-guarded sync/status for pinned external sources under `integrations/`; supports remote update and audit logging)
- `integrations-import` (allowlisted selective importer from pinned external sources into controlled destination roots with JSONL audit records)
- `cihub-setup` (allowlisted CIHub setup runner with preview/apply modes, capability probing, and strict unsupported-step gating)
- `security` (RustSec policy gate with optional workflow scan support via `--with-zizmor`, optional GitHub code-scanning alert gate via `--with-codeql-alerts`, and Python scope control via `--python-scope auto|changed|all`)
- `mutation-score` (reports outcomes source freshness; optional stale-data gate via `--max-age-hours`)
- `mutants`
- `release`
- `release-notes`
- `ship`
- `pypi`
- `homebrew` (tap formula URL/version/checksum updates plus canonical `desc` text sync)
- `status` (supports optional guarded Dev Mode log summaries via `--dev-logs`)
- `orchestrate-status` (single-view orchestrator summary for active-plan sync + multi-agent coordination guard state)
- `orchestrate-watch` (SLA watchdog for stale agent updates and overdue instruction ACKs)
- `report` (supports optional guarded Dev Mode log summaries via `--dev-logs`)
- `triage` (human/AI triage output with optional CIHub artifact ingestion/bundle emission for owner/risk routing)
- `triage-loop` (bounded CodeRabbit medium/high loop with mode controls: `report-only`, `plan-then-fix`, `fix-only`; emits md/json bundles and optional MASTER_PLAN proposal artifacts)
- `loop-packet` (builds a guarded terminal feedback packet from triage/loop JSON sources for dev-mode draft injection with freshness/risk/auto-send-eligibility gates)
- `autonomy-loop` (bounded controller loop that orchestrates triage-loop + loop-packet rounds, emits checkpoint packets/queue artifacts, writes phone-ready status snapshots under `dev/reports/autonomy/queue/phone/`, and enforces policy-driven stop reasons; non-dry-run write modes require `AUTONOMY_MODE=operate`)
- `autonomy-benchmark` (active-plan-scoped swarm matrix runner for tactic/swarm-size tradeoff analysis; executes `autonomy-swarm` batches across configurable count/tactic grids, emits per-swarm and per-scenario productivity metrics, and writes benchmark bundles under `dev/reports/autonomy/benchmarks/<label>/`; non-report modes require `--fix-command`)
- `autonomy-run` (guarded plan-scoped autonomy pipeline that derives next unchecked plan steps, runs `autonomy-swarm` with reviewer + post-audit defaults, executes governance checks (`check_active_plan_sync`, `check_multi_agent_sync`, `docs-check --strict-tooling`, `orchestrate-status/watch`), and appends run evidence to plan-doc `Progress Log` + `Audit Evidence`; non-report modes require `--fix-command`)
- `autonomy-report` (builds a human-readable autonomy digest bundle from loop/watch artifacts under `dev/reports/autonomy/library/<label>` with summary markdown/json, copied sources, and optional matplotlib charts)
- `phone-status` (renders iPhone/SSH-safe autonomy status projections from `dev/reports/autonomy/queue/phone/latest.json` with selectable views `full|compact|trace|actions` and optional projection bundle emission: `full.json`, `compact.json`, `trace.ndjson`, `actions.json`, `latest.md`)
- `controller-action` (policy-gated operator action surface for `refresh-status`, `dispatch-report-only`, `pause-loop`, and `resume-loop`; dispatch and mode writes are bounded by workflow/branch allowlists and autonomy mode gates, with optional dry-run and mode-state artifact output)
- `autonomy-swarm` (adaptive multi-agent orchestration wrapper with metadata-driven worker sizing, optional `--plan-only` allocation mode, bounded per-agent autonomy-loop fanout, default reserved `AGENT-REVIEW` lane for post-audit review when execution runs with more than one lane, per-run swarm summary bundles under `dev/reports/autonomy/swarms/<label>/`, and default post-audit digest bundles under `dev/reports/autonomy/library/<label>-digest/`; disable with `--no-post-audit` and/or `--no-reviewer-lane`; non-report modes require `--fix-command`)
- `mutation-loop` (bounded mutation remediation loop with mode controls: `report-only`, `plan-then-fix`, `fix-only`; emits md/json/playbook bundles and supports policy-gated fix execution)
- `failure-cleanup` (guarded cleanup for local failure triage bundles under `dev/reports/failures`; default path-root guard, optional `--allow-outside-failure-root` constrained to `dev/reports/**`, CI-green gating with optional `--ci-branch`/`--ci-workflow`/`--ci-event`/`--ci-sha` filters, plus `--dry-run` and confirmation)
- `audit-scaffold`
  - Builds/updates `dev/active/RUST_AUDIT_FINDINGS.md` from Rust/Python guard failures.
  - Auto-runs when AI-guard checks fail.
  - Run manually when you want a fresh findings file or a commit-range scoped view.
- `list`

### Quick command intent (plain language)

| Command | Run it when | Why |
|---|---|---|
| `python3 dev/scripts/devctl.py check --profile ci` | before a normal push | catches compile/test/lint issues early |
| `python3 dev/scripts/devctl.py docs-check --user-facing` | user behavior/docs changed | keeps user docs aligned with behavior |
| `python3 dev/scripts/devctl.py docs-check --strict-tooling` | tooling/process/CI changed | enforces governance and active-plan sync |
| `python3 dev/scripts/devctl.py integrations-sync --status-only --format md` | you want current external source pins (`code-link-ide`, `ci-cd-hub`) before import/sync work | gives auditable source SHA + status visibility in one command |
| `python3 dev/scripts/devctl.py integrations-import --list-profiles --format md` | you want to import reusable upstream surfaces safely | shows allowlisted source/profile mappings before any file writes |
| `python3 dev/scripts/devctl.py triage-loop --branch develop --mode plan-then-fix --max-attempts 3 --format md` | you want bounded CodeRabbit remediation automation with artifacts | runs report/fix loop and writes actionable loop evidence |
| `python3 dev/scripts/devctl.py loop-packet --format json` | you want one guarded packet for terminal draft injection from loop/triage evidence | builds a risk-scored packet with draft text and auto-send eligibility metadata |
| `python3 dev/scripts/devctl.py autonomy-loop --plan-id <id> --branch-base develop --mode report-only --max-rounds 6 --max-hours 4 --max-tasks 24 --format json` | you want a bounded autonomy-controller run with checkpoint packets and queue artifacts | orchestrates triage-loop/loop-packet rounds with policy-gated stop reasons, run-scoped outputs, and phone-ready `latest.json`/`latest.md` status snapshots |
| `python3 dev/scripts/devctl.py phone-status --view compact --format md` | you want one fast iPhone/SSH-safe controller snapshot from loop artifacts | loads `queue/phone/latest.json`, renders a compact/trace/actions/full view, and can emit controller-state projection files for downstream clients |
| `python3 dev/scripts/devctl.py controller-action --action dispatch-report-only --repo <owner/repo> --branch develop --dry-run --format md` | you want one guarded remote-control action surface without ad-hoc shell steps | validates policy allowlists/mode gates, then executes or previews bounded dispatch/pause/resume/status actions with auditable output |
| `python3 dev/scripts/devctl.py autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --swarm-counts 10,15,20,30,40 --tactics uniform,specialized,research-first,test-first --dry-run --format md` | you want measurable swarm tradeoff data before scaling live worker runs | validates active-plan scope, runs tactic/swarm-size matrix batches, and emits one benchmark report with per-scenario productivity metrics/charts |
| `python3 dev/scripts/devctl.py autonomy-run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --mode report-only --run-label <label> --format md` | you want one fully-guarded plan-scoped swarm run without manual glue steps | loads active-plan scope, executes swarm with reviewer+post-audit defaults, runs governance checks, and appends progress/audit evidence to the plan doc |
| `python3 dev/scripts/devctl.py autonomy-report --source-root dev/reports/autonomy --library-root dev/reports/autonomy/library --run-label <label> --format md` | you want one operator-readable autonomy digest | assembles latest loop/watch artifacts into a dated bundle with markdown/json summary and chart outputs |
| `python3 dev/scripts/devctl.py autonomy-swarm --question-file <plan.md> --adaptive --min-agents 4 --max-agents 20 --plan-only --format md` | you want one governed worker-allocation decision before launching Claude/Codex lanes | computes metadata-driven agent sizing with rationale and emits a deterministic swarm plan artifact |
| `python3 dev/scripts/devctl.py autonomy-swarm --agents 10 --question-file <plan.md> --mode report-only --run-label <label> --format md` | you want one-command live swarm execution with built-in review lane and digest | runs bounded worker fanout, reserves default `AGENT-REVIEW` when possible, and auto-runs post-audit digest artifacts |
| `python3 dev/scripts/devctl.py mutation-loop --branch develop --mode report-only --threshold 0.80 --max-attempts 3 --format md` | you want bounded mutation remediation automation with hotspot evidence | runs report/fix loop and writes actionable mutation artifacts |
| `python3 dev/scripts/devctl.py security` | deps or security-sensitive code changed | catches policy/advisory issues |
| `python3 dev/scripts/devctl.py audit-scaffold --force --yes --format md` | guard failures need a fix plan | creates one shared remediation file |

Implementation note for maintainers:

- Shared internals in `devctl` are intentional and should stay centralized:
  `dev/scripts/devctl/process_sweep.py` (process parsing/cleanup),
  `dev/scripts/devctl/security_parser.py` (security CLI parser wiring),
  `dev/scripts/devctl/security_codeql.py` (CodeQL alert-fetch wiring for security gate),
  `dev/scripts/devctl/security_python_scope.py` (Python changed/all scope resolution + core scanner targets),
  `dev/scripts/devctl/audit_events.py` (auto-emitted per-command audit-metrics event logging),
  `dev/scripts/devctl/autonomy_report_helpers.py` (autonomy-report source discovery + summarization helpers),
  `dev/scripts/devctl/autonomy_report_render.py` (autonomy-report markdown/chart renderer helpers),
  `dev/scripts/devctl/autonomy_swarm_helpers.py` (adaptive swarm metadata scoring + sizing + report renderer helpers),
  `dev/scripts/devctl/autonomy_swarm_post_audit.py` (shared autonomy-swarm post-audit payload + digest helpers),
  `dev/scripts/devctl/autonomy_loop_helpers.py` (shared autonomy-loop packet/policy/render helper logic),
  `dev/scripts/devctl/autonomy_phone_status.py` (phone-ready autonomy status payload/render helpers),
  `dev/scripts/devctl/phone_status_views.py` (phone-status projection/render helpers and projection-bundle writer),
  `dev/scripts/devctl/autonomy_status_parsers.py` (shared parser wiring for autonomy-report + phone-status),
  `dev/scripts/devctl/controller_action_parser.py` (`controller-action` parser wiring),
  `dev/scripts/devctl/controller_action_support.py` (`controller-action` policy/mode/dispatch helper logic),
  `dev/scripts/devctl/sync_parser.py` (sync CLI parser wiring),
  `dev/scripts/devctl/integrations_sync_parser.py` (`integrations-sync` parser wiring),
  `dev/scripts/devctl/integrations_import_parser.py` (`integrations-import` parser wiring),
  `dev/scripts/devctl/cihub_setup_parser.py` (`cihub-setup` parser wiring),
  `dev/scripts/devctl/integration_federation_policy.py` (external federation policy + allowlist helpers),
  `dev/scripts/devctl/orchestrate_parser.py` (orchestrator CLI parser wiring),
  `dev/scripts/devctl/script_catalog.py` (canonical check-script path registry),
  `dev/scripts/devctl/path_audit_parser.py` (path-audit/path-rewrite parser wiring),
  `dev/scripts/devctl/path_audit.py` (shared stale-path scanner + rewrite engine),
  `dev/scripts/devctl/triage_parser.py` (triage parser wiring),
  `dev/scripts/devctl/triage_loop_parser.py` (triage-loop parser wiring),
  `dev/scripts/devctl/triage_loop_support.py` (triage-loop connectivity/comment/bundle helper logic),
  `dev/scripts/devctl/loop_packet_parser.py` (loop-packet parser wiring),
  `dev/scripts/devctl/autonomy_loop_parser.py` (autonomy-loop parser wiring),
  `dev/scripts/devctl/autonomy_benchmark_parser.py` (autonomy-benchmark parser wiring),
  `dev/scripts/devctl/autonomy_run_parser.py` (autonomy-run parser wiring),
  `dev/scripts/devctl/autonomy_benchmark_helpers.py` (autonomy-benchmark scenario orchestration + metrics helpers),
  `dev/scripts/devctl/autonomy_benchmark_matrix.py` (autonomy-benchmark matrix planner/execution helpers),
  `dev/scripts/devctl/autonomy_benchmark_runner.py` (autonomy-benchmark scenario runner + per-scenario bundle helpers),
  `dev/scripts/devctl/autonomy_benchmark_render.py` (autonomy-benchmark markdown/chart renderer),
  `dev/scripts/devctl/autonomy_run_helpers.py` (autonomy-run shared scope/prompt/governance/plan-update helpers),
  `dev/scripts/devctl/autonomy_run_render.py` (autonomy-run markdown renderer),
  `dev/scripts/devctl/failure_cleanup_parser.py` (failure-cleanup parser wiring),
  `dev/scripts/devctl/commands/audit_scaffold.py` (guard-to-remediation scaffold generation),
  `dev/scripts/devctl/triage_support.py` (triage rendering + bundle helpers),
  `dev/scripts/devctl/triage_enrich.py` (triage owner/category/severity enrichment),
  `dev/scripts/devctl/commands/triage_loop.py` (bounded CodeRabbit loop command),
  `dev/scripts/devctl/commands/controller_action.py` (policy-gated controller action command),
  `dev/scripts/devctl/commands/loop_packet.py` (guarded loop-to-terminal packet builder),
  `dev/scripts/devctl/commands/autonomy_loop.py` (bounded autonomy controller loop command + checkpoint queue artifacts),
  `dev/scripts/devctl/commands/autonomy_benchmark.py` (active-plan-scoped swarm matrix benchmark command),
  `dev/scripts/devctl/commands/autonomy_run.py` (guarded plan-scoped autonomy swarm pipeline command),
  `dev/scripts/devctl/commands/autonomy_report.py` (human-readable autonomy digest command),
  `dev/scripts/devctl/commands/autonomy_swarm.py` (adaptive swarm planner/executor with per-agent autonomy-loop fanout),
  `dev/scripts/devctl/commands/autonomy_loop_support.py` (autonomy-loop validation + policy-deny report helpers),
  `dev/scripts/devctl/commands/autonomy_loop_rounds.py` (autonomy-loop round executor helper),
  `dev/scripts/devctl/commands/docs_check_support.py` (docs-check policy + failure-action helper builders),
  `dev/scripts/devctl/commands/docs_check_render.py` (docs-check markdown renderer helpers),
  `dev/scripts/devctl/commands/check_profile.py` (check profile normalization),
  `dev/scripts/devctl/policy_gate.py` (shared JSON policy gate runner),
  `dev/scripts/devctl/status_report.py` (status/report payload + markdown
  rendering), `dev/scripts/devctl/commands/security.py` (local security gate
  orchestration + optional scanner policy),
  `dev/scripts/devctl/commands/integrations_sync.py` (policy-guarded external-source sync/status command),
  `dev/scripts/devctl/commands/integrations_import.py` (allowlisted selective external-source importer + audit log),
  `dev/scripts/devctl/commands/cihub_setup.py` (allowlisted CIHub setup command implementation),
  `dev/scripts/devctl/commands/failure_cleanup.py` (guarded failure-artifact cleanup), and `dev/scripts/devctl/commands/ship_common.py` /
  `dev/scripts/devctl/commands/ship_steps.py` (release-step helpers), plus
  `dev/scripts/devctl/common.py` for shared command-execution failure handling.
  Keep new logic in these helpers to avoid command drift.

Supporting scripts:

- `dev/scripts/checks/check_agents_contract.py`
- `dev/scripts/checks/check_active_plan_sync.py`
- `dev/scripts/checks/check_multi_agent_sync.py`
- `dev/scripts/checks/check_cli_flags_parity.py`
- `dev/scripts/checks/check_release_version_parity.py`
- `dev/scripts/checks/check_coderabbit_gate.py`
- `dev/scripts/checks/check_coderabbit_ralph_gate.py`
- `dev/scripts/checks/check_screenshot_integrity.py`
- `dev/scripts/checks/check_code_shape.py`
- `dev/scripts/checks/check_rust_lint_debt.py`
- `dev/scripts/checks/check_rust_best_practices.py`
- `dev/scripts/checks/check_rust_security_footguns.py`
- `dev/scripts/checks/check_mutation_score.py`
- `dev/scripts/checks/check_rustsec_policy.py`
- `dev/scripts/checks/run_coderabbit_ralph_loop.py`
- `dev/scripts/checks/mutation_ralph_loop_core.py`
- `dev/scripts/audits/audit_metrics.py`
- `dev/scripts/tests/measure_latency.sh`
- `dev/scripts/tests/wake_word_guard.sh`
- `scripts/macros.sh`

`check_code_shape.py` enforces both language-level limits and path-level
hotspot budgets for Phase 3C decomposition targets.
`check_active_plan_sync.py` enforces active-doc index/spec parity, mirrored-spec
phase heading and `MASTER_PLAN` link contracts, and `MASTER_PLAN` Status
Snapshot release freshness (branch policy + release-tag consistency).
`check_multi_agent_sync.py` enforces dynamic multi-agent coordination parity
between the `MASTER_PLAN` board and the runbook (lane/MP/worktree/branch alignment,
instruction/ack protocol validation, lane-lock + MP-collision handoff checks,
status/date format checks, ledger traceability, and end-of-cycle signoff when
all agent lanes are marked merged).
`check_rust_lint_debt.py` enforces non-regressive growth for `#[allow(...)]`
and non-test `unwrap/expect` call-sites in changed Rust files.
`check_rust_best_practices.py` blocks non-regressive growth of reason-less
`#[allow(...)]`, undocumented `unsafe { ... }` blocks, public `unsafe fn`
surfaces without `# Safety` docs, and `std::mem::forget`/`mem::forget` usage
in changed Rust files.

## CI workflows (reference)

- `rust_ci.yml`
- `voice_mode_guard.yml`
- `wake_word_guard.yml`
- `perf_smoke.yml`
- `latency_guard.yml`
- `memory_guard.yml`
- `mutation-testing.yml`
- `security_guard.yml`
- `dependency_review.yml`
- `workflow_lint.yml`
- `coderabbit_triage.yml`
- `scorecard.yml`
- `parser_fuzz_guard.yml`
- `coverage.yml`
- `docs_lint.yml`
- `lint_hardening.yml`
- `coderabbit_ralph_loop.yml`
- `autonomy_controller.yml`
- `autonomy_run.yml`
- `release_preflight.yml`
- `release_attestation.yml`
- `tooling_control_plane.yml`
- `orchestrator_watchdog.yml`
- `failure_triage.yml`
- `publish_pypi.yml`
- `publish_homebrew.yml`
- `publish_release_binaries.yml`

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
- CI runtime hardening: workflows define explicit `timeout-minutes` budgets for long-running/security-sensitive jobs

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
- [ ] Repeat-to-automate outcomes captured (new automation or debt-register entry).
- [ ] Follow-up work captured as MP items.
- [ ] Handoff summary captured.
- [ ] Root `--*` artifact check run and clean.
- [ ] Git state is clean or intentionally staged/committed.

## Notes

- `dev/archive/2026-01-29-claudeaudit-completed.md` contains the production readiness checklist.
- Prefer editing existing files over creating new ones.
