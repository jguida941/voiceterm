#!/usr/bin/env python3
"""Backward-compat shim -- use `compat_matrix.compat_matrix_smoke`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable compatibility-matrix smoke entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/compat_matrix/compat_matrix_smoke.py

from compat_matrix.compat_matrix_smoke import *


if __name__ == "__main__":
    raise SystemExit(main())
