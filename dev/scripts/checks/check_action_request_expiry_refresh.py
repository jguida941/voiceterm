#!/usr/bin/env python3
"""Fail when a selected action_request expires before target-session body-open/ack
and no refresh packet, replacement packet, or typed blocker covers the gap.

G24 Action Request Expiry Refresh Guard.

Acceptance:

- If the selected action_request expires before target-session body-open or ack,
  ``develop next`` / sync-status must stop selecting the expired packet.
- The system must require either a fresh replacement packet or a typed blocker
  that says why replacement is impossible.
- Refresh packets must reference the expired packet, the current plan row, and
  the same role/session target when the old target is still valid.
- A stale selected action_request must not prevent the reviewer/orchestrator
  lane from recording a newer current-row finding or replacement request as
  actionable typed evidence; an attempted-action receipt becomes current-row
  blocker evidence and the selector must stop treating the stale packet as the
  only active instruction.
"""

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
        normalized_packet_ids as _normalized_packet_ids,
        packets_from_review_state as _packets_from_review_state,
        parse_utc as _parse_utc,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _iter_jsonl,
        normalized_packet_ids as _normalized_packet_ids,
        packets_from_review_state as _packets_from_review_state,
        parse_utc as _parse_utc,
        utc_timestamp,
    )


COMMAND = "check_action_request_expiry_refresh"
CONTRACT_ID = "ActionRequestExpiryRefreshGuard"

DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"

RULE_SELECTED_EXPIRED_NO_REPLACEMENT = (
    "selected_action_request_expired_without_refresh_or_blocker"
)
RULE_REFRESH_MISSING_EXPIRED_REF = (
    "refresh_packet_missing_expired_packet_reference"
)
RULE_REFRESH_MISSING_PLAN_ROW = "refresh_packet_missing_plan_row_reference"
RULE_REFRESH_MISMATCHED_TARGET = "refresh_packet_mismatched_role_session_target"
RULE_STALE_BLOCKS_NEWER_FINDING = (
    "expired_selected_packet_blocks_newer_current_row_evidence"
)

DISPLAY_TEXT = (
    "Action request expiry refresh violation. A selected action_request expired "
    "before body-open/ack with no fresh refresh packet, replacement packet, or "
    "typed blocker. Selectors must stop treating the stale packet as the only "
    "active instruction."
)

PACKET_KIND_ACTION_REQUEST = "action_request"
PACKET_KIND_REFRESH_PACKETS = frozenset(
    {
        "action_request_refresh",
        "action_request",
    }
)
PACKET_KIND_BLOCKER_PACKETS = frozenset(
    {
        "task_blocked",
        "blocker",
        "finding",
        "decision",
    }
)
PACKET_KIND_NEWER_EVIDENCE = frozenset(
    {
        "finding",
        "action_request",
        "action_request_refresh",
        "task_blocked",
        "decision",
    }
)

BODY_OPEN_EVENT_TYPES = frozenset(
    {
        "packet_body_observed",
        "packet_acknowledged",
        "packet_body_open",
        "packet_ack",
    }
)


@dataclass(frozen=True, slots=True)
class ExpiryRefreshViolation:
    rule_id: str
    packet_id: str
    detail: str
    remediation: str
    evidence_packet_ids: tuple[str, ...] = ()


