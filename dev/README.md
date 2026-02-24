# Developer Index

Start here when working in the repo.
This page points you to the right doc based on your task.
Root shortcut: [`../DEV_INDEX.md`](../DEV_INDEX.md).

## Pick Your Path

| I want to... | Go here |
|---|---|
| See what is in scope right now | [`dev/active/INDEX.md`](active/INDEX.md), then [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) |
| Build, test, or release | [`dev/DEVELOPMENT.md`](DEVELOPMENT.md) |
| Understand how the runtime works | [`dev/ARCHITECTURE.md`](ARCHITECTURE.md) |
| Change tooling, process, or CI | [`AGENTS.md`](../AGENTS.md) and [`dev/scripts/README.md`](scripts/README.md) |

## Recommended Reading Order

1. [`dev/active/INDEX.md`](active/INDEX.md) -- registry of active planning docs (read this first).
2. [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) -- current scope and what ships next.
3. [`dev/active/theme_upgrade.md`](active/theme_upgrade.md) -- Theme + Overlay Studio spec (`TS-G*`, `MP-148+`).
4. [`dev/active/memory_studio.md`](active/memory_studio.md) -- Memory + Action Studio spec (`MS-G*`, `MP-230+`).
5. [`dev/active/autonomous_control_plane.md`](active/autonomous_control_plane.md) -- autonomous loop + mobile control-plane phased execution spec (`MP-325+`).
6. [`dev/integrations/EXTERNAL_REPOS.md`](integrations/EXTERNAL_REPOS.md) -- linked external repos (`code-link-ide`, `ci-cd-hub`) and governed import workflow.
7. [`dev/audits/README.md`](audits/README.md) -- audit-cycle entry points and evidence conventions.
8. [`dev/audits/AUTOMATION_DEBT_REGISTER.md`](audits/AUTOMATION_DEBT_REGISTER.md) -- repeat-to-automate debt tracking.
9. [`dev/audits/METRICS_SCHEMA.md`](audits/METRICS_SCHEMA.md) -- event schema and KPI/chart definitions for scientific audit runs.
10. [`dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md`](active/MULTI_AGENT_WORKTREE_RUNBOOK.md) -- parallel worktree orchestration for this cycle.
11. [`dev/history/ENGINEERING_EVOLUTION.md`](history/ENGINEERING_EVOLUTION.md) -- why major design/process choices were made.
12. [`dev/history/README.md`](history/README.md) -- index for historical records.
13. [`dev/ARCHITECTURE.md`](ARCHITECTURE.md) -- how the runtime is structured today.
14. [`dev/DEVELOPMENT.md`](DEVELOPMENT.md) -- build, test, and release commands.
15. [`dev/adr/README.md`](adr/README.md) -- architecture decision records.
16. [`dev/CHANGELOG.md`](CHANGELOG.md) -- release history and user-visible changes.

## Three Core Docs

| Doc | What it tells you | Update when... |
|---|---|---|
| `dev/ARCHITECTURE.md` | How the system works right now | Runtime, data flow, lifecycle, or CI/release mechanics change |
| `dev/DEVELOPMENT.md` | Exact commands to build, test, and release | Build workflow, checks, toolchain, or contribution flow change |
| `dev/history/ENGINEERING_EVOLUTION.md` | Why we do it this way | Major inflection points, reversals, or process shifts happen |

User docs start here:

- [`guides/README.md`](../guides/README.md)

## Repository Docs Layout

| Location | Audience | What is there |
|---|---|---|
| `README.md` + `QUICK_START.md` | Users | Onboarding and fast start |
| `guides/` | Users | Usage, install, flags, troubleshooting |
| `scripts/README.md` | Users | Install/start/setup script reference |
| `dev/` | Developers | Architecture, workflow, release process, ADRs |
| `dev/history/` | Developers | History with linked evidence |
| `dev/scripts/README.md` | Developers | Automation and release tooling |
| `dev/archive/` | Developers | Completed plans and audits (read-only) |

## Folder Guide

| Path | What lives here |
|---|---|
| `dev/active/` | Current plans and active execution files |
| `dev/deferred/` | Paused plans (not currently in execution) |
| `dev/archive/` | Completed plans and audits (read-only history) |
| `dev/history/` | Engineering history and timeline |
| `dev/adr/` | Architecture decision records |
| `dev/scripts/` | Developer automation and tooling docs |
| `dev/integrations/` | External repo federation playbooks and import guardrails |
| `dev/audits/` | Audit runbooks, baseline checklists, and automation debt register |

## Fast Workflow Commands

Run these for a quick local check before pushing:

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/devctl.py status --ci --format md
```

### Why these guardrails exist

- **`docs-check`** -- blocks behavior changes that ship without matching docs.
- **`docs-check --strict-tooling`** -- requires a matching `dev/history/ENGINEERING_EVOLUTION.md` entry when `MASTER_PLAN` moves.
- **`hygiene`** -- catches doc/process drift (ADR index, archive naming, scripts list).
- **`check_cli_flags_parity.py`** -- keeps CLI docs in sync with clap flags.
- **`check_screenshot_integrity.py`** -- catches missing image links and stale screenshots.
