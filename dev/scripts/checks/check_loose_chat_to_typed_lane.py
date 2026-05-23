#!/usr/bin/env python3
"""Fail when loose chat reaches implementation authority without a typed lane.

G25 Loose-Chat-To-Typed-Lane Guard. Extends the A16 topology contract so
provider chat replies cannot become implementation authority by themselves,
while ensuring valid typed packet bodies routed by the operator cannot be
blocked forever by stale ``action_request`` projections.

Acceptance (delete_after_ingest.md G25):

* Loose chat alone remains insufficient collaboration proof.
* Typed packet body visibility plus target-provider session evidence must
  have a supported lifecycle transition path.
* If that path is missing, the required output is a typed blocker or
  refreshed packet (not Codex taking the implementer lane).
* The instruction-priority selector must prefer current-row, role/session
  bound packets over stale packet projections. A stale ``action_request``
  such as ``rev_pkt_4804`` must not hide newer same-row blockers such as
  ``rev_pkt_4821`` from the Claude implementer inbox or from reviewer
  final-gate continuation.
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
        matches_row as _matches_row,
        packet_row_id as _packet_row_id,
        packets_from_review_state as _packets_from_review_state,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        matches_row as _matches_row,
        packet_row_id as _packet_row_id,
        packets_from_review_state as _packets_from_review_state,
        utc_timestamp,
    )


COMMAND = "check_loose_chat_to_typed_lane"
CONTRACT_ID = "LooseChatToTypedLaneGuard"

# Rule identifiers for typed violations.
RULE_LOOSE_CHAT_AUTHORITY = "loose_chat_alone_promoted_to_authority"
RULE_MISSING_TARGET_SESSION_EVIDENCE = "typed_body_lacks_target_session_evidence"
RULE_LIFECYCLE_TRANSITION_MISSING = "lifecycle_transition_path_missing"
RULE_CODEX_TAKES_IMPLEMENTER_LANE = "codex_took_implementer_lane_without_blocker"
RULE_STALE_PACKET_HIDES_NEWER_BLOCKER = "stale_action_request_hides_newer_same_row_blocker"

DISPLAY_TEXT = (
    "Loose-chat-to-typed-lane violation. Provider chat cannot promote to "
    "implementation authority without a typed packet body, target-provider "
    "session evidence, and a supported lifecycle transition. Stale "
    "action_request packets must not hide newer same-row blockers."
)

# Lifecycle transitions accepted for typed-body + session-evidence promotion.
SUPPORTED_LIFECYCLE_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("posted", "acknowledged"),
        ("posted", "delivered"),
        ("delivered", "acknowledged"),
        ("delivered", "implementer_ack"),
        ("acknowledged", "implementer_ack"),
        ("implementer_ack", "task_progress"),
        ("implementer_ack", "task_started"),
        ("acknowledged", "task_started"),
        ("acknowledged", "task_progress"),
        ("task_started", "task_progress"),
        ("task_progress", "task_produced"),
        ("task_started", "task_produced"),
        ("posted", "task_blocked"),
        ("delivered", "task_blocked"),
        ("acknowledged", "task_blocked"),
        ("implementer_ack", "task_blocked"),
        ("task_started", "task_blocked"),
        ("task_progress", "task_blocked"),
        ("posted", "superseded"),
        ("delivered", "superseded"),
        ("posted", "refreshed"),
        ("delivered", "refreshed"),
    }
)

# Packet "kinds" that are typed blockers / refreshed packets.
TYPED_BLOCKER_KINDS: frozenset[str] = frozenset(
    {
        "task_blocked",
        "finding",
        "decision",
        "refreshed",
        "supersede",
        "superseded",
        "continuation_anchor",
    }
)

# Packet kinds the implementer lane mutates against.
IMPLEMENTER_LANE_KINDS: frozenset[str] = frozenset(
    {
        "task_progress",
        "task_started",
        "task_produced",
        "implementer_ack",
    }
)


@dataclass(frozen=True, slots=True)
class LooseChatViolation:
    """Typed violation row for the G25 guard."""

    rule_id: str
    packet_id: str
    detail: str
    remediation: str
    evidence_packet_ids: tuple[str, ...] = ()


def build_report(
    *,
    packets: Sequence[Mapping[str, object]] | None = None,
    review_state_path: Path | None = None,
    current_row_id: str = "",
    instructions_priority_actor_role: str = "implementer",
) -> dict[str, object]:
    """Assemble the typed report for the G25 guard.

    Parameters
    ----------
    packets:
        Iterable of packet projection rows. When ``None`` the report falls
        back to the default review-state path.
    review_state_path:
        Override for the default review-state projection path.
    current_row_id:
        When set, only evaluate packets whose ``target_ref`` or ``plan_id``
        matches the current PlanRow id. Required input for the
        instruction-priority selector rule.
    instructions_priority_actor_role:
        Role whose inbox is being projected (defaults to ``implementer``).
    """
    warnings: list[str] = []
    checked_surfaces: list[str] = []
    source_path: Path | None = None
    if packets is None:
        source_path = review_state_path or _default_review_state_path()
        checked_surfaces.append(str(source_path))
        packets = _packets_from_review_state(source_path, warnings)
    else:
        packets = tuple(packets)

    violations: list[LooseChatViolation] = []

    # Acceptance 1, 2, 3: per-packet typed-body lifecycle checks.
    for packet in packets:
        if not _matches_row(packet, current_row_id):
            continue
        violations.extend(_evaluate_packet_typed_lane(packet))

    # Acceptance 4 & 5: instruction-priority selector hiding newer blockers.
    violations.extend(
        _evaluate_instruction_priority_ordering(
            packets=packets,
            current_row_id=current_row_id,
            actor_role=instructions_priority_actor_role,
        )
    )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "current_row_id": current_row_id,
        "instructions_priority_actor_role": instructions_priority_actor_role,
        "checked_surfaces": checked_surfaces,
        "review_state_path": str(source_path) if source_path is not None else "",
        "checked_packet_count": sum(1 for p in packets if _matches_row(p, current_row_id)),
        "violation_count": len(violations),
        "violations": [asdict(violation) for violation in violations],
        "warnings": warnings,
    }


def _evaluate_packet_typed_lane(
    packet: Mapping[str, object],
) -> tuple[LooseChatViolation, ...]:
    """Evaluate acceptance criteria 1, 2 and 3 for a single packet."""
    violations: list[LooseChatViolation] = []
    packet_id = str(packet.get("packet_id") or "").strip()
    kind = _kind(packet)
    typed_body = str(packet.get("body") or "").strip()
    chat_only_source = bool(packet.get("chat_only_source"))
    target_session_id = str(packet.get("target_session_id") or "").strip()
    target_role = str(packet.get("target_role") or "").strip()
    transition_from = str(packet.get("lifecycle_previous_state") or "").strip().lower()
    transition_to = str(
        packet.get("lifecycle_current_state") or packet.get("status") or ""
    ).strip().lower()
    implementer_lane = kind in IMPLEMENTER_LANE_KINDS

    # Acceptance 1: chat-only sourcing with no typed body promoted to
    # implementer lane is loose-chat-as-authority.
    if chat_only_source and not typed_body and implementer_lane:
        violations.append(
            LooseChatViolation(
                rule_id=RULE_LOOSE_CHAT_AUTHORITY,
                packet_id=packet_id,
                detail=(
                    f"packet kind={kind!r} sourced from chat_only_source=True "
                    "promoted to implementer lane without a typed packet body"
                ),
                remediation=(
                    "Loose chat is not collaboration proof. Re-emit the work "
                    "as a typed packet body before advancing the implementer "
                    "lane."
                ),
            )
        )
        return tuple(violations)

    # Only continue if the packet would be eligible for implementer-lane
    # promotion (typed body present and aimed at the implementer lane).
    if not typed_body or not implementer_lane:
        return tuple(violations)

    # Acceptance 2 (half 1): typed body without target-provider session
    # evidence cannot satisfy the lane.
    if not target_session_id:
        violations.append(
            LooseChatViolation(
                rule_id=RULE_MISSING_TARGET_SESSION_EVIDENCE,
                packet_id=packet_id,
                detail=(
                    f"packet kind={kind!r} has typed body but no "
                    f"target_session_id (target_role={target_role!r})"
                ),
                remediation=(
                    "Bind the packet to a live target_session_id from the "
                    "target provider before advancing the implementer lane."
                ),
            )
        )

    # Acceptance 2 (half 2): there must be a supported lifecycle transition.
    transition_supported = (
        transition_from,
        transition_to,
    ) in SUPPORTED_LIFECYCLE_TRANSITIONS or (
        # When previous-state is empty, allow any "posted" entry transition.
        not transition_from and transition_to in {"posted", "delivered"}
    )

    if not transition_supported:
        violations.append(
            LooseChatViolation(
                rule_id=RULE_LIFECYCLE_TRANSITION_MISSING,
                packet_id=packet_id,
                detail=(
                    f"packet kind={kind!r} lacks supported lifecycle "
                    f"transition: from={transition_from!r} -> "
                    f"to={transition_to!r}"
                ),
                remediation=(
                    "Emit a typed blocker (task_blocked, finding) or a "
                    "refreshed packet -- never let Codex take the implementer "
                    "lane on an unsupported transition."
                ),
            )
        )

    # Acceptance 3: when the transition path is missing, the actor field must
    # not show Codex stepping into the implementer lane.
    if not transition_supported and _actor_is_codex(packet) and kind in IMPLEMENTER_LANE_KINDS:
        violations.append(
            LooseChatViolation(
                rule_id=RULE_CODEX_TAKES_IMPLEMENTER_LANE,
                packet_id=packet_id,
                detail=(
                    f"packet kind={kind!r} authored by codex while transition "
                    f"path is missing; required output is a typed blocker or "
                    "refreshed packet"
                ),
                remediation=(
                    "Codex must emit a typed blocker or refreshed packet, "
                    "not take the implementer lane when the lifecycle path "
                    "is missing."
                ),
            )
        )

    return tuple(violations)


def _evaluate_instruction_priority_ordering(
    *,
    packets: Sequence[Mapping[str, object]],
    current_row_id: str,
    actor_role: str,
) -> tuple[LooseChatViolation, ...]:
    """Acceptance 4/5: stale ``action_request`` must not hide newer blockers.

    For each PlanRow id covered by the packets, find the newest blocker
    (``task_blocked``/``finding``) and ensure no older ``action_request`` is
    being projected as the active selector entry. The selector input is
    encoded by the ``selector_priority`` and ``selector_active`` fields on
    each packet projection row.
    """
    violations: list[LooseChatViolation] = []
    row_packets = _group_by_row(packets, current_row_id)
    for row_id, row_packet_list in row_packets.items():
        # Find the newest blocker packet for this row that is bound to the
        # implementer's actor role.
        blockers = [
            p
            for p in row_packet_list
            if _kind(p) in TYPED_BLOCKER_KINDS
            and _packet_target_role(p) == actor_role
        ]
        if not blockers:
            continue
        newest_blocker = max(
            blockers,
            key=lambda p: str(p.get("posted_at") or p.get("timestamp_utc") or ""),
        )
        newest_blocker_ts = str(
            newest_blocker.get("posted_at")
            or newest_blocker.get("timestamp_utc")
            or ""
        )

        # Find any active ``action_request`` packet for this row that is
        # older than the newest blocker but still projected as the active
        # selector entry.
        offenders = [
            p
            for p in row_packet_list
            if _kind(p) == "action_request"
            and _packet_target_role(p) == actor_role
            and bool(p.get("selector_active"))
            and str(p.get("posted_at") or p.get("timestamp_utc") or "")
            < newest_blocker_ts
        ]
        if not offenders:
            continue
        for offender in offenders:
            violations.append(
                LooseChatViolation(
                    rule_id=RULE_STALE_PACKET_HIDES_NEWER_BLOCKER,
                    packet_id=str(offender.get("packet_id") or ""),
                    detail=(
                        f"row_id={row_id!r}: stale action_request "
                        f"{offender.get('packet_id')!r} "
                        f"posted={offender.get('posted_at')!r} is "
                        "selector_active while newer same-row blocker "
                        f"{newest_blocker.get('packet_id')!r} "
                        f"posted={newest_blocker_ts!r} exists"
                    ),
                    remediation=(
                        "Refresh the instruction-priority selector so the "
                        "newer same-row blocker surfaces. Stale action_request "
                        "packets must not hide newer task_blocked or finding "
                        "packets from the implementer inbox or final-gate "
                        "continuation."
                    ),
                    evidence_packet_ids=(
                        str(newest_blocker.get("packet_id") or ""),
                    ),
                )
            )
    return tuple(violations)


def _group_by_row(
    packets: Sequence[Mapping[str, object]],
    current_row_id: str,
) -> dict[str, list[Mapping[str, object]]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for packet in packets:
        if not _matches_row(packet, current_row_id):
            continue
        row_id = _packet_row_id(packet)
        if not row_id:
            continue
        grouped.setdefault(row_id, []).append(packet)
    return grouped


def _packet_target_role(packet: Mapping[str, object]) -> str:
    return str(packet.get("target_role") or "").strip()


def _kind(packet: Mapping[str, object]) -> str:
    return str(packet.get("kind") or "").strip().lower()


def _actor_is_codex(packet: Mapping[str, object]) -> bool:
    actor = str(packet.get("actor") or packet.get("author_role") or "").strip().lower()
    if actor == "codex":
        return True
    author = str(packet.get("author_provider") or packet.get("author") or "").strip().lower()
    return author == "codex"


def _default_review_state_path() -> Path:
    return REPO_ROOT / "dev/reports/review_channel/projections/latest/review_state.json"


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- current_row_id: `{report.get('current_row_id')}`")
    lines.append(
        f"- instructions_priority_actor_role: "
        f"`{report.get('instructions_priority_actor_role')}`"
    )
    lines.append(f"- checked_packet_count: {report.get('checked_packet_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('rule_id')}: "
                f"{violation.get('packet_id')} -- "
                f"{violation.get('detail')}"
            )
    warnings = report.get("warnings")
    if isinstance(warnings, Sequence) and not isinstance(warnings, (str, bytes)) and warnings:
        lines.extend(("", "## Warnings", ""))
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--review-state-path",
        type=Path,
        default=_default_review_state_path(),
        help="Path to review-channel projection review_state.json",
    )
    parser.add_argument(
        "--row-id",
        default="",
        help=(
            "If set, only evaluate packets whose target_ref or plan_id "
            "matches this row id (current-row scope)."
        ),
    )
    parser.add_argument(
        "--actor-role",
        default="implementer",
        help="Role whose instruction-priority inbox is being audited.",
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            review_state_path=args.review_state_path,
            current_row_id=args.row_id,
            instructions_priority_actor_role=args.actor_role,
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
