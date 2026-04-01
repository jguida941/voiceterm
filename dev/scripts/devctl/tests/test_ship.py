"""Backward-compat shim -- use tests.release.test_ship instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable ship test path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/release/test_ship.py

from dev.scripts.devctl.tests.release.test_ship import *
