#!/usr/bin/env python3
"""Fail closed when pending packets violate A19 lifecycle hygiene rules."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _iter_jsonl,
        packets_from_review_state as _packets_from_review_state,
        parse_utc as _parse_utc,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _iter_jsonl,
        packets_from_review_state as _packets_from_review_state,
        parse_utc as _parse_utc,
        utc_timestamp,
    )


COMMAND = "check_packet_hygiene_enforcement"
CONTRACT_ID = "PacketHygieneEnforcementGuard"

DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
DEFAULT_HYGIENE_WINDOW_SECONDS = 24 * 3600
DEFAULT_DELIVERY_PENDING_SECONDS = 300
DEFAULT_MATERIALIZATION_INTERVAL_SECONDS = 3600
DEFAULT_EXPIRE_PACKETS_LIMIT = 20

RULE_STALE_IN_DEFAULT_VIEW = "stale_pending_in_default_inbox_view"
RULE_NO_RECENT_MATERIALIZATION = "stale_count_with_no_recent_materialization"
RULE_DELIVERY_PENDING = "delivery_emitted_at_utc_missing_past_threshold"
RULE_DURABLE_BINDING_MISSING = "live_pending_lacks_durable_binding"
RULE_SWEEP_CANNOT_DRAIN = "expire_packets_default_below_stale_backlog"

DISPLAY_TEXT = (
    "Packet hygiene violation. Past-hygiene-window pendings, missing "
    "materialization receipts, delivery-pending posts, durably-unbound packets, "
    "or under-sized sweep defaults will not be tolerated."
)

PACKET_EXPIRED_EVENT_TYPE = "packet_expired"
SANCTIONED_ROUTE_KINDS = frozenset(
    {
        "task_progress",
        "task_started",
        "task_blocked",
        "task_produced",
        "action_request",
        "decision",
        "finding",
        "continuation_anchor",
    }
)


@dataclass(frozen=True, slots=True)
class HygieneViolation:
    rule_id: str
    detail: str
    remediation: str
    evidence_packet_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "detail": self.detail,
            "remediation": self.remediation,
            "evidence_packet_ids": list(self.evidence_packet_ids),
        }


@dataclass(frozen=True, slots=True)
class DeliveryStallViolation:
    packet_id: str
    posted_at: str
    threshold_seconds: int
    route_kind: str
    reason: str = RULE_DELIVERY_PENDING

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_delivery_stall(
    *,
    packets: Sequence[Mapping[str, object]],
    now: datetime | None = None,
    stall_threshold_seconds: int = DEFAULT_DELIVERY_PENDING_SECONDS,
) -> dict[str, object]:
    """Evaluate the delivery half of packet lifecycle progression.

    This is a narrow G40 helper for TDD and callers that need packet-level
    violation rows instead of the aggregate hygiene report.
    """
    now_utc = now or datetime.now(timezone.utc)
    stalled = tuple(
        _filter_delivery_pending(packets, now_utc, stall_threshold_seconds)
    )
    violations = tuple(
        DeliveryStallViolation(
            packet_id=str(packet.get("packet_id") or ""),
            posted_at=str(packet.get("posted_at") or ""),
            threshold_seconds=stall_threshold_seconds,
            route_kind=str(packet.get("kind") or ""),
        ).to_dict()
        for packet in stalled
    )
    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": f"{COMMAND}.evaluate_delivery_stall",
        "ok": not violations,
        "stall_threshold_seconds": stall_threshold_seconds,
        "delivery_stall_count": len(violations),
        "violations": list(violations),
    }


def build_report(
    *,
    packets: Sequence[Mapping[str, object]] | None = None,
    events: Sequence[Mapping[str, object]] | None = None,
    review_state_path: Path | None = None,
    event_log_path: Path | None = None,
    current_row_id: str = DEFAULT_ROW_ID,
    hygiene_window_seconds: int = DEFAULT_HYGIENE_WINDOW_SECONDS,
    delivery_pending_seconds: int = DEFAULT_DELIVERY_PENDING_SECONDS,
    materialization_interval_seconds: int = DEFAULT_MATERIALIZATION_INTERVAL_SECONDS,
    expire_packets_limit_default: int = DEFAULT_EXPIRE_PACKETS_LIMIT,
    include_stale: bool = False,
    now: datetime | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    checked_surfaces: list[str] = []
    if packets is None:
        review_path = review_state_path or _default_review_state_path()
        checked_surfaces.append(str(review_path))
        packets = _packets_from_review_state(review_path, warnings)
    if events is None:
        event_path = event_log_path or _default_event_log_path()
        checked_surfaces.append(str(event_path))
        events = tuple(_iter_jsonl(event_path, warnings=warnings))
    now_utc = now or datetime.now(timezone.utc)

    failures: list[HygieneViolation] = []
    pending_packets = tuple(_filter_pending(packets))
    pending_total = len(pending_packets)
    past_expires = tuple(_filter_past_expires(pending_packets, now_utc))
    stale_in_window = tuple(_filter_older_than(pending_packets, now_utc, hygiene_window_seconds))
    delivery_pending = tuple(
        _filter_delivery_pending(pending_packets, now_utc, delivery_pending_seconds)
    )
    binding_missing = tuple(_filter_durable_binding_missing(stale_in_window))
    last_materialization = _last_materialization_timestamp(events)

    if not include_stale and stale_in_window:
        failures.append(
            HygieneViolation(
                rule_id=RULE_STALE_IN_DEFAULT_VIEW,
                detail=(
                    f"{len(stale_in_window)} pending packet(s) older than "
                    f"{hygiene_window_seconds}s visible in default view "
                    "without --include-stale opt-in"
                ),
                remediation=(
                    "Auto-archive past-hygiene-window pendings via "
                    "PacketExpiryMaterialization or hide them behind "
                    "--include-stale."
                ),
                evidence_packet_ids=_packet_ids(stale_in_window)[:10],
            )
        )

    if past_expires and not _materialization_is_recent(
        last_materialization, now_utc, materialization_interval_seconds
    ):
        failures.append(
            HygieneViolation(
                rule_id=RULE_NO_RECENT_MATERIALIZATION,
                detail=(
                    f"queue.stale_packet_count={len(past_expires)} "
                    "without PacketExpiryMaterialization receipt within "
                    f"{materialization_interval_seconds}s"
                ),
                remediation=(
                    "Run review-channel --action expire-packets and emit a "
                    "PacketExpiryMaterialization receipt."
                ),
                evidence_packet_ids=_packet_ids(past_expires)[:10],
            )
        )

    if delivery_pending:
        failures.append(
            HygieneViolation(
                rule_id=RULE_DELIVERY_PENDING,
                detail=(
                    f"{len(delivery_pending)} pending packet(s) with "
                    f"delivery_emitted_at_utc=None older than "
                    f"{delivery_pending_seconds}s on sanctioned routes"
                ),
                remediation=(
                    "Advance the delivery half of the packet lifecycle or "
                    "emit a typed blocker."
                ),
                evidence_packet_ids=_packet_ids(delivery_pending)[:10],
            )
        )

    if binding_missing:
        failures.append(
            HygieneViolation(
                rule_id=RULE_DURABLE_BINDING_MISSING,
                detail=(
                    f"{len(binding_missing)} pending packet(s) older than "
                    "hygiene window with no PlanRow target, finding, defer/"
                    "reject/supersede/closure receipt, or operator-bound TTL"
                ),
                remediation=(
                    "Bind to a PlanRow, finding, or operator TTL — or "
                    "dispatch supersede/dismiss."
                ),
                evidence_packet_ids=_packet_ids(binding_missing)[:10],
            )
        )

    if past_expires and expire_packets_limit_default < len(past_expires):
        failures.append(
            HygieneViolation(
                rule_id=RULE_SWEEP_CANNOT_DRAIN,
                detail=(
                    f"expire-packets default limit={expire_packets_limit_default} "
                    f"< past_expires_count={len(past_expires)}; "
                    "single sweep cannot drain backlog"
                ),
                remediation=(
                    "Raise the default sweep limit via repo-pack policy or "
                    "shard sweeps with a scheduled invocation."
                ),
            )
        )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not failures,
        "display_text": DISPLAY_TEXT if failures else "",
        "current_plan_row_id": current_row_id,
        "live_pending_total": pending_total,
        "stale_within_hygiene_window_count": len(stale_in_window),
        "past_expires_count": len(past_expires),
        "delivery_pending_count": len(delivery_pending),
        "durable_binding_missing_count": len(binding_missing),
        "last_expire_packets_at_utc": last_materialization or "",
        "hygiene_window_seconds": hygiene_window_seconds,
        "checked_surfaces": checked_surfaces,
        "failures": [violation.to_dict() for violation in failures],
        "warnings": warnings,
    }


def _filter_pending(packets: Iterable[Mapping[str, object]]) -> Iterable[Mapping[str, object]]:
    for packet in packets:
        status = str(packet.get("status") or packet.get("lifecycle_current_state") or "").strip().lower()
        if status in {"pending", "delivered", "task_progress", "task_started", ""}:
            terminal = str(packet.get("disposition_state") or "").strip().lower()
            if terminal in {"archived", "applied", "dismissed", "absorbed", "expired", "superseded"}:
                continue
            yield packet


def _filter_past_expires(
    packets: Iterable[Mapping[str, object]], now: datetime
) -> Iterable[Mapping[str, object]]:
    for packet in packets:
        expires = _parse_utc(str(packet.get("expires_at_utc") or ""))
        if expires is None:
            continue
        if expires <= now:
            yield packet


def _filter_older_than(
    packets: Iterable[Mapping[str, object]], now: datetime, window_seconds: int
) -> Iterable[Mapping[str, object]]:
    threshold = now.timestamp() - window_seconds
    for packet in packets:
        posted = _parse_utc(str(packet.get("posted_at") or packet.get("timestamp_utc") or ""))
        if posted is None:
            continue
        if posted.timestamp() <= threshold:
            yield packet


def _filter_delivery_pending(
    packets: Iterable[Mapping[str, object]], now: datetime, seconds: int
) -> Iterable[Mapping[str, object]]:
    threshold = now.timestamp() - seconds
    for packet in packets:
        delivery = str(packet.get("delivery_emitted_at_utc") or "").strip()
        if delivery:
            continue
        kind = str(packet.get("kind") or "").strip().lower()
        if kind and kind not in SANCTIONED_ROUTE_KINDS:
            continue
        posted = _parse_utc(str(packet.get("posted_at") or ""))
        if posted is None:
            continue
        if posted.timestamp() <= threshold:
            yield packet


def _filter_durable_binding_missing(
    packets: Iterable[Mapping[str, object]],
) -> Iterable[Mapping[str, object]]:
    for packet in packets:
        if _has_durable_binding(packet):
            continue
        yield packet


def _has_durable_binding(packet: Mapping[str, object]) -> bool:
    if str(packet.get("target_ref") or "").strip():
        return True
    if str(packet.get("plan_id") or "").strip():
        return True
    if str(packet.get("absorbed_at_utc") or "").strip():
        return True
    if str(packet.get("dismissed_at_utc") or "").strip():
        return True
    if str(packet.get("apply_pending_after_execution_at_utc") or "").strip():
        return True
    if str(packet.get("operator_bound_ttl") or "").strip():
        return True
    binding = packet.get("packet_creation_binding")
    if isinstance(binding, Mapping):
        status = str(binding.get("status") or "").strip().lower()
        if status and status not in {"unbound", ""}:
            return True
    return False


def _last_materialization_timestamp(
    events: Iterable[Mapping[str, object]],
) -> str | None:
    latest = ""
    for event in events:
        if str(event.get("event_type") or "").strip() != PACKET_EXPIRED_EVENT_TYPE:
            continue
        ts = str(event.get("timestamp_utc") or "").strip()
        if ts and ts > latest:
            latest = ts
    return latest or None


def _materialization_is_recent(
    last_materialization: str | None, now: datetime, interval_seconds: int
) -> bool:
    if not last_materialization:
        return False
    parsed = _parse_utc(last_materialization)
    if parsed is None:
        return False
    return parsed.timestamp() >= now.timestamp() - interval_seconds


def _packet_ids(packets: Iterable[Mapping[str, object]]) -> tuple[str, ...]:
    return tuple(str(p.get("packet_id") or "") for p in packets)


def _default_review_state_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/projections/latest/review_state.json"


def _default_event_log_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/events/trace.ndjson"


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- current_plan_row_id: `{report.get('current_plan_row_id')}`")
    lines.append(f"- live_pending_total: {report.get('live_pending_total')}")
    lines.append(f"- stale_within_hygiene_window_count: {report.get('stale_within_hygiene_window_count')}")
    lines.append(f"- past_expires_count: {report.get('past_expires_count')}")
    lines.append(f"- delivery_pending_count: {report.get('delivery_pending_count')}")
    lines.append(f"- durable_binding_missing_count: {report.get('durable_binding_missing_count')}")
    lines.append(f"- last_expire_packets_at_utc: `{report.get('last_expire_packets_at_utc')}`")
    lines.append(f"- hygiene_window_seconds: {report.get('hygiene_window_seconds')}")
    failures = report.get("failures")
    if isinstance(failures, Sequence) and not isinstance(failures, (str, bytes)) and failures:
        lines.extend(("", "## Failures", ""))
        for violation in failures:
            if not isinstance(violation, Mapping):
                continue
            lines.append(f"- {violation.get('rule_id')}: {violation.get('detail')}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--review-state-path",
        type=Path,
        default=_default_review_state_path(),
    )
    parser.add_argument(
        "--event-log-path",
        type=Path,
        default=_default_event_log_path(),
    )
    parser.add_argument("--row-id", default=DEFAULT_ROW_ID)
    parser.add_argument(
        "--hygiene-window-seconds",
        type=int,
        default=DEFAULT_HYGIENE_WINDOW_SECONDS,
    )
    parser.add_argument(
        "--delivery-pending-seconds",
        type=int,
        default=DEFAULT_DELIVERY_PENDING_SECONDS,
    )
    parser.add_argument(
        "--materialization-interval-seconds",
        type=int,
        default=DEFAULT_MATERIALIZATION_INTERVAL_SECONDS,
    )
    parser.add_argument(
        "--expire-packets-limit-default",
        type=int,
        default=DEFAULT_EXPIRE_PACKETS_LIMIT,
    )
    parser.add_argument("--include-stale", action="store_true")
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            review_state_path=args.review_state_path,
            event_log_path=args.event_log_path,
            current_row_id=args.row_id,
            hygiene_window_seconds=args.hygiene_window_seconds,
            delivery_pending_seconds=args.delivery_pending_seconds,
            materialization_interval_seconds=args.materialization_interval_seconds,
            expire_packets_limit_default=args.expire_packets_limit_default,
            include_stale=args.include_stale,
        )
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
