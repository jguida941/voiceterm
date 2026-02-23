# Developer Scripts

Canonical maintainer control plane:

```bash
python3 dev/scripts/devctl.py ...
```

Use `devctl` first for release, verification, docs-governance, and reporting.
Legacy shell scripts remain as compatibility adapters that route into `devctl`.
For active-doc discovery, use `dev/active/INDEX.md`.
For current execution scope, use `dev/active/MASTER_PLAN.md`.
For consolidated visual planning context (Theme Studio + overlay research +
redesign), use `dev/active/theme_upgrade.md`.
For a quick lifecycle/check/push guide, see `dev/DEVELOPMENT.md` sections
`End-to-end lifecycle flow`, `What checks protect us`, and `When to push where`.

For workflow routing (what to run for a normal push vs tooling/process changes vs tagged release), follow `AGENTS.md` first.
Check scripts now live under `dev/scripts/checks/`, with centralized path
registry wiring in `dev/scripts/devctl/script_catalog.py`.

Engineering quality rule:

- For non-trivial Rust runtime/tooling changes, follow the Rust reference pack
  in `AGENTS.md` and `dev/DEVELOPMENT.md` before coding:
  - `https://doc.rust-lang.org/book/`
  - `https://doc.rust-lang.org/reference/`
  - `https://rust-lang.github.io/api-guidelines/`
  - `https://doc.rust-lang.org/nomicon/`
  - `https://doc.rust-lang.org/std/`
  - `https://rust-lang.github.io/rust-clippy/master/`
- Capture references consulted in handoff notes for non-trivial changes.

Documentation style rule:

- Write docs in plain language first.
- Keep steps short and concrete.
- Prefer "what to run and why" over policy-heavy wording.

## Canonical Commands

