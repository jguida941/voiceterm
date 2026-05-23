#!/usr/bin/env python3
"""Fail when reviewer-result transitions are blocked, drop, or leak into implementer lane.

G26 (Reviewer Result Transition Guard) enforces:

1. A reviewer session with current-row verification evidence has a typed path to
   post a review-result packet (`review_accepted`, `review_failed`, or
   `review_result`) without taking the implementer lane.
2. `ControlDecisionObeyedGuard` preserves and evaluates the supplied
   `--control-decision-input`; a readable decision file must not be summarized
   as `no_control_decision_input`.
3. If review-result posting is intentionally blocked by `body_open_required` or
   a checkpoint gate, the attempted-action receipt must be recorded as
   current-row blocker evidence and the route must declare the next supported
   transition.
4. A correct scoped control-decision artifact that still blocks review-result
   posting because `body_open_required` is active must surface as a route
   lifecycle blocker, never as reviewer completion and never as permission for
   Codex to take the implementer lane.
5. Acceptance evidence for `rev_pkt_4821` must include
   `command_output:test-python:744231b533e97e1c`, the live
   `check_active_topology_liveness.py` blocker state, and confirmation that
   `conftest.py` stayed untouched.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _iter_jsonl,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        iter_jsonl as _iter_jsonl,
        utc_timestamp,
    )


COMMAND = "check_reviewer_result_transition"
CONTRACT_ID = "ReviewerResultTransitionGuard"

REVIEW_RESULT_KINDS = frozenset({"review_accepted", "review_failed", "review_result"})
ROW_VERIFIED_EVENT_TYPE = "current_row_verified"
REVIEW_RESULT_ATTEMPT_EVENT_TYPE = "review_result_attempt"
REVIEW_RESULT_POSTED_EVENT_TYPE = "review_result_posted"
CONTROL_DECISION_EVALUATED_EVENT_TYPE = "control_decision_evaluated"
ATTEMPTED_ACTION_RECEIPT_EVENT_TYPE = "attempted_action_receipt"
BLOCKER_EVIDENCE_RECORDED_EVENT_TYPE = "current_row_blocker_recorded"
IMPLEMENTER_LANE_CLAIM_EVENT_TYPE = "implementer_lane_claim"

REASON_NO_TYPED_PATH = "reviewer_result_path_missing_after_verification"
REASON_CONTROL_DECISION_INPUT_DISCARDED = "control_decision_input_discarded_as_no_input"
REASON_BLOCKED_NO_RECEIPT = "blocked_review_result_missing_attempted_action_receipt"
REASON_BLOCKED_NO_NEXT_TRANSITION = "blocked_review_result_missing_next_transition_hint"
REASON_BLOCKER_NOT_PROMOTED = "body_open_blocker_not_promoted_to_route_lifecycle_blocker"
REASON_IMPLEMENTER_LANE_TAKEN = "reviewer_session_took_implementer_lane_during_review"
REASON_REV_PKT_4821_MISSING_EVIDENCE = "rev_pkt_4821_missing_required_acceptance_evidence"

DISPLAY_TEXT = (
    "Reviewer result transition violation. A reviewer-owned lifecycle output "
    "was blocked, dropped, or leaked into the implementer lane without typed "
    "blocker promotion."
)

REQUIRED_REV_PKT_4821_EVIDENCE_TAGS: tuple[str, ...] = (
    "command_output:test-python:744231b533e97e1c",
    "check_active_topology_liveness.py",
    "conftest.py:untouched",
)

# Sanctioned blocker reasons for a review-result attempt. When a posting attempt
# carries one of these, the route is *intentionally* blocked and must produce a
# typed blocker receipt rather than a silent drop.
SANCTIONED_BLOCKERS = frozenset({"body_open_required", "checkpoint_gate"})


@dataclass(frozen=True, slots=True)
class TransitionViolation:
    reason: str
    detail: str
    remediation: str
    packet_id: str = ""
    session_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    events: Sequence[Mapping[str, object]] | None = None,
    event_log_path: Path | None = None,
    row_id_filter: str = "",
    require_rev_pkt_4821_evidence: bool = True,
) -> dict[str, object]:
    """Evaluate G26 reviewer-result transition rules over an event stream."""
    warnings: list[str] = []
    source_path: Path | None = None
    if events is None:
        source_path = event_log_path or _default_event_log_path()
        events = tuple(_iter_jsonl(source_path, warnings=warnings))
    else:
        events = tuple(events)

    filtered = tuple(_filter_by_row(events, row_id_filter))
    indexed = _index_events(filtered)

    violations: list[TransitionViolation] = []
    violations.extend(_check_typed_path_after_verification(indexed))
    violations.extend(_check_control_decision_preserved(indexed))
    violations.extend(_check_blocked_attempts_promote_blocker(indexed))
    violations.extend(_check_no_implementer_lane_claim(indexed))
    if require_rev_pkt_4821_evidence:
        violations.extend(_check_rev_pkt_4821_acceptance_evidence(indexed))

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "event_log_path": str(source_path) if source_path is not None else "",
        "row_id_filter": row_id_filter,
        "checked_event_count": len(filtered),
        "verified_session_count": len(indexed["verified_sessions"]),
        "review_result_attempt_count": len(indexed["attempts"]),
        "review_result_posted_count": len(indexed["postings"]),
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def _check_typed_path_after_verification(
    indexed: Mapping[str, object],
) -> Iterable[TransitionViolation]:
    """A verified reviewer session must have a posting or sanctioned blocked attempt."""
    verified_sessions: set[str] = indexed["verified_sessions"]  # type: ignore[assignment]
    postings_by_session: Mapping[str, tuple[Mapping[str, object], ...]] = (
        indexed["postings_by_session"]  # type: ignore[assignment]
    )
    attempts_by_session: Mapping[str, tuple[Mapping[str, object], ...]] = (
        indexed["attempts_by_session"]  # type: ignore[assignment]
    )
    for session_id in sorted(verified_sessions):
        if postings_by_session.get(session_id):
            continue
        attempts = attempts_by_session.get(session_id, ())
        if any(_attempt_has_sanctioned_blocker(attempt) for attempt in attempts):
            # Intentional block; covered by `_check_blocked_attempts_promote_blocker`.
            continue
        yield TransitionViolation(
            reason=REASON_NO_TYPED_PATH,
            detail=(
                f"reviewer session {session_id!r} has current_row_verified "
                "evidence but no review_result_posted or sanctioned blocked "
                "review_result_attempt"
            ),
            remediation=(
                "Expose a typed reviewer-result post route (review_accepted, "
                "review_failed, or review_result) for the verified reviewer "
                "session; do not require the reviewer to take the implementer lane."
            ),
            session_id=session_id,
        )


def _check_control_decision_preserved(
    indexed: Mapping[str, object],
) -> Iterable[TransitionViolation]:
    """`ControlDecisionObeyedGuard` must not summarize a readable input as no_control_decision_input."""
    evaluations: tuple[Mapping[str, object], ...] = (
        indexed["control_decision_events"]  # type: ignore[assignment]
    )
    for event in evaluations:
        supplied = _coerce_str(event.get("control_decision_input"))
        readable = bool(event.get("control_decision_input_readable"))
        summary = _coerce_str(event.get("control_decision_summary"))
        if not supplied or not readable:
            continue
        if summary == "no_control_decision_input":
            yield TransitionViolation(
                reason=REASON_CONTROL_DECISION_INPUT_DISCARDED,
                detail=(
                    f"event_id={event.get('event_id')!r} supplied "
                    f"control_decision_input={supplied!r} marked readable, but "
                    "ControlDecisionObeyedGuard summary collapsed to "
                    "'no_control_decision_input'"
                ),
                remediation=(
                    "Pass --control-decision-input through to "
                    "ControlDecisionObeyedGuard.evaluate(); preserve the "
                    "decision artifact in the evaluation record."
                ),
                packet_id=_coerce_str(event.get("packet_id")),
                session_id=_coerce_str(event.get("session_id")),
            )


def _check_blocked_attempts_promote_blocker(
    indexed: Mapping[str, object],
) -> Iterable[TransitionViolation]:
    """Intentionally blocked attempts must emit attempted-action receipt + next-transition hint."""
    attempts: tuple[Mapping[str, object], ...] = indexed["attempts"]  # type: ignore[assignment]
    receipts_by_attempt: Mapping[str, tuple[Mapping[str, object], ...]] = (
        indexed["receipts_by_attempt"]  # type: ignore[assignment]
    )
    blockers_by_attempt: Mapping[str, tuple[Mapping[str, object], ...]] = (
        indexed["blockers_by_attempt"]  # type: ignore[assignment]
    )
    for attempt in attempts:
        if not _attempt_has_sanctioned_blocker(attempt):
            continue
        attempt_id = _coerce_str(attempt.get("attempt_id") or attempt.get("event_id"))
        blocker_reason = _coerce_str(attempt.get("blocker_reason"))
        receipts = receipts_by_attempt.get(attempt_id, ())
        blockers = blockers_by_attempt.get(attempt_id, ())
        if not receipts:
            yield TransitionViolation(
                reason=REASON_BLOCKED_NO_RECEIPT,
                detail=(
                    f"review_result_attempt {attempt_id!r} blocked by "
                    f"{blocker_reason!r} but no attempted_action_receipt was "
                    "recorded as current-row blocker evidence"
                ),
                remediation=(
                    "Emit an AttemptedActionReceipt and bind it to the "
                    "current row as blocker evidence."
                ),
                packet_id=_coerce_str(attempt.get("packet_id")),
                session_id=_coerce_str(attempt.get("session_id")),
            )
            continue
        next_transition_present = any(
            _coerce_str(receipt.get("next_transition")).strip()
            for receipt in receipts
        )
        if not next_transition_present:
            yield TransitionViolation(
                reason=REASON_BLOCKED_NO_NEXT_TRANSITION,
                detail=(
                    f"review_result_attempt {attempt_id!r} blocked by "
                    f"{blocker_reason!r}; attempted_action_receipt did not "
                    "declare a supported next_transition"
                ),
                remediation=(
                    "Populate AttemptedActionReceipt.next_transition with the "
                    "supported review-result route (e.g. body_open, "
                    "checkpoint_complete)."
                ),
                packet_id=_coerce_str(attempt.get("packet_id")),
                session_id=_coerce_str(attempt.get("session_id")),
            )
        if blocker_reason == "body_open_required" and not blockers:
            yield TransitionViolation(
                reason=REASON_BLOCKER_NOT_PROMOTED,
                detail=(
                    f"review_result_attempt {attempt_id!r} carried a correct "
                    "scoped control-decision artifact but body_open_required "
                    "block was not promoted to a current_row_blocker_recorded "
                    "route lifecycle blocker"
                ),
                remediation=(
                    "Promote the body_open_required block into a typed route "
                    "lifecycle blocker; never present it as reviewer completion "
                    "or as permission for Codex to take the implementer lane."
                ),
                packet_id=_coerce_str(attempt.get("packet_id")),
                session_id=_coerce_str(attempt.get("session_id")),
            )


def _check_no_implementer_lane_claim(
    indexed: Mapping[str, object],
) -> Iterable[TransitionViolation]:
    """Reviewer sessions must not take the implementer lane during a review window."""
    verified_sessions: set[str] = indexed["verified_sessions"]  # type: ignore[assignment]
    lane_claims: tuple[Mapping[str, object], ...] = (
        indexed["implementer_lane_claims"]  # type: ignore[assignment]
    )
    for claim in lane_claims:
        actor = _coerce_str(claim.get("actor_role"))
        session_id = _coerce_str(claim.get("session_id"))
        if actor != "reviewer":
            continue
        if session_id and session_id not in verified_sessions:
            continue
        yield TransitionViolation(
            reason=REASON_IMPLEMENTER_LANE_TAKEN,
            detail=(
                f"reviewer session {session_id!r} emitted an "
                f"implementer_lane_claim event {claim.get('event_id')!r} "
                "during the verified-row review window"
            ),
            remediation=(
                "Keep reviewer sessions on the reviewer lane; route work that "
                "requires implementer authority via a typed handoff packet."
            ),
            session_id=session_id,
        )


def _check_rev_pkt_4821_acceptance_evidence(
    indexed: Mapping[str, object],
) -> Iterable[TransitionViolation]:
    """rev_pkt_4821 must carry the three named acceptance-evidence tags."""
    postings_by_packet: Mapping[str, tuple[Mapping[str, object], ...]] = (
        indexed["postings_by_packet"]  # type: ignore[assignment]
    )
    postings = postings_by_packet.get("rev_pkt_4821", ())
    if not postings:
        return
    for posting in postings:
        evidence = _coerce_evidence_tags(posting.get("acceptance_evidence"))
        missing = tuple(
            tag for tag in REQUIRED_REV_PKT_4821_EVIDENCE_TAGS if tag not in evidence
        )
        if not missing:
            continue
        yield TransitionViolation(
            reason=REASON_REV_PKT_4821_MISSING_EVIDENCE,
            detail=(
                "rev_pkt_4821 review_result_posted is missing required "
                f"acceptance evidence: {missing!r}"
            ),
            remediation=(
                "Include command_output:test-python:744231b533e97e1c, the live "
                "check_active_topology_liveness.py blocker state, and a "
                "conftest.py:untouched confirmation in acceptance_evidence."
            ),
            packet_id="rev_pkt_4821",
            session_id=_coerce_str(posting.get("session_id")),
        )


def _index_events(events: Sequence[Mapping[str, object]]) -> dict[str, object]:
    verified_sessions: set[str] = set()
    attempts: list[Mapping[str, object]] = []
    postings: list[Mapping[str, object]] = []
    control_events: list[Mapping[str, object]] = []
    receipts_by_attempt: dict[str, list[Mapping[str, object]]] = {}
    blockers_by_attempt: dict[str, list[Mapping[str, object]]] = {}
    lane_claims: list[Mapping[str, object]] = []
    postings_by_session: dict[str, list[Mapping[str, object]]] = {}
    attempts_by_session: dict[str, list[Mapping[str, object]]] = {}
    postings_by_packet: dict[str, list[Mapping[str, object]]] = {}

    for event in events:
        event_type = _coerce_str(event.get("event_type"))
        if event_type == ROW_VERIFIED_EVENT_TYPE:
            session_id = _coerce_str(event.get("session_id"))
            actor_role = _coerce_str(event.get("actor_role"))
            if session_id and (not actor_role or actor_role == "reviewer"):
                verified_sessions.add(session_id)
        elif event_type == REVIEW_RESULT_ATTEMPT_EVENT_TYPE:
            attempts.append(event)
            session_id = _coerce_str(event.get("session_id"))
            if session_id:
                attempts_by_session.setdefault(session_id, []).append(event)
        elif event_type == REVIEW_RESULT_POSTED_EVENT_TYPE:
            kind = _coerce_str(event.get("kind")).lower()
            if kind and kind not in REVIEW_RESULT_KINDS:
                continue
            postings.append(event)
            session_id = _coerce_str(event.get("session_id"))
            if session_id:
                postings_by_session.setdefault(session_id, []).append(event)
            packet_id = _coerce_str(event.get("packet_id"))
            if packet_id:
                postings_by_packet.setdefault(packet_id, []).append(event)
        elif event_type == CONTROL_DECISION_EVALUATED_EVENT_TYPE:
            control_events.append(event)
        elif event_type == ATTEMPTED_ACTION_RECEIPT_EVENT_TYPE:
            attempt_id = _coerce_str(event.get("attempt_id"))
            if attempt_id:
                receipts_by_attempt.setdefault(attempt_id, []).append(event)
        elif event_type == BLOCKER_EVIDENCE_RECORDED_EVENT_TYPE:
            attempt_id = _coerce_str(event.get("attempt_id"))
            if attempt_id:
                blockers_by_attempt.setdefault(attempt_id, []).append(event)
        elif event_type == IMPLEMENTER_LANE_CLAIM_EVENT_TYPE:
            lane_claims.append(event)

    return {
        "verified_sessions": verified_sessions,
        "attempts": tuple(attempts),
        "postings": tuple(postings),
        "control_decision_events": tuple(control_events),
        "receipts_by_attempt": {k: tuple(v) for k, v in receipts_by_attempt.items()},
        "blockers_by_attempt": {k: tuple(v) for k, v in blockers_by_attempt.items()},
        "implementer_lane_claims": tuple(lane_claims),
        "postings_by_session": {k: tuple(v) for k, v in postings_by_session.items()},
        "attempts_by_session": {k: tuple(v) for k, v in attempts_by_session.items()},
        "postings_by_packet": {k: tuple(v) for k, v in postings_by_packet.items()},
    }


def _attempt_has_sanctioned_blocker(attempt: Mapping[str, object]) -> bool:
    reason = _coerce_str(attempt.get("blocker_reason")).lower()
    return reason in SANCTIONED_BLOCKERS


def _filter_by_row(
    events: Iterable[Mapping[str, object]], row_id_filter: str
) -> Iterable[Mapping[str, object]]:
    if not row_id_filter:
        yield from events
        return
    for event in events:
        target_ref = _coerce_str(event.get("target_ref"))
        plan_id = _coerce_str(event.get("plan_id"))
        row_id = _coerce_str(event.get("row_id"))
        if row_id_filter in (target_ref, plan_id, row_id):
            yield event
            continue
        if target_ref and row_id_filter in target_ref:
            yield event


def _coerce_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _coerce_evidence_tags(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        return tuple(_coerce_str(v) for v in value.values())
    if isinstance(value, Sequence):
        return tuple(_coerce_str(item) for item in value)
    return ()


def _default_event_log_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/events/trace.ndjson"


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- checked_event_count: {report.get('checked_event_count')}")
    lines.append(f"- verified_session_count: {report.get('verified_session_count')}")
    lines.append(
        f"- review_result_attempt_count: {report.get('review_result_attempt_count')}"
    )
    lines.append(
        f"- review_result_posted_count: {report.get('review_result_posted_count')}"
    )
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("row_id_filter"):
        lines.append(f"- row_id_filter: `{report.get('row_id_filter')}`")
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
                f"- {violation.get('reason')} "
                f"(packet={violation.get('packet_id') or '-'}, "
                f"session={violation.get('session_id') or '-'}): "
                f"{violation.get('detail')}"
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
        "--event-log-path",
        type=Path,
        default=_default_event_log_path(),
        help="Review-channel event log (NDJSON).",
    )
    parser.add_argument(
        "--row-id",
        default="",
        help="If set, only consider events matching this row_id/plan_id/target_ref.",
    )
    parser.add_argument(
        "--skip-rev-pkt-4821-evidence",
        action="store_true",
        help=(
            "Skip the rev_pkt_4821 acceptance-evidence check; used by tests "
            "that drive the other invariants in isolation."
        ),
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            event_log_path=args.event_log_path,
            row_id_filter=args.row_id,
            require_rev_pkt_4821_evidence=not args.skip_rev_pkt_4821_evidence,
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
