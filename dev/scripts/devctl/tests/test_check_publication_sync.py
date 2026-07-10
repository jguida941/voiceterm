"""Backward-compat shim -- use tests.checks.test_check_publication_sync instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable publication-sync test module path while the implementation lives under `tests/checks`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/tests/checks/test_check_publication_sync.py

from dev.scripts.devctl.tests.checks.test_check_publication_sync import *
