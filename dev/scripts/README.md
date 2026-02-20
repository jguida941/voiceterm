# Developer Scripts

Canonical maintainer control plane:

```bash
python3 dev/scripts/devctl.py ...
```

Use `devctl` first for release, verification, docs-governance, and reporting.
Legacy shell scripts remain as compatibility adapters that route into `devctl`.
For active-doc discovery, use `dev/active/INDEX.md`.
For current execution scope, use `dev/active/MASTER_PLAN.md`.
For a quick lifecycle/check/push guide, see `dev/DEVELOPMENT.md` sections
`End-to-end lifecycle flow`, `What checks protect us`, and `When to push where`.

For workflow routing (what to run for a normal push vs tooling/process changes vs tagged release), follow `AGENTS.md` first.

Documentation style rule:

- Write docs in plain language first.
- Keep steps short and concrete.
- Prefer "what to run and why" over policy-heavy wording.

## Canonical Commands

```bash
# Core quality checks
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py check --profile maintainer-lint
python3 dev/scripts/devctl.py check --profile release

# Docs + governance checks
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/check_agents_contract.py
python3 dev/scripts/check_active_plan_sync.py
python3 dev/scripts/check_release_version_parity.py
python3 dev/scripts/check_cli_flags_parity.py
python3 dev/scripts/check_screenshot_integrity.py --stale-days 120
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
# `docs-check --strict-tooling` enforces ENGINEERING_EVOLUTION updates for tooling/process/CI shifts.
# For UI behavior changes, refresh screenshot coverage in the same pass:
# see dev/DEVELOPMENT.md -> "Screenshot refresh capture matrix".

# Release notes from git diff range
python3 dev/scripts/devctl.py release-notes --version X.Y.Z

# Coverage workflow (mirrors .github/workflows/coverage.yml)
cd src && cargo llvm-cov --workspace --all-features --lcov --output-path lcov.info
gh run list --workflow coverage.yml --limit 1

# Tag + notes (legacy release flow)
python3 dev/scripts/devctl.py release --version X.Y.Z

# Workflow-first release path (recommended)
python3 dev/scripts/devctl.py ship --version X.Y.Z --verify --tag --notes --github --yes
gh run list --workflow publish_pypi.yml --limit 1

# Distribution steps
python3 dev/scripts/devctl.py homebrew --version X.Y.Z

# Manual fallback (local PyPI publish)
python3 dev/scripts/devctl.py pypi --upload --yes
```

## Scripts Inventory

| Script | Role | Notes |
|---|---|---|
| `dev/scripts/devctl.py` | Canonical maintainer CLI | Use this first. |
| `dev/scripts/generate-release-notes.sh` | Release-notes helper | Called by `devctl release-notes`/`devctl ship --notes`. |
| `dev/scripts/release.sh` | Legacy adapter | Routes to `devctl release`. |
| `dev/scripts/publish-pypi.sh` | Legacy adapter | Routes to `devctl pypi`; internal mode used by devctl. |
| `dev/scripts/update-homebrew.sh` | Legacy adapter | Routes to `devctl homebrew`; internal mode used by devctl. |
| `dev/scripts/mutants.py` | Mutation helper | Interactive module/shard helper with `--shard`, `--results-only`, and JSON hotspot output. |
| `dev/scripts/check_mutation_score.py` | Mutation score gate | Used in CI and local validation. |
| `dev/scripts/check_agents_contract.py` | AGENTS contract gate | Verifies required AGENTS SOP sections, bundles, and routing rows are present. |
| `dev/scripts/check_active_plan_sync.py` | Active-plan sync gate | Verifies `dev/active/INDEX.md` registry coverage, tracker authority, cross-doc links, and `MP-*` scope parity between index/spec docs and `MASTER_PLAN`. |
| `dev/scripts/check_release_version_parity.py` | Release version parity gate | Ensures Cargo, PyPI, and macOS app plist versions match before tagging/publishing. |
| `dev/scripts/check_cli_flags_parity.py` | CLI docs/schema parity gate | Compares clap long flags in Rust schema files against `guides/CLI_FLAGS.md`. |
| `dev/scripts/check_screenshot_integrity.py` | Screenshot docs integrity gate | Validates markdown image references and reports stale screenshot age. |
| `dev/scripts/render_ci_badge.py` | CI badge endpoint JSON renderer | Updates `.github/badges/ci-status.json` with pass/fail color state. |
| `dev/scripts/render_mutation_badge.py` | Mutation badge endpoint JSON renderer | Updates `.github/badges/mutation-score.json`. |
| `dev/scripts/check_rustsec_policy.py` | RustSec policy gate | Enforces advisory thresholds. |

## Devctl Command Set

- `check`: fmt/clippy/tests/build profiles (`ci`, `prepush`, `release`, `maintainer-lint`, `quick`)
  - `release` profile includes wake-word regression/soak guardrails and mutation-score gating.
- `mutants`: mutation test helper wrapper
- `mutation-score`: threshold gate for outcomes
- `docs-check`: docs coverage + tooling/deprecated-command policy guard
- `hygiene`: archive/ADR/scripts governance checks plus orphaned `target/debug/deps/voiceterm-*` test-process detection
- `release`: tag + notes flow (legacy release behavior)
- `release-notes`: git-diff driven markdown notes generation
- `ship`: full release/distribution orchestrator with step toggles
- `homebrew`: Homebrew tap update flow
- `pypi`: PyPI build/check/upload flow
- `status` and `report`: machine-readable project status outputs
- `list`: command/profile inventory

Historical shard artifacts from previous CI runs are useful for hotspot triage,
but release gating should always use a full aggregated score generated from the
current commit's shard outcomes.

## Markdown Lint Config

Markdown lint policy files live under `dev/config/`:

- `dev/config/markdownlint.yaml`
- `dev/config/markdownlint.ignore`

## Release Workflow (Recommended)

```bash
# 1) align release versions across Cargo/PyPI/macOS app plist + changelog
python3 dev/scripts/check_release_version_parity.py

# 2) create tag + notes
python3 dev/scripts/devctl.py release --version X.Y.Z

# 3) publish GitHub release (triggers publish_pypi.yml)
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file /tmp/voiceterm-release-vX.Y.Z.md

# 4) monitor the PyPI publish workflow
gh run list --workflow publish_pypi.yml --limit 1
# gh run watch <run-id>

# 5) verify published package
curl -fsSL https://pypi.org/pypi/voiceterm/X.Y.Z/json | rg '"version"'

# 6) update Homebrew tap
python3 dev/scripts/devctl.py homebrew --version X.Y.Z
```

Manual fallback (if GitHub Actions publish lane is unavailable):

```bash
python3 dev/scripts/devctl.py pypi --upload --yes
```

Or run unified control-plane commands directly:

```bash
# Workflow-first release path
python3 dev/scripts/devctl.py ship --version X.Y.Z --verify --tag --notes --github --yes
python3 dev/scripts/devctl.py ship --version X.Y.Z --homebrew --yes

# Manual fallback (local PyPI publish)
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
