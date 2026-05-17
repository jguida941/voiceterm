#!/usr/bin/env python3
"""Backward-compat shim -- use ``dev.scripts.checks.multi_agent_sync``."""
# shim-owner: tooling/review-channel
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/multi_agent_sync/command.py

from multi_agent_sync.api import *
from multi_agent_sync.command import main


if __name__ == "__main__":
    raise SystemExit(main())