def build_report(
    *,
    packets: Sequence[Mapping[str, object]] | None = None,
    events: Sequence[Mapping[str, object]] | None = None,
    review_state_path: Path | None = None,
    event_log_path: Path | None = None,
    current_row_id: str = DEFAULT_ROW_ID,
    packet_ids: Sequence[str] = (),
    now: datetime | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    checked_surfaces: list[str] = []
    if packets is None:
        review_path = review_state_path or _default_review_state_path()
        checked_surfaces.append(str(review_path))
        packets = _packets_from_review_state(review_path, warnings)
    else:
        packets = tuple(packets)
    if events is None:
        event_path = event_log_path or _default_event_log_path()
        checked_surfaces.append(str(event_path))
        events = tuple(_iter_jsonl(event_path, warnings=warnings))
    else:
        events = tuple(events)

    now_utc = now or datetime.now(timezone.utc)
    packet_id_filter = _normalized_packet_ids(packet_ids)
    body_open_packet_ids = _body_open_packet_ids(events)
    packets_by_id = {
        str(p.get("packet_id") or "").strip(): p
        for p in packets
        if str(p.get("packet_id") or "").strip()
    }

    selected_action_requests = tuple(
        _filter_selected_action_requests(packets)
    )
    violations: list[ExpiryRefreshViolation] = []
    checked_packet_ids: list[str] = []

    for packet in selected_action_requests:
        packet_id = str(packet.get("packet_id") or "").strip()
        if not packet_id:
            continue
        if packet_id_filter and packet_id not in packet_id_filter:
            continue
        checked_packet_ids.append(packet_id)
        expires = _parse_utc(str(packet.get("expires_at_utc") or ""))
        if expires is None or expires > now_utc:
            continue
        if packet_id in body_open_packet_ids:
            continue
        refresh_packets = tuple(
            _find_refresh_packets(
                packets=packets,
                expired_packet_id=packet_id,
                current_row_id=current_row_id,
            )
        )
        blocker_packets = tuple(
            _find_blocker_packets(
                packets=packets,
                expired_packet_id=packet_id,
            )
        )
        candidate_refresh_packets = tuple(
            _find_candidate_refresh_packets(
                packets=packets,
                expired_packet=packet,
            )
        )
        newer_evidence = tuple(
            _find_newer_current_row_evidence(
                packets=packets,
                expired_packet=packet,
                current_row_id=current_row_id,
                now=now_utc,
            )
        )
        if not refresh_packets and not blocker_packets:
            violations.append(
                ExpiryRefreshViolation(
                    rule_id=RULE_SELECTED_EXPIRED_NO_REPLACEMENT,
                    packet_id=packet_id,
                    detail=(
                        f"selected action_request packet_id={packet_id!r} "
                        f"expired at {packet.get('expires_at_utc')!r} without "
                        "body-open/ack from the target session and no valid "
                        "refresh packet or typed blocker packet covers the gap"
                    ),
                    remediation=(
                        "Post a fresh action_request_refresh packet that "
                        "references the expired packet + current plan row + "
                        "same role/session target, or post a typed blocker "
                        "packet explaining why refresh is impossible."
                    ),
                )
            )
        # Inspect candidate refresh-kind packets (whether or not they linked).
        # Validated refreshes are checked for plan-row + target-match
        # consistency; unlinked candidates raise RULE_REFRESH_MISSING_EXPIRED_REF.
        inspection_pool = tuple(refresh_packets) + tuple(
            r
            for r in candidate_refresh_packets
            if r not in refresh_packets
        )
        for refresh in inspection_pool:
            refresh_id = str(refresh.get("packet_id") or "").strip()
            if not _refresh_references_expired_packet(refresh, packet_id):
                violations.append(
                    ExpiryRefreshViolation(
                        rule_id=RULE_REFRESH_MISSING_EXPIRED_REF,
                        packet_id=refresh_id,
                        detail=(
                            f"refresh packet_id={refresh_id!r} does not "
                            f"reference expired packet_id={packet_id!r} via "
                            "refresh_of_packet_id, supersedes_packet_id, or "
                            "expired_packet_ref"
                        ),
                        remediation=(
                            "Set refresh_of_packet_id or supersedes_packet_id "
                            "on the refresh packet to the expired packet id."
                        ),
                        evidence_packet_ids=(packet_id,),
                    )
                )
            if not _refresh_references_plan_row(refresh, current_row_id):
                violations.append(
                    ExpiryRefreshViolation(
                        rule_id=RULE_REFRESH_MISSING_PLAN_ROW,
                        packet_id=refresh_id,
                        detail=(
                            f"refresh packet_id={refresh_id!r} does not "
                            f"reference current plan row "
                            f"{current_row_id!r} via target_ref or plan_id"
                        ),
                        remediation=(
                            "Set target_ref/plan_id on the refresh packet to "
                            "the current plan row id so refresh authority is "
                            "rebound to the live row."
                        ),
                        evidence_packet_ids=(packet_id,),
                    )
                )
            if not _refresh_matches_target(refresh, packet):
                violations.append(
                    ExpiryRefreshViolation(
                        rule_id=RULE_REFRESH_MISMATCHED_TARGET,
                        packet_id=refresh_id,
                        detail=(
                            f"refresh packet_id={refresh_id!r} target_role="
                            f"{refresh.get('target_role')!r} target_session_id="
                            f"{refresh.get('target_session_id')!r} does not "
                            f"match expired packet target_role="
                            f"{packet.get('target_role')!r} target_session_id="
                            f"{packet.get('target_session_id')!r}"
                        ),
                        remediation=(
                            "When the old target is still valid, set the "
                            "refresh packet's target_role and target_session_id "
                            "to match the expired packet. If the target has "
                            "changed, post a typed blocker explaining the "
                            "retargeting decision."
                        ),
                        evidence_packet_ids=(packet_id,),
                    )
                )

    # Independent rule: newer current-row finding/replacement should not be
    # blocked by a stale selected action_request. If the selector still treats
    # an expired packet as the only active instruction when newer evidence
    # references the current row, surface that as a selector-stuck violation.
    # The rule only fires when no valid refresh/blocker packet has been posted;
    # if a refresh exists it already covers the gap and the selector should
    # release on the next reducer tick.
    for packet in selected_action_requests:
        packet_id = str(packet.get("packet_id") or "").strip()
        if packet_id_filter and packet_id not in packet_id_filter:
            continue
        if not packet_id:
            continue
        expires = _parse_utc(str(packet.get("expires_at_utc") or ""))
        if expires is None or expires > now_utc:
            continue
        if packet_id in body_open_packet_ids:
            continue
        if not _is_selected_only_active(packet):
            continue
        refresh_packets = tuple(
            _find_refresh_packets(
                packets=packets,
                expired_packet_id=packet_id,
                current_row_id=current_row_id,
            )
        )
        blocker_packets = tuple(
            _find_blocker_packets(
                packets=packets,
                expired_packet_id=packet_id,
            )
        )
        if refresh_packets or blocker_packets:
            continue
        newer_evidence = tuple(
            _find_newer_current_row_evidence(
                packets=packets,
                expired_packet=packet,
                current_row_id=current_row_id,
                now=now_utc,
            )
        )
        if not newer_evidence:
            continue
        violations.append(
            ExpiryRefreshViolation(
                rule_id=RULE_STALE_BLOCKS_NEWER_FINDING,
                packet_id=packet_id,
                detail=(
                    f"expired selected packet_id={packet_id!r} still marked "
                    "selected_only_active despite "
                    f"{len(newer_evidence)} newer current-row evidence "
                    "packet(s) (finding/replacement) for current_row="
                    f"{current_row_id!r}"
                ),
                remediation=(
                    "Selector must release the expired packet so the newer "
                    "current-row evidence becomes actionable; record an "
                    "attempted-action receipt as current-row blocker evidence "
                    "if body-open is blocked."
                ),
                evidence_packet_ids=tuple(
                    str(e.get("packet_id") or "") for e in newer_evidence
                ),
            )
        )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "current_plan_row_id": current_row_id,
        "selected_action_request_count": len(selected_action_requests),
        "checked_packet_ids": checked_packet_ids,
        "checked_packet_count": len(checked_packet_ids),
        "packet_ids": list(packet_id_filter),
        "body_open_packet_count": len(body_open_packet_ids),
        "checked_surfaces": checked_surfaces,
        "violation_count": len(violations),
        "violations": [asdict(violation) for violation in violations],
        "warnings": warnings,
    }


