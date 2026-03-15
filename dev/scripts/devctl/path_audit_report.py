"""Backward-compat shim -- use devctl.path_audit_support.report instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable path-audit report import while support helpers move under `devctl.path_audit_support`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/path_audit_support/report.py

from __future__ import annotations

from .path_audit_support.report import *
