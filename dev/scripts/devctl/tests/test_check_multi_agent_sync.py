"""Backward-compat shim -- use tests.checks.test_check_multi_agent_sync instead."""
# shim-owner: tooling/review-channel
# shim-reason: preserve the stable multi-agent-sync test import path during the test-package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/tests/checks/test_check_multi_agent_sync.py

from dev.scripts.devctl.tests.checks.test_check_multi_agent_sync import *
