#!/usr/bin/env python3
"""Backward-compat shim -- use `rust_analysis.check_rust_lint_debt`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Rust lint-debt guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/rust_analysis/check_rust_lint_debt.py

from rust_analysis.check_rust_lint_debt import *


if __name__ == "__main__":
    raise SystemExit(main())
