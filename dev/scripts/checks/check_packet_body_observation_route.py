#!/usr/bin/env python3
"""Fail when packet body is observable in projection without a route-matched body_observation event."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _iter_jsonl,
        normalized_packet_ids as _normalized_packet_ids,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _iter_jsonl,
        normalized_packet_ids as _normalized_packet_ids,
        utc_timestamp,
    )


COMMAND = "check_packet_body_observation_route"
CONTRACT_ID = "PacketBodyObservationRouteGuard"

REASON_ROUTE_MISSING = "packet_body_observation_route_missing"
REASON_CROSS_ROLE_SPOOF = "packet_body_observation_cross_role_spoofing"
REASON_CROSS_SESSION_SPOOF = "packet_body_observation_cross_session_spoofing"

DISPLAY_TEXT = (
    "Packet body observation route violation. A packet body is visible in "
    "projection without a target-route-matched body_observation event, or a "
    "reviewer/orchestrator replayed an implementer body-open."
)

PACKET_POSTED_EVENT_TYPE = "packet_posted"
PACKET_BODY_OBSERVED_EVENT_TYPE = "packet_body_observed"


@dataclass(frozen=True, slots=True)
class PacketBodyRouteViolation:
    packet_id: str
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    events: Sequence[Mapping[str, object]] | None = None,
    event_log_path: Path | None = None,
    row_id_filter: str = "",
    packet_ids: Sequence[str] = (),
) -> dict[str, object]:
    warnings: list[str] = []
    source_path: Path | None = None
    if events is None:
        source_path = event_log_path or _default_event_log_path()
        events = tuple(_iter_jsonl(source_path, warnings=warnings))
    else:
        events = tuple(events)

    packets, observations = _index_events(events)
    packet_id_filter = _normalized_packet_ids(packet_ids)
    violations: list[PacketBodyRouteViolation] = []
    checked_packet_ids: list[str] = []
    checked_packet_count = 0
    for packet_id, packet in packets.items():
        if packet_id_filter and packet_id not in packet_id_filter:
            continue
        if row_id_filter and not _packet_matches_row(packet, row_id_filter):
            continue
        checked_packet_ids.append(packet_id)
        checked_packet_count += 1
        packet_obs = observations.get(packet_id, ())
        violations.extend(
            _violations_for_packet(packet=packet, observations=packet_obs)
        )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "event_log_path": str(source_path) if source_path is not None else "",
        "row_id_filter": row_id_filter,
        "packet_ids": list(packet_id_filter),
        "checked_packet_ids": checked_packet_ids,
        "checked_packet_count": checked_packet_count,
        "observation_event_count": sum(len(obs) for obs in observations.values()),
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def _violations_for_packet(
    *,
    packet: Mapping[str, object],
    observations: Sequence[Mapping[str, object]],
) -> tuple[PacketBodyRouteViolation, ...]:
    violations: list[PacketBodyRouteViolation] = []
    packet_id = str(packet.get("packet_id") or "").strip()
    body = str(packet.get("body") or "")
    if not body:
        return ()
    target_role = str(packet.get("target_role") or "").strip()
    target_session = str(packet.get("target_session_id") or "").strip()
    if not target_role and not target_session:
        return ()

    route_matched = False
    for event in observations:
        observed_role = str(event.get("body_observed_role") or "").strip()
        observed_session = str(event.get("body_observed_session_id") or "").strip()
        if target_role and observed_role and observed_role != target_role:
            violations.append(
                PacketBodyRouteViolation(
                    packet_id=packet_id,
                    reason=REASON_CROSS_ROLE_SPOOF,
                    detail=(
                        f"packet target_role={target_role!r}; "
                        f"body_observed_role={observed_role!r}; "
                        f"event_id={event.get('event_id')!r}"
                    ),
                    remediation=(
                        "Body-open must be performed by the packet's target role. "
                        "Reviewer/orchestrator cannot satisfy an implementer body-open."
                    ),
                )
            )
            continue
        if (
            target_session
            and observed_session
            and observed_session != target_session
        ):
            violations.append(
                PacketBodyRouteViolation(
                    packet_id=packet_id,
                    reason=REASON_CROSS_SESSION_SPOOF,
                    detail=(
                        f"packet target_session_id={target_session!r}; "
                        f"body_observed_session_id={observed_session!r}; "
                        f"event_id={event.get('event_id')!r}"
                    ),
                    remediation=(
                        "Body-open must be performed by the packet's target session. "
                        "Cross-session observation does not satisfy the body_observation route."
                    ),
                )
            )
            continue
        role_ok = (not target_role) or (observed_role == target_role)
        session_ok = (not target_session) or (observed_session == target_session)
        if role_ok and session_ok:
            route_matched = True

    if not route_matched:
        violations.append(
            PacketBodyRouteViolation(
                packet_id=packet_id,
                reason=REASON_ROUTE_MISSING,
                detail=(
                    f"packet body is visible (len={len(body)}) but no "
                    f"packet_body_observed event matches "
                    f"target_role={target_role!r} target_session_id={target_session!r}"
                ),
                remediation=(
                    "Record a PacketBodyObservation event from the target provider/session "
                    "inbox/show path before the packet can be treated as observed."
                ),
            )
        )
    return tuple(violations)


def _index_events(
    events: Sequence[Mapping[str, object]],
) -> tuple[dict[str, Mapping[str, object]], dict[str, tuple[Mapping[str, object], ...]]]:
    packets: dict[str, Mapping[str, object]] = {}
    observations: dict[str, list[Mapping[str, object]]] = {}
    for event in events:
        event_type = str(event.get("event_type") or "").strip()
        packet_id = str(event.get("packet_id") or "").strip()
        if not packet_id:
            continue
        if event_type == PACKET_POSTED_EVENT_TYPE:
            packets.setdefault(packet_id, event)
        elif event_type == PACKET_BODY_OBSERVED_EVENT_TYPE:
            observations.setdefault(packet_id, []).append(event)
    return packets, {pid: tuple(events) for pid, events in observations.items()}


def _packet_matches_row(packet: Mapping[str, object], row_id_filter: str) -> bool:
    target_ref = str(packet.get("target_ref") or "").strip()
    if not target_ref:
        return False
    if row_id_filter in target_ref:
        return True
    plan_id = str(packet.get("plan_id") or "").strip()
    return row_id_filter == plan_id


def _default_event_log_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/events/trace.ndjson"


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- checked_packet_count: {report.get('checked_packet_count')}")
    lines.append(f"- observation_event_count: {report.get('observation_event_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("row_id_filter"):
        lines.append(f"- row_id_filter: `{report.get('row_id_filter')}`")
    packet_ids = report.get("packet_ids")
    if isinstance(packet_ids, Sequence) and not isinstance(packet_ids, (str, bytes)) and packet_ids:
        rendered = ", ".join(f"`{packet_id}`" for packet_id in packet_ids)
        lines.append(f"- packet_ids: {rendered}")
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('packet_id')}: {violation.get('reason')} "
                f"({violation.get('detail')})"
            )
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)) and warnings:
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event-log-path",
        type=Path,
        default=_default_event_log_path(),
        help="Review-channel event log (NDJSON).",
    )
    parser.add_argument(
        "--row-id",
        default="",
        help="If set, only check packets whose target_ref or plan_id matches this row id.",
    )
    parser.add_argument(
        "--packet-id",
        action="append",
        default=[],
        help="Limit validation to one packet id. Repeat for multiple active packets.",
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            event_log_path=args.event_log_path,
            row_id_filter=args.row_id,
            packet_ids=tuple(args.packet_id),
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
