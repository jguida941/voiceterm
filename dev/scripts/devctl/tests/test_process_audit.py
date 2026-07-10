"""Backward-compat shim -- use tests.commands.process.test_process_audit instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable process-audit test path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/commands/process/test_process_audit.py

from dev.scripts.devctl.tests.commands.process.test_process_audit import *
