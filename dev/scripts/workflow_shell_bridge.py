#!/usr/bin/env python3
"""Backward-compat shim -- use `workflow_bridge.shell`."""
# shim-owner: tooling/workflow
# shim-reason: preserve the stable script entrypoint while workflow_shell_bridge lives under `workflow_bridge/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/workflow_bridge/shell.py

from workflow_bridge.shell import main

if __name__ == "__main__":
    raise SystemExit(main())
