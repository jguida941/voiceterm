#!/usr/bin/env python3
"""Backward-compat shim -- use `python_analysis.probe_single_use_helpers`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable probe entrypoint while the single-use-helper implementation lives under `python_analysis/`
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/python_analysis/probe_single_use_helpers.py

from python_analysis.probe_single_use_helpers import *


if __name__ == "__main__":
    raise SystemExit(main())