```bash
# Core quality checks
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py check --profile maintainer-lint
python3 dev/scripts/devctl.py check --profile ai-guard
python3 dev/scripts/devctl.py check --profile release
# Optional: force sequential check execution (parallel phases are default)
python3 dev/scripts/devctl.py check --profile ci --no-parallel
# Optional: disable automatic orphaned-test cleanup sweep
python3 dev/scripts/devctl.py check --profile ci --no-process-sweep-cleanup

# Docs + governance checks
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/devctl.py path-audit
python3 dev/scripts/devctl.py path-rewrite --dry-run
python3 dev/scripts/devctl.py path-rewrite
# Branch sync guardrail helper (develop/master/current by default)
python3 dev/scripts/devctl.py sync
# Also push local-ahead branches after sync
python3 dev/scripts/devctl.py sync --push
# CIHub setup helper (preview allowlisted steps + capability probe)
python3 dev/scripts/devctl.py cihub-setup --format md
# Strict-capability preview for selected steps
python3 dev/scripts/devctl.py cihub-setup --steps detect validate --strict-capabilities --format json
# Apply mode (use --dry-run first in new environments)
python3 dev/scripts/devctl.py cihub-setup --apply --dry-run --yes --format md
# Security guardrails (RustSec baseline + optional workflow scan)
python3 dev/scripts/devctl.py security
python3 dev/scripts/devctl.py security --scanner-tier core --python-scope all
python3 dev/scripts/devctl.py security --with-zizmor --require-optional-tools
python3 dev/scripts/devctl.py security --with-codeql-alerts --codeql-repo owner/repo --codeql-min-severity high
python3 dev/scripts/devctl.py security --with-zizmor --with-codeql-alerts --codeql-repo owner/repo --require-optional-tools
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 30 --format md
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_release_version_parity.py
python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
python3 dev/scripts/checks/run_coderabbit_ralph_loop.py --repo owner/repo --branch develop --max-attempts 3 --format md
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_audit_patterns.py
python3 dev/scripts/checks/check_rust_security_footguns.py
rg -n "^\\s*-?\\s*uses:\\s*[^@\\s]+@" .github/workflows/*.yml | rg -v "@[0-9a-fA-F]{40}$"
for f in .github/workflows/*.yml; do rg -q '^permissions:' \"$f\" || echo \"missing permissions: $f\"; rg -q '^concurrency:' \"$f\" || echo \"missing concurrency: $f\"; done
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
# `docs-check --strict-tooling` enforces ENGINEERING_EVOLUTION updates for tooling/process/CI shifts and runs active-plan + multi-agent sync gates plus stale-path audit (using `dev/scripts/devctl/script_catalog.py` as canonical check-script path registry). Use `path-rewrite` to auto-fix stale path references.
# For UI behavior changes, refresh screenshot coverage in the same pass:
# see dev/DEVELOPMENT.md -> "Screenshot refresh capture matrix".

# Triage output for humans + AI agents (optional CIHub ingestion)
python3 dev/scripts/devctl.py triage --ci --format md --output /tmp/devctl-triage.md
python3 dev/scripts/devctl.py triage --ci --cihub --emit-bundle --bundle-dir .cihub --bundle-prefix triage
# Optional: route categories to team owners via JSON map
python3 dev/scripts/devctl.py triage --ci --cihub --owner-map-file dev/config/triage_owner_map.json --format json
# Optional: ingest external AI-review findings (CodeRabbit, custom bots, etc.)
python3 dev/scripts/devctl.py triage --no-cihub --external-issues-file .cihub/coderabbit/priority.json --format md --output /tmp/devctl-triage-external.md
# CI note: `.github/workflows/coderabbit_triage.yml` enforces a blocking
# medium/high severity gate for CodeRabbit findings, and `release_preflight.yml`
# verifies that gate passed for the exact release commit. Publish workflows
# (`publish_pypi`, `publish_homebrew`, `release_attestation`) also enforce
# the same gate before distribution/attestation steps run.
# If your cihub binary doesn't support `triage`, devctl records an infra warning
# and still emits local triage output.
# Clean local failure triage bundles only after CI is green
python3 dev/scripts/devctl.py failure-cleanup --require-green-ci --dry-run
python3 dev/scripts/devctl.py failure-cleanup --require-green-ci --yes
# Generate a guard-driven remediation scaffold for Rust modularity/pattern debt
python3 dev/scripts/devctl.py audit-scaffold --force --yes --format md
# Commit-range scoped scaffold generation (useful in CI/PR review lanes)
python3 dev/scripts/devctl.py audit-scaffold --since-ref origin/develop --head-ref HEAD --force --yes --format json
# Optional: gate cleanup against a scoped CI slice
python3 dev/scripts/devctl.py failure-cleanup --require-green-ci --ci-branch develop --ci-event push --ci-workflow "Rust TUI CI" --dry-run
# Optional: override the default cleanup root guard (still restricted to dev/reports/**)
python3 dev/scripts/devctl.py failure-cleanup --directory dev/reports/archive-failures --allow-outside-failure-root --dry-run
# Workflow note: failure-triage branch scope defaults to develop/master and can be overridden
# with GitHub repo variable FAILURE_TRIAGE_BRANCHES (comma-separated branch names, no spaces).

# Release notes from git diff range
python3 dev/scripts/devctl.py release-notes --version X.Y.Z

# Coverage workflow (mirrors .github/workflows/coverage.yml)
cd src && cargo llvm-cov --workspace --all-features --lcov --output-path lcov.info
gh run list --workflow coverage.yml --limit 1

# Tag + notes (legacy release flow)
python3 dev/scripts/devctl.py release --version X.Y.Z
# Optional: auto-prepare release metadata before tag/notes
python3 dev/scripts/devctl.py release --version X.Y.Z --prepare-release

# Workflow-first release path (recommended)
python3 dev/scripts/devctl.py ship --version X.Y.Z --verify --tag --notes --github --yes
# One-command prep + verify + tag + notes + GitHub release
python3 dev/scripts/devctl.py ship --version X.Y.Z --prepare-release --verify --tag --notes --github --yes
# Optional explicit gate check (same check used by ship --verify and release CI)
python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow release_attestation.yml --limit 1

# Optional: run release preflight workflow in CI before tagging
gh workflow run release_preflight.yml -f version=X.Y.Z -f verify_docs=true

# Optional: manually trigger Homebrew workflow for an existing tag/version
gh workflow run publish_homebrew.yml -f version=X.Y.Z -f release_branch=master
# Optional: manually trigger bounded CodeRabbit backlog remediation loop
gh workflow run coderabbit_ralph_loop.yml -f branch=develop -f max_attempts=3
# Optional auto-run config (repo variables):
# RALPH_LOOP_ENABLED=true
# RALPH_LOOP_MAX_ATTEMPTS=3
# RALPH_LOOP_POLL_SECONDS=20
# RALPH_LOOP_TIMEOUT_SECONDS=1800
# RALPH_LOOP_FIX_COMMAND='<your auto-fix command that commits + pushes>'

# Manual fallback (local PyPI/Homebrew publish)
python3 dev/scripts/devctl.py pypi --upload --yes
python3 dev/scripts/devctl.py homebrew --version X.Y.Z
```

