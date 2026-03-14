"""Backward-compat shim -- use devctl.publication_sync.git instead."""
# shim-owner: tooling/publication-sync
# shim-reason: preserve the stable root import while implementation lives under `devctl.publication_sync.git`
# shim-expiry: 2026-09-30
# shim-target: dev/scripts/devctl/publication_sync/git.py
from .publication_sync.git import *
