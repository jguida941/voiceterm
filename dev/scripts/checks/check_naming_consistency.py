#!/usr/bin/env python3
"""Backward-compat shim -- use `naming_consistency.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable naming-consistency guard entrypoint while implementation lives under `naming_consistency/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/naming_consistency/command.py

from naming_consistency.command import main


if __name__ == "__main__":
    raise SystemExit(main())
