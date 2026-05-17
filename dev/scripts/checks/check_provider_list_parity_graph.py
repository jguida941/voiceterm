#!/usr/bin/env python3
"""Backward-compat shim -- use `provider_list_parity_graph.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable provider-list parity guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/provider_list_parity_graph/command.py

if __package__: from .provider_list_parity_graph.command import build_report, main
else: from provider_list_parity_graph.command import build_report, main


if __name__ == "__main__":
    raise SystemExit(main())
