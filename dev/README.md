# Developer Index

Start here when working in the repo.
This page points you to the right doc based on your task.
This is the canonical developer index.
Root shortcut: [`../DEV_INDEX.md`](../DEV_INDEX.md).

## System Frame

VoiceTerm is evolving into a local-first agent operating system for
terminal-native AI work.

- [`dev/active/memory_studio.md`](active/memory_studio.md) owns durable recall,
  context packs, and survival-index recovery.
- [`dev/active/autonomous_control_plane.md`](active/autonomous_control_plane.md)
  owns operator surfaces, governance, and the umbrella `controller_state`
  contract.
- [`dev/active/review_channel.md`](active/review_channel.md) owns structured
  agent-review coordination and shared-screen visibility.
- [`dev/active/continuous_swarm.md`](active/continuous_swarm.md) owns the
  local-first continuous Codex-reviewer / Claude-coder loop hardening path:
  next-task continuation, peer-liveness guards, context rotation, and the
  phase-gated later template-extraction proof path.
- [`dev/active/operator_console.md`](active/operator_console.md) owns the
  optional VoiceTerm Operator Console: a thin PyQt6 shared-screen wrapper over
  the existing review-channel and launcher flow.

These lanes must share one auditable artifact contract. Hidden side channels or
plan-local shadow state are out of bounds.

## Pick Your Path

| I want to... | Go here |
|---|---|
| See what is in scope right now | [`dev/active/INDEX.md`](active/INDEX.md), then [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) |
| Build, test, or release | [`dev/guides/DEVELOPMENT.md`](guides/DEVELOPMENT.md) |
| Understand how the runtime works | [`dev/guides/ARCHITECTURE.md`](guides/ARCHITECTURE.md) |
| Understand how the current Codex/Claude collaboration system works | [`dev/guides/AGENT_COLLABORATION_SYSTEM.md`](guides/AGENT_COLLABORATION_SYSTEM.md) |
| Launch or extend the optional PyQt6 Operator Console | [`../app/operator_console/README.md`](../app/operator_console/README.md) and [`dev/active/operator_console.md`](active/operator_console.md) |
| Change tooling, process, or CI | [`AGENTS.md`](../AGENTS.md) and [`dev/scripts/README.md`](scripts/README.md) |

## Recommended Reading Order

