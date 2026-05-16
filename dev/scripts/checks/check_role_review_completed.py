#!/usr/bin/env python3
"""Backward-compat shim -- use `role_review_completed.command`."""
# shim-owner: tooling/platform
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/role_review_completed/command.py

from role_review_completed.command import main


if __name__ == "__main__":
    raise SystemExit(main())
