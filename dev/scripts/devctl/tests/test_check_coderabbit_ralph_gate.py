"""Backward-compat shim -- use tests.checks.test_check_coderabbit_ralph_gate instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable guard-test path during the checks package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/checks/test_check_coderabbit_ralph_gate.py

from dev.scripts.devctl.tests.checks.test_check_coderabbit_ralph_gate import *
