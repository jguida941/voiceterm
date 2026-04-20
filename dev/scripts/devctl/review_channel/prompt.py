"""Prompt-building helpers for the transitional review-channel launcher."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..approval_mode import DEFAULT_APPROVAL_MODE
from ..runtime.role_profile import normalize_tandem_role, role_for_provider
from .launch_records import resolve_lane_worktree_path
from .prompt_sections import (
    OperatingContractInput,
    operating_contract_lines,
    worker_budget_lines,
)
from .prompt_support import (
    bootstrap_files,
    bridge_liveness_lines,
    context_escalation_lines,
    opening_line,
    resolve_conductor_capability,
    resolve_worker_budget,
    rollover_ack_details,
    rollover_ack_lines,
)
from .prompt_session_resume import build_session_resume_preamble

if TYPE_CHECKING:
    from ..commands.governance.session_resume_support import SessionCachePacket
    from .core import LaneAssignment


def build_conductor_prompt(
    *,
    provider: str,
    provider_name: str,
    other_name: str,
    role: str | None = None,
    other_provider: str | None = None,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    lanes: list["LaneAssignment"],
    workspace_root: Path | None = None,
    codex_workers: int,
    claude_workers: int,
    requested_worker_budget: int | None = None,
    dangerous: bool,
    rollover_threshold_pct: int,
    await_ack_seconds: int,
    retirement_note: str,
    rollover_command: str,
    promote_command: str,
    approval_mode: str = DEFAULT_APPROVAL_MODE,
    bridge_liveness: dict[str, object] | None = None,
    handoff_bundle: dict[str, str] | None = None,
    session_resume_packet: "SessionCachePacket | None" = None,
) -> str:
    """Render the initial conductor prompt for Codex or Claude."""
    resolved_role = (normalize_tandem_role(role) or role_for_provider(provider)).value
    resolved_workspace_root = (
        workspace_root.resolve() if workspace_root is not None else repo_root.resolve()
    )
    capability = resolve_conductor_capability(
        provider=provider,
        role=resolved_role,
        bridge_liveness=bridge_liveness,
    )
    provider_worker_budget = resolve_worker_budget(
        provider=provider,
        requested_worker_budget=requested_worker_budget,
        codex_workers=codex_workers,
        claude_workers=claude_workers,
    )
    rollover_ack_line, rollover_ack_section = rollover_ack_details(
        provider=provider,
        handoff_bundle=handoff_bundle,
    )
    lane_lines = [
        (
            f"- {lane.agent_id}: {lane.lane} | worktree {lane.worktree or '.'} | "
            f"workspace {resolve_lane_worktree_path(repo_root=repo_root, lane=lane)} | "
            f"branch {lane.branch} | scope {lane.mp_scope}"
        )
        for lane in lanes
    ]
    context_lines = context_escalation_lines(lanes=lanes)
    preamble = build_session_resume_preamble(
        provider=provider,
        role=resolved_role,
        repo_root=repo_root,
        session_resume_packet=session_resume_packet,
    )
    body = "\n".join(
        [
            opening_line(provider_name=provider_name, handoff_bundle=handoff_bundle),
            "",
            "Bootstrap in this exact order before acting:",
            *[
                f"- {item}"
                for item in bootstrap_files(
                    capability=capability,
                    repo_root=repo_root,
                    review_channel_path=review_channel_path,
                    bridge_path=bridge_path,
                    handoff_bundle=handoff_bundle,
                )
            ],
            "",
            (
                "After bootstrap, FIRST drain the review-channel inbox and "
                "ack any pending operator-authority packets BEFORE any "
                "reviewer-bootstrap, code reading, git diff, or routed bundle:"
            ),
            (
                f"- `python3 dev/scripts/devctl.py review-channel --action inbox "
                f"--target {provider} --status pending --terminal none --format md`"
            ),
            (
                f"- For each pending instruction-class packet: "
                f"`review-channel --action ack --packet-id <id> --actor {provider}`."
            ),
            "",
            "Operating contract:",
            *operating_contract_lines(
                OperatingContractInput(
                    capability=capability,
                    provider_id=provider,
                    provider_name=provider_name,
                    counterpart_provider_id=str(other_provider or "").strip().lower(),
                    counterpart_provider_name=other_name,
                    repo_root=repo_root,
                    approval_mode=approval_mode,
                    rollover_threshold_pct=rollover_threshold_pct,
                    promote_command=promote_command,
                )
            ),
            f"- Planned rollover command: `{rollover_command}`",
            f"- Planned next-task promotion command: `{promote_command}`",
            (
                "- After the fresh conductor sessions launch and acknowledge the "
                "handoff bundle, exit the old session cleanly so it does not linger "
                "in memory or on the host."
            ),
            f"- Session workspace root: `{resolved_workspace_root}`",
            *bridge_liveness_lines(bridge_liveness),
            *rollover_ack_lines(
                rollover_ack_line=rollover_ack_line,
                rollover_ack_section=rollover_ack_section,
            ),
            "",
            *worker_budget_lines(
                capability=capability,
                provider_name=provider_name,
                planned_lane_count=len(lanes),
                provider_worker_budget=provider_worker_budget,
            ),
            *context_lines,
            "",
            f"{provider_name} planned lane assignments:",
            *lane_lines,
            "",
            "Execution reminders:",
            (
                "- Keep `bridge.md` current-state only; do not turn it into a "
                "transcript dump."
            ),
            (
                "- Keep the active markdown bridge disciplined until the structured "
                "`review-channel` / overlay-native path replaces it."
            ),
            retirement_note,
            "",
            (
                f"Coordinate with {other_name} only through `bridge.md` plus the "
                "required operator-visible progress updates."
            ),
        ]
    )
    if preamble:
        return preamble + "\n\n" + body
    return body
