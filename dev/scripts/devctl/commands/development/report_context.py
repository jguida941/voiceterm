"""Context helpers for the development report builder."""

from __future__ import annotations

from typing import Any

from ...config import REPO_ROOT
from ...runtime.dashboard_snapshot_authority import build_dashboard_snapshot
from ...runtime.plan_intent_ingestion import (
    PLAN_INTENT_INGESTION_RECEIPT_STORE_REL,
    plan_row_id_by_packet_receipt,
    read_plan_intent_ingestion_receipts,
    terminal_packet_receipt_by_packet,
)
from .packet_attention import packet_attention_from_review_state


def orchestration_dashboard(repo_root) -> dict[str, Any]:
    """Return the dashboard-backed blocker view used by agent-loop, if available."""
    try:
        return build_dashboard_snapshot(
            repo_root=repo_root,
            view="overview",
            role="dashboard",
            include_review_state=False,
        )
    except Exception:  # broad-except: allow reason=dashboard snapshot is advisory context for /develop fallback=omit orchestration dashboard
        return {}


def packet_attention_context(
    review_state: Any,
    *,
    rows: Any,
    agent: str,
) -> tuple[dict[str, Any], Any]:
    """Return terminal packet receipts and packet attention for one actor."""
    receipts = read_plan_intent_ingestion_receipts(
        REPO_ROOT / PLAN_INTENT_INGESTION_RECEIPT_STORE_REL
    )
    terminal_receipts = terminal_packet_receipt_by_packet(receipts)
    packet_attention = packet_attention_from_review_state(
        review_state,
        rows=rows,
        agent=agent,
        terminal_receipt_by_packet=terminal_receipts,
        durable_row_id_by_packet=plan_row_id_by_packet_receipt(receipts),
        repo_root=REPO_ROOT,
    )
    return terminal_receipts, packet_attention


def packet_ingestion_next_command(ingestion_decision: Any) -> str:
    """Return the command for durable packet-intent ingestion decisions."""
    if not isinstance(ingestion_decision, dict):
        return ""
    if str(ingestion_decision.get("decision") or "").strip() != "ingest_durable_intent":
        return ""
    return str(ingestion_decision.get("next_command") or "").strip()


__all__ = [
    "orchestration_dashboard",
    "packet_attention_context",
    "packet_ingestion_next_command",
]
