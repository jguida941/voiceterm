#!/usr/bin/env python3
"""Backward-compat shim -- use checks.bundle_registry_dry.command instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable bundle-registry DRY guard entrypoint while the implementation lives under `checks/bundle_registry_dry`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/bundle_registry_dry/command.py

from bundle_registry_dry.command import *


if __name__ == "__main__":
    raise SystemExit(main())
