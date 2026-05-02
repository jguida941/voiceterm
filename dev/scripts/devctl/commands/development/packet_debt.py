"""Packet-debt report wiring for the typed `/develop` controller."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...review_channel.event_store import resolve_artifact_paths
from ...review_channel.packet_debt_remediation import (
    PacketDebtRemediationInputs,
    packet_debt_remediation_report,
)
from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL


def packet_debt_payload(
    action: str,
    args: Any,
    *,
    repo_root: Path,
) -> dict[str, Any] | None:
    """Return the packet-debt payload for audit-packets actions."""
    if action != "audit-packets":
        return None
    report = packet_debt_remediation_report(
        PacketDebtRemediationInputs(
            repo_root=repo_root,
            artifact_paths=resolve_artifact_paths(repo_root=repo_root),
            review_state_path=(
                repo_root
                / "dev/reports/review_channel/projections/latest/review_state.json"
            ),
            plan_store_path=repo_root / DEFAULT_MASTER_PLAN_STORE_REL,
            finding_log_path=repo_root / "dev/reports/governance/finding_reviews.jsonl",
            limit=max(1, int(getattr(args, "max_packets", 30) or 30)),
            write=(
                bool(getattr(args, "drain_packets", False))
                and not bool(getattr(args, "dry_run", False))
            ),
        )
    )
    return report.to_dict()


__all__ = ["packet_debt_payload"]
