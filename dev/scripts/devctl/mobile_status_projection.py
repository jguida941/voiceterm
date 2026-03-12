"""Typed projections and helpers for mobile-status views."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class MobileStatusView(StrEnum):
    FULL = "full"
    COMPACT = "compact"
    ALERT = "alert"
    ACTIONS = "actions"


@dataclass(frozen=True)
class OperatorActionPayload:
    name: str
    command: str
    kind: str
    guard: str = "none"


@dataclass(frozen=True)
class CompactMobileStatusProjection:
    headline: str
    controller_phase: str
    controller_reason: str
    controller_risk: str
    plan_id: str
    controller_run_id: str
    review_bridge_state: str
    codex_poll_state: str
    codex_last_poll_utc: str
    last_worktree_hash: str
    pending_total: int
    unresolved_count: int
    current_instruction: str
    open_findings: str
    claude_status: str
    claude_ack: str
    codex_status: str
    claude_lane_status: str
    operator_status: str
    source_run_url: str
    approval_mode: str
    approval_summary: str
    next_actions: list[str] = field(default_factory=list)
    schema_version: int = 1
    view: str = MobileStatusView.COMPACT.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AlertMobileStatusProjection:
    severity: str
    summary: str
    approval_mode: str
    approval_summary: str
    why: list[str] = field(default_factory=list)
    current_instruction: str = ""
    next_actions: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    schema_version: int = 1
    view: str = MobileStatusView.ALERT.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionsMobileStatusProjection:
    summary: str
    approval_mode: str
    approval_summary: str
    next_actions: list[str] = field(default_factory=list)
    operator_actions: list[OperatorActionPayload] = field(default_factory=list)
    schema_version: int = 1
    view: str = MobileStatusView.ACTIONS.value

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_mobile_status_view(view: str | MobileStatusView) -> MobileStatusView:
    if isinstance(view, MobileStatusView):
        return view
    try:
        return MobileStatusView(str(view).strip().lower())
    except ValueError:
        return MobileStatusView.COMPACT


def string_rows(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    rows: list[str] = []
    for row in value:
        text = str(row).strip()
        if text:
            rows.append(text)
    return rows


def operator_action_rows(value: Any) -> list[OperatorActionPayload]:
    if not isinstance(value, list):
        return []
    rows: list[OperatorActionPayload] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        rows.append(
            OperatorActionPayload(
                name=str(row.get("name") or "action"),
                command=str(row.get("command") or ""),
                kind=str(row.get("kind") or "unknown"),
                guard=str(row.get("guard") or "none"),
            )
        )
    return rows


def append_bullets(lines: list[str], rows: list[str]) -> None:
    if rows:
        for row in rows:
            lines.append(f"- {row}")
        return
    lines.append("- none")


def append_operator_actions(
    lines: list[str],
    operator_actions: list[OperatorActionPayload],
) -> None:
    if operator_actions:
        for row in operator_actions:
            lines.append(f"- {row.name} ({row.kind}, guard={row.guard}): `{row.command}`")
        return
    lines.append("- none")
