# GitHub Workflows (Simple Guide)

This folder has our CI and release workflows.

Goal: keep workflow docs simple and accurate.

Rules we follow:

1. Keep language plain. Say what the workflow does and why.
2. Keep a short purpose comment at the top of every workflow file.
3. Keep details here in this README.
4. When a workflow changes, update this file in the same PR.

For exact run-by-run detail, open the workflow run in GitHub and read:

- the job summary
- uploaded artifacts
- failed step logs

## Core product quality workflows

| Workflow file | What it does | When it runs | Main checks/actions | First local command |
|---|---|---|---|---|
| `rust_ci.yml` | Main Rust quality lane. | Push/PR when runtime paths or this workflow change. | `cargo fmt`, `cargo clippy`, `cargo test`, CI badge update. | `python3 dev/scripts/devctl.py check --profile ci` |
| `voice_mode_guard.yml` | Protects macro mode + send mode behavior. | Push/PR on runtime path changes. | Targeted `cargo test` checks for macro/send mode paths. | `python3 dev/scripts/devctl.py check --profile ci` |
| `wake_word_guard.yml` | Protects wake-word behavior. | Push/PR on runtime + wake-word guard script changes. | Runs wake-word guard script. | `bash dev/scripts/tests/wake_word_guard.sh` |
| `latency_guard.yml` | Protects latency behavior from regressions. | Push/PR on runtime + latency script changes. | Runs synthetic latency guard script. | `./dev/scripts/tests/measure_latency.sh --ci-guard` |
| `perf_smoke.yml` | Quick performance sanity checks. | Push/PR on runtime path changes. | Perf smoke test + metrics check. | `python3 dev/scripts/devctl.py check --profile prepush` |
| `memory_guard.yml` | Protects thread/memory teardown behavior. | Push/PR on runtime path changes. | Targeted memory guard test loop. | `cd rust && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture` |
| `parser_fuzz_guard.yml` | Protects ANSI/parser boundaries. | Daily schedule, manual run, and push/PR on parser path changes. | Property-style parser boundary tests. | `python3 dev/scripts/devctl.py check --profile prepush` |
| `lint_hardening.yml` | Stricter Rust lint lane for maintainers. | Push/PR on runtime/devctl path changes. | `devctl check --profile maintainer-lint`. | `python3 dev/scripts/devctl.py check --profile maintainer-lint` |
| `security_guard.yml` | Security lane for Rust/Python/workflow checks. | Daily schedule, manual run, and push/PR on security/tooling path changes. | Core security tier, Rust audit-pattern guard, workflow security scan, CodeQL analysis. | `python3 dev/scripts/devctl.py security` |
| `coverage.yml` | Builds and uploads Rust coverage. | Push on `master`/`develop`, PRs on runtime paths, and manual run. | `cargo llvm-cov` + Codecov upload + LCOV artifact. | `cd rust && cargo llvm-cov --workspace --all-features --lcov --output-path lcov.info` |
| `mutation-testing.yml` | Nightly mutation run + score tracking. | Nightly schedule and manual run. | Sharded `cargo mutants`, aggregate mutation score, badge update. | `python3 dev/scripts/devctl.py mutation-score --threshold 0.80 --max-age-hours 72` |

## Docs, process, and policy workflows

| Workflow file | What it does | When it runs | Main checks/actions | First local command |
|---|---|---|---|---|
| `docs_lint.yml` | Lints user/developer markdown docs. | Push/PR on key markdown docs and lint config paths. | `markdownlint` for key docs. | `python3 dev/scripts/devctl.py docs-check --user-facing` |
| `workflow_lint.yml` | Lints workflow YAML syntax/structure. | Push/PR on workflow file changes. | Runs `actionlint`. | `python3 dev/scripts/devctl.py docs-check --strict-tooling` |
| `dependency_review.yml` | Checks dependency-risk deltas in PRs. | PRs that touch lockfiles/manifests/workflows/dependabot config. | `actions/dependency-review-action`. | `python3 dev/scripts/devctl.py security` |
| `tooling_control_plane.yml` | Main tooling/governance gate. | Push/PR on tooling/docs/governance/workflow paths. | Devctl unit tests, script integrity, strict docs/governance checks, remediation scaffold on failure. | `python3 dev/scripts/devctl.py docs-check --strict-tooling` |
| `orchestrator_watchdog.yml` | Watches multi-agent status freshness. | Every 15 minutes and manual run. | `devctl orchestrate-status` + `devctl orchestrate-watch`. | `python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 30 --format md` |
| `scorecard.yml` | Supply-chain posture drift checks. | Weekly schedule, branch protection changes, `master` push, and manual run. | OpenSSF Scorecard + SARIF upload. | `python3 dev/scripts/devctl.py security --with-zizmor` |

