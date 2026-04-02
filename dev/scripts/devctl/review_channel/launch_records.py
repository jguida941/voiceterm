"""Typed launch request and session-record helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..approval_mode import DEFAULT_APPROVAL_MODE

if TYPE_CHECKING:
    from .core import LaneAssignment


@dataclass(slots=True)
class LaunchSessionRequest:
    repo_root: Path
    review_channel_path: Path
    bridge_path: Path
    codex_lanes: list["LaneAssignment"]
    claude_lanes: list["LaneAssignment"]
    codex_workers: int
    claude_workers: int
    rollover_threshold_pct: int
    await_ack_seconds: int
    retirement_note: str
    promotion_plan_rel: str
    approval_mode: str = DEFAULT_APPROVAL_MODE
    dangerous: bool = False
    bridge_liveness: dict[str, object] | None = None
    handoff_bundle: dict[str, str] | None = None
    script_dir: Path | None = None
    session_output_root: Path | None = None
    cursor_lanes: list["LaneAssignment"] | None = None
    cursor_workers: int = 0
    provider_lane_map: dict[str, list["LaneAssignment"]] | None = None
    requested_worker_budgets: dict[str, int | None] | None = None
    providers_to_launch: tuple[str, ...] | None = None


@dataclass(slots=True)
class PreparedSessionRecord:
    session_name: str
    provider: str
    provider_name: str
    role: str
    approval_mode: str
    planned_lanes: list["LaneAssignment"]
    requested_worker_budget: int
    repo_root: Path
    script_path: Path
    launch_command: str
    prepared_at: str
    terminal_window_id: int | None = None
    log_path: Path | None = None
    metadata_path: Path | None = None

    def write_metadata(self) -> None:
        if self.metadata_path is None or self.log_path is None:
            return
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.write_text(
            json.dumps(self.metadata_payload(), indent=2),
            encoding="utf-8",
        )

    def metadata_payload(self) -> dict[str, object]:
        assert self.log_path is not None
        return asdict(
            SessionMetadataPayload(
                provider=self.provider,
                provider_name=self.provider_name,
                session_name=self.session_name,
                capture_mode="terminal-script",
                prepared_at=self.prepared_at,
                repo_root=str(self.repo_root),
                script_path=str(self.script_path),
                log_path=str(self.log_path),
                launch_command=self.launch_command,
                supervision_mode="restart-on-clean-exit",
                approval_mode=self.approval_mode,
                role=self.role,
                planned_lane_count=len(self.planned_lanes),
                requested_worker_budget=self.requested_worker_budget,
                terminal_window_id=self.terminal_window_id,
                planned_lanes=[asdict(lane) for lane in self.planned_lanes],
            )
        )

    def report_payload(self) -> dict[str, object]:
        return asdict(
            SessionReportPayload(
                session_name=self.session_name,
                provider=self.provider,
                requested_worker_budget=self.requested_worker_budget,
                approval_mode=self.approval_mode,
                role=self.role,
                planned_lane_count=len(self.planned_lanes),
                planned_lanes=[asdict(lane) for lane in self.planned_lanes],
                script_path=str(self.script_path),
                launch_command=self.launch_command,
                log_path=str(self.log_path) if self.log_path is not None else None,
                supervision_mode="restart-on-clean-exit",
                metadata_path=(
                    str(self.metadata_path) if self.metadata_path is not None else None
                ),
                capture_mode="terminal-script" if self.log_path is not None else None,
                terminal_window_id=self.terminal_window_id,
            )
        )


@dataclass(frozen=True, slots=True)
class SessionMetadataPayload:
    provider: str
    provider_name: str
    session_name: str
    capture_mode: str
    prepared_at: str
    repo_root: str
    script_path: str
    log_path: str
    launch_command: str
    supervision_mode: str
    approval_mode: str
    role: str
    planned_lane_count: int
    requested_worker_budget: int
    terminal_window_id: int | None
    planned_lanes: list[dict[str, object]]


@dataclass(frozen=True, slots=True)
class SessionReportPayload:
    session_name: str
    provider: str
    requested_worker_budget: int
    approval_mode: str
    role: str
    planned_lane_count: int
    planned_lanes: list[dict[str, object]]
    script_path: str
    launch_command: str
    log_path: str | None
    supervision_mode: str
    metadata_path: str | None
    capture_mode: str | None
    terminal_window_id: int | None


def legacy_provider_lane_map(
    *,
    codex_lanes: list["LaneAssignment"],
    claude_lanes: list["LaneAssignment"],
    cursor_lanes: list["LaneAssignment"] | None,
) -> dict[str, list["LaneAssignment"]]:
    provider_lane_map = {
        "codex": codex_lanes,
        "claude": claude_lanes,
    }
    if cursor_lanes:
        provider_lane_map["cursor"] = cursor_lanes
    return provider_lane_map


def session_output_paths(
    *,
    session_dir: Path | None,
    session_name: str,
) -> tuple[Path | None, Path | None]:
    if session_dir is None:
        return None, None
    return (
        session_dir / f"{session_name}.log",
        session_dir / f"{session_name}.json",
    )
