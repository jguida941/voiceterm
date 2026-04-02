#!/usr/bin/env python3
"""Backward-compat shim -- use `bundle_workflow_parity.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable bundle-workflow parity guard entrypoint while implementation lives under `bundle_workflow_parity/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/bundle_workflow_parity/command.py

from bundle_workflow_parity.command import main


if __name__ == "__main__":
    raise SystemExit(main())
