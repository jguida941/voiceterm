#!/usr/bin/env python3
"""Backward-compat shim -- use ``contract_connectivity.command``."""
# shim-owner: tooling/platform
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/contract_connectivity/command.py

from contract_connectivity.command import main


if __name__ == "__main__":
    raise SystemExit(main())
