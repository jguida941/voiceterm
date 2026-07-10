"""Backward-compat shim -- use commands.governance.orchestrate_watch instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable orchestrate-watch command entrypoint during command package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/governance/orchestrate_watch.py

from .governance.orchestrate_watch import *