def _filter_selected_action_requests(
    packets: Iterable[Mapping[str, object]],
) -> Iterable[Mapping[str, object]]:
    for packet in packets:
        kind = str(packet.get("kind") or "").strip().lower()
        if kind != PACKET_KIND_ACTION_REQUEST:
            continue
        if not _packet_is_selected(packet):
            continue
        yield packet


def _packet_is_selected(packet: Mapping[str, object]) -> bool:
    selected = packet.get("selected_as_active_implementer_packet")
    if isinstance(selected, bool) and selected:
        return True
    selector_state = str(packet.get("selector_state") or "").strip().lower()
    if selector_state in {"selected", "active", "selected_only_active"}:
        return True
    selection = packet.get("selection")
    if isinstance(selection, Mapping):
        if str(selection.get("status") or "").strip().lower() in {
            "selected",
            "active",
        }:
            return True
    return False


def _is_selected_only_active(packet: Mapping[str, object]) -> bool:
    if str(packet.get("selector_state") or "").strip().lower() == (
        "selected_only_active"
    ):
        return True
    if packet.get("selected_only_active") is True:
        return True
    selection = packet.get("selection")
    if isinstance(selection, Mapping):
        if str(selection.get("status") or "").strip().lower() == (
            "selected_only_active"
        ):
            return True
    # Fall back: if the packet is selected and nothing else carries the
    # exclusive marker, treat plain selected as "only active" too.
    return _packet_is_selected(packet)


