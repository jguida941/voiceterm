#!/usr/bin/env python3
"""Backward-compat shim -- use ``platform_contract_closure.command``."""
# shim-owner: tooling/platform
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/platform_contract_closure/command.py

from platform_contract_closure.command import main


if __name__ == "__main__":
    raise SystemExit(main())
