#!/usr/bin/env python3
"""Backward-compat shim -- use `rust_analysis.check_rust_best_practices`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Rust best-practices guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/rust_analysis/check_rust_best_practices.py

import sys

from rust_analysis import check_rust_best_practices as _impl

sys.modules[__name__] = _impl


if __name__ == "__main__":
    raise SystemExit(_impl.main())
