#!/usr/bin/env python3
"""Backward-compat shim -- use ``daemon_state_parity.command``."""
# shim-owner: tooling/platform
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/daemon_state_parity/command.py

from daemon_state_parity.command import main

if __name__ == "__main__":
    raise SystemExit(main())
