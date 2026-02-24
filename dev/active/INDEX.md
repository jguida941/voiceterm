# Active Docs Index

This file is the canonical registry for `dev/active/*.md`.
Agents must read this file first before loading active planning docs.

## Registry

| Path | Role | Execution authority | MP scope | When agents read |
|---|---|---|---|---|
| `dev/active/MASTER_PLAN.md` | `tracker` | `canonical` | all active MP execution state | always |
| `dev/active/theme_upgrade.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-099`, `MP-148..MP-151`, `MP-161..MP-167`, `MP-172..MP-182` | when Theme Studio, overlay visual research, or visual-surface redesign is in scope |
| `dev/active/memory_studio.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-230..MP-255` | only when memory/action/context-pack work is in scope |
| `dev/active/devctl_reporting_upgrade.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-306` | when improving `devctl` reporting, dashboard outputs, CIHub integration, or triage utility workflows |
| `dev/active/autonomous_control_plane.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-325..MP-337` | when implementing autonomous loop hardening, mutation remediation loop orchestration, mobile-control-plane surfaces, or autonomy policy gates |
| `dev/active/loop_chat_bridge.md` | `runbook` | `supporting` | `MP-338` | when coordinating loop artifact-to-chat suggestion flow, operator handoff updates, or dry-run/live-run loop validation evidence |
| `dev/active/rust_workspace_layout_migration.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-339` | when migrating the Rust workspace path/layout or updating repository path contracts from `src/` to `rust/` |
| `dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md` | `runbook` | `supporting` | multi-agent worktree orchestration | only when running parallel area execution |
| `dev/active/RUST_AUDIT_FINDINGS.md` | `reference` | `reference-only` | guard-driven Rust remediation scaffold/findings notes (`devctl audit-scaffold`; supporting context, not execution authority) | when AI guard checks fail, when running full-codebase Rust audits, or when updating remediation findings artifacts |
| `dev/active/phase2.md` | `reference` | `reference-only` | phase-2 companion-platform research context (not active MP execution state) | only when evaluating long-range terminal companion planning |

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
   - `python3 dev/scripts/checks/check_active_plan_sync.py`
   - `python3 dev/scripts/devctl.py docs-check --strict-tooling`
   - `python3 dev/scripts/devctl.py hygiene`
6. Commit docs and governance updates in the same change as the new file.
