"""Startup/session carry-forward projections for compact AI context."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from .master_plan_store import read_plan_rows_jsonl
from .packet_carry_forward import (
    durable_packet_ids_from_finding_rows,
    durable_packet_ids_from_plan_rows,
    packet_carry_forward_debts,
)
from .packet_continuity import (
    PacketContinuityIndex,
    PacketContinuityRow,
    build_packet_continuity_index,
    compact_packet_continuity_index,
    packet_continuity_index_from_payload,
)

if TYPE_CHECKING:
    from .review_state_models import ReviewState


DEFAULT_PACKET_DEBT_LIMIT = 12
DEFAULT_ATTENTION_ITEM_LIMIT = 3
PACKET_CONTINUITY_CONSUMER_CONTRACTS = (
    PacketContinuityIndex,
    PacketContinuityRow,
)


def startup_continuity_attention(
    *,
    runtime_spine_closure: dict[str, object],
    packet_carry_forward_debt: tuple[dict[str, object], ...],
    packet_continuity_index: dict[str, object] | None = None,
    limit: int = DEFAULT_ATTENTION_ITEM_LIMIT,
) -> dict[str, object]:
    """Return the compact post-compaction attention packet for AI bootstraps."""
    runtime_items = _dict_rows(runtime_spine_closure.get("items"))
    violations = _dict_rows(runtime_spine_closure.get("violations"))
    packet_debts = tuple(dict(row) for row in packet_carry_forward_debt)
    packet_continuity = dict(packet_continuity_index or {})
    risky_count = int(runtime_spine_closure.get("risky_item_count") or 0)
    requires_attention = bool(
        not bool(runtime_spine_closure.get("ok", False))
        or risky_count
        or violations
        or packet_debts
    )
    return {
        "contract_id": "StartupContinuityAttention",
        "schema_version": 1,
        "requires_attention": requires_attention,
        "message": (
            "After compaction or resume, read typed continuity state before acting."
        ),
        "runtime_spine_contract_id": str(
            runtime_spine_closure.get("contract_id")
            or "RuntimeSpineClosureState"
        ),
        "runtime_spine_ok": bool(runtime_spine_closure.get("ok", False)),
        "runtime_spine_risky_item_count": risky_count,
        "runtime_spine_violation_count": len(violations),
        "runtime_spine_attention_items": [
            _compact_spine_item(item) for item in runtime_items[:limit]
        ],
        "packet_debt_count": len(packet_debts),
        "packet_debt_ids": [
            str(row.get("packet_id") or "")
            for row in packet_debts[:limit]
            if str(row.get("packet_id") or "").strip()
        ],
        "packet_continuity_contract_id": str(
            packet_continuity.get("contract_id") or "PacketContinuityIndex"
        ),
        "packet_continuity_digest": str(packet_continuity.get("digest") or ""),
        "packet_continuity_sink_counts": dict(
            packet_continuity.get("sink_counts") or {}
        ),
    }


def startup_runtime_spine_closure(repo_root: Path) -> dict[str, object]:
    """Return compact typed runtime-spine closure state for startup surfaces."""
    try:
        from dev.scripts.checks.runtime_spine_closure.report import build_report

        report = build_report(repo_root=repo_root)
    except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
        return {
            "contract_id": "RuntimeSpineClosureState",
            "schema_version": 1,
            "ok": False,
            "violations": [
                {
                    "check": "runtime_spine_closure_state_available",
                    "detail": str(exc),
                }
            ],
        }
    return _compact_runtime_spine_report(report)


def startup_packet_carry_forward_debt(
    *,
    repo_root: Path,
    review_state: "ReviewState | None",
    limit: int = DEFAULT_PACKET_DEBT_LIMIT,
) -> tuple[dict[str, object], ...]:
    """Return compact ACKed packet debt for startup and session-resume."""
    packets = _packets_from_review_state(review_state)
    plan_store = _typed_plan_store_path(repo_root)
    plan_rows = (
        read_plan_rows_jsonl(plan_store)
        if plan_store is not None and plan_store.is_file()
        else ()
    )
    finding_log = _governance_review_log_path(repo_root)
    finding_rows = (
        _read_jsonl_rows(finding_log)
        if finding_log is not None and finding_log.is_file()
        else ()
    )
    debts = packet_carry_forward_debts(
        packets,
        durable_packet_ids=(
            durable_packet_ids_from_plan_rows(plan_rows)
            + durable_packet_ids_from_finding_rows(finding_rows)
        ),
    )
    newest_first = tuple(sorted(debts, key=lambda row: row.packet_id, reverse=True))
    return tuple(_compact_packet_debt(row.to_dict()) for row in newest_first[:limit])


def startup_packet_continuity_index(
    review_state: "ReviewState | None",
    *,
    limit: int = DEFAULT_PACKET_DEBT_LIMIT,
) -> dict[str, object]:
    """Return compact packet continuity state for startup and session-resume."""
    payload = _review_state_payload(review_state)
    existing = packet_continuity_index_from_payload(payload)
    if existing:
        return compact_packet_continuity_index(existing, limit=limit)
    return compact_packet_continuity_index(
        build_packet_continuity_index(_packets_from_review_state(review_state)).to_dict(),
        limit=limit,
    )


def _compact_runtime_spine_report(report: dict[str, object]) -> dict[str, object]:
    return {
        "contract_id": str(report.get("contract_id") or "RuntimeSpineClosureState"),
        "schema_version": int(report.get("schema_version") or 1),
        "ok": bool(report.get("ok")),
        "risky_item_count": int(report.get("risky_item_count") or 0),
        "closure_matrix_row_count": int(report.get("closure_matrix_row_count") or 0),
        "violations": list(report.get("violations") or ())[:3],
        "items": [
            _compact_spine_item(item)
            for item in _dict_rows(report.get("items"))[:8]
        ],
    }


def _compact_spine_item(item: dict[str, object]) -> dict[str, object]:
    return {
        "name": str(item.get("name") or ""),
        "status": str(item.get("status") or ""),
        "owner_refs": list(item.get("owner_refs") or ())[:1],
    }


def _compact_packet_debt(debt: dict[str, object]) -> dict[str, object]:
    return {
        "contract_id": str(debt.get("contract_id") or "PacketCarryForwardDebt"),
        "packet_id": str(debt.get("packet_id") or ""),
        "kind": str(debt.get("kind") or ""),
        "from_agent": str(debt.get("from_agent") or ""),
        "to_agent": str(debt.get("to_agent") or ""),
        "plan_id": str(debt.get("plan_id") or ""),
        "latest_event_id": str(debt.get("latest_event_id") or ""),
        "reason": str(debt.get("reason") or ""),
    }


def _packets_from_review_state(
    review_state: "ReviewState | None",
) -> tuple[dict[str, object], ...]:
    payload = _review_state_payload(review_state)
    if payload:
        return tuple(_dict_rows(payload.get("packets")))
    return ()


def _review_state_payload(review_state: "ReviewState | None") -> dict[str, object]:
    if review_state is None:
        return {}
    to_dict = getattr(review_state, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, dict):
            return payload
    if isinstance(review_state, dict):
        return dict(review_state)
    packets = getattr(review_state, "packets", ()) or ()
    rows: list[dict[str, object]] = []
    for packet in packets:
        if isinstance(packet, dict):
            rows.append(dict(packet))
            continue
        packet_to_dict = getattr(packet, "to_dict", None)
        if callable(packet_to_dict):
            payload = packet_to_dict()
            if isinstance(payload, dict):
                rows.append(payload)
    return {"packets": rows}


def _typed_plan_store_path(repo_root: Path) -> Path | None:
    try:
        from ..governance.draft import scan_repo_governance

        master_plan = scan_repo_governance(repo_root).master_plan
    except (ImportError, OSError, RuntimeError, ValueError):
        return None
    typed_store_path = str(master_plan.typed_store_path or "").strip()
    projection_path = str(
        master_plan.projection_path or master_plan.source_path or ""
    ).strip()
    if not typed_store_path:
        return None
    if not projection_path or not (repo_root / projection_path).is_file():
        return None
    return repo_root / typed_store_path


def _governance_review_log_path(repo_root: Path) -> Path | None:
    try:
        from .governance_scan import scan_repo_governance_safely
        from .review_snapshot_sources import resolve_governance_log_path

        governance = scan_repo_governance_safely(repo_root)
        return resolve_governance_log_path(repo_root, governance)
    except (ImportError, OSError, RuntimeError, ValueError):
        fallback = repo_root / "dev/reports/governance/finding_reviews.jsonl"
        return fallback if fallback.is_file() else None


def _read_jsonl_rows(path: Path) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return tuple(rows)


def _dict_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [dict(row) for row in value if isinstance(row, dict)]


__all__ = [
    "DEFAULT_ATTENTION_ITEM_LIMIT",
    "DEFAULT_PACKET_DEBT_LIMIT",
    "PACKET_CONTINUITY_CONSUMER_CONTRACTS",
    "startup_continuity_attention",
    "startup_packet_continuity_index",
    "startup_packet_carry_forward_debt",
    "startup_runtime_spine_closure",
]