1. [`dev/active/INDEX.md`](active/INDEX.md) -- list of active planning docs (read this first).
2. [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) -- current scope and what ships next.
3. [`dev/active/theme_upgrade.md`](active/theme_upgrade.md) -- Theme and overlay design plan.
4. [`dev/active/memory_studio.md`](active/memory_studio.md) -- Memory and action-system plan.
5. [`dev/active/autonomous_control_plane.md`](active/autonomous_control_plane.md) -- autonomy loop and mobile control-plane plan.
6. [`dev/active/review_channel.md`](active/review_channel.md) -- shared review-channel and dual-agent shared-screen execution plan for `MP-355`.
7. [`dev/active/continuous_swarm.md`](active/continuous_swarm.md) -- local-first continuous Codex-reviewer / Claude-coder loop hardening plan for `MP-358`.
8. [`dev/active/operator_console.md`](active/operator_console.md) -- bounded optional VoiceTerm Operator Console plan for `MP-359`.
9. [`dev/active/host_process_hygiene.md`](active/host_process_hygiene.md) -- host-side process cleanup and Activity Monitor automation plan for `MP-356`.
10. [`dev/guides/AGENT_COLLABORATION_SYSTEM.md`](guides/AGENT_COLLABORATION_SYSTEM.md) -- plain-language map of the current Codex/Claude collaboration system, bridge flow, execution modes, and report artifacts.
11. [`dev/active/loop_chat_bridge.md`](active/loop_chat_bridge.md) -- how loop output is handed to chat suggestions.
12. [`dev/active/naming_api_cohesion.md`](active/naming_api_cohesion.md) -- naming/API cohesion execution plan for `MP-267`.
13. [`dev/active/ide_provider_modularization.md`](active/ide_provider_modularization.md) -- host/provider adapter modularization and compatibility-hardening plan for `MP-346`.
14. [`dev/active/pre_release_architecture_audit.md`](active/pre_release_architecture_audit.md) -- canonical pre-release architecture/tooling findings + execution plan for `MP-347` and `MP-349`.
15. [`dev/guides/MCP_DEVCTL_ALIGNMENT.md`](guides/MCP_DEVCTL_ALIGNMENT.md) -- durable architecture/rules for MCP as an optional read-only adapter.
16. [`dev/integrations/EXTERNAL_REPOS.md`](integrations/EXTERNAL_REPOS.md) -- external repo links and import rules.
17. [`dev/audits/README.md`](audits/README.md) -- where audit runs and evidence rules live.
18. [`dev/audits/AUTOMATION_DEBT_REGISTER.md`](audits/AUTOMATION_DEBT_REGISTER.md) -- repeated manual work we still need to automate.
19. [`dev/audits/METRICS_SCHEMA.md`](audits/METRICS_SCHEMA.md) -- audit metrics and chart definitions.
20. [`dev/active/review_channel.md`](active/review_channel.md) -- also carries the merged markdown-swarm lane map and signoff template for the current parallel Codex/Claude cycle.
21. [`dev/history/ENGINEERING_EVOLUTION.md`](history/ENGINEERING_EVOLUTION.md) -- why major design/process choices were made.
22. [`dev/history/README.md`](history/README.md) -- index for historical records.
23. [`dev/archive/2026-03-07-rust-workspace-layout-migration.md`](archive/2026-03-07-rust-workspace-layout-migration.md) -- closed record for the completed Rust workspace path/layout migration.
24. [`dev/guides/ARCHITECTURE.md`](guides/ARCHITECTURE.md) -- how the runtime is structured today.
25. [`dev/guides/DEVELOPMENT.md`](guides/DEVELOPMENT.md) -- build, test, and release commands.
26. [`dev/adr/README.md`](adr/README.md) -- architecture decision records.
27. [`dev/CHANGELOG.md`](CHANGELOG.md) -- release history and user-visible changes.

## Three Core Docs

| Doc | What it tells you | Update when... |
|---|---|---|
| `dev/guides/ARCHITECTURE.md` | How the system works right now | Runtime, data flow, lifecycle, or CI/release mechanics change |
| `dev/guides/DEVELOPMENT.md` | Exact commands to build, test, and release | Build workflow, checks, toolchain, or contribution flow change |
| `dev/history/ENGINEERING_EVOLUTION.md` | Why we do it this way | Major inflection points, reversals, or process shifts happen |

User docs start here:

- [`guides/README.md`](../guides/README.md)

## Repository Docs Layout

| Location | Audience | What is there |
|---|---|---|
| `README.md` + `QUICK_START.md` | Users | Onboarding and fast start |
| `guides/` | Users | Usage, install, flags, troubleshooting |
| `scripts/README.md` | Users | Install/start/setup script reference |
| `app/operator_console/README.md` | Users + Developers | Optional PyQt6 Operator Console launcher, themes, and live-swarm monitor flow |
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
| `dev/integrations/` | External repo links and import rules |
| `dev/audits/` | Audit runbooks, baseline checklists, and automation debt register |

## Fast Workflow Commands

Run these for a quick local check before pushing:

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/devctl.py process-cleanup --verify --format md
python3 dev/scripts/devctl.py process-audit --strict --format md
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/devctl.py status --ci --format md
```

### Why these checks exist

- **`docs-check`** -- blocks behavior changes that ship without matching docs.
- **`docs-check --strict-tooling`** -- requires a matching `dev/history/ENGINEERING_EVOLUTION.md` entry when `MASTER_PLAN` moves.
- **`hygiene`** -- catches doc/process drift (ADR index, archive naming, script list).
- **`process-cleanup`** -- safely kills orphaned/stale repo-related host process trees and then verifies the host table again.
- **`process-audit`** -- read-only check of the real host process table for repo leftovers that would show up in Activity Monitor, including descendant PTY children and orphaned repo-tooling wrappers.
- **`check_cli_flags_parity.py`** -- keeps CLI docs in sync with clap flags.
- **`check_screenshot_integrity.py`** -- catches missing image links and stale screenshots.
