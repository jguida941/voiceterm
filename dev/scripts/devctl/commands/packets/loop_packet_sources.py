"""Source-discovery helpers for `devctl loop-packet` packet generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from ...common import read_json_object, resolve_repo_path
from ...config import REPO_ROOT
from ...status_report import build_project_report
from ...triage.enrich import apply_defaults_to_issues, build_issue_rollup
from ...triage.support import build_next_actions, classify_issues


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
            warnings.append(f"{path}: unsupported command '{raw_command or 'missing'}'")
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
        preferred_command.value if preferred_command is not None else LoopPacketSourceCommand.TRIAGE_LOOP.value
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
    }
    payload["project"] = project_report
    payload["issues"] = issues
    payload["rollup"] = build_issue_rollup(issues)
    payload["next_actions"] = build_next_actions(issues)
    return ArtifactSourceRow(
        path="<generated:live-triage>",
        command=LoopPacketSourceCommand.TRIAGE.value,
        payload=payload,
        timestamp=_parse_iso_timestamp(payload.get("timestamp")),
        mtime=datetime.now(UTC).timestamp(),
    )
