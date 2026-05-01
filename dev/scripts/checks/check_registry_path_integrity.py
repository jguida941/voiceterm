#!/usr/bin/env python3
"""Backward-compat shim -- use `registry_path_integrity.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable registry-path integrity guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/registry_path_integrity/command.py

if __package__: from .registry_path_integrity.command import build_report, main
else: from registry_path_integrity.command import build_report, main


if __name__ == "__main__":
    raise SystemExit(main())
