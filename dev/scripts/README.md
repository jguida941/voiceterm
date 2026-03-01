# Developer Scripts

Canonical maintainer control plane:

```bash
python3 dev/scripts/devctl.py ...
```

Use `devctl` first for release, verification, docs-governance, and reporting.
Legacy shell scripts remain as compatibility adapters that route into `devctl`.
For active-doc discovery, use `dev/active/INDEX.md`.
For current execution scope, use `dev/active/MASTER_PLAN.md`.
For loop output to chat-suggestion coordination, use
`dev/active/loop_chat_bridge.md`.
For consolidated visual planning context (Theme Studio + overlay research +
redesign), use `dev/active/theme_upgrade.md`.
For a quick lifecycle/check/push guide, see `dev/DEVELOPMENT.md` sections
`End-to-end lifecycle flow`, `What checks protect us`, and `When to push where`.
For automation-first `devctl` routing and Ralph loop controls, see
`dev/DEVCTL_AUTOGUIDE.md`.
For plain-language CI lane docs, see `.github/workflows/README.md`.

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
# `release` adds strict remote gates: `status --ci --require-ci` + CI-mode CodeRabbit/Ralph checks.
# Optional: force sequential check execution (parallel phases are default)
python3 dev/scripts/devctl.py check --profile ci --no-parallel
# Optional: disable automatic orphaned/stale test-process cleanup sweep
python3 dev/scripts/devctl.py check --profile ci --no-process-sweep-cleanup

# Docs + governance checks
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
# Optional: automatically clear detected dev/scripts/**/__pycache__ dirs
python3 dev/scripts/devctl.py hygiene --fix
python3 dev/scripts/devctl.py path-audit
python3 dev/scripts/devctl.py path-rewrite --dry-run
python3 dev/scripts/devctl.py path-rewrite
# Branch sync guardrail helper (develop/master/current by default)
python3 dev/scripts/devctl.py sync
# Also push local-ahead branches after sync
python3 dev/scripts/devctl.py sync --push
# Federated repo source pins (code-link-ide + ci-cd-hub)
python3 dev/scripts/devctl.py integrations-sync --status-only
python3 dev/scripts/devctl.py integrations-sync --remote
# Allowlisted selective import from pinned federated sources
python3 dev/scripts/devctl.py integrations-import --list-profiles --format md
python3 dev/scripts/devctl.py integrations-import --source code-link-ide --profile iphone-core --format md
python3 dev/scripts/devctl.py integrations-import --source ci-cd-hub --profile workflow-templates --apply --yes --format md
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
# CodeRabbit release gates (strict local verification mode).
CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master
python3 dev/scripts/checks/run_coderabbit_ralph_loop.py --repo owner/repo --branch develop --max-attempts 3 --format md
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_markdown_metadata_header.py
# Auto-fix markdown metadata header style where Status/Last updated/Owner blocks exist
python3 dev/scripts/checks/check_markdown_metadata_header.py --fix
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
# `docs-check --strict-tooling` enforces ENGINEERING_EVOLUTION updates for tooling/process/CI shifts and runs active-plan + multi-agent sync gates, markdown metadata-header style checks, plus stale-path audit (using `dev/scripts/devctl/script_catalog.py` as canonical check-script path registry). Use `path-rewrite` to auto-fix stale path references.
# For UI behavior changes, refresh screenshot coverage in the same pass:
# see dev/DEVELOPMENT.md -> "Screenshot refresh capture matrix".

