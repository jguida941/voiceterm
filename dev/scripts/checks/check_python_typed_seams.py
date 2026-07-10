#!/usr/bin/env python3
"""Backward-compat shim -- use `python_typed_seams.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve a stable public guard entrypoint while the implementation lives under `dev/scripts/checks/python_typed_seams/`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/python_typed_seams/command.py

from python_typed_seams.command import main


if __name__ == "__main__":
    raise SystemExit(main())
