"""Backward-compat shim -- use `devctl.commands.discover` package instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable discover command module path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/discover/__init__.py

from .discover import *
