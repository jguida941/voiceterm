#!/usr/bin/env python3
"""Backward-compat shim -- use `package_layout.probe_compatibility_shims`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable probe entrypoint while shim-governance internals live under `package_layout/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/package_layout/probe_compatibility_shims.py

from __future__ import annotations

from package_layout.probe_compatibility_shims import main


if __name__ == "__main__":
    raise SystemExit(main())
