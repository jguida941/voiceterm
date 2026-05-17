"""Backward-compat shim -- use tests.commands.docs.test_check_constants instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable docs-check constants test path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/commands/docs/test_check_constants.py

from dev.scripts.devctl.tests.commands.docs.test_check_constants import *
