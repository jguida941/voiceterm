"""Typed launch request and session-record helpers."""

from __future__ import annotations

from collections.abc import Sequence
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
    headless: bool = False
    bridge_liveness: dict[str, object] | None = None
    handoff_bundle: dict[str, str] | None = None
    script_dir: Path | None = None
    session_output_root: Path | None = None
    cursor_lanes: list["LaneAssignment"] | None = None
    cursor_workers: int = 0
    provider_lane_map: dict[str, list["LaneAssignment"]] | None = None
    requested_worker_budgets: dict[str, int | None] | None = None
    providers_to_launch: tuple[str, ...] | None = None
    interaction_mode: str = ""
    rollover_provider: str = ""
    review_state_path: Path | None = None
    worktree_path: Path | None = None


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
    interaction_mode: str = ""
    rollover_provider: str = ""
    prepared_head_sha: str = ""
    prepared_instruction_revision: str = ""
    prepared_session_token: str = ""
    review_state_path: Path | None = None
    workspace_root: Path | None = None

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
                interaction_mode=self.interaction_mode,
                rollover_provider=self.rollover_provider,
                prepared_head_sha=self.prepared_head_sha,
                prepared_instruction_revision=self.prepared_instruction_revision,
                prepared_session_token=self.prepared_session_token,
                review_state_path=(
                    str(self.review_state_path)
                    if self.review_state_path is not None
                    else ""
                ),
                workspace_root=(
                    str(self.workspace_root) if self.workspace_root is not None else ""
                ),
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
                interaction_mode=self.interaction_mode,
                rollover_provider=self.rollover_provider,
                prepared_head_sha=self.prepared_head_sha,
                prepared_instruction_revision=self.prepared_instruction_revision,
                prepared_session_token=self.prepared_session_token,
                review_state_path=(
                    str(self.review_state_path)
                    if self.review_state_path is not None
                    else None
                ),
                workspace_root=(
                    str(self.workspace_root)
                    if self.workspace_root is not None
                    else None
                ),
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
    interaction_mode: str = ""
    rollover_provider: str = ""
    prepared_head_sha: str = ""
    prepared_instruction_revision: str = ""
    prepared_session_token: str = ""
    review_state_path: str = ""
    workspace_root: str = ""


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
    interaction_mode: str = ""
    rollover_provider: str = ""
    prepared_head_sha: str = ""
    prepared_instruction_revision: str = ""
    prepared_session_token: str = ""
    review_state_path: str | None = None
    workspace_root: str | None = None


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


def resolve_lane_worktree_path(
    *,
    repo_root: Path,
    lane: "LaneAssignment",
) -> Path:
    """Resolve one planned lane worktree to an absolute workspace path."""
    return _resolve_worktree_path(repo_root, getattr(lane, "worktree", ""))


def resolve_session_workspace_root(
    *,
    repo_root: Path,
    lanes: Sequence["LaneAssignment"],
    default_worktree_path: Path | None = None,
) -> Path:
    """Resolve the single workspace root a launched provider session may own."""
    resolved_repo_root = repo_root.resolve()
    explicit_rows: list[tuple[str, Path]] = []
    for lane in lanes:
        raw_worktree = str(getattr(lane, "worktree", "") or "").strip()
        if not raw_worktree:
            continue
        explicit_rows.append(
            (
                str(getattr(lane, "agent_id", "") or "").strip() or "lane",
                _resolve_worktree_path(resolved_repo_root, raw_worktree),
            )
        )
    if not explicit_rows:
        return (
            _resolve_worktree_path(resolved_repo_root, default_worktree_path)
            if default_worktree_path is not None
            else resolved_repo_root
        )
    unique_roots = tuple(dict.fromkeys(path for _agent_id, path in explicit_rows))
    if len(unique_roots) > 1:
        detail = ", ".join(f"{agent_id}={path}" for agent_id, path in explicit_rows)
        raise ValueError(
            "Planned lanes for one launched session span multiple worktrees; "
            f"bind one provider session to one workspace root. Saw: {detail}"
        )
    return unique_roots[0]


def _resolve_worktree_path(repo_root: Path, worktree: object) -> Path:
    text = str(worktree or "").strip()
    if not text:
        return repo_root.resolve()
    candidate = Path(text)
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


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
