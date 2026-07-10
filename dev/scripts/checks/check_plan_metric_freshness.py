#!/usr/bin/env python3
"""Backward-compat shim -- use ``plan_metric_freshness.command``."""
# shim-owner: tooling/governance
# shim-reason: stable guard entrypoint for plan metric freshness checks
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/plan_metric_freshness/command.py

from plan_metric_freshness.command import main


if __name__ == "__main__":
    raise SystemExit(main())
