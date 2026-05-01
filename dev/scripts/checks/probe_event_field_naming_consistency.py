#!/usr/bin/env python3
"""Backward-compat shim — use ``review_probes.probe_event_field_naming_consistency``."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable event-field-naming probe entrypoint during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_event_field_naming_consistency.py

from review_probes.probe_event_field_naming_consistency import *


if __name__ == "__main__":
    raise SystemExit(main())
