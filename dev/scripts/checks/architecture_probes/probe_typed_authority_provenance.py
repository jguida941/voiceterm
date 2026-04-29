"""Probe typed authority surfaces for missing provenance and decisions."""

from __future__ import annotations

import json
from pathlib import Path
import sys

try:
    from probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.probe_support.bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )

try:
    from dev.scripts.devctl.config import REPO_ROOT
except ModuleNotFoundError:  # pragma: no cover
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
    from dev.scripts.devctl.config import REPO_ROOT

COMMAND = "probe_typed_authority_provenance"
AUTHORITY_DOCS = [
    "dev/scripts/devctl/runtime/master_plan_contract.py",
    "dev/scripts/devctl/runtime/instruction_authority.py",
    "dev/scripts/devctl/review_channel/instruction_transitions.py",
]
REQUIRED_PROVENANCE_FIELDS = (
    "source_file",
    "source_line",
    "source_kind",
    "source_hash",
    "observed_at_utc",
    "section_authority",
)


def build_provenance_hints(repo_root: Path) -> list[RiskHint]:
    """Return risk hints for typed authority rows missing proof fields."""
    hints: list[RiskHint] = []
    hints.extend(_plan_row_hints(repo_root))
    hints.extend(_queue_hints(repo_root))
    return hints


def _plan_row_hints(repo_root: Path) -> list[RiskHint]:
    path = repo_root / "dev/state/plan_index.jsonl"
    if not path.exists():
        return []
    hints: list[RiskHint] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        payload = _loads(line)
        if not isinstance(payload, dict):
            continue
        missing = _missing_provenance_fields(payload.get("provenance"))
        if not missing:
            continue
        row_id = str(payload.get("row_id") or f"line-{line_number}")
        hints.append(
            _hint(
                file="dev/state/plan_index.jsonl",
                symbol=row_id,
                signals=[
                    f"row_id={row_id}",
                    "missing_provenance=" + ",".join(missing),
                ],
                instruction=(
                    "Every PlanRow that can drive authority must carry "
                    "IngestionProvenance. Re-ingest the row through the typed "
                    "adapter or attach source_file/source_line/source_kind/"
                    "source_hash/observed_at_utc/section_authority before "
                    "treating it as executable state."
                ),
            )
        )
    return hints


def _queue_hints(repo_root: Path) -> list[RiskHint]:
    path = repo_root / "dev/reports/review_channel/projections/latest/review_state.json"
    payload = _read_json(path)
    queue = payload.get("queue") if isinstance(payload, dict) else None
    if not isinstance(queue, dict):
        return []
    instruction = str(queue.get("derived_next_instruction") or "").strip()
    if not instruction:
        return []

    source = queue.get("derived_next_instruction_source")
    if not isinstance(source, dict):
        source = {}
    hints: list[RiskHint] = []
    missing = _missing_provenance_fields(source.get("provenance"))
    if missing:
        hints.append(
            _hint(
                file="dev/reports/review_channel/projections/latest/review_state.json",
                symbol="queue.derived_next_instruction_source",
                signals=["missing_provenance=" + ",".join(missing)],
                instruction=(
                    "Queue-derived instructions are runtime authority. Attach "
                    "IngestionProvenance to derived_next_instruction_source so "
                    "downstream surfaces can prove where the active instruction "
                    "came from."
                ),
            )
        )
    decision = queue.get("instruction_priority_decision") or source.get(
        "priority_decision"
    )
    if not isinstance(decision, dict) or not decision.get("contract_id"):
        hints.append(
            _hint(
                file="dev/reports/review_channel/projections/latest/review_state.json",
                symbol="queue.instruction_priority_decision",
                signals=["missing InstructionPriorityDecision"],
                instruction=(
                    "Queue projection must include InstructionPriorityDecision "
                    "for every active instruction so operators can ask why that "
                    "signal won over alternatives."
                ),
            )
        )
    return hints


def _missing_provenance_fields(value: object) -> tuple[str, ...]:
    if not isinstance(value, dict):
        return REQUIRED_PROVENANCE_FIELDS
    missing: list[str] = []
    for field in REQUIRED_PROVENANCE_FIELDS:
        if field == "source_line":
            if value.get(field) is None:
                missing.append(field)
            continue
        if not str(value.get(field) or "").strip():
            missing.append(field)
    return tuple(missing)


def _hint(
    *,
    file: str,
    symbol: str,
    signals: list[str],
    instruction: str,
) -> RiskHint:
    return RiskHint(
        file=file,
        symbol=symbol,
        risk_type="typed_authority_missing_provenance",
        severity="high",
        signals=signals,
        ai_instruction=instruction,
        review_lens="architecture",
        attach_docs=AUTHORITY_DOCS,
    )


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _loads(line: str) -> object:
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return {}


def build_report(*, since_ref: str | None, head_ref: str) -> ProbeReport:
    hints = build_provenance_hints(REPO_ROOT)
    return ProbeReport(
        command=COMMAND,
        risk_hints=hints,
        files_scanned=2,
        files_with_hints=len({hint.file for hint in hints}),
        since_ref=since_ref,
        head_ref=head_ref,
    )


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = build_report(since_ref=args.since_ref, head_ref=args.head_ref)
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    raise SystemExit(main())
