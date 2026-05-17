"""Backward-compat shim -- use tests.checks.test_check_rust_compiler_warnings instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable guard-test path during the checks package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/checks/test_check_rust_compiler_warnings.py

from dev.scripts.devctl.tests.checks.test_check_rust_compiler_warnings import *
