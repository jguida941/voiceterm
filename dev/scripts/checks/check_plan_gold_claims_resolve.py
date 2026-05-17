#!/usr/bin/env python3
"""Validate GOLD/proof promotion claims resolve to real repo symbols."""

from __future__ import annotations

import sys

try:
    from plan_gold_claims_resolve.command import main
except ModuleNotFoundError:
    from dev.scripts.checks.plan_gold_claims_resolve.command import main


if __name__ == "__main__":
    sys.exit(main())
