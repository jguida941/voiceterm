#!/usr/bin/env python3
"""Backward-compat shim -- use `non_trivial_output_proof.command`."""
# shim-owner: tooling/platform
# shim-reason: stable guard entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/non_trivial_output_proof/command.py

from non_trivial_output_proof.command import *  # noqa: F401,F403


if __name__ == "__main__":
    raise SystemExit(main())  # noqa: F405
