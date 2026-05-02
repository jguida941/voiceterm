#!/usr/bin/env python3
"""Review probe: flag packets without durable plan/finding ownership."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from check_bootstrap import REPO_ROOT
    from probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )
except ModuleNotFoundError:  # pragma: no cover - package-style fallback
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
    from dev.scripts.checks.probe_support.bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )

from dev.scripts.devctl.runtime.master_plan_store import read_plan_rows_jsonl
from dev.scripts.devctl.runtime.packet_carry_forward import (
    durable_packet_ids_from_finding_rows,
    durable_packet_ids_from_plan_rows,
    packet_carry_forward_debts,
)


PROBE_NAME = "packet_carry_forward_debt"
REVIEW_LENS = "packet_lifecycle_continuity"
DEFAULT_MAX_HINTS = 30
REVIEW_STATE_PATHS = (
    Path("dev/reports/review_channel/projections/latest/review_state.json"),
    Path("dev/reports/review_channel/state/latest.json"),
)
PLAN_STORE_PATHS = (
    Path("dev/state/plan_index.jsonl"),
)
GOVERNANCE_LOG_PATHS = (
    Path("dev/reports/governance/finding_reviews.jsonl"),
)


def main(argv: list[str] | None = None) -> int:
    parser = build_probe_parser(PROBE_NAME)
    parser.add_argument(
        "--min-packet-number",
        type=int,
        default=0,
        help="Only report packet ids with a numeric suffix at or above this value.",
    )
    parser.add_argument(
        "--max-hints",
        type=int,
        default=DEFAULT_MAX_HINTS,
        help="Maximum packet debt hints to emit.",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    review_state_path = _resolve_first(REVIEW_STATE_PATHS)
    plan_store_path = _resolve_first(PLAN_STORE_PATHS)
    finding_log_path = _resolve_first(GOVERNANCE_LOG_PATHS)
    risk_hints: list[RiskHint] = []
    files_scanned = 0
    if review_state_path is not None:
        files_scanned += 1
        if plan_store_path is not None:
            files_scanned += 1
        if finding_log_path is not None:
            files_scanned += 1
        risk_hints = packet_carry_forward_debt_hints(
            review_state_path=review_state_path,
            plan_store_path=plan_store_path,
            finding_log_path=finding_log_path,
            min_packet_number=max(0, int(args.min_packet_number)),
            max_hints=max(1, int(args.max_hints)),
        )

    report = ProbeReport(
        command=PROBE_NAME,
        risk_hints=risk_hints,
        files_scanned=files_scanned,
        files_with_hints=1 if risk_hints else 0,
    )
    return emit_probe_report(report, output_format=args.format)


def packet_carry_forward_debt_hints(
    *,
    review_state_path: Path,
    plan_store_path: Path | None,
    finding_log_path: Path | None = None,
    min_packet_number: int = 0,
    max_hints: int = DEFAULT_MAX_HINTS,
) -> list[RiskHint]:
    """Return risk hints for packets not represented in durable state."""
    packets = _review_state_packets(review_state_path)
    plan_rows = (
        read_plan_rows_jsonl(plan_store_path)
        if plan_store_path is not None and plan_store_path.is_file()
        else ()
    )
    finding_rows = (
        _read_jsonl_rows(finding_log_path)
        if finding_log_path is not None and finding_log_path.is_file()
        else ()
    )
    durable_packet_ids = (
        durable_packet_ids_from_plan_rows(plan_rows)
        + durable_packet_ids_from_finding_rows(finding_rows)
    )
    debts = packet_carry_forward_debts(
        packets,
        durable_packet_ids=durable_packet_ids,
        min_packet_number=min_packet_number,
    )
    newest_first = tuple(sorted(debts, key=lambda row: row.packet_id, reverse=True))
    return [
        _debt_hint(review_state_path, debt)
        for debt in newest_first[:max_hints]
    ]


def _debt_hint(path: Path, debt) -> RiskHint:
    return RiskHint(
        file=path.as_posix(),
        symbol=debt.packet_id,
        risk_type=debt.reason,
        severity="HIGH",
        signals=[
            f"packet_id={debt.packet_id}",
            f"reason={debt.reason}",
            f"kind={debt.kind}",
            f"route={debt.from_agent}->{debt.to_agent}",
            f"status={debt.status}",
            f"lifecycle_state={debt.lifecycle_state}",
            f"plan_id={debt.plan_id}",
            f"intake_ref={debt.intake_ref}",
            f"latest_event_id={debt.latest_event_id}",
            f"required_next_action={_required_next_action(debt)}",
        ],
        ai_instruction=(
            "Packets are transport and provenance, not durable work authority. "
            "If a packet carries plan, finding, guard, probe, or architecture "
            "intent, promote that work into MasterPlan/PlanRow, FindingReview, "
            "GuardPromotionCandidate, or another typed ingestion receipt with "
            "the packet id recorded before TTL expiry. ACK/disposition alone "
            "does not prove the work was absorbed."
        ),
        review_lens=REVIEW_LENS,
    )


def _required_next_action(debt) -> str:
    if debt.kind in {"finding", "plan_gap_review", "plan_patch_review"}:
        return "ingest_packet_into_plan_row_or_finding_review"
    if debt.kind in {"approval_request", "commit_approval", "question"}:
        return "link_packet_to_lifecycle_owner_or_terminal_disposition"
    return "classify_packet_intent_and_record_typed_owner"


def _review_state_packets(path: Path) -> tuple[dict[str, object], ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    if not isinstance(payload, dict):
        return ()
    packets = payload.get("packets")
    if not isinstance(packets, list):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, dict))


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


def _resolve_first(paths: tuple[Path, ...]) -> Path | None:
    for rel in paths:
        candidate = REPO_ROOT / rel
        if candidate.is_file():
            return candidate
    return None


if __name__ == "__main__":
    raise SystemExit(main())
