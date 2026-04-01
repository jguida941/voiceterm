"""Backward-compat shim -- use `review_probes.probe_path_filters`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable review-probe path-filter helper surface during package extraction
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_path_filters.py

from review_probes.probe_path_filters import *
