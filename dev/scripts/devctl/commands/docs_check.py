"""Backward-compat shim -- use devctl.commands.docs.check instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable docs-check command module while the implementation lives under `devctl.commands.docs`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/devctl/commands/docs/check.py

from __future__ import annotations

from .docs.check import *
