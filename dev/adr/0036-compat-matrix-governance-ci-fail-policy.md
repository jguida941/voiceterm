# ADR 0036: Compatibility Matrix Governance and CI Fail Policy

Status: Accepted
Date: 2026-03-05

## Context

Before MP-346 Phase 4, host/provider compatibility expectations were mostly
implicit. That allowed runtime/provider drift and unclear support claims across
docs, checks, and release gates.

MP-346 added a machine-readable compatibility source and two enforcement gates:

- `check_compat_matrix.py` for schema/policy validity.
- `compat_matrix_smoke.py` for runtime-to-matrix alignment.

Manual matrix attestations are also tracked in MP-346 checkpoints and required
for phase transitions that affect host/provider behavior.

## Decision

Adopt the following governance and fail policy:

- `dev/config/compat/ide_provider_matrix.yaml` is the single source of truth
  for host/provider support state and provider IPC mode classification.
- `python3 dev/scripts/checks/check_compat_matrix.py` is a blocking CI gate.
  It must fail on missing required hosts/providers, missing/duplicate cells,
  invalid compat states, invalid provider modes, or provider-mode policy
  violations.
- `python3 dev/scripts/checks/compat_matrix_smoke.py` is a blocking CI gate.
  It must fail when runtime enums/backends are not represented in the matrix,
  when runtime host/provider cells are missing, or when runtime-visible
  non-IPC providers are mislabeled.
- `python3 dev/scripts/devctl.py compat-matrix` remains the local/operator
  wrapper for validation plus smoke checks.
- Manual matrix checkpoint policy is mandatory for MP-346:
  - rerun manual matrix when host/provider behavior changes, or
  - explicitly cite the latest accepted matrix attestation when behavior is
    contract-equivalent and a rerun is deferred.
  - before Phase-3 closure, record full `7/7` manual matrix coverage (or an
    explicit approved waiver packet).

## Consequences

**Positive:**

- Matrix drift becomes a deterministic CI failure, not a review-time guess.
- Runtime enum/backend expansion cannot silently bypass compatibility docs.
- Manual attestation policy closes the gap between static checks and live
  host/provider behavior.

**Negative:**

- Adding hosts/providers now requires matrix + gate updates in the same change.
- Checkpoint hygiene must be maintained to avoid stale manual evidence.

## Alternatives Considered

- **Docs-only compatibility table without machine checks**: rejected because it
  does not enforce completeness or runtime sync.
- **CI-only static checks with no manual gate**: rejected because terminal host
  behavior still needs targeted operator validation for release confidence.

## Links

- `dev/config/compat/ide_provider_matrix.yaml`
- `dev/scripts/checks/check_compat_matrix.py`
- `dev/scripts/checks/compat_matrix_smoke.py`
- `dev/scripts/devctl/commands/compat_matrix.py`
- `dev/active/ide_provider_modularization.md` (`MP-346`, Phase 3/4 policy)
