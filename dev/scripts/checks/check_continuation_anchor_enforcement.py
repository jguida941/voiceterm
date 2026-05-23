#!/usr/bin/env python3
"""Fail when a live ``continuation_anchor`` for the current row is not enforced
as runtime stop protection.

G27 Continuation Anchor Enforcement And Peer Steady-State Guard.

Acceptance:

- A live ``continuation_anchor`` for the current row must prevent the reviewer
  lane from emitting final completion / idle / ended state until the anchor is
  consumed, released by a ``stop_anchor``, or converted into a typed blocker.
- Session-scoped anchors must fail visibly when the target session id is stale.
  The route must refresh the anchor for the live reviewer session OR promote a
  plan-scoped / role-scoped anchor that survives session replacement.
- If startup/session authority reports ``reviewer_mode=tools_only``,
  ``observed_control_topology=no_live_agents``, or ``safe_to_continue=false``
  while a current-row continuation anchor is still pending, the controller must
  emit a current-row blocker such as ``continuation_anchor_not_enforced``.
- A peer loop that reports "no new packets" while the peer inbox still contains
  a current-row pending packet (e.g. ``rev_pkt_4821``) must not be treated as a
  healthy steady state. It must surface as
  ``peer_steady_state_with_pending_current_row_packet`` and route the next
  supported lifecycle transition.
- Trace-only liveness expiry events such as ``participant_liveness_expired``
  must either wake / route the responsible lane OR create blocker evidence tied
  to the current row, not be the only output.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
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


COMMAND = "check_continuation_anchor_enforcement"
CONTRACT_ID = "ContinuationAnchorEnforcementGuard"

DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"

RULE_FINAL_COMPLETION_WITH_LIVE_ANCHOR = (
    "final_completion_emitted_while_continuation_anchor_live"
)
RULE_REVIEWER_IDLE_WITH_LIVE_ANCHOR = (
    "reviewer_idle_or_ended_while_continuation_anchor_live"
)
RULE_SESSION_SCOPED_ANCHOR_STALE_SESSION = (
    "session_scoped_anchor_target_session_stale_without_refresh_or_promotion"
)
RULE_STARTUP_AUTHORITY_NOT_ENFORCED = (
    "continuation_anchor_not_enforced"
)
RULE_PEER_STEADY_STATE_WITH_PENDING_PACKET = (
    "peer_steady_state_with_pending_current_row_packet"
)
RULE_TRACE_ONLY_LIVENESS_EXPIRY = (
    "trace_only_liveness_expiry_without_wake_or_blocker"
)

DISPLAY_TEXT = (
    "Continuation anchor enforcement violation. A live current-row "
    "continuation_anchor must block final completion/idle, fail visibly on "
    "stale session scope, become a typed blocker when startup/session "
    "authority degrades, surface pending peer packets, and route liveness "
    "expiry to a lane wake or current-row blocker."
)

ANCHOR_KIND_CONTINUATION = "continuation_anchor"
ANCHOR_KIND_STOP = "stop_anchor"

BLOCKER_KINDS = frozenset(
    {
        "task_blocked",
        "blocker",
        "finding",
        "decision",
    }
)

PEER_STEADY_STATE_EVENT_TYPES = frozenset(
    {
        "peer_steady_state",
        "review_channel_peer_steady_state",
        "no_new_packets",
    }
)

LIVENESS_EXPIRY_EVENT_TYPES = frozenset({"participant_liveness_expired"})

LANE_WAKE_EVENT_TYPES = frozenset(
    {
        "lane_wake",
        "lane_woken",
        "session_wake_requested",
        "agent_loop_resume",
        "participant_relaunch_requested",
    }
)

REVIEWER_TERMINAL_STATES = frozenset(
    {
        "final_completion",
        "task_complete",
        "completed",
        "idle",
        "ended",
        "session_ended",
        "no_more_work",
    }
)

REVIEWER_DEGRADED_MODES = frozenset(
    {
        "tools_only",
        "no_live_agents",
    }
)


@dataclass(frozen=True, slots=True)
class AnchorViolation:
    rule_id: str
    anchor_packet_id: str
    detail: str
    remediation: str
    evidence_packet_ids: tuple[str, ...] = ()
    evidence_event_ids: tuple[str, ...] = ()
    target_role: str = ""
    target_session_id: str = ""
    target_scope: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "anchor_packet_id": self.anchor_packet_id,
            "detail": self.detail,
            "remediation": self.remediation,
            "evidence_packet_ids": list(self.evidence_packet_ids),
            "evidence_event_ids": list(self.evidence_event_ids),
            "target_role": self.target_role,
            "target_session_id": self.target_session_id,
            "target_scope": self.target_scope,
        }


def build_report(
    *,
    packets: Sequence[Mapping[str, object]] | None = None,
    events: Sequence[Mapping[str, object]] | None = None,
    startup_authority: Mapping[str, object] | None = None,
    review_state_path: Path | None = None,
    event_log_path: Path | None = None,
    current_row_id: str = DEFAULT_ROW_ID,
    live_reviewer_session_ids: Sequence[str] = (),
    live_reviewer_role: str = "reviewer",
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
    live_sessions = frozenset(s for s in live_reviewer_session_ids if s)

    live_anchors = tuple(
        _live_current_row_anchors(packets, current_row_id, now_utc)
    )
    stop_anchors_by_target = _index_stop_anchors(packets, current_row_id)
    blockers_by_anchor = _index_blockers_by_anchor(packets)

    violations: list[AnchorViolation] = []

    # Rule 1+2: final completion or reviewer idle/ended emitted while a live
    # current-row continuation anchor still exists, with no covering blocker.
    reviewer_terminal_events = tuple(
        _filter_reviewer_terminal_events(events)
    )
    for anchor in live_anchors:
        if _anchor_released_by_stop(anchor, stop_anchors_by_target):
            continue
        if _anchor_has_typed_blocker(anchor, blockers_by_anchor):
            continue
        for event in reviewer_terminal_events:
            event_at = _parse_utc(str(event.get("timestamp_utc") or ""))
            anchor_posted = _parse_utc(str(anchor.get("posted_at") or ""))
            if (
                event_at is not None
                and anchor_posted is not None
                and event_at < anchor_posted
            ):
                continue
            terminal_state = str(
                event.get("reviewer_state")
                or event.get("state")
                or event.get("final_state")
                or event.get("event_type")
                or ""
            ).strip().lower()
            rule_id = _terminal_rule_id(terminal_state, event)
            violations.append(
                AnchorViolation(
                    rule_id=rule_id,
                    anchor_packet_id=_packet_id(anchor),
                    detail=(
                        f"reviewer event_id={event.get('event_id')!r} "
                        f"emitted terminal_state={terminal_state!r} while "
                        f"continuation_anchor packet_id={_packet_id(anchor)!r} "
                        f"for current_row={current_row_id!r} is still live "
                        "(no stop_anchor release, no typed blocker)"
                    ),
                    remediation=(
                        "Block reviewer final completion/idle until the "
                        "continuation_anchor is consumed, released by a "
                        "stop_anchor, or converted to a typed current-row "
                        "blocker."
                    ),
                    evidence_event_ids=(str(event.get("event_id") or ""),),
                    target_role=str(anchor.get("target_role") or ""),
                    target_session_id=str(
                        anchor.get("target_session_id") or ""
                    ),
                    target_scope=_anchor_scope(anchor),
                )
            )

    # Rule 3: session-scoped anchors with stale target sessions and no refresh
    # or scope promotion.
    for anchor in live_anchors:
        target_session = str(anchor.get("target_session_id") or "").strip()
        scope = _anchor_scope(anchor)
        if not target_session:
            continue
        if scope in {"plan", "role"}:
            continue
        if live_sessions and target_session in live_sessions:
            continue
        if _anchor_promoted_or_refreshed(
            anchor=anchor,
            packets=packets,
            live_sessions=live_sessions,
            current_row_id=current_row_id,
            now=now_utc,
        ):
            continue
        if _anchor_has_typed_blocker(anchor, blockers_by_anchor):
            continue
        violations.append(
            AnchorViolation(
                rule_id=RULE_SESSION_SCOPED_ANCHOR_STALE_SESSION,
                anchor_packet_id=_packet_id(anchor),
                detail=(
                    f"continuation_anchor packet_id={_packet_id(anchor)!r} "
                    f"target_session_id={target_session!r} is not in the live "
                    f"reviewer session set {sorted(live_sessions)!r}; no "
                    "refresh anchor and no plan-scoped/role-scoped promotion "
                    "covers the gap"
                ),
                remediation=(
                    "Either post a refresh continuation_anchor for the live "
                    "reviewer session, or promote the anchor to "
                    "scope=plan/role so it survives session replacement; "
                    "otherwise post a typed current-row blocker."
                ),
                target_role=str(anchor.get("target_role") or ""),
                target_session_id=target_session,
                target_scope=scope,
            )
        )

    # Rule 4: startup/session authority reports degraded state while a live
    # current-row continuation anchor is still pending.
    authority = startup_authority or {}
    degraded_reasons = _startup_authority_degraded_reasons(authority)
    if degraded_reasons and live_anchors:
        for anchor in live_anchors:
            if _anchor_has_typed_blocker(
                anchor,
                blockers_by_anchor,
                expected_reason=RULE_STARTUP_AUTHORITY_NOT_ENFORCED,
            ):
                continue
            violations.append(
                AnchorViolation(
                    rule_id=RULE_STARTUP_AUTHORITY_NOT_ENFORCED,
                    anchor_packet_id=_packet_id(anchor),
                    detail=(
                        "startup/session authority reports "
                        f"{sorted(degraded_reasons)!r} while "
                        f"continuation_anchor packet_id={_packet_id(anchor)!r} "
                        f"for current_row={current_row_id!r} is still pending"
                    ),
                    remediation=(
                        "Emit a current-row blocker packet such as "
                        "continuation_anchor_not_enforced so the anchor "
                        "becomes typed evidence instead of silently surviving "
                        "a degraded session."
                    ),
                    target_role=str(anchor.get("target_role") or ""),
                    target_session_id=str(
                        anchor.get("target_session_id") or ""
                    ),
                    target_scope=_anchor_scope(anchor),
                )
            )

    # Rule 5: peer_steady_state / "no_new_packets" event while peer inbox
    # still has a current-row pending packet that targets the peer role.
    pending_peer_packets = tuple(_pending_current_row_peer_packets(
        packets, current_row_id, now_utc
    ))
    if pending_peer_packets:
        for event in events:
            event_type = str(event.get("event_type") or "").strip().lower()
            if event_type not in PEER_STEADY_STATE_EVENT_TYPES:
                continue
            peer_role = str(
                event.get("peer_role")
                or event.get("observed_role")
                or ""
            ).strip()
            relevant_pending = tuple(
                p for p in pending_peer_packets
                if not peer_role
                or str(p.get("target_role") or "").strip() == peer_role
            )
            if not relevant_pending:
                continue
            if _event_routed_lifecycle_transition(event):
                continue
            for pending in relevant_pending:
                violations.append(
                    AnchorViolation(
                        rule_id=RULE_PEER_STEADY_STATE_WITH_PENDING_PACKET,
                        anchor_packet_id=_packet_id(pending),
                        detail=(
                            f"peer steady-state event_id="
                            f"{event.get('event_id')!r} reports "
                            f"event_type={event_type!r} while "
                            f"peer_role={peer_role!r} inbox still has "
                            f"pending current-row packet "
                            f"packet_id={_packet_id(pending)!r}"
                        ),
                        remediation=(
                            "Surface the peer steady-state as "
                            "peer_steady_state_with_pending_current_row_packet "
                            "and route the next supported lifecycle "
                            "transition (refresh, supersede, blocker, or "
                            "body-open)."
                        ),
                        evidence_event_ids=(str(event.get("event_id") or ""),),
                        target_role=str(pending.get("target_role") or ""),
                        target_session_id=str(
                            pending.get("target_session_id") or ""
                        ),
                    )
                )

    # Rule 6: participant_liveness_expired must wake a lane or produce a
    # current-row blocker; trace-only output is insufficient.
    liveness_events = tuple(_filter_liveness_expired_events(events))
    if liveness_events:
        wake_keys = _wake_event_keys(events)
        for event in liveness_events:
            if _liveness_routed_to_wake(event, wake_keys):
                continue
            if _liveness_routed_to_current_row_blocker(
                event, packets, current_row_id
            ):
                continue
            session_name = str(event.get("session_name") or "")
            provider = str(event.get("provider") or "")
            violations.append(
                AnchorViolation(
                    rule_id=RULE_TRACE_ONLY_LIVENESS_EXPIRY,
                    anchor_packet_id="",
                    detail=(
                        f"participant_liveness_expired event_id="
                        f"{event.get('event_id')!r} for provider="
                        f"{provider!r} session={session_name!r} produced "
                        "neither a lane-wake event nor a current-row "
                        "blocker packet"
                    ),
                    remediation=(
                        "Route participant_liveness_expired to either a "
                        "lane_wake event or a typed current-row blocker "
                        "packet bound to the current plan row."
                    ),
                    evidence_event_ids=(str(event.get("event_id") or ""),),
                    target_role=str(event.get("role") or ""),
                    target_session_id=session_name,
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
        "live_anchor_count": len(live_anchors),
        "checked_anchor_packet_ids": [_packet_id(a) for a in live_anchors],
        "pending_peer_packet_count": len(pending_peer_packets),
        "reviewer_terminal_event_count": len(reviewer_terminal_events),
        "liveness_expired_event_count": len(liveness_events),
        "startup_authority_degraded_reasons": sorted(degraded_reasons),
        "live_reviewer_session_ids": sorted(live_sessions),
        "checked_surfaces": checked_surfaces,
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def _live_current_row_anchors(
    packets: Iterable[Mapping[str, object]],
    current_row_id: str,
    now: datetime,
) -> Iterable[Mapping[str, object]]:
    for packet in packets:
        kind = str(packet.get("kind") or "").strip().lower()
        if kind != ANCHOR_KIND_CONTINUATION:
            continue
        if not _packet_targets_row(packet, current_row_id):
            continue
        if _packet_is_consumed(packet):
            continue
        if _packet_is_expired(packet, now):
            continue
        yield packet


def _packet_targets_row(packet: Mapping[str, object], current_row_id: str) -> bool:
    if not current_row_id:
        return False
    target_ref = str(packet.get("target_ref") or "").strip()
    if current_row_id in target_ref:
        return True
    plan_id = str(packet.get("plan_id") or "").strip()
    return plan_id == current_row_id


def _packet_is_consumed(packet: Mapping[str, object]) -> bool:
    disposition = str(packet.get("disposition_state") or "").strip().lower()
    if disposition in {
        "absorbed",
        "applied",
        "archived",
        "consumed",
        "released",
        "dismissed",
        "superseded",
    }:
        return True
    if str(packet.get("absorbed_at_utc") or "").strip():
        return True
    if str(packet.get("released_at_utc") or "").strip():
        return True
    return False


def _packet_is_expired(packet: Mapping[str, object], now: datetime) -> bool:
    expires = _parse_utc(str(packet.get("expires_at_utc") or ""))
    if expires is None:
        return False
    return expires <= now


def _index_stop_anchors(
    packets: Iterable[Mapping[str, object]], current_row_id: str
) -> dict[str, tuple[Mapping[str, object], ...]]:
    by_anchor_id: dict[str, list[Mapping[str, object]]] = {}
    for packet in packets:
        kind = str(packet.get("kind") or "").strip().lower()
        if kind != ANCHOR_KIND_STOP:
            continue
        if current_row_id and not _packet_targets_row(packet, current_row_id):
            continue
        target_id = (
            str(packet.get("releases_anchor_packet_id") or "").strip()
            or str(packet.get("stop_of_packet_id") or "").strip()
            or str(packet.get("anchor_packet_id") or "").strip()
        )
        if target_id:
            by_anchor_id.setdefault(target_id, []).append(packet)
    return {key: tuple(value) for key, value in by_anchor_id.items()}


def _index_blockers_by_anchor(
    packets: Iterable[Mapping[str, object]],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    by_anchor_id: dict[str, list[Mapping[str, object]]] = {}
    for packet in packets:
        kind = str(packet.get("kind") or "").strip().lower()
        if kind not in BLOCKER_KINDS:
            continue
        target_id = (
            str(packet.get("blocker_for_anchor_packet_id") or "").strip()
            or str(packet.get("blocks_packet_id") or "").strip()
            or str(packet.get("anchor_packet_id") or "").strip()
        )
        refs = packet.get("references")
        if isinstance(refs, (list, tuple)):
            for ref in refs:
                if isinstance(ref, Mapping):
                    rid = str(ref.get("packet_id") or "").strip()
                    rkind = str(ref.get("kind") or "").strip().lower()
                    if rid and rkind in {
                        "blocker_for",
                        "anchor_blocker",
                        "blocks",
                    }:
                        target_id = rid
                        break
        if target_id:
            by_anchor_id.setdefault(target_id, []).append(packet)
    return {key: tuple(value) for key, value in by_anchor_id.items()}


def _anchor_released_by_stop(
    anchor: Mapping[str, object],
    stop_anchors_by_target: Mapping[str, Sequence[Mapping[str, object]]],
) -> bool:
    return _packet_id(anchor) in stop_anchors_by_target


def _anchor_has_typed_blocker(
    anchor: Mapping[str, object],
    blockers_by_anchor: Mapping[str, Sequence[Mapping[str, object]]],
    expected_reason: str | None = None,
) -> bool:
    blockers = blockers_by_anchor.get(_packet_id(anchor), ())
    if not blockers:
        return False
    if expected_reason is None:
        return True
    for blocker in blockers:
        reason = str(
            blocker.get("reason")
            or blocker.get("rule_id")
            or blocker.get("blocker_reason")
            or ""
        ).strip()
        if reason == expected_reason:
            return True
    return False


def _filter_reviewer_terminal_events(
    events: Iterable[Mapping[str, object]],
) -> Iterable[Mapping[str, object]]:
    for event in events:
        observed_role = str(
            event.get("reviewer_role") or event.get("role") or ""
        ).strip().lower()
        if observed_role and observed_role != "reviewer":
            continue
        state = str(
            event.get("reviewer_state")
            or event.get("state")
            or event.get("final_state")
            or event.get("event_type")
            or ""
        ).strip().lower()
        if state in REVIEWER_TERMINAL_STATES:
            yield event
            continue
        if str(event.get("event_type") or "").strip().lower() in {
            "reviewer_final_completion",
            "reviewer_idle",
            "reviewer_ended",
            "final_response_emitted",
        }:
            yield event


def _terminal_rule_id(state: str, event: Mapping[str, object]) -> str:
    if state in {"final_completion", "task_complete", "completed"} or (
        str(event.get("event_type") or "").strip().lower()
        in {"reviewer_final_completion", "final_response_emitted"}
    ):
        return RULE_FINAL_COMPLETION_WITH_LIVE_ANCHOR
    return RULE_REVIEWER_IDLE_WITH_LIVE_ANCHOR


def _anchor_scope(anchor: Mapping[str, object]) -> str:
    scope = str(anchor.get("scope") or anchor.get("anchor_scope") or "").strip().lower()
    if scope:
        return scope
    if str(anchor.get("target_session_id") or "").strip():
        return "session"
    if str(anchor.get("target_role") or "").strip():
        return "role"
    if _packet_targets_row(anchor, str(anchor.get("plan_id") or "")):
        return "plan"
    return ""


def _anchor_promoted_or_refreshed(
    *,
    anchor: Mapping[str, object],
    packets: Iterable[Mapping[str, object]],
    live_sessions: frozenset[str],
    current_row_id: str,
    now: datetime,
) -> bool:
    anchor_id = _packet_id(anchor)
    role = str(anchor.get("target_role") or "").strip()
    for packet in packets:
        if _packet_id(packet) == anchor_id:
            continue
        kind = str(packet.get("kind") or "").strip().lower()
        if kind != ANCHOR_KIND_CONTINUATION:
            continue
        if current_row_id and not _packet_targets_row(packet, current_row_id):
            continue
        if _packet_is_consumed(packet) or _packet_is_expired(packet, now):
            continue
        refresh_of = (
            str(packet.get("refresh_of_packet_id") or "").strip()
            or str(packet.get("supersedes_packet_id") or "").strip()
            or str(packet.get("anchor_refresh_of") or "").strip()
        )
        scope = _anchor_scope(packet)
        if refresh_of == anchor_id and (
            (
                live_sessions
                and str(packet.get("target_session_id") or "").strip() in live_sessions
            )
            or scope in {"plan", "role"}
        ):
            return True
        if scope in {"plan", "role"} and (
            (not role)
            or str(packet.get("target_role") or "").strip() == role
        ):
            return True
    return False


def _startup_authority_degraded_reasons(
    authority: Mapping[str, object],
) -> frozenset[str]:
    reasons: set[str] = set()
    reviewer_mode = str(authority.get("reviewer_mode") or "").strip().lower()
    if reviewer_mode in REVIEWER_DEGRADED_MODES:
        reasons.add(f"reviewer_mode={reviewer_mode}")
    topology = str(
        authority.get("observed_control_topology") or ""
    ).strip().lower()
    if topology == "no_live_agents":
        reasons.add(f"observed_control_topology={topology}")
    safe_to_continue = authority.get("safe_to_continue")
    if isinstance(safe_to_continue, bool) and not safe_to_continue:
        reasons.add("safe_to_continue=false")
    elif isinstance(safe_to_continue, str) and safe_to_continue.strip().lower() == "false":
        reasons.add("safe_to_continue=false")
    return frozenset(reasons)


def _pending_current_row_peer_packets(
    packets: Iterable[Mapping[str, object]],
    current_row_id: str,
    now: datetime,
) -> Iterable[Mapping[str, object]]:
    for packet in packets:
        if not _packet_targets_row(packet, current_row_id):
            continue
        if _packet_is_consumed(packet):
            continue
        if _packet_is_expired(packet, now):
            continue
        status = str(
            packet.get("status")
            or packet.get("lifecycle_current_state")
            or ""
        ).strip().lower()
        if status in {"applied", "absorbed", "dismissed", "archived"}:
            continue
        body_observed = str(packet.get("body_observed_at_utc") or "").strip()
        if body_observed:
            continue
        target_role = str(packet.get("target_role") or "").strip()
        if not target_role:
            continue
        yield packet


def _event_routed_lifecycle_transition(event: Mapping[str, object]) -> bool:
    if str(event.get("routed_lifecycle_transition") or "").strip():
        return True
    if event.get("steady_state_blocked_by_pending_packet") is True:
        return True
    routed = event.get("routed_actions")
    if isinstance(routed, (list, tuple)) and routed:
        return True
    return False


def _filter_liveness_expired_events(
    events: Iterable[Mapping[str, object]],
) -> Iterable[Mapping[str, object]]:
    for event in events:
        if str(event.get("event_type") or "").strip() in (
            LIVENESS_EXPIRY_EVENT_TYPES
        ):
            yield event


def _wake_event_keys(
    events: Iterable[Mapping[str, object]],
) -> frozenset[str]:
    keys: set[str] = set()
    for event in events:
        if str(event.get("event_type") or "").strip() in LANE_WAKE_EVENT_TYPES:
            session = str(
                event.get("session_name")
                or event.get("target_session_id")
                or ""
            ).strip()
            role = str(
                event.get("role") or event.get("target_role") or ""
            ).strip()
            if session:
                keys.add(f"session::{session}")
            if role:
                keys.add(f"role::{role}")
    return frozenset(keys)


def _liveness_routed_to_wake(
    event: Mapping[str, object], wake_keys: frozenset[str]
) -> bool:
    session = str(event.get("session_name") or "").strip()
    role = str(event.get("role") or "").strip()
    if session and f"session::{session}" in wake_keys:
        return True
    if role and f"role::{role}" in wake_keys:
        return True
    return False


def _liveness_routed_to_current_row_blocker(
    event: Mapping[str, object],
    packets: Iterable[Mapping[str, object]],
    current_row_id: str,
) -> bool:
    session = str(event.get("session_name") or "").strip()
    role = str(event.get("role") or "").strip()
    event_id = str(event.get("event_id") or "").strip()
    for packet in packets:
        kind = str(packet.get("kind") or "").strip().lower()
        if kind not in BLOCKER_KINDS:
            continue
        if not _packet_targets_row(packet, current_row_id):
            continue
        refs = packet.get("references")
        if isinstance(refs, (list, tuple)):
            for ref in refs:
                if isinstance(ref, Mapping):
                    rid = str(ref.get("event_id") or "").strip()
                    if rid and rid == event_id:
                        return True
        if (
            event_id
            and str(packet.get("triggering_event_id") or "").strip() == event_id
        ):
            return True
        if (
            session
            and str(packet.get("source_session_id") or "").strip() == session
        ):
            return True
        if (
            role
            and str(packet.get("source_role") or "").strip() == role
            and str(
                packet.get("source_event_type") or ""
            ).strip() == "participant_liveness_expired"
        ):
            return True
    return False


def _packet_id(packet: Mapping[str, object]) -> str:
    return str(packet.get("packet_id") or "").strip()


def _default_review_state_path() -> Path:
    return (
        REPO_ROOT
        / "dev/reports/review_channel/projections/latest/review_state.json"
    )


def _default_event_log_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/events/trace.ndjson"


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(
        f"- current_plan_row_id: `{report.get('current_plan_row_id')}`"
    )
    lines.append(f"- live_anchor_count: {report.get('live_anchor_count')}")
    lines.append(
        f"- pending_peer_packet_count: {report.get('pending_peer_packet_count')}"
    )
    lines.append(
        f"- reviewer_terminal_event_count: "
        f"{report.get('reviewer_terminal_event_count')}"
    )
    lines.append(
        f"- liveness_expired_event_count: "
        f"{report.get('liveness_expired_event_count')}"
    )
    degraded = report.get("startup_authority_degraded_reasons")
    if isinstance(degraded, Sequence) and not isinstance(degraded, (str, bytes)):
        rendered = ", ".join(f"`{r}`" for r in degraded) if degraded else "(none)"
        lines.append(f"- startup_authority_degraded_reasons: {rendered}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
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
                f"- {violation.get('anchor_packet_id')}: "
                f"{violation.get('rule_id')} ({violation.get('detail')})"
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
        "--startup-authority-path",
        type=Path,
        default=None,
        help=(
            "Optional StartupContext JSON file used to detect "
            "reviewer_mode/topology/safe_to_continue degradation."
        ),
    )
    parser.add_argument(
        "--row-id",
        default=DEFAULT_ROW_ID,
        help="Current plan row id used for anchor scope binding.",
    )
    parser.add_argument(
        "--live-reviewer-session-id",
        action="append",
        default=[],
        help=(
            "Live reviewer session id. Repeat for multiple. Used to detect "
            "stale session-scoped anchors."
        ),
    )
    parser.add_argument(
        "--live-reviewer-role",
        default="reviewer",
        help="Live reviewer role name (default: reviewer).",
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    startup_authority: Mapping[str, object] | None = None
    if args.startup_authority_path is not None:
        try:
            startup_authority = json.loads(
                args.startup_authority_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            startup_authority = None
    try:
        report = build_report(
            review_state_path=args.review_state_path,
            event_log_path=args.event_log_path,
            startup_authority=startup_authority,
            current_row_id=args.row_id,
            live_reviewer_session_ids=tuple(args.live_reviewer_session_id),
            live_reviewer_role=args.live_reviewer_role,
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
