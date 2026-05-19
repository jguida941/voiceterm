#!/usr/bin/env python3
"""Backward-compat shim -- use ``bridge_projection_only.command``."""
# shim-owner: tooling/governance
# shim-reason: stable bridge projection-only guard entrypoint
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/bridge_projection_only/command.py

from bridge_projection_only.command import _build_report, main


if __name__ == "__main__":
    raise SystemExit(main())
