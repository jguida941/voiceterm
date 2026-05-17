#!/usr/bin/env python3
"""Backward-compat shim -- use `ground_truth_probe_gate.command`."""
# shim-owner: tooling/governance
# shim-reason: stable dev/scripts/checks/ public guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/ground_truth_probe_gate/command.py

from ground_truth_probe_gate.command import main

if __name__ == "__main__":
    raise SystemExit(main())
