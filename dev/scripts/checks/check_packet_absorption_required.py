#!/usr/bin/env python3
"""Backward-compat shim -- use `packet_absorption_required.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve a stable packet-absorption guard entrypoint
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/packet_absorption_required/command.py

from packet_absorption_required.command import main


if __name__ == "__main__":
    raise SystemExit(main())
