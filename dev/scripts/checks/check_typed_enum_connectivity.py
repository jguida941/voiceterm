#!/usr/bin/env python3
"""Backward-compat shim -- use ``typed_enum_connectivity.command``."""
# shim-owner: tooling/platform
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/typed_enum_connectivity/command.py

from typed_enum_connectivity.command import main


if __name__ == "__main__":
    raise SystemExit(main())
