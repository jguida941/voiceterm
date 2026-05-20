#!/usr/bin/env python3
"""Backward-compat shim -- use `push_complete_proof.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable push-proof guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/push_complete_proof/command.py
if __package__:
    from .push_complete_proof.command import *
else:
    from push_complete_proof.command import *
if __name__ == "__main__": raise SystemExit(main())
