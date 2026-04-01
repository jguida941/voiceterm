"""Backward-compat shim -- use `rust_analysis.rust_check_text_utils`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Rust text-utils import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/rust_analysis/rust_check_text_utils.py

from rust_analysis.rust_check_text_utils import *
