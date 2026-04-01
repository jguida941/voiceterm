"""Backward-compat shim -- use `devctl.commands.release` package instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable release command module path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/release/__init__.py

from .release import *