# Triage output for humans + AI agents (optional CIHub ingestion)
python3 dev/scripts/devctl.py triage --ci --format md --output /tmp/devctl-triage.md
python3 dev/scripts/devctl.py triage --ci --cihub --emit-bundle --bundle-dir .cihub --bundle-prefix triage
# Optional: route categories to team owners via JSON map
python3 dev/scripts/devctl.py triage --ci --cihub --owner-map-file dev/config/triage_owner_map.json --format json
# Optional: ingest external AI-review findings (CodeRabbit, custom bots, etc.)
python3 dev/scripts/devctl.py triage --no-cihub --external-issues-file .cihub/coderabbit/priority.json --format md --output /tmp/devctl-triage-external.md
# Bounded CodeRabbit backlog loop (report/fix attempts + bundle evidence)
python3 dev/scripts/devctl.py triage-loop --repo owner/repo --branch develop --mode plan-then-fix --max-attempts 3 --source-event workflow_dispatch --notify summary-and-comment --comment-target auto --emit-bundle --bundle-dir .cihub/coderabbit --bundle-prefix coderabbit-ralph-loop --mp-proposal --format md --output /tmp/coderabbit-ralph-loop.md --json-output /tmp/coderabbit-ralph-loop.json
# Record operator-facing suggestion decisions in dev/active/loop_chat_bridge.md
# after each dry-run/live-run loop packet.
# Bounded mutation remediation loop (report-only default, optional policy-gated fix mode)
python3 dev/scripts/devctl.py mutation-loop --repo owner/repo --branch develop --mode report-only --threshold 0.80 --max-attempts 3 --emit-bundle --bundle-dir .cihub/mutation --bundle-prefix mutation-ralph-loop --format md --output /tmp/mutation-ralph-loop.md --json-output /tmp/mutation-ralph-loop.json
# Bounded autonomy controller loop (triage-loop + loop-packet + checkpoint queue + phone-status artifacts)
python3 dev/scripts/devctl.py autonomy-loop --repo owner/repo --plan-id acp-poc-001 --branch-base develop --mode report-only --max-rounds 6 --max-hours 4 --max-tasks 24 --checkpoint-every 1 --loop-max-attempts 1 --packet-out dev/reports/autonomy/packets --queue-out dev/reports/autonomy/queue --format json --output /tmp/autonomy-controller.json
# iPhone/SSH-safe controller status projection view from queue artifacts
python3 dev/scripts/devctl.py phone-status --phone-json dev/reports/autonomy/queue/phone/latest.json --view compact --emit-projections dev/reports/autonomy/controller_state/latest --format md --output /tmp/phone-status.md
# Policy-gated controller actions (safe subset: refresh, report-only dispatch, pause/resume)
python3 dev/scripts/devctl.py controller-action --action refresh-status --view compact --format md --output /tmp/controller-action-refresh.md
python3 dev/scripts/devctl.py controller-action --action dispatch-report-only --repo owner/repo --branch develop --dry-run --format md --output /tmp/controller-action-dispatch.md
python3 dev/scripts/devctl.py controller-action --action pause-loop --repo owner/repo --mode-file dev/reports/autonomy/queue/phone/controller_mode.json --dry-run --format md --output /tmp/controller-action-pause.md
python3 dev/scripts/devctl.py controller-action --action resume-loop --repo owner/repo --mode-file dev/reports/autonomy/queue/phone/controller_mode.json --dry-run --format md --output /tmp/controller-action-resume.md
# Human-readable autonomy digest bundle (dated library + md/json + charts)
python3 dev/scripts/devctl.py autonomy-report --source-root dev/reports/autonomy --library-root dev/reports/autonomy/library --run-label daily-ops --format md --output /tmp/autonomy-report.md --json-output /tmp/autonomy-report.json
# Adaptive autonomy swarm (auto-select agent count from metadata + token budget)
python3 dev/scripts/devctl.py autonomy-swarm --question "large refactor across runtime/parser/security" --prompt-tokens 48000 --token-budget 120000 --max-agents 20 --parallel-workers 6 --dry-run --no-post-audit --run-label swarm-plan --format md --output /tmp/autonomy-swarm.md --json-output /tmp/autonomy-swarm.json
# Live swarm defaults (reserves AGENT-REVIEW when possible and auto-runs digest)
python3 dev/scripts/devctl.py autonomy-swarm --agents 10 --question-file dev/active/autonomous_control_plane.md --mode report-only --run-label swarm-live --format md --output /tmp/autonomy-swarm-live.md --json-output /tmp/autonomy-swarm-live.json
# Swarm benchmark matrix (active-plan-scoped tactics x swarm-size tradeoff report)
python3 dev/scripts/devctl.py autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --swarm-counts 10,15,20,30,40 --tactics uniform,specialized,research-first,test-first --agents 4 --parallel-workers 4 --max-concurrent-swarms 10 --dry-run --format md --output /tmp/autonomy-benchmark.md --json-output /tmp/autonomy-benchmark.json
# Full guarded plan pipeline (scope load + swarm + reviewer + governance + plan evidence append)
python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --agents 10 --mode report-only --run-label swarm-guarded --format md --output /tmp/swarm-run.md --json-output /tmp/swarm-run.json
# Optional continuous mode: keep cycling through checklist scope until failure/limit
python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --mode report-only --continuous --continuous-max-cycles 10 --feedback-sizing --feedback-no-signal-rounds 2 --feedback-stall-rounds 2 --run-label swarm-continuous --format md --output /tmp/swarm-run-continuous.md --json-output /tmp/swarm-run-continuous.json
# CI note: `.github/workflows/coderabbit_triage.yml` enforces a blocking
# medium/high severity gate for CodeRabbit findings, and `release_preflight.yml`
# verifies that gate passed for the exact release commit. Publish workflows
# (`publish_pypi`, `publish_homebrew`, `release_attestation`) also enforce
# the same gate before distribution/attestation steps run.
# Scorecard note: keep workflow-level permissions read-only and place
# `id-token: write`/`security-events: write` at the scorecard job level so
# OpenSSF `publish_results` verification passes.
# Pinning note: keep GitHub-owned actions pinned to valid 40-character SHAs
# (for example `actions/attest-build-provenance`, `github/codeql-action/upload-sarif`).
# If your cihub binary doesn't support `triage`, devctl records an infra warning
# and still emits local triage output.
# Explicit `--cihub` now forces the capability probe path even when PATH lookup
# cannot resolve the binary during preflight checks.
# Loop comment publication uses API endpoints with explicit `/repos/{owner}/{repo}`
# paths and does not append `--repo` to `gh api` calls.
# Clean local failure triage bundles only after CI is green
python3 dev/scripts/devctl.py failure-cleanup --require-green-ci --dry-run
python3 dev/scripts/devctl.py failure-cleanup --require-green-ci --yes
# Clean stale run artifacts under dev/reports with retention safeguards
python3 dev/scripts/devctl.py reports-cleanup --dry-run
python3 dev/scripts/devctl.py reports-cleanup --max-age-days 30 --keep-recent 10 --yes
# Generate a guard-driven remediation scaffold for Rust modularity/pattern debt
python3 dev/scripts/devctl.py audit-scaffold --force --yes --format md
# Commit-range scoped scaffold generation (useful in CI/PR review lanes)
python3 dev/scripts/devctl.py audit-scaffold --since-ref origin/develop --head-ref HEAD --force --yes --format json
# Audit-cycle metrics (automation coverage, AI-vs-script share, chart outputs)
python3 dev/scripts/audits/audit_metrics.py \
  --input dev/reports/audits/baseline-events.jsonl \
  --output-md dev/reports/audits/baseline-metrics.md \
  --output-json dev/reports/audits/baseline-metrics.json \
  --chart-dir dev/reports/audits/charts
