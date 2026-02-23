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
# Branch sync guardrail helper (develop/master/current by default)
python3 dev/scripts/devctl.py sync
# Also push local-ahead branches after sync
python3 dev/scripts/devctl.py sync --push
# Security guardrails (RustSec baseline + optional workflow scan)
python3 dev/scripts/devctl.py security
python3 dev/scripts/devctl.py security --with-zizmor --require-optional-tools
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 30 --format md
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_release_version_parity.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
python3 dev/scripts/checks/check_rust_security_footguns.py
rg -n "^\\s*-?\\s*uses:\\s*[^@\\s]+@" .github/workflows/*.yml | rg -v "@[0-9a-fA-F]{40}$"
for f in .github/workflows/*.yml; do rg -q '^permissions:' \"$f\" || echo \"missing permissions: $f\"; rg -q '^concurrency:' \"$f\" || echo \"missing concurrency: $f\"; done
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
# `docs-check --strict-tooling` enforces ENGINEERING_EVOLUTION updates for tooling/process/CI shifts and runs active-plan + multi-agent sync gates plus stale-path audit.
# For UI behavior changes, refresh screenshot coverage in the same pass:
# see dev/DEVELOPMENT.md -> "Screenshot refresh capture matrix".

# Triage output for humans + AI agents (optional CIHub ingestion)
python3 dev/scripts/devctl.py triage --ci --format md --output /tmp/devctl-triage.md
python3 dev/scripts/devctl.py triage --ci --cihub --emit-bundle --bundle-dir .cihub --bundle-prefix triage
# Optional: route categories to team owners via JSON map
python3 dev/scripts/devctl.py triage --ci --cihub --owner-map-file dev/config/triage_owner_map.json --format json
# If your cihub binary doesn't support `triage`, devctl records an infra warning
# and still emits local triage output.

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
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1

# Optional: run release preflight workflow in CI before tagging
gh workflow run release_preflight.yml -f version=X.Y.Z -f verify_docs=true

# Optional: manually trigger Homebrew workflow for an existing tag/version
gh workflow run publish_homebrew.yml -f version=X.Y.Z

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
| `dev/scripts/checks/check_cli_flags_parity.py` | CLI docs/schema parity gate | Compares clap long flags in Rust schema files against `guides/CLI_FLAGS.md`. |
| `dev/scripts/checks/check_screenshot_integrity.py` | Screenshot docs integrity gate | Validates markdown image references and reports stale screenshot age. |
| `dev/scripts/checks/check_code_shape.py` | Source-shape drift guard | Blocks new Rust/Python God-file growth using language-level soft/hard limits plus path-level hotspot budgets for active decomposition targets, and emits audit-first remediation guidance (modularize/consolidate before merge, with Python/Rust best-practice links). |
| `dev/scripts/checks/check_rust_lint_debt.py` | Rust lint-debt non-regression guard | Fails when changed non-test Rust files increase `#[allow(...)]` usage or `unwrap/expect` call-sites. |
| `dev/scripts/checks/check_rust_best_practices.py` | Rust best-practices non-regression guard | Fails when changed non-test Rust files increase reason-less `#[allow(...)]`, undocumented `unsafe { ... }` blocks, or public `unsafe fn` surfaces lacking `# Safety` docs. |
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
- `docs-check`: docs coverage + tooling/deprecated-command policy guard (`--strict-tooling` also runs active-plan sync + multi-agent sync)
- `hygiene`: archive/ADR/scripts governance checks plus orphaned `target/debug/deps/voiceterm-*` test-process detection
- `path-audit`: stale-reference scan for legacy check-script paths (skips `dev/archive/`)
- `sync`: guarded branch-sync workflow (clean-tree preflight, remote/local ref checks, `--ff-only` pull, optional `--push` for ahead branches, and start-branch restore)
- `security`: RustSec policy checks plus optional workflow security scanning (`--with-zizmor`)
- `release`: tag + notes flow (legacy release behavior)
- `release-notes`: git-diff driven markdown notes generation
- `ship`: full release/distribution orchestrator with step toggles and optional metadata prep (`--prepare-release`)
- `homebrew`: Homebrew tap update flow
- `pypi`: PyPI build/check/upload flow
- `orchestrate-status`: one-shot orchestrator accountability view (active-plan sync + multi-agent sync guard status with git context)
- `orchestrate-watch`: SLA watchdog for stale lane updates and overdue instruction ACKs
- `status` and `report`: machine-readable project status outputs (optional guarded Dev Mode session summaries via `--dev-logs`, `--dev-root`, and `--dev-sessions-limit`)
- `triage`: combined human/AI triage output with optional `cihub triage` artifact ingestion and bundle emission (`<prefix>.md`, `<prefix>.ai.json`); extracts priority/triage records into normalized issue routing fields (`category`, `severity`, `owner`), supports optional category-owner overrides via `--owner-map-file`, and emits rollups for severity/category/owner counts
- `list`: command/profile inventory

## Devctl Internals

`devctl` keeps shared behavior in a few helper modules so command output stays
consistent:

- `dev/scripts/devctl/process_sweep.py`: shared process parsing/cleanup logic
  used by both `check` and `hygiene`.
- `dev/scripts/devctl/security_parser.py`: shared CLI parser wiring for the
  `security` command so `cli.py` stays smaller and easier to maintain.
- `dev/scripts/devctl/sync_parser.py`: shared CLI parser wiring for the
  `sync` command so `cli.py` stays within shape budgets.
- `dev/scripts/devctl/orchestrate_parser.py`: shared CLI parser wiring for
  `orchestrate-status` and `orchestrate-watch`.
- `dev/scripts/devctl/script_catalog.py`: canonical check-script path registry
  used by commands to avoid ad-hoc path strings.
- `dev/scripts/devctl/path_audit.py`: shared stale-path scanner used by
  `path-audit` and `docs-check --strict-tooling`.
- `dev/scripts/devctl/triage_parser.py`: shared CLI parser wiring for the
  `triage` command so `cli.py` remains under shape limits.
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
- `dev/scripts/devctl/commands/ship_common.py` and
  `dev/scripts/devctl/commands/ship_steps.py`: shared ship step/runtime helpers
  used by `dev/scripts/devctl/commands/ship.py`.
- `dev/scripts/devctl/commands/security.py`: shared local security gate runner
  (RustSec policy + optional `zizmor` scanner behavior).
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
# Optional: auto-prepare these files in one step
python3 dev/scripts/devctl.py ship --version X.Y.Z --prepare-release

# 2) create tag + notes
python3 dev/scripts/devctl.py release --version X.Y.Z

# 3) publish GitHub release (triggers publish_pypi.yml + publish_homebrew.yml)
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file /tmp/voiceterm-release-vX.Y.Z.md

# 4) monitor publish workflows
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
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
