#!/usr/bin/env python3
"""Review probe: flag duplicate review-channel event ids."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

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


PROBE_NAME = "event_id_uniqueness"
REVIEW_LENS = "runtime_event_integrity"
EVENT_LOG_PATHS = (
    Path("dev/reports/review_channel/latest/trace.ndjson"),
    Path("dev/reports/review_channel/projections/latest/trace.ndjson"),
    Path("dev/reports/review_channel/projections/latest/event_log.jsonl"),
    Path("dev/reports/review_channel/events/trace.ndjson"),
)


def main(argv: list[str] | None = None) -> int:
    parser = build_probe_parser(PROBE_NAME)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    event_log = _resolve_event_log()
    risk_hints: list[RiskHint] = []
    files_scanned = 0
    if event_log is not None:
        files_scanned = 1
        risk_hints = duplicate_event_id_hints(event_log)

    report = ProbeReport(
        command=PROBE_NAME,
        risk_hints=risk_hints,
        files_scanned=files_scanned,
        files_with_hints=1 if risk_hints else 0,
    )
    return emit_probe_report(report, output_format=args.format)


def duplicate_event_id_hints(path: Path) -> list[RiskHint]:
    rows = _scan_event_ids(path)
    hints: list[RiskHint] = []
    for event_id, count in sorted(rows["counts"].items()):
        if count <= 1:
            continue
        event_types = sorted(rows["event_types"].get(event_id, ()))
        packets = sorted(rows["packet_ids"].get(event_id, ()))
        hints.append(
            RiskHint(
                file=path.as_posix(),
                symbol=event_id,
                risk_type="duplicate_review_channel_event_id",
                severity="HIGH",
                signals=[
                    f"event_id={event_id}",
                    f"occurrences={count}",
                    "event_types=" + ",".join(event_types),
                    "packet_ids=" + ",".join(packets[:5]),
                ],
                ai_instruction=(
                    "Review-channel event ids must be unique append-only "
                    "identifiers. A duplicate id can collapse reducer history, "
                    "hide packet lifecycle transitions, or make agent sync "
                    "advance from the wrong event. Trace the writer that "
                    "emitted this event_id more than once, add an idempotency "
                    "or allocation regression test, and keep the event log "
                    "append path single-writer safe."
                ),
                review_lens=REVIEW_LENS,
            )
        )
    return hints


def _scan_event_ids(path: Path) -> dict[str, object]:
    counts: Counter[str] = Counter()
    event_types: dict[str, set[str]] = defaultdict(set)
    packet_ids: dict[str, set[str]] = defaultdict(set)
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                event = _json_object(line)
                if not event:
                    continue
                event_id = str(event.get("event_id") or "").strip()
                if not event_id:
                    continue
                counts[event_id] += 1
                event_type = str(event.get("event_type") or "").strip()
                if event_type:
                    event_types[event_id].add(event_type)
                packet_id = str(event.get("packet_id") or "").strip()
                if packet_id:
                    packet_ids[event_id].add(packet_id)
    except OSError:
        pass
    return {
        "counts": counts,
        "event_types": event_types,
        "packet_ids": packet_ids,
    }


def _json_object(line: str) -> dict[str, object]:
    text = line.strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_event_log() -> Path | None:
    for rel in EVENT_LOG_PATHS:
        candidate = REPO_ROOT / rel
        if candidate.is_file():
            return candidate
    return None


if __name__ == "__main__":
    raise SystemExit(main())
