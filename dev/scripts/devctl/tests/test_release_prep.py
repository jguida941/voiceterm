"""Backward-compat shim -- use tests.release.test_release_prep instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable release-prep test path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/release/test_release_prep.py

from dev.scripts.devctl.tests.release.test_release_prep import *
