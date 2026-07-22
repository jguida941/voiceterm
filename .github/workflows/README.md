# GitHub Workflows

## Runtime quality

| Workflow | Purpose | Local equivalent |
|---|---|---|
| `rust_ci.yml` | Format, Clippy, tests, docs, feature modes, and macOS smoke build | `make ci` |
| `coverage.yml` | Rust coverage report | `cargo llvm-cov` |
| `voice_mode_guard.yml` | Voice macro and send-mode regression tests | `make test-bin` |
| `wake_word_guard.yml` | Wake-word behavior | `scripts/tests/wake_word_guard.sh` |
| `latency_guard.yml` | Synthetic latency regression thresholds | `scripts/tests/measure_latency.sh --ci-guard` |
| `memory_guard.yml` | Runtime memory/thread cleanup | `make test-mem` |
| `parser_fuzz_guard.yml` | ANSI and PTY parser property tests | `make parser-fuzz` |
| `perf_smoke.yml` | Fast performance sanity test | `make test-perf` |

## Repository quality and security

| Workflow | Purpose | Local equivalent |
|---|---|---|
| `docs_lint.yml` | Markdown style and broken local references across every maintained Markdown surface | Run the exact command from `docs_lint.yml` |
| `workflow_lint.yml` | GitHub Actions syntax | `actionlint` |
| `security_guard.yml` | Rust advisory/license checks and CodeQL | `make security` |
| `dependency_review.yml` | Pull-request dependency review | GitHub-only |
| `scorecard.yml` | OpenSSF supply-chain posture | GitHub-only |

## Releases

Publishing begins when a GitHub release is published. The release tag must be
`vX.Y.Z`, and all package metadata must match that version.

| Workflow | Output |
|---|---|
| `release_preflight.yml` | Manual version, CI, PyPI package, and release-note validation |
| `publish_release_binaries.yml` | Linux and macOS binaries plus SHA-256 files |
| `publish_pypi.yml` | PyPI package |
| `publish_homebrew.yml` | Formula update in `jguida941/homebrew-voiceterm` |
| `release_attestation.yml` | Source archive and build provenance |

Useful local commands:

```bash
make release-check V=X.Y.Z
make release-notes V=X.Y.Z
make pypi
make release V=X.Y.Z
```

`make release` creates the GitHub release; the GitHub workflows perform the
platform publications. Required repository secrets and trusted-publishing
configuration must be present before publishing.
