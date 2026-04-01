"""Backward-compat shim -- use tests.commands.check.test_check instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check-command test path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/commands/check/test_check.py

from dev.scripts.devctl.tests.commands.check.test_check import *
