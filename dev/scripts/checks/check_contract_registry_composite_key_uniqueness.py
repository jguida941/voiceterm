#!/usr/bin/env python3
"""Backward-compat shim -- use `contract_registry_composite_key_uniqueness.command`."""
# shim-owner: tooling/platform
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/contract_registry_composite_key_uniqueness/command.py

from contract_registry_composite_key_uniqueness.command import *  # noqa: F401,F403


if __name__ == "__main__":
    raise SystemExit(main())  # noqa: F405
