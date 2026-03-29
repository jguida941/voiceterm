#!/usr/bin/env python3
"""Backward-compat shim -- use ``guide_contract_sync.command``."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable durable-guide contract guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/guide_contract_sync/command.py

from guide_contract_sync.command import build_report, main, render_md


if __name__ == "__main__":
    raise SystemExit(main())
