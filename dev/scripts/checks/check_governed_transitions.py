#!/usr/bin/env python3
"""Backward-compat shim -- use `governed_transitions.command`."""
# shim-owner: tooling/governance
# shim-reason: stable dev/scripts/checks/ public guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/governed_transitions/command.py

if __package__: from .governed_transitions.command import build_report, main
else: from governed_transitions.command import build_report, main

if __name__ == "__main__":
    raise SystemExit(main())
