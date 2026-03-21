# Active Plan Helpers

Internal support package for `check_active_plan_sync.py`.

- `contract.py`: execution-plan marker/metadata/section validation shared with
  tests.
- `snapshot.py`: git/Cargo plus `MASTER_PLAN` snapshot helpers used by the
  active-plan sync guard.
- `sync_report.py`: registry/discovery/spec-range report helpers used by the
  active-plan sync guard.

Layout rule:
- Keep `check_active_plan_sync.py` at the `checks/` root as the runnable
  entrypoint.
- Keep active-plan validation internals here so the `checks/` root stays
  focused on actual runnable guard/probe scripts.
