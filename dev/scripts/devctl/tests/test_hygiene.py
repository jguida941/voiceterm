"""Backward-compat shim -- use tests.governance.test_hygiene instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable hygiene test module path while the implementation lives under `tests/governance`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/tests/governance/test_hygiene.py

from dev.scripts.devctl.tests.governance.test_hygiene import *
