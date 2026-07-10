#!/usr/bin/env python3
"""Backward-compat shim -- use `system_picture_freshness.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable SystemPicture freshness guard entrypoint during package extraction
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/system_picture_freshness/command.py

try:
    from system_picture_freshness.command import *
except ModuleNotFoundError:
    from dev.scripts.checks.system_picture_freshness.command import *


if __name__ == "__main__":
    raise SystemExit(main())
