#!/usr/bin/env python3
"""Backward-compat shim -- use `architecture_boundary.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable platform-layer-boundaries guard entrypoint while implementation lives under `architecture_boundary/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/architecture_boundary/command.py

from __future__ import annotations

from architecture_boundary.command import main


if __name__ == "__main__":
    raise SystemExit(main())
