"""Backward-compat shim -- use `devctl.commands.check` package instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable check command module path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/check/__init__.py

from .check import *
