"""Typed projections for `devctl phone-status` views."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class PhoneStatusView(str, Enum):
    FULL = "full"
    TRACE = "trace"
    ACTIONS = "actions"
    COMPACT = "compact"

    @classmethod
    def parse(cls, raw_value: object) -> PhoneStatusView:
        normalized = str(raw_value or cls.COMPACT.value).strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        return cls.COMPACT


@dataclass(frozen=True)
class CompactPhoneStatusProjection:
    schema_version: int
    view: str
    phase: str
    reason: str
    plan_id: str
    controller_run_id: str
    branch_base: str
    mode_effective: str
    resolved: bool
    rounds_completed: int
    max_rounds: int
    tasks_completed: int
    max_tasks: int
    latest_working_branch: str
    unresolved_count: int
    risk: str
    source_run_url: str
    source_run_id: Any
    source_run_sha: Any
    trace_lines: int
    draft_preview: str
    next_actions: list[str]
    ralph_phase: str
    ralph_fix_rate_pct: float
    ralph_unresolved: int
    warnings_count: int
    errors_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TracePhoneStatusProjection:
    schema_version: int
    view: str
    controller_run_id: str
    phase: str
    reason: str
    trace: list[str]
    draft_text: str
    auto_send: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionsPhoneStatusProjection:
    schema_version: int
    view: str
    controller_run_id: str
    phase: str
    reason: str
    next_actions: list[str]
    operator_actions: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
