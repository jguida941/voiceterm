"""Ordering helpers for packet-debt remediation batches."""

from __future__ import annotations

import re


def newest_debts_first(debts) -> tuple[object, ...]:
    """Return packet-debt rows ordered by numeric packet suffix, newest first."""

    return tuple(
        sorted(
            debts,
            key=lambda debt: _packet_number(str(getattr(debt, "packet_id", "") or "")),
            reverse=True,
        )
    )


def _packet_number(packet_id: str) -> int:
    match = re.search(r"(\d+)$", packet_id.strip())
    if match is None:
        return 0
    return int(match.group(1))


__all__ = ["newest_debts_first"]
