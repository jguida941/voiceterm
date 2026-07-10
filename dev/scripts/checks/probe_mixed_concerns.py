#!/usr/bin/env python3
"""Backward-compat shim -- use ``code_shape_support.probe_mixed_concerns``."""
# shim-owner: tooling/code-governance
# shim-reason: runnable probe entrypoint delegates to subpackage
# shim-expiry: 2026-06-30
# shim-target: dev/scripts/checks/code_shape_support/probe_mixed_concerns.py

from code_shape_support.probe_mixed_concerns import main, find_function_clusters

__all__ = ["main", "find_function_clusters"]

if __name__ == "__main__":
    raise SystemExit(main())
