"""Backward-compat shim -- use devctl.integrations.import_parser instead."""
# shim-owner: tooling/integrations
# shim-reason: preserve the stable root import while implementation lives under `devctl.integrations.import_parser`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/integrations/import_parser.py
from .integrations.import_parser import *
