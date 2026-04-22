"""devctl orphan-inventory command seam."""

from __future__ import annotations

from .orphan_inventory_parser import add_parser
from .orphan_inventory_run import run

__all__ = ["add_parser", "run"]
