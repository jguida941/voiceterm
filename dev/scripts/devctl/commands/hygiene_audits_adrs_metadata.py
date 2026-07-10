"""Backward-compat shim -- use `devctl.commands.governance.hygiene_audits_adrs_metadata` instead."""
# shim-owner: tooling/devctl
# shim-reason: preserve the stable hygiene ADR metadata helper path during package split
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/commands/governance/hygiene_audits_adrs_metadata.py

from __future__ import annotations

import sys

from .governance import hygiene_audits_adrs_metadata as _impl

sys.modules[__name__] = _impl
