#!/usr/bin/env python3
"""Backward-compat shim -- use `review_surface_consistency.command`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable review-surface consistency guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_surface_consistency/command.py

from review_surface_consistency import REPO_ROOT, _disk_turn_authority_parity_errors, build_report, main


if __name__ == "__main__":
    raise SystemExit(main())