## Scripts Inventory

| Script | Role | Notes |
|---|---|---|
| `dev/scripts/devctl.py` | Canonical maintainer CLI | Use this first. |
| `dev/scripts/generate-release-notes.sh` | Release-notes helper | Called by `devctl release-notes`/`devctl ship --notes`. |
| `dev/scripts/release.sh` | Legacy adapter | Routes to `devctl release`. |
| `dev/scripts/publish-pypi.sh` | Legacy adapter | Routes to `devctl pypi`; internal mode used by devctl. |
| `dev/scripts/update-homebrew.sh` | Legacy adapter | Routes to `devctl homebrew`; internal mode used by devctl. |
| `dev/scripts/mutants.py` | Mutation helper | Interactive module/shard helper with `--shard`, `--results-only`, and JSON hotspot output (includes outcomes source age metadata). |
| `dev/scripts/checks/check_mutation_score.py` | Mutation score gate | Used in CI and local validation; prints outcomes source freshness and supports `--max-age-hours` stale-data gating. |
| `dev/scripts/checks/check_agents_contract.py` | AGENTS contract gate | Verifies required AGENTS SOP sections, bundles, and routing rows are present. |
| `dev/scripts/checks/check_active_plan_sync.py` | Active-plan sync gate | Verifies `dev/active/INDEX.md` registry coverage, tracker authority, mirrored-spec phase headings, cross-doc links, `MP-*` scope parity between index/spec docs and `MASTER_PLAN`, and `MASTER_PLAN` Status Snapshot release metadata freshness. |
| `dev/scripts/checks/check_multi_agent_sync.py` | Multi-agent coordination gate | Verifies `MASTER_PLAN` 3-agent board parity with `MULTI_AGENT_WORKTREE_RUNBOOK.md` (lane/MP/worktree/branch alignment, instruction/ack protocol checks, lane-lock + MP-collision handoff checks, status/date formatting, ledger traceability, and required end-of-cycle signoff when all agent lanes are merged). |
| `dev/scripts/checks/check_release_version_parity.py` | Release version parity gate | Ensures Cargo, PyPI, and macOS app plist versions match before tagging/publishing. |
| `dev/scripts/checks/check_coderabbit_gate.py` | CodeRabbit release gate | Verifies the latest `CodeRabbit Triage Bridge` run is successful for a target branch+commit SHA before release/publish steps proceed. |
| `dev/scripts/checks/run_coderabbit_ralph_loop.py` | CodeRabbit remediation loop | Runs a bounded retry loop over CodeRabbit medium/high backlog artifacts and optional auto-fix command hooks. |
| `dev/scripts/checks/check_cli_flags_parity.py` | CLI docs/schema parity gate | Compares clap long flags in Rust schema files against `guides/CLI_FLAGS.md`. |
| `dev/scripts/checks/check_screenshot_integrity.py` | Screenshot docs integrity gate | Validates markdown image references and reports stale screenshot age. |
| `dev/scripts/checks/check_code_shape.py` | Source-shape drift guard | Blocks new Rust/Python God-file growth using language-level soft/hard limits plus path-level hotspot budgets for active decomposition targets, and emits audit-first remediation guidance (modularize/consolidate before merge, with Python/Rust best-practice links). |
| `dev/scripts/checks/check_rust_lint_debt.py` | Rust lint-debt non-regression guard | Fails when changed non-test Rust files increase `#[allow(...)]` usage or `unwrap/expect` call-sites. |
| `dev/scripts/checks/check_rust_best_practices.py` | Rust best-practices non-regression guard | Fails when changed non-test Rust files increase reason-less `#[allow(...)]`, undocumented `unsafe { ... }` blocks, or public `unsafe fn` surfaces lacking `# Safety` docs. |
| `dev/scripts/checks/check_rust_audit_patterns.py` | Rust audit regression guard | Fails when known critical audit anti-patterns reappear (UTF-8-unsafe prefix slicing, byte-limit truncation via `INPUT_MAX_CHARS`, single-pass `redacted.find(...)` secret redaction, deterministic timestamp-hash ID suffixes, and lossy `clamped * 32_768.0 as i16` VAD casts). |
| `dev/scripts/checks/check_rust_security_footguns.py` | Rust security-footguns non-regression guard | Fails when changed non-test Rust files add risky AI-prone patterns (`todo!/unimplemented!/dbg!`, shell-style process spawns, permissive `0o777/0o666` modes, weak-crypto references like MD5/SHA1). |
| `dev/scripts/render_ci_badge.py` | CI badge endpoint JSON renderer | Updates `.github/badges/ci-status.json` with pass/fail color state. |
| `dev/scripts/render_mutation_badge.py` | Mutation badge endpoint JSON renderer | Updates `.github/badges/mutation-score.json`. |
| `dev/scripts/checks/check_rustsec_policy.py` | RustSec policy gate | Enforces advisory thresholds. |

