#!/usr/bin/env python3
"""Backward-compat shim -- use ``systemmap_covers_contract_registry.command``."""
# shim-owner: tooling/platform
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/systemmap_covers_contract_registry/command.py

from systemmap_covers_contract_registry.command import main


if __name__ == "__main__":
    raise SystemExit(main())
