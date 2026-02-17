# Tooling Control Plane Consolidation (Active Plan)

## Goal

Consolidate maintainer workflows around one canonical control-plane CLI:
`python3 dev/scripts/devctl.py ...`.

Keep current scripts and Make targets for compatibility, but convert them into
thin adapters so AI and humans follow one consistent workflow.

## Scope

- Maintainer workflows in `dev/scripts/`, `dev/scripts/devctl/`, `Makefile`,
  and maintainer macro packs.
- Release/distribution orchestration (tag, GitHub release, PyPI, Homebrew).
- Documentation/governance updates so the canonical workflow is explicit.

## Non-goals

- Replacing end-user install/runtime scripts in `scripts/` (`start.sh`,
  `setup.sh`, `install.sh`, `macros.sh`).
- Deleting legacy scripts immediately (deprecate first, remove later).

## Codebase Audit Baseline (2026-02-17)

### Maintainer entry points (current)

- `Makefile` exposes release paths (`release`, `release-notes`, `homebrew`) and
  many direct task aliases.
- Raw maintainer scripts still exist:
  - `dev/scripts/release.sh`
  - `dev/scripts/generate-release-notes.sh`
  - `dev/scripts/update-homebrew.sh`
  - `dev/scripts/publish-pypi.sh`
- `devctl` currently wraps only parts of release:
  - `release` (tag/push + optional homebrew)
  - `homebrew`
  - `release-notes`
- Macro packs still include release operations.

### Release/distribution flow (current)

- Tagging flow is split:
  - `release.sh` handles branch/clean-tree/version checks + tag push.
  - GitHub release creation remains a manual `gh release create ...`.
- PyPI publish is separate (`publish-pypi.sh`).
- Homebrew update is separate (`update-homebrew.sh`), with interactive prompt
  and tap-repo commit.

### Gaps to address in consolidation

- No single command that performs full release pipeline end-to-end.
- No unified machine-readable step report for release/distribution.
- Partial dry-run support: available in `devctl` wrappers, not uniformly across
  all underlying scripts.
- No enforcement that docs/macros avoid deprecated release commands.
- `devctl docs-check` is currently policy-light: it only validates changelog +
  broad doc coverage and does not yet enforce change-class-specific coverage.
- No dedicated tooling CI lane currently validates `devctl` command behavior and
  maintainer shell-script integrity as one explicit quality gate.

## Target Architecture

1. Canonical maintainer interface: `devctl`.
2. Other entry points are adapters only:
   - `Makefile` delegates to `devctl`.
   - shell release scripts delegate to `devctl` (or internal helper modules).
   - maintainer macro packs call `devctl`, not raw release scripts.
3. Clear domain split:
   - `scripts/` = user operations
   - `dev/scripts/devctl/` = maintainer operations
4. Release orchestration from one command:
   - `devctl ship --version X.Y.Z ...`

## Execution Plan

### Phase 0 - Governance Freeze

- Freeze new standalone maintainer scripts unless they are wrappers over
  `devctl`.
- Define deprecation matrix (legacy command -> canonical `devctl` command).

### Phase 1 - Orchestrator Command

- Add `devctl ship` with explicit step toggles and ordering:
  - `--verify` (`devctl check --profile release` + docs/hygiene as configured)
  - `--tag` (tag/push)
  - `--notes` (release notes generation)
  - `--github` (create GitHub release from notes file)
  - `--pypi` (publish)
  - `--homebrew` (tap update)
  - `--verify-pypi` (JSON endpoint check)
- Add global controls: `--yes`, `--dry-run`, deterministic exit codes.
- Emit machine-readable summary (`--format json|md`, plus output file option).

### Phase 2 - Adapter Conversion

- Convert `release.sh`, `update-homebrew.sh`, `publish-pypi.sh` to thin
  compatibility wrappers around canonical `devctl` flows.
- Keep existing command signatures where practical to avoid breaking habits.
- Update `Makefile` release targets to call `devctl` only.
- Update maintainer macro packs to call canonical `devctl` commands.

### Phase 3 - Enforcement

- Extend governance checks to detect deprecated command references in:
  - `AGENTS.md`
  - `dev/DEVELOPMENT.md`
  - `dev/scripts/README.md`
  - maintainer macro packs
  - `Makefile` help text
- Add CI lane (or extend existing docs/governance lane) to fail on deprecated
  command drift.
- Expand `devctl docs-check` from broad coverage enforcement to policy-aware
  checks (change class -> required doc set + deprecated-command guard).
- Add a dedicated tooling CI lane for `devctl` tests and maintainer shell-script
  validation.

### Phase 4 - Removal Window

- After 1-2 successful release cycles on `devctl ship`, remove obsolete
  wrappers/scripts that no longer add compatibility value.

### Phase 5 - Adjacent Runtime Debt Coordination

- Treat `event_loop.rs` / `voice_control/drain.rs` modularization as adjacent
  architecture debt (tracked in `MASTER_PLAN` MP-143), not part of release
  tooling control-plane scope.
- Coordinate scheduling so tooling and runtime refactors do not overlap in one
  release cut when avoidable.

## Acceptance Gates

1. `devctl ship --version X.Y.Z --verify --tag --notes --github --pypi --homebrew --verify-pypi`
   can run the full release pipeline with deterministic step outcomes.
2. Release artifacts are emitted from one command path:
   - notes markdown path
   - GitHub release URL
   - PyPI verify result
   - Homebrew tap commit hash
3. `Makefile` release-related targets and maintainer macro pack release commands
   delegate to `devctl`.
4. Docs/governance explicitly identify `devctl` as canonical maintainer
   interface.
5. CI guard fails when deprecated release commands reappear in maintained docs
   or macro packs.

## Risk Controls

- Keep legacy script wrappers during migration.
- Add `--dry-run` and step-level logging before enabling broad automation.
- Keep interactive confirmation defaults; require explicit opt-in for
  non-interactive publish.

## Audit Additions (Not in initial proposal, required by current codebase)

- Homebrew path/auth realities:
  - Respect `HOMEBREW_VOICETERM_PATH` and tap repo discovery fallbacks.
  - Preserve explicit failure messages when tap repo or tarball lookup fails.
- PyPI safety:
  - Preserve Cargo/PyPI version parity checks before upload.
  - Keep twine artifact validation gate before upload.
- GitHub release safety:
  - Add `gh auth status` preflight in orchestrator before attempting publish.
  - Include `--fail-on-no-commits` option support for stricter release control.
- Idempotency:
  - Step-aware behavior when tag already exists or a release is already
    published.
- Runtime modularization boundary:
  - Keep control-plane work focused on release/tooling surfaces; do not bundle
    runtime decomposition into the same change set.