## AI triage and autonomy workflows

| Workflow file | What it does | When it runs | Main checks/actions | First local command |
|---|---|---|---|---|
| `coderabbit_triage.yml` | Pulls CodeRabbit findings into one triage format. | Push to `develop`/`master`, review/comment events, and manual run. | Collect findings, build triage bundles, enforce medium/high gate, upload artifacts. | `python3 dev/scripts/devctl.py triage --no-cihub --external-issues-file .cihub/coderabbit/priority.json --format md` |
| `coderabbit_ralph_loop.yml` | Bounded remediation loop for CodeRabbit backlog. | After triage workflow completes (`workflow_run`) and manual run. | `devctl triage-loop` + policy-gated fix attempts + summary/artifact publication + review-escalation comments when retries exhaust unresolved findings. | `python3 dev/scripts/devctl.py triage-loop --repo owner/repo --branch develop --mode report-only --max-attempts 3 --format md` |
| `mutation_ralph_loop.yml` | Bounded remediation loop for mutation backlog. | After mutation workflow completes (`workflow_run`) and manual run. | `devctl mutation-loop` + summary/artifact publication. | `python3 dev/scripts/devctl.py mutation-loop --repo owner/repo --branch develop --mode report-only --threshold 0.80 --max-attempts 3 --format md` |
| `failure_triage.yml` | Auto-captures context when another workflow fails. | On completion of listed workflows (`workflow_run`). | Download source-run artifacts, run triage snapshot, publish failure bundle. | `python3 dev/scripts/devctl.py triage --ci --format md` |
| `autonomy_controller.yml` | Runs bounded controller rounds and emits queue packets. | Every 6 hours and manual run. | `devctl autonomy-loop`, summary/artifact publishing, optional PR promote job. | `python3 dev/scripts/devctl.py autonomy-loop --repo owner/repo --plan-id acp-poc-001 --branch-base develop --mode report-only --format json` |
| `autonomy_run.yml` | Runs guarded plan-scoped swarm execution. | Manual run (`workflow_dispatch`). | `devctl swarm_run`, summary/artifact publishing. | `python3 dev/scripts/devctl.py swarm_run --plan-doc dev/active/autonomous_control_plane.md --mp-scope MP-338 --mode report-only --format md` |

## Release and publish workflows

| Workflow file | What it does | When it runs | Main checks/actions | First local command |
|---|---|---|---|---|
| `release_preflight.yml` | Manual release gate before tagging/publish. | Manual run. | Version parity checks, CodeRabbit gates, CI/runtime/security/docs bundles, ship dry-runs. | `python3 dev/scripts/devctl.py check --profile release` |
| `publish_pypi.yml` | Publishes PyPI package for release tags. | On `release: published`. | Verify gates + secret checks + `devctl ship --pypi`. | `python3 dev/scripts/devctl.py ship --version X.Y.Z --pypi --verify-pypi --yes` |
| `publish_homebrew.yml` | Publishes Homebrew formula update for release tags. | On `release: published` and manual run. | Verify gates + token checks + `devctl ship --homebrew`. | `python3 dev/scripts/devctl.py ship --version X.Y.Z --homebrew --yes` |
| `publish_release_binaries.yml` | Builds and uploads release binaries to GitHub Release. | On `release: published`. | Build/package matrix for Linux + macOS, upload release assets. | `cargo build --release --manifest-path rust/Cargo.toml --bin voiceterm` |
| `release_attestation.yml` | Creates source provenance attestation. | On `release: published` and manual run. | Build source archive, upload artifact, run provenance attestation action. | `python3 dev/scripts/devctl.py ship --version X.Y.Z --verify --tag --notes --github --yes` |

## Failure handling quick steps

1. Open the failing workflow run in GitHub.
2. Read the first failed step and artifact summary.
3. Re-run the matching local command from the table above.
4. Fix root cause and push.
5. If this is repeat manual work, add or update automation under `dev/scripts/devctl.py` and document it.
