#!/usr/bin/env python3
"""Review probe: flag known consumer/event_type/field mismatches.

Per Codex rev_pkt_2318 1A + rev_pkt_2333/2365 + operator directive
2026-04-30 ("recurring bug class = architecture fix, not band-aid").
This probe scans the live review-channel event log to derive each
``event_type``'s populated field shape, then cross-references a
hardcoded ``_KNOWN_CONSUMER_FIELDS`` table. When a consumer is
registered as reading a field that 0 live events of that ``event_type``
populate, the probe emits a HIGH-severity ``RiskHint``.

Output (per the standard ``ProbeReport`` contract): ``ok``,
``files_scanned``, ``files_with_hints``, ``risk_hints``. The
``_scan_event_log`` inventory is computed internally to drive the
mismatch decisions but is NOT emitted as a separate report block —
consumers should use ``risk_hints`` as the authoritative output.

**Supported invocation modes** (per rev_pkt_2365):

- Shim entrypoint: ``python3 dev/scripts/checks/probe_event_field_naming_consistency.py``
- ``python -m`` from ``dev/scripts/checks``: ``python3 -m probe_event_field_naming_consistency``
- Import (with PYTHONPATH including repo root): ``from dev.scripts.checks.review_probes.probe_event_field_naming_consistency import main``

**NOT supported**: direct invocation of the underlying file in
``review_probes/`` (e.g., ``python3 dev/scripts/checks/review_probes/probe_event_field_naming_consistency.py``).
The probe relies on ``check_bootstrap`` / ``probe_bootstrap`` modules
that are siblings to the shim, not to the underlying file. This
matches the existing pattern across all ``review_probes/probe_*.py``
files; the shim is the public entrypoint.

Why: this loop alone produced 5 instances of the same bug class —
consumer code reading ``event.get("actor")`` or ``event.get("from_agent")``
when the acting actor lives in ``event["metadata"]["actor"]``. The probe
catches the mismatch before it ships, anchored to typed event-log
evidence.

This probe always exits 0 (advisory).
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from collections.abc import Mapping
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
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
    from dev.scripts.checks.probe_support.bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )


REVIEW_LENS = "contract_quality"
PROBE_NAME = "event_field_naming_consistency"

EVENT_LOG_PATHS = (
    Path("dev/reports/review_channel/projections/latest/event_log.jsonl"),
    Path("dev/reports/review_channel/projections/latest/trace.ndjson"),
    Path("dev/reports/review_channel/events/trace.ndjson"),
)


def main(argv: list[str] | None = None) -> int:
    parser = build_probe_parser(PROBE_NAME)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    event_log = _resolve_event_log()
    if event_log is None:
        report = ProbeReport(
            command=PROBE_NAME,
            risk_hints=[],
            files_scanned=0,
            files_with_hints=0,
        )
        emit_probe_report(report, args.format)
        return 0

    inventory = _scan_event_log(event_log)
    risk_hints = _flag_known_consumer_mismatches(inventory)
    report = ProbeReport(
        command=PROBE_NAME,
        risk_hints=risk_hints,
        files_scanned=1,
        files_with_hints=(1 if risk_hints else 0),
    )
    emit_probe_report(report, output_format=args.format)
    return 0


def _resolve_event_log() -> Path | None:
    for rel in EVENT_LOG_PATHS:
        candidate = REPO_ROOT / rel
        if candidate.exists():
            return candidate
    return None


def _scan_event_log(path: Path) -> dict[str, dict[str, object]]:
    """Return ``{event_type: {count, top_level_keys, metadata_keys}}``."""
    inventory: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "count": 0,
            "top_level_keys": set(),
            "metadata_keys": set(),
        }
    )
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                event_type = str(event.get("event_type") or "_unknown")
                shape = inventory[event_type]
                shape["count"] += 1  # type: ignore[operator]
                for key in event:
                    value = event[key]
                    is_populated = (
                        value not in (None, "", [], {}, ())
                        or (isinstance(value, dict) and any(value.values()))
                    )
                    if is_populated:
                        shape["top_level_keys"].add(key)  # type: ignore[union-attr]
                metadata = event.get("metadata")
                if isinstance(metadata, Mapping):
                    for mkey, mval in metadata.items():
                        if mval not in (None, "", [], {}, ()):
                            shape["metadata_keys"].add(mkey)  # type: ignore[union-attr]
    except OSError:
        pass
    return dict(inventory)


# Known consumer/event_type/field triples. Each tuple says: when this
# consumer code reads from this field on this event_type, the field MUST
# be populated by ≥1 event in the live log. If not, the consumer is reading
# the wrong key — exactly the bug class rev_pkt_2318 1A targets.
_KNOWN_CONSUMER_FIELDS: tuple[tuple[str, str, str, str], ...] = (
    # (consumer file:line, event_type, field path, ai_instruction tag)
    (
        "review_channel/agent_sync_projection.py::_is_consumption_by_agent",
        "packet_acked",
        "metadata.actor",
        "consumption_actor",
    ),
    (
        "review_channel/agent_sync_projection.py::_is_consumption_by_agent",
        "packet_applied",
        "metadata.actor",
        "consumption_actor",
    ),
    (
        "review_channel/agent_sync_projection.py::_is_consumption_by_agent",
        "packet_dismissed",
        "metadata.actor",
        "consumption_actor",
    ),
    (
        "review_channel/agent_work_board_projection.py::_plan_row_for",
        "packet_posted",
        "target_kind",
        "plan_row_extraction",
    ),
    (
        "review_channel/agent_work_board_projection.py::_plan_row_for",
        "packet_posted",
        "target_ref",
        "plan_row_extraction",
    ),
)


def _flag_known_consumer_mismatches(
    inventory: dict[str, dict[str, object]],
) -> list[RiskHint]:
    """For each known consumer/field/event_type triple, flag if field is unpopulated."""
    risk_hints: list[RiskHint] = []
    for consumer, event_type, field, tag in _KNOWN_CONSUMER_FIELDS:
        shape = inventory.get(event_type)
        if not shape:
            continue
        top_keys = shape["top_level_keys"]
        meta_keys = shape["metadata_keys"]
        is_metadata_field = field.startswith("metadata.")
        leaf = field.removeprefix("metadata.") if is_metadata_field else field
        present = (
            leaf in meta_keys if is_metadata_field else leaf in top_keys  # type: ignore[operator]
        )
        if not present:
            risk_hints.append(
                RiskHint(
                    file=consumer.split("::")[0],
                    symbol=consumer.split("::", 1)[1] if "::" in consumer else "",
                    risk_type=f"event_field_naming_mismatch:{tag}",
                    severity="HIGH",
                    signals=[
                        f"event_type={event_type}",
                        f"reads={field}",
                        f"populated_in_live_events=0/{shape['count']}",
                    ],
                    ai_instruction=(
                        f"Field-naming mismatch ({tag}): the consumer reads "
                        f"{field!r} from {event_type} events, but 0 of "
                        f"{shape['count']} live events populate that path. "
                        f"Inspect a real event with `jq` and confirm the "
                        f"actual key shape. Update the consumer to read "
                        f"from the correct field path. Per memory rule "
                        f"feedback_recurring_bug_class_means_architecture_fix.md, "
                        f"this is the recurring bug class — verify against "
                        f"live event shape, do NOT band-aid."
                    ),
                    review_lens=REVIEW_LENS,
                )
            )
    return risk_hints


if __name__ == "__main__":
    raise SystemExit(main())
