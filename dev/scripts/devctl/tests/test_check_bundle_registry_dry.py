"""Backward-compat shim -- use tests.checks.test_check_bundle_registry_dry instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable bundle-registry-dry test module path while the implementation lives under `tests/checks`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/tests/checks/test_check_bundle_registry_dry.py

from dev.scripts.devctl.tests.checks.test_check_bundle_registry_dry import *
