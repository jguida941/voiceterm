"""Batch triage helpers for packet carry-forward debt."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from .packet_debt_remediation_contracts import (
    DecidedPacketDebtDetector,
    PacketBatchTriage,
    PacketBatchTriageRow,
)

PacketResolver = Callable[[Mapping[str, object]], str]


def decided_packet_debt_detector(
    debts: tuple[object, ...],
) -> DecidedPacketDebtDetector:
    """Return ACKed-but-unbuilt packet-debt summary."""
    decided = tuple(
        debt for debt in debts
        if getattr(debt, "reason", "") == "acked_without_terminal_or_durable_owner"
    )
    return DecidedPacketDebtDetector(
        reason="acked_without_terminal_or_durable_owner",
        total_count=len(decided),
        sample_packet_ids=tuple(getattr(debt, "packet_id", "") for debt in decided[:10]),
        kind_counts=_counts_by_attr(decided, "kind"),
        status_counts=_counts_by_attr(decided, "status"),
    )


def packet_batch_triage(
    *,
    debts: tuple[object, ...],
    packet_by_id: dict[str, dict[str, object]],
    target_ref_for_packet: PacketResolver,
    action_for_packet: PacketResolver,
    cluster_id_for: Callable[[str, str, str], str],
) -> PacketBatchTriage:
    """Return clustered triage rows for all packet debt."""
    batches: dict[str, list[object]] = {}
    batch_metadata: dict[str, tuple[str, str, str]] = {}
    for debt in debts:
        packet = packet_by_id.get(getattr(debt, "packet_id", ""), {})
        target_ref = target_ref_for_packet(packet)
        action = action_for_packet(packet)
        reason = getattr(debt, "reason", "")
        cluster_id = cluster_id_for(reason, target_ref, getattr(debt, "kind", ""))
        batches.setdefault(cluster_id, []).append(debt)
        batch_metadata[cluster_id] = (reason, action, target_ref)

    rows = tuple(
        _packet_batch_triage_row(
            cluster_id=cluster_id,
            debts=tuple(batch_debts),
            metadata=batch_metadata[cluster_id],
        )
        for cluster_id, batch_debts in batches.items()
    )
    sorted_rows = tuple(
        sorted(rows, key=lambda row: (-row.packet_count, row.cluster_id))
    )
    largest = sorted_rows[0].packet_count if sorted_rows else 0
    return PacketBatchTriage(
        rows=sorted_rows,
        total_cluster_count=len(sorted_rows),
        largest_batch_size=largest,
    )


def _packet_batch_triage_row(
    *,
    cluster_id: str,
    debts: tuple[object, ...],
    metadata: tuple[str, str, str],
) -> PacketBatchTriageRow:
    reason, action, target_ref = metadata
    return PacketBatchTriageRow(
        cluster_id=cluster_id,
        reason=reason,
        recommended_action=action,
        target_ref=target_ref,
        packet_count=len(debts),
        sample_packet_ids=tuple(getattr(debt, "packet_id", "") for debt in debts[:10]),
        kind_counts=_counts_by_attr(debts, "kind"),
        status_counts=_counts_by_attr(debts, "status"),
    )


def _counts_by_attr(rows: tuple[object, ...], attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(getattr(row, attr, "") or "").strip() or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


__all__ = [
    "decided_packet_debt_detector",
    "packet_batch_triage",
]
