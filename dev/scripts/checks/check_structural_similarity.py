#!/usr/bin/env python3
"""Backward-compat shim -- use `code_shape.check_structural_similarity`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable structural-similarity guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/code_shape/check_structural_similarity.py

from code_shape.check_structural_similarity import *


if __name__ == "__main__":
    raise SystemExit(main())
