#!/usr/bin/env python3
"""Backward-compat shim -- use ``code_shape_support.probe_split_advisor``."""
# shim-owner: tooling/code-governance
# shim-reason: runnable probe entrypoint delegates to subpackage
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/code_shape_support/probe_split_advisor.py

from code_shape_support.probe_split_advisor import main

__all__ = ["main"]

if __name__ == "__main__":
    raise SystemExit(main())
