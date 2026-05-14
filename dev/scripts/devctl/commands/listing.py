"""Backward-compat shim -- use `devctl.commands.listing` package instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable list command module path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/listing/__init__.py
# command-surface-guard-visible: "bypass"

from .listing import *
