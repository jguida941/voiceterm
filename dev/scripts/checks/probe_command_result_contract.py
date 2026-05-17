#!/usr/bin/env python3
"""Backward-compat shim -- use ``review_probes.probe_command_result_contract``."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable command-result contract probe entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_command_result_contract.py

from review_probes.probe_command_result_contract import *


if __name__ == "__main__":
    raise SystemExit(main())
