"""Backward-compat shim -- use tests.checks.test_check_ide_provider_isolation instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable guard-test path during the checks package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/checks/test_check_ide_provider_isolation.py

from dev.scripts.devctl.tests.checks.test_check_ide_provider_isolation import *
