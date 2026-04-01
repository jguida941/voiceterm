"""Backward-compat shim -- use `devctl.quality_policy.scopes` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable quality-policy scopes path during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/quality_policy/scopes.py

from .quality_policy.scopes import *
