# Federated Internal Repositories

**Status**: active  |  **Last updated**: 2026-02-26 | **Owner:** tooling/control-plane

## Purpose

`codex-voice` tracks two of your other repos as pinned federation sources so we
can reuse proven components without copy-paste drift.

Git submodules always materialize the full upstream repository at a pinned SHA.
Seeing full trees under `integrations/*` is expected; active runtime behavior
still comes from first-party code in this repo after selective import.

## Linked Repositories

| Path | Repository | Primary reuse surfaces |
|---|---|---|
| `integrations/code-link-ide` | `https://github.com/jguida941/code-link-ide.git` | iPhone control patterns, Rust agent control API patterns, Xcode CLI harness patterns |
| `integrations/ci-cd-hub` | `https://github.com/jguida941/ci-cd-hub.git` | CI/CD orchestration patterns, workflow controls, reporting surfaces |

## 2026-02-26 Fit-Gap Audit (Targeted Reuse)

Mapped against active scopes `MP-297`, `MP-298`, `MP-330`, `MP-331`,
`MP-332`, and `MP-340`.

| Source repo | Candidate components | Why this helps `codex-voice` | MP scope | Decision |
|---|---|---|---|---|
| `code-link-ide` | `agent/src/commands/path.rs` | Strong canonical-path + allowlist guard patterns for remote-action safety boundaries | `MP-332`, `MP-340` | `import pattern now` |
| `code-link-ide` | `agent/src/schema.rs`, `agent/schemas/*` | Deterministic schema validation model for controller-state/action payload contracts | `MP-330`, `MP-340` | `import pattern now` |
| `code-link-ide` | `agent/src/audit.rs` | Hash-chain audit log + retention/compression model for tamper-evident control actions | `MP-332`, `MP-340` | `import pattern now` |
| `code-link-ide` | `agent/src/ws/routing.rs`, `agent/src/commands/types.rs` | Typed envelope + error-code surface design for future Rust `voiceterm-control` service | `MP-330`, `MP-331` | `implement later` |
| `ci-cd-hub` | `cihub/services/report_validator/{schema,content,artifact}.py` | Stronger artifact/schema consistency checks when ingesting CIHub triage outputs | `MP-297`, `MP-298` | `import pattern now` |
| `ci-cd-hub` | `cihub/services/triage/{types,evidence,detection}.py` | Better failure typing (`required_not_run`, evidence-based status) and regression signals | `MP-297`, `MP-298`, `MP-338` | `import pattern now` |
| `ci-cd-hub` | `cihub/services/registry/{diff,sync}.py` | Deterministic diff planning patterns useful for improving federation sync/import previews | `MP-298`, `MP-334` | `implement later` |
| `ci-cd-hub` | Full workflow/template trees | Too broad for immediate value in this repo; high drift/coupling risk | n/a | `do not bulk import` |

## License Gate (Before Code Copy)

1. `codex-voice` is MIT (`LICENSE` at repo root).
2. `integrations/ci-cd-hub` is Elastic License 2.0; treat as reference-only
   unless explicit relicensing/permission is confirmed for copied code.
3. `integrations/code-link-ide` does not expose a top-level license file at the
   pinned SHA; do not copy verbatim code until license terms are explicit.
4. Safe path today: reimplement patterns in first-party code, then validate
   behavior with local tests.

## Immediate Integration Sequence

1. Use narrow import profiles only (no whole-tree imports).
2. Import reference slices into `dev/integrations/imports/` for review.
3. Reimplement selected behavior in first-party `devctl`/Rust code with tests.
4. Keep submodules pinned as auditable upstream references.

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

# Preview narrow control-plane import (no writes)
python3 dev/scripts/devctl.py integrations-import --source code-link-ide --profile control-plane-guardrails-core --format md

# Apply narrow triage-evidence reference import (writes allowlisted paths only, audit logged)
python3 dev/scripts/devctl.py integrations-import --source ci-cd-hub --profile triage-evidence-core --apply --yes --format md
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