# Auto-emitted devctl event logging (default: dev/reports/audits/devctl_events.jsonl)
DEVCTL_AUDIT_CYCLE_ID=baseline-2026-02-24 \
DEVCTL_EXECUTION_SOURCE=script_only \
python3 dev/scripts/devctl.py check --profile ci
# Data-science snapshot (command telemetry + swarm/benchmark agent sizing stats)
python3 dev/scripts/devctl.py data-science --format md --output /tmp/data-science-summary.md
# Optional: gate cleanup against a scoped CI slice
python3 dev/scripts/devctl.py failure-cleanup --require-green-ci --ci-branch develop --ci-event push --ci-workflow "Rust TUI CI" --dry-run
# Optional: override the default cleanup root guard (still restricted to dev/reports/**)
python3 dev/scripts/devctl.py failure-cleanup --directory dev/reports/archive-failures --allow-outside-failure-root --dry-run
# Optional: tighten retention when report growth spikes
python3 dev/scripts/devctl.py reports-cleanup --max-age-days 14 --keep-recent 5 --dry-run
# Workflow note: failure-triage branch scope defaults to develop/master and can be overridden
# with GitHub repo variable FAILURE_TRIAGE_BRANCHES (comma-separated branch names, no spaces).

# Release notes from git diff range
python3 dev/scripts/devctl.py release-notes --version X.Y.Z

# Coverage workflow (mirrors .github/workflows/coverage.yml)
cd rust && cargo llvm-cov --workspace --all-features --lcov --output-path lcov.info
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
CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow publish_release_binaries.yml --limit 1
gh run list --workflow release_attestation.yml --limit 1

# Optional: run release preflight workflow in CI before tagging
gh workflow run release_preflight.yml -f version=X.Y.Z -f verify_docs=true

# External integrations (pinned vendor bridges for reusable patterns)
bash dev/scripts/sync_external_integrations.sh --status-only
bash dev/scripts/sync_external_integrations.sh
bash dev/scripts/sync_external_integrations.sh --remote

