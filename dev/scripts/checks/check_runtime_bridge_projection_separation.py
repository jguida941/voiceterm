#!/usr/bin/env python3
"""Backward-compat shim -- use `runtime_bridge_projection_separation.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable check entrypoint while implementation lives under a check package
# shim-expiry: 2026-11-11
# shim-target: dev/scripts/checks/runtime_bridge_projection_separation/command.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BridgeSeparationGuard:
    """Registry-facing contract for the runtime bridge-separation guard report."""

    guard_id: str
    ok: bool
    report_only: bool
    would_fail: bool
    checked_paths: tuple[str, ...] = field(default_factory=tuple)
    violation_count: int = 0
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    migration_policy: str = ""
    schema_version: int = 1
    contract_id: str = "BridgeSeparationGuard"
    command: str = "check_runtime_bridge_projection_separation"


try:
    from runtime_bridge_projection_separation.command import main
except ModuleNotFoundError:
    from dev.scripts.checks.runtime_bridge_projection_separation.command import main


if __name__ == "__main__":
    raise SystemExit(main())
