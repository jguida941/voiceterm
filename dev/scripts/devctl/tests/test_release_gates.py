"""Backward-compat shim -- use tests.release.test_release_gates instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable release-gates test path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/release/test_release_gates.py

from dev.scripts.devctl.tests.release.test_release_gates import *