# Optional: manually trigger Homebrew workflow for an existing tag/version
gh workflow run publish_homebrew.yml -f version=X.Y.Z -f release_branch=master
# Optional: manually trigger bounded CodeRabbit backlog remediation loop
gh workflow run coderabbit_ralph_loop.yml -f branch=develop -f max_attempts=3 -f execution_mode=plan-then-fix
# Optional auto-run config (repo variables):
# RALPH_LOOP_MODE=always              # always|failure-only|disabled
# RALPH_EXECUTION_MODE=plan-then-fix  # report-only|plan-then-fix|fix-only
# RALPH_LOOP_MAX_ATTEMPTS=3
# RALPH_LOOP_POLL_SECONDS=20
# RALPH_LOOP_TIMEOUT_SECONDS=1800
# RALPH_LOOP_FIX_COMMAND='<your auto-fix command that commits + pushes>'
# RALPH_NOTIFY_MODE=summary-and-comment
# RALPH_COMMENT_TARGET=auto
# RALPH_COMMENT_PR_NUMBER=<optional pr number>
# Optional: manually trigger bounded Mutation remediation loop
gh workflow run mutation_ralph_loop.yml -f branch=develop -f execution_mode=report-only -f threshold=0.80
# Optional: manually trigger bounded autonomy controller loop
gh workflow run autonomy_controller.yml -f plan_id=acp-poc-001 -f branch_base=develop -f mode=report-only -f max_rounds=6 -f max_hours=4 -f max_tasks=24 -f checkpoint_every=1 -f loop_max_attempts=1 -f notify_mode=summary-only -f promote_pr=false
# Optional: manually trigger guarded plan-scoped swarm pipeline
gh workflow run autonomy_run.yml -f plan_doc=dev/active/autonomous_control_plane.md -f mp_scope=MP-338 -f branch_base=develop -f mode=report-only -f agents=10 -f dry_run=true
# Optional auto-run config (repo variables):
# MUTATION_LOOP_MODE=always               # always|failure-only|disabled
# MUTATION_EXECUTION_MODE=report-only     # report-only|plan-then-fix|fix-only
# MUTATION_LOOP_MAX_ATTEMPTS=3
# MUTATION_LOOP_POLL_SECONDS=20
# MUTATION_LOOP_TIMEOUT_SECONDS=1800
# MUTATION_LOOP_THRESHOLD=0.80
# MUTATION_LOOP_FIX_COMMAND='<allowlisted fix command that commits + pushes>'
# MUTATION_NOTIFY_MODE=summary-only
# MUTATION_COMMENT_TARGET=auto
# MUTATION_COMMENT_PR_NUMBER=<optional pr number>
# AUTONOMY_MODE=read-only                 # off|read-only|operate
# MUTATION_LOOP_ALLOWED_PREFIXES='python3 dev/scripts/devctl.py check --profile ci;python3 dev/scripts/devctl.py mutants'
# TRIAGE_LOOP_ALLOWED_PREFIXES='python3 dev/scripts/devctl.py check --profile ci'

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
| `dev/scripts/sync_external_integrations.sh` | External integration sync helper | Syncs pinned `integrations/code-link-ide` and `integrations/ci-cd-hub` submodules (optional `--remote` tracking updates). |
| `dev/scripts/update-homebrew.sh` | Legacy adapter | Routes to `devctl homebrew`; internal mode syncs formula URL/version/SHA, canonical `desc`, and rewrites legacy Cargo manifest paths from `libexec/src/Cargo.toml` to `libexec/rust/Cargo.toml`. |
| `dev/scripts/mutants.py` | Mutation helper | Interactive module/shard helper with `--shard`, `--results-only`, and JSON hotspot output (includes outcomes source age metadata). |
| `dev/scripts/mutants_plot.py` | Mutation plot helper | Shared hotspot plotting helpers imported by `mutants.py` (keeps CLI logic and plotting logic separated for shape governance). |
| `dev/scripts/checks/check_mutation_score.py` | Mutation score gate | Used in CI and local validation; prints outcomes source freshness and supports `--max-age-hours` stale-data gating. |
| `dev/scripts/checks/check_agents_contract.py` | AGENTS contract gate | Verifies required AGENTS SOP sections, bundles, and routing rows are present. |
| `dev/scripts/checks/check_active_plan_sync.py` | Active-plan sync gate | Verifies `dev/active/INDEX.md` registry coverage, tracker authority, mirrored-spec phase headings, cross-doc links, `MP-*` scope parity between index/spec docs and `MASTER_PLAN`, and `MASTER_PLAN` Status Snapshot release metadata freshness. |
| `dev/scripts/checks/check_multi_agent_sync.py` | Multi-agent coordination gate | Verifies `MASTER_PLAN` board parity with `MULTI_AGENT_WORKTREE_RUNBOOK.md` for dynamic `AGENT-<N>` lanes (lane/MP/worktree/branch alignment, instruction/ack protocol checks, lane-lock + MP-collision handoff checks, status/date formatting, ledger traceability, and required end-of-cycle signoff when all agent lanes are merged). |
| `dev/scripts/checks/check_release_version_parity.py` | Release version parity gate | Ensures Cargo, PyPI, and macOS app plist versions match before tagging/publishing. |
| `dev/scripts/checks/check_coderabbit_gate.py` | CodeRabbit release gate | Verifies the latest `CodeRabbit Triage Bridge` run is successful for a target branch+commit SHA before release/publish steps proceed. |
| `dev/scripts/checks/check_coderabbit_ralph_gate.py` | CodeRabbit Ralph release gate | Verifies the latest `CodeRabbit Ralph Loop` run is successful for a target branch+commit SHA before release/publish steps proceed. |
| `dev/scripts/checks/run_coderabbit_ralph_loop.py` | CodeRabbit remediation loop | Runs a bounded retry loop over CodeRabbit medium/high backlog artifacts and optional auto-fix command hooks. |
| `dev/scripts/checks/mutation_ralph_loop_core.py` | Mutation remediation loop core helpers | Shared run/artifact/score/hotspot logic used by `devctl mutation-loop`. |
| `dev/scripts/checks/check_cli_flags_parity.py` | CLI docs/schema parity gate | Compares clap long flags in Rust schema files against `guides/CLI_FLAGS.md`. |
| `dev/scripts/checks/check_markdown_metadata_header.py` | Markdown metadata header style gate | Normalizes `Status`/`Last updated`/`Owner` doc metadata to one canonical line style. |
| `dev/scripts/checks/check_screenshot_integrity.py` | Screenshot docs integrity gate | Validates markdown image references and reports stale screenshot age. |
| `dev/scripts/checks/check_code_shape.py` | Source-shape drift guard | Blocks new Rust/Python God-file growth using language-level soft/hard limits plus path-level hotspot budgets for active decomposition targets, and emits audit-first remediation guidance (modularize/consolidate before merge, with Python/Rust best-practice links). |
| `dev/scripts/checks/check_rust_lint_debt.py` | Rust lint-debt non-regression guard | Fails when changed non-test Rust files increase `#[allow(...)]` usage or `unwrap/expect` call-sites. |
| `dev/scripts/checks/check_rust_best_practices.py` | Rust best-practices non-regression guard | Fails when changed non-test Rust files increase reason-less `#[allow(...)]`, undocumented `unsafe { ... }` blocks, public `unsafe fn` surfaces lacking `# Safety` docs, or `std::mem::forget`/`mem::forget` usage. |
| `dev/scripts/checks/check_rust_audit_patterns.py` | Rust audit regression guard | Scans active Rust source roots (`rust/src`, legacy fallbacks) and fails when known critical audit anti-patterns reappear (UTF-8-unsafe prefix slicing, byte-limit truncation via `INPUT_MAX_CHARS`, single-pass `redacted.find(...)` secret redaction, deterministic timestamp-hash ID suffixes, and lossy `clamped * 32_768.0 as i16` VAD casts). |
| `dev/scripts/checks/check_rust_security_footguns.py` | Rust security-footguns non-regression guard | Fails when changed non-test Rust files add risky AI-prone patterns (`todo!/unimplemented!/dbg!`, shell-style process spawns, permissive `0o777/0o666` modes, weak-crypto references like MD5/SHA1). |
| `dev/scripts/render_ci_badge.py` | CI badge endpoint JSON renderer | Updates `.github/badges/ci-status.json` with pass/fail color state. |
| `dev/scripts/render_mutation_badge.py` | Mutation badge endpoint JSON renderer | Updates `.github/badges/mutation-score.json`. |
| `dev/scripts/checks/check_rustsec_policy.py` | RustSec policy gate | Enforces advisory thresholds. |

