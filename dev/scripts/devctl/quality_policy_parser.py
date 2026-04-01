"""Backward-compat shim -- use `devctl.quality_policy.parser` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable quality-policy parser path during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/quality_policy/parser.py

from .quality_policy.parser import *
