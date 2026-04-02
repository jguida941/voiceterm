#!/usr/bin/env python3
"""Backward-compat shim -- use `duplication_audit.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable duplication-audit guard entrypoint while implementation lives under `duplication_audit/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/duplication_audit/command.py

from duplication_audit.command import main


if __name__ == "__main__":
    raise SystemExit(main())
