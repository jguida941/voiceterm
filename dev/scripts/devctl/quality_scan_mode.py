"""Backward-compat shim -- use `devctl.quality_policy.scan_mode` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable quality scan-mode path during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/quality_policy/scan_mode.py

from .quality_policy.scan_mode import *
