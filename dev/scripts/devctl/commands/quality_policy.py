"""Backward-compat shim -- use `devctl.quality_policy.command`."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable quality-policy command module during package split
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/devctl/quality_policy/command.py

from ..quality_policy.command import run
