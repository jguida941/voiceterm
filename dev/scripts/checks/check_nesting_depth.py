#!/usr/bin/env python3
"""Backward-compat shim -- use `code_shape.check_nesting_depth`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable nesting-depth guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/code_shape/check_nesting_depth.py

from code_shape.check_nesting_depth import *


if __name__ == "__main__":
    raise SystemExit(main())
