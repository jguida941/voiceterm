"""Live packet-to-plan promotion checks for active-plan authority."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, import_repo_module
except ModuleNotFoundError:  # pragma: no cover - package execution fallback
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, import_repo_module

_packet_storage = import_repo_module(
    "dev.scripts.devctl.review_channel.pending_packet_storage",
    repo_root=REPO_ROOT,
)
_plan_refs = import_repo_module(
    "dev.scripts.devctl.runtime.plan_reference_resolution",
    repo_root=REPO_ROOT,
)
_project_governance = import_repo_module(
    "dev.scripts.devctl.runtime.project_governance",
    repo_root=REPO_ROOT,
)

PlanRegistry = _project_governance.PlanRegistry
PlanRegistryEntry = _project_governance.PlanRegistryEntry
collect_packet_plan_authority_gaps = _plan_refs.collect_packet_plan_authority_gaps
load_pending_packets = _packet_storage.load_pending_packets


def validate_live_packet_plan_sync(
    *,
    repo_root: Path,
    registry_by_path: Mapping[str, Mapping[str, str]],
) -> list[str]:
    """Return unresolved pending packet->plan promotion gaps."""
    packets = load_pending_packets(repo_root, fail_closed=False)
    if not packets:
        return []
    plan_registry = _plan_registry_from_rows(registry_by_path)
    return list(
        collect_packet_plan_authority_gaps(
            repo_root=repo_root,
            plan_registry=plan_registry,
            packets=packets,
        )
    )


def _plan_registry_from_rows(
    registry_by_path: Mapping[str, Mapping[str, str]],
) -> PlanRegistry:
    entries = tuple(
        PlanRegistryEntry(
            path=path,
            role=str(row.get("role") or "").strip(),
            authority=str(row.get("authority") or "").strip(),
            scope=str(row.get("scope") or row.get("mp_scope") or "").strip(),
            when_agents_read=str(
                row.get("when") or row.get("when_read") or ""
            ).strip(),
        )
        for path, row in sorted(registry_by_path.items())
    )
    return PlanRegistry(entries=entries)


__all__ = ["validate_live_packet_plan_sync"]
