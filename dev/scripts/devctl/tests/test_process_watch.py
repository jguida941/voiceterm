"""Backward-compat shim -- use tests.commands.process.test_process_watch instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable process-watch test path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/commands/process/test_process_watch.py

from dev.scripts.devctl.tests.commands.process.test_process_watch import *
