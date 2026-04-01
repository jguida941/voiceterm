"""Backward-compat shim -- use tests.process_sweep.test_process_sweep instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable process-sweep test path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/process_sweep/test_process_sweep.py

from dev.scripts.devctl.tests.process_sweep.test_process_sweep import *
