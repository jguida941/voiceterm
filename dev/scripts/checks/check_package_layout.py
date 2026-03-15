#!/usr/bin/env python3
"""Backward-compat shim -- use `package_layout.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable check entrypoint while package-layout internals live under `package_layout/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/package_layout/command.py

from __future__ import annotations

from package_layout.command import main


if __name__ == "__main__":
    raise SystemExit(main())
