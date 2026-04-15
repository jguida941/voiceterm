#!/usr/bin/env python3
"""Backward-compat shim -- use `review_snapshot_freshness.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable ReviewSnapshot freshness guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_snapshot_freshness/command.py

from review_snapshot_freshness.command import *


if __name__ == "__main__":
    raise SystemExit(main())
