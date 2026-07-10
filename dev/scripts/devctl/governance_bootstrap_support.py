"""Backward-compat shim -- use `devctl.governance.bootstrap_support` instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable root governance-bootstrap support import while implementation lives under `devctl.governance`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/governance/bootstrap_support.py

from .governance.bootstrap_support import *
from .governance.bootstrap_support import _run_git
