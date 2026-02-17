# Developer Scripts

Canonical maintainer control plane:

```bash
python3 dev/scripts/devctl.py ...
```

Use `devctl` first for release, verification, docs-governance, and reporting.
Legacy shell scripts remain as compatibility adapters that route into `devctl`.
For current execution scope, use `dev/active/MASTER_PLAN.md` and
`dev/active/CODE_QUALITY_EXECUTION_PLAN.md`.

## Canonical Commands

```bash
# Core quality checks
python3 dev/scripts/devctl.py check --profile ci

# Docs + governance checks
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md

# Release notes from git diff range
python3 dev/scripts/devctl.py release-notes --version X.Y.Z

# Tag + notes (legacy release flow)
python3 dev/scripts/devctl.py release --version X.Y.Z

# Full release pipeline (single command)
python3 dev/scripts/devctl.py ship --version X.Y.Z --verify --tag --notes --github --pypi --homebrew --verify-pypi

# Distribution steps
python3 dev/scripts/devctl.py pypi --upload
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
| `dev/scripts/mutants.py` | Mutation helper | Interactive module/shard helper. |
| `dev/scripts/check_mutation_score.py` | Mutation score gate | Used in CI and local validation. |
| `dev/scripts/render_mutation_badge.py` | Mutation badge endpoint JSON renderer | Updates `.github/badges/mutation-score.json`. |
| `dev/scripts/check_rustsec_policy.py` | RustSec policy gate | Enforces advisory thresholds. |

## Devctl Command Set

- `check`: fmt/clippy/tests/build profiles (`ci`, `prepush`, `release`, `quick`)
- `mutants`: mutation test helper wrapper
- `mutation-score`: threshold gate for outcomes
- `docs-check`: docs coverage + tooling/deprecated-command policy guard
- `hygiene`: archive/ADR/scripts governance checks
- `release`: tag + notes flow (legacy release behavior)
- `release-notes`: git-diff driven markdown notes generation
- `ship`: full release/distribution orchestrator with step toggles
- `homebrew`: Homebrew tap update flow
- `pypi`: PyPI build/check/upload flow
- `status` and `report`: machine-readable project status outputs
- `list`: command/profile inventory

## Markdown Lint Config

Markdown lint policy files live under `dev/config/`:

- `dev/config/markdownlint.yaml`
- `dev/config/markdownlint.ignore`

## Release Workflow (Recommended)

```bash
# 1) prepare version/changelog and commit
# 2) create tag + notes
python3 dev/scripts/devctl.py release --version X.Y.Z

# 3) publish GitHub release
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file /tmp/voiceterm-release-vX.Y.Z.md

# 4) publish package + update tap
python3 dev/scripts/devctl.py pypi --upload
python3 dev/scripts/devctl.py homebrew --version X.Y.Z

# 5) verify published package
curl -fsSL https://pypi.org/pypi/voiceterm/X.Y.Z/json | rg '"version"'
```

Or run the unified control-plane flow:

```bash
python3 dev/scripts/devctl.py ship --version X.Y.Z --verify --tag --notes --github --pypi --homebrew --verify-pypi
```

## Test Scripts

| Script | Purpose |
|---|---|
| `dev/scripts/tests/benchmark_voice.sh` | Voice pipeline benchmarking |
| `dev/scripts/tests/measure_latency.sh` | Latency profiling + CI guardrails |
| `dev/scripts/tests/integration_test.sh` | IPC integration testing |

Example latency guard command:

```bash
dev/scripts/tests/measure_latency.sh --ci-guard --count 3
```
