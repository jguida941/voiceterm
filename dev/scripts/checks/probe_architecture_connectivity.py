#!/usr/bin/env python3
"""Backward-compat shim -- use `architecture_probes.probe_architecture_connectivity`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable architecture probe entrypoint while implementation lives under `architecture_probes/`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/architecture_probes/probe_architecture_connectivity.py

from architecture_probes.probe_architecture_connectivity import *


if __name__ == "__main__":
    raise SystemExit(main())
