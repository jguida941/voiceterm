#!/usr/bin/env python3
"""Backward-compat shim -- use ``governance_closure.command``."""
# shim-owner: tooling/platform
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/governance_closure/command.py

from governance_closure.command import main

if __name__ == "__main__":
    raise SystemExit(main())
