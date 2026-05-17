#!/usr/bin/env python3
"""Report task_started packets missing ADR/evidence linkage.

P7 guard: codex task_started packets created in response to finding/mandate
packets must preserve the evidence chain, plan-family anchor, and ADR-style
precedent context instead of relying on body prose alone. The originating
mandate packet remains policy-owned in devctl_repo_policy.json.

The guard is report-only while historical task_started packets are being
backfilled. `would_fail` tracks the future strict-mode baseline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


COMMAND = "check_task_started_adr_precedent_linking"
TASK_STARTED_ADR_PRECEDENT_GUARD_ID = "TaskStartedAdrPrecedentLinking"
TASK_STARTED_ADR_PRECEDENT_CONTRACT_ID = "TaskStartedAdrPrecedentLinkingGuard"
DEFAULT_EVENT_LOG_REL = "dev/reports/review_channel/events/trace.ndjson"

_PACKET_REF_RE = re.compile(r"\brev_pkt_\d+\b")
_PLAN_FAMILY_RE = re.compile(r"\bMP-\d+\b")
_ADR_MARKERS = (
    "precedent_packet_ids:",
    "adoption_rationale:",
    "status: extends",
    "status: refines",
    "status_extends:",
)


@dataclass(frozen=True, slots=True)
class TaskStartedAdrPrecedentLinkingGuard:
    """Registry-facing contract for task_started ADR/evidence linking."""

    guard_id: str
    ok: bool
    report_only: bool
    would_fail: bool
    event_log_path: str
    task_started_count: int = 0
    precedent_linked_count: int = 0
    violation_count: int = 0
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = 1
    contract_id: str = "TaskStartedAdrPrecedentLinkingGuard"
    command: str = COMMAND


@dataclass(frozen=True)
class TaskStartedPacket:
    line_number: int
    packet_id: str
    event_type: str
    plan_id: str
    summary: str
    body: str
    evidence_refs: tuple[str, ...]
    anchor_refs: tuple[str, ...]
    guidance_refs: tuple[str, ...]


@dataclass(frozen=True)
class TaskStartedAdrViolation:
    line_number: int
    packet_id: str
    plan_id: str
    expected_plan_family: str
    missing: tuple[str, ...]
    precedent_packet_ids: tuple[str, ...]
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "line_number": self.line_number,
            "packet_id": self.packet_id,
            "plan_id": self.plan_id,
            "expected_plan_family": self.expected_plan_family,
            "missing": list(self.missing),
            "precedent_packet_ids": list(self.precedent_packet_ids),
            "detail": self.detail,
        }


def evaluate_task_started_adr_precedent_linking(
    *,
    repo_root: Path = REPO_ROOT,
    event_log_path: Path | None = None,
) -> TaskStartedAdrPrecedentLinkingGuard:
    resolved_event_log = event_log_path or repo_root / DEFAULT_EVENT_LOG_REL
    packets, errors = _read_latest_task_started_packets(resolved_event_log)
    violations: list[TaskStartedAdrViolation] = []
    precedent_linked_count = 0
    for packet in packets:
        precedent_packet_ids = _precedent_packet_ids(packet)
        if not precedent_packet_ids:
            continue
        precedent_linked_count += 1
        missing = _missing_links(packet)
        if not missing:
            continue
        expected_plan_family = _expected_plan_family(packet)
        violations.append(
            TaskStartedAdrViolation(
                line_number=packet.line_number,
                packet_id=packet.packet_id,
                plan_id=packet.plan_id,
                expected_plan_family=expected_plan_family,
                missing=missing,
                precedent_packet_ids=precedent_packet_ids,
                detail=(
                    "task_started packets that cite preceding packets must carry "
                    "evidence_refs, packet and plan anchors, ADR precedent text, "
                    "and a matching plan_id family."
                ),
            )
        )

    return TaskStartedAdrPrecedentLinkingGuard(
        guard_id=TASK_STARTED_ADR_PRECEDENT_GUARD_ID,
        ok=True,
        report_only=True,
        would_fail=bool(violations or errors),
        event_log_path=_display_path(resolved_event_log, repo_root=repo_root),
        task_started_count=len(packets),
        precedent_linked_count=precedent_linked_count,
        violation_count=len(violations),
        violations=tuple(violation.to_dict() for violation in violations[:50]),
        errors=tuple(errors),
    )


def _read_latest_task_started_packets(
    path: Path,
) -> tuple[list[TaskStartedPacket], list[str]]:
    latest: dict[str, TaskStartedPacket] = {}
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"event_log_read_failed:{exc.__class__.__name__}:{path}"]
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid_event_jsonl:{line_number}:{exc.msg}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"non_object_event:{line_number}")
            continue
        packet = _packet_from_event(line_number, payload)
        if packet is None:
            continue
        latest[packet.packet_id] = packet
    return list(latest.values()), errors


def _packet_from_event(
    line_number: int,
    payload: dict[str, object],
) -> TaskStartedPacket | None:
    if _text(payload.get("from_agent")) != "codex":
        return None
    if _text(payload.get("kind")) != "task_started":
        return None
    if _text(payload.get("event_type")) not in {"packet_posted", "packet_applied"}:
        return None
    packet_id = _text(payload.get("packet_id"))
    if not packet_id:
        return None
    return TaskStartedPacket(
        line_number=line_number,
        packet_id=packet_id,
        event_type=_text(payload.get("event_type")),
        plan_id=_text(payload.get("plan_id")),
        summary=_text(payload.get("summary")),
        body=_text(payload.get("body")),
        evidence_refs=_refs(payload.get("evidence_refs")),
        anchor_refs=_refs(payload.get("anchor_refs")),
        guidance_refs=_refs(payload.get("guidance_refs")),
    )


def _precedent_packet_ids(packet: TaskStartedPacket) -> tuple[str, ...]:
    refs = [
        packet.summary,
        packet.body,
        *packet.evidence_refs,
        *packet.anchor_refs,
        *packet.guidance_refs,
    ]
    seen: set[str] = set()
    packet_ids: list[str] = []
    for ref in refs:
        for match in _PACKET_REF_RE.findall(ref):
            if match == packet.packet_id or match in seen:
                continue
            seen.add(match)
            packet_ids.append(match)
    return tuple(packet_ids)


def _missing_links(packet: TaskStartedPacket) -> tuple[str, ...]:
    missing: list[str] = []
    if not _has_packet_ref(packet.evidence_refs):
        missing.append("evidence_refs.packet")
    if not _has_packet_ref(packet.anchor_refs):
        missing.append("anchor_refs.packet")
    if not _has_plan_anchor(packet.anchor_refs):
        missing.append("anchor_refs.plan_or_section")
    if not _has_adr_precedent_block(packet.body):
        missing.append("adr_precedent_block")
    expected_plan_family = _expected_plan_family(packet)
    if expected_plan_family and packet.plan_id != expected_plan_family:
        missing.append("plan_id_matches_work_family")
    return tuple(missing)


def _expected_plan_family(packet: TaskStartedPacket) -> str:
    haystack = " ".join(
        (
            packet.summary,
            packet.body,
            " ".join(packet.anchor_refs),
            " ".join(packet.evidence_refs),
        )
    )
    for family in _PLAN_FAMILY_RE.findall(haystack):
        if family != packet.plan_id:
            return family
    return packet.plan_id


def _has_adr_precedent_block(body: str) -> bool:
    lower_body = body.lower()
    return any(marker in lower_body for marker in _ADR_MARKERS)


def _has_packet_ref(refs: tuple[str, ...]) -> bool:
    return any(_PACKET_REF_RE.search(ref) for ref in refs)


def _has_plan_anchor(refs: tuple[str, ...]) -> bool:
    return any(ref.startswith(("plan:MP-", "section:MP-")) for ref in refs)


def _refs(value: object) -> tuple[str, ...]:
    if isinstance(value, list | tuple):
        return tuple(_text(item) for item in value if _text(item))
    return ()


def _text(value: object) -> str:
    return str(value or "").strip()


def _display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def _render_md(report: TaskStartedAdrPrecedentLinkingGuard) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- report_only: {report.report_only}")
    lines.append(f"- would_fail: {report.would_fail}")
    lines.append(f"- event_log_path: {report.event_log_path}")
    lines.append(f"- task_started_count: {report.task_started_count}")
    lines.append(f"- precedent_linked_count: {report.precedent_linked_count}")
    lines.append(f"- violation_count: {report.violation_count}")
    if report.errors:
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in report.errors)
    if report.violations:
        lines.append("")
        lines.append("## Violations (first 50)")
        for violation in report.violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                "- "
                f"line {violation.get('line_number')} "
                f"`{violation.get('packet_id')}` missing "
                f"{', '.join(violation.get('missing') or [])}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-log", default=DEFAULT_EVENT_LOG_REL)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = evaluate_task_started_adr_precedent_linking(
        event_log_path=REPO_ROOT / args.event_log,
    )
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(_render_md(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
