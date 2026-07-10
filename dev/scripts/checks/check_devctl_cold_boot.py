#!/usr/bin/env python3
"""Backward-compat shim -- use ``devctl_cold_boot.command``."""
# shim-owner: tooling/devctl
# shim-reason: preserve stable cold-boot guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/devctl_cold_boot/command.py

from devctl_cold_boot.command import main


if __name__ == "__main__":
    raise SystemExit(main())
