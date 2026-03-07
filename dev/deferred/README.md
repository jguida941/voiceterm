# Deferred Plans

This folder stores plans that are intentionally paused while active priorities are
executed from `dev/active/`.

## Current deferred plans

- `DEV_MODE_PLAN.md` - devtools overlay and offline analytics tool.
- `LOCAL_BACKLOG.md` - local-only reference backlog (`LB-*` IDs); promote
  items to `MASTER_PLAN` as `MP-*` before active execution.

## Rules

- Do not pull deferred items into active implementation without adding a scoped
  item to `dev/active/MASTER_PLAN.md`.
- When a deferred plan is resumed, move it back to `dev/active/` and record the
  decision in `dev/active/MASTER_PLAN.md`.
