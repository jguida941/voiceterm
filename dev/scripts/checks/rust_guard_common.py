"""Backward-compat shim -- use `rust_analysis.rust_guard_common`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable Rust guard-common import surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/rust_analysis/rust_guard_common.py

from rust_analysis.rust_guard_common import *