def _body_open_packet_ids(
    events: Iterable[Mapping[str, object]],
) -> frozenset[str]:
    ids: set[str] = set()
    for event in events:
        event_type = str(event.get("event_type") or "").strip()
        if event_type not in BODY_OPEN_EVENT_TYPES:
            continue
        packet_id = str(event.get("packet_id") or "").strip()
        if packet_id:
            ids.add(packet_id)
    return frozenset(ids)


def _find_refresh_packets(
    *,
    packets: Iterable[Mapping[str, object]],
    expired_packet_id: str,
    current_row_id: str,
) -> Iterable[Mapping[str, object]]:
    for packet in packets:
        kind = str(packet.get("kind") or "").strip().lower()
        if kind not in PACKET_KIND_REFRESH_PACKETS:
            continue
        if str(packet.get("packet_id") or "").strip() == expired_packet_id:
            continue
        if _refresh_references_expired_packet(packet, expired_packet_id):
            yield packet


def _find_candidate_refresh_packets(
    *,
    packets: Iterable[Mapping[str, object]],
    expired_packet: Mapping[str, object],
) -> Iterable[Mapping[str, object]]:
    """Return refresh-shaped packets posted after the expired packet.

    A candidate refresh is any ``action_request_refresh`` (or later
    ``action_request``) packet posted after the expired packet that does not
    itself match the expired packet id. Candidates that fail to reference the
    expired packet, current row, or matching target are surfaced as refresh
    hygiene violations even when ``_find_refresh_packets`` rejects them.
    """
    expired_packet_id = str(expired_packet.get("packet_id") or "").strip()
    expired_posted = _parse_utc(str(expired_packet.get("posted_at") or ""))
    for packet in packets:
        kind = str(packet.get("kind") or "").strip().lower()
        if kind not in PACKET_KIND_REFRESH_PACKETS:
            continue
        if str(packet.get("packet_id") or "").strip() == expired_packet_id:
            continue
        if kind == PACKET_KIND_ACTION_REQUEST:
            # Only treat newer action_request packets as candidate refreshes
            # when they appear after the expired one (to avoid double-counting
            # other unrelated action requests).
            posted = _parse_utc(str(packet.get("posted_at") or ""))
            if (
                expired_posted is not None
                and posted is not None
                and posted <= expired_posted
            ):
                continue
        yield packet


def _find_blocker_packets(
    *,
    packets: Iterable[Mapping[str, object]],
    expired_packet_id: str,
) -> Iterable[Mapping[str, object]]:
    for packet in packets:
        kind = str(packet.get("kind") or "").strip().lower()
        if kind not in PACKET_KIND_BLOCKER_PACKETS:
            continue
        if _refresh_references_expired_packet(packet, expired_packet_id):
            yield packet


def _find_newer_current_row_evidence(
    *,
    packets: Iterable[Mapping[str, object]],
    expired_packet: Mapping[str, object],
    current_row_id: str,
    now: datetime,
) -> Iterable[Mapping[str, object]]:
    expired_packet_id = str(expired_packet.get("packet_id") or "").strip()
    expired_posted = _parse_utc(str(expired_packet.get("posted_at") or ""))
    for packet in packets:
        if str(packet.get("packet_id") or "").strip() == expired_packet_id:
            continue
        kind = str(packet.get("kind") or "").strip().lower()
        if kind not in PACKET_KIND_NEWER_EVIDENCE:
            continue
        if not _refresh_references_plan_row(packet, current_row_id):
            continue
        posted = _parse_utc(str(packet.get("posted_at") or ""))
        if expired_posted is not None and posted is not None and posted <= expired_posted:
            continue
        yield packet


