#!/usr/bin/env python3
"""Backward-compat shim -- use `guard_enforcement_inventory.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable guard-enforcement inventory entrypoint
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/guard_enforcement_inventory/command.py

from guard_enforcement_inventory.command import main


if __name__ == "__main__":
    raise SystemExit(main())
