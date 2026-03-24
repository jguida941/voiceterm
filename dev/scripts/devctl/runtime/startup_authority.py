"""Shared startup-authority report helpers for devctl surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_startup_authority_report(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Return the canonical startup-authority guard report."""
    try:
        from dev.scripts.checks.startup_authority_contract.command import (
            _build_report,
        )
    except ModuleNotFoundError:
        from checks.startup_authority_contract.command import _build_report

    return dict(_build_report(repo_root=repo_root))
