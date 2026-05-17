"""Backward-compat shim -- use devctl.integrations.federation_policy instead."""
# shim-owner: tooling/integrations
# shim-reason: preserve the stable root import while implementation lives under `devctl.integrations.federation_policy`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/integrations/federation_policy.py
from .integrations.federation_policy import *
