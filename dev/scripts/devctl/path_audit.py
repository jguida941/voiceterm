"""Backward-compat shim -- use devctl.path_audit_support.core instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable path-audit helper import while the implementation lives under `devctl.path_audit_support`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/path_audit_support/core.py

from .path_audit_support.core import *
