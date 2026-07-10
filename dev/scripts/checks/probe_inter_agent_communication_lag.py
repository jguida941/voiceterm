#!/usr/bin/env python3
"""Backward-compat shim -- use ``review_probes.probe_inter_agent_communication_lag``."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable inter-agent communication lag probe entrypoint
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/checks/review_probes/probe_inter_agent_communication_lag.py

from review_probes.probe_inter_agent_communication_lag import *


if __name__ == "__main__":
    raise SystemExit(main())
