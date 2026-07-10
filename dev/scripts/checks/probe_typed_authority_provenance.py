#!/usr/bin/env python3
"""Backward-compat shim -- use `architecture_probes.probe_typed_authority_provenance`."""
# shim-owner: tooling/code-governance
# shim-reason: preserve the stable typed-authority provenance probe entrypoint while implementation lives under `architecture_probes/`
# shim-expiry: 2026-10-31
# shim-target: dev/scripts/checks/architecture_probes/probe_typed_authority_provenance.py

from architecture_probes.probe_typed_authority_provenance import *


if __name__ == "__main__":
    raise SystemExit(main())
