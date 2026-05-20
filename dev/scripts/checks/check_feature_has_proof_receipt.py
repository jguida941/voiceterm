#!/usr/bin/env python3
"""Backward-compat shim -- use `feature_has_proof_receipt.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable feature-proof guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/feature_has_proof_receipt/command.py
if __package__:
    from .feature_has_proof_receipt.command import *
else:
    from feature_has_proof_receipt.command import *
if __name__ == "__main__": raise SystemExit(main())
