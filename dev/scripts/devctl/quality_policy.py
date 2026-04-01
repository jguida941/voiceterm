"""Backward-compat shim -- use `devctl.quality_policy` package instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable quality-policy module path during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/quality_policy/__init__.py

from .quality_policy import *
