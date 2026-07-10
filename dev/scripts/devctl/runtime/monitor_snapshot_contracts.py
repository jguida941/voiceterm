"""Typed contracts for the monitor snapshot surface."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class MonitorSourceLabel:
    """One classified input source used by the monitor snapshot."""

    source_id: str
    classification: str
    path: str
    present: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MonitorSelfAudit:
    """Bounded self-audit decision derived from monitor state."""

    should_emit_finding: bool
    finding_type: str
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return dict(
            [
                ("should_emit_finding", self.should_emit_finding),
                ("finding_type", self.finding_type),
                ("reasons", list(self.reasons)),
            ]
        )


@dataclass(frozen=True, slots=True)
class MonitorSnapshot:
    """Typed remote-phone monitor snapshot."""

    schema_version: int
    contract_id: str
    command: str
    timestamp: str
    snapshot_id: str
    mode: str
    agent: str
    canonical_runtime_state: dict[str, object]
    observational_telemetry: dict[str, object]
    verdict_presence: dict[str, object]
    worktree_state: dict[str, object]
    source_labels: tuple[MonitorSourceLabel, ...]
    summary: dict[str, object]
    self_audit: MonitorSelfAudit

    def to_dict(self) -> dict[str, object]:
        return dict(
            [
                ("schema_version", self.schema_version),
                ("contract_id", self.contract_id),
                ("command", self.command),
                ("timestamp", self.timestamp),
                ("snapshot_id", self.snapshot_id),
                ("mode", self.mode),
                ("agent", self.agent),
                ("canonical_runtime_state", dict(self.canonical_runtime_state)),
                ("observational_telemetry", dict(self.observational_telemetry)),
                ("verdict_presence", dict(self.verdict_presence)),
                ("worktree_state", dict(self.worktree_state)),
                ("source_labels", [row.to_dict() for row in self.source_labels]),
                ("summary", dict(self.summary)),
                ("self_audit", self.self_audit.to_dict()),
            ]
        )


@dataclass(frozen=True, slots=True)
class MonitorSnapshotPaths:
    """Written monitor snapshot bundle paths."""

    root_dir: str
    json_path: str
    markdown_path: str
