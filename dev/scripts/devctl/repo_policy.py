"""Backward-compat shim -- use devctl.governance.repo_policy instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable repo-policy import while governance helpers move under `devctl.governance`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/governance/repo_policy.py

from __future__ import annotations

from .governance.repo_policy import *
