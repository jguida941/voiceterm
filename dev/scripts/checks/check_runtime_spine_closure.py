#!/usr/bin/env python3
"""Backward-compat shim -- use ``runtime_spine_closure.command``."""
# shim-owner: tooling/platform
# shim-reason: stable runtime-spine closure guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/runtime_spine_closure/command.py

from runtime_spine_closure.command import main


if __name__ == "__main__":
    raise SystemExit(main())

