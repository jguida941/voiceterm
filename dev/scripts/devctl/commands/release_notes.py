"""Backward-compat shim -- use `devctl.commands.release.notes` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable release notes helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/release/notes.py

from __future__ import annotations

import sys

from .release import notes as _impl

sys.modules[__name__] = _impl
