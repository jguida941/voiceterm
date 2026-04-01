"""Backward-compat shim -- use `devctl.quality_policy.loader` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable quality-policy loader path during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/quality_policy/loader.py

from .quality_policy.loader import *
