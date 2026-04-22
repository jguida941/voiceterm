"""Public seam for report-only bounded worktree-orphan inventory scans."""

from __future__ import annotations

from .worktree_orphan_inventory_builder import (
    DEFAULT_SCAN_SCOPE,
    build_orphan_inventory_report,
)
from .worktree_orphan_inventory_parse import orphan_inventory_report_from_mapping
from .worktree_orphan_inventory_report import OrphanInventoryReport

__all__ = [
    "DEFAULT_SCAN_SCOPE",
    "OrphanInventoryReport",
    "build_orphan_inventory_report",
    "orphan_inventory_report_from_mapping",
]
