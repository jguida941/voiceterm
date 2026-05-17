#!/usr/bin/env python3
"""Backward-compat shim -- use `command_output_consumed.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve a stable command-output consumption guard entrypoint
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/command_output_consumed/command.py

from command_output_consumed.command import main


if __name__ == "__main__":
    raise SystemExit(main())
