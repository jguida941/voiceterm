# Federated Internal Repositories

**Status**: active  |  **Last updated**: 2026-02-24 | **Owner:** tooling/control-plane

## Purpose

`codex-voice` tracks two of your other repos as pinned federation sources so we
can reuse proven components without copy-paste drift.

## Linked Repositories

| Path | Repository | Primary reuse surfaces |
|---|---|---|
| `integrations/code-link-ide` | `https://github.com/jguida941/code-link-ide.git` | iPhone control patterns, Rust agent control API patterns, Xcode CLI harness patterns |
| `integrations/ci-cd-hub` | `https://github.com/jguida941/ci-cd-hub.git` | CI/CD orchestration patterns, workflow controls, reporting surfaces |

## Operating Model

1. Treat `integrations/*` as read-only federated source inputs.
2. Reuse by selective import into first-party paths (for example `dev/scripts/`,
   `dev/scripts/devctl/`, `.github/workflows/`, `src/`), never by hard runtime
   dependency on submodule internals.
3. Every import must be anchored to an active plan item in
   `dev/active/MASTER_PLAN.md` and reflected in the relevant execution spec.
4. Capture upstream source SHA(s) in handoff/audit notes whenever importing.

## Ralph/Wiggum Loop Position

The Ralph/Wiggum loop in this repo is a custom `codex-voice` implementation
(`devctl triage-loop` and `devctl mutation-loop`) with its own policy and
workflow wiring. Your other repos are reference sources for patterns and
targeted imports, not direct runtime executors for this loop.

## Sync Commands

```bash
# Initialize/update pinned submodule SHAs (devctl)
python3 dev/scripts/devctl.py integrations-sync --format md

# Move both integrations to latest remote tracked commits (devctl)
python3 dev/scripts/devctl.py integrations-sync --remote --format md

# Print status only (devctl)
python3 dev/scripts/devctl.py integrations-sync --status-only --format md

# Legacy shell helper (same behavior)
bash dev/scripts/sync_external_integrations.sh --status-only
```

## Selective Import Commands

```bash
# Inspect allowlisted source/profile mappings
python3 dev/scripts/devctl.py integrations-import --list-profiles --format md

# Preview import (no writes)
python3 dev/scripts/devctl.py integrations-import --source code-link-ide --profile iphone-core --format md

# Apply import (writes allowlisted paths only, audit logged)
python3 dev/scripts/devctl.py integrations-import --source ci-cd-hub --profile workflow-templates --apply --yes --format md
```

## Import Checklist

1. Link MP scope before code changes.
2. Identify exact upstream file(s) and commit SHA.
3. Import only required logic into first-party paths.
4. Add/adjust tests in this repo.
5. Update docs (`dev/scripts/README.md`, `dev/DEVELOPMENT.md`, active plan).
6. Run tooling bundle checks before merge.

## Guardrails

1. No direct CI execution from `integrations/*` paths.
2. No destructive sync operations in helper scripts.
3. Preserve independent releaseability of `codex-voice`.
4. Keep federated repo links pinned and auditable (`git submodule status`).
