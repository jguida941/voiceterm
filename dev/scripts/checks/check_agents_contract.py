#!/usr/bin/env python3
"""Backward-compat shim -- use `agents_contract.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable AGENTS.md contract guard entrypoint while the implementation lives under `checks/agents_contract`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/agents_contract/command.py

from __future__ import annotations

from agents_contract.command import *


if __name__ == "__main__":
    raise SystemExit(main())