def _refresh_references_expired_packet(
    refresh: Mapping[str, object], expired_packet_id: str
) -> bool:
    if not expired_packet_id:
        return False
    candidates = (
        str(refresh.get("refresh_of_packet_id") or "").strip(),
        str(refresh.get("supersedes_packet_id") or "").strip(),
        str(refresh.get("expired_packet_ref") or "").strip(),
        str(refresh.get("expired_packet_id") or "").strip(),
    )
    if expired_packet_id in candidates:
        return True
    refs = refresh.get("references")
    if isinstance(refs, (list, tuple)):
        for ref in refs:
            if isinstance(ref, Mapping):
                value = str(ref.get("packet_id") or "").strip()
                kind = str(ref.get("kind") or "").strip().lower()
                if value == expired_packet_id and kind in {
                    "refresh_of",
                    "supersedes",
                    "expired_packet_ref",
                    "",
                }:
                    return True
            elif isinstance(ref, str) and ref.strip() == expired_packet_id:
                return True
    return False


def _refresh_references_plan_row(
    refresh: Mapping[str, object], current_row_id: str
) -> bool:
    if not current_row_id:
        return False
    target_ref = str(refresh.get("target_ref") or "").strip()
    if current_row_id in target_ref:
        return True
    plan_id = str(refresh.get("plan_id") or "").strip()
    return plan_id == current_row_id


def _refresh_matches_target(
    refresh: Mapping[str, object], expired: Mapping[str, object]
) -> bool:
    expired_role = str(expired.get("target_role") or "").strip()
    expired_session = str(expired.get("target_session_id") or "").strip()
    if not expired_role and not expired_session:
        return True
    refresh_role = str(refresh.get("target_role") or "").strip()
    refresh_session = str(refresh.get("target_session_id") or "").strip()
    role_ok = (not expired_role) or refresh_role == expired_role
    session_ok = (not expired_session) or refresh_session == expired_session
    return role_ok and session_ok


def _default_review_state_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/projections/latest/review_state.json"


def _default_event_log_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/events/trace.ndjson"


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- current_plan_row_id: `{report.get('current_plan_row_id')}`")
    lines.append(
        f"- selected_action_request_count: {report.get('selected_action_request_count')}"
    )
    lines.append(f"- checked_packet_count: {report.get('checked_packet_count')}")
    lines.append(f"- body_open_packet_count: {report.get('body_open_packet_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    packet_ids = report.get("packet_ids")
    if (
        isinstance(packet_ids, Sequence)
        and not isinstance(packet_ids, (str, bytes))
        and packet_ids
    ):
        rendered = ", ".join(f"`{packet_id}`" for packet_id in packet_ids)
        lines.append(f"- packet_ids: {rendered}")
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
    violations = report.get("violations")
    if (
        isinstance(violations, Sequence)
        and not isinstance(violations, (str, bytes))
        and violations
    ):
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('packet_id')}: {violation.get('rule_id')} "
                f"({violation.get('detail')})"
            )
    warnings = report.get("warnings")
    if (
        isinstance(warnings, Sequence)
        and not isinstance(warnings, (str, bytes))
        and warnings
    ):
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--review-state-path",
        type=Path,
        default=_default_review_state_path(),
        help="Review-channel projection state (JSON).",
    )
    parser.add_argument(
        "--event-log-path",
        type=Path,
        default=_default_event_log_path(),
        help="Review-channel event log (NDJSON).",
    )
    parser.add_argument(
        "--row-id",
        default=DEFAULT_ROW_ID,
        help="Current plan row id used for refresh/newer-evidence binding.",
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
            review_state_path=args.review_state_path,
            event_log_path=args.event_log_path,
            current_row_id=args.row_id,
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
