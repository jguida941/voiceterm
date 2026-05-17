#!/usr/bin/env python3
"""Backward-compat shim -- use ``review_probes.probe_event_id_uniqueness``."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable event-id uniqueness probe entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_event_id_uniqueness.py

from review_probes.probe_event_id_uniqueness import *


if __name__ == "__main__":
    raise SystemExit(main())
