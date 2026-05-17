#!/usr/bin/env python3
"""Backward-compat shim -- use `mutation_bypass_graph_closure.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable mutation-bypass graph check entrypoint while the packaged guard lands replay-only
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/mutation_bypass_graph_closure/command.py

from mutation_bypass_graph_closure.command import main


if __name__ == "__main__":
    raise SystemExit(main())