## Devctl Command Set

- `check`: fmt/clippy/tests/build profiles (`ci`, `prepush`, `release`, `maintainer-lint`, `quick`, `ai-guard`)
  - Runs setup gates (`fmt`, `clippy`, AI guard scripts) and test/build phases in parallel batches by default.
  - Tune parallelism with `--parallel-workers <n>` or force sequential execution with `--no-parallel`.
  - Runs an automatic orphaned/stale test-process sweep before/after checks (`target/*/deps/voiceterm-*`, detached `PPID=1`, plus stale active runners aged `>=600s`).
  - Disable only when needed with `--no-process-sweep-cleanup`.
  - `release` profile includes wake-word regression/soak guardrails, mutation-score gating, and strict remote release gates (`status --ci --require-ci`, CodeRabbit, Ralph).
  - Structured `check` report timestamps are UTC for consistent CI/local correlation.
- `mutants`: mutation test helper wrapper
- `mutation-score`: threshold gate for outcomes with freshness reporting and optional stale-data fail gate (`--max-age-hours`)
- `docs-check`: docs coverage + tooling/deprecated-command policy guard (`--strict-tooling` also runs active-plan sync + multi-agent sync + markdown metadata-header + stale-path audit)
- `hygiene`: archive/ADR/scripts governance checks plus orphaned/stale `target/debug/deps/voiceterm-*` test-process detection (stale active threshold: `>=600s`); includes automatic report-retention drift warnings for stale `dev/reports/**` run artifacts; optional `--fix` removes detected `dev/scripts/**/__pycache__` directories and re-audits scripts hygiene
- `path-audit`: stale-reference scan for legacy check-script paths (skips `dev/archive/`)
- `path-rewrite`: auto-rewrite legacy check-script paths to canonical registry targets (use `--dry-run` first)
- `sync`: guarded branch-sync workflow (clean-tree preflight, remote/local ref checks, `--ff-only` pull, optional `--push` for ahead branches, and start-branch restore)
- `integrations-sync`: guarded submodule sync/status command for pinned federated integration sources defined in `control_plane_policy.json`
- `integrations-import`: allowlisted selective importer from pinned federated sources into controlled destination roots with JSONL audit logging
- `cihub-setup`: allowlisted CIHub repo-setup helper (`detect/init/update/validate`) with capability probing, preview/apply modes, and strict unsupported-step gating
- `security`: RustSec policy checks plus optional workflow/code-scanning security scans (`--with-zizmor`, `--with-codeql-alerts`) and Python-scope selection (`--python-scope auto|changed|all`)
- `release`: tag + notes flow (legacy release behavior)
- `release-notes`: git-diff driven markdown notes generation
- `ship`: full release/distribution orchestrator with step toggles and optional metadata prep (`--prepare-release`); `--verify` now includes both CodeRabbit gates (`check_coderabbit_gate` + `check_coderabbit_ralph_gate`) and version reads from TOML roots (`[package]`/`[project]`) with Python 3.10-compatible fallback parsing
- `homebrew`: Homebrew tap update flow (URL/version/SHA + canonical formula `desc` sync + legacy Cargo manifest path rewrite to `libexec/rust/Cargo.toml`)
- `pypi`: PyPI build/check/upload flow
- `orchestrate-status`: one-shot orchestrator accountability view (active-plan sync + multi-agent sync guard status with git context)
- `orchestrate-watch`: SLA watchdog for stale lane updates and overdue instruction ACKs
- `status` and `report`: machine-readable project status outputs (optional guarded Dev Mode session summaries via `--dev-logs`, `--dev-root`, and `--dev-sessions-limit`)
- `data-science`: rolling telemetry snapshot builder that summarizes devctl event metrics plus swarm/benchmark agent-size productivity history, writes `summary.{md,json}` + SVG charts under `dev/reports/data_science/latest/`, and supports local source/output overrides for experiments
- `triage`: combined human/AI triage output with optional `cihub triage` artifact ingestion, optional external issue-file ingestion (`--external-issues-file` for CodeRabbit/custom bot payloads), and bundle emission (`<prefix>.md`, `<prefix>.ai.json`); extracts priority/triage records into normalized issue routing fields (`category`, `severity`, `owner`), supports optional category-owner overrides via `--owner-map-file`, emits rollups for severity/category/owner counts, and stamps reports with UTC timestamps
- `triage-loop`: bounded CodeRabbit medium/high loop with mode controls (`report-only`, `plan-then-fix`, `fix-only`), source-run correlation (`--source-run-id`, `--source-run-sha`, `--source-event`), policy-gated fix execution (`AUTONOMY_MODE=operate`, branch allowlist, command-prefix allowlist), notify/comment targeting (`--notify`, `--comment-target`, `--comment-pr-number`), automatic review-escalation comment upserts when max attempts are exhausted with unresolved backlog, attempt-level reporting, optional bundle emission, and optional MASTER_PLAN proposal output
- `mutation-loop`: bounded mutation remediation loop with report-only default, threshold controls, hotspot/freshness reporting, optional policy-gated fix execution, optional summary comment updates, and bundle/playbook outputs
- `autonomy-loop`: bounded autonomy controller wrapper around `triage-loop` + `loop-packet` with hard caps (`--max-rounds`, `--max-hours`, `--max-tasks`), run-scoped packet artifacts, queue inbox outputs, phone-ready status snapshots (`dev/reports/autonomy/queue/phone/latest.{json,md}`), and strict policy gating for write modes (`AUTONOMY_MODE=operate` required for non-dry-run fix modes; dry-run still downgrades to `report-only`)
- `phone-status`: iPhone/SSH-safe read surface for autonomy controller snapshots; renders one selected projection view (`full|compact|trace|actions`) from `dev/reports/autonomy/queue/phone/latest.json` and can emit controller-state files (`full.json`, `compact.json`, `trace.ndjson`, `actions.json`, `latest.md`)
- `controller-action`: policy-gated control surface for `refresh-status`, `dispatch-report-only`, `pause-loop`, and `resume-loop`; dispatch/mode actions enforce allowlisted workflows/branches, respect `AUTONOMY_MODE=off` kill-switch behavior, and emit auditable action reports plus optional local controller-mode state artifact
- `autonomy-benchmark`: active-plan-scoped swarm benchmark matrix runner (`swarm-counts x tactics`) that launches `autonomy-swarm` batches, captures per-swarm/per-scenario productivity metrics, and writes benchmark bundles under `dev/reports/autonomy/benchmarks/<label>` (non-report modes require `--fix-command`)
- `swarm_run`: guarded autonomy pipeline wrapper around `autonomy-swarm` that loads plan scope context, derives next unchecked plan steps into one prompt, enforces reviewer lane + post-audit digest, runs governance checks (`check_active_plan_sync`, `check_multi_agent_sync`, `docs-check --strict-tooling`, `orchestrate-status/watch`), and appends run evidence to the active plan doc (`Progress Log` + `Audit Evidence`); supports optional continuous multi-cycle execution (`--continuous --continuous-max-cycles`) plus feedback sizing controls (`--feedback-sizing`, `--feedback-no-signal-rounds`, `--feedback-stall-rounds`, `--feedback-downshift-factor`, `--feedback-upshift-rounds`, `--feedback-upshift-factor`) for hands-off checklist progression (non-report modes require `--fix-command`)
- `autonomy-report`: human-readable autonomy digest builder that scans loop/watch artifacts, writes dated bundles under `dev/reports/autonomy/library/<label>`, and emits summary markdown/json plus optional matplotlib charts
- `autonomy-swarm`: adaptive swarm orchestrator that sizes agent count from change/question metadata (with optional token-budget cap), runs per-agent bounded `autonomy-loop` lanes in parallel, reserves a default `AGENT-REVIEW` lane for post-audit review when execution runs with >1 lane, writes one dated swarm bundle under `dev/reports/autonomy/swarms/<label>`, and by default runs a post-audit digest bundle under `dev/reports/autonomy/library/<label>-digest` (use `--no-post-audit` and/or `--no-reviewer-lane` to disable; non-report modes require `--fix-command`)
- `failure-cleanup`: guarded cleanup for local failure triage bundles (`dev/reports/failures`) with default path-root enforcement, optional override constrained to `dev/reports/**` (`--allow-outside-failure-root`), optional scoped CI gate filters (`--ci-branch`, `--ci-workflow`, `--ci-event`, `--ci-sha`), plus dry-run/confirmation controls
- `reports-cleanup`: retention-based cleanup for stale run artifacts under managed `dev/reports/**` roots (default `max-age-days=30`, `keep-recent=10`) with protected paths, preview mode (`--dry-run`), and explicit confirmation/`--yes` before deletion
- `audit-scaffold`: build/update `dev/active/RUST_AUDIT_FINDINGS.md` from guard findings (with safe output path and overwrite guards)
- `list`: command/profile inventory

