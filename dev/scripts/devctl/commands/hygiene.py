"""Backward-compat shim -- use devctl.commands.governance.hygiene instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable hygiene command import while the implementation lives under `devctl.commands.governance`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/commands/governance/hygiene.py

from .governance.hygiene import *
