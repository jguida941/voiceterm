# Developer Index

Use this page first when working in the repo.
It tells you where to look next based on what you are trying to do.
Root shortcut pointer: [`../DEV_INDEX.md`](../DEV_INDEX.md).

## Pick a Path

| If you need to... | Read this first |
|---|---|
| Find active scope and execution state | [`dev/active/INDEX.md`](active/INDEX.md), then [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) |
| Build/test/release | [`dev/DEVELOPMENT.md`](DEVELOPMENT.md) |
| Understand runtime architecture | [`dev/ARCHITECTURE.md`](ARCHITECTURE.md) |
| Change tooling/process/CI | [`AGENTS.md`](../AGENTS.md) and [`dev/scripts/README.md`](scripts/README.md) |

## Start Here

1. [`dev/active/INDEX.md`](active/INDEX.md) - list of active planning docs and the order to read them.
2. [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) - what is currently in scope and what ships next.
3. [`dev/active/theme_upgrade.md`](active/theme_upgrade.md) - canonical Theme + Overlay Studio spec (Theme Studio architecture/gates plus consolidated visual research/redesign detail; `TS-G*`, `MP-148+`).
4. [`dev/active/memory_studio.md`](active/memory_studio.md) - Memory + Action Studio spec and test gates (`MS-G*`, `MP-230+`).
5. [`dev/active/devctl_reporting_upgrade.md`](active/devctl_reporting_upgrade.md) - phased `devctl` reporting and CIHub integration roadmap (`MP-306`).
6. [`dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md`](active/MULTI_AGENT_WORKTREE_RUNBOOK.md) - how parallel worktrees are run this cycle.
7. [`dev/history/ENGINEERING_EVOLUTION.md`](history/ENGINEERING_EVOLUTION.md) - why major design/process choices were made.
8. [`dev/history/README.md`](history/README.md) - index for historical records.
9. [`dev/ARCHITECTURE.md`](ARCHITECTURE.md) - how the runtime is put together today.
10. [`dev/DEVELOPMENT.md`](DEVELOPMENT.md) - build/test/release commands and day-to-day workflow.
11. [`dev/adr/README.md`](adr/README.md) - architecture decision records and status.
12. [`dev/CHANGELOG.md`](CHANGELOG.md) - release history and user-visible changes.

## Three Core Docs (Developer Lens)

| Doc | Question it answers | Update trigger |
|---|---|---|
| `dev/ARCHITECTURE.md` | How does the system work right now? | Runtime/data flow, architecture, lifecycle, CI/release mechanics change |
| `dev/DEVELOPMENT.md` | What exact commands should I run to build/test/release? | Build workflow, checks, toolchain, contribution flow change |
| `dev/history/ENGINEERING_EVOLUTION.md` | Why do we do it this way? | Major inflection points, reversals, or process shifts |

User docs entrypoint:

- [`guides/README.md`](../guides/README.md)

## Repository Docs Layout

| Location | Primary audience | Purpose |
|---|---|---|
| `README.md` + `QUICK_START.md` | Users | Top-level onboarding and fast start. |
| `guides/` | Users | Usage, install, flags, troubleshooting. |
| `scripts/README.md` | Users | Install/start/setup script reference. |
| `dev/` | Developers | Architecture, workflow, release process, ADRs. |
| `dev/history/` | Developers | History with linked evidence. |
| `dev/scripts/README.md` | Developers | Automation and release tooling. |
| `dev/archive/` | Developers | Completed plans/audits (do not edit). |

## Folder Guide

| Path | Purpose |
|---|---|
| `dev/active/` | Current plans and active execution files. |
| `dev/deferred/` | Paused plans not currently in execution. |
| `dev/archive/` | Completed plans/audits (history only). |
| `dev/history/` | Engineering history and timeline. |
| `dev/adr/` | Architecture decisions and status. |
| `dev/scripts/` | Developer automation and helper docs. |

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

- `docs-check`: stops behavior changes from shipping without matching docs.
- `docs-check --strict-tooling`: when `dev/active/MASTER_PLAN.md` moves, record the process shift in `dev/history/ENGINEERING_EVOLUTION.md` in the same change.
- `hygiene`: catches doc/process drift (ADR index, archive naming, scripts list).
- `check_cli_flags_parity.py`: keeps CLI docs in sync with clap flags.
- `check_screenshot_integrity.py`: catches missing image links and stale screenshots.
