#!/usr/bin/env python3
"""Backward-compat shim -- use `compat_matrix.check_compat_matrix`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable compatibility-matrix guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/compat_matrix/check_compat_matrix.py

from compat_matrix.check_compat_matrix import *


if __name__ == "__main__":
    raise SystemExit(main())
