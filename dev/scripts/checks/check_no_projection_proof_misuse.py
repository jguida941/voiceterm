#!/usr/bin/env python3
"""Backward-compat shim -- use `no_projection_proof_misuse.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable projection-proof guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/no_projection_proof_misuse/command.py
if __package__:
    from .no_projection_proof_misuse.command import *
else:
    from no_projection_proof_misuse.command import *
if __name__ == "__main__": raise SystemExit(main())
