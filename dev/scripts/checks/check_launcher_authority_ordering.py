#!/usr/bin/env python3
"""Backward-compat shim -- use ``launcher_authority_ordering.command``."""
# shim-owner: tooling/review-channel
# shim-reason: preserve the stable guard entrypoint while implementation lives under `launcher_authority_ordering/`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/launcher_authority_ordering/command.py

from launcher_authority_ordering.command import main


if __name__ == "__main__":
    raise SystemExit(main())
