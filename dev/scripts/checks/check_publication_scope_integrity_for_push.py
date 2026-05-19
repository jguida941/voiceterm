#!/usr/bin/env python3
"""Backward-compat shim -- use publication_scope_integrity_for_push.command."""
# shim-owner: tooling/governance
# shim-reason: keep push preflight's stable check path while implementation lives under `checks/publication_scope_integrity_for_push`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/publication_scope_integrity_for_push/command.py

from __future__ import annotations

from publication_scope_integrity_for_push.command import main


if __name__ == "__main__":
    raise SystemExit(main())
