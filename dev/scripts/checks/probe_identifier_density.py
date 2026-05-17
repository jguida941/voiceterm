#!/usr/bin/env python3
"""Backward-compat shim -- use `code_shape_probes.probe_identifier_density`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable probe entrypoint during code-shape probe packaging
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/code_shape_probes/probe_identifier_density.py

from code_shape_probes.probe_identifier_density import main


if __name__ == "__main__":
    raise SystemExit(main())
