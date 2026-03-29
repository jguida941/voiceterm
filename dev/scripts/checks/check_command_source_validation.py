#!/usr/bin/env python3
"""Backward-compat shim -- use `package_layout.check_command_source_validation`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable command-source validation entrypoint while package-layout internals live under `package_layout/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/package_layout/check_command_source_validation.py

from __future__ import annotations

from package_layout.check_command_source_validation import main


if __name__ == "__main__":
    raise SystemExit(main())
