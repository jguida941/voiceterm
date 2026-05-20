#!/usr/bin/env python3
"""Backward-compat shim -- use `commit_complete_proof.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable commit-proof guard entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/commit_complete_proof/command.py
if __package__:
    from .commit_complete_proof.command import *
else:
    from commit_complete_proof.command import *
if __name__ == "__main__": raise SystemExit(main())
