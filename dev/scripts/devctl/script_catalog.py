"""Backward-compat shim -- use devctl.governance.script_catalog_registry instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable script-catalog import while the implementation lives under `devctl.governance`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/governance/script_catalog_registry.py

from .governance.script_catalog_registry import *
