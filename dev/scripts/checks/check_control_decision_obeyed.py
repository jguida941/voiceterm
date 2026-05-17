#!/usr/bin/env python3
"""Backward-compat shim -- use `control_decision_obeyed.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve a stable control-decision obedience guard entrypoint
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/control_decision_obeyed/command.py

from control_decision_obeyed.command import main


if __name__ == "__main__":
    raise SystemExit(main())
