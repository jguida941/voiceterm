"""Shared helper logic for `devctl loop-packet` packet generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from ..common import read_json_object, resolve_repo_path
from ..config import REPO_ROOT
from ..status_report import build_project_report
from ..triage.enrich import apply_defaults_to_issues, build_issue_rollup
from ..triage.support import build_next_actions, classify_issues


class LoopPacketSourceCommand(StrEnum):
    TRIAGE_LOOP = "triage-loop"
    MUTATION_LOOP = "mutation-loop"
    TRIAGE = "triage"

    @classmethod
    def parse(cls, value: Any) -> LoopPacketSourceCommand | None:
        normalized = str(value or "").strip().lower()
        if normalized == "mutation_loop":
            normalized = cls.MUTATION_LOOP.value
        try:
            return cls(normalized)
        except ValueError:
            return None


ALLOWED_SOURCE_COMMANDS = frozenset(command.value for command in LoopPacketSourceCommand)
SYSTEM_TMPDIR = Path(gettempdir())
DEFAULT_SOURCE_CANDIDATES = (
    ".cihub/coderabbit/coderabbit-ralph-loop.json",
    ".cihub/mutation/mutation-ralph-loop.json",
    ".cihub/devctl-triage.ai.json",
    str(SYSTEM_TMPDIR / "coderabbit-ralph-loop.json"),
    str(SYSTEM_TMPDIR / "mutation-ralph-loop.json"),
    str(SYSTEM_TMPDIR / "devctl-triage.ai.json"),
)
RISK_CONFIDENCE = {"low": 0.9, "medium": 0.65, "high": 0.45}


@dataclass(frozen=True)
class ArtifactSourceRow:
    """One discovered or generated source artifact used to build a loop packet."""

    path: str
    command: str
    payload: dict[str, Any]
    timestamp: datetime | None
    mtime: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "command": self.command,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "mtime": self.mtime,
        }


def _truncate_chars(value: str, max_chars: int) -> str:
    trimmed = str(value)
    if max_chars <= 0:
        return ""
    if len(trimmed) <= max_chars:
        return trimmed
    return trimmed[: max_chars - 3] + "..."


def _parse_iso_timestamp(raw_value: Any) -> datetime | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _freshness_hours(timestamp: datetime, now_utc: datetime) -> float:
    age_seconds = max((now_utc - timestamp).total_seconds(), 0.0)
    return age_seconds / 3600.0


def _discover_artifact_sources(
    source_paths: list[str],
) -> tuple[list[ArtifactSourceRow], list[str], list[str]]:
    rows: list[ArtifactSourceRow] = []
    warnings: list[str] = []
    checked_paths: list[str] = []
    for raw_path in source_paths:
        path = resolve_repo_path(raw_path, repo_root=REPO_ROOT)
        checked_paths.append(str(path))
        if not path.exists():
            continue
        payload, read_error = read_json_object(
            path,
            missing_message="{path}: file does not exist",
        )
        if read_error:
            warnings.append(f"{path}: {read_error}")
            continue
        if not isinstance(payload, dict):
            warnings.append(f"{path}: unexpected non-object payload")
            continue
        command = LoopPacketSourceCommand.parse(payload.get("command"))
        if command is None:
            raw_command = str(payload.get("command") or "").strip().lower()
            warnings.append(
                f"{path}: unsupported command '{raw_command or 'missing'}'"
            )
            continue
        timestamp = _parse_iso_timestamp(payload.get("timestamp"))
        rows.append(
            ArtifactSourceRow(
                path=str(path),
                command=command.value,
                payload=payload,
                timestamp=timestamp,
                mtime=path.stat().st_mtime,
            )
        )
    return rows, warnings, checked_paths


def _choose_source(
    *,
    rows: list[ArtifactSourceRow],
    prefer_source: str,
) -> ArtifactSourceRow | None:
    if not rows:
        return None
    preferred_command = LoopPacketSourceCommand.parse(prefer_source)
    preferred_value = (
        preferred_command.value
        if preferred_command is not None
        else LoopPacketSourceCommand.TRIAGE_LOOP.value
    )
    command_order = [preferred_value] + [
        name
        for name in (
            LoopPacketSourceCommand.TRIAGE_LOOP.value,
            LoopPacketSourceCommand.MUTATION_LOOP.value,
            LoopPacketSourceCommand.TRIAGE.value,
        )
        if name != preferred_value
    ]
    rank = {name: idx for idx, name in enumerate(command_order)}

    def sort_key(row: ArtifactSourceRow) -> tuple[int, float]:
        command_rank = rank.get(row.command, len(command_order))
        if isinstance(row.timestamp, datetime):
            freshness_seed = row.timestamp.timestamp()
        else:
            freshness_seed = row.mtime
        return command_rank, -freshness_seed

    ordered = sorted(rows, key=sort_key)
    return ordered[0] if ordered else None


def _build_live_triage_source() -> ArtifactSourceRow:
    project_report = build_project_report(
        command="loop-packet",
        include_ci=True,
        ci_limit=10,
        include_dev_logs=False,
        dev_root=None,
        dev_sessions_limit=5,
        include_probe_report=True,
    )
    issues = apply_defaults_to_issues(classify_issues(project_report), {})
    payload = {
        "command": LoopPacketSourceCommand.TRIAGE.value,
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "project": project_report,
        "issues": issues,
        "rollup": build_issue_rollup(issues),
        "next_actions": build_next_actions(issues),
    }
    return ArtifactSourceRow(
        path="<generated:live-triage>",
        command=LoopPacketSourceCommand.TRIAGE.value,
        payload=payload,
        timestamp=_parse_iso_timestamp(payload.get("timestamp")),
        mtime=datetime.now(UTC).timestamp(),
    )


def _build_packet_body(
    *,
    source_command: str,
    payload: dict[str, Any],
) -> tuple[str, str, list[str]]:
    if source_command == "triage-loop":
        unresolved = int(payload.get("unresolved_count") or 0)
        reason = str(payload.get("reason") or "unknown")
        branch = str(payload.get("branch") or "unknown")
        source_run = payload.get("source_run_id")
        context = [
            f"CodeRabbit loop snapshot for branch `{branch}`.",
            f"Reason: `{reason}`.",
            f"Unresolved medium/high findings: `{unresolved}`.",
        ]
        if isinstance(source_run, int) and source_run > 0:
            context.append(f"Source run id: `{source_run}`.")
        risk = "low" if unresolved == 0 else ("high" if unresolved > 8 else "medium")
        actions = []
        if unresolved == 0:
            actions.append("No medium/high backlog remains. Continue with normal CI verification.")
        else:
            actions.append("Review unresolved findings and apply bounded fixes with the same source run correlation.")
            actions.append("Re-run report-only loop and verify unresolved count trends downward.")
        draft = "\n".join(
            [
                "Loop feedback packet:",
                *context,
                "",
                "Task: propose the next bounded remediation step with guardrails and verification.",
            ]
        )
        return risk, draft, actions
    if source_command == "mutation-loop":
        score = payload.get("last_score")
        threshold = payload.get("threshold")
        reason = str(payload.get("reason") or "unknown")
        branch = str(payload.get("branch") or "unknown")
        score_text = "n/a" if score is None else f"{float(score):.2%}"
        threshold_text = "n/a" if threshold is None else f"{float(threshold):.2%}"
        below_threshold = (
            isinstance(score, int | float) and isinstance(threshold, int | float) and float(score) < float(threshold)
        )
        risk = "high" if below_threshold else "low"
        hotspots = payload.get("last_hotspots") if isinstance(payload.get("last_hotspots"), list) else []
        hotspot_items: list[str] = []
        for row in hotspots[:3]:
            if not isinstance(row, dict):
                continue
            module = str(row.get("module") or row.get("target") or row.get("path") or "unknown")
            missed = row.get("missed")
            if isinstance(missed, int):
                hotspot_items.append(f"{module} (missed={missed})")
            else:
                hotspot_items.append(module)

        actions = []
        if below_threshold:
            actions.append("Prioritize mutation hotspots and add focused tests before enabling fix mode.")
        else:
            actions.append("Mutation score meets threshold. Keep report-only monitoring active.")
        if hotspot_items:
            actions.append("Top hotspots: " + ", ".join(hotspot_items))

        lines = [
            "Loop feedback packet:",
            f"Mutation loop snapshot for branch `{branch}`.",
            f"Reason: `{reason}`.",
            f"Score `{score_text}` vs threshold `{threshold_text}`.",
            "",
            "Task: propose the smallest safe test/code change sequence to improve confidence.",
        ]
        return risk, "\n".join(lines), actions

    rollup = payload.get("rollup") if isinstance(payload.get("rollup"), dict) else {}
    total = int(rollup.get("total") or 0)
    by_severity = rollup.get("by_severity") if isinstance(rollup.get("by_severity"), dict) else {}
    high = int(by_severity.get("high") or 0)
    medium = int(by_severity.get("medium") or 0)
    if high > 0:
        risk = "high"
    elif medium > 0:
        risk = "medium"
    else:
        risk = "low"
    next_actions = payload.get("next_actions")
    actions = [str(row).strip() for row in next_actions] if isinstance(next_actions, list) else []
    actions = [row for row in actions if row]
    if not actions:
        actions = ["No explicit next actions found; review triage snapshot and owners."]
    lines = [
        "Loop feedback packet:",
        "Triage snapshot from local control-plane signals.",
        f"Issue rollup: total={total}, high={high}, medium={medium}.",
        "",
        "Task: convert this triage snapshot into an ordered, guarded execution plan.",
    ]
    return risk, "\n".join(lines), actions


def _auto_send_eligible(source_command: str, payload: dict[str, Any], risk: str) -> bool:
    if risk != "low":
        return False
    selected_source = LoopPacketSourceCommand.parse(source_command)
    if selected_source is LoopPacketSourceCommand.TRIAGE_LOOP:
        unresolved = int(payload.get("unresolved_count") or 0)
        return unresolved == 0 and str(payload.get("reason") or "") == "resolved"
    if selected_source is LoopPacketSourceCommand.MUTATION_LOOP:
        return str(payload.get("reason") or "") == "threshold_met"
    if selected_source is LoopPacketSourceCommand.TRIAGE:
        rollup = payload.get("rollup") if isinstance(payload.get("rollup"), dict) else {}
        return int(rollup.get("total") or 0) == 0
    return False
