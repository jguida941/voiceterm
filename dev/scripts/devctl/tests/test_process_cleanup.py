"""Backward-compat shim -- use tests.commands.process.test_process_cleanup instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable process-cleanup test path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/commands/process/test_process_cleanup.py

from dev.scripts.devctl.tests.commands.process.test_process_cleanup import *
