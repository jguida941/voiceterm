"""Backward-compat shim -- use devctl.integrations.sync_parser instead."""
# shim-owner: tooling/integrations
# shim-reason: preserve the stable root import while implementation lives under `devctl.integrations.sync_parser`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/integrations/sync_parser.py
from .integrations.sync_parser import *
