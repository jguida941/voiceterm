#!/usr/bin/env python3
"""Backward-compat shim -- use `context_graph_snapshot_freshness.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve stable ContextGraph freshness guard entrypoint mirroring the ReviewSnapshot pattern
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/context_graph_snapshot_freshness/command.py

from context_graph_snapshot_freshness.command import *  # noqa: F401,F403


if __name__ == "__main__":
    raise SystemExit(main())  # noqa: F405
