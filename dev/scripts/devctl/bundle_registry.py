"""Backward-compat shim -- use devctl.bundles.registry instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable bundle-registry import while the implementation lives under `devctl.bundles`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/bundles/registry.py

from .bundles.registry import *
