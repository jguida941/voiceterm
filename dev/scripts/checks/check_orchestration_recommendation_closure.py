#!/usr/bin/env python3
"""Backward-compat shim -- use `orchestration_recommendation_closure.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable orchestration recommendation-closure guard entrypoint
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/orchestration_recommendation_closure/command.py

from orchestration_recommendation_closure.command import main


if __name__ == "__main__":
    raise SystemExit(main())
