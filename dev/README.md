# Developer Index

Use this page as the entrypoint for all developer documentation.
Root shortcut pointer: [`../DEV_INDEX.md`](../DEV_INDEX.md).

## Start Here

1. [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) - current execution plan, scope, and release targets.
2. [`dev/active/CODE_QUALITY_EXECUTION_PLAN.md`](active/CODE_QUALITY_EXECUTION_PLAN.md) - active code-quality audit execution detail for the current master plan track.
3. [`dev/history/ENGINEERING_EVOLUTION.md`](history/ENGINEERING_EVOLUTION.md) - historical design/process journey with commit evidence.
4. [`dev/history/README.md`](history/README.md) - index for historical engineering records.
5. [`dev/ARCHITECTURE.md`](ARCHITECTURE.md) - current runtime architecture and operational workflows.
6. [`dev/DEVELOPMENT.md`](DEVELOPMENT.md) - build/test/devctl workflow.
7. [`dev/adr/README.md`](adr/README.md) - ADR index and decision statuses.
8. [`dev/CHANGELOG.md`](CHANGELOG.md) - release history and user-visible deltas.

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
python3 dev/scripts/devctl.py status --ci --format md
```
