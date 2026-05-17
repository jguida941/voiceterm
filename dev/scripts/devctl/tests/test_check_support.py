"""Backward-compat shim -- use tests.commands.check.test_check_support instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check-support test path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/commands/check/test_check_support.py

from dev.scripts.devctl.tests.commands.check.test_check_support import *