## Devctl Command Set

- `check`: fmt/clippy/tests/build profiles (`ci`, `prepush`, `release`, `maintainer-lint`, `quick`, `ai-guard`)
  - Runs setup gates (`fmt`, `clippy`, AI guard scripts) and test/build phases in parallel batches by default.
  - Tune parallelism with `--parallel-workers <n>` or force sequential execution with `--no-parallel`.
  - Runs an automatic orphaned-test sweep before/after checks (`target/*/deps/voiceterm-*`, detached `PPID=1`).
  - Disable only when needed with `--no-process-sweep-cleanup`.
  - `release` profile includes wake-word regression/soak guardrails and mutation-score gating.
- `mutants`: mutation test helper wrapper
- `mutation-score`: threshold gate for outcomes with freshness reporting and optional stale-data fail gate (`--max-age-hours`)
- `docs-check`: docs coverage + tooling/deprecated-command policy guard (`--strict-tooling` also runs active-plan sync + multi-agent sync + stale-path audit)
- `hygiene`: archive/ADR/scripts governance checks plus orphaned `target/debug/deps/voiceterm-*` test-process detection
- `path-audit`: stale-reference scan for legacy check-script paths (skips `dev/archive/`)
- `path-rewrite`: auto-rewrite legacy check-script paths to canonical registry targets (use `--dry-run` first)
- `sync`: guarded branch-sync workflow (clean-tree preflight, remote/local ref checks, `--ff-only` pull, optional `--push` for ahead branches, and start-branch restore)
- `cihub-setup`: allowlisted CIHub repo-setup helper (`detect/init/update/validate`) with capability probing, preview/apply modes, and strict unsupported-step gating
- `security`: RustSec policy checks plus optional workflow/code-scanning security scans (`--with-zizmor`, `--with-codeql-alerts`) and Python-scope selection (`--python-scope auto|changed|all`)
- `release`: tag + notes flow (legacy release behavior)
- `release-notes`: git-diff driven markdown notes generation
- `ship`: full release/distribution orchestrator with step toggles and optional metadata prep (`--prepare-release`); `--verify` now includes the CodeRabbit release gate check
- `homebrew`: Homebrew tap update flow
- `pypi`: PyPI build/check/upload flow
- `orchestrate-status`: one-shot orchestrator accountability view (active-plan sync + multi-agent sync guard status with git context)
- `orchestrate-watch`: SLA watchdog for stale lane updates and overdue instruction ACKs
- `status` and `report`: machine-readable project status outputs (optional guarded Dev Mode session summaries via `--dev-logs`, `--dev-root`, and `--dev-sessions-limit`)
- `triage`: combined human/AI triage output with optional `cihub triage` artifact ingestion, optional external issue-file ingestion (`--external-issues-file` for CodeRabbit/custom bot payloads), and bundle emission (`<prefix>.md`, `<prefix>.ai.json`); extracts priority/triage records into normalized issue routing fields (`category`, `severity`, `owner`), supports optional category-owner overrides via `--owner-map-file`, and emits rollups for severity/category/owner counts
- `failure-cleanup`: guarded cleanup for local failure triage bundles (`dev/reports/failures`) with default path-root enforcement, optional override constrained to `dev/reports/**` (`--allow-outside-failure-root`), optional scoped CI gate filters (`--ci-branch`, `--ci-workflow`, `--ci-event`, `--ci-sha`), plus dry-run/confirmation controls
- `audit-scaffold`: build/update `dev/active/RUST_AUDIT_FINDINGS.md` from guard findings (with safe output path and overwrite guards)
- `list`: command/profile inventory

## Quick command guide (plain language)

