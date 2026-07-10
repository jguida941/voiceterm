"""Backward-compat shim -- use tests.governance.test_bundle_registry instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable bundle-registry test module path while the implementation lives under `tests/governance`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/tests/governance/test_bundle_registry.py

from dev.scripts.devctl.tests.governance.test_bundle_registry import *
