"""Backward-compat shim -- use `devctl.commands.governance.hygiene_audits_archive` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable hygiene archive audit helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/governance/hygiene_audits_archive.py

from __future__ import annotations

import sys

from .governance import hygiene_audits_archive as _impl

sys.modules[__name__] = _impl