## Quick command guide (plain language)

| Command | Run it when | Why |
|---|---|---|
| `check --profile ci` | before a normal push | catches build/test/lint issues early |
| `data-science --format md` | you want a fresh productivity/agent-sizing snapshot from current telemetry | builds `summary.{md,json}` + charts from devctl events and swarm/benchmark history |
| `check --profile release` | before release/tag verification on `master` | adds strict remote CI-status + CodeRabbit/Ralph release gates on top of local release checks |
| `check --profile ai-guard` | after touching larger Rust/Python files | catches shape/lint-debt/best-practice drift |
| `docs-check --user-facing` | you changed user docs or user behavior | keeps docs and behavior aligned |
| `docs-check --strict-tooling` | you changed tooling, workflows, or process docs | enforces governance and active-plan sync |
| `hygiene` | before merge on tooling/process work | catches doc/process drift and leaked runtime test processes |
| `hygiene --fix` | after local test runs leave Python caches | clears `dev/scripts/**/__pycache__` safely and re-checks hygiene |
| `reports-cleanup --dry-run` | hygiene warns that report artifacts are stale/heavy | previews what retention cleanup would remove without deleting anything |
| `security` | you changed dependencies or security-sensitive code | catches advisory/policy issues |
| `triage --ci` | CI failed and you need an actionable summary | creates a clean failure summary for humans/AI |
| `triage-loop --branch develop --mode plan-then-fix --max-attempts 3` | you want bounded automation over medium/high backlog | runs report/fix retry loop with deterministic md/json artifacts |
| `mutation-loop --branch develop --mode report-only --threshold 0.80` | you want bounded mutation-score automation with hotspots and optional fixes | runs report/fix retry loop with deterministic md/json/playbook artifacts |
| `autonomy-loop --plan-id acp-poc-001 --branch-base develop --mode report-only --max-rounds 6 --max-hours 4 --max-tasks 24 --format json` | you want one bounded controller run that emits queue-ready checkpoint packets | orchestrates triage-loop/loop-packet rounds, writes run-scoped packet artifacts, and refreshes phone-ready `latest.json`/`latest.md` status snapshots |
| `phone-status --phone-json dev/reports/autonomy/queue/phone/latest.json --view compact --format md` | you want one iPhone/SSH-safe autonomy snapshot | renders a selected phone-status projection view and can emit controller-state projection files for downstream clients |
| `controller-action --action dispatch-report-only --repo owner/repo --branch develop --dry-run --format md` | you want one guarded operator action without ad-hoc shell scripting | validates policy + mode gates and executes (or previews) bounded dispatch/pause/resume/status actions with structured output |
| `autonomy-benchmark --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --swarm-counts 10,15,20,30,40 --tactics uniform,specialized,research-first,test-first --dry-run` | you want measurable swarm tradeoff data before scaling live runs | validates active-plan scope, runs tactic/swarm-size matrix batches, and emits one benchmark report with per-scenario metrics/charts |
| `swarm_run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --mode report-only --run-label <label>` | you want one fully-guarded plan-scoped swarm run without manual glue steps | loads active-plan scope, executes swarm with reviewer+post-audit defaults, runs governance checks, appends progress/audit evidence to the plan doc, and in continuous mode can auto-tune agent count with `--feedback-*` sizing controls |
| `autonomy-report --source-root dev/reports/autonomy --library-root dev/reports/autonomy/library --run-label daily-ops` | you want one human-readable autonomy digest | bundles latest loop/watch artifacts into a dated folder with summary markdown/json and optional charts |
| `autonomy-swarm --question \"<scope>\" --prompt-tokens <n> --token-budget <n>` | you want adaptive multi-agent autonomy execution | computes recommended agent count from metadata + budget, reserves one default reviewer lane (`AGENT-REVIEW`) when possible, runs bounded loops, writes one swarm summary bundle, then auto-runs a post-audit digest bundle (unless `--no-post-audit`) |
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
- `dev/scripts/devctl/triage_loop_parser.py`: shared CLI parser wiring for the
  `triage-loop` command.
