# Active Docs Index

This file is the canonical registry for `dev/active/*.md`.
Agents must read this file first before loading active planning docs.

## Registry

| Path | Role | Execution authority | MP scope | When agents read |
|---|---|---|---|---|
| `dev/active/MASTER_PLAN.md` | `tracker` | `canonical` | all active MP execution state | always |
| `dev/active/theme_upgrade.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-099`, `MP-148..MP-151`, `MP-161..MP-167`, `MP-172..MP-182` | when Theme Studio, overlay visual research, or visual-surface redesign is in scope |
| `dev/active/memory_studio.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-230..MP-255` | only when memory/action/context-pack work is in scope |
| `dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md` | `runbook` | `supporting` | multi-agent worktree orchestration | only when running parallel area execution |

## Load Order (Agent Bootstrap)

1. Read this file (`dev/active/INDEX.md`).
2. Read `dev/active/MASTER_PLAN.md`.
3. Read only registry docs required by the task class.
4. Do not treat any non-tracker file as execution state authority.

## Process: Add A New `dev/active/*.md` File

1. Create the new markdown file under `dev/active/`.
2. Add one registry row in this file with path, role, authority, MP scope, and read trigger.
3. If the new file introduces execution state, wire that scope into `dev/active/MASTER_PLAN.md`.
4. Update links in `AGENTS.md`, `DEV_INDEX.md`, and `dev/README.md` when discovery/navigation changes.
5. Run sync/governance checks:
   - `python3 dev/scripts/check_active_plan_sync.py`
   - `python3 dev/scripts/devctl.py docs-check --strict-tooling`
   - `python3 dev/scripts/devctl.py hygiene`
6. Commit docs and governance updates in the same change as the new file.
