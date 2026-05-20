#!/usr/bin/env python3
"""Backward-compat shim -- use `substrate_commits_have_applied_plan_row.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable substrate-plan-row guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/substrate_commits_have_applied_plan_row/command.py
if __package__:
    from .substrate_commits_have_applied_plan_row.command import *
else:
    from substrate_commits_have_applied_plan_row.command import *
if __name__ == "__main__": raise SystemExit(main())
