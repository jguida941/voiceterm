# Developer Index

Start here when working in the repo.
This page points you to the right doc based on your task.
This is the canonical developer index.

## What This Folder Is For

Use `dev/` when you are changing the product, tooling, CI, or release process.
The main starting points are:

- [`dev/active/INDEX.md`](active/INDEX.md) for active-doc routing
- [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) for current execution scope
- [`dev/guides/DEVELOPMENT.md`](guides/DEVELOPMENT.md) for build/test/check commands
- [`dev/guides/ARCHITECTURE.md`](guides/ARCHITECTURE.md) for runtime structure

## Pick Your Path

| I want to... | Go here |
|---|---|
| See what is in scope right now | [`dev/active/INDEX.md`](active/INDEX.md), then [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) |
| Build, test, or release | [`dev/guides/DEVELOPMENT.md`](guides/DEVELOPMENT.md) |
| Understand how the runtime works | [`dev/guides/ARCHITECTURE.md`](guides/ARCHITECTURE.md) |
| Understand the reusable AI governance platform thesis and architecture | [`dev/guides/AI_GOVERNANCE_PLATFORM.md`](guides/AI_GOVERNANCE_PLATFORM.md) and [`dev/active/ai_governance_platform.md`](active/ai_governance_platform.md) |
| Choose Python contract/modeling patterns for platform/runtime tooling | [`dev/guides/PYTHON_ARCHITECTURE.md`](guides/PYTHON_ARCHITECTURE.md) after [`dev/guides/AI_GOVERNANCE_PLATFORM.md`](guides/AI_GOVERNANCE_PLATFORM.md) |
| Understand the current `MP-377` priority lane for startup authority, repo packs, typed plan routing, and runtime/evidence/context closure | [`dev/active/platform_authority_loop.md`](active/platform_authority_loop.md) after [`dev/active/ai_governance_platform.md`](active/ai_governance_platform.md) |
| Edit governed active-plan markdown or active-plan schema enforcement | [`dev/active/PLAN_FORMAT.md`](active/PLAN_FORMAT.md) after [`dev/active/platform_authority_loop.md`](active/platform_authority_loop.md) |
| Understand how the current Codex/Claude collaboration system works | [`dev/guides/AGENT_COLLABORATION_SYSTEM.md`](guides/AGENT_COLLABORATION_SYSTEM.md) |
| Export or benchmark the portable governance stack on other repos | [`dev/guides/PORTABLE_CODE_GOVERNANCE.md`](guides/PORTABLE_CODE_GOVERNANCE.md) and [`dev/active/portable_code_governance.md`](active/portable_code_governance.md) |
| Plan or execute the full reusable AI governance platform extraction | [`dev/active/ai_governance_platform.md`](active/ai_governance_platform.md) and [`dev/guides/AI_GOVERNANCE_PLATFORM.md`](guides/AI_GOVERNANCE_PLATFORM.md) |
| Launch or extend the optional PyQt6 Operator Console | [`../app/operator_console/AGENTS.md`](../app/operator_console/AGENTS.md), [`../app/operator_console/README.md`](../app/operator_console/README.md), and [`dev/active/operator_console.md`](active/operator_console.md) |
| Change tooling, process, or CI | [`AGENTS.md`](../AGENTS.md) and [`dev/scripts/README.md`](scripts/README.md) |

## Recommended Reading Order

1. [`dev/active/INDEX.md`](active/INDEX.md) for active-doc routing.
2. [`dev/active/MASTER_PLAN.md`](active/MASTER_PLAN.md) for current scope.
3. [`dev/guides/DEVELOPMENT.md`](guides/DEVELOPMENT.md) for exact commands.
4. [`dev/guides/ARCHITECTURE.md`](guides/ARCHITECTURE.md) for runtime design.
5. [`dev/scripts/README.md`](scripts/README.md) for `devctl` and check commands.
6. [`dev/guides/AI_GOVERNANCE_PLATFORM.md`](guides/AI_GOVERNANCE_PLATFORM.md) when the task is about the standalone governance product, repo packs, extraction, or frontend/runtime convergence.
7. [`dev/guides/PYTHON_ARCHITECTURE.md`](guides/PYTHON_ARCHITECTURE.md) when the task is about Python runtime/tooling contracts, modeling choices, or composition patterns under `MP-377`.
8. [`dev/guides/PORTABLE_CODE_GOVERNANCE.md`](guides/PORTABLE_CODE_GOVERNANCE.md) when the task is about portable guards, exports, or multi-repo evaluation.
9. [`dev/history/ENGINEERING_EVOLUTION.md`](history/ENGINEERING_EVOLUTION.md) if you need the why behind the current process.

## Active Plans By Area

- Visual/theme work: [`dev/active/theme_upgrade.md`](active/theme_upgrade.md)
- Memory/context-pack work: [`dev/active/memory_studio.md`](active/memory_studio.md)
- Autonomy/mobile control plane: [`dev/active/autonomous_control_plane.md`](active/autonomous_control_plane.md)
- Shared review workflow: [`dev/active/review_channel.md`](active/review_channel.md)
- Continuous Codex/Claude loop: [`dev/active/continuous_swarm.md`](active/continuous_swarm.md)
- Host process cleanup/audit: [`dev/active/host_process_hygiene.md`](active/host_process_hygiene.md)
- Optional operator console: [`dev/active/operator_console.md`](active/operator_console.md)
- Ralph guardrail loop: [`dev/active/ralph_guardrail_control_plane.md`](active/ralph_guardrail_control_plane.md)
- Review probes: [`dev/active/review_probes.md`](active/review_probes.md)
- Portable code governance engine/adoption companion: [`dev/active/portable_code_governance.md`](active/portable_code_governance.md)
- AI governance platform extraction only main active plan for this product scope: [`dev/active/ai_governance_platform.md`](active/ai_governance_platform.md)
- Platform authority loop priority lane under `MP-377`: [`dev/active/platform_authority_loop.md`](active/platform_authority_loop.md)
- Governed active-plan markdown contract: [`dev/active/PLAN_FORMAT.md`](active/PLAN_FORMAT.md)
- Naming/API cleanup: [`dev/active/naming_api_cohesion.md`](active/naming_api_cohesion.md)
- IDE/provider modularization: [`dev/active/ide_provider_modularization.md`](active/ide_provider_modularization.md)
- Pre-release audit follow-up: [`dev/active/pre_release_architecture_audit.md`](active/pre_release_architecture_audit.md)
- Loop-to-chat handoff runbook: [`dev/active/loop_chat_bridge.md`](active/loop_chat_bridge.md)

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
| `app/operator_console/AGENTS.md` | Developers + Agents | Local file-placement and validation rules for the Operator Console subtree |
| `app/operator_console/views/README.md` | Developers + Agents | View package map for `shared`, `workspaces`, `actions`, `workflow`, `layout`, and `collaboration` |
| `app/operator_console/theme/README.md` | Developers + Agents | Theme package map for `runtime`, `editor`, `io`, `config`, and `qss` |
| `app/operator_console/state/README.md` | Developers + Agents | State package map and what no longer belongs in `state/` root |
| `app/operator_console/tests/README.md` | Developers + Agents | Test package map that mirrors the runtime package layout |
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
