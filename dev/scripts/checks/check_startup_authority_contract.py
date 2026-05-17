#!/usr/bin/env python3
"""Backward-compat shim -- use ``startup_authority_contract.command``."""
# shim-owner: tooling/platform
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/startup_authority_contract/command.py

from startup_authority_contract.command import main

if __name__ == "__main__":
    raise SystemExit(main())
