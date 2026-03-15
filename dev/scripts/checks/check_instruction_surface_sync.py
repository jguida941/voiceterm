#!/usr/bin/env python3
"""Backward-compat shim -- use `package_layout.check_instruction_surface_sync`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable instruction-surface sync entrypoint while package-layout internals live under `package_layout/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/package_layout/check_instruction_surface_sync.py

from __future__ import annotations

from package_layout.check_instruction_surface_sync import main


if __name__ == "__main__":
    raise SystemExit(main())
