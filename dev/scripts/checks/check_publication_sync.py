#!/usr/bin/env python3
"""Backward-compat shim -- use checks.publication_sync_guard.command instead."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable publication-sync guard entrypoint while the implementation lives under `checks/publication_sync_guard`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/publication_sync_guard/command.py

from __future__ import annotations

from publication_sync_guard.command import main


if __name__ == "__main__":
    raise SystemExit(main())
