#!/usr/bin/env python3
"""Backward-compat shim -- use ``tandem_consistency.command``."""
# shim-owner: MP-358
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/tandem_consistency/command.py
from tandem_consistency.command import main
if __name__ == "__main__":
    raise SystemExit(main())
