#!/usr/bin/env python3
"""Backward-compat shim -- use `runtime_bridge_projection_separation.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable check entrypoint while implementation lives under a check package
# shim-expiry: 2026-11-11
# shim-target: dev/scripts/checks/runtime_bridge_projection_separation/command.py

from runtime_bridge_projection_separation.command import BridgeSeparationGuard, main


if __name__ == "__main__":
    raise SystemExit(main())
