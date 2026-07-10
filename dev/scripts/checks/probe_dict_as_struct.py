#!/usr/bin/env python3
"""Backward-compat shim -- use `review_probes.probe_dict_as_struct`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable dict-as-struct probe entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_dict_as_struct.py

from review_probes.probe_dict_as_struct import *


if __name__ == "__main__":
    raise SystemExit(main())
