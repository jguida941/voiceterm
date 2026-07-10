"""Backward-compat shim -- use devctl.commands.vcs.parser instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable root sync/push/commit parser module path during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/vcs/parser.py

from .commands.vcs.parser import *
