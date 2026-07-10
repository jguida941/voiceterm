"""Backward-compat shim -- use tests.governance.test_orchestrate_watch instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable orchestrate-watch test import path during the governance package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/governance/test_orchestrate_watch.py

from dev.scripts.devctl.tests.governance.test_orchestrate_watch import *
