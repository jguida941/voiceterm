# GitHub Automation Guide

VoiceTerm keeps CI and publishing automation under `.github/workflows/`.
The repository-level `Makefile` provides the corresponding local commands.

## Local verification

```bash
make check
make test
make integration
make prepush
```

For a release version:

```bash
make release-check V=X.Y.Z
make release-notes V=X.Y.Z
```

## CI groups

- `rust_ci.yml`, `coverage.yml`, `voice_mode_guard.yml`,
  `wake_word_guard.yml`, `latency_guard.yml`, `memory_guard.yml`,
  `parser_fuzz_guard.yml`, and `perf_smoke.yml` validate the runtime.
- `docs_lint.yml` and `workflow_lint.yml` validate documentation and workflow
  syntax.
- `security_guard.yml`, `dependency_review.yml`, and `scorecard.yml` cover
  dependency and supply-chain checks.
- `release_preflight.yml` validates a candidate version before publication.
- `publish_release_binaries.yml`, `publish_pypi.yml`,
  `publish_homebrew.yml`, and `release_attestation.yml` run from a published
  GitHub release.

See [the workflow reference](workflows/README.md) for triggers and outputs.
