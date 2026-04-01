"""Backward-compat shim -- use `devctl.quality_policy.values` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable quality-policy values path during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/quality_policy/values.py

from .quality_policy.values import *