- `dev/scripts/devctl/loop_fix_policy.py`: shared fix-policy engine used by
  both `triage-loop` and `mutation-loop` wrappers.
- `dev/scripts/devctl/triage_loop_policy.py`: shared policy-gate evaluation
  for `triage-loop` fix execution (`AUTONOMY_MODE`, branch allowlist, command
  prefix allowlist).
- `dev/scripts/devctl/triage_loop_escalation.py`: shared review-escalation
  comment renderer/upsert helper for `triage-loop`.
- `dev/scripts/devctl/triage_loop_support.py`: shared connectivity/comment/
  bundle helper logic used by `triage-loop`.
- `dev/scripts/devctl/autonomy_loop_parser.py`: shared CLI parser wiring for
  the `autonomy-loop` controller command.
- `dev/scripts/devctl/autonomy_benchmark_parser.py`: shared CLI parser wiring
  for the `autonomy-benchmark` swarm-matrix command.
- `dev/scripts/devctl/autonomy_run_parser.py`: shared CLI parser wiring for
  the `swarm_run` guarded plan-scoped swarm command.
- `dev/scripts/devctl/autonomy_benchmark_helpers.py`: shared helpers for
  `autonomy-benchmark` scenario orchestration, tactic prompts, and metric
  aggregation.
- `dev/scripts/devctl/autonomy_benchmark_matrix.py`: swarm-matrix execution
  helpers for `autonomy-benchmark`.
- `dev/scripts/devctl/autonomy_benchmark_runner.py`: per-scenario runner and
  bundle helpers for `autonomy-benchmark`.
- `dev/scripts/devctl/autonomy_benchmark_render.py`: markdown/chart renderer
  for `autonomy-benchmark` bundles.
- `dev/scripts/devctl/autonomy_run_helpers.py`: shared helpers for
  `swarm_run` scope validation, prompt derivation, command fanout, and plan
  markdown section updates.
- `dev/scripts/devctl/autonomy_run_feedback.py`: closed-loop sizing helpers
  for `swarm_run` continuous mode (cycle signal extraction + downshift/upshift decisions).
