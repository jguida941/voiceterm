#!/usr/bin/env python3
"""Backward-compat shim -- use `memory_authority.command`."""
# shim-owner: tooling/governance
# shim-reason: stable dev/scripts/checks/ public guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/memory_authority/command.py

from memory_authority.command import main


if __name__ == "__main__":
    raise SystemExit(main())
