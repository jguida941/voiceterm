# Developer Index

Use this page as the entrypoint for all developer documentation.
Root shortcut pointer: [`../DEV_INDEX.md`](../DEV_INDEX.md).

## Start Here

1. [`dev/active/INDEX.md`](active/INDEX.md) - registry for all active planning docs and read order.
2. [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) - current execution plan, scope, and release targets.
3. [`dev/active/theme_upgrade.md`](active/theme_upgrade.md) - Theme Studio architecture/spec and `TS-G*` gate checklist used by `MP-148+`.
4. [`dev/active/memory_studio.md`](active/memory_studio.md) - Memory + Action Studio architecture/spec and `MS-G*` gate checklist used by `MP-230+`.
5. [`dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md`](active/MULTI_AGENT_WORKTREE_RUNBOOK.md) - current parallel area orchestration and reviewer gate protocol.
6. [`dev/history/ENGINEERING_EVOLUTION.md`](history/ENGINEERING_EVOLUTION.md) - historical design/process journey with commit evidence.
7. [`dev/history/README.md`](history/README.md) - index for historical engineering records.
8. [`dev/ARCHITECTURE.md`](ARCHITECTURE.md) - current runtime architecture and operational workflows.
9. [`dev/DEVELOPMENT.md`](DEVELOPMENT.md) - build/test/devctl workflow.
10. [`dev/adr/README.md`](adr/README.md) - ADR index and decision statuses.
11. [`dev/CHANGELOG.md`](CHANGELOG.md) - release history and user-visible deltas.

## Three Core Docs (Developer Lens)

| Doc | Question it answers | Update trigger |
|---|---|---|
| `dev/ARCHITECTURE.md` | What does the system look like now? | Runtime/data flow, architecture, lifecycle, CI/release mechanics change |
| `dev/DEVELOPMENT.md` | How do I build, test, and ship safely? | Build workflow, checks, toolchain, contribution flow change |
| `dev/history/ENGINEERING_EVOLUTION.md` | Why did the design/process become this way? | Major inflection points, reversals, or governance shifts |

User docs entrypoint:

- [`guides/README.md`](../guides/README.md)

## Repository Docs Layout

| Location | Primary audience | Purpose |
|---|---|---|
| `README.md` + `QUICK_START.md` | Users | Top-level onboarding and fast start path. |
| `guides/` | Users | Canonical usage/install/flags/troubleshooting docs. |
| `scripts/README.md` | Users | Install/start/setup script reference. |
| `dev/` | Developers | Architecture, workflow, governance, release, ADRs. |
| `dev/history/` | Developers | Evidence-linked evolution and historical context. |
| `dev/scripts/README.md` | Developers | Automation and release tooling reference. |
| `dev/archive/` | Developers | Historical completed plans/audits (immutable). |

## Folder Guide

| Path | Purpose |
|---|---|
| `dev/active/` | Active strategy and execution files (authoritative work-in-progress). |
| `dev/deferred/` | Paused plans not currently in execution. |
| `dev/archive/` | Historical completed plans/audits (immutable record). |
| `dev/history/` | Narrative history and engineering evolution timeline. |
| `dev/adr/` | Architecture decisions with status lifecycle. |
| `dev/scripts/` | Developer automation, tooling docs, and workflow helpers. |

## Fast Workflow Commands

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/check_cli_flags_parity.py
python3 dev/scripts/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/devctl.py status --ci --format md
```

Why these guardrails exist:

- `docs-check`: prevents user-facing/tooling behavior changes from shipping without aligned docs.
- `hygiene`: prevents process/governance drift (ADR index, archive naming, scripts inventory).
- `check_cli_flags_parity.py`: prevents clap flag/schema drift from `guides/CLI_FLAGS.md`.
- `check_screenshot_integrity.py`: prevents broken markdown image references and surfaces stale UI captures for refresh planning.