- `dev/scripts/devctl/autonomy_run_render.py`: markdown renderer for
  `swarm_run` run bundles.
- `dev/scripts/devctl/autonomy_report_helpers.py`: data-collection helpers for
  `autonomy-report` source discovery, summarization, and bundle assembly.
- `dev/scripts/devctl/autonomy_report_render.py`: markdown/chart rendering
  helpers used by `autonomy-report` output bundles.
- `dev/scripts/devctl/autonomy_swarm_helpers.py`: adaptive swarm planning
  helpers (metadata scoring, agent-count recommendation, swarm report rendering/charts).
- `dev/scripts/devctl/autonomy_swarm_post_audit.py`: shared post-audit helper
  logic used by `autonomy-swarm` for digest payload normalization and bundle writes.
- `dev/scripts/devctl/autonomy_loop_helpers.py`: shared autonomy-loop
  policy/schema helpers (caps, packet refs, trace extraction, markdown render).
- `dev/scripts/devctl/autonomy_phone_status.py`: phone-status payload + markdown
  helpers used by `autonomy-loop` queue snapshots.
- `dev/scripts/devctl/phone_status_views.py`: projection/render helpers used by
  `phone-status` (`full|compact|trace|actions`) and controller-state bundle writes.
- `dev/scripts/devctl/autonomy_status_parsers.py`: shared parser wiring for
  `autonomy-report` and `phone-status`.
- `dev/scripts/devctl/controller_action_parser.py`: parser wiring for
  `controller-action`.
- `dev/scripts/devctl/controller_action_support.py`: policy/mode/dispatch
  helper logic used by `controller-action`.
- `dev/scripts/devctl/mutation_loop_parser.py`: shared CLI parser wiring for
  the `mutation-loop` command.
- `dev/scripts/devctl/failure_cleanup_parser.py`: shared CLI parser wiring for
  the `failure-cleanup` command.
- `dev/scripts/devctl/reports_cleanup_parser.py`: shared CLI parser wiring for
  the `reports-cleanup` command.
- `dev/scripts/devctl/reports_retention.py`: shared report-retention planning
  helpers used by both `hygiene` warnings and `reports-cleanup`.
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
- `dev/scripts/devctl/commands/triage_loop.py`: bounded CodeRabbit loop command
  with source-run correlation controls and summary/comment notification wiring.
- `dev/scripts/devctl/commands/controller_action.py`: policy-gated operator
  action command (`refresh-status`, `dispatch-report-only`, `pause-loop`, `resume-loop`).
- `dev/scripts/devctl/commands/autonomy_loop.py`: bounded autonomy controller
  command that runs triage-loop/loop-packet rounds and emits packet/queue
  artifacts for phone/chat handoff paths.
- `dev/scripts/devctl/commands/autonomy_benchmark.py`: active-plan-scoped
  swarm matrix benchmark command that compares tactic/swarm-size tradeoffs.
- `dev/scripts/devctl/commands/autonomy_report.py`: autonomy digest command
  that writes dated human-readable summaries under `dev/reports/autonomy/library`.
- `dev/scripts/devctl/commands/autonomy_run.py`: guarded plan-scoped autonomy
  pipeline command that executes swarm + governance + plan-evidence append in
  one step.
- `dev/scripts/devctl/commands/autonomy_swarm.py`: adaptive swarm command that
  auto-sizes and runs parallel autonomy-loop lanes with one consolidated report bundle.
- `dev/scripts/devctl/commands/autonomy_loop_support.py`: validation and
  policy-deny report helpers used by `autonomy-loop`.
- `dev/scripts/devctl/commands/autonomy_loop_rounds.py`: per-round controller
  execution helper for `autonomy-loop` (triage-loop/loop-packet/checkpoint +
  phone snapshot emission).
- `dev/scripts/devctl/commands/mutation_loop.py`: bounded mutation loop command
  with report/fix modes, hotspot playbook output, and policy-gated fix paths.
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
- `dev/scripts/devctl/commands/reports_cleanup.py`: retention-based stale
  report cleanup command for managed run-artifact roots under `dev/reports/**`
  with protected paths, dry-run preview, and confirmation-safe deletion flow.
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
CI=1 python3 dev/scripts/checks/check_coderabbit_gate.py --branch master
CI=1 python3 dev/scripts/checks/check_coderabbit_ralph_gate.py --branch master
# Optional: auto-prepare these files in one step
python3 dev/scripts/devctl.py ship --version X.Y.Z --prepare-release

# 2) create tag + notes
python3 dev/scripts/devctl.py release --version X.Y.Z

# 3) publish GitHub release (triggers publish_pypi.yml + publish_homebrew.yml + publish_release_binaries.yml + release_attestation.yml)
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file /tmp/voiceterm-release-vX.Y.Z.md

# 4) monitor publish workflows
gh run list --workflow publish_pypi.yml --limit 1
gh run list --workflow publish_homebrew.yml --limit 1
gh run list --workflow publish_release_binaries.yml --limit 1
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
gh run list --workflow publish_release_binaries.yml --limit 1
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

Workspace-path note:
- `dev/scripts/tests/measure_latency.sh` auto-detects `rust/` and falls back to
  legacy `src/` so CI/local guard commands remain stable across migration-era
  branches.
