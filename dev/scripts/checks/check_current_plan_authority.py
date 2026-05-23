#!/usr/bin/env python3
"""Backward-compat shim -- use `current_plan_authority.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable current-plan authority guard entrypoint
# shim-expiry: 2026-12-31
# shim-target: dev/scripts/checks/current_plan_authority/command.py
if __package__:
    from .current_plan_authority.command import *
else:
    from current_plan_authority.command import *
if __name__ == "__main__": raise SystemExit(main())
