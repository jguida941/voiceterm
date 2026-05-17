#!/usr/bin/env python3
"""Backward-compat shim -- use `schema_fixture_handshake.command`."""
# shim-owner: tooling/governance
# shim-reason: stable dev/scripts/checks/ public guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/schema_fixture_handshake/command.py

if __package__: from .schema_fixture_handshake.command import evaluate_schema_fixture_handshake, main
else: from schema_fixture_handshake.command import evaluate_schema_fixture_handshake, main

if __name__ == "__main__":
    raise SystemExit(main())