| Command | Run it when | Why |
|---|---|---|
| `check --profile ci` | before a normal push | catches build/test/lint issues early |
| `check --profile ai-guard` | after touching larger Rust/Python files | catches shape/lint-debt/best-practice drift |
| `docs-check --user-facing` | you changed user docs or user behavior | keeps docs and behavior aligned |
| `docs-check --strict-tooling` | you changed tooling, workflows, or process docs | enforces governance and active-plan sync |
| `hygiene` | before merge on tooling/process work | catches doc/process drift |
| `security` | you changed dependencies or security-sensitive code | catches advisory/policy issues |
| `triage --ci` | CI failed and you need an actionable summary | creates a clean failure summary for humans/AI |
| `audit-scaffold` | AI-guard/tooling guards failed | creates one shared fix list file |
| `failure-cleanup --dry-run` | CI is green and you want to clean old failure artifacts | safely previews/removes stale failure bundles |

## `audit-scaffold` in plain language

What it does:

- Creates one fix list at `dev/active/RUST_AUDIT_FINDINGS.md`.
- Pulls findings from the guard scripts so you do not have to read many logs.

When it runs automatically:

- After `devctl check --profile ai-guard` fails.
- On tooling-control-plane CI failure paths that generate remediation artifacts.

When to run it yourself:

- You fixed part of the issues and want a fresh fix list.
- You want findings for only one commit range (`--since-ref` and `--head-ref`).
- You are about to split remediation work across multiple agents.

When to skip it:

- Guard checks are already green.
- The change is docs-only and does not touch source-quality guards.

What you should expect:

- A single markdown file with:
  - which guards failed,
  - which files are affected,
  - what to fix next,
  - what to re-run to confirm green.

## Devctl Internals

`devctl` keeps shared behavior in a few helper modules so command output stays
consistent:

- `dev/scripts/devctl/process_sweep.py`: shared process parsing/cleanup logic
  used by both `check` and `hygiene`.
- `dev/scripts/devctl/security_parser.py`: shared CLI parser wiring for the
  `security` command so `cli.py` stays smaller and easier to maintain.
- `dev/scripts/devctl/security_python_scope.py`: shared Python changed/all
  scope resolution and target derivation for core security scanners.
- `dev/scripts/devctl/sync_parser.py`: shared CLI parser wiring for the
  `sync` command so `cli.py` stays within shape budgets.
- `dev/scripts/devctl/cihub_setup_parser.py`: shared CLI parser wiring for the
  `cihub-setup` command.
- `dev/scripts/devctl/orchestrate_parser.py`: shared CLI parser wiring for
  `orchestrate-status` and `orchestrate-watch`.
- `dev/scripts/devctl/script_catalog.py`: canonical check-script path registry
  used by commands to avoid ad-hoc path strings.
- `dev/scripts/devctl/path_audit.py`: shared stale-path scanner and rewrite
  engine used by `path-audit`, `path-rewrite`, and `docs-check --strict-tooling`.
- `dev/scripts/devctl/triage_parser.py`: shared CLI parser wiring for the
  `triage` command so `cli.py` remains under shape limits.
- `dev/scripts/devctl/failure_cleanup_parser.py`: shared CLI parser wiring for
  the `failure-cleanup` command.
- `dev/scripts/devctl/commands/check_profile.py`: shared `check` profile
  toggles/normalization.
- `dev/scripts/devctl/commands/check_steps.py`: shared `check` step-spec
  builder plus serial/parallel execution helpers with stable result ordering.
- `dev/scripts/devctl/status_report.py`: shared payload collection and markdown
  rendering used by both `status` and `report`.
- `dev/scripts/devctl/triage_support.py`: shared triage classification,
  artifact-ingestion, markdown rendering, and bundle writers used by
  `dev/scripts/devctl/commands/triage.py`.
- `dev/scripts/devctl/triage_enrich.py`: normalization/routing helpers used to
  map triage issues and `cihub` artifact records into consistent severity +
  owner labels, including optional owner-map file overrides.
- `dev/scripts/devctl/policy_gate.py`: shared JSON policy-script runner used by
  `docs-check` strict-tooling plus orchestrator accountability summaries
  (active-plan + multi-agent sync checks).
- `dev/scripts/devctl/commands/docs_check_support.py`: shared docs-check policy
  helpers (path classification, deprecated-reference scan, failure-reason and
  next-action builders).
- `dev/scripts/devctl/commands/docs_check_render.py`: shared docs-check
  markdown renderer used by `dev/scripts/devctl/commands/docs_check.py`.
- `dev/scripts/devctl/commands/ship_common.py` and
  `dev/scripts/devctl/commands/ship_steps.py`: shared ship step/runtime helpers
  used by `dev/scripts/devctl/commands/ship.py`.
- `dev/scripts/devctl/commands/security.py`: shared local security gate runner
  (RustSec policy + optional `zizmor` scanner behavior).
- `dev/scripts/devctl/commands/cihub_setup.py`: allowlisted CIHub setup command
  implementation (preview/apply flow with capability probing + strict mode).
- `dev/scripts/devctl/commands/failure_cleanup.py`: guarded cleanup command for
  local failure triage artifact directories with default root guard, optional
  scoped CI-green filters, and explicit override mode for non-default cleanup
  roots under `dev/reports/**`.
- `dev/scripts/devctl/commands/audit_scaffold.py`: guard-driven remediation
  scaffold generator for Rust modularity/pattern drift; aggregates JSON outputs
  from `check_code_shape.py`, `check_rust_lint_debt.py`,
  `check_rust_best_practices.py`, `check_rust_audit_patterns.py`, and
  `check_rust_security_footguns.py` into one active markdown execution surface.
- `dev/scripts/devctl/collect.py`: shared git/CI collection helpers with
  compatibility fallback for older `gh run list --json` field support.
- `dev/scripts/devctl/commands/release_prep.py`: shared release metadata
  preparation helpers used by `ship/release --prepare-release` (Cargo/PyPI/app
  version fields, changelog heading rollover, and `MASTER_PLAN` Status
  Snapshot refresh).
- `dev/scripts/devctl/common.py`: shared command runner returns structured
  non-zero results (including missing-binary failures) instead of uncaught
  exceptions, streams live subprocess output, and keeps bounded failure-output
  excerpts for markdown/json report diagnostics.

Historical shard artifacts from previous CI runs are useful for hotspot triage,
but release gating should always use a full aggregated score generated from the
current commit's shard outcomes. Use `--max-age-hours` in local gates when you
need freshness enforcement instead of historical trend visibility.

## Markdown Lint Config

Markdown lint policy files live under `dev/config/`:

- `dev/config/markdownlint.yaml`
- `dev/config/markdownlint.ignore`

## Release Workflow (Recommended)

```bash
# 1) align release versions across Cargo/PyPI/macOS app plist + changelog
python3 dev/scripts/checks/check_release_version_parity.py
python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
# Optional: auto-prepare these files in one step
python3 dev/scripts/devctl.py ship --version X.Y.Z --prepare-release

# 2) create tag + notes
python3 dev/scripts/devctl.py release --version X.Y.Z

# 3) publish GitHub release (triggers publish_pypi.yml + publish_homebrew.yml + release_attestation.yml)
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file /tmp/voiceterm-release-vX.Y.Z.md

# 4) monitor publish workflows
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow release_attestation.yml --limit 1
# gh run watch <run-id>

# 5) verify published package
curl -fsSL https://pypi.org/pypi/voiceterm/X.Y.Z/json | rg '"version"'

# 6) fallback Homebrew update (if workflow path is unavailable)
python3 dev/scripts/devctl.py homebrew --version X.Y.Z
```

Manual fallback (if GitHub Actions publish lanes are unavailable):

```bash
python3 dev/scripts/devctl.py pypi --upload --yes
python3 dev/scripts/devctl.py homebrew --version X.Y.Z
```

Or run unified control-plane commands directly:

```bash
# Workflow-first release path
python3 dev/scripts/devctl.py ship --version X.Y.Z --verify --tag --notes --github --yes
# Workflow-first with auto metadata prep
python3 dev/scripts/devctl.py ship --version X.Y.Z --prepare-release --verify --tag --notes --github --yes
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow release_attestation.yml --limit 1

# Manual fallback (local PyPI/Homebrew publish)
python3 dev/scripts/devctl.py ship --version X.Y.Z --pypi --verify-pypi --homebrew --yes
```

## Test Scripts

| Script | Purpose |
|---|---|
| `dev/scripts/tests/benchmark_voice.sh` | Voice pipeline benchmarking |
| `dev/scripts/tests/measure_latency.sh` | Latency profiling + CI guardrails |
| `dev/scripts/tests/integration_test.sh` | IPC integration testing |
| `dev/scripts/tests/wake_word_guard.sh` | Wake-word regression + soak guardrails |

Example latency guard command:

```bash
dev/scripts/tests/measure_latency.sh --ci-guard --count 3
```
